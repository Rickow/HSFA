#!/usr/bin/env python3
"""Essai MAME : bandes de 32 px des captures decalees (fenetre elargie simulee) vs apercu 448 de reimport.py, hors
sprites/HUD (pixels non noirs de la meme bande dans l'essai temoin, ou les plans y sont vides) ; vue 4:3 vs temoin."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(D, "py"), os.path.join(D, "export")]
import numpy as np
from PIL import Image
from recio import read_scr
t = read_scr(os.path.join(HERE, "essai/temoin_scr.bin"))
for k, im in t.items():
    Image.fromarray(im).resize((768, 448), Image.NEAREST).save(os.path.join(HERE, "essai/temoin_%d.png" % k))
ok = True
for nom, dos in (("inj", "test_0C"), ("pal", "test_0C_pal")):
    s = read_scr(os.path.join(HERE, "essai/%s_scr.bin" % nom))
    for k, im in s.items():
        Image.fromarray(im).resize((768, 448), Image.NEAREST).save(os.path.join(HERE, "essai/%s_%d.png" % (nom, k)))
    for tag, side in ((2, "gauche"), (4, "droite")):
        ap = np.array(Image.open(os.path.join(HERE, dos, "apercu_448_%s.png" % side)))[::2, ::2]
        sl = slice(0, 32) if side == "gauche" else slice(352, 384)
        bm, bt = s[tag][:, sl], t[tag][:, sl]
        ba = ap[:, :32] if side == "gauche" else ap[:, 416:]
        sp = (bt != 0).any(2)
        n = int(((bm != ba).any(2) & ~sp).sum()); ok &= n == 0
        print("%s %s : bande MAME vs apercu, hors sprites/HUD : %d px differents sur %d" % (nom, side, n, int((~sp).sum())))
    same = all((s[k] == t[k]).all() for k in (1, 3)); ok &= same
    print("%s : vue 4:3 identique au temoin : %s" % (nom, same))
print("ESSAI MAME", "OK" if ok else "ECARTS")
