#!/usr/bin/env python3
"""appelants.py MOD VA... : appelants (graphe approche de l'etude : jal, constantes de code, tables) de chaque VA."""
import sys, pickle, collections
EU = "<workspace>/work/etude_upper_hyper"
mod = sys.argv[1]
g = pickle.load(open(EU + '/graphe_%s.pkl' % mod, 'rb'))
pred = collections.defaultdict(set)
for a, s in g['succ'].items():
    for b in s: pred[b].add(a)
for v in sys.argv[2:]:
    v = int(v, 16)
    print("0x%X <- %s ; -> %s" % (v, ' '.join('0x%X' % x for x in sorted(pred[v])), ' '.join('0x%X' % x for x in sorted(g['succ'].get(v, ())))))
