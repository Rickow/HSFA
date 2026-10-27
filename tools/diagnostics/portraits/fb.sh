#!/bin/bash
# fb.sh NOM COEUR [ZIP] : Upper (ou autre, selon le zip) dans le coeur FBNeo HSFA via hsfa_run, entrees de la tournee
# (piece, Start, bouton 1 periodiques), dossier systeme vide. Variables : NF, SNAPS, INPUTS (remplace les entrees).
A=${HSFA_WORKSPACE}/work/agent_portraits; N=$1; C=$2; Z=${3:-$A/zips/sfa3uhsfa.zip}
D=$A/runs/fb_$N; rm -rf $D; mkdir -p $D/snap $D/sys
IN=${INPUTS:-"1500-1860%60,8::IN2:Coin 1;1900-1990%40,6::IN2:1 Player Start;2000-${FINB:-2300}%24,4::IN0:P1 Button 1"}
INPUTS="$IN" OUTDIR=$D/snap SYSDIR=$D/sys OUT=$D/log.txt WAV=/dev/null NF=${NF:-3000} \
  nice -n 19 $A/outils/hsfa_run $C $Z > $D/fb.out 2>&1
echo "fini fb $N : $(ls $D/snap | wc -l) captures"
