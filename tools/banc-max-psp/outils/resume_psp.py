#!/usr/bin/env python3
"""resume_psp.py <resultats/candidat> [sortie.md] : agrège les TSV du banc PSP en RESUME-PSP.md (écarts classés)."""
import csv, glob, os, re, sys, collections, datetime

d = sys.argv[1]
sortie = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(d))), "RESUME-PSP.md")
fichiers = sorted(glob.glob(os.path.join(d, "*.tsv")))
lignes = []
for f in fichiers:
    nom = os.path.basename(f)[:-4]
    for r in csv.DictReader(open(f), delimiter="\t"):
        r["fichier"] = nom
        lignes.append(r)


def classe(r):
    v, det = r["verdict"], r["detail"]
    if v == "IDENTIQUE":
        return "ok"
    if v == "PROCHE":
        return "proche"
    if v == "NC":
        return "nc"
    if v == "MUR":
        return "mur"
    if v == "DÉCALÉ":
        return "C1 décalé"
    if "exception" in det:
        return "A exception Upper"
    if "sort sur PSP mais PAS dans Upper" in det:
        return "B coup absent dans Upper"
    if "dégâts" in det:
        return "C2 dégâts différents"
    if "le coup sort dans Upper mais PAS sur PSP" in det:
        return "E manip non reconnue sur PSP (à adapter)"
    m = re.search(r"1re : tour (\d+) (\S+ ?\S*) :", det)
    if m and m.group(2).startswith("etat"):
        return "D état / animation différent"
    if m:
        return "D position / vie différente"
    return "D autre"


cl = collections.defaultdict(list)
for r in lignes:
    cl[classe(r)].append(r)

pc = collections.OrderedDict()
for r in lignes:
    k = (r["perso"], r["adv"], r["ism"], r["fichier"])
    pc.setdefault(k, collections.Counter())[r["verdict"]] += 1

out = []
out.append("# RESUME-PSP : mode B du banc des coups (PSP oracle / Upper MAX)\n")
out.append("Généré le %s par `outils/resume_psp.py` sur `%s` (%d essais, %d fichiers). Méthode, correspondances et limites : `BANC-PSP.md`.\n" % (
    datetime.date.today(), d, len(lignes), len(fichiers)))
out.append("## 1. Vue d'ensemble\n")
out.append("| série (fichier) | perso | adv | ISM | IDENTIQUE | PROCHE | DÉCALÉ | MUR | DIFFÉRENT | NC |")
out.append("|---|---|---|---|---|---|---|---|---|---|")
for (p, a, i, f), c in pc.items():
    out.append("| %s | %s | %s | %s | %d | %d | %d | %d | %d | %d |" % (f, p, a, i, c["IDENTIQUE"], c["PROCHE"], c["DÉCALÉ"], c["MUR"], c["DIFFÉRENT"], c["NC"]))
tot = collections.Counter(r["verdict"] for r in lignes)
out.append("\nTotal : " + ", ".join("%s %d" % kv for kv in sorted(tot.items())) + "\n")
out.append("## 2. Écarts classés (du plus grave au moins grave)\n")
ordre = ["B coup absent dans Upper", "A exception Upper", "C2 dégâts différents", "D état / animation différent", "D position / vie différente",
         "D autre", "C1 décalé", "E manip non reconnue sur PSP (à adapter)"]
expl = {
    "B coup absent dans Upper": "le coup sort sur PSP, rien (ou autre chose) dans Upper : à corriger en priorité",
    "A exception Upper": "plantage / adresse illégale dans Upper pendant le coup",
    "C2 dégâts différents": "les deux jouent le coup mais la vie perdue diffère",
    "D état / animation différent": "suite d'états de J1 ou de J2 différente (1re divergence indiquée)",
    "D position / vie différente": "mêmes états mais position X / Y ou vie différente de plus de 2 px",
    "D autre": "divergence autre",
    "C1 décalé": "même suite d'états, décalée de n tours (délai d'un spécial, durée d'une phase)",
    "E manip non reconnue sur PSP (à adapter)": "Upper sort le coup, la PSP non : très probablement la manip scriptée (timing, diagonales, distance) ; à rejouer avec une autre manip avant de conclure",
}
for k in ordre:
    L = cl.get(k, [])
    out.append("### %s (%d)\n\n%s.\n" % (k, len(L), expl[k]))
    for r in L[:150]:
        out.append("- `%s` **%s %s** %s : %s" % (r["fichier"], r["perso"], r["ism"], r["coup"], r["detail"][:220]))
    if len(L) > 150:
        out.append("- … %d autres (voir les TSV)" % (len(L) - 150))
    out.append("")
out.append("### Écarts non significatifs\n")
out.append("- MUR : %d (divergence de position près d'un bord de scène ; la scène PSP est plus large)." % len(cl.get("mur", [])))
out.append("- PROCHE : %d (±2 px / ±1 tour)." % len(cl.get("proche", [])))
out.append("- NC : %d (rien ne sort des deux côtés : manip ou condition à revoir)." % len(cl.get("nc", [])))
open(sortie, "w").write("\n".join(out) + "\n")
print(sortie, len(lignes))
