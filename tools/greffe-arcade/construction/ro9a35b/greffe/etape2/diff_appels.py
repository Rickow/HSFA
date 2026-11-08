#!/usr/bin/env python3
"""diff_appels.py ta_upper.txt debuts_ro5.map ta_ro9a.txt debuts_ro9a.map [image] : sequences d'entrees de routines
(lua/trace_appels.lua), ramenees aux identifiants d'Upper, comparees image par image (difflib)."""
import sys, difflib, collections
def charge(t, m):
    M = {int(a, 16): i for a, i in (l.split() for l in open(m))}
    S = collections.defaultdict(list)
    for l in open(t):
        r, a = l.split(); S[int(r)].append(M.get(int(a, 16), '?%s' % a).rstrip('?'))
    return S
U = charge(sys.argv[1], sys.argv[2]); N = charge(sys.argv[3], sys.argv[4])
im = [int(sys.argv[5])] if len(sys.argv) > 5 else sorted(set(U) | set(N))
for k in im:
    a, b = U.get(k, []), N.get(k, [])
    print("== image %d : Upper %d entrees, ro9a %d" % (k, len(a), len(b)))
    for l in difflib.unified_diff(a, b, lineterm='', n=2):
        if l.startswith(('---', '+++')): continue
        print('   ' + l)
