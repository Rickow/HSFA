#!/bin/bash
# lance9.sh <nom> <dossier (mame_ro9 | mame_ro9_old)> : Hyper au fork, tournee_hyper.lua VERSUS + journaux. Env : NF SNAPP... TOUT
B=${HSFA_WORKSPACE}/work/agent_bandeau_A; N=$1; WD=$B/$2; W9=${HSFA_WORKSPACE}/work/mame_ro9; T=$B/essais/$N; rm -rf $T; mkdir -p $T/nv $T/cfg $T/snap
cd ${HSFA_WORKSPACE}/work/mame
LISTE=${LISTE:-"00.A/01.Z,02.Z/03.Z"} MODEJEU=1 NF=${NF:-20000} OUT=$T/vs.log BANC_COMMUN=545 HSFA_PLANS=300,340,3a0 \
HSFA_GFX=$W9/hsfa_gfx.bin,$W9/hsfa_plans.bin@3000000 BANC_BANQUES=$W9/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_DIR=$WD/ \
BASE_LUA2=${BASE_LUA2:-${HSFA_WORKSPACE}/work/agent_hyper_etats/lua/tournee_hyper.lua} \
timeout ${TMO:-2400} nice -n 19 ${HSFA_WORKSPACE}/mame-fork/mame/cps2f sfa3hx -rompath $WD/roms_fork -nvram_directory $T/nv -cfg_directory $T/cfg \
  -snapshot_directory $T/snap -video none -sound none -nothrottle -skip_gameinfo -autoboot_script ${SCRIPT:-$B/lua/tache.lua} > $T/mame.txt 2>&1
rm -rf $T/nv $T/cfg
