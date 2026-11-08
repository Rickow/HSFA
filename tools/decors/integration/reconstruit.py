#!/usr/bin/env python3
"""reconstruit.py sfa1|sfa2 BLOCS ENTREES PLANS SORTIE — reconstruit, DEPUIS LE LOT et la banque OBJ produits par
convertit_decors.py (et la famille de tuiles des plans, chargée à l'adresse de la région graphique), un dossier
« donnees » au format des extracteurs (decors_sfa1 / decors_sfa2_iso) : JSON, bibliothèques, pixels des plans
(DÉCODÉS de la famille de tuiles, par le code famille que donnent les blocs), pixels_obj.npz (DÉCODÉS de la banque OBJ
par la table des rangées du lot). Les outils de rendu d'origine (rendu_sfa1, planches_sfa2, rejoue_anims), lancés sur ce
dossier, doivent redonner les planches au pixel près.

ENTREES ne sert qu'à renum.json (SFA2 : bijection code d'origine <-> code famille publiée avec sfa2_plans.bin) et aux
bornes des tableaux de pixels (codes_s*)."""
import os, sys, json, struct
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from relit_blocs import charge
from format_zone import decode

jeu, B, E, PLANS, OUT = sys.argv[1:6]
os.makedirs(OUT, exist_ok=True)
lot = charge(jeu, B, E)
json.dump(lot.decors, open(os.path.join(OUT, "%s_decors.json" % jeu), "w"))
json.dump(lot.anims, open(os.path.join(OUT, "%s_anims.json" % jeu), "w"))
fam = open(PLANS, "rb").read()
J = lot.decors

def ecrit_bib(nom, p, nt):
    n = max(lot.bib[p]) + 1; b = bytearray(4 * nt * n)
    for blk, paires in lot.bib[p].items():
        for k, (c, a) in enumerate(paires): struct.pack_into(">HH", b, 4 * nt * blk + 4 * k, c, a)
    open(os.path.join(OUT, nom), "wb").write(bytes(b))

ecrit_bib("bib_s2.bin", 2, 256); ecrit_bib("bib_s3.bin", 3, 64)
P_ent = {p: np.load(os.path.join(E, "pixels_s%d.npy" % p)) for p in ((2, 3) if jeu == "sfa1" else (1, 2, 3))}
def tuile16(o): return decode(fam[o:o + 128])
def tuile32(o): return np.stack([tuile16(o + 128 * q) for q in range(4)]).reshape(64, 16).reshape(32, 32)
def tuile8(o): return decode(fam[o:o + 64] + bytes(64))[:8, :8]
stats = {}
if jeu == "sfa1":
    ORG = int(J["plans"]["charge_en"], 16); b2 = int(J["plans"]["base_s2"], 16) << 16; b3 = int(J["plans"]["base_s3"], 16) << 16
    lo2, lo3 = J["codes_s2"][0], J["codes_s3"][0]
    P2 = np.full_like(P_ent[2], 15); P3 = np.full_like(P_ent[3], 15)
    for i in range(len(P2)): P2[i] = tuile16(b2 + (lo2 + i) * 128 - ORG)
    for i in range(len(P3)): P3[i] = tuile32(b3 + (lo3 + i) * 512 - ORG)
    np.save(os.path.join(OUT, "pixels_s2.npy"), P2); np.save(os.path.join(OUT, "pixels_s3.npy"), P3)
    stats["pixels identiques à l'extraction"] = [bool((P2 == P_ent[2]).all()), bool((P3 == P_ent[3]).all())]
else:
    open(os.path.join(OUT, "cel_s1.bin"), "wb").write(b"")
    nb1 = max(lot.bib[1]) + 1; b = bytearray(128 * nb1)
    for blk, cels in lot.bib[1].items():
        for k, c in enumerate(cels): struct.pack_into(">H", b, 128 * blk + 2 * k, c)
    open(os.path.join(OUT, "bib_s1.bin"), "wb").write(bytes(b))
    nc = max(lot.cel) + 1; c1 = bytearray(64 * nc)
    for c, paires in lot.cel.items():
        for i, (code, at) in enumerate(paires): struct.pack_into(">HH", c1, 64 * c + 4 * i, code, at)
    open(os.path.join(OUT, "cel_s1.bin"), "wb").write(bytes(c1))
    F = J["famille"]; ren = json.load(open(os.path.join(E, "renum.json")))
    lo = {1: 0, 2: J["codes_s2"][0], 3: J["codes_s3"][0]}
    ega = []
    for p, t in ((1, tuile8), (2, tuile16), (3, tuile32)):
        P = P_ent[p].copy(); off = F["s%d" % p]["decalage"]; sz = {1: 64, 2: 128, 3: 512}[p]; n = 0
        for c, i in ren["s%d" % p].items():
            k = int(c) - lo[p]
            if 0 <= k < len(P): P[k] = t(off + sz * i); n += 1
        np.save(os.path.join(OUT, "pixels_s%d.npy" % p), P)
        ega.append([n, bool((P == P_ent[p]).all())])
    stats["tuiles de la famille décodées / tableaux identiques"] = ega
    for f in ("parallaxe.json", "effets.json", "renum.json"):
        if os.path.exists(os.path.join(E, f)): open(os.path.join(OUT, f), "wb").write(open(os.path.join(E, f), "rb").read())
# banque OBJ -> pixels_obj.npz (mêmes clés que l'extraction)
z = np.load(os.path.join(E, "pixels_obj.npz"))
codes = []; px = []; ban = []
for r, (b, ro_) in enumerate(lot.rangs):
    for k in range(16):
        codes.append(16 * ro_ + k); ban.append(b); px.append(decode(lot.obj_bin[128 * (16 * r + k):128 * (16 * r + k) + 128]))
if jeu == "sfa1":
    ref = {int(c): p for c, p in zip(z["codes"], z["pixels"])}
    keep = [i for i, c in enumerate(codes) if c in ref]
    np.savez_compressed(os.path.join(OUT, "pixels_obj.npz"), codes=np.array([codes[i] for i in keep]), pixels=np.stack([px[i] for i in keep]))
    stats["tuiles OBJ identiques"] = sum(bool((px[i] == ref[codes[i]]).all()) for i in keep), len(ref)
else:
    ref = {(str(b), int(c)): p for b, c, p in zip(z["banque"], z["codes"], z["px"])}
    keep = [i for i, c in enumerate(codes) if (ban[i], c) in ref]
    np.savez_compressed(os.path.join(OUT, "pixels_obj.npz"), banque=np.array([ban[i] for i in keep]),
                        codes=np.array([codes[i] for i in keep]), px=np.stack([px[i] for i in keep]))
    stats["tuiles OBJ identiques"] = sum(bool((px[i] == ref[(ban[i], codes[i])]).all()) for i in keep), len(ref)
print(jeu, json.dumps(stats, ensure_ascii=False))
