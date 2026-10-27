#!/usr/bin/env python3
"""biblio.py : bibliotheques de blocs de decor (s1 128 o, super-tuiles 64 o, s2 768 o, s3 192 o) d'Upper et d'Hyper
(adresses d'exec. des LEA, homologues par routine identique) : nombre d'elements et presence des blocs d'Upper dans Hyper."""
import os
DIR = "<workspace>/anthology_extract/decompressed"; BASE = 0x1F0000
B = {m: open(os.path.join(DIR, "%s_usa_prog68k.bin" % m), "rb").read() for m in ("ro3", "ro5", "ro9")}
# (nom, Upper, fin Upper, Hyper, fin Hyper, taille element) ; fins = adresse de la bibliotheque suivante
L = [("blocs scroll1", 0x69B830, 0x69F3B0, 0x63DA20, 0x63DD20, 128),
     ("super-tuiles", 0x69F3B0, 0x6CF5F0, 0x63DD20, 0x640960, 64),
     ("blocs scroll2", 0x6CF5F0, 0x6EF3F0, 0x640960, 0x643C60, 768),
     ("blocs scroll3", 0x6EF3F0, None, 0x643C60, None, 192)]
for nom, a5, f5, a9, f9, sz in L:
    if f5 is None:   # fin = premier zero-long-run ou table suivante : borne prudente 256 blocs
        f5 = a5 + 256 * sz; f9 = a9 + 256 * sz
    n5 = (f5 - a5) // sz; n9 = (f9 - a9) // sz
    s9 = {B["ro9"][a9 - BASE + k*sz: a9 - BASE + (k+1)*sz] for k in range(n9)}
    hit = sum(1 for k in range(n5) if B["ro5"][a5 - BASE + k*sz: a5 - BASE + (k+1)*sz] in s9)
    anyw = sum(1 for k in range(min(n5, 400)) if B["ro9"].find(B["ro5"][a5 - BASE + k*sz: a5 - BASE + (k+1)*sz]) >= 0)
    print("%-14s Upper %x (%d el.) | Hyper %x (%d el.) | blocs d'Upper dans la bibliotheque d'Hyper : %d ; ailleurs dans ro9 : %d/%d"
          % (nom, a5, n5, a9, n9, hit, anyw, min(n5, 400)))
