#!/usr/bin/env python3
"""Essai MAME : captures -> PNG, comparaison temoin / injection, et rendu 448x224 hors ligne (py/cpsgfx.py, fidele au
pilote MAME) depuis le releve FRM0 des images capturees avec la region gfx CORRIGEE par les blocs de reimport.py.
Usage : venv/bin/python reimport/essai_rendu.py [dossier de sortie de reimport.py]"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(D, "py"), os.path.join(D, "export")]
import numpy as np
from PIL import Image
from recio import read_rec, read_scr
import cpsgfx as G

ES = os.path.join(HERE, "essai")
SORTIE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "test_0C")
NOMS = {1: "gauche", 2: "gauche_decale-32", 3: "droite", 4: "droite_decale+32"}


def rendu(f, larg, gx):
    """composite des plans, ecran de largeur larg ; gx = decalage du bord gauche par rapport a l'ecran 384 (-32 pour 448)"""
    img = np.zeros((224, larg, 3), np.uint8)
    for L in G.layer_order(f):
        Lg = G.LAYERS[L]; ts = Lg["ts"]; W = G.TM * ts
        pen, pal = G.tilemap_pens(f, L)
        sx = np.arange(larg) + gx; sy = np.arange(224)
        ty = (sy + 16 + f.reg(Lg["ry"])) % W
        rs = np.zeros(224, np.int64)
        if L == 2 and (f.reg(0x22) & 1):
            oo = (((f.reg(0x08) << 8) & 0xfff800) - 0x900000) // 2
            v = f.vram[oo + ((sy + 16 + f.reg(0x20)) & 0x3ff)]; rs = np.where(v >= 0x8000, v - 0x10000, v)
        tx = (sx[None, :] + 64 + f.reg(Lg["rx"]) + rs[:, None]) % W
        p = pen[ty[:, None], tx]; q = pal[ty[:, None], tx]
        m = p != 15
        img[m] = f.pal[q.astype(np.int64) * 16 + p][m]
    return img


def main():
    res = {}
    for nom in ("temoin", "inj"):
        scr = read_scr(os.path.join(ES, nom + "_scr.bin"))
        for t, im in scr.items():
            Image.fromarray(im).resize((im.shape[1] * 2, im.shape[0] * 2), Image.NEAREST).save(
                os.path.join(ES, "%s_%s.png" % (nom, NOMS[t])))
        res[nom] = scr
    for t in res["temoin"]:
        d = (res["temoin"][t] != res["inj"][t]).any(2)
        cols = np.nonzero(d.any(0))[0]
        print("capture %-18s : %6d px differents temoin/injection, colonnes ecran %s" % (
            NOMS[t], int(d.sum()), "%d-%d" % (cols.min(), cols.max()) if cols.size else "-"))
    # rendu 448 hors ligne : region corrigee
    reg = np.fromfile(os.path.join(D, "gfx/gfx_region.bin"), np.uint8)
    for b in json.load(open(os.path.join(SORTIE, "blocs.json"))):
        o = int(b["decalage_region"][1:], 16); data = np.fromfile(os.path.join(SORTIE, b["fichier"]), np.uint8)
        reg[o:o + len(data)] = data
    G.GFX = reg; G.tile.cache_clear()
    for nom in ("temoin", "inj"):
        frs = read_rec(os.path.join(ES, nom + "_frm.bin"))
        for f in frs:
            if f.t not in (1, 3): continue
            im = rendu(f, 448, -32)
            Image.fromarray(im).resize((896, 448), Image.NEAREST).save(os.path.join(ES, "%s_rendu448_%s.png" % (nom, NOMS[f.t])))
            # controle : la partie centrale 384 du rendu = capture MAME normale (registres de l'image precedente :
            # tolerance, on compte seulement)
            c = (im[:, 32:416] != res[nom][f.t]).any(2).sum()
            print("rendu448 %s %s : centre vs capture MAME : %d px differents" % (nom, NOMS[f.t], int(c)))
            if nom == "inj":
                dec = res[nom][f.t + 1]
                if f.t == 1: band_mame, band_rendu = dec[:, :32], im[:, :32]
                else: band_mame, band_rendu = dec[:, 352:], im[:, 416:]
                print("   bande de 32 px : rendu 448 hors ligne vs capture MAME decalee : %d px differents"
                      % int((band_mame != band_rendu).any(2).sum()))


if __name__ == "__main__":
    main()
