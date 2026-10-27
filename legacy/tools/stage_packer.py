#!/usr/bin/env python3
"""
stage_packer.py — construit un package de stage (format UPST v7) depuis une extraction z5.
Étape par étape, chaque brique vérifiable. Cible : reproduire le format e527 pour tout stage.

BRIQUE 1 (ici) : DÉ-COMPOSEUR. z5 streame (pas de pool natif) ; le composeur z9 attend un POOL
de pages + une LISTE de sels. On dé-compose le ring composé en pages dédupliquées + liste.

Ring (composé) : cellules {tile, attr} de 4 o.
  - SCR2 : tile a le bit |0x1000 ; page = 16x16 cellules = 0x400 o dans le ring ; 16 pages (0x4000).
  - SCR3 : pas d'offset ; page = 8x8 = 0x100 o ; 64 pages (0x4000).
Pool (attendu par le composeur) :
  - SCR2 page = 0x300 o : tiles u16[256] (@+0) + attrs u8[256] (@+0x200) ; tile SANS |0x1000.
  - SCR3 page = 0xc0 o  : tiles u16[64]  (@+0) + attrs u8[64]  (@+0x80).
"""
import struct

def decompose(ring, cells_per_side, tile_mask_off=0):
    """ring -> (pages uniques [bytes], liste d'indices de page). cells_per_side=16(SCR2)/8(SCR3)."""
    ncells = cells_per_side * cells_per_side
    ring_page = ncells * 4                    # o/page dans le ring
    npages = len(ring) // ring_page
    tsz = ncells * 2                          # taille zone tiles (u16)
    pool_page = tsz + ncells                  # + attrs u8
    uniq = []; index = {}; layout = []
    for p in range(npages):
        base = p * ring_page
        tiles = bytearray(); attrs = bytearray()
        for c in range(ncells):
            t, a = struct.unpack_from("<HH", ring, base + c*4)
            t = (t - tile_mask_off) & 0xffff  # retire |0x1000 pour SCR2
            tiles += struct.pack("<H", t); attrs += struct.pack("<B", a & 0xff)
        page = bytes(tiles + attrs)
        if page not in index:
            index[page] = len(uniq); uniq.append(page)
        layout.append(index[page])
    return uniq, layout

def recompose(uniq, layout, cells_per_side, tile_add=0):
    """inverse : reconstruit le ring depuis pages+liste (pour vérif)."""
    ncells = cells_per_side * cells_per_side
    out = bytearray()
    for pidx in layout:
        page = uniq[pidx]
        for c in range(ncells):
            t = struct.unpack_from("<H", page, c*2)[0]
            a = page[ncells*2 + c]
            out += struct.pack("<HH", (t + tile_add) & 0xffff, a)
    return bytes(out)

def collect_pages_and_tiles(base):
    """dé-compose SCR2+SCR3 -> (pages, layouts, set de tuiles utilisées)."""
    out = {}
    tiles = set()
    for tag, side, off in (("scr2", 16, 0x1000), ("scr3", 8, 0)):
        ring = open(f"{base}.ring_{tag}.bin", "rb").read()
        uniq, layout = decompose(ring, side, off)
        out[tag] = (uniq, layout, side)
        for pg in uniq:
            for i in range(side * side):
                t = struct.unpack_from("<H", pg, i * 2)[0]
                if t:
                    tiles.add(t)
    return out, tiles

def tile_ranges(z5bank, z9bank, tiles, gap=0x10):
    """plages contiguës de tuiles qui DIFFÈRENT entre z5 et z9 (à copier)."""
    def tl(d, t):
        o = t * 0x20
        return d[o:o + 0x20]
    diff = sorted(t for t in tiles if tl(z5bank, t) != tl(z9bank, t))
    if not diff:
        return []
    ranges = []
    s = p = diff[0]
    for t in diff[1:]:
        if t - p > gap:
            ranges.append((s, p)); s = t
        p = t
    ranges.append((s, p))
    return ranges

# emplacements pool z9 des pages portées (slots libres) + décalage de liste
SCR2_SLOT0 = 1     # pages SCR2 -> slots 1.. (slot 0 partagé intact)
SCR3_SLOT0 = 0xe   # pages SCR3 -> slots 0xe..

# adresses des homes z9 (composeur)
BANK_Z9   = 0xdb4000
SCR2_POOL = 0x640960; SCR2_PAGE = 0x300
SCR3_POOL = 0x643c60; SCR3_PAGE = 0xc0
SCR2_LIST = 0x696018
SCR3_LIST = 0x696050
PAL_DST   = 0xbac000

def build_package(base, z5bank_path, z9bank_path, out_path):
    """Assemble un package CSTG = header + TABLE DE COPIES {dst_ee, size, src_off} + data.
    Toutes les maths (slots pool, adresses) sont faites ICI → le cave n'est qu'une boucle memcpy."""
    pages, tiles = collect_pages_and_tiles(base)
    m = 0x1ffffff
    z5bank = open(z5bank_path, "rb").read()[(0xd35800 & m):(0xd35800 & m) + 0x2d8000]
    z9bank = open(z9bank_path, "rb").read()[(0xdb4000 & m):(0xdb4000 & m) + 0x2d8000]
    ranges = tile_ranges(z5bank, z9bank, tiles)
    scr2_pages, scr2_layout, _ = pages["scr2"]
    scr3_pages, scr3_layout, _ = pages["scr3"]
    scr2_list = bytes((SCR2_SLOT0 + s) & 0xff for s in scr2_layout)
    scr3_list = bytes((SCR3_SLOT0 + s) & 0xff for s in scr3_layout)
    palette = open(base + ".palette.bin", "rb").read()

    copies = []   # (dst_ee, data)
    for lo, hi in ranges:
        copies.append((BANK_Z9 + lo * 0x20, z5bank[lo * 0x20: (hi + 1) * 0x20]))
    for p, pg in enumerate(scr2_pages):
        copies.append((SCR2_POOL + (SCR2_SLOT0 + p) * SCR2_PAGE, pg))
    for p, pg in enumerate(scr3_pages):
        copies.append((SCR3_POOL + (SCR3_SLOT0 + p) * SCR3_PAGE, pg))
    copies.append((SCR2_LIST, scr2_list))
    copies.append((SCR3_LIST, scr3_list))
    copies.append((PAL_DST, palette))

    # corps : table {dst u32, size u32, data_off u32} puis data (chaque bloc aligné 4)
    data = bytearray(); table = bytearray()
    for dst, blob in copies:
        if len(blob) % 4: blob = blob + b"\0" * (4 - len(blob) % 4)
        doff = len(data); data += blob
        table += struct.pack("<III", dst, len(blob), doff)
    off_table = 0x20
    off_data = off_table + len(table)
    hdr = struct.pack("<4sIII", b"CSTG", len(copies), off_table, off_data).ljust(0x20, b"\0")
    pkg = hdr + bytes(table) + bytes(data)
    open(out_path, "wb").write(pkg)
    return dict(size=len(pkg), n_copies=len(copies), ranges=len(ranges),
                tiles=sum((hi - lo + 1) for lo, hi in ranges),
                scr2_pages=len(scr2_pages), scr3_pages=len(scr3_pages))


if __name__ == "__main__":
    import sys, os
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        base = sys.argv[2]; z5 = sys.argv[3]
        z9 = "<workspace>/hyper_re/eeMemory_versus.bin"
        out = base + ".cstg"
        import json
        print(json.dumps(build_package(base, z5, z9, out), indent=1)); print("->", out)
        sys.exit(0)
    base = sys.argv[1] if len(sys.argv) > 1 else "stage_packs/SFA3U_Chun-Li_LIVE"
    for tag, side, off in (("ring_scr2", 16, 0x1000), ("ring_scr3", 8, 0)):
        ring = open(base + "." + tag + ".bin", "rb").read()
        uniq, layout = decompose(ring, side, off)
        rc = recompose(uniq, layout, side, off)
        ok = rc == ring
        print(f"{tag}: {len(ring)//((side*side)*4)} pages ring -> {len(uniq)} uniques ; "
              f"liste={layout} ; re-compose {'✅ OK' if ok else '❌ DIFFERE'}")
