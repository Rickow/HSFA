"""Aller-retour sur Ryu : sortie du convertisseur vs données réelles de l'Anthology (ro3, banque e258)."""
import sys, struct, collections
sys.path.insert(0, "../frames289"); sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
from convert_max import convert
from frame_map import build_map
from scripts import pairs
from cps2_tiles import cps2_pixels
C = convert("pl00")
M = build_map(); A = M["A"]
loc = open(__import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "mame", "banques", "f258.bin"), "rb").read()
l2c = struct.unpack(f"<{len(loc)//4}I", loc)
CP = cps2_pixels()
def anth_tile(l):
    c = l2c[l] if l < len(l2c) else 0xFFFFFFFF
    return None if c == 0xFFFFFFFF else bytes(15 - v for v in CP[c])
def placed(objs, tilefn):
    s = set()
    for dx, dy, code, attr in objs:
        w, h = ((attr >> 8) & 15) + 1, ((attr >> 12) & 15) + 1
        for j in range(h):
            for i in range(w):
                ii = (w - 1 - i) if attr & 0x20 else i
                jj = (h - 1 - j) if attr & 0x40 else j
                t = tilefn(code + ii + 16 * jj)
                if t is not None and len(set(t)) > 1:
                    s.add((dx + 16*i, dy + 16*j, hash(t), attr & 0x60))
    return s
mine = lambda l: C["bank"][l] if l < len(C["bank"]) else None
# (a) frames
ident = tot = 0; sims = []
for n, rec in M["psp2rec"].items():
    a, b = placed(C["frames"][n]["objs"], mine), placed(A[rec], anth_tile)
    if not a or not b: continue
    tot += 1; sim = len(a & b) / len(a | b); sims.append(sim); ident += sim == 1.0
print(f"(a) frames converties vs Anthology : {tot} comparées, IDENTIQUES (pixels, positions, miroirs) : {ident} ({100*ident/tot:.0f} %), ≥ 0,9 : {sum(s >= 0.9 for s in sims)}")
T_ok = sum(1 for f in C["frames"] if f["T"] == sum((((a >> 8) & 15) + 1) * (((a >> 12) & 15) + 1) for *_, a in f["objs"]))
print(f"    budget T cohérent : {T_ok}/{len(C['frames'])}")
# (b) scripts : pas convertis vs pas Anthology appariés
conv = {off: run for off, run in C["scripts"]}
st_tot = st_ok = dur_ok = box_ok = 0
for p, a, steps in pairs():
    run = conv.get(p)
    if not run or len(run) != len(steps): continue
    for cs, (ps, as_) in zip(run, steps):
        st_tot += 1
        d = (cs["ctl"] & 0xFF) == as_["dur"] and bool(cs["ctl"] & 0x8000) == as_["end"]
        bx = (cs["A"], cs["B"]) == (as_["attr"], as_["w3"])
        dur_ok += d; box_ok += bx; st_ok += d and bx
print(f"(b) pas de scripts appariés : {st_tot} ; durée + fin identiques {dur_ok} ; mots de collision identiques {box_ok} ; tout identique {st_ok} ({100*st_ok/max(st_tot,1):.0f} %)")
