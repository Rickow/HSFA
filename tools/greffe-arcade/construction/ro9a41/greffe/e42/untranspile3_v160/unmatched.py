#!/usr/bin/env python3
"""Instructions de la ROM restees SANS correspondance dans les fonctions alignees, pour une
famille donnee : on affiche l'instruction ROM, nos instructions voisines et le MIPS au meme
endroit. Usage : unmatched.py <famille (opclass)> [N]"""
import sys, os, re, json, struct, random, bisect, collections
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import translate as T, verify, e2e, m68k
from assemble import assemble, size
from layout_probe import insts
from opclass import klass
from mips import decode, CODE0, CODE1
FAM=sys.argv[1]; N=int(sys.argv[2]) if len(sys.argv)>2 else 6
buf=open(verify.RO3,"rb").read(); k68=open(verify.K68,"rb").read()[:0x100000]
kw=struct.unpack('>%dH'%(len(k68)//2),k68)
fz=json.load(open(os.path.join(D,"hooks_a5.json"))); foreign={int(k,16) for k in fz["foreign"]}
bad={0x05,0x18,0x19,0x1a,0x1b,0x38,0x39,0x02,0x03,0x04}
starts=sorted({x.tgt-T.RUNTIME_BASE for x in decode(buf,CODE0,CODE1) if x.m=='jal'})
random.seed(9); cand=[s for s in starts if (s>>16) not in bad]; random.shuffle(cand)
ext=e2e.snapped_external(kw); shown=0
for a in cand[:900]:
    if shown>=N: break
    k=bisect.bisect_right(starts,a); b=starts[k] if k<len(starts) else CODE1
    if b-a>0x3000 or b-a<0x40: continue
    k0=T.mips_to_68k(a)
    if k0 is None: continue
    its,words,u=assemble(buf,a,b,external=ext)
    if len(words)<8 or any(int(d,16) in foreign for it in its for d in re.findall(r'\$([0-9a-f]{4})\(A5\)',it.mn)): continue
    sc,j=e2e.locate_mapped(kw,words,k0)
    if j is None or sc<6: continue
    its,words,u=assemble(buf,a,b,base=j*2,external=ext)
    E=insts(list(words)); R=insts(list(kw[j:j+len(words)]))
    w2it=[]
    for it in its: w2it+=[it]*(size(it)//2)
    Eit=[]; p=0
    for e in E: Eit.append(w2it[p] if p<len(w2it) else None); p+=len(e)
    n1,n2=len(E),len(R); dp=[[0]*(n2+1) for _ in range(n1+1)]
    for x in range(n1-1,-1,-1):
        for y in range(n2-1,-1,-1):
            dp[x][y]=dp[x+1][y+1]+1 if E[x][0]==R[y][0] else max(dp[x+1][y],dp[x][y+1])
    x=y=0; match=[]
    while x<n1 and y<n2:
        if E[x][0]==R[y][0]: match.append((x,y)); x+=1; y+=1
        elif dp[x+1][y]>=dp[x][y+1]: x+=1
        else: y+=1
    my={yy:xx for xx,yy in match}
    for yy,r in enumerate(R):
        if yy in my or klass(r[0])!=FAM: continue
        prev=[(xx,q) for xx,q in match if q<yy]; nxt=[(xx,q) for xx,q in match if q>yy]
        if not prev or not nxt: continue
        px,nx=prev[-1][0],nxt[0][0]
        itp=Eit[px]; itn=Eit[nx]
        if itp is None or itn is None: continue
        print("=== ROM %06x : %s   (entre nos '%s' et '%s')"%(j*2,' '.join('%04x'%w for w in r),itp.mn[:30],itn.mn[:30]))
        for z in decode(buf,itp.va,itn.va+4):
            if z.m!='lui' or z.imm!=0x7000: print("        %07x  %s"%(z.va,z))
        shown+=1
        if shown>=N: break
