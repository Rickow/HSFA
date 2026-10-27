#!/usr/bin/env python3
"""tri_tables.py CONSTRUCTION : routines renvoyees a HYPER par le tri (regle d) ou f/g) qui contiennent une table de
pointeurs de code (aiguilleur) : liste, avec la table d'Upper et les cibles."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'etape2'))
import plan as PL
c = sys.argv[1]
J = json.load(open(os.path.join(PL.G, 'constructions', c, 'greffe.json')))
for k, d in sorted(J['decisions'].items(), key=lambda x: int(x[0], 16)):
    f = int(k, 16)
    if d[0] != 'HYPER' or not d[-1].startswith(('d)', 'g)', 'f) service')) or f not in PL.E5: continue
    T = [(v, PL.ptrs_code(v)) for kk, t, v in PL.consts(PL.ins(PL.b5, f, PL.E5[f])) if t == 'c' and PL.GR.classe_valeur(v, PL.GR.H5) == 'data']
    T = [(v, p) for v, p in T if p]
    if T: print('0x%X -> %s (%s) : %s' % (f, d[1], d[-1], ' ; '.join('T_%X[%d]' % (v, len(p)) for v, p in T)))
