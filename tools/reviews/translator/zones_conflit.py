#!/usr/bin/env python3
"""zones_conflit.py roN -- for each borrowed zone (extra_regs.plan): is the REAL borrowed register read or written by
the MIPS in [start, end] (conflict), is there a call or a jr in the zone, do two zones of the same register overlap?
Review angle 7 (borrowed zones).
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, struct, collections
sys.dont_write_bytecode=True
mod=sys.argv[1]; os.environ['MODULE']=mod
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
import extra_regs
from mips import Ins
buf=paths.module(mod)
I=lambda a: Ins(a, struct.unpack_from('<I',buf,a)[0])
p,_=extra_regs.plan(buf); C=collections.Counter(); Z=[]
for f,zs in p.items():
    for kind,reg,s,lo,hi in zs:
        Z.append((lo,hi,kind,reg,s)); C['zones']+=1
        real=(0x1100 if kind=='A' else 0x1124)+4*reg; l7=set(); bad=[]
        for a in range(lo,hi+4,4):
            x=I(a)
            if x.m=='lui': (l7.add if x.imm==0x7000 else l7.discard)(x.rt); continue
            if x.m in ('lw','lh','lb','lbu','lhu','sw','sh','sb') and x.rs in l7 and real<=x.imm<real+4: bad.append(a)
            if x.m in ('jal','jalr'): C['appel dans la zone']+=1; print("  appel dans la zone 0x%x-0x%x (%s%d pour %s) en 0x%x"%(lo,hi,kind,reg,'A8' if s==0x1120 else 'D8',a))
        if bad: C['vrai registre utilise dans la zone']+=1; print("  CONFLIT zone 0x%x-0x%x : %s%d prete a %s, vrai registre accede en %s"%(lo,hi,kind,reg,'A8' if s==0x1120 else 'D8',' '.join('0x%x'%b for b in bad[:6])))
Z.sort()
for i in range(len(Z)):
    for j in range(i+1,len(Z)):
        if Z[j][0]>Z[i][1]: break
        if Z[i][2:4]==Z[j][2:4]: C['chevauchement meme registre']+=1; print("  CHEVAUCHEMENT",[hex(q) if isinstance(q,int) and q>99 else q for q in Z[i]],[hex(q) if isinstance(q,int) and q>99 else q for q in Z[j]])
print(mod,dict(C))
