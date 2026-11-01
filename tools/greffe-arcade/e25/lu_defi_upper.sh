#!/bin/bash
# (e25) journal des donnees lues par Upper pendant le defi : NOM NF "VARS" -> traces/NOM/lu.txt (prise par greffe3 si NOM = u_lu*)
G=${HSFA_WORKSPACE}/work/greffe_arcade
PC=$(awk '{v=strtonum("0x"$2); if (v>=0x24f9d0 && v<0x24fbd0) {print $1; exit}}' $G/fige/ro5/carte_image.txt)
TMAX=${TMAX:-6000} $G/outils/lance_upper_lua.sh $1 "LUA_BASE_L=$G/lua/defi.lua LUA_BASE_D=$G/lua/graine_pc.lua LUA_BASE=$G/lua/tournee_greffe.lua GRAINE_PC=$PC GRAINE_OUT=$G/traces/$1.graine FORCE_ADR=ff8120=32,ff8123=82 DEFI_OUT=$G/e25/$1.txt PERSO=00 DLOG=$G/traces/$1/lu.txt DLOG_F0=2600 $3" $2 $G/lua/donnees_lues3.lua
