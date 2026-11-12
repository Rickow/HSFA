#!/usr/bin/env python3
"""decision.py -- graft review: the graft's decision (grafted block, or last decision GREFFE / HYPER / ... before it)
for the Upper routine that contains a site.

Usage:  python3 -I decision.py SITE [SITE...]     (file offsets of Upper's module ro5, hex)
Input:  greffe.json of the frozen graft build ($HSFA_GRAFT_BUILD). Read only. See paths.py.
"""
import sys, os, json, bisect
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
J = json.load(open(os.path.join(paths.construction(), "greffe.json"), encoding="utf-8"))
D = {int(k, 16): v for k, v in J['decisions'].items()}; K = sorted(D)
BL = sorted((int(a, 16), int(b, 16), int(c, 16)) for a, b, c in J['blocs'])
for s in sys.argv[1:]:
    a = int(s, 16); k = bisect.bisect_right(K, a) - 1
    g = [(x, y, c) for x, y, c in BL if x <= a < y]
    if g: print("%x : GREFFEE (bloc Upper %x-%x -> copie fichier %x, site copie %x)" % (a, g[0][0], g[0][1], g[0][2], g[0][2] + a - g[0][0]))
    else: print("%x : NON greffee (derniere decision avant : %x %s)" % (a, K[k], D[K[k]]))
