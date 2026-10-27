"""Rendu hors ligne 448x224, PLAN PAR PLAN, d'une image capturee (FRM0) avec la camera deplacee verticalement de dy px
(registres de defilement Y des 3 plans + dy) : montre ce que le jeu afficherait si la camera montait/descendait au-dela
de la course enregistree (contenu des tilemaps en VRAM). Compare deux essais (temoin / injection) plan par plan.
Usage : rendu_plans_dy.py <frm temoin> <plans temoin> <frm essai> <plans essai> <etiquette> dy [dy...]"""
import sys, numpy as np
sys.path[:0] = ["<workspace>/work/decors_ws/py", "<workspace>/work/decors_ws/reimport"]
from recio import read_rec
import cpsgfx as G
from PIL import Image
OFF = {1: 0, 2: 0x400000, 3: 0xA00000}
G.phys_code = lambda l, c: OFF[l] // G.LAYERS[l]["tbytes"] + (c & 0x3fff if l == 3 else c)


def rend(frm, plans, dy, tag):
    G.GFX = np.fromfile(plans, np.uint8); G.tile.cache_clear()
    f = [f for f in read_rec(frm) if f.t == tag][0]
    f.A = f.A.copy()
    for o in (0x0e, 0x12, 0x16): f.A[o // 2] = (int(f.A[o // 2]) + dy) & 0xffff
    out = {}
    for L in (1, 2, 3):
        im = np.zeros((224, 448, 3), np.uint8)
        Lg = G.LAYERS[L]; ts = Lg["ts"]; W = G.TM * ts
        pen, pal = G.tilemap_pens(f, L)
        sx = np.arange(448) - 32; sy = np.arange(224)
        ty = (sy + 16 + f.reg(Lg["ry"])) % W
        rs = np.zeros(224, np.int64)
        if L == 2 and (f.reg(0x22) & 1):
            oo = (((f.reg(0x08) << 8) & 0xfff800) - 0x900000) // 2
            v = f.vram[oo + ((sy + 16 + f.reg(0x20)) & 0x3ff)]; rs = np.where(v >= 0x8000, v - 0x10000, v)
        tx = (sx[None, :] + 64 + f.reg(Lg["rx"]) + rs[:, None]) % W
        p = pen[ty[:, None], tx]; q = pal[ty[:, None], tx]; m = p != 15
        im[m] = f.pal[q.astype(np.int64) * 16 + p][m]
        out[L] = (im, q, m)
    return out


if __name__ == "__main__":
    ft, pt, fe, pe, tag = sys.argv[1:6]
    for dy in [int(x) for x in sys.argv[6:]]:
        a = rend(ft, pt, dy, int(tag)); b = rend(fe, pe, dy, int(tag))
        for L in (1, 2, 3):
            d = (a[L][0] != b[L][0]).any(2); d[:, 416:] = False; d[:, :32] = False
            y, x = np.nonzero(d)
            pals = sorted({int(v) for v in b[L][1][d]}) if d.any() else []
            print("dy %+d scroll%d : %d px differents dans la vue 4:3 %s palettes (essai) %s" % (
                dy, L, int(d.sum()), ("x %d-%d y %d-%d" % (x.min(), x.max(), y.min(), y.max())) if d.any() else "",
                " ".join("%02X" % p for p in pals)))
