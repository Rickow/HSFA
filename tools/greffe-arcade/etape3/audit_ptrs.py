#!/usr/bin/env python3
"""audit_ptrs.py CONSTRUCTION : pointeurs de DONNEES reloges dans le bloc de la greffe (longs du bloc differents de
ceux d'Upper, visant une source d'Upper) -> classement : cible impaire, paire de mots signes (bas >= $FE00 ou
haut/bas petits), cible lue par Upper (journaux u_lu*), cible debut de segment."""
import os, sys, json, struct, collections, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'etape2'))
import donnees2 as D2
G = "<workspace>/work/greffe_arcade"; c = sys.argv[1]
J = json.load(open(os.path.join(G, 'constructions', c, 'greffe.json')))
blob = open(os.path.join(G, 'constructions', c, 'greffe_donnees.bin'), 'rb').read()
lj = sorted(glob.glob(os.path.join(G, 'traces', 'u_lu*', 'lu.txt'))); LU = D2.lu_ps2(lj)
segs = {int(v, 16) for v, n in J['donnees_copiees']}
st = collections.Counter(); ex = collections.defaultdict(list)
for a, b, o in J['regions']:
    a, b, o = int(a, 16), int(b, 16), int(o, 16)
    src = D2.octets(a, b - a)
    for i in range((-a) & 3, b - a - 3, 4):
        p = struct.unpack_from('<I', src, i)[0]; q = struct.unpack_from('<I', blob, o + i)[0]
        if p == q or not D2.source(p): continue
        lo, hi = p & 0xffff, p >> 16
        k = ('impaire' if p & 1 else 'paire') + (' bas>=FE00' if lo >= 0xFE00 else '') + \
            (' cible lue' if (p & ~1) in LU or p in LU else ' cible non lue') + (' debut de segment' if p in segs else '')
        st[k] += 1
        if len(ex[k]) < 4: ex[k].append('%x:%08x' % (a + i, p))
for k, n in sorted(st.items(), key=lambda x: -x[1]): print('%6d  %-45s %s' % (n, k, ' '.join(ex[k])))
print(sum(st.values()), 'pointeurs de donnees reloges')
