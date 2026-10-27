#!/usr/bin/env python3
"""Chaines ASCII des donnees lues en mots 16 bits ECHANGES (rangement 68K des modules : octets permutes 2 a 2)
-> chaines_ech_<mod>.txt (decalage fichier / exec du debut)."""
import re, sys
sys.path.insert(0, '.')
import commun as C
for m in sys.argv[1:] or ['ro1','ro2','ro3','ro4','ro5','ro6','ro7','ro8','ro9']:
    b = bytearray(C.load(m)); b[0::2], b[1::2] = b[1::2], b[0::2]
    with open('chaines_ech_%s.txt' % m, 'w') as f:
        for mo in re.finditer(rb'[\x20-\x7e]{5,}', bytes(b)):
            f.write('%07x %07x %s\n' % (mo.start(), mo.start() + 0x1F0000, mo.group().decode()))
