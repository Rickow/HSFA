#!/usr/bin/env python3
"""(banc_coups) meme traduction, deux oracles : compare_oracles.py resultats/coups_ro3.tsv resultats/coups_ro3-jp.tsv
-> matrice des verdicts (sfa3ud en lignes, japonais 980727 en colonnes) et liste des coups qui changent."""
import csv, sys, collections
A = {(r['perso'], r['version'], r['ligne']): r for r in csv.DictReader(open(sys.argv[1]), delimiter='\t')}
B = {(r['perso'], r['version'], r['ligne']): r for r in csv.DictReader(open(sys.argv[2]), delimiter='\t')}
M = collections.Counter()
ch = []
for k in sorted(set(A) & set(B)):
    a, b = A[k]['verdict'], B[k]['verdict']
    M[(a, b)] += 1
    if a != b:
        ch.append((k, a, b, A[k]['coup'], A[k]['cause'][:90], B[k]['cause'][:90]))
V = ['OK', 'DÉCALÉ', 'KO', 'NC', 'NT']
print('sfa3ud \\ 980727 | ' + ' | '.join(V))
for a in V:
    print('%-15s | %s' % (a, ' | '.join('%4d' % M[(a, b)] for b in V)))
print('\ncoups qui changent : %d' % len(ch))
for (p, v, l), a, b, c, ca, cb in ch:
    print('%s %s L%s %s : %s -> %s | us: %s | jp: %s' % (p, v, l, c, a, b, ca, cb))
