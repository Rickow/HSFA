#!/usr/bin/env python3
"""donnees_mortes.py : donnees d'Hyper lues par l'Arcade d'Hyper seul (hors manches, traces/lus_h_*.txt) et JAMAIS lues
dans ro9a (Arcade greffee, VERSUS, attraction : traces/lus_arc*.txt, lus_vs*.txt, lus_attr*.txt). Granularite 256 o.
Adresses donnees en decalage PS2 depuis la fin du code (D = PS2 - $5AF140) et en 68K de ro9a (e7m/ro9a5)."""
import glob
CE = 0x5AF140; S9 = 0x87A000 - CE; SH = 0x8D9000 - CE
def d_ro9a(x):
    if 0xB3000 <= x < 0xB3000 + S9: return x - 0xB3000
    if 0x940000 <= x < 0x940000 + (0xB67200 - 0x87A000): return S9 + (x - 0x940000)
def d_hyper(y):
    if 0x94000 <= y < 0x94000 + SH: return y - 0x94000
    if 0x940000 <= y < 0x940000 + (0xB67200 - 0x8D9000): return SH + (y - 0x940000)
def x_ro9a(d): return 0xB3000 + d if d < S9 else 0x940000 + d - S9
def lit(motifs, f):
    s = set()
    for m in motifs:
        for fn in glob.glob('<workspace>/work/greffe_arcade/traces/' + m):
            for l in open(fn):
                d = f(int(l, 16))
                if d is not None: s.add(d >> 8)
    return s
H = lit(['lus_h_*.txt'], d_hyper); R = lit(['lus_arc*.txt', 'lus_vs*.txt', 'lus_attr*.txt'], d_ro9a)
M = sorted(H - R)
z = []
for b in M:
    if z and b == z[-1][1]: z[-1][1] = b + 1
    else: z.append([b, b + 1])
tot = sum(e - s for s, e in z) * 256
print("lus par l'Arcade d'Hyper (hors manches) : %d Ko ; jamais lus dans ro9a : %d Ko en %d zones" % (len(H) // 4, tot // 1024, len(z)))
for s, e in sorted(z, key=lambda t: t[0] - t[1])[:25]:
    a = x_ro9a(s << 8); print("  ro9a $%06X-$%06X  %6d o  (PS2 $%06X)" % (a, x_ro9a((e << 8)) - 1, (e - s) * 256, CE + (s << 8)))
