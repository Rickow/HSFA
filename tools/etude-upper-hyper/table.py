#!/usr/bin/env python3
"""table.py MOD EXEC N [l|w|b] : vide N elements d'une table de donnees (adresse d'execution = fichier + 0x1F0000)."""
import sys, struct
mod, ex, n = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3])
t = sys.argv[4] if len(sys.argv) > 4 else 'l'
b = open("<workspace>/anthology_extract/decompressed/%s_usa_prog68k.bin" % mod, 'rb').read()
o = ex - 0x1F0000; sz = {'l': 4, 'w': 2, 'b': 1}[t]; f = {'l': '<I', 'w': '<h', 'b': '<B'}[t]
v = [struct.unpack_from(f, b, o + k * sz)[0] for k in range(n)]
if t == 'l': print(' '.join("%x" % x for x in v)); print(' '.join("(f %x)" % (x - 0x1F0000) for x in v))
else: print(' '.join("%x" % (x & 0xffff if t == 'w' else x) for x in v))
