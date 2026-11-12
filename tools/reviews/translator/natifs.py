#!/usr/bin/env python3
"""natifs.py roN [start end] -- functions of the module (cut on jal targets / jump-table pointers and 'jr ra') in
[start, end) (file offsets): size, accesses to the 0x7000xxxx register slots (= recompiled 68K code), class in the
hooks file ("natif du module" -> RTS stub if native_at), map lines emitted, callers (jal) in TRANSLATED code and in the
zone itself. Says "traduit / non traduit / partiel". Review E2.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, struct, json, collections, bisect, os
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
from mips import Ins, CODE0
import carte
mod=sys.argv[1]
buf=paths.module(mod)
CODE1=struct.unpack_from('<I',buf,12)[0]; RB=0x1f0000
lo=int(sys.argv[2],16) if len(sys.argv)>2 else CODE0; hi=int(sys.argv[3],16) if len(sys.argv)>3 else CODE1
H=json.load(open(os.path.join(paths.SRC,'hooks_fork_%s.json'%mod),encoding='utf-8'))
HK={int(k,16):v for k,v in H.items()}
L=[Ins(a,struct.unpack_from('<I',buf,a)[0]) for a in range(CODE0,CODE1,4)]
starts=collections.defaultdict(list)
for x in L:
    if x.m=='jal' and CODE0<=x.tgt-RB<CODE1: starts[x.tgt-RB].append(x.va)
S=sorted(starts)
E=carte.lit(mod); CV=collections.Counter()
for a,v,t in E: CV[v]+=1
cvs=sorted(CV)
def fonction(t):
    k=bisect.bisect_right(S,t); fin=S[k] if k<len(S) else CODE1
    return [x for x in L[(t-CODE0)//4:(fin-CODE0)//4]]
print("%s : fonctions dans %x-%x"%(mod,lo,hi))
print("  debut   n   reg7000 ecrit_mem carte  appelants(zone/jeu)  hooks")
tot=collections.Counter()
for t in S:
    if not (lo<=t<hi): continue
    F=fonction(t); n=len(F)
    a=sum(1 for x in F if x.m=='lui' and x.imm==0x7000)
    w=sum(1 for x in F if x.m in ('sb','sh','sw','sd') and x.rs not in (29,))
    c=sum(CV[x.va] for x in F)
    cz=sum(1 for v in starts[t] if lo<=v<hi); cj=len(starts[t])-cz
    h=HK.get(t,{}); ht=h.get('type','-') if isinstance(h,dict) else str(h)
    etat='traduit' if c>n/40 and a else ('non traduit' if c==0 else 'partiel')
    tot[(etat,ht)]+=1
    print("  %06x %4d %5d %6d %6d   %3d/%-3d  %-22s %s"%(t,n,a,w,c,cz,cj,ht[:22],etat))
for k,v in sorted(tot.items()): print("  %4d %s"%(v,k))
