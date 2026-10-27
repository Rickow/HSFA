#!/usr/bin/env python3
"""(palettes MAX) compare le releve de verif_palettes.lua (palettes d'objets 0-9 en combat) au groupe
attendu : groupe = ((ism + 1) x 2 + couleur) x 5 dans le bloc de palettes de l'ID (table fichier 0x451230), ou dans
palettes_module.bin du perso MAX pour J1 (--j1 plNN). Le moteur pose la luminosite F et garde le mot 15 (numero).
Usage : compare_palettes.py sorties/<nom>.pal [--j1 pl26]"""
import sys, struct, re, os
buf = open("<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin", "rb").read()
TPAL = 0x451230
tab = struct.unpack_from('<32H', buf, TPAL)
max_j1 = sys.argv[sys.argv.index("--j1") + 1] if "--j1" in sys.argv else None
def bloc(pid, j):
    if j == 1 and max_j1:
        return open(os.path.expanduser("~/.cache/sfa3max/converti/%s/palettes_module.bin" % max_j1), "rb").read()
    return buf[TPAL + tab[pid]:TPAL + tab[pid] + 0x3C0]
L = open(sys.argv[1]).read().split("\n")
ok = ko = 0
for i in range(0, len(L) - 1, 2):
    m = re.match(r"K (\d+) J1 id=(\w+) ism=(\w+) col=(\w+) J2 id=(\w+) ism=(\w+) col=(\w+)", L[i])
    if not m: continue
    k = int(m.group(1)); P = [int(w, 16) for w in L[i + 1].split()[1:]]
    res = []
    for j, (pid, ism, col) in ((1, m.group(2, 3, 4)), (2, m.group(5, 6, 7))):
        pid, ism, col = int(pid, 16), struct.unpack('b', bytes([int(ism, 16)]))[0], int(col, 16)
        g = ((ism + 1) * 2 + col) * 5
        b = bloc(pid, j)
        att = [0xF000 | struct.unpack_from('<H', b, 32 * (g + p) + 2 * w)[0] for p in range(5) for w in range(16)]
        lu = P[80 * (j - 1):80 * j]
        bon = sum(1 for a, v in zip(att, lu) if a == v)
        res.append("J%d id=%x groupe %2d : %2d/80" % (j, pid, g, bon))
        if bon == 80: ok += 1
        else: ko += 1
    print("image %5d  %s" % (k, "   ".join(res)))
print("releves conformes : %d, non conformes : %d" % (ok, ko))
