"""« WINNER:<nom> » vertical de l'écran de victoire d'Upper pour les 4 persos MAX (2026-10-18, structure trouvée par
l'agent d'intégration HSFA). Upper (ro5, adresses PS2) : structure rel16 0x966740 (48 mots d'en-tête -> pas d'animation
de 8 o : u16 $4001, u16 attr, u32 frame), index = T_616850[ID] (0x616850, 2 rangées de $28 : rangée 1 noms JP (GOUKI),
rangée 2 si $90(A5) ≠ 0, noms US (AKUMA)) ; frame type $0C : frise verticale « WINNER: » ($091F, 1×3 tuiles, attr $201C)
+ nom (1 × h tuiles, attr (h−1) << 12 | $1C), répétée ; police verticale : lettres empilées, séparées par des rangées
transparentes. Banque : tuile = code + $1C00 + $8000 dans hsfa_plans.bin (= règle des noms).
Lettres découpées dans RYU (0), KEN (1), GOUKI (2), DAN (12), ROLENTO (14), AKUMA (27) ; noms MAX identiques en JP et US.
Sorties (<racine SFA3MAX_CACHE>/converti/winner_noms/) : tuiles.bin (brut CPS2, 2 rangées de 16 : nom k en colonne k,
codes local k + 16·y), winner_noms.json, apercu.png ; avec « source » : winner_noms_max.s (disposition image, après
portraits_fork.py qui pose code_global).
Usage : python winner_noms_max.py [source]"""
import os, sys, struct, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx_fork import decode
import paths
RO5 = os.path.join(os.environ.get("ANTHOLOGY_DIR", "anthology_extract"), "decompressed", "ro5_usa_prog68k.bin")
PLANS = os.environ.get("HSFA_PLANS", __import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "mame_ro5", "hsfa_plans.bin"))
RB, H = 0x1F0000, 0x966740
SOURCES = {0: "RYU", 1: "KEN", 2: "GOUKI", 12: "DAN", 14: "ROLENTO", 27: "AKUMA", 8: "BIRDIE"}   # entrées de 0x966740
# lettres de 5 rangées, 1 rangée d'écart ; les noms serrés emploient des variantes de 4 rangées (BIRDIE : I, D) : on les prend
# pour gagner une tuile quand il le faut (INGRID : 2 tuiles comme BIRDIE)
NOMS = {"pl26": (0x26, "EAGLE"), "pl27": (0x27, "MAKI"), "pl28": (0x2D, "YUN"), "pl29": (0x2E, "INGRID")}
B = open(RO5, "rb").read(); D = open(PLANS, "rb").read()
tuile = lambda c: decode(D[(0x8000 + c + 0x1C00) * 128:(0x8000 + c + 0x1C00) * 128 + 128])
HDR = struct.unpack_from("<48h", B, H - RB)


def entree(k):
    a = H + HDR[k]; w0, at = struct.unpack_from("<HH", B, a - RB); p = struct.unpack_from("<I", B, a - RB + 4)[0]
    o = p - RB; t, T, n1, z, pos = struct.unpack_from("<HHHHI", B, o); assert t == 0x0C
    objs = [struct.unpack_from("<HH", B, o + 12 + 4 * j) for j in range(n1 + 1)]
    return {"pas": (w0, at), "frame": p, "T": T, "n": n1 + 1, "positions": pos, "objets": objs}


def bloc(c, at):
    h = ((at >> 12) & 15) + 1
    return np.vstack([tuile(c + 16 * y) for y in range(h)])


def glyphes():
    G, ecarts = {}, []
    for k, nom in SOURCES.items():
        e = entree(k); c, at = e["objets"][1]; im = bloc(c, at); plein = (im != 15).any(axis=1)
        spans, y = [], 0
        while y < im.shape[0]:
            if not plein[y]: y += 1; continue
            y0 = y
            while y < im.shape[0] and plein[y]: y += 1
            spans.append((y0, y))
        assert len(spans) == len(nom), (nom, spans)
        ecarts += [b[0] - a[1] for a, b in zip(spans, spans[1:])]
        for ch, (y0, y1) in zip(nom, spans):
            G.setdefault(ch, [])
            if not any(g.shape[0] == y1 - y0 for g in G[ch]): G[ch].append(im[y0:y1])
    ecart = max(set(ecarts), key=ecarts.count)
    debut = {k: (lambda im: int(np.argmax((im != 15).any(axis=1))))(bloc(*entree(k)["objets"][1])) for k in SOURCES}
    return G, ecart, max(set(debut.values()), key=list(debut.values()).count)


def compose(nom, G, ecart, y0):
    choix = [max(G[c], key=lambda g: g.shape[0]) for c in nom]
    haut = lambda ch: sum(g.shape[0] for g in ch) + ecart * (len(ch) - 1) + y0
    h0 = -(-haut(choix) // 16)
    for i, c in enumerate(nom):                         # variantes courtes tant qu'on peut gagner une tuile
        if haut(choix) <= 16 * (h0 - 1): break
        court = min(G[c], key=lambda g: g.shape[0])
        if court.shape[0] < choix[i].shape[0] and haut(choix) - (choix[i].shape[0] - court.shape[0]) > 0:
            essai = choix[:i] + [court] + choix[i + 1:]
            if any(min(G[x], key=lambda g: g.shape[0]).shape[0] < 5 for x in nom): choix = essai
    if haut(choix) > 16 * (h0 - 1): choix = [max(G[c], key=lambda g: g.shape[0]) for c in nom]   # rien gagné : lettres pleines
    parts = []
    for i, c in enumerate(nom):
        parts.append(choix[i])
        if i + 1 < len(nom): parts.append(np.full((ecart, 16), 15, np.uint8))
    txt = np.vstack(parts); h = -(-(txt.shape[0] + y0) // 16)
    blk = np.full((16 * h, 16), 15, np.uint8); blk[y0:y0 + txt.shape[0]] = txt
    return blk, h


def modele(h):
    """1re entrée (0-30) dont le nom a h tuiles"""
    for k in range(31):
        e = entree(k)
        if ((e["objets"][1][1] >> 12) & 15) + 1 == h: return k, e
    raise KeyError(h)


def main():
    G, ecart, y0 = glyphes(); out = {}
    tuiles = [np.full((16, 16), 15, np.uint8) for _ in range(64)]          # 4 rangées de 16 au plus
    hmax = 0
    for col, (pl, (uid, nom)) in enumerate(NOMS.items()):
        blk, h = compose(nom, G, ecart, y0); hmax = max(hmax, h)
        for y in range(h): tuiles[col + 16 * y] = blk[16 * y:16 * y + 16]
        k, e = modele(h)
        out[pl] = {"id": "0x%02X" % uid, "nom": nom, "hauteur_tuiles": h, "code_local": col,
                   "attr_nom": "0x%04X" % ((h - 1) << 12 | 0x1C),
                   "modele": {"entree": k, "frame": "0x%X" % e["frame"], "pas": "%04x %04x" % e["pas"], "T": e["T"], "n": e["n"],
                              "positions": "0x%X" % e["positions"], "objets": ["%04x/%04x" % o for o in e["objets"]]}}
    tuiles = tuiles[:16 * hmax]
    d = os.path.join(paths.CACHE, "converti", "winner_noms"); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "tuiles.bin"), "wb") as f:
        for t in tuiles: f.write(bytes(int(t[y, 2 * j]) | (int(t[y, 2 * j + 1]) << 4) for y in range(16) for j in range(8)))
    json.dump(out, open(os.path.join(d, "winner_noms.json"), "w"), indent=1, ensure_ascii=False)
    from PIL import Image
    a = np.vstack([np.hstack(tuiles[16 * r:16 * r + 4]) for r in range(hmax)]); g = np.where(a == 15, 255, 40 + 14 * a).astype(np.uint8)
    Image.fromarray(g).resize((g.shape[1] * 6, g.shape[0] * 6), Image.NEAREST).save(os.path.join(d, "apercu.png"))
    for pl, v in out.items(): print(pl, v["nom"], "h", v["hauteur_tuiles"], "local", v["code_local"], "modèle", v["modele"]["entree"])
    print("écart", ecart, "début", y0, "tuiles", len(tuiles), "->", d)


def source_s():
    import gfx_fork as GF
    d = os.path.join(paths.CACHE, "converti", "winner_noms"); J = json.load(open(os.path.join(d, "winner_noms.json")))
    G0 = GF.EXT0 + os.path.getsize(GF.HSFA_GFX) // 128 + os.path.getsize(os.path.join(paths.CACHE, "fork", "max_gfx.bin")) // 128
    PB1 = 0xA60C + ((G0 - 0xA60C) % 16)
    plan2 = lambda g: PB1 + (g - G0) - 0x1C00
    sw = lambda v: "$%08X" % (((v & 0xFFFF) << 16) | (v >> 16))
    L = ["; « WINNER:<nom> » vertical des persos MAX (structure 0x966740) — généré par convert/winner_noms_max.py",
         "; DISPOSITION IMAGE (longs à moitiés échangées) ; G0 = $%X, PB1 = $%X : code = PB1 + (G − G0) − $1C00" % (G0, PB1), ""]
    for pl, v in J.items():
        uid = int(v["id"], 16); g = int(v["code_global"][1:], 16); c = plan2(g); m = v["modele"]
        assert 0 <= g - G0 < 0x2000
        objs = []
        for k, o in enumerate(m["objets"]):
            code, attr = (int(x, 16) for x in o.split("/"))
            if k % 2: code, attr = c, int(v["attr_nom"], 16)
            objs.append((code, attr))
        w0, at = (int(x, 16) for x in m["pas"].split())
        L += ["        even", "MAXWIN_PAS_%02X:            ; pas d'animation (entrée 48+ de 0x966740), modèle %d" % (uid, m["entree"]),
              "        dc.w    $%04X, $%04X" % (w0, at), "        dc.w    (MAXWIN_%02X)&$ffff, (MAXWIN_%02X)>>16" % (uid, uid),
              "MAXWIN_%02X:                ; WINNER:%s, nom G $%X (h = %d)" % (uid, v["nom"], g, v["hauteur_tuiles"]),
              "        dc.w    $000C, %d, %d, 0" % (m["T"], m["n"] - 1), "        dc.l    %s" % sw(int(m["positions"], 16))]
        L += ["        dc.w    $%04X, $%04X" % o for o in objs]
    open(os.path.join(d, "winner_noms_max.s"), "w").write("\n".join(L) + "\n")
    print("écrit winner_noms_max.s ; codes", {v["nom"]: "$%04X" % plan2(int(v["code_global"][1:], 16)) for v in J.values()})


if __name__ == "__main__":
    source_s() if sys.argv[1:] == ["source"] else main()
