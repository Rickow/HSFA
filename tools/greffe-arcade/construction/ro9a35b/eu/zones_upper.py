#!/usr/bin/env python3
"""Attribution du code d'Upper absent d'Hyper, par atteignabilite BLOQUEE aux aiguilleurs de haut niveau
(taches systeme / jeu / menu et leurs aiguilleurs A5+0, A5+4) : chaque scene n'atteint alors que son sous-arbre.
Pour chaque racine : routines atteintes, et parmi elles celles dont l'homologue Hyper est absent (classe
'nouvelle'/'apparentee'), modifie, ou identique mais MORT dans Hyper (non atteint depuis le reset de ro9)."""
import os, sys, pickle, collections
import atteint as AT
OUT = os.path.dirname(os.path.abspath(__file__))
INV = pickle.load(open(os.path.join(OUT, "inverse_ro5.pkl"), "rb"))
arc = pickle.load(open(os.path.join(OUT, "arcade_upper.pkl"), "rb")); viv9 = arc['vivant9']
T5 = AT.taille('ro5')
HUBS = [0x4c3f0, 0x4c820, 0x260330, 0x2611a0, 0x4d950, 0x4dd90, 0x261210, 0x261470, 0x261560, 0x261530,
        0x2614a0, 0x2614d0, 0x261500, 0x270920, 0x2524b0, 0x40cf70, 0xCED70, 0x322A0, 0x324B0, 0x32830]
RAC = {
 'scene 6': 0x24a480, 'scene 8': 0x24b050, 'scene A': 0x2a300, 'scene C': 0x270920,
 'scene 2 selection': 0x2524b0, 'scene 4 VS/combat': 0x261560, 'scene E resultat (C)': 0x40cf70,
 'scene 0 init': 0x261210,
}
def statut(a):
    r = INV[a]; c = r['classe']
    if c in ('nouvelle (<40 %)', 'apparentee (40-70 %)'): return 'absent'
    if c == 'modifiee (70-90 %)': return 'modifie'
    return 'present_vivant' if r['partenaire'] in viv9 else 'present_mort'
res = {}
for nom, r in RAC.items():
    bl = [h for h in HUBS if h != r]
    R = AT.reach('ro5', [r], bloque=bl, cle=os.environ.get('CLE', 'succ'))
    c = collections.Counter(); n = collections.Counter()
    for a in R: s = statut(a); c[s] += T5[a]; n[s] += 1
    res[nom] = R
    print("%-22s %5d routines %8d o | absent %7d o (%4d) | modifie %6d o (%3d) | present mort %6d o (%3d) | present vivant %8d o (%4d)" % (
        nom, len(R), sum(T5[a] for a in R), c['absent'], n['absent'], c['modifie'], n['modifie'],
        c['present_mort'], n['present_mort'], c['present_vivant'], n['present_vivant']))
arc6 = set().union(*(res[k] for k in ('scene 6', 'scene 8', 'scene A', 'scene C')))
autres = set().union(*(res[k] for k in res if not k.startswith('scene 6') and k not in ('scene 8', 'scene A', 'scene C')))
excl = arc6 - autres
c = collections.Counter(); n = collections.Counter()
for a in excl: s = statut(a); c[s] += T5[a]; n[s] += 1
print("\nscenes 6/8/A/C hors sous-arbres des autres scenes : %d routines, %d o ; absent %d o (%d), modifie %d o (%d), mort %d o (%d), vivant %d o (%d)" % (
    len(excl), sum(T5[a] for a in excl), c['absent'], n['absent'], c['modifie'], n['modifie'], c['present_mort'], n['present_mort'], c['present_vivant'], n['present_vivant']))
pickle.dump(dict(res=res, excl=excl), open(os.path.join(OUT, "zones_upper%s.pkl" % ("_petit" if os.environ.get("CLE") == "petit" else "")), "wb"))
