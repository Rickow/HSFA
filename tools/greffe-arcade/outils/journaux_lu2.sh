#!/bin/bash
# (etape 4) Journaux des DONNEES LUES par Upper jusqu'a la FIN (lua/donnees_lues2.lua : tournee_arcade.lua, SCENEA_PASSIF)
# pour une liste de persos, P en parallele. Sorties traces/u_lu2_XX/lu.txt (prises par greffe3 : glob u_lu*).
# Usage : journaux_lu2.sh "00 01 ..." [P=3] [NF=34000]
G=${HSFA_WORKSPACE}/work/greffe_arcade
run() { TMAX=6000 $G/outils/lance_upper_donnees2.sh u_lu2_$1 "PERSO=$1${VER:-.Z3} SCENEA_PASSIF=1 BLOCAGE=20000" ${NF:-34000} > /dev/null 2>&1; }
export -f run; export G NF
echo $1 | tr ' ' '\n' | xargs -P ${P:-3} -I{} bash -c 'run {}'
