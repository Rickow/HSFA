"""Graphismes de NOM des frises « 1P RYU 1P RYU… » d'Upper pour les 4 persos MAX (2026-10-18, « WINNER : RYU » chez Eagle).
Upper (fichier ro5, adresses PS2) : 4 tables {u32 attr, u32 frame} × 40 ID : 1P JP 0x9620B8, 1P US 0x9621F8, 2P JP 0x962338,
2P US 0x962478 ; frame de type $0C : u16 $0C, u16 T, u16 n−1, 0, u32 positions, n × (u16 code, u16 attr) = alternance
« 1P » (code $694, attr $001D ; « 2P » : $695 / $001E) et nom (code, attr (largeur−1) << 8 | palette) ; le nom est UN
graphisme par perso (Ryu $696 2 tuiles, Akuma US $6F8 4 tuiles…), aussi employé seul (frames 0x96F290… de la liste de
mots 0x96A970 : « WINNER : nom »). Banque : tuile = code + $1C00 + $68000 dans hsfa_plans.bin (règle des cartouches de
noms_max, vérifiée sur RYU / KEN / JULI&JUNI ; ⚠ hsfa_plans chargé en $3200000 depuis le lot 2b11 : seule la base change).
Police : lettres de 6 lignes (encres 2 / 1 / 0, dégradé), séparées par des colonnes transparentes ; les lettres sont
découpées dans les noms US existants, assemblées avec 2 px d'écart et centrées dans w tuiles.
Sorties (<racine SFA3MAX_CACHE>/converti/bandeau_noms/) : tuiles.bin (brut CPS2 4 bpp, une rangée de 16 tuiles par nom),
bandeau_noms.json (code local, largeur, attributs, frise modèle de même largeur par table : à recopier en changeant le
code du nom), apercu.png.
Usage : python bandeau_noms_max.py"""
import os, sys, struct, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx_fork import decode
import paths
RO5 = os.path.join(os.environ.get("ANTHOLOGY_DIR", "anthology_extract"), "decompressed", "ro5_usa_prog68k.bin")
PLANS = os.environ.get("HSFA_PLANS", __import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "mame_ro5", "hsfa_plans.bin"))
RB = 0x1F0000
TABLES = {"1P_JP": 0x9620B8, "1P_US": 0x9621F8, "2P_JP": 0x962338, "2P_US": 0x962478}
SOURCES = {0x00: "RYU", 0x01: "KEN", 0x02: "AKUMA", 0x03: "CHARLIE", 0x07: "GUY", 0x0C: "DAN"}   # table 1P US
NOMS = {"pl26": (0x26, "EAGLE"), "pl27": (0x27, "MAKI"), "pl28": (0x2D, "YUN"), "pl29": (0x2E, "INGRID")}
B = open(RO5, "rb").read(); D = open(PLANS, "rb").read()
tuile = lambda g: decode(D[(g - 0x60000) * 128:(g - 0x60000) * 128 + 128])


def frame(T, ID):
    a, p = struct.unpack_from("<II", B, T - RB + 8 * ID); o = p - RB
    t, tt, n1, z, pos = struct.unpack_from("<HHHHI", B, o); assert t == 0x0C
    objs = [struct.unpack_from("<HH", B, o + 12 + 4 * k) for k in range(n1 + 1)]
    return {"attr_table": a, "frame": p, "T": tt, "n": n1 + 1, "positions": pos, "objets": objs}


def graphisme(code, attr):
    w = ((attr >> 8) & 15) + 1
    return np.hstack([tuile(code + 0x1C00 + 0x68000 + k) for k in range(w)])


def glyphes():
    G = {}
    for ID, nom in SOURCES.items():
        f = frame(TABLES["1P_US"], ID); code, attr = f["objets"][1]
        im = graphisme(code, attr); vide = (im == 15).all(axis=0)
        spans, x = [], 0
        while x < im.shape[1]:
            if vide[x]: x += 1; continue
            x0 = x
            while x < im.shape[1] and not vide[x]: x += 1
            spans.append((x0, x))
        assert len(spans) == len(nom), (nom, spans)
        for ch, (x0, x1) in zip(nom, spans): G.setdefault(ch, im[:, x0:x1])
    return G


def compose(nom, G, ecart=2):
    parts = []
    for i, c in enumerate(nom):
        parts.append(G[c])
        if i + 1 < len(nom): parts.append(np.full((16, ecart), 15, np.uint8))
    txt = np.hstack(parts); w = -(-txt.shape[1] // 16)             # RYU : 30 px dans 2 tuiles
    blk = np.full((16, 16 * w), 15, np.uint8); x0 = (16 * w - txt.shape[1]) // 2
    blk[:, x0:x0 + txt.shape[1]] = txt
    return blk, w


def main():
    G = glyphes(); out = {}; tuiles = []
    for pl, (uid, nom) in NOMS.items():
        blk, w = compose(nom, G)
        while len(tuiles) % 16: tuiles.append(np.full((16, 16), 15, np.uint8))
        code = len(tuiles)
        for k in range(w): tuiles.append(blk[:, 16 * k:16 * k + 16])
        modeles = {}
        for tab, T in TABLES.items():                 # frise modèle : une entrée de la même table dont le nom a w tuiles
            for ID in range(40):
                f = frame(T, ID)
                if f["n"] >= 2 and ((f["objets"][1][1] >> 8) & 15) + 1 == w:
                    modeles[tab] = {"id_modele": ID, "frame": "0x%X" % f["frame"], "attr_table": "0x%08X" % f["attr_table"],
                                    "T": f["T"], "n": f["n"], "positions": "0x%X" % f["positions"],
                                    "objets": ["%04x/%04x" % o for o in f["objets"]]}
                    break
        out[pl] = {"id": "0x%02X" % uid, "nom": nom, "largeur_tuiles": w, "code_local": code,
                   "attr_nom_1P": "0x%04X" % ((w - 1) << 8 | 0x1D), "attr_nom_2P": "0x%04X" % ((w - 1) << 8 | 0x1E),
                   "frise_modele": modeles}
    while len(tuiles) % 16: tuiles.append(np.full((16, 16), 15, np.uint8))
    d = os.path.join(paths.CACHE, "converti", "bandeau_noms"); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "tuiles.bin"), "wb") as f:
        for t in tuiles: f.write(bytes(int(t[y, 2 * j]) | (int(t[y, 2 * j + 1]) << 4) for y in range(16) for j in range(8)))
    json.dump(out, open(os.path.join(d, "bandeau_noms.json"), "w"), indent=1, ensure_ascii=False)
    from PIL import Image
    rang = [np.hstack(tuiles[16 * r:16 * r + 16]) for r in range(len(tuiles) // 16)]
    a = np.vstack(rang)[:, :128]; g = np.where(a == 15, 255, 60 + 60 * a).astype(np.uint8)
    Image.fromarray(g).resize((g.shape[1] * 4, g.shape[0] * 4), Image.NEAREST).save(os.path.join(d, "apercu.png"))
    for pl, v in out.items(): print(pl, v["nom"], "largeur", v["largeur_tuiles"], "code local", v["code_local"],
                                   "modèles", {k: m["id_modele"] for k, m in v["frise_modele"].items()})
    print("écrit", d)


if __name__ == "__main__" and sys.argv[1:] != ["source"]:
    main()


# (2026-10-18, accord HSFA) frises en source 68K, DISPOSITION IMAGE (comme prepare_max.habillage : mots tels quels,
# longs à moitiés échangées) : 8 frames (4 persos × 1P / 2P ; JP et US identiques pour un nom MAX) + entrées des 4
# tables par ID. Code de frame = code_plan2(G) = PB1 + (G − G0) − $1C00 (max_cache : G0 = début de max_portraits_gfx,
# PB1 = $A60C + ((G0 − $A60C) mod 16)) ; G = code_global de bandeau_noms.json (posé par portraits_fork.py).
def source_s():
    import gfx_fork as GF
    d = os.path.join(paths.CACHE, "converti", "bandeau_noms"); J = json.load(open(os.path.join(d, "bandeau_noms.json")))
    G0 = GF.EXT0 + os.path.getsize(GF.HSFA_GFX) // 128 + os.path.getsize(os.path.join(paths.CACHE, "fork", "max_gfx.bin")) // 128
    PB1 = 0xA60C + ((G0 - 0xA60C) % 16)
    plan2 = lambda g: PB1 + (g - G0) - 0x1C00
    sw = lambda v: "$%08X" % (((v & 0xFFFF) << 16) | (v >> 16))
    L = ["; frises « 1P / 2P nom » des persos MAX (tables par ID 1P JP 0x9620B8, 1P US 0x9621F8, 2P JP 0x962338, 2P US 0x962478)",
         "; généré par convert/bandeau_noms_max.py — DISPOSITION IMAGE (longs à moitiés échangées, comme prepare_max.habillage)",
         "; G0 = $%X, PB1 = $%X : code = PB1 + (G − G0) − $1C00" % (G0, PB1), ""]
    entrees = {}
    for pl, v in J.items():
        uid = int(v["id"], 16); g = int(v["code_global"][1:], 16); c = plan2(g)
        assert 0 <= g - G0 < 0x2000
        for j, tab in (("1P", "1P_JP"), ("2P", "2P_JP")):
            m = v["frise_modele"][tab]; mu = v["frise_modele"][tab.replace("JP", "US")]
            assert (m["T"], m["n"], m["positions"]) == (mu["T"], mu["n"], mu["positions"]), (pl, tab)
            objs = []
            for k, o in enumerate(m["objets"]):
                code, attr = (int(x, 16) for x in o.split("/"))
                if k % 2: code = c; attr = int(v["attr_nom_%s" % j], 16)
                objs.append((code, attr))
            lab = "MAXBN_%02X_%s" % (uid, j)
            L += ["        even", "%s:                ; %s, %s : nom G $%X, frise de l'ID %d" % (lab, v["nom"], j, g, m["id_modele"]),
                  "        dc.w    $000C, %d, %d, 0" % (m["T"], m["n"] - 1), "        dc.l    %s" % sw(int(m["positions"], 16))]
            L += ["        dc.w    $%04X, $%04X" % o for o in objs]
            for t in ("JP", "US"):
                entrees[(j, t, uid)] = (int(v["frise_modele"]["%s_%s" % (j, t)]["attr_table"], 16), lab)
    L += ["", "; entrées des tables par ID (u32 attr, u32 frame), disposition image ; à poser aux ID $26 / $27 / $2D / $2E"]
    for j in ("1P", "2P"):
        for t in ("JP", "US"):
            for uid in (0x26, 0x27, 0x2D, 0x2E):
                at, lab = entrees[(j, t, uid)]
                L += ["MAXBN_E_%s_%s_%02X:   ; table %s %s, ID $%02X" % (j, t, uid, j, t, uid),
                      "        dc.l    %s" % sw(at), "        dc.w    (%s)&$ffff, (%s)>>16" % (lab, lab)]
    open(os.path.join(d, "bandeau_noms_max.s"), "w").write("\n".join(L) + "\n")
    print("écrit bandeau_noms_max.s ; G0 $%X PB1 $%X ; codes" % (G0, PB1), {v["nom"]: "$%04X" % plan2(int(v["code_global"][1:], 16)) for v in J.values()})


if __name__ == "__main__" and sys.argv[1:] == ["source"]:
    source_s()
