#!/usr/bin/env python3
"""compare_mame.py DONNEES MAME_DIR [décors hexa…] — contrôle des données ISO contre SFA2 joué (arcade sfa2u, MAME,
ORACLE local ; méthode de decors_sfa1/outils/compare_mame.py). Pour chaque décor et chaque position (gauche / droite /
centre de mame/lua/sonde_sfa2.lua) :
  1. tilemaps scroll2 / scroll3 entières (VRAM) contre la grille construite depuis l'ISO, EN PIXELS (les codes de ro2
     et de sfa2u diffèrent pour les blocs scroll2 ≥ 58 : renumérotation du portage) : nombre de tuiles différentes ;
     scroll1 : colonnes de l'anneau (512 px) comparées au monde ISO replié ;
  2. palettes scroll1 / 2 / 3 (pens de MAME) contre celles de l'ISO (+$F000) ;
  3. contrôle CPS-B (ordre des plans) contre la table de l'ISO ; rowscroll (constant ? valeur) ;
  4. écran : rendu hors jeu (données ISO, registres MAME, rowscroll VRAM) contre la capture MAME sans sprites.
Écrit MAME_DIR/../controle/ (images de différence, controle.tsv)."""
import os, sys, struct
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_mame as M, rendu_sfa2 as RS
TUILES = os.environ.get("SFA2_TUILES", "<workspace>/work/carto_sfa2/gfx/sfa2_tiles_raw.npy")   # ROM gfx sfa2u (oracle)
T = np.load(TUILES, mmap_mode="r")

def tuile_arcade(plan, code):
    if plan == 1: return np.asarray(T[0x10000 + (code >> 1)])[8 * (code & 1):8 * (code & 1) + 8, :8]
    if plan == 2: return np.asarray(T[0x10000 + code])
    c = code & 0x3FFF
    return np.concatenate([np.asarray(T[0x10000 + 4 * c + q]) for q in range(4)], 0).reshape(32, 32)

def vram_idx(d, plan):
    """tilemap de la VRAM en indices palette·16 + pen (tuiles de la ROM sfa2u), grille 64 × 64"""
    C, A = (M.tilemap_s1 if plan == 1 else M.tilemap_s2 if plan == 2 else M.tilemap_s3)(d)
    ts = {1: 8, 2: 16, 3: 32}[plan]
    idx = np.zeros((64 * ts, 64 * ts), np.int32)
    for r in range(64):
        for c in range(64):
            t = tuile_arcade(plan, int(C[r, c])).astype(np.int32); at = int(A[r, c])
            if at & 0x20: t = t[:, ::-1]
            if at & 0x40: t = t[::-1, :]
            idx[r * ts:(r + 1) * ts, c * ts:(c + 1) * ts] = (at & 0x1F) * 16 + t
    return idx

def tuiles_diff(a, b, ts):
    h, w = a.shape; d = (a != b).reshape(h // ts, ts, w // ts, ts).any((1, 3))
    return int(d.sum())

def main():
    D = RS.Donnees(sys.argv[1]); MD = sys.argv[2]
    sel = [int(x, 16) // 2 for x in sys.argv[3:]] or range(18)
    sortie = os.path.join(os.path.dirname(os.path.abspath(MD.rstrip("/"))), "controle"); os.makedirs(sortie, exist_ok=True)
    tsv = os.path.join(sortie, "controle.tsv")
    res = open(tsv).read().splitlines()[1:] if os.path.exists(tsv) else []
    tete = "decor\tvue\ts1X\ts1Y\ts2X\ts2Y\ts3X\ts3Y\tcam\tlc\tlc_iso\ttuiles_s1\ttuiles_s2\ttuiles_s3\tpal_s1\tpal_s2\tpal_s3\trowscroll\tk_s1\tpixels_diff\tpixels"
    # sfa2u a les listes révisées (= ro4 / ro6, variantes ALPHA) pour Dan, Sakura, Gen : on les compare à ces variantes
    VAR = {d["variante_de"]: i for i, d in enumerate(D.J["decors"]) if d.get("variante_de")}
    for s0 in sel:
        stg = "%02X" % (2 * s0)
        s = VAR.get("$" + stg, s0)
        f = os.path.join(MD, "out", "stg%s_dmp.bin" % stg)
        if not os.path.exists(f): print("absent", f); continue
        res = [l for l in res if not l.startswith("$" + stg + "\t")]
        dumps = M.lit(f)
        iso = {p: D.image_plan(s, p)[0] for p in (1, 2, 3)}
        snaps = sorted(os.listdir(os.path.join(MD, "snap", "stg" + stg, "sfa2u")))
        vues = [d for d in dumps if not d["tag"].endswith("-1")]
        for i, d in enumerate(vues):
            prev = [x for x in dumps if x["tag"] == d["tag"] + "-1"][0]
            A, Bv = prev["A"], d["B"]                   # image affichée à t = registres de t-1, VRAM de t
            ram = d["ram"]
            v = {p: vram_idx(d, p) for p in (2, 3)}
            e2 = tuiles_diff(v[2], iso[2], 16); e3 = tuiles_diff(v[3], iso[3], 32)
            # scroll1 : anneau 512 px contre le monde ISO replié (colonnes de 8 px), meilleur décalage de 512 px
            v1 = vram_idx(d, 1); W1 = iso[1].shape[1]; H1 = iso[1].shape[0]
            # colonne de l'anneau juste si elle égale une colonne du monde (x + 512 kx, lignes y + 512 ky)
            ok = np.zeros(64, bool)
            for ky in range(max(1, H1 // 512)):
                for kx in range(max(1, W1 // 512)):
                    m = iso[1][512 * ky:512 * ky + 512, 512 * kx:512 * kx + 512]
                    if m.shape != (512, 512): continue
                    ok |= np.array([(v1[:, x0:x0 + 8] == m[:, x0:x0 + 8]).all() for x0 in range(0, 512, 8)])
            e1 = "%d/64 col." % ok.sum()
            pens = d["pens"]
            ep = []
            for p, base in ((1, 0x200), (2, 0x400), (3, 0x600)):
                iso_c = np.array([RS.couleur(w) for w in D.palettes(s, p)])
                m_c = np.stack([(pens[base:base + 512] >> 16) & 255, (pens[base:base + 512] >> 8) & 255, pens[base:base + 512] & 255], 1)
                ep.append(int((iso_c != m_c).any(1).sum()))
            rows = M.mots(d["gfx"], A[4], 1024).astype(np.int64) if A[0x11] & 1 else None
            rdesc = ("cst %+d" % (rows[0] - 0x10000 if rows[0] >= 0x8000 else rows[0])) if rows is not None and (rows == rows[0]).all() else ("variable" if rows is not None else "off")
            if rows is not None: rows = np.where(rows >= 0x8000, rows - 0x10000, rows)
            lc = Bv[0x13]; lc_iso = int(D.decor(s)["cpsb"][0][1:], 16) | 0x0E
            snap = np.asarray(Image.open(os.path.join(MD, "snap", "stg" + stg, "sfa2u", snaps[i + 1])).convert("RGB"))
            bestimg = None
            for kx in range(max(1, W1 // 512)):
              for ky in range(max(1, H1 // 512)):
                regs = {1: ((A[6] & 0x1FF) + 512 * kx, (A[7] & 0x1FF) + 512 * ky), 2: (A[8], A[9]), 3: (A[10], A[11])}
                r = RS.ecran(D, s, regs, rows, A[0x10], s1_anneau=True)
                nd = int(np.any(r != snap, -1).sum())
                if bestimg is None or nd < bestimg[0]: bestimg = (nd, kx + 10 * ky, r)
            nd, k1, r = bestimg
            dif = np.any(r != snap, -1)
            if nd:
                vv = np.concatenate([snap, r, np.where(dif[..., None], [255, 0, 0], snap // 3).astype(np.uint8)], 1)
                Image.fromarray(vv).save(os.path.join(sortie, "diff_%s_%s.png" % (stg, d["tag"].strip())))
            cam = struct.unpack_from(">H", ram, 0x290)[0]
            res.append("$%s\t%s\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%s\t%d\t%d\t%d\t%d\t%d\t%s\t%d\t%d\t%d" % (
                stg, d["tag"].strip(), A[6], A[7], A[8], A[9], A[10], A[11], cam, lc, lc_iso, e1, e2, e3, *ep, rdesc, k1, nd, dif.size))
            print(res[-1], flush=True)
    res.sort()
    open(tsv, "w").write(tete + "\n" + "\n".join(res) + "\n")

if __name__ == "__main__":
    main()
