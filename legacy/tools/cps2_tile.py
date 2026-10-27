#!/usr/bin/env python3
"""Décodage de tuiles CPS2 (codec PLANAIRE 4 bits/plan).

Une tuile 8x8 4bpp = 32 o : chaque ligne = 4 octets = 1 octet par bitplane.
Offsets de plan (MAME cps1/cps2 gfxlayout) : {3*8, 1*8, 2*8, 0*8} en bits
=> plan3=octet3, plan1=octet1, plan2=octet2, plan0=octet0 de la ligne.
Le pixel x prend le bit (7-x) de chaque octet de plan.

Une tuile 32x32 (0x200 o) = 16 sous-tuiles 8x8, arrangement à déterminer (4x4).
"""

PLANE_BYTE = (0, 1, 2, 3)   # plan0..plan3 -> octet de la ligne

def decode8(data, off=0, planes=PLANE_BYTE):
    """-> liste de 8 lignes de 8 index (0-15)."""
    rows = []
    for y in range(8):
        base = off + y * 4
        b = [data[base + planes[p]] for p in range(4)]
        row = []
        for x in range(8):
            bit = 7 - x
            idx = 0
            for p in range(4):
                if (b[p] >> bit) & 1:
                    idx |= (1 << p)
            row.append(idx)
        rows.append(row)
    return rows

def decode32(block, order="row", planes=PLANE_BYTE):
    """bloc de 0x200 -> grille 32x32 d'index. order: 'row' ou 'col' (4x4 de sous-tuiles)."""
    grid = [[0] * 32 for _ in range(32)]
    for st in range(16):
        if order == "row":
            sx, sy = (st % 4) * 8, (st // 4) * 8
        else:
            sx, sy = (st // 4) * 8, (st % 4) * 8
        sub = decode8(block, st * 32, planes)
        for y in range(8):
            for x in range(8):
                grid[sy + y][sx + x] = sub[y][x]
    return grid
