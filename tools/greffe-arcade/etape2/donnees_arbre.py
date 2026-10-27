import os, sys, collections, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan as PL, donnees2 as D2, force as FO
rac = [0x4E1C0, 0x24EA30, 0x261560, 0x2614A0, 0x2614D0, 0x261500]
TC = PL.tables_a_completer()
P = PL.ferme(rac + sorted({u for _, u, _, _, _ in TC}), FO.FORCE)
# qui reference chaque constante de depart
qui = collections.defaultdict(set)
for r in P.atteint:
    for t, v, va in PL.refs_routine(r):
        if t == 'data': qui[v].add(r)
res = []
for v in sorted(P.donnees):
    S, Pt, RE = D2.ferme_donnees([v], max_total=4 << 20)
    res.append((sum(S.values()), v, len(S), len(RE)))
for t, v, n, re in sorted(res, reverse=True)[:25]:
    print("0x%X : %7d o, %4d segments, %4d reutilises ; code : %s" % (v, t, n, re, ' '.join('0x%X' % r for r in sorted(qui[v])[:4])))
