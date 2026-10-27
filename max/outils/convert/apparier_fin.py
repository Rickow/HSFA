"""Appariement d'une fin arcade (plans scroll2/scroll3 reconstitués depuis les blocs de la ROM sfa3ud) avec la carte
PSP de endXX_e.pac : test « la tuile PSP est une fonction de la tuile arcade » (couleurs en double fusionnées par la PSP).
Usage : python3 apparier_fin.py <n° fin arcade hex> <endXX PSP> [jeu op6 scroll2] [jeu op6 scroll3]"""
import sys, struct, pickle, os, collections
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plpac import split
import fins_max as F
ROMD = os.path.expanduser("~/.cache/sfa3max/sfa3ud_donnees.bin")
TUILES = os.path.expanduser("~/.cache/sfa3max/cps2_sfa3_tiles.pkl")
T_PLANS = 0x26CC4
GFX2 = 0x10000 + 0x6C00                   # scroll2 : code + $6C00, fenêtre du quart 1 de la ROM graphique (16×16)


def plans_arcade(b, fin, k2=1):
    tab = struct.unpack_from(">I", b, T_PLANS + 4 * fin)[0]
    off = struct.unpack_from(">H", b, tab + 2 * k2)[0]
    return list(b[tab + off:tab + off + 16])


def scroll2(b, rom, blocs):
    """{(col, ligne): pixels} du plan scroll2 64×64 ; blocs 4×4, ordre colonne dans le bloc"""
    plan = {}
    for bi, blk in enumerate(blocs):
        if not blk: continue
        base = 0x391014 + blk * 0x300
        codes = struct.unpack_from(">256H", b, base); attrs = b[base + 0x200:base + 0x300]
        bx, by = (bi % 4) * 16, (bi // 4) * 16
        for i in range(256):
            e = codes[i] + GFX2
            if e >= len(rom): continue
            t = list(rom[e]); rows = [t[k * 16:(k + 1) * 16] for k in range(16)]
            if attrs[i] & 0x20: rows = [q[::-1] for q in rows]
            if attrs[i] & 0x40: rows = rows[::-1]
            plan[(bx + i // 16, by + i % 16)] = (bi, sum(rows, []))
    return plan


def carte_psp(n):
    E = split(open(os.path.join(F.SRC, "end%s_e.pac" % n), "rb").read()); tex = F.textures(E); v = F.carte(E)
    out = {}
    for idx, x in enumerate(v):
        if x == F.VIDE or ((x >> 8) & 0xFF) not in tex: continue
        fmt, px = F.tuile(tex, (x >> 8) & 0xFF, x & 0xFF)
        if fmt != 1: continue
        px = [p if p & 0x8000 else -1 for p in px]
        rows = [px[r * 16:(r + 1) * 16] for r in range(16)]
        if x & 0x10000000: rows = [r[::-1] for r in rows]
        if x & 0x20000000: rows = rows[::-1]
        out[(idx % 64, idx // 64)] = sum(rows, [])
    return out


def fonction(rt, pt):
    m = {}
    for a, c in zip(rt, pt):
        if m.setdefault(a, c) != c: return False
    return True


if __name__ == "__main__":
    fin = int(sys.argv[1], 16); n = sys.argv[2]
    b = open(ROMD, "rb").read(); rom = pickle.load(open(TUILES, "rb"))
    blocs = plans_arcade(b, fin); print("blocs scroll2", blocs)
    plan = scroll2(b, rom, blocs); psp = carte_psp(n)
    idx = collections.defaultdict(list)                  # index grossier : nb de couleurs distinctes
    for p, t in psp.items(): idx[len(set(t))].append(p)
    par_bloc = collections.defaultdict(collections.Counter)
    for (cx, cy), (bi, t) in plan.items():
        k = len(set(t))
        if k < 4: continue
        for kk in range(2, k + 1):
            for (px_, py_) in idx[kk]:
                if fonction(t, psp[(px_, py_)]): par_bloc[bi][((px_ - cx) % 64, py_ - cy)] += 1
    for bi in sorted(par_bloc):
        print("bloc %2d (n°%3d) :" % (bi, blocs[bi]), par_bloc[bi].most_common(3))
