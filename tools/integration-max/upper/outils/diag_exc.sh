#!/bin/bash
# (agent_integration_max) diagnostic d'une exception : diag_exc.sh BANC SORTIE IMAGE [variables de tournee dans l'env]
# état sauvé à IMAGE-2 (SAVEAT), puis trace de 3 images ; affiche les 50 instructions avant l'entrée en $A0x
I=${HSFA_WORKSPACE}/work/agent_integration_max; B=$1; O=$2; F=$3
cd $I
NF=$((F)) SAVEAT=$((F-${K:-6})) SAVENAME=d$F GARDE=1 ./lance_max.sh $B $O > /dev/null
GARDE=1 LUA=$I/lua/trace_etat.lua ETAT=d$F TRACE=$I/$O.trace NTR=$((${K:-6}+1)) EXTRA="-debug -debugger none" ./lance_max.sh $B $O > /dev/null
n=$(grep -n -m1 "^000A0" $O.trace | cut -d: -f1)
if [ -z "$n" ]; then echo "pas d'exception dans la trace"; head -3 $O.trace; else sed -n "$((n>50?n-50:1)),${n}p" $O.trace; fi
