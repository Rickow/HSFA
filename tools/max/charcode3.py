"""Tentative intermédiaire : routines accrochées aux DONNÉES de chaque perso.
Résultat : ~1 racine par perso (le reste passe par des tables internes). Remplacé par modules.py."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

import bisect, collections, json
from charcode2 import P, PA, W, NW, S, fstart, fend, jal, tables, data_span, TEXT_END
# graphe d'appels (jal) : appelant -> appelés, et appelés -> appelants
callees, callers = collections.defaultdict(set), collections.defaultdict(set)
for k, w in enumerate(W):
    if w >> 26 == 3:
        t = jal(w)
        if 0 <= t < TEXT_END:
            f = fstart(k*4); callees[f].add(t); callers[t].add(f)
# fonctions aussi référencées depuis des données quelconques (pointeurs) : ne sont pas « appelées seulement par jal »
data_ref = collections.Counter(t for t in P.values() if t < TEXT_END)
def handlers(c):
    """routines accrochées aux données du perso c (on ne suit que les données)."""
    seen_d, out, todo = set(), set(), [P[t[c]] for t in tables]
    while todo:
        a = todo.pop()
        if a < TEXT_END: out.add(fstart(a)); continue
        if a in seen_d: continue
        seen_d.add(a)
        lo = bisect.bisect_left(PA, a); hi = data_span(a)
        while lo < len(PA) and PA[lo] < hi: todo.append(P[PA[lo]]); lo += 1
    return out
H = {c: handlers(c) for c in range(42)}
owner = collections.defaultdict(set)
for c, hs in H.items():
    for f in hs: owner[f].add(c)
def private_code(c):
    own = {f for f in H[c] if owner[f] == {c}}
    changed = True
    while changed:                       # appelés dont TOUS les appelants sont privés, jamais pointés ailleurs
        changed = False
        for f in list(own):
            for t in callees[f]:
                if t not in own and callers[t] and callers[t] <= own and t not in owner:
                    own.add(t); changed = True
    return own
if __name__ == "__main__":
    names = json.load(open(paths.MAPPING))
    size = lambda fs: sum(fend(f) - f for f in fs)
    print(f"routines accrochées aux persos (toutes) : {len(owner)}")
    res = {}
    for c in range(42):
        pc = private_code(c); res[c] = pc
        tag = " <== MAX" if c >= 0x26 else (" <== Upper" if 0x20 <= c <= 0x24 else "")
        print(f"  {c:#04x} {names[f'{c:02x}']:<13} accrochées {len(H[c]):4} | privées {len(pc):4} fonctions ~{size(pc)/1024:6.1f} Ko{tag}")
    tot = set().union(*(res[c] for c in (0x26, 0x27, 0x28, 0x29)))
    print(f"=> code privé des 4 persos MAX : {len(tot)} fonctions, ~{size(tot)/1024:.0f} Ko de MIPS")
