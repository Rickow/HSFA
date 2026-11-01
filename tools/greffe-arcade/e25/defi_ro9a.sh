#!/bin/bash
# (e25) Defi dans ro9a : CONSTR NOM NF "VARS en plus" ; SURVC=adr:long:image -> e25/NOM_surv.txt (lua/surv_chg.lua)
G=${HSFA_WORKSPACE}/work/greffe_arcade
if [ -n "$SURVC" ]; then
  SCRIPT_LUA=$G/lua/surv_chg.lua TMAX=${TMAX:-3000} $G/outils/oracle_ro9a.sh $1 $2 $3 "LUA_BASE_S=$G/lua/defi.lua LUA_BASE_D=$G/lua/graine_pc.lua DEFI_OUT=$G/e25/$2.txt SURVC=$SURVC SURVC_OUT=$G/e25/$2_surv.txt $4"
else
  SCRIPT_LUA=$G/lua/defi.lua TMAX=${TMAX:-3000} $G/outils/oracle_ro9a.sh $1 $2 $3 "LUA_BASE_D=$G/lua/graine_pc.lua DEFI_OUT=$G/e25/$2.txt $4"
fi
