#!/usr/bin/env python3
"""applique verif/*.tsv a coups_sfa_anthology.csv (produit par assemble.py) -> coups_sfa_anthology.csv/.md corriges + journal"""
import csv, glob, os
G = os.environ.get("GUIDE", os.getcwd())   # dossier de travail (hors depot)
COL = "jeu;mode;personnage;version_style;type;nom_du_coup;manipulation;boutons;conditions;page_pdf".split(";")
rows = [l.rstrip("\n").split(";") for l in open(os.path.join(G, "coups_sfa_anthology.csv"), encoding="utf-8")][1:]
journal, rate, nv = [], [], []
for f in sorted(glob.glob(os.path.join(G, "verif", "*.tsv"))):
    for r in csv.DictReader(open(f, encoding="utf-8"), delimiter="\t"):
        if not r.get("champ") or r["champ"] not in COL: continue
        if r["cause"] == "non_verifiable": nv.append(r); continue
        k = COL.index(r["champ"]); nouveau = r["nouveau"].replace(";", " /").strip()
        cand = [x for x in rows if x[9] == r["page_pdf"].strip() and x[k] == r["ancien"].strip()
                and (x[5] == r["nom_du_coup"].strip() or r["champ"] == "nom_du_coup") and x[2] == r["personnage"].strip()]
        if not cand:
            cand = [x for x in rows if x[9] == r["page_pdf"].strip() and x[k] == r["ancien"].strip() and x[5] == r["nom_du_coup"].strip()]
        if not cand: rate.append(r); continue
        for x in cand:
            x[k] = nouveau
        journal.append("p.%s %s / %s : %s « %s » -> « %s » (%s, %s)" % (r["page_pdf"], r["personnage"], r["nom_du_coup"], r["champ"],
                       r["ancien"], nouveau, r["cause"], r["source"]))
open(os.path.join(G, "coups_sfa_anthology.csv"), "w", encoding="utf-8").write(";".join(COL) + "\n" + "".join(";".join(x) + "\n" for x in rows))
md = ["# Coups — Street Fighter Alpha Anthology (guide BradyGames), une ligne par coup", "",
      "Manipulations vérifiées contre SuperCombo Wiki (wiki.supercombo.gg) ; les coquilles du guide sont corrigées et signalées dans « conditions ».", "",
      "| " + " | ".join(COL) + " |", "|" + "---|" * 10] + ["| " + " | ".join(c.replace("|", "/") for c in x) + " |" for x in rows]
open(os.path.join(G, "coups_sfa_anthology.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
open(os.path.join(G, "corrections_supercombo.txt"), "w", encoding="utf-8").write(
    "\n".join(journal) + "\n\n# non appliquees (ligne introuvable)\n" + "\n".join(str(dict(r)) for r in rate) +
    "\n\n# non verifiables\n" + "\n".join("p.%s %s / %s" % (r["page_pdf"], r["personnage"], r["nom_du_coup"]) for r in nv) + "\n")
print("%d corrections appliquees, %d introuvables, %d non verifiables ; reste %d lignes [douteux]" %
      (len(journal), len(rate), len(nv), sum("douteux" in x[8] for x in rows)))
