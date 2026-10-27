#!/usr/bin/env python3
"""Exploration : tables lues par les sauts indirects JSR/JMP (An) de la carte ; valeurs, cles de code, refs."""
import sys, os, struct, re, bisect
U = "<workspace>/work/agent_reorg_B/untranspile"; sys.path.insert(0, U)
os.environ["MEMMODE"] = "cps2"
import translate as T
from mips import CODE0, decode
from profils import P, chemin
buf = open(chemin(), "rb").read(); T.set_module_bounds(buf)
end = struct.unpack_from('<I', buf, 12)[0]
Lm = list(decode(buf, CODE0, end))
keys = {x.tgt for x in Lm if x.m == 'jal' and T.RUNTIME_BASE + CODE0 <= x.tgt < T.CODE_END_RT}
def prologue(va):
    w = struct.unpack_from('<I', buf, va)[0]
    return ((w >> 16) == 0x27bd and (w & 0x8000)) or w == 0x03e00008 or (w & 0xffe0ffff) == 0x3c007000
for o in range(end, len(buf) - 3, 4):
    v = struct.unpack_from('<I', buf, o)[0]
    if T.RUNTIME_BASE + CODE0 <= v < T.CODE_END_RT and v % 4 == 0 and prologue(v - T.RUNTIME_BASE): keys.add(v)
refs = T.data_refs(buf)
carte = sys.argv[1]
rows = [l.rstrip('\n').split(' ', 2) for l in open(carte)]
srcs = set()
for i, (a, va, mn) in enumerate(rows):
    if re.match(r'(JSR|JMP) \(A[0-7]\)$', mn):
        for a2, va2, mn2 in rows[max(0, i-10):i]:
            m = re.search(r'T_([0-9a-f]{6})', mn2) if 'MOVEA.L T_' in mn2 else None
            if m: srcs.add(int(m.group(1), 16))
            m = re.search(r'LEA \$[0-9a-f]+\.L,A[0-7]  \[PS2 ([0-9a-f]+)\]', mn2)
            if m: srcs.add(int(m.group(1), 16))
for p in sorted(srcs):
    k = bisect.bisect_right(refs, p); nxt = refs[k] if k < len(refs) else None
    line = []
    for j in range(80):
        v = struct.unpack_from('<I', buf, p - T.RUNTIME_BASE + 4*j)[0]
        if nxt and p + 4*j >= nxt: line.append('|')
        line.append(('%x' % v) + ('*' if v in keys else ('0' if v == 0 else '?')))
        if v not in keys and v != 0 and j > 0 and (not nxt or p + 4*j >= nxt): break
    print('%06x ref_suivante=%s : %s' % (p, ('%06x' % nxt) if nxt else '-', ' '.join(line)))
