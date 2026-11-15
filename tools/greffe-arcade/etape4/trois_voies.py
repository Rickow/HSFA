#!/usr/bin/env python3
"""trois_voies.py : pour chaque fin de la greffe (TRACES_G/PREF_<p>_<v>), écarts image par image (même image relative)
à l'ancien oracle (TRACES_A/u_<p>) et au nouveau (TRACES_N/u_<p>), et ancien contre nouveau.
Usage : trois_voies.py TRACES_G PREF TRACES_A TRACES_N [--seuil 3.0] [--tsv sortie.tsv] [--fins 1c_Z3,21_Z3]
Ecart = % de pixels différents (> 24 sur un canal), comme cmp_fins_upper.py.
Par fin : n, moyenne(G-A), moyenne(G-N), images où l'oracle a changé (A-N >= seuil), parmi elles G plus proche de N
(gain > 1 pt) / plus loin ; images où G s'écarte des DEUX (>= seuil) alors que A = N (< seuil) = écart non imputable
à l'oracle ; durées (journal FIN_A) des deux oracles."""
import sys, os, glob, re
from PIL import Image, ImageChops
def opt(k, d):
    if k in sys.argv: i = sys.argv.index(k); v = sys.argv[i + 1]; del sys.argv[i:i + 2]; return v
    return d
seuil = float(opt('--seuil', '3.0')); tsv = opt('--tsv', None); fins_sel = opt('--fins', None)
TG, P, TA, TN = sys.argv[1:5]
def serie(d, sf):
    if not (os.path.isdir(d) and os.path.exists(sf)): return {}
    fs = sorted(glob.glob(os.path.join(d, '**', '*.png'), recursive=True), key=lambda f: (len(f), f))
    rel = [int(l.split()[2]) for l in open(sf, encoding='utf-8') if len(l.split()) > 2]
    return dict(zip(rel, fs))
_c = {}
def img(f):
    if f not in _c:
        if len(_c) > 900: _c.clear()
        _c[f] = Image.open(f).convert('RGB')
    return _c[f]
def ec(a, b):
    x, y = img(a), img(b)
    if x.size != y.size: return 100.0
    d = ImageChops.difference(x, y).convert('L').point(lambda v: 255 if v > 24 else 0)
    return 100.0 * d.histogram()[255] / (x.size[0] * x.size[1])
def plages(xs):
    o = []
    for x in sorted(xs):
        if o and x - o[-1][1] <= 60: o[-1][1] = x
        else: o.append([x, x])
    return ' '.join('%d' % a if a == b else '%d-%d' % (a, b) for a, b in o) or '-'
def duree(d):
    try: t = open(os.path.join(d, 'journal.txt'), encoding='utf-8', errors='replace').read()
    except OSError: return '-'
    m = re.search(r'FIN_A (\d+) duree (\d+)', t)
    return m.group(2) if m else '-'
fins = sorted(os.path.basename(d)[len(P) + 1:] for d in glob.glob(os.path.join(TG, P + '_*_*')) if os.path.isdir(d))
if fins_sel: fins = [f for f in fins if f in fins_sel.split(',')]
out = []
tot = dict(n=0, chg=0, mieux=0, pire=0, gA=0.0, gN=0.0, rest=0)
print('fin\tn\tmoy_G-A\tmoy_G-N\toracle_change\tG_plus_proche_N\tG_plus_loin_N\tecart_G_hors_oracle\tplages_change\tplages_mieux\tplages_pire\tplages_hors_oracle')
for f in fins:
    p, v = f.split('_', 1)
    G = serie(os.path.join(TG, '%s_%s' % (P, f)), os.path.join(TG, '%s_%s.sf' % (P, f)))
    A = serie(os.path.join(TA, 'u_' + p), os.path.join(TA, 'u_%s.sf' % p))
    N = serie(os.path.join(TN, 'u_' + p), os.path.join(TN, 'u_%s.sf' % p))
    rs = sorted(set(G) & set(A) & set(N))
    rs = [r for r in rs if r > 0]
    ga = {r: ec(G[r], A[r]) for r in rs}; gn = {r: ec(G[r], N[r]) for r in rs}; an = {r: ec(A[r], N[r]) for r in rs}
    chg = [r for r in rs if an[r] >= seuil]
    mieux = [r for r in chg if gn[r] < ga[r] - 1.0]; pire = [r for r in chg if gn[r] > ga[r] + 1.0]
    hors = [r for r in rs if an[r] < seuil and gn[r] >= seuil]
    n = len(rs); mA = sum(ga.values()) / n if n else 0; mN = sum(gn.values()) / n if n else 0
    tot['n'] += n; tot['chg'] += len(chg); tot['mieux'] += len(mieux); tot['pire'] += len(pire); tot['rest'] += len(hors)
    tot['gA'] += sum(ga.values()); tot['gN'] += sum(gn.values())
    l = '%s\t%d\t%.1f\t%.1f\t%d\t%d\t%d\t%d\t%s\t%s\t%s\t%s' % (f, n, mA, mN, len(chg), len(mieux), len(pire), len(hors), plages(chg), plages(mieux), plages(pire), plages(hors))
    print(l, flush=True); out.append(l)
    if tsv:
        with open(tsv + '.images', 'a', encoding='utf-8') as fi:
            for r in rs: fi.write('%s\t%d\t%.2f\t%.2f\t%.2f\n' % (f, r, ga[r], gn[r], an[r]))
r = '# %d fins, %d images ; moyenne G-ancien %.2f %%, G-nouveau %.2f %% ; oracle changé sur %d images : G plus proche du nouveau %d, plus loin %d ; écart de G hors oracle (A = N, G != N) : %d' % (
    len(fins), tot['n'], tot['gA'] / max(1, tot['n']), tot['gN'] / max(1, tot['n']), tot['chg'], tot['mieux'], tot['pire'], tot['rest'])
print(r)
if tsv: open(tsv, 'w', encoding='utf-8').write(r + '\n' + '\n'.join(out) + '\n')
