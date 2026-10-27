#!/usr/bin/env python3
"""Quelles instructions de la ROM correspondent a un motif MIPS non traduit ?

Dans les fonctions d'origine alignees sur la ROM (LCS sur les opcodes), un acces MIPS non
traduit tombe dans un TROU entre deux instructions emises appariees. Les instructions de la
ROM situees dans le trou correspondant sont celles que le motif represente. On les compte
sur tous les sites. Usage : gapprobe.py <slot hex,...>"""
import sys, os, struct, bisect, collections, random
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import translate as T, verify, e2e, m68k
from assemble import assemble, size
from layout_probe import insts
from mips import decode, CODE0, CODE1
SLOTS=[int(x,16) for x in sys.argv[1].split(',')]
buf=open(verify.RO3,"rb").read(); k68=open(verify.K68,"rb").read()[:0x100000]
kw=struct.unpack('>%dH'%(len(k68)//2),k68)
starts=sorted({x.tgt-T.RUNTIME_BASE for x in decode(buf,CODE0,CODE1) if x.m=='jal'})
L=list(decode(buf,CODE0,CODE1)); sites=collections.defaultdict(list)
for j in range(1,len(L)):
    x=L[j]
    if x.m in ('sw','sh','sb','lw','lh','lb','lhu','lbu') and L[j-1].m=='lui' and L[j-1].imm==0x7000 \
       and L[j-1].rt==x.rs and x.imm in SLOTS:
        k=bisect.bisect_right(starts,x.va)-1
        if k>=0: sites[starts[k]].append((x.va,x.m,x.imm))
ext=e2e.snapped_external(kw)
def name(ins):
    w=ins[0]
    return '%04x'%w
res=collections.defaultdict(collections.Counter); ex=collections.defaultdict(list); nf=0
for a,lst in sites.items():
    k=bisect.bisect_right(starts,a); b=starts[k] if k<len(starts) else CODE1
    if b-a>0x3000: continue
    k0=T.mips_to_68k(a)
    if k0 is None: continue
    its,words,u=assemble(buf,a,b,external=ext)
    if len(words)<8: continue
    sc,j=e2e.locate_mapped(kw,words,k0)
    if j is None or sc<6: continue
    its,words,u=assemble(buf,a,b,base=j*2,external=ext)
    E=insts(list(words)); R=insts(list(kw[j:j+len(words)+80]))
    w2va=[]
    for it in its: w2va+=[it.va]*(size(it)//2)
    Eva=[]; p=0
    for e in E: Eva.append(w2va[p] if p<len(w2va) else 1<<30); p+=len(e)
    n1,n2=len(E),len(R); dp=[[0]*(n2+1) for _ in range(n1+1)]
    for x in range(n1-1,-1,-1):
        for y in range(n2-1,-1,-1):
            dp[x][y]=dp[x+1][y+1]+1 if E[x]==R[y] else max(dp[x+1][y],dp[x][y+1])
    x=y=0; match=[]
    while x<n1 and y<n2:
        if E[x]==R[y]: match.append((x,y)); x+=1; y+=1
        elif dp[x+1][y]>=dp[x][y+1]: x+=1
        else: y+=1
    if len(match)<5: continue
    nf+=1
    for va,m,slot in lst:
        prev=[(xx,yy) for xx,yy in match if Eva[xx]<=va]; nxt=[(xx,yy) for xx,yy in match if Eva[xx]>va]
        if not prev or not nxt: continue
        (px,py),(nx,ny)=prev[-1],nxt[0]
        gapE=E[px+1:nx]; gapR=R[py+1:ny]
        if len(gapR)==0 or len(gapR)>3: continue          # trou net et court seulement
        for r in gapR:
            res[(slot,m)][name(r)]+=1
            if len(ex[(slot,m)])<3: ex[(slot,m)].append(' '.join('%04x'%w for w in r))
print("fonctions alignees : %d"%nf)
for key in sorted(res):
    print("\ncase %#x (%s) : instructions ROM dans le trou correspondant :"%(key[0],key[1]))
    for op,c in res[key].most_common(8): print("   %s  x%d"%(op,c))
    print("   exemples :",' | '.join(ex[key]))
