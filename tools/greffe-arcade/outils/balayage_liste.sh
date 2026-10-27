#!/bin/bash
# (etape 6) Balayage des fins sur une LISTE de combinaisons (defaut donnees/combinaisons_selectionnables.txt : 85).
# Usage : balayage_liste.sh CONSTRUCTION PREFIXE [fichier] (P=3)
G=${HSFA_WORKSPACE}/work/greffe_arcade; C=$1; PF=$2; L=${3:-$G/donnees/combinaisons_selectionnables.txt}
run() { set -- $1; TMAX=6000 $G/outils/oracle_ro9a.sh $C ${PF}_$1_$2 45000 "PERSO=$1.$2 SCENEA_PASSIF=1 BLOCAGE=20000 ARRET_FIN=1" > /dev/null 2>&1; }
export -f run; export G C PF
cat $L | xargs -P ${P:-3} -I{} bash -c 'run "{}"'
