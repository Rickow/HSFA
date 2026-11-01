#!/bin/bash
# (28/10) couverture d'Upper (opcodes) pour les parties Arcade de tous les persos : traces/gagneXX/couv.txt
G=${HSFA_WORKSPACE}/work/greffe_arcade
run() { set -- $1; $G/outils/lance_traces.sh gagne$1 "PERSO=$1" $2 > /dev/null 2>&1; }
export -f run; export G
cat $G/outils/liste_couv.txt | xargs -P ${P:-10} -I{} bash -c 'run "{}"'
