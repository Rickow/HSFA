#!/usr/bin/env python3
"""pourquoi.py VA... : chaine des parents (plan de l'etape 3, force3) qui fait greffer chaque routine d'Upper VA"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import greffe3 as G3
PL = G3.PL; import force3 as FO
rac = [0x4E1C0, 0x24EA30, 0x261560, 0x2614A0, 0x2614D0, 0x261500, 0x1346A0] + list(G3.KO_ARCADE) + [0x269340, 0x26E900]
TC = PL.tables_a_completer()
P = PL.ferme(rac + sorted({u for _, u, _, _, _ in TC}), FO.force())
print(PL.resume(P).splitlines()[0])
for a in sys.argv[1:]:
    x = int(a, 16); ch = []
    while x in P.parent and len(ch) < 30:
        p, how = P.parent[x]; ch.append('0x%X <-(%s) 0x%X [%s]' % (x, how, p, P.dec.get(p, ('?',))[0])); x = p
    print('\n'.join(ch) or '%s : racine ou non atteinte' % a); print()
