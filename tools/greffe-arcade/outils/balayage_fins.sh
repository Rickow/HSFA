#!/bin/bash
# (etape 5) BALAYAGE DES FINS : 40 persos x 4 versions sur une construction (defaut ro9a5_fige), P parties en parallele,
# arret ARRET_FIN (300 images apres la sortie de la scene A). Traces traces/f5_<perso>_<version>/journal.txt.
# Usage : balayage_fins.sh [CONSTRUCTION] ["00 01 ..."] ["Z Z2 A Z3"]   (P=3)
G=${HSFA_WORKSPACE}/work/greffe_arcade; C=${1:-ro9a5_fige}
PERSOS=${2:-$(python3 -c "print(' '.join('%02x' % i for i in range(40)))")}; VERS=${3:-"Z3 Z Z2 A"}
run() { set -- $1; TMAX=6000 $G/outils/oracle_ro9a.sh $C ${PREFIXE:-f5}_$1_$2 45000 "PERSO=$1.$2 SCENEA_PASSIF=1 BLOCAGE=20000 ARRET_FIN=1" > /dev/null 2>&1; }
export -f run; export G C PREFIXE
for v in $VERS; do for p in $PERSOS; do echo "$p $v"; done; done | xargs -P ${P:-3} -I{} bash -c 'run "{}"'
