#!/usr/bin/env python3
"""ecritures_mem.py roN -- MEMORY writes of the MIPS (sb/sh/sw outside the stack and the 0x7000xxxx register bank)
with no map entry at that address nor within FEN neighbouring instructions (FEN, default 0). Audit independent of
AUDIT_MEM (translate.py).
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, struct, collections, bisect
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
import carte
from mips import decode
mod=sys.argv[1]; FEN=int(os.environ.get('FEN','0'))
buf=paths.module(mod)
E=carte.lit(mod); V=collections.defaultdict(list)
for a,v,t in E: V[v].append((a,t))
vs=sorted(V); last=vs[-1]
end=struct.unpack_from('<I',buf,12)[0]; c0=0x22de0 if end==0x3bf140 else 0x22b00
l7=set(); miss=[]; tot=0
L=list(decode(buf,c0,min(end,last+4)))
for i,x in enumerate(L):
    if x.m=='lui': (l7.add if x.imm==0x7000 else l7.discard)(x.rt); continue
    d=None
    if x.m in ('lw','lh','lhu','lb','lbu','addiu','andi','ori','xori','slti','sltiu'): d=x.rt
    elif x.op==0 and x.m not in ('jr','jalr','mult','multu','div','divu'): d=x.rd
    if x.m in ('sb','sh','sw','swl','swr') and x.rs!=29 and x.rs not in l7:
        tot+=1
        k=bisect.bisect_left(vs,x.va-4*FEN)
        if not (k<len(vs) and vs[k]<=x.va+4*FEN): miss.append(x)
    if d is not None: l7.discard(d)
print("%s : %d ecritures memoire, %d sans entree de carte (fenetre %d)"%(mod,tot,len(miss),FEN))
g=[]
for x in miss:
    if g and x.va-g[-1][-1].va<0x100: g[-1].append(x)
    else: g.append([x])
for grp in g: print("   0x%x-0x%x : %d  %s"%(grp[0].va,grp[-1].va,len(grp),' | '.join(repr(y) for y in grp[:4])))
