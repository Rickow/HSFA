#!/usr/bin/env python3
"""mults.py roN -- each mult/multu/div/divu (and the mfhi/mflo that follow) of the translated zone: form (3 operands:
rd != 0), what the map emits at that address and in the next 12 instructions (MULS/MULU/DIVS/DIVU or nothing), and
whether the function is native C. Review angle 5.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, struct, collections
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
from mips import Ins, CODE0
import carte
mod=sys.argv[1]
buf=paths.module(mod)
CODE1=struct.unpack_from('<I',buf,12)[0]
E=carte.lit(mod); C=collections.defaultdict(list)
for a,v,t in E: C[v].append((a,t))
L=[Ins(a,struct.unpack_from('<I',buf,a)[0]) for a in range(CODE0,CODE1,4)]
for k,x in enumerate(L):
    if x.m not in ('mult','multu','div','divu'): continue
    rd=(x.w>>11)&31
    # contexte recompile ? (case 0x7000 dans les 30 instructions avant)
    rec=sum(1 for y in L[max(0,k-30):k+30] if y.m=='lui' and y.imm==0x7000)
    em=[]
    for y in L[k:k+14]:
        for a,t in C.get(y.va,[]): em.append("%06x %s"%(a,t[:48]))
    mf=[y.m for y in L[k+1:k+8] if y.m in ('mfhi','mflo')]
    print("%07x %-5s rd=%-2d %s %s | %s"%(x.va,x.m,rd,'recompile' if rec>=6 else 'C        ',','.join(mf) or '-',' || '.join(em[:3]) if em else 'RIEN'))
