#!/usr/bin/env python3
"""Verification CROISEE de la carte densifiee, par le signal RECIPROQUE.

Les ancres ajoutees par densify.py ont ete trouvees avec le signal d'OPCODES : les
verifier avec ce meme signal serait circulaire. On les verifie donc avec l'AUTRE
signal, les CONSTANTES : autour d'une ancre juste, les immediats du MIPS doivent se
retrouver parmi les operandes du 68K au meme endroit.

Temoin obligatoire : meme mesure a des offsets 68K tires au hasard.
"""
import sys,os,json,random
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
from mips import CODE0, CODE1
import chain as C
RO3="<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin"
K68="<workspace>/work/cps2/sfa3_prog.bin"
WM,WK=0x600,0xd0                     # fenetres appairees (ratio ~7x)

if __name__=="__main__":
    ro3=open(RO3,"rb").read(); k68=open(K68,"rb").read()
    ms=C.mips_consts(ro3,CODE0,CODE1)
    ks=C.k68_consts(k68)
    import bisect
    mx=[a for a,_ in ms]; kx=[a for a,_ in ks]
    def mwin(a,b):
        i=bisect.bisect_left(mx,a); j=bisect.bisect_left(mx,b)
        return set(v for _,v in ms[i:j])
    def kwin(a,b):
        i=bisect.bisect_left(kx,a); j=bisect.bisect_left(kx,b)
        return set(v for _,v in ks[i:j])
    dense=json.load(open(os.path.join(D,"map_dense.json")))["pts"]
    base=set()
    for b in json.load(open(os.path.join(D,"map_chain2.json")))["blocks"]:
        base|=set(tuple(x) for x in (b.get("pts") or []))
    added=[tuple(p) for p in dense if tuple(p) not in base]
    random.seed(11)
    for name,pool in (("ancres AJOUTEES par densification",added),
                      ("ancres d'ORIGINE (temoin positif)",sorted(base))):
        smp=random.sample(pool,min(400,len(pool)))
        g=[];r=[]
        for m,k in smp:
            cm=mwin(m,m+WM)
            if len(cm)<3: continue
            hit=len(cm & kwin(k,k+WK))/len(cm)
            ctrl=max(len(cm & kwin(x,x+WK)) for x in
                     (random.randrange(0,0xf0000)&~1 for _ in range(12)))/len(cm)
            g.append(hit); r.append(ctrl)
        if not g: print("%s : rien d'exploitable"%name); continue
        g.sort(); r.sort()
        win=sum(1 for a,b in zip(sorted(g),sorted(r)) if a>b)
        print("%s  (%d sondes)"%(name,len(g)))
        print("   recouvrement de constantes a l'endroit predit : median %.0f%%  moyenne %.0f%%"%(
            100*g[len(g)//2],100*sum(g)/len(g)))
        print("   temoin (max de 12 tirages au hasard)          : median %.0f%%  moyenne %.0f%%"%(
            100*r[len(r)//2],100*sum(r)/len(r)))
