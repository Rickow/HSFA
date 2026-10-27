#!/usr/bin/env python3
"""build_ctx.py — construit un CONTEXTE DE COUCHE (format moteur) depuis un dump z5.

Mécanisme (capturé sur le v7 Blanka en marche, 2026-09-26) : le drawer lit les graphismes
de tuiles dans un « contexte de couche » pointé par [0x1dc078+0x44/0x48/0x4c] (=[0x1dc2f4]+0/4/8).
v7 fournit ce contexte DANS son package et repointe ces 3 mots chaque frame.

Format du contexte :
  +0x20 : base_tile (0)
  +0x24 : count (nb de records)
  +0x28 : recoff (0x30)
  +0x30 : table de records u32, un par tuile :
            0                -> tuile VIDE
            offset (bit31=0) -> « clean » : le drawer utilise ctx+offset TEL QUEL
            offset (bit31=1) -> « dirty » : le jeu DÉCOMPRESSE ctx+offset (format natif)
  données : blocs de 0x200 o = tuile 32x32 pixels 4bpp linéaire (16 o/ligne x 32 lignes)

On lit le ctx z5 (records dirty/compressés), on DÉCOMPRESSE chaque tuile utilisée
(algo FUN_148778, cf. lz148778.py) et on réécrit un ctx à records CLEAN.
"""
import struct, sys
sys.path.insert(0, "<workspace>/scripts")
from lz148778 import decompress

TILE_BLOCK = 0x200
RECOFF = 0x30

def read_ctx_header(dump, ctx):
    base = struct.unpack_from("<I", dump, ctx + 0x20)[0]
    cnt = struct.unpack_from("<I", dump, ctx + 0x24)[0]
    ro = struct.unpack_from("<I", dump, ctx + 0x28)[0]
    return base, cnt, ro

def build(dump_path, ctx_va, tiles, out_path):
    """tiles = itérable d'indices de tuile à embarquer. Renvoie (blob, infos)."""
    d = open(dump_path, "rb").read()
    base, cnt, ro = read_ctx_header(d, ctx_va)
    tiles = sorted(set(t for t in tiles if base <= t < base + cnt))
    max_t = max(tiles)
    new_cnt = max_t - base + 1

    blocks = {}
    missing = []
    for t in tiles:
        rec = struct.unpack_from("<I", d, ctx_va + ro + (t - base) * 4)[0]
        if rec == 0:
            missing.append(t); continue
        src = ctx_va + (rec & 0xffffff)
        if rec & 0x80000000:                      # dirty -> compressé
            blk = decompress(d, src, TILE_BLOCK)
        else:                                     # déjà clean -> brut
            blk = d[src:src + TILE_BLOCK]
        blocks[t] = blk

    # assemblage : header + records + data
    rec_bytes = new_cnt * 4
    data_off = RECOFF + rec_bytes
    data_off = (data_off + 0xf) & ~0xf            # alignement 16
    recs = bytearray(rec_bytes)
    data = bytearray()
    for t in sorted(blocks):
        off = data_off + len(data)
        assert off < 0x80000000, "offset trop grand"
        struct.pack_into("<I", recs, (t - base) * 4, off)   # bit31 = 0 -> CLEAN
        data += blocks[t]

    blob = bytearray(data_off + len(data))
    struct.pack_into("<I", blob, 0x20, base)
    struct.pack_into("<I", blob, 0x24, new_cnt)
    struct.pack_into("<I", blob, 0x28, RECOFF)
    blob[RECOFF:RECOFF + rec_bytes] = recs
    blob[data_off:data_off + len(data)] = data

    open(out_path, "wb").write(blob)
    return dict(out=out_path, size=len(blob), tiles=len(blocks), missing=len(missing),
                count=hex(new_cnt), data_off=hex(data_off),
                src_ctx=hex(ctx_va), src_count=hex(cnt))

if __name__ == "__main__":
    import json
    from stage_packer import decompose
    basep = "<workspace>/stage_packs/SFA3U_Chun-Li_LIVE"
    # tuiles utilisées par le ring SCR3 (la couche décor que v7 remplace)
    ring = open(basep + ".ring_scr3.bin", "rb").read()
    uniq, layout = decompose(ring, 8, 0)
    tiles = set()
    for u in uniq:
        for c in range(64):
            t = struct.unpack_from("<H", u, c * 2)[0]
            if t: tiles.add(t)
    info = build("<workspace>/tmp_hdd/ee_z5chunli.bin", 0x1265800, tiles,
                 basep + ".ctx.bin")
    print(json.dumps(info, indent=1))
