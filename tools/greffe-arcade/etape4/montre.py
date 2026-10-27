#!/usr/bin/env python3
"""montre.py MOD VA [avant] [apres] : MIPS + traduction cote a cote (comme show.py du traducteur), pour ro3/ro5/ro9,
MEMMODE=cps2 (traducteur : $TRAD, defaut untranspile3)."""
import sys, os
mod = sys.argv[1]; os.environ['MODULE'] = mod; os.environ.setdefault('MEMMODE', 'cps2')
TR = os.environ.get('TRAD', '<workspace>/work/greffe_arcade/untranspile3'); sys.path.insert(0, TR)
import profils
from mips import decode
import translate as T
buf = open(os.path.join(profils.EXTRACT, profils.PROFILS[mod]['fichier']), 'rb').read()
T.set_module_bounds(buf); T.RAM_HI = T.ram_hi_of(buf)
va = int(sys.argv[2], 16); bef = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x40; aft = int(sys.argv[4], 16) if len(sys.argv) > 4 else 0x30
out, _ = T.translate(buf, va - bef - 0x200, va + aft + 0x100)
em = {}
for a, t, ws in out: em.setdefault(a, []).append(t + '  ' + ' '.join('%04x' % w for w in ws))
def nm(x):
    s = str(x)
    for off, n in ((0x1150, 'RES'), (0x1158, 'C')): s = s.replace('%d(' % off, n + '(')
    for k in range(7): s = s.replace('%d(' % (0x1100 + 4 * k), 'A%d(' % k)
    for k in range(8): s = s.replace('%d(' % (0x1124 + 4 * k), 'D%d(' % k)
    return s
for x in decode(buf, va - bef, va + aft):
    if (x.m == 'lui' and x.imm == 0x7000) or (x.m == 'sll' and x.w == 0): continue
    print("%07x%s %-28s %s" % (x.va, '*' if x.va == va else ' ', nm(x), ' | '.join(em.get(x.va, []))))
