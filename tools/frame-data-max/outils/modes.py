"""(frame_data_max) modes.py <cand> : compare la mesure en TOURS (resultats/<cand>/lignes.json) et en IMAGES BRUTES
(resultats/<cand>/images/lignes.json) -> resultats/<cand>/modes.md :
  bilan dans les deux modes ; écarts qui DISPARAISSENT en tours (dus aux images de ralentissement du 68000) ;
  écarts qui RESTENT en tours (ne s'expliquent pas par un ralentissement : vrais défauts)."""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
import tableaux as TB

ICI = TB.ICI
nc = os.path.basename(os.path.normpath(sys.argv[1]))
D = os.path.join(ICI, "resultats", nc)
LT = json.load(open(os.path.join(D, "lignes.json")))
LI = {(l["perso"], l["ism"], l["id"]): l for l in json.load(open(os.path.join(D, "images", "lignes.json")))}
V = ("identique", "écart 1", "écart >1", "absent/exception")


def bilan(L):
    c = collections.Counter(l["verdict"] for l in L)
    return " / ".join(str(c[v]) for v in V)


def ecarts(l):
    return ", ".join("%s %s → %s" % (TB.TITRE[g], TB.cel(l["psp"].get(g)), TB.cel(l["upper"].get(g))) for g, e in l["ecart"].items() if e != 0)


out = ["# Mesure en tours contre images brutes : `%s`" % nc, "",
       "Bilan (identique / écart 1 / écart >1 / absent-exception) : **tours %s** ; images brutes %s." % (bilan(LT), bilan(LI.values())), "",
       "| perso | tours | images brutes |", "|---|---|---|"]
for p in TB.PERSOS:
    out.append("| %s | %s | %s |" % (TB.NOMS[p], bilan([l for l in LT if l["perso"] == p]), bilan([l for l in LI.values() if l["perso"] == p])))
dis, reste, nouv = [], [], []
for l in LT:
    li = LI.get((l["perso"], l["ism"], l["id"]))
    if li is None:
        continue
    if l["verdict"] == "identique" and li["verdict"] != "identique":
        dis.append((l, li))
    elif l["verdict"] != "identique":
        reste.append((l, li))
        if li["verdict"] == "identique":
            nouv.append(l)
out += ["", "## Écarts dus aux ralentissements (images brutes ≠ PSP, tours = PSP) : %d" % len(dis), "",
        "| perso | isme | coup | images brutes (PSP → Upper) | ralentis w/h/b |", "|---|---|---|---|---|"]
for l, li in dis:
    out.append("| %s | %s | %s | %s | %s |" % (TB.NOMS[l["perso"]], l["ism"], l["coup"], ecarts(li), l["ralentis"]))
out += ["", "## Écarts qui restent en tours (vrais défauts, ralentissements exclus) : %d" % len(reste), "",
        "| perso | isme | coup | verdict | en tours (PSP → Upper) | images brutes | ralentis w/h/b | note |", "|---|---|---|---|---|---|---|---|"]
for l, li in reste:
    out.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (TB.NOMS[l["perso"]], l["ism"], l["coup"], l["verdict"], ecarts(l),
                                                          "idem" if ecarts(li) == ecarts(l) else ecarts(li) or "identique", l["ralentis"], l["note"]))
if nouv:
    out += ["", "**Attention** : %d couple(s) identiques en images brutes mais pas en tours : %s" % (
        len(nouv), ", ".join("%s %s %s" % (l["perso"], l["ism"], l["coup"]) for l in nouv))]
open(os.path.join(D, "modes.md"), "w").write("\n".join(out) + "\n")
print("modes : tours %s ; images %s ; %d écarts dus aux ralentissements, %d restent" % (bilan(LT), bilan(LI.values()), len(dis), len(reste)))
