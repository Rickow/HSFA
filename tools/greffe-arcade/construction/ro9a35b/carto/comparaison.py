#!/usr/bin/env python3
"""Correspondance fonction par fonction de ro9 (Hyper) avec ro5 (Upper) et ro3 (SFA3), ROBUSTE aux decalages
d'adresses et a la version du recompilateur :
  niveau 1 'identique'      : MIPS egal, cibles de jal et adresses lui/addiu masquees (modcompare.sig)
  niveau 2 'deplacements'   : idem en masquant aussi les deplacements memoire
  niveau 3 'identique 68K'  : suite des OPCODES 68K produits par le traducteur egale (deplacements, adresses,
                              deplacements de branchement masques) -> insensible aux deux formes de CMP (§52)
  niveau 4 ressemblance     : max(Jaccard des 4-grammes MIPS normalises, Jaccard des 4-grammes 68K)
Sorties : comparaison_ro9.json (par fonction), segments colineaires (decalages), bilan texte."""
import os, sys, json, pickle, collections, bisect, hashlib
import commun as C
from modcompare import sig, grams

def norm68(seq):
    out = []
    for va, w, mn in seq or ():
        if w is None: continue
        if 0x6000 <= w <= 0x6fff: w &= 0xff00             # Bcc/BRA/BSR : deplacement masque
        out.append(w)
    return out

def g68(ws, k=4):
    return {hash(tuple(ws[i:i+k])) for i in range(len(ws)-k+1)}

def profile(mod):
    tr = pickle.load(open(os.path.join(C.OUT, "tr68k_%s%s.pkl" % (mod, C.SUF)), "rb"))
    P = {}
    for a, b in C.funcs(mod):
        s = C.seg(mod, a, b)
        nat = C.is_native(s)[0]
        w = [] if nat else norm68(tr.get(a))          # natives (C du portage) : le niveau 68K n'a pas de sens
        P[a] = dict(b=b, ex=sig(s, a, b, False)[0], st=sig(s, a, b, True)[0], gm=grams(s),
                    h68=hashlib.blake2b(repr(w).encode(), digest_size=12).digest() if len(w) >= 8 else None,
                    g6=g68(w), n68=len(w), nat=nat)
    return P

def index(P):
    ex = collections.defaultdict(list); st = collections.defaultdict(list); h6 = collections.defaultdict(list)
    ig = collections.defaultdict(list); i6 = collections.defaultdict(list)
    for a, p in P.items():
        ex[p['ex']].append(a); st[p['st']].append(a)
        if p['h68']: h6[p['h68']].append(a)
        for g in p['gm']: ig[g].append(a)
        for g in p['g6']: i6[g].append(a)
    return ex, st, h6, ig, i6

def jac(x, y): return len(x & y) / len(x | y) if x and y else 0.0

def best(p, P, I, prefer=None):
    ex, st, h6, ig, i6 = I
    def pick(lst):
        if prefer is not None:                          # partenaire le plus proche de la position attendue
            return min(lst, key=lambda a: abs(a - prefer))
        return lst[0]
    if p['ex'] in ex: return 'identique', pick(ex[p['ex']]), 1.0
    if p['h68'] and p['h68'] in h6: return 'identique 68K', pick(h6[p['h68']]), 1.0
    if p['st'] in st: return 'deplacements', pick(st[p['st']]), 1.0
    cnt = collections.Counter()
    for g in p['gm']:
        l = ig.get(g)
        if l and len(l) < 40: cnt.update(l)
    for g in p['g6']:
        l = i6.get(g)
        if l and len(l) < 40: cnt.update(l)
    bj, ba = 0.0, None
    for a, _ in cnt.most_common(10):
        j = max(jac(p['gm'], P[a]['gm']), jac(p['g6'], P[a]['g6']))
        if j > bj: bj, ba = j, a
    return 'flou', ba, bj

def classe(kind, j):
    if kind != 'flou': return kind
    if j >= 0.9: return 'quasi identique (>=90 %)'
    if j >= 0.7: return 'modifiee (70-90 %)'
    if j >= 0.4: return 'apparentee (40-70 %)'
    return 'nouvelle (<40 %)'

ORDRE = ['identique', 'identique 68K', 'deplacements', 'quasi identique (>=90 %)', 'modifiee (70-90 %)',
         'apparentee (40-70 %)', 'nouvelle (<40 %)']

def segments(pairs):
    """paires (a9, aR) identiques triees par a9 -> plus longue sous-suite croissante en aR (colinearite),
    puis segments de decalage constant"""
    pairs = sorted(pairs)
    # LIS
    import bisect as B
    tails = []; tidx = []; prev = [-1]*len(pairs)
    for i, (a, r) in enumerate(pairs):
        k = B.bisect_left(tails, r)
        if k == len(tails): tails.append(r); tidx.append(i)
        else: tails[k] = r; tidx[k] = i
        prev[i] = tidx[k-1] if k > 0 else -1
    seq = []; i = tidx[-1] if tidx else -1
    while i >= 0: seq.append(pairs[i]); i = prev[i]
    seq.reverse()
    segs = []
    for a, r in seq:
        d = r - a
        if segs and segs[-1]['delta'] == d: segs[-1]['fin9'] = a; segs[-1]['n'] += 1
        else: segs.append(dict(debut9=a, fin9=a, delta=d, n=1))
    return seq, segs

def main():
    P = {m: profile(m) for m in ('ro3', 'ro5', 'ro9')}
    I = {m: index(P[m]) for m in ('ro3', 'ro5')}
    res = {}
    for a, p in P['ro9'].items():
        r = {'fin': p['b'], 'taille': p['b'] - a, 'natif': p['nat'], 'n68': p['n68']}
        for m in ('ro5', 'ro3'):
            k, pa, j = best(p, P[m], I[m])
            r[m] = dict(classe=classe(k, j), partenaire=pa, score=round(j, 3))
        res[a] = r
    # second passage : pour les identiques a partenaires multiples, choisir le plus proche de la position
    # attendue (decalage median des voisins)
    for m in ('ro5', 'ro3'):
        ids = sorted((a, r[m]['partenaire']) for a, r in res.items() if isinstance(a, int) and r[m]["classe"] in ('identique', 'identique 68K', 'deplacements'))
        seq, segs = segments(ids)
        dl = sorted(s['delta'] for s in segs for _ in range(s['n']))
        res['_segments_' + m] = segs
        res['_colineaires_' + m] = len(seq)
        res['_identiques_' + m] = len(ids)
    json.dump({("%x" % k if isinstance(k, int) else k): v for k, v in res.items()}, open(os.path.join(C.OUT, "comparaison_ro9%s.json" % C.SUF), "w"), indent=0,
              default=lambda o: ("%x" % o) if isinstance(o, int) else str(o))
    # ---------------- bilan ----------------
    F = {a: r for a, r in res.items() if isinstance(a, int)}
    tot = sum(r['taille'] for r in F.values()); totj = sum(r['taille'] for r in F.values() if not r['natif'])
    print("ro9 : %d fonctions (cibles de jal), %d octets MIPS ; dont natives (C du portage) %d (%d o)" % (
        len(F), tot, sum(1 for r in F.values() if r['natif']), sum(r['taille'] for r in F.values() if r['natif'])))
    for m in ('ro5', 'ro3'):
        print("\nro9 contre %s (part de la taille du code ; nombre de fonctions) :" % m)
        for c in ORDRE:
            sz = sum(r['taille'] for r in F.values() if r[m]['classe'] == c); n = sum(1 for r in F.values() if r[m]['classe'] == c)
            print("   %-26s %5.1f %%  %5d" % (c, 100*sz/tot, n))
        print("   colinearite des identiques : %d / %d dans l'ordre ; %d segments de decalage constant" % (
            res['_colineaires_' + m], res['_identiques_' + m], len(res['_segments_' + m])))
    # combine : meilleur des deux
    print("\nro9 contre (ro5 OU ro3) :")
    rank = {c: i for i, c in enumerate(ORDRE)}
    comb = collections.Counter(); combn = collections.Counter()
    for r in F.values():
        c = min((r['ro5']['classe'], r['ro3']['classe']), key=lambda c: rank[c]); comb[c] += r['taille']; combn[c] += 1
        r['meilleur'] = c
    for c in ORDRE: print("   %-26s %5.1f %%  %5d" % (c, 100*comb[c]/tot, combn[c]))
    # ce qu'Hyper doit a Upper seul (identique a ro5 mais pas a ro3)
    up = sum(r['taille'] for r in F.values() if rank[r['ro5']['classe']] <= 2 and rank[r['ro3']['classe']] > 2)
    s3 = sum(r['taille'] for r in F.values() if rank[r['ro3']['classe']] <= 2 and rank[r['ro5']['classe']] > 2)
    print("   identique a Upper mais pas a SFA3 : %.1f %% ; a SFA3 mais pas a Upper : %.1f %%" % (100*up/tot, 100*s3/tot))
    # meme bilan symetrique : part du code de ro5 retrouvee dans ro9
    seen5 = collections.Counter()
    for r in F.values():
        if rank[r['ro5']['classe']] <= 2: seen5[r['ro5']['partenaire']] += 1
    tot5 = sum(b - a for a, b in C.funcs('ro5'))
    print("\nro5 : %.1f %% de son code (taille) a un jumeau identique dans ro9" % (
        100*sum(P['ro5'][a]['b'] - a for a in seen5)/tot5))
    pickle.dump(F, open(os.path.join(C.OUT, "comparaison_ro9%s.pkl" % C.SUF), "wb"))

if __name__ == "__main__":
    main()
