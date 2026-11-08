#!/usr/bin/env python3
"""ecrit_doc.py : assemble DECORS.md (texte + tableau decor par decor tire d'inventaire_decors.tsv)."""
import os, csv
H = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(H, "inventaire_decors.tsv")), delimiter='\t'))
def pc(x): return "%d" % round(float(x))
tab = ["| décor | export DECORS-WS | persos qui y mènent (Upper, `T_61BE10`) | données dans Hyper | gfx s1 / s2 / s3 dans Hyper | pal. s1 Upper | listes s1 / s2 / s3 Upper | données partagées |",
       "|---|---|---|---|---|---|---|---|"]
for r in rows:
    d = r['decor']
    don = "**oui** : décor 4/6 d'Hyper" if d == "$4E" else "non"
    gf = "%s / %s / %s %%" % (pc(r['gfx_s1_%Hyper']), pc(r['gfx_s2_%Hyper']), pc(r['gfx_s3_%Hyper']))
    if d == "$4E": gf = "**%s**" % gf
    exp = r['groupe_export'] or "—"
    if exp == "Upper (neuf)": exp = "neuf (Upper)"
    pers = r['persos_arcade_Upper'] or "—"
    if d == "$14": pers = "— (Bison final : `$174 = $14`)"
    tab.append("| `%s` | %s | %s | %s | %s | `0x%s` | `0x%s` / `0x%s` / `0x%s` | %s |" % (d, exp, pers, don, gf,
               r['pal_s1_Upper'].upper(), r['liste_s1_Upper'].upper(), r['liste_s2_Upper'].upper(), r['liste_s3_Upper'].upper(), r['alias'] or ""))
TAB = "\n".join(tab)
doc = open(os.path.join(H, "DECORS.gabarit.md")).read().replace("@@TABLEAU@@", TAB)
open(os.path.join(H, "DECORS.md"), "w").write(doc)
print("DECORS.md : %d lignes" % doc.count("\n"))
