#!/bin/bash
# (banc_coups) lance.sh <dossier_sortie> <module> <script.lua> [VAR=val ...]
#  module : ref3 (arcade sfa3ud, REF=1) | ro3 (SFA3 traduit, v150) | ro5 (Upper, fork) | ro9 (Hyper, fork) | max (Upper + MAX)
#           | sfa | sfa2 | sfz2al (arcades SFA1 / SFA2 / Alpha 2 Gold, REF=1)
# Sorties : <dossier>/log.txt (OUT), mame.txt ; nvram / cfg / etats propres au lancement (dossier <dossier>/tmp).
# Jamais -state : la sauvegarde d'etat est prise et rechargee par le script Lua (-state_directory = <dossier>/tmp/sta).
set -u
D=$(readlink -f "$1"); MOD=$2; LUA=$(readlink -f "$3"); shift 3
# (max58, 13/11) readlink -f rend une chaîne VIDE si le parent n'existe pas : dossier vide -> mkdir '' + /mame.txt ;
# script vide -> MAME tournait sans script jusqu'au délai (fins « OK, 0 manche »). Refus net dans les deux cas.
[ -n "$D" ] && [ "$D" != "/" ] || { echo "lance.sh : dossier de sortie invalide « $1 » (parent absent ?)" >&2; exit 2; }
[ -n "$LUA" ] && [ -f "$LUA" ] || { echo "lance.sh : script Lua introuvable « $3 »" >&2; exit 2; }
# (agent_integration_max, b38, 01/11) MAXDIR passé en argument : exporté AVANT le choix du module (sinon le module max
# chargeait max6 : fd.py / frame_data.sh mesuraient max6 quelle que soit la copie demandée)
for kv in "$@"; do case $kv in MAXDIR=*) export "$kv";; esac; done
H=${HSFA_WORKSPACE:-$HOME/hsfa}; R=${REFS:-$H/work/references/v150}; B=$H/work/banc_coups; FORK=$H/mame-fork/mame/cps2f
mkdir -p "$D"
[ -n "$D" ] && [ "$D" != "/" ] && rm -rf "${D:?}/tmp" "${D:?}/log.txt"
mkdir -p "$D/tmp/nv" "$D/tmp/cfg" "$D/tmp/sta" "$D/tmp/snap"
COM=(-video none -sound none -nothrottle -skip_gameinfo -nvram_directory "$D/tmp/nv" -cfg_directory "$D/tmp/cfg"
     -state_directory "$D/tmp/sta" -snapshot_directory "$D/tmp/snap" -autoboot_script "$LUA")
export OUT="$D/log.txt" MODULE=$MOD
case $MOD in
  ref3) export REF=1; JEU=(mame sfa3ud -rompath $H/work/mame/roms);;
  refjp) # oracle japonais 980727 (sfz3jr1) : ROM brute + opcodes dechiffres poses par le Lua (oracle_jp/LISEZMOI)
        export REF=1 OPCODES=$B/oracle_jp/opcodes_jp_be.bin; JEU=(mame sfa3ud -rompath $B/oracle_jp/roms);;
  ro3)  export BANC_DIR=$R/ro3/; JEU=(mame sfa3ud -rompath $R/ro3/roms_tr);;
  ro5)  export BANC_DIR=$R/ro5/ BANC_COMMUN=351 HSFA_PLANS=300,340,3a0 HSFA_GFX=$R/ro5/hsfa_gfx.bin,$R/ro5/hsfa_plans.bin@3000000 \
          BANC_BANQUES=$R/ro5/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_GFX_INTRO=456 UPPER=1
        JEU=($FORK sfa3hx -rompath $R/ro5/roms_fork);;
  ro9)  export BANC_DIR=$R/ro9/ BANC_COMMUN=545 HSFA_PLANS=300,340,3a0 HSFA_GFX=$R/ro9/hsfa_gfx.bin,$R/ro9/hsfa_plans.bin@3000000 \
          BANC_BANQUES=$R/ro9/banques_hx/ BANC_PTR_ANIM=FF40BC HYPER=1
        JEU=($FORK sfa3hx -rompath $R/ro9/roms_fork);;
  max)  # construction d'essai MAX (copie figee : MAXDIR, defaut max6/). Disposition graphique : MAXDIR/env_max_cache.txt
        # (sortie figee de max_cache.py : MAXG PORTG PLUSG PLANSG PLANS MAXFORK) si present, sinon celle de max6
        M=$(readlink -f ${MAXDIR:-$B/max6}); W5=$H/work/mame_ro5
        MAXG=26D5580; PORTG=2E03600; PLUSG=2E45000; PLANSG=3000000; PLANS=300,340,3a0; MAXFORK=$HOME/.cache/sfa3max/fork/
        [ -s $M/env_max_cache.txt ] && eval "$(cat $M/env_max_cache.txt)"
        G=${MAXFORK%/}
        GP=""; [ -f $M/max_plus_gfx.bin ] && GP=",$M/max_plus_gfx.bin@$PLUSG"
        export HSFA_GFX=$W5/hsfa_gfx.bin,$G/max_gfx.bin@$MAXG,$G/max_portraits_gfx.bin@$PORTG${GP},$W5/hsfa_plans.bin@$PLANSG \
          BANC_COMMUN=351 HSFA_PLANS=$PLANS BANC_BANQUES=$M/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_GFX_INTRO=456 \
          BANC_DIR=$M/ HSFA_EXT=$M UPPER=1
        JEU=($FORK sfa3hx -rompath $M/roms_fork);;
  sfa|sfa2|sfz2al|sfa2u) export REF=1 ARCADE=$MOD; JEU=(mame $MOD -rompath $B/roms_arc);;
  *) echo "module inconnu : $MOD"; exit 2;;
esac
for kv in "$@"; do export "$kv"; done
cd $H/work/mame
timeout -s KILL ${DELAI:-3000} nice -n 19 "${JEU[@]}" "${COM[@]}" > "$D/mame.txt" 2>&1
echo "fin $MOD $(basename "$D") code=$?"
