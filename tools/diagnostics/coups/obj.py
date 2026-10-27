#!/usr/bin/env python3
"""obj.py log.txt ref|tr [champs hex...] : résumé par image des objets projectiles + vie J2 / état."""
import sys
f, mode = sys.argv[1], sys.argv[2]
champs = [int(x, 16) for x in sys.argv[3:]] or [0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x33, 0x35, 0x3b, 0x72, 0xdc]
def b(ws, off):
    if mode == 'tr': off ^= 1
    w = ws[off // 2]
    return (w >> 8) if off % 2 == 0 else (w & 0xff)
vie = None
for l in open(f):
    t = l.split()
    if t[0] == 'F':
        v = int(t[-3].split('=')[1], 16)
        if vie is not None and v < vie: print('  r=%s  J2 vie %x -> %x  (J2 %s, J1 %s jauge %s)' % (t[1], vie, v, t[8], t[3], t[7] + ' ' + t[-2]))
        vie = v
    elif t[0] == 'O':
        ws = [int(x, 16) for x in t[3:]]
        print('O r=%s %s ' % (t[1], t[2]) + ' '.join('%x=%02x' % (c, b(ws, c)) for c in champs))
    elif t[0] in ('A', 'T0'): print(l.rstrip())
