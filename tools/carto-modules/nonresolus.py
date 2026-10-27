#!/usr/bin/env python3
"""Detail des non resolus d'essai_mod.py : entrees de tables de sauts et branchements dont la cible sort de la zone
assemblee (autre zone 68K, Z80, natif...). Usage : nonresolus.py roN"""
import os, sys
sys.argv.append('x'); mod = sys.argv[1]
exec(open('essai_mod.py').read().split("t0 = time.time()")[0])
for a0, a1 in Z['m68k']:
    if a1 - a0 < 0x1000: continue
    e1 = T.code_end_translate(buf) if a1 == end else a1
    T.TABLES.clear()
    its, words, unres = assemble(buf, a0, e1, base=0x1000, external=lambda t: 0x800, native=NAT)
    out = []
    for tb, ents in T.TABLES.items():
        for e in ents:
            if e and not (a0 <= e - 0x1F0000 < e1): out.append(('table %x' % tb, e - 0x1F0000))
    for it in its:
        if it.kind == 'bcc' and it.tgt is not None and not (a0 <= it.tgt < e1): out.append(('bcc %x' % it.va, it.tgt))
    print(mod, 'zone %x-%x non resolus %d :' % (a0, e1, unres), ' ; '.join('%s -> %x' % o for o in out[:20]))
