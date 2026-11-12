#!/usr/bin/env python3
"""MONTRE UN MANQUE (HANDOFF §78) : MIPS autour d'une adresse et traduction emise pour la meme plage.
Usage : showmiss.py va_hex [avant=0x40] [apres=0x10]"""
import sys, os
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
os.environ.setdefault("MEMMODE", "cps2")
import census, translate as T
from mips import decode
buf = open(census.RO3, "rb").read(); T.set_module_bounds(buf)
va = int(sys.argv[1], 16); av = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x40
ap = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x10
lo, hi = va - av, va + ap
out, _ = T.translate(buf, lo - 0x100, hi)
em = {}
for a, t, w in out:
    if lo <= a < hi: em.setdefault(a, []).append((t, w))
for x in decode(buf, lo, hi):
    if x.m == 'lui' and x.imm == 0x7000: continue
    mark = '>>' if x.va == va else '  '
    print("%s %07x %-6s rs=%2d rt=%2d rd=%2s imm=%04x   %s" % (mark, x.va, x.m, x.rs, x.rt, getattr(x, 'rd', ''), x.simm & 0xffff,
          " | ".join(t[:70] for t, w in em.get(x.va, []) if w)))
