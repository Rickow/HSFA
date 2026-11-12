#!/usr/bin/env python3
"""scan2.py -- max-tables tracer, step 4: tables of the graft build read with a field that carries an id (seeds +
derived fields given as arguments, form OFF or OFF:A5), classed KNOWN (Upper MAX list carried over, Hyper's index) or
NEW.

Usage:  nice -n 19 python3 -I scan2.py [OFF[:A5] ...] > sorties/scan_derives.txt
Inputs: frozen build ($HSFA_GRAFT_BUILD), $HSFA_REVIEW_OUT/croise.pkl, $HSFA_HYPER_INDEX/{scan_tables102,tables_102}.json.
See paths.py. Output: stdout.
"""
import sys, os, collections, pickle, json, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import lib_idx as L
X = L.charge(upper=False); A9 = X.A9
R = pickle.load(open(paths.sorties('croise.pkl'), 'rb'))
plages = []
for t in R:
    lg = t['fin'] - t['u']
    for b in (t['copie'], t['reut'] or t['hom']):
        if b: plages.append((b, b + lg, 'UM %06x' % t['u']))
HI = json.load(open(paths.index_hyper('scan_tables102.json'), encoding='utf-8'))
for k, v in HI.items(): plages.append((int(k, 16), int(k, 16) + max(v.get('ecart_suivante') or 1, 1), 'HI'))
for t in json.load(open(paths.index_hyper('tables_102.json'), encoding='utf-8'))['tables']:
    a = int(t['table'], 16); plages.append((a, a + t['element'] * t['entrees'], 'H102'))
def connue(c):
    return sorted({n for a, b, n in plages if a <= c < b})
want = []
for a in sys.argv[1:]:
    q = a.split(':'); want.append((int(q[0], 16), q[1] if len(q) > 1 else None))
def ok(f):
    for off, reg in want:
        if f[0] == off and f[1] == 1 and (reg is None or (f[2] == 'A5') == (reg == 'A5')) and not (reg is None and f[2] == 'A5'): return True
    return False
T = collections.defaultdict(list)
for a in A9.acc:
    if any(ok(f) for f in L.feuilles(a[4])): T[a[1]].append(a)
Cs = sorted(A9.consts | set(X.reut.values()))
for c in sorted(T):
    k = bisect.bisect_right(Cs, c); tl = Cs[k] - c if k < len(Cs) else 0
    u = X.vers_upper(c); kn = connue(c)
    print("T_%06x%s taille<=$%x %s" % (c, (' (copie de U %06x)' % u) if u else '', tl, ('CONNUE ' + ','.join(kn)) if kn else 'NOUVELLE'))
    for a in T[c]:
        og = X.origine(a[0])
        print("   %s %06x %s+%x [%s] %s | %s" % (X.cote(a[0]), a[0], '.bwl'[a[3]] if a[3] < 3 else 'l', a[2], L.signature(a[4])[0][:90], ('<-U %06x' % og) if og is not None else '', X.t68(a[0])[:60]))
