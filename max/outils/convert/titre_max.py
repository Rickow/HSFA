"""Logo de l'écran titre de SFA3 MAX (PSP) -> tuiles CPS2 (2026-10-27, demande de l'utilisateur : le logo japonais
« Street Fighter ZERO3 ↑↑ Double Upper » sur la version CPS2).
PSP : <région>/data/title_<x>.pac ; entrée 9 = image PVRT 8 bpp (en-tête 16 o, 512 × 256, image utile 384 × 224 =
l'écran CPS2), entrée 10 = palette de 256 couleurs ABGR1555 (bit 15 = opaque). Pas de « swizzle ».
CPS2 : tuiles 16 × 16 en 4 bpp (format des autres livrables MAX : linéaire, quartet bas à gauche, 128 o par tuile),
palettes de 16 mots au format module (0x0RGB ; mot 0 transparent, mots 1-14 = couleurs, mot 15 = n°). Couleurs ramenées à 4 bits par canal ;
regroupement des tuiles en palettes (≤ 14 couleurs opaques chacune) par fusion gloutonne ; une tuile de plus de 15
couleurs (au-delà de 14) est réduite au plus proche dans sa palette.
Sortie : <racine SFA3MAX_CACHE>/converti/titre/<nom>_tuiles.bin, _palettes.bin, _carte.json (grille 24 × 14 :
n° de tuile ou null, n° de palette), _apercu.png (rendu CPS2).
Usage : python titre_max.py <title_x.pac> [nom] [K palettes, défaut 8]"""
import os, sys, json, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import paths
from plpac import split
W, H, T = 384, 224, 16
NC = 14                     # couleurs opaques par palette (format module : mot 0 transparent, mot 15 = n° de palette)


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


def convertir(img, pal, K=8, fond=None, tours=12):
    """-> tuiles (indices 0-14), palettes (≤ 14 couleurs 4 bits), carte {(tx, ty): (n° tuile, n° palette)}.
    fond = index PSP traité comme transparent (par défaut : la couleur la plus fréquente du bord de l'image).
    Quantification : K palettes ; chaque tuile prend la palette qui l'approche le mieux, chaque palette est recalculée
    (k-moyennes pondérées sur les pixels de ses tuiles) ; quelques tours suffisent."""
    import numpy as np
    if fond is None:
        bord = [img[0][x] for x in range(W)] + [img[H - 1][x] for x in range(W)]
        fond = max(set(bord), key=bord.count)
    cols = [None if i == fond else rgb12(c) for i, c in enumerate(pal)]
    grille = {}
    for ty in range(H // T):
        for tx in range(W // T):
            p = [cols[img[ty * T + y][tx * T + x]] for y in range(T) for x in range(T)]
            if any(p): grille[(tx, ty)] = p
    cles = sorted(grille, key=lambda k: (k[1], k[0]))
    px = {k: np.array([c for c in grille[k] if c], float) for k in cles}
    def kmoy(X, n):
        u = np.unique(X, axis=0)
        if len(u) <= n: return u
        C = u[np.linspace(0, len(u) - 1, n).astype(int)]
        for _ in range(10):
            a = ((X[:, None] - C[None]) ** 2).sum(2).argmin(1)
            C = np.array([X[a == j].mean(0) if (a == j).any() else C[j] for j in range(n)])
        return np.unique(np.clip(np.rint(C), 0, 15), axis=0)
    def erreur(X, C): return ((X[:, None] - C[None]) ** 2).sum(2).min(1).sum()
    # départ : regroupement par couleur moyenne
    moy = np.array([px[k].mean(0) for k in cles]); K = min(K, len(cles))
    a = ((moy[:, None] - moy[np.linspace(0, len(cles) - 1, K).astype(int)][None]) ** 2).sum(2).argmin(1)
    for _ in range(tours):
        P = [kmoy(np.concatenate([px[k] for k, j in zip(cles, a) if j == q]) if (a == q).any() else np.zeros((1, 3)), NC)
             for q in range(K)]
        a2 = np.array([min(range(K), key=lambda q: erreur(px[k], P[q])) for k in cles])
        if (a2 == a).all(): break
        a = a2
    palettes = [[tuple(int(v) for v in c) for c in P[q]] for q in range(K)]
    d2 = lambda a_, b: sum((x - y) ** 2 for x, y in zip(a_, b))
    tuiles, carte = [], {}
    for k, q in zip(cles, a):
        Pq = palettes[q]
        idx = [0 if c is None else 1 + min(range(len(Pq)), key=lambda i: d2(Pq[i], c)) for c in grille[k]]
        carte[k] = (len(tuiles), int(q)); tuiles.append(idx)
    e = [max((d2(palettes[q][v - 1], c) for v, c in zip(tuiles[carte[k][0]], grille[k]) if c), default=0) for k, q in zip(cles, a)]
    print("  écart max par pixel (unités 4 bits, somme des carrés) : %d ; tuiles avec écart > 3 : %d / %d" %
          (max(e), sum(x > 3 for x in e), len(e)))
    return tuiles, palettes, carte


def ecrire(tuiles, palettes, carte, nom):
    d = os.path.join(paths.CACHE, "converti", "titre"); os.makedirs(d, exist_ok=True)
    b = bytearray()
    for t in tuiles:
        for i in range(0, 256, 2): b.append(t[i] | (t[i + 1] << 4))
    open(os.path.join(d, nom + "_tuiles.bin"), "wb").write(b)
    pb = bytearray()
    for n, P in enumerate(palettes):
        mots = [0] + [(r << 8) | (g << 4) | bl for r, g, bl in P] + [0] * (14 - len(P)) + [n]
        pb += struct.pack(">16H", *mots)
    open(os.path.join(d, nom + "_palettes.bin"), "wb").write(pb)
    js = {"largeur_tuiles": W // T, "hauteur_tuiles": H // T, "tuiles": len(tuiles), "palettes": len(palettes),
          "grille": [[(lambda v: None if v is None else {"tuile": v[0], "palette": v[1]})(carte.get((x, y)))
                      for x in range(W // T)] for y in range(H // T)]}
    json.dump(js, open(os.path.join(d, nom + "_carte.json"), "w"), indent=0)
    try:
        from PIL import Image
        im = Image.new("RGB", (W, H), (40, 40, 40))
        for (tx, ty), (n, p) in carte.items():
            P = palettes[p]
            for i, v in enumerate(tuiles[n]):
                if v: im.putpixel((tx * T + i % T, ty * T + i // T), tuple(c * 17 for c in P[v - 1]))
        im.save(os.path.join(d, nom + "_apercu.png"))
    except ImportError: pass
    return d


def main():
    chemin = sys.argv[1]; nom = sys.argv[2] if len(sys.argv) > 2 else "titre"
    K = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    img, pal = lire_pac(chemin)
    tuiles, palettes, carte = convertir(img, pal, K)
    d = ecrire(tuiles, palettes, carte, nom)
    print("%s : %d tuiles non vides, %d palettes de 16 -> %s" % (nom, len(tuiles), len(palettes), d))


if __name__ == "__main__":
    main()
