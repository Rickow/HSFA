#!/usr/bin/env python3
"""plage.py DEBUT FIN : routines d'Upper (ro5) de la plage, classe vs Hyper, homologue vivant ?, variables A5
propres a Upper utilisees, appartenance aux sous-arbres de scene (zones_upper.pkl)."""
import sys, os, pickle
import atteint as AT
OUT = os.path.dirname(os.path.abspath(__file__))
INV = pickle.load(open(os.path.join(OUT, "inverse_ro5.pkl"), "rb"))
arc = pickle.load(open(os.path.join(OUT, "arcade_upper.pkl"), "rb")); viv9 = arc['vivant9']
Z = pickle.load(open(os.path.join(OUT, "zones_upper.pkl"), "rb"))
A = pickle.load(open(os.path.join(OUT, "a5.pkl"), "rb")); D5, D9 = A['D5'], A['D9']
seul5 = {d for d in D5 if d not in D9}
par_r = {}
for d in seul5:
    for r in D5[d]['routines']: par_r.setdefault(r, set()).add(d)
a, b = int(sys.argv[1], 16), int(sys.argv[2], 16)
for f, e in AT.G('ro5')['funcs']:
    if not (a <= f < b): continue
    r = INV[f]; p = r['partenaire']
    sc = ''.join(k.split()[1][0] for k in Z['res'] if f in Z['res'][k])
    v = ('V' if p in viv9 else 'm') if p is not None else '-'
    print("%07x %5d %-26s %s %-8s sc=%-8s %s %s" % (f, e - f, r['classe'], v, '%x' % p if p else '', sc,
          'EXCL' if f in Z['excl'] else '    ', ' '.join('$%04X' % d for d in sorted(par_r.get(f, ())))))
