#!/usr/bin/env python3
"""Chainage COLINEAIRE (et non plus simplement croissant) + fusion des signaux.

DEUX DEFAUTS des versions precedentes, tous deux corriges ici :

1. LIS = "plus longue sous-suite CROISSANTE" n'impose que l'ORDRE. Deux points aux
   deux bouts du binaire satisfont l'ordre, donc la LIS fabrique des chaines qui
   traversent tout le binaire avec des ratios d'expansion de 50x (impossibles).
   => ici : chainage avec CONTRAINTE LOCALE. Deux points ne peuvent se suivre dans
   une chaine que si le ratio d'expansion local (d_mips/d_68k) tient dans une bande
   plausible et si le saut reste borne. C'est le chainage a penalite de saut des
   aligneurs de genomes, pas une LIS.

2. Un seul signal (les constantes) laisse muettes les fonctions sans immediat
   distinctif. => ici : FUSION des ancres de plusieurs signaux (constantes via
   chain.py, opcodes traduits via xsearch.py) dans un meme chainage.

Couverture toujours mesuree en UNION.
"""
import sys, os, json, collections
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
from mips import CODE0, CODE1

RATIO_LO, RATIO_HI = 3.0, 12.0      # bande d'expansion MIPS/68K (theorie ~6.7)
MAXGAP_M           = 0x20000        # saut maximal cote MIPS entre deux ancres
MINLEN             = 5              # longueur minimale d'une chaine retenue
CODE_END           = 0x100000

def chain_colinear(anchors):
    """extraction iterative de chaines localement colineaires."""
    pts=sorted(set(anchors))
    used=[False]*len(pts)
    chains=[]
    while True:
        # DP sur les points encore libres
        idx=[i for i,p in enumerate(pts) if not used[i]]
        if len(idx)<MINLEN: break
        best={}; prev={}
        lo=0
        for n,i in enumerate(idx):
            mi,ki=pts[i]
            best[i]=1; prev[i]=None
            while idx[lo] < i and mi-pts[idx[lo]][0] > MAXGAP_M: lo+=1
            for j in idx[lo:n]:
                mj,kj=pts[j]
                dm=mi-mj; dk=ki-kj
                if dm<=0 or dk<=0: continue
                r=dm/dk
                if not (RATIO_LO<=r<=RATIO_HI): continue
                if best[j]+1>best[i]: best[i]=best[j]+1; prev[i]=j
        if not best: break
        top=max(best,key=lambda i:best[i])
        if best[top]<MINLEN: break
        ch=[]; cur=top
        while cur is not None: ch.append(pts[cur]); used[cur]=True; cur=prev[cur]
        chains.append(ch[::-1])
    return chains

def union_cov(iv):
    iv=sorted(iv); u=[]
    for a,b in iv:
        if b<=a: continue
        if u and a<=u[-1][1]: u[-1]=(u[-1][0],max(u[-1][1],b))
        else: u.append((a,b))
    return sum(b-a for a,b in u),u

def seg_intervals(chains, maxgap=0x800, lo=2.0, hi=16.0):
    """intervalles 68K couverts a PRECISION UTILISABLE.

    Un bloc n'est pas utilisable d'un bout a l'autre : le taux d'expansion varie
    localement, donc interpoler sur toute son etendue est faux (verifie par
    l'independant verify.py). Ce qui est reellement utilisable, c'est le segment
    entre DEUX POINTS D'ANCRAGE CONSECUTIFS, a condition que le saut soit court et
    le ratio local plausible. C'est la metrique honnete."""
    iv=[]
    for c in chains:
        for (m0,k0),(m1,k1) in zip(c,c[1:]):
            if m1-m0>maxgap or k1<=k0: continue
            r=(m1-m0)/(k1-k0)
            if lo<=r<=hi: iv.append((k0,k1))
    return iv

def report(chains,label):
    iv=[(c[0][1],c[-1][1]) for c in chains]
    cov,_=union_cov(iv)
    raw=sum(max(0,b-a) for a,b in iv)
    print("\n== %s =="%label)
    print("  chaines : %d   points chaines : %d"%(len(chains),sum(len(c) for c in chains)))
    print("  COUVERTURE 68K (union) : %d o  (%.1f%%)   [somme brute %.1f%%, surcomptage %.1fx]"%(
        cov,100*cov/CODE_END,100*raw/CODE_END,raw/max(1,cov)))
    rs=sorted((c[-1][0]-c[0][0])/max(1,c[-1][1]-c[0][1]) for c in chains)
    if rs: print("  ratios d'expansion : min %.1f  median %.1f  max %.1f"%(
        rs[0],rs[len(rs)//2],rs[-1]))
    sv=seg_intervals(chains); scov,_=union_cov(sv)
    print("  >> COUVERTURE UTILISABLE (segments entre ancres consecutives) :")
    print("     %d o = %.1f%% de la zone code   (%d segments)"%(
        scov,100*scov/CODE_END,len(sv)))
    return cov,chains

if __name__=="__main__":
    src=sys.argv[1] if len(sys.argv)>1 else "both"
    anchors=collections.defaultdict(list)
    if src in ("const","both"):
        import chain as C
        ro3=open(C.__dict__.get("RO3") or "<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin","rb").read()
        S="<workspace>/work/cps2"
        k68=open(S+"/sfa3_prog.bin","rb").read()
        ms=C.mips_consts(ro3,CODE0,CODE1); ks=C.k68_consts(k68)
        for k in (3,4):
            km=C.kmers(ms,k); kk=C.kmers(ks,k)
            for key,mi in km.items():
                ki=kk.get(key)
                if not ki or len(mi)*len(ki)>4: continue
                for p in mi:
                    for q in ki: anchors['const'].append((ms[p][0],ks[q][0]))
        print("ancres CONSTANTES : %d"%len(set(anchors['const'])))
    if src in ("op","both"):
        f=os.path.join(D,"op_anchors.json")
        if os.path.exists(f):
            anchors['op']=[tuple(x) for x in json.load(open(f))]
            print("ancres OPCODES : %d (cache)"%len(set(anchors['op'])))
    allp=[p for v in anchors.values() for p in v]
    print("total ancres : %d"%len(set(allp)))
    ch=chain_colinear(allp)
    cov,ch=report(ch,"chainage colineaire (%s)"%src)
    out={"blocks":[{"mips":[c[0][0],c[-1][0]],"m68k":[c[0][1],c[-1][1]],"n":len(c),
                    "pts":c} for c in ch]}
    for b in sorted(out["blocks"],key=lambda z:-z["n"])[:10]:
        r=(b["mips"][1]-b["mips"][0])/max(1,b["m68k"][1]-b["m68k"][0])
        print("   %4d pts  MIPS %07x..%07x <-> 68K %06x..%06x  ratio %.1fx"%(
            b["n"],b["mips"][0],b["mips"][1],b["m68k"][0],b["m68k"][1],r))
    json.dump(out,open(os.path.join(D,"map_chain2.json"),"w"))
    print("\ncarte exportee -> map_chain2.json")
