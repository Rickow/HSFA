#!/usr/bin/env python3
"""Couverture instruction par instruction du code d'HYPER par celui d'Upper (K=12, adresses masquees) ; par routine
de ro9 : part couverte. Sortie couv_k9.pkl. Puis bilan pour la voie A : routines d'Hyper a reporter dans Upper
(nouvelles < 50 %, modifiees 50-90 %), tests BTST $D3, proprietaire (perso / moteur / selection...)."""
import os, sys, pickle, bisect, collections, csv
import numpy as np
os.environ["GRAIN"] = "routine"
sys.path.insert(0, "<workspace>/work/carto_ro9")
import commun as C
from couverture import cover
import atteint as AT
OUT = os.path.dirname(os.path.abspath(__file__))
f = os.path.join(OUT, "couv_k9.pkl")
if not os.path.exists(f):
    cov, va = cover('ro9', ('ro5',), False)
    starts = [a for a, _ in AT.G('ro9')['funcs']]
    n = collections.Counter(); k = collections.Counter()
    for v, c in zip(va.tolist(), cov.tolist()):
        i = bisect.bisect_right(starts, v) - 1
        if i >= 0: n[starts[i]] += 1; k[starts[i]] += c
    pickle.dump({a: (k[a] / n[a] if n[a] else 1.0) for a in starts}, open(f, "wb"))
    print("ro9 couvert par ro5 : %.1f %%" % (100 * cov.mean()))
CV9 = pickle.load(open(f, "rb"))
CMP9 = pickle.load(open(os.path.join("<workspace>/work/carto_ro9", "comparaison_ro9_routine.pkl"), "rb"))
T9 = AT.taille('ro9')
# tests BTST $D3 par routine
bt = collections.Counter(); btp = {}
for r in csv.DictReader(open("<workspace>/work/agent_hyper_index/btst_d3.tsv"), delimiter='\t'):
    a = int(r['routine'], 16); bt[a] += 1; btp[a] = r['proprietaire']
# bornes du code par perso (INDEX-HYPER §2.3)
B = [(0xAC350, 'Ryu'), (0x2A0000, 'fin persos')]
def proprio(a):
    if a in btp: return 'perso' if btp[a] != 'moteur' else 'moteur'
    return 'perso' if 0xAC350 <= a < 0x2A0000 else 'moteur/autre'
def etat(a):
    c = CV9.get(a, 1.0); return 'nouveau' if c < 0.5 else ('modifie' if c < 0.9 else 'present')
tab = collections.defaultdict(collections.Counter)
for a in T9:
    if CMP9[a]['natif']: continue
    e = etat(a); p = proprio(a); t = tab[(e, p)]
    t['o'] += T9[a]; t['n'] += 1; t['i'] += CMP9[a]['n68']; t['bt'] += bt[a]
print("%-10s %-14s %9s %6s %8s %6s" % ("etat", "proprietaire", "octets", "rout.", "instr68K", "BTST"))
for (e, p), t in sorted(tab.items()):
    print("%-10s %-14s %9d %6d %8d %6d" % (e, p, t['o'], t['n'], t['i'], t['bt']))
# BTST dans des routines 'present' (>= 90 %) ?
print("BTST $D3 dans des routines couvertes >= 90 % :", sum(bt[a] for a in bt if etat(a) == 'present'))
pickle.dump(dict(etat={a: etat(a) for a in T9}, bt=bt), open(os.path.join(OUT, "bilan_a.pkl"), "wb"))
with open(os.path.join(OUT, "hyper_a_reporter.tsv"), "w") as fo:
    fo.write("routine_ro9\ttaille\tn68\tcouverture_par_ro5\tetat\tproprietaire\tbtst_d3\tpartenaire_ro5\tclasse\n")
    for a in sorted(T9):
        if CMP9[a]['natif'] or etat(a) == 'present': continue
        r = CMP9[a]['ro5']
        fo.write("0x%X\t%d\t%d\t%.2f\t%s\t%s\t%d\t%s\t%s\n" % (a, T9[a], CMP9[a]['n68'], CV9[a], etat(a), proprio(a), bt[a],
                 '0x%X' % r['partenaire'] if r['partenaire'] is not None else '', r['classe']))
