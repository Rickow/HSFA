#!/bin/bash
# run.sh NOM ref|tr140|up140|<dossier> : lance coups.lua ; env PERSO, PERSO2, ACTS, FIN, SNAPREL, DUMPOBJ, DUMPAT
# <dossier> commencant par "up" = Upper (fork cps2f sfa3hx), sinon SFA3 (mame sfa3ud) ; <dossier>/roms + ext_*.bin
A=${HSFA_WORKSPACE}/work/agent_coups; N=$1; R=$2; V=${3:-none}; W5=${HSFA_WORKSPACE}/work/mame_ro5
mkdir -p $A/out/$N; rm -rf $A/out/$N/nv $A/out/$N/cfg $A/out/$N/snap
JEU="mame sfa3ud"
case $R in
  ref) RP=${HSFA_WORKSPACE}/work/mame/roms; export REF=1;;
  tr140) RP=$A/tr140; export BANC_DIR=$A/banc140/;;
  up*) RP=$A/$R/roms; JEU="${HSFA_WORKSPACE}/mame-fork/mame/cps2f sfa3hx"
       export BANC_DIR=$A/$R/ BANC_COMMUN=351 HSFA_PLANS=300,340,3a0 HSFA_GFX=$W5/hsfa_gfx.bin,$W5/hsfa_plans.bin@3000000 \
         BANC_BANQUES=$W5/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_GFX_INTRO=456 UPPER=1;;
  *) RP=$A/$R/roms; export BANC_DIR=$A/$R/;;
esac
cd ${HSFA_WORKSPACE}/work/mame
OUT=$A/out/$N/log.txt timeout -s KILL 1500 nice -n 19 $JEU -rompath $RP -video $V -sound none -nothrottle -skip_gameinfo \
  -nvram_directory $A/out/$N/nv -cfg_directory $A/out/$N/cfg -snapshot_directory $A/out/$N/snap \
  -autoboot_script $A/${SCRIPT:-coups.lua} >$A/out/$N/mame.txt 2>&1
