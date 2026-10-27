"""Relocations de l'EBOOT (.rel.data/.rel.rodata) -> ensemble des mots-pointeurs en données."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

import struct
b = open(paths.eboot(),"rb").read(); img = b[0x74:]
TEXT_END = 0x1f835c
def sections():
    shoff, = struct.unpack_from("<I", b, 0x20); es, n, si = struct.unpack_from("<HHH", b, 0x2E)
    S = [struct.unpack_from("<10I", b, shoff + i*es) for i in range(n)]; so = S[si][4]
    return {b[so+s[0]:b.index(b"\0", so+s[0])].decode(): s for s in S}
SEC = sections()
def u32(va): return struct.unpack_from("<I", img, va)[0]
def pointer_words():
    """{va_du_mot: cible} pour les relocations R_MIPS_32 des données."""
    out = {}
    for name in (".rel.data", ".rel.rodata"):
        s = SEC[name]; off, size = s[4], s[5]
        for k in range(size // 8):
            r_off, r_info = struct.unpack_from("<II", b, off + 8*k)
            if r_info & 0xFF == 2: out[r_off] = u32(r_off)
    return out
