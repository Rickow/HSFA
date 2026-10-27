#!/usr/bin/env python3
"""Corrections de voix d'Hyper deduites des comparaisons avec l'arcade (compare_voix_arcade.py).

Pour chaque geste en ecart, les voix d'Hyper et de l'arcade sont appariees dans l'ordre. Une voix d'Hyper est soit
« SFA3:c » (voix SFA3 gardee : le code SFA3 c est connu), soit une voix d'origine x (rejeu) : le code SFA3 qui la
produit est cherche dans correspondance.tsv (correspondance.tsv : jeu, perso de base, code_SFA3 -> code_source) ; s'il y en a plusieurs, la
correction est marquee ambigue. Les cris de degats / K.O. (n = 0-6 du bloc) sont exclus : corrige_cris.py les traite.

  analyse_voix_arcade.py <dossier des comparaisons> > corrections_voix_arcade.tsv
Colonnes : jeu, base, perso, versions, code_SFA3, actuel, arcade, gestes, statut (sur / ambigu / sans_SFA3).
"""
import collections, csv, glob, os, re, sys

ICI = os.path.dirname(os.path.abspath(__file__))
FAM_JEU = {"ZERO": "sfa1", "ZERO 2": "sfa2", "ZERO 2 ALPHA": "sfa2"}


def main():
    dossier = sys.argv[1]
    red = collections.defaultdict(lambda: collections.defaultdict(set))    # (jeu, base) -> code_source -> {code_SFA3}
    for r in csv.DictReader(open(os.path.join(ICI, "correspondance.tsv")), delimiter="\t"):
        if r["decision"] in ("voix", "cri", "ko"):
            red[(r["source"].lower(), int(r["base"], 16))][int(r["code_source"], 16)].add(int(r["code_SFA3"], 16))
    props = collections.OrderedDict()
    for f in sorted(glob.glob(os.path.join(dossier, "*.tsv"))):
        nom = os.path.basename(f)[:-4]
        lignes = open(f).read().split("\n")
        m = re.search(r"CHOIX J1 image \d+ : \$102=(\w+) base=(\w+)", lignes[-2] if lignes[-1] == "" else lignes[-1])
        if not m: continue
        v, base = int(m.group(1), 16), int(m.group(2), 16)
        jeu = "sfa1" if 0x30 <= v < 0x40 else "sfa2"
        for l in lignes[1:]:
            t = l.split("\t")
            if len(t) < 4 or t[3] != "ECART": continue
            geste, va, vh = t[0], t[1].split(), t[2].split()
            va = [] if va == ["-"] else va
            vh = [] if vh == ["-"] else vh
            for h, a in zip(vh, va):
                if h == a: continue
                ac = int(a, 16)
                if h.startswith("SFA3:"):
                    sources = [int(h[5:], 16)]; actuel = h
                else:
                    sources = sorted(red[(jeu, base)].get(int(h, 16), [])); actuel = h
                for c in sources or [None]:
                    if c is not None and (c - 0x300) % 0x20 <= 6 and (c - 0x300) // 0x20 == base:
                        continue                                       # cri du bloc (corrige_cris.py)
                    statut = "sans_SFA3" if c is None else ("sur" if len(sources) == 1 else "ambigu")
                    k = (jeu, base, c, ac)
                    p = props.setdefault(k, dict(nom=nom.rsplit("_", 1)[0], versions=set(), actuel=actuel,
                                                 gestes=set(), statut=statut))
                    p["versions"].add("%02X" % v); p["gestes"].add(geste)
    print("jeu\tbase\tperso\tversions\tcode_SFA3\tactuel\tarcade\tgestes\tstatut")
    for (jeu, base, c, ac), p in props.items():
        print("%s\t%02X\t%s\t%s\t%s\t%s\t%04X\t%s\t%s" % (jeu, base, p["nom"], " ".join(sorted(p["versions"])),
              "-" if c is None else "%04X" % c, p["actuel"], ac, " ; ".join(sorted(p["gestes"])), p["statut"]))


if __name__ == "__main__":
    main()
