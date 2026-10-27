#!/usr/bin/env python3
"""(etape B) RESUME DE CADENCE d'un releve runs/cadence.lua (charge avant commandes.lua) : cadence.py cad1.txt [cad2.txt...]
Par iteration de la boucle de jeu (tours « T » jusqu'a la fin de liste d'objets « F ») : nombre de tours et ligne de la fin
de liste comptee depuis le debut de l'image ou l'iteration commence (> 262 : la liste deborde sur l'image suivante).
« sans tour » = images ou le jeu n'a fait aucun tour (image perdue) ; « listes/image » = 1,0 a l'arcade."""
import sys, statistics as st, collections
for p in sys.argv[1:]:
    rows = []
    for l in open(p):
        k, _, *ev = l.split(); rows.append([(e[0], int(e[1:])) for e in ev])
    flat = sorted((i * 262 + v, t) for i, ev in enumerate(rows) for t, v in ev if t in 'TF')
    it = []; cur = None
    for a, t in flat:
        if t == 'T':
            if cur is None: cur = [a, 0]
            cur[1] += 1
        elif t == 'F' and cur is not None:
            it.append((cur[1], a - (cur[0] - cur[0] % 262))); cur = None
    by = collections.defaultdict(list)
    for n, f in it: by[n].append(f)
    z = sum(1 for ev in rows if not any(t == 'T' for t, v in ev)); nl = sum(1 for ev in rows for t, v in ev if t == 'F')
    nt = sum(1 for ev in rows for t, v in ev if t == 'T')
    print('%s : %d images, %d tours (%.1f %%), sans tour %d, listes/image %.3f ; ' % (p.split('/')[-1], len(rows), nt,
          100.0 * nt / len(rows), z, nl / len(rows)) + ' ; '.join('%d tour(s) : %d iterations, fin de liste mediane ligne %d (max %d)'
          % (n, len(v), st.median(v), max(v)) for n, v in sorted(by.items())))
