#!/usr/bin/env python3
"""bcc_apres_appel.py roN -- Bcc of the image whose instruction emitted just before is a JSR (the branch thus reads
the flags returned by the callee) WHILE the MIPS, between the jal and the branch, recomputes the RES (0x1150) or C
(0x1158) slot: a compare / test of the original 68K was not emitted. Gives the last MIPS subtraction seen (operands)
to identify the lost compare.
Review E7 / E7 bis (CMP_D8, CMP_MEMDN); integrated into the v161 build as a safeguard ("Bcc after call", build.log).
Expected on a v161 build: 0 sites in the three games.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, struct, re, collections
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
from mips import Ins
import carte
mod=sys.argv[1]
buf=paths.module(mod)
E=carte.lit(mod); n=0
BCC=re.compile(r'^B(EQ|NE|PL|MI|CS|CC|GT|LE|LT|GE|HI|LS|VC|VS) ')
for k in range(1,len(E)):
    a,v,t=E[k]; h=carte.tete(t)
    if not BCC.match(h): continue
    pa,pv,pt=E[k-1]; ph=carte.tete(pt)
    if not (ph.startswith('JSR') or 'JSR ' in ph.split(' ; ')[-1]) or 'T_' in ph: continue
    if not (pv<v<=pv+0x400): continue
    w=[]; sub=None
    for va in range(pv+8,v+4,4):
        x=Ins(va,struct.unpack_from('<I',buf,va)[0])
        if x.m=='sw' and (x.imm&0xffff) in (0x1150,0x1158) and x.rs!=29: w.append((va,'RES' if (x.imm&0xffff)==0x1150 else 'C'))
        if x.m in ('subu','sltu','slt','andi','and'): sub="%07x %r"%(va,x)
    if any(c=='RES' for _,c in w):
        n+=1
        print("%06x %07x %-28s apres %06x %-40s | RES recalcule en %07x ; dernier calcul : %s"%(a,v,h[:28],pa,ph[:40],w[0][0],sub))
print("%s : %d branchements sur les drapeaux de l'appele alors que le MIPS recalcule RES"%(mod,n))
