#!/usr/bin/env python3
"""CONTROLE PIXEL A PIXEL du décor importé : tilemaps complètes (contenu de la RAM vidéo + palettes MAME) du fork
(programme traduit corrigé, région en mode « bases de plans ») contre l'arcade sfa2u (relevé de l'export).

  - scroll2 / scroll3 : tilemaps statiques (posées une fois au chargement) -> comparaison de la tilemap ENTIERE
    (1024x1024 / 2048x2048 px), couleur et transparence ;
  - scroll1 (anneau de 512 px recomposé selon la caméra) : on prend l'image sfa2u dont le défilement scroll1 est le
    même que celui de la capture du fork, et on compare l'anneau entier ;
  - défilements : pour chaque capture du fork, images sfa2u au même défilement scroll2 (caméra) -> défilements
    scroll1 / scroll3 attendus (parallaxe).
Usage : compare_plans.py <frm fork> <hsfa_plans du fork> <full.rec sfa2u> <région :gfx sfa2u> [dossier images]
"""
import sys, os, numpy as np
sys.path[:0] = ["<workspace>/work/decors_ws/py"]
import importlib.util
_sp = importlib.util.spec_from_file_location("recio2", "<workspace>/work/decors_sfa2/export/py/recio.py")
recio2 = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(recio2)
read_rec = recio2.read_rec
import cpsgfx as G
from PIL import Image

OFF = {1: 0, 2: 0x400000, 3: 0xA00000}
phys_cps2 = G.phys_code
phys_base = lambda l, c: OFF[l] // G.LAYERS[l]["tbytes"] + (c & 0x3fff if l == 3 else c)


def tilemap_rgb(f, L, gfx, phys):
    G.GFX = gfx; G.phys_code = phys; G.tile.cache_clear()
    pen, pal = G.tilemap_pens(f, L)
    rgb = f.pal[pal.astype(np.int64) * 16 + pen]
    return rgb, pen != 15


def regs(f):
    return {L: (f.reg(G.LAYERS[L]["rx"]), f.reg(G.LAYERS[L]["ry"])) for L in (1, 2, 3)}


def main():
    ffork, pfork, frec, g2 = sys.argv[1:5]
    dimg = sys.argv[5] if len(sys.argv) > 5 else None
    gf = np.fromfile(pfork, np.uint8); g2 = np.fromfile(g2, np.uint8)
    fk = read_rec(ffork)
    s2 = read_rec(frec)
    print("fork : %d captures ; sfa2u : %d images" % (len(fk), len(s2)))
    res = {}
    # défilements
    idx = {}
    for i, f in enumerate(s2):
        r = regs(f); idx.setdefault((r[2][0], r[2][1]), []).append(i)
    for f in fk:
        r = regs(f)
        cand = idx.get((r[2][0], r[2][1]), [])
        att = sorted({(regs(s2[i])[1], regs(s2[i])[3]) for i in cand})
        print("capture %d : scroll2 %04X,%04X | fork s1 %04X,%04X s3 %04X,%04X | sfa2u au même scroll2 : %s" % (
            f.t, r[2][0], r[2][1], r[1][0], r[1][1], r[3][0], r[3][1],
            " ".join("s1 %04X,%04X s3 %04X,%04X" % (a[0], a[1], b[0], b[1]) for a, b in att[:3]) or "aucune"))
    # tilemaps
    ref = s2[len(s2) // 2]
    for L in (2, 3):
        a, ma = tilemap_rgb(ref, L, g2, phys_cps2)
        for f in fk:
            b, mb = tilemap_rgb(f, L, gf, phys_base)
            dm = (ma != mb); dc = (ma & mb) & (a != b).any(2)
            n = int(dm.sum() + dc.sum())
            print("scroll%d capture %d : tilemap entière %dx%d : %d px différents (transparence %d, couleur %d) sur %d opaques" % (
                L, f.t, a.shape[1], a.shape[0], n, int(dm.sum()), int(dc.sum()), int(ma.sum())))
            res[(L, f.t)] = n
            if dimg and f.t == fk[0].t:
                os.makedirs(dimg, exist_ok=True)
                Image.fromarray(np.where(ma[..., None], a, 0).astype(np.uint8)).save(os.path.join(dimg, "s%d_sfa2u.png" % L))
                Image.fromarray(np.where(mb[..., None], b, 0).astype(np.uint8)).save(os.path.join(dimg, "s%d_fork.png" % L))
    # scroll1 : image sfa2u au même défilement scroll1
    for f in fk:
        r = regs(f)
        cand = [g for g in s2 if regs(g)[1] == r[1]]
        if not cand:
            print("scroll1 capture %d : aucune image sfa2u au même défilement %04X,%04X" % (f.t, *r[1])); continue
        g = cand[len(cand) // 2]
        a, ma = tilemap_rgb(g, 1, g2, phys_cps2)
        b, mb = tilemap_rgb(f, 1, gf, phys_base)
        dm = (ma != mb); dc = (ma & mb) & (a != b).any(2)
        print("scroll1 capture %d (sfa2u image %d, %d candidates) : anneau 512x512 : %d px différents (transparence %d, couleur %d) sur %d opaques" % (
            f.t, g.t, len(cand), int(dm.sum() + dc.sum()), int(dm.sum()), int(dc.sum()), int(ma.sum())))
        if dimg:
            Image.fromarray(np.where(ma[..., None], a, 0).astype(np.uint8)).save(os.path.join(dimg, "s1_sfa2u_c%d.png" % f.t))
            Image.fromarray(np.where(mb[..., None], b, 0).astype(np.uint8)).save(os.path.join(dimg, "s1_fork_c%d.png" % f.t))
            d = (dm | dc)
            if d.any():
                Image.fromarray((d * 255).astype(np.uint8)).save(os.path.join(dimg, "s1_ecarts_c%d.png" % f.t))


if __name__ == "__main__" and not os.environ.get("ECRAN"):
    main()


def ecran(ffork, pfork, frec, g2, dimg=None):
    """composite des 3 plans (ordre CPS-B, rowscroll) à l'écran, fork vs sfa2u au même défilement des 3 plans"""
    gf = np.fromfile(pfork, np.uint8); g2 = np.fromfile(g2, np.uint8)
    fk = read_rec(ffork); s2 = read_rec(frec)
    for f in fk:
        r = regs(f)
        cand = [i for i, g in enumerate(s2) if i > 0 and regs(s2[i - 1]) == r]
        if not cand: print("ecran capture %d : pas d'image sfa2u au même défilement" % f.t); continue
        i = cand[len(cand) // 2]
        g = G.mix(s2[i - 1], s2[i])                 # image affichée = registres t-1 + VRAM t
        out = []
        for fr, gfx, ph in ((g, g2, phys_cps2), (f, gf, phys_base)):
            G.GFX = gfx; G.phys_code = ph; G.tile.cache_clear()
            img = np.zeros((224, 384, 3), np.uint8)
            for L in G.layer_order(fr):
                rgb, m = G.render_screen_layer(fr, L); img[m] = rgb[m]
            out.append(img)
        d = (out[0] != out[1]).any(2)
        print("ecran capture %d (sfa2u image %d) : layer control fork %04X sfa2u %04X, video %04X/%04X, composite 3 plans : %d px différents / %d" % (
            f.t, s2[i].t, f.breg(0x26), g.breg(0x26), f.reg(0x22), g.reg(0x22), int(d.sum()), d.size))
        if dimg:
            Image.fromarray(np.concatenate([out[0], out[1], np.where(d[..., None], 255, out[1] // 3).astype(np.uint8)], 1)).save(
                os.path.join(dimg, "ecran_c%d_sfa2u_fork_ecarts.png" % f.t))


if __name__ == "__main__" and os.environ.get("ECRAN"):
    ecran(*sys.argv[1:6])
