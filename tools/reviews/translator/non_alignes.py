#!/usr/bin/env python3
"""non_alignes.py roN -- lwl/lwr/swl/swr of the 68K zone: pairs recognised by unaligned_pairs (adjacent, same
registers, displacement +3) and LEFTOVERS (unpaired: no translation), then what the map emits at the address of each
pair (nothing = loss). Review E3 (found sound).
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
vas=sorted(C); import bisect
def proche(v,n=3):
    """lignes de carte dans [v, v+4n]"""
    r=[]
    for w in range(v,v+4*n+1,4): r+=C.get(w,[])
    return r
L=[Ins(a,struct.unpack_from('<I',buf,a)[0]) for a in range(CODE0,CODE1,4)]
tot=collections.Counter(); pairs=[]; restes=[]; used=set()
for k,x in enumerate(L):
    if x.m not in ('lwl','lwr','swl','swr') or k in used: continue
    tot[x.m]+=1
    j=k+1
    while j<len(L) and L[j].w==0: j+=1
    y=L[j] if j<len(L) else None
    pr={'swl':'swr','swr':'swl','lwl':'lwr','lwr':'lwl'}[x.m]
    ok=False
    if y is not None and y.m==pr and y.rs==x.rs and y.rt==x.rt:
        l,r=(x,y) if x.m in ('swl','lwl') else (y,x)
        if l.simm==r.simm+3: ok=True
    if ok: used.add(j); tot[y.m]+=1; pairs.append((x,y,r.simm))
    else: restes.append(x)
print("%s : zone %x-%x ; %s ; paires reconnues %d ; restes non apparies %d"%(mod,CODE0,CODE1,dict(tot),len(pairs),len(restes)))
for x in restes: print("  RESTE %07x %r | carte : %s"%(x.va,x,' || '.join(t[:60] for a,t in proche(x.va))))
# deplacement des paires : pair non multiple de 4 attendu ; impair = long a adresse impaire
cl=collections.Counter()
for x,y,d in pairs:
    e=proche(x.va,2)
    kind=('ecrit' if x.m[0]=='s' else 'lit')
    key=(kind,'d%%4=%d'%(d%4),'emis' if e else 'RIEN')
    cl[key]+=1
    if not e or d%2: print("  %s %07x d=%d base r%d reg r%d | carte : %s"%(kind,x.va,d,x.rs,x.rt,' || '.join(t[:70] for a,t in e)))
for k,n in sorted(cl.items()): print("  %5d %s"%(n,' '.join(k)))
