#!/usr/bin/env python3
"""(e25) mips_copie.py CONSTR UPPER_DEBUT UPPER_FIN : mots MIPS de la copie greffee (module ro9a) face a l'original d'Upper"""
import sys, json, struct
sys.path.insert(0, '<workspace>/scripts/untranspile'); sys.path.insert(0, '<workspace>/work/carto_ro9')
import commun as C
from mips import decode
G = '<workspace>/work/greffe_arcade'
c, a, b = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16)
J = json.load(open('%s/constructions/%s/greffe.json' % (G, c)))
mod = open('%s/constructions/%s/ro9a_module.bin' % (G, c), 'rb').read(); b5 = C.load('ro5')
for x0, x1, n in J['blocs']:
    x0, x1, n = int(x0, 16), int(x1, 16), int(n, 16)
    if x0 <= a < x1: break
else: sys.exit('hors blocs')
d = n - x0
for va in range(a, b, 4):
    w5 = struct.unpack_from('<I', b5, va)[0]; w9 = struct.unpack_from('<I', mod, va + d)[0]
    i5 = list(decode(b5, va, va + 4)); i9 = list(decode(mod, va + d, va + d + 4))
    print('%06x %06x %08x %-34s %s %08x %s' % (va, va + d, w5, str(i5[0]) if i5 else '', ' ' if w5 == w9 else '*', w9, str(i9[0]) if (i9 and w5 != w9) else ''))
