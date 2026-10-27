#!/usr/bin/env python3
"""assemble les lots : guide/csv/*.csv -> coups_sfa_anthology.csv + .md (commandes et pages seulement, aucun texte du guide)"""
import glob, os, sys
S = os.environ.get("GUIDE", os.getcwd())   # dossier de travail (hors depot)
TETE = "jeu;mode;personnage;version_style;type;nom_du_coup;manipulation;boutons;conditions;page_pdf"
lignes, err = [], []
for f in sorted(glob.glob(os.path.join(S, "csv", "*.csv"))):
    for i, l in enumerate(open(f, encoding="utf-8").read().splitlines()):
        if not l.strip() or l.strip() == TETE: continue
        c = [x.strip() for x in l.split(";")]
        if len(c) != 10: err.append("%s:%d : %d champs : %s" % (os.path.basename(f), i + 1, len(c), l)); continue
        lignes.append(c)
lignes.sort(key=lambda c: int(c[9]) if c[9].isdigit() else 999)
open(os.path.join(S, "coups_sfa_anthology.csv"), "w", encoding="utf-8").write(TETE + "\n" + "".join(";".join(c) + "\n" for c in lignes))
md = ["# Coups — Street Fighter Alpha Anthology (guide BradyGames), une ligne par coup", "",
      "| " + " | ".join(TETE.split(";")) + " |", "|" + "---|" * 10]
md += ["| " + " | ".join(x.replace("|", "/") for x in c) + " |" for c in lignes]
open(os.path.join(S, "coups_sfa_anthology.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
print("%d coups ; %d lignes rejetees" % (len(lignes), len(err))); [print(e) for e in err]
