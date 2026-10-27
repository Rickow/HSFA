#!/usr/bin/env python3
"""Donnees d'Upper absentes d'Hyper (fenetres de 32 o, pointeurs masques, methode de carto_ro9/donnees.py, sens
inverse), et rattachement des plages absentes aux routines qui les referencent (constantes du code) :
arcade (sous-arbres des scenes 6/8/A/C, scene 4/2) / autres. Sortie donnees_b.tsv, donnees_b.pkl."""
import os, sys, pickle, bisect, collections
import numpy as np
os.environ["GRAIN"] = "routine"
sys.path.insert(0, "<workspace>/work/carto_ro9")
import commun as C
import donnees as DN
import atteint as AT
OUT = os.path.dirname(os.path.abspath(__file__))
a5, e5 = DN.data('ro5')
S9 = DN.index('ro9')
cov = np.zeros(len(a5), bool)
for ph in (0, 2):
    h, nz = DN.win_hashes(DN.masked(a5, ph), ph)
    hit = np.fromiter((x in S9 for x in h.tolist()), dtype=bool, count=len(h)) & nz
    for i in np.nonzero(hit)[0]:
        o = ph + 4 * i; cov[o:o + DN.W] = True
zero = (a5 == 0)
absent = (~cov) & (~zero)
print("donnees d'Upper : %d o ; retrouvees dans Hyper %.1f %% ; zeros %.1f %% ; ABSENTES non nulles %d o (%.2f Mo)" % (
    len(a5), 100 * cov.mean(), 100 * (zero & ~cov).mean(), absent.sum(), absent.sum() / 2**20))
# plages absentes (fusion des trous < 64 o)
pl = []; i = 0; n = len(a5)
idx = np.nonzero(absent)[0]
if len(idx):
    d = idx[0]; f = idx[0]
    for x in idx[1:]:
        if x - f > 64: pl.append((d, f + 1)); d = x
        f = x
    pl.append((d, f + 1))
# references : constantes de donnees des routines
G = AT.G('ro5'); refs = []
for r, ds in G['data'].items():
    for x in ds: refs.append((x - C.BASE - e5, r))
refs.sort(); ro = [x for x, _ in refs]
Z = pickle.load(open(os.path.join(OUT, "zones_upper_petit.pkl"), "rb"))
BA = pickle.load(open(os.path.join(OUT, "bilan_absent.pkl"), "rb"))
arc = set().union(*(Z['res'][k] for k in ('scene 6', 'scene 8', 'scene A', 'scene C')))
def cat(r):
    if r in arc: return 'arcade 6/8/A/C'
    if r in Z['res']['scene 4 VS/combat']: return 'scene 4'
    if r in Z['res']['scene 2 selection']: return 'scene 2'
    return 'autre'
tot = collections.Counter(); lignes = []
for d, f in pl:
    # references dans la plage ou juste avant (base de table <= 256 o avant)
    k0 = bisect.bisect_left(ro, d - 256); k1 = bisect.bisect_left(ro, f)
    rs = {refs[k][1] for k in range(k0, k1)}
    cs = collections.Counter(cat(r) for r in rs)
    c = cs.most_common(1)[0][0] if cs else 'non referencee'
    tot[c] += int(absent[d:f].sum())
    lignes.append((d + e5 + C.BASE, f - d, int(absent[d:f].sum()), c, ' '.join('0x%X' % r for r in sorted(rs)[:6])))
print("donnees absentes rattachees :", dict(tot))
with open(os.path.join(OUT, "donnees_b.tsv"), "w") as fo:
    fo.write("exec_debut\tlongueur\toctets_absents_non_nuls\tcategorie_referents\treferents_ro5\n")
    for l in lignes: fo.write("0x%X\t%d\t%d\t%s\t%s\n" % l)
