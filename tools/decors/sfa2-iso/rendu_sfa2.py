#!/usr/bin/env python3
"""rendu_sfa2.py — rendu HORS JEU des décors de SFA2 à partir des données extraites de l'ISO (extrait_sfa2.py).
(Structure reprise de decors_sfa1/outils/rendu_sfa1.py ; compositeur CPS2 comme decors_sfa2/export/py/cpsgfx.py.)

Modèle (vérifié contre la VRAM de MAME, compare_mame.py) :
  - scroll1 : monde de blocs de 256 × 256 (32 × 32 tuiles 8×8) ; bloc = 8 × 8 cellules (colonne d'abord), cellule =
    4 × 4 tuiles (colonne d'abord) ; liste de 4 / 8 / 16 / 12 blocs selon le type (0 / 2 / 4 / 6), LARGEUR_S1 blocs
    par rangée ; la tilemap de 512 × 512 est un anneau recomposé par le moteur (monde mod 512) ;
  - scroll2 : tilemap 1024 × 1024 = 4 × 4 blocs de 16 × 16 tuiles (colonne d'abord) ;
  - scroll3 : tilemap 2048 × 2048 = 8 × 8 blocs de 8 × 8 tuiles 32×32 ;
  - attribut : palette bits 0-4, miroir X bit 5, miroir Y bit 6 ; pen 15 transparent ; plans dessinés sur fond noir dans
    l'ordre du contrôle CPS-B (bits 6, 8, 10, 12 ; 0 = sprites) ;
  - couleur CPS2 : mot BRGB, luminosité forcée à $F (OR $F000) ; MAME : c × $11 × (15 + 2B) / 45.

Usage : rendu_sfa2.py DONNEES/ PLANCHES/ [décors hexa…]  -> planches PNG par décor + planche générale"""
import os, sys, json, struct
import numpy as np

LARGEUR_S1 = {0: 2, 2: 4, 4: 8, 6: 4}       # blocs par rangée du monde scroll1 : 2×2, 4×2, 8×2, 4×3 (vérifié VRAM + écran)
POS = dict(gauche=0x000, centre=0x0C0, droite=0x180)   # registre scroll2 X aux butées et au centre (caméra $100-$280)

def couleur(mot):
    b = 0x0F + ((mot >> 12) << 1)
    return tuple(((mot >> s) & 0xF) * 0x11 * b // 0x2D for s in (8, 4, 0))

class Donnees:
    def __init__(self, dossier):
        self.J = json.load(open(os.path.join(dossier, "sfa2_decors.json")))
        self.b = {k: open(os.path.join(dossier, k + ".bin"), "rb").read() for k in ("bib_s1", "cel_s1", "bib_s2", "bib_s3")}
        self.P = {p: np.load(os.path.join(dossier, "pixels_s%d.npy" % p)) for p in (1, 2, 3)}
        self.lo = {1: 0, 2: self.J["codes_s2"][0], 3: self.J["codes_s3"][0]}
        self.cache = {}
    def decor(self, s): return self.J["decors"][s]
    def grille(self, s, plan):
        """(codes, attributs) de la tilemap entière du plan : s1 monde (rangées × largeur), s2 64 × 64, s3 64 × 64"""
        d = self.decor(s); L = d["liste_s%d" % plan]
        if plan == 1:
            nb = LARGEUR_S1[d["type_s1"]]; ny = (len(L) + nb - 1) // nb
            C = np.zeros((32 * ny, 32 * nb), np.int64); T = np.zeros_like(C)
            for j, b in enumerate(L):
                by, bx = divmod(j, nb)
                for k in range(64):
                    cel = struct.unpack_from(">H", self.b["bib_s1"], 128 * b + 2 * k)[0]
                    cx, cy = k >> 3, k & 7
                    for i in range(16):
                        code, at = struct.unpack_from(">HH", self.b["cel_s1"], 64 * cel + 4 * i)
                        r, c = by * 32 + cy * 4 + (i & 3), bx * 32 + cx * 4 + (i >> 2)
                        C[r, c] = code; T[r, c] = at
            return C, T
        bib, nb, tb, taille = (self.b["bib_s2"], 4, 16, 1024) if plan == 2 else (self.b["bib_s3"], 8, 8, 256)
        n = nb * tb; C = np.zeros((n, n), np.int64); T = np.zeros((n, n), np.int64)
        for j, b in enumerate(L[:nb * nb]):
            by, bx = divmod(j, nb)
            for k in range(tb * tb):
                code, at = struct.unpack_from(">HH", bib, b * taille + 4 * k)
                C[by * tb + k % tb, bx * tb + k // tb] = code; T[by * tb + k % tb, bx * tb + k // tb] = at
        return C, T
    def palettes(self, s, plan):
        h = self.decor(s)["pal_s%d" % plan]
        return [int(h[4 * i:4 * i + 4], 16) | 0xF000 for i in range(512)]
    def image_plan(self, s, plan):
        """tilemap entière : (indices palette·16 + pen, RGBA) ; alpha 0 = pen 15"""
        key = (s, plan)
        if key in self.cache: return self.cache[key]
        C, T = self.grille(s, plan); ts = {1: 8, 2: 16, 3: 32}[plan]
        P, lo = self.P[plan], self.lo[plan]
        idx = np.zeros((C.shape[0] * ts, C.shape[1] * ts), np.int32)
        for r in range(C.shape[0]):
            for c in range(C.shape[1]):
                k = C[r, c] - lo
                t = (P[k] if 0 <= k < len(P) else np.full((ts, ts), 15, np.uint8)).astype(np.int32)
                at = T[r, c]
                if at & 0x20: t = t[:, ::-1]
                if at & 0x40: t = t[::-1, :]
                idx[r * ts:(r + 1) * ts, c * ts:(c + 1) * ts] = (at & 0x1F) * 16 + t
        pal = np.array([couleur(m) for m in self.palettes(s, plan)], np.uint8)
        rgba = np.zeros(idx.shape + (4,), np.uint8); rgba[..., :3] = pal[idx]
        rgba[..., 3] = np.where((idx & 15) == 15, 0, 255)
        self.cache[key] = (idx, rgba); return idx, rgba

def ordre(lc):
    """plans du bas vers le haut d'après le contrôle CPS-B (MAME cps2) ; 0 = sprites, ignorés"""
    return [l for l in ((lc >> s) & 3 for s in (6, 8, 10, 12)) if l]

def ecran(D, s, regs, rows=None, rso=0, largeur=384, dx=0, plans=(1, 2, 3), s1_anneau=False, sans_repli=False, couverture=None):
    """composite des plans sur fond noir. regs = {plan: (X, Y)} déroulés (scroll1 : coordonnées du MONDE, sauf
    s1_anneau = registre modulo 512 appliqué au monde replié) ; rows : rowscroll (1024 mots) ; dx : élargissement."""
    out = np.zeros((224, largeur, 3), np.uint8); xs = np.arange(largeur) - dx
    lc = int(D.decor(s)["cpsb"][0][1:], 16) | 0x0E
    for p in ordre(lc):
        if p not in plans: continue
        idx, c = D.image_plan(s, p); H, W = idx.shape
        X, Y = regs[p]
        for y in range(224):
            ly = y + 16 + Y
            if p == 1:
                if s1_anneau: ly %= H
                if not (0 <= ly < H): continue
                cx = xs + 64 + X
                if s1_anneau: cx = cx % W
                ok = (cx >= 0) & (cx < W)
                px = np.zeros((largeur, 4), np.uint8); px[ok] = c[ly, cx[ok]]
            else:
                sx = X + (int(rows[(y + 16 + rso) & 0x3FF]) if (rows is not None and p == 2) else 0)
                cx = xs + 64 + sx
                if sans_repli and p == 2:    # 16:9 : le bord de la tilemap de 1024 px n'est pas un bord peint (repli)
                    x0 = (X + 64 + int(rows[(112 + 16 + rso) & 0x3FF]) if rows is not None else X + 64) // W * W
                    px = np.zeros((largeur, 4), np.uint8); ok = (cx >= x0) & (cx < x0 + W); px[ok] = c[ly % H, cx[ok] % W]
                else:
                    px = c[ly % H, cx % W]
            m = px[:, 3] > 0; out[y, m] = px[m, :3]
            if couverture is not None: couverture[y] |= m
    return out
