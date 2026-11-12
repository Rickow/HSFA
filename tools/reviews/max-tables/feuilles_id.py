#!/usr/bin/env python3
"""feuilles_id.py -- max-tables tracer, step 2: fields that carry a character id. Seeds: $102 / $116 of a structure
(PS2 numbering). For each known table (Upper MAX list carried over into the graft build: copy + Hyper homologue),
leaves of the index of each access; then, the other way round, every table of the build read with one of these leaves.

Usage:  nice -n 19 python3 -I feuilles_id.py [frozen_build] > sorties/feuilles_id.txt
Inputs: frozen build (argument or $HSFA_GRAFT_BUILD), $HSFA_REVIEW_OUT/croise.pkl (croise_upper_max.py). See paths.py.
Output: stdout, and $HSFA_REVIEW_OUT/feuilles.pkl.
"""
import sys, os, collections, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import lib_idx as L
X = L.charge(sys.argv[1] if len(sys.argv) > 1 else None, upper=False); A9 = X.A9
R = pickle.load(open(paths.sorties('croise.pkl'), 'rb'))
plages = []
for t in R:
    lg = t['fin'] - t['u']
    for b in (t['copie'], t['reut'] or t['hom']):
        if b: plages.append((b, b + lg, t['u']))
def connue(c):
    for a, b, u in plages:
        if a <= c < b: return u
    return None
F = collections.defaultdict(lambda: collections.defaultdict(set))
for a in A9.acc:
    u = connue(a[1])
    for f in L.feuilles(a[4]): F[f]['connue' if u else 'autre'].add(a[1])
print("# feuille (decalage PS2, taille, registre de base) : nb de tables connues par id / autres tables")
for f, d in sorted(F.items(), key=lambda kv: -len(kv[1]['connue'])):
    if d['connue']: print("$%x.%s(%s)\t%d\t%d\t%s" % (f[0], 'bwl'[f[1] >> 1], f[2], len(d['connue']), len(d['autre']), ' '.join('%x' % c for c in sorted(d['autre'])[:12])))
pickle.dump({f: {k: sorted(v) for k, v in d.items()} for f, d in F.items()}, open(paths.sorties('feuilles.pkl'), 'wb'))
