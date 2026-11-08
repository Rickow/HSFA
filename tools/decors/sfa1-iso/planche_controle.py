#!/usr/bin/env python3
"""planche_controle.py DONNEES MAME_DIR SORTIE.png : pour chaque décor, SFA1 joué (MAME, capture en combat) | capture
MAME sans HUD ni sprites (vue « centre ») | rendu hors jeu depuis l'ISO aux mêmes registres | différences (rouge)."""
import os, sys, struct
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_mame as M, rendu_sfa1 as RS
D = RS.Donnees(sys.argv[1]); MD = sys.argv[2]
L = []
for s in range(13):
    stg = "%02X" % (2 * s); sn = lambda i: np.asarray(Image.open(os.path.join(MD, "snap", "stg" + stg, "sfa", "%04d.png" % i)).convert("RGB"))
    d = M.lit(os.path.join(MD, "out", "stg%s_dmp.bin" % stg))[2]; A = d["A"]
    rows = M.mots(d["gfx"], A[4], 1024).astype(np.int64)
    r = RS.ecran(D, s, A[8], A[9], A[10], A[11], rows if A[0x11] & 1 else None, A[0x10])
    m = sn(3); dif = np.any(r != m, -1)
    L.append(np.concatenate([sn(0), m, r, np.where(dif[..., None], [255, 0, 0], m // 3).astype(np.uint8)], 1))
g = np.full((len(L) * 232, 4 * 384, 3), 30, np.uint8)
for i, v in enumerate(L): g[i * 232:i * 232 + 224] = v
im = Image.fromarray(g); dr = ImageDraw.Draw(im)
for i in range(13):
    dr.text((4, i * 232 + 2), "$%02X %s" % (2 * i, D.decor(i)["perso"]), fill=(255, 255, 0))
im.save(sys.argv[3])
