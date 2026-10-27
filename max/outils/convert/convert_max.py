"""Convertisseur PSP (SFA3 MAX, plXX_e.pac) -> formats de l'Anthology / CPS2 (prototype).

Sorties (en mémoire, voir `convert(pl)`) :
  bank   : liste de tuiles 16x16 en valeurs BRUTES CPS2 (raw = 15 - fbneo ; fbneo = (16 - i) % 16 depuis l'index PSP i),
           numérotation locale ; la case PSP j (4 tuiles, ordre PSP en colonnes TL,BL,TR,BR) devient le bloc 2x2
           b, b+1, b+16, b+17 avec b = 32*(j // 8) + 2*(j % 8).
  frames : une frame de type 2 par frame PSP : liste d'objets (dx, dy, code local, attributs CPS2) + T = somme des tuiles.
           objet = case PSP non vide ; attributs = 0x1100 (bloc 2x2) | 0x20 miroir H | 0x40 miroir V | sous-palette (bits 0-1).
  scripts: scripts PSP (entrée [6], pas de 5 x u16) -> pas Anthology (contrôle, n° de frame, mot A, mot B, 0) ;
           mots A/B/C = table des jeux de boîtes (12 o/entrée = mots A, B, C des pas du module) en T[7] + 0x208 de
           l'en-tête de [6] ; tous les persos (Yun compris). Ryu vs module : A 82 %, B 84 %, C 99 % des pas identiques.
  sections : sections de [6] recopiées telles quelles ; emplacement = T[k] + 0x208 (avant le 2026-10-04 : SANS
           le + 0x208, exports faux)."""
import sys, os, struct
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import paths
from plpac import split
from maxtile import decode, tiles
from frames import frames

def bank_code(j):
    b = 32 * (j // 8) + 2 * (j % 8)
    return b, (b, b + 16, b + 1, b + 17)            # TL, BL, TR, BR (ordre PSP en colonnes)

SEUIL_RAMPE = 14   # (2026-10-17) 0x70 / 0xF8 : encres 1-6 de la rampe d'Ingrid
BASE6 = 0x208   # l'en-tête de [6] (67 u32) donne des décalages RELATIFS à 0x208 (début des données)
def find_boxset(b6):
    """table des jeux de boîtes = T[7] + 0x208 (vaut pour TOUS les persos, Yun compris ; contrôle : Ryu 0x2994,
    Eagle 0x3354, comme l'ancienne recherche par signature)"""
    return struct.unpack_from("<I", b6, 28)[0] + BASE6

# (2026-10-18, mesure HSFA ×1,186 sur captures PPSSPP) ÉTIREMENT HORIZONTAL DES PERSOS MAX : FUN_0000D2A8 / FUN_0000CD84
# (dessin des frames) testent l'octet +0x57 de l'objet sprite (= +0xAB de l'objet de jeu, posé à 1 par les inits MAX et par
# leurs tirs / effets) : case de 32 texels dessinée sur 0x26 = 38 px (19/16), ancre X × 12/10 (division entière C), Y
# inchangé ; boîtes non touchées (étirement purement graphique). Ingrid ($29) : mesurée à ×1 (autre chemin de dessin).
# Conversion : case PSP j -> bloc CPS2 3×2 tuiles (48×32 : colonnes 0-37 = texel floor(k·32/38), 38-47 transparentes),
# b = 32·(j // 5) + 3·(j % 5) ; objet à x = col·38 − trunc(ancre·12/10), attributs 0x1200 ; case en miroir H : x − 10
# (le miroir CPS2 retourne les 48 px). SFA3MAX_ETIRE = liste des pl étirés (défaut « pl26,pl27,pl28 » ; vide = aucun).
ETIRE = [p for p in os.environ.get("SFA3MAX_ETIRE", "pl26,pl27,pl28").split(",") if p]
LARGEUR_CASE = 38
def bank_code_etire(j):
    b = 32 * (j // 5) + 3 * (j % 5)
    return b, [b + x + 16 * y for y in range(2) for x in range(3)]   # ligne haute puis basse
def trunc_div(a, b):
    return -(-a // b) if a < 0 else a // b

def etirer_banque(bank, ncell):
    """banque par cases 2×2 -> banque par cases étirées 3×2"""
    import numpy as np
    out = [None] * (32 * ((ncell + 4) // 5))
    cols = [k * 32 // LARGEUR_CASE for k in range(LARGEUR_CASE)]
    for j in range(ncell):
        _, (tl, bl, tr, br) = bank_code(j)
        if all(bank[q] is None for q in (tl, bl, tr, br)): continue
        img = np.full((32, 32), 15, np.uint8)
        for q, (x0, y0) in ((tl, (0, 0)), (bl, (0, 16)), (tr, (16, 0)), (br, (16, 16))):
            if bank[q] is not None: img[y0:y0 + 16, x0:x0 + 16] = np.frombuffer(bank[q], np.uint8).reshape(16, 16)
        e = np.full((32, 48), 15, np.uint8); e[:, :LARGEUR_CASE] = img[:, cols]
        _, locs = bank_code_etire(j)
        for i, q in enumerate(locs):
            y, x = divmod(i, 3); out[q] = e[16 * y:16 * y + 16, 16 * x:16 * x + 16].tobytes()
    return out

def convert(pl, boxset_off="auto", etire=None):
    etire = (pl in ETIRE) if etire is None else etire
    E = split(open(os.path.join(paths.pac_dir(), f"{pl}_e.pac"), "rb").read())
    g = E[1][1]; T = tiles(g); F = frames(E[0][1]); b6 = E[6][1]
    if boxset_off == "auto": boxset_off = BASE6 if pl == "pl28" else find_boxset(b6)   # Yun : boîtes en tête de [6]
    ncell = len(T) // 4
    size = 32 * ((ncell + 7) // 8)
    bank = [None] * size
    for j in range(ncell):
        _, locs = bank_code(j)
        for q in range(4):
            t = decode(g, T[4*j + q][0])[0]
            px = [n for b in t for n in (b & 0xF, b >> 4)]
            bank[locs[q]] = bytes(15 - ((16 - i) % 16) for i in px)   # valeurs brutes CPS2
    # (2026-10-17, demande HSFA : liseré sombre autour des tirs d'Ingrid) palettes « en rampe » (entrée 1 noire, luminance
    # croissante jusqu'au blanc : effets lumineux tracés en mélange ADDITIF sur PSP, où le noir n'ajoute rien) : en CPS2
    # (opaque) leurs encres sombres (composante max <= SEUIL_RAMPE / 31) deviennent transparentes (encre 15) dans les
    # cases qui emploient cette sous-palette (Ingrid : sous-palette 3, encres 1-6 ; aucune case partagée avec une autre)
    P2 = E[2][1]
    def rampe(k):
        w = struct.unpack_from("<16H", P2, 32 * k); L = [max(v & 31, (v >> 5) & 31, (v >> 10) & 31) for v in w[1:]]
        return L[0] == 0 and all(L[i] <= L[i + 1] for i in range(14)) and L[-1] >= 28
    RAMPES = {r: {i for i in range(1, 16) if max((lambda v: (v & 31, (v >> 5) & 31, (v >> 10) & 31))(struct.unpack_from("<H", P2, 32 * r + 2 * i)[0])) <= SEUIL_RAMPE}
              for r in range(4) if 32 * r + 32 <= len(P2) and rampe(r)}
    if RAMPES:
        faites = set()
        for fr in F:
            for cell in fr["cells"]:
                if cell and (cell[1] & 3) in RAMPES and cell[0] not in faites:
                    faites.add(cell[0]); sombres = RAMPES[cell[1] & 3]
                    for q in bank_code(cell[0])[1]:
                        bank[q] = bytes(15 if (0 if r == 15 else r + 1) in sombres else r for r in bank[q])
    out_frames = []
    for fr in F:
        objs = []
        ax = fr["a"] | fr["b"] << 8; ax -= 0x10000 if ax & 0x8000 else 0     # (2026-10-18) ancre X = mot SIGNÉ (a, b) :
        # b = $FF sur quelques frames (témoin Ryu : 192, 418, 420, 445-447 décalées de −256 px avec l'octet a seul)
        if etire: ax = trunc_div(ax * 12, 10)
        for k, cell in enumerate(fr["cells"]):
            if cell is None: continue
            cx, cy = (k % fr["w"]) * (LARGEUR_CASE if etire else 32) - ax, (k // fr["w"]) * 32 - fr["c"]
            b, _ = bank_code_etire(cell[0]) if etire else bank_code(cell[0])
            # (2026-10-17) miroirs des cases PSP : bit 6 (0x40) = HORIZONTAL, bit 7 (0x80) = VERTICAL (inverse de la
            # note de render.py ; mesuré sur les 4 persos + Ryu par continuité des bords de cases, aucun contre-exemple ;
            # Yun F28_175-178 en mosaïque avec l'ancienne lecture) -> CPS2 0x20 = miroir H, 0x40 = miroir V
            attr = (0x1200 if etire else 0x1100) | (0x20 if cell[1] & 0x40 else 0) | (0x40 if cell[1] & 0x80 else 0) | (cell[1] & 3)
            if etire and cell[1] & 0x40: cx -= 48 - LARGEUR_CASE
            objs.append((cx, cy, b, attr))
        out_frames.append({"objs": objs, "T": (6 if etire else 4) * len(objs)})
    if etire: bank = etirer_banque(bank, ncell)
    H = struct.unpack_from(f"<{len(b6)//2}H", b6)
    ok = lambda i: i + 4 < len(H) and H[i+2] < len(F) and (H[i] <= 0xFF or H[i] & 0x8000) and H[i+3] in (0, 1)
    scripts, i = [], 0
    while i < len(H) - 5:
        if ok(i) and ok(i + 5):
            run, j = [], i
            while ok(j):
                d, fl, frn, one, col = H[j:j+5]
                wa, wb, wc = (struct.unpack_from("<3I", b6, boxset_off + 12*col)
                              if boxset_off is not None and boxset_off + 12*col + 12 <= len(b6) else (None, None, None))
                run.append({"ctl": (d & 0xFF) | (0x8000 if d & 0x8000 else 0), "frame": frn, "A": wa, "B": wb, "C": wc, "col": col})
                j += 5
                if d & 0x8000: break
            scripts.append((2*i, run)); i = j
        else: i += 1
    remap = None
    if pl == "pl29" or pl == "pl29r":
        out_frames, scripts, remap = merge_ingrid(out_frames, scripts)
    Hs = [v + BASE6 for v in struct.unpack_from("<67I", b6, 0)]   # sections : décalages relatifs à 0x208 (corrigé 2026-10-04)
    pts = sorted(set(Hs) | {len(b6)})
    sections = {k: b6[v:min(x for x in pts if x > v)] for k, v in enumerate(Hs) if v < len(b6)}
    return {"bank": bank, "frames": out_frames, "scripts": scripts, "sections": sections, "ncell": ncell,
            "boxset": boxset_off, "remap": remap}

# Ingrid : sprite composite. Frames PSP 0-201 + 206-690 = bas du corps (sous-palette 1), 691-892 + 897-1381 = haut
# (sous-palette 0), même ancre par paire (687/687). Hypothèse de travail (cohérente avec les scripts, qui désignent la
# pose par sa moitié haute) : pose k = haut k + bas k. On fusionne chaque paire en UNE frame de type 2.
INGRID_LOWER = list(range(0, 202)) + list(range(206, 691))
INGRID_UPPER = list(range(691, 893)) + list(range(897, 1382))
def merge_ingrid(frames_, scripts):
    remap, merged = {}, []
    for k, (lo, up) in enumerate(zip(INGRID_LOWER, INGRID_UPPER)):
        objs = frames_[up]["objs"] + frames_[lo]["objs"]
        merged.append({"objs": objs, "T": frames_[up]["T"] + frames_[lo]["T"]})
        remap[lo] = remap[up] = k
    for n, fr in enumerate(frames_):                    # poses complètes et effets, inchangés
        if n not in remap:
            remap[n] = len(merged); merged.append(fr)
    new_scripts = [(o, [dict(st, frame=remap[st["frame"]]) for st in run]) for o, run in scripts]
    return merged, new_scripts, remap

def export(pl, outdir=None):
    """Écrit la conversion dans le cache (données dérivées du jeu : hors dépôt).
    bank.bin = tuiles 16x16 en 4 bpp linéaire, quartet bas à gauche, valeurs BRUTES CPS2 (format des conteneurs Anthology) ;
    frames.json, scripts.json ; sections/sNN.bin."""
    import json
    C = convert(pl)
    outdir = outdir or os.path.join(paths.CACHE, "converti", pl); os.makedirs(os.path.join(outdir, "sections"), exist_ok=True)
    with open(os.path.join(outdir, "bank.bin"), "wb") as f:
        for t in C["bank"]:
            t = t or bytes([15] * 256)                     # tuile absente = transparente (brut 15)
            f.write(bytes(t[2*i] | (t[2*i+1] << 4) for i in range(128)))
    json.dump([{"T": fr["T"], "objs": fr["objs"]} for fr in C["frames"]], open(os.path.join(outdir, "frames.json"), "w"))
    json.dump([{"psp_offset": o, "steps": run} for o, run in C["scripts"]], open(os.path.join(outdir, "scripts.json"), "w"))
    # scripts rangés dans l'EBOOT (eboot_scripts.py) ; numéros de frame remappés pour Ingrid ; mots de collision si table connue
    from eboot_scripts import scripts_for
    cid = int(pl[2:4], 16)
    b6 = split(open(os.path.join(paths.pac_dir(), f"{pl}_e.pac"), "rb").read())[6][1]
    ES = []
    for taddr, k, addr, run in scripts_for(cid):
        steps = []
        for st in run:
            fr = C["remap"].get(st["frame"], st["frame"]) if C["remap"] else st["frame"]
            wa = wb = wc = None
            if C["boxset"] is not None and C["boxset"] + 12*st["col"] + 12 <= len(b6):
                wa, wb, wc = struct.unpack_from("<3I", b6, C["boxset"] + 12*st["col"])
            steps.append(dict(st, frame=fr, A=wa, B=wb, C=wc))
        ES.append({"table": taddr, "index": k, "eboot_addr": addr, "steps": steps})
    json.dump(ES, open(os.path.join(outdir, "scripts_eboot.json"), "w"))
    C["eboot_scripts"] = ES
    # tables d'animation PAR COUP ($2B0/$2B4/$2B8/$2BC du module), 2026-10-04
    from tables_anim import animations, animations_yun
    json.dump(animations_yun() if pl == "pl28" else animations(pl, C["remap"]), open(os.path.join(outdir, "animations.json"), "w"))
    for k, sec in C["sections"].items(): open(os.path.join(outdir, "sections", f"s{k:02d}.bin"), "wb").write(sec)
    return outdir, C

if __name__ == "__main__":
    for pl in sys.argv[1:] or ["pl26", "pl27", "pl28", "pl29"]:
        out, C = export(pl)
        nbox = sum(1 for _, r in C["scripts"] for st in r if st["A"] is not None)
        nst = sum(len(r) for _, r in C["scripts"])
        ne = C["eboot_scripts"]; nes = sum(len(e["steps"]) for e in ne)
        print(f"{pl}: banque {len(C['bank'])} tuiles, {len(C['frames'])} frames, scripts [6] {len(C['scripts'])} ({nst} pas, "
              f"collisions {nbox}) + EBOOT {len(ne)} ({nes} pas) ; table des boîtes {hex(C['boxset']) if C['boxset'] is not None else 'NON TROUVÉE'}")
