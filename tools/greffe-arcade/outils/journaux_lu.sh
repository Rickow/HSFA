#!/bin/bash
# (etape 4) Journaux des DONNEES LUES par Upper hors des manches (lua/donnees_lues.lua) pour une liste de persos, P en
# parallele, parties gagnees jusqu'a la fin (NF=56000). Usage : journaux_lu.sh "00 01 ..." [P=2]
G=${HSFA_WORKSPACE}/work/greffe_arcade
run() { TMAX=5000 $G/outils/lance_upper_donnees.sh u_lu_$1 "PERSO=$1" ${NF:-56000} > /dev/null 2>&1; }
export -f run; export G NF
echo $1 | tr ' ' '\n' | xargs -P ${P:-2} -I{} bash -c 'run {}'
