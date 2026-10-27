#!/usr/bin/env python3
"""build_pkg_ctx.py — package Chun-Li « méthode v7 » : copies SCR3 (pool+liste) + CONTEXTE.

Layout dans le fichier (chargé par l'ISO à RAM 0x1580000) :
  +0x00000 : header CSTG {magic, n_copies, off_table, off_data} + table {dst,size,src_off} + data
  +0x10000 : blob CONTEXTE (records CLEAN + blocs de tuiles décompressés)  -> RAM 0x1590000

Le cave : gate magic -> applique les copies -> efface le magic ; et CHAQUE frame repointe
[0x1dc2f4]/+4/+8 vers RAM 0x1590000 (le build du jeu les réécrit sans arrêt).
"""
import struct, sys, json
sys.path.insert(0, "<workspace>/scripts")
from stage_packer import decompose

PKG_RAM   = 0x01580000
CTX_OFF   = 0x10000                 # offset du ctx dans le package
CTX_RAM   = PKG_RAM + CTX_OFF       # = 0x1590000
SCR3_POOL = 0x643c60; SCR3_PAGE = 0xc0; SCR3_SLOT0 = 0x0e
SCR3_LIST = 0x696050

def build(base, ctx_path, out_path):
    ring = open(base + ".ring_scr3.bin", "rb").read()
    uniq, layout = decompose(ring, 8, 0)
    lst = bytes((SCR3_SLOT0 + s) & 0xff for s in layout)

    copies = []
    for p, pg in enumerate(uniq):
        copies.append((SCR3_POOL + (SCR3_SLOT0 + p) * SCR3_PAGE, bytes(pg)))
    copies.append((SCR3_LIST, lst))

    data = bytearray(); table = bytearray()
    for dst, blob in copies:
        if len(blob) % 4:
            blob = blob + b"\0" * (4 - len(blob) % 4)
        off = len(data); data += blob
        table += struct.pack("<III", dst, len(blob), off)
    off_table = 0x20
    off_data = off_table + len(table)
    hdr = struct.pack("<4sIII", b"CSTG", len(copies), off_table, off_data).ljust(0x20, b"\0")
    head = hdr + bytes(table) + bytes(data)
    assert len(head) <= CTX_OFF, "en-tête déborde sur le ctx (%#x)" % len(head)

    ctx = open(ctx_path, "rb").read()
    pkg = bytearray(CTX_OFF + len(ctx))
    pkg[0:len(head)] = head
    pkg[CTX_OFF:CTX_OFF + len(ctx)] = ctx
    open(out_path, "wb").write(pkg)
    return dict(out=out_path, size=len(pkg), n_copies=len(copies),
                scr3_pages=len(uniq), list_len=len(lst),
                ctx_size=len(ctx), ctx_ram=hex(CTX_RAM), head_size=hex(len(head)))

if __name__ == "__main__":
    b = "<workspace>/stage_packs/SFA3U_Chun-Li_LIVE"
    print(json.dumps(build(b, b + ".ctx.bin", b + ".pkgctx.bin"), indent=1))
