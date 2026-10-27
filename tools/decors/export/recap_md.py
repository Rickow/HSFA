#!/usr/bin/env python3
"""Tableau recapitulatif (Markdown) des decors exportes, depuis out/decors/recap.json -> out/decors/RECAP.md"""
import json
D = "<workspace>/work/decors_ws/out/decors"
R = json.load(open(D + "/recap.json"))
PL = ("scroll1", "scroll2", "scroll3")


def fp(v):
    return v.split(" ")[0] if isinstance(v, str) else "%.2f" % v


def zone(r, e):
    """largeurs gauche+droite par plan (px) et hauteur (lignes) de la zone « course reelle » ; + decor qui s'arrete"""
    z = r["zones"]; parts = []
    for L in PL:
        zz = z[L][str(e)]
        if zz["px_course_reelle"] or zz["px_marge_y"]:
            lig = zz["lignes"]
            parts.append("s%s %d+%d%s" % (L[-1], zz["largeur_gauche"], zz["largeur_droite"],
                                          " ×%d" % (lig[1] - lig[0]) if lig else " (marge Y)"))
    a = r.get("decor_arrete", {}).get(str(e), {})
    if a.get("px"): parts.append("arrêt %d px" % a["px"])
    return "<br>".join(parts) or "—"


def pal(r, k):
    p = r["palettes_libres"].get(k, {})
    return "/".join(str(len(p.get(L, []))) for L in PL)


def pal_list(r):
    p = r["palettes_libres"].get("reloge", {})
    return " ; ".join("s%s %s" % (L[-1], ",".join(p.get(L, [])) or "—") for L in PL)


def anim(r):
    t = r["anim_tuiles"]; ap = r["anim_palettes"]; ad = r.get("anim_defilement", {})
    s = "tuiles %s" % "/".join(str(t[L]) for L in PL)
    s += " ; pal. cycl. %s" % "/".join(str(len(ap[L])) for L in PL)
    d = [("s%s %d ph." % (L[-1], ad[L])) for L in PL if ad.get(L, 1) > 1]
    if d: s += " ; défil. " + ", ".join(d)
    au = [L for L in PL if isinstance(r["parallaxe"][L], str)]
    if au: s += " ; auto " + ",".join("s" + L[-1] for L in au)
    return s


lines = ["| Groupe (décors) | Perso(s) | Canevas | Ordre bas→haut | Parallaxe s1/s2/s3 | Rowscroll s2 | Course X | Y réelle haut/bas | Y exportée | À combler 448 (plan g+d ×lignes) | À combler 512 | Palettes utilisables s1/s2/s3 : relogé (en place) | Animations | Contrôle px hors anim. s1/s2/s3/compo |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for r in R:
    c = r["controle"]
    lines.append("| %s | %s | %d×%d | %s | %s | %s | %d | −%d / +%d | −%d / +%d | %s | %s | %s (%s) | %s | %s |" % (
        " ".join("$" + i for i in r["lies"]), ", ".join(r["persos"]), r["canevas"][0], r["canevas"][1],
        ",".join(x[-1] for x in r["ordre"]), "/".join(fp(r["parallaxe"][k]) for k in PL),
        r["rowscroll"].replace(" valeurs", " val."), r["course_x"], r["course_y_reelle"][0], r["course_y_reelle"][1],
        r["course_y_exportee"][0], r["course_y_exportee"][1], zone(r, 32), zone(r, 64),
        pal(r, "reloge"), pal(r, "en_place"), anim(r),
        "/".join(str(c[k]["hors_cases_animees"]) for k in PL + ("composite_3_plans",))))
lines += ["", "Palettes utilisables (relogement fork/FBNeo ; `$7F` jamais en scroll3) :", ""]
for r in R:
    lines.append("- %s : %s" % (" ".join("$" + i for i in r["lies"]), pal_list(r)))
open(D + "/RECAP.md", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
