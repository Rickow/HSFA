#!/usr/bin/env python3
"""forme40.py -- max-tables tracer, net 4 (by the SHAPE of the data): tables read by the code of the graft build
(copies and Hyper) missing from TABLES.tsv whose shape is that of a per-character table: (a) header of u16 offsets
starting at $50 (40 entries) or $100 (128); (b) gap to the next constant = 40 x e or 48 x e (e = 1, 2, 4, 8).

Usage:  nice -n 19 python3 -I forme40.py [frozen_build] > sorties/forme40.txt
Inputs: frozen build (argument or $HSFA_GRAFT_BUILD), $HSFA_REVIEW_OUT/TABLES.tsv (maitre.py). See paths.py.
"""
import sys, os, struct, bisect, collections, csv
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import lib_idx as L
X = L.charge(sys.argv[1] if len(sys.argv) > 1 else None, upper=False); A9 = X.A9; BASE = L.BASE
connues = set()
for r in list(csv.reader(open(paths.sorties('TABLES.tsv'), encoding='utf-8'), delimiter='\t'))[1:]:
    if r[0].startswith('T_'): connues.add(int(r[0][2:], 16))
def lit(a, n):
    u = X.vers_upper(a)
    if u is not None: return X.b5[u - BASE:u - BASE + n]
    return X.b9[a - BASE:a - BASE + n]
acc = collections.defaultdict(list)
for a in A9.acc: acc[a[1]].append(a)
Cs = sorted(A9.consts | set(X.reut.values()))
def ecart(c):
    k = bisect.bisect_right(Cs, c); return Cs[k] - c if k < len(Cs) else 0
def pres(c):
    return any(abs(c - k) < 0x10 for k in connues)
for c in sorted(set(acc) | set(A9.csite)):
    if c in connues: continue
    d = lit(c, 0x100)
    if len(d) < 0x100: continue
    w = struct.unpack('<128H', d)
    genre = None
    if w[0] == 0x50 and all(0x50 <= x < 0x8000 or x == 0 for x in w[:40]) and len(set(w[:40])) > 4: genre = 'rel16 x40'
    elif w[0] == 0x100 and all(0x100 <= x < 0x8000 or x == 0 for x in w[:128]) and len(set(w[:128])) > 4: genre = 'rel16 x128'
    else:
        ec = ecart(c); szs = {a[3] for a in acc.get(c, ())}
        for e in sorted(szs):
            if ec in (40 * e, 48 * e) and e in (1, 2, 4): genre = 'ecart %d x %d' % (ec // e, e)
        if ec in (0x140, 0x180) and not genre and acc.get(c): genre = 'ecart %d x 8' % (ec // 8)
    if not genre: continue
    cotes = collections.Counter(X.cote(o) for o in set(A9.csite.get(c, ())) | {a[0] for a in acc.get(c, ())})
    u = X.vers_upper(c)
    print("T_%06x%s %s lecteurs %s%s" % (c, (' (U %06x)' % u) if u else '', genre, dict(cotes), ' PRES' if pres(c) else ''))
    for a in acc.get(c, ())[:4]:
        og = X.origine(a[0])
        print("    %s %06x %s+%x [%s] %s | %s" % (X.cote(a[0]), a[0], '.bwl'[a[3]] if a[3] < 3 else 'l', a[2], L.signature(a[4])[0][:80], ('<-U %x' % og) if og else '', X.t68(a[0])[:50]))
