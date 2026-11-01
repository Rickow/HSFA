#!/usr/bin/env python3
"""ptrs_src.py CONSTR [lo-hi ...] : pointeurs reloges (greffe_ptrs.txt, decalages du bloc) ramenes a l'adresse PS2
d'Upper (regions de greffe.json) ; filtre optionnel sur des plages PS2."""
import json, sys
G = '<workspace>/work/greffe_arcade/constructions/'
c = sys.argv[1]; J = json.load(open(G + c + '/greffe.json'))
R = [(int(a, 16), int(b, 16), int(o, 16)) for a, b, o in J['regions']]
pl = [tuple(int(x, 16) for x in s.split('-')) for s in sys.argv[2:]]
for l in open(G + c + '/greffe_ptrs.txt'):
    o = int(l, 16); src = None
    for a, b, off in R:
        if off <= o < off + (b - a): src = a + o - off; break
    if pl and not (src is not None and any(lo <= src < hi for lo, hi in pl)): continue
    print('%x %s' % (o, '%x' % src if src is not None else '-'))
