#!/bin/bash
# (etape B) PARTIE VERSUS d'Hyper (comme scripts/untranspile/valide_tout.sh) sur un dossier de l'etape B :
#   hyper_vs_B.sh <dossier>   (TRAVAIL de MODULE=ro9 mame_test.py ; roms_fork/sfa3hx -> ../roms_ro9/sfa3ud)
# Graphismes / banques : work/mame_ro9 (lecture seule). Attendu : aucune exception (lignes SELECTION/MANCHE/FIN).
H=${HSFA_WORKSPACE}; W9=${1:?dossier}; G=$H/work/mame_ro9
T=$(mktemp -d -p $W9 vs_XXXX); cd $T
LISTE="00.A/01.Z,02.Z/03.Z" MODEJEU=1 NF=${NF:-20000} OUT=$T/vs.log BANC_COMMUN=545 HSFA_PLANS=300,340,3a0 \
  HSFA_GFX=$G/hsfa_gfx.bin,$G/hsfa_plans.bin@3000000 BANC_BANQUES=$G/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_DIR=$W9/ \
  timeout 2400 nice -n 19 $H/mame-fork/mame/cps2f sfa3hx -rompath $W9/roms_fork -nvram_directory $T/nv -cfg_directory $T/cfg \
  -snapshot_directory $T/snap -video none -sound none -nothrottle -skip_gameinfo \
  -autoboot_script $H/work/agent_hyper_etats/lua/tournee_hyper.lua > $T/mame.txt 2>&1
grep -E "SELECTION|MANCHE|EXC|FIN" $T/vs.log | tail -n 6; cp $T/vs.log $W9/vs.log; rm -rf $T
