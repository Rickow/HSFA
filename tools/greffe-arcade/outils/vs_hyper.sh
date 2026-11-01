#!/bin/bash
# (28/10) VERSUS d'Hyper seule (banc tournee_hyper, K.O. forces), ROM d'un dossier de construction : vs_hyper.sh DOSSIER_ROM DOSSIER_BLOCS TRACE "LISTE" NF ["VARS"]
H=${HSFA_WORKSPACE}; G=$H/work/greffe_arcade; W=$H/work/mame_ro9; T=$G/traces/$3; rm -rf $T; mkdir -p $T
mkdir -p $T/roms; ln -sfn $1 $T/roms/sfa3hx
cd $H/work/mame; env LISTE="$4" MODEJEU=1 NF=$5 OUT=$T/vs.log BANC_COMMUN=545 HSFA_PLANS=300,340,3a0 CONTOURNE_E=1 \
  HSFA_GFX=$W/hsfa_gfx.bin,$W/hsfa_plans.bin@3000000 BANC_BANQUES=$W/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_DIR=$2/ HSFA_BANC_LUA=$H/work/mame $6 \
  timeout ${TMAX:-3000} nice -n 19 $H/mame-fork/mame/cps2f sfa3hx -rompath $T/roms -nvram_directory $T/nv -cfg_directory $T/cfg \
  -video none -sound none -nothrottle -skip_gameinfo -autoboot_script ${SCRIPT_LUA:-$G/lua/tournee_hyper_guy.lua} > $T/mame.txt 2>&1
echo "$3 : $(grep -c MANCHE $T/vs.log) manches, $(tail -1 $T/vs.log)"
