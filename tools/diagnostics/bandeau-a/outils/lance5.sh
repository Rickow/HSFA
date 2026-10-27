#!/bin/bash
# lance5.sh <nom> <dossier de travail (mame_ro5 | mame_ro5_old)> : Upper au fork (sfa3hx), tournee.lua + journaux. Env : NF SNAPP SNAP0 PERSO SCRIPT TOUT
B=${HSFA_WORKSPACE}/work/agent_bandeau_A; N=$1; WD=$B/$2; W5=${HSFA_WORKSPACE}/work/mame_ro5; T=$B/essais/$N; rm -rf $T; mkdir -p $T/nv $T/cfg $T/snap
cd ${HSFA_WORKSPACE}/work/mame
unset REF
BANC_COMMUN=351 PERSO=${PERSO:-00} HSFA_PLANS=300,340,3a0 HSFA_GFX=$W5/hsfa_gfx.bin,$W5/hsfa_plans.bin@3000000 BANC_BANQUES=$W5/banques_hx/ \
BANC_PTR_ANIM=FF40BC BANC_GFX_INTRO=456 BANC_DIR=$WD/ OUT=$T/tour.txt REGOUT=$T/regs.txt REG0=${REG0:-999999} \
timeout ${TMO:-2400} nice -n 19 ${HSFA_WORKSPACE}/mame-fork/mame/cps2f sfa3hx -rompath $WD/roms_fork -video none -sound none -nothrottle -skip_gameinfo \
  -nvram_directory $T/nv -cfg_directory $T/cfg -snapshot_directory $T/snap -autoboot_script ${SCRIPT:-$B/lua/tache.lua} > $T/mame.txt 2>&1
rm -rf $T/nv $T/cfg
