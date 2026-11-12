#!/usr/bin/env python3
"""relectures.py roN EA[,EA...] [n] -- every re-read "MOVEA.L EA,An" of a field and the n following lines (to see
whether the re-read pointer is used by a byte access with a fixed XOR 1). Review E1.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
import carte
E=carte.lit(sys.argv[1]); n=int(sys.argv[3]) if len(sys.argv)>3 else 6
for ea in sys.argv[2].split(','):
    print('=====',ea)
    for k,(a,v,t) in enumerate(E):
        if ('MOVEA.L %s,A'%ea) in t or ('MOVE.L %s,A'%ea) in t:
            for j in range(k,min(len(E),k+n+1)): print("%s%06x %07x %s"%('>' if j==k else ' ',E[j][0],E[j][1],E[j][2][:140]))
            print('  --')
