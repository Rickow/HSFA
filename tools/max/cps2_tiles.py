"""Tuiles 16x16 de la CPS2 SFA3 d'origine (décodage FBNeo via cps2gfx.py), en listes de 256 index."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

import sys, os, pickle, zipfile
import cps2gfx
CACHEF = os.path.join(paths.CACHE, "cps2_sfa3_tiles.pkl")
def cps2_pixels():
    if os.path.exists(CACHEF): return pickle.load(open(CACHEF, "rb"))
    z = zipfile.ZipFile(paths.sfa3_zip())
    roms = [z.read(n) for n in ["sz3.13m","sz3.15m","sz3.17m","sz3.19m","sz3.14m","sz3.16m","sz3.18m","sz3.20m"]]
    T = cps2gfx.decode_gfx(roms)
    tiles = []
    for t in range(len(T) // 128):
        px = []
        for y in range(16):
            row = t*128 + y*8
            for half in (0, 4):
                b = int.from_bytes(T[row+half:row+half+4], "little")
                for _ in range(8):
                    px.append((b >> 28) & 0xF); b = (b << 4) & 0xFFFFFFFF
        tiles.append(bytes(px))
    pickle.dump(tiles, open(CACHEF, "wb")); return tiles
