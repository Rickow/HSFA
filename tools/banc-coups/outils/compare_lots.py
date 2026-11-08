#!/usr/bin/env python3
"""(banc_coups) deux passages de banc_max.sh : compare_lots.py resultats_max/<ancien> resultats_max/<nouveau>
-> ce qui change, en bien ou en mal, par etape (coups des natifs, persos MAX, croises, arcade, fins)."""
import csv, glob, os, sys, collections
A, N = sys.argv[1], sys.argv[2]
RANG = {'IDENTIQUE': 0, 'OK': 0, 'OK*': 0, 'RALENTI': 1, 'DÉCALÉ': 1, 'NC': 1, 'NT': 1, 'DIFFÉRENT': 2, 'KO': 3}


def lit(d, motif, cle, verdict='verdict'):
    r = {}
    for f in glob.glob(os.path.join(d, motif)):
        for x in csv.DictReader(open(f), delimiter='\t'):
            r[cle(f, x)] = x
    return r


def bilan(nom, a, n, verdict='verdict', detail=('detail', 'cause')):
    mieux, pire, autre = [], [], []
    for k in sorted(set(a) | set(n)):
        va = a.get(k, {}).get(verdict, '-'); vn = n.get(k, {}).get(verdict, '-')
        if va == vn:
            continue
        d = next((n.get(k, {}).get(c) for c in detail if n.get(k, {}).get(c)), '') or ''
        e = (k, va, vn, d[:110])
        ra, rn = RANG.get(va, 1), RANG.get(vn, 1)
        (mieux if rn < ra else pire if rn > ra else autre).append(e)
    print('== %s : %d mieux, %d pire, %d autres changements' % (nom, len(mieux), len(pire), len(autre)))
    for t, L in (('mieux', mieux), ('PIRE', pire), ('autre', autre)):
        for k, va, vn, d in L[:25]:
            print('  %-5s %s : %s -> %s %s' % (t, ' / '.join(str(x) for x in k), va, vn, d))
    c = collections.Counter(x.get(verdict) for x in n.values())
    print('  nouveau lot :', dict(c))


bilan('coups des natifs', lit(A, 'coups_*.tsv', lambda f, x: (x['etiquette'], x['id'])),
      lit(N, 'coups_*.tsv', lambda f, x: (x['etiquette'], x['id'])))
bilan('persos MAX', lit(A, 'max_*.tsv', lambda f, x: (os.path.basename(f)[4:-4], x['variante'])),
      lit(N, 'max_*.tsv', lambda f, x: (os.path.basename(f)[4:-4], x['variante'])))
bilan('croisés', lit(A, 'croises.tsv', lambda f, x: (x['max'], x['natif'], x['sens'])),
      lit(N, 'croises.tsv', lambda f, x: (x['max'], x['natif'], x['sens'])))
bilan('arcade MAX', lit(A, 'arcade.tsv', lambda f, x: (x['max'],)), lit(N, 'arcade.tsv', lambda f, x: (x['max'],)))
bilan('fins des natifs', lit(A, 'fins.tsv', lambda f, x: (x['perso'],)), lit(N, 'fins.tsv', lambda f, x: (x['perso'],)))
