#!/usr/bin/env python3
"""Cherche, dans les donnees de chaque module, les tables u16 (ou u32) qui contiennent la plupart des entrees
X_DATA d'un ensemble (banques de persos d'un groupe) dans une fenetre courte -> table 'perso -> banque' du module."""
import sys, struct
sys.path.insert(0, '.')
import commun as C
ENS = {'SFA1 e208-e220': set(range(208, 221)), 'SFA2 e229-e248': set(range(229, 249)), 'SFA3 e258-e285': set(range(258, 286)),
       'SFA3 MOMO e314-e344': set(range(314, 345)), 'Upper e355-e386': set(range(355, 387)), 'ro6 e527-e535': set(range(527, 536)),
       'ro7 e537-e542': set(range(537, 543))}
for m in sys.argv[1:] or ['ro1','ro2','ro3','ro4','ro5','ro6','ro7','ro8','ro9']:
    d = C.load(m); e = C.header(m)['code_end'] + 0x40
    for nom, S in ENS.items():
        for sz, fmt in ((2, '<H'), (4, '<I')):
            W = 2 * len(S) + 8; best = []
            vals = [struct.unpack_from(fmt, d, o)[0] for o in range(e, len(d) - sz + 1, sz)]
            o = 0
            while o < len(vals) - W:
                win = vals[o:o + W]; hit = S & set(win)
                if len(hit) >= max(5, int(0.6 * len(S))):
                    # bornes de la table : premiere/derniere valeur de S dans la fenetre
                    i0 = next(i for i, v in enumerate(win) if v in S)
                    best.append((e + (o + i0) * sz, len(hit), win[i0:i0 + len(S) + 6]))
                    o += W
                else: o += 1
            for a, n, w in best[:6]:
                print('%s %-20s u%d exec %#x (fichier %#x) : %d/%d -> %s' % (m, nom, 8 * sz, a + 0x1F0000, a, n, len(S), ' '.join(str(v) for v in w)))
