"""Assemblage d'une frame : case = 4 tuiles 16x16 (numéro de case x 4, ordre en colonnes TL,BL,TR,BR), palette = base + (attr & 3),
bit 0x40 = miroir HORIZONTAL, bit 0x80 = miroir VERTICAL, bit 0x20 toujours posé (2026-10-17 : l'inverse de la
note d'origine ; mesuré par continuité des bords de cases sur Ryu et les 4 persos MAX, aucun contre-exemple ; Yun
frames 175-178 en mosaïque avec l'ancienne lecture)."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

import struct
from PIL import Image
from plpac import split
from maxtile import decode, tiles
from frames import frames
def palettes(pal_entry):
    n = len(pal_entry) // 32; out = []
    for k in range(n):
        row = []
        for i in range(16):
            v = struct.unpack_from("<H", pal_entry, 32*k + 2*i)[0]
            row.append((( v & 31)*255//31, ((v >> 5) & 31)*255//31, ((v >> 10) & 31)*255//31, 0 if i == 0 else 255))
        out.append(row)
    return out
class Char:
    def __init__(self, path):
        E = split(open(path, "rb").read())
        self.g = E[1][1]; self.T = tiles(self.g); self.F = frames(E[0][1]); self.P = palettes(E[2][1]); self._c = {}
    def tile(self, i):
        if i not in self._c: self._c[i] = decode(self.g, self.T[i][0])[0]
        return self._c[i]
    def frame(self, n, base=0, order=((0,0),(0,1),(1,0),(1,1)), bg=(40,40,40,255)):
        fr = self.F[n]; W, H = fr["w"]*32, fr["h"]*32
        im = Image.new("RGBA", (W, H), bg); px = im.load()
        for k, cell in enumerate(fr["cells"]):
            if cell is None: continue
            idx, attr = cell; cx, cy = (k % fr["w"])*32, (k // fr["w"])*32
            pal = self.P[min(base + (attr & 3), len(self.P)-1)]
            for q, (qx, qy) in enumerate(order):
                t = self.tile(idx*4 + q)
                for y in range(16):
                    for x in range(16):
                        b = t[y*8 + x//2]; c = b & 0xF if x % 2 == 0 else b >> 4
                        if not c: continue
                        X, Y = qx*16 + x, qy*16 + y
                        if attr & 0x40: X = 31 - X
                        if attr & 0x80: Y = 31 - Y
                        px[cx + X, cy + Y] = pal[c]
        return im
