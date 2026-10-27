#!/usr/bin/env python3
"""Routines d'Upper SUPPRIMEES dans Hyper : classe inverse 'nouvelle'/'apparentee' (aucune routine d'Hyper ne leur
ressemble a >= 70 %) ET aucune routine d'Hyper ne les designe comme partenaire (>= 40 %). Attribution aux sous-arbres
(graphe sans grandes tables) : scenes arcade 6/8/A/C, scene 2 (selection), scene 4 (combat), scene E, autres
(attraction, menus, systeme) ; plus le code par perso (atteint seulement par les grandes tables)."""
import os, sys, pickle, collections
import atteint as AT
OUT = os.path.dirname(os.path.abspath(__file__))
INV = pickle.load(open(os.path.join(OUT, "inverse_ro5.pkl"), "rb"))
CMP9 = pickle.load(open("<workspace>/work/carto_ro9/comparaison_ro9_routine.pkl", "rb"))
Z = pickle.load(open(os.path.join(OUT, "zones_upper_petit.pkl"), "rb"))
A = pickle.load(open(os.path.join(OUT, "a5.pkl"), "rb")); D5, D9 = A['D5'], A['D9']
T5 = AT.taille('ro5')
vise = collections.defaultdict(float)
for a, r in CMP9.items():
    p = r['ro5']['partenaire']
    if p is not None: vise[p] = max(vise[p], r['ro5']['score'] if r['ro5']['classe'] not in ('identique', 'identique 68K', 'deplacements') else 1.0)
RAC5 = [0xCED70, 0x322A0, 0x324B0, 0x32830]
tout_petit = AT.reach('ro5', RAC5, cle='petit')
supp = {a for a, r in INV.items() if r['classe'] in ('nouvelle (<40 %)', 'apparentee (40-70 %)') and vise.get(a, 0) < 0.4 and not r['nat']}
reecr = {a for a, r in INV.items() if r['classe'] in ('nouvelle (<40 %)', 'apparentee (40-70 %)', 'modifiee (70-90 %)') and a not in supp}
groupes = collections.OrderedDict()
arc = set().union(*(Z['res'][k] for k in ('scene 6', 'scene 8', 'scene A', 'scene C')))
groupes['scenes arcade 6/8/A/C'] = arc
groupes['scene 4 VS/combat (hors arcade)'] = Z['res']['scene 4 VS/combat'] - arc
groupes['scene 2 selection (hors 4, arcade)'] = Z['res']['scene 2 selection'] - Z['res']['scene 4 VS/combat'] - arc
groupes['scene E / 0'] = (Z['res']['scene E resultat (C)'] | Z['res']['scene 0 init']) - Z['res']['scene 4 VS/combat'] - arc - Z['res']['scene 2 selection']
deja = set().union(*groupes.values())
groupes['reste atteint (attraction, menus, systeme)'] = tout_petit - deja
groupes['non atteint sans grandes tables (code par perso, objets)'] = set(INV) - tout_petit
par_r = collections.defaultdict(set)
for d in set(D5) - set(D9):
    for r in D5[d]['routines']: par_r[r].add(d)
print("Upper : %d routines supprimees dans Hyper (%d o MIPS) ; %d reecrites par Hyper (%d o)" % (
    len(supp), sum(T5[a] for a in supp), len(reecr), sum(T5[a] for a in reecr)))
lignes = []
for g, S in groupes.items():
    s = S & supp; w = S & reecr
    v = set().union(*(par_r[a] for a in s)) if s else set()
    print("  %-52s supprimees %4d (%7d o, %5d instr. 68K) | reecrites %4d (%7d o) | var. A5 propres a Upper : %d" % (
        g, len(s), sum(T5[a] for a in s), sum(INV[a]['n68'] for a in s), len(w), sum(T5[a] for a in w), len(v)))
    for a in sorted(s): lignes.append((g, a))
with open(os.path.join(OUT, "upper_supprimees.tsv"), "w") as f:
    f.write("groupe\troutine_ro5\ttaille\tn68\tclasse\tvar_A5_upper_seul\n")
    for g, a in lignes:
        f.write("%s\t0x%X\t%d\t%d\t%s\t%s\n" % (g, a, T5[a], INV[a]['n68'], INV[a]['classe'], ' '.join('$%04X' % d for d in sorted(par_r[a]))))
pickle.dump(dict(supp=supp, reecr=reecr, groupes=groupes), open(os.path.join(OUT, "supprimees.pkl"), "wb"))
