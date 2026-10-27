#!/usr/bin/env python3
"""Rend la couche SCR3 depuis un ctx construit (blocs 32x32 4bpp) + ring + palette.
Validation visuelle offline AVANT toute injection."""
import struct, sys
from PIL import Image

def load_palette(path):
    raw = open(path, "rb").read()
    rows = []
    for r in range(len(raw) // 32):
        row = []
        for i in range(16):
            c = struct.unpack_from("<H", raw, r * 32 + i * 2)[0]
            bri = (c >> 12) + 0x10
            R = ((c >> 8) & 0xf) * bri * 0x11 // 0x1f
            G = ((c >> 4) & 0xf) * bri * 0x11 // 0x1f
            B = (c & 0xf) * bri * 0x11 // 0x1f
            row.append((min(R, 255), min(G, 255), min(B, 255)))
        rows.append(row)
    return rows

def main():
    base = "<workspace>/stage_packs/SFA3U_Chun-Li_LIVE"
    ctx = open(base + ".ctx.bin", "rb").read()
    ring = open(base + ".ring_scr3.bin", "rb").read()
    pal = load_palette(base + ".palette.bin")
    cnt = struct.unpack_from("<I", ctx, 0x24)[0]
    ro = struct.unpack_from("<I", ctx, 0x28)[0]

    def block(t):
        if t >= cnt: return None
        rec = struct.unpack_from("<I", ctx, ro + t * 4)[0]
        if not rec: return None
        off = rec & 0x7fffffff
        return ctx[off:off + 0x200]

    # ring SCR3 : pages de 8x8 cellules, cellule = bloc 32x32 px
    SIDE = 8; CELL = 32
    npages = len(ring) // (SIDE * SIDE * 4)
    # disposition : on met les pages en grille 8 x (npages/8)
    cols = 8
    rows_pg = (npages + cols - 1) // cols
    W = cols * SIDE * CELL
    H = rows_pg * SIDE * CELL
    img = Image.new("RGB", (W, H), (20, 20, 28))
    px = img.load()
    drawn = 0
    for pg in range(npages):
        pgx = (pg % cols) * SIDE * CELL
        pgy = (pg // cols) * SIDE * CELL
        for c in range(SIDE * SIDE):
            t, attr = struct.unpack_from("<HH", ring, (pg * SIDE * SIDE + c) * 4)
            if not t: continue
            b = block(t)
            if b is None: continue
            prow = pal[(0x60 + (attr & 0x1f)) % len(pal)]
            cx = pgx + (c % SIDE) * CELL
            cy = pgy + (c // SIDE) * CELL
            # bloc 0x200 = 16 sous-tuiles CPS2 8x8 (0x20 o) arrangées 4x4
            for st in range(16):
                sx = (st % 4) * 8
                sy = (st // 4) * 8
                so = st * 0x20
                for y in range(8):
                    for xb in range(4):
                        byte = b[so + y * 4 + xb]
                        for half in (0, 1):
                            idx = (byte >> (4 * half)) & 0xf   # LSB = pixel gauche
                            if idx:
                                px[cx + sx + xb * 2 + half, cy + sy + y] = prow[idx]
            drawn += 1
    out = base + ".ctx_scr3.png"
    img.save(out)
    print("rendu:", out, img.size, "cellules dessinees:", drawn)

if __name__ == "__main__":
    main()
