"""bouge.py <cand> <ref> : coups dont une valeur Upper diffère entre deux copies (lignes.json des deux relevés)."""
import json, os, sys
ICI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a, r = (os.path.basename(os.path.normpath(x)) for x in sys.argv[1:3])
A = {(l["perso"], l["ism"], l["id"]): l for l in json.load(open(os.path.join(ICI, "resultats", a, "lignes.json")))}
R = {(l["perso"], l["ism"], l["id"]): l for l in json.load(open(os.path.join(ICI, "resultats", r, "lignes.json")))}
L = ["# Valeurs Upper qui ont bougé : `%s` contre `%s`" % (a, r), "", "| perso | isme | coup | grandeur | %s | %s | PSP |" % (r, a), "|---|---|---|---|---|---|---|"]
n = 0
for k in sorted(set(A) | set(R)):
    x, y = A.get(k), R.get(k)
    if not x or not y:
        L.append("| %s | %s | %s | (coup %s) | | | |" % (k[0], k[1], (x or y)["coup"], "nouveau" if x else "disparu")); n += 1; continue
    for g in sorted(set(x["upper"]) | set(y["upper"])):
        if not g.startswith("_ralentis") and x["upper"].get(g) != y["upper"].get(g):
            L.append("| %s | %s | %s | %s | %s | %s | %s |" % (k[0], k[1], x["coup"], g, y["upper"].get(g, ""), x["upper"].get(g, ""), x["psp"].get(g, ""))); n += 1
L.insert(2, "%d différence(s)." % n)
open(os.path.join(ICI, "resultats", a, "bouge_depuis_%s.md" % r), "w").write("\n".join(L) + "\n")
print("%d valeur(s) Upper ont bougé depuis %s" % (n, r))
