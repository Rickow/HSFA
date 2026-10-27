#!/usr/bin/env python3
"""debuts68.py ro5|CONSTRUCTION SORTIE : adresses 68K des debuts de routines (premiere instruction 68K de chaque
routine MIPS) d'apres la carte d'image ; ecrit aussi SORTIE.map (adresse 68K -> identifiant en espace Upper)."""
import sys, os, bisect, json
sys.path.insert(0, "<workspace>/work/greffe_arcade/outils")
os.environ.setdefault("GRAIN", "routine")
import greffe as GRF
import commun as C
G = "<workspace>/work/greffe_arcade"
mod, sortie = sys.argv[1], sys.argv[2]
st5, st9 = C.starts('ro5'), C.starts('ro9'); s5, s9 = set(st5), set(st9)
if mod == 'ro5':
    carte = G + '/fige/ro5/carte_image.txt'
    def ident(v):
        k = bisect.bisect_right(st5, v) - 1; return ('U%X' % st5[k]) if k >= 0 else None
else:
    carte = G + '/constructions/%s/b9/carte_image.txt' % mod
    J = json.load(open(G + '/constructions/%s/greffe.json' % mod))
    blocs = sorted((int(n, 16), int(a, 16), int(b, 16)) for a, b, n in J['blocs']); bn = [n for n, _, _ in blocs]
    inv = {}
    for f, d in J['decisions'].items():
        if d[0] in ('HYPER', 'NATIF') and len(d) > 1 and d[1].startswith('0x'): inv.setdefault(int(d[1], 16), 'U%X' % int(f, 16))
    for a, r in GRF.INV.items():
        if r.get('partenaire') is not None: inv.setdefault(r['partenaire'], 'U%X?' % a)
    def ident(v):
        k = bisect.bisect_right(bn, v) - 1
        if k >= 0 and blocs[k][0] <= v < blocs[k][0] + blocs[k][2] - blocs[k][1]:
            f = blocs[k][1] + v - blocs[k][0]; r = st5[bisect.bisect_right(st5, f) - 1]; return 'U%X' % r
        h = st9[bisect.bisect_right(st9, v) - 1]
        return inv.get(h, 'H%X' % h)
vus = set(); out = []; prec = None
for l in open(carte):
    p = l.split(None, 2); o = int(p[0], 16); v = int(p[1], 16)
    i = ident(v)
    if i and i != prec and (i, o >> 12) not in vus: vus.add((i, o >> 12)); out.append((o, i))
    prec = i
open(sortie, 'w').write(''.join('%x\n' % o for o, i in out))
open(sortie + '.map', 'w').write(''.join('%x %s\n' % (o, i) for o, i in out))
print(len(out))
