#!/usr/bin/env python3
"""controle_tuiles_anim.py sfa1|sfa2 BLOCS ENTREES PLANS — chaque case de chaque bloc d'animation de tuiles du lot :
tuile lue dans la FAMILLE (sfa*_plans.bin) au code famille rangé dans le lot = tuile de l'extraction au code d'origine."""
import os, sys, json, struct
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from relit_blocs import charge
from format_zone import decode, Lecteur
jeu, B, E, PL = sys.argv[1:5]
lot = charge(jeu, B, E); fam = open(PL, "rb").read(); J = lot.decors; L = lot.L; d = lot.data
P = {p: np.load(os.path.join(E, "pixels_s%d.npy" % p)) for p in ((2,) if jeu == "sfa1" else (1, 2, 3))}
def t16(o): return decode(fam[o:o + 128])
def t32(o): return np.stack([t16(o + 128 * q) for q in range(4)]).reshape(64, 16).reshape(32, 32)
def t8(o): return decode(fam[o:o + 64] + bytes(64))[:8, :8]
if jeu == "sfa1":
    ORG = int(J["plans"]["charge_en"], 16); adr = {2: lambda cf: (int(J["plans"]["base_s2"], 16) << 16) + 128 * cf - ORG}
    lo = {2: J["codes_s2"][0]}; lire = {2: t16}
else:
    F = J["famille"]; sz = {1: 64, 2: 128, 3: 512}
    adr = {p: (lambda cf, p=p: F["s%d" % p]["decalage"] + sz[p] * cf) for p in (1, 2, 3)}
    lo = {1: 0, 2: J["codes_s2"][0], 3: J["codes_s3"][0]}; lire = {1: t8, 2: t16, 3: t32}
E227 = None
if jeu == "sfa2":
    e = np.fromfile("<workspace>/work/decors_sfa2_iso/donnees/e227.bin", np.uint8); E227 = np.stack([e & 0xF, e >> 4], -1).reshape(-1)
T32 = {}
if jeu == "sfa2":
    sys.path.insert(0, "<workspace>/work/decors_sfa2_iso/outils"); sys.path.insert(0, "<workspace>/github/src/hsfa")
    import anthgfx; from xdata import XData
    for k_, m_, p_ in anthgfx.tiles(XData(iso="<workspace>/iso/SFA_Anthology_AllUnlocked_WORK.iso").entree(226)):
        if k_ == 2: T32[m_] = p_ if p_ is not None else np.full((32, 32), 15, np.uint8)
def ref(p, c):
    """tuile d'extraction au code d'origine c (tableaux de pixels, sinon mémoire e227 : s1 élément 8×8 c, s2 élément c + $3600)"""
    if jeu == "sfa1": j = c + 0xD400 - lo[2]
    else: j = c - lo[p]
    if 0 <= j < len(P[p]): return P[p][j]
    if E227 is not None and p == 1: return E227[64 * c:64 * c + 64].reshape(8, 8)
    if E227 is not None and p == 2: return E227[256 * (c + 0x3600):256 * (c + 0x3600) + 256].reshape(16, 16)
    if p == 3 and c + 0x900 in T32: return T32[c + 0x900]
    return None
o = lot.sec["BLOC"]; fin = lot.sec["COUL"]; n = ok = hors = 0
while o < fin:
    o = (o + 3) & ~3
    if o >= fin or L.u32(o) == 0: break
    p = d[o + 10]; k = L.u16(o + 12)
    for i in range(k):
        cf = L.u16(o + 14 + 4 * i); c = lot.code_orig(p, cf); n += 1; r = ref(p, c)
        if r is None: hors += 1; continue
        ok += bool((lire[p](adr[p](cf)) == r).all())
    o += 14 + 4 * k
print("%s : cases des blocs d'animation %d ; tuile famille = tuile d'extraction : %d ; sans référence  : %d" % (jeu, n, ok, hors))
