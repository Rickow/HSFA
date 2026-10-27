#!/usr/bin/env python3
"""gfx_cmp.py : memoires de decor (MWo3) et conteneurs 32x32 des modules ro3/ro5/ro9 (X_DATA via manifest) :
tailles, inclusion d'Upper (e353 / e525) dans Hyper (e546 / e548), par tuile 8x8 et 16x16 et par position."""
import os, sys, csv, hashlib
import numpy as np
sys.path.insert(0, "<workspace>/anthology_extract"); sys.path.insert(0, "<workspace>/scripts/untranspile")
from mwo3_codec import decompress
import anthgfx
XD = "<workspace>/work/xdata/X_DATA.BIN"; MAN = "<workspace>/anthology_extract/manifest.csv"
man = {int(r['idx']): (int(r['offset']), int(r['size'])) for r in csv.DictReader(open(MAN))}
def fichier(n):
    o, s = man[n]
    with open(XD, "rb") as f: f.seek(o); return f.read(s)
H = os.path.dirname(os.path.abspath(__file__))
out = open(os.path.join(H, "gfx_cmp.txt"), "w")
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); out.write(s + "\n")
dec = {m: bytes(decompress(fichier(n))) for m, n in (('ro3', 256), ('ro5', 353), ('ro9', 546))}
for m, b in dec.items(): P("decor %s : %d o decompresses, %d tuiles 8x8 (32 o), %d tuiles 16x16 (128 o)" % (m, len(b), len(b)//32, len(b)//128))
# meme position ?
for a, b in (('ro3', 'ro5'), ('ro5', 'ro9'), ('ro3', 'ro9')):
    x, y = dec[a], dec[b]; n = min(len(x), len(y)) // 128
    same = sum(1 for k in range(n) if x[128*k:128*k+128] == y[128*k:128*k+128])
    # prefixe identique
    p = 0
    while p < n and x[128*p:128*p+128] == y[128*p:128*p+128]: p += 1
    P("%s vs %s : 16x16 a la meme position %d / %d ; prefixe identique %d tuiles 16x16 (%d o)" % (a, b, same, n, p, 128*p))
def tiles(b, sz): return [b[k:k+sz] for k in range(0, len(b) - sz + 1, sz)]
for sz, nom in ((32, "8x8"), (128, "16x16")):
    S9 = set(tiles(dec['ro9'], sz))
    for a in ('ro3', 'ro5'):
        T = tiles(dec[a], sz); u = set(T)
        P("%s : tuiles %s distinctes %d ; presentes dans ro9 %d (%.1f %%)" % (a, nom, len(u), len(u & S9), 100 * len(u & S9) / len(u)))
# conteneurs 32x32
for m, n in (('ro3', 312), ('ro5', 525), ('ro9', 548)):
    buf = fichier(n); recs = anthgfx.records(buf)
    P("32x32 %s e%d : %d o, enregistrements %s" % (m, n, len(buf), [(r[0], r[1], r[2]) for r in recs]))
T32 = {}
for m, n in (('ro3', 312), ('ro5', 525), ('ro9', 548)):
    d = {}
    for k, idx, p in anthgfx.tiles(fichier(n)):
        if k == 2: d[idx] = None if p is None else hashlib.md5(np.asarray(p, np.uint8).tobytes()).hexdigest()
    T32[m] = d
for a, b in (('ro3', 'ro5'), ('ro5', 'ro9')):
    x, y = T32[a], T32[b]
    same = sum(1 for k in x if k in y and x[k] == y[k]); vb = set(y.values())
    P("32x32 %s (%d) vs %s (%d) : meme indice et contenu %d ; contenu present ailleurs %d" % (a, len(x), b, len(y), same, sum(1 for v in x.values() if v in vb)))
out.close()
