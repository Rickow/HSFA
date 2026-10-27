#!/usr/bin/env python3
"""ROM DU VISUALISEUR D'ETAT PS2 (HANDOFF §89) : programme minimal (SR=$2700, boucle sur place) pour roms_vis/sfa3ud ;
les autres fichiers (graphismes, son, cle) sont des liens vers roms_tr. Le rendu est fait par mame/visu.lua.
Usage : visu_rom.py   puis   ETAT=<etats_ps2/ee/nom> mame sfa3ud -rompath roms_vis -autoboot_script visu.lua"""
import os, struct
W = "<workspace>/work/mame"
out = os.path.join(W, "roms_vis", "sfa3ud"); os.makedirs(out, exist_ok=True)
names = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]
src = os.path.join(W, "roms_tr", "sfa3ud")
for f in os.listdir(src):
    if f not in names:
        d = os.path.join(out, f)
        if os.path.lexists(d): os.remove(d)
        os.symlink(os.path.realpath(os.path.join(src, f)), d)
img = bytearray(0x400000)
struct.pack_into('>II', img, 0, 0x00FFF000, 0x400)
for v in range(2, 64): struct.pack_into('>I', img, 4 * v, 0x406)
struct.pack_into('>HHHH', img, 0x400, 0x46fc, 0x2700, 0x60fe, 0x4e73)   # MOVE #$2700,SR ; BRA.S * ; RTE
sw = bytes(b for i in range(0, len(img), 2) for b in (img[i + 1], img[i]))
for k, n in enumerate(names): open(os.path.join(out, n), "wb").write(sw[k * 0x80000:(k + 1) * 0x80000])
print("roms_vis pret")
