"""Localise la table des jeux de boîtes (12 o / entrée) dans la section 7 de l'entrée [6] d'un perso PSP :
offset (pair) dont les entrées visées par les scripts ont la forme de celles de Ryu
(mot A = deux u16 < 0x100 ; moitié basse du mot B < 0x400 ; moitié haute non nulle)."""
import sys, struct, os
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import paths
from plpac import split
def find(pl):
    E = split(open(os.path.join(paths.pac_dir(), f"{pl}_e.pac"), "rb").read()); b6 = E[6][1]
    s7, s8 = struct.unpack_from("<2I", b6, 4*7)
    H = struct.unpack_from(f"<{len(b6)//2}H", b6)
    nfr = struct.unpack_from("<I", E[0][1], 0)[0] // 12
    cols = set()
    for i in range(len(H) - 10):
        if all(H[i+5*k+2] < nfr and (H[i+5*k] <= 0xFF or H[i+5*k] & 0x8000) and H[i+5*k+3] in (0, 1) for k in range(2)):
            if H[i+4] < 1024: cols.add(H[i+4])
    best = (0, None)
    for o in range(s7, s8 - 12, 2):
        ok = n = 0
        for c in cols:
            if o + 12*c + 12 > s8: continue
            a, bb = struct.unpack_from("<2I", b6, o + 12*c); n += 1
            ok += (a & 0xFFFF) < 0x100 and (a >> 16) < 0x100 and (bb & 0xFFFF) < 0x400 and (bb >> 16) != 0
        if n >= 0.8 * len(cols) and ok / max(n, 1) > best[0]: best = (ok / n, o)
    return best[1], best[0], len(cols), (s7, s8)
if __name__ == "__main__":
    for pl in sys.argv[1:] or ["pl00", "pl20", "pl26", "pl27", "pl28", "pl29"]:
        o, score, nc, (s7, s8) = find(pl)
        print(f"{pl}: table des jeux de boîtes = {o:#x} (section 7 + {o - s7:#x}) ; {nc} index ; forme conforme {100*score:.0f} %")
