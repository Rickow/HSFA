"""Scripts d'animation des persos rangés dans l'EBOOT (en plus de ceux de l'entrée [6] du conteneur).
Tables de pointeurs relogés (.rel.data) dont au moins la moitié des cibles sont des scripts (pas de 5 x u16 terminés par
0x8000), attribuées au perso dont le MODULE de code charge l'adresse de la table (paire lui/addiu).
Résultat type : Ryu 165 scripts (12 tables), Eagle 187, Maki 138, Yun 462 (dont la table 0x2A9EC4 de 272), Ingrid 158 ;
moteur commun 3 901."""
import sys, struct, collections, json, functools
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import paths
from relocs import pointer_words, img, TEXT_END
from charcode2 import P as PW
ROOTS = 0x215040
@functools.lru_cache(None)
def _index():
    P = pointer_words()
    root = lambda c: PW[ROOTS + 4*c]
    order = sorted({(root(c), c) for c in range(42)})
    bounds = [(a, order[i+1][0] if i + 1 < len(order) else 0x1caf0c, c) for i, (a, c) in enumerate(order)]
    own = lambda addr: next((c for a, b, c in bounds if a <= addr < b), None)
    PA = sorted(P); runs, cur = [], [PA[0]]
    for x in PA[1:]:
        if x == cur[-1] + 4: cur.append(x)
        else: runs.append(cur); cur = [x]
    runs.append(cur)
    W = struct.unpack_from(f"<{TEXT_END//4}I", img, 0)
    s16 = lambda x: x - 0x10000 if x & 0x8000 else x
    refs = collections.defaultdict(collections.Counter)
    for k, w in enumerate(W):
        if w >> 26 != 0x0F: continue
        rt, hi = (w >> 16) & 31, w & 0xFFFF
        for m in range(k + 1, min(k + 8, len(W))):
            x = W[m]
            if (x >> 21) & 31 == rt and x >> 26 in (0x09, 0x23, 0x21, 0x25):
                refs[((hi << 16) + s16(x & 0xFFFF)) & 0xFFFFFFFF][own(4*k)] += 1
                break
    out = collections.defaultdict(list)
    for r in runs:
        tg = [P[a] for a in r]
        if len(r) < 2 or sum(1 for t in tg if parse(t)) < 0.5 * len(r): continue
        users = collections.Counter()
        for a in range(r[0] - 0x10, r[-1] + 4, 2): users.update(refs.get(a, {}))
        for u in users: out[u].append((r[0], tg))
    return out
def parse(o, maxs=80):
    run = []
    for n in range(maxs):
        if o + 10*n + 10 > len(img): return None
        d, fl, fr, one, col = struct.unpack_from("<5H", img, o + 10*n)
        if not (fr < 2000 and (d <= 0xFF or d & 0x8000)): return None
        run.append({"ctl": (d & 0xFF) | (0x8000 if d & 0x8000 else 0), "flag": fl, "frame": fr, "one": one, "col": col})
        if d & 0x8000: return run
    return None
def scripts_for(cid):
    """-> [(adresse de table, index, adresse du script, pas)] pour le perso cid."""
    out = []
    for taddr, targets in _index().get(cid, []):
        for k, t in enumerate(targets):
            s = parse(t)
            if s: out.append((taddr, k, t, s))
    return out
if __name__ == "__main__":
    for cid, nm in ((0x00, "Ryu"), (0x26, "Eagle"), (0x27, "Maki"), (0x28, "Yun"), (0x29, "Ingrid")):
        S = scripts_for(cid)
        print(f"{nm:<7} {len(S)} scripts EBOOT valides, {sum(len(s) for *_, s in S)} pas, tables {sorted({hex(t) for t, *_ in S})[:6]}")
