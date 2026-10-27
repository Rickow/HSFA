#!/usr/bin/env python3
"""table_noms.py mod debut fin : toutes les chaines (>=2 car., terminees par 0) de [debut,fin), avec leur decalage
fichier -> permet de voir la table de noms complete (les noms de 3 lettres RYU/KEN/GUY/DAN echappent a 'strings')."""
import sys, re
sys.path.insert(0, '.')
import commun as C
m, a, b = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16)
d = C.load(m)
out = []
for mo in re.finditer(rb'[\x20-\x7e]{2,}(?=\x00)', d[a:b]):
    out.append('%x:%s' % (a + mo.start(), mo.group().decode()))
print(' | '.join(out))
