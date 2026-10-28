"""(agent_integration_max) INTÉGRATION DES PERSOS MAX (Eagle, Maki, Yun, Ingrid) DANS UPPER — option de construction.

MAX=1 (avec MODULE=ro5) : mame_test.py appelle les 3 étapes ci-dessous. Sans MAX (ou MAX=0) : rien n'est appelé, la ROM
est identique à l'octet. Le code et les données MAX sont préparés à part (outils/prepare_max.py) dans MAX_DIR (défaut
work/agent_integration_max/prep) : ext_b80000.bin (code + données MAX, $B80000, hors des plages converties par CONV),
symboles.json, ext_d40000.bin ... ext_e00000.bin (frames et animations, convertit_frames.py).
Persos actifs : MAX_PERSOS (défaut : ceux marqués « actif » dans outils/persos_max.json), ex. MAX_PERSOS=26.

Étapes :
  donnees(...)      : tables de DONNÉES par perso (pointeurs PS2 petit-boutistes dans 'data', avant relogement)
  tables_code(...)  : tables de CODE relogées (étape B) -> enveloppes MAX ; tables déplacées remplies dans le bloc MAX
  image(...)        : LEA des tables déplacées, seuil de la grille, blocs externes écrits dans W."""
import max_cache as MC
import os, sys, json, struct, hashlib, re
import agrandit_max as AG
ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.environ.get("MAX_RACINE", "<workspace>/work/agent_integration_max")   # outils, persos_max.json, prep
DIR = os.environ.get("MAX_DIR", os.path.join(RACINE, "prep"))
PERSOS = {k: v for k, v in json.load(open(os.path.join(RACINE, "outils", "persos_max.json"))).items() if not k.startswith("_")}
ACTIFS = [p for p in (os.environ.get("MAX_PERSOS") or ",".join(k for k, v in PERSOS.items() if v.get("actif"))).split(",") if p]
SYM = None; BLOB = None; ORG = None
RB = 0x1F0000

J = None
def charge():
    global SYM, BLOB, ORG, J
    if SYM is None:
        J = json.load(open(os.path.join(DIR, "symboles.json")))
        SYM, ORG = J["symboles"], J["org"]; SYM["_carte_md5"] = J["carte_md5"]
        BLOB = bytearray(open(os.path.join(DIR, "blocs", "ext_%06x.bin" % ORG), "rb").read())
    return SYM

ASSET_EXT = 0xC00000                    # bloc des tables d'animation natives hors de l'image ($BC0000-$BFFFFF : base
                                        # chargée nativement par le fork, non convertie ; données MAX en $B80000)
def asset_ext(n):
    assert ASSET_EXT + n <= 0xC80000, "bloc des animations natives : %d octets > $80000" % n   # (17/10 : $BC0000 -> $C00000, bios MAX)
    charge(); assert ORG + J["taille"] <= ASSET_EXT, "données MAX ($%x+%d) sur le bloc des animations natives" % (ORG, J["taille"])
    return ASSET_EXT

# BIO (écran d'histoire) : fichiers d'animation natifs par perso (T_PERSO 0x628470 -> table $37AF00 -> $C0BC(A5)) ;
# session MAX : converti/plXX/bio/anim_bio.bin (pointeurs relatifs à $B83800) ; tuiles dans max_plus_gfx (hud_apercu_max)
BIO_N = {"26": 3938, "27": 3939, "2d": 3945, "2e": 3946}     # n° de fichier fictifs (banques_hx/f<N>.bin, carte « anim »)
FIN_N = {"26": 3978, "27": 3979, "2d": 3985, "2e": 3986}     # fichiers de fin MAX (emplacement 4) : n° fictifs
FIN_FICHIERS = {}; AN_BUF = []
def bio(ablob, ava, aperso, AN):
    import shutil
    charge()
    HP = json.load(open(os.path.join(DIR, "max_plus.json"))); B = HP.get("bio", {})
    ablob = bytearray(ablob); ava = dict(ava); ap = list(aperso) + [aperso[0]] * (48 - len(aperso))
    W_ = os.environ.get("MAX_W"); carte = []
    for p in ACTIFS:
        if p not in B: continue
        n = BIO_N[p]; d = bytearray(open(B[p]["anim"], "rb").read()); d += bytes(-len(d) % 16)
        base = AN.VBASE + len(ablob)
        for o in range(0, len(d) - 3, 4):
            v = struct.unpack_from("<I", d, o)[0]
            if AN.LOAD_BASE <= v < AN.LOAD_BASE + len(d): struct.pack_into("<I", d, o, v - AN.LOAD_BASE + base)
        ablob += d; ava[n] = base; ap[int(p, 16)] = n
        shutil.copy(os.path.join(DIR, B[p]["table"]), os.path.join(W_, "banques_hx", "f%d.bin" % n))
        carte.append("anim %d %d" % (AN.swapped(base), n))
    # PALIER 4 : fichier de fin MAX (emplacement 4) = copie du fichier d'animation de fin du modèle, à une adresse PROPRE
    # (clé de la carte du fork) ; sa banque gfx = tuiles des décors MAX (codes locaux 0..) ; table du chargeur de fin
    # (fins_fichiers) -> ce fichier
    global FIN_FICHIERS
    FIN_FICHIERS = {}
    if os.environ.get("MAX_FINS") == "1" and os.environ.get("MAX_P4", "1") == "1":
        afin0 = AN.fin_tables(AN_BUF[0]) if AN_BUF else []
        for p in ACTIFS:
            if p not in FIN_MODELE or p not in HP.get("decor", {}) or not afin0: continue
            n = FIN_N[p]; nm = afin0[FIN_MODELE[p]] or afin0[0]     # modèle sans fichier (Maki : $07) : conteneur = 1er
            d = bytearray(AN.fichier(nm)); d += bytes(-len(d) % 16)
            base = AN.VBASE + len(ablob)
            for o in range(0, len(d) - 3, 4):
                v = struct.unpack_from("<I", d, o)[0]
                if AN.LOAD_BASE <= v < AN.LOAD_BASE + len(d): struct.pack_into("<I", d, o, v - AN.LOAD_BASE + base)
            ablob += d; ava[n] = base; FIN_FICHIERS[p] = n
            # banque = table du fichier de fin du MODÈLE (N entrées, sprites du modèle) PUIS tuiles des FD (codes des FD
            # décalés de N à l'assemblage, prepare_max.decor_base)
            g = struct.unpack_from("<h", AN_BUF[0], AN.T_FIN - 0x1F0000 + 4 * FIN_MODELE[p])[0]
            fm = os.path.join(W_, "banques_hx", "f%d.bin" % g)
            tm = open(fm, "rb").read() if g and os.path.exists(fm) else b""
            open(os.path.join(W_, "banques_hx", "f%d.bin" % n), "wb").write(tm + open(os.path.join(DIR, HP["decor"][p]["table"]), "rb").read())
            carte.append("anim %d %d" % (AN.swapped(base), n))
        if FIN_FICHIERS: log("fins : fichiers de fin MAX (emplacement 4, décors) : %s" % ", ".join("$%s -> %d" % kv for kv in FIN_FICHIERS.items()))
    f = os.path.join(W_, "banques_hx", "carte.txt")
    L = [l for l in open(f).read().splitlines() if not any(l.endswith(" %d" % BIO_N[p]) or l.endswith(" %d" % FIN_N[p]) for p in BIO_N)]
    open(f, "w").write("\n".join(L + carte) + "\n")
    log("bio : %s (fichiers natifs ajoutés au bloc, table par perso à %d entrées)" % (", ".join(PERSOS[p]["nom"] for p in ACTIFS if p in B), len(ap)))
    return bytes(ablob), ava, ap

def ecrit_asset(W, ext_plus, d):
    open(os.path.join(W, "ext_%06x.bin" % ASSET_EXT), "wb").write(d); ext_plus.append("%06x" % ASSET_EXT)
    log("tables d'animation natives : %d octets en bloc externe $%x (place libérée dans l'image pour le code MAX)" % (len(d), ASSET_EXT))

def reserve():
    """octets réservés en haut de l'image (sous la table de hachage $3C0000) pour le CODE MAX"""
    charge(); assert J["code_org"] + J["reserve"] == 0x3C0000
    return J["reserve"]

def S(n):
    s = charge()
    assert n in s, "symbole MAX absent : %s" % n
    return s[n]

# ------------------------------------------------------------------------------------------------- tables d'Upper
# tables par perso (40 entrées, PS2) : homologues des tables arcade $DCB12... (même ordre, $A0 au lieu de $80)
T_DCB12, T_DD012, T_DD092, T_DD112, T_DD412 = 0x748CF8, 0x749338, 0x7493D8, 0x749478, 0x749838
T_DF892 = 0x74C5D8                                  # -> $264 (arcade $DF892)
T_MARCHE = (0x7498D8, 0x749A18, 0x749B58)           # arcade $DD492 / $DD592 / $DD692 (8 o par perso)
T_SAUTS = (0x749C98, 0x74A698, 0x74B098)            # arcade $DD792 / $DDF92 / $DE792 (64 o par perso)
CLES_PHYS = ("$DD492 (marche, $132=0)", "$DD592 (marche, $132 autre)", "$DD692 (marche, $132=$FF)",
             "$DD792 (saut, $132=0)", "$DDF92 (saut, $132 autre)", "$DE792 (saut, $132=$FF)")
T_PROJ = 0x6102B0                                   # routines des projectiles ($32F46), par TYPE d'objet
T_EFFETS = 0x60D070                                 # classes du réservoir d'effets $4800(A5) (40 entrées)
T_PAL = 0x6F72B0                                    # palettes par perso (40 décalages signés relatifs à la table)
T_PROPRIO = 0x61C0E0                                # « propriétaire » de banque par perso (choix de $1A, BANQUE-1A §2.1)
PROPRIO = {"26": 0x26, "27": 0x27, "2d": 0x24, "2e": 0x25}   # distincts de tous les autres (< $28 : compteur $C26C)
T_GRILLE = 0x61BFB0                                 # grille de sélection (8 x 8 octets)
SEUIL_VA = 0x255C84                                 # CMPI.B #$26,D0 (seuil des cases « ? »)
SEUIL = 0x30                                        # nouveau seuil : au-delà de $2E (Ingrid)
T_CURSEUR = 0x61BE70                                # (colonne, rangée) par ID, 48 entrées déjà
TYPE_PROJ = {"26": "TYPE_PROJ_EAGLE", "2d": "TYPE_PROJ_YUN", "2e": "TYPE_PROJ_INGRID"}
FILS = {"26": "psp_fils_26", "2d": "psp_fils_28", "2e": "psp_fils_29"}
# classes MAX du réservoir d'effets ($1C368, en-tête $0100ttss) -> routine (moteur-integration §7)
CLASSES = {"26": {0x33: "psp_1b3904", 0x34: "psp_1b3c20"}, "27": {0x2F: "psp_1ba87c", 0x30: "psp_1ba38c", 0x31: "psp_1ba3d8"},
           "2d": {0x32: "psp_1bfbf4", 0x38: "psp_1c08b0", 0x39: "psp_1c0914"},
           "2e": {0x35: "psp_1c7260", 0x36: "psp_1c6e58", 0x37: "psp_1c8874", 0x3A: "psp_1c8f10"}}
JOURNAL = []
CRIS = {"26": 0x05D9, "27": 0x05E2, "2d": 0x05F0, "2e": 0x06F6}   # bases de cris (agent_son_max, 17/10)

def log(m): JOURNAL.append(m); print("MAX : " + m)

def donnees(buf, data, end, T, W=None):
    """pointeurs et valeurs PAR PERSO dans les données PS2 (petit-boutistes)"""
    charge()
    if W: os.environ["MAX_W"] = W
    o = lambda a: a - RB - end
    put = lambda a, v: struct.pack_into("<I", data, o(a), v & 0xFFFFFFFF)
    global ORIG; ORIG = bytes(buf)
    def pose(t, i, b, e=None, decal=0, rang=0):
        """entrée i (rangée rang) de la table t (PS2) : en place si i < 40, sinon dans la copie agrandie (agrandit_max)"""
        e = e or len(b)
        a = t + e * (40 * rang + i) + decal
        if i < 40: data[o(a):o(a) + len(b)] = b
        else: AG.ajout(t, i, b, decal, rang)
    p32 = lambda v: struct.pack("<I", v & 0xFFFFFFFF)
    phys = json.load(open(os.path.join(RACINE, "max_trad", "rosette_code", "physique_max_arcade.json")))
    # contrôle : Ryu ($00) des tables de sauts = arcade (adresses PS2 des tables)
    assert struct.unpack_from("<4I", data, o(T_SAUTS[0])) == (0, 0x72000, 0, 0xFFFFB000), "table de sauts d'Upper inattendue"
    for p in ACTIFS:
        i = int(p, 16); P = PERSOS[p]
        D = "MAXD_%s_" % p
        for t, n in ((T_DCB12, "DCB12"), (T_DD012, "ENTETE_ISM"), (T_DD092, "T88"), (T_DD112, "TC0"), (T_DF892, "T264")):
            pose(t, i, p32(S(D + n)))
        pose(T_DD412, i, p32(S("ANIM_%s_PTRS" % P["suffixe"])))
        pose(0x613350, i, bytes([MUSIQUE[p]]))           # musique (QSound, sans flux) : choix provisoire
        pose(0x74C538, i, p32(S("SONS_PAS_%s" % P["suffixe"])))   # sons par pas ($E6) : session MAX, sons_pas_max.s
        if p in CRIS:                                    # cris (agent_son_max, ROM son roms_son_max) : base, et base + 5
            pose(0x613490, i, struct.pack("<H", CRIS[p])); pose(0x613440, i, struct.pack("<H", CRIS[p] + 5))
        for k, cle in enumerate(CLES_PHYS):
            v = [int(x, 16) for x in phys[cle][P["suffixe"]]]
            base = (T_MARCHE + T_SAUTS)[k]; pas = 8 if k < 3 else 64
            assert len(v) * 4 == pas
            pose(base, i, struct.pack("<%dI" % len(v), *v))
        pose(0x61C160, i, bytes([i]))                    # ID -> ID (va 0x272DCC) : le perso reste lui-même
        pose(0x60AD90, i, bytes([i]))                    # ID -> ID de base (chargeur natif par perso : bio) : lui-même
        pr = o(T_PROPRIO)
        assert PROPRIO[p] not in [data[pr + k] for k in range(0x26)], "propriétaire $%x déjà pris" % PROPRIO[p]
        avant = data[pr + i] if i < 40 else data[pr]; pose(T_PROPRIO, i, bytes([PROPRIO[p]]))
        log("%s ($%s) : propriétaire de banque T_61c0e0[$%s] $%02x -> $%02x" % (P["nom"], p, p, avant, PROPRIO[p]))
        log("%s ($%s) : tables de données (en-tête/boîtes/attaques, $88, $C0, $DCB12, $264, animations, marche, sauts)" % (P["nom"], p))
    # habillage : noms (cartouche JP / US), bandeaux défilants (J1/J2, JP/US), icône de la grille
    ico = json.load(open(MC.CV + "icones/icones.json"))
    for p in ACTIFS:
        i = int(p, 16); pl = PERSOS[p]["pl"]
        for t in (0x961B30, 0x961C70): pose(t, i, p32(S("MAXNOM_%s" % p)), e=8, decal=4)
        BJ = json.load(open(MC.CV + "noms/bandeau.json"))[pl]
        for t, k in ((0x9625B8, "J1_JP"), (0x9626F8, "J1_US"), (0x962838, "J2_JP"), (0x962978, "J2_US")):
            if "MAXBV_26_1P" in SYM:
                # (2b22) ces 4 tables sont les COLONNES VERTICALES de la sélection (frames $0A, une lettre par objet) :
                # entrées MAXBV_E de la session MAX (frises_verticales_max.s : attr du modèle avec $4000, frame MAXBV)
                j_ = "1P" if k.startswith("J1") else "2P"
                fv = open(MC.CV + "bandeau_noms/frises_verticales_max.s").read()
                m_ = re.search(r"^MAXBV_E_%s_%s_%s:.*\n\s+dc\.l\s+\$([0-9A-Fa-f]{8})" % (j_, k[3:], p.upper()), fv, re.M)
                v_ = int(m_.group(1), 16)
                pose(t, i, struct.pack("<II", ((v_ & 0xFFFF) << 16) | (v_ >> 16), S("MAXBV_%s_%s" % (p.upper(), j_))), e=8)
                continue
            pose(t, i, p32(S("MAXBAND_%s_%s" % (p, k))), e=8, decal=4)
            # (2b21) attribut (longueur du défilement, octet haut) = celui du natif dont le bandeau a la même table de
            # positions et le même nombre de tuiles (session MAX : « comme MA1PAKUMA… ») ; avant : attribut de l'entrée
            # par défaut (Ryu / place 38-39) -> nom d'Eagle (23) et d'Ingrid (24) défilant de travers
            pos_ = int(BJ[k]["positions"].split()[0], 16); n_ = BJ[k]["n"]; attr_ = None
            for j in range(0x26):
                a_, q_ = struct.unpack_from("<II", data, o(t + 8 * j))
                if RB <= q_ < RB + len(ORIG) and struct.unpack_from("<HHHHI", ORIG, q_ - RB)[1] == n_ \
                        and struct.unpack_from("<HHHHI", ORIG, q_ - RB)[4] == pos_:
                    attr_ = a_; break
            # (essai 2b21 : sans effet sur le sens du défilement d'Eagle -> désactivé, MAX_BANDEAU_ATTR=1 pour l'essayer)
            if attr_ is not None and os.environ.get("MAX_BANDEAU_ATTR") == "1": pose(t, i, p32(attr_), e=8, decal=0)
            else: log("%s ($%s) : bandeau %s : aucun natif de même table de positions $%x / %d tuiles" % (PERSOS[p]["nom"], p, k, pos_, n_))
        I = ico[pl]; e = I["entree_liste_icones"]
        assert struct.unpack_from("<H", data, o(0x962B30))[0] == 0x10 and e < 37
        struct.pack_into("<HH", data, o(0x962B3C + 4 * e), MC.PB1 + (int(I["code_global"][1:], 16) - MC.G0) - 0x1C00, I["attribut"])
        log("%s ($%s) : nom, bandeaux, icône (entrée %d de la liste $10)" % (PERSOS[p]["nom"], p, e))
    # (2b12) bandeau « WINNER : nom » de l'écran de victoire : 4 listes de {attr, frame} par ID (0x961AF0 +$5C8/$708/$848/
    # $988, agrandies à 48 par la structure) -> entrées MAXBN_E_<1P|2P>_<JP|US>_<ID> de bandeau_noms_max.s (session MAX)
    fb = MC.CV + "bandeau_noms/bandeau_noms_max.s"
    if os.path.exists(fb) and "MAXBN_26_1P" in SYM:
        import re as _re
        txt = open(fb).read(); nb_ = 0
        for jp, t in (("1P_JP", 0x9620B8), ("1P_US", 0x9621F8), ("2P_JP", 0x962338), ("2P_US", 0x962478)):
            for p in ACTIFS:
                m = _re.search(r"^MAXBN_E_%s_%s:.*\n\s+dc\.l\s+\$([0-9A-Fa-f]{8})\s*\n\s+dc\.w\s+\(MAXBN_(\w+)\)" % (jp, p.upper()), txt, _re.M)
                if not m: continue
                v = int(m.group(1), 16); attr = ((v & 0xFFFF) << 16) | (v >> 16)        # long image -> valeur PS2
                pose(t, int(p, 16), struct.pack("<II", attr, S("MAXBN_%s" % m.group(2))), e=8); nb_ += 1
        log("bandeau WINNER : %d entrées (4 listes x persos MAX)" % nb_)
    # (2b15) colonne de nom de la CARTE DU MONDE : listes {attr, frame} par ID de la structure 0x967F2A (+$292 et +$3D2,
    # frames $0A : une tuile-nom répétée) ; attr de l'entrée native de même hauteur (Gouki h 3, Ryu h 2)
    if "MAXCARTE_26" in SYM:
        nc = 0
        for p in ACTIFS:
            lab = "MAXCARTE_%s" % p.upper()
            if lab not in SYM: continue
            attr = 0x30000008 if p in ("26", "2e") else 0x20000008
            for o_ in (0x292, 0x3D2): pose(0x967F2A + o_, int(p, 16), struct.pack("<II", attr, S(lab)), e=8); nc += 1
        log("carte du monde : %d entrées de nom MAX (0x967F2A +$292 / +$3D2)" % nc)
    # (2b12) « WINNER:<nom> » vertical : animation n° T_616850[ID (+$28 US)] de 0x966740 ; persos MAX -> 48 + rang
    # (winner_noms_max.s de la session MAX : MAXWIN_PAS_xx = pas de 8 o, MAXWIN_xx = frame $0C)
    fw = MC.CV + "winner_noms/winner_noms_max.s"
    if os.path.exists(fw) and "MAXWIN_26" in SYM:
        import re as _re
        txt = open(fw).read(); nw = 0
        for rang_, p in enumerate(("26", "27", "2d", "2e")):
            if p not in ACTIFS: continue
            m = _re.search(r"^MAXWIN_PAS_%s:.*\n\s+dc\.w\s+\$([0-9A-Fa-f]{4}),\s*\$([0-9A-Fa-f]{4})" % p.upper(), txt, _re.M)
            pas = struct.pack("<HHI", int(m.group(1), 16), int(m.group(2), 16), S("MAXWIN_%s" % p.upper()))
            AG.bloc_rel16(0x966740, 48 + rang_, pas)
            for r in (0, 1): pose(0x616850, int(p, 16), bytes([48 + rang_]), e=1, rang=r)
            nw += 1
        log("WINNER:<nom> : %d animations MAX (0x966740 48+) et T_616850 (2 rangées)" % nw)
    # (2b18) ancrages des flammes de brûlure sur une victime MAX (table 0x74C358 par ID touché, agrandie à 48) :
    # FLAMMES_xx de la session MAX (converti/flammes/flammes_max.s, 16 couples dx, dy déjà en ordre image)
    nf = 0
    if os.environ.get("MAX_FLAMMES_IDX", "aj") == "dup":     # (2b19) natifs : copies doublées (prepare_max.flammes_natives)
        nn = 0
        for i in range(0x26):
            q = struct.unpack_from("<I", ORIG, 0x74C358 - RB + 4 * i)[0]
            if "FLAMMES_N_%06X" % q in SYM: pose(0x74C358, i, p32(S("FLAMMES_N_%06X" % q))); nn += 1
        assert nn == 0x26, "flammes natives : %d entrées" % nn
    for p in ACTIFS:
        if "FLAMMES_%s" % p.upper() in SYM: pose(0x74C358, int(p, 16), p32(S("FLAMMES_%s" % p.upper()))); nf += 1
    log("flammes (0x74C358) : %d entrées MAX" % nf)
    # (2b18) recul des types de réaction 28-32 (session MAX, converti/recul/recul_max.s, ORDRE IMAGE) : séquences
    # RECUL_S25-S29 en entrées 25-29 des deux tables rel16 (0x9719C0 / 0x971CC0, mêmes séquences) ; T_61B460 -> RECUL_TYPES
    # (33 types, LEA en image $52DCE posé par image())
    fr = MC.CV + "recul/recul_max.s"
    if os.path.exists(fr) and "RECUL_TYPES" in SYM and os.environ.get("MAX_RECUL", "1") == "1":
        import re as _re
        txt = open(fr).read()
        for k in range(25, 30):
            m = _re.search(r"^RECUL_S%d:.*\n((?:\s+dc\.b\s+[^\n]*\n)+)" % k, txt, _re.M)
            b = bytes(int(x.strip().lstrip("$"), 16) for l in m.group(1).strip().split("\n") for x in l.split("dc.b")[1].split(";")[0].split(","))
            assert len(b) % 2 == 0
            ps2 = bytes(b[i ^ 1] for i in range(len(b)))       # ordre image -> ordre PS2 (octets échangés par mot)
            for t in (0x9719C0, 0x971CC0): AG.bloc_rel16(t, k, ps2)
        log("recul : séquences MAX 25-29 (types 28-32) dans 0x9719C0 / 0x971CC0")
    # (2b19) répliques de victoire : T_614E20 (index de réplique propre à l'adversaire, chemin $92(A5) = 0) -> $FF pour
    # un PERDANT MAX (réplique au hasard, comme hors table)
    for p in ACTIFS: pose(0x614E20, int(p, 16), b"\xff")
    # (2b24, N20) IA des persos MAX (session MAX, converti/ia/ia_max.s) : scripts propres en T0-T3 (0x74C0D8 / 0x74C178 /
    # 0x74C218 / 0x74C2B8) à la place des copies de Ryu (et de l'ancienne entrée 39 de Maki) ; condition 40 : talon_cond40
    if os.environ.get("MAX_IA", "1") == "1" and "IA_T0_26" in SYM:
        nia = 0
        for p in ACTIFS:
            for k, t in enumerate((0x74C0D8, 0x74C178, 0x74C218, 0x74C2B8)):
                lab = "IA_T%d_%s" % (k, p.upper())
                if lab in SYM: pose(t, int(p, 16), p32(S(lab))); nia += 1
        log("IA MAX : %d pointeurs de scripts posés (T0-T3)" % nia)
    # (2b24) défense par VICTIME (moteur de coups $51FC : tables 0x697FE0 / 0x6989E0 / 0x698EE0 [ID défenseur × 32 + ...]) :
    # l'arcade masque l'ID par $1F (Eagle $26 -> ligne 6 de Sodom) ; la PSP a ses propres lignes pour les 4 MAX (EBOOT EU
    # 0x2190C8 + 32 × id PSP, 0x697FE0 seule ; mesuré : Eagle prend 1 point de plus sur PSP sous Mika). image() passe les
    # deux ANDI.W #$1F en #$3F (même coût) ; ici, lignes $20-$2F = ligne (id & $1F) pour tout id non MAX (natifs inchangés),
    # lignes MAX de 0x697FE0 = PSP, de 0x6989E0 / 0x698EE0 = ligne (id & $1F) comme avant.
    if os.environ.get("MAX_DEF_VICTIME", "1") == "1":
        eb = open(os.environ.get("SFA3MAX_EBOOT", "<workspace>/sfa3max-psp-widescreen/work/eboot/ULES00235_EBOOT.BIN"), "rb").read()[0x74:]
        PSPID = {"26": 0x26, "27": 0x27, "2d": 0x28, "2e": 0x29}
        assert eb[0x2190C8:0x2190C8 + 32 * 0x26] == ORIG[0x697FE0 - RB:0x697FE0 - RB + 32 * 0x26], "défense par victime : table PSP 0x2190C8 inattendue"
        for t in (0x697FE0, 0x6989E0, 0x698EE0):
            for i in range(0x20, 0x30):
                h = "%02x" % i
                if t == 0x697FE0 and h in ACTIFS: b_ = eb[0x2190C8 + 32 * PSPID[h]:][:32]
                else: b_ = ORIG[t - RB + 32 * (i & 0x1F):][:32]
                pose(t, i, b_)
        log("défense par victime : lignes $20-$2F des 3 tables (0x697FE0 MAX = PSP 0x2190C8) ; ANDI #$1F -> #$3F en image")
    pose_generique(pose)
    # (2b24, N21) dialogues Arcade des MAX (converti/dialogues/dialogues_upper_max.s, disposition ARCADE) : répliques ->
    # 0x683C28 (US, rel16n, n° 756+ ; octets tels quels comme les textes de fin), scénarios -> 0x970F40 (rel16n, n° 154+ ;
    # mots -> ordre PS2) ; choix 0x61B580 / 0x61B600 : rangées de 48 posées en image() (talon_dialogues)
    fd = MC.CV + "dialogues/dialogues_upper_max.s"
    if os.path.exists(fd) and os.environ.get("MAX_DIALOGUES", "1") == "1":
        import re as _re
        txt = open(fd).read(); nr = ns = 0
        for m in _re.finditer(r"^DLG_R(\d+):[^\n]*\n((?:\s+dc\.b[^\n]*\n)+)", txt, _re.M):
            b = bytearray()
            for l in m.group(2).strip().split("\n"):
                for tok in _re.findall(r'"[^"]*"|\$[0-9A-Fa-f]+|\b\d+\b', l.split("dc.b", 1)[1]):
                    if tok.startswith('"'): b += tok[1:-1].encode("latin-1")
                    elif tok.startswith("$"): b.append(int(tok[1:], 16))
                    else: b.append(int(tok))
            AG.bloc_rel16(0x683C28, int(m.group(1)) - 1, bytes(b)); nr += 1      # n° global 1-based : n -> entrée n - 1 (en-tête de 755)
        for m in _re.finditer(r"^DLG_S(\d+):[^\n]*\n\s+dc\.w\s+([^\n;]+)", txt, _re.M):
            ws = [int(x.strip().lstrip("$"), 16) if x.strip().startswith("$") else int(x) for x in m.group(2).split(",")]
            AG.bloc_rel16(0x970F40, int(m.group(1)), struct.pack("<%dH" % len(ws), *ws)); ns += 1
        global DLG_CHOIX
        DLG_CHOIX = [(int(t, 16), (int(c) - 8) // 2, int(i, 16), int(v)) for t, c, i, v in
                     _re.findall(r"; +0x(61B580|61B600)\[\((\d+) - 8\) / 2 \* 40 \+ \$([0-9A-F]{2})\] = (\d+)", txt)]
        log("dialogues MAX : %d répliques (0x683C28), %d scénarios (0x970F40), %d choix" % (nr, ns, len(DLG_CHOIX)))
    # (2b22, R8 / R9 de la session MAX : converti/tables_id/tables_id_max.s) valeurs physiques par perso et carte du monde
    ft = MC.CV + "tables_id/tables_id_max.s"
    if os.path.exists(ft):
        tt = open(ft).read(); nb = 0
        # (2b24, R9-bis) genres à parenthèses imbriquées (« octet signé -> table … (moteur de coups) ») ; « ID -> … » = octet ;
        # lignes « probable » laissées de côté (valeurs MAX = défauts tant qu'elles ne sont pas confirmées)
        for m in re.finditer(r"; (0x[0-9A-F]+)(?: / 0x[0-9A-F]+)? \((.*?)\)\[\$([0-9A-F]{2})\] = (\([^)]*\)|[^\s(]+)\s+\(([^\n]*)", tt):
            t_, genre, idh, val = int(m.group(1), 16), m.group(2), m.group(3).lower(), m.group(4).strip()
            if idh not in ACTIFS or val.startswith("aucune"): continue
            if "probable" in m.group(5) and os.environ.get("MAX_TABLES_PROBABLES", "0") != "1": continue
            v = [int(x) for x in val.strip("()").split(",")]
            if genre.startswith("octet") or genre.startswith("ID ->"): b_ = bytes([v[0] & 0xFF])
            elif genre.startswith("mot"): b_ = struct.pack("<h", v[0])
            else: b_ = struct.pack("<hh", *v)
            rangs = (0,)
            for r in rangs: pose(t_, int(idh, 16), b_, rang=r)
            nb += 1
        # Ingrid : « FROM: ? » sur PSP (aucune origine) -> position de Ryu en attendant le relevé PPSSPP (R8-bis)
        if "2e" in ACTIFS: pose(0x616B30, 0x2E, struct.pack("<hh", 373, 910)); nb += 1
        log("tables par id (R8 / R9) : %d valeurs posées (demi-largeur, jauges, étoiles, positions, carte)" % nb)
    # (2b22, R6) parcours de l'Arcade (0x978D1C : 16 rangées de 10 id, index 4 = adversaire fixe, 8 = rival, 9 = boss) :
    # rangée 0 = tirage relevé sur PSP (persos MAX adversaires remplacés : le CPU ne les joue pas), rangées 1-15 = celles
    # de Ryu avec les places fixes du perso MAX ; combat secret 0x61B680 (Eagle : Balrog $15 ; autres : aucun)
    fp = MC.CV + "arcade/parcours_max.json"
    if os.path.exists(fp):
        PJ = json.load(open(fp)); RY = [ORIG[0x978D1C - RB + struct.unpack_from("<H", ORIG, 0x978D1C - RB)[0] + 10 * k:][:10] for k in range(16)]
        MAXIDS = {0x26, 0x27, 0x28, 0x29, 0x2D, 0x2E}
        FIXE_MAKI = int(os.environ.get("MAX_MAKI_RANG5", "0d"), 16)     # (R11) rang 5 de Maki = Sakura
        for cle, d in PJ.items():
            p = cle.split("$")[1].lower()
            if p not in ACTIFS: continue
            r5 = int(d["rang5"].split()[0], 16) if p != "27" else FIXE_MAKI
            r9 = int(d["rang9"].split()[0], 16)
            PSP2UP = {0x28: 0x2D, 0x29: 0x2E}          # id PSP -> id Upper (Yun, Ingrid)
            rel = [PSP2UP.get(int(x, 16), int(x, 16)) for x in d["releve_psp"] if int(x, 16) != 0x15 or p != "26"][:10]
            def rangee(base):
                r = list(base)
                for k_, v_ in ((4, r5), (8, r9), (9, 0x0A)):
                    if v_ in r and r.index(v_) != k_: r[r.index(v_)] = r[k_]
                    r[k_] = v_
                # (décision de l'utilisateur, 2b23) les persos MAX peuvent être des ADVERSAIRES CPU, comme sur PSP : tirage PSP
                # gardé tel quel (MAX_PARCOURS_NATIFS=1 : les remplacer par des natifs)
                # 2b23 : le plantage du CPU MAX ($ED48 -> instruction illégale, A0 écrasé par le rappel 74C038) est corrigé
                # dans l'enveloppe MAXW_xx_74c038 (prepare_max, MAX_IA_A0) -> tirage PSP gardé PAR DÉFAUT ; IA = scripts
                # natifs (pas encore de données IA MAX, Q13)
                if os.environ.get("MAX_PARCOURS_NATIFS", "0") == "1":
                    libres = [x for x in RY[0] if x not in r and x not in MAXIDS]
                    for k_ in range(10):
                        if r[k_] in MAXIDS: r[k_] = libres.pop(0)
                assert len(set(r)) == 10 and r[9] == 0x0A, "parcours %s : %s" % (p, r)
                return bytes(r)
            bloc = rangee(rel) + b"".join(rangee(RY[k]) for k in range(1, 16))
            # (essai, 2b23) MAX_PARCOURS_ADV1="2d:26,27:2e" : 1er adversaire imposé (banc du CPU MAX : Eagle, Ingrid)
            A1 = dict(x.split(":") for x in os.environ.get("MAX_PARCOURS_ADV1", "").split(",") if ":" in x)
            if p in A1:
                v_ = int(A1[p], 16)
                if v_ in rel: rel.remove(v_)
                rel = [v_] + rel[:9]
            if os.environ.get("MAX_PARCOURS_ESSAI") == "1": bloc = rangee(rel) * 16   # (essai) tirage PSP dans les 16 rangées
            AG.bloc_rel16(0x978D1C, int(p, 16), bloc)
            pose(0x61B680, int(p, 16), bytes([{"26": 0x15, "2d": 0x1E}.get(p, 0xFF)]))   # (R11) Eagle Balrog, Yun Juli + Juni
            for r_ in (0, 1): pose(0x61B6D0, int(p, 16), bytes([0x0A]), rang=r_)        # (R11) décor imposé $0A (combats 8 / 9)
        log("parcours Arcade (R6) : %s ; combat secret d'Eagle = Balrog" % ", ".join(PERSOS[p]["nom"] for p in ACTIFS))
    # (2b22, audit 97AF50) noms ASCII de l'écran RESULT du VERSUS (2 rangées : nom aligné à droite / à gauche) :
    # format natif « x, $20 + 4·ID, $1E, 10 caractères, $7F » (Ryu : 03 20 1E « ······RYU » 7F / 23 20 1E « RYU······ » 7F)
    for p in ACTIFS:
        i = int(p, 16); nm = PERSOS[p]["nom"].upper()[:10]; c_ = (0x20 + 4 * i) & 0xFF
        AG.bloc_rel16(0x97AF50, i, bytes([0x03, c_, 0x1E]) + (nm[:9].rjust(9) + " ").encode() + b"\x7f")   # comme « ······RYU· »
        AG.bloc_rel16(0x97AF50, 48 + i, bytes([0x23, c_, 0x1E]) + nm.ljust(10).encode() + b"\x7f")
    log("RESULT du VERSUS : noms %s (0x97AF50, 2 rangées)" % ", ".join(PERSOS[p]["nom"].upper() for p in ACTIFS))
    portraits(buf, data, end, pose)
    hud_apercu(pose)
    # grille de sélection : Eagle (0,2), Maki (0,4), Yun (6,4), Ingrid (6,2) ; les « ? » restantes renumérotées au-delà
    # du seuil ($30), mêmes drapeaux
    g = o(T_GRILLE)
    attendu = {2: 0xA6, 4: 0x67, 6 * 8 + 2: 0x69, 6 * 8 + 4: 0xA8}
    assert all(data[g + k] == v for k, v in attendu.items()), "grille de sélection inattendue"
    case = {"26": 2, "27": 4, "2d": 6 * 8 + 4, "2e": 6 * 8 + 2}
    for p, k in case.items():
        v = attendu[k]
        data[g + k] = int(p, 16) if p in ACTIFS else (v & 0xC0) | (SEUIL + (v & 0x3F) - 0x26)
        if p in ACTIFS:                                   # curseur : (colonne, rangée) de l'ID (table de 48 déjà)
            c = o(T_CURSEUR) + 2 * int(p, 16)
            if int(p, 16) >= 40: data[c:c + 2] = bytes([k % 8, k // 8])
            assert data[c:c + 2] == bytes([k % 8, k // 8]), "curseur de $%s inattendu" % p
    log("grille : %s" % " ".join("%02x" % data[g + k] for k in sorted(attendu)))
    citations(data, end)
    prologue()
    fins(data, end, pose)
    projections()

# ------------------------------------------------------------------------------------------------- HUD, aperçu, jauges
MUSIQUE = {"26": 0x11, "27": 0x10, "2d": 0x1A, "2e": 0x12}   # thèmes QSound d'Upper (sans flux) : Eagle = Birdie,
                                     # Maki = Guy, Yun = Gen, Ingrid = Rose (choix provisoire ; Upper : [$26] $26, [$27] $35
                                     # (thème à flux), [$2D/$2E] hors de la table de 45 -> $00)
JAUGES = {"26": (40, 72), "27": (40, 68), "2d": (40, 64), "2e": (40, 68)}   # (garde $2CC, seuil d'étourdissement $24D) :
                                     # session MAX (tables PSP = Upper 0x74C680 / 0x74C6A8, ordre brut du fichier)
def hud_apercu(pose):
    """noms et visages de la barre de vie, petit sprite d'aperçu de la sélection, jauges (outils/hud_apercu_max.py)"""
    HP = json.load(open(os.path.join(DIR, "max_plus.json")))
    for p in ACTIFS:
        i = int(p, 16); N = HP["noms"][p]; V = HP["visages"][p]
        for r in (0, 1):                                  # JP, US : même nom
            pose(0x95C700, i, struct.pack("<H", N["code"]), rang=r)
            pose(0x95C7A0, i, struct.pack("<h", N["x_J1"]), rang=r)
            pose(0x95C840, i, struct.pack("<h", N["x_J2"]), rang=r)
        for t, jx, x in ((0x95C8E0, "J1", 0), (0x95CA30, "J2", None), (0x95CB80, "J1", -16), (0x95CCD0, "J2", 16)):
            v = V[jx]; at = ((v["h"] - 1) << 12) | ((v["w"] - 1) << 8) | v["r"]
            if x is None: x = 384 - 16 * v["w"]
            elif jx == "J2": x = 384 - 16 * v["w"] + x          # (2b22, audit) 4e variante : J2 décalé de +16
            pose(t, i, struct.pack("<HHhh", v["code"], at, x, 16))
        pose(0x97CA90, i, struct.pack("<I", S("APS_%s" % p)))
        g, s_ = JAUGES[p]
        pose(0x74C680, i, bytes([g])); pose(0x74C6A8, i, bytes([s_]))
    log("HUD : noms et visages de la barre de vie, aperçu de sélection, jauges (garde / étourdissement) : %s" %
        ", ".join(PERSOS[p]["nom"] for p in ACTIFS))
    # tuiles : fichier graphique propre (HSFA_GFX ...@2E45000) ; banque commune prolongée pour l'aperçu
    import shutil, array
    W_ = os.environ.get("MAX_W")
    shutil.copy(os.path.join(DIR, "max_plus_gfx.bin"), os.path.join(W_, "max_plus_gfx.bin"))
    f = os.path.join(W_, "banques_hx", "f351.bin")
    t = array.array("I", open(f, "rb").read())
    assert len(t) <= 0x7000, "banque commune : %d entrées" % len(t)
    t = t + array.array("I", [0xFFFFFFFF] * (0x7000 - len(t)))
    for p in ACTIFS:
        A = HP["apercu"][p]
        assert len(t) <= A["local"]
        t += array.array("I", [0xFFFFFFFF] * (A["local"] - len(t)))   # codes locaux alignés sur 16
        t += array.array("I", range(A["g"], A["g"] + A["n"]))
    open(f, "wb").write(t.tobytes())
    log("aperçu : banque commune f351 prolongée à %d entrées (codes locaux $7000+ -> tuiles $%x+)" % (len(t), HP["apercu"][ACTIFS[0]]["g"]))

# ------------------------------------------------------------------------------------------------- fins (palier 3)
# tables de fin d'Upper indexées par $1C9(A5) (n° de fin = ID) : acteurs (JP/US), palettes ($8008), plans ($800C),
# script ($8034), paramètres (3 mots -> $802A/$802E/$8030)
T_FIN = {"acteurs": (0x60B220, 0x60B2D0), "palettes": (0x60B5A0, 0x60B650), "plans": (0x60B700, 0x60B7B0),
         "script": (0x60B860, 0x60B910)}
T_FIN_PARAMS = 0x60B9C0
FIN_MODELE = {"26": 0x10, "27": 0x07, "2d": 0x06, "2e": 0x10}   # fin d'arcade servant de modèle (session MAX, 17/10)
# (18/10 nuit, session MAX) table des positions de projection 7495b8 ([attaquant] -> rel16 [victime]) : lignes natives
# $00-$25 -> PROJ_NAT_xx (48 colonnes, colonnes natives identiques), lignes MAX -> PROJ_POS_xx
def projections():
    import agrandit_max as AG_
    charge(); n = 0
    for i in range(0x26 if os.environ.get("MAX_PROJ_NAT", "1") == "1" else 0):   # (2b22) MAX_PROJ_NAT=0 : lignes natives d'origine
        if "PROJ_NAT_%02X" % i in SYM: AG_.ajout(0x7495B8, i, struct.pack("<I", S("PROJ_NAT_%02X" % i))); n += 1
    for p in ACTIFS:
        lab = "PROJ_POS_%s" % p.upper()
        if lab in SYM: AG_.ajout(0x7495B8, int(p, 16), struct.pack("<I", S(lab))); n += 1
    log("projections : %d lignes de 7495b8 -> PROJ_NAT_xx / PROJ_POS_xx (session MAX)" % n)

def fins(data, end, pose):
    o = lambda a: a - RB - end
    essai = os.environ.get("MAX_FIN_ESSAI", "")
    for p in ACTIFS:
        if p not in FIN_MODELE: continue
        i = int(p, 16); m = FIN_MODELE[p]
        if essai == "modele":                            # fin du modèle telle quelle (contrôle du mécanisme)
            for k, (tj, tu) in T_FIN.items():
                for t in (tj, tu): pose(t, i, bytes(data[o(t + 4 * m):o(t + 4 * m) + 4]))
            pose(T_FIN_PARAMS, i, bytes(data[o(T_FIN_PARAMS + 6 * m):o(T_FIN_PARAMS + 6 * m) + 6]))
            log("%s ($%s) : fin = celle du modèle $%02X (essai)" % (PERSOS[p]["nom"], p, m))
    if os.environ.get("MAX_FINS") != "1": return
    # PALIER 3 : fins MAX (session MAX : script, acteurs, textes ; plans / palettes / paramètres = ceux du modèle)
    info = json.load(open(os.path.join(DIR, "fins_max.json")))
    for p in ACTIFS:
        I = info.get(p)
        if not I or not I["script"] or p not in FIN_MODELE: continue
        i = int(p, 16); m = FIN_MODELE[p]
        for k in ("palettes", "plans"):
            for t in T_FIN[k]: pose(t, i, bytes(data[o(t + 4 * m):o(t + 4 * m) + 4]))
        # (palier 4, session MAX 18/10 nuit) plans VIDES pour Maki seule (scroll2 PSP vide, images toutes en FD) ; Eagle /
        # Ingrid (Zangief) et Yun (modèle $06) gardent les plans du modèle (leurs illustrations y sont)
        if "FIN_PLANS_VIDES" in SYM and p in os.environ.get("MAX_PLANS_VIDES", "27").split(","):
            for t in T_FIN["plans"]: pose(t, i, struct.pack("<I", S("FIN_PLANS_VIDES")))
        if I.get("jeu_neuf"):                            # jeu de palettes neuf (invités) : liste propre + source n° 13
            for t in T_FIN["palettes"]: pose(t, i, struct.pack("<I", S("FIN%s_PAL_LISTE" % p)))
            v13 = struct.unpack_from("<I", data, o(0x60B594))[0]
            assert v13 in (0, S("FINMAX_PAL_SRC")), "source de palettes n° 13 occupée"
            struct.pack_into("<I", data, o(0x60B594), S("FINMAX_PAL_SRC"))      # source partagée des jeux neufs
        pose(T_FIN_PARAMS, i, bytes(data[o(T_FIN_PARAMS + 6 * m):o(T_FIN_PARAMS + 6 * m) + 6]))
        for t in T_FIN["script"]: pose(t, i, struct.pack("<I", S("FIN%s_SCRIPT" % p)))
        if os.environ.get("MAX_FIN_SCRIPT_MODELE") == "1":      # (bissection) script, acteurs, palettes du MODÈLE
            for k in ("script", "acteurs", "palettes"):
                for t in T_FIN[k]: pose(t, i, bytes(data[o(t + 4 * m):o(t + 4 * m) + 4]))
            log("%s ($%s) : BISSECTION : script / acteurs / palettes du modèle $%02X (fichiers du palier 4 gardés)" % (PERSOS[p]["nom"], p, m))
            continue
        if I["acteurs"]:
            for t in T_FIN["acteurs"]: pose(t, i, struct.pack("<I", S("FIN%s_ACTEURS" % p)))
        for k, tx in enumerate(I["textes"]): AG.bloc_rel16(T_TEXTES_FIN, I["texte0"] + k, bytes.fromhex(tx))
        log("%s ($%s) : fin MAX (script, %s, %d textes en %d-%d ; plans / palettes / paramètres du modèle $%02X)%s" % (
            PERSOS[p]["nom"], p, "acteurs MAX" if I["acteurs"] else "acteurs du modèle ($%02X)" % m, len(I["textes"]),
            I["texte0"], I["texte0"] + len(I["textes"]) - 1, m,
            (" ; décors PROVISOIRES : " + ", ".join(I.get("nd_provisoires", []))) if I.get("nd_provisoires") else ""))
    # (palier 4) décors MAX ajoutés à la table de classe $48 (0x960180) : pas de 8 o recopiés depuis le bloc externe
    # assemblé (decor_fin_<perso>.s, disposition image) jusqu'au pas qui boucle (bit 7, reprise) ou s'arrête (bit 6)
    nd = {}
    for p in ACTIFS:
        nd.update((info.get(p) or {}).get("nd_81522", {}))
    if nd:
        import re as _re, glob as _gl
        sy, bl = {}, {}
        for lst in _gl.glob(os.path.join(DIR, "blocs", "bloc_*.lst")):
            org = int(_re.search(r"bloc_([0-9a-f]{6})", lst).group(1), 16)
            dans = False
            for l in open(lst, errors="replace"):
                if l.startswith("Symbols by name"): dans = True; continue
                if l.startswith("Symbols by value"): break
                m = _re.match(r"^(P8_\w+)\s+A:([0-9A-Fa-f]{8})", l) if dans else None
                if m: sy[m.group(1)] = (int(m.group(2), 16), org)
            bl[org] = open(os.path.join(DIR, "blocs", "ext_%06x.bin" % org), "rb").read()
        for n, (k, lab) in sorted(nd.items(), key=lambda x: x[1][0]):
            a, org = sy[lab]; b = bl[org]; o = a - org; pas = bytearray()
            while True:
                fl = b[o]                                  # image : octet 0 = drapeaux (octet 1 arcade)
                t = 12 if fl & 0x80 else 8
                pas += b[o:o + t]; o += t
                if fl & 0xC0: break
                assert len(pas) < 0x400, "décor %s : pas sans fin" % lab
            ps2 = bytes(x for i in range(0, len(pas), 2) for x in (pas[i + 1], pas[i]))
            AG.bloc_rel16(0x960180, k, ps2)
            log("décor de fin %s = entrée %d de 0x960180 (%s, %d pas)" % (n, k, lab, len(pas) // 8))
    # banques d'animation des acteurs (octet +$1F = n° de banque ; numérotation MAX $26-$29) -> FIN_ANIM_xx
    for p in ACTIFS:
        suf = PERSOS[p]["suffixe"]
        if "FIN_ANIM_%s" % suf in SYM: pose(T_BANQUES_ACTEURS, int(suf, 16), struct.pack("<I", S("FIN_ANIM_%s" % suf)))
    log("acteurs de fin : banques %s -> FIN_ANIM_xx (T_619b50)" % ", ".join("$%s" % PERSOS[p]["suffixe"] for p in ACTIFS))
# aiguillages EN LIGNE des acteurs de fin par sous-type (« MOVE.B $2(A6),D0 ; ANDI.W #$7F,D0 ; ADD.W D0,D0 ;
# MOVE.W T(PC,D0.W),D1 ; JMP/JSR T(PC,D1.W) ») : va de la lecture de la table -> (classe, n entrées)
AIG_ACTEURS = {0x1EFFA8: (0x4B, 82), 0x1E5988: (0x49, 43), 0x211B7C: (0x4F, 25), 0x21AFAC: (0x4F, 25), 0x21B8E0: (0x4F, 25),
               # classe $4F, état 2 (image $4C522) : table de 29 dont les entrées 25-27 sont nulles (inutilisées) -> le
               # sous-type MAX $19 (25) y passe aussi (sinon saut dans la table : ILLEGAL, fins de Maki / Yun)
               0x213980: (0x4F, 25, 29)}
# classe -> {sous-type MAX : routine} (session MAX : en-tête d'acteurs_fins_max.s) ; les 3 tables de 25 (une est la classe
# $4F) reçoivent toutes le sous-type $19 : jamais atteint par les autres classes (25 entrées)
ACTEURS_MAX = {0x4B: {0x52: "acteur_1d3844", 0x53: "acteur_1d3bb8", 0x54: "acteur_1d3dfc", 0x55: "acteur_1d4008",
                      0x56: "acteur_1d4370", 0x57: "acteur_1d48ac"},
               0x4F: {0x19: "acteur_1d6588"},
               0x49: {0x2D: "acteur_1c9704", 0x2E: "acteur_1c970c"}}     # (18/10 soir, MAX) $2B/$2C : bouche-trous, plus inscrits
# aiguillages « secondaires » (JSR suivi d'autre code) : les sous-types MAX y prennent l'entrée 0 (commune) au lieu
# d'une entrée hors table / nulle : va -> (sous-types)
# classe $49, pré-traitement (image $4618C, T_619160 à 45 entrées : 41-43 nulles, 44 = sous-type d'Upper !)
AIG_ENTREE0 = {0x1E5338: (0x2D, 0x2E)}            # (MAX) seuls $2D (Maki) et $2E (Yun) servent ; entrées 45 / 46
def talons_entree0(img, its, a):
    par_va = {}
    for it in its: par_va.setdefault(it.va, []).append(it)
    for va, sts in sorted(AIG_ENTREE0.items()):
        ok = [it for it in par_va.get(va, []) if struct.unpack_from(">H", img, it.off)[0] == 0x323B]
        assert len(ok) == 1, "aiguillage secondaire va %x introuvable" % va
        k = ok[0].off
        assert struct.unpack_from(">HHHHH", img, k - 10) == (0x102E, 0x0002, 0x0240, 0x007F, 0xD040)
        ext = struct.unpack_from(">H", img, k + 2)[0]; d8 = ext & 0xFF; d8 -= 0x100 if d8 & 0x80 else 0
        tab = k + 2 + d8
        w = [0x102E, 0x0002, 0x0240, 0x007F, 0xD040]
        for st in sts: w += [0x0C40, 2 * st, 0x6602, 0x7000]          # CMPI.W #2st,D0 ; BNE.S +2 ; MOVEQ #0,D0
        w += [0x2F08, 0x41F9, tab >> 16, tab & 0xFFFF, 0x3230, 0x0000, 0x205F, 0x4E75]
        assert not any(img[a:a + 2 * len(w)])
        struct.pack_into(">%dH" % len(w), img, a, *w)
        struct.pack_into(">HHHHHHH", img, k - 10, 0x4EB9, a >> 16, a & 0xFFFF, 0x4E71, 0x4E71, 0x4E71, 0x4E71)
        log("acteurs de fin : aiguillage secondaire $%x : sous-types %s -> entrée 0 (talon $%x)" % (k - 10, ", ".join("$%02X" % x for x in sts), a))
        a = (a + 2 * len(w) + 3) & ~3
    return a

def talons_acteurs(img, its, a0):
    """sous-types MAX des acteurs de fin : les 14 octets avant « JMP/JSR T(PC,D1.W) » -> JSR talon ; NOP x4 ; talon :
    sous-type < n -> D1 = T[D0] et retour (le JMP/JSR d'origine suit) ; sinon saut direct à la routine MAX (le JSR des
    sites $4F est suivi d'un RTS : sauter à la routine revient au même)"""
    par_va = {}
    for it in its: par_va.setdefault(it.va, []).append(it)
    a = a0; faits = []
    for va, spec in sorted(AIG_ACTEURS.items()):
        cl, n = spec[:2]; ntab = spec[2] if len(spec) > 2 else n
        ok = [it for it in par_va.get(va, []) if struct.unpack_from(">H", img, it.off)[0] == 0x323B]
        assert len(ok) == 1, "aiguillage d'acteurs va %x introuvable" % va
        k = ok[0].off
        assert struct.unpack_from(">HHHHH", img, k - 10) == (0x102E, 0x0002, 0x0240, 0x007F, 0xD040), "aiguillage %x : octets" % va
        ext = struct.unpack_from(">H", img, k + 2)[0]; jop = struct.unpack_from(">H", img, k + 4)[0]
        assert ext & 0xFF00 == 0x0000 and jop in (0x4EFB, 0x4EBB), "aiguillage %x : forme inattendue" % va
        d8 = ext & 0xFF; d8 -= 0x100 if d8 & 0x80 else 0
        tab = k + 2 + d8
        mx = ACTEURS_MAX[cl]; s0 = n; s1 = max(mx) + 1
        assert min(mx) >= n
        tmax = a; a += 4 * (s1 - s0)
        w = [0x102E, 0x0002, 0x0240, 0x007F, 0xD040,            # MOVE.B $2(A6),D0 ; ANDI.W #$7F,D0 ; ADD.W D0,D0
             0x0C40, 2 * s0, 0x6410,                            # CMPI.W #2n,D0 ; BCC.S max
             0x2F08, 0x41F9, tab >> 16, tab & 0xFFFF,           # MOVE.L A0,-(SP) ; LEA T,A0
             0x3230, 0x0000, 0x205F, 0x4E75,                    # MOVE.W 0(A0,D0.W),D1 ; MOVEA.L (SP)+,A0 ; RTS
             0x0C40, 2 * s1, 0x6512, 0x7000 if ntab <= s1 else 0x4E71,   # max : CMPI.W #2(s1),D0 ; BCS.S m2 ; MOVEQ #0,D0 (ou NOP
             0x2F08, 0x41F9, tab >> 16, tab & 0xFFFF,           #   si la table d'origine va au-delà) ; hors table MAX : origine
             0x3230, 0x0000, 0x205F, 0x4E75,
             0x2F08, 0x41F9, tmax >> 16, tmax & 0xFFFF,         # m2 : MOVE.L A0,-(SP) ; LEA TMAX,A0
             0x3200, 0x0441, 2 * s0, 0xD241,                    # MOVE.W D0,D1 ; SUBI.W #2n,D1 ; ADD.W D1,D1
             0x2F70, 0x1000, 0x0004,                            # MOVE.L 0(A0,D1.W),4(SP) (retour -> routine MAX)
             0x205F, 0x4E75]                                    # MOVEA.L (SP)+,A0 ; RTS
        st_ = a; a += 2 * len(w)
        assert not any(img[tmax:a]), "talons d'acteurs : zone non libre en $%x" % tmax
        for st in range(s0, s1): struct.pack_into(">I", img, tmax + 4 * (st - s0), S(mx[st]) if st in mx else 0)
        struct.pack_into(">%dH" % len(w), img, st_, *w)
        struct.pack_into(">HHHHHHH", img, k - 10, 0x4EB9, st_ >> 16, st_ & 0xFFFF, 0x4E71, 0x4E71, 0x4E71, 0x4E71)
        faits.append("$%02X/%d en $%x (talon $%x)" % (cl, n, k - 10, st_))
        a = (a + 3) & ~3
    log("acteurs de fin : sous-types MAX branchés : " + ", ".join(faits))
    return a

# CONTRES (octet $0D du pas, image $C) : pour D0 >= 4, Upper fait « JSR $23ACE » -> va 0x226880 = image $40D4 :
# « SUBQ.W #4,D0 ; LSL.W #1,D0 ; MOVE.W T(PC,D0.W),D1 ; JMP T(PC,D1.W) » (6 entrées, 4-9). Talon : 4-9 -> table
# d'origine ; 11-14 -> CONTRE_MAX_11..14 (session MAX, contres_max.s) ; 10 et >= 15 -> coup normal ($23A3C)
VA_CONTRES = 0x36898
def talon_contres(img, its, a):
    ok = [it for it in its if it.va == VA_CONTRES and struct.unpack_from(">H", img, it.off)[0] == 0x5940]
    assert len(ok) == 1, "aiguillage des contres (va %x) introuvable" % VA_CONTRES
    k = ok[0].off
    w0 = struct.unpack_from(">HHHHH", img, k)
    assert w0[1] == 0xE348 and w0[2] == 0x323B and w0[3] & 0xFF00 == 0 and w0[4] == 0x4EFB, "contres : octets inattendus"
    d8 = w0[3] & 0xFF; d8 -= 0x100 if d8 & 0x80 else 0
    tab = k + 4 + 2 + d8
    cn = S("COUP_NORMAL")
    tmax = a; a += 16
    st_ = a
    w = [0x0C40, 0x000A, 0x6414, 0x5940, 0xE348, 0x2F08, 0x41F9, tab >> 16, tab & 0xFFFF, 0x3230, 0x0000, 0x205F, 0x4E75,
         0x0C40, 0x000B, 0x6520, 0x0C40, 0x000F, 0x641A,
         0x2F08, 0x41F9, tmax >> 16, tmax & 0xFFFF, 0x3200, 0x0441, 0x000B, 0xE549, 0x2F70, 0x1000, 0x0004, 0x205F, 0x4E75,
         0x2EBC, cn >> 16, cn & 0xFFFF, 0x4E75]
    a += 2 * len(w)
    assert not any(img[tmax:a]), "contres : zone non libre"
    for n in range(11, 15): struct.pack_into(">I", img, tmax + 4 * (n - 11), S("CONTRE_MAX_%d" % n))
    struct.pack_into(">%dH" % len(w), img, st_, *w)
    struct.pack_into(">HHHH", img, k, 0x4EB9, st_ >> 16, st_ & 0xFFFF, 0x4E71)
    log("contres : aiguillage $%x (table $%x) -> talon $%x : 11-14 -> CONTRE_MAX_11..14, 10 / >= 15 -> coup normal $%x" % (k, tab, st_, cn))
    return a

# APERÇU DE SÉLECTION d'Ingrid en UNE palette (session MAX, 17/10 : converti/pl29/apercu/palettes_module.bin = 6 × 1) :
# le chargeur d'Upper (image $37FC2-$38012, va 0x1916cc) prend la palette 0 du jeu de COMBAT (T_PAL[ID] + 5 × couleur)
# -> talon : pour un ID dont l'aperçu a ses propres palettes, A0 = bloc de 6 × 5 palettes (palette de la couleur v en 5v)
VA_APERCU_PAL = 0x1916CC
def talon_apercu_pal(img, its, a):
    ids = {}
    for p in ACTIFS:
        f = MC.CV + "%s/apercu/palettes_module.bin" % PERSOS[p]["pl"]
        if os.path.exists(f) and os.path.getsize(f) == 6 * 32: ids[int(p, 16)] = open(f, "rb").read()
    if not ids: return a
    ok = [it for it in its if it.va == VA_APERCU_PAL and struct.unpack_from(">H", img, it.off)[0] == 0x41F9]
    assert len(ok) == 1, "chargeur de palette d'aperçu introuvable"
    k = ok[0].off
    w0 = struct.unpack_from(">HIHHH", img, k)
    assert w0[2:] == (0xD270, 0x0000, 0xD0C1), "chargeur d'aperçu : octets inattendus"
    t_pal = w0[1]
    blocs = {}
    for i, pal in sorted(ids.items()):
        blocs[i] = a
        for v in range(6):
            ws = struct.unpack_from("<16H", pal, 32 * v)
            struct.pack_into(">16H", img, a + 160 * v, *[x & 0x0FFF for x in ws])
        a += 960
    st_ = a; w = []
    for i, b in sorted(blocs.items()):
        w += [0x0C40, 2 * i, 0x660A, 0x41F9, b >> 16, b & 0xFFFF, 0xD0C1, 0x4E75]   # CMPI.W #2i,D0 ; BNE.S ; LEA ; ADDA.W D1,A0 ; RTS
    w += [0x41F9, t_pal >> 16, t_pal & 0xFFFF, 0xD270, 0x0000, 0xD0C1, 0x4E75]
    struct.pack_into(">%dH" % len(w), img, st_, *w); a = st_ + 2 * len(w)
    struct.pack_into(">HHHHHH", img, k, 0x4EB9, st_ >> 16, st_ & 0xFFFF, 0x4E71, 0x4E71, 0x4E71)
    log("aperçu : palettes propres (%s) -> chargeur $%x, talon $%x" % (", ".join("$%02X" % i for i in blocs), k, st_))
    return a

T_TEXTES_FIN = 0x68DC72         # textes de fin (rel16, 789 entrées) : textes MAX à la suite (agrandit_max.REL16_N)
T_BANQUES_ACTEURS = 0x619B50    # banques d'animation des acteurs (40 longs, LEA en $4B51A) : agrandie à 48

def fins_fichiers(afin):
    """(palier 3) table du talon du chargeur de FIN (index = octet bas de D8) : 48 entrées (40-47 = entrée 0) ; une fin
    MAX bâtie sur un modèle charge le fichier d'animation de fin (emplacement 4) du modèle"""
    a = list(afin) + [afin[0]] * (48 - len(afin))
    for p in ACTIFS:
        if p in FIN_MODELE: a[int(p, 16)] = FIN_FICHIERS.get(p, afin[FIN_MODELE[p]])
    log("fins : table du chargeur de fin à %d entrées (%s)" % (len(a), ", ".join("$%s <- fichier $%02X" % (p, FIN_MODELE[p]) for p in ACTIFS if p in FIN_MODELE)))
    return a

# ------------------------------------------------------------------------------------------------- citations
T_CITATIONS = 0x67E2A0          # 40 décalages u16 relatifs à la table -> bloc par perso (8 citations) ; session MAX :
                                # converti/plXX/citations_upper.bin = bloc complet, ordre du fichier ro5 (PS2)
T_PROLOGUE_LISTES = 0x960090   # 40 décalages s16 relatifs à la table -> liste de n° de pages (dernier | $80) ; agrandie
def prologue():
    """listes de pages des persos MAX (PROLOGUE_MAX_xx, n° dans la réserve PROLOGUE_MAX ; session MAX)"""
    f = MC.CV + "prologue_max.s"
    if not os.path.exists(f): return
    import re as _re
    t = open(f).read()
    for p in ACTIFS:
        m = _re.search(r"PROLOGUE_MAX_%s:[^\n]*\n\s*dc\.b\s+([^\n;]+)" % PERSOS[p]["suffixe"], t)
        b = bytes(int(x.strip().lstrip("$"), 16) for x in m.group(1).split(","))
        assert b[-1] & 0x80 and all(not (x & 0x80) for x in b[:-1])
        # (2b22) la liste se termine par un octet NUL (lecteur image $56F9C : TST.B ; BNE) ; $80 = fin de page. Sans lui, une
        # liste de longueur paire (Yun, Ingrid) n'avait pas de bourrage nul : Yun enchaînait sur les lignes d'Ingrid
        AG.bloc_rel16(T_PROLOGUE_LISTES, int(p, 16), b + b"\x00")
    log("bio : listes de pages du prologue (réserve PROLOGUE_MAX) : %s" % ", ".join(PERSOS[p]["nom"] for p in ACTIFS))

# réserve des pages : « LEA 0x61C0C0,A1 ; MOVE.W $92(A5),D1 ; … » (image $56FA0, va 0x25d22c) : talon -> pour un ID MAX
# ($147(A5)), A1 = petite table dont chaque long vise PROLOGUE_MAX
VA_PROLOGUE = 0x25D22C
def talon_prologue(img, its, a):
    if "PROLOGUE_MAX" not in SYM: return a
    ok = [it for it in its if it.va == VA_PROLOGUE and struct.unpack_from(">H", img, it.off)[0] == 0x43F9]
    assert len(ok) == 1, "réserve du prologue introuvable"
    k = ok[0].off; t61 = struct.unpack_from(">I", img, k + 2)[0]
    pm = S("PROLOGUE_MAX"); tab = a
    assert not any(img[tab:tab + 0x60]), "talon du prologue : zone non libre"
    for j in range(8): struct.pack_into(">HH", img, tab + 4 * j, pm & 0xFFFF, pm >> 16)    # longs en moitiés échangées
    st_ = tab + 32; w = [0x7200, 0x122D, 0x0147]                          # MOVEQ #0,D1 ; MOVE.B $147(A5),D1
    ids = [int(p, 16) for p in ACTIFS]
    for n, i in enumerate(ids):
        w += [0x0C01, i, 0x6700 | (2 * (3 * (len(ids) - n - 1) + 4))]       # CMPI.B #i,D1 ; BEQ.S max
    w += [0x43F9, t61 >> 16, t61 & 0xFFFF, 0x4E75, 0x43F9, tab >> 16, tab & 0xFFFF, 0x4E75]
    struct.pack_into(">%dH" % len(w), img, st_, *w)
    struct.pack_into(">HHH", img, k, 0x4EB9, st_ >> 16, st_ & 0xFFFF)
    log("bio : réserve PROLOGUE_MAX pour %s (talon $%x)" % (", ".join("$%02X" % i for i in ids), st_))
    return st_ + 2 * len(w)

_SYM_BLOCS = None
def sym_blocs():
    """symboles des blocs par perso assemblés à part (prep/blocs/bloc_*.lst : frames, décors des fins FDxx_n…)"""
    global _SYM_BLOCS
    if _SYM_BLOCS is None:
        _SYM_BLOCS = {}
        import glob as _g
        for f in _g.glob(os.path.join(DIR, "blocs", "bloc_*.lst")):
            for l in open(f, errors="replace"):
                m = re.match(r"^(\w+)\s+A:([0-9A-F]{8})\s*$", l)
                if m: _SYM_BLOCS.setdefault(m.group(1), int(m.group(2), 16))
    return _SYM_BLOCS

def pose_generique(pose):
    """(2b22) pose finale du générique (acteur $4E/00, liste $E/$F de l'arcade $301FA2 = Upper 0x674C00 + 3012, rang =
    octet +3 de l'acteur = ID ; $3D pour la 2e de Yun) : pas de 8 o MAXPOSE_xx de la session MAX (pose_generique_max.s,
    ordre logique = ordre PS2 des données) ; frame FDxx_n = décor de fin (symbole des blocs par perso)"""
    f = MC.CV + "pose_generique_max.s"
    if not os.path.exists(f): return
    t = open(f).read(); SB = sym_blocs(); n = 0
    for m in re.finditer(r"^MAXPOSE_([0-9A-F]{2}):[^\n]*\n\s+dc\.b\s+([^\n;]+)\n\s+dc\.l\s+(\w+)", t, re.M):
        rang = int(m.group(1), 16)
        b = bytes(int(x.strip().lstrip("$"), 16) for x in m.group(2).split(","))
        assert len(b) == 4 and m.group(3) in SB, "pose du générique %s : %s" % (m.group(1), m.group(3))
        pose(0x674C00 + 3012, rang, b + struct.pack("<I", SB[m.group(3)]), e=8); n += 1
    log("générique : %d poses finales MAX (0x674C00 + 3012, rangs %s)" % (n, ", ".join("$" + x for x in re.findall(r"^MAXPOSE_([0-9A-F]{2})", t, re.M))))

def citations(data, end):
    for p in ACTIFS:
        f = MC.CV + "%s/citations_upper.bin" % PERSOS[p]["pl"]
        b = open(f, "rb").read()
        assert struct.unpack_from("<H", b, 0)[0] == 18, "%s : bloc de citations inattendu" % f
        AG.bloc_rel16(T_CITATIONS, int(p, 16), b)
    log("citations de victoire : %s (table agrandie, blocs ajoutés)" % ", ".join(PERSOS[p]["nom"] for p in ACTIFS))

# ------------------------------------------------------------------------------------------------- portraits
# Mécanisme du §130-§131 (mame_test.py, MAX_PORTRAITS, un seul perso) refait pour PLUSIEURS persos : frames de type 8
# (code + $1C00 -> plan2 prolongé : index $A60C + k -> global $5C06C + k), palettes de portrait, poses de 0x484C00
# (fichier ; 66 poses x 40 ID) et table des palettes 0x53BDF0 redirigées ; palettes de SÉLECTION (rendu 0x56E9C,
# décalages 16 bits) : déviation du LEA vers un talon qui reconnaît chaque ID MAX (image()).
PORTRAIT_BASE, PORTRAIT_PAS = 0xD60000, 0x2000
SELPAL = {}
def portraits(buf, data, end, pose):
    import array
    W_ = os.environ.get("MAX_W")
    G0 = MC.G0; PB1 = MC.PB1
    pl2p = os.path.join(W_, "banques_hx", "plan2.bin")
    p2 = array.array('I', open(pl2p, "rb").read())
    # (2b11) hsfa_plans.bin déplacé (version étirée : MAX occupe les codes jusqu'à $627xx) : codes des plans d'Upper des
    # tables plan1 / plan2 (sprites de l'emplacement 1) décalés de PLANS_DELTA (copies fraîches de construit_max.sh)
    if MC.PLANS_DELTA and not os.path.exists(pl2p + ".decale"):
        a0, a1 = MC.PLANS_CODES
        for nm in ("plan1.bin", "plan2.bin"):
            fp = os.path.join(W_, "banques_hx", nm); t = array.array('I', open(fp, "rb").read())
            nb = 0
            for j in range(min(len(t), 0xA60C) if nm == "plan2.bin" else len(t)):
                if a0 <= t[j] < a1: t[j] += MC.PLANS_DELTA; nb += 1
            open(fp, "wb").write(t.tobytes()); log("plans : %s, %d codes décalés de $%x (hsfa_plans en $%x)" % (nm, nb, MC.PLANS_DELTA, MC.PLANS_ORG))
        open(pl2p + ".decale", "w").write("1")
        p2 = array.array('I', open(pl2p, "rb").read())
    if len(p2) <= PB1 or p2[PB1] != G0:                   # prolongement (une fois) : PB1 = même valeur que G0 mod 16
        p2 = p2[:min(PB1, 0xA60C)] + array.array('I', [0xFFFFFFFF] * max(0, PB1 - min(PB1, 0xA60C, len(p2)))) + array.array('I', range(G0, G0 + 0x2000))
        open(pl2p, "wb").write(p2.tobytes())
    offs = struct.unpack_from('<66H', buf, 0x484C00)
    pal0 = struct.unpack_from('<I', buf, 0x53BDF0)[0] - RB                    # bloc de palettes de portrait de Ryu
    for k, p in enumerate(ACTIFS):
        pl = PERSOS[p]["pl"]; i = int(p, 16); PB = PORTRAIT_BASE + PORTRAIT_PAS * k
        CV = MC.CV + "%s/" % pl
        pj = json.load(open(CV + "portraits.json"))
        hx = array.array('I', open(MC.FORK + "p%s_portraits_hx.bin" % pl[2:], "rb").read())
        loc = lambda L: PB1 + (int(hx[L]) - G0) - 0x1C00
        blk = bytearray(buf[pal0:pal0 + 0x600]); src = open(CV + "portraits_palettes.bin", "rb").read()
        var_ = pj.get("128x224", {}).get("variantes", {}); mp_ = var_.get("palette_du_fichier_vers_r")
        # R_DIRECT (Ingrid) : les attributs des portraits de sélection / HUD / VS visent r directement (palettes de
        # fichier 3-5 = variante 0) ; ceux du portrait de victoire (320x160) visent les palettes de fichier 0-2.
        # Bloc de base : emplacements 0..n-1 = palettes de fichier f (r), puis les palettes de victoire décalées de n.
        rdir = bool(mp_) and "direct" in var_.get("attributs", "")
        dec_ = 0
        if rdir:
            n_ = len(mp_); f0_ = min(int(f) for f in mp_); s2 = bytearray(len(src))
            for f_, r_ in mp_.items(): s2[32*r_:32*r_+32] = src[32*int(f_):32*int(f_)+32]
            for k_ in range(f0_): s2[32*(n_+k_):32*(n_+k_)+32] = src[32*k_:32*k_+32]
            src = bytes(s2); dec_ = n_
        blk[:len(src)] = src
        # (2b4, retour utilisateur) bloc de 48 palettes = 6 COULEURS × 8 (Upper : 0x72BDF0[ID] + 8 × couleur, comme Ryu) ;
        # session MAX : portraits_victoire_variantes.bin (winXX_e.pac entrée 4 : couleur v, palette r = k·v + r, k = 8
        # ou 4) et portraits_palettes_variantes.bin (sélection : 4v + r) -> chaque groupe reçoit SES couleurs
        vic_ = CV + "portraits_victoire_variantes.bin"; var2_ = CV + "portraits_palettes_variantes.bin"
        if os.path.exists(vic_) and os.path.exists(var2_) and mp_:
            vb_ = open(vic_, "rb").read(); sb_ = open(var2_, "rb").read(); kk = len(vb_) // 32 // 6
            assert kk in (4, 8) and len(vb_) == 32 * 6 * kk
            P_ = lambda d, n: d[32 * n:32 * n + 32]
            for v_ in range(6):
                g = 0x100 * v_
                if rdir:                                     # sélection r -> r ; victoire r -> n + r
                    for f_, r_ in mp_.items(): blk[g + 32 * r_:g + 32 * r_ + 32] = P_(sb_, 4 * v_ + r_)
                    for r_ in range(min(int(f) for f in mp_)): blk[g + 32 * (dec_ + r_):g + 32 * (dec_ + r_) + 32] = P_(vb_, kk * v_ + r_)
                else:                                        # victoire 0..k-1 -> 0..k-1, sauf les emplacements de sélection
                    for r_ in range(kk): blk[g + 32 * r_:g + 32 * r_ + 32] = P_(vb_, kk * v_ + r_)
                    for f_, r_ in mp_.items(): blk[g + 32 * int(f_):g + 32 * int(f_) + 32] = P_(sb_, 4 * v_ + r_)
        nred = 0; nbande = 0; yeux_ = []
        for fam, x in pj.items():
            a = PB + len(blk); objs = x["objs"]
            blk += struct.pack('<HHH', 8, x["T"], len(objs) - 1)
            d_ = dec_ if fam == "320x160" else 0
            for L, at, xx, yy in objs:
                if d_: assert (at & 0x1f) + d_ < 0x20; at += d_
                blk += struct.pack('<HHhh', loc(L) & 0xffff, at & 0xffff, xx, yy)
            for po in x["poses"]:
                t_ = po["table_0x484C00"]
                assert t_["id"] in (i, int(PERSOS[p]["suffixe"], 16)), "%s : poses pour l'ID %x" % (pl, t_["id"])   # MAX : n° d'avant ($28/$29)
                if offs[t_["pose"]] >= 0x1704:   # poses >= 32 : bande PARTAGÉE A[pose-32+ID] (non agrandie) : y écrire pour
                    nbande += 1                    # $26/$27 écrasait les poses 33-64 des ID 6-37 (relevé 17/10) -> jamais ;
                    yeux_.append((t_["pose"], a)); continue   # (18/10) table PROPRE (talon_yeux) : yeux VS / victoire
                pose(0x674C00 + offs[t_["pose"]], i, struct.pack('<I', a), e=8, decal=4); nred += 1
        pose(0x72BDF0, i, struct.pack('<I', PB))
        if yeux_:                                     # table propre des poses >= 32 : en-tête de 66 mots + fiches de 8 o
            while len(blk) & 3: blk += b"\0"
            tp = PB + len(blk); hd = [0] * 66
            for k_, (po_, a_) in enumerate(yeux_): hd[po_] = 2 * 66 + 8 * k_
            blk += struct.pack("<66H", *hd)
            for po_, a_ in yeux_:
                blk += bytes(buf[0x484C00 + offs[po_]:0x484C00 + offs[po_] + 4]) + struct.pack("<I", a_)
            YEUX_T[i] = tp
        while len(blk) & 0x1f: blk += b"\0"
        SELPAL[i] = PB + len(blk)
        vf_ = CV + "portraits_palettes_variantes.bin"
        cible_ = lambda f_, r_: r_ if rdir else int(f_)      # emplacement visé par les attributs du 128x224
        if os.path.exists(vf_) and mp_ and all(cible_(f, r) < 4 for f, r in mp_.items()):
            vv_ = open(vf_, "rb").read()
            for v_ in range(6):
                q_ = bytearray(src[:0x80])
                for f_, r_ in mp_.items(): q_[32*cible_(f_, r_):32*cible_(f_, r_)+32] = vv_[32*(4*v_+r_):32*(4*v_+r_)+32]
                blk += q_
        else: blk += src[:0x80] * 6
        blk += bytes(len(blk) & 1)
        assert len(blk) <= PORTRAIT_PAS
        open(os.path.join(W_, "ext_%06x.bin" % PB), "wb").write(bytes(b for j in range(0, len(blk), 2) for b in (blk[j+1], blk[j])))
        BLOCS_PLUS.append("%06x" % PB)
        log("%s ($%s) : portraits, %d poses redirigées (%d de la bande partagée ignorées), bloc $%x (%d o)" % (PERSOS[p]["nom"], p, nred, nbande, PB, len(blk)))
BLOCS_PLUS = []
YEUX_T = {}
ALPHA_TAB, ALPHA_TMP = 0xFF7F00, 0xFF7F84       # table MAX_ALPHA (session MAX) ; position de liste au début de l'objet
def talon_alpha(img, its, a):
    """(2b13) effets additifs (bit 12 du mot X, cœur 0010 v3) : les 35 écrivains d'entrées de la passe de dessin d'Upper
    (prologue « MOVE.W (A0)+,D5 ; CMP.W D5,D7 ; Bcc », A2 = position d'écriture dans $70xxxx, D7 = place) sont déviés vers
    un talon : prologue rejoué, reste de l'écrivain appelé en sous-routine, puis, si l'objet A6 est un objet MAX (type
    octet 3 dans [$2B, $3A], réservoirs $FF9400-$FFCFFF) et MAX_ALPHA[(A6.w - $9400) >> 7] = 1 : ORI.W #$1000 sur le mot X
    de chaque entrée écrite et $804240 = 1 (mode additif)"""
    if os.environ.get("MAX_ALPHA_BIT12", "0") != "1": return a      # (2b13) non retenu : +cycles sur TOUS les objets -> nonreg décalée
    sites = []
    k = img.find(bytes.fromhex("3a18be45"), 0x1000, 0x3A0000)
    while k >= 0:
        op = struct.unpack_from(">H", img, k + 4)[0]
        if (op & 0xFF00) == 0x6500:
            d8 = op & 0xFF
            if d8 == 0: tgt = k + 6 + struct.unpack_from(">h", img, k + 6)[0]; lp = 8
            else: tgt = k + 6 + (d8 - 0x100 if d8 & 0x80 else d8); lp = 6
            sites.append((k, tgt, lp))
        k = img.find(bytes.fromhex("3a18be45"), k + 2, 0x3A0000)
    # écritures dans la mémoire d'objets $70xxxx : ÉCRITURE SEULE (relire donne 0) -> pas d'ORI après coup. Les écrivains
    # composent le mot X par « OR.W $18(A6),D0 » : bit 12 posé dans $18(A6) le temps de l'écrivain (ON), retiré après (OFF)
    on = a
    w = [0x4239, 0x00FF, 0x7F84, 0x48E7, 0x8040, 0x300E, 0x0440, 0x9400, 0x0C40, 0x3C00, 0x643C, 0x0C2E, 0x002B, 0x0003,
         0x6534, 0x0C2E, 0x003A, 0x0003, 0x622C, 0xEE48, 0x43F9, 0x00FF, 0x7F00, 0x4A31, 0x0000, 0x671E, 0x082E, 0x0004,
         0x0018, 0x6616, 0x006E, 0x1000, 0x0018, 0x13FC, 0x0001, 0x00FF, 0x7F84, 0x33FC, 0x0001, 0x0080, 0x4240, 0x4CDF,
         0x0201, 0x4E75,
         0x4A39, 0x00FF, 0x7F84, 0x6706, 0x026E, 0xEFFF, 0x0018, 0x4E75]      # (assemblé avec vasm, scratchpad m2.s)
    off = on + 0x58
    struct.pack_into(">%dH" % len(w), img, a, *w)
    a += 2 * len(w); a = (a + 3) & ~3
    for k, tgt, lp in sites:
        r = k + lp
        # objets hors réservoirs $FF9400-$FFCFFF (A6 étendu : $FFFFxxxx) : saut direct au reste de l'écrivain (coût minimal)
        t = [0x588F, 0x3A18, 0xBE45, 0x6406, 0x4EF9, tgt >> 16, tgt & 0xFFFF,
             0xBCFC, 0x9400, 0x6518, 0xBCFC, 0xD000, 0x6412,
             0x4EB9, on >> 16, on & 0xFFFF, 0x4EB9, r >> 16, r & 0xFFFF, 0x4EF9, off >> 16, off & 0xFFFF,
             0x4EF9, r >> 16, r & 0xFFFF]
        if os.environ.get("MAX_ALPHA_NOP") == "1":          # (diagnostic) talon minimal : prologue rejoué, saut au reste
            t = [0x588F, 0x3A18, 0xBE45, 0x6406, 0x4EF9, tgt >> 16, tgt & 0xFFFF, 0x4EF9, r >> 16, r & 0xFFFF]
        assert not any(img[a:a + 2 * len(t)])
        struct.pack_into(">%dH" % len(t), img, a, *t)
        p = [0x4EB9, a >> 16, a & 0xFFFF] + ([0x4E71] if lp == 8 else [])
        struct.pack_into(">%dH" % len(p), img, k, *p)
        a += 2 * len(t)
    marque = on
    log("alpha (bit 12) : %d écrivains d'entrées déviés, marquage $%x" % (len(sites), marque))
    return a
def talon_citation(img, its, a):
    """(2b19) réplique de victoire, chemin $92(A5) = 0 (image $2FFF2 : LEA T_614E20,A1) : gagnant MAX ($133(A5) >= $26)
    -> pas d'index propre à l'adversaire (les MAX n'ont que 8 répliques) : D0 = aléa & $E déjà posé, saut en $30018"""
    t = AG.NOUVEAU[0x614E20]
    pat = struct.pack(">HI", 0x43F9, t)
    k = img.find(pat, 0x1000, 0x3A0000); assert k > 0 and img.find(pat, k + 2, 0x3A0000) < 0, "citation : site %x" % k
    # cible = celle du BRA.S qui précède (« ANDI.W #$E,D0 ; BRA.S suite » 16 octets avant le LEA ; $2FFE2 -> $30018 en v150)
    b_ = k - 0x10
    assert struct.unpack_from(">HH", img, b_ - 4) == (0x0240, 0x000E) and img[b_] == 0x60, "citation : BRA attendu en $%x" % b_
    suite = b_ + 2 + struct.unpack_from(">b", img, b_ + 1)[0]
    w = [0x0C2D, 0x0026, 0x0133, 0x6508, 0x588F, 0x4EF9, suite >> 16, suite & 0xFFFF, 0x43F9, t >> 16, t & 0xFFFF, 0x4E75]
    assert not any(img[a:a + 2 * len(w)])
    struct.pack_into(">%dH" % len(w), img, a, *w)
    struct.pack_into(">HI", img, k, 0x4EB9, a)
    log("répliques : gagnant MAX -> index 0-7 (site $%x -> talon $%x) ; T_614E20[MAX] = $FF" % (k, a))
    return a + 2 * len(w)

def reactions_psp(img, a):
    """(2b22, R5) réactions PSP 34-36 (fiche +$0D -> victime $55 arcade / $54 image ; Upper n'en a que 0-33). Les trois
    aiguillages EN LIGNE ont 48 entrées dont 34-47 inutilisées par les natifs : on n'y touche qu'aux rangs >= 34.
    1. coup porté, au sol et en l'air (deux tables à la suite, « MOVE.W T(PC,D0),D1 ; JSR T(PC,D1) ») : 34 / 36 = comme 18,
       35 = comme 14 ;
    2. gestionnaire de réaction (après « MOVE.B $54(A6),D0 ; ADD.W D0,D0 ») : 34 = 18 ; 35 / 36 = nouveaux (talons) :
       36 = $54 arcade = $10 puis la suite de 18 ; 35 = $26A = $7F, $258 = 1 puis 36. Talons atteints par des JMP posés
       DANS les entrées 37-47 de la table (inutilisées), à portée de décalage 16 bits.
    3. table d'animation (0x61B4A0) : copie prolongée MAX_ANIM_REACTIONS (LEA, image())."""
    # 1. coup porté
    pat = struct.pack(">5H", 0x323B, 0x0008, 0x4EBB, 0x1004, 0x6068)
    k = img.find(pat, 0x1000, 0x3A0000); assert k > 0 and img.find(pat, k + 2, 0x3A0000) < 0, "réactions : coup porté"
    t1 = k + 10; k2 = t1 + 96
    assert struct.unpack_from(">5H", img, k2) == (0x323B, 0x0008, 0x4EBB, 0x1004, 0x4E75), "réactions : 2e table"
    for t in (t1, k2 + 10):
        e = list(struct.unpack_from(">48H", img, t))
        assert e[34] == e[35] == e[36] == e[47], "réactions : entrées 34-36 déjà prises en $%x" % t
        struct.pack_into(">3H", img, t + 68, e[18], e[14], e[18])
    # 2. gestionnaire
    pat = struct.pack(">7H", 0x102E, 0x0054, 0xD040, 0x323B, 0x0008, 0x4EBB, 0x1004)
    k = img.find(pat, 0x1000, 0x3A0000); assert k > 0 and img.find(pat, k + 2, 0x3A0000) < 0, "réactions : gestionnaire"
    t = k + 16; assert struct.unpack_from(">H", img, t - 2)[0] == 0x4E75
    e = list(struct.unpack_from(">48H", img, t))
    assert len(set(e[34:48])) == 1 and e[34] == e[0], "réactions : entrées 34-47 du gestionnaire inattendues"
    h18 = t + e[18]
    assert struct.unpack_from(">3H", img, h18) == (0x1D7C, 0x0008, 0x0055), "réactions : gestionnaire 18 inattendu"
    suite = h18 + 6
    h35 = a; w = [0x1D7C, 0x007F, 0x026B, 0x1D7C, 0x0001, 0x0259]          # 35 : $26A = $7F, $258 = 1
    # 36 : $54 arcade = $10 sur PSP ; Upper n'a que 8 variantes ($0-$E, aiguillage image $503A0 : $10 lit le RTS qui suit
    # la table -> saut hors code, exception pc=$A08, croisé Ingrid contre Akuma du banc max17) -> 8, comme la réaction 18
    h36 = a + 2 * len(w); w += [0x1D7C, int(os.environ.get("MAX_REACTION_54", "8"), 16), 0x0055, 0x4EF9, suite >> 16, suite & 0xFFFF]
    assert not any(img[a:a + 2 * len(w)])
    struct.pack_into(">%dH" % len(w), img, a, *w)
    s35, s36 = t + 2 * 37, t + 2 * 40                                   # JMP posés dans les entrées 37-42 (inutilisées)
    struct.pack_into(">HIHI", img, s35, 0x4EF9, h35, 0x4EF9, h36)
    struct.pack_into(">3H", img, t + 68, e[18], s35 - t, s36 - t)
    log("réactions PSP 34-36 : coup porté $%x / $%x, gestionnaire $%x (talons $%x / $%x)" % (t1, k2 + 10, t, h35, h36))
    return a + 2 * len(w)

def lancer_vertical(img, a):
    """(2b24, R14) lancer de la victime : tables T1 ($B0FB0, 80 x 4), T2 ($B10F0, 80 paires), T3 ($B1190, rangées $00-$5F
    de 16 o) lues par le seul lecteur image $525A2 (LEA abs.l x 3, accès directs : pas de CONV) = PSP 0x5F168, qui a 84 /
    83 / $63 entrées (EBOOT 0x2140C8 / 0x214218 / 0x2142C0 ; 0-79 identiques). Copies prolongées depuis l'EBOOT, LEA
    redirigés (même instruction : même coût). La réaction 36 (fiche +$A = 83 : contres d'Ingrid) passe par la variante 4
    ($54 = 8), qui appelle aussi 0x5F130 sur PSP : la variante $10 n'est pas nécessaire pour le vol droit en l'air."""
    if os.environ.get("MAX_LANCER_VERTICAL", "1") != "1": return a
    eb = open(os.environ.get("SFA3MAX_EBOOT", "<workspace>/sfa3max-psp-widescreen/work/eboot/ULES00235_EBOOT.BIN"), "rb").read()[0x74:]
    sw = lambda b: bytes(b[i ^ 1] for i in range(len(b)))
    tabs = [(0xB0FB0, 0x2140C8, 4 * 80, 4 * 84), (0xB10F0, 0x214218, 2 * 80, 2 * 0x53), (0xB1190, 0x2142C0, 16 * 0x60, 16 * 0x63)]
    pat = [0x525AE, 0x525CE, 0x525F0]
    # lecteur repéré par motif (MOVE.B $29E(A6),D0 ; LSL.W #2,D0 ; ADD.B $25E(A6),D0 ; LEA T1,A0)
    m = bytes.fromhex("102e029ee548d02e025e41f9")
    k = img.find(m, 0x1000, 0x3A0000); assert k > 0 and img.find(m, k + 2, 0x3A0000) < 0, "lancer : lecteur T1-T3"
    leas = [k + 10, k + 10 + 0x20, k + 10 + 0x42]
    a = (a + 0xF) & ~0xF
    for (adr, psp, n0, n1), l in zip(tabs, leas):
        assert struct.unpack_from(">HI", img, l) == (0x41F9, adr), "lancer : LEA $%x attendu en $%x" % (adr, l)
        assert img[adr:adr + n0] == sw(eb[psp:psp + n0]), "lancer : table $%x différente de la PSP" % adr
        img[a:a + n1] = sw(eb[psp:psp + n1])
        struct.pack_into(">I", img, l + 2, a)
        log("lancer : table $%x (%d o) -> copie prolongée $%x (%d o), LEA $%x" % (adr, n0, a, n1, l))
        a = (a + n1 + 0xF) & ~0xF
    return a

def talon_cond40(img, a):
    """(2b24, N20) condition 40 de l'IA PSP (0x75B94 : op = (A0)+ ; op >= aléa & 31 -> suite, sinon saut de bloc). La table
    des conditions est EN LIGNE ($DEEC : MOVE.W T(PC,D0.W),D1 ; JMP T(PC,D1.W), T = $DEF4, 39 entrées, gestionnaire 0
    collé derrière) : aucune place pour l'index $50. Crochet en $DEE6 (MOVE.W (A0)+,D0 ; MOVE.W D0,$20A(A6) = 6 octets ->
    JMP talon) : talon = ces deux instructions, index $50 -> COND40, sinon JMP $DEEC. Suite = $ED48, saut = $E432
    (comme la condition 0, image $DF52 / $DF58), aléa = $1A720 (condition 2)."""
    if os.environ.get("MAX_IA", "1") != "1" or "IA_T0_26" not in SYM: return a
    k = 0xDEE6
    assert bytes(img[k:k + 14]) == bytes.fromhex("30183d40020a323b00064efb1002"), "IA : motif de l'interpréteur en $DEE6"
    assert bytes(img[0xDF52:0xDF54]) == bytes.fromhex("6100") and bytes(img[0xDF78:0xDF7A]) == bytes.fromhex("4eb9")
    w = [0x3018, 0x3D40, 0x020A, 0x0C40, 0x0050, 0x6706, 0x4EF9, 0x0000, 0xDEEC,
         0x3218, 0x3F01, 0x4EB9, 0x0001, 0xA720, 0x321F, 0x0240, 0x001F, 0xB240, 0x6506,
         0x4EF9, 0x0000, 0xED48, 0x4EF9, 0x0000, 0xE432]
    assert not any(img[a:a + 2 * len(w)])
    struct.pack_into(">%dH" % len(w), img, a, *w)
    struct.pack_into(">HI", img, k, 0x4EF9, a)
    log("IA : condition 40 (index $50) : crochet $%x -> talon $%x" % (k, a))
    a += 2 * len(w)
    # saut de bloc ($F944 : ADDQ.B #1,$214(A6) ; MOVE.W (A0)+,D0 ; MOVE.W T(PC,D0.W),D1 ; JSR T(PC,D1.W), T = $F956,
    # 39 entrées : $F9FC = 1 opérande, $FA00 = aucune) : la condition 40 a 1 opérande -> ADDQ.W #2,A0 puis BRA $FB60
    k2 = 0xF944
    assert bytes(img[k2:k2 + 18]) == bytes.fromhex("522e02143018323b000a4ebb10066000020c"), "IA : motif du saut de bloc en $F944"
    w2 = [0x522E, 0x0214, 0x3018, 0x0C40, 0x0050, 0x6608, 0x5448, 0x4EF9, 0x0000, 0xFB60, 0x4EF9, 0x0000, 0xF94A]
    assert not any(img[a:a + 2 * len(w2)])
    struct.pack_into(">%dH" % len(w2), img, a, *w2)
    struct.pack_into(">HI", img, k2, 0x4EF9, a)
    log("IA : condition 40 dans le saut de bloc : crochet $%x -> talon $%x" % (k2, a))
    return a + 2 * len(w2)

DLG_CHOIX = []
def talon_dialogues(img, a):
    """(2b24, N21) choix des scénarios d'avant / après combat : octet [($13E - 8) / 2 x 40 + ID] de 0x61B580 (image $B18C0)
    et 0x61B600 ($B1940), lus en $588A6 / $5957C (×16 + ×4 = ×20 : rangées de 40, Yun / Ingrid hors table). Rangées de 48 :
    LSL.W #2,D1 -> #3 (×24) aux deux sites, copies de 3 x 48 octets (ordre image : index logique j en j ^ 1), LEA redirigés."""
    if not DLG_CHOIX or os.environ.get("MAX_DIALOGUES", "1") != "1": return a
    a = (a + 0xF) & ~0xF
    for site, tab, ps2 in ((0x588A6, 0xB18C0, 0x61B580), (0x5957C, 0xB1940, 0x61B600)):
        assert bytes(img[site:site + 18]) == bytes.fromhex("102d013e51403200e948e549d041d02e0103"), "dialogues : motif en $%x" % site
        assert struct.unpack_from(">HI", img, site + 18) == (0x41F9, tab), "dialogues : LEA $%x attendu" % tab
        lig = [[img[tab + ((r * 40 + i) ^ 1)] for i in range(40)] + [0xFF] * 8 for r in range(3)]
        for t_, r_, i_, v_ in DLG_CHOIX:
            if t_ == ps2: lig[r_][i_] = v_
        flat = [x for r in lig for x in r]
        for j, v in enumerate(flat): img[a + (j ^ 1)] = v
        struct.pack_into(">H", img, site + 10, 0xE749)
        struct.pack_into(">I", img, site + 20, a)
        log("dialogues : 0x%X (image $%x) -> rangées de 48 en $%x, ×24 en $%x" % (ps2, tab, a, site))
        a += 0x90
    return a

def talon_flammes(img, its, a):
    """(2b18) ancrage des flammes (image $32D5C : MOVE.B $10(A2),D1 ; ANDI.W #$F,D1, A4 = victime) : index du pas
    SANS le masque $F pour une victime MAX (PSP : octet +$11 du pas, jusqu'à 21 ; FLAMMES_xx de 22 couples) -> & $1F ;
    natifs inchangés (& $F)"""
    pat = struct.pack(">4H", 0x122A, 0x0010, 0x0241, 0x000F)
    sites = []; k = img.find(pat, 0x1000, 0x3A0000)
    while k >= 0:
        if k % 2 == 0: sites.append(k)
        k = img.find(pat, k + 2, 0x3A0000)
    assert len(sites) == 1, "flammes : %d sites" % len(sites)
    ids = [int(p, 16) for p in ("26", "27", "2d", "2e") if p in ACTIFS]
    if os.environ.get("MAX_FLAMMES_IDX") == "temoin": ids = []   # (2b18) témoin : même JSR, aucun test (coût seul)
    w = [0x122A, 0x0010]
    for j, i in enumerate(ids):
        reste = len(ids) - 1 - j                                  # CMPI.B #id,$103(A4) ; BEQ.S .max
        w += [0x0C2C, i, 0x0103, 0x6700 | (8 * reste + 6)]
    w += [0x0241, 0x000F, 0x4E75, 0x0241, 0x001F, 0x4E75]
    assert not any(img[a:a + 2 * len(w)])
    struct.pack_into(">%dH" % len(w), img, a, *w)
    struct.pack_into(">HIH", img, sites[0], 0x4EB9, a, 0x4E71)
    log("flammes : index du pas sans masque $F pour les MAX : site $%x -> talon $%x" % (sites[0], a))
    return a + 2 * len(w)

def talon_yeux(img, its, a):
    """(18/10) poses >= 32 (yeux VS / victoire, bande partagée A[pose-32+ID] de 0x674C00) : lecteurs « LEA copie,A0 ;
    ADD.W 0(A0,D0.W),D1 » (D0 = 2·pose, D1 = 8·ID) -> JSR talon : ID MAX et pose >= 32 -> table propre, D1 = 0"""
    if not YEUX_T: return a
    t = AG.NOUVEAU[0x674C00]
    sites = [k - 2 for k in AG.lea_sites(img, 0x1000, 0x3A0000, t)          # lea_sites : position de l'OPÉRANDE
             if struct.unpack_from(">H", img, k - 2)[0] == 0x41F9 and struct.unpack_from(">HH", img, k + 4) == (0xD270, 0x0000)]
    assert sites, "yeux : aucun lecteur de 0x674C00"
    w = [0x41F9, t >> 16, t & 0xFFFF, 0x0C40, 0x0040, 0x6500 | (16 * len(YEUX_T))]
    for i, tp in sorted(YEUX_T.items()):
        w += [0x0C41, 8 * i, 0x660A, 0x41F9, tp >> 16, tp & 0xFFFF, 0x7200, 0x4E75]   # CMPI.W ; BNE.S ; LEA ; MOVEQ #0,D1 ; RTS
    w += [0x4E75]
    assert not any(img[a:a + 2 * len(w)])
    struct.pack_into(">%dH" % len(w), img, a, *w)
    for k in sites: struct.pack_into(">HI", img, k, 0x4EB9, a)
    log("yeux (poses >= 32) : %d lecteurs de 0x674C00 -> talon $%x (%s)" % (len(sites), a, ", ".join("$%02X" % i for i in sorted(YEUX_T))))
    return a + 2 * len(w)

def talon_selpal(img, T, CODE_FIN, DATA_BASE):
    """(§131) rendu des palettes de sélection : 'LEA $1BB4E0,A0 ; ADD.W (A0,D0.W),D1 ; ADDA.W D1,A0' (D0 = 2 x ID) ->
    'JSR talon ; NOP x3' ; talon : pour chaque ID MAX, A0 = son bloc + D1 ; sinon la forme d'origine"""
    if not SELPAL: return
    a_ = T.addr_to_68k(0x7251A0) & 0xffffff
    pat = struct.pack('>HHHHHH', 0x41f9, a_ >> 16, a_ & 0xffff, 0xd270, 0x0000, 0xd0c1)
    o_ = img.find(pat, 0, DATA_BASE)
    assert o_ > 0 and img.find(pat, o_ + 2, DATA_BASE) < 0, "portraits : motif de sélection introuvable ou multiple"
    w = []
    for i, sp in sorted(SELPAL.items()):
        w += [0x0c40, 2 * i, 0x660a, 0x41f9, sp >> 16, sp & 0xffff, 0xd0c1, 0x4e75]   # CMPI.W #2i,D0 ; BNE.S +10 ; LEA ; ADDA.W D1,A0 ; RTS
    w += [0x41f9, a_ >> 16, a_ & 0xffff, 0xd270, 0x0000, 0xd0c1, 0x4e75]
    st_ = (CODE_FIN + 0x0f) & ~0x0f
    stub = struct.pack('>%dH' % len(w), *w)
    assert st_ + len(stub) <= DATA_BASE and not any(img[st_:st_ + len(stub)]), "portraits : pas de place pour le talon"
    img[st_:st_ + len(stub)] = stub
    img[o_:o_ + 12] = struct.pack('>HHHHHH', 0x4eb9, st_ >> 16, st_ & 0xffff, 0x4e71, 0x4e71, 0x4e71)
    log("portraits : palettes de sélection déviées en $%x (talon $%x, %d persos)" % (o_, st_, len(SELPAL)))

def _code68(data, T, a, natif):
    """lit une case de table de code relogée (étape B) -> adresse 68K"""
    o = a - T.CODE_END_RT
    if natif:
        hi, lo = struct.unpack_from("<HH", data, o); return (hi << 16) | lo
    return struct.unpack_from("<I", data, o)[0]

def _pose68(data, T, a, v, natif):
    o = a - T.CODE_END_RT
    if natif: struct.pack_into("<HH", data, o, v >> 16, v & 0xFFFF)
    else: struct.pack_into("<I", data, o, v)

def _pose_id(data, T, t, i, v, natif):
    """case i d'une table de code : en place si i < 40, sinon dans la copie agrandie"""
    if i < 40: _pose68(data, T, t + 4 * i, v, natif)
    else: AG.ajout(t, i, struct.pack("<HH", v >> 16, v & 0xFFFF) if natif else struct.pack("<I", v))

def tables_code(data, T):
    """après l'étape B : cases des tables de code -> enveloppes / routines MAX ; tables déplacées (effets, palettes)"""
    charge()
    global DATA_PS2; DATA_PS2 = data
    assert T.RELOGE_TABLES, "MAX=1 suppose l'étape B (RELOGE_CODE=1)"
    tables = {p_: f_ for p_, f_ in T.RELOGE_TABLES.items()}
    natif = lambda t: t in T.RELOGE_NATIF_TABLES
    for p in ACTIFS:
        i = int(p, 16); P = PERSOS[p]; n = 0
        for tab, rappel in P["rappels"].items():
            t = int(tab, 16)
            assert t in tables and tables[t] >= t + 4 * min(i + 1, 40), "table de code %x non relogée" % t
            _pose_id(data, T, t, i, S("MAXW_%s_%s" % (p, tab)), natif(t)); n += 1
        if p in TYPE_PROJ:
            ty = S(TYPE_PROJ[p]) if TYPE_PROJ[p] in SYM else None
            assert ty is not None and ty < 48, "type de projectile %s" % TYPE_PROJ[p]
            if ty < 0x28: assert _code68(data, T, T_PROJ + 4 * ty, natif(T_PROJ)) == 0, "type de projectile $%x occupé" % ty
            _pose_id(data, T, T_PROJ, ty, S("TIR_W_%s" % p) if "TIR_W_%s" % p in SYM else S(FILS[p]), natif(T_PROJ)); n += 1
        log("%s ($%s) : %d cases de tables de code" % (P["nom"], p, n))
    # classes du réservoir d'effets : table déplacée (64 entrées) = 40 d'Upper + classes MAX
    assert T_EFFETS in tables and tables[T_EFFETS] == T_EFFETS + 160
    eff = [_code68(data, T, T_EFFETS + 4 * k, natif(T_EFFETS)) for k in range(40)] + [0] * 24
    for p in ACTIFS:
        for c, r in CLASSES[p].items():
            assert eff[c] == 0; eff[c] = S("EFFET_W_%02X" % c) if (os.environ.get("MAX_EFFETS_AFF", "1") == "1" and "EFFET_W_%02X" % c in SYM) else S(r)
    struct.pack_into(">64I", BLOB, S("MAX_T_EFFETS") - ORG, *eff)
    log("classes d'effets : table déplacée en $%x (%s)" % (S("MAX_T_EFFETS"), ", ".join("$%02X" % c for p in ACTIFS for c in CLASSES[p])))
    # tables par ID agrandies à 48 (après TOUTES les écritures par ID dans les données)
    AG.construit(data, T, ORIG)

T_PALE = 0x700540                                   # palettes d'EFFETS par perso (40 décalages signés, blocs de 30)

def palettes(data, end):
    """tables des palettes par perso DÉPLACÉES dans le bloc MAX : 64 entrées au MILIEU des blocs d'Upper recopiés et des
    blocs MAX ; décalages signés 16 bits recalculés. Corps (T_6f72b0, 13 sites) et effets (T_700540, 2 sites)."""
    global PALE_NOUVELLE
    PALE_NOUVELLE = deplace_palettes(data, end, T_PALE, "MAX_PALE_ZONE", "palettes_effets_module.bin", "palettes d'effets")
    return deplace_palettes(data, end, T_PAL, "MAX_PAL_ZONE", "palettes_module.bin", "palettes")

def deplace_palettes(data, end, T_ps2, zone, fichier, nom):
    o = lambda a: a - RB - end
    t0 = o(T_ps2)
    off = list(struct.unpack_from("<40h", data, t0))
    blocs = sorted(set(off)); N = 0x3C0
    # taille réelle de chaque bloc = écart au bloc suivant (Chun-Li, Sodom, Vega ont plus de 30 palettes d'effets),
    # au plus $600 ; le bloc qui précède la table s'arrête à la table
    tailles = {b: min(((blocs[k + 1] if k + 1 < len(blocs) else b + 0x600) - b), 0x600) for k, b in enumerate(blocs)}
    for b in blocs:
        if b < 0 < b + tailles[b]: tailles[b] = -b
    corps = {b: bytes(data[t0 + b:t0 + b + tailles[b]]) for b in blocs}
    for p in ACTIFS:
        f_ = MC.CV + "%s/%s" % (PERSOS[p]["pl"], fichier)
        fu_ = f_.replace(".bin", "_upper.bin")        # Ingrid : 48 palettes PSP -> 6 x 5 (session MAX, point 7)
        d = open(fu_ if os.path.exists(fu_) else f_, "rb").read()
        corps["max" + p] = d[:N] if len(d) >= N else d + bytes(N - len(d))
    cles = blocs + ["max" + p for p in ACTIFS]
    taille = lambda k: len(corps[k])
    avant, apres, tot = [], [], sum(taille(k) for k in cles)
    acc = 0
    for k in cles:
        (avant if acc + taille(k) <= tot // 2 else apres).append(k); acc += taille(k)
    Z = bytearray(); pos = {}
    for k in avant: pos[k] = len(Z); Z += corps[k]
    tz = len(Z); Z += bytes(0x80)
    for k in apres: pos[k] = len(Z); Z += corps[k]
    tab = [pos[b] - tz for b in off] + [pos[off[0]] - tz] * 24     # au-delà de 40 : bloc de Ryu par défaut
    for p in ACTIFS: tab[int(p, 16)] = pos["max" + p] - tz
    assert all(-0x8000 <= x <= 0x7FFF - N for x in tab)
    struct.pack_into("<64h", Z, tz, *tab)
    za = S(zone)
    im = bytes(x for i in range(0, len(Z), 2) for x in (Z[i + 1], Z[i]))   # PS2 -> image (mots échangés)
    suite = min(v for k, v in SYM.items() if not k.startswith("_") and isinstance(v, int) and v > za)   # symbole suivant
    assert za + len(im) <= suite, "%s : %d octets > place réservée ($%x)" % (zone, len(im), suite - za)
    BLOB[za - ORG:za - ORG + len(im)] = im
    log("%s : table déplacée en $%x (%d blocs, %d octets)" % (nom, za + tz, len(cles), len(Z)))
    return za + tz

def image(img, its, T, W, ext_plus, carte_lignes, code_fin=None):
    """code : LEA des tables déplacées, seuil des cases « ? » ; blocs externes"""
    charge()
    md5 = hashlib.md5("".join(" ".join(l.split()[:2]) + "\n" for l in carte_lignes).encode()).hexdigest()
    assert md5 == SYM["_carte_md5"], "MAX : la carte de cette construction (%s) n'est pas celle de la préparation (%s) : relancer outils/prepare_max.py" % (md5, SYM["_carte_md5"])
    def lea_abs(ancien, nouveau, attendu):
        n = 0
        for reg in range(8):
            pat = struct.pack(">HI", 0x41F9 | (reg << 9), ancien)
            k = img.find(pat)
            while 0 <= k < 0x3C0000:
                if k % 2 == 0: struct.pack_into(">I", img, k + 2, nouveau); n += 1
                k = img.find(pat, k + 2)
        assert n == attendu, "LEA $%x : %d sites (%d attendus)" % (ancien, n, attendu)
        return n
    if os.environ.get("MAX_DEF_VICTIME", "1") == "1":       # (2b24) défense par victime : ID non masqué (voir plus haut)
        for pat in ("102901030240001feb48", "182901030244001feb4c"):
            b_ = bytes.fromhex(pat); k = img.find(b_, 0x1000, 0x3A0000)
            assert k > 0 and img.find(b_, k + 2, 0x3A0000) < 0, "défense par victime : motif %s" % pat
            img[k + 7] = 0x3F
    a_eff = T.addr_to_68k(T_EFFETS) & 0xFFFFFF
    lea_abs(a_eff, S("MAX_T_EFFETS"), 1)
    # (2b20) lecteur PROPRE à Rolento ($4479A : LEA de sa ligne 0x76E9FE, indexée par l'ID de la victime) : la copie
    # agrandie de la ligne (colonnes MAX = Ryu) -> PROJ_NAT_0E (session MAX, colonnes MAX propres ; natives identiques)
    if "PROJ_NAT_0E" in SYM and os.environ.get("MAX_PROJ_NAT", "1") == "1":
        a_ro = T.addr_to_68k(0x76E9FE) & 0xFFFFFF       # (avant AG.patch_code : le LEA vise encore l'original)
        if a_ro: lea_abs(a_ro, S("PROJ_NAT_0E"), 1); log("projections : lecteur de Rolento $4479A -> PROJ_NAT_0E ($%x)" % S("PROJ_NAT_0E"))
    if "MAX_ANIM_REACTIONS" in SYM:                    # (2b22, R5) table d'animation des réactions 0-36
        lea_abs(T.addr_to_68k(0x61B4A0) & 0xFFFFFF, S("MAX_ANIM_REACTIONS"), 2)
        log("réactions : table d'animation 0x61B4A0 -> MAX_ANIM_REACTIONS ($%x)" % S("MAX_ANIM_REACTIONS"))
    if "RECUL_TYPES" in SYM and os.environ.get("MAX_RECUL", "1") == "1":   # (2b18) types de recul 0-32 (T_61B460 n'en a que 28)
        a_rec = T.addr_to_68k(0x61B460) & 0xFFFFFF
        lab_ = "MAX_RECUL_TYPES" if "MAX_RECUL_TYPES" in SYM else "RECUL_TYPES"
        lea_abs(a_rec, S(lab_), 1); log("recul : T_61B460 ($%x) -> %s ($%x)" % (a_rec, lab_, S(lab_)))
    a_pal = T.addr_to_68k(T_PAL) & 0xFFFFFF
    a_pale = T.addr_to_68k(T_PALE) & 0xFFFFFF
    if os.environ.get("MAX_PAL_DEPLACE", "1") == "1":
        n = lea_abs(a_pal, PAL_NOUVELLE, 13)
        n2 = lea_abs(a_pale, PALE_NOUVELLE, 2)
    else: n = n2 = 0                                  # (2b22, essai) palettes NON déplacées (couleurs MAX fausses)
    log("LEA : table d'effets $%x -> $%x ; palettes $%x -> $%x (%d sites) ; palettes d'effets $%x -> $%x (%d sites)" % (
        a_eff, S("MAX_T_EFFETS"), a_pal, PAL_NOUVELLE, n, a_pale, PALE_NOUVELLE, n2))
    if code_fin is not None: talon_selpal(img, T, code_fin, T.DATA_BASE)
    it = [x for x in its if x.va == SEUIL_VA and x.ws and x.mn.startswith("CMPI.B #$26,D0")]
    assert len(it) == 1 and struct.unpack_from(">HH", img, it[0].off) == (0x0C00, 0x0026), "seuil des « ? » introuvable"
    struct.pack_into(">H", img, it[0].off + 2, SEUIL)
    log("seuil des cases « ? » : CMPI.B #$%02X,D0 en $%x" % (SEUIL, it[0].off))
    AG.ecrit(W, ext_plus)
    global CTX; CTX = (its, T, W)
    import shutil
    ext_plus.extend(BLOCS_PLUS)
    for b in sorted(set(J["blocs"])):
        if b == "%06x" % ORG: open(os.path.join(W, "ext_%06x.bin" % ORG), "wb").write(BLOB)
        else: shutil.copy(os.path.join(DIR, "blocs", "ext_%s.bin" % b), W)
        ext_plus.append(b)
    open(os.path.join(W, "max_journal.txt"), "w").write("\n".join(JOURNAL) + "\n")
    log("blocs externes : %s" % ", ".join(ext_plus))

PAL_NOUVELLE = None; PALE_NOUVELLE = None; DATA_PS2 = None; CTX = None

def fin(img):
    """CODE MAX dans l'image ($3A0000-$3BFFFF, place libérée par le plafond abaissé des données) ; la zone doit être vide"""
    charge()
    c = open(os.path.join(DIR, "code_%06x.bin" % J["code_org"]), "rb").read()
    o = J["code_org"]
    assert not any(img[o:0x3C0000]), "MAX : la zone du code ($%x-$3C0000) n'est pas libre" % o
    if os.environ.get("MAX_ANALYSE") == "1":
        import agrandit_max
        its, T, W = CTX
        agrandit_max.recense(img, its, T, DATA_PS2, c, o, W)
    img[o:o + len(c)] = c
    log("code MAX : %d octets en $%x-$%x" % (len(c), o, o + len(c)))
    its, T, W = CTX
    fin_ = AG.patch_code(img, its, T, T.DATA_BASE, (o + len(c) + 0xF) & ~0xF)
    z_ = (fin_ + 0xF) & ~0xF
    while any(img[z_:z_ + 0x1200]): z_ += 0x10
    fin_ = max(fin_, talon_apercu_pal(img, its, z_))
    assert fin_ <= z_ + 0x1200
    z_ = (fin_ + 0xF) & ~0xF
    while any(img[z_:z_ + 0x100]): z_ += 0x10
    fin_ = max(fin_, talon_prologue(img, its, z_))
    z_ = (fin_ + 0xF) & ~0xF
    while any(img[z_:z_ + 0x100]): z_ += 0x10
    fin_ = max(fin_, talon_yeux(img, its, z_))
    z_ = (fin_ + 0xF) & ~0xF
    while any(img[z_:z_ + 0x600]): z_ += 0x10
    fin_ = max(fin_, talon_alpha(img, its, z_))
    z_ = (fin_ + 0xF) & ~0xF
    while any(img[z_:z_ + 0x100]): z_ += 0x10
    fin_ = max(fin_, talon_citation(img, its, z_))
    z_ = (fin_ + 0xF) & ~0xF
    while any(img[z_:z_ + 0x100]): z_ += 0x10
    fin_ = max(fin_, reactions_psp(img, z_))
    z_ = (fin_ + 0xF) & ~0xF
    while any(img[z_:z_ + 0x800]): z_ += 0x10
    fin_ = max(fin_, lancer_vertical(img, z_))
    z_ = (fin_ + 0xF) & ~0xF
    while any(img[z_:z_ + 0x100]): z_ += 0x10
    fin_ = max(fin_, talon_cond40(img, z_))
    z_ = (fin_ + 0xF) & ~0xF
    while any(img[z_:z_ + 0x200]): z_ += 0x10
    fin_ = max(fin_, talon_dialogues(img, z_))
    if "MAX_PALPROPRE" in SYM:                          # (2b21) palette propre des acteurs de fin (générateur $1AA8)
        # site repéré par l'adresse MIPS (va 0x21A2B4 : MOVE.B #$FF,$D(A4) du générateur $2750E) : image $1B1C en v150
        # motif : MOVE.L $1C(A1),$7C(A4) ; MOVE.B #$FF,$D(A4) (fin du générateur, image $1B16 en v150)
        pat_ = struct.pack(">6H", 0x2969, 0x001C, 0x007C, 0x197C, 0x00FF, 0x000D)
        k_ = []; q_ = img.find(pat_, 0x1000, 0x3A0000)
        while q_ >= 0:
            if q_ % 2 == 0: k_.append(q_ + 6)
            q_ = img.find(pat_, q_ + 2, 0x3A0000)
        assert len(k_) == 1, "générateur d'acteurs : %d sites" % len(k_)
        struct.pack_into(">HI", img, k_[0], 0x4EB9, S("MAX_PALPROPRE"))
        log("acteurs de fin : palette propre (perso du joueur) -> palette OBJ 30, générateur $%x -> $%x" % (k_[0], S("MAX_PALPROPRE")))
    if "FLAMMES_26" in SYM and os.environ.get("MAX_FLAMMES_IDX", "aj") in ("dup", "and1f"):  # (2b19) & $F -> & $1F en place
        pat = struct.pack(">4H", 0x122A, 0x0010, 0x0241, 0x000F)
        k_ = img.find(pat, 0x1000, 0x3A0000); assert k_ > 0 and img.find(pat, k_ + 2, 0x3A0000) < 0
        struct.pack_into(">H", img, k_ + 6, 0x001F)
        log("flammes : index du pas & $1F en $%x (natifs : 16 couples doublés)" % k_)
    if "FLAMMES_26" in SYM and os.environ.get("MAX_FLAMMES_IDX", "aj") in ("1", "temoin"):
        z_ = (fin_ + 0xF) & ~0xF
        while any(img[z_:z_ + 0x100]): z_ += 0x10
        fin_ = max(fin_, talon_flammes(img, its, z_))
    if os.environ.get("MAX_CONTRES") == "1":
        z_ = (fin_ + 0xF) & ~0xF
        while any(img[z_:z_ + 0x100]): z_ += 0x10
        fin_ = max(fin_, talon_contres(img, its, z_))
    if os.environ.get("MAX_FINS") == "1":
        z_ = (fin_ + 0xF) & ~0xF
        while any(img[z_:z_ + 0x400]): z_ += 0x10                # zone libre (la place après le talon 620630 peut servir)
        fin_ = max(fin_, talons_acteurs(img, its, z_))
        z_ = (fin_ + 0xF) & ~0xF
        while any(img[z_:z_ + 0x100]): z_ += 0x10
        fin_ = max(fin_, talons_entree0(img, its, z_))
    assert fin_ <= 0x3C0000
    AG.journal(W)
    open(os.path.join(W, "max_journal.txt"), "a").write("\n".join(AG.JOURNAL) + "\n")
