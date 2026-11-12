#!/usr/bin/env python3
"""fragments_c.py roN APPELS_C_FILE -- for each native C function NOT listed in hooks_fork (so not replaced by the
RTS stub) and called by 'jal' from recompiled code (saved output of appels_c.py): what the image REALLY executes at
the target's label = the fragments emitted by the translator from the function's address, up to the first RTS / JMP
(linear reading of the map, 30 lines at most). "HORS FONCTION": the first emitted line is beyond the end of the C
function (the call falls into the next function). Review E2.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, re, struct, bisect
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
from mips import Ins
import carte
mod=sys.argv[1]
buf=paths.module(mod)
E=carte.lit(mod); V=[e[1] for e in E]
T={}; ok=False
if len(sys.argv)<3: sys.exit(__doc__)
for l in open(sys.argv[2],encoding='utf-8',errors='replace'):
    if l.startswith('---'): ok='C-NON-LISTEE / appelant recompile' in l; continue
    m=re.match(r'\s+site ([0-9a-f]+) -> ([0-9a-f]+) \(n=(\d+)',l)
    if m and ok: T.setdefault(int(m.group(2),16),[int(m.group(3)),[]])[1].append(int(m.group(1),16))
for t,(n,sites) in sorted(T.items()):
    fin=t+4*n; k=bisect.bisect_left(V,t)
    jeu=[s for s in sites]
    print("== %s cible %06x (%d instr., fin %06x), %d sites : %s"%(mod,t,n,fin,len(sites),' '.join('%x'%s for s in sites[:8])))
    if k>=len(E): print("   rien d'emis apres"); continue
    if E[k][1]>=fin: print("   HORS FONCTION : 1re ligne emise a mips %07x (image %06x)"%(E[k][1],E[k][0]))
    for j in range(k,min(len(E),k+30)):
        a,v,tx=E[j]; h=carte.tete(tx)
        print("   %06x %07x%s %s"%(a,v,' ' if v<fin else '*',tx[:100]))
        if h.startswith(('RTS','JMP')) and 'T_' not in h: break
