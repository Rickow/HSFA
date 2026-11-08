"""(frame_data_max) Annexe indicative : rapprochement des mesures PSP (A-isme) avec SuperCombo CvS2 (Eagle, Maki, Yun).
annexe.py <candidat> -> resultats/<cand>/annexe_supercombo.md. La PSP fait référence ; CvS2 est un autre jeu (système Groove, autre cadence) :
écarts attendus. Convention SuperCombo (déduite, annexe/SOURCES.md) : démarrage = images AVANT la 1re active, comme notre « dém. »."""
import csv, json, os, re, sys
ICI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORCE = {"LP": "Jab", "MP": "Strong", "HP": "Fierce", "LK": "Short", "MK": "Forward", "HK": "Roundhouse"}
BTN = {"LP": "LP", "MP": "MP", "HP": "HP", "LK": "LK", "MK": "MK", "HK": "HK"}


def cle_sc(perso, nom):
    """motif (regex) du nom SuperCombo correspondant à notre coup, ou None"""
    m = re.match(r"(debout|proche|accroupi|saut avant) (\w\w)$", nom)
    if m:
        pos, b = m.groups()
        f = FORCE[b]
        return {"debout": r"^Far (Standing )?%s\b" % f, "proche": r"^Close (Standing )?%s\b" % f,
                "accroupi": r"^Crouch(ing)? %s\b" % f, "saut avant": r"^Jump(ing)? %s\b(?!.*\[u/)" % f}[pos]
    if nom.startswith("prise avant"):
        k = "PP" in nom
        return {"eagle": "^Pile of Fools" if k else "^Fool Percussion", "yun": "^Chugeki" if k else "^Monkey Flip"}.get(perso)
    m = re.search(r"niv\. (\d)", nom)
    niv = int(m.group(1)) if m else None
    b = re.search(r"\b(LP|MP|HP|LK|MK|HK)\b", nom)
    b = b.group(1) if b else None
    T = [("Manchester Black", r"^Manchester Black \[%s\]"), ("Canterbury Blue", r"^Canterbury Blue \[%s\]"), ("Oxford Red", r"^Oxford Red \[%s\]"),
         ("Liverpool White", r"^Liverpool White \[%s\]"), ("St. Andrew", r"^Saint Andrew's Green \[%s\]"),
         ("Genko", r"^Genko \[%s\]"), ("Tetsuzankou", r"^Tetsuzanko \[623 \+ %s\]"), ("Zesshou", r"^Zessho Hoho \[236 \+ %s\]"),
         ("Senkyutai", r"^Senkyutai \[236 \+ %s\]"), ("Kobokushi ", r"^Kobokushi \[214 \+ %s\]")]
    for k, motif in T:
        if nom.startswith(k) and b:
            return motif % b
    L = {"Fake Kobokushi": r"^Kobokushi \[214 \+ PP\]", "Zenpou": "^Zenpo Tenshin", "Senpuu": "^Senpukyaku", "Raigeki": "^Raigeki Shu",
         "Hiji Otoshi": "^Elbow Drop", "Reppukyaku": "^Reppukyaku", "Hayagake > arrêt": r"^Hayagake \[Run Stop\]",
         "Hayagake > Kage": r"^Hayagake \[Low Slide\]", "Hayagake > Kubikari": r"^Hayagake \[Overhead\]", "Hiten": "^Hiten Soryujin"}
    for k, motif in L.items():
        if nom.startswith(k):
            return motif
    if niv:
        P = "LP MP HP".split()[niv - 1]
        S = {"Union Jack": r"^Union Jack Platinum \[236236\+%s\]" % P, "Manchester Gold": r"^Manchester Gold \[214214\+%s\]" % P,
             "Bushin Gouraiha": r"^Bushin Gouraiha \[Level %d\]" % niv, "Tesshinhou": r"^Tesshinhou \[Level %d\]" % niv,
             "Sourai": r"^Sorai Rengeki \[236236 \+ %s\]" % P, "You Hou": r"^Yoho"}
        for k, motif in S.items():
            if nom.startswith(k):
                return motif
    return None


def main(cand):
    nc = os.path.basename(os.path.normpath(cand))
    lignes = json.load(open(os.path.join(ICI, "resultats", nc, "lignes.json")))
    sc = list(csv.DictReader(open(os.path.join(ICI, "annexe", "supercombo.tsv")), delimiter="\t"))
    md = ["# Annexe (indicative) : mesures PSP et frame data publiée de CvS2 (SuperCombo)", "",
          "**La PSP (SFA3 MAX) fait référence.** CvS2 est un autre jeu (Groove, autre moteur, autre cadence) : ce rapprochement sert seulement à "
          "repérer une mesure aberrante. Sources, révisions et convention : `annexe/SOURCES.md`. Ingrid : aucune donnée chiffrée publiée (CFE). "
          "Colonnes `P` = PSP (A-isme, tours de jeu), `SC` = SuperCombo CvS2 (images). Dégâts SuperCombo en points CvS2 (non comparables).", ""]
    stats = {"egal": 0, "pres": 0, "loin": 0}
    for perso, nom in (("eagle", "Eagle"), ("maki", "Maki"), ("yun", "Yun")):
        md += ["## %s" % nom, "", "| coup | coup SuperCombo | dém. P / SC | actifs P / SC | récup. P / SC | garde P / SC | touche P / SC |", "|---|---|---|---|---|---|---|"]
        for l in lignes:
            if l["perso"] != perso or l["ism"] != "A":
                continue
            k = cle_sc(perso, l["coup"])
            r = next((x for x in sc if x["perso"] == nom and k and re.search(k, x["coup_publie"])), None) if k else None
            if not r:
                continue
            p = l["psp"]
            act = p.get("morceaux", p.get("actif", ""))
            act = re.sub(r"\((\d+)\)", r"[\1]", str(act)).replace(",", "")
            for g, s in (("demarrage", "demarrage"), ("recuperation", "recuperation")):
                try:
                    d = abs(int(p.get(g)) - int(r[s]))
                    stats["egal" if d == 0 else "pres" if d <= 2 else "loin"] += 1
                except (TypeError, ValueError):
                    pass
            md.append("| %s | %s | %s / %s | %s / %s | %s / %s | %s / %s | %s / %s |" % (
                l["coup"], r["coup_publie"], p.get("demarrage", ""), r["demarrage"], act, r["actifs"], p.get("recuperation", ""), r["recuperation"],
                p.get("avantage_garde", ""), r["garde"], p.get("avantage_touche", ""), r["touche"]))
        md.append("")
    md.insert(4, "Démarrage et récupération comparables : %d égaux, %d à 2 près, %d plus loin." % (stats["egal"], stats["pres"], stats["loin"]))
    md.insert(5, "")
    open(os.path.join(ICI, "resultats", nc, "annexe_supercombo.md"), "w").write("\n".join(md) + "\n")
    print(stats)


if __name__ == "__main__":
    main(sys.argv[1])
