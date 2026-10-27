#!/usr/bin/env python3
"""Correspondance MIPS(recompile) <-> 68K(original) par SIGNATURE DE CONSTANTES.

Principe : la recompilation preserve les valeurs immediates. Une fenetre de code MIPS
utilisant une suite de constantes peu frequentes doit retrouver les MEMES constantes,
dans le meme ordre, dans la fonction 68K correspondante.
Cela donne la carte de correspondance SANS ecrire le traducteur.
"""
import sys, struct, collections
sys.path.insert(0, "<workspace>/scripts/untranspile")
from mips import CODE0, CODE1
from mips import decode

def mips_consts(buf, start, end, minv=0x100):
    """-> [(va, imm)] des immediats 'interessants' (assez grands pour etre distinctifs)."""
    out=[]
    for ins in decode(buf, start, end):
        if ins.m in ('addiu','addi','ori','andi','xori','slti','sltiu','lui'):
            v=ins.imm
            if minv <= v <= 0xfffe and v not in (0x7000,0xffff):
                out.append((ins.va, v))
    return out

def m68k_words(buf):
    """le 68K est big-endian 16 bits : toute constante immediate est un mot aligne."""
    n=len(buf)//2
    return struct.unpack('>%dH'%n, buf[:n*2])

def build_index(words, minv=0x100):
    idx=collections.defaultdict(list)
    for i,w in enumerate(words):
        if minv <= w <= 0xfffe: idx[w].append(i)
    return idx

def match(mips_seq, idx, k=4, span=240):
    """cherche k constantes consecutives du MIPS, dans l'ordre, proches dans le 68K."""
    res=[]
    for i in range(len(mips_seq)-k+1):
        vals=[v for _,v in mips_seq[i:i+k]]
        # on exige des valeurs distinctes et pas trop communes
        if len(set(vals))<k: continue
        cand=idx.get(vals[0],[])
        if not cand or len(cand)>400: continue
        for c in cand:
            pos=c; ok=True
            for v in vals[1:]:
                nxt=[p for p in idx.get(v,[]) if pos < p <= pos+span]
                if not nxt: ok=False; break
                pos=nxt[0]
            if ok:
                res.append((mips_seq[i][0], c*2, vals))
                break
    return res

if __name__=="__main__":
    ro3=open("<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin","rb").read()
    S="<workspace>/work/cps2"
    k68=open(S+"/sfa3_prog.bin","rb").read()
    words=m68k_words(k68); idx=build_index(words)
    print("68K : %d mots, %d constantes distinctes indexees"%(len(words),len(idx)))
    seq=mips_consts(ro3, CODE0,CODE1)
    print("MIPS: %d immediats extraits\n"%len(seq))
    hits=match(seq, idx, k=4)
    print("=== correspondances (4 constantes consecutives, meme ordre) : %d ==="%len(hits))
    for mva,kva,vals in hits[:25]:
        print("  MIPS %08x  <->  68K %06x   %s"%(mva,kva," ".join("%04x"%v for v in vals)))
