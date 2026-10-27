#!/usr/bin/env python3
"""Deux generations du recompilateur (HANDOFF §52) : forme 'ancienne' des comparaisons (slt/sltu puis beq/bne,
RES = resultat) contre forme 'recente' (drapeaux complets : nor + masques 0x8000/0x80 du bit de signe).
Compte par module et par routine : part du code (taille) dont la majorite des comparaisons est recente."""
import os, collections
os.environ.setdefault("GRAIN", "routine")
import commun as C
def style(mod):
    tot = collections.Counter(); size = collections.Counter()
    for a, b in C.funcs(mod):
        L = C.seg(mod, a, b)
        if C.is_native(L)[0]: continue
        anc = sum(1 for i in range(len(L)-2) if L[i].m in ('slt', 'sltu') and any(y.m in ('beq', 'bne') for y in L[i+1:i+3]))
        rec = sum(1 for x in L if x.m == 'nor')
        tot['slt+beq'] += anc; tot['nor'] += rec
        k = 'sans comparaison' if anc + rec == 0 else ('recente' if rec > anc else 'ancienne')
        size[k] += b - a
    return tot, size
if __name__ == "__main__":
    for m in ('ro1','ro2','ro3','ro4','ro5','ro6','ro7','ro8','ro9'):
        t, s = style(m); T = sum(s.values())
        print("%s : slt+beq %6d   nor %6d   | code (taille) majoritairement : recent %4.1f %%, ancien %4.1f %%, sans comparaison %4.1f %%" % (
            m, t['slt+beq'], t['nor'], 100*s['recente']/T, 100*s['ancienne']/T, 100*s['sans comparaison']/T))
