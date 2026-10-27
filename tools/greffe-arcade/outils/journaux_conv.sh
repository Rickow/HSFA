#!/bin/bash
# (etape 3) Journaux des conversions d'Upper (lua/donnees_conv.lua) pour une liste de persos, P en parallele.
# Usage : journaux_conv.sh "01 03 05 ..." [P=2] [NF=56000]
G=${HSFA_WORKSPACE}/work/greffe_arcade
run() { TMAX=5000 $G/outils/lance_upper_lua.sh uc2_$1 "PERSO=$1 JCONV_OUT=$G/traces/uc2_$1/conv.txt" ${NF:-56000} $G/lua/donnees_conv.lua > $G/traces/uc2_$1.out 2>&1; }
export -f run; export G NF
echo $1 | tr ' ' '\n' | xargs -P ${P:-2} -I{} bash -c 'run {}'
