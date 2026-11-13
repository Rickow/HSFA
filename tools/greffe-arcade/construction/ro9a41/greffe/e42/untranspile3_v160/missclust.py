#!/usr/bin/env python3
"""Regroupe TOUS les manques du recensement (branchements, ecritures registre,
ecritures memoire) par signature abstraite des instructions qui precedent.
Usage : missclust.py [genre[,genre]] [profondeur] [n]   genre = beq,bne,ecrit-D,mem,...
"""
import sys,os,collections,struct
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
from mips import decode, CODE0
import translate as T, census
from cluster import abst
import natmiss
buf=open(census.RO3,"rb").read()
end=struct.unpack_from('<I',buf,12)[0]
kinds=sys.argv[1].split(",") if len(sys.argv)>1 and sys.argv[1] else None
depth=int(sys.argv[2]) if len(sys.argv)>2 else 7
N=int(sys.argv[3]) if len(sys.argv)>3 else 12
sig=collections.defaultdict(collections.Counter); ex={}
x=CODE0
while x<end:
    b=min(x+census.CHUNK,end)
    out,_=T.translate(buf,x,b); em={va for va,_,ws in out}
    L=list(decode(buf,x,b))
    for i,ins in enumerate(L):
        m=ins.m; k0=None
        if m in census.BR: k0=m
        elif m in ('sb','sh','sw') and ins.rs!=29:
            if i>0 and L[i-1].m=='lui' and L[i-1].imm==0x7000 and ins.rs==L[i-1].rt:
                nm=census.slot(ins.imm)
                if nm in ('RES','NFLG'): continue
                k0='ecrit-'+nm[0]
            else: k0='mem'
        if not k0 or (kinds and k0 not in kinds): continue
        if natmiss.native(natmiss.fidx(ins.va)): continue
        if ins.va >= int(os.environ.get("MAXVA","ffffffff"),16): continue   # (HANDOFF §78) zone du portage exclue
        if any(v in em for v in (ins.va-8,ins.va-4,ins.va,ins.va+4)): continue
        pre=[s for s in (abst(y) for y in L[max(0,i-16):i]) if s][-depth:]
        tail=m+(' rs,zero' if m in('beq','bne') and ins.rt==0 else '')
        k=tuple(pre)+(tail,)
        sig[k0][k]+=1; ex.setdefault(k,ins.va)
    x=b
for k0,c in sorted(sig.items(),key=lambda t:-sum(t[1].values())):
    tot=sum(c.values()); print("\n=== %s manques : %d"%(k0,tot))
    for k,n in c.most_common(N): print("  %4d (%2.0f%%) @%07x  %s"%(n,100*n/tot,ex[k],' ; '.join(k)))
