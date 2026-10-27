"""PIERRE DE ROSETTE DE CONSTRUCTION : comment la PSP (SFA3 MAX) a été construite à partir d'Upper (Anthology, ro5).
2026-10-11. But : mesurer, perso par perso, ce que chaque élément PSP est devenu par rapport à sa source Upper, pour en
tirer les RÈGLES de construction (puis les inverser pour les persos MAX et les vérifier par aller-retour).

Sources
- Upper (module ro5, petit-boutiste, fichier = adresse PS2 − 0x1F0000) :
  T_61A100 (fichier 0x42A100) = 40 pointeurs vers le bloc de chaque perso (homologue de $DD412 : 3 ismes × 4 longs
  $2B0, $2B8, $2B4, $2BC) ; sous-tables = mots relatifs à leur début ; pas de 20 o (durée, drapeaux, …, frame +4) ;
  frames de type 2 (type, T, n−1, pos alignée sur 4, n × (code local, attributs)) ; positions dans le fichier fixe 390
  ($B04000, banc HSFA ext_b04000.bin, mots gros-boutistes) ; tuiles : conteneur gfx du perso (carte.txt « perso c N »,
  X_DATA.BIN, anthgfx.py d'HSFA), valeurs BRUTES CPS2.
- PSP : plXX_e.pac (frames : cases 32×32 = 2×2 tuiles TL, BL, TR, BR ; tuiles maxtile.decode ; brut = 15 − ((16 − i) mod 16)) ;
  tables d'animation $2B0/$2B4/$2B8/$2BC (convert/tables_anim.py).
Méthode : frame = ensemble de tuiles AFFICHÉES (x, y, empreinte des pixels après miroirs), ramené à son coin haut-gauche ;
appariement PSP -> Upper par index inversé des empreintes puis similarité de Jaccard (≥ 0,9).
Sorties : ~/.cache/sfa3max/rosette/plXX.json, synthèse imprimée.
Usage : python rosette_construction.py [n° perso hexa …]   (défaut : tous les persos d'arcade 00-25)"""
import os, sys, csv, json, struct, hashlib, collections
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max")); sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "src", "hsfa"))
sys.path.insert(0, os.path.join(ICI, "..", "convert"))
UP = open(os.path.join(os.environ.get("ANTHOLOGY_DIR", "anthology_extract"),
                       "decompressed", "ro5_usa_prog68k.bin"), "rb").read()
X = 0x1F0000
T_BLOCS = 0x559838                      # fichier ; PS2 0x749838 = VRAIE table des blocs par perso (rapport HSFA
                                        # EFFETS-UPPER.md ; T_61A100 = homologue de $ACDE0, PAS des pointeurs de blocs)
F5 = open(__import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "mame_ro5", "ext_b04000.bin"), "rb").read(); FBASE = 0xB04000
XDATA = __import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "xdata", "X_DATA.BIN")
MANIF = __import__("os").path.join(__import__("os").environ.get("ANTHOLOGY_DIR", "anthology_extract"), "manifest.csv")
CARTE = __import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "mame_ro5", "banques", "carte.txt")
SORTIE = os.path.expanduser("~/.cache/sfa3max/rosette"); os.makedirs(SORTIE, exist_ok=True)
NOMS_T = ("$2B0", "$2B8", "$2B4", "$2BC")   # ordre du bloc
L = lambda a: struct.unpack_from("<I", UP, a - X)[0]
H = lambda a: struct.unpack_from("<H", UP, a - X)[0]
h = lambda a: struct.unpack_from("<h", UP, a - X)[0]


def empreinte(px):
    """px : tableau 16×16 de valeurs brutes CPS2 ; None si tuile vide (tout transparent, 15)"""
    a = np.asarray(px, np.uint8)
    if (a == 15).all(): return None
    return hashlib.blake2b(a.tobytes(), digest_size=8).digest()


def miroir(px, fx, fy):
    a = np.asarray(px)
    if fx: a = a[:, ::-1]
    if fy: a = a[::-1, :]
    return a


def norm(s):
    if not s: return frozenset()
    mx = min(x for x, _, _ in s); my = min(y for _, y, _ in s)
    return frozenset((x - mx, y - my, e) for x, y, e in s)


# ---------------- côté UPPER ----------------
def gfx_perso(c):
    for l in open(CARTE):
        p = l.split()
        if len(p) == 3 and p[0] == "perso" and int(p[1]) == c: return int(p[2])
    return None


_man = None
def entree_xdata(n):
    global _man
    if _man is None: _man = {int(r["idx"]): (int(r["offset"]), int(r["size"])) for r in csv.DictReader(open(MANIF))}
    o, s = _man[n]
    with open(XDATA, "rb") as f: f.seek(o); return f.read(s)


def tuiles_upper(n):
    import anthgfx
    return {m: px for k, m, px in anthgfx.tiles(entree_xdata(n)) if k == 1 and px is not None}


def tables_upper(c, ism=0):
    """-> {nom table: [adresse PS2 du 1er pas de l'animation n, …]}"""
    bloc = L(T_BLOCS + X + 4 * c)
    starts = [L(bloc + 16 * ism + 4 * k) for k in range(4)]
    out = {}
    for k, t in enumerate(starts):
        lim = min([s for s in starts if s > t] + [1 << 30]); offs = []; i = 0
        while t + 2 * i < lim:
            o = H(t + 2 * i)
            if o == 0 or o % 2 or t + o - X >= len(UP): break
            offs.append(t + o); lim = min(lim, t + o); i += 1
        out[NOMS_T[k]] = offs
    return out


def anim_upper(a):
    out = []
    for k in range(80):
        p = a + 20 * k
        if p - X + 24 > len(UP): break
        d, fl, fp = UP[p - X], UP[p - X + 1], L(p + 4)
        out.append((fp, d, fl & 0xC0, (L(p + 20) - p) // 20 if fl & 0x80 else None))
        if fl & 0xC0: break
    return out


# types de frames à pointeur vers le fichier 290/390 (note HSFA frames-anthology-emetteur.md) ; 00/02 : codes LOCAUX
# (banque du perso) ; 0A/0C/0E/10/16 : codes de la banque COMMUNE (code + $1600 ; Upper : conteneur e351)
TYPES_289 = (0x00, 0x02, 0x0A, 0x0C, 0x0E, 0x10, 0x16)
# types SANS pointeur 289 : 04 / 06 = positions dans la table fixe (Upper : fichier 0x424050, homologue de ro3 0x58B790)
# en idx / idx+2, plus (dx0, dy0), codes LOCAUX ; 08 / 14 = n × 12 o (mot, X, Y, mot, code, attr), codes COMMUNS
TYPES_DIRECTS = (0x04, 0x06, 0x08, 0x14)
T_POS = 0x424050 + 0x1F0000
COMMUNE = 351
_toutes = None
def toutes_frames_upper():
    """toutes les frames de type 2 du module (pointeurs vers elles trouvés n'importe où, positions dans 390 ou le module)"""
    global _toutes
    if _toutes is None:
        h16 = np.frombuffer(UP[:len(UP) // 2 * 2], np.uint16).astype(np.uint32)
        W32 = h16[:-1] | (h16[1:] << 16)                 # pointeurs à TOUTE adresse paire (pas alignés sur 2)
        W32 = W32[(W32 >= X) & (W32 < X + len(UP)) & (W32 % 2 == 0)]
        W = np.unique(W32).tolist(); vus = set()
        for w in W:
            o = w - X
            if not (0 <= o < len(UP) - 12) or o % 2 or w in vus: continue
            t, TT, n1 = struct.unpack_from("<3H", UP, o)
            if t in TYPES_DIRECTS:
                n_ = TT if t == 4 else n1 + 1
                if 0 < n_ <= 48: vus.add(w)
                continue
            if t not in TYPES_289 or n1 >= 64: continue
            ent = 4 if t == 0 else (8 if t in (0x0A, 0x0E, 0x16) else 6)   # mots d'en-tête avant l'alignement
            if o + ent + 8 > len(UP): continue
            pos = struct.unpack_from("<I", UP, ((w + ent + 3) & ~3) - X)[0]
            if FBASE <= pos < FBASE + len(F5) or X <= pos < X + len(UP): vus.add(w)
        _toutes = sorted(vus)
    return _toutes


def frame_upper(fp, T, TC=None):
    """-> ensemble normalisé des tuiles affichées, ou None ; T = tuiles du perso, TC = tuiles de la banque commune"""
    o = fp - X
    if not (0 <= o < len(UP) - 12): return None
    t = H(fp)
    if t in TYPES_DIRECTS: return frame_directe(fp, t, T, TC)
    if t not in TYPES_289: return None
    if t == 0:                                     # type, N, attr commun, [align], ptr, N × code
        n, attr_c = H(fp + 2), H(fp + 4); ent = 6
    elif t in (0x0A, 0x0E, 0x16):                  # type, T, n−1, attr commun, [align], ptr, n × code
        n, attr_c = H(fp + 4) + 1, H(fp + 6); ent = 8
    else:                                          # 02 / 0C / 10 : type, T, n−1, [align], ptr, n × (code, attr)
        n, attr_c = H(fp + 4) + 1, None; ent = 6
    if not 0 < n <= 64: return None
    p = (fp + ent + 3) & ~3; pos = L(p)
    banque = T if t in (0x00, 0x02) else TC
    if banque is None: return None
    dec = 0                                        # Upper : code = index local e351 direct (pas de +$1600, rapport HSFA)
    s = set()
    for k in range(n):
        if attr_c is None: c, at = H(p + 4 + 4 * k), H(p + 6 + 4 * k)
        else: c, at = H(p + 4 + 2 * k), attr_c
        if FBASE <= pos < FBASE + len(F5) - 4 * n: dx, dy = struct.unpack_from(">hh", F5, pos - FBASE + 4 * k)
        elif X <= pos < X + len(UP): dx, dy = struct.unpack_from("<hh", UP, pos - X + 4 * k)
        else: return None
        w = ((at >> 8) & 15) + 1; hh = ((at >> 12) & 15) + 1
        if t == 0x0E or t == 0x10: w = hh = 1      # échelle dans l'attribut : taille non fiable, 1 tuile
        fx, fy = at & 0x20, at & 0x40
        for j in range(hh):
            for i in range(w):
                px = banque.get(dec + c + i + 16 * j)
                if px is None: continue
                e = empreinte(miroir(px, fx, fy))
                if e is None: continue
                ii = (w - 1 - i) if fx else i; jj = (hh - 1 - j) if fy else j
                s.add((dx + 16 * ii, dy + 16 * jj, e))
    return norm(s)


def frame_directe(fp, t, T, TC):
    s = set()
    try:
        if t in (0x04, 0x06):
            if t == 4: n, attr_c, dx0, dy0 = H(fp + 2), H(fp + 4), h(fp + 6), h(fp + 8); q = fp + 10; pas = 4
            else: n, attr_c, dx0, dy0 = H(fp + 4) + 1, None, h(fp + 6), h(fp + 8); q = fp + 10; pas = 6
            if not 0 < n <= 48: return None
            objs = []
            for k in range(n):
                idx, c = H(q + pas * k), H(q + pas * k + 2)
                at = attr_c if attr_c is not None else H(q + pas * k + 4)
                objs.append((h(T_POS + idx) + dx0, h(T_POS + idx + 2) + dy0, c, at))
            banque = T
        else:
            n = H(fp + 4) + 1
            if not 0 < n <= 48: return None
            objs = []
            for k in range(n):
                e = fp + 6 + 12 * k
                objs.append((h(e + 2), h(e + 4), H(e + 8), H(e + 10)))
            banque = TC
    except struct.error:
        return None
    if banque is None: return None
    for dx, dy, c, at in objs:
        w = ((at >> 8) & 15) + 1; hh = ((at >> 12) & 15) + 1; fx, fy = at & 0x20, at & 0x40
        for j in range(hh):
            for i in range(w):
                px = banque.get(c + i + 16 * j)
                if px is None: continue
                e_ = empreinte(miroir(px, fx, fy))
                if e_ is None: continue
                ii = (w - 1 - i) if fx else i; jj = (hh - 1 - j) if fy else j
                s.add((dx + 16 * ii, dy + 16 * jj, e_))
    return norm(s)


# fichiers d'animation PAR PERSO chargés à l'exécution (table 0x628470 : (gfx 419-454, anim 486-521)) : effets, intros,
# poses ; décompressés par HSFA dans work/cps2/anims/f<N>.bin, pointeurs internes relatifs à $B83800
T_PERSO_FICHIERS = 0x628470; B_ANIM = 0xB83800
def fichiers_perso(c):
    g, a = struct.unpack_from("<hh", UP, T_PERSO_FICHIERS - X + 4 * c)
    return (g, a) if g else (None, None)


def frames_fichier_anim(na, T):
    """frames de type 2 d'un fichier d'animation chargé (positions dans le fichier) -> {clé: ensemble}"""
    f = __import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "cps2", "anims", "f%d.bin") % na
    if not os.path.exists(f): return {}
    d = open(f, "rb").read(); out = {}
    for o in range(0, len(d) - 12, 2):
        t, TT, n1 = struct.unpack_from("<3H", d, o)
        if t != 2 or n1 >= 48 or TT == 0: continue
        p = (o + B_ANIM + 6 + 3) & ~3; q = p - B_ANIM
        if q + 4 + 4 * (n1 + 1) > len(d): continue
        pos = struct.unpack_from("<I", d, q)[0]
        if not (B_ANIM <= pos < B_ANIM + len(d) - 4 * (n1 + 1)): continue
        objs = struct.unpack_from("<%dH" % (2 * (n1 + 1)), d, q + 4)
        if sum((((objs[2*k+1] >> 8) & 15) + 1) * (((objs[2*k+1] >> 12) & 15) + 1) for k in range(n1 + 1)) != TT: continue
        s = set()
        for k in range(n1 + 1):
            dx, dy = struct.unpack_from("<hh", d, pos - B_ANIM + 4 * k); c, at = objs[2 * k], objs[2 * k + 1]
            w = ((at >> 8) & 15) + 1; hh = ((at >> 12) & 15) + 1; fx, fy = at & 0x20, at & 0x40
            for j in range(hh):
                for i in range(w):
                    px = T.get(c + i + 16 * j)
                    if px is None: continue
                    e = empreinte(miroir(px, fx, fy))
                    if e is None: continue
                    ii = (w - 1 - i) if fx else i; jj = (hh - 1 - j) if fy else j
                    s.add((dx + 16 * ii, dy + 16 * jj, e))
        if s: out[("f%d" % na, o)] = norm(s)
    return out


_tc = None
def tuiles_communes():
    global _tc
    if _tc is None: _tc = tuiles_upper(COMMUNE)
    return _tc


# ---------------- côté PSP ----------------
def psp(c):
    from plpac import split
    from frames import frames
    from maxtile import tiles, decode
    import paths
    E = split(open(os.path.join(paths.pac_dir(), "pl%02x_e.pac" % c), "rb").read())
    g = E[1][1]; TT = tiles(g); F = frames(E[0][1]); cache = {}
    def tuile(i):
        if i not in cache:
            t = decode(g, TT[i][0])[0]
            cache[i] = np.array([15 - ((16 - n) % 16) for b in t for n in (b & 0xF, b >> 4)], np.uint8).reshape(16, 16)
        return cache[i]
    out = []
    for fr in F:
        s = set(); c16 = fr["c"] & 0xFFFF; c16 -= 0x10000 if c16 & 0x8000 else 0
        for k, cell in enumerate(fr["cells"]):
            if cell is None: continue
            cx, cy = (k % fr["w"]) * 32 - fr["a"], (k // fr["w"]) * 32 - c16
            fx, fy = cell[1] & 0x80, cell[1] & 0x40
            for q, (qx, qy) in enumerate(((0, 0), (0, 16), (16, 0), (16, 16))):
                if 4 * cell[0] + q >= len(TT): continue
                e = empreinte(miroir(tuile(4 * cell[0] + q), fx, fy))
                if e is None: continue
                X_ = (16 - qx) if fx else qx; Y_ = (16 - qy) if fy else qy
                s.add((cx + X_, cy + Y_, e))
        out.append(norm(s))
    return out


# ---------------- appariement ----------------
def apparier(P, U):
    """P : [ensemble] par n° PSP ; U : {adresse: ensemble} -> {n: (adresse, similarité)}"""
    inv = collections.defaultdict(set)
    for a, s in U.items():
        for (_, _, e) in s: inv[e].add(a)
    out = {}
    for n, s in enumerate(P):
        if len(s) < 1: continue
        cand = collections.Counter(a for (_, _, e) in s for a in inv[e]).most_common(30)
        # à similarité égale, la frame lue avec la banque DU PERSO l'emporte sur sa lecture en banque commune (clé ≥ 2^40)
        best = max(((len(s & U[a]) / len(s | U[a]), a < (1 << 40), a) for a, _ in cand), default=(0, False, None))
        best = (best[0], best[2])
        if best[0] >= 0.9: out[n] = (best[1], round(best[0], 3))
        elif best[0] >= 0.5: PROCHES[n] = (best[1], round(best[0], 3))
    return out
PROCHES = {}


def etudier(c):
    import tables_anim
    n_gfx = gfx_perso(c); T = tuiles_upper(n_gfx)
    TU = tables_upper(c)
    anims_u = {nom: [anim_upper(a) for a in offs] for nom, offs in TU.items()}
    U = {}
    for nom, L_ in anims_u.items():
        for an in L_:
            for fp, *_ in an:
                if fp not in U:
                    s = frame_upper(fp, T, tuiles_communes())
                    if s: U[fp] = s
    TCc = tuiles_communes()
    for fp in toutes_frames_upper():            # frames hors des 4 tables (tables explicites, objets fils…)
        if fp not in U:
            s_ = frame_upper(fp, T, TCc)
            if s_: U[fp] = s_
        s_ = frame_upper(fp, TCc, TCc)          # même frame lue avec la banque COMMUNE (objets attachés, $1A = 0)
        if s_: U[(1 << 40) | fp] = s_
    g_, a_ = fichiers_perso(c)                  # fichier d'animation propre au perso (effets, intros…)
    if a_:
        for k, v in frames_fichier_anim(a_, tuiles_upper(g_)).items(): U[(0xF0000000 | (a_ << 20) | k[1])] = v
    P = psp(c); PROCHES.clear()
    M = apparier(P, U)
    # ordre : les n° PSP suivent-ils l'ordre des adresses Upper ?
    paires = sorted((n, a) for n, (a, _) in M.items())
    mono = sum(1 for (n1, a1), (n2, a2) in zip(paires, paires[1:]) if a2 > a1) / max(1, len(paires) - 1)
    # animations
    A_psp = tables_anim.animations("pl%02x" % c)
    st = collections.Counter(); renum = []; amap = collections.defaultdict(dict)   # (table, n PSP) -> n Upper
    for nom in NOMS_T:
        LU = anims_u.get(nom, []); seqU = [tuple(x[0] for x in an) for an in LU]
        for x in A_psp.get(nom, []):
            if not x["steps"]: st["illisible PSP"] += 1; continue
            fr = tuple(M.get(s_["frame"], (None,))[0] for s_ in x["steps"])
            du = tuple(s_["ctl"] & 0xFF for s_ in x["steps"])
            n = x["n"]
            if None in fr: st["frames non appariées"] += 1; continue
            if n < len(LU) and seqU[n] == fr:
                st["même n°, mêmes frames, mêmes durées" if tuple(y[1] for y in LU[n]) == du else "même n°, durées retouchées"] += 1
                amap[nom][n] = n
            elif fr in seqU:
                m = seqU.index(fr); st["renuméroté"] += 1; renum.append((nom, n, m)); amap[nom][n] = m
            else: st["sans équivalent Upper"] += 1
    res = {"perso": "%02x" % c, "gfx_upper": n_gfx, "frames_psp": len(P), "frames_upper": len(U),
           "frames_upper_tables": sum(1 for an in sum(anims_u.values(), []) for _ in an),
           "frames_appariees": len(M), "exactes": sum(1 for _, v in M.items() if v[1] == 1.0),
           "ordre_monotone": round(mono, 3),
           "non_appariees": [n for n in range(len(P)) if n not in M and P[n]],
           "retouchees": {str(n): ["%x" % a, s_] for n, (a, s_) in PROCHES.items()},
           "sans_source": [n for n in range(len(P)) if n not in M and n not in PROCHES and P[n]],
           "anims": dict(st), "renumerotations": renum, "anims_map": {k: v for k, v in amap.items()},
           "map": {str(n): ["%x" % a, s] for n, (a, s) in M.items()}}
    json.dump(res, open(os.path.join(SORTIE, "pl%02x.json" % c), "w"))
    import pickle
    pickle.dump({"U": U, "P": P}, open(os.path.join(SORTIE, "pl%02x.pkl" % c), "wb"))
    return res


def invites(persos_src, persos_cibles):
    """frames PSP sans source dans la banque Upper de leur perso (ou persos MAX, sans banque Upper) cherchées parmi les
    frames Upper de TOUS les persos -> {perso: {n PSP: (perso Upper, adresse, similarité)}}"""
    import pickle
    pools = {}
    for c in persos_src:
        f = os.path.join(SORTIE, "pl%02x.pkl" % c)
        if os.path.exists(f): pools[c] = pickle.load(open(f, "rb"))["U"]
    inv = collections.defaultdict(set); Ut = {}
    for c, U in pools.items():
        for a, s in U.items():
            Ut[(c, a)] = s
            for (_, _, e) in s: inv[e].add((c, a))
    out = {}
    for c in persos_cibles:
        f = os.path.join(SORTIE, "pl%02x.json" % c)
        if c >= 0x26: P = psp(c); cand_n = range(len(P))
        else:
            P = pickle.load(open(os.path.join(SORTIE, "pl%02x.pkl" % c), "rb"))["P"]; r = json.load(open(f))
            cand_n = r["sans_source"] + [int(k) for k in r["retouchees"]]
        res = {}
        for n in cand_n:
            s = P[n]
            if len(s) < 2: continue
            cand = collections.Counter(k for (_, _, e) in s for k in inv[e]).most_common(20)
            best = max(((len(s & Ut[k]) / len(s | Ut[k]), k) for k, _ in cand), default=(0, None))
            if best[0] >= 0.9: res[n] = (best[1][0], "%x" % best[1][1], round(best[0], 3))
        out[c] = res
    json.dump({"%02x" % c: {str(n): v for n, v in r.items()} for c, r in out.items()}, open(os.path.join(SORTIE, "invites.json"), "w"))
    return out


def plages(L_):
    out, d = [], None
    for n in L_:
        if d is None or n != f + 1:
            if d is not None: out.append((d, f))
            d = n
        f = n
    if d is not None: out.append((d, f))
    return ", ".join("%d" % a if a == b else "%d-%d" % (a, b) for a, b in out)


if __name__ == "__main__" and sys.argv[1:2] == ["invites"]:
    src = [c for c in range(0x26) if os.path.exists(os.path.join(SORTIE, "pl%02x.pkl" % c))]
    R = invites(src, src + [0x26, 0x27, 0x28, 0x29])
    for c, r in R.items():
        if not r: continue
        par = collections.defaultdict(list)
        for n, (d, a, sim) in sorted(r.items()): par[d].append(n)
        print("pl%02x : %d frames trouvées chez d'autres persos : %s" % (c, len(r), "; ".join(
            "perso %02x : %s" % (d, plages(ns)) for d, ns in sorted(par.items()))[:300]))
    sys.exit()

if __name__ == "__main__":
    persos = [int(x, 16) for x in sys.argv[1:]] or list(range(0x26))
    for c in persos:
        try: r = etudier(c)
        except Exception as e: print("pl%02x : erreur %s" % (c, e)); continue
        print("pl%02x (gfx %s) : frames PSP %d, appariées %d (%d exactes), retouchées %d, sans source %d, ordre monotone %.0f %% ; sans source : %s"
              % (c, r["gfx_upper"], r["frames_psp"], r["frames_appariees"], r["exactes"], len(r["retouchees"]),
                 len(r["sans_source"]), 100 * r["ordre_monotone"], plages(r["sans_source"])[:100]))
        print("      anims :", r["anims"], "; renumérotées :", r["renumerotations"][:6])
