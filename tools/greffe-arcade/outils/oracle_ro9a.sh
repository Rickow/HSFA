#!/bin/bash
# Partie ro9a « oracle » : meme variante de liste d'adversaires qu'Upper ($120 = $32, $123 = $82 imposes a l'entree de la
# copie de 0x24F9D0, cf. lua/graine_pc.lua). Usage : oracle_ro9a.sh CONSTRUCTION TRACE NF ["VARS en plus"]
G=${HSFA_WORKSPACE}/work/greffe_arcade
PC=$(python3 - "$1" <<'P'
import json,sys
J=json.load(open('${HSFA_WORKSPACE}/work/greffe_arcade/constructions/%s/greffe.json' % sys.argv[1]))
n=[int(n,16)+int('0x24f9d0',16)-int(a,16) for a,b,n in J['blocs'] if int(a,16)<=0x24f9d0<int(b,16)][0]
for l in open('${HSFA_WORKSPACE}/work/greffe_arcade/constructions/%s/b9/carte_image.txt' % sys.argv[1]):
    p=l.split(None,2)
    if n <= int(p[1],16) < n+0x200: print(p[0]); break
P
)
TMAX=${TMAX:-3000} $G/outils/lance_ro9a.sh $1 $2 "PERSO=00.Z3 SNAPETAT=1 LUA_BASE=$G/lua/tournee_arcade.lua GRAINE_PC=$PC GRAINE_OUT=$G/traces/$2.graine FORCE_ADR=ff8120=32,ff8123=82 $4" $3 ${SCRIPT_LUA:-$G/lua/graine_pc.lua}
grep -E "MANCHE|EXC|BLOQUE|^FIN" $G/traces/$2/journal.txt
