#!/bin/bash
# (banc_coups) REPRODUCTIBILITE d'un essai : determinisme.sh <n> <module> <plan> <id> [VAR=val ...]
# Lance n fois le meme plan (sequentiellement, 1 MAME), puis compare les journaux de l'essai <id> image par image
# (tous les champs F, sauf le compteur absolu de tours) et la ligne SAVE. Sorties : essais/determinisme/<id>_<k>/.
cd "$(dirname "$(readlink -f "$0")")"; N=$1; MOD=$2; PLAN=$(readlink -f "$3"); ID=$4; shift 4
D=essais/determinisme; mkdir -p $D
for k in $(seq 1 $N); do
  mkdir -p $D/${ID}_$k
  ./lance.sh $D/${ID}_$k $MOD lua/banc_coups.lua PLAN=$PLAN "$@" > /dev/null
  echo "$k : $(grep -m1 SAVE $D/${ID}_$k/log.txt) | $(awk -v id=$ID '$1=="F" && $2==id {print $4}' $D/${ID}_$k/log.txt | md5sum | cut -c1-8) | 1re image hors neutre : $(awk -v id=$ID '$1=="F" && $2==id && $3>=8 && $4!="02000002" {print $3, $4; exit}' $D/${ID}_$k/log.txt)"
done
python3 - "$D" "$ID" "$N" <<'PY'
import sys
d, i, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
def lit(k):
    L = {}
    for l in open('%s/%s_%d/log.txt' % (d, i, k)):
        t = l.split()
        if t and t[0] == 'F' and t[1] == i:
            L[int(t[2])] = t[3:14] + t[15:]
    return L
A = lit(1)
for k in range(2, n + 1):
    B = lit(k)
    r = next((r for r in sorted(A) if A.get(r) != B.get(r)), None)
    print('lancement %d contre 1 : %s' % (k, 'IDENTIQUE' if r is None else 'diffère dès l\'image %d : %s / %s' % (r, ' '.join(A.get(r, [])[:2]), ' '.join(B.get(r, [])[:2]))))
PY
