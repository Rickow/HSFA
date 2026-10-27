#!/usr/bin/env python3
"""dis68.py CONSTRUCTION ADR68K [N] : desassemble l'image programme 68K construite (constructions/<c>/b9/roms_ro9)."""
import sys, os
G = "<workspace>/work/greffe_arcade"
def image(c):
    d = c if c.startswith('/') else os.path.join(G, 'constructions', c, 'b9', 'roms_ro9', 'sfa3ud')
    img = bytearray()
    for f in ('sz3ud.03c', 'sz3ud.04c', 'sz3.05c', 'sz3.06c', 'sz3.07c', 'sz3.08c', 'sz3.09c', 'sz3.10b'):
        b = open(os.path.join(d, f), 'rb').read()
        img += bytes(x for i in range(0, len(b), 2) for x in (b[i + 1], b[i]))
    return bytes(img)
if __name__ == "__main__":
    import capstone
    img = image(sys.argv[1]); a = int(sys.argv[2], 16); n = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    md = capstone.Cs(capstone.CS_ARCH_M68K, capstone.CS_MODE_BIG_ENDIAN | capstone.CS_MODE_M68K_000)
    for k, i in enumerate(md.disasm(img[a:a + 8 * n], a)):
        if k >= n: break
        print("%06x  %-24s %-8s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
