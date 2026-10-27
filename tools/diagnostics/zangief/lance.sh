#!/bin/bash
# agent_zangief : lanceur Upper au fork (cf. scripts/untranspile/nonreg_ro5.sh). Variables : PERSO, STG, NF, DUMPAT, TAG,
# GFX (defaut ROM partagee), PLANS (fichier hsfa_plans.bin), LUA (defaut lua/usine.lua)
A=${HSFA_WORKSPACE}/work/agent_zangief; W5=${HSFA_WORKSPACE}/work/mame_ro5
PLANS=${PLANS:-$W5/hsfa_plans.bin}
cd ${HSFA_WORKSPACE}/work/mame
BANC_COMMUN=351 PERSO=${PERSO:-10} NF=${NF:-6000} HSFA_PLANS=300,340,3a0 \
HSFA_GFX=$W5/hsfa_gfx.bin,$PLANS@3000000 BANC_BANQUES=$W5/banques_hx/ BANC_PTR_ANIM=FF40BC \
BANC_GFX_INTRO=456 BANC_DIR=$W5/ OUT=$A/dump/${TAG:-u}.txt DDIR=$A/dump/ \
timeout 1500 nice -n 19 ${HSFA_WORKSPACE}/mame-fork/mame/cps2f sfa3hx \
  -rompath $W5/roms_fork -video ${VIDEO:-none} -sound none -nothrottle -skip_gameinfo \
  -nvram_directory $A/nv/${TAG:-u} -cfg_directory $A/cfg/${TAG:-u} -snapshot_directory $A/snap/${TAG:-u} \
  -autoboot_script ${LUA:-$A/lua/usine.lua} 2>&1 | grep -v -E "^(Driver|S )" | tail -20
