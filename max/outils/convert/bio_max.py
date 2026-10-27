"""Illustration de la BIO (écran d'histoire de l'Arcade) des persos MAX au format des fichiers natifs d'Upper, 2026-10-17.
Upper : table par ID PS2 0x628470 (T_PERSO) = (fichier graphique, fichier d'animation), Ryu (419, 486) ; le chargeur
natif pose $C0BC(A5). Fichier d'animation (modèle work/cps2/anims/f486.bin, lu seulement), petit-boutiste, pointeurs
relatifs à LOAD_BASE = $B83800 :
  +0      u16 0x0608, u16 9 (identiques dans les 36 fichiers 486-521)
  +4      48 palettes de 16 mots (format module : 0x0RGB, mot 15 = 0) = 6 couleurs × 8 ; palette Upper 8v + r =
          palette PSP 20 + 8v + r de opXX_e.pac (contrôle : 48 / 48 identiques chez Ryu, voir valider())
  +0x604  u16 0, u16 9, puis UN pas : u16 $40FF (fin), u16 0, u32 -> frame du portrait
  +0x610  5 frames de type 2 à la suite : u16 2, T (Σ tuiles), n−1, 9 ; u32 -> positions ; n × (u16 code local,
          u16 attributs : (h−1) << 12 | (w−1) << 8 | palette / miroirs) ; puis les tables de positions (s16 x, y) :
          0, 1 = bandes latérales (codes 1-9, palette 27) : IDENTIQUES dans les 36 fichiers -> recopiées de Ryu ;
          2, 3 = bandeaux (avec le nom) = frames 2 / 3 du pac PSP (case = une tuile 16×16), x = col·16 − a, y = lig·16 − c ;
          4    = portrait = calques PSP 4, 5, 6… (jusqu'à la bande suivante) mis bout à bout, palettes 0/1/2 :
                 ancres du 2e jeu de frames du pac (le 1er est décalé) : x = col·16 − a, y = lig·16 − c (c signé),
                 exact sur Sagat, Ken, Chun-Li, Adon ; ordre des calques = celui du 1er jeu (palette 0, 1, 2).
Graphismes : table u32 code local -> tuile globale (format banques_hx/f4xx.bin) ; codes 1-9 = ceux de Ryu (bandes
latérales), codes 16 et suivants = tuiles neuves (tuiles.bin, même numérotation locale) ; leurs entrées valent
0x40000000 | code local, à remplacer par la tuile globale à l'intégration.
Sorties : ~/.cache/sfa3max/converti/plXX/bio/{anim_bio.bin, tuiles.bin, table_tuiles.bin, bio.json, rendu.png}.
Usage : python bio_max.py [valider]"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from portraits_max import Sortie, charger
OP = os.path.expanduser("~/.cache/sfa3max/data/textes/op%02x_e.pac")
MODELE = __import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "cps2", "anims", "f486.bin")
BANQUE_RYU = __import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "mame_ro5", "banques_hx", "f419.bin")
B = 0xB83800
NOMS = {0x26: "pl26", 0x27: "pl27", 0x28: "pl28", 0x29: "pl29"}


def lire_modele(d):
    o, F = 0x610, []
    while o < len(d) - 12 and struct.unpack_from("<H", d, o)[0] == 2:
        _, T, n1, w3 = struct.unpack_from("<4H", d, o); p = struct.unpack_from("<I", d, o + 8)[0] - B
        F.append({"T": T, "w3": w3, "objs": [struct.unpack_from("<2H", d, o + 12 + 4 * k) for k in range(n1 + 1)],
                  "pos": [struct.unpack_from("<2h", d, p + 4 * k) for k in range(n1 + 1)]})
        o += 12 + 4 * (n1 + 1)
    return F


def palettes_upper(ec):
    out = b""
    for k in range(20, 68):
        p = ec.P_brut(k); w = []
        for r in range(15):
            v = struct.unpack_from("<H", p, 2 * (r + 1))[0]
            w.append(((v & 31) >> 1) << 8 | (((v >> 5) & 31) >> 1) << 4 | ((v >> 10) & 31) >> 1)
        out += struct.pack("<16H", *w, 0)
    return out


def calques_portrait(ec):
    """calques du portrait : ORDRE du 1er jeu (frames 4… : palette 0, 1, 2…, = ordre des objets d'Upper), ANCRES du 2e jeu
    (même calque après les 2 bandes et les 2 bandeaux du 2e jeu ; le 1er jeu est décalé, position de départ d'une
    animation PSP) : x = col·16 − a, y = lig·16 − c, exact sur Sagat, Ken, Chun-Li, Adon (toutes les tuiles)"""
    n, L1 = 4, []
    while n < len(ec.F) and not (ec.F[n]["w"] == 2 and ec.F[n]["h"] == 14): L1.append(n); n += 1
    L2 = list(range(n + 4, len(ec.F))); out = []
    for k in L1:
        cle = lambda f: (f["w"], f["h"], [c for c in f["cells"]])
        m = [j for j in L2 if cle(ec.F[j]) == cle(ec.F[k]) and j not in out]
        assert m, "calque %d sans homologue dans le 2e jeu" % k
        out.append(m[0])
    return out


def convertir(cid):
    ec = charger(OP % cid, (0, 1, 2)); M = open(MODELE, "rb").read(); FM = lire_modele(M)
    S = Sortie(); S.palette = lambda e, p: p; S.tuiles = [None] * 16          # codes 0-15 : bandes latérales (Ryu)
    def cal(n, dy=0):
        f = ec.F[n]; c = f["c"] & 0xFFFF; c -= 0x10000 if c & 0x8000 else 0     # c : s16 (Ingrid 0xFFF0 = −16)
        return S.calque(ec, n, 0, -f["a"], -c + dy)
    frames = [(FM[0]["objs"], FM[0]["pos"]), (FM[1]["objs"], FM[1]["pos"])]
    for n in (2, 3):
        o = cal(n); frames.append(([(c, a) for c, a, x, y in o], [(x, y) for c, a, x, y in o]))
    port = [x for n in calques_portrait(ec) for x in cal(n)]
    frames.append(([(c, a) for c, a, x, y in port], [(x, y) for c, a, x, y in port]))
    # fichier
    corps = bytearray(M[:4]) + palettes_upper(ec)
    assert len(corps) == 0x604
    tete = len(corps) + 12; offs = []
    o = tete
    for objs, _ in frames: offs.append(o); o += 12 + 4 * len(objs)
    pos_offs = []
    for _, pos in frames: pos_offs.append(o); o += 4 * len(pos)
    corps += M[0x604:0x60C] + struct.pack("<I", B + offs[4])
    for k, (objs, pos) in enumerate(frames):
        T = sum((((a >> 8) & 15) + 1) * (((a >> 12) & 15) + 1) for c, a in objs)
        corps += struct.pack("<4HI", 2, T, len(objs) - 1, 9, B + pos_offs[k])
        corps += b"".join(struct.pack("<2H", c, a) for c, a in objs)
    for _, pos in frames: corps += b"".join(struct.pack("<2h", x, y) for x, y in pos)
    # tuiles et table
    br = open(BANQUE_RYU, "rb").read()
    table = [0xFFFFFFFF] * len(S.tuiles)
    for c in range(1, 10): table[c] = struct.unpack_from("<I", br, 4 * c)[0]
    for c in range(16, len(S.tuiles)):
        if S.tuiles[c] is not None: table[c] = 0x40000000 | c
    tuiles = b"".join(bytes((15 - ((16 - t[2 * i]) % 16)) | ((15 - ((16 - t[2 * i + 1]) % 16)) << 4) for i in range(128))
                      if t else bytes([0xFF] * 128) for t in S.tuiles)
    return bytes(corps), tuiles, struct.pack("<%dI" % len(table), *table), frames, ec


def rendu(cid, frames, tuiles, palettes, var=0):
    from PIL import Image
    im = Image.new("RGB", (448, 256), (30, 30, 50))
    for k in (2, 3, 4):
        for (c, a), (x, y) in zip(*frames[k]):
            w = ((a >> 8) & 15) + 1; h = ((a >> 12) & 15) + 1; pl = (a & 0x1F) + 8 * var
            for by in range(h):
                for bx in range(w):
                    t = tuiles[(c + bx + 16 * by) * 128:(c + bx + 16 * by) * 128 + 128]
                    for q in range(256):
                        b = t[q // 2]; raw = (b >> 4) if q & 1 else b & 15
                        if raw == 15: continue
                        v = struct.unpack_from("<H", palettes, 32 * pl + 2 * raw)[0]
                        X, Y = 32 + x + 16 * bx + q % 16, 16 + y + 16 * by + q // 16
                        if 0 <= X < 448 and 0 <= Y < 256: im.putpixel((X, Y), (((v >> 8) & 15) * 17, ((v >> 4) & 15) * 17, (v & 15) * 17))
    return im


def valider():
    """Ryu (op00) : palettes octet pour octet = f486 ; bandeaux : mêmes positions de tuiles"""
    ec = charger(OP % 0, (0, 1, 2)); M = open(MODELE, "rb").read()
    print("palettes Ryu PSP 20-67 converties = f486 :", palettes_upper(ec) == M[4:0x604])
    FM = lire_modele(M)
    for n in (2, 3):
        S = Sortie(); S.palette = lambda e, p: p; f = ec.F[n]
        P = {(x + 16 * i, y) for c, a, x, y in S.calque(ec, n, 0, -f["a"], -(f["c"] & 0xFFFF)) for i in range(((a >> 8) & 15) + 1)}
        U = {(x + 16 * bx, y + 16 * by) for (c, a), (x, y) in zip(FM[n]["objs"], FM[n]["pos"])
             for by in range(((a >> 12) & 15) + 1) for bx in range(((a >> 8) & 15) + 1)}
        print("bandeau %d : %d tuiles PSP, %d Upper, positions communes %d" % (n, len(P), len(U), len(P & U)))


if __name__ == "__main__":
    if sys.argv[1:] == ["valider"]: valider(); sys.exit()
    for cid, pl in NOMS.items():
        corps, tuiles, table, frames, ec = convertir(cid)
        d = os.path.expanduser("~/.cache/sfa3max/converti/%s/bio" % pl); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "anim_bio.bin"), "wb").write(corps)
        open(os.path.join(d, "tuiles.bin"), "wb").write(tuiles)
        open(os.path.join(d, "table_tuiles.bin"), "wb").write(table)
        from PIL import Image
        pal = corps[4:0x604]; ims = [rendu(cid, frames, tuiles, pal, v) for v in range(6)]
        pl_ = Image.new("RGB", (448 * 3, 256 * 2))
        for v, im in enumerate(ims): pl_.paste(im, (448 * (v % 3), 256 * (v // 3)))
        pl_.save(os.path.join(d, "rendu.png"))
        info = {"taille": len(corps), "frames": [{"objets": len(o), "tuiles": sum((((a >> 8) & 15) + 1) for c, a in o)} for o, _ in frames],
                "calques_portrait": calques_portrait(ec), "tuiles_neuves": sum(1 for k in range(16, len(tuiles) // 128) if tuiles[128 * k:128 * k + 128] != bytes([0xFF] * 128)),
                "codes_locaux": len(tuiles) // 128, "T_fichier": [struct.unpack_from("<H", corps, o + 2)[0] for o in (0x610,)]}
        json.dump(info, open(os.path.join(d, "bio.json"), "w"), indent=1)
        print(pl, info)
