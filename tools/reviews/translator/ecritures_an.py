#!/usr/bin/env python3
"""ecritures_an.py roN -- MIPS writes of an A0-A6 slot with no map entry at that address nor at the 2 neighbouring
instructions, outside the MOVEA.W correction (An += RAM base after bgez) and outside prologues. List by site.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, struct, collections, bisect
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
import carte
from mips import decode
mod=sys.argv[1]
buf=paths.module(mod)
E=carte.lit(mod); vs=sorted({v for a,v,t in E}); last=vs[-1]
end=struct.unpack_from('<I',buf,12)[0]; c0=0x22de0 if end==0x3bf140 else 0x22b00
L=list(decode(buf,c0,min(end,last+4))); l7=set(); out=[]; tot=0
for i,x in enumerate(L):
    if x.m=='lui': (l7.add if x.imm==0x7000 else l7.discard)(x.rt); continue
    d=None
    if x.m in ('lw','lh','lhu','lb','lbu','addiu','andi','ori','xori','slti','sltiu'): d=x.rt
    elif x.op==0 and x.m not in ('jr','jalr','mult','multu','div','divu'): d=x.rd
    if x.m in ('sw','sh','sb') and x.rs in l7 and 0x1100<=x.imm<0x111c:
        tot+=1
        k=bisect.bisect_left(vs,x.va-8)
        if not (k<len(vs) and vs[k]<=x.va+28):
            # correction MOVEA.W : addu avec lui RAM juste avant
            prev=[y.m for y in L[max(0,i-6):i]]
            fix=any(y.m=='addu' for y in L[max(0,i-4):i]) and any(y.m=='lui' and y.imm!=0x7000 for y in L[max(0,i-5):i]) and any(y.m in('bgez','bltz') for y in L[max(0,i-9):i])
            if not fix: out.append(x)
    if d is not None: l7.discard(d)
print("%s : %d ecritures de A0-A6, %d sans entree proche"%(mod,tot,len(out)))
for x in out: print("   0x%x A%d %s"%(x.va,(x.imm-0x1100)//4,x.m))
