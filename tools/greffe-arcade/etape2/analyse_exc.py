#!/usr/bin/env python3
"""analyse_exc.py CONSTRUCTION TRACE : exception du journal -> instruction fautive, chaine d'appels (pile), adresse
d'acces (bloc de la greffe -> adresse d'Upper d'origine)."""
import sys, os, json, subprocess, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
G = "<workspace>/work/greffe_arcade"
cons, tr = sys.argv[1], sys.argv[2]
J = json.load(open(os.path.join(G, 'constructions', cons, 'greffe.json')))
L = open(os.path.join(G, 'traces', tr, 'journal.txt')).read().splitlines()
pile = next((l.split()[1:] for l in L if l.startswith('PILE')), None)
exc = next((l for l in L if l.startswith('EXCEPTION')), None)
print(exc)
if not pile: sys.exit()
w = [int(x, 16) for x in pile]
pc = int(re.search(r'pc=([0-9a-f]+)', exc).group(1), 16)
if pc in (0xa06, 0xa04): acc = (w[1] << 16) | w[2]; pcx = (w[5] << 16) | w[6]; ret = w[7:]
else: acc = None; pcx = (w[1] << 16) | w[2]; ret = w[3:]
adrs = [pcx - 4, pcx - 2, pcx] + [(ret[i] << 16) | ret[i + 1] for i in range(0, 12, 2) if ret[i] < 0x10]
subprocess.run(['python3', os.path.join(G, 'etape2', 'ou.py'), cons] + ['%x' % a for a in adrs if a])
if acc is not None:
    a68 = acc & 0xffffff; print("adresse d'acces $%06x" % a68)
    gy = int(J.get('grf_y', '0xd10000'), 16) if isinstance(J.get('grf_y'), str) else 0xD10000
    if gy <= a68 < gy + J['taille_bloc']:
        import donnees2 as D2  # noqa
        o = a68 - gy
        R = J.get('regions')
        if R:
            for a, b, off in R:
                a, b, off = int(a, 16), int(b, 16), int(off, 16)
                if off <= o < off + (b - a): print("  bloc de la greffe +$%x = Upper 0x%X (region 0x%X-0x%X)" % (o, a + o - off, a, b))
