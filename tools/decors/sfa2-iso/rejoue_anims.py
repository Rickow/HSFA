#!/usr/bin/env python3
"""rejoue_anims.py DONNEES PLANCHES : rejoue HORS JEU les animations de décor de SFA2 extraites de l'ISO
(sfa2_anims.json, pixels_obj.npz, e227, e226) : pour chaque animation, une planche PNG (cadres côte à côte, n° et
durée sous chaque cadre) et un GIF à la vitesse du jeu (durées en IMAGES à 59,64 Hz ; classes au pas par tic : voir
RAPPORT §5) -> PLANCHES/anims/*.png|gif. Reprise de decors_sfa1/outils/rejoue_anims.py (copie : sfa1_ref/).
  - tuiles s1 / s2 / s3 : blocs du cadre (pixels e227 / e226, attributs, palettes du décor qui l'utilise) ;
  - palettes (tables et listes) : nuanciers des entrées du cadre (16 couleurs par destination) ;
  - sprites : descripteurs de l'ISO (types 0, 2, 4) posés aux positions de l'ISO, palettes de sprites du décor."""
import os, sys, json, re, collections
import numpy as np
from PIL import Image, ImageDraw
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ICI)
from rendu_sfa2 import couleur
DON, PL = sys.argv[1], sys.argv[2]; OUTD = os.path.join(PL, "anims"); os.makedirs(OUTD, exist_ok=True)
A = json.load(open(os.path.join(DON, "sfa2_anims.json"))); J = json.load(open(os.path.join(DON, "sfa2_decors.json")))
Z = np.load(os.path.join(DON, "pixels_obj.npz")); OBJ = {(b, int(c)): p for b, c, p in zip(Z["banque"], Z["codes"], Z["px"])}
e = np.fromfile(os.path.join(DON, "e227.bin"), np.uint8); P8 = np.stack([e & 0xF, e >> 4], -1).reshape(-1)
sys.path.insert(0, os.environ.get("HSFA_SRC", "<workspace>/github/src/hsfa"))
IMG_MS = 1000 / 59.637
DEC = J["decors"]; PERSO = {d["perso"]: d["decor"] for d in DEC}
VIDE = np.full((16, 16), 15, np.uint8)

def pal(s, plan):
    h = DEC[s]["pal_%s" % plan]; n = len(h) // 4
    return np.array([couleur(int(h[4 * i:4 * i + 4], 16) | 0xF000) for i in range(n)], np.uint8)

def tuile(plan, code):
    if plan == 1: return P8[64 * code:64 * code + 64].reshape(8, 8) if 64 * code + 64 <= len(P8) else np.full((8, 8), 15, np.uint8)
    if plan == 2:
        el = code + 0x3600
        return P8[256 * el:256 * el + 256].reshape(16, 16) if 256 * el + 256 <= len(P8) else VIDE
    return T32.get(code + 0x900, np.full((32, 32), 15, np.uint8))

def image_bloc(plan, bl, P):
    ts = {1: 8, 2: 16, 3: 32}[plan]; nl, nc = bl["lignes"], bl["colonnes"]
    im = np.zeros((nl * ts, nc * ts, 4), np.uint8); im[..., :3] = 40; im[..., 3] = 255
    for k, (c, at) in enumerate(bl["paires"]):
        col, row = divmod(k, nl); t = tuile(plan, c)
        if at & 0x20: t = t[:, ::-1]
        if at & 0x40: t = t[::-1, :]
        rgb = P[((at & 0x1F) * 16 + t.astype(int)) % len(P)]
        m = t != 15; sub = im[row * ts:(row + 1) * ts, col * ts:(col + 1) * ts]; sub[m, :3] = rgb[m]
    return Image.fromarray(im, "RGBA").convert("RGB")

def image_sprites(spr, P):
    if not spr: return Image.new("RGB", (16, 16), (40, 40, 40))
    pts = {}
    for s in spr:
        at = s["attr"]; w, h = ((at >> 8) & 15) + 1, ((at >> 12) & 15) + 1; fx, fy = at & 0x20, at & 0x40
        for j in range(h):
            for i in range(w):
                t = OBJ.get((s.get("banque", "e249"), s["code"] + i + 16 * j), VIDE)
                if fx: t = t[:, ::-1]
                if fy: t = t[::-1, :]
                ox = s["x"] + 16 * ((w - 1 - i) if fx else i); oy = s["y"] + 16 * ((h - 1 - j) if fy else j)
                for yy, xx in zip(*np.nonzero(t != 15)): pts[(ox + xx, oy + yy)] = (at & 0x1F) * 16 + int(t[yy, xx])
    xs = [p[0] for p in pts] or [0]; ys = [p[1] for p in pts] or [0]
    im = np.full((max(ys) - min(ys) + 1, max(xs) - min(xs) + 1, 3), 40, np.uint8)
    for (x, y), v in pts.items(): im[y - min(ys), x - min(xs)] = P[v % len(P)]
    return Image.fromarray(im, "RGB")

def image_entrees(ent):
    im = Image.new("RGB", (16 * 6, 6 * len(ent) + 1), (40, 40, 40)); dr = ImageDraw.Draw(im)
    for r, e_ in enumerate(ent):
        for q, c in enumerate(e_["couleurs"][:15]): dr.rectangle([6 * q, 6 * r, 6 * q + 5, 6 * r + 5], fill=couleur(c | 0xF000))
    return im

def sortie(nom, images, durees, echelle=2):
    W = max(i.width for i in images); H = max(i.height for i in images)
    pl = Image.new("RGB", (min(len(images), 16) * (W + 4), ((len(images) + 15) // 16) * (H + 14)), (20, 20, 20)); dr = ImageDraw.Draw(pl)
    for k, (im, d) in enumerate(zip(images, durees)):
        x, y = (k % 16) * (W + 4), (k // 16) * (H + 14)
        pl.paste(im, (x, y)); dr.text((x + 2, y + H + 2), "%d:%s" % (k, d if d else "∞"), fill=(255, 255, 0))
    pl.save(os.path.join(OUTD, nom + ".png"))
    g = [i.resize((max(1, i.width * echelle), max(1, i.height * echelle)), Image.NEAREST) for i in images]
    cv = [Image.new("RGB", (W * echelle, H * echelle), (40, 40, 40)) for _ in g]
    for c, i in zip(cv, g): c.paste(i, (0, 0))
    cv[0].save(os.path.join(OUTD, nom + ".gif"), save_all=True, append_images=cv[1:], loop=0,
               duration=[max(20, int(round((d or 120) * IMG_MS))) for d in durees])

# décor qui utilise chaque table / animation (objets de l'ISO, rôles des classes, canaux)
UTIL = collections.defaultdict(set)
for d in DEC[:18]:
    for o in d["objets"]:
        an = o.get("anim") or {}
        if an.get("table"):
            for i in (an["anims"] if isinstance(an.get("anims"), list) else [None]): UTIL[(an["table"], i)].add(d["decor"])
for k, c in A["classes"].items():
    m = [p for p in PERSO if p.split()[0] in c["role"]]
    t = next((x for x, v in A["tables"].items() if v["arcade"] == c["table"]), None)
    if t and m: UTIL[(t, None)].add(PERSO[m[0]])
for c in A["canaux_s2"].values():
    m = [p for p in PERSO if p in c["role"]]
    if m and c.get("canaux"):
        t = next(x for x, v in A["tables"].items() if v["arcade"] == "$23F110")
        for ch in c["canaux"]: UTIL[(t, ch["anim"])].add(PERSO[m[0]])
def decor_de(t, i):
    s = UTIL.get((t, i)) or UTIL.get((t, None))
    return min(s) if s else 0

import anthgfx
from xdata import XData
T32 = {}
if os.path.exists(os.path.join(DON, "e226.bin")): buf = open(os.path.join(DON, "e226.bin"), "rb").read()
else: buf = XData(iso="<workspace>/iso/SFA_Anthology_AllUnlocked_WORK.iso").entree(226)
for k, m, p in anthgfx.tiles(buf):
    if k == 2: T32[m] = p if p is not None else np.full((32, 32), 15, np.uint8)

n = collections.Counter()
for T, t in A["tables"].items():
    eng = t["moteur"]
    for i, an in t["anims"].items():
        s = decor_de(T, int(i)); cad = an["cadres"]; ims = []
        if eng.startswith("tuiles"):
            plan = int(eng[-1]); P = pal(s, "s%d" % plan)
            ims = [image_bloc(plan, A["blocs"][c["ptr"]], P) for c in cad]
        elif eng == "palette":
            ims = [image_entrees(A["entrees_palette"][c["ptr"]]) for c in cad]
        else:
            P = np.concatenate([pal(s, "spr"), np.zeros((512, 3), np.uint8) + 128])
            ims = [image_sprites((A["descripteurs"].get(c["ptr"]) or {}).get("sprites") or [], P) for c in cad]
        nom = "%s_%s_%s_a%02d" % (eng, t["arcade"][1:], DEC[s]["perso"].split()[0].replace(".", ""), int(i))
        sortie(nom, ims, [c["duree"] for c in cad]); n[eng] += 1
for la, l_ in A["listes_palette"].items():
    ims = [image_entrees(A["entrees_palette"][c["ptr"]]) for c in l_["cadres"]]
    sortie("liste_palette_%s" % l_["arcade"][1:], ims, [c["duree"] for c in l_["cadres"]]); n["liste_palette"] += 1
# sinus de Gen : profil du rowscroll (48 lignes) sur 32 pas de phase
sin = A["sinus_gen"]["valeurs"]; ims = []
for ph in range(0, 0x200, 0x10):
    im = Image.new("RGB", (40, 48), (40, 40, 40)); dr = ImageDraw.Draw(im)
    for j in range(24):
        v = sin[((ph + 0xA0 * j) & 0x1FE) // 2] >> 12
        for y in (23 - j, 24 + j): dr.line([(20, y), (20 + 6 * v, y)], fill=(255, 200, 0)); dr.point((20 + 6 * v, y), fill=(255, 255, 255))
    ims.append(im)
sortie("sinus_gen_rowscroll", ims, [1] * len(ims), echelle=4); n["sinus"] += 1
print("planches/anims :", dict(n), "->", OUTD)
