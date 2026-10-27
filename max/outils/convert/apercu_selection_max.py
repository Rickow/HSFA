"""Petit sprite d'aperçu de l'écran de sélection des 4 persos MAX (2026-10-17, demande 2 de l'agent d'intégration HSFA).
PSP : routine 0x99074 : animation = PTR 0x2256C0[perso] (pas de 8 o : u16 durée (bit 15 = boucle), u16 drapeaux,
u16 n° de frame de select_e.pac jeu 0 (frames [0], tuiles [1], palettes [2]), s16 saut vers le pas suivant (boucle :
négatif)) ; palette = 0x538 + perso × 6 + couleur ($178) copiée en palette 0x20 + 2 × joueur (Ingrid, ')' = $29 :
0x538 + perso × 6 + 2 × couleur, DEUX palettes, sprites fusionnés +0/+1).
Upper : T_97CA90[ID] -> décalages u16 par isme -> animation en pas de 20 o (durée, drapeaux $80 = reprise avec pointeur
en +$14, frame type 2, boîtes de Ryu 01 00 03 00 00 00 01 58 00 00 00 00) ; frames de type 2 du module.
Sortie ~/.cache/sfa3max/converti/plXX/apercu/ :
  tuiles.bin  : tuiles brutes CPS2 (4 bpp, 15 = transparent), codes locaux, blocs consécutifs dans une rangée de 16 ;
  apercu.s    : APERCU_xx (pas de 20 o, une seule animation pour les 3 ismes, reprise sur le pas de boucle) et frames
                AP_xx_n (type 2 : dc.w 2, T, n-1, 0 ; dc.l positions ; n × code local, attributs ((w-1) << 8 | r)),
                positions APP_xx_n (dx, dy depuis l'origine PSP, convention de convert_max.py) ;
  palettes_module.bin : 6 couleurs × 1 palette (Ingrid × 2), format module (0x0RGB, mot 15 = n°) ; r = palette relative ;
  apercu.json : résumé (frames PSP, durées, boucle, palettes)."""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from portraits_max import Sortie, charger
from relocs import img, pointer_words
SEL = os.path.expanduser("~/.cache/sfa3max/data/select_e.pac")
NOMS = {0x26: "pl26", 0x27: "pl27", 0x28: "pl28", 0x29: "pl29"}
BOITES = "$01, $00, $03, $00, $00, $00, $01, $58, $00, $00, $00, $00"      # pas d'aperçu de Ryu (Upper 0x97CBF0)


def animation(cid):
    a = pointer_words()[0x2256C0 + 4 * cid]; pas, k = [], 0
    while True:
        d, fl, fr, saut = struct.unpack_from("<HHHh", img, a + 8 * k)
        pas.append((d & 0x7FFF, fr))
        if d & 0x8000: return pas, k + saut              # boucle : retour au pas k + saut
        k += saut


def une_palette(S, frames, pals, n_var=6):
    """Ingrid (demande HSFA 2026-10-17) : Upper ne copie qu'une palette pour l'aperçu (image $37FC2-$38012, table 0x6F72B0) ;
    les jambes (sous-palette 1) passeraient sur la palette suivante (rouge en 1 joueur, celle de J2 en VERSUS).
    Corps (14 couleurs) + jambes (10) = 24 > 15 : regroupement des sources (r, i) les plus proches, en distance
    cumulée sur les 6 variantes de couleur (même indice pour toutes les variantes), pondérée par le nombre de pixels ;
    couleur d'un groupe = moyenne pondérée, par variante. Tuiles réécrites, tous les objets en palette relative 0."""
    import collections
    rgb = lambda p, i: [((struct.unpack_from("<H", p, 2 * i)[0] >> s) & 31) for s in (0, 5, 10)]
    poids = collections.Counter()
    par_code = {}
    for objs in frames.values():
        for code, attr, _, _ in objs:
            r = attr & 0xFF
            for k in range((attr >> 8) + 1):
                par_code[code + k] = r
    for code, r in par_code.items():
        for i in S.tuiles[code]:
            if i: poids[(r, i)] += 1
    groupes = [[s] for s in poids]
    def coul(g, v):
        w = sum(poids[s] for s in g)
        return [sum(rgb(pals[2 * v + s[0]], s[1])[c] * poids[s] for s in g) / w for c in range(3)]
    def cout(a, b):
        wa, wb = sum(poids[s] for s in a), sum(poids[s] for s in b)
        d = sum(sum((x - y) ** 2 for x, y in zip(coul(a, v), coul(b, v))) for v in range(n_var))
        return d * wa * wb / (wa + wb)
    while len(groupes) > 15:
        _, i, j = min((cout(groupes[i], groupes[j]), i, j) for i in range(len(groupes)) for j in range(i + 1, len(groupes)))
        groupes[i] += groupes.pop(j)
    groupes.sort(key=lambda g: min(g))
    nouv = {s: k + 1 for k, g in enumerate(groupes) for s in g}
    for code, r in par_code.items():
        S.tuiles[code] = [nouv[(r, i)] if i else 0 for i in S.tuiles[code]]
    frames = {n: [(c, a & ~0xFF, x, y) for c, a, x, y in objs] for n, objs in frames.items()}
    out = []
    for v in range(n_var):
        b = bytearray(pals[2 * v][:2])
        for g in groupes:
            r_, g_, b_ = (min(31, round(x)) for x in coul(g, v))
            b += struct.pack("<H", 0x8000 | r_ | g_ << 5 | b_ << 10)
        out.append(bytes(b))
    une_palette.groupes = [[("corps" if s[0] == 0 else "jambes", s[1]) for s in g] for g in groupes]
    return frames, out


def module(pals):
    out = []
    for n, p in enumerate(pals):
        cols = []
        for r in range(15):
            v = struct.unpack_from("<H", p, 2 * (r + 1))[0]
            cols.append(((v & 31) >> 1) << 8 | (((v >> 5) & 31) >> 1) << 4 | ((v >> 10) & 31) >> 1)
        out += cols + [n]
    return struct.pack("<%dH" % len(out), *out)


# (2026-10-18) ÉTIREMENT : la routine d'aperçu PSP 0x99074 pose +0xAB = 1 pour les ID $26-$29 (Ingrid comprise) ;
# select_e.pac = cases de 16 px -> FUN_0000CD84 : case dessinée sur 0x13 = 19 px (×19/16), ancre X × 12/10 (division
# entière C), Y inchangé. Ici : frame rendue par cases, chaque case 16 -> 19 px (texel floor(k·16/19)), puis redécoupée
# en tuiles 16×16 à partir de X = −trunc(a·12/10) + 19·col_min. SFA3MAX_ETIRE_APERCU = liste des ID étirés (défaut 26-29).
ETIRE_APERCU = {int(x, 16) for x in os.environ.get("SFA3MAX_ETIRE_APERCU", "26,27,28,29").split(",") if x}


def etirer(frames, S, ancres):
    S2 = Sortie(); out = {}
    for n, objs in frames.items():
        a = ancres[n]; A = -(-(a * 12) // 10) if a < 0 else (a * 12) // 10
        cel = {}; pals = set()
        for code, attr, x, y in objs:
            w = ((attr >> 8) & 15) + 1; pals.add(attr & 0x1F)
            for k in range(w):
                t = S.tuiles[code + k]
                if t is None: continue
                cle = ((x + 16 * k + a) // 16, y)
                if cle in cel:                          # calques superposés (Ingrid : haut + jambes) : le 1er objet garde
                    cel[cle] = [p if p else q for p, q in zip(cel[cle], t)]   # la priorité, comme sur CPS2
                else: cel[cle] = list(t)
        assert len(pals) <= 1, "aperçu : plusieurs palettes dans une frame (%d)" % n
        pal = pals.pop() if pals else 0
        if not cel: out[n] = []; continue
        c0 = min(c for c, _ in cel); c1 = max(c for c, _ in cel); W = 19 * (c1 - c0 + 1); objs2 = []
        for y in sorted({y for _, y in cel}):
            ligne = [[0] * W for _ in range(16)]
            for (c, yy), t in cel.items():
                if yy != y: continue
                for u in range(19):
                    sx = u * 16 // 19
                    for r in range(16): ligne[r][19 * (c - c0) + u] = t[16 * r + sx]
            nt = -(-W // 16); run = []
            def vide():
                if not run: return
                code = S2.nouveau_bloc(len(run))
                for k, (tx, px) in enumerate(run): S2.tuiles[code + k] = px
                objs2.append((code, ((len(run) - 1) << 8) | pal, -A + 19 * c0 + 16 * run[0][0], y))
            for tx in range(nt):
                px = [ligne[r][16 * tx + i] if 16 * tx + i < W else 0 for r in range(16) for i in range(16)]
                if not any(px): vide(); run = []; continue
                if len(run) == 16: vide(); run = []
                run.append((tx, px))
            vide()
        out[n] = objs2
    return out, S2


def perso(cid):
    ec = charger(SEL, (0, 1, 2)); S = Sortie(); S.palette = lambda e, p: p
    pas, boucle = animation(cid); frames = {}
    for _, n in pas:
        if n in frames: continue
        f = ec.F[n]; frames[n] = S.calque(ec, n, 0, -f["a"], -(f["c"] & 0xFFFF))
        if cid == 0x29 and 1026 <= n <= 1067:          # Ingrid : jambes = frame n + 42 (1068-1109, sous-palette 1,
            g = ec.F[n + 42]                            # même ancre), ajoutées comme ses sprites de combat (haut + bas)
            frames[n] += S.calque(ec, n + 42, 0, -g["a"], -(g["c"] & 0xFFFF))
    ing = cid == 0x29
    pals = [ec.P_brut(0x538 + 6 * cid + (2 * v + r if ing else v)) for v in range(6) for r in ((0, 1) if ing else (0,))]
    if ing:                                             # (2026-10-17) Upper ne copie qu'UNE palette pour l'aperçu
        frames, pals = une_palette(S, frames, pals)
    if cid in ETIRE_APERCU:
        frames, S = etirer(frames, S, {n: ec.F[n]["a"] for n in frames})
    L = ["; aperçu de sélection du perso $%02X — généré par apercu_selection_max.py (select_e.pac, animation PSP %#x)"
         % (cid, pointer_words()[0x2256C0 + 4 * cid]), "APERCU_%02X:" % cid]
    for k, (d, n) in enumerate(pas):
        fin = k == len(pas) - 1
        L += ["AP_PAS_%02X_%d:" % (cid, k), "        dc.b    $%02x, $%02x, $00, $00" % (d, 0x80 if fin else 0),
              "        dc.l    AP_%02X_%d" % (cid, n), "        dc.b    " + BOITES]
        if fin: L.append("        dc.l    AP_PAS_%02X_%d          ; reprise (boucle PSP)" % (cid, boucle))
    for n, objs in frames.items():
        T = sum(((a >> 8 & 15) + 1) for _, a, _, _ in objs)
        L += ["        cnop    0,4", "AP_%02X_%d:" % (cid, n), "        dc.w    2, %d, %d, 0" % (T, len(objs) - 1),
              "        dc.l    APP_%02X_%d" % (cid, n)]
        L += ["        dc.w    $%04x, $%04x" % (c, a) for c, a, _, _ in objs]
        L += ["        cnop    0,4", "APP_%02X_%d:" % (cid, n)] + ["        dc.w    %d, %d" % (x, y) for _, _, x, y in objs]
    d = os.path.join(os.path.expanduser(os.environ.get("SFA3MAX_CACHE", "~/.cache/sfa3max")), "converti", NOMS[cid], "apercu")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "tuiles.bin"), "wb") as fo:
        for t in S.tuiles:
            raw = [15 - ((16 - i) % 16) for i in (t or [0] * 256)]
            fo.write(bytes(raw[2 * k] | (raw[2 * k + 1] << 4) for k in range(128)))
    open(os.path.join(d, "apercu.s"), "w").write("\n".join(L) + "\n")
    open(os.path.join(d, "palettes_module.bin"), "wb").write(module(pals))
    info = {"pas": [{"duree": d_, "frame_psp": n} for d_, n in pas], "boucle_vers_pas": boucle,
            "palettes": ("6 couleurs × 1, fusion corps + jambes (n° PSP %#x + 2 × couleur + r) : %s" % (0x538 + 6 * cid, une_palette.groupes)) if ing else "6 couleurs × 1 (n° PSP %#x + couleur)" % (0x538 + 6 * cid),
            "tuiles": len(S.tuiles), "frames": len(frames)}
    json.dump(info, open(os.path.join(d, "apercu.json"), "w"), indent=1)
    return info


if __name__ == "__main__":
    for cid in NOMS:
        i = perso(cid); print(NOMS[cid], "pas", len(i["pas"]), "boucle", i["boucle_vers_pas"], "frames", i["frames"], "tuiles", i["tuiles"])
