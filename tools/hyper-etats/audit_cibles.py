#!/usr/bin/env python3
"""audit_cibles.py : appels/sauts absolus (JSR/JMP abs.L) de l'image 68K de ro9 dont la cible MIPS (annotation de
carte_image.txt) n'a pas de ligne de carte : l'assembleur les a resolus vers une AUTRE adresse (premiere ligne suivante).
Sortie : site 68K, va MIPS du site, cible MIPS voulue, adresse 68K obtenue et va MIPS reelle de cette adresse."""
import re, os, collections
W = "<workspace>/work/mame_ro9"
names = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]
sw = b"".join(open(os.path.join(W, "roms_ro9/sfa3ud", n), "rb").read() for n in names)
img = bytes(x for i in range(0, len(sw), 2) for x in (sw[i + 1], sw[i]))
rows = [l.rstrip("\n").split(" ", 2) for l in open(os.path.join(W, "carte_image.txt"))]
va_de = {}; par_va = collections.defaultdict(list)
for a, va, mn in rows: va_de.setdefault(int(a, 16), int(va, 16)); par_va[int(va, 16)].append(int(a, 16))
n = 0; mauvais = collections.Counter(); ex = {}
for a, va, mn in rows:
    m = re.search(r"(JMP|JSR) \?\?\?  \[cible ([0-9a-f]+) -> fichier ([0-9a-f]+)", mn)
    if not m: continue
    a = int(a, 16); f = int(m.group(3), 16)
    if not (0x22de0 <= f < 0x3bf180): continue
    op = int.from_bytes(img[a:a + 2], "big")
    if op not in (0x4eb9, 0x4ef9): continue
    t = int.from_bytes(img[a + 2:a + 6], "big")
    n += 1
    if f in par_va: continue
    mauvais[f] += 1; ex.setdefault(f, (a, int(va, 16), t, va_de.get(t)))
print("sauts/appels absolus vers le code du module : %d ; cibles sans ligne de carte : %d (%d sites)" % (n, len(mauvais), sum(mauvais.values())))
for f, c in sorted(mauvais.items()):
    a, va, t, vt = ex[f]
    print("cible mips %06x : %3d site(s), ex. 68k %06x (mips %06x) -> $%06x = mips %s" % (f, c, a, va, t, "%06x" % vt if vt is not None else "?"))

# (2) instructions MIPS sautees entre la cible voulue et la ligne obtenue, hors prologue (pile, cases registre)
import sys
sys.path.insert(0, "<workspace>/work/agent_ro9/untranspile")
from mips import decode
buf = open("<workspace>/anthology_extract/decompressed/ro9_usa_prog68k.bin", "rb").read()
print("\n== cibles dont l'intervalle saute du code utile ==")
for f, c in sorted(mauvais.items()):
    a, va, t, vt = ex[f]
    if vt is None or vt < f: continue
    utiles = []
    for x in decode(buf, f, vt):
        s = repr(x)
        if x.w == 0 or re.match(r"(addiu sp,sp|sd ra|ld ra|sq |lq |sd s|ld s)", s) or re.search(r"\(sp\)|,sp,|lui \w+,0x7000|4372\(", s): continue
        utiles.append("%06x %s" % (x.va, s))
    if len(utiles) >= 3:
        print("cible %06x -> %06x : %d instr. utiles sautees, %d site(s) ; ex. %s" % (f, vt, len(utiles), c, " | ".join(utiles[:4])))
