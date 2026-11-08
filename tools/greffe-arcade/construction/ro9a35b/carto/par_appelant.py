#!/usr/bin/env python3
"""Homologue d'une routine par ses APPELANTS : sites jal / jalr-constante vers T dans le module source ->
instruction homologue dans la cible (alignement) -> cible appelee la. Vote."""
import os, sys, collections
os.environ.setdefault("GRAIN", "routine")
import commun as C, homologue as H

def call_sites(mod, T):
    out = []; lu = {}
    for x in C.instrs(mod):
        if x.m == 'lui': lu[x.rt] = x.imm << 16
        elif x.m == 'addiu' and x.rs in lu: lu[x.rt] = (lu[x.rs] + x.simm) & 0xffffffff
        if x.m == 'jal' and x.tgt == T + C.BASE: out.append(x.va)
        if x.m == 'jalr' and lu.get(x.rs) == T + C.BASE: out.append(x.va)
    return out

def target_at(mod, va):
    L = C.seg(mod, va - 0x20, va + 4); lu = {}
    for x in L:
        if x.m == 'lui': lu[x.rt] = x.imm << 16
        elif x.m == 'addiu' and x.rs in lu: lu[x.rt] = (lu[x.rs] + x.simm) & 0xffffffff
        if x.va == va:
            if x.m == 'jal': return x.tgt - C.BASE
            if x.m == 'jalr' and x.rs in lu: return lu[x.rs] - C.BASE
    return None

def par_appelant(src, T, dst):
    votes = collections.Counter(); det = []
    for s in call_sites(src, T):
        r = H.homologue(src, s, dst)
        t = target_at(dst, r['va_dst']) if r and r['va_dst'] is not None else None
        det.append((s, r and r['classe'], t))
        if t is not None: votes[t] += 1
    return votes, det

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    for x in sys.argv[3:]:
        v, d = par_appelant(src, int(x, 16), dst)
        print("%s %s -> %s : %s   (%d sites appelants)" % (src, x, dst, ', '.join('%s x%d' % (C.fe(k), n) for k, n in v.most_common(3)), len(d)))
