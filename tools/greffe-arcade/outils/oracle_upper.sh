#!/bin/bash
# (etape 3) Partie ORACLE dans Upper (fige/ro5) : meme variante de liste d'adversaires que oracle_ro9a.sh ($120 = $32,
# $123 = $82 imposes a l'entree de 0x24F9D0). Usage : oracle_upper.sh TRACE NF ["VARS en plus" : PERSO=hh, PERDRE=1,
# CONTINUE=1, SNAPETAT=1...]
G=${HSFA_WORKSPACE}/work/greffe_arcade
PC=$(awk '{v=strtonum("0x"$2); if (v>=0x24f9d0 && v<0x24fbd0) {print $1; exit}}' $G/fige/ro5/carte_image.txt)
TMAX=${TMAX:-3000} $G/outils/lance_upper_lua.sh $1 "LUA_BASE=$G/lua/tournee_greffe.lua GRAINE_PC=$PC GRAINE_OUT=$G/traces/$1.graine FORCE_ADR=ff8120=32,ff8123=82 $3" $2 $G/lua/graine_pc.lua
grep -E "COMBAT|EXC|^FIN" $G/traces/$1/journal.txt | head -40
