#!/usr/bin/env python3
"""IMPORT D'UN DECOR DE SFA2 DANS LA TRADUCTION 68000 DE SFA3 (fork sfa3hx, mode « bases de plans ») — DECOR-SFA2.md.

Premier essai : décor de RYU de SFA2 (arcade sfa2u, $100 = $00) -> NOUVEAU décor $100 = $50 dans SFA3 traduit.
Numérotation : décor SFA2 de $100 = s  ->  SFA3 $100 = $50 + s (Upper occupe déjà $40-$4E : pas de collision) ;
indice de table = $100 / 2 = 40 + s/2 ; les tables étendues ont NDEC = 58 entrées (SFA3 0-31, Upper 32-39 (copies
de l'entrée 0, inutilisées par SFA3), SFA2 40-57).

Entrées :
  - image traduite ro3 (base/roms/sfa3hx ; carte base/carte_image.txt) ;
  - mémoire de décor du fork en mode base (base/hsfa_plans.bin, hsfa_plans.py, VIDE15=1) ;
  - programme sfa2u (carto_sfa2/dump/sfa2u/prog_donnees.bin + prog_opcodes.bin), région :gfx de sfa2u
    (export/gfx/gfx_region.bin, vidée par MAME).
Sorties (--sortie) :
  roms/sfa3hx/  (programme corrigé ; liens vers les autres fichiers)   ext/ (ext_a04000 + ext_b00000 + ext_c80000)
  hsfa_plans_sfa2.bin (mémoire de décor + tuiles SFA2)   tramp.s / tramp.bin / rapport.json
Lancement : HSFA_PLANS=300,340,3a0 HSFA_GFX=<sortie>/hsfa_plans_sfa2.bin@3000000 HSFA_EXT=<sortie>/ext cps2f sfa3hx ...
"""
import os, sys, json, struct, subprocess, argparse, collections, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(HERE)
sys.path[:0] = [HERE, "<workspace>/work/decors_ws/injection_fork/py"]
import sfa2 as S2
import image, blocs_tr as BT

VASM = "~/outils/vasm/vasmm68k_mot"
NDEC = 58                     # entrées des tables étendues (indice = $100/2)
D_NEW = 0x50                  # $100 du décor de Ryu SFA2
CODE0, CODE1 = 0x93200, 0x94000          # zone libre de l'image (fin du code traduit, zéros)
EXT_LIB, EXT_TAB = 0xB00000, 0xC80000    # blocs externes (bases lues par le fork : HSFA_EXT/ext_<base>.bin)
OFF = {1: 0x0000000, 2: 0x0400000, 3: 0x0A00000}; TBF = {1: 64, 2: 128, 3: 512}   # hsfa_plans.bin
NEUF0 = {1: 0x6000, 2: 0x8A00, 3: 0x1000}; NEUF1 = {1: 0x10000, 2: 0xC000, 3: 0x4000}
QUART = 0x800000


def w(d, a): return struct.unpack_from(">H", d, a)[0]
def ws(d, a): return struct.unpack_from(">h", d, a)[0]
def L(d, a): return struct.unpack_from(">I", d, a)[0]


class Ext:
    """bloc externe (mots gros-boutistes, adresses 68000)"""
    def __init__(s, base, taille): s.base = base; s.b = bytearray(taille); s.fin = 0
    def alloue(s, n, align=2):
        s.fin = (s.fin + align - 1) // align * align; a = s.base + s.fin; s.fin += n
        assert s.fin <= len(s.b), "bloc externe $%X trop petit" % s.base
        return a
    def ecrit(s, a, data): s.b[a - s.base:a - s.base + len(data)] = data
    def put(s, data, align=2):
        a = s.alloue(len(data), align); s.ecrit(a, data); return a
    def octets(s): return bytes(s.b[:s.fin])


def sw_octets(bs):
    """octets lus par le code traduit à l'adresse k^1 : on range les paires échangées"""
    b = bytearray(bs) + (b"\0" if len(bs) & 1 else b"")
    b[0::2], b[1::2] = b[1::2], b[0::2]
    return bytes(b)


# --------------------------------------------------------------------------- 1. tuiles SFA2 -> codes locaux du fork
def tuiles(region2, plans, cases):
    """copie dans la mémoire de décor du fork les tuiles SFA2 utilisées (format MAME identique), dédoublonnées ;
    -> {plan: {code VRAM SFA2: code local}}"""
    carte = {1: {}, 2: {}, 3: {}}
    vus = {1: {}, 2: {}, 3: {}}
    suiv = dict(NEUF0)
    for Lp in (1, 2, 3):
        for code in sorted({v[0] for v in cases[Lp].values()}):
            if Lp == 3: o = QUART + (code & 0x3FFF) * 512
            else: o = QUART + code * TBF[Lp]
            raw = bytes(region2[o:o + TBF[Lp]])
            if raw in vus[Lp]:
                carte[Lp][code] = vus[Lp][raw]; continue
            n = suiv[Lp]; suiv[Lp] += 1
            assert n < NEUF1[Lp], "plus de codes locaux libres (plan %d)" % Lp
            fo = OFF[Lp] + n * TBF[Lp]
            if len(plans) < fo + TBF[Lp]: plans.extend(b"\xff" * (fo + TBF[Lp] - len(plans)))
            plans[fo:fo + TBF[Lp]] = raw
            vus[Lp][raw] = n; carte[Lp][code] = n
    return carte, {Lp: suiv[Lp] - NEUF0[Lp] for Lp in (1, 2, 3)}


# --------------------------------------------------------------------------- 2. programme : tables, bibliothèques
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sortie", default=os.path.join(R, "import/essai"))
    ap.add_argument("--roms", default=os.path.join(R, "base/roms/sfa3hx"))
    ap.add_argument("--carte", default=os.path.join(R, "base/carte_image.txt"))
    ap.add_argument("--plans", default=os.path.join(R, "base/hsfa_plans.bin"))
    ap.add_argument("--gfx2", default=os.path.join(R, "export/gfx/gfx_region.bin"))
    ap.add_argument("--selection", choices=["aucune", "sfa3", "sfa2", "alea"], default="aucune",
                    help="crochet au point de choix du décor du mode Arcade ($4A428) : toujours SFA3 / toujours SFA2 / tirage")
    ap.add_argument("--table-essai", action="store_true",
                    help="(essai) tous les décors de persos SFA3 -> décor SFA2 importé $50 (un seul décor importé)")
    a = ap.parse_args()
    so = a.sortie; os.makedirs(so, exist_ok=True)
    img = image.lit(a.roms); img0 = bytes(img)
    M = BT.depuis_carte(a.carte, "ro3")
    rap = collections.OrderedDict()
    patches = []                                    # (adresse, octets attendus, octets neufs, rôle)

    def patch(adr, neuf, attendu=None, role=""):
        if attendu is not None:
            assert bytes(img[adr:adr + len(attendu)]) == attendu, "site $%06X : %s != %s" % (adr, img[adr:adr + len(attendu)].hex(), attendu.hex())
        patches.append((adr, bytes(img0[adr:adr + len(neuf)]).hex(), bytes(neuf).hex(), role))
        img[adr:adr + len(neuf)] = neuf

    def lea_site(site, ancien, neuf, role):
        op = w(img, site)
        assert op & 0xF1FF == 0x41F9 and L(img, site + 2) == ancien, "LEA $%06X" % site
        patch(site + 2, struct.pack(">I", neuf), struct.pack(">I", ancien), role)

    # ---- données SFA2 du décor
    s = 0x00                                          # $100 du décor dans SFA2 (Ryu)
    cas = {Lp: S2.cases(Lp, s) for Lp in (1, 2, 3)}
    typ = {Lp: S2.liste(Lp, s)[0] for Lp in (1, 2, 3)}
    lst = {Lp: S2.liste(Lp, s)[1] for Lp in (1, 2, 3)}
    pal2 = {Lp: S2.palettes(Lp, s) for Lp in (1, 2, 3)}
    # scroll3 : la routine de SFA3 ne copie que 31 palettes et force $7F ; palette 31 de SFA2 -> emplacement libre
    utilisees3 = sorted({v[1] & 31 for v in cas[3].values()})
    remap3 = {}
    if 31 in utilisees3:
        libre = next(p for p in range(31) if p not in utilisees3)
        remap3[31] = libre; pal2[3][libre] = pal2[3][31]
    rap["sfa2"] = dict(decor="$%02X" % s, types=typ, listes={Lp: [hex(x) for x in lst[Lp]] for Lp in lst},
                       palettes_utilisees={Lp: sorted({(v[1] & 31) for v in cas[Lp].values()}) for Lp in (1, 2, 3)},
                       remap_palette_s3={str(k): v for k, v in remap3.items()})

    # ---- 1. tuiles
    plans = bytearray(open(a.plans, "rb").read())
    region2 = open(a.gfx2, "rb").read()
    ctab, nneuf = tuiles(region2, plans, cas)
    rap["tuiles_neuves"] = {"scroll%d" % Lp: "%d (codes locaux $%X-$%X)" % (nneuf[Lp], NEUF0[Lp], NEUF0[Lp] + nneuf[Lp] - 1) for Lp in (1, 2, 3)}

    ext_l = Ext(EXT_LIB, 0x180000)                    # $B00000-$C7FFFF
    ext_t = Ext(EXT_TAB, 0x80000)                     # $C80000-$CFFFFF

    # ---- 2. bibliothèques relogées (copies des originales + blocs neufs)
    TAILLE = {1: 0x80, 2: 0x300, 3: 0xC0}
    nb_orig = {1: 94, 2: 146, 3: 256}
    nst_orig = (M["b2"] - M["st1"]) // 0x40          # super-tuiles d'origine (2 377)
    # scroll1 : blocs + super-tuiles neufs
    blocs1 = {}; st_neuves = []; st_index = {}
    for n in sorted(set(lst[1])):
        mots = []
        for k in range(64):
            st_old = w(S2.D, S2.T["b1"] + n * 0x80 + 2 * k)
            if st_old not in st_index:
                cel = bytearray()
                a0 = S2.T["st1"] + st_old * 0x40
                for j in range(16):
                    code, attr = w(S2.D, a0 + 4 * j), w(S2.D, a0 + 4 * j + 2)
                    cel += struct.pack(">HH", attr, ctab[1][code])        # long PS2 : (attr, code)
                st_index[st_old] = nst_orig + len(st_neuves); st_neuves.append(bytes(cel))
            mots.append(st_index[st_old])
        blocs1[n] = struct.pack(">64H", *mots)
    # numéros neufs
    num = {Lp: {} for Lp in (1, 2, 3)}
    for i, n in enumerate(sorted(set(lst[1]))): num[1][n] = nb_orig[1] + i
    for i, n in enumerate(sorted(set(lst[2]))): num[2][n] = nb_orig[2] + i
    libres3 = [int(x[1:], 16) for x in json.load(open("<workspace>/work/decors_ws/reimport/blocs_libres.json"))["ro3"]["scroll3"]["libres"]]
    libres3 = [x for x in libres3 if x > 0x8A]
    for i, n in enumerate(sorted(set(lst[3]))): num[3][n] = libres3[i]
    assert max(num[1].values()) < 256 and max(num[2].values()) < 256
    # scroll2 / scroll3 : blocs neufs au format traduit (codes mots, puis attributs octets ^1)
    blocs = {2: {}, 3: {}}
    for Lp in (2, 3):
        nb = 256 if Lp == 2 else 64
        for n in sorted(set(lst[Lp])):
            codes, attrs = [], []
            a0 = S2.T["b%d" % Lp] + n * nb * 4
            for k in range(nb):
                c = (w(S2.D, a0 + 4 * k) + S2.T["add%d" % Lp]) & 0xFFFF
                at = w(S2.D, a0 + 4 * k + 2)
                assert at < 0x100, "attribut 16 bits non représentable (plan %d) : %04X" % (Lp, at)
                if Lp == 3 and (at & 31) in remap3: at = (at & ~31) | remap3[at & 31]
                loc = ctab[Lp][c]
                codes.append((loc - 0x1600) & 0xFFFF if Lp == 2 else loc)
                attrs.append(at)
            blocs[Lp][n] = struct.pack(">%dH" % nb, *codes) + sw_octets(bytes(attrs))
    # copies relogées
    def copie_lib(src, taille, neufs):
        base = ext_l.alloue(taille + sum(len(x) for x in neufs.values()) + 0x40, 4)
        ext_l.ecrit(base, img[src:src + taille])
        return base
    lib = {}
    lib[1] = ext_l.alloue(256 * 0x80, 4); ext_l.ecrit(lib[1], img[M["b1"]:M["b1"] + nb_orig[1] * 0x80])
    for n, data in blocs1.items(): ext_l.ecrit(lib[1] + num[1][n] * 0x80, data)
    lib["st"] = ext_l.alloue((nst_orig + len(st_neuves)) * 0x40, 4)
    ext_l.ecrit(lib["st"], img[M["st1"]:M["st1"] + nst_orig * 0x40])
    for i, cel in enumerate(st_neuves): ext_l.ecrit(lib["st"] + (nst_orig + i) * 0x40, cel)
    lib[2] = ext_l.alloue(256 * 0x300, 4); ext_l.ecrit(lib[2], img[M["b2"]:M["b2"] + nb_orig[2] * 0x300])
    for n, data in blocs[2].items(): ext_l.ecrit(lib[2] + num[2][n] * 0x300, data)
    lib[3] = ext_l.alloue(256 * 0xC0, 4); ext_l.ecrit(lib[3], img[M["b3"]:M["b3"] + 256 * 0xC0])
    for n, data in blocs[3].items(): ext_l.ecrit(lib[3] + num[3][n] * 0xC0, data)
    for site in M["sites"]["bloc1"]: lea_site(site, M["b1"], lib[1], "bibliothèque blocs scroll1")
    for site in M["sites"]["st1"]: lea_site(site, M["st1"], lib["st"], "super-tuiles scroll1")
    for site in M["sites"]["bloc2"]: lea_site(site, M["b2"], lib[2], "bibliothèque blocs scroll2")
    for site in M["sites"]["bloc3"]: lea_site(site, M["b3"], lib[3], "bibliothèque blocs scroll3")
    rap["bibliotheques"] = {"scroll1": "$%X (+%d blocs : %s)" % (lib[1], len(blocs1), [hex(num[1][n]) for n in sorted(blocs1)]),
                            "super_tuiles": "$%X (+%d, indices %d-%d)" % (lib["st"], len(st_neuves), nst_orig, nst_orig + len(st_neuves) - 1),
                            "scroll2": "$%X (+%d : %s)" % (lib[2], len(blocs[2]), [hex(num[2][n]) for n in sorted(blocs[2])]),
                            "scroll3": "$%X (+%d : %s)" % (lib[3], len(blocs[3]), [hex(num[3][n]) for n in sorted(blocs[3])])}

    # ---- 3. tables par décor relogées et étendues (NDEC entrées)
    def alias(i):
        """entrée d'origine servant aux indices >= 32 : SFA2 (40-57) -> décor SFA3 du même perso ; Upper (32-39) -> 0"""
        return i - 40 if i >= 40 else (0 if i >= 32 else i)
    tabs = collections.OrderedDict()

    def table_abs(nom, T, pas, neuf=None, sites=(), extra=0):
        """table de valeurs (pas = octets par décor) ; neuf = {indice: octets}"""
        base = ext_t.alloue(NDEC * pas + extra, 4)
        for i in range(NDEC):
            j = alias(i)
            ext_t.ecrit(base + i * pas, img[T + j * pas:T + (j + 1) * pas])
        for i, data in (neuf or {}).items(): ext_t.ecrit(base + i * pas, data)
        for site, dec in sites: lea_site(site, T + dec, base + dec, nom)
        tabs[nom] = "$%06X -> $%06X (%d x %d o)" % (T, base, NDEC, pas)
        return base

    I = D_NEW // 2
    # types des plans (mot dont l'octet faible est lu)
    table_abs("type scroll1", M["type1"], 2, {I: struct.pack(">H", typ[1])}, [(0x24D86, 0)])
    table_abs("type scroll2", 0x18CB1C, 2, {I: struct.pack(">H", typ[2])}, [(0x251D0, 0)])
    table_abs("type scroll3", 0x18CD4C, 2, {I: struct.pack(">H", typ[3])}, [(0x252D6, 0)])
    # longs $40/$44 des objets de plan (SFA2 Ryu : identiques à SFA3 : s1/s3 $FFFFFFFF, s2 $00100000/$01000280)
    for nom, T, s1, s2 in (("longs scroll1", 0x9C0D0, 0x24E7C, 0x24E8C), ("longs scroll2", 0x9C1F0, 0x25268, 0x25278),
                           ("longs scroll3", 0x9C2F0, 0x2535C, 0x2536C)):
        table_abs(nom, T, 8, None, [(s1, 0), (s2, 4)])
    # contrôle CPS-B ($32/$3A(A5)) : SFA2 $1C34A
    cps = (w(S2.O, S2.T["cpsb"] + 2 * s), w(S2.O, S2.T["cpsb"] + 2 * s + 2))
    table_abs("controle CPS-B", 0x9C940, 4, {I: struct.pack(">HH", *cps)}, [(0x26724, 0), (0x26732, 2)])
    rap["cpsb"] = "%04X %04X" % cps
    # tables d'alias (même perso SFA3)
    table_abs("couleur ROUND (decalages)", 0x98FB0, 2, None, [(0x17968, 0), (0x17988, 0)])
    table_abs("init joueur $F(A6)", 0xA3030, 2, None, [(0x491A6, 0)])
    table_abs("init joueur $18/$D0(A6)", 0xA3070, 4, None, [(0x491CA, 0), (0x491DA, 2)])
    table_abs("init joueur X/Y", 0xA30F0, 4, None, [(0x49228, 0), (0x49238, 2)])
    table_abs("positions par decor ($2F7E4)", 0x9E480, 4, None, [(0x2F7E8, 0), (0x2F7F6, 2)])

    def table_rel(nom, T, sites, blocs_data, taille_bloc, signe=True):
        """table de décalages (relatifs à la table) vers des blocs de données : copie de la table étendue + de tous
        les blocs référencés (taille_bloc) ; blocs_data = {indice: octets} pour les neufs"""
        offs = [(ws if signe else w)(img, T + 2 * j) for j in range(32)]
        cibles = sorted(set(T + o for o in offs))
        lo = min(cibles); hi = max(cibles) + taille_bloc
        nt = NDEC * 2
        # disposition : [table][données d'origine lo..hi][blocs neufs] ; table au début si tout est après
        tot = nt + (hi - lo) + sum(len(x) for x in blocs_data.values()) + 16
        base = ext_t.alloue(tot, 4)
        dl = base + nt + ((lo - base - nt) & 1)
        ext_t.ecrit(dl, img[lo:hi])
        fin = dl + (hi - lo)
        for i in range(NDEC):
            j = alias(i)
            cible = dl + (T + offs[j] - lo)
            ext_t.ecrit(base + 2 * i, struct.pack(">h" if signe else ">H", cible - base))
        for i, data in blocs_data.items():
            fin = (fin + 3) & ~3
            ext_t.ecrit(fin, data)
            assert -0x8000 <= fin - base < (0x8000 if signe else 0x10000)
            ext_t.ecrit(base + 2 * i, struct.pack(">h" if signe else ">H", fin - base))
            fin += len(data)
        ext_t.fin = max(ext_t.fin, fin - ext_t.base)
        assert hi - lo + nt < (0x8000 if signe else 0x10000), "%s : données trop étendues" % nom
        for site in sites: lea_site(site, T, base, nom)
        tabs[nom] = "$%06X -> $%06X (%d entrées, données $%X o)" % (T, base, NDEC, hi - lo)
        return base

    # listes (la routine copie 128 octets de liste)
    def liste_tr(Lp):
        b = bytes(num[Lp][n] for n in lst[Lp])
        return sw_octets(b + b"\0" * (128 - len(b)))
    table_rel("listes scroll1", M["list1"], M["sites"]["liste1"], {I: liste_tr(1)}, 128)
    table_rel("listes scroll2", M["list2"], M["sites"]["liste2"], {I: liste_tr(2)}, 128)
    table_rel("listes scroll3", M["list3"], M["sites"]["liste3"], {I: liste_tr(3)}, 128)
    # palettes (0RGB, la routine ajoute $F000) : 32 palettes x 32 o
    for Lp in (1, 2, 3):
        data = b"".join(struct.pack(">16H", *p) for p in pal2[Lp])
        table_rel("palettes scroll%d" % Lp, M["pal"][Lp], M["sites"]["pal%d" % Lp], {I: data}, 0x400)
    table_rel("palettes sprites de decor", 0x15D910, [0x6326, 0x6588], {}, 0x100)
    # objets de décor (listes d'enregistrements de 16 o, fin = mot négatif) : liste vide pour l'essai
    def taille_objets(a):
        n = 0
        while w(img, a + 16 * n) < 0x8000: n += 1
        return 16 * n + 2
    T = 0x358BC0
    tob = max(taille_objets(T + ws(img, T + 2 * j)) for j in range(32))
    table_rel("objets de decor", T, [0x670A, 0x6716], {I: b"\xff\xff\xff\xff"}, tob)

    # ---- 4. code : trampolines (tables de sauts en ligne, alias de registre), gestionnaires neufs, musique
    sauts = collections.OrderedDict()
    import tables_saut as TS
    for site, nom in ((0x02540A, "ordre des plans"), (0x025470, "gestionnaire scroll1"), (0x025B9A, "gestionnaire scroll2"),
                      (0x025EF0, "gestionnaire scroll3"), (0x022556, "effet par decor"), (0x001FA8, "ordre des plans (fins)")):
        k, t1, t2, cib = TS.lit(img0, site)
        sauts[site] = dict(nom=nom, kind=k, t1=t1, t2=t2, cibles=cib)
    asm = []
    A = asm.append
    A("; genere par construit.py — trampolines et gestionnaires du decor SFA2 (programme traduit ro3)")
    A("\torg $%X" % CODE0)
    A("\tdc.l\tSYMTAB_N\t; table des symboles (lue par construit.py)")
    A("SYMTAB:")
    # tables de sauts étendues
    nouv = {0x02540A: "$2545A", 0x025470: "H1_RYU2", 0x025B9A: None, 0x025EF0: "H3_RYU2", 0x022556: "$23134", 0x001FA8: None}
    for site, t in sauts.items():
        lab = "TJ_%06X" % site
        A("%s:\tcmpi.w\t#$40,d0\n\tbcc.s\t.ext\n\tmove.l\ta0,-(sp)\n\tlea\t($%X).l,a0\n\tmove.w\t(a0,d0.w),d1\n\tlea\t($%X).l,a0\n\tadda.w\td1,a0\n\tbra.s\t.go" % (lab, t["t1"], t["t2"]))
        A(".ext:\tmove.l\ta0,-(sp)\n\tlea\t(%s_L-$80).l,a0\n\tmove.w\td0,d1\n\tadd.w\td1,d1\n\tmovea.l\t(a0,d1.w),a0" % lab)
        A(".go:\tmove.l\ta0,-(sp)\n\tmovea.l\t4(sp),a0\n\tmove.l\t(sp)+,(sp)\n\trts")
        A("\tcnop\t0,4\n%s_L:" % lab)
        for i in range(32, NDEC):
            cible = t["cibles"][alias(i)]
            if i == I and nouv.get(site): A("\tdc.l\t%s\t; decor $%02X (SFA2 Ryu)" % (nouv[site], 2 * i))
            else: A("\tdc.l\t$%X" % cible)
        patch(site + 4, bytes.fromhex(("4eb9" if t["kind"] == "jsr" else "4ef9") + "00000000") + bytes.fromhex("4e71"),
              None, "%s : table de sauts étendue" % t["nom"])
        t["lab"] = lab
    # alias de registre : Dn = $100 ; si >= $50 : Dn -= $50 (décor SFA3 du même perso)
    alias_sites = [  # site, octets d'origine (hexa), registre, instructions déplacées après l'alias, rôle
        (0x02FA1A, "322d0100e549", "d1", "\tlsl.w\t#2,d1", "animation par decor ($304E8)"),
        (0x02FB66, "322d0100e549", "d1", "\tlsl.w\t#2,d1", "animation par decor ($304E8, 2e site)"),
        (0x0193F8, "322d010041f900378a20", "d1", "\tlea\t($378A20).l,a0", "animations des objets de decor ($378A20)"),
        (0x01A76E, "302d010041f9001868b0", "d0", "\tlea\t($1868B0).l,a0", "donnees par decor ($1868B0)"),
        (0x02F804, "302d0100e208", "d0", "\tlsr.b\t#1,d0", "masque par decor ($C0A00400)"),
        (0x079880, "302d0100e248", "d0", "\tlsr.w\t#1,d0", "masque par decor ($3F60BDB3)"),
    ]
    for site, orig, r, depl, role in alias_sites:
        lab = "TA_%06X" % site
        A("%s:\tmove.w\t$100(a5),%s\n\tcmpi.w\t#$%X,%s\n\tbcs.s\t.ok\n\tsubi.w\t#$%X,%s\n.ok:\n%s\n\trts" % (lab, r, D_NEW, r, D_NEW, r, depl))
        ob = bytes.fromhex(orig)
        patch(site, bytes.fromhex("4eb900000000") + bytes.fromhex("4e71") * ((len(ob) - 6) // 2), ob, "alias : " + role)
    # sites dont l'instruction suivante est une cible de branchement (boucle) : seule la lecture (4 o) est remplacée,
    # par « jsr $0C40.w » (zone libre basse $C40-$FFF, après le gestionnaire d'IRQ)
    court = os.path.join(so, "court.s")
    open(court, "w").write("\torg $C40\nTA_D3:\tmove.w\t$100(a5),d3\n\tcmpi.w\t#$%X,d3\n\tbcs.s\t.ok\n\tsubi.w\t#$%X,d3\n.ok:\trts\n" % (D_NEW, D_NEW))
    r = subprocess.run([VASM, "-Fbin", "-m68000", "-no-opt", "-quiet", "-o", court[:-2] + ".bin", court], capture_output=True, text=True)
    if r.returncode: raise SystemExit("vasm court :\n" + r.stdout + r.stderr)
    cb = open(court[:-2] + ".bin", "rb").read()
    assert img[0xC40:0xC40 + len(cb)] == b"\0" * len(cb)
    img[0xC40:0xC40 + len(cb)] = cb
    for site, role in ((0x010E68, "animation de palettes (table par decor)"), (0x03C32A, "animation de palettes (2e copie)")):
        patch(site, bytes.fromhex("4eb80c40"), bytes.fromhex("362d0100"), "alias : " + role + " (jsr $C40.w)")
    # gestionnaires neufs (parallaxe de Ryu SFA2 : scroll1 X,Y = 3/4 ; scroll3 X,Y = 1/4 ; positions initiales)
    A("""; scroll1 (SFA2 $1A8D2 : init X=$1C0 Y=0 ; X = 3/4 camera ($1AF54), Y = 3/4 ($1B104))
H1_RYU2:\tmove.b\t$5(a6),d0
\tbne.s\t.maj
\tmove.w\t#$1C0,d0
\tmoveq\t#0,d1
\tjsr\t($2594C).l
\tjmp\t($25B68).l
.maj:\tbsr.s\t.x
\tbsr.s\t.y
\tjmp\t($25B68).l
.x:\tmove.w\t$2A2(a5),d0
\tsub.w\t$28A(a5),d0
\tmove.w\td0,d1
\tasr.w\t#2,d1
\tsub.w\td1,d0
\tadd.w\t$A(a6),d0
\tjmp\t($25A84).l
.y:\tmove.w\t$2A6(a5),d0
\tsub.w\t$28E(a5),d0
\tmove.w\td0,d1
\tasr.w\t#2,d1
\tsub.w\td1,d0
\tadd.w\t$E(a6),d0
\tjmp\t($25B22).l
; scroll3 (SFA2 $1B86A : init X=$140 Y=0 ; X = 1/4 ($1BE0C), Y = 1/4 ($1BF22))
H3_RYU2:\tmove.b\t$5(a6),d0
\tbne.s\t.maj
\tmove.w\t#$140,d0
\tmoveq\t#0,d1
\tjsr\t($26330).l
\tjmp\t($264EA).l
.maj:\tbsr.s\t.x
\tjsr\t($26476).l
\tjmp\t($264EA).l
.x:\tmove.w\t$2A2(a5),d0
\tsub.w\t$28A(a5),d0
\tasr.w\t#2,d0
\tadd.w\t$A(a6),d0
\tjmp\t($2646C).l""")
    # musique : au départ de la commande de musique de combat ($2219E : moveq #0,d2 ; moveq #0,d3 ; bra $21F9C)
    mus2 = [w(S2.O, S2.T["musique"] + 2 * k) for k in range(18)]
    A("""; musique : decor >= $50 -> code de la musique SFA2 du decor (flux ADX ZERO 2 = $50 + code SFA2)
TM_MUS:\tmove.w\t$100(a5),d2
\tsubi.w\t#$%X,d2
\tbcs.s\t.sfa3
\tmove.w\tTM_MUS_T(pc,d2.w),d1
.sfa3:\tmoveq\t#0,d2
\tmoveq\t#0,d3
\tjmp\t($21F9C).l
TM_MUS_T:""" % D_NEW)
    for k in range(18): A("\tdc.w\t$%04X\t; decor SFA2 $%02X" % (0x50 + mus2[k], 2 * k))
    patch(0x2219E, bytes.fromhex("4ef9000000004e71"), bytes.fromhex("740076006000fdf8"), "musique : code SFA2 pour un decor >= $50")
    rap["musique"] = {"Ryu SFA2": "commande $%04X (table SFA2 $154EE : %02X)" % (0x50 + mus2[0], mus2[0])}
    # sélection Arcade : au point de choix ($4A406 : D0 = décor SFA3 x 2 du perso adverse, avant les cas des combats
    # spéciaux (Bison final $14, rivaux $A33B0) qui gardent leurs décors SFA3)
    if a.selection != "aucune":
        mode = {"sfa3": 0, "sfa2": 1, "alea": 2}[a.selection]
        tab = [0xFF] * 18
        tab[0] = D_NEW                                    # Ryu ($00) -> Ryu SFA2 ($50)
        if a.table_essai: tab = [D_NEW] * 18
        A("""; selection du decor (mode Arcade) : D0 = decor SFA3 x 2 ; SEL_MODE 0 = SFA3, 1 = SFA2, 2 = tirage (hasard $11514)
SEL:\tmove.l\td1,-(sp)
\tcmpi.w\t#$24,d0
\tbcc.s\t.garde
\tmove.w\td0,d1
\tlsr.w\t#1,d1
\tmove.b\tSEL_TAB(pc,d1.w),d1
\tcmpi.b\t#$FF,d1
\tbeq.s\t.garde
\tmove.b\tSEL_MODE(pc),-(sp)
\tmove.b\t(sp)+,d1
\tbeq.s\t.garde
\tsubq.b\t#1,d1
\tbeq.s\t.sfa2
\tmove.w\td0,-(sp)
\tjsr\t($11514).l
\tbtst\t#0,d0
\tmovem.w\t(sp)+,d0
\tbeq.s\t.garde
.sfa2:\tmove.w\td0,d1
\tlsr.w\t#1,d1
\tmove.b\tSEL_TAB(pc,d1.w),d0
\tandi.w\t#$FF,d0
.garde:\tmove.w\td0,$174(a5)
\tclr.b\t$110(a5)
\tmove.l\t(sp)+,d1
\trts
SEL_MODE:\tdc.b\t%d
SEL_TAB:""" % mode)
        A("\tdc.b\t" + ",".join("$%02X" % x for x in tab))
        A("\teven")
        patch(0x4A428, bytes.fromhex("4eb9000000004e71"), bytes.fromhex("3b400174422d0110"), "selection Arcade : tirage SFA3/SFA2 par perso")
        rap["selection"] = dict(mode=a.selection, table=["$%02X" % x for x in tab])
    A("CODE_FIN:")
    noms = [t["lab"] for t in sauts.values()] + ["TA_%06X" % x[0] for x in alias_sites] + ["TM_MUS", "H1_RYU2", "H3_RYU2"] + (["SEL"] if a.selection != "aucune" else []) + ["CODE_FIN"]
    i0 = asm.index("SYMTAB:")
    asm[i0 + 1:i0 + 1] = ["\tdc.l\t%s" % n for n in noms]
    asm[i0 - 1] = "\tdc.l\t%d\t; nombre de symboles" % len(noms)
    src = os.path.join(so, "tramp.s"); open(src, "w").write("\n".join(asm) + "\n")
    binf = os.path.join(so, "tramp.bin"); lst_f = os.path.join(so, "tramp.lst")
    r = subprocess.run([VASM, "-Fbin", "-m68000", "-no-opt", "-quiet", "-L", lst_f, "-o", binf, src], capture_output=True, text=True)
    if r.returncode: raise SystemExit("vasm :\n" + r.stdout + r.stderr)
    code = open(binf, "rb").read()
    assert CODE0 + len(code) <= CODE1, "zone de code trop petite (%d o)" % len(code)
    assert img[CODE0:CODE0 + len(code)] == b"\0" * len(code)
    img[CODE0:CODE0 + len(code)] = code
    nsym = L(code, 0)
    syms = {n: L(code, 4 + 4 * k) for k, n in enumerate(noms)}
    assert nsym == len(noms)
    for site, t in sauts.items():
        img[site + 6:site + 10] = struct.pack(">I", syms[t["lab"]])
    for site, *_ in alias_sites:
        img[site + 2:site + 6] = struct.pack(">I", syms["TA_%06X" % site])
    img[0x2219E + 2:0x2219E + 6] = struct.pack(">I", syms["TM_MUS"])
    if "SEL" in syms: img[0x4A428 + 2:0x4A428 + 6] = struct.pack(">I", syms["SEL"])
    rap["code"] = {"zone": "$%X-$%X (%d o)" % (CODE0, CODE0 + len(code), len(code)), "symboles": {k: "$%X" % v for k, v in syms.items()}}
    rap["tables_relogees"] = tabs
    rap["patches"] = [dict(adresse="$%06X" % p[0], avant=p[1], apres=img[p[0]:p[0] + len(bytes.fromhex(p[2]))].hex(), role=p[3]) for p in patches]

    # ---- 5. écritures
    image.ecrit(img, os.path.join(so, "roms/sfa3hx"), modele=a.roms)
    ed = os.path.join(so, "ext"); os.makedirs(ed, exist_ok=True)
    for f in os.listdir(ed): os.unlink(os.path.join(ed, f))
    os.symlink(os.path.realpath(os.path.join(R, "base/ext/ext_a04000.bin")), os.path.join(ed, "ext_a04000.bin"))
    open(os.path.join(ed, "ext_b00000.bin"), "wb").write(ext_l.octets())
    open(os.path.join(ed, "ext_c80000.bin"), "wb").write(ext_t.octets())
    open(os.path.join(ed, "ext_liste.txt"), "w").write("a04000\nb00000\nc80000\n")
    open(os.path.join(so, "hsfa_plans_sfa2.bin"), "wb").write(plans)
    rap["ext"] = {"ext_b00000.bin": len(ext_l.octets()), "ext_c80000.bin": len(ext_t.octets())}
    json.dump(rap, open(os.path.join(so, "rapport.json"), "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: rap[k] for k in ("tuiles_neuves", "bibliotheques", "cpsb", "musique", "ext")}, indent=1, ensure_ascii=False))
    print("code", rap["code"]["zone"], "; patches", len(patches))


if __name__ == "__main__":
    main()
