#!/bin/bash
# lance9.sh <nom> [dossier, defaut mame_ro9] : Hyper au fork, tournee_hyper.lua VERSUS (ou SCRIPT + BASE_LUA). Env : NF SNAPP SNAP0 LISTE
V=${HSFA_WORKSPACE}/work/agent_victoire; N=$1; WD=$V/${2:-mame_ro9}; W9=${HSFA_WORKSPACE}/work/mame_ro9; T=$V/essais/$N; rm -rf $T; mkdir -p $T/nv $T/cfg $T/snap
cd $T
LISTE=${LISTE:-"00.A/01.Z,02.Z/03.Z"} MODEJEU=${MODEJEU:-1} NF=${NF:-20000} OUT=$T/vs.log BANC_COMMUN=545 HSFA_PLANS=300,340,3a0 \
HSFA_GFX=$W9/hsfa_gfx.bin,$W9/hsfa_plans.bin@3000000 BANC_BANQUES=$W9/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_DIR=$WD/ \
timeout ${TMO:-2400} nice -n 19 ${HSFA_WORKSPACE}/mame-fork/mame/cps2f sfa3hx -rompath $WD/roms_fork -nvram_directory $T/nv -cfg_directory $T/cfg $XOPT \
  -snapshot_directory $T/snap -video none -sound none -nothrottle -skip_gameinfo -autoboot_script ${SCRIPT:-${HSFA_WORKSPACE}/work/agent_hyper_etats/lua/tournee_hyper.lua} > $T/mame.txt 2>&1
rm -rf $T/nv $T/cfg
