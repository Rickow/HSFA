#!/usr/bin/env python3
"""reloc_perdues.py A B [lo-hi ...] : longs alignes des regions copiees modifies (reloges) dans la construction A et
laisses bruts dans B (adresses PS2 d'Upper), dans les plages donnees."""
import json, sys, struct, os
G = '<workspace>/work/greffe_arcade/constructions/'
U = open(os.environ.get('HSFA_RO5', '<workspace>/work/modules_son/ro5_usa_prog68k.bin'), 'rb').read()
def charge(c):
    J = json.load(open(G + c + '/greffe.json')); B = open(G + c + '/greffe_donnees.bin', 'rb').read()
    return [(int(a, 16), int(b, 16), int(o, 16)) for a, b, o in J['regions']], B
def val(R, B, a):
    for lo, hi, o in R:
        if lo <= a < hi and a + 4 <= hi: return struct.unpack_from('<I', B, o + a - lo)[0]
    return None
RA, BA = charge(sys.argv[1]); RB, BB = charge(sys.argv[2])
pl = [tuple(int(x, 16) for x in s.split('-')) for s in sys.argv[3:]] or [(0, 1 << 32)]
for lo, hi, o in RA:
    for a in range(lo + ((-lo) & 3), hi - 3, 4):
        if not any(p <= a < q for p, q in pl): continue
        u = struct.unpack_from('<I', U, a - 0x1F0000)[0]
        va = val(RA, BA, a); vb = val(RB, BB, a)
        if va != u and vb == u: print('%x brut %08x A %08x B %08x' % (a, u, va, vb))
