#!/usr/bin/env python3
"""Appariement MIPS<->68K par ALIGNEMENT ORDONNE des constantes.

Valide sur l'ancre MIPS 0x201fa8 <-> 68K 0x9350 : 40/40 constantes alignees dans
l'ordre, le 68K montrant `1b40 xxxx` = MOVE.B Dn,(d16,A5) avec exactement les
memes offsets. L'ordre est un critere bien plus sur que le simple recouvrement.
"""
import sys, struct, collections, difflib
sys.path.insert(0, "<workspace>/scripts/untranspile")
from mips import CODE0, CODE1
from mips import decode
from funcs import mips_functions_by_calls as mips_functions, m68k_functions

def mips_const_seq(buf,a,b):
    out=[]
    for ins in decode(buf,a,b):
        v=None
        if ins.m in ('addiu','addi','ori','andi','xori','slti','sltiu','lui'):
            v=ins.imm
        elif ins.m in ('lb','lh','lw','lbu','lhu','sb','sh','sw','ld','sd'):
            if not (0x1000 <= ins.imm <= 0x11ff): v=ins.imm
        if v is not None and 0x100<=v<=0xfffe and v!=0x7000: out.append(v)
    return out

def k_const_seq(buf,a,b):
    n=(b-a)//2
    return [x for x in struct.unpack('>%dH'%n, buf[a:a+n*2]) if 0x100<=x<=0xfffe]

def ordered_ratio(m,k):
    if not m: return 0.0,0
    sm=difflib.SequenceMatcher(None,m,k,autojunk=False)
    tot=sum(bl.size for bl in sm.get_matching_blocks())
    return tot/len(m), tot

if __name__=="__main__":
    ro3=open("<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin","rb").read()
    S="<workspace>/work/cps2"
    k68=open(S+"/sfa3_prog.bin","rb").read()
    mf=mips_functions(ro3,CODE0,CODE1)
    kf=m68k_functions(k68)
    inv=collections.defaultdict(set)
    for i,(a,b,c) in enumerate(kf):
        for v in c:
            if len(inv[v])<2500: inv[v].add(i)
    rich=[f for f in mf if len(f[2])>=6]
    print("MIPS %d fn (%d riches >=8 const) | 68K %d fn\n"%(len(mf),len(rich),len(kf)))
    pairs=[]
    for (a,b,cs) in rich:
        cand=collections.Counter()
        for v in cs:
            for i in inv.get(v,()): cand[i]+=1
        best=None
        ms=mips_const_seq(ro3,a,b)
        for i,_ in cand.most_common(6):
            ks=k_const_seq(k68,kf[i][0],kf[i][1])
            r,t=ordered_ratio(ms,ks)
            if best is None or r>best[0]: best=(r,t,i)
        if best and best[0]>=0.85 and best[1]>=6:
            r,t,i=best
            pairs.append((r,t,a,b,kf[i][0],kf[i][1]))
    pairs.sort(key=lambda x:(-x[0],-x[1]))
    print("=== appariements (alignement ordonne >= 85%%, >=8 const) : %d ===\n"%len(pairs))
    for r,t,a,b,ka,kb in pairs[:26]:
        print("  %3.0f%%  %2d const   MIPS %07x (%5d o)  <->  68K %06x (%4d o)   ratio taille %4.1fx"%(
            100*r,t,a,b-a,ka,kb-ka,(b-a)/max(1,kb-ka)))
