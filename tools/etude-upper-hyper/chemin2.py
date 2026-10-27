#!/usr/bin/env python3
"""chemin2.py MOD DE VERS [bloques...] : plus court chemin en evitant des noeuds ; indique pour chaque arete si elle
vient d'un jal / constante code / table (et la taille de la table)."""
import sys, collections, struct
import atteint as AT
sys.path.insert(0, "<workspace>/work/carto_ro9")
mod, a, b = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16)
bl = {AT.fstart(mod, int(x, 16)) for x in sys.argv[4:]}
G = AT.G(mod); g = G['succ']; a = AT.fstart(mod, a); b = AT.fstart(mod, b)
prev = {a: None}; q = collections.deque([a])
while q:
    x = q.popleft()
    if x == b: break
    for y in g.get(x, ()):
        if y not in prev and y not in bl: prev[y] = x; q.append(y)
if b not in prev: print('pas de chemin'); sys.exit()
p = []; x = b
while x is not None: p.append(x); x = prev[x]
p.reverse()
tabs = G['tables']; data = G['data']
for u, v in zip(p, p[1:]):
    via = [hex(t) + '(%d)' % len(tabs[t]) for t in data.get(u, ()) if any(AT.fstart(mod, e) == v for e in tabs.get(t, []))]
    print("%x -> %x  %s" % (u, v, ' '.join(via) if via else 'appel/constante'))
