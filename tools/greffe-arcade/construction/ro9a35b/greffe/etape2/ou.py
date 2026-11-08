#!/usr/bin/env python3
"""ou.py CONSTRUCTION ADR68K... : instruction de la carte d'image -> va MIPS -> routine (greffee : routine d'Upper)"""
import sys, os, bisect, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import couv_ro9a as CR
G = CR.G
cons = sys.argv[1]
off, va, txt = [], [], []
for l in open(os.path.join(G, 'constructions', cons, 'b9', 'carte_image.txt')):
    p = l.split(None, 2); off.append(int(p[0], 16)); va.append(int(p[1], 16)); txt.append(p[2].rstrip() if len(p) > 2 else '')
J = json.load(open(os.path.join(G, 'constructions', cons, 'greffe.json')))
blocs = sorted((int(n, 16), int(a, 16), int(b, 16)) for a, b, n in J['blocs']); bn = [n for n, _, _ in blocs]
import commun as C
st5, st9 = C.starts('ro5'), C.starts('ro9')
for a in sys.argv[2:]:
    a = int(a, 16); i = bisect.bisect_right(off, a) - 1
    v = va[i]; k = bisect.bisect_right(bn, v) - 1; s = ''
    if k >= 0 and blocs[k][0] <= v < blocs[k][0] + blocs[k][2] - blocs[k][1]:
        f = blocs[k][1] + v - blocs[k][0]; s = 'greffe : Upper 0x%X (routine 0x%X)' % (f, st5[bisect.bisect_right(st5, f) - 1])
    else: s = 'Hyper 0x%X (routine 0x%X)' % (v, st9[bisect.bisect_right(st9, v) - 1])
    print("$%06x -> ligne $%06x mips 0x%X : %s  | %s" % (a, off[i], v, s, txt[i]))
