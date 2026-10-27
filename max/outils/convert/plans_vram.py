"""Plans CPS2 vidés par mame_fin.lua (VIDAGE=1 : s2_NNNN.bin = $914000, s3_NNNN.bin = $918000) -> images d'index
(pens 0-15, 15 = transparent) ; calage capture <-> plan (pixel en haut à gauche de l'écran dans le plan).
Décodage des tuiles : cpsenc.py d'HSFA (région :gfx de MAME, quart 1)."""
import os, sys, struct
import numpy as np
from PIL import Image
sys.path.insert(0, __import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "decors_ws", "reimport"))
import cpsenc
REGION = __import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "decors_ws", "gfx", "gfx_region.bin")   # région :gfx de MAME au format cpsenc (validée par HSFA)
_R = None


def region():
    global _R
    if _R is None: _R = open(REGION, "rb").read()
    return _R


def index_case(plan, c, r):
    if plan == 2: return (r & 0x0F) + ((c & 0x3F) << 4) + ((r & 0x30) << 6)
    return (r & 0x07) + ((c & 0x3F) << 3) + ((r & 0x38) << 6)


def plan_image(dump, plan):
    """vidage 16 Ko -> tableau (64·ts, 64·ts) de pens"""
    W = struct.unpack(">%dH" % (len(dump) // 2), dump); ts = cpsenc.TS[plan]
    img = np.full((64 * ts, 64 * ts), 15, np.uint8)
    for r in range(64):
        for c in range(64):
            e = index_case(plan, c, r); code, attr = W[2 * e], W[2 * e + 1]
            t = cpsenc.flip(cpsenc.decode_tile(region(), plan, code), attr & 0x20, attr & 0x40)
            img[r * ts:(r + 1) * ts, c * ts:(c + 1) * ts] = t
    return img


def fonction(idx, col):
    m = {}
    for a, c in zip(idx, col):
        if a == 15: continue
        if m.setdefault(a, c) != c: return False
    return True


def caler(img, sh, y0=0, y1=128, pas=16):
    """meilleur (x, y) du plan tel que la bande [y0, y1) de la capture soit une fonction des pens du plan"""
    H, Wd = img.shape; best = []
    cap = sh[y0:y1].reshape(-1, 3); cap = [tuple(p) for p in cap]
    for y in range(0, H, pas):
        for x in range(0, Wd, pas):
            ys = (np.arange(y0, y1) + y) % H; xs = (np.arange(384) + x) % Wd
            w = img[np.ix_(ys, xs)].reshape(-1)
            opaque = (w != 15).sum()
            if opaque < 0.5 * w.size: continue
            if fonction(w, cap): best.append((int(opaque), x, y))
    return sorted(best, reverse=True)[:5]


if __name__ == "__main__":
    D = os.path.expanduser(sys.argv[1]); n = int(sys.argv[2]); plan = int(sys.argv[3])
    img = plan_image(open(os.path.join(D, "s%d_%04d.bin" % (plan, n)), "rb").read(), plan)
    Image.fromarray((img * 16).astype(np.uint8)).save(os.path.join(D, "plan%d_%04d.png" % (plan, n)))
    if len(sys.argv) > 4:
        sh = np.array(Image.open(os.path.join(D, "snap/sfa3ud/%04d.png" % n)).convert("RGB"))
        print(caler(img, sh, int(sys.argv[4]), int(sys.argv[5])))


def score_majoritaire(w, cap):
    """part des pixels opaques dont la couleur est la couleur majoritaire de leur pen (tolère sprites / texte)"""
    m = w != 15
    if m.sum() == 0: return 0.0
    cle = (w[m].astype(np.int64) << 24) | cap[m]
    u, n = np.unique(cle, return_counts=True)
    pen = u >> 24; ordre = np.lexsort((-n, pen)); premier = np.r_[True, pen[ordre][1:] != pen[ordre][:-1]]
    return n[ordre][premier].sum() / m.sum()


def caler_tolerant(img, sh, y0=0, y1=128, pas=16, x_pas=None):
    H, Wd = img.shape
    c = sh[y0:y1].astype(np.int64); cap = (c[..., 0] << 16) | (c[..., 1] << 8) | c[..., 2]
    res = []
    for y in range(0, H, pas):
        ys = (np.arange(y0, y1) + y) % H
        for x in range(0, Wd, x_pas or pas):
            xs = (np.arange(384) + x) % Wd
            w = img[np.ix_(ys, xs)]
            if (w != 15).mean() < 0.5: continue
            res.append((round(score_majoritaire(w, cap), 3), x, y))
    return sorted(res, reverse=True)[:5]
