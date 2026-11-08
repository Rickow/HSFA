#!/usr/bin/env python3
"""planches_sfa2.py DONNEES MAME_DIR PLANCHES — planches de contrôle et de vues des décors SFA2 rendus depuis l'ISO.
Registres de plans (scroll1/2/3 X/Y, rowscroll) = ceux relevés dans MAME (sonde) aux 3 positions de caméra (butée gauche,
centre, butée droite), pour que la comparaison se fasse à caméra identique.
  sXX_vues.png        : rangée 1 = 3 vues 4:3 rendues depuis l'ISO ; rangée 2 = 16:9 (512 px) aux deux butées, sans
                        complément (noir = hors du plan peint / hors du monde scroll1 ; bord droit de scroll2 replié)
  planche_controle_mame_iso.png : par décor (vue centre) : SFA2 joué (MAME, avec sprites) | MAME sans sprites |
                        rendu ISO | différences (rouge)
  planche_sfa2_iso.png : les 18 décors, vue centre
  largeurs.tsv        : marges peintes de chaque plan au-delà de la vue 4:3 aux butées (pour le 16:9 à 512 px)"""
import os, sys, csv
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_mame as M, rendu_sfa2 as RS
D = RS.Donnees(sys.argv[1]); MD = sys.argv[2]; OUT = sys.argv[3]; os.makedirs(OUT, exist_ok=True)
CT = {(r["decor"], r["vue"]): r for r in csv.DictReader(open(os.path.join(MD, "..", "controle", "controle.tsv")), delimiter="\t")}
def regs_de(s, d, k):
    A = d["A"]; kx, ky = k % 10, k // 10
    rows = M.mots(d["gfx"], A[4], 1024).astype(np.int64) if A[0x11] & 1 else None
    if rows is not None: rows = np.where(rows >= 0x8000, rows - 0x10000, rows)
    return {1: ((A[6] & 0x1FF) + 512 * kx, (A[7] & 0x1FF) + 512 * ky), 2: (A[8], A[9]), 3: (A[10], A[11])}, rows, A[0x10]
def peint(s, p, y0, wrapW):
    """colonnes peintes du plan p dans les 224 lignes visibles (à partir de la ligne y0 du plan)"""
    idx, rgba = D.image_plan(s, p); H, W = idx.shape
    lig = [(y0 + 16 + y) % H if p != 1 else y0 + 16 + y for y in range(224)]
    lig = [l for l in lig if 0 <= l < H]
    cols = (rgba[lig, :, 3] > 0).any(0)
    return np.where(cols)[0], W
larg = ["decor\tperso\tplan\tvue_gauche_x\tvue_droite_x\tpeint_min\tpeint_max\tlargeur_plan\tmarge_gauche\tmarge_droite\tcomplet_16_9"]
L_ctrl = []; L_centre = []
for s in range(18):
    stg = "%02X" % (2 * s); dec = D.decor(s)
    f = os.path.join(MD, "out", "stg%s_dmp.bin" % stg)
    if not os.path.exists(f): continue
    dumps = {d["tag"].strip(): d for d in M.lit(f)}
    snaps = sorted(os.listdir(os.path.join(MD, "snap", "stg" + stg, "sfa2u")))
    vues = {}; v169 = {}
    for i, tag in enumerate(("gauche", "droite", "centre")):
        k = int(CT[("$" + stg, tag)]["k_s1"]) if ("$" + stg, tag) in CT else 0
        regs, rows, rso = regs_de(s, dumps[tag + "-1"], k)
        vues[tag] = RS.ecran(D, s, regs, rows, rso, s1_anneau=True)
        if tag != "centre":
            cv = np.zeros((224, 512), bool)
            v169[tag] = RS.ecran(D, s, regs, rows, rso, largeur=512, dx=64, sans_repli=True, couverture=cv)
            nc = ~cv.all(0)      # colonnes où un pixel n'est couvert par aucun plan (hors du décor peint)
            cal = int(np.argmin(nc[:64][::-1])) if False else 0
            g_ = 0
            while g_ < 64 and nc[g_]: g_ += 1
            d_ = 0
            while d_ < 64 and nc[511 - d_]: d_ += 1
            vues.setdefault("_c", {})[tag] = (g_, d_)
            # marges peintes par plan (scroll2 : X + rowscroll de la ligne de base ; scroll1 : monde ; scroll3 : X)
            for p in (1, 2, 3):
                X, Y = regs[p]
                if p == 2 and rows is not None: X += int(rows[(16 + rso + 112) & 0x3FF])
                cols, W = peint(s, p, Y, None)
                x0 = X + 64
                if p != 1: x0 %= W
                vues.setdefault("_m", {}).setdefault(p, {})[tag] = (x0, cols, W)
    cg, cd = vues["_c"]["gauche"][0], vues["_c"]["droite"][1]
    larg.append("$%s\t%s\tcouverture\t\t\t\t\t\t%d\t%d\t%s" % (stg, dec["perso"], cg, cd, "oui" if cg == 0 and cd == 0 else "calage %d/%d px" % (cg, cd)))
    for p in (1, 2, 3):
        (xg, cols, W), (xd, _, _) = vues["_m"][p]["gauche"], vues["_m"][p]["droite"]
        if len(cols) == 0: continue
        mg = xg - cols.min(); md = cols.max() + 1 - (xd + 384)
        larg.append("$%s\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%s" % (stg, dec["perso"], p, xg, xd, cols.min(), cols.max(), W, mg, md,
                    "oui" if mg >= 64 and md >= 64 else "non"))
    pl = np.full((224 * 2 + 8, 384 * 3 + 16, 3), 40, np.uint8)
    for i, tag in enumerate(("gauche", "centre", "droite")): pl[:224, i * 392:i * 392 + 384] = vues[tag]
    pl[232:, :512] = v169["gauche"]; pl[232:, 520:1032] = v169["droite"]
    im = Image.fromarray(pl); dr = ImageDraw.Draw(im)
    dr.text((4, 2), "$%s %s (D4 $%02X) - ISO ro2 : gauche / centre / droite (4:3) ; 16:9 512 px aux butees" % (stg, dec["perso"], 0x50 + 2 * s), fill=(255, 255, 0))
    im.save(os.path.join(OUT, "s%s_vues.png" % stg))
    jeu = np.asarray(Image.open(os.path.join(MD, "snap", "stg" + stg, "sfa2u", snaps[0])).convert("RGB"))
    m = np.asarray(Image.open(os.path.join(MD, "snap", "stg" + stg, "sfa2u", snaps[3])).convert("RGB"))
    dif = np.any(vues["centre"] != m, -1)
    L_ctrl.append((stg, dec["perso"], np.concatenate([jeu, m, vues["centre"], np.where(dif[..., None], [255, 0, 0], m // 3).astype(np.uint8)], 1), int(dif.sum())))
    L_centre.append((stg, dec["perso"], vues["centre"]))
g = np.full((len(L_ctrl) * 232, 4 * 384, 3), 30, np.uint8)
for i, (_, _, v, _) in enumerate(L_ctrl): g[i * 232:i * 232 + 224] = v
im = Image.fromarray(g); dr = ImageDraw.Draw(im)
for i, (stg, nom, _, nd) in enumerate(L_ctrl):
    dr.text((4, i * 232 + 2), "$%s %s : MAME en jeu | MAME sans sprites | ISO | ecart %d px" % (stg, nom, nd), fill=(255, 255, 0))
im.save(os.path.join(OUT, "planche_controle_mame_iso.png"))
g = np.full((6 * 232, 3 * 392, 3), 30, np.uint8)
for i, (stg, nom, v) in enumerate(L_centre):
    r, c = divmod(i, 3); g[r * 232:r * 232 + 224, c * 392:c * 392 + 384] = v
im = Image.fromarray(g); dr = ImageDraw.Draw(im)
for i, (stg, nom, v) in enumerate(L_centre):
    r, c = divmod(i, 3); dr.text((c * 392 + 4, r * 232 + 2), "$%s %s" % (stg, nom), fill=(255, 255, 0))
im.save(os.path.join(OUT, "planche_sfa2_iso.png"))
open(os.path.join(OUT, "largeurs.tsv"), "w").write("\n".join(larg) + "\n")
print("\n".join(larg))
