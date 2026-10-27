#!/usr/bin/env python3
"""Grappes monotones + interpolation de la carte MIPS<->68K.

Constat : le recompilateur emet les fonctions dans l'ordre de l'original, par blocs.
Donc entre deux ancres d'une meme grappe, les fonctions MIPS intermediaires
correspondent aux fonctions 68K intermediaires, dans l'ordre.
On interpole, puis on VERIFIE chaque paire interpolee par alignement de constantes.
"""
import sys, struct, collections, difflib
sys.path.insert(0, "<workspace>/scripts/untranspile")
from mips import CODE0, CODE1
from mips import decode
from funcs import mips_functions, m68k_functions
from rosetta2 import mips_const_seq, k_const_seq, ordered_ratio

def anchors(mf, kf, k68, ro3, minc=8, thr=0.85):
    inv=collections.defaultdict(set)
    for i,(a,b,c) in enumerate(kf):
        for v in c:
            if len(inv[v])<2500: inv[v].add(i)
    out=[]
    for mi,(a,b,cs) in enumerate(mf):
        if len(cs)<minc: continue
        cand=collections.Counter()
        for v in cs:
            for i in inv.get(v,()): cand[i]+=1
        ms=mips_const_seq(ro3,a,b); best=None
        for i,_ in cand.most_common(6):
            ks=k_const_seq(k68,kf[i][0],kf[i][1])
            r,t=ordered_ratio(ms,ks)
            if best is None or r>best[0]: best=(r,t,i)
        if best and best[0]>=thr and best[1]>=minc:
            out.append((mi,best[2],best[0]))
    return out

def build_clusters(anch, max_gap_m=40, max_gap_k=40):
    """suites ou les indices MIPS ET 68K croissent ensemble."""
    anch=sorted(anch)
    cl=[]; cur=[anch[0]]
    for a in anch[1:]:
        pm,pk,_=cur[-1]
        if a[0]>pm and a[1]>pk and a[0]-pm<=max_gap_m and a[1]-pk<=max_gap_k:
            cur.append(a)
        else:
            if len(cur)>=2: cl.append(cur)
            cur=[a]
    if len(cur)>=2: cl.append(cur)
    return cl

if __name__=="__main__":
    ro3=open("<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin","rb").read()
    S="<workspace>/work/cps2"
    k68=open(S+"/sfa3_prog.bin","rb").read()
    mf=mips_functions(ro3,CODE0,CODE1); kf=m68k_functions(k68)
    anch=anchors(mf,kf,k68,ro3)
    print("ancres : %d"%len(anch))
    cl=build_clusters(anch)
    print("grappes monotones : %d\n"%len(cl))
    total_interp=0; total_ok=0
    for ci,c in enumerate(cl):
        span_m=c[-1][0]-c[0][0]; span_k=c[-1][1]-c[0][1]
        print("  grappe %d : %d ancres | MIPS fn[%d..%d] <-> 68K fn[%d..%d]"%(
            ci,len(c),c[0][0],c[-1][0],c[0][1],c[-1][1]))
        # interpolation entre ancres consecutives
        for (m1,k1,_),(m2,k2,_) in zip(c,c[1:]):
            nm=m2-m1-1; nk=k2-k1-1
            if nm<=0 or nk<=0 or nm!=nk: continue
            for d in range(1,nm+1):
                mi,ki=m1+d,k1+d
                ms=mips_const_seq(ro3,mf[mi][0],mf[mi][1])
                ks=k_const_seq(k68,kf[ki][0],kf[ki][1])
                r,t=ordered_ratio(ms,ks)
                total_interp+=1
                if r>=0.7 and t>=3:
                    total_ok+=1
                    print("      + interpolee OK  %3.0f%% (%2d const)  MIPS %07x <-> 68K %06x"%(
                        100*r,t,mf[mi][0],kf[ki][0]))
    print("\ninterpolations proposees : %d | confirmees par les constantes : %d"%(total_interp,total_ok))
