"""Portraits des persos MAX au format convenu avec HSFA (note max-portraits.md) :
  portraits.bin           : tuiles 16x16 brutes CPS2 (4 bpp linéaire, quartet bas à gauche), numérotation locale ;
  portraits.json          : par famille de poses : objets (code local, attributs CPS2, x, y) = frame de type 8 avant le
                            +$1600 du constructeur, liste des poses et, pour chaque pose, l'entrée remplacée (index de la
                            table ro5 0x484C00 et adresse fichier de la frame actuellement en place pour l'ID visé) ;
  portraits_palettes.bin  : palettes 16 couleurs au format module (0x0RGB, mot 15 = n°) ; attributs bits 0-4 = n°.
Chaque calque PSP est découpé en bandes horizontales de tuiles non vides de même palette (largeur ≤ 16), codes
consécutifs par bande (bloc CPS2 : code + i) ; conversion pixel / palette identique aux persos (validée)."""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ecrans import Ecran
from portraits_upper import entree, frame8, OFFS
D = os.path.expanduser("~/.cache/sfa3max/data/textes/")
def tuiles_calque(ec, n, base):
    """-> {(col, ligne): (pixels PSP 256, palette absolue)} pour la frame n (cases 32 ou 16)"""
    fr = ec.F[n]; s = 32 if ec.case32 else 16; out = {}
    for k, cell in enumerate(fr["cells"]):
        if cell is None: continue
        idx, attr = cell; cx, cy = (k % fr["w"]) * (s // 16), (k // fr["w"]) * (s // 16)
        quads = ((0, 0), (0, 1), (1, 0), (1, 1)) if s == 32 else ((0, 0),)
        for q, (qx, qy) in enumerate(quads):
            t = ec.tile(idx * len(quads) + q)
            px = [t[y * 8 + x // 2] & 0xF if x % 2 == 0 else t[y * 8 + x // 2] >> 4 for y in range(16) for x in range(16)]
            if attr & 0x80: px = [px[y * 16 + 15 - x] for y in range(16) for x in range(16)]; qx = (s // 16 - 1) - qx
            if attr & 0x40: px = [px[(15 - y) * 16 + x] for y in range(16) for x in range(16)]; qy = (s // 16 - 1) - qy
            if any(px): out[(cx + qx, cy + qy)] = (px, base + (attr & 0x1F))
    return out
class Sortie:
    def __init__(s): s.tuiles, s.palettes, s.pal_idx = [], [], {}
    def palette(s, ec, p):
        cle = (id(ec), p)
        if cle not in s.pal_idx: s.pal_idx[cle] = len(s.palettes); s.palettes.append(ec.P_brut(p))
        return s.pal_idx[cle]
    def calque(s, ec, n, base, x0, y0, xmin=-10**6, xmax=10**6):
        T = {k: v for k, v in tuiles_calque(ec, n, base).items() if xmin <= x0 + 16 * k[0] and x0 + 16 * k[0] + 16 <= xmax}
        objs = []
        lignes = sorted({r for _, r in T})
        for r in lignes:
            cols = sorted(c for c, rr in T if rr == r); run = []
            def vide():
                if not run: return
                pal = T[(run[0], r)][1]; code = s.nouveau_bloc(len(run))
                for k, c in enumerate(run): s.tuiles[code + k] = T[(c, r)][0]
                objs.append((code, ((len(run) - 1) << 8) | s.palette(ec, pal), x0 + 16 * run[0], y0 + 16 * r))
            for c in cols:
                if run and (c != run[-1] + 1 or T[(c, r)][1] != T[(run[0], r)][1] or len(run) == 16): vide(); run = []
                run.append(c)
            vide(); run = []
        return objs
    def nouveau_bloc(s, w):
        """w codes consécutifs sans franchir une ligne de 16 (bloc CPS2 : code + i)"""
        n = len(s.tuiles)
        if n % 16 + w > 16: s.tuiles += [None] * (16 - n % 16); n = len(s.tuiles)
        s.tuiles += [None] * w; return n
def _p_brut(ec, p):
    import struct as st
    return ec.pal_brut[32 * p: 32 * p + 32]
def charger(path, ti):
    from plpac import split
    ec = Ecran(path, ti); ec.pal_brut = split(open(path, "rb").read())[ti[2]][1]
    ec.P_brut = lambda p, ec=ec: _p_brut(ec, p); return ec
def famille(poses, ID):
    """ID ≥ 40 (Yun $28, Ingrid $29) : hors de la table actuelle (40 ID par pose), pas de frame en place"""
    return [{"pose": p, "table_0x484C00": {"pose": p, "id": ID},
             "frame_actuelle_ro5": "%#x" % (entree(p, ID)[1] - 0x1F0000) if ID < 40 and frame8(entree(p, ID)[1]) else None} for p in poses]
# perso : (ID, calques du portrait de victoire winXX_e.pac, calques du portrait vertical select_e.pac jeu 2, base de
# palettes de select_e.pac (recherche pondérée sur les couleurs du portrait de victoire, contrôlée à l'œil))
PERSOS = {"pl26": (0x26, (0, 1, 2), (195, 196), 1240), "pl27": (0x27, (0, 1), (197, 198), 1264),
          "pl28": (0x28, (0, 1), (199, 200), 1288), "pl29": (0x29, (0, 1, 2), (201, 202, 203), 1312)}
POSES_320 = [12, 13, 14, 15, 16, 17, 30, 31]; POSES_128 = [0, 1, 2, 3, 4, 5, 24, 25, 26, 27, 28, 29]
# bandeaux : chez Upper, recadrages EXACTS du portrait vertical (vérifié sur 6 ID : 100 % des pixels) ; ici fenêtre de
# 48 px (haut, aligné sur 16) sur les yeux, et bord gauche du 96x48, repérés à l'œil sur bandeaux_reperes.png
BANDEAUX = {"pl26": (-96, -48), "pl27": (-64, -48), "pl28": (-96, -64), "pl29": (-80, -48)}
# bande d'yeux 96x16 (pose 32 de 0x484C00 = écran VS ; recadrage exact du vertical chez Upper) : haut de la fenêtre
YEUX = {"pl26": -64, "pl27": -48, "pl28": -80, "pl29": -64}
R_DIRECT = {"pl29"}     # persos dont les objets de sélection/bandeaux visent r = 0..3 (variantes) directement
POSES_B128 = [6, 7, 8, 9, 10, 11]; POSES_B96 = [18, 19, 20, 21, 22, 23]
def recadre(objs, wx, wy, W, H=48):
    """objets (bandes d'une tuile de haut) du portrait vertical gardés dans [wx, wx+W) x [wy, wy+H), recentrés"""
    out = []
    for code, a, x, y in objs:
        if not wy <= y < wy + H: continue
        n = ((a >> 8) & 15) + 1; ks = [i for i in range(n) if wx <= x + 16 * i < wx + W]
        if ks: out.append((code + ks[0], (a & ~0xF00) | ((len(ks) - 1) << 8), x + 16 * ks[0] - wx - W // 2, y - wy - H // 2))
    return out
def perso(pl):
    """Coordonnées d'Upper (frames type 8) : 320x160 centré, x -192..192 (rognage au pas de 16), y -80..80 ;
    128x224 : x -64..64, y -128..128 (Upper : -120..120). Calques PSP : coin = origine - (a, c) ; premier calque dessus."""
    ID, cw, cs, base = PERSOS[pl]; S = Sortie(); fam = {}
    win = charger(D + "win%s_e.pac" % pl[2:], (2, 3, 4)); sel = charger(D + "select_e.pac", (3, 4, 2))
    objs = []
    for n in cw:
        f = win.F[n]; objs += S.calque(win, n, 0, -f["a"], 16 - (f["c"] & 0xFFFF), -192, 192)
    fam["320x160"] = {"objs": objs, "poses": famille(POSES_320, ID), "source": "win%s_e.pac (calques %s)" % (pl[2:], list(cw))}
    objs = []
    for n in cs:
        f = sel.F[n]; objs += S.calque(sel, n, base, -f["a"], -(f["c"] & 0xFFFF))
    fam["128x224"] = {"objs": objs, "poses": famille(POSES_128, ID), "source": "select_e.pac jeu 2 (frames %s, base %d)" % (list(cs), base)}
    # 6 variantes de couleurs x 4 palettes (base + 4 v + r) ; les objets du 128x224 (et des bandeaux) visent la variante 0
    S.variantes = [sel.P_brut(base + 4 * v + r) for v in range(6) for r in range(4)]
    fam["128x224"]["variantes"] = {"fichier": "portraits_palettes_variantes.bin (24 palettes : variante v, palette r = 4 v + r)",
        "palette_du_fichier_vers_r": {str(i): p - base for (e, p), i in S.pal_idx.items() if e == id(sel)}}
    if pl in R_DIRECT:      # (HSFA §131) le jeu ne copie que 4 palettes par variante : attributs = r directement (0..3)
        rmap = {i: q - base for (e, q), i in S.pal_idx.items() if e == id(sel)}
        objs = [(c, (a & ~0x1F) | rmap[a & 0x1F], x, y) for c, a, x, y in objs]
        fam["128x224"]["objs"] = objs
        fam["128x224"]["variantes"]["attributs"] = "r direct : palette 4 v + r de portraits_palettes_variantes.bin (pas portraits_palettes.bin)"
    wy, wx96 = BANDEAUX[pl]
    fam["128x48"] = {"objs": recadre(objs, -64, wy, 128), "poses": famille(POSES_B128, ID), "source": "128x224, fenêtre x -64..64 y %d..%d" % (wy, wy + 48)}
    fam["96x48"] = {"objs": recadre(objs, wx96, wy, 96), "poses": famille(POSES_B96, ID), "source": "128x224, fenêtre x %d..%d y %d..%d" % (wx96, wx96 + 96, wy, wy + 48)}
    fam["96x16"] = {"objs": recadre(objs, wx96, YEUX[pl], 96, 16), "poses": famille([32], ID), "source": "128x224, fenêtre x %d..%d y %d..%d (yeux, écran VS)" % (wx96, wx96 + 96, YEUX[pl], YEUX[pl] + 16)}
    return S, fam
def ecrire(S, fam, pl):
    d = os.path.join(os.path.expanduser("~/.cache/sfa3max/converti"), pl); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "portraits.bin"), "wb") as f:
        for t in S.tuiles:
            raw = [15 - ((16 - i) % 16) for i in (t or [0] * 256)]          # brut CPS2 (15 = transparent)
            f.write(bytes(raw[2 * k] | (raw[2 * k + 1] << 4) for k in range(128)))
    def module(pals):
        """palettes PSP brutes -> format module (0x0RGB, CPS2[r] = PSP[r+1], mot 15 = n°)"""
        pal = []
        for k, p in enumerate(pals):
            cols = []
            for r in range(15):
                v = struct.unpack_from("<H", p, 2 * (r + 1))[0]
                cols.append(((v & 31) >> 1) << 8 | (((v >> 5) & 31) >> 1) << 4 | ((v >> 10) & 31) >> 1)
            pal += cols + [k]
        return struct.pack("<%dH" % len(pal), *pal)
    open(os.path.join(d, "portraits_palettes.bin"), "wb").write(module(S.palettes))
    open(os.path.join(d, "portraits_palettes_variantes.bin"), "wb").write(module(S.variantes))
    for k, v in fam.items(): v["T"] = sum(((a >> 8 & 15) + 1) * ((a >> 12 & 15) + 1) for _, a, _, _ in v["objs"])
    json.dump(fam, open(os.path.join(d, "portraits.json"), "w"), indent=1)
    return d
if __name__ == "__main__":
    for pl in (sys.argv[1:] or PERSOS):
        S, fam = perso(pl); d = ecrire(S, fam, pl)
        print(pl, "tuiles", len(S.tuiles), "palettes", len(S.palettes), {k: (len(v["objs"]), v["T"]) for k, v in fam.items()}, "->", d)
