#!/usr/bin/env python3
"""decalages.py roN -- for each MIPS sllv/srlv/srav, the map entry emitted next (at most 12 instructions further);
histogram of the 68K forms and list of the sites with no shift emitted. Review angle 5 (variable shifts).
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, struct, collections, bisect, re
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
import carte
from mips import decode
mod=sys.argv[1]; E=carte.lit(mod)
buf=paths.module(mod)
V=collections.defaultdict(list)
for a,v,t in E: V[v].append(t)
vs=sorted(V); end=struct.unpack_from('<I',buf,12)[0]; c0=0x22de0 if end==0x3bf140 else 0x22b00
C=collections.Counter(); ex=collections.defaultdict(list)
for x in decode(buf,c0,min(end,vs[-1])):
    if x.m not in ('sllv','srlv','srav'): continue
    k=bisect.bisect_left(vs,x.va); t=None
    if k<len(vs) and vs[k]-x.va<=48: t=' || '.join(V[vs[k]])
    key=re.sub(r'D\d','Dn',re.sub(r'\$[0-9a-f]+','$N',carte.tete(t).split(' ||')[0])) if t else 'RIEN'
    key=x.m+' -> '+key.split(',')[0][:30]
    C[key]+=1; ex[key].append((x.va,t))
print(mod)
for k,n in C.most_common(): print("  %4d %s   (ex. 0x%x)"%(n,k,ex[k][0][0]))
