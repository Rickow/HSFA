"""Essai fork : bandes de 32 px des captures decalees (fenetre 448 simulee) vs apercu 448 de reimport.py, hors
sprites/HUD (pixels non noirs de la meme bande dans le temoin, ou les plans sont vides) ; vue 4:3 vs temoin.
Usage : compare_essai.py <prefixe essai> <dossier reimport (apercus)> [<prefixe temoin>]"""
import os, sys
sys.path.insert(0, "<workspace>/work/decors_ws/py")
import numpy as np
from PIL import Image
from recio import read_scr
ess, dos = sys.argv[1], sys.argv[2]
tem = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(ess), "temoin")
t = read_scr(tem + "_scr.bin"); s = read_scr(ess + "_scr.bin")
ok = True; res = {}
for tag, side in ((2, "gauche"), (4, "droite")):
    ap = np.array(Image.open(os.path.join(dos, "apercu_448_%s.png" % side)).convert("RGB"))[::2, ::2]
    sl = slice(0, 32) if side == "gauche" else slice(352, 384)
    bm, bt = s[tag][:, sl], t[tag][:, sl]
    ba = ap[:, :32] if side == "gauche" else ap[:, 416:]
    sp = (bt != 0).any(2)
    d = (bm != ba).any(2)
    n = int((d & ~sp).sum()); ok &= n == 0
    res[side] = n
    print("%s %s : bande MAME vs apercu, hors sprites/HUD : %d px differents sur %d (bande entiere : %d)" % (
        os.path.basename(ess), side, n, int((~sp).sum()), int(d.sum())))
    # image de controle : bande MAME | bande apercu | ecarts (magenta)
    e = np.zeros_like(bm); e[d & ~sp] = (255, 0, 255); e[sp] = (60, 60, 60)
    Image.fromarray(np.concatenate([bm, ba, e], 1)).resize((96 * 4, 224 * 4), Image.NEAREST).save(ess + "_bande_%s.png" % side)
for k in (1, 3):
    same = (s[k] == t[k]).all(); ok &= bool(same)
    print("%s capture %d (4:3) identique au temoin : %s (%d px differents)" % (os.path.basename(ess), k, same, int((s[k] != t[k]).any(2).sum())))
for k, im in s.items():
    Image.fromarray(im).resize((768, 448), Image.NEAREST).save("%s_%d.png" % (ess, k))
print("ESSAI", "OK" if ok else "ECARTS")
