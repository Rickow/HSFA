#!/bin/bash
# lance.sh NOM SCRIPT_LUA NF "VARS..." : Upper (copie locale ro5/) sur le fork sfa3hx, nvram/cfg temporaires, sans -state.
# Sorties dans runs/NOM/.
A=${HSFA_WORKSPACE}/work/agent_effets_upper; R=$A/ro5
N=$1; S=$2; nf=$3; vars=$4; D=$A/runs/$N; rm -rf $D; mkdir -p $D
cd $D
env $vars OUT=$D/journal.txt NF=$nf BANC_COMMUN=351 HSFA_PLANS=300,340,3a0 \
  HSFA_GFX=$R/hsfa_gfx.bin,$R/hsfa_plans.bin@3000000 BANC_BANQUES=$R/banques_hx/ BANC_PTR_ANIM=FF40BC \
  BANC_GFX_INTRO=456 BANC_DIR=$R/ RUN=$D \
  timeout 7200 nice -n 19 ${HSFA_WORKSPACE}/mame-fork/mame/cps2f sfa3hx -rompath $R/roms_fork -video none -sound none -nothrottle \
  -skip_gameinfo -nvram_directory $D/nv -cfg_directory $D/cfg -snapshot_directory $D/snap \
  -autoboot_script $S > $D/mame.log 2>&1
echo "$N termine : $(tail -1 $D/journal.txt)"
