#!/usr/bin/env python3
"""aides_appels.py roN -- every 'jal' to a recompiler helper declared in profils.py (movem_push, movem_pop,
andi_ccr, abcd, roxr; sbcd listed for reference): does the map carry the expected inline form at that site, or a JSR /
nothing (helper not recognised = call to the helper's C body, which does nothing in the image)?
Review E5 (BCD_REG: combo score bonus lost); v161 build guard GARDE_AIDES makes the build fail on such a site.
Expected on a v161 build: no "NON RENDU" line. Helper addresses are those of ro3 / ro5 / ro9 (table A below).
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, struct, collections, re
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
from mips import Ins, CODE0
import carte
A={'ro3':{0x570360:'movem_push',0x5706c0:'movem_pop',0x570a20:'andi_ccr',0x570d00:'abcd',0x570aa0:'roxr',0x570bb0:'sbcd (non declaree)'},
   'ro5':{0x212b00:'movem_push',0x212e60:'movem_pop',0x2131c0:'andi_ccr',0x2134a0:'abcd',0x213240:'roxr',0x213350:'sbcd (non declaree)'},
   'ro9':{0x212dc0:'movem_push',0x213120:'movem_pop',0x213480:'andi_ccr',0x213610:'abcd',0x213500:'roxr'}}
ATT={'movem_push':'MOVEM','movem_pop':'MOVEM','andi_ccr':'CCR','abcd':'ABCD','roxr':'ROXR','sbcd (non declaree)':'SBCD'}
mod=sys.argv[1]
buf=paths.module(mod)
CODE1=struct.unpack_from('<I',buf,12)[0]
E=carte.lit(mod); C=collections.defaultdict(list)
for a,v,t in E: C[v].append((a,t))
tot=collections.Counter()
for va in range(CODE0,CODE1,4):
    x=Ins(va,struct.unpack_from('<I',buf,va)[0])
    if x.m!='jal' or x.tgt not in A[mod]: continue
    nom=A[mod][x.tgt]; em=[]
    for w in range(va-8,va+12,4): em+=C.get(w,[])
    ok=any(ATT[nom] in t for a,t in em)
    tot[(nom,'en ligne' if ok else 'NON RENDU')]+=1
    if not ok: print("  %07x -> %-18s : %s"%(va,nom,' || '.join('%06x %s'%(a,t[:56]) for a,t in em) or 'RIEN'))
print(mod,dict(tot))
