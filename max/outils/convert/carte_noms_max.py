"""Colonne de nom verticale de la CARTE DU MONDE d'Upper pour les 4 persos MAX (2026-10-18, demande HSFA : « RYU » chez
Eagle, « JULI&JUNI » chez Maki). Upper (ro5, adresses PS2) : frames de type $0A référencées par les listes par perso de
0x967F2A : u16 $0A, u16 T, u16 n−1, u16 attr ((h−1) << 12 | palette $10), [mot 0 d'alignement], u32 positions, n × u16
code : la MÊME tuile-nom (1 × h tuiles, code + 16·y) répétée n fois ; positions par hauteur : h 2 -> 0x9696BE (n 8),
h 3 -> 0x9696DE (6), h 4 -> 0x9696F6 (5). Police : nom pivoté, lettres EN CREUX (encre 15) dans une plaque pleine
(encre 0) ; banque : tuile = code + $1C00 + $8000 dans hsfa_plans.bin (règle des noms).
Les lettres (masques des creux) sont découpées dans les noms existants ; la plaque vient d'un nom natif de même
hauteur, creux rebouchés ; début et écart des lettres = ceux de ce modèle.
Sorties (<racine SFA3MAX_CACHE>/converti/carte_noms/) : tuiles.bin (brut CPS2 ; nom k en colonne k, code local k + 16·y),
carte_noms.json, apercu.png ; « source » : carte_noms_max.s (disposition image, après portraits_fork.py).
Usage : python carte_noms_max.py [source]"""
import os, sys, struct, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx_fork import decode
import paths
RO5 = os.path.join(os.environ.get("ANTHOLOGY_DIR", "anthology_extract"), "decompressed", "ro5_usa_prog68k.bin")
PLANS = os.environ.get("HSFA_PLANS", __import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "mame_ro5", "hsfa_plans.bin"))
RB = 0x1F0000
# frames natives (adresse PS2) -> nom
NATIFS = {0x968E84: "RYU", 0x968EA0: "KEN", 0x968EBC: "GOUKI", 0x968F34: "GUY", 0x968F80: "VEGA", 0x968FB0: "DAN",
          0x9690D8: "BALROG", 0x969140: "AKUMA", 0x969186: "GUILE", 0x968F50: "BIRDIE", 0x9690A6: "R.MIKA", 0x96902A: "GEN"}
NOMS = {"pl26": (0x26, "EAGLE"), "pl27": (0x27, "MAKI"), "pl28": (0x2D, "YUN"), "pl29": (0x2E, "INGRID"),
        "pl29?": (0x2E, "?")}          # (2026-10-25, R8-bis : Ingrid garde « ? » comme sur PSP, fiche « FROM: ? »)
# « ? » absent des noms natifs : dessiné à la main dans le style de la police (traits de 2 px, 8 de large × 10 de haut),
# en coordonnées de la lettre (y vers le bas) ; rangé comme les lettres découpées (pivoté : rangée 0 = bord DROIT de la
# lettre, colonne 4 + y ; colonnes 0-1 = marge déjà à 15)
QUESTION = ["..####..", ".######.", "##....##", ".....##.", "....##..", "...##...", "...##...", "........", "...##...", "...##..."]
def glyphe_question():
    g = np.zeros((8, 16), bool); g[:, 0:2] = True
    for y, rang in enumerate(QUESTION):
        for x, c in enumerate(rang):
            if c == "#": g[7 - x, 4 + y] = True
    return g
B = open(RO5, "rb").read(); D = open(PLANS, "rb").read()
tuile = lambda c: decode(D[(0x8000 + c + 0x1C00) * 128:(0x8000 + c + 0x1C00) * 128 + 128])


def frame(p):
    o = p - RB; t, T, n1, at = struct.unpack_from("<HHHH", B, o); assert t == 0x0A
    q = o + 8
    if q % 4: q += 2                                    # mot d'alignement avant le long
    pos = struct.unpack_from("<I", B, q)[0]; codes = struct.unpack_from("<%dH" % (n1 + 1), B, q + 4)
    return {"frame": p, "T": T, "n": n1 + 1, "attr": at, "h": ((at >> 12) & 15) + 1, "positions": pos, "code": codes[0]}


def bloc(f): return np.vstack([tuile(f["code"] + 16 * y) for y in range(f["h"])])


def segments(im):
    """lettres = rangées contenant un creux (encre 15) entre les colonnes de la plaque"""
    plaque = (im == 0).any(axis=0); c0 = int(np.argmax(plaque)); c1 = len(plaque) - int(np.argmax(plaque[::-1]))
    creux = ((im[:, c0:c1] == 15) & (im[:, c0:c1] != 0)).any(axis=1)
    rangs_plaque = (im[:, c0:c1] == 0).any(axis=1)
    creux &= rangs_plaque
    spans, y = [], 0
    while y < len(creux):
        if not creux[y]: y += 1; continue
        y0 = y
        while y < len(creux) and creux[y]: y += 1
        spans.append((y0, y))
    return spans, c0, c1


def lettres():
    G, ordre = {}, None
    for p, nom in NATIFS.items():
        f = frame(p); im = bloc(f); sp, c0, c1 = segments(im)
        lets = [ch for ch in nom if ch not in " "]
        assert len(sp) == len(lets), (nom, sp)
        if ordre is None:                               # sens de lecture : GUY / GEN commencent tous deux par G
            g1, g2 = (segments(bloc(frame(q)))[0] for q in (0x968F34, 0x96902A))
            m = lambda im_, s: (bloc(frame(im_))[s[0]:s[1]] == 15)
            haut = np.array_equal(m(0x968F34, g1[0]), m(0x96902A, g2[0]))
            ordre = "haut" if haut else "bas"
        if ordre == "bas": sp = sp[::-1]
        for ch, (y0, y1) in zip(lets, sp): G.setdefault(ch, (im[y0:y1] == 15))
    return G, ordre


def modele(h):
    for p in NATIFS:
        f = frame(p)
        if f["h"] == h: return p, f
    raise KeyError(h)


def compose(nom, G, ordre):
    if "?" in nom and "?" not in G: G["?"] = glyphe_question()
    for h in (2, 3, 4):
        p, f = modele(h); im = bloc(f); sp, c0, c1 = segments(im)
        debut = sp[0][0] if ordre == "haut" else 16 * h - sp[-1][1]
        ecarts = [b[0] - a[1] for a, b in zip(sp, sp[1:])]; ecart = max(set(ecarts), key=ecarts.count)
        lets = [G[c] for c in nom]; L = sum(g.shape[0] for g in lets) + ecart * (len(lets) - 1)
        if debut + L <= 16 * h - debut: break
    out = im.copy(); zone = out[:, c0:c1]
    rangs = (zone == 0).any(axis=1)
    zone[rangs] = np.where(zone[rangs] == 15, 0, zone[rangs])         # creux rebouchés (plaque pleine)
    y = debut if ordre == "haut" else 16 * h - debut - L
    seq = lets if ordre == "haut" else lets[::-1]
    for g in seq:
        sub = out[y:y + g.shape[0], :]; sub[g] = 15; y += g.shape[0] + ecart   # masques pleine largeur (marges déjà à 15)
    return out, h, p, f


def main():
    G, ordre = lettres(); out = {}; tuiles = [np.full((16, 16), 15, np.uint8) for _ in range(64)]; hmax = 0
    for col, (pl, (uid, nom)) in enumerate(NOMS.items()):
        im, h, p, f = compose(nom, G, ordre); hmax = max(hmax, h)
        for y in range(h): tuiles[col + 16 * y] = im[16 * y:16 * y + 16]
        out[pl] = {"id": "0x%02X" % uid, "nom": nom, "hauteur_tuiles": h, "code_local": col,
                   "modele": {"frame": "0x%X" % p, "nom": NATIFS[p], "T": f["T"], "n": f["n"], "attr": "0x%04X" % f["attr"],
                              "positions": "0x%X" % f["positions"]}}
    tuiles = tuiles[:16 * hmax]
    d = os.path.join(paths.CACHE, "converti", "carte_noms"); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "tuiles.bin"), "wb") as fo:
        for t in tuiles: fo.write(bytes(int(t[y, 2 * j]) | (int(t[y, 2 * j + 1]) << 4) for y in range(16) for j in range(8)))
    json.dump(out, open(os.path.join(d, "carte_noms.json"), "w"), indent=1, ensure_ascii=False)
    from PIL import Image
    a = np.vstack([np.hstack(tuiles[16 * r:16 * r + len(NOMS)]) for r in range(hmax)]); g = np.where(a == 15, 255, 40 + 14 * a).astype(np.uint8)
    Image.fromarray(np.rot90(g, -1 if ordre == "haut" else 1)).resize((g.shape[0] * 6, g.shape[1] * 6), Image.NEAREST).save(os.path.join(d, "apercu.png"))
    for pl, v in out.items(): print(pl, v["nom"], "h", v["hauteur_tuiles"], "modèle", v["modele"]["nom"])
    print("sens", ordre, "tuiles", len(tuiles), "->", d)


def source_s():
    import gfx_fork as GF
    d = os.path.join(paths.CACHE, "converti", "carte_noms"); J = json.load(open(os.path.join(d, "carte_noms.json")))
    G0 = GF.EXT0 + os.path.getsize(GF.HSFA_GFX) // 128 + os.path.getsize(os.path.join(paths.CACHE, "fork", "max_gfx.bin")) // 128
    PB1 = 0xA60C + ((G0 - 0xA60C) % 16)
    plan2 = lambda g: PB1 + (g - G0) - 0x1C00
    sw = lambda v: "$%08X" % (((v & 0xFFFF) << 16) | (v >> 16))
    L = ["; colonne de nom verticale de la carte du monde, persos MAX (frames $0A, listes 0x967F2A) — convert/carte_noms_max.py",
         "; DISPOSITION IMAGE (longs à moitiés échangées) ; G0 = $%X, PB1 = $%X : code = PB1 + (G − G0) − $1C00" % (G0, PB1), ""]
    for pl, v in J.items():
        uid = int(v["id"], 16); g = int(v["code_global"][1:], 16); c = plan2(g); m = v["modele"]
        assert 0 <= g - G0 < 0x2000
        lab = "MAXCARTE_%02X" % uid + ("_INCONNU" if v["nom"] == "?" else "")
        L += ["        cnop    0,4", "%s:              ; %s, nom G $%X (h = %d), frise du modèle %s" % (lab, v["nom"], g, v["hauteur_tuiles"], m["nom"]),
              "        dc.w    $000A, %d, %d, $%04X" % (m["T"], m["n"] - 1, int(m["attr"], 16)),
              "        dc.l    %s" % sw(int(m["positions"], 16)),
              "        dc.w    " + ", ".join(["$%04X" % c] * m["n"])]
    open(os.path.join(d, "carte_noms_max.s"), "w").write("\n".join(L) + "\n")
    print("écrit carte_noms_max.s ; codes", {v["nom"]: "$%04X" % plan2(int(v["code_global"][1:], 16)) for v in J.values()})


if __name__ == "__main__":
    source_s() if sys.argv[1:] == ["source"] else main()
