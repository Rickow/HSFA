#!/usr/bin/env python3
"""Outils d'atteignabilite sur graphe_<mod>.pkl."""
import os, pickle, bisect, functools
OUT = os.path.dirname(os.path.abspath(__file__))

@functools.lru_cache(None)
def G(mod): return pickle.load(open(os.path.join(OUT, "graphe_%s.pkl" % mod), "rb"))

def fstart(mod, va):
    st = [a for a, _ in G(mod)['funcs']]
    k = bisect.bisect_right(st, va) - 1
    return st[k]

@functools.lru_cache(None)
def taille(mod):
    return {a: b - a for a, b in G(mod)['funcs']}

def reach(mod, roots, bloque=(), cle='succ'):
    g = G(mod)[cle]; bl = set(bloque); seen = set(); pile = [fstart(mod, r) for r in roots]
    while pile:
        a = pile.pop()
        if a in seen or a in bl: continue
        seen.add(a); pile.extend(g.get(a, ()))
    return seen

def preds(mod):
    p = {}
    for a, s in G(mod)['succ'].items():
        for t in s: p.setdefault(t, set()).add(a)
    return p
