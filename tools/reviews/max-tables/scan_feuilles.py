#!/usr/bin/env python3
"""scan_feuilles.py -- max-tables tracer, helper: raw list of every access of the graft build whose index contains a
given leaf.

Usage:  nice -n 19 python3 -I scan_feuilles.py OFF [OFF ...]     (PS2 field offsets, hex)
Input:  frozen build ($HSFA_GRAFT_BUILD). See paths.py. Output: stdout.
"""
import sys, os, collections, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import lib_idx as L
X = L.charge(upper=False); A9 = X.A9
offs = {int(a, 16) for a in sys.argv[1:]}
T = collections.defaultdict(list)
for a in A9.acc:
    fs = L.feuilles(a[4])
    if any(f[0] in offs and f[1] == 1 for f in fs): T[a[1]].append(a)
Cs = sorted(A9.consts | set(X.reut.values()))
import bisect
for c in sorted(T):
    k = bisect.bisect_right(Cs, c); tl = Cs[k] - c if k < len(Cs) else 0
    u = X.vers_upper(c)
    print("T_%06x%s taille<=$%x" % (c, (' (copie de U %06x)' % u) if u else '', tl))
    for a in T[c]:
        og = X.origine(a[0])
        print("   %s %06x %s+%x [%s] %s | %s" % (X.cote(a[0]), a[0], '.bwl'[a[3]] if a[3] < 3 else 'l', a[2], L.signature(a[4])[0], ('<-U %06x' % og) if og is not None else '', X.t68(a[0])[:60]))
