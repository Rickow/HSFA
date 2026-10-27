"""Sprites des ÉCRANS du PSP (op/select/end…_e.pac) : même conteneur et mêmes en-têtes de frames que les persos, mais
une case = UNE tuile 16x16 (et non 2x2) ; attributs : bit 7 miroir H, bit 6 miroir V, bit 5 toujours posé,
bits 0-4 = palette (relative à une base, cf. rendu)."""
import os, sys
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
from plpac import split
from frames import frames
from maxtile import tiles, decode
from render import palettes
from PIL import Image
class Ecran:
    def __init__(s, path, ti=(0, 1, 2), case32=None):
        E = split(open(path, "rb").read())
        s.g = E[ti[1]][1]; s.T = tiles(s.g); s.F = frames(E[ti[0]][1]); s.P = palettes(E[ti[2]][1]); s._c = {}
        if case32 is None:                     # case 2x2 si l'index max x 4 couvre les tuiles (portraits de victoire)
            m = max((c[0] for f in s.F for c in f["cells"] if c), default=0)
            case32 = m + 1 < len(s.T) and 4 * (m + 1) <= len(s.T) + 3
        s.case32 = case32
    def tile(s, i):
        if i not in s._c: s._c[i] = decode(s.g, s.T[i][0])[0]
        return s._c[i]
    def frame(s, n, base=0, masque=0x1F, bg=(40, 40, 40, 255)):
        if getattr(s, "case32", False): return s.frame32(n, base, masque, bg)
        fr = s.F[n]; W, H = fr["w"] * 16, fr["h"] * 16
        im = Image.new("RGBA", (max(W, 1), max(H, 1)), bg); px = im.load()
        for k, cell in enumerate(fr["cells"]):
            if cell is None: continue
            idx, attr = cell; cx, cy = (k % fr["w"]) * 16, (k // fr["w"]) * 16
            pal = s.P[min(base + (attr & masque), len(s.P) - 1)]; t = s.tile(idx)
            for y in range(16):
                for x in range(16):
                    b = t[y * 8 + x // 2]; c = b & 0xF if x % 2 == 0 else b >> 4
                    if not c: continue
                    X, Y = x, y
                    if attr & 0x80: X = 15 - X
                    if attr & 0x40: Y = 15 - Y
                    px[cx + X, cy + Y] = pal[c]
        return im
def _frame32(s, n, base=0, masque=0x1F, bg=(40, 40, 40, 255)):
    """case = 2x2 tuiles (ordre TL, BL, TR, BR comme les persos), 32x32"""
    fr = s.F[n]; W, H = fr["w"] * 32, fr["h"] * 32
    im = Image.new("RGBA", (max(W, 1), max(H, 1)), bg); px = im.load()
    for k, cell in enumerate(fr["cells"]):
        if cell is None: continue
        idx, attr = cell; cx, cy = (k % fr["w"]) * 32, (k // fr["w"]) * 32
        pal = s.P[min(base + (attr & masque), len(s.P) - 1)]
        for q, (qx, qy) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
            t = s.tile(idx * 4 + q)
            for y in range(16):
                for x in range(16):
                    b = t[y * 8 + x // 2]; c = b & 0xF if x % 2 == 0 else b >> 4
                    if not c: continue
                    X, Y = qx * 16 + x, qy * 16 + y
                    if attr & 0x80: X = 31 - X
                    if attr & 0x40: Y = 31 - Y
                    px[cx + X, cy + Y] = pal[c]
    return im
Ecran.frame32 = _frame32
def planche(ec, nums, fichier, base=0):
    ims = [ec.frame(n, base) for n in nums]
    W = sum(i.width for i in ims) + 8 * len(ims); H = max(i.height for i in ims)
    sh = Image.new("RGBA", (W, H), (40, 40, 40, 255)); x = 0
    for i in ims: sh.paste(i, (x, 0)); x += i.width + 8
    sh.save(fichier); return sh.size
if __name__ == "__main__":
    d = os.path.expanduser("~/.cache/sfa3max/data/textes")
    print(planche(Ecran(os.path.join(d, "op26_e.pac")), range(14), "op26_rendu.png"))
