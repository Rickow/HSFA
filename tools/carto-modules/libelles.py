#!/usr/bin/env python3
"""Libelles des menus (frames de type $0A : {000A, n, n-1, attr, [align], ptr, n x (0x0200 | car|0x80)}, HANDOFF §101)
-> texte. Balayage de toute la section de donnees d'un module ; table des libelles du menu des modes."""
import struct, sys, collections
import commun as C

def decode(b, o):
    t, n, n1 = struct.unpack_from('<3H', b, o)
    if t != 0x0A or not (1 <= n <= 48) or n1 != n - 1: return None
    p = (o + 8 + 3) & ~3
    cs = struct.unpack_from('<%dH' % n, b, p + 4)
    if not all((c & 0xff00) in (0x0200, 0x0000, 0x0100, 0x0300) and (c & 0x80) for c in cs): return None
    s = ''.join(chr(c & 0x7f) if 0x20 <= (c & 0x7f) < 0x7f else '?' for c in cs)
    return s

def scan(mod):
    b = C.load(mod); e = C.header(mod)['code_end']; out = []
    for o in range(e, len(b) - 16, 2):
        if b[o] == 0x0A and b[o+1] == 0:
            s = decode(b, o)
            if s: out.append((o, s))
    return out

if __name__ == "__main__":
    mod = sys.argv[1] if len(sys.argv) > 1 else 'ro9'
    L = scan(mod)
    print(mod, len(L), "libelles")
    for o, s in L: print("  %s  %r" % (C.fe(o), s))
