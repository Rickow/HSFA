"""Anneau scroll1 en mouvement (REIMPORT §7C) : pour chaque image du releve FRMTOUT (essai_fork.lua, ALLER_RETOUR=1),
colonnes de l'anneau (tilemap 512 px) visibles dans une fenetre 448 (ecran -32..416) comparees a la carte du monde
attendue (tilemap complete du decor, 1024 px, reconstruite depuis le programme corrige + bloc externe).
Synchronisation : image affichee t = registres de t-1 + VRAM de t (DECORS-WS §2).
Usage : anneau.py <frm> <sortie injection_fork (rapport_fork.json, roms, ext)> [decor]"""
import sys, os, json, collections
import numpy as np
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), "<workspace>/work/decors_ws/py"]
from recio import read_rec
import image, blocs_tr as BT
frm, sortie = sys.argv[1:3]; dec = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x0C
r = json.load(open(os.path.join(sortie, "rapport_fork.json")))
reloc = {k: int(v[1:], 16) for k, v in r["relogement"].items()}
d1 = image.lit(os.path.join(sortie, "roms/sfa3hx")); EXT = int(r["ext_base"][1:], 16)
ext = open(os.path.join(sortie, "ext/ext_%06x.bin" % EXT), "rb").read()
D = bytearray(EXT + len(ext)); D[:len(d1)] = d1; D[EXT:] = ext
M = dict(BT.MOD["ro3"], **{k: reloc[k] for k in ("b1", "st1", "list1")})
T1 = BT.cases_tilemap(D, M, 1, dec)
frs = read_rec(frm)
stat = collections.Counter(); pires = []
for prev, f in zip(frs, frs[1:]):
    s1x, s1y, s3x = prev.reg(0x0c), prev.reg(0x0e), prev.reg(0x14)
    base = ((prev.reg(0x02) << 8) & 0xffc000); o0 = (base - 0x900000) // 2
    rows = sorted({((sy + 16 + s1y) % 512) // 8 for sy in range(224)})
    mauvais = {"gauche": 0, "4:3": 0, "droite": 0}
    for sx in range(-32 - ((64 + s1x) % 8), 416, 8):
        wx = sx + 64 + s3x
        if wx // 8 != (sx + 64 + s1x) // 8 + ((s3x - s1x) // 8): pass
        wc = (wx // 8); rc = ((sx + 64 + s1x) % 512) // 8
        ok = True
        for row in rows:
            idx = (row & 0x1f) + ((rc & 0x3f) << 5) + ((row & 0x20) << 6)
            v = (int(f.vram[o0 + 2 * idx]), int(f.vram[o0 + 2 * idx + 1]))
            e = T1.get((wc % 128, row))
            if e is None or v[0] != e[0] or (v[1] & 0x7F) != (e[1] & 0x7F):
                ok = False; break
        if not ok:
            zone = "gauche" if sx + 8 <= 0 else "droite" if sx >= 384 else "4:3"
            mauvais[zone] += 1
    sens = "->" if f.c > prev.c else "<-" if f.c < prev.c else "=="
    for z, n in mauvais.items():
        stat[(sens, z, n)] += 1
    if mauvais["4:3"] or mauvais["gauche"] or mauvais["droite"]:
        pires.append((f.c, sens, mauvais))
print("images comparees :", len(frs) - 1)
for sens in ("->", "<-", "=="):
    for z in ("gauche", "4:3", "droite"):
        c = {n: k for (s_, z_, n), k in stat.items() if s_ == sens and z_ == z}
        if c: print("  camera %s  zone %-6s : colonnes de 8 px fausses par image -> nombre d'images %s" % (sens, z, dict(sorted(c.items()))))
print("exemples :", pires[:5], pires[-5:])
