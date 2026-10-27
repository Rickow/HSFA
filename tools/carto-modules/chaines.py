#!/usr/bin/env python3
"""Chaines ASCII (>= 4 car.) des DONNEES de chaque module -> chaines_<mod>.txt (fichier / exec)."""
import re, sys, struct
sys.path.insert(0, '.')
import commun as C
for m in sys.argv[1:] or ['b','ro1','ro2','ro3','ro4','ro5','ro6','ro7','ro8','ro9']:
    b = C.load(m); h = C.header(m)
    base = h['base']
    with open('chaines_%s.txt' % m, 'w') as f:
        for mo in re.finditer(rb'[\x20-\x7e]{4,}', b):
            f.write('%07x %07x %s\n' % (mo.start(), mo.start() + base, mo.group().decode()))
