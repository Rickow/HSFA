#!/usr/bin/env python3
"""ctx.py -- graft review: show the context (16-bit words, PS2 order) of a cell of Upper's data, with the cells the
graft relocates marked "*".

Usage:  python3 -I ctx.py ADR [before] [after]     (PS2 execution address of Upper, hex; before / after in hex, $20)
Inputs: module ro5 ($HSFA_MODULES), classe.tsv of classe_relogements.py ($HSFA_REVIEW_OUT, default ./sorties).
Read only. See paths.py.
"""
import sys, struct, os
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
b5 = paths.module("ro5"); BASE = paths.BASE
rel = {}
for l in open(paths.sortie("classe.tsv"), encoding="utf-8"):
    p = l.rstrip('\n').split('\t')
    if p[1] == 'RELOGE': rel[int(p[0], 16)] = p
a = int(sys.argv[1], 16); av = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x20; ap = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x20
for x in range((a - av) & ~15, a + ap, 16):
    ws = struct.unpack_from('<8H', b5, x - BASE)
    s = ''
    for k, w in enumerate(ws):
        c = (x + 2 * k) & ~3
        s += ' %04x%s' % (w, '*' if c in rel else ' ')
    print('%06x:%s' % (x, s))
