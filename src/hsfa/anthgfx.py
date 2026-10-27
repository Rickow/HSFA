#!/usr/bin/env python3
"""CONTENEURS GRAPHIQUES DE L'ANTHOLOGY -> tuiles CPS2 (HANDOFF §45).

En-tete : 3 enregistrements de 4 mots (u32 LE), un par TAILLE de tuile :
    rec0 = 8x8, rec1 = 16x16, rec2 = 32x32 ;  (premier_index, nombre, position_table, 0)
Table : un u32 par tuile ; 0 = tuile vide (toute a 15, transparent brut) ;
        bit31 = 1 -> flux compresse (lz148778), sinon tuile non compressee.
Pixels : 4 bpp lineaires, quartet bas = pixel de gauche, valeurs BRUTES de la ROM CPS2.
Tailles : 8x8 = 0x20 o, 16x16 = 0x80 o, 32x32 = 0x200 o.

Correspondance avec la ROM CPS2 (en « slots » = lignes de 16 pixels, cf. cps2rom.py) :
    16x16 d'index m -> slots 16m .. 16m+15
    32x32 d'index m -> slots 64m .. 64m+63 (2 slots par ligne de 32 pixels)
    8x8   d'index m -> slots 8m .. 8m+7, la tuile 8 px DUPLIQUEE dans les deux moities
Les index sont relatifs au QUART de la ROM que couvre le conteneur (65 536 tuiles 16x16),
pour les conteneurs GFX de la ROM ; les banques DATA (sprites charges a la demande) ont
premier_index = 0 et une numerotation propre.
"""
import struct, numpy as np
import sys as _s, os as _o; _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), ".."))
from lz148778 import decompress

SIZES = {0: (8, 0x20), 1: (16, 0x80), 2: (32, 0x200)}

def records(buf):
    out = []
    for k in range(3):
        first, count, tab, z = struct.unpack_from('<4I', buf, 16*k)
        if count and 0x30 <= tab < len(buf) and count < 0x20000:
            out.append((k, first, count, tab))
    return out

def is_container(buf):
    r = records(buf)
    return bool(r) and all(struct.unpack_from('<I', buf, 16*k+12)[0] == 0 for k in range(3))

def pixels(d, w):
    a = np.frombuffer(d, np.uint8)
    return np.stack([a & 0xF, a >> 4], -1).reshape(w, w)

def tiles(buf):
    """-> [(taille k, index m, pixels (w,w) ou None si vide)]"""
    out = []
    for k, first, count, tab in records(buf):
        w, sz = SIZES[k]
        for j in range(count):
            if tab + 4*j + 4 > len(buf): break
            v = struct.unpack_from('<I', buf, tab + 4*j)[0]
            if v == 0: out.append((k, first + j, None)); continue
            o = v & 0x7fffffff
            if not (0 < o < len(buf)): continue
            try: d = decompress(buf, o, sz) if v & 0x80000000 else buf[o:o+sz]
            except Exception: continue
            if len(d) < sz: continue
            out.append((k, first + j, pixels(d[:sz], w)))
    return out

def to_slots(k, px):
    """pixels d'une tuile -> lignes de 16 pixels (slots)"""
    if k == 1: return px
    if k == 2: return px.reshape(64, 16)
    return np.concatenate([px, px], 1)          # 8x8 dupliquee

SLOTS = {0: 8, 1: 16, 2: 64}
