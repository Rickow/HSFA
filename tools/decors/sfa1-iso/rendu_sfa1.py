#!/usr/bin/env python3
"""rendu_sfa1.py — rendu HORS JEU des décors de SFA1 à partir des données extraites de l'ISO (extrait_sfa1.py).

Modèle (vérifié contre la VRAM de MAME, compare_mame.py) :
  - scroll2 : tilemap 1024 × 1024 (64 × 64 tuiles 16×16) = liste de 16 blocs, ligne par ligne (j = 4·by + bx) ;
    bloc = 16 × 16 tuiles, colonne par colonne (k : colonne k // 16, ligne k % 16) ; code + $D400 ;
  - scroll3 : tilemap 2048 × 2048 (64 × 64 tuiles 32×32) = 8 × 8 blocs de 8 × 8 tuiles (mêmes ordres) ; code + $3D00 ;
  - attribut : palette bits 0-4, miroir X bit 5, miroir Y bit 6 ; pen 15 transparent (scroll3 dessiné opaque) ;
  - couleur CPS2 : mot BRGB, luminosité = $F au chargement (le jeu fait OR $F000) ; MAME : c × $11 × (15 + 2B) / 45.

Usage : rendu_sfa1.py DONNEES/ PLANCHES/   -> une planche PNG par décor + planche générale"""
import os, sys, json, struct
import numpy as np
from PIL import Image

def couleur(mot):
    b = 0x0F + ((mot >> 12) << 1)
    return tuple(((mot >> s) & 0xF) * 0x11 * b // 0x2D for s in (8, 4, 0))

class Donnees:
    def __init__(self, dossier):
        self.J = json.load(open(os.path.join(dossier, "sfa1_decors.json")))
        self.bib2 = open(os.path.join(dossier, "bib_s2.bin"), "rb").read()
        self.bib3 = open(os.path.join(dossier, "bib_s3.bin"), "rb").read()
        self.P2 = np.load(os.path.join(dossier, "pixels_s2.npy")); self.P3 = np.load(os.path.join(dossier, "pixels_s3.npy"))
        self.lo2 = self.J["codes_s2"][0]; self.lo3 = self.J["codes_s3"][0]
    def decor(self, s): return self.J["decors"][s]
    def grille(self, s, plan):
        d = self.decor(s)
        if plan == 2: L, bib, nb, tb, add = d["liste_s2"], self.bib2, 4, 16, 0xD400
        else: L, bib, nb, tb, add = d["liste_s3"], self.bib3, 8, 8, 0x3D00
        n = nb * tb; C = np.zeros((n, n), np.int64); T = np.zeros((n, n), np.int64); taille = tb * tb * 4
        for j, b in enumerate(L):
            by, bx = divmod(j, nb)
            for k in range(tb * tb):
                code, at = struct.unpack_from(">HH", bib, b * taille + 4 * k)
                C[by * tb + k % tb, bx * tb + k // tb] = (code + add) & 0xFFFF; T[by * tb + k % tb, bx * tb + k // tb] = at
        return C, T
    def palettes(self, s, plan):
        h = self.decor(s)["pal_s%d" % plan]
        return [int(h[4 * i:4 * i + 4], 16) | 0xF000 for i in range(512)]
    def image_plan(self, s, plan, opaque=False):
        """tilemap entière en RGBA (alpha 0 = transparent) et en indices (palette·16 + pen)"""
        C, T = self.grille(s, plan); ts = 16 if plan == 2 else 32
        P, lo = (self.P2, self.lo2) if plan == 2 else (self.P3, self.lo3)
        n = C.shape[0]; idx = np.zeros((n * ts, n * ts), np.int32)
        for r in range(n):
            for c in range(n):
                t = P[C[r, c] - lo]; at = T[r, c]
                if at & 0x20: t = t[:, ::-1]
                if at & 0x40: t = t[::-1, :]
                idx[r * ts:(r + 1) * ts, c * ts:(c + 1) * ts] = (at & 0x1F) * 16 + t
        pal = np.array([couleur(m) for m in self.palettes(s, plan)], np.uint8)
        rgba = np.zeros(idx.shape + (4,), np.uint8); rgba[..., :3] = pal[idx]
        rgba[..., 3] = 255 if opaque else np.where((idx & 15) == 15, 0, 255)
        return idx, rgba

def ecran(D, s, s2x, s2y, s3x, s3y, rows=None, rso=0, largeur=384, dx=0, img=None):
    """composite scroll3 (opaque) + scroll2 comme le CPS2 (fenêtre 384×224 = x 64.., y 16.. de la tilemap défilée).
    rows : table rowscroll (1024 mots) ; dx : élargissement symétrique (16:9 : largeur 512, dx = 64)"""
    i3, c3 = img[3] if img else D.image_plan(s, 3, opaque=True)
    i2, c2 = img[2] if img else D.image_plan(s, 2)
    out = np.zeros((224, largeur, 3), np.uint8)
    xs = np.arange(largeur) - dx
    for y in range(224):
        l3 = (y + 16 + s3y) & 0x7FF
        out[y] = c3[l3, (xs + 64 + s3x) & 0x7FF, :3]
        l2 = (y + 16 + s2y) & 0x3FF
        sx = s2x + (int(rows[(y + 16 + rso) & 0x3FF]) if rows is not None else 0)
        p = c2[l2, (xs + 64 + sx) & 0x3FF]
        m = p[:, 3] > 0; out[y, m] = p[m, :3]
    return out

def rowscroll_modele(effet, cam2x_l, base=0x3D8, effets=None, cam0_l=0x1C00000):
    """table de 1024 mots : sol en perspective de SFA1 (sfa $1B63E…). cam2x_l = X caméra scroll2 en 16.16
    ($FF82A0, long), cam0_l = X initial ($FF8288 = $1C0.0000). d = (cam2x − cam0) / k, division signée tronquée
    ($16070) ; ligne de base + i (i = 0..23) : $C0 + ⌊i·d⌋ (mot fort) ; au-dessus : « haut » lignes en dégradé
    (−d par ligne) puis 216 − haut lignes constantes ; le reste de la table reste à $C0 (240 lignes écrites)."""
    if effet == "-" or effet is None: return None
    r = np.full(1024, 0xC0, np.int64)
    k, haut = effets[effet]["k"], effets[effet]["haut"]
    x = cam2x_l - cam0_l; d = abs(x) // k; d = -d if x < 0 else d
    acc = 0
    for i in range(24):
        r[(base + i) & 0x3FF] = 0xC0 + (acc >> 16); acc += d
    acc = 0; v = 0xC0
    for i in range(1, haut + 1):
        acc -= d; v = 0xC0 + (acc >> 16); r[(base - i) & 0x3FF] = v
    for i in range(haut + 1, haut + 1 + 216 - haut):
        r[(base - i) & 0x3FF] = v
    return r & 0xFFFF

def main():
    D = Donnees(sys.argv[1]); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    vues = []
    for s in range(13):
        d = D.decor(s)
        img = {3: D.image_plan(s, 3, opaque=True), 2: D.image_plan(s, 2)}
        # tilemaps entières (bande visible), vues 4:3 aux butées / centre, et 16:9 (512) aux butées
        Image.fromarray(img[2][1]).save(os.path.join(out, "s%02X_scroll2_1024.png" % (2 * s)))
        Image.fromarray(img[3][1][:, :, :3]).save(os.path.join(out, "s%02X_scroll3_2048.png" % (2 * s)))
        s3 = lambda cam: (d["gest_s3"]["x0"] - 0xA0 + cam // 2) & 0x7FF      # mesuré (compare_mame) : X0 − $A0 + s2X/2
        rs = lambda cam: rowscroll_modele(d["effet"], (cam + 0x100) << 16, effets=D.J["effets"])   # caméra = s2X + $100
        lignes = [ecran(D, s, cam, 0x300, s3(cam), 0x700, rs(cam), 0x300, img=img) for cam in (0x000, 0x0C0, 0x180)]
        l169 = [ecran(D, s, cam, 0x300, s3(cam), 0x700, rs(cam), 0x300, largeur=512, dx=64, img=img) for cam in (0x000, 0x180)]
        pl = np.full((224 * 2 + 8, 384 * 3 + 16, 3), 40, np.uint8)
        for i, v in enumerate(lignes): pl[:224, i * 392:i * 392 + 384] = v
        pl[232:, :512] = l169[0]; pl[232:, 520:1032] = l169[1]
        Image.fromarray(pl).save(os.path.join(out, "s%02X_vues.png" % (2 * s)))
        vues.append(lignes[1])
    g = np.full((224 * 5 + 32, 384 * 3 + 16, 3), 40, np.uint8)
    for i, v in enumerate(vues):
        r, c = divmod(i, 3); g[r * 232:r * 232 + 224, c * 392:c * 392 + 384] = v
    Image.fromarray(g).save(os.path.join(out, "planche_sfa1_iso.png"))

if __name__ == "__main__":
    main()
