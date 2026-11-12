#!/usr/bin/env python3
"""Carte du code de ro9 par tranches : part identique a Upper/SFA3, modifiee, nouvelle ; plus grosses routines
nouvelles ; et ce qui caracterise le code nouveau (tests de version $D3, LEA vers la zone de donnees nouvelle)."""
import os, re, pickle, collections
os.environ.setdefault("GRAIN", "routine")
import commun as C
F = pickle.load(open(os.path.join(C.OUT, "comparaison_ro9_routine.pkl"), "rb"))
tr = pickle.load(open(os.path.join(C.OUT, "tr68k_ro9_routine.pkl"), "rb"))
ID = ('identique', 'identique 68K', 'deplacements')
def grp(c):
    if c in ID: return 'id'
    if c.startswith('quasi') or c.startswith('modifiee'): return 'mod'
    if c.startswith('apparentee'): return 'app'
    return 'new'
B = collections.defaultdict(collections.Counter)
for a, r in F.items(): B[a // 0x20000][grp(r['meilleur'])] += r['taille']
print("tranche (fichier)      identique  modifiee  apparentee  nouvelle   (%% de la taille)")
for k in sorted(B):
    t = sum(B[k].values())
    print("  %s  %5.0f %9.0f %10.0f %9.0f" % (C.fe(k * 0x20000), 100*B[k]['id']/t, 100*B[k]['mod']/t, 100*B[k]['app']/t, 100*B[k]['new']/t))
# routines nouvelles : caracteristiques
new = [(r['taille'], a) for a, r in F.items() if grp(r['meilleur']) == 'new' and not r['natif']]
new.sort(reverse=True)
d3 = sum(1 for _, a in new if any('$00d3(' in mn for _, _, mn in tr.get(a) or ()))
print("\nroutines nouvelles (hors natif) : %d, %d o ; dont avec test $D3 : %d" % (len(new), sum(s for s, _ in new), d3))
for s, a in new[:15]:
    mns = [mn for _, _, mn in tr.get(a) or ()]
    n3 = sum(1 for m in mns if '$00d3(' in m); n2 = sum(1 for m in mns if '$0102(' in m or '$0116(' in m)
    print("   %s  %6d o  BTST/acces $D3 %3d  acces $102/$116 %3d" % (C.fe(a), s, n3, n2))
