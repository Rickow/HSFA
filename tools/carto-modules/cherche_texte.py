#!/usr/bin/env python3
"""Cherche un mot (ex. TRAINING) sous des codages simples : octet = car + k, ou mot 16 bits (octet bas = car + k ou
car|0x80, octet haut quelconque mais constant), dans les deux ordres d'octets. Usage : cherche_texte.py mod MOT..."""
import sys, re, struct
sys.path.insert(0, '.')
import commun as C
m = sys.argv[1]; d = C.load(m)
for mot in sys.argv[2:]:
    res = []
    for k in range(-0x40, 0xa0):
        pat = bytes(((ord(c) + k) & 0xff) for c in mot)
        for mo in re.finditer(re.escape(pat), d): res.append(('octet k=%+d' % k, mo.start()))
    # mots 16 bits : octet bas = code, octet haut constant
    for k in range(-0x40, 0xa0):
        codes = [((ord(c) + k) & 0xff) for c in mot]
        rx = b''.join(re.escape(bytes([c])) + b'(.)' if True else b'' for c in codes)
        for mo in re.finditer(rx, d, re.S):
            hs = set(mo.groups())
            if len(hs) == 1 and mo.start() % 2 == 0: res.append(('mot LE k=%+d haut=%02x' % (k, mo.group(1)[0]), mo.start()))
        rx = b''.join(b'(.)' + re.escape(bytes([c])) for c in codes)
        for mo in re.finditer(rx, d, re.S):
            hs = set(mo.groups())
            if len(hs) == 1 and mo.start() % 2 == 0: res.append(('mot BE k=%+d haut=%02x' % (k, mo.group(1)[0]), mo.start()))
    print(m, mot, len(res), ' '.join('%s@%x' % (a, o) for a, o in res[:12]))
