#!/bin/bash
# (etape 6) PILE AU PLANTAGE d'une fin : relit EXCEPTION <image> pc=.. dans traces/<PREFIXE>_<perso>_<v>/journal.txt,
# rejoue la partie avec sonde_pile.lua a l'entree de la routine fautive (2 images avant), decode la pile (ou.py).
# Usage : pile_plantage.sh CONSTRUCTION PREFIXE PERSO [VERSION=Z3]
G=${HSFA_WORKSPACE}/work/greffe_arcade; C=$1; PF=$2; p=$3; v=${4:-Z3}; cd $G
J=traces/${PF}_${p}_${v}/journal.txt
F=$(grep -o "EXCEPTION [0-9]*" $J | awk '{print $2}'); PC=$(grep -o "EXCEPTION.*" $J | awk '{print $NF}')
R=$(python3 etape2/ou.py $C ${PC:2} | tail -1 | grep -o "routine 0x[0-9A-F]*" | awk '{print $2}')
E68=$(python3 - "$C" "$R" <<'P'
import sys
c, r = sys.argv[1], int(sys.argv[2], 16)
best = None
for l in open('${HSFA_WORKSPACE}/work/greffe_arcade/constructions/%s/b9/carte_image.txt' % c):
    x = l.split(None, 2)
    if len(x) < 2: continue
    m = int(x[1], 16)
    if r <= m < r + 0x100 and (best is None or m < best[0]): best = (m, x[0])
print(best[1] if best else '')
P
)
SCRIPT_LUA=$G/lua/sonde_pile.lua TMAX=5000 outils/oracle_ro9a.sh $C pp_${p}_${v} $((F + 1)) "PERSO=$p.$v SCENEA_PASSIF=1 BLOCAGE=20000 LUA_BASE=$G/lua/graine_pc.lua LUA_BASE_G=$G/lua/tournee_arcade.lua SONDE_PC=$E68 SONDE_F0=$((F - 1)) SONDE_N=200 SONDE_OUT=$G/traces/pp_${p}_${v}.txt" > /dev/null 2>&1
echo "== $p.$v plantage $F pc $PC routine $R (entree 68K $E68)"
L=$(tail -1 traces/pp_${p}_${v}.txt); echo "$L" | cut -c1-120
for x in $(echo "$L" | sed 's/.*pile //' | awk '{for(i=1;i<=13;i+=2) printf "%s%s ", $i, $(i+1)}'); do python3 etape2/ou.py $C ${x:2} 2>/dev/null | tail -1 | cut -c1-150; done
