#!/usr/bin/env python3
"""voir68.py VA [FIN|+LONG] : traduction 68K seule (une ligne par instruction emise) d'une plage MIPS.
MODULE=ro5|ro9 MEMMODE=cps2 (comme show.py). VA en hexa, decalage fichier."""
import sys, os
UT = "<workspace>/scripts/untranspile"; sys.path.insert(0, UT)
import census, translate as T
buf = open(census.RO3, 'rb').read()
va = int(sys.argv[1], 16)
if len(sys.argv) > 2:
    s = sys.argv[2]; fin = va + int(s[1:], 16) if s.startswith('+') else int(s, 16)
else:
    fin = va + 0x400
out, _ = T.translate(buf, va - 0x200, fin + 0x100)
for a, t, ws in out:
    if va <= a < fin: print("%07x  %s" % (a, t))
