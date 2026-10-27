#!/bin/bash
# (etape 7) copie de lance_vs.sh avec LISTE prise dans l environnement. Non-regression VERSUS d'Hyper (tournee_hyper.lua d'agent_hyper_etats, lecture seule) sur une construction figee.
# Usage : lance_vs.sh ROMS_FORK BANC_DIR TRACE NF   (ex. fige/ro9/roms_fork fige/ro9/ ; constructions/ro9a/roms_fork constructions/ro9a/b9/)
H=${HSFA_WORKSPACE}; W9=$H/work/mame_ro9; G=$H/work/greffe_arcade
R=$G/$1; B=$G/$2; D=$G/traces/$3; nf=$4; rm -rf $D; mkdir -p $D
cd $H/work/mame
CONTOURNE_E=${CONTOURNE_E:-1} LISTE="${LISTE:-00.A/01.Z}" MODEJEU=1 NF=$nf OUT=$D/journal.txt BANC_COMMUN=545 HSFA_PLANS=300,340,3a0 \
  HSFA_GFX=$W9/hsfa_gfx.bin,$W9/hsfa_plans.bin@3000000 BANC_BANQUES=$W9/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_DIR=$B \
  timeout ${TMAX:-2400} nice -n 19 $H/mame-fork/mame/cps2f sfa3hx -rompath $R -nvram_directory $D/nv -cfg_directory $D/cfg \
  -video none -sound none -nothrottle -skip_gameinfo -autoboot_script $H/work/agent_hyper_etats/lua/tournee_hyper.lua > $D/mame.log 2>&1
echo "$3 : $(grep -cE 'MANCHE' $D/journal.txt) manches ; $(grep -E 'EXC|FIN' $D/journal.txt | tail -1)"
