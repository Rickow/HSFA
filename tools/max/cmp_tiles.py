import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import sys, json
from plpac import split
from maxtile import decode, tiles
from ro_tiles import tileset
def nontrivial(t): return len(set(t)) > 2          # écarte vides/unies
def hflip(t):                                        # miroir horizontal d'une tuile 4bpp packée
    out = bytearray()
    for y in range(16):
        row = t[y*8:(y+1)*8]
        px = [n for b in row for n in (b & 0xF, b >> 4)][::-1]
        out += bytes(px[i] | (px[i+1] << 4) for i in range(0, 16, 2))
    return bytes(out)
def swapnib(t): return bytes(((b & 0xF) << 4) | (b >> 4) for b in t)
def psp_tiles(pl):
    g = split(open(os.path.join(paths.pac_dir(), f"{pl}_e.pac"), "rb").read())[1][1]
    return [decode(g, o)[0] for o, _ in tiles(g)]
def psp_fbneo(t):
    """tuile PSP (0x80 o packés) -> 256 pixels en espace FBNeo : i -> 16-i, 0 -> 0 (validate_cps2.py)."""
    return bytes((16 - n) % 16 for b in t for n in (b & 0xF, b >> 4))
if __name__ == "__main__":
    ro5 = tileset("ro5")
    names = json.load(open(paths.MAPPING))
    for pl in sys.argv[1:]:
        T = [psp_fbneo(t) for t in psp_tiles(pl) if nontrivial(t)]
        ex = sum(t in ro5 for t in T)
        print(f"{pl} {names[pl[2:]]:<13} tuiles non triviales {len(T):6} | identiques dans Upper (ro5) {ex:6} ({100*ex/len(T):5.1f} %)")
