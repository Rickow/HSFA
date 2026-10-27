#!/usr/bin/env python3
"""resume.py log.txt : par action, coups (baisses de vie de J2), jauge consommée, objets vus (type, $3, $72), durée de vie."""
import sys
acts = []; F = {}; O = {}
for l in open(sys.argv[1]):
    t = l.split()
    if t[0] == 'A': acts.append((int(t[1]), t[2] + '+' + t[3]))
    elif t[0] == 'F':
        r = int(t[1]); F[r] = (int(t[-3].split('=')[1], 16), int(t[7].split('=')[1], 16), t[3], t[-2])
    elif t[0] == 'O':
        O.setdefault(int(t[1]), []).append((t[2], [int(x, 16) for x in t[3:]]))
fin = max(F) if F else 0
for i, (r0, nom) in enumerate(acts):
    r1 = acts[i + 1][0] if i + 1 < len(acts) else fin
    coups = []; prev = None; objs = {}; cmax = 0
    for r in range(r0, r1):
        if r not in F: continue
        v = F[r][0]; cmax = max(cmax, int(F[r][3].split('=')[1].split('/')[1], 16))
        if prev is not None and v < prev: coups.append((r - r0, prev - v))
        prev = v if r % 150 else None
        for a, ws in O.get(r, []):
            objs.setdefault(a, [r, r, ws[1]])[1] = r
    print('%-10s r=%d  coups=%d combo_max_J2=%d %s' % (nom, r0, len(coups), cmax, coups[:12]))
    for a, (d, f, w2) in objs.items(): print('     objet %s de r+%d a r+%d (mot $2=%04x)' % (a, d - r0, f - r0, w2))
