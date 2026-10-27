"""Chaîne de correspondance pour Ryu : tuile PSP -> code CPS2 (contenu) -> numéro local dans la banque e258."""
import sys, os, struct, pickle
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import paths
from cps2_tiles import cps2_pixels
from plpac import split
from maxtile import decode, tiles
from frames import frames
CACHE = os.path.join(paths.CACHE, "rosetta_ryu.pkl")
def build():
    if os.path.exists(CACHE): return pickle.load(open(CACHE, "rb"))
    C = cps2_pixels()
    first = {}
    for code, p in enumerate(C):
        first.setdefault(p, code)
    E = split(open(os.path.join(paths.pac_dir(), "pl00_e.pac"), "rb").read())
    g = E[1][1]; T = tiles(g)
    psp2code = []
    for o, _ in T:
        t = decode(g, o)[0]
        p = bytes((16 - n) % 16 for b in t for n in (b & 0xF, b >> 4))
        psp2code.append(first.get(p) if len(set(p)) > 1 else None)
    loc = open(__import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "mame", "banques", "f258.bin"), "rb").read()
    local2code = struct.unpack(f"<{len(loc)//4}I", loc)
    code2local = {}
    for l, c in enumerate(local2code):
        if c != 0xFFFFFFFF: code2local.setdefault(c, l)
    R = {"psp2code": psp2code, "local2code": local2code, "code2local": code2local, "F": frames(E[0][1])}
    pickle.dump(R, open(CACHE, "wb")); return R
if __name__ == "__main__":
    R = build()
    p2c = R["psp2code"]; nonempty = [c for c in p2c if c is not None]
    inbank = [c for c in nonempty if c in R["code2local"]]
    print(f"tuiles PSP de Ryu : {len(p2c)} | avec un code CPS2 exact : {len(nonempty)} | dont présentes dans la banque e258 : {len(inbank)}")
    print(f"banque e258 : {len(R['local2code'])} tuiles locales, {len(R['code2local'])} codes CPS2 distincts")
    # frame 0 de Ryu : ses tuiles -> codes locaux
    fr = R["F"][0]
    locs = []
    for cell in fr["cells"]:
        if cell is None: continue
        for q in range(4):
            c = p2c[cell[0]*4 + q]
            locs.append(R["code2local"].get(c) if c is not None else None)
    print("frame 0 de Ryu -> codes locaux :", locs)
