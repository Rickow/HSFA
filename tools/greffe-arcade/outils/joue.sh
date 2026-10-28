#!/bin/bash
# (reprise 28/10) Joue une liste de parties « CONSTRUCTION PERSO VERSION PREFIXE » en parallele (P=...), une par ligne.
# Trace : traces/<PREFIXE>_<PERSO>_<VERSION>. Usage : joue.sh fichier_liste (ou stdin)
G=${HSFA_WORKSPACE}/work/greffe_arcade
run() { set -- $1; TMAX=${TMAX:-6000} $G/outils/oracle_ro9a.sh $1 $4_$2_$3 45000 "PERSO=$2.$3 SCENEA_PASSIF=1 BLOCAGE=20000 ARRET_FIN=1 $EXTRA" > /dev/null 2>&1; }
export -f run; export G EXTRA
cat ${1:--} | xargs -P ${P:-5} -I{} bash -c 'run "{}"'
