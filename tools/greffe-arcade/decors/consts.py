#!/usr/bin/env python3
"""consts.py : constantes 32 bits formees par lui + addiu/ori dans le code MIPS (ro5, ro9) -> {valeur: [va]}
Usage en module : C(mod) ; en ligne : consts.py MOD VAL... (exec. hexa) -> sites + routine"""
import os, sys, collections, functools
os.environ.setdefault("GRAIN", "routine")
sys.path.insert(0, "<workspace>/work/carto_ro9")
import commun as K
@functools.lru_cache(None)
def C(mod):
    L = K.instrs(mod); s0 = K.start68k(mod) or 0
    d = collections.defaultdict(list); lu = {}
    for x in L:
        if x.m == 'lui': lu[x.rt] = (x.imm << 16, x.va); continue
        if x.m in ('addiu', 'ori') and x.rs in lu and x.va - lu[x.rs][1] < 0x80:
            v = (lu[x.rs][0] + (x.simm if x.m == 'addiu' else x.imm)) & 0xffffffff
            d[v].append(x.va)
        elif x.m in ('lw','lh','lhu','lb','lbu','sw','sh','sb') and x.rs in lu and x.va - lu[x.rs][1] < 0x80:
            d[(lu[x.rs][0] + x.simm) & 0xffffffff].append(x.va)
    return d
if __name__ == "__main__":
    mod = sys.argv[1]; d = C(mod)
    for a in sys.argv[2:]:
        v = int(a, 16)
        print("%s %x : %s" % (mod, v, ' '.join("%x(r%x)" % (s, K.func_of(mod, s)[0]) for s in d.get(v, []))))
