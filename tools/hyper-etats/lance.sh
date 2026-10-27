#!/bin/bash
# (agent_hyper_etats) lance Hyper (ro9) sur le fork sfa3hx. Usage : lance.sh <nom>  (variables d'env exportees : INPUTS, NF, SCRIPT...)
# Sorties : essais/<nom>.log, essais/<nom>/ (captures), essais/nv_<nom>/ (NVRAM propre), essais/cfg_<nom>/
N=$1; B=${HSFA_WORKSPACE}/work/agent_hyper_etats; W=${HSFA_WORKSPACE}/work/mame_ro9
rm -rf $B/essais/$N $B/essais/nv_$N $B/essais/cfg_$N; mkdir -p $B/essais/$N $B/essais/nv_$N $B/essais/cfg_$N
cd ${HSFA_WORKSPACE}/work/mame
OUT=$B/essais/$N.log BANC_COMMUN=545 HSFA_PLANS=300,340,3a0 \
HSFA_GFX=$W/hsfa_gfx.bin,$W/hsfa_plans.bin@3000000 BANC_BANQUES=$W/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_DIR=$W/ \
nice -n 19 ${HSFA_WORKSPACE}/mame-fork/mame/cps2f sfa3hx -rompath $W/roms_fork -nvram_directory $B/essais/nv_$N \
  -cfg_directory $B/essais/cfg_$N -snapshot_directory $B/essais/$N -video none -sound none -nothrottle -skip_gameinfo \
  ${DEBUG:+-debug -debugger none} -autoboot_script ${SCRIPT:-$B/lua/hyper.lua} > $B/essais/$N.mame.txt 2>&1
