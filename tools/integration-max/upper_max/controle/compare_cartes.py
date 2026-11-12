#!/usr/bin/env python3
"""compare deux carte_image.txt (va MIPS -> adresse d'image) : zones où le décalage change.
Usage : compare_cartes.py carte_A carte_B  -> une ligne par changement de décalage (image A, image B, va, delta)."""
import sys
def lit(p):
    d = {}; o = []
    for l in open(p, encoding="utf-8"):
        c = l.split()
        if len(c) < 2: continue
        try: i, v = int(c[0], 16), int(c[1], 16)
        except ValueError: continue
        if v not in d: d[v] = i; o.append(v)
    return d, o
A, oa = lit(sys.argv[1]); B, ob = lit(sys.argv[2])
print("# va communes %d ; seulement A %d ; seulement B %d" % (len(set(A) & set(B)), len(set(A) - set(B)), len(set(B) - set(A))))
prec = 0; n = 0
for v in oa:
    if v not in B: continue
    d = B[v] - A[v]
    if d != prec:
        print("image A $%06X -> B $%06X  va 0x%06X  delta %+d (pas %+d)" % (A[v], B[v], v, d, d - prec)); prec = d; n += 1
print("# %d changements de décalage ; décalage final %+d ; dernière adresse A $%X B $%X" % (n, prec, max(A.values()), max(B.values())))
