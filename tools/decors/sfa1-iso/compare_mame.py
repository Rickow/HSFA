#!/usr/bin/env python3
"""compare_mame.py DONNEES MAME_DIR [decors…] — contrôle des données ISO contre SFA1 joué (arcade sfa, MAME, local).
Pour chaque décor et chaque vidage (gauche / droite / centre de mame/lua/sonde.lua) :
  1. tilemaps scroll2 / scroll3 entières (VRAM) contre la grille construite depuis l'ISO ;
  2. palettes scroll2 / scroll3 (RAM de palette) contre celles de l'ISO (+$F000) ;
  3. table rowscroll de la VRAM contre le modèle du sol (rendu_sfa1.rowscroll_modele) ;
  4. écran : rendu hors jeu (données ISO, registres MAME, rowscroll VRAM) contre la capture MAME sans HUD ni sprites.
Écrit MAME_DIR/../controle/… (images de différence) et un résumé TSV."""
import os, sys, json, struct
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_mame as M, rendu_sfa1 as RS

def main():
    D = RS.Donnees(sys.argv[1]); MD = sys.argv[2]
    sel = [int(x, 16) // 2 for x in sys.argv[3:]] or range(13)
    sortie = os.path.join(os.path.dirname(os.path.abspath(MD.rstrip("/"))), "controle"); os.makedirs(sortie, exist_ok=True)
    res = ["decor\tvue\ts2X\ts2Y\ts3X\ts3Y\tcam2X\tgrille_s2\tgrille_s3\tpal_s2\tpal_s3\trowscroll\tpixels_diff\tpixels"]
    for s in sel:
        stg = "%02X" % (2 * s)
        dumps = M.lit(os.path.join(MD, "out", "stg%s_dmp.bin" % stg))
        G2 = D.grille(s, 2); G3 = D.grille(s, 3)
        img = {3: D.image_plan(s, 3, opaque=True), 2: D.image_plan(s, 2)}
        for i, d in enumerate(dumps):
            A = d["A"]; ram = d["ram"]
            C2, T2 = M.tilemap_s2(d); C3, T3 = M.tilemap_s3(d)
            e2 = int(((C2 != G2[0]) | (T2 != G2[1])).sum()); e3 = int(((C3 != G3[0]) | (T3 != G3[1])).sum())
            pal = M.mots(d["gfx"], A[5], 0xC00)
            p2 = np.array(D.palettes(s, 2)); p3 = np.array(D.palettes(s, 3))
            ep2 = int((pal[0x400:0x600] != p2).sum()); ep3 = int((pal[0x600:0x800] != p3).sum())
            rows = M.mots(d["gfx"], A[4], 1024).astype(np.int64)
            cam2x = struct.unpack_from(">i", ram, 0x2A0)[0] >> 16; cam_l = struct.unpack_from(">i", ram, 0x2A0)[0]; cam0_l = struct.unpack_from(">i", ram, 0x288)[0]
            mod = RS.rowscroll_modele(D.decor(s)["effet"], cam_l, effets=D.J["effets"], cam0_l=cam0_l)
            er = int((rows != (mod if mod is not None else rows)).sum()) if A[0x11] & 1 else -1
            s2x, s2y, s3x, s3y, rso = A[8], A[9], A[10], A[11], A[0x10]
            r = RS.ecran(D, s, s2x, s2y, s3x, s3y, rows if A[0x11] & 1 else None, rso, img=img)
            snap = os.path.join(MD, "snap", "stg" + stg, "sfa", "%04d.png" % (i + 1))
            m = np.asarray(Image.open(snap).convert("RGB"))
            dif = np.any(r != m, -1); nd = int(dif.sum())
            if nd:
                v = np.concatenate([m, r, np.where(dif[..., None], [255, 0, 0], m // 3).astype(np.uint8)], 1)
                Image.fromarray(v).save(os.path.join(sortie, "diff_%s_%s.png" % (stg, d["tag"])))
            res.append("$%s\t%s\t%04X\t%04X\t%04X\t%04X\t%04X\t%d\t%d\t%d\t%d\t%d\t%d\t%d" % (
                stg, d["tag"], s2x, s2y, s3x, s3y, cam2x & 0xFFFF, e2, e3, ep2, ep3, er, nd, dif.size))
            print(res[-1], flush=True)
    open(os.path.join(sortie, "controle.tsv"), "w").write("\n".join(res) + "\n")

if __name__ == "__main__":
    main()
