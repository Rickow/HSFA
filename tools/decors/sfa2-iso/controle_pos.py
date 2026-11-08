#!/usr/bin/env python3
"""controle_pos.py [DONNEES] [MAME] [STG…] (côté ORACLE, local ; agent decors_restes, 07/11) : POSITIONS des sprites de
décor de SFA2 au pixel contre l'OBJ de MAME (sonde mame/obj_sfa2.sh -> mame/out_pos/stgXX_pos.txt, lignes « d »).

Pour CHAQUE dessin d'un objet des pools de décor (état de l'objet, ancre D4 du jeu, entrées OBJ réellement écrites) :
  (1) image : les entrées écrites, rendues avec les tuiles de l'arcade (ROM, code OBJ + $10000) et rapportées à l'ancre,
      = le descripteur de l'ISO du cadre courant (ro2 redécoupé, tuiles e249 / e226) rendu au même endroit, retourné selon
      $B(A6), palettes comprises ($C / $D(A6)) : comparaison PIXEL PAR PIXEL (indice de couleur et palette) ;
  (2) ancre ($13028) : Y0 = $100 − (Y [+ $14E(A5) si $F] − plan.Y) ; X0 = X [+ $144(A6) si $8 ≤ 4] − plan.X + $40 − d0
      (plan = $E(A6) : 4/8/12 -> $FF8200/$FF8280/$FF8300 ; 0 : écran) ; d0 = correction de rowscroll lue par la sonde.
Le descripteur ISO est trouvé par le cadre arcade $1C(A6) (parcours parallèle des tables, arcade_anims.walk).
Sortie : controle/controle_pos.tsv + résumé."""
import os, sys, json, glob, collections
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ICI)
import arcade_anims as AA
args = list(sys.argv[1:])
DON = args.pop(0) if args and os.path.isdir(args[0]) else os.path.join(os.path.dirname(ICI), "donnees")
MAME = args.pop(0) if args and os.path.isdir(args[0]) else os.path.join(os.path.dirname(ICI), "mame")
FILTRE = [a.upper() for a in args]
A = json.load(open(os.path.join(DON, "sfa2_anims.json")))
Z = np.load(os.path.join(DON, "pixels_obj.npz")); PX = {(b, c): p for b, c, p in zip(Z["banque"].tolist(), Z["codes"].tolist(), Z["px"])}
RAW = np.load("<workspace>/work/carto_sfa2/gfx/sfa2_tiles_raw.npy", mmap_mode="r")

def rendu(sprites, tuile):
    """image {(x, y): (palette, pixel)} d'une liste de sprites {code, attr, x, y[, banque]} ; retournements CPS2"""
    img = {}
    for s in sprites:
        at = s["attr"]; w, h = ((at >> 8) & 15) + 1, ((at >> 12) & 15) + 1; fx, fy = at & 0x20, at & 0x40; pal = at & 0x1F
        for j in range(h):
            for i in range(w):
                t = np.asarray(tuile((s["code"] + i + 16 * j) & 0xFFFF, s.get("banque", "e249")))
                if fx: t = t[:, ::-1]
                if fy: t = t[::-1, :]
                ox = s["x"] + 16 * ((w - 1 - i) if fx else i); oy = s["y"] + 16 * ((h - 1 - j) if fy else j)
                for yy, xx in zip(*np.nonzero(t != 15)): img[(ox + int(xx), oy + int(yy))] = (pal, int(t[yy, xx]))
    return img
def tuile_iso(c, b): return PX.get((b, c), np.full((16, 16), 15, np.uint8))
def tuile_arc(c, b): return RAW[0x10000 + c]

# cadre arcade -> descripteur ISO
C2D = {}
for T, t in A["tables"].items():
    if t["moteur"] != "sprite": continue
    ra = int(t["arcade"][1:], 16)
    for i, an in t["anims"].items():
        sa, _ = AA.walk(ra, int(i), 16)
        if not sa: continue
        for c, fa in zip(an["cadres"], sa): C2D.setdefault(fa[0], c["ptr"])
for e in A.get("cadres_fixes", {}).values(): C2D.setdefault(int(e["arcade"][1:], 16), e["ptr"])     # cadres posés par lea
PLAN = {4: 0, 8: 1, 12: 2}
def s10(v):
    v &= 0x3FF
    return v - 0x400 if v >= 0x200 else v

def lit(fn):
    """lignes d : 1 k, 2 pool, 3 fente, 4 classe, 5 sous, 6 cadre, 7 X, 8 Y, 9 $8, 10 $A, 11 $B, 12 $C, 13 $D, 14 $E, 15 $F,
    16 $144, 17 $26, 18 $18, 19 $1A, 20 $20, 21 $22, 22 $24, 23 d0, 24 $14E(A5), 25-30 plans s1/s2/s3 (X, Y), 31 D4, 32 entrées"""
    R = []
    for x in open(fn):
        v = x.split()
        if v[0] != "d": continue
        h = [int(t, 16) for t in v[25:31]]; ent = v[32] if len(v) > 32 else ""
        R.append(dict(k=int(v[1]) + 1, pool=v[2], fente=int(v[3]), cl=int(v[4], 16), ss=int(v[5], 16), cadre=int(v[6], 16) & 0xFFFFFF,
                      X=int(v[7], 16), Y=int(v[8], 16), b8=int(v[9], 16), ba=int(v[10], 16), bb=int(v[11], 16),
                      bc=int(v[12], 16), bd=int(v[13], 16), be=int(v[14], 16), bf=int(v[15], 16), x144=int(v[16], 16),
                      w20=int(v[20], 16), w22=int(v[21], 16), w24=int(v[22], 16), d0=int(v[23]), s14e=int(v[24], 16),
                      cam=[(h[0], h[1]), (h[2], h[3]), (h[4], h[5])], D4=int(v[31], 16), recouvert=ent.startswith("X"),
                      ent=[tuple(int(t, 16) for t in e.split(",")) for e in ent.lstrip("X").split(";") if e]))
    return R

def ancre(o):
    y = o["Y"] + (o["s14e"] if o["bf"] else 0); x = o["X"] + (o["x144"] if o["b8"] <= 4 else 0)
    if o["be"] == 0: return (x + 0x40) & 0xFFFF, (0x100 - y) & 0xFFFF
    px, py = o["cam"][PLAN[o["be"]]]
    return (x - px + 0x40 - o["d0"]) & 0xFFFF, (0x100 - (y - py)) & 0xFFFF

C_ISO = {}; C_ARC = {}
def image_iso(o):
    dp = C2D.get(o["cadre"])
    if dp is None: return None
    e = A["descripteurs"][dp]
    cle = (dp, o["bb"] & 3, o["bc"], o["bd"])
    if cle not in C_ISO:
        spr = []
        for s in e.get("sprites", []):
            at = s["attr"]
            if o["bc"]:                    # palette : $D, ou $D + palette du descripteur si $C < 0
                at = (at & 0xFFE0) | ((o["bd"] + ((at & 0x1F) if o["bc"] & 0x80 else 0)) & 0x1F)
            spr.append(dict(s, attr=at))
        img = rendu(spr, tuile_iso)
        fx, fy = o["bb"] & 1, o["bb"] & 2   # $B : bit 0 = X, bit 1 = Y (<< 5 -> attributs $20 / $40)
        img = {((-1 - x) if fx else x, (-1 - y) if fy else y): v for (x, y), v in img.items()}
        C_ISO[cle] = (img, e["type"])
    return C_ISO[cle]
def image_arc(o):
    X0, Y0 = o["D4"] & 0xFFFF, o["D4"] >> 16
    rel = tuple((s10(x - X0), s10(y - Y0), c, a) for x, y, c, a in o["ent"])
    if rel not in C_ARC:
        C_ARC[rel] = rendu([dict(code=c, attr=a, x=x, y=y) for x, y, c, a in rel], tuile_arc)
    return C_ARC[rel]

lignes = []; bilan = collections.Counter()
def note(stg, quoi, ok, detail):
    r = "OK" if ok else ("NON CONTRÔLÉ" if ok is None else "ÉCART")
    lignes.append("%s\t%s\t%s\t%s" % (stg, quoi, r, detail)); bilan[r] += 1
    print("%s %-30s %-5s %s" % (stg, quoi, r, detail))
DEC = {d["decor"]: d for d in json.load(open(os.path.join(DON, "sfa2_decors.json")))["decors"]}
TOT = collections.Counter()
for fn in sorted(glob.glob(os.path.join(MAME, "out_pos", "stg*_pos.txt"))):
    stg = os.path.basename(fn)[3:5]
    if FILTRE and stg not in FILTRE: continue
    nom = "%s %s" % (stg, DEC.get(int(stg, 16) // 2, {}).get("perso", "?"))
    R = lit(fn)
    par = collections.Counter(); ec = collections.Counter(); ex = {}; px = collections.Counter(); anc = collections.Counter()
    anc_ec = collections.Counter(); anc_ex = {}; rec = collections.Counter(); hors = collections.Counter(); hors_ex = {}
    cams = collections.defaultdict(set); types = collections.defaultdict(set)
    for o in R:
        cle = "%s $%02X%02X" % (o["pool"], o["cl"], o["ss"])
        if o["recouvert"]: rec[cle] += 1; continue
        ii = image_iso(o)
        if ii is None:
            hors[cle] += 1; hors_ex.setdefault(cle, "cadre $%06X" % o["cadre"]); continue
        img_i, ty = ii; types[cle].add(ty)
        img_a = image_arc(o)
        if img_i == img_a:
            par[cle] += 1; px[cle] += len(img_a); cams[cle].add(o["cam"][1][0])
        else:
            ec[cle] += 1
            if cle not in ex:
                d1 = set(img_i.items()) ^ set(img_a.items())
                ex[cle] = "img %d cadre $%06X type %d : %d px différents (ISO %d / MAME %d)" % (o["k"], o["cadre"], ty, len(d1), len(img_i), len(img_a))
        X0, Y0 = ancre(o)
        if (X0, Y0) == (o["D4"] & 0xFFFF, o["D4"] >> 16): anc[cle] += 1
        else:
            anc_ec[cle] += 1
            anc_ex.setdefault(cle, "img %d : formule (%X, %X) / jeu (%X, %X)" % (o["k"], X0, Y0, o["D4"] & 0xFFFF, o["D4"] >> 16))
    for cle in sorted(set(par) | set(ec) | set(hors)):
        n, m = par[cle], ec[cle]
        TOT["dessins"] += n; TOT["pixels"] += px[cle]; TOT["ecarts"] += m; TOT["ancre_ok"] += anc[cle]; TOT["ancre_ko"] += anc_ec[cle]
        TOT["hors"] += hors[cle]
        note(nom, "positions %s" % cle, (m == 0 and anc_ec[cle] == 0 and n > 0) if n + m else None,
             "%d dessins identiques au pixel (%d px), %d écarts%s ; ancre = formule %d / %d%s ; types %s ; caméra s2 X %s ; "
             "recouverts %d ; cadre hors des tables de l'ISO %d%s"
             % (n, px[cle], m, (" (" + ex[cle] + ")") if m else "", anc[cle], anc[cle] + anc_ec[cle],
                (" (" + anc_ex[cle] + ")") if anc_ec[cle] else "", sorted(types[cle]),
                ("%03X-%03X" % (min(cams[cle]), max(cams[cle]))) if cams[cle] else "-", rec[cle], hors[cle],
                (" (" + hors_ex[cle] + ")") if hors[cle] else ""))
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(DON)), "controle"), exist_ok=True)
open(os.path.join(os.path.dirname(os.path.abspath(DON)), "controle", "controle_pos.tsv"), "w").write(
    "decor\tcontrole\tresultat\tdetail\n" + "\n".join(lignes) + "\n")
print("TOTAL : " + ", ".join("%s %d" % kv for kv in sorted(TOT.items())))
print("BILAN : " + ", ".join("%s %d" % kv for kv in sorted(bilan.items())))
