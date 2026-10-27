#!/usr/bin/env python3
"""Normalise le flot MIPS recompile : les paires (lui 0x7000 ; load/store off(r))
deviennent des acces symboliques SPAD[off]. Le reste est laisse tel quel.
Objectif : faire emerger la grammaire du recompilateur 68K->MIPS."""
import sys, collections
sys.path.insert(0, "<workspace>/scripts/untranspile")
from mips import CODE0, CODE1
from mips import decode, REG, LOADSTORE

# mapping deduit (a affiner par les donnees)
def spad_name(off):
    if 0x1100 <= off <= 0x111c: return "A%d" % ((off-0x1100)//4)
    if 0x1124 <= off <= 0x1140: return "D%d" % ((off-0x1124)//4)
    if off == 0x1150: return "RES"      # dernier resultat (test Z)
    if off == 0x1158: return "NFLG"     # signe
    return "SP%04x" % off

def lift(buf, start, end):
    """-> liste de tokens normalises (str) + l'instruction d'origine."""
    out=[]; lui={}
    for ins in decode(buf, start, end):
        if ins.m == 'lui':
            lui[ins.rt] = ins.imm
            out.append((ins, None))          # marque, peut etre absorbee
            continue
        if ins.m in LOADSTORE.values() and lui.get(ins.rs) == 0x7000:
            off = ins.imm
            kind = 'ld' if ins.m[0]=='l' else 'st'
            w = {'b':'B','h':'W','w':'L'}.get(ins.m[1] if len(ins.m)>1 else 'w','L')
            if ins.m in ('lw','sw'): w='L'
            elif ins.m in ('lh','sh','lhu'): w='W'
            elif ins.m in ('lb','sb','lbu'): w='B'
            elif ins.m in ('ld','sd'): w='Q'
            tok = "%s.%s %s" % (kind, w, spad_name(off))
            # absorbe le lui precedent
            if out and out[-1][1] is None and out[-1][0].m=='lui': out.pop()
            out.append((ins, tok))
            continue
        if ins.m in ('jal','j'):
            out.append((ins, "%s %#x" % (ins.m, ins.tgt))); lui={}
            continue
        if ins.m=='sll' and ins.w==0:
            out.append((ins, "nop")); continue
        out.append((ins, ins.m))
    return out

if __name__ == "__main__":
    f="<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin"
    buf=open(f,'rb').read()
    toks=[t for _,t in lift(buf, CODE0,CODE1) if t]
    print("tokens normalises : %d\n" % len(toks))
    N=int(sys.argv[1]) if len(sys.argv)>1 else 5
    print("=== 22 idiomes les plus frequents (sequences de %d) ===" % N)
    ng=collections.Counter(tuple(toks[i:i+N]) for i in range(len(toks)-N))
    for seq,c in ng.most_common(22):
        print("  %6d x   %s" % (c, "  |  ".join(seq)))
