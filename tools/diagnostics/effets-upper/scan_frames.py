#!/usr/bin/env python3
"""Balayage heuristique des frames type 0 / 2 de l'image d'Upper (prog.bin + ext_c80000) dont un code tombe dans une
plage (defaut 15396-16482 = tuiles e351 des effets de Vega cote PSP). usage : scan_frames.py [lo hi]"""
import sys, struct
exec(open(__file__.replace('scan_frames.py', 'decode_attaches.py')).read().split("if __name__")[0])
lo, hi = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (15396, 16482)
B0, B1 = 0xB04000, 0xB04000 + len(EXT[0xB04000])
zones = [(0x80000, len(IMG))] + [(b, b + len(s)) for b, s in EXT.items() if b == 0xC80000]
res = []
for z0, z1 in zones:
    for a in range(z0, z1 - 16, 2):
        t = w(a)
        if t not in (0, 2): continue
        try:
            p = (a + 6 + 3) & ~3
            pos = l_ech(p)
            if not (B0 <= pos < B1): continue
            if t == 2:
                T, n = w(a + 2), w(a + 4) + 1
                if not (1 <= T <= 128 and 1 <= n <= 64): continue
                cs = [w(p + 4 + 4 * i) for i in range(n)]
            else:
                n = w(a + 2)
                if not (1 <= n <= 64): continue
                cs = [w(p + 4 + 2 * i) for i in range(n)]
            if any(lo <= c <= hi for c in cs): res.append((a, t, n, min(cs), max(cs)))
        except Exception:
            pass
print('%d frames candidates' % len(res))
for a, t, n, mi, ma in res:
    ps2 = a + 0x569CC0 if a < 0x37F508 else a - 0x39B520
    print('frame $%06X (PS2 %08X) type %d n=%d codes %d-%d' % (a, ps2, t, n, mi, ma))
