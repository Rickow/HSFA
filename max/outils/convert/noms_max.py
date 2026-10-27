"""Cartouches de nom de l'écran de sélection (police dégradée orange d'Upper, palette $1B) pour les 4 persos MAX.
Upper : tables de noms {u32 attr, u32 frame} × 40 ID, JP à 0x771B30 et US à 0x771C70 (fichier ro5) ; frame de type $0C
(16 o : u16 $0C, u16 largeur, 0, 0, u32 positions [0x965E6C + 4 (w-4)], u16 code, u16 attr ($w-1)1B) ; code local
(+$1C00 → plan2). Les lettres sont découpées dans les cartouches US existants (séparateur = colonne sans dégradé :
seulement contour 0 ou transparent), puis assemblées et centrées dans un bloc de w tuiles comme les originaux.
Sortie ~/.cache/sfa3max/converti/noms/ : noms.bin (tuiles brutes CPS2, 1 rangée de 16 par nom), noms.json."""
import os, sys, struct, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx_fork import decode
RO5 = os.path.join(os.environ.get("ANTHOLOGY_DIR", "anthology_extract"), "decompressed", "ro5_usa_prog68k.bin")
PLANS = __import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "mame_ro5", "hsfa_plans.bin")
US = 0x771C70
SOURCES = {0x00: "RYU", 0x01: "KEN", 0x02: "AKUMA", 0x0c: "DAN", 0x0e: "ROLENTO", 0x08: "BIRDIE", 0x11: "GEN"}
NOMS = {"pl26": "EAGLE", "pl27": "MAKI", "pl28": "YUN", "pl29": "INGRID"}
B = open(RO5, "rb").read(); D = open(PLANS, "rb").read()
def tuile(g): o = (g - 0x60000) * 128; return decode(D[o:o + 128])
def plaque(ID):
    a, p = struct.unpack_from("<II", B, US + 8 * ID); o = p - 0x1F0000
    t, n, _, _, ptr, code, attr = struct.unpack_from("<HHHHIHH", B, o); assert t == 0x0C
    w = ((attr >> 8) & 15) + 1; g = code + 0x1C00 + 0x68000
    return np.hstack([tuile(g + k) for k in range(w)])
def glyphes():
    G = {}
    for ID, nom in SOURCES.items():
        im = plaque(ID); sep = [((im[:, x] == 15) | (im[:, x] == 0)).all() for x in range(im.shape[1])]
        spans, x = [], 0
        while x < len(sep):
            if sep[x]: x += 1; continue
            x0 = x
            while x < len(sep) and not sep[x]: x += 1
            spans.append((x0, min(x + 1, len(sep))))          # + la colonne d'ombre à droite
        if len(spans) != len(nom): spans = spans[:-1]       # lettres collées en fin (ROLENTO : « TO ») : têtes seulement
        for ch, (x0, x1) in zip(nom, spans): G.setdefault(ch, im[:, x0:x1])
    return G
def compose(nom, G):
    txt = np.hstack([G[c] for c in nom]); w = -(-(txt.shape[1] + 8) // 16)
    blk = np.full((16, 16 * w), 15, np.uint8); x0 = (16 * w - txt.shape[1]) // 2
    sub = blk[:, x0:x0 + txt.shape[1]]; m = txt != 15; sub[m] = txt[m]
    return blk, w
def main():
    G = glyphes(); out = {}; tuiles = []
    for pl, nom in NOMS.items():
        blk, w = compose(nom, G)
        while len(tuiles) % 16 + w > 16: tuiles.append(np.full((16, 16), 15, np.uint8))
        code = len(tuiles)
        for k in range(w): tuiles.append(blk[:, 16 * k:16 * k + 16])
        out[pl] = {"nom": nom, "largeur_tuiles": w, "code_local": code, "attribut": ((w - 1) << 8) | 0x1B,
                   "frame_type_0C": {"positions": "0x%X (comme les originaux de largeur %d)" % (0x965E6C + 4 * (w - 4), w) if w >= 4 else None},
                   "tables_noms": "US 0x771C70 / JP 0x771B30 (fichier ro5), entrée ID"}
    while len(tuiles) % 16: tuiles.append(np.full((16, 16), 15, np.uint8))
    d = os.path.expanduser("~/.cache/sfa3max/converti/noms"); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "noms.bin"), "wb") as f:
        for t in tuiles: f.write(bytes(int(t[y, 2 * j]) | (int(t[y, 2 * j + 1]) << 4) for y in range(16) for j in range(8)))
    json.dump(out, open(os.path.join(d, "noms.json"), "w"), indent=1, ensure_ascii=False)
    return out, tuiles
# BANDEAU défilant (texte, police proportionnelle) : tables {u32 attr, u32 enregistrement} × 40 ID : J1 JP 0x7725B8,
# J1 US 0x7726F8, J2 JP 0x772838, J2 US 0x772978. Enregistrement : u16 $0A, u16 n, u16 n-1, u16 $1C (palette),
# [u16 0 d'alignement], u32 table de positions (n × (s16 −3, s16 x)), n × u16 caractère (ASCII + $80).
# Les positions ne dépendent que du motif (chasse 12, +8 après « 1P » et après le nom) : on reprend celles d'un nom
# existant de même motif (vérifié).
BANDEAU = {"pl26": ("EAGLE", "LE{p}EAGLE{p}EAGLE{p}EAGLE"), "pl27": ("MAKI", "MAKI{p}MAKI{p}MAKI{p}MAKI"),
           "pl28": ("YUN", "{p}YUN{p}YUN{p}YUN{p}YUN"), "pl29": ("INGRID", "{p}INGRID{p}INGRID{p}INGRID")}
TABLES_BANDEAU = {"J1_JP": (0x7725B8, "1P"), "J1_US": (0x7726F8, "1P"), "J2_JP": (0x772838, "2P"), "J2_US": (0x772978, "2P")}
def enregistrement(p):
    o = p - 0x1F0000; t, n, n1, at = struct.unpack_from("<HHHH", B, o); assert t == 0x0A
    q = o + 8; ptr = struct.unpack_from("<I", B, q)[0]
    if not 0x900000 <= ptr < 0xA00000: q += 2; ptr = struct.unpack_from("<I", B, q)[0]
    txt = "".join(chr(w - 0x80) for w in struct.unpack_from("<%dH" % n, B, q + 4))
    return n, at, ptr, txt
def bandeau():
    out = {}
    for pl, (nom, motif) in BANDEAU.items():
        out[pl] = {}
        for tab, (T, jp) in TABLES_BANDEAU.items():
            txt = motif.format(p=jp); masque = [i for i, c in enumerate(txt) if txt[i:i + 2] == jp]
            for idm in range(40):
                a, p = struct.unpack_from("<II", B, T + 8 * idm)
                try: n, at, ptr, txt_m = enregistrement(p)
                except Exception: continue
                if n == len(txt) and [i for i, c in enumerate(txt_m) if txt_m[i:i + 2] == jp] == masque: break
            else: raise SystemExit("pas de modèle pour %s %s" % (nom, tab))
            mots = [0x0A, n, n - 1, at]
            out[pl][tab] = {"texte": txt, "n": n, "palette": at, "positions": "0x%X (fichier ro5 0x%X, comme %s)" % (ptr, ptr - 0x1F0000, txt_m),
                            "mots_u16": ["%04x" % w for w in mots] + ["<u32 0x%X>" % ptr] + ["%04x" % (ord(c) + 0x80) for c in txt]}
    return out
if __name__ == "__main__":
    bd = bandeau(); d = os.path.expanduser("~/.cache/sfa3max/converti/noms")
    json.dump(bd, open(os.path.join(d, "bandeau.json"), "w"), indent=1, ensure_ascii=False)
    print({pl: {t: (v["texte"], v["n"], v["positions"][:8]) for t, v in x.items() if t in ("J1_US", "J2_US")} for pl, x in bd.items()})
    out, t = main(); print({k: (v["nom"], v["largeur_tuiles"], v["code_local"]) for k, v in out.items()}, len(t), "tuiles")
