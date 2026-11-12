#!/usr/bin/env python3
"""appelants.py roN OFFSET... -- start of the MIPS function containing OFFSET (prologue addiu sp,-N ; sd ra), its
callers (jal), and whether each caller READS RES/C after the return before rewriting them (flags returned to the
caller). Helper for rendus.py / drapeaux.py findings.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, struct
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
from mips import Ins
mod=sys.argv[1]
buf=paths.module(mod)
e=struct.unpack_from('<I',buf,12)[0]; c0=0x22de0 if e==0x3bf140 else 0x22b00
def I(a): return Ins(a, struct.unpack_from('<I',buf,a)[0])
JAL={}
for a in range(c0,e,4):
    x=I(a)
    if x.m=='jal': JAL.setdefault(x.tgt-0x1f0000,[]).append(a)
def debut(o):
    a=o
    while a>c0:
        x=I(a)
        if x.m=='addiu' and x.rs==29 and x.rt==29 and x.simm<0 and I(a+4).m=='sd' and I(a+4).rt==31: return a
        a-=4
    return None
def lit_apres(a):
    """apres le jal en a : 'RES'/'C' lu avant ecriture ? (lineaire, 40 instr., suit pas les sauts)"""
    r=[]
    seen=set()
    for k in range(2,60):
        y=I(a+4*k)
        if y.m in ('lw','lh','lb') and y.rs!=29 and y.imm in (0x1150,0x1158) and y.imm not in seen: r.append({0x1150:'RES',0x1158:'C'}[y.imm]); seen.add(y.imm)
        if y.m=='sw' and y.rs!=29 and y.imm in (0x1150,0x1158): seen.add(y.imm)
        if y.m in ('jal','jalr') or (y.m=='jr'): break
    return r
for s in sys.argv[2:]:
    o=int(s,16); d=debut(o); cs=JAL.get(d,[])
    print("site 0x%x : fonction 0x%x, %d appelants jal"%(o,d,len(cs)))
    for c in cs:
        print("    appel en 0x%x : lit apres le retour %s"%(c,lit_apres(c) or '-'))
