#!<workspace>/venv/bin/python
"""Correspondance voix SFA3 (codes que Hyper envoie, bloc du perso de base) -> voix d'origine SFA1 (ZERO) / SFA2 (ZERO 2,
ALPHA), par DTW des MFCC entre l'echantillon SFA3 et ceux du bloc source du meme perso.
Regles : identique (d < 0,03 : SFA3 reutilise deja l'echantillon d'origine) -> rien a faire ;
voix longue (>= 0,45 s) : acceptee si rapport de durees 0,5-2 et (d <= 0,20, ou d <= 0,27 et meilleur appariement
mutuel) ; cri court : meilleur cri court (< 0,5 s)
de la source si d <= 0,40 ; K.O. (n = 0 et 4 du bloc) : cri de fin de bloc de la source ; decision prise par
echantillon SFA3 (les codes qui jouent le meme echantillon ont la meme) ; sinon : pas d'equivalent (on garde SFA3).
Sorties : catalogue/correspondance.json, correspondance.tsv"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blocs, sources
from empreintes import empreinte, dtw
from assigne import NOMS
D = blocs.D
S3 = blocs.sfa3()
FAM = {"sfa1": "ZERO", "sfa2": "ZERO 2 / ALPHA"}
res = []
for jeu in ("sfa1", "sfa2"):
    for b in sorted(S3):
        src = sources.source(jeu, b)
        if not src: continue
        ko = src[-1]                                     # fin de bloc = cri de K.O. (sequence voix + echo/bruitage)
        ech3 = []
        for c, e, g in S3[b]:
            if e not in ech3: ech3.append(e)
        dec_e = {}
        for e in ech3:
            A = empreinte("sfa3", e)
            cand = sorted((dtw(A["m"], empreinte(jeu, e2)["m"]), c2, e2, empreinte(jeu, e2)["duree"]) for c2, e2, g2 in src)
            d, c2, e2, du2 = cand[0]
            mutuel = min((dtw(empreinte("sfa3", x)["m"], empreinte(jeu, e2)["m"]), x) for x in ech3)[1] == e
            ok_du = 0.5 <= du2 / A["duree"] <= 2
            codes_e = [c for c, x, g in S3[b] if x == e]
            court = A["duree"] < 0.45
            if any((c - 0x300) % 0x20 in (0, 4) for c in codes_e):          # K.O. : structure (fin de bloc)
                d = dtw(A["m"], empreinte(jeu, ko[1])["m"]); c2, e2, du2 = ko[0], ko[1], empreinte(jeu, ko[1])["duree"]
                dec = "identique" if d < 0.03 else "ko"
            elif d < 0.03: dec = "identique"
            elif not court and ok_du and (d <= 0.20 or (d <= 0.27 and mutuel)): dec = "voix"
            elif court:
                cc = [x for x in cand if x[3] < 0.5]
                if cc and cc[0][0] <= 0.40: d, c2, e2, du2 = cc[0]; dec = "cri"
                else: dec = "aucun"
            else: dec = "aucun"
            dec_e[e] = (d, c2, e2, du2, dec, A["duree"])
        for c, e, g in S3[b]:
            d, c2, e2, du2, dec, du3 = dec_e[e]
            A = dict(duree=du3)
            res.append(dict(jeu=jeu, base=b, perso=NOMS[b], code="%04x" % c, ech3=e, duree3=round(A["duree"], 3),
                            src="%04x" % c2, ech=e2, duree=round(du2, 3), d=round(d, 3), decision=dec))
json.dump(res, open(os.path.join(D, "catalogue", "correspondance.json"), "w"), indent=0)
with open(os.path.join(D, "correspondance.tsv"), "w") as f:
    f.write("famille\tperso\tbase\tcode_SFA3\tduree_SFA3\tsource\tcode_source\techantillon_source\tduree_source\tdistance\tdecision\n")
    for r in res:
        f.write("%s\t%s\t%02x\t%s\t%.2f\t%s\t%s\t%s\t%.2f\t%.3f\t%s\n" % (FAM[r["jeu"]], r["perso"], r["base"], r["code"], r["duree3"],
                r["jeu"].upper(), r["src"], r["ech"], r["duree"], r["d"], r["decision"]))
from collections import Counter
for jeu in ("sfa1", "sfa2"):
    R = [r for r in res if r["jeu"] == jeu]
    ech = set(r["ech"] for r in R if r["decision"] in ("voix", "cri", "ko"))
    print(jeu, Counter(r["decision"] for r in R), "echantillons a ajouter :", len(ech))
