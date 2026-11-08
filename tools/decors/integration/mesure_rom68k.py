#!/usr/bin/env python3
"""mesure_rom68k.py CONSTRUCTION : occupation de la ROM programme 68K (4 Mo, sz3ud.03c … sz3.10b) d'une construction
figée de la greffe : plages non nulles et trous de zéros >= 4 Ko (une zone de zéros n'est pas forcément libre :
à croiser avec re/allocations.tsv). Écrit sur la sortie standard (TSV)."""
import os, sys
C = sys.argv[1]
d = os.path.join(C, "b9", "roms_ro9", "sfa3ud")
noms = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]
rom = b"".join(open(os.path.join(d, n), "rb").read() for n in noms)
assert len(rom) == 0x400000
G = 0x400                                  # granule
occ = [any(rom[i:i + G]) for i in range(0, len(rom), G)]
runs = []; i = 0
while i < len(occ):
    j = i
    while j < len(occ) and occ[j] == occ[i]: j += 1
    runs.append((occ[i], i * G, j * G - 1)); i = j
print("etat\tdebut\tfin\toctets")
for o, a, b in runs:
    if o or (b - a + 1) >= 0x1000:
        print("%s\t$%06X\t$%06X\t%d" % ("occupé" if o else "zéros", a, b, b - a + 1))
