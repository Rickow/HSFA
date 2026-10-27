#!/usr/bin/env python3
"""REIMPORTATION « image -> tuiles CPS2 » d'un decor exporte par le pilote (py/export_decor.py).

Entrees : PSD au format du pilote (groupe par decor, sous-groupe par plan), dossier d'export du decor
(carte_tuiles.json, palettes.json), region :gfx de MAME (gfx/gfx_region.bin, 32 Mo).
Sorties (dossier --sortie) :
  carte_etendue.json     grille monde etendue par plan : [code, palette 0-31, flipX, flipY, prio, attr, origine]
                         (origine : o = d'origine, n = nouvelle, r = retouche reencodee, v = vide -> code blanc)
  table_codes.json       codes alloues : plan, code, decalage dans la region, cases servies
  palettes_nouvelles.json  palettes creees (mots CPS2, emplacement absolu $20-$7F)
  blocs/blk_XXXXXXX.bin  octets a ecrire dans la region (format interne MAME / fork) ; blocs.json ; hsfa_gfx.txt
  injection.lua          donnees pour lua/inject.lua (essai MAME)
  apercus : monde_<plan>_{psd,quantifie,recompose,ecart}.png, apercu_448_{gauche,droite}.png (+512), tuiles_<plan>.png
  rapport.json
Usage : venv/bin/python reimport/reimport.py --psd out/decors_sfa3.psd --export out/decor0C_temple_cloche --sortie ...
"""
import sys, os, json, argparse, collections, pickle
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import numpy as np
from PIL import Image
import cpsenc as E

EXCLUS = ("à combler", "animations", "VRAM hors course")       # calques d'aide du pilote (jamais lus)
CLE_PLAN = {1: "(scroll1", 2: "(scroll2", 3: "(scroll3"}
ORDRE_CPSB = (2, 3, 1)                                           # bas -> haut (layer control $1E0E du decor $0C)
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float64) / 16.0 - 15 / 32


# =====================================================================================================
# PSD
# =====================================================================================================
def lire_psd(path, motif):
    """-> (largeur, hauteur, {plan: rgba (H,W,4) uint8}, nom du groupe). Composite des calques de contenu du
    sous-groupe (tous les calques sauf les calques d'aide), visibilite et opacite respectees, mode normal."""
    from psd_tools import PSDImage
    p = PSDImage.open(path)
    W, H = p.width, p.height
    groupes = [g for g in p if g.is_group() and (motif is None or motif in g.name)]
    if not groupes:
        raise SystemExit("groupe de decor introuvable (motif %r)" % motif)
    g = groupes[0]
    res = {}
    for L, cle in CLE_PLAN.items():
        sg = [s for s in g if s.is_group() and cle in s.name]
        if not sg:
            raise SystemExit("sous-groupe du plan %s introuvable" % cle)
        acc = np.zeros((H, W, 4), np.float64)

        def visite(grp, opa):
            for l in grp:                                       # psd-tools : du BAS vers le HAUT
                if not l.visible: continue
                if l.is_group():
                    visite(l, opa * l.opacity / 255); continue
                if any(l.name.startswith(e) for e in EXCLUS): continue
                im = l.topil()
                if im is None: continue
                a = np.asarray(im.convert("RGBA"), np.float64)
                x0, y0 = l.left, l.top
                h, w = a.shape[:2]
                xs, ys = max(0, x0), max(0, y0)
                xe, ye = min(W, x0 + w), min(H, y0 + h)
                if xe <= xs or ye <= ys: continue
                src = a[ys - y0:ye - y0, xs - x0:xe - x0]
                al = src[:, :, 3:4] / 255 * (opa * l.opacity / 255)
                dst = acc[ys:ye, xs:xe]
                outa = al + dst[:, :, 3:4] / 255 * (1 - al)
                rgb = np.where(outa > 0, (src[:, :, :3] * al + dst[:, :, :3] * (dst[:, :, 3:4] / 255) * (1 - al))
                               / np.maximum(outa, 1e-9), 0)
                acc[ys:ye, xs:xe, :3] = rgb
                acc[ys:ye, xs:xe, 3:4] = outa * 255
        visite(sg[0], sg[0].opacity / 255)
        res[L] = np.rint(acc).clip(0, 255).astype(np.uint8)
    return W, H, res, g.name


# =====================================================================================================
# Donnees d'origine
# =====================================================================================================
class Plan:
    def __init__(self, L, cp, pj, region):
        self.L = L; self.ts = ts = cp["taille_tuile"]
        self.cases = cp["cases"]; self.R = cp["lignes"]; self.C = cp["colonnes"]
        m = cp["monde_tilemap_px"]; self.x0, self.y0 = m["x0"], m["y0"]
        self.ox, self.oy = cp["origine_dans_canevas_psd"]
        self.zones = cp["zones_a_combler"]
        # palettes du plan (32) : RGB de reference, mots, statut
        self.pal_rgb = np.zeros((32, 16, 3), np.uint8); self.pal_mot = np.zeros((32, 16), np.int64)
        self.anim = set(); self.utilisee = set()
        for p in range(32):
            e = pj["$%02X" % (E.PAL0[L] + p)]
            self.pal_rgb[p] = [[int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)] for h in e["rgb_ref"]]
            self.pal_mot[p] = [int(w, 16) for w in e["cps2_mots_ref"]]
            if e["nb_versions"] > 1: self.anim.add(p)
            if e["utilisee"]: self.utilisee.add(p)
        self.libres = [p for p in range(32) if p not in self.utilisee and p not in self.anim]
        # rendu d'origine (pens, palette, connu) dans l'espace grille (R*ts, C*ts)
        H, W = self.R * ts, self.C * ts
        self.pen = np.full((H, W), 15, np.uint8); self.pal = np.zeros((H, W), np.int64)
        self.connu = np.zeros((self.R, self.C), bool)
        self.codes_decor = collections.Counter()
        for r in range(self.R):
            for c in range(self.C):
                e = self.cases[r][c]
                if e is None: continue
                code, pal, fx, fy = e[0], e[1], e[2], e[3]
                t = E.flip(E.decode_tile(region, L, code, self.colabs(c)), fx, fy)
                self.pen[r*ts:(r+1)*ts, c*ts:(c+1)*ts] = t
                self.pal[r*ts:(r+1)*ts, c*ts:(c+1)*ts] = pal
                self.connu[r, c] = True
                self.codes_decor[code] += 1

    def colabs(self, c):          # colonne de tilemap (deroulee) de la colonne de grille c
        return self.x0 // self.ts + c

    def rowabs(self, r):
        return self.y0 // self.ts + r

    def rgba(self, pen, pal, pal_rgb):
        rgb = pal_rgb[pal, pen]
        a = np.where(pen != 15, 255, 0).astype(np.uint8)
        return np.dstack([rgb, a]).astype(np.uint8)


# =====================================================================================================
# Quantification
# =====================================================================================================
def kmeans_couleurs(cols, poids, k, it=25, graine=1):
    """k-moyennes ponderees sur des couleurs (n,3) -> centres (<=k,3)"""
    cols = cols.astype(np.float64); poids = poids.astype(np.float64)
    if len(cols) <= k:
        return cols.copy()
    rng = np.random.default_rng(graine)
    c0 = [cols[np.argmax(poids)]]
    for _ in range(1, k):                                      # k-means++ (deterministe : graine fixe)
        d = ((cols[:, None, :] - np.array(c0)[None]) ** 2).sum(2).min(1) * poids
        if d.sum() <= 0: break
        c0.append(cols[rng.choice(len(cols), p=d / d.sum())])
    cen = np.array(c0)
    for _ in range(it):
        a = ((cols[:, None, :] - cen[None]) ** 2).sum(2).argmin(1)
        new = np.array([np.average(cols[a == j], axis=0, weights=poids[a == j]) if (a == j).any() else cen[j]
                        for j in range(len(cen))])
        if np.allclose(new, cen): break
        cen = new
    return cen


def erreurs(tuiles, pals):
    """tuiles : liste de (couleurs uniques (n,3) int, comptes (n,)) ; pals : (P,15,3) -> SSE (T,P)"""
    out = np.zeros((len(tuiles), len(pals)))
    P = pals.astype(np.int64)
    for i, (cu, cn) in enumerate(tuiles):
        if len(cu) == 0: continue
        d = ((cu.astype(np.int64)[:, None, None, :] - P[None]) ** 2).sum(3).min(2)   # (n, P)
        out[i] = (d * cn[:, None]).sum(0)
    return out


def palette_cps2(cen):
    """centres -> 15 couleurs CPS2 distinctes (+ mots) ; complete par du noir"""
    mots, rgb = E.vers_cps2(np.rint(cen))
    vu = {}
    for m, c in zip(mots, rgb):
        vu.setdefault(tuple(c), m)
    items = list(vu.items())[:15]
    cols = [list(c) for c, m in items]; ms = [int(m) for c, m in items]
    while len(cols) < 15:
        cols.append(list(cols[-1]) if cols else [0, 0, 0]); ms.append(ms[-1] if ms else 0xF000)
    return np.array(cols, np.uint8), ms


def nouvelles_palettes(tuiles, k, graine=1, iters=8):
    """regroupe les tuiles en k palettes de 15 couleurs (k-moyennes sur les tuiles, palette = k-moyennes
    ponderees des pixels du groupe). -> (pals (k,15,3), mots [k][15], affectation (T,))"""
    T = len(tuiles)
    # initialisation : histogramme grossier 4x4x4 de chaque tuile, k-moyennes sur ces histogrammes
    feat = np.zeros((T, 64))
    for i, (cu, cn) in enumerate(tuiles):
        b = (cu // 64).astype(np.int64)
        np.add.at(feat[i], b[:, 0] * 16 + b[:, 1] * 4 + b[:, 2], cn)
        feat[i] /= max(1, cn.sum())
    k = min(k, T)
    aff = np.zeros(T, np.int64)
    if k > 1:
        cen = kmeans_couleurs(feat, np.ones(T), k, graine=graine) if T > k else feat.copy()
        aff = ((feat[:, None, :] - cen[None]) ** 2).sum(2).argmin(1)
    best = None
    for _ in range(iters):
        pals, mots = [], []
        for j in range(k):
            sel = [i for i in range(T) if aff[i] == j]
            if not sel:                                          # groupe vide : la tuile la plus mal servie
                sel = [int(np.argmax(erreurs(tuiles, np.array(pals)).min(1)))] if pals else [0]
            cu = np.concatenate([tuiles[i][0] for i in sel]); cn = np.concatenate([tuiles[i][1] for i in sel])
            u, inv = np.unique(cu, axis=0, return_inverse=True)
            w = np.bincount(inv.reshape(-1), weights=cn)
            pr, m = palette_cps2(kmeans_couleurs(u, w, 15, graine=graine + j))
            pals.append(pr); mots.append(m)
        pals = np.array(pals)
        err = erreurs(tuiles, pals)
        aff2 = err.argmin(1); tot = err.min(1).sum()
        if best is None or tot < best[0]:
            best = (tot, pals, mots, aff2.copy())
        if np.array_equal(aff2, aff): break
        aff = aff2
    return best[1], best[2], best[3]


def pens_tuile(rgba, palrgb, dither, wx, wy, force):
    """tuile RGBA (ts,ts,4) -> pens (pens 0-14 opaques ; 15 transparent). A couleur egale, le plus petit pen."""
    ts = rgba.shape[0]
    rgb = rgba[:, :, :3].astype(np.float64)
    if dither:
        yy, xx = np.mgrid[0:ts, 0:ts]
        rgb = rgb + BAYER4[(wy + yy) % 4, (wx + xx) % 4][:, :, None] * force
    d = ((rgb[:, :, None, :] - palrgb[None, None, :15, :].astype(np.float64)) ** 2).sum(3)
    p = d.argmin(2).astype(np.uint8)
    return np.where(rgba[:, :, 3] >= 128, p, 15).astype(np.uint8)


def canon(palrgb):
    """pen -> plus petit pen de meme couleur (pens 0-14) ; 15 -> 15"""
    c = np.arange(16, dtype=np.uint8)
    for i in range(15):
        for j in range(i):
            if (palrgb[j] == palrgb[i]).all():
                c[i] = c[j]; break
    return c


# =====================================================================================================
# Places libres dans la region
# =====================================================================================================
class Libre:
    """carte des octets libres de la region (True = libre) ; allocation alignee par plan"""
    def __init__(self, n):
        self.ok = np.zeros(n, bool)

    def ajoute(self, a, b):
        self.ok[a:b] = True

    def retire(self, a, b):
        self.ok[a:b] = False

    def codes(self, L, base=None):
        """codes du plan dont tous les octets sont libres"""
        n = E.code_max(L); tb = E.TB[L]
        o0 = E.offset(L, 0, base)
        blk = self.ok[o0:o0 + n * tb].reshape(n, tb).all(1)
        return np.nonzero(blk)[0]

    def prend(self, L, n, depuis_fin=False, base=None):
        cs = self.codes(L, base)
        if depuis_fin: cs = cs[::-1]
        if len(cs) < n:
            raise SystemExit("PLUS DE PLACE pour le plan %d : %d codes demandes, %d libres" % (L, n, len(cs)))
        cs = sorted(int(c) for c in cs[:n])
        for c in cs:
            o = E.offset(L, c, base); self.retire(o, o + E.TB[L])
        return cs


def places_libres(region, codes_utilises, spec=None):
    """par defaut : (a) le bourrage $FF de la fin du quart des plans ($FF3000-$FFFFFF : scroll2/scroll3),
    (b) pour scroll1 (adressable sous $C00000 seulement) les series de >= 8 blocs de 64 o tout a $FF.
    On retire les octets de toute tuile referencee dans le releve (codes_utilises)."""
    g = np.frombuffer(region, np.uint8)
    lib = Libre(len(g))
    if spec:
        for part in spec.split(","):
            a, b = part.split("-"); lib.ajoute(int(a, 16), int(b, 16))
    else:
        q = g[E.QUART:2 * E.QUART]
        nz = np.nonzero(q != 0xFF)[0]
        fin = E.QUART + int(nz[-1]) + 1
        fin = (fin + 511) // 512 * 512
        lib.ajoute(fin, 2 * E.QUART)
        b64 = (g[E.QUART:E.QUART + 0x400000].reshape(-1, 64) == 0xFF).all(1)
        idx = np.nonzero(b64)[0]
        if len(idx):
            br = np.nonzero(np.diff(idx) != 1)[0]
            st = np.r_[idx[0], idx[br + 1]]; en = np.r_[idx[br], idx[-1]]
            for a, b in zip(st, en):
                if b - a + 1 >= 8:
                    lib.ajoute(E.QUART + 64 * int(a), E.QUART + 64 * (int(b) + 1))
    for L, cs in codes_utilises.items():
        for c in cs:
            o = E.offset(L, c); lib.retire(o, o + E.TB[L])
    return lib


def codes_du_releve(rec, cache):
    """tous les codes presents dans les 3 tilemaps sur toutes les images du releve (rec2/full.rec)"""
    if cache and os.path.exists(cache):
        return {int(k): v for k, v in json.load(open(cache)).items()}
    sys.path[:0] = [os.path.join(D, "py"), os.path.join(D, "export")]
    from recio import read_rec
    import cpsgfx as G
    fr = read_rec(rec)
    out = {1: set(), 2: set(), 3: set()}
    for f in fr:
        for L in (1, 2, 3):
            base = (f.reg(G.LAYERS[L]["base"]) << 8) & 0xffc000
            o0 = (base - 0x900000) // 2
            out[L].update(np.unique(f.vram[o0:o0 + 8192:2]).tolist())
    out = {L: sorted(int(x) for x in v) for L, v in out.items()}
    if cache:
        os.makedirs(os.path.dirname(cache), exist_ok=True); json.dump(out, open(cache, "w"))
    return out


# =====================================================================================================
# Principal
# =====================================================================================================
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--psd", default=os.path.join(D, "out/decors_sfa3.psd"))
    ap.add_argument("--groupe", default="$0C", help="motif du nom du groupe de decor dans le PSD")
    ap.add_argument("--export", default=os.path.join(D, "out/decor0C_temple_cloche"))
    ap.add_argument("--gfx", default=os.path.join(D, "gfx/gfx_region.bin"))
    ap.add_argument("--rec", default=os.path.join(D, "rec2/full.rec"), help="releve (codes utilises a proteger)")
    ap.add_argument("--monde", default=os.path.join(D, "work/monde.pkl"), help="pour la position Y nominale des apercus")
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--tramage", choices=("aucun", "ordonne"), default="aucun")
    ap.add_argument("--force-tramage", type=float, default=24.0, help="amplitude du tramage ordonne (0-255)")
    ap.add_argument("--seuil", type=float, default=6.0,
                    help="erreur RMS (RVB 0-255, par pixel opaque) acceptee pour reutiliser une palette existante")
    ap.add_argument("--palettes-animees", choices=("exact", "jamais", "toujours"), default="exact",
                    help="reutiliser une palette animee : seulement si la tuile y est exacte (defaut), jamais, toujours")
    ap.add_argument("--retouches", choices=("ignorer", "reencoder"), default="ignorer",
                    help="cases d'origine modifiees dans le PSD : garder l'origine (defaut) ou les reencoder")
    ap.add_argument("--zone", choices=("tout", "448", "512"), default="tout",
                    help="cases nouvelles a encoder : toutes celles qui ont du contenu, ou seulement la bande 448/512")
    ap.add_argument("--decor", default="0C", help="numero de decor ($100(A5) = $FF8100), pour les palettes propres")
    ap.add_argument("--prog", default="<workspace>/work/cps2/sfa3ud_prog.bin",
                    help="programme 68000 (palettes propres du decor) ; 'aucun' = ne pas restreindre")
    ap.add_argument("--palettes-libres", default=None,
                    help="emplacements de palettes utilisables, ex. '7A,7D' (sinon : non utilises, non animes, PROPRES au decor)")
    ap.add_argument("--libres", default=None, help="places libres de la region : 'debut-fin,...' en hexa (sinon auto)")
    a = ap.parse_args(argv)

    os.makedirs(a.sortie, exist_ok=True); os.makedirs(os.path.join(a.sortie, "blocs"), exist_ok=True)
    region = open(a.gfx, "rb").read()
    carte = json.load(open(os.path.join(a.export, "carte_tuiles.json")))
    palj = json.load(open(os.path.join(a.export, "palettes.json")))
    CW, CH, psd, gnom = lire_psd(a.psd, a.groupe)
    assert [CW, CH] == carte["canevas_psd"], "canevas PSD %dx%d != carte %s" % (CW, CH, carte["canevas_psd"])
    rapport = dict(psd=a.psd, groupe=gnom, options=vars(a), plans={})
    plans = {L: Plan(L, carte["plans"][E.NOM[L]], palj["plans"][E.NOM[L]], region) for L in (1, 2, 3)}
    # emplacements de palettes : un emplacement « non utilise » au-dela du bloc propre du decor appartient a un AUTRE
    # decor (la routine du jeu copie toujours 32 palettes) -> interdit
    if a.palettes_libres is not None:
        lp = {int(x, 16) for x in a.palettes_libres.split(",") if x}
        for L, P in plans.items(): P.libres = [p for p in range(32) if E.PAL0[L] + p in lp]
    elif a.prog != "aucun":
        import blocs as BL
        dprog = open(a.prog, "rb").read()
        for L, P in plans.items():
            adr, n = BL.palettes_bloc(dprog, L, int(a.decor, 16))
            P.libres = [p for p in P.libres if p < n]
            rapport["plans"].setdefault(E.NOM[L], {})["palettes_propres"] = dict(bloc="$%06X" % adr, nombre=n)
    for L, P in plans.items():
        print("plan %d : emplacements de palettes libres %s" % (L, ["$%02X" % (E.PAL0[L] + p) for p in P.libres]))
    utilises = codes_du_releve(a.rec, os.path.join(HERE, "cache", "codes_releve.json")) if os.path.exists(a.rec) else {}
    for L, P in plans.items():
        utilises.setdefault(L, [])
        utilises[L] = sorted(set(utilises[L]) | set(P.codes_decor))
    libre = places_libres(region, utilises, a.libres)

    travail = {}
    for L in (1, 2, 3):
        P = plans[L]; ts = P.ts
        H, W = P.R * ts, P.C * ts
        # image PSD dans l'espace grille ; pixels hors canevas = sans importance (jamais visibles dans la course)
        img = np.zeros((H, W, 4), np.uint8); dans = np.zeros((H, W), bool)
        ys, xs = max(0, P.oy), max(0, P.ox)
        ye, xe = min(CH, P.oy + H), min(CW, P.ox + W)
        img[ys - P.oy:ye - P.oy, xs - P.ox:xe - P.ox] = psd[L][ys:ye, xs:xe]
        dans[ys - P.oy:ye - P.oy, xs - P.ox:xe - P.ox] = True
        # bords hors canevas : on prolonge la derniere ligne/colonne (aide la deduplication, invisible)
        if not dans.all():
            rr = np.nonzero(dans.any(1))[0]; cc = np.nonzero(dans.any(0))[0]
            iy = np.clip(np.arange(H), rr.min(), rr.max()); ix = np.clip(np.arange(W), cc.min(), cc.max())
            img = img[iy][:, ix]
        opq = img[:, :, 3] >= 128
        orig = P.rgba(P.pen, P.pal, P.pal_rgb)
        oo = P.pen != 15
        # ---- 1. pixels d'origine : inchanges ? ----
        connu_px = np.kron(P.connu, np.ones((ts, ts), bool)) & dans
        diff = connu_px & ((opq != oo) | (opq & oo & (img[:, :, :3] != orig[:, :, :3]).any(2)))
        retouches = sorted({(int(y) // ts, int(x) // ts) for y, x in zip(*np.nonzero(diff))})
        # ---- 2. cases a encoder ----
        zone_ok = np.ones((P.R, P.C), bool)
        if a.zone != "tout":
            z = P.zones[a.zone]; zm = np.zeros((H, W), bool)
            for side in ("gauche", "droite"):
                if z[side]:
                    zm[z["lignes"][0] - P.oy:z["lignes"][1] - P.oy, z[side][0] - P.ox:z[side][1] - P.ox] = True
            zone_ok = zm.reshape(P.R, ts, P.C, ts).any((1, 3))
        # cases null dans carte_tuiles.json mais presentes dans les donnees de decor du programme (le pilote les
        # dessine dans le PSD : « completees par colonne ») : si le PSD les montre a l'identique (lignes du canevas),
        # ce sont des cases d'origine -> reprises du programme, pas reencodees
        repris = 0
        if a.prog != "aucun":
            import blocs as BL
            Tp = BL.cases_tilemap(open(a.prog, "rb").read(), L, int(a.decor, 16))
            WT = {1: 128, 2: 64, 3: 64}[L]
            for r in range(P.R):
                for c in range(P.C):
                    if P.connu[r, c]: continue
                    v = Tp.get(((P.colabs(c)) % WT, P.rowabs(r) % 64))
                    if v is None: continue
                    t = E.flip(E.decode_tile(region, L, v[0], P.colabs(c)), v[1] & 0x20, v[1] & 0x40)
                    sl = (slice(r*ts, (r+1)*ts), slice(c*ts, (c+1)*ts))
                    m = dans[sl]
                    rg = P.rgba(t, np.full_like(t, v[1] & 0x1F, dtype=np.int64), P.pal_rgb)
                    ps = img[sl]
                    same = ((rg[:, :, 3] == 255) == (ps[:, :, 3] >= 128)) & (
                        (rg[:, :, 3] == 0) | (rg[:, :, :3] == ps[:, :, :3]).all(2))
                    if (same | ~m).all() and m.any():
                        P.cases[r][c] = [v[0], v[1] & 0x1F, (v[1] >> 5) & 1, (v[1] >> 6) & 1, (v[1] >> 7) & 3, v[1]]
                        P.connu[r, c] = True; P.pen[sl] = t; P.pal[sl] = v[1] & 0x1F; repris += 1
                        P.codes_decor[v[0]] += 1
            if repris:
                orig = P.rgba(P.pen, P.pal, P.pal_rgb); oo = P.pen != 15
        cell_opq = (opq & dans).reshape(P.R, ts, P.C, ts).any((1, 3))
        cells = {}                          # (r,c) -> origine 'n' / 'r' / 'v'
        ignorees = []
        for r in range(P.R):
            for c in range(P.C):
                if P.connu[r, c]:
                    if a.retouches == "reencoder" and (r, c) in retouches: cells[(r, c)] = "r"
                    continue
                if not cell_opq[r, c]: cells[(r, c)] = "v"
                elif zone_ok[r, c]: cells[(r, c)] = "n"
                else: cells[(r, c)] = "v"; ignorees.append((r, c))
        travail[L] = dict(img=img, opq=opq, dans=dans, orig=orig, diff=diff, retouches=retouches, cells=cells,
                          ignorees=ignorees, repris=repris)
        print("plan %d : %d cases reprises du programme (completees du pilote) ;" % (L, repris))
        print("plan %d : %d cases d'origine, %d retouchees (%d px), %d nouvelles, %d vides, %d ignorees (hors zone)"
              % (L, int(P.connu.sum()), len(retouches), int(diff.sum()),
                 sum(1 for v in cells.values() if v == "n"), sum(1 for v in cells.values() if v == "v"), len(ignorees)))

    # ---- 3. quantification par plan ----
    nouv_pal = {}
    for L in (1, 2, 3):
        P = plans[L]; Tw = travail[L]; ts = P.ts
        aenc = [rc for rc, o in sorted(Tw["cells"].items()) if o in "nr"]
        tuiles = []
        for (r, c) in aenc:
            t = Tw["img"][r*ts:(r+1)*ts, c*ts:(c+1)*ts]
            m = t[:, :, 3] >= 128
            cu, cn = np.unique(t[:, :, :3][m].reshape(-1, 3), axis=0, return_counts=True)
            tuiles.append((cu.astype(np.int64), cn))
        cand = [p for p in range(32) if p in P.utilisee and (p not in P.anim or a.palettes_animees != "jamais")]
        pals = np.array([P.pal_rgb[p, :15] for p in cand])
        npx = np.array([max(1, cn.sum()) for cu, cn in tuiles]) if tuiles else np.zeros(0)
        choix = {}
        if tuiles:
            err = erreurs(tuiles, pals)
            if a.palettes_animees == "exact":            # palettes animees : seulement en cas d'egalite exacte
                for j, p in enumerate(cand):
                    if p in P.anim: err[err[:, j] > 0, j] = np.inf
            bi = err.argmin(1); rms = np.sqrt(err.min(1) / npx)
            mal = [i for i in range(len(tuiles)) if rms[i] > a.seuil]
            for i in range(len(tuiles)):
                choix[i] = cand[bi[i]]
            nouvelles = []
            if mal:
                sub = [tuiles[i] for i in mal]
                meilleur = None
                for k in range(1, len(P.libres) + 1):
                    npal, mots, aff = nouvelles_palettes(sub, k)
                    allp = np.concatenate([pals, npal])
                    e2 = erreurs(sub, allp)
                    for j, p in enumerate(cand):
                        if p in P.anim and a.palettes_animees == "exact": e2[e2[:, j] > 0, j] = np.inf
                    r2 = np.sqrt(e2.min(1) / npx[mal])
                    meilleur = (k, npal, mots, e2)
                    if r2.max() <= a.seuil: break
                if meilleur is None:
                    print("plan %d : %d tuiles hors seuil mais AUCUN emplacement de palette libre" % (L, len(mal)))
                else:
                    k, npal, mots, e2 = meilleur
                    slots = P.libres[:k]
                    utilises_k = set()
                    for ii, i in enumerate(mal):
                        j = int(e2[ii].argmin())
                        if j >= len(cand):
                            choix[i] = slots[j - len(cand)]; utilises_k.add(j - len(cand))
                        else:
                            choix[i] = cand[j]
                    for q in range(k):
                        if q not in utilises_k: continue
                        p = slots[q]
                        P.pal_rgb[p, :15] = npal[q]; P.pal_mot[p, :15] = mots[q]
                        nouvelles.append(p)
            nouv_pal[L] = nouvelles
        else:
            nouv_pal[L] = []
        # pens finals
        Tw["aenc"] = aenc; Tw["choix"] = {aenc[i]: p for i, p in choix.items()}
        Tw["pens"] = {}
        for (r, c) in aenc:
            p = Tw["choix"][(r, c)]
            t = Tw["img"][r*ts:(r+1)*ts, c*ts:(c+1)*ts]
            q = pens_tuile(t, P.pal_rgb[p], a.tramage == "ordonne", P.x0 + c*ts, P.y0 + r*ts, a.force_tramage)
            Tw["pens"][(r, c)] = canon(P.pal_rgb[p])[q]
        print("plan %d : %d tuiles a encoder ; palettes reutilisees %s ; nouvelles %s" % (
            L, len(aenc), sorted({"$%02X" % (E.PAL0[L] + p) for p in Tw["choix"].values() if p not in nouv_pal[L]}),
            ["$%02X" % (E.PAL0[L] + p) for p in nouv_pal[L]]))

    # ---- 4. deduplication (retournements X/Y) contre la ROM, puis entre tuiles nouvelles ----
    alloc = {}
    for L in (3, 2, 1):                                         # 32x32 d'abord (gros blocs)
        P = plans[L]; Tw = travail[L]; ts = P.ts
        rom = E.decode_all(region, L)                           # (N, ts, ts) ou (N, 2, 8, 8)
        index = {}
        def idx_pal(p, par):
            key = (canon(P.pal_rgb[p]).tobytes(), par)
            if key not in index:
                cmap = canon(P.pal_rgb[p])
                tl = rom[:, par] if L == 1 else rom
                ct = cmap[tl].reshape(len(tl), -1)
                d = {}
                pref = set(P.codes_decor)
                for code in range(len(ct)):
                    k = ct[code].tobytes()
                    if k not in d or (code in pref and d[k] not in pref):
                        d[k] = code
                index[key] = d
            return index[key]
        neuves = {}                                             # (cle pens, parite) -> indice de tuile neuve
        liste = []                                              # tuiles neuves : (pens, parite)
        res = {}
        nrom = nnew = ndup = 0
        for (r, c) in Tw["aenc"]:
            q = Tw["pens"][(r, c)]; p = Tw["choix"][(r, c)]
            par = P.colabs(c) & 1 if L == 1 else 0
            d = idx_pal(p, par)
            trouve = None
            for fx in (0, 1):
                for fy in (0, 1):
                    k = E.flip(q, fx, fy).tobytes()
                    if k in d: trouve = ("rom", d[k], fx, fy); break
                if trouve: break
            if trouve is None:
                for fx in (0, 1):
                    for fy in (0, 1):
                        k = (E.flip(q, fx, fy).tobytes(), par)
                        if k in neuves: trouve = ("neuve", neuves[k], fx, fy); break
                    if trouve: break
                if trouve: ndup += 1
            else:
                nrom += 1
            if trouve is None:
                neuves[(q.tobytes(), par)] = len(liste); liste.append((q, par)); nnew += 1
                trouve = ("neuve", len(liste) - 1, 0, 0)
            res[(r, c)] = (trouve, p)
        # cases vides -> code blanc (tuile tout pen 15 deja utilisee par le decor)
        blanc = None
        for code, _ in P.codes_decor.most_common():
            t = rom[code]
            if (t == 15).all(): blanc = code; break
        if blanc is None: blanc = idx_pal(0, 0).get(np.full((ts, ts) if L != 1 else (8, 8), 15, np.uint8).tobytes())
        # allocation des codes des tuiles neuves
        if L == 1:
            paires = [i for i, (q, par) in enumerate(liste) if par == 0]
            impaires = [i for i, (q, par) in enumerate(liste) if par == 1]
            n = max(len(paires), len(impaires))
            codes = libre.prend(1, n)
            code_de = {}; blocs = []
            for k in range(n):
                a_ = liste[paires[k]][0] if k < len(paires) else None
                b_ = liste[impaires[k]][0] if k < len(impaires) else None
                if k < len(paires): code_de[paires[k]] = codes[k]
                if k < len(impaires): code_de[impaires[k]] = codes[k]
                blocs.append((codes[k], E.encode_code(1, (a_, b_))))
        else:
            codes = libre.prend(L, len(liste), depuis_fin=(L == 3))
            code_de = {i: codes[i] for i in range(len(liste))}
            blocs = [(codes[i], E.encode_code(L, liste[i][0])) for i in range(len(liste))]
        alloc[L] = dict(res=res, liste=liste, code_de=code_de, blocs=blocs, blanc=blanc, nrom=nrom, nnew=nnew, ndup=ndup)
        print("plan %d : %d cases -> %d tuiles d'origine reutilisees, %d doublons de tuiles neuves, %d tuiles neuves "
              "-> %d codes alloues %s ; code blanc $%X" % (L, len(res), nrom, ndup, nnew, len(blocs),
                                                       ("$%X-$%X" % (min(codes), max(codes))) if blocs else "", blanc))

    # ---- 5. carte etendue ----
    carte_ext = {"decor": carte["decor"], "canevas_psd": carte["canevas_psd"],
                 "format_case": "[code, palette 0-31, flipX, flipY, groupe prio, attr brut, origine (o/n/r/v)]",
                 "plans": {}}
    tab_codes = []
    for L in (1, 2, 3):
        P = plans[L]; Tw = travail[L]; A = alloc[L]; ts = P.ts
        prio_def = collections.Counter(e[5] for row in P.cases for e in row if e).most_common(1)[0][0]
        grid = []
        for r in range(P.R):
            ligne = []
            for c in range(P.C):
                e = P.cases[r][c]
                o = Tw["cells"].get((r, c), "o")
                if o == "o":
                    ligne.append(list(e) + ["o"]); continue
                # attributs hors palette/flip : ceux de la case connue la plus proche sur la meme ligne
                voisins = [(abs(cc - c), P.cases[r][cc][5]) for cc in range(P.C) if P.cases[r][cc]]
                attr0 = min(voisins)[1] if voisins else prio_def
                if o == "v":
                    code, pal, fx, fy = A["blanc"], 0, 0, 0
                else:
                    (kind, ref, fx, fy), pal = A["res"][(r, c)]
                    code = ref if kind == "rom" else A["code_de"][ref]
                attr = (attr0 & ~0x7F) | pal | (fx << 5) | (fy << 6)
                ligne.append([code, pal, fx, fy, (attr >> 7) & 3, attr, o])
            grid.append(ligne)
        cp = carte["plans"][E.NOM[L]]
        carte_ext["plans"][E.NOM[L]] = dict(taille_tuile=ts, monde_tilemap_px=cp["monde_tilemap_px"],
                                            colonnes=P.C, lignes=P.R, origine_dans_canevas_psd=cp["origine_dans_canevas_psd"],
                                            base_vram=cp["base_vram"], code_blanc=A["blanc"],
                                            palettes_nouvelles=["$%02X" % (E.PAL0[L] + p) for p in nouv_pal[L]],
                                            cases=grid)
        servies = collections.defaultdict(list)
        for (r, c), ((kind, ref, fx, fy), pal) in A["res"].items():
            if kind == "neuve": servies[A["code_de"][ref]].append([r, c])
        for code, raw in A["blocs"]:
            tab_codes.append(dict(plan=E.NOM[L], code="$%04X" % code, decalage_region="$%07X" % E.offset(L, code),
                                  octets=len(raw), cases=servies[code]))
        P.grid_ext = grid
    json.dump(carte_ext, open(os.path.join(a.sortie, "carte_etendue.json"), "w"), ensure_ascii=False)
    json.dump(tab_codes, open(os.path.join(a.sortie, "table_codes.json"), "w"), indent=0, ensure_ascii=False)
    pals_out = {E.NOM[L]: {"$%02X" % (E.PAL0[L] + p): ["%04X" % int(w) for w in plans[L].pal_mot[p]]
                           for p in nouv_pal[L]} for L in (1, 2, 3)}
    json.dump(pals_out, open(os.path.join(a.sortie, "palettes_nouvelles.json"), "w"), indent=1)

    # ---- 6. blocs d'octets (region) ----
    patched = bytearray(region)
    ecr = []
    for L in (1, 2, 3):
        for code, raw in alloc[L]["blocs"]:
            o = E.offset(L, code)
            assert all(b == 0xFF for b in region[o:o + len(raw)]), "place non libre %x" % o
            patched[o:o + len(raw)] = raw; ecr.append((o, raw))
    ecr.sort()
    blocs = []
    for o, raw in ecr:
        if blocs and blocs[-1][0] + len(blocs[-1][1]) == o: blocs[-1][1].extend(raw)
        else: blocs.append([o, bytearray(raw)])
    bl_json = []
    for o, raw in blocs:
        nom = "blk_%07X.bin" % o
        open(os.path.join(a.sortie, "blocs", nom), "wb").write(raw)
        bl_json.append(dict(fichier="blocs/" + nom, decalage_region="$%07X" % o, octets=len(raw)))
    json.dump(bl_json, open(os.path.join(a.sortie, "blocs.json"), "w"), indent=1)
    open(os.path.join(a.sortie, "hsfa_gfx.txt"), "w").write(
        ",".join("%s@%X" % (os.path.join(os.path.abspath(a.sortie), b["fichier"]), int(b["decalage_region"][1:], 16))
                 for b in bl_json) + "\n")
    assert sum(1 for x, y in zip(region, patched) if x != y) <= sum(len(r) for _, r in ecr)

    # ---- 7. controle : recomposition depuis les tuiles ENCODEES = image quantifiee, au pixel ----
    ctrl = {}
    for L in (1, 2, 3):
        P = plans[L]; Tw = travail[L]; ts = P.ts
        H, W = P.R * ts, P.C * ts
        pen_r = np.full((H, W), 15, np.uint8); pal_r = np.zeros((H, W), np.int64)
        pen_q = P.pen.copy(); pal_q = P.pal.copy()
        for r in range(P.R):
            for c in range(P.C):
                e = P.grid_ext[r][c]
                t = E.flip(E.decode_tile(patched, L, e[0], P.colabs(c)), e[2], e[3])
                pen_r[r*ts:(r+1)*ts, c*ts:(c+1)*ts] = t; pal_r[r*ts:(r+1)*ts, c*ts:(c+1)*ts] = e[1]
                o = e[6]
                if o in "nr":
                    pen_q[r*ts:(r+1)*ts, c*ts:(c+1)*ts] = Tw["pens"][(r, c)]
                    pal_q[r*ts:(r+1)*ts, c*ts:(c+1)*ts] = Tw["choix"][(r, c)]
                elif o == "v":
                    pen_q[r*ts:(r+1)*ts, c*ts:(c+1)*ts] = 15
        rec_ = P.rgba(pen_r, pal_r, P.pal_rgb); qua = P.rgba(pen_q, pal_q, P.pal_rgb)
        dq = (rec_ != qua).any(2)
        # erreur de quantification sur les cases nouvelles (pixels du canevas)
        newm = np.zeros((H, W), bool)
        for (r, c), o in Tw["cells"].items():
            if o in "nr": newm[r*ts:(r+1)*ts, c*ts:(c+1)*ts] = True
        newm &= Tw["dans"]
        img = Tw["img"]
        both = newm & Tw["opq"] & (qua[:, :, 3] == 255)
        de = np.sqrt(((img[:, :, :3].astype(int) - qua[:, :, :3]) ** 2).sum(2))
        transp_err = int((newm & (Tw["opq"] != (qua[:, :, 3] == 255))).sum())
        orig_ok = int(((rec_ != Tw["orig"]).any(2) & np.kron(P.connu, np.ones((ts, ts), bool))
                       & ~np.kron(np.array([[Tw["cells"].get((r, c)) == "r" for c in range(P.C)] for r in range(P.R)]),
                                  np.ones((ts, ts), bool))).sum())
        ctrl[E.NOM[L]] = dict(recompose_vs_quantifie_px=int(dq.sum()), origine_vs_recompose_px=orig_ok,
                              cases_nouvelles=sum(1 for v in Tw["cells"].values() if v == "n"),
                              px_nouveaux_opaques=int(both.sum()),
                              erreur_rms=round(float(np.sqrt((de[both] ** 2).mean())) if both.any() else 0.0, 2),
                              erreur_max=round(float(de[both].max()) if both.any() else 0.0, 1),
                              px_exacts_pct=round(100 * float((de[both] == 0).mean()) if both.any() else 100.0, 2),
                              erreurs_transparence_px=transp_err,
                              retouches_cases=len(Tw["retouches"]), retouches_px=int(Tw["diff"].sum()),
                              retouches_liste=[list(x) for x in Tw["retouches"][:200]],
                              tuiles_reutilisees_rom=alloc[L]["nrom"], tuiles_neuves=alloc[L]["nnew"],
                              doublons_neuves=alloc[L]["ndup"], codes_alloues=len(alloc[L]["blocs"]),
                              octets=sum(len(r) for _, r in alloc[L]["blocs"]),
                              palettes_nouvelles=["$%02X" % (E.PAL0[L] + p) for p in nouv_pal[L]],
                              cases_ignorees_hors_zone=len(Tw["ignorees"]), cases_reprises_du_programme=Tw["repris"])
        Tw["rec"] = rec_; Tw["qua"] = qua
        # images de controle (espace canevas)
        def canv(arr):
            out = np.zeros((CH, CW) + arr.shape[2:], arr.dtype)
            ys, xs = max(0, P.oy), max(0, P.ox); ye, xe = min(CH, P.oy + H), min(CW, P.ox + W)
            out[ys:ye, xs:xe] = arr[ys - P.oy:ye - P.oy, xs - P.ox:xe - P.ox]
            return out
        Tw["canv"] = canv
        n = E.NOM[L]
        Image.fromarray(canv(img)).save(os.path.join(a.sortie, "monde_%s_psd.png" % n))
        Image.fromarray(canv(qua)).save(os.path.join(a.sortie, "monde_%s_quantifie.png" % n))
        Image.fromarray(canv(rec_)).save(os.path.join(a.sortie, "monde_%s_recompose.png" % n))
        ec = np.zeros((H, W, 4), np.uint8)
        ec[Tw["diff"]] = (255, 0, 255, 255)
        dd = np.clip(de * 4, 0, 255).astype(np.uint8)
        ec[both] = np.stack([dd[both], dd[both], dd[both], np.full(both.sum(), 255, np.uint8)], 1)
        ec[dq] = (255, 0, 0, 255)
        Image.fromarray(canv(ec)).save(os.path.join(a.sortie, "monde_%s_ecart.png" % n))
        # planche des tuiles neuves
        lst = alloc[L]["blocs"]
        if lst:
            per = 16; tw = 16 if L == 1 else ts
            sh = np.zeros((((len(lst) + per - 1) // per) * (ts + 2), per * (tw + 2), 3), np.uint8); sh[:] = (40, 0, 40)
            for k, (code, raw) in enumerate(lst):
                px = E.dec_rows(raw, ts, tw)
                g_ = (px.astype(np.uint16) * 16).clip(0, 255).astype(np.uint8)
                rgb = np.where((px != 15)[:, :, None], np.dstack([g_, g_, g_]), 0)
                y, x = (k // per) * (ts + 2), (k % per) * (tw + 2)
                sh[y:y + ts, x:x + tw] = rgb
            Image.fromarray(sh).resize((sh.shape[1] * 2, sh.shape[0] * 2), Image.NEAREST).save(
                os.path.join(a.sortie, "tuiles_neuves_%s.png" % n))
        print("CONTROLE %s" % n, {k: v for k, v in ctrl[n].items() if k != "retouches_liste"})

    # ---- 8. apercus 448x224 (et 512) aux deux butees de camera ----
    ytop = 16
    try:
        Wm = pickle.load(open(a.monde, "rb"))
        ref = json.load(open(os.path.join(a.export, "controle.json")))["ref"]
        ytop = Wm[3]["scroll_y"][ref] - min(Wm[3]["scroll_y"])
    except Exception as ex:
        print("ytop par defaut (16) :", ex)
    MX = 64; course = CW - 2 * MX - 384
    for larg in (448, 512):
        e = (larg - 384) // 2
        for nom, x0 in (("gauche", MX - e), ("droite", MX + course - e)):
            for quoi in ("rec", "orig"):
                im = np.zeros((224, larg, 3), np.uint8)
                for L in ORDRE_CPSB:
                    Tw = travail[L]
                    src = Tw["canv"](Tw["rec"] if quoi == "rec" else Tw["orig"])[ytop:ytop + 224, x0:x0 + larg]
                    m = src[:, :, 3] == 255
                    im[m] = src[:, :, :3][m]
                big = Image.fromarray(im).resize((larg * 2, 448), Image.NEAREST)
                big.save(os.path.join(a.sortie, "apercu_%d_%s%s.png" % (larg, nom, "" if quoi == "rec" else "_avant")))

    # ---- 9. donnees pour l'essai MAME (lua/inject.lua) ----
    with open(os.path.join(a.sortie, "injection.lua"), "w") as f:
        f.write("-- genere par reimport.py : cases nouvelles/vides (tilemap), palettes, octets de la region gfx\nreturn {\n")
        f.write(" blocs = {\n")
        for o, raw in blocs:
            f.write('  {off=0x%X, hex="%s"},\n' % (o, bytes(raw).hex()))
        f.write(" },\n palettes = {\n")
        for L in (1, 2, 3):
            for p in nouv_pal[L]:
                f.write("  {pal=0x%02X, mots={%s}},\n" % (E.PAL0[L] + p, ",".join("0x%04X" % int(w) for w in plans[L].pal_mot[p])))
        f.write(" },\n cases = {\n")
        for L in (1, 2, 3):
            P = plans[L]
            f.write("  [%d] = {ts=%d, x0=%d, y0=%d, liste={\n" % (L, P.ts, P.x0, P.y0))
            for r in range(P.R):
                for c in range(P.C):
                    e = P.grid_ext[r][c]
                    if e[6] == "o": continue
                    f.write("   {%d,%d,0x%X,0x%X},\n" % (P.colabs(c), P.rowabs(r), e[0], e[5]))
            f.write("  }},\n")
        f.write(" },\n}\n")

    rapport["controle"] = ctrl
    rapport["blocs"] = bl_json
    rapport["palettes_nouvelles"] = pals_out
    rapport["places_libres_restantes"] = {E.NOM[L]: int(len(libre.codes(L))) for L in (1, 2, 3)}
    json.dump(rapport, open(os.path.join(a.sortie, "rapport.json"), "w"), indent=1, ensure_ascii=False, default=str)
    ok = all(v["recompose_vs_quantifie_px"] == 0 and v["origine_vs_recompose_px"] == 0 for v in ctrl.values())
    print("RECOMPOSITION = QUANTIFIE AU PIXEL :", "OUI" if ok else "NON")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
