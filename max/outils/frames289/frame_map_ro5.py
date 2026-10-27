"""Correspondance frame PSP de Ryu <-> frame de Ryu dans UPPER (module ro5), même méthode que frame_map.py (ro3) :
tuiles placées (x, y, code ROM) ; ro5 : positions dans le bloc externe $B04000 (ext_b04000.bin du banc ro5 d'HSFA),
codes locaux -> codes ROM par la banque de Ryu d'Upper (banques/f355.bin du banc ro5)."""
import os, sys, struct, collections, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anth_frames import expand
from frame_map import norm
from rosetta_ryu import build
W5 = os.environ.get("HSFA_WORK_RO5", __import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "mame_ro5"))
P5 = open(os.path.join(os.environ["ANTHOLOGY_DIR"], "decompressed", "ro5_usa_prog68k.bin"), "rb").read()
F5 = open(os.path.join(W5, "ext_b04000.bin"), "rb").read()
BASE, FBASE = 0x1F0000, 0xB04000
L355 = struct.unpack("<%dI" % (os.path.getsize(os.path.join(W5, "banques", "f355.bin")) // 4), open(os.path.join(W5, "banques", "f355.bin"), "rb").read())
def records5():
    W = struct.unpack_from("<%dI" % (len(P5) // 4), P5); out = {}
    for w in W:
        o = w - BASE
        if not (0 <= o < len(P5) - 8) or o % 2 or o in out: continue
        t, T, n1 = struct.unpack_from("<3H", P5, o)
        if t != 2 or n1 >= 64: continue
        p = (o + 6 + 3) & ~3; ptr = struct.unpack_from("<I", P5, p)[0]
        if not (FBASE <= ptr < FBASE + len(F5) - 4 * (n1 + 1)): continue
        objs = struct.unpack_from("<%dH" % (2 * (n1 + 1)), P5, p + 4)
        pos = [struct.unpack_from(">hh", F5, ptr - FBASE + 4 * i) for i in range(n1 + 1)]   # ext_*.bin du banc : mots gros-boutistes
        out[o] = [(dx, dy, c, a) for (dx, dy), c, a in zip(pos, objs[0::2], objs[1::2])]
    return out
def build_map5():
    R = build(); p2c = R["psp2code"]
    A = records5()
    AE = {}
    for o, v in A.items():
        s = {(x, y, L355[l]) for x, y, l in expand(v) if l < len(L355) and L355[l] != 0xFFFFFFFF}
        if len(s) >= 2: AE[o] = norm(s)
    inv = collections.defaultdict(set)
    for o, s in AE.items():
        for (_, _, c) in s: inv[c].add(o)
    psp2rec = {}
    for n, fr in enumerate(R["F"]):
        s = set()
        for k, cell in enumerate(fr["cells"]):
            if cell is None: continue
            cx, cy = (k % fr["w"]) * 32 - fr["a"], (k // fr["w"]) * 32 - fr["c"]
            for q, (qx, qy) in enumerate(((0, 0), (0, 16), (16, 0), (16, 16))):
                if cell[1] & 0x80: qx = 16 - qx
                if cell[1] & 0x40: qy = 16 - qy
                c = p2c[cell[0] * 4 + q]
                if c is not None: s.add((cx + qx, cy + qy, c))
        s = norm(s)
        if len(s) < 2: continue
        cand = collections.Counter(o for (_, _, c) in s for o in inv[c]).most_common(40)
        sim, o = max(((len(s & AE[o]) / len(s | AE[o]), o) for o, _ in cand), default=(0, None))
        if sim >= 0.9: psp2rec[n] = (o, round(sim, 3))
    return psp2rec, len(A)
if __name__ == "__main__":
    m, nA = build_map5()
    print("frames de type 2 dans ro5 :", nA, "; frames PSP de Ryu appariées :", len(m))
    json.dump({str(k): ["%x" % v[0], v[1]] for k, v in m.items()}, open(os.path.expanduser("~/.cache/sfa3max/frame_map_ro5_ryu.json"), "w"))
