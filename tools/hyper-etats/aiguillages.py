#!/usr/bin/env python3
"""aiguillages.py : aiguillages (JMP/JSR T_xxx(PC,Dn)) sur les variables de scene A5+0/4/8/C/10 et sur $4/$5(A6)
de la carte_image.txt de ro9 ; table videe dans le module (longs = adresses exec), adresses en fichier (exec - 0x1F0000)"""
import re, struct, sys
C = "<workspace>/work/mame_ro9/carte_image.txt"
b = open("<workspace>/anthology_extract/decompressed/ro9_usa_prog68k.bin", "rb").read()
L = [l.rstrip("\n").split(" ", 2) for l in open(C)]
motif = re.compile(sys.argv[1] if len(sys.argv) > 1 else r"MOVE\.[WB] (\(A5\)|\$000[048c]\(A5\)|\$0010\(A5\)),D[01]$")
for i, (a, va, mn) in enumerate(L):
    if not motif.search(mn): continue
    for j in range(i + 1, min(i + 6, len(L))):
        m = re.search(r"(JMP|JSR) T_([0-9a-f]+)\(PC,D\d\.W\).*table de (\d+)", L[j][2])
        if m:
            t = int(m.group(2), 16); n = int(m.group(3))
            ent = []
            for k in range(n):
                v = struct.unpack_from("<I", b, t - 0x1F0000 + 4 * k)[0]
                ent.append("%x:%s" % (2 * k, ("%06x" % (v - 0x1F0000)) if 0x1F0000 <= v < 0xB67200 else "-"))
            print("68k %s mips %s  %-22s T_%x  %s" % (a, va, mn.split(",")[0].replace("MOVE.", ""), t, " ".join(ent)))
            break
