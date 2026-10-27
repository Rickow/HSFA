#!/usr/bin/env python3
"""Carte MIPS<->68K par CHAINAGE DE K-MERS (sans decoupage en fonctions).

Le decoupage en fonctions est peu fiable des deux cotes (MIPS sur-decoupe par
'jr ra', 68K par RTS multiples). On s'en passe : on aligne directement les deux
SUITES de constantes, comme on aligne deux genomes.

1. k-mers : k constantes consecutives -> empreinte.
2. Appariement exact des empreintes rares (non repetees).
3. Chainage monotone (plus longue sous-suite croissante) -> blocs colineaires.
"""
import sys, struct, collections, bisect
sys.path.insert(0, "<workspace>/scripts/untranspile")
from mips import CODE0, CODE1
from mips import decode

def mips_consts(buf,a,b):
    out=[]
    for ins in decode(buf,a,b):
        v=None
        if ins.m in ('addiu','addi','ori','andi','xori','slti','sltiu','lui'):
            v=ins.imm
        elif ins.m in ('lb','lh','lw','lbu','lhu','sb','sh','sw','ld','sd'):
            if not (0x1000<=ins.imm<=0x11ff): v=ins.imm
        if v is not None and 0x100<=v<=0xfffe and v!=0x7000: out.append((ins.va,v))
    return out

def k68_consts(buf, end=0x100000):
    # SEUL LE 1er Mo EST CHIFFRE => seul le 1er Mo est du CODE. Au-dela = donnees.
    # On DECODE le 68000 pour n'extraire que les VRAIS operandes (plus d'opcodes).
    from m68k import walk
    ops,bad=walk(buf,0,end,resync=True)
    print("   (68K decode : %d operandes, %d opcodes inconnus)"%(len(ops),bad))
    return [(off,v) for off,v,kind in ops if 0x100<=v<=0xfffe]

def kmers(seq,k):
    d=collections.defaultdict(list)
    for i in range(len(seq)-k+1):
        d[tuple(v for _,v in seq[i:i+k])].append(i)
    return d

def lis(pairs):
    """plus longue sous-suite strictement croissante sur le 2e element."""
    pairs=sorted(pairs)
    tails=[]; idx=[]; back=[None]*len(pairs)
    for n,(a,b) in enumerate(pairs):
        j=bisect.bisect_left(tails,b)
        if j==len(tails): tails.append(b); idx.append(n)
        else: tails[j]=b; idx[j]=n
        back[n]=idx[j-1] if j>0 else None
    out=[]; cur=idx[-1] if idx else None
    while cur is not None:
        out.append(pairs[cur]); cur=back[cur]
    return out[::-1]

if __name__=="__main__":
    K=int(sys.argv[1]) if len(sys.argv)>1 else 5
    AMB=int(sys.argv[2]) if len(sys.argv)>2 else 4
    ro3=open("<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin","rb").read()
    S="<workspace>/work/cps2"
    k68=open(S+"/sfa3_prog.bin","rb").read()
    ms=mips_consts(ro3,CODE0,CODE1); ks=k68_consts(k68)
    print("constantes : MIPS %d | 68K %d   (k=%d)"%(len(ms),len(ks),K))
    km=kmers(ms,K); kk=kmers(ks,K)
    pairs=[]
    uniq=0
    for key,mi in km.items():
        ki=kk.get(key)
        if not ki: continue
        if len(mi)*len(ki) > AMB: continue       # tolerance d'ambiguite (AMB)
        uniq+=1
        for a in mi:
            for b in ki:
                pairs.append((ms[a][0], ks[b][0]))
    print("empreintes rares appariees : %d  ->  %d couples"%(uniq,len(pairs)))
    # EXTRACTION ITERATIVE : les blocs sont REORDONNES, une seule LIS n'en voit qu'un.
    remaining=set(pairs); blocks=[]; rounds=0
    while remaining and rounds < 60:
        rounds+=1
        ch=lis(list(remaining))
        if len(ch)<4: break
        cur=[ch[0]]
        for q in ch[1:]:
            dm=q[0]-cur[-1][0]; dk=q[1]-cur[-1][1]
            if 0<dm<0x8000 and 0<dk<0x4000: cur.append(q)
            else:
                if len(cur)>=4: blocks.append(cur)
                cur=[q]
        if len(cur)>=4: blocks.append(cur)
        remaining -= set(ch)
    print("extraction iterative : %d passes\n"%rounds)
    print("=== blocs colineaires (>=4 points) : %d ==="%len(blocks))
    blocks.sort(key=lambda b:-len(b))
    # COUVERTURE EN UNION : des blocs se chevauchent dans l'espace 68K ; additionner
    # leurs etendues comptait plusieurs fois les memes octets (surcomptage 1,5 a 1,8x).
    _iv=sorted((b[0][1],b[-1][1]) for b in blocks if b[-1][1]>b[0][1])
    _u=[]
    for _a,_b in _iv:
        if _u and _a<=_u[-1][1]: _u[-1]=(_u[-1][0],max(_u[-1][1],_b))
        else: _u.append((_a,_b))
    cov=sum(_b-_a for _a,_b in _u)
    cov_sum=sum(b[-1][1]-b[0][1] for b in blocks)
    for b in blocks[:10]:
        print("  %4d pts   MIPS %07x..%07x   <->   68K %06x..%06x   (x%.1f)"%(
            len(b),b[0][0],b[-1][0],b[0][1],b[-1][1],
            (b[-1][0]-b[0][0])/max(1,(b[-1][1]-b[0][1]))))
    print("\nCOUVERTURE 68K (union, la vraie) : %d o  (%.1f%% de la zone code)"%(cov,100*cov/0x100000))
    print("  [somme brute des blocs : %.1f%% - surcomptage %.1fx du au chevauchement]"%(
        100*cov_sum/0x100000, cov_sum/max(1,cov)))
    # export de la carte
    import json, os
    out=[{"mips":[b[0][0],b[-1][0]],"m68k":[b[0][1],b[-1][1]],"pts":len(b),
          "ratio":round((b[-1][0]-b[0][0])/max(1,(b[-1][1]-b[0][1])),2),
          "points":[[x,y] for x,y in b]} for b in blocks]
    d=os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(d,"map_ro3_sfa3.json"),"w") as f:
        json.dump({"blocks":out,"coverage_bytes":cov,"k":K,"amb":AMB},f,indent=1)
    print("carte exportee -> map_ro3_sfa3.json (%d blocs)"%len(out))
