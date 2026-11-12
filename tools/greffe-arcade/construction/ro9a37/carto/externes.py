#!/usr/bin/env python3
"""Empreinte par APPELS AU MOTEUR PS2 (cibles de jal hors module : l'executable est commun a tous les modules,
donc ces adresses sont stables d'un module a l'autre) -> homologues des fonctions natives / du portage."""
import collections, functools, sys
import commun as C

@functools.lru_cache(None)
def ext_sets(mod):
    e = C.header(mod)['code_end']; out = {}
    for a, b in C.funcs(mod):
        s = [x.tgt for x in C.seg(mod, a, b) if x.m == 'jal' and not (C.BASE <= x.tgt < C.BASE + e)]
        if s: out[a] = s
    return out

def match(src, va, dst, n=5):
    f = C.func_of(src, va)[0]
    E = ext_sets(src).get(f, [])
    S = set(E); res = []
    for a, L in ext_sets(dst).items():
        T = set(L)
        j = len(S & T) / len(S | T) if S | T else 0
        if j > 0: res.append((j, -abs(len(L) - len(E)), a, L))
    res.sort(reverse=True)
    return f, E, res[:n]

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    for x in sys.argv[3:]:
        f, E, r = match(src, int(x, 16), dst)
        print("%s fn %x : appels moteur %s" % (src, f, [hex(t) for t in E]))
        for j, _, a, L in r: print("    %s %x  J=%.2f  %s" % (dst, a, j, [hex(t) for t in L][:12]))
