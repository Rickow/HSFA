#!/usr/bin/env python3
"""Sous-ensemble du coeur execute dans une trace d'Upper avant une image donnee (objectif : 2 combats).
Usage : sous_ensemble.py TRACE IMAGE_MAX"""
import os, sys, pickle, collections
sys.path.insert(0, "<workspace>/work/greffe_arcade/outils")
import couverture as CV
G = CV.G
tr, kmax = sys.argv[1], int(sys.argv[2])
L = pickle.load(open(os.path.join(G, 'donnees/liste_arcade.pkl'), 'rb'))
core = set(pickle.load(open(os.path.join(G, 'donnees/coeur_greffe.pkl'), 'rb')))
by = {l['r']: l for l in L['lignes']}
R, Cr, noms = CV.charge('ro5', tr)
sel = sorted((e['k0'], r) for r, e in R.items() if e['k0'] <= kmax)
c = collections.Counter(); t = collections.Counter()
for k0, r in sel:
    l = by.get(r)
    if r in core:
        c[l['etat']] += 1; t[l['etat']] += l['taille']
        print("%6d 0x%06X %-8s %-28s %5d %s %s" % (k0, r, l['etat'], l['classe'][:28], l['taille'], 'VS' if l['vs'] else '--', l['zone'][:30]))
print(dict(c), dict(t))
