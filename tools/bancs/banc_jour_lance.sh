#!/bin/bash
# banc_jour_lance.sh <dossier_sortie> <module> <script.lua> [VAR=val ...] — lancement d'UNE partie MAME pour banc_jour.
# = banc_coups/lance.sh (modules ro3 / ro5 / ro9 / max) + module greffe (banc_greffe_upper/lance.sh), avec :
#   - lance_emu (nice, places globales, étiquette HSFA_AGENT, registre) ;
#   - empreinte de ce qui est réellement chargé écrite dans <dossier>/empreinte.txt, comparée à ATTENDU_REF /
#     ATTENDU_MD5 (différente -> rien n'est lancé, code 86) ;
#   - graphismes et banques pris dans les références FIGÉES (REFS, défaut v153), jamais dans work/mame_ro* (reconstruits).
# Modules : ro3 | ro5 | ro9 (REFS/<module>) ; max (MAXDIR = copie figée, obligatoire) ; greffe (GREFFE_C = construction
# figée, obligatoire). Sorties : <dossier>/log.txt (OUT), mame.txt, empreinte.txt ; nvram / cfg / états dans <dossier>/tmp.
# DELAI (s, défaut 3000) : arrêt forcé. Jamais -state.
set -u
mkdir -p "$1" && D=$(readlink -f "$1"); MOD=$2; LUA=$(readlink -f "$3"); shift 3
[ -n "$D" ] && [ -f "$LUA" ] || { echo "banc_jour_lance.sh : dossier ou script Lua invalide ($1, $3)" >&2; exit 2; }
for kv in "$@"; do case $kv in MAXDIR=*|GREFFE_C=*|REFS=*|DELAI=*) export "$kv";; esac; done
H=${HSFA_WORKSPACE:-$HOME/hsfa}; R=${REFS:-$H/work/references/v153}; FORK=$H/mame-fork/mame/cps2f; O=$(dirname "$(readlink -f "$0")")   # lance_emu à côté
mkdir -p "$D"
[ -n "$D" ] && [ "$D" != "/" ] && rm -rf "${D:?}/tmp" "${D:?}/log.txt"
mkdir -p "$D/tmp/nv" "$D/tmp/cfg" "$D/tmp/sta" "$D/tmp/snap"
COM=(-video none -sound none -nothrottle -skip_gameinfo -nvram_directory "$D/tmp/nv" -cfg_directory "$D/tmp/cfg"
     -state_directory "$D/tmp/sta" -snapshot_directory "$D/tmp/snap" -autoboot_script "$LUA")
export OUT="$D/log.txt" MODULE=$MOD
case $MOD in
  ro3)  export BANC_DIR=$R/ro3/; JEU=(mame sfa3ud -rompath $R/ro3/roms_tr);;
  ro5)  export BANC_DIR=$R/ro5/ BANC_COMMUN=351 HSFA_PLANS=300,340,3a0 HSFA_GFX=$R/ro5/hsfa_gfx.bin,$R/ro5/hsfa_plans.bin@3000000 \
          BANC_BANQUES=$R/ro5/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_GFX_INTRO=456 UPPER=1
        JEU=($FORK sfa3hx -rompath $R/ro5/roms_fork);;
  ro9)  export BANC_DIR=$R/ro9/ BANC_COMMUN=545 HSFA_PLANS=300,340,3a0 HSFA_GFX=$R/ro9/hsfa_gfx.bin,$R/ro9/hsfa_plans.bin@3000000 \
          BANC_BANQUES=$R/ro9/banques_hx/ BANC_PTR_ANIM=FF40BC HYPER=1
        JEU=($FORK sfa3hx -rompath $R/ro9/roms_fork);;
  max)  [ -n "${MAXDIR:-}" ] || { echo "module max : MAXDIR obligatoire" >&2; exit 2; }
        M=$(readlink -f "$MAXDIR"); W5=$R/ro5
        MAXG=26D5580; PORTG=2E03600; PLUSG=2E45000; PLANSG=3000000; PLANS=300,340,3a0; MAXFORK=$HOME/.cache/sfa3max/fork/
        [ -s $M/env_max_cache.txt ] && eval "$(cat $M/env_max_cache.txt)"
        G=${MAXFORK%/}
        GP=""; [ -f $M/max_plus_gfx.bin ] && GP=",$M/max_plus_gfx.bin@$PLUSG"
        export HSFA_GFX=$W5/hsfa_gfx.bin,$G/max_gfx.bin@$MAXG,$G/max_portraits_gfx.bin@$PORTG${GP},$W5/hsfa_plans.bin@$PLANSG \
          BANC_COMMUN=351 HSFA_PLANS=$PLANS BANC_BANQUES=$M/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_GFX_INTRO=456 \
          BANC_DIR=$M/ HSFA_EXT=$M UPPER=1
        JEU=($FORK sfa3hx -rompath $M/roms_fork);;
  greffe) [ -n "${GREFFE_C:-}" ] || { echo "module greffe : GREFFE_C obligatoire" >&2; exit 2; }
        C=$(readlink -f "$GREFFE_C"); BQ=$R/ro9/banques_hx/; [ -d $C/banques_hx ] && BQ=$C/banques_hx/
        export BANC_DIR=$C/b9/ BANC_COMMUN=545 BANC_COMMUN_UPPER=351 HSFA_PLANS=300,340,3a0 \
          HSFA_GFX=$R/ro9/hsfa_gfx.bin,$R/ro9/hsfa_plans.bin@3000000,$R/ro5/hsfa_plans.bin@4000000 \
          BANC_BANQUES=$BQ BANC_PTR_ANIM=FF40BC HYPER=1
        RP=$C/roms_fork; [ -e $RP/sfa3hx ] || { RP=$D/tmp/roms; mkdir -p $RP; ln -sfn $C/b9/roms_ro9/sfa3ud $RP/sfa3hx; }
        JEU=($FORK sfa3hx -rompath $RP);;
  *) echo "module inconnu : $MOD" >&2; exit 2;;
esac
for kv in "$@"; do export "$kv"; done
export HSFA_AGENT=${HSFA_AGENT:-banc_jour}
cd $H/work/mame
"$O/lance_emu" --empreinte "$D/empreinte.txt" -- timeout -s KILL "${DELAI:-3000}" "${JEU[@]}" "${COM[@]}" > "$D/mame.txt" 2>&1
c=$?
echo "fin $MOD $(basename "$D") code=$c"
exit $c
