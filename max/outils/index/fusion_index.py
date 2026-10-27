"""Fusion des lignes MAX (index_max_psp.py) dans re/connaissances/max_psp.tsv et champs.tsv du dépôt HSFA (2026-10-17).
- max_psp.tsv : adresse déjà présente -> on garde le texte existant, on complète score / outil (et confiance
  « mesuré » si l'appariement a un soutien de votes) ; adresse nouvelle -> ligne ajoutée (forme 0x%08X, homologues
  normalisés : upper -> ro5, arcade sur 6 chiffres).
- champs.tsv : champs PSP du joueur (structure psp_objet) dont le décalage PSP n'est couvert par aucune ligne existante.
Usage : python fusion_index.py <racine du dépôt> [--appliquer]"""
import os, sys, re, csv, io
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ICI)
import index_max_psp as I

DEPOT = sys.argv[1]; APP = "--appliquer" in sys.argv
K = os.path.join(DEPOT, "re", "connaissances")


def lire(p):
    with open(p, newline="") as f:
        r = list(csv.reader(f, delimiter="\t"))
    return r[0], r[1:]


def ecrire(p, tete, rows):
    s = io.StringIO(); w = csv.writer(s, delimiter="\t", lineterminator="\n"); w.writerow(tete); w.writerows(rows)
    open(p, "w").write(s.getvalue())


def autres(t):
    out = []
    for x in [y.strip() for y in t.split(";") if y.strip()]:
        x = re.sub(r"^upper:T_([0-9A-Fa-f]{6})(\[.*\])?$", lambda m: "ro5:0x%s" % m.group(1).upper(), x)
        x = re.sub(r"^upper:", "ro5:", x)
        m = re.match(r"^arcade:\$([0-9A-Fa-f]+)(?:\(A5\))?(.*)$", x)
        if m:
            v = int(m.group(1), 16)
            if "(A5)" in x: v += 0xFF8000
            x = "arcade:$%06X" % v
        m = re.match(r"^ro5:0x([0-9A-Fa-f]+)$", x)
        if m: x = "ro5:0x%06X" % int(m.group(1), 16)
        if re.match(r"^(arcade:\$[0-9A-F]{6}|ro5:0x[0-9A-F]{6})$", x): out.append(x)
    return "; ".join(out)


def source(s):
    s = s.replace("max/notes/max-rosette-code.md ; api_moteur.json", "max/notes/max-rosette-code.md + max/outils/rosette_code/README.md")
    s = s.replace(" ; ", " + ").replace("ghidra_decomp.py", "max/outils/ghidra/ghidra_decomp.py")
    s = s.replace("max/outils/rosette_code/champs.py + carte_champs.json", "max/outils/rosette_code/champs.py")
    return s


def outil(o):
    return "max/outils/ghidra/ghidra_decomp.py" if o == "ghidra_decomp.py" else o


# --- max_psp.tsv
tete, rows = lire(os.path.join(K, "max_psp.tsv")); col = {c: i for i, c in enumerate(tete)}
par_adr = {int(r[0].split("-")[0], 16): r for r in rows if r and r[0].startswith("0x")}
maj = ajout = 0
for m in I.L:
    a = int(m[0], 16); score, out = m[9], outil(m[10])
    if a in par_adr:
        r = par_adr[a]
        while len(r) < len(tete): r.append("")
        chg = False
        if score and not r[col["score"]]: r[col["score"]] = score.replace(" (", " votes (", 1) if "/" in score else score; chg = True
        if score and "/" in score and r[col["confiance"]] != "mesuré": r[col["confiance"]] = "mesuré"; chg = True
        if out and not r[col["outil"]]: r[col["outil"]] = out; chg = True
        if m[1] and not r[col["adresse_autres"]]: r[col["adresse_autres"]] = autres(m[1]); chg = True
        maj += chg
    else:
        rows.append(["0x%08X" % a, autres(m[1]), m[2], m[3] or "psp_%x" % a, m[4], m[5], m[6], source(m[7]), m[8],
                     score.replace(" (", " votes (", 1) if "/" in score else score, out]); ajout += 1
print("max_psp.tsv : %d lignes existantes complétées, %d ajoutées (total %d)" % (maj, ajout, len(rows)))
if APP: ecrire(os.path.join(K, "max_psp.tsv"), tete, rows)

# --- champs.tsv (psp_objet)
tc, rc = lire(os.path.join(K, "champs.tsv")); cc = {c: i for i, c in enumerate(tc)}
couvert = set()
for r in rc:
    if r[cc["structure"]] != "psp_objet": continue
    for esp, adr in [x.split(":", 1) for x in r[cc["decalage_autres"]].split(";") if ":" in x]:
        if esp.strip() != "psp": continue
        m = re.match(r"\+\$([0-9A-Fa-f]+)(?:-\$?\+?\$?([0-9A-Fa-f]+))?", adr.strip())
        if m:
            lo = int(m.group(1), 16); hi = int(m.group(2), 16) if m.group(2) else lo
            couvert.update(range(lo, hi + 1))
n = 0
for m in I.C:
    p = int(m[0].split("+0x")[1], 16)
    if p in couvert: continue
    ar = m[1].split("+$")[1] if m[1] else ""
    rc.append(["psp_objet", "", ("+$%s" % ar.upper()) if ar else "", "psp:+$%X" % p, "psp,arcade" if ar else "psp",
               "champ_%x" % p, m[4], "", m[6], source(m[7]), m[8], "", m[10]]); n += 1; couvert.add(p)
print("champs.tsv : %d champs PSP ajoutés (total %d)" % (n, len(rc)))
if APP: ecrire(os.path.join(K, "champs.tsv"), tc, rc)
