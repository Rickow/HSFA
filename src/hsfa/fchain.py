#!/usr/bin/env python3
"""Carte MIPS<->68K par CHAINAGE AU NIVEAU DES FONCTIONS.

Reprend tout ce qui a ete corrige :
  - decoupage MIPS par CIBLES DE JAL (2788 fn) et non par 'jr ra' (9219, faux) ;
  - filtre par RATIO DE TAILLE (mediane d'expansion 6,9x, faible dispersion :
    une paire a 0,3x ou 30x est fausse) ;
  - selection de candidats ELARGIE (l'ancienne se limitait au top-6) ;
  - chainage ITERATIF (les blocs sont reordonnes : une seule LIS n'en voit qu'un).

On travaille sur les INDICES de fonction, pas sur les octets : la colinearite a ete
demontree a ce niveau (fonctions consecutives des deux cotes).
"""
import sys, json, bisect, collections
sys.path.insert(0, "<workspace>/scripts/untranspile")
from mips import CODE0, CODE1
from funcs import mips_functions_by_calls, m68k_functions
from rosetta2 import mips_const_seq, k_const_seq, ordered_ratio

RATIO_LO, RATIO_HI = 2.0, 14.0        # expansion plausible (mediane mesuree 6,9x)

def candidates(mf, kf, min_const=5, topn=25):
    """-> {i_mips: [(score, j_68k), ...]} par index inverse sur les constantes."""
    inv=collections.defaultdict(list)
    for j,(a,b,c) in enumerate(kf):
        for v in c:
            if len(inv[v])<4000: inv[v].append(j)
    out={}
    for i,(a,b,cs) in enumerate(mf):
        if len(cs)<min_const: continue
        cnt=collections.Counter()
        for v in cs:
            for j in inv.get(v,()): cnt[j]+=1
        if not cnt: continue
        msz=b-a
        keep=[]
        for j,sc in cnt.most_common(topn):
            ksz=kf[j][1]-kf[j][0]
            if ksz<=0: continue
            r=msz/ksz
            if not (RATIO_LO<=r<=RATIO_HI): continue      # filtre de taille
            keep.append((sc,j))
        if keep: out[i]=keep
    return out

def score_pairs(ro3,k68,mf,kf,cand,thr=0.75,minc=5):
    """verifie chaque candidat par alignement ordonne des constantes."""
    pairs=[]
    for i,lst in cand.items():
        ms=mips_const_seq(ro3,mf[i][0],mf[i][1])
        best=None
        for sc,j in lst:
            ks=k_const_seq(k68,kf[j][0],kf[j][1])
            r,t=ordered_ratio(ms,ks)
            if best is None or r>best[0]: best=(r,t,j)
        if best and best[0]>=thr and best[1]>=minc:
            pairs.append((i,best[2],best[0],best[1]))
    return pairs

def lis_pairs(pairs):
    """plus longue suite ou i et j croissent ensemble (indices de fonction)."""
    p=sorted(pairs)
    tails=[]; idx=[]; back=[None]*len(p)
    for n,(i,j,_,_) in enumerate(p):
        q=bisect.bisect_left(tails,j)
        if q==len(tails): tails.append(j); idx.append(n)
        else: tails[q]=j; idx[q]=n
        back[n]=idx[q-1] if q>0 else None
    out=[]; cur=idx[-1] if idx else None
    while cur is not None:
        out.append(p[cur]); cur=back[cur]
    return out[::-1]

if __name__=="__main__":
    ro3=open("<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin","rb").read()
    S="<workspace>/work/cps2"
    k68=open(S+"/sfa3_prog.bin","rb").read()
    mf=mips_functions_by_calls(ro3,CODE0,CODE1)
    kf=m68k_functions(k68)
    print("fonctions : MIPS %d (par cibles de jal) | 68K %d"%(len(mf),len(kf)))
    cand=candidates(mf,kf)
    print("fonctions MIPS avec candidats apres filtre de taille : %d"%len(cand))
    pairs=score_pairs(ro3,k68,mf,kf,cand)
    print("paires verifiees (alignement >=75%%) : %d\n"%len(pairs))
    # chainage iteratif
    rem=list(pairs); chains=[]
    while rem:
        ch=lis_pairs(rem)
        if len(ch)<3: break
        chains.append(ch)
        used={(i,j) for i,j,_,_ in ch}
        rem=[p for p in rem if (p[0],p[1]) not in used]
    print("=== chaines colineaires (>=3 fonctions) : %d ==="%len(chains))
    tot=0; cov=0
    for c in sorted(chains,key=len,reverse=True)[:10]:
        i0,j0=c[0][0],c[0][1]; i1,j1=c[-1][0],c[-1][1]
        span=kf[j1][1]-kf[j0][0]
        cov+=span; tot+=len(c)
        print("  %3d fn   MIPS fn[%4d..%4d] (%07x..%07x)  <->  68K fn[%4d..%4d] (%06x..%06x)"%(
            len(c),i0,i1,mf[i0][0],mf[i1][1],j0,j1,kf[j0][0],kf[j1][1]))
    for c in sorted(chains,key=len,reverse=True)[10:]:
        cov+=kf[c[-1][1]][1]-kf[c[0][1]][0]; tot+=len(c)
    print("\nfonctions chainees : %d   couverture 68K : %d o (%.1f%% de la zone code)"%(
        tot,cov,100*cov/0x100000))
    json.dump([[mf[i][0],kf[j][0],round(r,3),t] for i,j,r,t in pairs],
              open("<workspace>/scripts/untranspile/fpairs.json","w"))
    print("paires exportees -> fpairs.json")
