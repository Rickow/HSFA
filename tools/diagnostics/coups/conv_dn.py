#!/usr/bin/env python3
"""conv_dn.py carte_image.txt : constantes 'lui' seules rangees dans Dn et CONVERTIES en adresse (valeur emise != lui)."""
import sys, re, os
sys.path.insert(0, '<workspace>/work/agent_coups/untranspile')
import census
from mips import decode
buf = open(census.RO3, 'rb').read()
L = open(sys.argv[1]).read().splitlines()
for k, l in enumerate(L):
    m = re.match(r'(\w+) (\w+) MOVE\.L #\$(\w+),D(\d)$', l)
    if not m: continue
    va = int(m.group(2), 16); v = int(m.group(3), 16)
    ins = list(decode(buf, va - 0x30, va + 4))
    lu = [x for x in ins if x.m == 'lui' and x.imm != 0x7000]
    if not lu: continue
    lv = (lu[-1].imm << 16) & 0xffffffff
    if lv != v and not [x for x in ins if x.m in ('ori', 'addiu') and x.rs == lu[-1].rt and x.va > lu[-1].va]:
        print('%s  lui=$%x  emis=$%x  | %s' % (l, lv, v, ' / '.join(x.split(None, 2)[2] for x in L[k+1:k+4])))
