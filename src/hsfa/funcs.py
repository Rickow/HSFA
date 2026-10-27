#!/usr/bin/env python3
"""Decoupage en fonctions des deux cotes + appariement par signature de constantes.

MIPS : une fonction se termine par 'jr ra' (+ delay slot).
68K  : une fonction se termine par RTS (0x4E75) / RTE (0x4E73).
La signature d'une fonction = l'ensemble de ses constantes immediates distinctives.
Les immediats survivant a la recompilation, deux fonctions jumelles partagent
une grande partie de cet ensemble.
"""
import sys, struct, collections
sys.path.insert(0, "<workspace>/scripts/untranspile")
from mips import CODE0, CODE1
from mips import decode

def mips_functions_by_calls(buf, start, end, runtime_base=0x1f0000):
    """Decoupage FIABLE : les cibles de 'jal' sont par definition de vrais debuts
    de fonction. Le decoupage par 'jr ra' sur-decoupe massivement (9219 contre 2788),
    parce qu'une fonction 68K a souvent plusieurs points de sortie."""
    from mips import decode
    tg=set()
    for ins in decode(buf,start,end):
        if ins.m=='jal':
            o=ins.tgt-runtime_base
            if start<=o<end: tg.add(o)
    starts=sorted(tg)
    out=[]
    for i,a in enumerate(starts):
        b=starts[i+1] if i+1<len(starts) else end
        consts=set()
        for ins in decode(buf,a,b):
            v=None
            if ins.m in ('addiu','addi','ori','andi','xori','slti','sltiu','lui'):
                v=ins.imm
            elif ins.m in ('lb','lh','lw','lbu','lhu','sb','sh','sw','ld','sd'):
                if not (0x1000 <= ins.imm <= 0x11ff): v=ins.imm
            if v is not None and 0x100<=v<=0xfffe and v!=0x7000: consts.add(v)
        out.append((a,b,consts))
    return out

def mips_functions(buf, start, end, minsz=12):
    """-> [(va_debut, va_fin, set(constantes))]"""
    out=[]; cur=start; consts=set()
    for ins in decode(buf, start, end):
        v=None
        if ins.m in ('addiu','addi','ori','andi','xori','slti','sltiu','lui'):
            v=ins.imm
        elif ins.m in ('lb','lh','lw','lbu','lhu','sb','sh','sw','ld','sd'):
            # le DEPLACEMENT est aussi une constante du 68K d'origine
            # (sauf les acces au fichier de registres, qui sont de la plomberie)
            if not (0x1000 <= ins.imm <= 0x11ff): v=ins.imm
        if v is not None and 0x100 <= v <= 0xfffe and v != 0x7000: consts.add(v)
        if ins.m=='jr' and ins.rs==31:          # jr ra
            fin=ins.va+8
            if (fin-cur)//4 >= minsz: out.append((cur,fin,consts))
            cur=fin; consts=set()
    return out

def m68k_functions(buf, minsz=12, maxsz=4000):
    """-> [(off_debut, off_fin, set(constantes))] ; delimite par RTS/RTE."""
    n=len(buf)//2
    w=struct.unpack('>%dH'%n, buf[:n*2])
    out=[]; cur=0; consts=set()
    for i,x in enumerate(w):
        if 0x100 <= x <= 0xfffe: consts.add(x)
        if x in (0x4e75,0x4e73):                # RTS / RTE
            fin=(i+1)*2
            ln=(fin-cur)//2
            if minsz <= ln <= maxsz: out.append((cur,fin,consts))
            cur=fin; consts=set()
    return out

def jaccard(a,b):
    if not a or not b: return 0.0
    return len(a&b)/len(a|b)

if __name__=="__main__":
    ro3=open("<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin","rb").read()
    S="<workspace>/work/cps2"
    k68=open(S+"/sfa3_prog.bin","rb").read()
    mf=mips_functions(ro3, CODE0,CODE1)
    kf=m68k_functions(k68)
    print("fonctions MIPS : %d   |   fonctions 68K : %d"%(len(mf),len(kf)))
    # index inverse : constante -> fonctions 68K qui la contiennent
    inv=collections.defaultdict(set)
    for i,(a,b,c) in enumerate(kf):
        for v in c:
            if len(inv[v])<3000: inv[v].add(i)
    print("index : %d constantes\n"%len(inv))
    RICHE=[f for f in mf if len(f[2])>=6]
    print("fonctions MIPS a signature riche (>=6 constantes) : %d\n"%len(RICHE))
    pairs=[]
    for (a,b,cs) in RICHE:
        cand=collections.Counter()
        for v in cs:
            for i in inv.get(v,()): cand[i]+=1
        if not cand: continue
        i,sc = cand.most_common(1)[0]
        if sc<5: continue
        j=jaccard(cs, kf[i][2])
        if j>=0.5: pairs.append((j,a,b,kf[i][0],kf[i][1],sc,len(cs)))
    pairs.sort(reverse=True)
    print("=== appariements (Jaccard >= 0.5) : %d ==="%len(pairs))
    for j,a,b,ka,kb,sc,nc in pairs[:20]:
        print("  J=%.2f  MIPS %07x-%07x (%4d o)  <->  68K %06x-%06x (%4d o)  [%d/%d const]"%(
            j,a,b,b-a,ka,kb,kb-ka,sc,nc))
