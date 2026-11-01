#!/bin/bash
# (e26) Releves un-par-decor (lua/rec_plans.lua REC_TOUS) : Upper (oracle) et ro9a, partie ARCADE de chaque perso.
# Usage : rec_lot.sh CONSTRUCTION PREFIXE "persos hexa" [NF]   (P = parallelisme, defaut 8, <= 10)
G=${HSFA_WORKSPACE}/work/greffe_arcade; C=$1; PF=$2; NF=${4:-45000}
run() { set -- $1
  if [ $1 = U ]; then TMAX=5400 $G/e26/rec_upper.sh ${PF}_u_$2 $((NF+6000)) "PERSO=$2 REC_TOUS=240 SCENEA_PASSIF=1" > /dev/null 2>&1
  else TMAX=5400 SCRIPT_LUA=$G/lua/rec_plans.lua $G/outils/oracle_ro9a.sh $C ${PF}_h_$2 $NF "PERSO=$2.Z3 REC=$G/traces/${PF}_h_$2.rec REC_TOUS=240 SCENEA_PASSIF=1 BLOCAGE=20000 ARRET_FIN=1" > /dev/null 2>&1; fi; }
export -f run; export G C PF NF
for p in $3; do [ "$COTE" != H ] && echo "U $p"; [ "$COTE" != U ] && echo "H $p"; done | xargs -P ${P:-8} -I{} bash -c 'run "{}"'
