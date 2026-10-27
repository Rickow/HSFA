#!/usr/bin/env python3
"""dis.py mod debut fin : desassemblage MIPS (fichier), avec cibles de jal en fichier."""
import sys
sys.path.insert(0, '<workspace>/scripts/untranspile')
from mips import decode
m, a, b = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16)
d = open('<workspace>/anthology_extract/decompressed/%s_usa_prog68k.bin' % m, 'rb').read()
for x in decode(d, a, b): print("%06x  %s" % (x.va, repr(x)) + ("   -> fichier %x" % (x.tgt - (0x1C8000 if m == "b" else 0x1F0000)) if x.m in ("jal", "j") else ""))
