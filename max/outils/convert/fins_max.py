"""Fins des persos MAX (PSP endXX_e.pac) : extraction et inventaire (2026-10-07).

Contenu d'un endXX_e.pac (types d'entrée entre parenthèses) :
  0 (0x10)        carte de 64 x 192 cases u32 (3 plans de 64 x 64, tuiles 16x16) : décors des scènes.
                  case = drapeaux << 24 | GBIX << 8 | tuile ; 0x1700 = vide ; drapeaux : 0x80 posée,
                  0x10 miroir H, 0x20 miroir V, 0x40 (bords : rôle à établir).
  1..n (0x10000cGG) textures GBIX/PVRT 256x256 : format 1 = ARGB1555 linéaire (planche de 16x16 tuiles 16x16),
                  format 5 = 4 bpp (masques / dégradés). Les tuiles 16 bits n'ont presque toutes que <= 16 couleurs :
                  ce sont des tuiles à palette 16 couleurs « dépliées » -> conversion CPS2 sans perte.
  (0x1000019 / 0x2000019 / 0x4000019) frames / tuiles / palettes des SPRITES animés (format des écrans, case 16x16).
  (0x10003)       textes (scénario + fin), cf. textes_max.py.
  (0x20000)       script de scène = script de fin ARCADE réencodé (même bytecode que la ROM SFA3, mots
                  petit-boutistes ; opcode 0x11 : longueur +1, un mot ajouté, pointeur -> position dans la carte).
  (0x20001..0x20005) animations des sprites (pas, têtes, index, attributs ; cf. pas 20 octets du module).
Usage : python3 fins_max.py [26 27 28 29]  -> ~/.cache/sfa3max/converti/plXX/fin/"""
import os, sys, struct, json
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
from plpac import split
from PIL import Image

SRC = os.path.expanduser("~/.cache/sfa3max/data/textes")
OUT = os.path.expanduser("~/.cache/sfa3max/converti")
VIDE = 0x1700


def textures(E):
    """{GBIX: (format, tuple de pixels)} ; format 1 = ARGB1555 (256x256), 5 = 4 bpp"""
    tex = {}
    for t, d in E:
        if d[:4] != b"GBIX": continue
        g = d[8]; fmt = d[0x19]; w, h = struct.unpack_from("<HH", d, 0x1C)
        if fmt == 1: tex[g] = (1, struct.unpack_from("<%dH" % (w * h), d, 32))
        else: tex[g] = (fmt, tuple((b >> s) & 15 for b in d[32:32 + w * h // 2] for s in (0, 4)))
    return tex


def rgba(fmt, v):
    if fmt == 1: return ((v & 31) << 3, ((v >> 5) & 31) << 3, ((v >> 10) & 31) << 3, 255 if v & 0x8000 else 0)
    return (v * 17, v * 17, v * 17, 255)


def tuile(tex, g, t):
    """pixels (256 valeurs brutes) de la tuile t de la texture g"""
    fmt, px = tex[g]
    tx, ty = (t % 16) * 16, (t // 16) * 16
    return fmt, [px[(ty + y) * 256 + tx + x] for y in range(16) for x in range(16)]


def carte(E):
    d = E[0][1]
    return struct.unpack("<%dI" % (len(d) // 4), d)


def images(v):
    """rectangles de cases posées (composantes 4-connexes) : [(col, ligne, largeur, hauteur)]"""
    W, H = 64, len(v) // 64
    vu = set(); rects = []
    for i, x in enumerate(v):
        if x == VIDE or i in vu: continue
        pile = [i]; vu.add(i); cs = []
        while pile:
            k = pile.pop(); cs.append(k); c, r = k % W, k // W
            for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c2, r2 = c + dc, r + dr
                if 0 <= c2 < W and 0 <= r2 < H:
                    k2 = r2 * W + c2
                    if k2 not in vu and v[k2] != VIDE: vu.add(k2); pile.append(k2)
        cols = [k % W for k in cs]; rows = [k // W for k in cs]
        rects.append((min(cols), min(rows), max(cols) - min(cols) + 1, max(rows) - min(rows) + 1, len(cs)))
    return sorted(rects, key=lambda r: (r[1], r[0]))


def rendre(tex, v, rect):
    c0, r0, w, h = rect[:4]
    im = Image.new("RGBA", (w * 16, h * 16), (0, 0, 0, 0))
    for r in range(h):
        for c in range(w):
            x = v[(r0 + r) * 64 + c0 + c]
            if x == VIDE or ((x >> 8) & 0xFF) not in tex: continue
            fmt, px = tuile(tex, (x >> 8) & 0xFF, x & 0xFF)
            t = Image.new("RGBA", (16, 16)); t.putdata([rgba(fmt, p) for p in px])
            if x & 0x10000000: t = t.transpose(Image.FLIP_LEFT_RIGHT)
            if x & 0x20000000: t = t.transpose(Image.FLIP_TOP_BOTTOM)
            im.paste(t, (c * 16, r * 16))
    return im


def palettes_min(jeux):
    """regroupement glouton des jeux de couleurs (<= 16, transparent compris) en palettes de 16 : estimation"""
    pals = []
    for j in sorted(jeux, key=len, reverse=True):
        for p in pals:
            if len(p | j) <= 16: p |= j; break
        else: pals.append(set(j))
    return pals


def inventaire(n):
    E = split(open(os.path.join(SRC, "end%s_e.pac" % n), "rb").read())
    tex = textures(E); v = carte(E)
    out = os.path.join(OUT, "pl%s" % n, "fin"); os.makedirs(out, exist_ok=True)
    rects = images(v); info = {"images": [], "textures": {"%02x" % g: f for g, (f, _) in tex.items()}}
    tuiles = {}; trop = 0
    for k, rc in enumerate(rects):
        im = rendre(tex, v, rc); im.save(os.path.join(out, "image_%02d.png" % k))
        info["images"].append({"col": rc[0], "ligne": rc[1], "l": rc[2], "h": rc[3], "cases": rc[4]})
        c0, r0, w, h = rc[:4]
        for r in range(h):
            for c in range(w):
                x = v[(r0 + r) * 64 + c0 + c]
                if x == VIDE: continue
                key = x & 0xFFFF
                if key in tuiles or ((x >> 8) & 0xFF) not in tex: continue
                fmt, px = tuile(tex, (x >> 8) & 0xFF, x & 0xFF)
                cs = frozenset(p if (fmt != 1 or p & 0x8000) else 0 for p in px)   # transparent = 0
                tuiles[key] = cs
    jeux = [cs for cs in tuiles.values() if len(cs) <= 16]
    trop = sum(1 for cs in tuiles.values() if len(cs) > 16)
    pals = palettes_min(set(jeux))
    info.update({"tuiles_distinctes": len(tuiles), "tuiles_plus_de_16_couleurs": trop,
                 "palettes_estimees": len(pals)})
    json.dump(info, open(os.path.join(out, "fin.json"), "w"), indent=1)
    # planche des images
    ims = [Image.open(os.path.join(out, "image_%02d.png" % k)) for k in range(len(rects))]
    W = 2 * 384 + 8; x = y = rh = 0; pos = []
    for im in ims:
        if x + im.width > W: x = 0; y += rh + 8; rh = 0
        pos.append((x, y)); x += im.width + 8; rh = max(rh, im.height)
    pl = Image.new("RGBA", (W, y + rh), (48, 48, 48, 255))
    for im, p in zip(ims, pos): pl.alpha_composite(im, p)
    pl.save(os.path.join(out, "planche_images.png"))
    return info


if __name__ == "__main__":
    for n in (sys.argv[1:] or ["26", "27", "28", "29"]):
        i = inventaire(n)
        print("end%s : %d images, %d tuiles distinctes (%d à plus de 16 couleurs), ~%d palettes" % (
            n, len(i["images"]), i["tuiles_distinctes"], i["tuiles_plus_de_16_couleurs"], i["palettes_estimees"]))
        print("   ", [(r["col"], r["ligne"], r["l"], r["h"]) for r in i["images"]])
