#!/usr/bin/env python3
"""Exemples de PREMIERE DIVERGENCE par categorie (traduction assemblee vs ROM), sur des
fonctions d'origine localisees par la carte. Usage : diverge.py [N par categorie] [cat,cat...]"""
import sys,os,struct,collections,json,re,random,bisect
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import translate as T, verify, e2e
from assemble import assemble, size
from mips import decode, CODE0, CODE1
N=int(sys.argv[1]) if len(sys.argv)>1 else 2
CATS=set(sys.argv[2].split(',')) if len(sys.argv)>2 else None
buf=open(verify.RO3,"rb").read(); k68=open(verify.K68,"rb").read()[:0x100000]
kw=struct.unpack('>%dH'%(len(k68)//2),k68)
fz=json.load(open(os.path.join(D,"hooks_a5.json"))); foreign={int(k,16) for k in fz["foreign"]}
bad={0x05,0x18,0x19,0x1a,0x1b,0x38,0x39,0x02,0x03,0x04}
starts=sorted({x.tgt-T.RUNTIME_BASE for x in decode(buf,CODE0,CODE1) if x.m=='jal'})
random.seed(9); cand=[s for s in starts if (s>>16) not in bad]; random.shuffle(cand)
ext=e2e.snapped_external(kw); want=collections.Counter()
for a in cand[:600]:
    k=bisect.bisect_right(starts,a); b=starts[k] if k<len(starts) else CODE1
    if b-a>0x3000 or b-a<0x40: continue
    k0=T.mips_to_68k(a)
    if k0 is None: continue
    its,words,u=assemble(buf,a,b,external=ext)
    if len(words)<8 or any(int(d,16) in foreign for it in its for d in re.findall(r'\$([0-9a-f]{4})\(A5\)',it.mn)): continue
    sc,j=e2e.locate_mapped(kw,words,k0)
    if j is None or sc<4: continue
    its,words,u=assemble(buf,a,b,base=j*2,external=ext)
    ref=kw[j:j+len(words)]; pos=0
    for n,it in enumerate(its):
        sz=size(it)//2
        if any(pos+t<len(words) and words[pos+t]!=ref[pos+t] for t in range(sz)):
            cat=it.mn.split()[0] if it.mn else '?'
            if want[cat]<N and (CATS is None or cat in CATS):
                want[cat]+=1
                print("=== %s  (MIPS %07x, ROM %06x, +%04x)"%(cat,a,j*2,pos*2))
                for m in its[max(0,n-2):n+3]: print("      %s %-50s"%(">>" if m is it else "  ",m.mn[:50]))
                print("   emis :",' '.join('%04x'%w for w in words[max(0,pos-4):pos+8]))
                print("   ROM  :",' '.join('%04x'%w for w in ref[max(0,pos-4):pos+8]))
            break
        pos+=sz
