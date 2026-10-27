#!/bin/bash
# (etape B) partie sur le fork avec le journal des talons : fork_j.sh ro5|ro9 <dossier> <sortie_journal> [VAR=val...]
# ro5 : tournee.lua (Ryu par defaut, PERSO) ; ro9 : partie VERSUS (tournee_hyper.lua, comme hyper_vs_B.sh).
H=${HSFA_WORKSPACE}; B=$H/work/agent_reorg_B; m=$1; W=$2; J=$3; shift 3
G=$H/work/mame_$m; T=$(mktemp -d -p $W fj_XXXX); cd $T
if [ $m = ro5 ]; then S=$B/runs/tournee_j.lua; X="BANC_COMMUN=351 BANC_GFX_INTRO=456 PERSO=${PERSO:-00} NF=${NF:-40000}"
else S=$B/runs/hyper_vs_j.lua; X="BANC_COMMUN=545 LISTE=00.A/01.Z,02.Z/03.Z MODEJEU=1 NF=${NF:-20000}"; fi
env $X "$@" OUT=$T/out.log JCONV_OUT=$J HSFA_PLANS=300,340,3a0 HSFA_GFX=$G/hsfa_gfx.bin,$G/hsfa_plans.bin@3000000 \
  BANC_BANQUES=$G/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_DIR=$W/ timeout 3600 nice -n 19 $H/mame-fork/mame/cps2f sfa3hx \
  -rompath $W/roms_fork -nvram_directory $T/nv -cfg_directory $T/cfg -snapshot_directory $T/snap -video none -sound none \
  -nothrottle -skip_gameinfo -autoboot_script $S > $T/mame.txt 2>&1
grep -E "EXC|FIN" $T/out.log | head -3; cp $T/out.log $J.log; rm -rf $T
