#!/usr/bin/env python3
"""oracle_anims.py (côté ORACLE, local) : contrôle STATIQUE des animations extraites de l'ISO (donnees/sfa2_anims.json,
pixels_obj.npz, e227) contre le programme et la ROM graphique de l'arcade sfa2u (carto_sfa2), cadre par cadre :
  - durées, drapeaux, reprises (parcours arcade parallèle) ;
  - tuiles : blocs (lignes, colonnes, attributs) et PIXELS de chaque tuile (e227 élément code + $3600 / ROM VRAM +
    $10000 pour s2 ; codes s1 / s3 identiques à l'arcade) ;
  - palettes : 16 couleurs de chaque entrée (couleur 15 exclue : le portage y range le n° de palette) ;
  - sprites : IMAGE de chaque descripteur rendue des deux côtés (ISO : descripteur ro2 redécoupé + positions ro2 +
    tuiles e249 ; arcade : descripteur + positions $9F25C + ROM, code OBJ = code + $10000), comparée au pixel.
Écrit controle/oracle_anims.tsv. Usage : oracle_anims.py [donnees]"""
import os, sys, json, collections
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ICI)
import arcade_anims as AA
DON = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(ICI), "donnees")
A = json.load(open(os.path.join(DON, "sfa2_anims.json")))
Z = np.load(os.path.join(DON, "pixels_obj.npz")); PX = {(b, c): p for b, c, p in zip(Z["banque"].tolist(), Z["codes"].tolist(), Z["px"])}
RAW = np.load("<workspace>/work/carto_sfa2/gfx/sfa2_tiles_raw.npy", mmap_mode="r")
e = np.fromfile(os.path.join(DON, "e227.bin"), np.uint8); P8 = np.stack([e & 0xF, e >> 4], -1).reshape(-1)

def rendu(sprites, tuile):
    """image (dict (x, y) -> pixel opaque) d'une liste de sprites {code, attr, x, y} ; retournements CPS2"""
    img = {}
    for s in sprites:
        at = s["attr"]; w, h = ((at >> 8) & 15) + 1, ((at >> 12) & 15) + 1; fx, fy = at & 0x20, at & 0x40
        for j in range(h):
            for i in range(w):
                t = np.array(tuile(s["code"] + i + 16 * j, s.get("banque", "e249")))
                if fx: t = t[:, ::-1]
                if fy: t = t[::-1, :]
                ox = s["x"] + 16 * ((w - 1 - i) if fx else i); oy = s["y"] + 16 * ((h - 1 - j) if fy else j)
                for yy, xx in zip(*np.nonzero(t != 15)): img[(ox + xx, oy + yy)] = int(t[yy, xx])
    return img

def desc_arcade(p):
    t = AA.w(p); spr = []
    if t == 0:
        n, at, pi = AA.w(p + 2), AA.w(p + 4), AA.w(p + 6); lp = AA.l(0x9F25C + pi) & 0xFFFFFF
        for k in range(n): spr.append(dict(code=AA.w(p + 8 + 2 * k), attr=at, x=AA.sw(lp + 4 * k), y=AA.sw(lp + 4 * k + 2)))
    elif t == 2:
        n1, pi = AA.w(p + 4), AA.w(p + 6); lp = AA.l(0x9F25C + pi) & 0xFFFFFF
        for k in range(n1 + 1): spr.append(dict(code=AA.w(p + 8 + 4 * k), attr=AA.w(p + 10 + 4 * k), x=AA.sw(lp + 4 * k), y=AA.sw(lp + 4 * k + 2)))
    elif t == 4:
        n1 = AA.w(p + 4)
        for k in range(n1 + 1):
            q = p + 6 + 8 * k
            spr.append(dict(code=(AA.w(q) - 0x5C00) & 0xFFFF, attr=AA.w(q + 2), x=AA.sw(q + 4), y=AA.sw(q + 6), banque="e226"))
    elif t == 10: return []
    else: return None
    return spr

def tuile_iso(c, b): return PX.get((b, c), np.full((16, 16), 15, np.uint8))
def tuile_arc(c, b): return RAW[0x10000 + c]

res = collections.Counter(); ecarts = []
for T, t in A["tables"].items():
    ra = int(t["arcade"][1:], 16); eng = t["moteur"]; fs = AA.FS[eng]
    for i, an in t["anims"].items():
        sa, ba = AA.walk(ra, int(i), fs)
        for k, (c, fa) in enumerate(zip(an["cadres"], sa)):
            nom = "%s/%s/%d" % (t["arcade"], i, k)
            if (c["duree"], c["drapeaux"]) != (fa[1], fa[2]): res["cadre_ko"] += 1; ecarts.append(nom + " durée"); continue
            res["cadres"] += 1
            if eng.startswith("tuiles"):
                b = A["blocs"][c["ptr"]]; ba_ = AA.bloc_tuiles(fa[3])
                if (b["lignes"], b["colonnes"]) != (ba_["lignes"], ba_["colonnes"]): res["bloc_ko"] += 1; ecarts.append(nom + " bloc"); continue
                for (cr, ar), (ca, aa) in zip(b["paires"], ba_["paires"]):
                    if ca == 0x20 and cr == 0x20: res["case_vide"] += 1; continue
                    if ar != aa: res["attr_ko"] += 1; ecarts.append(nom + " attr"); continue
                    if eng == "tuiles_s2":
                        ok = (np.array(RAW[((ca - 0x5C00) & 0xFFFF) + 0x10000]) == P8[256 * (cr + 0x3600):256 * (cr + 0x3601)].reshape(16, 16)).all()
                    else: ok = cr == ca
                    res["tuile_ok" if ok else "tuile_ko"] += 1
                    if not ok: ecarts.append(nom + " tuile %X/%X" % (ca, cr))
            elif eng == "palette":
                ea = AA.entrees_palette(fa[3])
                for er, (d, b_, s) in zip(A["entrees_palette"][c["ptr"]], ea):
                    base = AA.BANQUES_PAL[b_ // 4] + (s & 0xFFE0)
                    ca = [AA.w(base + 2 * j) for j in range(15)]
                    ok = (er["dest"], er["banque"], er["source"]) == (d, b_, s) and er["couleurs"][:15] == ca
                    res["entree_ok" if ok else "entree_ko"] += 1
                    if not ok: ecarts.append(nom + " entrée")
            elif eng == "sprite" and c["duree"] and fa[3] < 0x400000:
                dr = A["descripteurs"].get(c["ptr"]); sa_ = desc_arcade(fa[3])
                if dr is None or dr["sprites"] is None or sa_ is None: res["desc_autre"] += 1; continue
                ok = rendu(dr["sprites"], tuile_iso) == rendu(sa_, tuile_arc)
                res["image_ok" if ok else "image_ko"] += 1
                if not ok: ecarts.append(nom + " image")
for la, l_ in A["listes_palette"].items():
    a = int(l_["arcade"][1:], 16); x = a; k = 0
    for c in l_["cadres"]:
        d, f, p = AA.w(x), AA.D[x + 2], AA.l(x + 4) & 0xFFFFFF
        if (c["duree"], c["drapeaux"]) != (d, f): res["cadre_ko"] += 1; ecarts.append(l_["arcade"] + " durée"); break
        res["cadres"] += 1
        for er, (dd, b_, s) in zip(A["entrees_palette"][c["ptr"]], AA.entrees_palette(p)):
            base = AA.BANQUES_PAL[b_ // 4] + (s & 0xFFFE)
            ok = er["couleurs"][:15] == [AA.w(base + 2 * j) for j in range(15)]
            res["entree_ok" if ok else "entree_ko"] += 1
            if not ok: ecarts.append(l_["arcade"] + " entrée")
        x = (AA.l(x + 8) & 0xFFFFFF) if f & 0x80 else x + 8
os.makedirs(os.path.join(os.path.dirname(ICI), "controle"), exist_ok=True)
with open(os.path.join(os.path.dirname(ICI), "controle", "oracle_anims.tsv"), "w") as f:
    f.write("contrôle\tnombre\n"); [f.write("%s\t%d\n" % kv) for kv in sorted(res.items())]
    f.write("# écarts\n"); [f.write(x + "\n") for x in ecarts]
print(dict(res)); print("écarts :", len(ecarts), ecarts[:15])
