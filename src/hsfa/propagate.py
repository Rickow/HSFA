#!/usr/bin/env python3
"""Elargissement de la carte par PROPAGATION DANS LE GRAPHE D'APPELS.

Principe : si une fonction MIPS cartographiee appelle N fonctions dans un certain
ordre, sa jumelle 68K appelle N fonctions dans le MEME ordre (la recompilation
preserve l'ordre des appels). On apparie positionnellement, ce qui produit de
NOUVELLES correspondances, puis on itere.

Bien plus puissant que le chainage de constantes : chaque paire connue en engendre
autant que la fonction fait d'appels.
"""
import sys, struct, json, collections
sys.path.insert(0, "<workspace>/scripts/untranspile")
from mips import CODE0, CODE1
from mips import decode
from m68k import decode_one

RUNTIME_BASE = 0x1f0000

def mips_calls(buf, a, b):
    """-> [offsets fichier des cibles de jal, dans l'ordre]"""
    out=[]
    for ins in decode(buf, a, b):
        if ins.m=='jal':
            out.append(ins.tgt - RUNTIME_BASE)
    return out

def m68k_calls(buf, a, b):
    """-> [adresses cibles de JSR abs.L / BSR, dans l'ordre]"""
    n=len(buf)//2
    w=struct.unpack('>%dH'%n, buf[:n*2])
    i=a//2; end=b//2; out=[]
    while i < end and i < n:
        r=decode_one(w, i, n)
        if r is None:
            break          # opcode inconnu = on a quitte le code : ARRETER.
                           # (resynchroniser octet par octet faisait lire des donnees
                           #  comme des instructions -> faux appels en masse)
        L,_=r
        op=w[i]
        if op==0x4eb9 and i+2 < n:                      # JSR (xxx).L
            out.append((w[i+1]<<16)|w[i+2])
        elif (op & 0xff00)==0x6100:                     # BSR
            d=op & 0xff
            if d==0: 
                if i+1<n:
                    dd=w[i+1]; dd=dd-0x10000 if dd&0x8000 else dd
                    out.append(i*2+2+dd)
            elif d!=0xff:
                dd=d-0x100 if d&0x80 else d
                out.append(i*2+2+dd)
        i += L
    return out

def snap_to_funcs(ro3, k68, pairs):
    """recale chaque paire sur le DEBUT de fonction qui l'englobe, des deux cotes.
    Sans ca les listes d'appels demarrent en milieu de fonction et ne s'alignent pas."""
    from funcs import mips_functions, m68k_functions
    mf=[a for a,b,c in mips_functions(ro3,CODE0,CODE1)]
    kf=[a for a,b,c in m68k_functions(k68)]
    import bisect
    out={}
    for m,k in pairs.items():
        i=bisect.bisect_right(mf,m)-1
        j=bisect.bisect_right(kf,k)-1
        if i>=0 and j>=0:
            out[mf[i]]=kf[j]
    return out

def load_map():
    f="<workspace>/scripts/untranspile/map_ro3_sfa3.json"
    return json.load(open(f))["blocks"]

def seed_pairs(blocks):
    """paires (mips_off, k68_off) issues des points de la carte"""
    p={}
    for b in blocks:
        for m,k in b["points"]:
            p[m]=k
    return p

def propagate(ro3, k68, pairs, blocks, rounds=8, window=0x3000, thr=0.70):
    """PROPOSER puis VERIFIER : une paire issue du graphe d'appels n'est acceptee
    que si l'alignement ordonne de ses constantes la confirme. Sans cette
    verification, ~43%% des paires propagees sont fausses (mesure faite)."""
    from funcs import mips_functions, m68k_functions
    from rosetta2 import mips_const_seq, k_const_seq, ordered_ratio
    import bisect
    mfl=mips_functions(ro3,CODE0,CODE1); kfl=m68k_functions(k68)
    mstart=[a for a,b,c in mfl]; kstart=[a for a,b,c in kfl]
    mend={a:b for a,b,c in mfl};  kend={a:b for a,b,c in kfl}
    def bounds(lst, ends, x):
        i=bisect.bisect_right(lst,x)-1
        if i<0: return None
        a=lst[i]; return (a, ends[a])
    def verify(m,k):
        bm=bounds(mstart,mend,m); bk=bounds(kstart,kend,k)
        if not bm or not bk: return 0.0,0
        ms=mips_const_seq(ro3,*bm); ks=k_const_seq(k68,*bk)
        if len(ms)<4: return 0.0,0
        return ordered_ratio(ms,ks)
    known=dict(pairs); rejected=0
    for r in range(rounds):
        new={}; prop=0
        for m,k in list(known.items()):
            # BORNES REELLES de fonction des deux cotes (une fenetre fixe debordait
            # sur les fonctions suivantes et ramassait leurs appels)
            bm=bounds(mstart,mend,m); bk=bounds(kstart,kend,k)
            if not bm or not bk: continue
            mc=mips_calls(ro3, bm[0], bm[1])
            kc=m68k_calls(k68, bk[0], bk[1])
            if not mc or not kc: continue
            n=min(len(mc),len(kc))
            if n==0 or abs(len(mc)-len(kc))>max(2,n//3): continue
            for a,b in zip(mc[:n],kc[:n]):
                if not (0<a<len(ro3) and 0<b<len(k68)): continue
                if a in known or a in new: continue
                prop+=1
                ratio,t=verify(a,b)
                if ratio>=thr and t>=4: new[a]=b
                else: rejected+=1
        if not new: break
        known.update(new)
        print("  passe %d : %d proposees, +%d VERIFIEES  (total %d)"%(r+1,prop,len(new),len(known)))
    print("  (rejetees faute de verification : %d)"%rejected)
    return known

if __name__=="__main__":
    ro3=open("<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin","rb").read()
    S="<workspace>/work/cps2"
    k68=open(S+"/sfa3_prog.bin","rb").read()
    blocks=load_map()
    seeds=seed_pairs(blocks)
    print("points de la carte : %d"%len(seeds))
    seeds=snap_to_funcs(ro3,k68,seeds)
    print("apres recalage sur les debuts de fonction : %d paires distinctes\n"%len(seeds))
    known=propagate(ro3,k68,seeds,blocks)
    print("\npaires apres propagation : %d  (x%.1f)"%(len(known),len(known)/max(1,len(seeds))))
    ks=sorted(set(known.values()))
    span=0
    if ks:
        # couverture 68K estimee : somme des ecarts < 0x400 entre paires voisines
        for a,b in zip(ks,ks[1:]):
            if 0<b-a<0x400: span+=b-a
    print("couverture 68K estimee : %d o (%.1f%% de la zone code)"%(span,100*span/0x100000))
    json.dump({str(m):k for m,k in known.items()},
              open("<workspace>/scripts/untranspile/pairs_propagated.json","w"))
    print("paires exportees -> pairs_propagated.json")
