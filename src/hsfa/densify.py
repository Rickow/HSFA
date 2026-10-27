#!/usr/bin/env python3
"""DENSIFICATION locale de la carte par le signal d'OPCODES.

Constat : le signal d'opcodes traduits est un tres bon VERIFICATEUR (96 % a l'ancre
connue contre 4 % au 95e centile du temoin) mais un mauvais CHERCHEUR global (les
opcodes 68000 emis sont peu varies : 1b7c/3b7c/1b40... donc une empreinte de 6
opcodes se retrouve partout). Conclusion : ne pas lui demander de chercher dans
tout le binaire, mais seulement DANS UNE FENETRE DEJA ENCADREE par deux ancres
fiables. Dans cette fenetre, l'ambiguite disparait.

Pour chaque paire d'ancres consecutives d'une chaine, on aligne la suite d'opcodes
traduits avec la suite d'opcodes reels de la fenetre 68K correspondante (alignement
type plus-longue-sous-suite-commune). Chaque opcode apparie devient une ANCRE.

On gagne donc en PRECISION (des ancres beaucoup plus rapprochees), ce qui augmente
la couverture UTILISABLE - la seule qui compte pour traduire.
"""
import sys, os, json, struct
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import translate, m68k
from chain2 import union_cov, CODE_END

RO3="<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin"
K68="<workspace>/work/cps2/sfa3_prog.bin"
GAP_MIN, GAP_MAX = 0x20, 0x4000
RUNMIN = int(os.environ.get('RUNMIN','3'))   # longueur minimale d'une suite apparieee

def ops68(w,n,a,b):
    out=[]; i=a//2; lim=b//2
    while i<min(n,lim):
        r=m68k.decode_one(w,i,n)
        if r is None: i+=1; continue
        out.append((i*2,w[i])); i+=r[0]
    return out

def lcs_pairs(A,B):
    """appariements de la plus longue sous-suite commune (sur la valeur d'opcode)."""
    na,nb=len(A),len(B)
    if na==0 or nb==0 or na*nb>400000: return []
    dp=[[0]*(nb+1) for _ in range(na+1)]
    for i in range(na-1,-1,-1):
        ri=dp[i]; rn=dp[i+1]; ai=A[i][1]
        for j in range(nb-1,-1,-1):
            ri[j]= rn[j+1]+1 if ai==B[j][1] else (rn[j] if rn[j]>=ri[j+1] else ri[j+1])
    out=[]; i=j=0
    while i<na and j<nb:
        if A[i][1]==B[j][1]: out.append((A[i][0],B[j][0])); i+=1; j+=1
        elif dp[i+1][j]>=dp[i][j+1]: i+=1
        else: j+=1
    return out

if __name__=="__main__":
    ro3=open(RO3,"rb").read(); k68=open(K68,"rb").read()
    n=len(k68)//2; w=struct.unpack('>%dH'%n,k68[:n*2])
    blocks=json.load(open(os.path.join(D,"map_chain2.json")))["blocks"]
    base=set(); chains=[]
    for b in blocks:
        p=[tuple(x) for x in (b.get("pts") or [])]
        if p: chains.append(p); base|=set(p)
    print("ancres de depart : %d dans %d chaines"%(len(base),len(chains)))
    new=set(); done=0; skipped=0
    for c in chains:
        for (m0,k0),(m1,k1) in zip(c,c[1:]):
            dm,dk=m1-m0,k1-k0
            if not (GAP_MIN<=dm<=GAP_MAX) or dk<=0: skipped+=1; continue
            if not (2.0<=dm/dk<=16.0): skipped+=1; continue
            try: ins,_=translate.translate(ro3,m0&~3,(m1&~3)+4)
            except Exception: skipped+=1; continue
            A=[(va,ws[0]) for va,_,ws in ins if ws]
            B=ops68(w,n,k0,k1+2)
            if len(A)<2 or len(B)<2: skipped+=1; continue
            # FILTRE DE SPECIFICITE : ne garder que les appariements pris dans une
            # SUITE de >=RUNMIN opcodes consecutifs apparies. Un opcode isole
            # (1b7c...) ne prouve rien ; trois de suite, si. Verifie par xcheck.py.
            pr=lcs_pairs(A,B)
            run=[]
            for t in pr+[None]:
                if t is not None and run and t[0]>run[-1][0] and t[1]>run[-1][1] \
                   and t[0]-run[-1][0]<=8 and t[1]-run[-1][1]<=8:
                    run.append(t); continue
                if len(run)>=RUNMIN: new.update(run)
                run=[t] if t is not None else []
            done+=1
    print("fenetres traitees : %d   (ignorees : %d)"%(done,skipped))
    allp=sorted(base|new)
    print("ancres apres densification : %d  (+%d, x%.1f)"%(
        len(allp),len(allp)-len(base),len(allp)/max(1,len(base))))
    # couverture utilisable : segments courts et de ratio plausible
    iv=[]
    for (m0,k0),(m1,k1) in zip(allp,allp[1:]):
        if not (0<m1-m0<=0x800) or k1<=k0: continue
        r=(m1-m0)/(k1-k0)
        if 2.0<=r<=16.0: iv.append((k0,k1))
    cov,_=union_cov(iv)
    print("\nCOUVERTURE UTILISABLE : %d o = %.1f%% de la zone code  (%d segments)"%(
        cov,100*cov/CODE_END,len(iv)))
    json.dump({"pts":allp},open(os.path.join(D,"map_dense.json"),"w"))
    print("carte densifiee -> map_dense.json")
