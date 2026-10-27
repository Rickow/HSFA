#!/bin/bash
# (HANDOFF §110) NON-REGRESSION de la traduction SFA3 (ro3), apres reconstruction (mame_test.py) :
#  1) 20 000 images sans entree, 2) 20 000 images avec piece / Start / bouton, 3) 60 000 images de partie offensive,
#  4) test des commandes arcade <-> traduction (reference : work/mame/cmd_ref.txt, REF=1 commandes.lua).
# Attendu : « aucune exception » x3, « 42 actions, 0 differentes », 5359 tours en 4019 images (133,3 %).
S=$(dirname "$(readlink -f "$0")"); H=${HSFA_WORKSPACE:?"HSFA_WORKSPACE non defini (voir config.example.env)"}; U=${HSFA_SRC:-$S/../../src/hsfa}; W=$H/work/mame
cd $U
MAXF=20000 timeout 1500 nice -n 19 python3 diag.py 30 --nobuild 2>&1 | tail -1
I="1500-1508::IN2:Coin 1;1600-1608::IN2:Coin 2;2000-2006::IN2:1 Player Start;3500-19900%200,6::IN0:P1 Button 1"
INPUTS="$I" MAXF=20000 timeout 1500 nice -n 19 python3 diag.py 30 --nobuild 2>&1 | tail -1
I="1500-1508::IN2:Coin 1;1600-1608::IN2:Coin 2;1700-1706::IN2:1 Player Start;3600-60000::IN0:P1 Right;1900-60000%12,4::IN0:P1 Button 1;2000-60000%3000,6::IN2:1 Player Start"
INPUTS="$I" MAXF=60000 timeout 3500 nice -n 19 python3 diag.py 30 --nobuild 2>&1 | grep -a "aucune\|EXCEPTION"
cd $W
T=$(mktemp)
OUT=$T timeout -s KILL 1200 nice -n 19 mame sfa3ud -rompath roms_tr -video none -sound none -nothrottle -skip_gameinfo -autoboot_script commandes.lua >/dev/null 2>&1
python3 $U/commandes.py $W/cmd_ref.txt $T | tail -3
rm -f $T
