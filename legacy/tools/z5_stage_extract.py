#!/usr/bin/env python3
"""
z5_stage_extract.py — Extracteur de stage Upper (z5) pour transplant cross-stage (chemin A).

Modèle : z5 (SFA3 Upper) STREAME ses stages (pas de pool de pages comme z9). On part donc du
**ring composé** de z5 (état combat), directement au format z9, + la palette + la bank de tuiles.
Cf. CARTO-Cross-Stage-Tables.md §8bis.

Sortie (par stage) : des .bin bruts + un manifest .json. Ces blobs alimenteront l'injecteur z9
(découpe ring→pages pool z9, palette→0xbac000, bank→repoint 0x1dc2e4).

Usage :
  python z5_stage_extract.py <ee_z5xxx.bin> <nom> [out_dir]
"""
import struct, json, sys, os

M = 0x1ffffff  # masque adresse EE -> offset dump 32 Mo

# --- Carte z5 (Upper), confirmée par décompilation 2026-08-31 ---
RING_SCR1 = (0xa20000, 0x4000)   # ciel/uni (souvent vide en combat)
RING_SCR2 = (0xa24000, 0x4000)   # {tile|0x1000, attr} — format z9
RING_SCR3 = (0xa28000, 0x4000)   # {tile, attr} — 0x4000 (le staging suit à +0x4000 = 0xa2c000)
PALETTE   = (0x6fa460, 0x1000)   # 128 rangées x 16 couleurs, CPS2 4444
BANK_PTR  = 0x1dc2e4             # [+0x34] struct BG -> base bank BG (z5 = 0xd35800)
BANK_LEN  = 0x2d8000            # taille bank BG (comme z9 0xdb4000..0x108c000)
CTXBASE   = 0xa08000            # contexte couche z5 (info)


def rd(d, addr, ln):
    a = addr & M
    return d[a:a + ln]


def extract(dump_path, name, out_dir):
    d = open(dump_path, "rb").read()
    os.makedirs(out_dir, exist_ok=True)
    u32 = lambda a: struct.unpack_from("<I", d, a & M)[0]
    bank_addr = u32(BANK_PTR)

    blobs = [
        ("ring_scr1", RING_SCR1[0], rd(d, *RING_SCR1)),
        ("ring_scr2", RING_SCR2[0], rd(d, *RING_SCR2)),
        ("ring_scr3", RING_SCR3[0], rd(d, *RING_SCR3)),
        ("palette",   PALETTE[0],   rd(d, *PALETTE)),
        ("bank",      bank_addr,    rd(d, bank_addr, BANK_LEN)),
    ]
    man = {"name": name, "src": os.path.basename(dump_path),
           "model": "z5-streamed; extract via composed ring", "bank_addr": hex(bank_addr),
           "blobs": []}
    slug = name.replace(" ", "_").replace("/", "-")
    for tag, addr, blob in blobs:
        nz = sum(1 for b in blob if b)
        fn = os.path.join(out_dir, f"{slug}.{tag}.bin")
        open(fn, "wb").write(blob)
        man["blobs"].append({"tag": tag, "src_addr": hex(addr), "len": len(blob),
                             "nonzero": nz, "file": os.path.basename(fn)})
    # aperçu : amplitude des n° de tuiles dans les rings (dimensionne la bank requise)
    def tmax(addr, ln, sub=0):
        hi = 0
        for i in range(ln // 4):
            t = struct.unpack_from("<H", d, (addr & M) + i * 4)[0] - sub
            if 0 < t < 0x10000:
                hi = max(hi, t)
        return hi
    man["scr2_tile_max"] = hex(tmax(*RING_SCR2, sub=0x1000))
    man["scr3_tile_max"] = hex(tmax(*RING_SCR3))
    json.dump(man, open(os.path.join(out_dir, f"{slug}.manifest.json"), "w"), indent=2)
    return man


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    dump, name = sys.argv[1], sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else \
        os.path.join(os.environ.get("HSFA", "<workspace>"), "stage_packs")
    m = extract(dump, name, out)
    print(json.dumps(m, indent=2))
