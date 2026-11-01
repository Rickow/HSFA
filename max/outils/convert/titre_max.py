"""Logo de l'écran titre de SFA3 MAX (PSP) -> frame d'objets CPS2 « type 8 » (2026-10-27/31, demande de l'utilisateur :
le logo japonais « Street Fighter ZERO 3 ↑↑ » (Double Upper) sur la version CPS2 ; format demandé par l'intégration, Q20.4 ;
retouches N25 : taille, contour, dégradés).
PSP : <région>/data/title_<x>.pac ; entrée 9 = image PVRT 8 bpp (en-tête 16 o, 512 × 256, image utile 384 × 224 =
l'écran CPS2), entrée 10 = palette de 256 couleurs ABGR1555 (bit 15 = opaque). Pas de « swizzle ». Fond = couleur
dominante du bord (206, 222, 255 en JP), traité comme transparent.
Chaîne (N25) :
1. contour : la PSP anticrénèle le logo contre son fond bleu clair ; chaque pixel de bord proche de ce fond est séparé en
   couleur pleine (moyenne des voisins intérieurs) + opacité (projection entre cette couleur et le fond PSP) ;
2. échelle (défaut 1,00, décalage (+4, +1)) : alpha prémultiplié, filtre de Lanczos. Le ZERO 3 et le « ALPHA 3 » d'Upper
   sont dessinés à la même échelle (cadres blancs identiques à 4 px près) : (+4, +1) pose le cadre du ZERO 3 sur celui de
   la plaque d'Upper (silhouette blanche + ombre tramée du logo natif, plans 1 / 2), qui sert alors de doublure. Sans
   plaque, 0,92 (+1, +5) donne la hauteur du « ALPHA 3 » (y 20-175) ;
3. bord recomposé sur le fond réel (--fond : capture de l'écran titre d'Upper sans objets, plaque comprise ; sinon la
   couleur unie (187, 221, 221)), opaque si alpha ≥ 0,5 : contour net ;
4. couleurs : K palettes de ≤ 15 couleurs (k-moyennes en couleur pleine, affectation des tuiles), puis tramage ordonné
   4 × 4 vers les couleurs 12 bits du CPS2 (les dégradés ne font plus de bandes), ou --diffusion : Floyd-Steinberg sur
   tout l'écran (chaque pixel prend la palette de sa tuile ; l'erreur passe d'une tuile à l'autre, ruptures adoucies ;
   erreur reportée bornée à ±20 pour ne pas traverser les bords nets) ; palettes : meilleur de 6 départs.
CPS2, conventions des portraits (portraits_max.py) : tuiles 16 × 16 BRUTES (4 bpp linéaire, quartet bas à gauche,
128 o / tuile, stylo 15 = transparent) ; palettes au format module (16 mots 0x0RGB : mots 0-14 = stylos 0-14, mot 15 =
n° relatif) ; frame type 8 = objets (code local, attributs, x, y) : bandes horizontales de tuiles de même palette
(largeur ≤ 16, codes consécutifs sans franchir une ligne de 16 codes), attributs = (largeur − 1) << 8 | n° de palette
relatif, x / y relatifs à l'ancre (192, 112) = centre de l'écran.
Sortie : <racine SFA3MAX_CACHE>/converti/titre/<nom>_tuiles.bin, _palettes.bin, _frame.json (objets, T), _apercu.png
(rendu de la frame) et, avec --fond <png 384 × 224>, _apercu_fond.png (frame posée sur ce fond).
Source HD (N26, 2026-10-31) : --source-hd <png RGBA> remplace le sprite PSP (logo agrandi par l'utilisateur ; source
PRIVÉE, jamais dans le dépôt). Elle est recalée sur le repère du sprite PSP (--recalage sx,sy,ox,oy ; défaut
0.394,0.408,15,6 = meilleur recouvrement des silhouettes, IoU 0,75, cadre et lettres superposés) par réduction en alpha
prémultiplié (Lanczos), puis suit la même chaîne (échelle, décalage, bord, palettes, tramage).
Usage : python titre_max.py <title_x.pac> [nom] [K palettes, défaut 8] [--echelle 1.0] [--decalage 4,1]
        [--source-hd logo.png] [--recalage 0.394,0.408,15,6] [--diffusion]
        [--couleur-fond 187,221,221] [--sans-tramage] [--fond capture.png]"""
import os, sys, json, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import paths
from plpac import split
W, H, T = 384, 224, 16
NC = 15                     # couleurs opaques par palette (format module : stylos 0-14, stylo 15 transparent, mot 15 = n°)
ANCRE = (192, 112)


def lire_pac(chemin):
    E = split(open(chemin, "rb").read())
    pv = E[9][1]; assert pv[:4] == b"PVRT", "entrée 9 : pas une image PVRT"
    lw, lh = struct.unpack_from("<HH", pv, 12)
    px = pv[16:16 + lw * lh]
    pal = struct.unpack_from("<256H", E[10][1])
    img = [[px[y * lw + x] for x in range(W)] for y in range(H)]
    return img, pal


def rgb12(c):
    """ABGR1555 -> (r, g, b) sur 4 bits, ou None si transparent"""
    if not c & 0x8000: return None
    return tuple(((c >> s) & 31) >> 1 for s in (0, 5, 10))


FOND_UPPER = (187, 221, 221)        # fond uni de l'écran titre d'Upper (plan 3), relevé sur la capture v151
BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def image_rgba(img, pal, fond=None):
    """-> tableau H × W × 4 (flottants 0-255, alpha 0-1) : fond transparent, frange anticrénelée séparée (couleur pleine
    + opacité)"""
    import numpy as np
    I = np.array(img)
    if fond is None:
        bord = [img[0][x] for x in range(W)] + [img[H - 1][x] for x in range(W)]
        fond = max(set(bord), key=bord.count)
    c5 = lambda v: (v << 3) | (v >> 2)
    P = np.array([(c5(p & 31), c5((p >> 5) & 31), c5((p >> 10) & 31)) for p in pal], float)
    rgb = P[I]; a = (I != fond).astype(float); bg = P[fond]
    proche = (np.abs(rgb - bg).sum(2) < 120) & (a > 0)
    sur = (a > 0) & ~proche                                   # intérieur franc
    for _ in range(3):                                        # anneaux de frange, de l'intérieur vers le bord
        out = rgb.copy(); a2 = a.copy(); nsur = sur.copy()
        for y, x in zip(*np.where(proche & ~sur)):
            y0, y1, x0, x1 = max(0, y - 2), min(H, y + 3), max(0, x - 2), min(W, x + 3)
            m = sur[y0:y1, x0:x1]
            if not m.any(): continue
            fg = rgb[y0:y1, x0:x1][m].mean(0); v = fg - bg; n2 = (v * v).sum()
            al = float(np.clip(((rgb[y, x] - bg) * v).sum() / n2, 0, 1)) if n2 > 1 else 1.0
            out[y, x] = fg; a2[y, x] = al; nsur[y, x] = True
        rgb, a, sur = out, a2, nsur
    a[proche & ~sur] = 0.0                                    # frange sans intérieur voisin : fond
    return np.dstack([rgb, a])


def image_hd(chemin, sx=0.394, sy=0.408, ox=15, oy=6):
    """source HD RGBA -> tableau H × W × 4 dans le repère du sprite PSP (réduction en alpha prémultiplié, Lanczos)"""
    import numpy as np
    from PIL import Image
    im = np.array(Image.open(chemin).convert("RGBA"), float)
    a = im[:, :, 3:4] / 255.0
    pm = np.dstack([im[:, :, :3] * a, im[:, :, 3]])
    h0, w0 = pm.shape[:2]; w, h = int(round(w0 * sx)), int(round(h0 * sy))
    chans = [np.array(Image.fromarray(pm[:, :, c].astype(np.float32), "F").resize((w, h), Image.LANCZOS)) for c in range(4)]
    p = np.clip(np.dstack(chans), 0, 255)
    out = np.zeros((H, W, 4))
    ys, xs = slice(max(0, oy), min(H, oy + h)), slice(max(0, ox), min(W, ox + w))
    out[ys, xs] = p[ys.start - oy:ys.stop - oy, xs.start - ox:xs.stop - ox]
    al = out[:, :, 3] / 255.0
    rgb = np.where(al[:, :, None] > 1e-3, out[:, :, :3] / np.maximum(al, 1e-3)[:, :, None], 0)
    return np.dstack([np.clip(rgb, 0, 255), al])


def mettre_a_echelle(rgba, echelle=1.0, dx=0, dy=0):
    """mise à l'échelle autour du centre de l'écran (alpha prémultiplié, Lanczos) puis décalage entier"""
    import numpy as np
    from PIL import Image
    if echelle == 1.0 and dx == 0 and dy == 0: return rgba
    pm = np.dstack([rgba[:, :, :3] * rgba[:, :, 3:4], rgba[:, :, 3] * 255])
    chans = []
    w, h = int(round(W * echelle)), int(round(H * echelle))
    for c in range(4):
        im = Image.fromarray(pm[:, :, c].astype(np.float32), "F").resize((w, h), Image.LANCZOS)
        chans.append(np.array(im))
    p = np.clip(np.dstack(chans), 0, 255)
    out = np.zeros((H, W, 4)); ox, oy = (W - w) // 2 + dx, (H - h) // 2 + dy
    ys, xs = slice(max(0, oy), min(H, oy + h)), slice(max(0, ox), min(W, ox + w))
    out[ys, xs] = p[ys.start - oy:ys.stop - oy, xs.start - ox:xs.stop - ox]
    al = out[:, :, 3] / 255.0
    rgb = np.where(al[:, :, None] > 1e-3, out[:, :, :3] / np.maximum(al, 1e-3)[:, :, None], 0)
    return np.dstack([np.clip(rgb, 0, 255), al])


def aplatir(rgba, couleur_fond=FOND_UPPER, seuil=0.5, fond_image=None):
    """bord recomposé sur le fond cible (image H × W × 3 si fournie, sinon couleur unie) ; -> (rgb flottant, masque opaque)"""
    import numpy as np
    a = rgba[:, :, 3:4]
    F = np.asarray(fond_image, float) if fond_image is not None else np.array(couleur_fond, float)
    rgb = rgba[:, :, :3] * a + F * (1 - a)
    return rgb, rgba[:, :, 3] >= seuil


def convertir_rgb(rgb, opaque, K=8, tramage=True, tours=30, diffusion=False, essais=6, borne=20.0):
    """-> tuiles (indices 0 = transparent, 1-15), palettes (≤ 15 couleurs 4 bits), carte {(tx, ty): (n° tuile, n° pal.)}"""
    import numpy as np
    meilleur = None
    for graine in range(essais):                       # plusieurs départs des k-moyennes : on garde le plus fidèle
        r = _palettes(rgb, opaque, K, tours, graine)
        if meilleur is None or r[0] < meilleur[0]: meilleur = r
    _, cles, a, palettes = meilleur
    return _pixels(rgb, opaque, cles, a, palettes, tramage, diffusion, borne)


def _palettes(rgb, opaque, K, tours, graine):
    import numpy as np
    rng = np.random.default_rng(graine)
    cles = [(tx, ty) for ty in range(H // T) for tx in range(W // T) if opaque[ty * T:ty * T + T, tx * T:tx * T + T].any()]
    px = {k: rgb[k[1] * T:k[1] * T + T, k[0] * T:k[0] * T + T][opaque[k[1] * T:k[1] * T + T, k[0] * T:k[0] * T + T]]
          for k in cles}
    def kmoy(X, n, iters=12):
        u = np.unique(np.round(X), axis=0)
        if len(u) <= n: return u
        C = [u[rng.integers(len(u))]]                           # k-moyennes++
        for _ in range(n - 1):
            d = ((u[:, None] - np.array(C)[None]) ** 2).sum(2).min(1); C.append(u[rng.choice(len(u), p=d / d.sum())])
        C = np.array(C, float)
        for _ in range(iters):
            a = ((X[:, None] - C[None]) ** 2).sum(2).argmin(1)
            C = np.array([X[a == j].mean(0) if (a == j).any() else C[j] for j in range(n)])
        return C
    q4 = lambda C: np.unique(np.clip(np.round(C / 17.0), 0, 15), axis=0)       # couleurs 12 bits
    def err(X, Q): return ((X[:, None] - (Q * 17.0)[None]) ** 2).sum(2).min(1).sum()
    K = min(K, len(cles))
    moy = np.array([px[k].mean(0) for k in cles])
    C0 = kmoy(moy, K); a = ((moy[:, None] - C0[None]) ** 2).sum(2).argmin(1)
    for _ in range(tours):
        Q = [q4(kmoy(np.concatenate([px[k] for k, j in zip(cles, a) if j == q]), NC)) if (a == q).any()
             else np.zeros((1, 3)) for q in range(K)]
        a2 = np.array([min(range(K), key=lambda q: err(px[k], Q[q])) for k in cles])
        if (a2 == a).all(): break
        a = a2
    palettes = [[tuple(int(v) for v in c) for c in Q[q]] for q in range(K)]
    total = sum(err(px[k], Q[q]) for k, q in zip(cles, a))
    return total, cles, a, palettes


def _pixels(rgb, opaque, cles, a, palettes, tramage, diffusion, borne):
    import numpy as np
    if diffusion:                         # Floyd-Steinberg en serpentin sur tout l'écran, palette = celle de la tuile
        pal_t = {k: np.array(palettes[q], float) * 17.0 for k, q in zip(cles, a)}
        work = rgb.astype(float).copy(); idx = np.zeros(opaque.shape, int)
        for Y in range(H):
            sens = range(W) if Y % 2 == 0 else range(W - 1, -1, -1); dxs = 1 if Y % 2 == 0 else -1
            for X in sens:
                if not opaque[Y, X]: continue
                Pq = pal_t[(X // T, Y // T)]; c = np.clip(work[Y, X], 0, 255)
                i = int(((Pq - c) ** 2).sum(1).argmin()); idx[Y, X] = i + 1; e = np.clip(c - Pq[i], -borne, borne)
                for ddx, ddy, w in ((dxs, 0, 7), (-dxs, 1, 3), (0, 1, 5), (dxs, 1, 1)):
                    x2, y2 = X + ddx, Y + ddy
                    if 0 <= x2 < W and y2 < H and opaque[y2, x2]: work[y2, x2] += e * w / 16.0
    tuiles, carte, e2 = [], {}, []
    for k, q in zip(cles, a):
        Pq = np.array(palettes[q], float) * 17.0
        t = []
        for y in range(T):
            for x in range(T):
                Y, X = k[1] * T + y, k[0] * T + x
                if not opaque[Y, X]: t.append(0); continue
                if diffusion:
                    i = idx[Y, X] - 1; t.append(1 + i); e2.append(((Pq[i] - rgb[Y, X]) ** 2).sum()); continue
                c = rgb[Y, X] + ((BAYER4[Y % 4][X % 4] + 0.5) / 16.0 - 0.5) * 17.0 * (1 if tramage else 0)
                i = int(((Pq - c) ** 2).sum(1).argmin()); t.append(1 + i); e2.append(((Pq[i] - rgb[Y, X]) ** 2).sum())
        carte[k] = (len(tuiles), int(q)); tuiles.append(t)
    e2 = np.sqrt(np.array(e2))
    print("  écart moyen par pixel (0-255, RGB) : %.1f ; 95e centile : %.1f" % (e2.mean(), np.percentile(e2, 95)))
    return tuiles, palettes, carte


def ecrire(tuiles, palettes, carte, nom):
    d = os.path.join(paths.CACHE, "converti", "titre"); os.makedirs(d, exist_ok=True)
    # frame type 8 : bandes horizontales de même palette, codes consécutifs (bloc CPS2 : code + i)
    brut = []                                    # tuiles locales (None = bourrage)
    def bloc(w):
        n = len(brut)
        if n % 16 + w > 16: brut.extend([None] * (16 - n % 16)); n = len(brut)
        brut.extend([None] * w); return n
    objs = []
    for ty in range(H // T):
        run = []
        def vide():
            if not run: return
            pal = carte[(run[0], ty)][1]; code = bloc(len(run))
            for k, tx in enumerate(run): brut[code + k] = tuiles[carte[(tx, ty)][0]]
            objs.append((code, ((len(run) - 1) << 8) | pal, T * run[0] - ANCRE[0], T * ty - ANCRE[1]))
        for tx in range(W // T):
            if (tx, ty) not in carte: vide(); run = []; continue
            if run and (carte[(tx, ty)][1] != carte[(run[0], ty)][1] or len(run) == 16): vide(); run = []
            run.append(tx)
        vide()
    with open(os.path.join(d, nom + "_tuiles.bin"), "wb") as f:
        for t in brut:
            raw = [15 - ((16 - i) % 16) for i in (t or [0] * 256)]          # brut CPS2 : indice 0 -> stylo 15 (transparent)
            f.write(bytes(raw[2 * k] | (raw[2 * k + 1] << 4) for k in range(128)))
    pb = bytearray()
    for n, P in enumerate(palettes):
        mots = [(r << 8) | (g << 4) | bl for r, g, bl in P] + [0] * (15 - len(P)) + [n]
        pb += struct.pack("<16H", *mots)                                     # comme portraits_palettes.bin
    open(os.path.join(d, nom + "_palettes.bin"), "wb").write(pb)
    js = {"ancre": list(ANCRE), "palettes": len(palettes), "tuiles": len(brut),
          "T": sum((a >> 8 & 15) + 1 for _, a, _, _ in objs), "objs": objs,
          "format": "objs = (code local, attributs ((largeur - 1) << 8 | palette relative), x, y relatifs à l'ancre)"}
    json.dump(js, open(os.path.join(d, nom + "_frame.json"), "w"), indent=0)
    try:                                         # rendu À PARTIR de la frame (contrôle du format)
        from PIL import Image
        im = Image.new("RGB", (W, H), (40, 40, 40))
        for code, a, x, y in objs:
            P = palettes[a & 0x1F]
            for k in range((a >> 8 & 15) + 1):
                t = brut[code + k]
                for i, v in enumerate(t):
                    if v: im.putpixel((ANCRE[0] + x + 16 * k + i % T, ANCRE[1] + y + i // T), tuple(c * 17 for c in P[v - 1]))
        im.save(os.path.join(d, nom + "_apercu.png"))
    except ImportError: pass
    return d, len(objs), len(brut)


def main():
    args = sys.argv[1:]
    def opt(nom, defaut):
        if nom in args: i = args.index(nom); v = args[i + 1]; del args[i:i + 2]; return v
        return defaut
    ech = float(opt("--echelle", "1.0")); dx, dy = map(int, opt("--decalage", "4,1").split(","))
    cf = tuple(map(int, opt("--couleur-fond", "%d,%d,%d" % FOND_UPPER).split(",")))
    fond_png = opt("--fond", None)
    hd = opt("--source-hd", None); rec = [float(x) for x in opt("--recalage", "0.394,0.408,15,6").split(",")]
    tramage = "--sans-tramage" not in args; diffusion = "--diffusion" in args
    args = [x for x in args if x not in ("--sans-tramage", "--diffusion")]
    chemin = args[0]; nom = args[1] if len(args) > 1 else "titre"; K = int(args[2]) if len(args) > 2 else 8
    img, pal = lire_pac(chemin)
    fimg = None
    if fond_png:
        from PIL import Image
        import numpy as np
        fimg = np.array(Image.open(fond_png).convert("RGB"), float)
    src = image_hd(hd, rec[0], rec[1], int(rec[2]), int(rec[3])) if hd else image_rgba(img, pal)
    rgb, opaque = aplatir(mettre_a_echelle(src, ech, dx, dy), cf, fond_image=fimg)
    tuiles, palettes, carte = convertir_rgb(rgb, opaque, K, tramage, diffusion=diffusion)
    d, no, nt = ecrire(tuiles, palettes, carte, nom)
    if fond_png:
        from PIL import Image
        f = Image.open(fond_png).convert("RGB"); a = Image.open(os.path.join(d, nom + "_apercu.png")).convert("RGB")
        import numpy as np
        A, F = np.array(a), np.array(f); m = (A != np.array([40, 40, 40])).any(2)
        F[m] = A[m]; Image.fromarray(F).save(os.path.join(d, nom + "_apercu_fond.png"))
    print("%s : échelle %.2f, décalage (%d, %d), %d tuiles non vides (%d codes avec bourrage), %d objets, %d palettes -> %s" %
          (nom, ech, dx, dy, len(tuiles), nt, no, len(palettes), d))


if __name__ == "__main__":
    main()
