#!/usr/bin/env python3
"""tuiles_decor.py : pour chaque decor (Upper : 40 numeros $00-$4E ; Hyper : $00-$06), cases des tilemaps completes
(listes -> blocs -> super-tuiles -> codes locaux, format de blocs_tr.py transpose au module : mots '<H', octets dans
l'ordre naturel) ; codes locaux utilises par plan ; presence du CONTENU de ces tuiles dans les memoires d'Hyper
(e546 vue 8x8 / 16x16, conteneur 32x32 e548). -> tuiles_decor.tsv
Lancer avec le python du venv (numpy)."""
import os, sys, csv, struct, hashlib, json
import numpy as np
sys.path.insert(0, "<workspace>/anthology_extract"); sys.path.insert(0, "<workspace>/scripts/untranspile")
from mwo3_codec import decompress
import anthgfx
DIR = "<workspace>/anthology_extract/decompressed"; BASE = 0x1F0000
XD = "<workspace>/work/xdata/X_DATA.BIN"; MAN = "<workspace>/anthology_extract/manifest.csv"
man = {int(r['idx']): (int(r['offset']), int(r['size'])) for r in csv.DictReader(open(MAN))}
def fichier(n):
    o, s = man[n]
    with open(XD, "rb") as f: f.seek(o); return f.read(s)
H = os.path.dirname(os.path.abspath(__file__))
M = {"ro5": dict(type1=0x747EE0, list1=0x747F30, list2=0x7480D4, list3=0x748344, b1=0x69B830, st1=0x69F3B0,
                 b2=0x6CF5F0, b3=0x6EF3F0, add2=0x1C00, ndec=40, decor=353, b32=525),
     "ro9": dict(type1=0x695FF0, list1=0x695FF8, list2=0x696010, list3=0x696048, b1=0x63DA20, st1=0x63DD20,
                 b2=0x640960, b3=0x643C60, add2=0x1000, ndec=4, decor=546, b32=548),
     "ro3": dict(type1=0x67C630, list1=0x67C670, list2=0x67C79C, list3=0x67C9CC, b1=0x5F72B0, st1=0x5FA1B0,
                 b2=0x61F3F0, b3=0x63A9F0, add2=0x1600, ndec=32, decor=256, b32=312)}
D = {m: open(os.path.join(DIR, "%s_usa_prog68k.bin" % m), "rb").read() for m in M}
def w(m, a): return struct.unpack_from('<H', D[m], a - BASE)[0]
def b(m, a): return D[m][a - BASE]
NL = {1: 8, 2: 16, 3: 64}; TB = {2: 0x300, 3: 0xC0}
COMMUNS = {}
def codes(m, dec, communs=None):
    P = M[m]; res = {1: set(), 2: set(), 3: set()}; bl = {1: set(), 2: set(), 3: set()}
    communs = communs or {1: set(), 2: set(), 3: set()}
    t = b(m, P["type1"] + dec)
    a = P["list1"] + w(m, P["list1"] + dec)
    for n in [b(m, a + k) for k in range(8 if t else 4)]:
        bl[1].add(n)
        if n in communs[1]: continue
        ab = P["b1"] + n * 0x80
        for k in range(64):
            st = w(m, ab + 2 * k); s = P["st1"] + st * 0x40
            for j in range(16): res[1].add(w(m, s + 4 * j + 2))
    for L in (2, 3):
        tl = P["list2"] if L == 2 else P["list3"]
        a = tl + w(m, tl + dec)
        nb = 256 if L == 2 else 64; add = P["add2"] if L == 2 else 0
        for n in [b(m, a + k) for k in range(NL[L])]:
            bl[L].add(n)
            if n in communs[L]: continue
            ab = (P["b2"] if L == 2 else P["b3"]) + n * TB[L]
            for k in range(nb): res[L].add((w(m, ab + 2 * k) + add) & 0xFFFF)
    return t, res, bl
mem = {m: bytes(decompress(fichier(M[m]["decor"]))) for m in M}
t32 = {}
for m in M:
    d = {}
    for k, idx, p in anthgfx.tiles(fichier(M[m]["b32"])):
        if k == 2: d[idx] = b"\0vide" if p is None else np.asarray(p, np.uint8).tobytes()
    t32[m] = d
def t8(m, c): return mem[m][32 * c:32 * c + 32]
def t16(m, c): return mem[m][128 * c:128 * c + 128]
S9 = {1: {t8("ro9", c) for c in range(len(mem["ro9"]) // 32)}, 2: {t16("ro9", c) for c in range(len(mem["ro9"]) // 128)},
      3: set(t32["ro9"].values())}
S3 = {1: {t8("ro3", c) for c in range(len(mem["ro3"]) // 32)}, 2: {t16("ro3", c) for c in range(len(mem["ro3"]) // 128)},
      3: set(t32["ro3"].values())}
def get(m, L, c):
    if L == 1: return t8(m, c)
    if L == 2: return t16(m, c)
    return t32[m].get(c)
import collections
for m in ("ro5", "ro9"):
    cnt = {L: collections.Counter() for L in (1, 2, 3)}
    n = M[m]["ndec"]
    for k in range(n):
        _, _, bl = codes(m, 2 * k)
        for L in (1, 2, 3): cnt[L].update(bl[L])
    COMMUNS[m] = {L: {x for x, c in cnt[L].items() if c >= 0.9 * n and n > 4} for L in (1, 2, 3)}
    print(m, "blocs communs a >= 90 %% des decors (exclus) :", {L: sorted(COMMUNS[m][L]) for L in (1, 2, 3)})
out = open(os.path.join(H, "tuiles_decor.tsv"), "w")
out.write("module\tdecor\ttype1\tplan\tcodes\tcode_min\tcode_max\thors_memoire\tcontenus_distincts\tdans_hyper\tpct_hyper\tdans_sfa3\tpct_sfa3\n")
res = {}
for m in ("ro5", "ro9"):
    for k in range(M[m]["ndec"]):
        dec = 2 * k
        t, C, _ = codes(m, dec, COMMUNS[m])
        for L in (1, 2, 3):
            cs = sorted(C[L]); cont = set(); hors = 0
            for c in cs:
                x = get(m, L, c)
                if x is None or len(x) == 0: hors += 1; continue
                cont.add(x)
            vide = {bytes(32), bytes(128), b"\0vide"}
            cont -= vide
            n9 = len(cont & S9[L]); n3 = len(cont & S3[L])
            out.write("%s\t$%02X\t%d\t%d\t%d\t%x\t%x\t%d\t%d\t%d\t%.1f\t%d\t%.1f\n" % (m, dec, t, L, len(cs), cs[0] if cs else 0,
                      cs[-1] if cs else 0, hors, len(cont), n9, 100 * n9 / max(1, len(cont)), n3, 100 * n3 / max(1, len(cont))))
            res[(m, dec, L)] = (len(cont), n9, n3)
out.close()
for m in ("ro5", "ro9"):
    for k in range(M[m]["ndec"]):
        dec = 2 * k
        print("%s $%02X " % (m, dec) + "  ".join("s%d %5d -> Hyper %5.1f%% SFA3 %5.1f%%" % (L, res[(m, dec, L)][0],
              100 * res[(m, dec, L)][1] / max(1, res[(m, dec, L)][0]), 100 * res[(m, dec, L)][2] / max(1, res[(m, dec, L)][0])) for L in (1, 2, 3)))
