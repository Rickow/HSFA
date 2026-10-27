#!/usr/bin/env python3
"""Lecture seule d'un ISO9660 : repertoire racine -> (nom, lba, taille)."""
import struct, sys
def racine(p):
    f = open(p, 'rb'); f.seek(16 * 2048); pvd = f.read(2048)
    lba, size = struct.unpack_from('<I', pvd, 156 + 2)[0], struct.unpack_from('<I', pvd, 156 + 10)[0]
    f.seek(lba * 2048); d = f.read(size); out = {}; o = 0
    while o < len(d):
        n = d[o]
        if n == 0: o = (o // 2048 + 1) * 2048; continue
        l, s = struct.unpack_from('<I', d, o + 2)[0], struct.unpack_from('<I', d, o + 10)[0]
        nm = d[o + 33:o + 33 + d[o + 32]].decode('latin1').split(';')[0]
        out[nm] = (l * 2048, s); o += n
    return out
if __name__ == '__main__':
    for k, v in racine(sys.argv[1]).items(): print(k, hex(v[0]), v[1])
