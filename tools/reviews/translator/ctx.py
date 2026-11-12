#!/usr/bin/env python3
"""ctx.py roN ADR_IMAGE[,ADR...] [before] [after] -- lines of carte_image.txt around an image address. Read-only.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
import carte, bisect
E=carte.lit(sys.argv[1]); A=[e[0] for e in E]
for s in sys.argv[2].split(','):
    a=int(s,16); na=int(sys.argv[3]) if len(sys.argv)>3 else 10; nb=int(sys.argv[4]) if len(sys.argv)>4 else 10
    k=bisect.bisect_left(A,a)
    for j in range(max(0,k-na),min(len(E),k+nb+1)): print("%s%06x %07x %s"%('>' if E[j][0]==a else ' ',E[j][0],E[j][1],E[j][2][:150]))
    print('   --')
