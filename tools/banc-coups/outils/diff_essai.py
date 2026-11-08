#!/usr/bin/env python3
"""(banc_coups) PISTE D'UN KO : images d'un essai cote a cote, arcade / traduction, en marquant les differences.
Usage : diff_essai.py <module> <Perso_version> <id> [champs]   ex. diff_essai.py ro3 Ryu_A L692.1
Colonnes : image, etat J1, etat J2, x1, y1, x2, vie2, $AA, pointeur et empreinte du pas, tours, vie1."""
import glob, os, sys
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mod, pv, tid = sys.argv[1:4]
p, v = pv.rsplit('_', 1)
tr = os.path.join(B, 'essais', mod, pv, mod, 'log.txt')
ref = glob.glob(os.path.join(B, 'essais', 'cache_arcade', '%s_%s_*' % (p, v), 'log.txt'))


def lit(f):
    d = {}
    for l in open(f, errors='replace'):
        t = l.split()
        if t and t[0] == 'F' and t[1] == tid:
            d[int(t[2])] = t
    return d


T = lit(tr)
R = lit(ref[0]) if ref else {}
for r in sorted(set(T) | set(R)):
    a, b = R.get(r), T.get(r)
    fa = ' '.join([a[3], a[4], a[8], a[9], a[11][:8]]) if a else '-'
    fb = ' '.join([b[3], b[4], b[8], b[9], b[11][:8]]) if b else '-'
    print('%4d %s %-40s %s' % (r, '  ' if fa == fb else '!!', fa, fb))
