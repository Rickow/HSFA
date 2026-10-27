"""Formule arcade écran <-> tilemap : pour une capture (premier passage de mame_fin.lua avec vidage du plan scroll2),
cherche la case (col, ligne) du plan en haut à gauche de l'écran (test : couleur = fonction de l'index de tuile)."""
import os, sys, struct, pickle, numpy as np
from PIL import Image
O = os.path.expanduser("~/.cache/sfa3max/mame_fin/ryu")
rom = pickle.load(open(os.path.expanduser("~/.cache/sfa3max/cps2_sfa3_tiles.pkl"), "rb"))
J = {int(l.split()[0]): l.split() for l in open(O + "/journal.txt")}
def fonction(idx, col):
    m = {}
    for a, c in zip(idx, col):
        if a == 15: continue
        if m.setdefault(a, c) != c: return False
    return True
for n in map(int, sys.argv[1:]):
    d = open(O + "/s2_%03d.bin" % n, "rb").read(); W = struct.unpack(">%dH" % (len(d) // 2), d)
    sh = np.array(Image.open(O + "/snap/sfa3ud/%04d.png" % (n - 1)).convert("RGB"))
    res = []
    for oc in range(64):
        for orow in range(64):
            ok = tot = 0
            for sy in range(8):
                for sx in range(24):
                    c, r = oc + sx, orow + sy
                    e = (r & 0x0f) + ((c & 0x3f) << 4) + ((r & 0x30) << 6)
                    code, attr = W[2 * e], W[2 * e + 1]
                    if 0x10000 + code >= len(rom): continue
                    t = np.frombuffer(rom[0x10000 + code], np.uint8).reshape(16, 16)
                    if attr & 0x20: t = t[:, ::-1]
                    if attr & 0x40: t = t[::-1]
                    if len(set(t.flatten())) < 4: continue
                    blk = sh[sy * 16:sy * 16 + 16, sx * 16:sx * 16 + 16].reshape(-1, 3)
                    tot += 1; ok += fonction(t.flatten(), [tuple(p) for p in blk])
            if tot > 18: res.append((round(ok / tot, 2), oc, orow, tot))
    res.sort(reverse=True); print(J[n][:8], res[:3])
