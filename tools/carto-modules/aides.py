#!/usr/bin/env python3
"""Aides du recompilateur (movem_push, movem_pop, andi_ccr, abcd) de chaque module, par empreinte des mots MIPS
d'ro5 (0x22B00, 0x22E60, 0x231C0, 0x234A0 ; CARTE-ro9 §1.1) et d'ro3 (0x380360...), adresses masquees."""
import sys, struct
sys.path.insert(0, '.')
import commun as C
REF = {'ro5': [0x22b00, 0x22e60, 0x231c0, 0x234a0], 'ro3': [0x380360, 0x3806c0, 0x380a20, 0x380d00]}
NOMS = ['movem_push', 'movem_pop', 'andi_ccr', 'abcd']
N = 40
def masq(w):
    op = w >> 26
    if op in (2, 3): return w & 0xfc000000
    if op == 0x0f: return w & 0xffff0000
    return w
def sig(b, o): return tuple(masq(x) for x in struct.unpack_from('<%dI' % N, b, o))
sigs = {}
for r, L in REF.items():
    b = C.load(r)
    for k, a in enumerate(L): sigs.setdefault(sig(b, a), set()).add(NOMS[k])
for m in sys.argv[1:] or ['ro1','ro2','ro3','ro4','ro5','ro6','ro7','ro8','ro9']:
    b = C.load(m); e = C.header(m)['code_end']; res = []
    for o in range(0x40, e - 4 * N, 4):
        s = sig(b, o)
        if s in sigs: res.append('%s fichier %#x (exec %#x)' % ('/'.join(sorted(sigs[s])), o, o + 0x1F0000))
    print(m, ' ; '.join(res))
