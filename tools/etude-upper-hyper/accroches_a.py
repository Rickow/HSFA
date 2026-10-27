#!/usr/bin/env python3
"""Voie A : points d'accroche dans Upper. Routines d'Hyper a reporter (nouvelles < 50 %, modifiees 50-90 %, ou
presentes mais contenant des BTST $D3). Pour les modifiees : routine d'Upper a remplacer (partenaire). Pour les
nouvelles : appelants dans Hyper ; un appelant 'present' = accroche a poser dans une routine d'Upper inchangee."""
import os, pickle, collections
import atteint as AT
OUT = os.path.dirname(os.path.abspath(__file__))
BA = pickle.load(open(os.path.join(OUT, "bilan_a.pkl"), "rb")); E = BA['etat']; bt = BA['bt']
CMP9 = pickle.load(open("<workspace>/work/carto_ro9/comparaison_ro9_routine.pkl", "rb"))
T9 = AT.taille('ro9'); P = AT.preds('ro9')
nouv = {a for a in T9 if E[a] == 'nouveau' and not CMP9[a]['natif']}
modif = {a for a in T9 if E[a] == 'modifie' and not CMP9[a]['natif']}
pres_bt = {a for a in T9 if E[a] == 'present' and bt[a] and not CMP9[a]['natif']}
remplace = {CMP9[a]['ro5']['partenaire'] for a in modif | pres_bt if CMP9[a]['ro5']['partenaire'] is not None}
acc = collections.Counter(); acc_r = set()
for a in nouv:
    for p in P.get(a, ()):
        if E.get(p) == 'present' and p not in pres_bt: acc[p] += 1; acc_r.add(p)
print("a reporter : nouvelles %d (%d o, %d instr.), modifiees %d (%d o, %d instr.), presentes avec BTST %d (%d o, %d BTST)" % (
    len(nouv), sum(T9[a] for a in nouv), sum(CMP9[a]['n68'] for a in nouv), len(modif), sum(T9[a] for a in modif),
    sum(CMP9[a]['n68'] for a in modif), len(pres_bt), sum(T9[a] for a in pres_bt), sum(bt[a] for a in pres_bt)))
print("routines d'Upper a remplacer (partenaires des modifiees / des presentes a BTST) : %d distinctes" % len(remplace))
print("accroches dans des routines inchangees (appelants presents des nouvelles) : %d routines, %d sites d'appel" % (len(acc_r), sum(acc.values())))
