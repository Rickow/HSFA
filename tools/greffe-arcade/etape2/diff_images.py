#!/usr/bin/env python3
"""diff_images.py CONSTRUCTION cf_upper.txt cf_ro9a.txt : couvertures image par image (lua/couv_images.lua) depuis
l'entree dans un meme etat ; routines ramenees a l'espace d'Upper (copie greffee -> routine d'Upper ; routine d'Hyper
-> routines d'Upper dont elle est l'homologue retenu) ; premiere image de chaque routine des deux cotes."""
import sys, os, bisect, json, collections
sys.path.insert(0, "<workspace>/work/greffe_arcade/outils"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import couverture as CV, couv_ro9a as CR, commun as C, greffe as GRF
G = CV.G
cons, fu, f9 = sys.argv[1:4]
off5, va5, rt5, _, _, _ = CV.carte('ro5')
def r5(a):
    i = bisect.bisect_right(off5, a) - 1
    return rt5[i] if i >= 0 else None
J = json.load(open(os.path.join(G, 'constructions', cons, 'greffe.json')))
blocs = sorted((int(n, 16), int(a, 16), int(b, 16)) for a, b, n in J['blocs']); bn = [n for n, _, _ in blocs]
inv = collections.defaultdict(set)
for f, d in J['decisions'].items():
    if d[0] == 'HYPER' and len(d) > 1 and d[1].startswith('0x'): inv[int(d[1], 16)].add(int(f, 16))
for a, r in GRF.INV.items():
    if r.get('partenaire') is not None and r['partenaire'] not in inv: inv[r['partenaire']].add(a)
off9, va9 = [], []
for l in open(os.path.join(G, 'constructions', cons, 'b9', 'carte_image.txt')):
    p = l.split(None, 2); off9.append(int(p[0], 16)); va9.append(int(p[1], 16))
st5, st9 = C.starts('ro5'), C.starts('ro9')
def r9(a):
    i = bisect.bisect_right(off9, a) - 1
    if i < 0: return set()
    v = va9[i]; k = bisect.bisect_right(bn, v) - 1
    if k >= 0 and blocs[k][0] <= v < blocs[k][0] + blocs[k][2] - blocs[k][1]:
        f = blocs[k][1] + v - blocs[k][0]; return {st5[bisect.bisect_right(st5, f) - 1]}
    h = st9[bisect.bisect_right(st9, v) - 1]
    return inv.get(h, {('H', h)})
def charge(f, fn):
    R = {}
    for l in open(f):
        rel, a = l.split(); rel = int(rel); a = int(a, 16)
        x = fn(a)
        for r in (x if isinstance(x, set) else {x}):
            if r is not None and r not in R: R[r] = rel
    return R
U = charge(fu, r5); N = charge(f9, r9)
out = []
for r, k in sorted(U.items(), key=lambda x: x[1]):
    k9 = N.get(r)
    if k9 is None or abs(k9 - k) > 2: out.append((k, r, k9))
print("routines d'Upper vues : Upper %d, ro9a %d ; ecarts (absentes ou decalees de plus de 2 images) : %d" % (len(U), len(N), len(out)))
for k, r, k9 in out[:60]:
    d = J['decisions'].get(hex(r))
    print("  Upper image %3d  0x%06X  ro9a %s  %s" % (k, r, k9, ' '.join(d) if d else ''))
