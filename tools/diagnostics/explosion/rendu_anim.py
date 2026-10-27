#!<workspace>/venv/bin/python3
"""Rendu des animations de la table 2E50A0 (SFA3 arcade, sfa3ud_prog.bin) depuis les tuiles CPS2 décodées.
Format d'un pas (8 o) : u8 durée, u8 drapeaux (0 = pas suivant, bit7 = saut au long en +8, bit6 = fin), u16 ?, u32 frame.
Frame type 6 (routine 0x2113A) : u16 6, u16 T, u16 n-1, s16 dx0, s16 dy0, n x (u16 idx, u16 code, u16 attr) ;
position objet = table 0x229AE[idx] (grille 16 px : idx/4 -> (16*(k%16), 16*(k//16))) + (dx0,dy0) ;
code final = code + ((Y & 0x6000) << 3), Y |= $1A(acteur) (= 0x6000 pour ces acteurs -> banque 0x30000).
Type 0x12 (routine 0x2150C = RTS) : frame vide."""
import sys, struct, numpy as np
from PIL import Image
P = open('<workspace>/work/cps2/sfa3ud_prog.bin', 'rb').read()
T = np.load('<workspace>/work/cps2/sfa3_tiles_raw.npy', mmap_mode='r')
TABLE = 0x2E50A0
POS = 0x229AE
w16 = lambda a: struct.unpack_from('>H', P, a)[0]
s16 = lambda a: struct.unpack_from('>h', P, a)[0]
l32 = lambda a: struct.unpack_from('>I', P, a)[0]

def pas(n):
    a = TABLE + w16(TABLE + 2 * n)
    out = []
    for i in range(64):
        dur, fl, fr = P[a], P[a + 1], l32(a + 4)
        out.append((a, dur, fl, fr))
        if fl & 0x40 or fl & 0x80:
            break
        a += 8
    return out

def objets(fr, banque=0x30000):
    t = w16(fr)
    if t != 6:
        return t, []
    tot, n1, dx0, dy0 = w16(fr + 2), w16(fr + 4), s16(fr + 6), s16(fr + 8)
    res = []
    for k in range(n1 + 1):
        o = fr + 10 + 6 * k
        idx, code, attr = w16(o), w16(o + 2), w16(o + 4)
        px, py = s16(POS + idx), s16(POS + idx + 2)
        res.append((px + dx0, py + dy0, banque + code, attr))
    return t, res

def rendu(fr, pal, banque=0x30000, taille=160, ox=80, oy=100):
    img = np.zeros((taille, taille, 4), np.uint8)
    t, objs = objets(fr, banque)
    for x, y, code, attr in objs:
        nx, ny = ((attr >> 8) & 0xF) + 1, ((attr >> 12) & 0xF) + 1
        fx, fy = attr & 0x20, attr & 0x40
        for j in range(ny):
            for i in range(nx):
                c = (code & ~0xF) + ((code + i) & 0xF) + 0x10 * j
                tile = np.array(T[c])
                if fx: tile = tile[:, ::-1]
                if fy: tile = tile[::-1, :]
                sx = x + ((nx - 1 - i) if fx else i) * 16 + ox
                sy = y + ((ny - 1 - j) if fy else j) * 16 + oy
                for yy in range(16):
                    for xx in range(16):
                        v = tile[yy, xx]
                        if v == 15:      # 15 = transparent sur CPS2
                            continue
                        X, Y = sx + xx, sy + yy
                        if 0 <= X < taille and 0 <= Y < taille:
                            img[Y, X] = pal[v]
    return t, objs, img
