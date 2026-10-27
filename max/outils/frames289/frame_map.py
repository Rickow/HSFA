"""Correspondance frame PSP de Ryu <-> enregistrement de frame de l'Anthology (similarité de tuiles placées)."""
import sys, collections, pickle, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anth_frames import records, expand
from rosetta_ryu import build
import paths
CACHE = os.path.join(paths.CACHE, "frame_map_ryu.pkl")
def norm(s):
    if not s: return frozenset()
    mx, my = min(x for x, _, _ in s), min(y for _, y, _ in s)
    return frozenset((x - mx, y - my, l) for x, y, l in s)
def build_map():
    if os.path.exists(CACHE): return pickle.load(open(CACHE, "rb"))
    R = build(); p2c, c2l = R["psp2code"], R["code2local"]
    A = records(); AE = {o: norm(expand(v)) for o, v in A.items()}
    inv = collections.defaultdict(set)
    for o, s in AE.items():
        for (_, _, l) in s: inv[l].add(o)
    psp2rec, rec2psp = {}, {}
    for n, fr in enumerate(R["F"]):
        s = set()
        for k, cell in enumerate(fr["cells"]):
            if cell is None: continue
            cx, cy = (k % fr["w"]) * 32 - fr["a"], (k // fr["w"]) * 32 - fr["c"]
            for q, (qx, qy) in enumerate(((0, 0), (0, 16), (16, 0), (16, 16))):
                if cell[1] & 0x80: qx = 16 - qx
                if cell[1] & 0x40: qy = 16 - qy
                c = p2c[cell[0]*4 + q]
                if c is not None and c in c2l: s.add((cx + qx, cy + qy, c2l[c]))
        s = norm(s)
        if len(s) < 2: continue
        cand = collections.Counter(o for (_, _, l) in s for o in inv[l]).most_common(40)
        sim, o = max(((len(s & AE[o]) / len(s | AE[o]), o) for o, _ in cand), default=(0, None))
        if sim >= 0.9:
            psp2rec[n] = o; rec2psp.setdefault(o, n)
    M = {"psp2rec": psp2rec, "rec2psp": rec2psp, "A": A}
    pickle.dump(M, open(CACHE, "wb")); return M
if __name__ == "__main__":
    M = build_map(); print(len(M["psp2rec"]), "frames PSP appariées ;", len(M["rec2psp"]), "enregistrements")
