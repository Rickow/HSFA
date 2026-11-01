#!/bin/bash
# (e26) Partie oracle Upper (fige/ro5, comme outils/oracle_upper.sh) avec releve des plans lua/rec_plans.lua.
# Usage : rec_upper.sh TRACE NF "VARS" (REC_IMAGES=..., SNAPS=..., PERSO=...)
G=${HSFA_WORKSPACE}/work/greffe_arcade
PC=$(awk '{v=strtonum("0x"$2); if (v>=0x24f9d0 && v<0x24fbd0) {print $1; exit}}' $G/fige/ro5/carte_image.txt)
TMAX=${TMAX:-3000} $G/outils/lance_upper_lua.sh $1 "LUA_BASE=$G/lua/tournee_greffe.lua GRAINE_PC=$PC GRAINE_OUT=$G/traces/$1.graine FORCE_ADR=ff8120=32,ff8123=82 REC=$G/traces/$1.rec $3" $2 $G/lua/rec_plans.lua
grep -E "COMBAT|EXC|^FIN" $G/traces/$1/journal.txt | head -5
