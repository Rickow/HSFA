"""Essai FBNeo widescreen (448x224 natif) : pour chaque capture aux butees (snap_<1|3>_<image>.ppm), bande de 32 px
de l'injection vs apercu 448 de reimport.py hors sprites/HUD (pixels non noirs de la bande du temoin a la meme image),
et partie centrale 384 (vue 4:3) de l'injection vs temoin.
Usage : compare_fb.py <dossier essai> <dossier temoin> <dossier reimport>"""
import os, sys, glob
import numpy as np
from PIL import Image
ess, tem, dos = sys.argv[1:4]
tot = {}
ok = True
for tag, side in ((1, "gauche"), (3, "droite")):
    ap = np.array(Image.open(os.path.join(dos, "apercu_448_%s.png" % side)).convert("RGB"))[::2, ::2]
    sl = slice(0, 32) if side == "gauche" else slice(416, 448)
    res = []
    for p in sorted(glob.glob(os.path.join(ess, "snap", "snap_%d_*.ppm" % tag))):
        q = os.path.join(tem, "snap", os.path.basename(p))
        a = np.array(Image.open(p)); t = np.array(Image.open(q))
        sp = (t[:, sl] != 0).any(2)
        d = (a[:, sl] != ap[:, sl]).any(2)
        n = int((d & ~sp).sum()); cen = int((a[:, 32:416] != t[:, 32:416]).any(2).sum())
        dy_ok = None
        if n:                       # camera deplacee (super, secousse) : recalage vertical de l'apercu (Y nominal)
            for dy in sorted(range(-24, 25), key=abs):
                ys = slice(max(0, dy), min(224, 224 + dy)); ya = slice(max(0, -dy), min(224, 224 - dy))
                if int((((a[ys, sl] != ap[ya, sl]).any(2)) & ~sp[ys]).sum()) == 0: dy_ok = dy; break
        res.append((os.path.basename(p), n, int((~sp).sum()), cen, dy_ok))
    nz = [r for r in res if r[1]]
    cz = [r for r in res if r[3]]
    nr = [r for r in nz if r[4] is None]
    ok &= not nr and not cz
    if nz: print("   %d captures en ecart : %d exactes apres recalage vertical (camera deplacee de %s px), %d non expliquees"
                 % (len(nz), len(nz) - len(nr), sorted({r[4] for r in nz if r[4] is not None}), len(nr)))
    print("%s : %d captures ; bande vs apercu hors sprites/HUD : %d captures avec ecart (max %d px), zone comparee %d-%d px ; "
          "vue 4:3 vs temoin : %d captures differentes" % (side, len(res), len(nz), max([r[1] for r in res] or [0]),
                                                           min(r[2] for r in res), max(r[2] for r in res), len(cz)))
    if res:
        b = res[len(res) // 2][0]
        a = np.array(Image.open(os.path.join(ess, "snap", b))); t = np.array(Image.open(os.path.join(tem, "snap", b)))
        Image.fromarray(np.concatenate([t, a, ap], 0)).resize((896, 1344), Image.NEAREST).save(
            os.path.join(ess, "planche_%s.png" % side))
print("ESSAI FBNEO", "OK" if ok else "ECARTS")
