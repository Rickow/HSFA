#!/bin/bash
# copie de scripts/untranspile/nonreg.sh sur MA construction (TRAVAIL=$B/mame3 ; nvram/cfg temporaires)
B=${HSFA_WORKSPACE}/work/agent_bandeau_A; U=$B/untranspile; export TRAVAIL=${TRAVAIL:-$B/mame3}; W=${HSFA_WORKSPACE}/work/mame
cd $U
MAXF=20000 timeout 1500 nice -n 19 python3 diag.py 30 --nobuild 2>&1 | tail -1
I="1500-1508::IN2:Coin 1;1600-1608::IN2:Coin 2;2000-2006::IN2:1 Player Start;3500-19900%200,6::IN0:P1 Button 1"
INPUTS="$I" MAXF=20000 timeout 1500 nice -n 19 python3 diag.py 30 --nobuild 2>&1 | tail -1
I="1500-1508::IN2:Coin 1;1600-1608::IN2:Coin 2;1700-1706::IN2:1 Player Start;3600-60000::IN0:P1 Right;1900-60000%12,4::IN0:P1 Button 1;2000-60000%3000,6::IN2:1 Player Start"
INPUTS="$I" MAXF=60000 timeout 3500 nice -n 19 python3 diag.py 30 --nobuild 2>&1 | grep -a "aucune\|EXCEPTION"
cd $W
T=$(mktemp -d -p $B)
BANC_DIR=$TRAVAIL/ OUT=$T/cmd.txt timeout -s KILL 1200 nice -n 19 mame sfa3ud -rompath $TRAVAIL/roms_tr -video none -sound none -nothrottle -skip_gameinfo \
  -nvram_directory $T/nv -cfg_directory $T/cfg -autoboot_script commandes.lua >/dev/null 2>&1
python3 $U/commandes.py $W/cmd_ref.txt $T/cmd.txt | tail -3
rm -rf $T
