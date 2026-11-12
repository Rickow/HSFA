#!/usr/bin/env python3
"""orig.py -- graft review: convert a FILE offset of ro9a_module.bin (copy of Upper) into the file offset of Upper
(uXXXX), or the other way round (prefix u).

Usage:  python3 -I orig.py ADR[,ADR...]     (hex; "u135430" = Upper -> copy)
Input:  greffe.json of the frozen graft build ($HSFA_GRAFT_BUILD; blocks [start_U, end_U, dest]). See paths.py.
Read only.
"""
import sys, os, json
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
g = json.load(open(os.path.join(paths.construction(), "greffe.json"), encoding="utf-8"))
B = [[int(x, 16) for x in b] for b in g['blocs']]
for s in sys.argv[1].split(','):
    if s.startswith('u'):
        a = int(s[1:], 16); r = [d + a - x for x, f, d in B if x <= a < f]
        print(s, "-> copie", ' '.join("%x" % v for v in r) or "non copie")
    else:
        a = int(s, 16); r = [x + a - d for x, f, d in B if d <= a < d + f - x]
        print(s, "-> u" + ' u'.join("%x" % v for v in r) if r else s + " : pas une copie (Hyper ou talon)")
