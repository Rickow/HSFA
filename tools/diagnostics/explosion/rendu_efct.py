"""Rendu des frames d'efct.pac (SFA3 MAX PSP) avec les modules de github/tools/max (lecture seule).
Valeur brute CPS2 équivalente : raw = i - 1 (i = index PSP, 0 = transparent) -> même échelle de gris que rendu_anim."""
import sys, numpy as np
sys.path.insert(0, '<workspace>/github/tools/max')
from plpac import split
from frames import frames
from maxtile import tiles, decode
E = split(open('~/.cache/sfa3max/data/efct.pac', 'rb').read())
F = frames(E[0][1]); G = E[1][1]; TT = tiles(G)
ORDER = ((0, 0), (0, 1), (1, 0), (1, 1))
def raw_frame(n):
    """-> liste de (x, y, valeur brute CPS2 0..14) relative à l'ancre (a, c)"""
    fr = F[n]; px = []
    for k, cell in enumerate(fr['cells']):
        if cell is None: continue
        idx, attr = cell; cx, cy = (k % fr['w']) * 32 - fr['a'], (k // fr['w']) * 32 - fr['c']
        for q, (qx, qy) in enumerate(ORDER):
            t = decode(G, TT[idx * 4 + q][0])[0]
            for y in range(16):
                for x in range(16):
                    b = t[y * 8 + x // 2]; c = b & 0xF if x % 2 == 0 else b >> 4
                    if not c: continue
                    X, Y = qx * 16 + x, qy * 16 + y
                    if attr & 0x80: X = 31 - X
                    if attr & 0x40: Y = 31 - Y
                    px.append((cx + X, cy + Y, c - 1))
    return px
def rendu(n, pal, taille=160, ox=80, oy=100):
    img = np.zeros((taille, taille, 4), np.uint8)
    for x, y, v in raw_frame(n):
        X, Y = x + ox, y + oy
        if 0 <= X < taille and 0 <= Y < taille: img[Y, X] = pal[v]
    return img
