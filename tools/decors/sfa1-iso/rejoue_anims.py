#!/usr/bin/env python3
"""rejoue_anims.py DONNEES PLANCHES : rejoue HORS JEU les animations de décor extraites de l'ISO (sfa1_anims.json) :
pour chaque animation, une planche (cadres côte à côte, durée en tics sous chaque cadre) et un GIF animé à la vitesse
du jeu (8 tics pour 7 images à 59,64 Hz) -> PLANCHES/anims/*.png|gif.
  - tuiles (Ken, Sodom, Guy) : fenêtre de scroll2 autour de l'objet, blocs écrits comme le moteur ($15DD8) ;
  - palettes (Ryu, Guy) : zone de scroll2 qui utilise la palette animée, couleurs de l'entrée du cadre ;
  - foule de Charlie : fenêtre de scroll2 décalée de Y (4 bandes, période en tics) ;
  - sprites : descripteurs (types 0 et 2) posés aux positions (x, y) de l'ISO, palettes OBJ 24-31 du décor."""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rendu_sfa1 import Donnees, couleur
DON, PL = sys.argv[1], sys.argv[2]; OUTD = os.path.join(PL, "anims"); os.makedirs(OUTD, exist_ok=True)
D = Donnees(DON); A = json.load(open(os.path.join(DON, "sfa1_anims.json")))
Z = np.load(os.path.join(DON, "pixels_obj.npz")); OBJ = {int(c): p for c, p in zip(Z["codes"], Z["pixels"])}
TIC_MS = 1000 * 7 / 8 / 59.637
def sortie(nom, images, durees, echelle=2):
    w = max(i.width for i in images); h = max(i.height for i in images)
    pl = Image.new("RGB", (len(images) * (w + 4), h + 14), (40, 40, 40)); dr = ImageDraw.Draw(pl)
    for k, (im, d) in enumerate(zip(images, durees)):
        pl.paste(im, (k * (w + 4), 0)); dr.text((k * (w + 4) + 2, h + 2), "%d:%d" % (k, d), fill=(255, 255, 0))
    pl.save(os.path.join(OUTD, nom + ".png"))
    g = [i.resize((i.width * echelle, i.height * echelle), Image.NEAREST) for i in images]
    g[0].save(os.path.join(OUTD, nom + ".gif"), save_all=True, append_images=g[1:], loop=0,
              duration=[max(20, int(round(d * TIC_MS))) for d in durees])
def suite(nom, i):
    sq = A["tables"][nom]["anims"][str(i)]; return sq["cadres"]       # un tour de boucle (reprise incluse)
def objets(classe):
    for d in D.J["decors"]:
        for o in d["objets"]:
            if int(o["routine"][1:3], 16) == classe: yield d, o
fait = []
# --- tuiles --------------------------------------------------------------------------------------------------------
for d, o in list(objets(0x14)) + list(objets(0x2E)):
    s = d["decor"]; idx, rgba = D.image_plan(s, 2, opaque=True); C, T = D.grille(s, 2)
    pal = np.array([couleur(m) for m in D.palettes(s, 2)], np.uint8)
    for i in o["anim"]["anims"]:
        Y = o["y"] + (0x200 if (o["routine"], i) == ("$2E00", 6) else 0)
        r0, c0 = ((-Y) >> 4) & 0x3F, (o["x"] >> 4) & 0x3F; cad = suite("tuiles_s2", i); ims = []
        for c in cad:
            b = A["blocs_tuiles"][c["ptr"]]; im = idx.copy()
            for cc in range(b["colonnes"]):
                for r in range(b["lignes"]):
                    q = cc * b["lignes"] + r; code = (b["codes"][q] + 0xD400) & 0xFFFF; at = b["attrs"][q]
                    t = D.P2[code - D.lo2].astype(np.int32)
                    if at & 0x20: t = t[:, ::-1]
                    if at & 0x40: t = t[::-1, :]
                    rr, ccol = (r0 + r) & 0x3F, (c0 + cc) & 0x3F
                    im[rr * 16:rr * 16 + 16, ccol * 16:ccol * 16 + 16] = (at & 0x1F) * 16 + t
            b0 = A["blocs_tuiles"][cad[0]["ptr"]]
            y0, x0 = max(0, (r0 - 2) * 16), max(0, (c0 - 2) * 16); y1, x1 = y0 + (b0["lignes"] + 4) * 16, x0 + (b0["colonnes"] + 4) * 16
            ims.append(Image.fromarray(pal[im[y0:y1, x0:x1]]))
        nom = "tuiles_%s_%s_anim%d" % (d["perso"].replace(".", ""), o["routine"][1:], i)
        sortie(nom, ims, [c["duree"] for c in cad]); fait.append(nom)
# --- palettes --------------------------------------------------------------------------------------------------------
for d, o in objets(0x33):
    s = d["decor"]; idx, _ = D.image_plan(s, 2, opaque=True); base = D.palettes(s, 2)
    for i in o["anim"]["anims"]:
        cad = suite("palettes", i); ent0 = A["palettes"][cad[0]["ptr"]][0]; p14 = ent0["pal"]
        ys, xs = np.nonzero((idx >> 4) == p14)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1; ims = []
        for c in cad:
            pal = list(base)
            for e in A["palettes"][c["ptr"]]:
                for j in range(16): pal[e["pal"] * 16 + j] = 0xF000 | e["couleurs"][j]
            P = np.array([couleur(m) for m in pal], np.uint8); ims.append(Image.fromarray(P[idx[y0:y1, x0:x1]]))
        nom = "palette_%s_anim%d" % (d["perso"], i); sortie(nom, ims, [c["duree"] for c in cad], 1); fait.append(nom)
# --- foule de Charlie --------------------------------------------------------------------------------------------------
fo = A["foule_charlie"]
for d in D.J["decors"]:
    if d["gest_s2"]["mode"] != "charlie": continue
    idx, rgba = D.image_plan(d["decor"], 2, opaque=True); pal = np.array([couleur(m) for m in D.palettes(d["decor"], 2)], np.uint8)
    ims = [Image.fromarray(pal[np.roll(idx, y, axis=0)[0x310:0x3F0, 0x100:0x400]]) for y in fo["y"]]
    sortie("foule_Charlie", ims, [fo["periode"]] * 4, 1); fait.append("foule_Charlie")
# --- sprites ---------------------------------------------------------------------------------------------------------------
def dessine(e, palobj, dp=0):
    pieces = []
    for code, at, (x, y) in zip(e["codes"], e["attrs"], e["xy"]):
        nx, ny = ((at >> 8) & 0xF) + 1, ((at >> 12) & 0xF) + 1
        for by in range(ny):
            for bx in range(nx):
                t = OBJ[(code + 0x400 + bx + 16 * by) & 0xFFFF]
                px = bx if not at & 0x20 else nx - 1 - bx; py = by if not at & 0x40 else ny - 1 - by
                if at & 0x20: t = t[:, ::-1]
                if at & 0x40: t = t[::-1, :]
                pieces.append((x + 16 * px, y + 16 * py, ((at + dp) & 0x1F), t))
    return pieces
deja = set()
for d in D.J["decors"]:
    palobj = [int(d["pal_obj24"][4 * k:4 * k + 4], 16) | 0xF000 for k in range(128)]
    for o in d["objets"]:
        t = o["anim"]["table"]
        if not t or not t.startswith("spr_"): continue
        dp = int(o["brut"][24:26], 16) if o["routine"].startswith("$15") else 0
        for i in o["anim"]["anims"]:
            cle = (t, i, dp, d["pal_obj24"])
            if cle in deja: continue
            deja.add(cle); cad = suite(t, i); P = [dessine(A["descripteurs"][c["ptr"]], palobj, dp) for c in cad]
            al = [p for f in P for p in f]
            if not al: continue
            xa, ya = min(p[0] for p in al), min(p[1] for p in al); xb, yb = max(p[0] for p in al) + 16, max(p[1] for p in al) + 16
            ims = []
            for f in P:
                im = np.zeros((yb - ya, xb - xa, 3), np.uint8); im[:] = (0, 60, 60)
                for x, y, pa, tt in f:
                    cols = np.array([couleur(palobj[((pa - 24) % 8) * 16 + j]) for j in range(16)], np.uint8)
                    m = tt != 15; sub = im[y - ya:y - ya + 16, x - xa:x - xa + 16]; sub[m] = cols[tt[m]]
                ims.append(Image.fromarray(im))
            nom = "sprites_%s_%s_%s_anim%d" % (d["perso"].replace(".", ""), o["routine"][1:], t[4:], i)
            sortie(nom, ims, [c["duree"] for c in cad]); fait.append(nom)
print("%d animations rejouées -> %s" % (len(fait), OUTD)); print("\n".join(fait))
