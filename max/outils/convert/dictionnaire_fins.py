"""Dictionnaire « tuile PSP -> tuile arcade » pour les plans des fins (scroll2, 16×16).
Source : captures MAME des fins d'arcade (lance_fins.sh : vidages s2_NNNN.bin = $914000 et pal_NNNN.bin = palettes),
chaque case du plan scroll2 rendue avec la palette chargée à ce moment-là (palettes scroll2 = index $40 + attr & $1F).
Clé de comparaison : couleurs à 4 bits par canal (CPS2 luminosité F : n·$11 ; PSP 5 bits : round(v·15/31)), case
rendue avec ses miroirs ; pixels transparents = clé -1.
Sortie : ~/.cache/sfa3max/dico_fins_s2.pkl = {clé: (code, attr, palette (16 mots CPS2), fin, capture)}.
Usage : python dictionnaire_fins.py construire 10 0c 1d 0e … | python dictionnaire_fins.py couvrir 26"""
import os, sys, struct, pickle, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, __import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "decors_ws", "reimport"))
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import plans_vram as PV, cpsenc
CAP = os.path.expanduser("~/.cache/sfa3max/mame_fin")
DICO = os.path.expanduser("~/.cache/sfa3max/dico_fins_s2.pkl")


def cle_arcade(pens, palette):
    rgb = cpsenc.cps_rgb(palette[pens.astype(int)]).astype(int)
    n = (rgb + 8) // 17
    k = (n[..., 0] << 8) | (n[..., 1] << 4) | n[..., 2]
    k[pens == 15] = -1
    return k.astype(np.int16).tobytes()


def cle_psp(px16):
    """px16 = (16,16) valeurs ARGB1555 (bit 15 = opaque) déjà retournées"""
    v = np.asarray(px16, np.int64)
    r, g, b = v & 31, (v >> 5) & 31, (v >> 10) & 31
    n = lambda x: (x * 15 + 15) // 31
    k = (n(r) << 8) | (n(g) << 4) | n(b)
    k[(v & 0x8000) == 0] = -1
    return k.astype(np.int16).tobytes()


def construire(fins):
    dico = pickle.load(open(DICO, "rb")) if os.path.exists(DICO) else {}
    deco = {}
    for f in fins:
        D = os.path.join(CAP, "f%s" % f); n0 = len(dico)
        for nom in sorted(os.listdir(D)):
            if not nom.startswith("s2_"): continue
            k = nom[3:7]
            W = struct.unpack(">8192H", open(os.path.join(D, nom), "rb").read())
            pal = np.array(struct.unpack(">4096H", open(os.path.join(D, "pal_%s.bin" % k), "rb").read()))
            for e in range(4096):
                code, attr = W[2 * e], W[2 * e + 1]
                p = 0x40 + (attr & 0x1F); palette = tuple(pal[p * 16:(p + 1) * 16])
                cle_tuile = (code, attr & 0x7F, palette)
                if cle_tuile in deco: continue
                t = cpsenc.flip(cpsenc.decode_tile(PV.region(), 2, code), attr & 0x20, attr & 0x40)
                if (t == 15).all(): deco[cle_tuile] = None; continue
                c = cle_arcade(t, np.array(palette)); deco[cle_tuile] = c
                dico.setdefault(c, (code, attr, palette, f, k))
        print("fin %s : %d entrées nouvelles (total %d)" % (f, len(dico) - n0, len(dico)))
    pickle.dump(dico, open(DICO, "wb"))


def couvrir(n):
    """cases en couleurs directes de la carte PSP de la fin n trouvées dans le dictionnaire (miroirs PSP appliqués)"""
    from plpac import split
    import fins_max as F
    dico = pickle.load(open(DICO, "rb"))
    E = split(open(os.path.join(F.SRC, "end%s_e.pac" % n), "rb").read()); tex = F.textures(E); v = F.carte(E)
    st = collections.Counter(); manq = collections.Counter()
    for i, x in enumerate(v):
        if x == F.VIDE or ((x >> 8) & 0xFF) not in tex: continue
        fmt, px = F.tuile(tex, (x >> 8) & 0xFF, x & 0xFF)
        if fmt != 1: continue
        a = np.array(px).reshape(16, 16)
        if x & 0x10000000: a = a[:, ::-1]
        if x & 0x20000000: a = a[::-1]
        plan = "ABC"[i // 4096]; ok = cle_psp(a) in dico
        st[(plan, ok)] += 1
        if not ok: manq[(plan, i // 64)] += 1
    print("end%s :" % n, dict(st)); return st, manq


if __name__ == "__main__":
    if sys.argv[1] == "construire": construire(sys.argv[2:])
    else:
        for n in sys.argv[2:]: couvrir(n)


# ---------------- appariement par voisinage de codes (palette déduite des couleurs PSP) ----------------
_TUILES = None
def tuiles_s2():
    """toutes les tuiles scroll2 adressables (65536, 16, 16) pens"""
    global _TUILES
    if _TUILES is None: _TUILES = cpsenc.decode_all(PV.region(), 2)
    return _TUILES


def fonction_vec(C, q):
    """C : (N,16,16) pens candidats ; q : (16,16) couleurs PSP (int, -1 = transparent). -> masque (N,) des candidats tels
    que transparence identique et couleur = fonction du pen"""
    N = len(C); ok = ((C == 15) == (q < 0)[None]).reshape(N, -1).all(1)
    for p in range(15):
        m = (C == p)
        lo = np.where(m, q[None], 1 << 20).reshape(N, -1).min(1); hi = np.where(m, q[None], -1).reshape(N, -1).max(1)
        ok &= (lo == 1 << 20) | (lo == hi)
    return ok


def apparier(n, rang=1536):
    """-> {index de case PSP: (code, fx, fy, {pen: couleur PSP})} pour les cases en couleurs directes de la fin n"""
    from plpac import split
    import fins_max as F
    dico = pickle.load(open(DICO, "rb")); T = tuiles_s2()
    E = split(open(os.path.join(F.SRC, "end%s_e.pac" % n), "rb").read()); tex = F.textures(E); v = F.carte(E)
    cases = {}
    for i, x in enumerate(v):
        if x == F.VIDE or ((x >> 8) & 0xFF) not in tex: continue
        fmt, px = F.tuile(tex, (x >> 8) & 0xFF, x & 0xFF)
        if fmt != 1: continue
        a = np.array(px).reshape(16, 16)
        if x & 0x10000000: a = a[:, ::-1]
        if x & 0x20000000: a = a[::-1]
        cases[i] = a
    q_de = lambda a: np.where(a & 0x8000, a & 0x7FFF, -1).astype(np.int64)
    res = {}; germes = []
    for i, a in cases.items():
        e = dico.get(cle_psp(a))
        if e: res[i] = (e[0], bool(e[1] & 0x20), bool(e[1] & 0x40)); germes.append(e[0])
    codes = sorted(set(germes)); cand = set()
    for c in codes: cand.update(range(max(0, c - rang), min(len(T), c + rang)))
    cand = np.array(sorted(cand))
    if len(cand):
        Cs = {(fx, fy): T[cand][:, :, ::-1 if fx else 1][:, ::-1 if fy else 1, :] for fx in (0, 1) for fy in (0, 1)}
        for i, a in cases.items():
            if i in res: continue
            q = q_de(a)
            if (q < 0).all(): continue
            for (fx, fy), C in Cs.items():
                ok = np.nonzero(fonction_vec(C, q))[0]
                if len(ok): res[i] = (int(cand[ok[0]]), bool(fx), bool(fy)); break
    # palette déduite : pen -> couleur PSP
    out = {}
    for i, (code, fx, fy) in res.items():
        t = T[code][:, ::-1] if fx else T[code]
        t = t[::-1] if fy else t
        q = q_de(cases[i]); pal = {int(p): int(q[t == p][0]) for p in np.unique(t) if p != 15}
        out[i] = (code, fx, fy, pal)
    return out, cases
