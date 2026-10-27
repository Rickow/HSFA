"""Noms de la barre de vie (HUD) des 4 persos MAX, 64x16 (4 tuiles), au style des noms d'Upper (2026-10-17, demande 1 de
l'agent d'intégration HSFA). Upper : descripteur 0x12CE9C-0x12D470 : code = T_95C700[ID] (u16, rangée JP puis US à
+$50, choix par $90(A5)), attribut #$316 (palette $16, 4 tuiles), x = T_95C7A0[ID] (J1) / T_95C840[ID] (J2), y = 35.
Tuiles : hsfa_plans.bin, index = code + $1C00 + $8000 (comme les cartouches de noms_max.py).
Police en petites capitales : initiale haute (8 lignes, couleurs 3 en haut / 4 en bas), autres lettres sur 6 lignes ;
couleur de remplissage selon le RANG : 2e lettre 3, suivantes 2 (relevé sur les 40 noms) ; contour 0, transparent 15.
Lettres découpées par COMPOSANTES CONNEXES du remplissage (2/3/4), contour 0 rattaché à la composante la plus proche ;
I et Y majuscules absents d'Upper : I = fût gauche du K ; Y dessiné au style du V de VEGA (JP).
Positions mesurées sur tous les noms d'Upper : J1 x = 3 − (1re colonne du texte), J2 x = 381 − (dernière colonne).
Sortie ~/.cache/sfa3max/converti/noms/hud_noms.bin (4 tuiles par perso, ordre pl26-pl29, brut CPS2 comme noms.bin) et
hud_noms.json (code local, attribut, x J1 / J2 ; même nom en JP et en US)."""
import os, sys, struct, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx_fork import decode
RO5 = os.path.join(os.environ.get("ANTHOLOGY_DIR", "anthology_extract"), "decompressed", "ro5_usa_prog68k.bin")
PLANS = os.path.join(os.environ.get("HSFA_WORK", "work"), "mame_ro5", "hsfa_plans.bin")
B = open(RO5, "rb").read(); Pl = open(PLANS, "rb").read(); X = 0x1F0000
US = {0x00: "RYU", 0x01: "KEN", 0x02: "AKUMA", 0x03: "CHARLIE", 0x05: "ADON", 0x06: "SODOM", 0x07: "GUY", 0x08: "BIRDIE",
      0x09: "ROSE", 0x0B: "SAGAT", 0x0C: "DAN", 0x0D: "SAKURA", 0x0E: "ROLENTO", 0x0F: "DHALSIM", 0x10: "ZANGIEF",
      0x11: "GEN", 0x15: "BALROG", 0x16: "CAMMY", 0x19: "BLANKA", 0x1B: "CODY", 0x1D: "KARIN", 0x1E: "JULI", 0x1F: "JUNI",
      0x20: "GUILE", 0x18: "E.HONDA", 0x0A: "M.BISON"}
JP = {0x02: "GOUKI", 0x03: "NASH", 0x0A: "VEGA"}
NOMS = {"pl26": "EAGLE", "pl27": "MAKI", "pl28": "YUN", "pl29": "INGRID"}


def image(code):
    g = code + 0x1C00 + 0x8000
    return np.hstack([decode(Pl[(g + k) * 128:(g + k + 1) * 128]) for k in range(4)])


def composantes(im):
    """étiquettes des composantes connexes (8-voisinage) du remplissage, triées de gauche à droite"""
    lab = np.zeros(im.shape, int); n = 0
    for y0 in range(16):
        for x0 in range(64):
            if im[y0, x0] in (2, 3, 4) and not lab[y0, x0]:
                n += 1; pile = [(y0, x0)]; lab[y0, x0] = n
                while pile:
                    y, x = pile.pop()
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            v, u = y + dy, x + dx
                            if 0 <= v < 16 and 0 <= u < 64 and im[v, u] in (2, 3, 4) and not lab[v, u]:
                                lab[v, u] = n; pile.append((v, u))
    ordre = sorted(range(1, n + 1), key=lambda k: np.argwhere(lab == k)[:, 1].min())
    return lab, ordre


def glyphes():
    G = {}
    for off, D in ((0x50, US), (0, JP)):
        T = struct.unpack_from("<40H", B, 0x95C700 - X + off)
        for i, txt in D.items():
            im = image(T[i]); lab, ordre = composantes(im)
            lettres = [c for c in txt]
            if len(ordre) != len(lettres): continue
            pts = {k: np.argwhere(lab == k) for k in ordre}
            proprio = np.zeros(im.shape, int)
            for y, x in np.argwhere(im == 0):                     # contour -> composante la plus proche
                proprio[y, x] = min(ordre, key=lambda k: np.abs(pts[k] - (y, x)).max(axis=1).min())
            for r, (c, k) in enumerate(zip(lettres, ordre)):
                if c == ".": continue
                m = (lab == k) | (proprio == k); cols = np.where(m.any(axis=0))[0]
                g = np.where(m, im, 15)[:, cols.min():cols.max() + 1]
                G.setdefault(("C" if r == 0 else "m") + c, g)
    # majuscules absentes : I = fût gauche du K ; Y = haut du V (VEGA) + fût du I
    k = G["CK"]; G["CI"] = k[:, :3].copy(); G["CI"][11, 2] = 0 if G["CI"][11, 2] != 15 else 15
    motif = ["330    330", "330    330", "0330  3300", " 03333300 ", "   0440   ", "    440   ", "    440   ", "    000   "]
    y = np.full((16, 10), 15, np.uint8)                      # Y dessiné au style du V (bras 3, fût 4, contour 0)
    for r, l in enumerate(motif):
        for c, ch in enumerate(l):
            if ch != " ": y[8 + r, c] = int(ch)
    G["CY"] = y
    return G


def couleur(g, rang):
    """remplissage selon le rang de la lettre (initiale : inchangée ; 2e : 3 ; suivantes : 2)"""
    if rang == 0: return g
    g = g.copy(); g[np.isin(g, (2, 3, 4))] = 3 if rang == 1 else 2; return g


def compose(nom, G):
    parts = [couleur(G[("C" if r == 0 else "m") + c], r) for r, c in enumerate(nom)]
    w = sum(p.shape[1] for p in parts) + (len(parts) - 1)        # 1 colonne d'écart
    assert w <= 62, "%s : %d px" % (nom, w)
    im = np.full((16, 64), 15, np.uint8); x = (64 - w) // 2
    for p in parts:
        sub = im[:, x:x + p.shape[1]]; m = p != 15; sub[m] = p[m]; x += p.shape[1] + 1
    cols = np.where((im != 15).any(axis=0))[0]
    return im, int(cols.min()), int(cols.max())


def main():
    G = glyphes(); out = {}; tuiles = []
    for pl, nom in NOMS.items():
        im, a, b = compose(nom, G); code = len(tuiles)
        tuiles += [im[:, 16 * k:16 * k + 16] for k in range(4)]
        out[pl] = {"nom": nom, "code_local": code, "attribut": 0x316, "x_J1": 3 - a, "x_J2": 381 - b, "y": 35,
                   "colonnes_texte": [a, b], "langues": "JP et US identiques"}
    d = os.path.expanduser("~/.cache/sfa3max/converti/noms"); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "hud_noms.bin"), "wb") as f:
        for t in tuiles: f.write(bytes(int(t[y, 2 * j]) | (int(t[y, 2 * j + 1]) << 4) for y in range(16) for j in range(8)))
    json.dump(out, open(os.path.join(d, "hud_noms.json"), "w"), indent=1, ensure_ascii=False)
    return out, tuiles, G


if __name__ == "__main__":
    out, t, G = main()
    print(sorted(G)); print({k: (v["nom"], v["x_J1"], v["x_J2"]) for k, v in out.items()})
