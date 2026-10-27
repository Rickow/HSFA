#!/usr/bin/env python3
"""table.py MOD EXEC N : N longs a l'adresse d'execution EXEC (fichier + 0x1F0000), avec la routine visee et son partenaire."""
import os, sys, struct, pickle, bisect
os.environ.setdefault("GRAIN", "routine")
sys.path.insert(0, "<workspace>/work/carto_ro9")
import commun as C
INV = pickle.load(open("<workspace>/work/etude_upper_hyper/inverse_ro5.pkl", "rb"))
mod, t, n = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3])
b = C.load(mod)
for i, v in enumerate(struct.unpack_from('<%dI' % n, b, t - 0x1F0000)):
    f = v - 0x1F0000; extra = ''
    if mod == 'ro5' and f in INV:
        r = INV[f]; extra = '%s -> %s' % (r['classe'], hex(r['partenaire']) if r['partenaire'] else '-')
    print("%2d %08x %s %s" % (i, v, hex(f) if 0 < f < len(b) else '', extra))
