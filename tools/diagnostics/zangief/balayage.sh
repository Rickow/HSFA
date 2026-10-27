#!/bin/bash
# agent_zangief : chaque decor d'Upper force (STG), capture a 100 images de combat, ROM de plans partagee (avant) et copie VIDE15 (apres)
A=${HSFA_WORKSPACE}/work/agent_zangief
un() { s=$1; v=$2; P=$A/hsfa_plans_vide15.bin; [ $v = avant ] && P=${HSFA_WORKSPACE}/work/mame_ro5/hsfa_plans.bin
  PLANS=$P STG=$s NF=3500 DUMPAT=100 TAG=c_${v}_$s $A/lance.sh >/dev/null 2>&1; }
export -f un; export A
for s in $(seq 0 2 74); do h=$(printf %02x $s); echo "$h avant"; echo "$h apres"; done | xargs -P 6 -n 2 bash -c 'un $0 $1'
