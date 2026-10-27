#!/usr/bin/env python3
"""Fonctions natives (C du portage) de chaque module (liste d'essai_<mod>.txt, critere natmiss/native_at) :
taille, appels a l'executable, homologue dans ro3 (signature MIPS identique, sinon Jaccard des appels moteur)."""
import sys, re, collections
sys.path.insert(0, '.')
import commun as C
from modcompare import sig
ROLES3 = {0x381410: 'couche manette', 0x381770: 'manette', 0x381900: 'remappage/directions', 0x393b20: 'attente d\'image',
          0x383c90: 'tache OPTION / libelle menu', 0x392fd0: 'libelle (R)', 0x38a4b0: 'BTST rendu', 0x383700: 'chargeur anim (site)',
          0x3837d0: 'chargeur anim (perso)', 0x39303c: 'pilote son : boite QSound', 0x393624: 'pilote son : commandes'}
def natives(mod):
    if mod == 'ro3':
        import json; return [int(x, 16) for x in json.load(open('<workspace>/work/carto_ro9/natives_ro3.json'))]
    t = open('essai_%s.txt' % mod).read()
    return [int(x, 16) for x in re.search(r'natives : (.*)', t).group(1).split()]
def fin(mod, a):
    for x in C.seg(mod, a, a + 0x8000):
        if x.m == 'jr' and x.rs == 31: return x.va + 8
    return a + 0x100
def ext(mod, a, b):
    e = C.header(mod)['code_end']
    return [x.tgt for x in C.seg(mod, a, b) if x.m in ('jal', 'j') and not (0x1F0000 <= x.tgt < 0x1F0000 + e)]
R3 = {}
for a in natives('ro3'):
    b = fin('ro3', a); s = C.seg('ro3', a, b); R3[a] = (sig(s, a, b, False)[0], set(ext('ro3', a, b)), b - a)
idx = {v[0]: a for a, v in R3.items()}
for m in sys.argv[1:] or ['ro1','ro2','ro4','ro6','ro7','ro8']:
    print('=== %s : %d natives' % (m, len(natives(m))))
    for a in natives(m):
        b = fin(m, a); s = C.seg(m, a, b); sg = sig(s, a, b, False)[0]; E = set(ext(m, a, b))
        if sg in idx: h = 'identique a ro3 %x' % idx[sg]; h3 = idx[sg]
        else:
            best = max(((len(E & v[1]) / len(E | v[1]) if E | v[1] else 0, k) for k, v in R3.items()), default=(0, None))
            h3 = best[1] if best[0] > 0.3 else None
            h = ('appels moteur ~ ro3 %x (J=%.2f)' % (best[1], best[0])) if h3 else '-'
        print('  %x (exec %x) %5d o  moteur %-40s %s %s' % (a, a + 0x1F0000, b - a, ','.join('%x' % t for t in sorted(E))[:40], h,
              ('[' + ROLES3[h3] + ']') if h3 in ROLES3 else ''))
