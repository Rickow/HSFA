#!/bin/bash
# (31/10, e23) distributeur : lance chaque combinaison quand moins de MAX MAME tournent (oracle_ro9a, comme balayage_liste)
G=${HSFA_WORKSPACE}/work/greffe_arcade; C=$1; PF=$2; L=$3; MAX=${MAX:-10}
while read p v; do
  while [ $(ps -u "$(id -un)" -o args | grep "^${HSFA_WORKSPACE}/mame-fork/mame/cps2f" | wc -l) -ge $MAX ]; do sleep 20; done
  (TMAX=${TM:-6000} $G/outils/oracle_ro9a.sh $C ${PF}_${p}_${v} ${NF:-45000} "PERSO=$p.$v SCENEA_PASSIF=1 BLOCAGE=20000 ARRET_FIN=1" > /dev/null 2>&1 &)
  sleep 15
done < $L
echo DISTRIBUE
