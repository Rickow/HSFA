#!/usr/bin/env python3
"""(agent_integration_max) compare les palettes AFFICHÉES de deux vidages de lua/pal_fin.lua (base = mot $20(A5)) :
régions OBJ +$000-$3FF, scroll1 +$400-$7FF, scroll2 +$800-$BFF, scroll3 +$C00-$FFF (palettes de 32 o).
Usage : compare_pal.py A.bin B.bin"""
import sys, struct
def charge(f):
    d = open(f, "rb").read(); return struct.unpack_from(">H", d, 0)[0], d[2:2 + 0x1800]
(ba, A), (bb, B) = charge(sys.argv[1]), charge(sys.argv[2])
print("base affichée A $%04x, B $%04x" % (ba, bb))
for nom, a, b in (("OBJ", 0, 0x400), ("scroll1", 0x400, 0x800), ("scroll2", 0x800, 0xC00), ("scroll3", 0xC00, 0x1000)):
    diff = [k for k in range((b - a) // 32) if A[a + 32 * k:a + 32 * k + 32] != B[a + 32 * k:a + 32 * k + 32]]
    print("%-8s : %2d / 32 palettes différentes %s" % (nom, len(diff), diff[:16]))
