#!/bin/bash
# (e25) Defi dans Upper (oracle) : NOM NF "VARS en plus" (ex. "DEFI_IMG=1000 PERDRE_ETAPE=0 PERDRE_J2=01 DEFI_J2_ATTAQUE=1")
# SURVC=adr:long:image -> e25/NOM_surv.txt (lua/surv_chg.lua)
G=${HSFA_WORKSPACE}/work/greffe_arcade
PC=$(awk '{v=strtonum("0x"$2); if (v>=0x24f9d0 && v<0x24fbd0) {print $1; exit}}' $G/fige/ro5/carte_image.txt)
V="LUA_BASE_D=$G/lua/graine_pc.lua LUA_BASE=$G/lua/tournee_greffe.lua GRAINE_PC=$PC GRAINE_OUT=$G/traces/$1.graine FORCE_ADR=ff8120=32,ff8123=82 DEFI_OUT=$G/e25/$1.txt SNAPETAT=1 PERSO=00"
if [ -n "$SURVC" ]; then
  TMAX=${TMAX:-3000} $G/outils/lance_upper_lua.sh $1 "$V LUA_BASE_S=$G/lua/defi.lua SURVC=$SURVC SURVC_OUT=$G/e25/$1_surv.txt $3" $2 $G/lua/surv_chg.lua
else
  TMAX=${TMAX:-3000} $G/outils/lance_upper_lua.sh $1 "$V $3" $2 $G/lua/defi.lua
fi
