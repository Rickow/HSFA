#!/usr/bin/env python3
"""
render_stage.py — Rendu OFFLINE d'un stage extrait (bank + palette + ring) → PNG.
Valide, sans PCSX2, que l'extraction z5 (CARTO §8bis) est correcte.

Palette : formule exacte décompilée de FUN_1d1300 (z9). Couleur u16 = [bri:4][R:4][G:4][B:4].
Tuile   : 8x8 4bpp, 0x20 o/tuile, 4bpp LSB (nibble bas = pixel pair). index dans une rangée pal.
Ring    : cellules {tile u16, attr u16}. attr bits bas = rangée palette (à caler).
"""
import struct, sys, os
import numpy as np
from PIL import Image

def load_palette(path):
    d = open(path, "rb").read()
    n = len(d) // 2
    rows = np.zeros((128, 16, 3), np.uint8)
    for i in range(min(n, 128 * 16)):
        c = struct.unpack_from("<H", d, i * 2)[0]
        bri = (c >> 12) + 0x10
        r = ((c >> 8) & 0xf) * bri * 0x11 // 0x1f
        g = ((c >> 4) & 0xf) * bri * 0x11 // 0x1f
        b = (c & 0xf) * bri * 0x11 // 0x1f
        rows[i // 16, i % 16] = (min(r, 255), min(g, 255), min(b, 255))
    return rows

def tile_px(bank, t):
    """8x8 index (0..15) pour la tuile t."""
    o = t * 0x20
    if o + 0x20 > len(bank):
        return np.zeros((8, 8), np.uint8)
    px = np.zeros((8, 8), np.uint8)
    for y in range(8):
        for x in range(8):
            byte = bank[o + y * 4 + (x >> 1)]
            px[y, x] = (byte >> 4) if (x & 1) else (byte & 0xf)
    return px

def render_ring(bank, pal, ring, width, palbits, out, cell_stride=4):
    """Rendu LINÉAIRE (déprécié — le ring est en pages, cf. render_ring_paged)."""
    n = len(ring) // cell_stride
    height = (n + width - 1) // width
    img = np.zeros((height * 8, width * 8, 3), np.uint8)
    for i in range(n):
        tile = struct.unpack_from("<H", ring, i * cell_stride)[0]
        attr = struct.unpack_from("<H", ring, i * cell_stride + 2)[0] if cell_stride >= 4 else 0
        tile &= 0x0fff
        if tile == 0:
            continue
        row = attr & palbits
        px = tile_px(bank, tile)
        cx, cy = (i % width) * 8, (i // width) * 8
        img[cy:cy + 8, cx:cx + 8] = pal[row % 128][px]
    Image.fromarray(img).save(out)
    return img.shape


def render_ring_paged2(bank, pal, ring, page_side, pages_wide, pal_base, out,
                       hflip=0x20, vflip=0x40):
    """Comme render_ring_paged mais rangée pal = pal_base + (attr & 0x1f), + flips H/V."""
    cells_pp = page_side * page_side
    bytes_pp = cells_pp * 4
    npages = len(ring) // bytes_pp
    pages_high = (npages + pages_wide - 1) // pages_wide
    W = pages_wide * page_side * 8
    H = pages_high * page_side * 8
    img = np.zeros((H, W, 3), np.uint8)
    for p in range(npages):
        pgx = (p % pages_wide) * page_side * 8
        pgy = (p // pages_wide) * page_side * 8
        base = p * bytes_pp
        for c in range(cells_pp):
            tile = struct.unpack_from("<H", ring, base + c * 4)[0] & 0x0fff
            attr = struct.unpack_from("<H", ring, base + c * 4 + 2)[0]
            if tile == 0 or attr == 0xffff:
                continue
            row = (pal_base + (attr & 0x1f)) % 128
            px = tile_px(bank, tile)
            if attr & hflip:
                px = px[:, ::-1]
            if attr & vflip:
                px = px[::-1, :]
            cx = pgx + (c % page_side) * 8
            cy = pgy + (c // page_side) * 8
            img[cy:cy + 8, cx:cx + 8] = pal[row][px]
    Image.fromarray(img).save(out)
    return img.shape


def render_ring_paged(bank, pal, ring, page_side, pages_wide, palbits, out):
    """Le ring est une grille de PAGES ; chaque page = page_side x page_side cellules
    stockées row-major (0x400 o pour 16x16, 0x100 o pour 8x8). On place les pages en
    grille pages_wide de large, ordre mémoire = row-major de pages."""
    cells_pp = page_side * page_side
    bytes_pp = cells_pp * 4
    npages = len(ring) // bytes_pp
    pages_high = (npages + pages_wide - 1) // pages_wide
    W = pages_wide * page_side * 8
    H = pages_high * page_side * 8
    img = np.zeros((H, W), np.uint16)  # index temporaire? non -> RGB
    img = np.zeros((H, W, 3), np.uint8)
    for p in range(npages):
        pgx = (p % pages_wide) * page_side * 8
        pgy = (p // pages_wide) * page_side * 8
        base = p * bytes_pp
        for c in range(cells_pp):
            tile = struct.unpack_from("<H", ring, base + c * 4)[0] & 0x0fff
            attr = struct.unpack_from("<H", ring, base + c * 4 + 2)[0]
            if tile == 0:
                continue
            cx = pgx + (c % page_side) * 8
            cy = pgy + (c // page_side) * 8
            img[cy:cy + 8, cx:cx + 8] = pal[(attr & palbits) % 128][tile_px(bank, tile)]
    Image.fromarray(img).save(out)
    return img.shape

def render_bank_sheet(bank, pal, row, ntiles, cols, out):
    rows = (ntiles + cols - 1) // cols
    img = np.zeros((rows * 8, cols * 8, 3), np.uint8)
    for t in range(ntiles):
        px = tile_px(bank, t)
        cx, cy = (t % cols) * 8, (t // cols) * 8
        img[cy:cy + 8, cx:cx + 8] = pal[row][px]
    Image.fromarray(img).save(out)
    return img.shape

if __name__ == "__main__":
    base = sys.argv[1]  # ex: stage_packs/SFA3U_Chun-Li_temple
    outd = os.path.dirname(base) or "."
    pal = load_palette(base + ".palette.bin")
    bank = open(base + ".bank.bin", "rb").read()
    name = os.path.basename(base)
    # 1) planche bank (valide tuiles+palette) — rangée pal 0x40 (souvent BG)
    print("bank sheet:", render_bank_sheet(bank, pal, 0x40, 4096, 64, f"{outd}/{name}.banksheet.png"))
    # 2) ring SCR2 = 16 pages 16x16 en grille 4x4 ; rangée pal = 0x40 + attr&0x1f ; flips
    r2 = open(base + ".ring_scr2.bin", "rb").read()
    print("ring scr2 :", render_ring_paged2(bank, pal, r2, 16, 4, 0x40, f"{outd}/{name}.scr2.png"))
    # 3) ring SCR3 = pages 8x8 ; rangée pal = 0x60 + attr&0x1f (largeur 24 à affiner)
    r3 = open(base + ".ring_scr3.bin", "rb").read()
    print("ring scr3 :", render_ring_paged2(bank, pal, r3, 8, 24, 0x60, f"{outd}/{name}.scr3.png"))
