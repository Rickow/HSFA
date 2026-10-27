#!/usr/bin/env python3
"""Fusionne les resultats de marque_voix.py en une table de voix par (jeu, perso de base, code SFA3) et la compare a la
correspondance actuelle (correspondance.tsv, decisions voix / cri / ko ; sinon la voix SFA3 est gardee).

  fusionne_voix_arcade.py <dossier de marque_voix.py> <lot.txt> > voix_arcade.tsv
lot.txt : lignes « jeu grille spec nom » (compare_voix_arcade.py).
Statut : identique (deja juste, ou voix SFA3 = meme echantillon que la voix d'arcade), a_corriger (autre voix d'origine), voix_SFA3 (voix SFA3 gardee, l'arcade en a une),
conflit (plusieurs voix d'arcade pour le meme code : a ecouter).
"""
import collections, csv, glob, os, sys

ICI = os.path.dirname(os.path.abspath(__file__))


def main():
    dmk, lot = sys.argv[1], sys.argv[2]
    base_de = {}
    for l in open(lot):
        t = l.split()
        if len(t) == 4: base_de[t[3]] = int(t[2].split(".")[0], 16)
    corr, ident = {}, {}
    for r in csv.DictReader(open(os.path.join(ICI, "correspondance.tsv")), delimiter="\t"):
        k = (r["source"].lower(), int(r["base"], 16), int(r["code_SFA3"], 16))
        if r["decision"] in ("voix", "cri", "ko"):
            corr[k] = (int(r["code_source"], 16), r["decision"], r["distance"])
        elif r["decision"] == "identique":
            ident[k] = int(r["code_source"], 16)        # la voix SFA3 est deja l'echantillon de la source
    agg = collections.OrderedDict()
    for f in sorted(glob.glob(os.path.join(dmk, "*.tsv"))):
        nom = os.path.basename(f)[:-4].replace(".super", "")
        perso = nom.rsplit("_", 1)[0]
        for l in open(f):
            if l.startswith(("#", "jeu")): continue
            jeu, v, c3, a, k, autres, gestes = l.rstrip("\n").split("\t")
            key = (jeu, base_de[nom], int(c3, 16))
            e = agg.setdefault(key, dict(perso=perso, votes=collections.Counter(), versions=set(), gestes=set()))
            e["votes"][int(a, 16)] += int(k)
            for x in autres.split():
                aa, kk = x.split(":"); e["votes"][int(aa, 16)] += int(kk)
            e["versions"].add(v); e["gestes"].update(g.strip() for g in gestes.split(";"))
    print("jeu\tbase\tperso\tcode_SFA3\tactuel\tarcade\tvotes\tversions\tstatut\tgestes")
    for (jeu, b, c3), e in agg.items():
        (a, n), = e["votes"].most_common(1)
        tot = sum(e["votes"].values())
        cur = corr.get((jeu, b, c3))
        if (c3 - 0x300) % 0x20 <= 6 and (c3 - 0x300) // 0x20 == b: continue      # cris du bloc : corrige_cris.py
        if n < tot: statut = "conflit"
        elif cur is None and ident.get((jeu, b, c3)) == a: statut = "identique"     # meme echantillon : rien a changer
        elif cur is None and b == 0x11 and jeu == "sfa2": statut = "identique"     # Gen : voix SFA2 = voix SFA3 (§2)
        elif cur is None: statut = "voix_SFA3"
        elif cur[0] == a: statut = "identique"
        else: statut = "a_corriger"
        votes = " ".join("%04X:%d" % x for x in e["votes"].most_common())
        print("%s\t%02X\t%s\t%04X\t%s\t%04X\t%s\t%s\t%s\t%s" % (jeu, b, e["perso"], c3,
              "SFA3" if cur is None else "%04X (%s %s)" % cur, a, votes, " ".join(sorted(e["versions"])), statut,
              " ; ".join(sorted(e["gestes"]))))


if __name__ == "__main__":
    main()
