#!/usr/bin/env python3
"""GENERE disposition_carte.lua (table de la disposition de la traduction SFA3, lue par disposition.lua).
Usage : gen_disposition.py [resultat_compare_ram.json]
Sources : vars.json (carte_vars.py : votes des instructions alignees + relocation de la zone basse) ; optionnellement
le resultat de compare_ram.py pour la FORME des longs (s32 = moities echangees par defaut ; 'u8x4' / 's16x2' si la
comparaison a la RAM arcade l'etablit)."""
import os, sys, json, pickle
A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = json.load(open(os.path.join(A, "vars.json")))
reloc = pickle.load(open("<workspace>/work/agent_symboles/_cache/reloc_a5.pkl", "rb"))
CMP = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else None
N = {"B": 1, "W": 2, "L": 4}
def s16(d): return d - 0x10000 if d & 0x8000 else d
# 1) intervalles relogés (deltas PAIRS = mots/longs) : arcade [lo+D, hi+D] -> traduction a - D
iv = []
for lo, hi, add in reloc:
    if add % 2: continue
    alo, ahi = 0xFF8000 + s16((lo + add) & 0xffff), 0xFF8000 + s16((hi + add) & 0xffff)
    add = (0xFF8000 + s16(lo)) - alo
    iv.append((alo, ahi + 1, add))
iv.sort()
def defaut(a, n):
    for lo, hi, d in iv:
        if lo <= a < hi or (n == 1 and lo <= (a ^ 1) < hi): return ((a ^ 1) if n == 1 else a) + d
    return (a ^ 1) if n == 1 else a
# 2) exceptions par variable : adresse arcade EFFECTIVE (oracle RAM d'abord, puis votes >= 2) ; formes
exc = {}; formes = {}; choix = {}
def effective(e, r):
    """(adresse arcade, forme) ou (None, None) ; r = verdict de compare_ram.py"""
    prim = e["paires"] if e["paires"] is not None else e["recette"]
    st = r["statut"] if r else ""
    if st.startswith("identique sous") or st.startswith("forme"):
        lst = st.split(" ", 2)[2].split(" (")[0].split(",") if st.startswith("identique sous") else st.split(" ", 1)[1].split(" (")[0].split(",")
        for src in ("paires", "recette", "type"):
            fs = [x.split("/")[1] for x in lst if x.split("/")[0] == src]
            if fs and e[src] is not None:
                f = "recette" if "recette" in fs else fs[0]
                return e[src], (None if f == "recette" else f)
    if st.startswith("identique") or st.startswith("dynamique") or st.startswith("pointeur"): return prim, None
    if e["paires"] is not None and e["votes"] >= 2: return e["paires"], None
    return None, None
for key, reg in (("var_a5", 5), ("var_a6", 6)):
    for k, e in V[key].items():
        t, T = k.split("/"); t = int(t, 16); n = N[T]
        r = CMP["a5" if reg == 5 else "joueurs"].get(k) if CMP else None
        p, f = effective(e, r)
        if p is None: continue
        if reg == 5:
            if defaut(p, n) != t: exc[(p, n)] = t
            if f: formes[(p, n)] = f
        else:
            if ((p ^ 1) if n == 1 else p) != t: exc[(0x1000000 | p, n)] = t
            if f: formes[(0x1000000 | p, n)] = f
        choix[k] = "%06x" % p
json.dump(choix, open(os.path.join(A, "resultats", "disposition_choix.json"), "w"), indent=0)
L = ["-- GENERE par gen_disposition.py (ne pas editer) : disposition de la traduction SFA3 (ro3, recette cps2)",
     "return {", "  intervalles = {   -- {arcade_debut, arcade_fin (exclue), traduction - arcade}"]
L += ["    {0x%06X, 0x%06X, %d}," % x for x in iv]
L += ["  },", "  exceptions = {   -- [adresse_arcade * 8 + taille] = adresse traduction (champs A6 : 0x1000000 + deplacement)"]
L += ["    [0x%07X * 8 + %d] = 0x%06X," % (a, n, t) for (a, n), t in sorted(exc.items())]
L += ["  },", "  formes = {   -- longs dont la forme n'est pas 'moities echangees'"]
L += ["    [0x%07X * 8 + %d] = \"%s\"," % (a, n, f) for (a, n), f in sorted(formes.items())]
L += ["  },", "  portage = { {0xFF4000, 0xFF5000} },   -- zone des variables propres au portage (A5 $C000-$CFFF)", "}"]
open(os.path.join(A, "outils", "disposition_carte.lua"), "w").write("\n".join(L) + "\n")
print("intervalles %d, exceptions %d (A5 %d, champs %d), formes %d" % (len(iv), len(exc), sum(1 for a, _ in exc if a < 0x1000000),
      sum(1 for a, _ in exc if a >= 0x1000000), len(formes)))
