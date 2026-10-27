#!/bin/bash
# (agent_integration_max) Lancement du fork MAME (sfa3hx) sur un dossier de construction d'Upper (avec ou sans MAX).
# Usage : lance_max.sh DOSSIER_BANC SORTIE [variables de tournee_max.lua dans l'environnement : PERSO, PERSO2, VS, MODE,
#         ALEA, NF, SNAPP...]. nvram / cfg / instantanés dans des dossiers propres à chaque lancement (SORTIE.d/).
mkdir -p "$(dirname "$2")"; H=${HSFA_WORKSPACE}; W5=$H/work/mame_ro5; B=$(readlink -f "$1"); O=$(readlink -f "$2"); D=$O.d
[ -s $B/sfa3max_cache.txt ] && export SFA3MAX_CACHE=$(cat $B/sfa3max_cache.txt)   # cache MAX du banc (2b11)
eval $(python3 ${HSFA_WORKSPACE}/work/agent_integration_max/untranspile/max_cache.py)   # (2b11) disposition selon SFA3MAX_CACHE
GP=""; [ -f $B/max_plus_gfx.bin ] && GP=",$B/max_plus_gfx.bin@$PLUSG"   # (agent_integration_max) HUD / aperçu MAX
[ -n "$GARDE" ] || rm -rf "$D"; mkdir -p "$D/nv" "$D/cfg" "$D/snap" "$D/sta"
MC=0-0
G=${MAXFORK%/}
export HSFA_GFX=$W5/hsfa_gfx.bin,$G/max_gfx.bin@$MAXG,$G/max_portraits_gfx.bin@$PORTG${GP},$W5/hsfa_plans.bin@$PLANSG
export BANC_COMMUN=351 HSFA_PLANS=$PLANS BANC_BANQUES=$B/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_GFX_INTRO=456 BANC_DIR=$B/
export HSFA_EXT=$B HSFA_SON=${HSFA_SON:-$H/work/agent_son_max/roms_son_max_pas} MAX_CODE=${MAX_CODE:-$MC} OUT=$O MODE_ADR=${MODE_ADR:-FF4201}
[ "$HSFA_SON" = aucun ] && unset HSFA_SON   # (2b23) comme le lance.sh du banc des coups (ROM son d'origine)
cd $H/work/mame
timeout ${DUREE:-3000} nice -n 19 $H/mame-fork/mame/cps2f sfa3hx -rompath $B/roms_fork ${VIDEO:--video none} -sound none -nothrottle \
  -skip_gameinfo -nvram_directory $D/nv -cfg_directory $D/cfg -snapshot_directory $D/snap -state_directory $D/sta $EXTRA \
  -autoboot_script ${LUA:-$H/work/agent_integration_max/lua/tournee_max.lua} > $D/mame.txt 2>&1
echo "fin : $(tail -1 $O)"
