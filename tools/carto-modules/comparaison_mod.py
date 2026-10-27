#!/usr/bin/env python3
"""Parente de code entre modules, au grain 'routine' (zones 68K de zones.py), niveau MIPS seulement
(le niveau 68K de carto_ro9 demande une traduction complete de chaque module) :
  identique     : MIPS egal, cibles de jal et adresses lui/addiu masquees (modcompare.sig)
  deplacements  : idem, deplacements memoire masques aussi
  ressemblance  : Jaccard des 4-grammes MIPS normalises (index inverse, 10 meilleurs candidats)
Natives (critere is_native) exclues des pourcentages 'code recompile'. Sorties : comparaison_mod.txt,
comparaison_mod.pkl. Usage : GRAIN=routine nice -n 19 python3 comparaison_mod.py"""
import os, sys, pickle, collections
os.environ.setdefault('GRAIN', 'routine')
sys.path.insert(0, '.')
import commun as C
from modcompare import sig, grams
from multiprocessing import Pool
MODS = ['ro1','ro2','ro3','ro4','ro5','ro6','ro7','ro8','ro9']
FLOU = {'ro1': ['ro3','ro5','ro9','ro2','ro7'], 'ro2': ['ro8','ro4','ro6','ro3','ro1'], 'ro4': ['ro2','ro8','ro6','ro3'],
        'ro6': ['ro4','ro2','ro8','ro3'], 'ro7': ['ro3','ro2','ro6','ro1','ro5'], 'ro8': ['ro2','ro4','ro6','ro3'],
        'ro9': ['ro1','ro2','ro4','ro6','ro8']}

def profile(mod):
    P = {}
    for a, b in C.funcs(mod):
        s = C.seg(mod, a, b)
        if not s: continue
        P[a] = dict(b=b, ex=sig(s, a, b, False)[0], st=sig(s, a, b, True)[0], gm=grams(s), nat=C.is_native(s)[0])
    return mod, P

def jac(x, y): return len(x & y) / len(x | y) if x and y else 0.0

def flou(args):
    X, R = args
    PX, PR = PROF[X], PROF[R]
    ig = collections.defaultdict(list)
    for a, p in PR.items():
        for g in p['gm']: ig[g].append(a)
    exR = {p['ex'] for p in PR.values()}; stR = {p['st'] for p in PR.values()}
    out = {}
    for a, p in PX.items():
        if p['ex'] in exR: out[a] = ('identique', 1.0); continue
        if p['st'] in stR: out[a] = ('deplacements', 1.0); continue
        cnt = collections.Counter()
        for g in p['gm']:
            l = ig.get(g)
            if l and len(l) < 40: cnt.update(l)
        bj = 0.0
        for c, _ in cnt.most_common(10): bj = max(bj, jac(p['gm'], PR[c]['gm']))
        out[a] = ('flou', bj)
    return X, R, out

def init(prof):
    global PROF; PROF = prof

if __name__ == '__main__':
    fp = 'comparaison_mod_profils.pkl'
    if os.path.exists(fp): PROF = pickle.load(open(fp, 'rb'))
    else:
        with Pool(4) as pool: PROF = dict(pool.map(profile, MODS))
        pickle.dump(PROF, open(fp, 'wb'))
    # 1) matrice d'identite exacte (rapide) : part de la taille du code recompile de X identique a R
    lines = ["Matrice : part (taille, code recompile hors natives) des routines de LIGNE identiques (MIPS, adresses masquees) a une routine de COLONNE"]
    lines.append('      ' + ' '.join('%6s' % r for r in MODS))
    for X in MODS:
        PX = PROF[X]; tot = sum(p['b'] - a for a, p in PX.items() if not p['nat'])
        row = []
        for R in MODS:
            if R == X: row.append('     -'); continue
            exR = {p['ex'] for p in PROF[R].values()}
            row.append('%5.1f%%' % (100 * sum(p['b'] - a for a, p in PX.items() if not p['nat'] and p['ex'] in exR) / tot))
        lines.append('%-5s ' % X + ' '.join(row))
    lines.append('')
    # 2) classes completes pour les paires d'interet
    jobs = [(X, R) for X, L in FLOU.items() for R in L]
    with Pool(4, initializer=init, initargs=(PROF,)) as pool: res = pool.map(flou, jobs)
    RES = {}
    for X, R, out in res: RES[(X, R)] = out
    ORD = ['identique', 'deplacements', '>=90 %', '70-90 %', '40-70 %', '<40 %']
    def cl(k, j):
        if k != 'flou': return k
        return '>=90 %' if j >= .9 else '70-90 %' if j >= .7 else '40-70 %' if j >= .4 else '<40 %'
    lines.append("Classes (part de la taille du code recompile de X) : " + ' | '.join(ORD))
    for X, L in FLOU.items():
        PX = PROF[X]; tot = sum(p['b'] - a for a, p in PX.items() if not p['nat'])
        for R in L:
            c = collections.Counter()
            for a, (k, j) in RES[(X, R)].items():
                if not PX[a]['nat']: c[cl(k, j)] += PX[a]['b'] - a
            lines.append('%s contre %s : ' % (X, R) + ' | '.join('%5.1f' % (100 * c[o] / tot) for o in ORD))
        # meilleur des references
        c = collections.Counter(); rk = {o: i for i, o in enumerate(ORD)}
        for a, p in PX.items():
            if p['nat']: continue
            best = min((cl(*RES[(X, R)][a]) for R in L), key=lambda o: rk[o]); c[best] += p['b'] - a
        lines.append('%s contre (%s) : ' % (X, ' ou '.join(L)) + ' | '.join('%5.1f' % (100 * c[o] / tot) for o in ORD))
        nat = [(a, p['b']) for a, p in PX.items() if p['nat']]
        lines.append('   %s : %d routines, code recompile %d o, natives %d routines (%d o)' % (X, len(PX), tot, len(nat), sum(b - a for a, b in nat)))
    open('comparaison_mod.txt', 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
    pickle.dump(RES, open('comparaison_mod.pkl', 'wb'))
