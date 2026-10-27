#!/bin/bash
# (etape B) cadence d'Upper sur le fork : fork_cad.sh <dossier ro5> <sortie> [VAR=val...] (tournee.lua, Ryu par defaut ;
# images CAD_F0-CAD_F1 du releve, defaut 4000-14000)
H=${HSFA_WORKSPACE}; B=$H/work/agent_reorg_B; W=$1; O=$2; shift 2; G=$H/work/mame_ro5; T=$(mktemp -d -p $W fc_XXXX); cd $T
env BANC_COMMUN=351 BANC_GFX_INTRO=456 PERSO=${PERSO:-00} NF=${NF:-14000} CAD_F0=${CAD_F0:-4000} CAD_F1=${CAD_F1:-14000} "$@" \
  OUT=$O.log CAD_OUT=$O HSFA_PLANS=300,340,3a0 HSFA_GFX=$G/hsfa_gfx.bin,$G/hsfa_plans.bin@3000000 \
  BANC_BANQUES=$G/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_DIR=$W/ timeout 3600 nice -n 19 $H/mame-fork/mame/cps2f sfa3hx \
  -rompath $W/roms_fork -nvram_directory $T/nv -cfg_directory $T/cfg -snapshot_directory $T/snap -video none -sound none \
  -nothrottle -skip_gameinfo -autoboot_script $B/runs/tour_cad.lua > $T/mame.txt 2>&1
rm -rf $T
