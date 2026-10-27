#!/usr/bin/env python3
"""agent_zangief : copie de work/mame_ro5/hsfa_plans.bin ou les tuiles 32x32 VIDES du conteneur e525 (entree 0 de la table
= « toute a 15, transparent brut ») sont rangees en pen 15 (transparent) au lieu de zeros (pen 0 opaque).
Equivalent a `HSFA_PLANS_VIDE15=1 MODULE=ro5 hsfa_plans.py` (scroll3 seul ; scroll1/2 inchanges), sans toucher aux fichiers partages.
Usage : MODULE=ro5 <workspace>/venv/bin/python3 plans_vide15.py <entree> <sortie>"""
import sys, numpy as np
sys.path.insert(0, "<workspace>/scripts/untranspile")
import banques, anthgfx
from hsfa_gfx import encode
src, dst = sys.argv[1], sys.argv[2]
blob = bytearray(open(src, "rb").read())
OFF3 = 0x0A00000
t15 = np.full((32, 32), 15, np.uint8)
s = anthgfx.to_slots(2, t15).astype(np.uint8).reshape(4, 16, 16)
tuile = b"".join(encode(s[q]) for q in range(4))
n = 0; fin = 0
for k, m, p in anthgfx.tiles(banques.fichier(banques.MOD['b32'])):
    if k != 2 or p is not None: continue
    o = OFF3 + 512 * m
    if o + 512 > len(blob): blob.extend(bytes(o + 512 - len(blob)))
    blob[o:o+512] = tuile; n += 1; fin = max(fin, m)
open(dst, "wb").write(bytes(blob))
print("%d tuiles 32x32 vides -> pen 15 (codes 0 ... %d) ; %s (%d o)" % (n, fin, dst, len(blob)))
