#!/usr/bin/env python3
"""Couverture INSTRUCTION par instruction du code d'Upper par celui d'Hyper : fenetres de K=12 instructions MIPS
(adresses masquees : cibles jal, constantes lui/addiu ; deplacements gardes), methode de carto_ro9/couverture.py.
Par routine : part des instructions couvertes. Sortie couv_k.pkl {routine_ro5: part couverte}."""
import os, sys, pickle, bisect, collections
import numpy as np
os.environ["GRAIN"] = "routine"
sys.path.insert(0, "<workspace>/work/carto_ro9")
import commun as C
from couverture import cover
import atteint as AT
OUT = os.path.dirname(os.path.abspath(__file__))
cov, va = cover('ro5', ('ro9',), False)
starts = [a for a, _ in AT.G('ro5')['funcs']]
n = collections.Counter(); k = collections.Counter()
for v, c in zip(va.tolist(), cov.tolist()):
    i = bisect.bisect_right(starts, v) - 1
    if i < 0: continue
    n[starts[i]] += 1; k[starts[i]] += c
part = {a: (k[a] / n[a] if n[a] else 1.0) for a in starts}
pickle.dump(part, open(os.path.join(OUT, "couv_k.pkl"), "wb"))
T = AT.taille('ro5'); h = collections.Counter()
for a, p in part.items(): h[min(int(p * 10), 9)] += T[a]
print("ro5 couvert par ro9 (K=12, adresses) : %.1f %% des instructions" % (100 * cov.mean()))
print("taille d'Upper par tranche de couverture :", ' '.join('%d0%%:%d' % (x, h[x]) for x in sorted(h)))
