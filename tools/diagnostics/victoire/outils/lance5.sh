#!/bin/bash
# lance5.sh <nom> [dossier de travail, defaut mame_ro5] : Upper au fork (sfa3hx), tournee.lua (ou SCRIPT). Env : NF SNAPP SNAP0 PERSO SCRIPT BASE_LUA
V=${HSFA_WORKSPACE}/work/agent_victoire; N=$1; WD=$V/${2:-mame_ro5}; W5=${HSFA_WORKSPACE}/work/mame_ro5; T=$V/essais/$N; rm -rf $T; mkdir -p $T/nv $T/cfg $T/snap
cd $T; unset REF
BANC_COMMUN=351 PERSO=${PERSO:-00} HSFA_PLANS=300,340,3a0 HSFA_GFX=$W5/hsfa_gfx.bin,$W5/hsfa_plans.bin@3000000 BANC_BANQUES=$W5/banques_hx/ \
BANC_PTR_ANIM=FF40BC BANC_GFX_INTRO=456 BANC_DIR=$WD/ OUT=$T/tour.txt \
timeout ${TMO:-2400} nice -n 19 ${HSFA_WORKSPACE}/mame-fork/mame/cps2f sfa3hx -rompath $WD/roms_fork -video none -sound none -nothrottle -skip_gameinfo $XOPT \
  -nvram_directory $T/nv -cfg_directory $T/cfg -snapshot_directory $T/snap -autoboot_script ${SCRIPT:-${HSFA_WORKSPACE}/work/mame/tournee.lua} > $T/mame.txt 2>&1
rm -rf $T/nv $T/cfg
