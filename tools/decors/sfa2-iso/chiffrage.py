#!/usr/bin/env python3
"""chiffrage.py DONNEES MAME_DIR — tailles par décor et totales (données 68K au format SFA3 / Upper de la cible, tuiles de
plans, tuiles de sprites de décor vues en jeu) pour le plan d'intégration (RAPPORT §4). Écrit DONNEES/chiffrage.json."""
import os, sys, json, struct, hashlib
import numpy as np
DON, MD = sys.argv[1], sys.argv[2]
J = json.load(open(os.path.join(DON, "sfa2_decors.json")))
bib1 = open(os.path.join(DON, "bib_s1.bin"), "rb").read()
# format cible (moteur SFA3 / Upper, DECOR-SFA2 §1) : bloc s1 128 o, cellule 64 o, bloc s2 768 o, bloc s3 192 o,
# listes 128 o (la routine copie 128 o), palettes 3 × 1 Ko + 7 × 32 o, objets 16 o, CPS-B 4 o, entrées de tables
T = dict(b1=128, cel=64, b2=768, b3=192, liste=128 * 3, pal=3 * 1024 + 224, obj=16, divers=64)
tot = dict(b1=set(), cel=set(), b2=set(), b3=set()); lignes = []; somme = 0
for d in J["decors"][:18]:
    b1 = set(d["liste_s1"]); cel = {c for b in b1 for c in struct.unpack_from(">64H", bib1, 128 * b)}
    b2 = set(d["liste_s2"]); b3 = set(d["liste_s3"])
    tot["b1"] |= b1; tot["cel"] |= cel; tot["b2"] |= b2; tot["b3"] |= b3
    o = len(b1) * T["b1"] + len(cel) * T["cel"] + len(b2) * T["b2"] + len(b3) * T["b3"] + T["liste"] + T["pal"] + len(d["objets"]) * T["obj"] + T["divers"]
    somme += o
    # sprites de décor vus en jeu (sonde, 300 images de combat ; borne basse) : tuiles 16×16 = code + blocs nx × ny
    spr = set(); f = os.path.join(MD, "out", "stg%s_obj.txt" % d["val"][1:])
    if os.path.exists(f):
        for l in open(f):
            c, pal, nx, ny, n = l.split(); c = int(c, 16)
            for y in range(int(ny)):
                for x in range(int(nx)):
                    t = (c & ~0xF | ((c + x) & 0xF)) + 0x10 * y
                    if 0x14800 <= t < 0x1B000: spr.add(t)      # zone des sprites de décor de SFA2 (CARTE-sfa2 §2.3)
    gfx = d["tuiles_s1"] * 64 + d["tuiles_s2"] * 128 + d["tuiles_s3"] * 512
    lignes.append(dict(decor=d["val"], d4=d["d4"], perso=d["perso"], donnees_68k=o, cellules=len(cel), blocs=[len(b1), len(b2), len(b3)],
                       tuiles=[d["tuiles_s1"], d["tuiles_s2"], d["tuiles_s3"]], gfx_plans=gfx, sprites_decor_tuiles=len(spr),
                       sprites_decor_octets=128 * len(spr), objets=len(d["objets"])))
uni = len(tot["b1"]) * T["b1"] + len(tot["cel"]) * T["cel"] + len(tot["b2"]) * T["b2"] + len(tot["b3"]) * T["b3"] + 18 * (T["liste"] + T["pal"] + T["divers"]) + sum(len(d["objets"]) for d in J["decors"][:18]) * T["obj"]
# dédoublonnage des tuiles AVEC retournements (X, Y, XY) : gain possible sur la ROM graphique
P = {p: np.load(os.path.join(DON, "pixels_s%d.npy" % p)) for p in (1, 2, 3)}
ren = json.load(open(os.path.join(DON, "renum.json")))
gain = {}
for p, k, lo in ((1, "s1", 0), (2, "s2", J["codes_s2"][0]), (3, "s3", J["codes_s3"][0])):
    vus = set(); n = 0
    for c in ren[k]:
        t = P[p][int(c) - lo]
        hs = [hashlib.md5(np.ascontiguousarray(v).tobytes()).digest() for v in (t, t[:, ::-1], t[::-1, :], t[::-1, ::-1])]
        if not any(h in vus for h in hs): n += 1
        vus.add(hs[0])
    gain[k] = dict(distinctes=len(ren[k]), avec_retournements=n)
res = dict(par_decor=lignes, somme_donnees=somme, union_donnees=uni, blocs_union=[len(tot["b1"]), len(tot["cel"]), len(tot["b2"]), len(tot["b3"])],
           gfx_plans=J["famille"], dedoublonnage_retournements=gain)
json.dump(res, open(os.path.join(DON, "chiffrage.json"), "w"), indent=1)
for l in lignes:
    print("%s %-8s 68K %6d o  cellules %4d  blocs %s  gfx plans %7d o  sprites décor %4d tuiles (%6d o)  objets %2d" % (
        l["decor"], l["perso"], l["donnees_68k"], l["cellules"], l["blocs"], l["gfx_plans"], l["sprites_decor_tuiles"], l["sprites_decor_octets"], l["objets"]))
print("somme par décor %d o ; union (blocs partagés une fois) %d o ; blocs union s1/cel/s2/s3 %s" % (somme, uni, res["blocs_union"]))
print("sprites de décor (borne basse) : %d tuiles" % sum(l["sprites_decor_tuiles"] for l in lignes))
print("dédoublonnage avec retournements :", gain)
