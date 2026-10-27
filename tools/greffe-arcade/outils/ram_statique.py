#!/usr/bin/env python3
"""Acces STATIQUES a la RAM de travail ($FF0000-$FFFFFF) d'un module :
  - par A5 (methode vars_a5.a5_access : lw 0x1114 puis load/store d(base)) -> octets [d, d+taille) ;
  - par constante absolue (lui RAM_HI.. ; load/store off(r) ou addiu/ori -> pointeur) sur TOUT le code
    (68K recompile, code C du portage, natifs).
Sortie : ram_statique_<mod>.pkl {'a5': {adr: set(va)}, 'abs': {adr: set(va)}, 'ptr': {adr: set(va)}} (adresses CPS2)."""
import os, sys, pickle, collections
os.environ["GRAIN"] = "routine"
sys.path.insert(0, "<workspace>/work/carto_ro9")
import commun as C
from vars_a5 import a5_access
G = "<workspace>/work/greffe_arcade"
TAILLE = {'lb': 1, 'lbu': 1, 'sb': 1, 'lh': 2, 'lhu': 2, 'sh': 2, 'lw': 4, 'sw': 4, 'lwu': 4, 'ld': 8, 'sd': 8, 'lq': 16, 'sq': 16}

def statique(mod):
    R = C.ram_base(mod)
    a5 = collections.defaultdict(set); ab = collections.defaultdict(set); ptr = collections.defaultdict(set)
    for va, (d, m) in a5_access(mod).items():
        base = (0xFF8000 + (d - 0x10000 if d >= 0x8000 else d)) & 0xFFFFFF
        for k in range(TAILLE.get(m, 1)): a5[(base + k) & 0xFFFFFF].add(va)
    L = C.instrs(mod); lu = {}
    for x in L:
        if x.m == 'lui': lu[x.rt] = x.imm << 16; continue
        if x.m in TAILLE and x.rs in lu:
            v = (lu[x.rs] + x.simm) & 0xffffffff
            if R <= v < R + 0x10000:
                for k in range(TAILLE[x.m]): ab[0xFF0000 + v - R + k].add(x.va)
        elif x.m in ('addiu', 'ori') and x.rs in lu:
            v = (lu[x.rs] + (x.simm if x.m == 'addiu' else x.imm)) & 0xffffffff
            if R <= v < R + 0x10000: ptr[0xFF0000 + v - R].add(x.va)
        d = x.rt if x.m in ('lb','lbu','lh','lhu','lw','ld','lq','andi','lui','ori','addiu','daddiu','xori','slti','sltiu') else (x.rd if x.op == 0 else None)
        if d is not None and x.m != 'lui': lu.pop(d, None)
        if x.m in ('jal', 'jalr', 'jr', 'j'): pass
    return dict(a5=dict(a5), abs=dict(ab), ptr=dict(ptr))

if __name__ == "__main__":
    for mod in sys.argv[1:] or ['ro9', 'ro5']:
        S = statique(mod)
        pickle.dump(S, open(os.path.join(G, "donnees", "ram_statique_%s.pkl" % mod), "wb"))
        print("%s : octets A5 %d, octets absolus %d, pointeurs %d" % (mod, len(S['a5']), len(S['abs']), len(S['ptr'])))
