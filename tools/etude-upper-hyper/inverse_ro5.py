#!/usr/bin/env python3
"""Correspondance INVERSE : chaque routine d'Upper (ro5, GRAIN=routine) -> meilleure routine d'Hyper (ro9).
Reprend les profils et la fonction 'best' de carto_ro9/comparaison.py (memes niveaux : identique, identique 68K,
deplacements, ressemblance Jaccard). Sortie : inverse_ro5.pkl {va5: dict(b, taille, nat, classe, partenaire, score)}."""
import os, sys, pickle
os.environ["GRAIN"] = "routine"
CR9 = "<workspace>/work/carto_ro9"; sys.path.insert(0, CR9)
import comparaison as CMP
OUT = os.path.dirname(os.path.abspath(__file__))
P5 = pickle.load(open(os.path.join(CR9, "profil_ro5_routine.pkl"), "rb"))
P9 = pickle.load(open(os.path.join(CR9, "profil_ro9_routine.pkl"), "rb"))
I9 = CMP.index(P9)
res = {}
for a, p in P5.items():
    k, pa, j = CMP.best(p, P9, I9)
    res[a] = dict(b=p['b'], taille=p['b'] - a, nat=p['nat'], n68=p['n68'], classe=CMP.classe(k, j), partenaire=pa, score=round(j, 3))
pickle.dump(res, open(os.path.join(OUT, "inverse_ro5.pkl"), "wb"))
import collections
tot = sum(r['taille'] for r in res.values()); c = collections.Counter(); n = collections.Counter()
for r in res.values(): c[r['classe']] += r['taille']; n[r['classe']] += 1
print("ro5 : %d routines, %d o MIPS" % (len(res), tot))
for k in CMP.ORDRE: print("  %-26s %5.1f %%  %5d" % (k, 100 * c[k] / tot, n[k]))
