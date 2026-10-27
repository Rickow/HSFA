#!/usr/bin/env python3
"""Hyper : sous-arbres (graphe sans grandes tables, aiguilleurs de haut niveau bloques) de la selection (scene 2),
du VS/combat (scene 4), de la fin de match (E) ; part nouvelle / modifiee par rapport a Upper (couverture K=12)."""
import os, pickle, collections
import atteint as AT
OUT = os.path.dirname(os.path.abspath(__file__))
BA = pickle.load(open(os.path.join(OUT, "bilan_a.pkl"), "rb")); E = BA['etat']; bt = BA['bt']
CMP9 = pickle.load(open("<workspace>/work/carto_ro9/comparaison_ro9_routine.pkl", "rb"))
T9 = AT.taille('ro9')
HUBS = [0x618c0, 0x61c90, 0x952e0, 0x962c0, 0x626e0, 0x62b30, 0x96330, 0x96590, 0x96620, 0x965f0, 0x2d550, 0x316070,
        0x3DA00, 0x3EC20, 0x3EE30, 0x3F1B0]
RAC = {'scene 2 selection': 0x316070, 'scene 4 VS/combat': 0x96620, 'scene E fin de match (C)': 0x2d550, 'menu des modes': 0x626e0}
res = {}
for nom, r in RAC.items():
    R = AT.reach('ro9', [r], bloque=[h for h in HUBS if h != AT.fstart('ro9', r)], cle='petit')
    res[nom] = R
    c = collections.Counter()
    for a in R:
        if CMP9[a]['natif']: continue
        e = E[a]; c[e] += T9[a]; c[e + 'n'] += 1; c[e + 'i'] += CMP9[a]['n68']; c[e + 'b'] += bt[a]
    print("%-26s %5d rout. | nouveau %6d o (%3d r., %5d instr., %4d BTST) | modifie %6d o (%3d r., %5d instr., %4d BTST) | present %7d o" % (
        nom, len(R), c['nouveau'], c['nouveaun'], c['nouveaui'], c['nouveaub'], c['modifie'], c['modifien'], c['modifiei'], c['modifieb'], c['present']))
pickle.dump(res, open(os.path.join(OUT, "sous_arbres9.pkl"), "wb"))
