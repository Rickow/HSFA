#!/bin/bash
# (etape B) NON-REGRESSION SFA3 sur un dossier de travail de l'etape B (copie de scripts/untranspile/nonreg.sh) :
#   nonreg_B.sh <dossier>   (dossier = TRAVAIL de mame_test.py : roms_tr/, carte_image.txt, ext_*.bin)
# 3 diagnostics (diag.py de la copie : nvram/cfg temporaires) + test des commandes (reference work/mame/cmd_ref.txt).
# Attendu : « aucune exception » x3, « 42 actions, 0 differentes ».
B=${HSFA_WORKSPACE}/work/agent_reorg_B; U=$B/untranspile; W=${1:?dossier}; export TRAVAIL=$W
cd $U
MAXF=20000 timeout 1500 nice -n 19 python3 diag.py 30 --nobuild 2>&1 | tail -1
I="1500-1508::IN2:Coin 1;1600-1608::IN2:Coin 2;2000-2006::IN2:1 Player Start;3500-19900%200,6::IN0:P1 Button 1"
INPUTS="$I" MAXF=20000 timeout 1500 nice -n 19 python3 diag.py 30 --nobuild 2>&1 | tail -1
I="1500-1508::IN2:Coin 1;1600-1608::IN2:Coin 2;1700-1706::IN2:1 Player Start;3600-60000::IN0:P1 Right;1900-60000%12,4::IN0:P1 Button 1;2000-60000%3000,6::IN2:1 Player Start"
INPUTS="$I" MAXF=60000 timeout 3500 nice -n 19 python3 diag.py 30 --nobuild 2>&1 | grep -a "aucune\|EXCEPTION"
cd $W
T=$(mktemp -d -p $W cmd_XXXX)
BANC_DIR=$W/ OUT=$T/cmd.txt timeout -s KILL 1200 nice -n 19 mame sfa3ud -rompath $W/roms_tr -video none -sound none -nothrottle \
  -skip_gameinfo -nvram_directory $T/nv -cfg_directory $T/cfg -autoboot_script ${HSFA_WORKSPACE}/work/mame/commandes.lua >/dev/null 2>&1
python3 $U/commandes.py ${HSFA_WORKSPACE}/work/mame/cmd_ref.txt $T/cmd.txt | tail -3
cp $T/cmd.txt $W/cmd_tr.txt; rm -rf $T
