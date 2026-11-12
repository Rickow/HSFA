#!/usr/bin/env python3
"""a8_hors_zone.py roN -- accesses to the recompiler's A8 (0x1120) and D8 (0x1144) slots that fall in NO borrowed
zone of the plan (extra_regs.plan of the repository, imported read-only). For A8, translate.py has no fallback: such
instructions produce nothing. Grouped by function, with the neighbouring map entries.
Review finding A2 (A8 outside zone: Mazi mode damage bonus never applied); fixed by A8_ENTREE in v161 (journal §219).
Expected on a v161 build: only the C helpers of the port remain (the "A8 without register" safeguard of build.log).
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, struct, collections, bisect
sys.dont_write_bytecode=True
mod=sys.argv[1]; os.environ['MODULE']=mod
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
import extra_regs, carte
from mips import decode
buf=paths.module(mod)
p,refus=extra_regs.plan(buf)
print(mod,"zones :",sum(len(v) for v in p.values()),"refus :",dict(refus))
Z=collections.defaultdict(list)
for f,zs in p.items():
    for kind,reg,s,lo,hi in zs: Z[s].append((lo,hi))
end=struct.unpack_from('<I',buf,12)[0]; c0=0x22de0 if end==0x3bf140 else 0x22b00
l7=set(); H=collections.defaultdict(list)
for x in decode(buf,c0,end):
    if x.m=='lui': (l7.add if x.imm==0x7000 else l7.discard)(x.rt); continue
    if x.m in ('lw','lh','lb','lbu','lhu','sw','sh','sb') and x.rs in l7:
        for s in (0x1120,0x1144):
            if s<=x.imm<s+4 and not any(lo<=x.va<=hi for lo,hi in Z[s]): H[s].append(x)
E=carte.lit(mod); vs=sorted({v for a,v,t in E}); last=vs[-1]
for s in (0x1120,0x1144):
    xs=[x for x in H[s] if x.va<=last]
    print("%s hors zone : %d acces (%d ecritures)"%('A8' if s==0x1120 else 'D8',len(xs),sum(1 for x in xs if x.m[0]=='s')))
    if s==0x1120:
        g=[]; 
        for x in xs:
            if g and x.va-g[-1][-1].va<0x200: g[-1].append(x)
            else: g.append([x])
        for grp in g: print("   0x%x-0x%x : %d acces  %s"%(grp[0].va,grp[-1].va,len(grp),' '.join(y.m for y in grp[:10])))
