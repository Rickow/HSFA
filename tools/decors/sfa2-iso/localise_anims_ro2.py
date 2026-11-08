#!/usr/bin/env python3
"""localise_anims_ro2.py (côté ORACLE, local) : retrouve dans ro2 (e224 décompressé, donnees/ro2.bin) les tables
d'ANIMATION des décors de SFA2 repérées dans le programme arcade sfa2u (outils/arcade_anims.py) et le prouve par un
parcours parallèle complet. Méthode reprise de decors_sfa1/outils/localise_anims_ro1.py (copie : sfa1_ref/).
Rangement constaté dans ro2 (même recompilateur que ro1) : mots petit-boutistes ; cadre = durée (mot), drapeaux (mot,
octet fort), pointeur (long petit-boutiste, adresse EXEC de ro2), +8..+15 mots ; les tables de tête ont des décalages
égaux à ceux de l'arcade + 0 à 6 (cadres réalignés sur 4 o). Blocs de tuiles : 3 mots, 2 o de bourrage, paires en
longs (code << 16 | attr). Entrées de palettes : 3 mots. Descripteurs de sprites : mots (codes renumérotés).
Écrit outils/carte_anims_ro2.json (adresses, correspondances de codes : aucune donnée graphique).
Usage : localise_anims_ro2.py [donnees/ro2.bin]"""
import sys, os, json, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arcade_anims as AA
ICI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ICI, "donnees", "ro2.bin"), "rb").read()
EX = 0x1F0000
wr = lambda a: struct.unpack_from("<H", R, a - EX)[0]
lr = lambda a: struct.unpack_from("<I", R, a - EX)[0]
dans = lambda a: EX <= a < EX + len(R) - 16

# ---- catalogue (lu dans le code 68K de sfa2u ; RAPPORT §5) -------------------------------------------------------
# racines à table de décalages : (arcade, moteur, rôle)
RACINES = [(r, "sprite", "sprites de décor (tables qui se chevauchent ; racine lue par le gestionnaire de classe)") for r in (
    0x21B7B6, 0x21B7BE, 0x21B7EA, 0x21B7F4, 0x21B80E, 0x21B82A, 0x21B846, 0x21B864, 0x21B878, 0x21B8A6, 0x21B8B4,
    0x21B8D8, 0x21B8E8, 0x21B914, 0x21B930, 0x21B942, 0x21B954, 0x21B982)] + [
    (0x23EFAE, "tuiles_s1", "classe $3F (Sakura) : tuiles scroll1"),
    (0x23F110, "tuiles_s2", "classe 1 (+$E = 8) et canaux $6F462 (classes $3C, $42, $5D, $6A, $6B)"),
    (0x243910, "tuiles_s3", "classe 1 (+$E = 12) et classe $44"),
    (0x05B54E, "palette", "classe 2 (sous-type = animation)"),
    (0x06EA6A, "palette", "classe $55 (Birdie)"),
    (0x06E920, "palette", "classe $53 (Gen)"),
    (0x06A55C, "sprite", "classe $39 (Birdie)"),
]
# listes de cadres de palette lues par le canal $6D62C (pas de table de tête)
LISTES_PAL = [(a, "classe $49 (Charlie) canal %d" % k) for k, a in enumerate(
    (0x6D6C2, 0x6D706, 0x6D71A, 0x6D80E, 0x6D932, 0x6D956, 0x6D68A, 0x6D69E))] + [
    (0x6C868, "classe $42 (Zangief) canal $70"), (0x6C89C, "classe $42 canal $78"), (0x6C8D0, "classe $42 canal $38"),
    (0x6FA16, "classe $60 (Zangief)"), (0x71580, "classe $6E (Zangief)"), (0x7113C, "classe $6A (Sakura)")]
# paramètres des canaux de tuiles s2 ($6F462 : octet +$C = animation de $23F110, +8/+$A = X/Y)
CANAUX_S2 = [(0x6C1F2, 0x6C1F6, 4, "classe $3C (Guy)"), (0x6C858, 0x6C85C, 3, "classe $42 (Zangief)"),
             (0x6F4BC, 0x6F4C0, 4, "classe $5D (Rolento)"), (0x7120E, 0x71210, 2, "classe $6B (Dan)"),
             (0x7120E, 0x71218, 2, "classe $6B (Dan), positions si ($90,A5) = 8")]
LISTE_CLASSE0 = (0x5B3EE, 39)       # espace OPCODES : longs (anim << 24 | racine), sous-type = indice
SINUS_GEN = (0x1DD98, 256)          # espace OPCODES (lecture PC-relative en $1DD60)

def mots_a(a, n, B=AA.D): return [AA.w(a + 2 * i, B) for i in range(n)]
def mots_r(a, n): return [wr(a + 2 * i) for i in range(n)]

class Corresp:
    """correspondance de codes arcade -> ro2 (doit être une fonction)"""
    def __init__(s): s.m = {}; s.conflits = 0
    def ajoute(s, a, r):
        if s.m.setdefault(a, r) != r: s.conflits += 1; return False
        return True

CODES = collections.defaultdict(Corresp)

def taille_desc(p):
    t = AA.w(p)
    if t == 0: return 3 + 2 * AA.w(p + 2)
    if t == 2: return 4 + 2 * (AA.w(p + 4) + 1)
    return None

def compare_cible(eng, pa, pr):
    if eng == "sprite":
        # le portage a redécoupé les sprites (descripteurs, positions et codes propres à ro2) : seul le type est commun
        return AA.w(pa) == wr(pr)
        n = taille_desc(pa)
        if n is None: return mots_a(pa, 1) == mots_r(pr, 1)
        ma, mr = mots_a(pa, n), mots_r(pr, n); t = ma[0]
        cod = set(range(4, n, 2)) if t == 0 else set(range(4, n, 2))
        for i, (x, y) in enumerate(zip(ma, mr)):
            if i in cod:
                if not CODES["sprite"].ajoute(x, y): return False
            elif x != y: return False
        return True
    if eng.startswith("tuiles"):
        h = mots_a(pa, 3)
        if mots_r(pr, 3) != h: return False
        n = (h[1] + 1) * (h[2] + 1)
        for k in range(n):
            ca, aa = AA.w(pa + 6 + 4 * k), AA.w(pa + 8 + 4 * k)
            v = lr(pr + 8 + 4 * k)
            if ca == 0x20 and v >> 16 == 0x20: continue        # case vide : le portage a remis son attribut à 0
            if (v & 0xFFFF) != aa: return False
            if not CODES[eng].ajoute(ca, v >> 16): return False
        return True
    if eng == "palette":
        for (d, b, s) in AA.entrees_palette(pa):
            if mots_r(pr, 3) != [d, b, s]: return False
            pr += 6
        return True

def parallele(sa, ba, eng, a_r):
    """sa : cadres arcade d'une animation ; a_r : 1er cadre dans ro2"""
    fs = AA.FS[eng]; vus = {}; a = a_r; cad = []
    for k, (aa, d, f, p) in enumerate(sa):
        if not dans(a): return None
        vus[a] = k
        if wr(a) != d or (wr(a + 2) >> 8) != f: return None
        if fs == 16 and mots_a(aa + 8, 4) != mots_r(a + 8, 4): return None
        pr = lr(a + 4)
        if d != 0 or p < 0x400000:
            if not dans(pr) or not compare_cible(eng, p, pr): return None
        cad.append(a); a += fs
        if f & 0x80:
            a = lr(a)
            if ba is not None and ba >= 0 and vus.get(a) != ba: return None
    return cad

OBS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "anims_observees.json")
def anims_utiles(T, eng):
    """sprites : animations vues sous MAME (anims_observees.json, écrit par anims_observees.py) ; autres : animations
    dont tous les cadres sont plausibles (bloc de tuiles, entrées de palette)"""
    if eng == "sprite" and os.path.exists(OBS):
        o = json.load(open(OBS)).get("$%06X" % T)
        if o:     # animations vues + toutes les animations valides de numéro inférieur au plus grand vu
            v = set(AA.anims_valides(T, 16))
            return sorted(set(o) | {i for i in v if i < max(o)})
    ok = []
    for i in AA.anims_valides(T, AA.FS[eng]):
        s, b = AA.walk(T, i, AA.FS[eng]); bon = True
        for (_, d, f, p) in s:
            if eng == "sprite" and (p >= 0x400000 or AA.w(p) not in (0, 2)): bon = False
            if eng.startswith("tuiles") and (p >= 0x400000 or AA.w(p + 2) > 63 or AA.w(p + 4) > 63): bon = False
            if eng == "palette" and (p >= 0x400000 or AA.w(p + 2) not in (0, 4, 8, 12)): bon = False
        if bon: ok.append(i)
    return ok

def localise_racine(T, eng):
    fs = AA.FS[eng]; anims = anims_utiles(T, eng)
    n = max(anims) + 1; offs = [AA.w(T + 2 * i) for i in range(n)]
    cands = set(); i0 = anims[0]
    for dl in range(0, 8, 2):
        t = struct.pack("<H", offs[i0] + dl)
        if i0 + 1 < n and offs[i0 + 1]:
            t += struct.pack("<H", offs[i0 + 1] + dl)
        o = R.find(t)
        while o >= 0:
            c = o + EX - 2 * i0
            if c % 2 == 0: cands.add(c)
            o = R.find(t, o + 1)
    bons = []
    for c in sorted(cands):
        ok = {}
        for i in anims:
            if not dans(c + 2 * i): break
            o = wr(c + 2 * i); s, b = AA.walk(T, i, fs)
            cad = parallele(s, b, eng, c + o)
            if cad is None: break
            ok[i] = cad
        else:
            bons.append((c, ok))
    return anims, bons, len(cands)

def localise_liste(a, eng="palette"):
    """liste de cadres sans table : on cherche le 1er cadre (durée, drapeaux) puis parcours parallèle"""
    fs = AA.FS[eng]; s, b = [], None; x = a; vus = {}
    while x not in vus:
        vus[x] = len(s); f = AA.D[x + 2]; s.append((x, AA.w(x), f, AA.l(x + 4) & 0xFFFFFF)); x += fs
        if AA.w(x - fs) == 0: b = -1; break
        if f & 0x80: x = AA.l(x) & 0xFFFFFF; b = vus.get(x); break
    t = struct.pack("<HH", s[0][1], s[0][2] << 8)
    bons = []; o = R.find(t)
    while o >= 0:
        if o % 4 == 0:
            cad = parallele(s, b, eng, o + EX)
            if cad: bons.append(o + EX)
        o = R.find(t, o + 1)
    return s, b, bons

def cherche_mots(B, a, n, fmt=">H"):
    v = [struct.unpack_from(fmt, B, a + 2 * i)[0] for i in range(n)]
    t = b"".join(struct.pack("<" + fmt[1], x) for x in v); o = R.find(t); h = []
    while o >= 0: h.append(o + EX); o = R.find(t, o + 1)
    return h

if __name__ == "__main__":
    out = {"racines": {}, "listes_palette": {}, "canaux_s2": {}, "banques": {}, "codes": {}}
    for T, eng, role in RACINES:
        anims, bons, nc = localise_racine(T, eng)
        e = dict(moteur=eng, role=role, anims=anims, ro2=["0x%06X" % c for c, _ in bons])
        if len(bons) == 1:
            c, ok = bons[0]
            e["decalage_tete"] = sorted({wr(c + 2 * i) - AA.w(T + 2 * i) for i in anims})
            e["cadres"] = {str(i): ["0x%06X" % x for x in ok[i]] for i in anims}
        out["racines"]["$%06X" % T] = e
        print("%-9s $%06X %3d anims -> ro2 %s (candidats %d)" % (eng, T, len(anims), e["ro2"], nc))
    for a, role in LISTES_PAL:
        s, b, bons = localise_liste(a)
        out["listes_palette"]["$%06X" % a] = dict(role=role, cadres=len(s), boucle=b, ro2=["0x%06X" % x for x in bons])
        print("liste pal $%06X %2d cadres boucle %s -> ro2 %s" % (a, len(s), b, ["0x%06X" % x for x in bons]))
    for ab, al, n, role in CANAUX_S2:
        hb = []; t = AA.D[ab:ab + n]; o = R.find(t)
        while o >= 0: hb.append(o + EX); o = R.find(t, o + 1)
        L = [AA.l(al + 4 * i) for i in range(n)]
        tl = b"".join(struct.pack("<I", x) for x in L); hl = []; o = R.find(tl)
        while o >= 0: hl.append(o + EX); o = R.find(tl, o + 1)
        tl2 = b"".join(struct.pack("<HH", x >> 16, x & 0xFFFF) for x in L); o = R.find(tl2)
        while o >= 0: hl.append(o + EX); o = R.find(tl2, o + 1)        # rangement constaté : mots (X, Y)
        hb = [x for x in hb if any(0 < p - x <= 16 for p in hl)] or hb  # octets juste avant les positions
        cle = "$%06X/$%06X" % (ab, al)
        out["canaux_s2"][cle] = dict(role=role, anims=list(t), pos=["%04X,%04X" % (x >> 16, x & 0xFFFF) for x in L],
                                             ro2_anims=["0x%06X" % x for x in hb[:5]], ro2_pos=[str(x) if isinstance(x, tuple) else "0x%06X" % x for x in hl[:5]])
        print("canaux s2 %s : anims %s pos %s -> ro2 %s / %s" % (role, list(t), out["canaux_s2"][cle]["pos"], out["canaux_s2"][cle]["ro2_anims"], out["canaux_s2"][cle]["ro2_pos"]))
    # liste des sous-types de la classe 0 : longs (anim << 24 | racine ro2)
    rm = {int(k[1:], 16): int(v["ro2"][0], 16) for k, v in out["racines"].items() if len(v["ro2"]) == 1}
    ent = [(AA.l(LISTE_CLASSE0[0] + 4 * s, AA.O) >> 24, AA.l(LISTE_CLASSE0[0] + 4 * s, AA.O) & 0xFFFFFF) for s in range(LISTE_CLASSE0[1])]
    t = b"".join(struct.pack("<I", (a << 24) | rm[r]) for a, r in ent if r in rm)
    o = R.find(t); out["classe0"] = dict(arcade="$%06X (opcodes)" % LISTE_CLASSE0[0], n=len(ent), ro2="0x%06X" % (o + EX) if o >= 0 else None,
                                          entrees=["$%06X/%d" % (r, a) for a, r in ent])
    print("liste de la classe 0 ->", out["classe0"]["ro2"])
    # table des positions de sprites ($9F25C : longs -> listes de (x, y)) : par le contenu d'une liste connue
    p = AA.l(0x9F25C + 0x3A1C) & 0xFFFFFF
    t = b"".join(struct.pack("<H", AA.w(p + 2 * i)) for i in range(8)); h = R.find(t)
    base = None
    if h >= 0:
        q = R.find(struct.pack("<I", h + EX))
        if q >= 0: base = q + EX - 0x3A1C
    ok = 0; n = 0
    if base:
        for idx in range(0, 0x4000, 4):
            pa = AA.l(0x9F25C + idx) & 0xFFFFFF; pr = lr(base + idx)
            if not (0x80000 <= pa < 0x400000 and dans(pr)): continue
            n += 1; ok += mots_a(pa, 4) == mots_r(pr, 4)
    out["positions"] = dict(arcade="$09F25C", ro2="0x%06X" % base if base else None, entrees_identiques=ok, entrees=n)
    print("positions de sprites -> ro2 %s (%d / %d entrées de 4 mots identiques)" % (out["positions"]["ro2"], ok, n))
    # banques de palettes (sélecteur 0/4/8/12) : parties utilisées
    used = collections.defaultdict(set)
    for T, eng, _ in RACINES:
        if eng != "palette": continue
        for i in anims_utiles(T, eng):
            for (_, _, _, p) in AA.walk(T, i, 8)[0]:
                for d, b, s in AA.entrees_palette(p): used[b].add(s & 0xFFFE)
    for a, _ in LISTES_PAL:
        for (_, _, _, p) in localise_liste(a)[0]:
            for d, b, s in AA.entrees_palette(p): used[b].add(s & 0xFFFE)
    # table des 4 banques ($18D58 et ses copies $6D67A… : 4 longs) -> dans ro2 : longs petit-boutistes
    tb = struct.pack("<III", 0x5BB210, 0x5BBFD0, 0x5BDED0)       # banques 4/8/12 trouvées telles quelles (contenu)
    tabs = []; o = R.find(tb)
    while o >= 0: tabs.append(o - 4 + EX); o = R.find(tb, o + 1)
    B = [lr(tabs[0] + 4 * k) for k in range(4)]
    out["banques"]["tables_ro2"] = ["0x%06X" % x for x in tabs]
    for b in sorted(used):
        base = AA.BANQUES_PAL[b // 4]; hi = max(used[b]) + 32; br = B[b // 4]
        # le portage range le n° de palette dans la couleur 15 (transparente) : on la saute
        ok = all(AA.w(base + 2 * i) == wr(br + 2 * i) for i in range(hi // 2) if i % 16 != 15)
        out["banques"][str(b)] = dict(arcade="$%06X" % base, taille=hi, ro2="0x%06X" % br, identique_hors_couleur15=ok)
        print("banque %2d $%06X (%d o utiles) -> ro2 0x%06X (tables %s) identique hors couleur 15 : %s" % (b, base, hi, br, out["banques"]["tables_ro2"], ok))
    h = cherche_mots(AA.O, SINUS_GEN[0], SINUS_GEN[1], ">h")
    out["sinus_gen"] = dict(arcade="$%06X (opcodes)" % SINUS_GEN[0], n=SINUS_GEN[1], ro2=["0x%06X" % x for x in h])
    print("sinus de Gen -> ro2", out["sinus_gen"]["ro2"])
    for k, c in CODES.items():
        out["codes"][k] = dict(n=len(c.m), conflits=c.conflits, ecarts=dict(collections.Counter("%X" % ((a - r) & 0xFFFF) for a, r in c.m.items()).most_common(6)))
        print("codes %-9s : %d correspondances, %d conflits, écarts arcade-ro2 %s" % (k, len(c.m), c.conflits, out["codes"][k]["ecarts"]))
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "carte_anims_ro2.json"), "w"), indent=1)
