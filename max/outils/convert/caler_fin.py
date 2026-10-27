"""Calage des scènes : captures arcade (MAME, mame_fin.lua) <-> fenêtres de la carte PSP (endXX_e.pac, entrée 0).
Pour chaque capture : position (col, ligne) de la carte PSP dont le contenu ressemble le plus à la bande d'image du haut
de l'écran (échantillonnage tous les 8 px, pixels PSP transparents ignorés). Python de l'environnement HSFA (numpy).
Usage : python caler_fin.py <dossier capture> <XX PSP> [y0 y1 de la bande, défaut 0 136]"""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plpac import split
import fins_max as F


def carte_rgba(n):
    E = split(open(os.path.join(F.SRC, "end%s_e.pac" % n), "rb").read()); tex = F.textures(E); v = F.carte(E)
    H = len(v) // 64
    M = np.zeros((H * 16, 64 * 16, 4), np.uint8)
    for i, x in enumerate(v):
        if x == F.VIDE or ((x >> 8) & 0xFF) not in tex: continue
        M[(i // 64) * 16:(i // 64) * 16 + 16, (i % 64) * 16:(i % 64) * 16 + 16] = np.array(F.rendre(tex, v, (i % 64, i // 64, 1, 1)))
    return M


def caler(M, sh, y0=0, y1=136):
    Ms = M[::8, ::8].astype(int); Mw = np.concatenate([Ms, Ms[:, :48]], axis=1)
    s = sh[y0:y1:8, 0:384:8]; h = s.shape[0]
    best = (1e9, None)
    for py in range(0, Ms.shape[0] - h, 2):
        for px in range(0, Ms.shape[1], 2):
            w = Mw[py:py + h, px:px + 48]; a = w[..., 3] > 0; n = a.sum()
            if n < 0.6 * a.size: continue
            d = np.abs(w[..., :3] - s)[a].sum() / n
            if d < best[0]: best = (d, (px // 2, py // 2 - y0 // 16))
    return best


if __name__ == "__main__":
    D, n = sys.argv[1], sys.argv[2]
    y0, y1 = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 136)
    M = carte_rgba(n)
    for l in open(os.path.join(D, "journal.txt")):
        p = l.split()
        if len(p) < 8: continue
        sh = np.array(Image.open(os.path.join(D, "snap/sfa3ud/%s.png" % p[0])).convert("RGB")).astype(int)
        if sh[y0:y1].mean() < 12: continue                       # écran noir (fondu)
        d, pos = caler(M, sh, y0, y1)
        print("%s %s %s -> PSP %s écart %.0f" % (p[0], p[1], " ".join(p[2:8]), pos, d))
