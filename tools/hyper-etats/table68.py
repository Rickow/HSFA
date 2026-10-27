#!/usr/bin/env python3
"""table68.py adr68 n : lit la table d'aiguillage 68K (mots relatifs) utilisee par 'MOVE.W d(PC,D0.W),D1 ; JMP/JSR d(PC,D1.W)'
qui commence a adr68 (ou la cherche dans les 16 octets suivants) ; affiche cible 68K et va MIPS de la carte"""
import sys, os, bisect
W = "<workspace>/work/mame_ro9"
names = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]
sw = b"".join(open(os.path.join(W, "roms_ro9/sfa3ud", n), "rb").read() for n in names)
img = bytes(x for i in range(0, len(sw), 2) for x in (sw[i + 1], sw[i]))
rows = sorted((int(l.split(" ", 2)[0], 16), int(l.split(" ", 2)[1], 16)) for l in open(os.path.join(W, "carte_image.txt")))
keys = [r[0] for r in rows]
w = lambda a: int.from_bytes(img[a:a + 2], "big")
a = int(sys.argv[1], 16); n = int(sys.argv[2])
for p in range(a, a + 24, 2):
    if w(p) in (0x4efb, 0x4ebb):                         # JMP/JSR d8(PC,Dn.W)
        ext = w(p + 2); d8 = ext & 0xff; d8 = d8 - 256 if d8 > 127 else d8
        base = p + 2 + d8
        print("aiguillage 68K en $%06x, table $%06x" % (p, base))
        for k in range(n):
            off = w(base + 2 * k); off = off - 65536 if off > 32767 else off
            t = base + off
            i = bisect.bisect_right(keys, t) - 1
            print("  %2x -> $%06x  mips %06x" % (2 * k, t, rows[i][1] if i >= 0 else 0))
        break
