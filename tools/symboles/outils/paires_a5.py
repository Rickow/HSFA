#!/usr/bin/env python3
"""Correspondance des déplacements A5 (variables globales) et A6 (champs de structure) entre
l'image traduite (numérotation PS2 : octet XOR 1, moitiés de long échangées, zone du portage
relogée) et la ROM arcade, votée sur les instructions alignées et les trous 1x1 de même mnémonique.
Sortie : _cache/paires_a5.json {'A5': {trad: [[arcade, votes, tailles]...]}, 'A6': ...}"""
import sys, os, re, json, pickle, bisect, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desasm as D, fonctions as F
ICI = os.path.dirname(os.path.abspath(__file__)); CA = os.path.join(ICI, '..', '_cache')
R = re.compile(r'\((-?)\$([0-9a-f]+),(A[56])\)')

def disps(ops):
    return [(r, ((-1 if s else 1) * int(h, 16)) & 0xffff) for s, h, r in R.findall(ops)]

def taille(mn):
    if mn.endswith('.b') or mn in D.OCTET: return 'B'
    if mn.endswith('.w'): return 'W'
    if mn.endswith('.l'): return 'L'
    return '?'

def main():
    T = D.desasm(os.path.join(ICI, '..', '_trad.bin'), 0, 0x1000, F.bornes_trad()[0], 'trad')
    A = D.desasm('<workspace>/work/cps2/sfa3ud_prog.bin', 0, 0, 0x100000, 'arc')
    m = pickle.load(open(os.path.join(CA, 'alignement.pkl'), 'rb'))
    ti = {x[0]: k for k, x in enumerate(T)}; ai = {x[0]: k for k, x in enumerate(A)}
    M = {ti[t]: ai[a] for t, (a, _) in m.items()}
    votes = {'A5': collections.defaultdict(collections.Counter), 'A6': collections.defaultdict(collections.Counter)}
    tail = collections.defaultdict(set)
    vt_taille = {'A5': collections.defaultdict(collections.Counter), 'A6': collections.defaultdict(collections.Counter)}
    def vote(x, y):
        if x[2] != y[2]: return
        p = disps(x[3]); q = disps(y[3])
        if len(p) != len(q): return
        for (r1, v1), (r2, v2) in zip(p, q):
            if r1 != r2: return
        tl = taille(x[2])
        for (r1, v1), (r2, v2) in zip(p, q):
            votes[r1][v1][v2] += 1; tail[(r1, v1)].add(tl)
            vt_taille[r1][(v1, tl)][v2] += 1
    ks = sorted(M)
    for i in ks: vote(T[i], A[M[i]])
    for a, b in zip(ks, ks[1:]):
        if b - a == 2 and M[b] - M[a] == 2: vote(T[a+1], A[M[a]+1])
    out = {}
    for r in votes:
        out[r] = {'%04x' % v: [['%04x' % w, c] for w, c in cnt.most_common(3)] + [''.join(sorted(tail[(r, v)]))]
                  for v, cnt in votes[r].items()}
    for r in vt_taille:
        out[r + '_taille'] = {'%04x/%s' % (v, tl): [['%04x' % w, c] for w, c in cnt.most_common(3)]
                              for (v, tl), cnt in vt_taille[r].items()}
    json.dump(out, open(os.path.join(CA, 'paires_a5.json'), 'w'), indent=0)
    for r in out: print(r, len(out[r]), 'déplacements appariés')

if __name__ == '__main__':
    main()
