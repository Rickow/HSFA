#!/usr/bin/env python3
"""finition apres applique_verif.py : doubles quarts de cercle complets en SFA3, notes ISM / points a tester"""
import os
G = os.environ.get("GUIDE", os.getcwd())   # dossier de travail (hors depot)
COL = "jeu;mode;personnage;version_style;type;nom_du_coup;manipulation;boutons;conditions;page_pdf".split(";")
rows = [l.rstrip("\n").split(";") for l in open(os.path.join(G, "coups_sfa_anthology.csv"), encoding="utf-8")][1:]
def note(x, s): x[8] = (x[8] + " — " if x[8] else "") + s
COMPLET = {"↓↘→↓↘": "↓↘→↓↘→", "↓↙←↓↙": "↓↙←↓↙←"}
NOTES = {("Street Fighter Alpha 3", "M. Bison", "Psycho Crusher"): "à tester : ISM selon SuperCombo = A-ISM seulement",
         ("Street Fighter Alpha 3", "M. Bison", "Knee Press Nightmare"): "à tester : ISM selon SuperCombo = X-ISM et A-ISM",
         ("Street Fighter Alpha 3", "Juli", "Spin Drive Smasher"): "à tester : ISM selon SuperCombo = X-ISM et A-ISM",
         ("Street Fighter Alpha 3", "Juli", "Reverse Shaft Breaker"): "à tester : ISM selon SuperCombo = A-ISM seulement",
         ("Street Fighter Alpha 3", "Rolento", "Take No Prisoner"): "à tester : ISM selon SuperCombo = X-ISM et A-ISM",
         ("Street Fighter Alpha", "Charlie", "Spin Back Knuckle"): "à tester : correction d'après SuperCombo peu sûre",
         ("Street Fighter Alpha", "Sagat", "Alpha Counter"): "à tester : SuperCombo donne MK debout, ←↙↓ + Kick",
         ("Street Fighter Alpha 2 Gold", "Sagat", "Angry Charge"): "à tester : SuperCombo (Angry Scar) donne ↓↘→ + Start"}
n = 0
for x in rows:
    if x[0] == "Street Fighter Alpha 3" and x[6] in COMPLET:
        note(x, "guide imprime : %s (raccourci accepté par le jeu)" % x[6]); x[6] = COMPLET[x[6]]; n += 1
    for (j, p, c), s in NOTES.items():
        if x[0] == j and x[2] == p and x[5].startswith(c): note(x, s)
open(os.path.join(G, "coups_sfa_anthology.csv"), "w", encoding="utf-8").write(";".join(COL) + "\n" + "".join(";".join(x) + "\n" for x in rows))
md = ["# Coups — Street Fighter Alpha Anthology (guide BradyGames), une ligne par coup", "",
      "Transcrit du guide (291 pages), flèches vérifiées à 300 dpi, puis manipulations confrontées à SuperCombo Wiki "
      "(wiki.supercombo.gg) pour SFA1, SFA2/Gold et SFA3 : les coquilles du guide sont corrigées et la forme imprimée est rappelée "
      "dans « conditions » (« guide imprime : … »). « [douteux] » = non tranché ; « à tester » = à confirmer en jeu. "
      "Super Gem Fighter : SuperCombo ne documente que Dan et Zangief, lignes non vérifiées.", "",
      "| " + " | ".join(COL) + " |", "|" + "---|" * 10] + ["| " + " | ".join(c.replace("|", "/") for c in x) + " |" for x in rows]
open(os.path.join(G, "coups_sfa_anthology.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
print("%d doubles quarts completes ; %d lignes [douteux] ; %d 'à tester'" % (n, sum("douteux" in x[8] for x in rows), sum("à tester" in x[8] for x in rows)))
