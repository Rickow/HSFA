"""Scripts d'animation : Anthology (pas de 5 x u32) et PSP (entrée [6], pas de 5 x u16), appariés par classes d'images."""
import sys, struct, os, collections, pickle
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
from plpac import split
from frame_map import build_map, norm
from anth_frames import expand
CACHE = os.path.join(paths.CACHE, "scripts_ryu.pkl")
def build():
    if os.path.exists(CACHE): return pickle.load(open(CACHE, "rb"))
    M = build_map(); A = M["A"]; p2r = M["psp2rec"]
    cls = {}; k2i = {}
    for o, objs in A.items(): cls[o] = k2i.setdefault(norm(expand(objs)), len(k2i))
    P = open(__import__("os").path.join(__import__("os").environ.get("ANTHOLOGY_DIR", "anthology_extract"), "decompressed", "ro3_usa_prog68k.bin"), "rb").read()
    W = struct.unpack_from(f"<{len(P)//4}I", P)
    steps = {}
    for i in range(len(W) - 5):
        o = W[i+1] - 0x1F0000
        if o in A and W[i+4] == 0 and (W[i] & 0x7F00) == 0:
            steps[4*i] = dict(cls=cls[o], dur=W[i] & 0xFF, end=bool(W[i] & 0x8000), ctl=W[i], attr=W[i+2], w3=W[i+3], rec=o)
    AS, seen = [], set()
    for a in sorted(steps):
        if a in seen: continue
        run, b2 = [], a
        while b2 in steps:
            seen.add(b2); run.append(steps[b2])
            if steps[b2]["end"]: break
            b2 += 20
        if len(run) >= 2: AS.append((a, run))
    E = split(open(os.path.join(paths.pac_dir(), "pl00_e.pac"), "rb").read()); b = E[6][1]
    H = struct.unpack_from(f"<{len(b)//2}H", b)
    ok = lambda i: i + 4 < len(H) and H[i+2] < 471 and (H[i] <= 0xFF or H[i] & 0x8000) and H[i+3] in (0, 1)
    PS, i = [], 0
    while i < len(H) - 5:
        if ok(i) and ok(i + 5):
            run, j = [], i
            while ok(j):
                d, fl, fr, one, col = H[j:j+5]
                run.append(dict(cls=cls.get(p2r.get(fr)), dur=d & 0xFF, end=bool(d & 0x8000), flag=fl, frame=fr, col=col, off=2*j))
                j += 5
                if d & 0x8000: break
            PS.append((2*i, run)); i = j
        else: i += 1
    R = {"AS": AS, "PS": PS, "cls": cls}
    pickle.dump(R, open(CACHE, "wb")); return R
def pairs():
    """pas alignés (PSP, Anthology) des scripts au même enchaînement de frames."""
    R = build(); key = lambda run: tuple(s["cls"] for s in run)
    Aidx = collections.defaultdict(list)
    for a, run in R["AS"]: Aidx[key(run)].append((a, run))
    out = []
    for p, run in R["PS"]:
        if None in key(run) or len(run) < 2 or key(run) not in Aidx: continue
        for a, arun in Aidx[key(run)]:
            out.append((p, a, list(zip(run, arun))))
    return out
