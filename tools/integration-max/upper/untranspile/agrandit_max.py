"""(agent_integration_max) TABLES PAR ID AGRANDIES À 48 ENTRÉES (palier 2b : Yun $2D, Ingrid $2E, n° libres,
décision « option 2 » du coordinateur ; aucun pseudo-ID d'Upper n'est renuméroté).

Principe : chaque table lue par ID est RECOPIÉE (jamais déplacée : l'original reste en place, inchangé, pour les accès
intérieurs) dans un bloc externe ($E80000, ext_e80000.bin), avec 48 entrées par rangée :
  entrées 0-44  = octets d'origine à T + e·i (0-39 = la table, 40-44 = ce qui la suit : les pseudo-ID d'Upper
                  $28/$29 (Vega, Chun-Li X-ism) et tout débordement lisent exactement les mêmes octets qu'avant) ;
  entrées 45/46 = Yun / Ingrid (valeurs MAX posées par integre_max via ajout()), sinon copie de l'entrée 0 (Ryu) ;
  entrée  47    = ancienne entrée 39 (dans les poses de portraits et la structure des noms, c'est la VARIANTE de
                  Juli/Juni, adressée par trois « MOVEQ #39,D1 » passés ici à #47).
Les lecteurs (LEA abs.L de l'adresse de la table, code de l'image) sont redirigés vers la copie ; les pointeurs PS2 des
données qui visent le début d'une table aussi. Genres :
  simple : entrée i à T + e·i, R rangées de 40 (constante de rangée dans le code passée de 40·e à 48·e) ;
  rel16  : en-tête de décalages u16 relatifs à la table + données qui suivent : en-tête de 48, données recopiées
           derrière (+$10), blocs MAX ajoutés à la suite ;
  struct : en-tête de H décalages u16 (poses de portraits 0x674C00, noms/bandeaux 0x961AF0) : la structure est recopiée
           telle quelle, et chaque liste par ID (40 × 8 octets, écart $140) est recopiée agrandie à la suite ;
  967bf0 : structure à rangées propre (voir speciale_967bf0) ;
  620630 : aiguillage EN LIGNE dans le code (40 mots après un JMP) : talon qui ramène les ID >= $28 à l'entrée 0.
Recensement des références : MAX_ANALYSE=1 (recense())."""
import os, json, struct, bisect, array
from collections import defaultdict

RACINE = os.environ.get("MAX_RACINE", "<workspace>/work/agent_integration_max")
TABLES = json.load(open(os.path.join(RACINE, "outils", "tables_par_id.json")))
RB = 0x1F0000
N48 = 48
BLOC = 0xE80000                   # bloc externe des tables agrandies (libre ; hors des plages de CONV ; FBNeo : hsfa_ext)
JOURNAL = []
def log(m): JOURNAL.append(m); print("MAX : " + m)

# ------------------------------------------------------------------------------------------------ inventaire
IGNOREES = {0x628320: "natif (banque de sprites)",
            0x628370: "natif (portrait X_DATA)", 0x628470: "natif (fichiers de pose)",
            0x60D070: "classes d'effets (déjà déplacée, 64 entrées)",
            0x620630: "aiguillage EN LIGNE dans le code (talon)", 0x967BF0: "structure à rangées (speciale_967bf0)",
            0x97A20C: "parcours Arcade « alternatif » : aucun lecteur dans Upper"}
# paires imbriquées (deux demi-tables de 2 octets dans des entrées de 4) : une seule copie, lecteurs à +0 et +2
PAIRES = {0x615572: 0x615570, 0x615792: 0x615790, 0x61AAD2: 0x61AAD0, 0x616B32: 0x616B30}
# tables par ID absentes des cartographies (trouvées ici : « MOVE.B $103(An),Dn » puis lecture indexée)
AJOUTEES = [  # (ps2, e, n d'origine, rôle)
    # 0x60AD90 (ID -> ID de base, cartographies) : lu par le talon natif 0x37AF90 (MOVE.L #table,D1 ; ID de base >= $28
    # ignoré par CMPI.W #$28) -> redirigé comme les LEA (lea_sites accepte MOVE.L / MOVEA.L #imm)
    (0x60C680, 1, 40, "octet par perso -> $28F (va 0x49EC8)"),
    (0x616B30, 4, 40, "carte du monde : (x, y) de départ par perso (lecteur va 0x3889C0 ; audit 2b22)"),
    (0x615380, 1, 40, "octet par perso, test (va 0x1725A8)"),
    (0x61BDB0, 1, 40, "adversaire spécial -> $103 de l'adversaire (va 0x250EE4)"),
    (0x61B650, 1, 40, "octet par perso -> $147(A5) (va 0x2667B4)"),
    (0x61D9F0, 2, 40, "mot par perso -> $6A (va 0x2B7434)"),
    (0x615940, 4, 42, "pseudo-ID de Vega (40/41) : 42 longs"),
    (0x613350, 1, 45, "musique par perso (adversaire) ; 40-44 = musiques spéciales (va 0x13A840)"),
    (0x614E20, 1, 40, "octet par gagnant ($132(A5)) -> index de citation (va 0x15C584)"),
    (0x61C160, 1, 40, "ID -> ID (variantes ramenées ; va 0x272DCC, joueurs 1-4) : identité pour les MAX"),
    # FINS (index $1C9(A5), 41 entrées + 3 nulles ; paires JP / US selon $90(A5)) : va 0x29E58, 0x2A9E8...
    (0x60B220, 4, 44, "fin : acteurs (JP)"), (0x60B2D0, 4, 44, "fin : acteurs (US)"),
    (0x60B5A0, 4, 44, "fin : $8008 (JP)"), (0x60B650, 4, 44, "fin : $8008 (US)"),
    (0x60B700, 4, 44, "fin : $800C (JP)"), (0x60B7B0, 4, 44, "fin : $800C (US)"),
    (0x60B860, 4, 44, "fin : script $8034 (JP)"), (0x60B910, 4, 44, "fin : script $8034 (US)"),
    (0x619B50, 4, 40, "banques d'animation des acteurs de fin (octet +$1F ; LEA $AFE90 en $4B51A)"),
    (0x60B9C0, 6, 44, "fin : 3 mots -> $802A/$802E/$8030"),
    (0x95C8E0, 8, 42, "visage HUD J1 (40 = Chun-Li $133<0, 41 = mode spécial)"),
    (0x95CA30, 8, 42, "visage HUD J2"),
    (0x95CB80, 8, 42, "visage HUD (3e variante)"),
    (0x95CCD0, 8, 42, "visage HUD (4e variante, J2 + 16 ; audit 2b22)"),
]
# tables à rangées : (ps2, e, rangées, [(va, ancien, nouveau) des « ADDI.W #rangée,Dn »], rôle)
MULTI = [
    (0x616850, 1, 2, [(0x194B54, 0x0028, 0x0030)], "noms graphiques (ID, ID+$28 selon $90(A5))"),
    (0x61B6D0, 1, 2, [(0x24F824, 0x0028, 0x0030)], "décor imposé aux combats 8/9"),
    (0x616130, 1, 2, [(0x183274, 0x0028, 0x0030)], "octet par perso, 2 rangées ($169/$15C(A5))"),
    (0x620E30, 2, 2, [(0x355304, 0x0050, 0x0060)], "mot par perso -> $6A, 2 rangées"),
    (0x623E50, 2, 3, [], "mot selon l'ID ADVERSE, 3 rangées (en l'air / accroupi / debout ; LEA $50(A0) x2)"),
    (0x61BA10, 1, 3, [(0x251FDC, 0x0050, 0x0060), (0x2520AC, 0x0050, 0x0060), (0x25240C, 0x0028, 0x0030)],
     "octet par perso, 3 rangées (ID, +$28 si $124, +$50) -> drapeaux (va 0x25243C)"),
    (0x95C700, 2, 2, [], "nom de la barre de vie : code (JP, US à +$50)"),
    (0x95C7A0, 2, 2, [], "nom de la barre de vie : x J1 (JP, US à +$50)"),
    (0x95C840, 2, 2, [], "nom de la barre de vie : x J2 (JP, US à +$50)"),
]
LEA_50 = [0x12CEF4, 0x12D134, 0x12D1CC, 0x12D400, 0x12D5E0, 0x12D6C8, 0x12D790, 0x12D88C,    # rangée US du nom : $50 -> $60
          0x3DDFD8, 0x3DE020, 0x3E28F8, 0x3E2940]                                               # rangées de 623e50
# (palier 3) rel16 de N entrées NON indexées par l'ID, prolongées par des entrées MAX (bloc_rel16(t, N + k, octets)) :
# en-tête de N + K décalages (décalages d'origine + 2K), corps recopié, blocs MAX à la suite
REL16_N = {0x683C28: (755, "répliques des dialogues Arcade (US) : répliques MAX 756-883 à la suite (N21)"),
           0x970F40: (154, "scénarios des dialogues Arcade : scénarios MAX 154-173 à la suite (N21)"),
           0x68DC72: (789, "textes de fin (2 lignes « [x] texte 0 ») : textes MAX à la suite"),
           # (palier 4) homologue d'Upper de la table arcade $81522 (acteurs de décor de classe $48, index $70, pas de 8 o
           # en $50) : 12 entrées (la 12e nulle) ; décors propres aux fins MAX (ND26_4, ND27_4, ND29_4) à la suite
           0x960180: (12, "décors de fin (classe $48, arcade $81522) : décors MAX à la suite"),
           # (2b12) « WINNER:<nom> » vertical de l'écran de victoire (index = T_616850[ID]) : entrées 48-51 = persos MAX
           0x966740: (48, "WINNER:<nom> (écran de victoire) : animations MAX 48+"),
           # (2b18) recul des types de réaction ($56 de la victime -> T_61B460 -> n° de séquence) : séquences 25-29 = types
           # 28-32 des MAX (session MAX, recul_max.s) ; 971CC0 (variante $26D) a des décalages NÉGATIFS vers les séquences
           # de 9719C0 (entrées 13-24) : zone d'avant recopiée devant la table (rel16n, « pre »)
           0x9719C0: (25, "recul : séquences par type de réaction ; 25-29 = types MAX 28-32"),
           0x971CC0: (25, "recul (variante $26D) : séquences par type ; 25-29 = types MAX 28-32")}
# rel16 à rangées (constante de rangée sur l'ID : ADDI.B #$28 -> #$30)
REL16_RANGS = [(0x97AF50, 2, [(0x40D2BC, 0x0028, 0x0030)], "textes par perso (2 rangées : $C30F, $C30E+$28) -> va 0x40E3C4")]
STRUCTS = [(0x674C00, 66, "poses des portraits"), (0x961AF0, 28, "noms / bandeaux (sprites par perso)"),
           (0x967F2A, 9, "carte du monde (Arcade) : listes 2/3 par perso (va 0x19DD20 ; $34 nul -> boucle infinie)"),
           (0x648BC8, 8, "listes d'animation par perso (3 listes de 40 x 8)")]
MOVEQ_39 = [0x17E000, 0x193324, 0x182614]   # variante Juli/Juni : place 39 -> 47 (poses x2, noms)
DEJA_48 = {0x61BE70: "positions du curseur (déjà 48 entrées)"}
LISTES_LONGUES = {(0x674C00, 3012): 0x3E}   # (2b22) poses du générique ($E/$F) : rangs jusqu'à $3D
# 967bf0 : [$00,$30) en-tête (index 2·$114+$18) ; mots par ID à $30 (+$50 si $90(A5)) ; octets par ID à $D0 (+$28) ;
# 2 paires de mots à $120/$124. Nouvelle disposition : mots $30/$90, octets $F0/$120, paires à $150.
C_967 = [(0x19CE88, 0x0640, 0x0050, 0x0060), (0x19CEC0, 0x303C, 0x00D0, 0x00F0), (0x19CF08, 0x0640, 0x0028, 0x0030),
         (0x19CF14, 0x303C, 0x0120, 0x0150)]
ZONE_TALONS = (0x370000, 0x3A0000)   # talons natifs du traducteur (ex. 0x37AF90 : ID de base -> pointeur d'animation)
AIG_VA = 0x33BC38                 # aiguillage 620630 : MOVE.B $103(A4),D0 ; ADD.W D0,D0 ; MOVE.W T(PC,D0.W),D1 ; JMP

def _selection(S):
    """(diagnostic) AG_SEL="a-b,c-d" : seules les copies d'indices listés sont branchées (lecteurs et pointeurs)"""
    v = os.environ.get("AG_SEL")
    if not v: return S
    ok = set()
    for r in v.split(","):
        a_, b_ = (r.split("-") + [r])[:2]; ok |= set(range(int(a_), int(b_) + 1))
    for k, s in enumerate(S): s["branchee"] = k in ok
    return S

def specs():
    S = []
    multi_ps2 = {m[0] for m in MULTI}
    for t in TABLES:
        p = int(t["ps2"], 16)
        if p in IGNOREES or p in PAIRES or p in multi_ps2 or p in DEJA_48: continue
        k = t["kind"]
        if k in ("simple", "code"):
            S.append(dict(ps2=p, kind="simple", e=t["e"], n=t.get("n", 40), rangs=1, refs=[0], role=t["role"][:60]))
        elif k == "rel16":
            S.append(dict(ps2=p, kind="rel16", e=2, n=40, refs=[0], role=t["role"][:60], region=t["region"],
                          suivante=int(t["suivante"], 16) if t.get("suivante") else None))
    for d, m in PAIRES.items():
        for s in S:
            if s["ps2"] == m: s["refs"].append(d - m)
    for p, e, n, r in AJOUTEES:                       # (2b22) paires aussi pour les tables ajoutées (0x616B32 = 0x616B30 + 2)
        S.append(dict(ps2=p, kind="simple", e=e, n=n, rangs=1, refs=[0] + [d - m for d, m in PAIRES.items() if m == p], role=r))
    for p, e, R, cst, r in MULTI:
        S.append(dict(ps2=p, kind="simple", e=e, n=40, rangs=R, refs=[0], cst=cst, role=r))
    for p, H, r in STRUCTS:
        S.append(dict(ps2=p, kind="struct", e=8, H=H, refs=[0], role=r))
    S.append(dict(ps2=0x967BF0, kind="967bf0", e=2, refs=[0, 2], role="mots/octets par ID à rangées (VS ?)"))
    for p, R, cst, r in REL16_RANGS:
        S.append(dict(ps2=p, kind="rel16", e=2, n=40, rangs=R, refs=[0], cst=cst, role=r, region=0, suivante=None))
    for p, (N, r) in REL16_N.items():                     # (palier 3) tables rel16 non indexées par l'ID : entrées ajoutées
        if BLOCS_REL.get(p):
            S.append(dict(ps2=p, kind="rel16n", e=2, n=N, refs=[0], role=r))
    S.sort(key=lambda s: s["ps2"])
    return _selection(S)

# ------------------------------------------------------------------------------------------------ ajouts MAX
AJ = defaultdict(dict)         # (ps2 de base de la table / de la liste, rangée) -> {i: [(décalage, octets PS2)]}
BLOCS_REL = defaultdict(dict)  # ps2 rel16 -> {i: octets du bloc (ordre PS2)}
def ajout(base, i, octets, decal=0, rang=0):
    """valeur d'un ID (>= 40, ou toute entrée de la COPIE) : octets PS2 posés sur l'entrée par défaut"""
    AJ[(base, rang)].setdefault(i, []).append((decal, bytes(octets)))
def bloc_rel16(t, i, octets):
    BLOCS_REL[t][i] = bytes(octets)

# ------------------------------------------------------------------------------------------------ construction
NOUVEAU = {}
SPECS = None
BLOB = None
def construit(data, T, orig):
    """data : données PS2 (bytearray depuis T.CODE_END_RT, écritures MAX faites) ; orig : fichier ro5 d'origine"""
    global SPECS, BLOB
    SPECS = specs()
    od = lambda a: a - T.CODE_END_RT
    oo = lambda a: a - RB
    rd = lambda a, n: bytes(data[od(a):od(a) + n])
    out = bytearray()
    def place(p, b):
        while len(out) % 4 != p % 4: out.append(0)
        a = BLOC + len(out); out.extend(b); return a
    utilises = set()
    def entree(base, e, i, r_key):
        if i < 45: ent = bytearray(rd(base + e * i, e))
        elif i < 47: ent = bytearray(rd(base, e))
        else: ent = bytearray(orig[oo(base + e * 39):oo(base + e * 39) + e])
        for dec, b in AJ.get(r_key, {}).get(i, []):
            ent[dec:dec + len(b)] = b; utilises.add(r_key + (i,))
        return ent
    def bati(s):
        p, e = s["ps2"], s["e"]
        if s["kind"] == "simple":
            nb = bytearray()
            for r in range(s["rangs"]):
                base = p + e * 40 * r
                for i in range(N48): nb += entree(base, e, i, (p, r))
            if p in PTR_REL16: nb = ptr_rel16(s, nb)
        elif s["kind"] == "rel16":
            R = s.get("rangs", 1); N = 40 * R; dl = 16 * R           # en-tête de R rangées de 40 -> 48 ; décalages + dl
            h = list(struct.unpack_from("<%dH" % N, data, od(p)))
            assert min(h) >= 2 * N and (R > 1 or min(h) == 2 * N), "rel16 %x : en-tête inattendu" % p
            fin = max(h) + 0x400
            if s.get("suivante") and s["suivante"] - p > max(h): fin = min(fin, s["suivante"] - p)
            fin = max(fin, min(s.get("region", 0), max(h) + 0x400))
            corps = bytearray(rd(p + 2 * N, fin - 2 * N))
            vieux = lambda k: struct.unpack_from("<H", data, od(p) + 2 * k)[0]   # mot k « de l'en-tête » d'origine (k >= N : données)
            nh = []
            for r in range(R):
                for i in range(N48):
                    if i < 45: nh.append((vieux(40 * r + i) + dl) & 0xFFFF)
                    elif i < 47: nh.append(vieux(40 * r) + dl)
                    else: nh.append(vieux(40 * r + 39) + dl)
            suite = bytearray()
            for i, b in sorted(BLOCS_REL.get(p, {}).items()):
                off = 2 * N48 * R + len(corps) + len(suite)
                assert off + len(b) < 0x10000, "rel16 %x : décalage > $FFFF" % p
                nh[i] = off; suite += b + bytes(len(b) & 1)
            nb = struct.pack("<%dH" % len(nh), *nh) + corps + suite
        elif s["kind"] == "rel16n":
            N = s["n"]; h = list(struct.unpack_from("<%dH" % N, data, od(p)))
            assert min(x for x in h if x) == 2 * N, "rel16 %x : en-tête inattendu (min %x, 2N %x, h0-3 %s)" % (p, min(x for x in h if x), 2 * N, h[:4])      # entrées nulles gardées nulles
            ajout = BLOCS_REL[p]; N2 = max(ajout) + 1
            assert min(ajout) == N and len(ajout) == N2 - N, "rel16 %x : entrées ajoutées non contiguës" % p
            # (2b18) décalages NÉGATIFS (u16 >= $8000 : données d'une table voisine AVANT celle-ci) : la zone [cible min, p)
            # est recopiée devant la nouvelle table, décalages négatifs inchangés
            neg = [x - 0x10000 for x in h if x >= 0x8000]
            pre = bytes(rd(p + min(neg), -min(neg))) if neg else b""
            pos = [x for x in h if x < 0x8000]
            corps = bytearray(rd(p + 2 * N, max(pos) + 0x400 - 2 * N))
            nh = [x + 2 * (N2 - N) if 0 < x < 0x8000 else x for x in h]
            suite = bytearray()
            for i in range(N, N2):
                off = 2 * N2 + len(corps) + len(suite); assert off + len(ajout[i]) < 0x10000
                nh.append(off); suite += ajout[i] + bytes(len(ajout[i]) & 1)
            nb = pre + struct.pack("<%dH" % N2, *nh) + corps + suite
            s["n2"] = N2; s["pre"] = len(pre)
        elif s["kind"] == "struct":
            H = s["H"]
            h = list(struct.unpack_from("<%dH" % H, data, od(p)))
            assert min(x for x in h if x) == 2 * H, "structure %x : en-tête inattendu" % p
            dist = sorted(set(x for x in h if x))
            listes = [o for k, o in enumerate(dist) if k + 1 < len(dist) and dist[k + 1] - o == 0x140]
            if len(dist) > 1 and dist[-1] - dist[-2] == 0x140: listes.append(dist[-1])   # dernière liste de la suite
            nb = bytearray(rd(p, max(h) + 0x180))
            neuf = {}
            for o in listes:
                neuf[o] = len(nb)
                # (2b22) listes LONGUES : pose finale du générique (0x674C00 + 3012 = listes $E/$F de l'arcade $301FA2,
                # rang = octet +3 de l'acteur, jusqu'à $3D pour la 2e pose de Yun) -> 62 entrées
                n_ = LISTES_LONGUES.get((p, o), N48)
                for i in range(n_): nb += entree(p + o, 8, i, (p + o, 0))
            nh = [neuf.get(o, o) for o in h]
            assert max(nh) < 0x10000
            struct.pack_into("<%dH" % H, nb, 0, *nh)
            s["listes"] = len(listes)
        elif s["kind"] == "967bf0":
            nb = bytearray(rd(p, 0x30))
            for base, ee in ((p + 0x30, 2), (p + 0x80, 2), (p + 0xD0, 1), (p + 0xF8, 1)):
                for i in range(N48): nb += entree(base, ee, i, (base, 0))
            assert len(nb) == 0x150
            nb += rd(p + 0x120, 0x10)
        s["nouveau"] = place(p - s.get("pre", 0), nb) + s.get("pre", 0); s["taille"] = len(nb)
        NOUVEAU[p] = s["nouveau"]
    global _construit_rel16, _DATA, _T
    _construit_rel16, _DATA, _T = bati, data, T
    for s in sorted(SPECS, key=lambda s: s["ps2"] in PTR_REL16):      # tables de pointeurs vers des rel16 : en dernier
        bati(s)
    for x in PTR_COPIES: SPECS.append(x)
    for (b, r), d in AJ.items():
        for i in d:
            assert (b, r, i) in utilises, "ajout MAX sans table agrandie : %x rangée %d entrée %d" % (b, r, i)
    for t in BLOCS_REL: assert t in NOUVEAU, "bloc rel16 sans table : %x" % t
    # pointeurs de données (PS2, alignés 4) vers le DÉBUT d'une table recopiée
    w = array.array("I", bytes(data[:len(data) & ~3]))
    cibles = {s["ps2"]: s for s in SPECS if s.get("branchee", True)}
    nptr = defaultdict(list)
    for k, v in enumerate(w):
        if v in cibles:
            nptr[v].append(T.CODE_END_RT + 4 * k)
            struct.pack_into("<I", data, 4 * k, cibles[v]["nouveau"])
    for v, L in sorted(nptr.items()): cibles[v]["ptr_donnees"] = L
    BLOB = bytes(out)
    log("tables agrandies : %d copies (%d octets) en $%x ; pointeurs de données redirigés : %s" % (
        len(SPECS), len(out), BLOC, ", ".join("%x x%d" % (v, len(L)) for v, L in sorted(nptr.items()))))
    return BLOB

# tables de POINTEURS vers des structures rel16 indexées par l'ID ADVERSE (7495b8 : [attaquant] -> en-tête de 40 décalages
# [défenseur] + données) : chaque structure pointée est recopiée agrandie (48) et la copie de la table pointe dessus
PTR_REL16 = {0x7495B8: "positions de projection : [attaquant] -> rel16 [défenseur]"}
PTR_COPIES = []
def ptr_rel16(s, nb):
    """remplace, dans la copie (48 x 4 o, PS2), chaque pointeur vers une structure rel16 par sa copie agrandie"""
    out = bytearray(nb)
    for k in range(0, len(out), 4):
        v = struct.unpack_from("<I", out, k)[0]
        if v in NOUVEAU: struct.pack_into("<I", out, k, NOUVEAU[v]); continue
        if v in _PTR_FAIT: struct.pack_into("<I", out, k, _PTR_FAIT[v]); continue
        if not (0x600000 <= v < 0xA00000): continue
        h = list(struct.unpack_from("<40H", _DATA, v - _T.CODE_END_RT))
        if min(h) != 0x50 or max(h) >= 0x8000: continue
        d = sorted(set(h)); gap = max([d[j + 1] - d[j] for j in range(len(d) - 1)] + [0x100])
        x = dict(ps2=v, kind="rel16", e=2, n=40, rangs=1, refs=[0], role="structure pointée par %x" % s["ps2"],
                 region=max(h) + gap, suivante=None)
        _construit_rel16(x)
        _PTR_FAIT[v] = x["nouveau"]; PTR_COPIES.append(x)
        struct.pack_into("<I", out, k, x["nouveau"])
    log("%x : %d structures rel16 pointées recopiées agrandies" % (s["ps2"], len(_PTR_FAIT)))
    return bytes(out)
_PTR_FAIT = {}

def ecrit(W, ext_plus):
    im = BLOB + bytes(len(BLOB) & 1)
    im = bytes(b for i in range(0, len(im), 2) for b in (im[i + 1], im[i]))
    open(os.path.join(W, "ext_%06x.bin" % BLOC), "wb").write(im)
    ext_plus.append("%06x" % BLOC)

# ------------------------------------------------------------------------------------------------ code de l'image
def _mot(img, k): return (img[k] << 8) | img[k + 1]
def lea_sites(img, lo, hi, cible):
    """sites « LEA cible.L,An » ; l'opérande peut porter l'étiquette HW_TAG ($01xxxxxx, adresses >= $400000)"""
    pat = struct.pack(">I", cible & 0xFFFFFF)[1:]
    L = []; k = img.find(pat, lo, hi)
    while k >= 0:
        o = k - 1
        if o % 2 == 0 and img[o] in (0, 1) and (_mot(img, o - 2) & 0xF1FF) in (0x41F9, 0x203C, 0x207C): L.append(o)
        k = img.find(pat, k + 1, hi)
    return L

def patch_code(img, its, T, data_base, talon):
    """après toutes les corrections de mame_test (fin()) ; talon : adresse libre (zone du code MAX) pour 620630"""
    par_va = defaultdict(list)
    for it in its: par_va[it.va].append(it)
    rapport = []
    for s in SPECS:
        a = T.addr_to_68k(s["ps2"]) & 0xFFFFFF
        n = 0
        for d in (s["refs"] if s.get("branchee", True) else []):
            for k in lea_sites(img, 0x1000, data_base, a + d) + lea_sites(img, ZONE_TALONS[0], ZONE_TALONS[1], a + d):
                struct.pack_into(">I", img, k, ((img[k] << 24) | s["nouveau"] + d)); n += 1     # étiquette gardée
        s["sites"] = n
        if n == 0 and not s.get("ptr_donnees"):
            rapport.append("%x (%s) : AUCUN lecteur trouvé" % (s["ps2"], s["role"][:40]))
        for va, ancien, nouveau in s.get("cst", []):
            ok = [it for it in par_va.get(va, []) if (_mot(img, it.off) & 0xFFF8) in (0x0640, 0x0600) and _mot(img, it.off + 2) == ancien]
            assert len(ok) == 1, "constante de rangée %x en va %x : %d sites" % (ancien, va, len(ok))
            struct.pack_into(">H", img, ok[0].off + 2, nouveau)
    for va, op, ancien, nouveau in C_967:
        msk = 0xFFF8 if op == 0x0640 else 0xF1FF
        ok = [it for it in par_va.get(va, []) if (_mot(img, it.off) & msk) == op and _mot(img, it.off + 2) == ancien]
        assert len(ok) == 1, "967bf0 : constante %x en va %x : %d sites" % (ancien, va, len(ok))
        struct.pack_into(">H", img, ok[0].off + 2, nouveau)
    for va in LEA_50:
        ok = [it for it in par_va.get(va, []) if (_mot(img, it.off) & 0xF1F8) == 0x41E8 and _mot(img, it.off + 2) == 0x50]
        assert len(ok) == 1, "LEA $50 en va %x introuvable" % va
        struct.pack_into(">H", img, ok[0].off + 2, 0x60)
    for va in MOVEQ_39:
        ok = [it for it in par_va.get(va, []) if _mot(img, it.off) == 0x7227]
        assert len(ok) == 1, "MOVEQ #39 en va %x introuvable" % va
        struct.pack_into(">H", img, ok[0].off, 0x722F)
    # aiguillage 620630 (40 mots EN LIGNE après « JMP (PC,D1.W) ») : ID >= $28 -> entrée 0
    ok = [it for it in par_va.get(AIG_VA, []) if _mot(img, it.off) == 0x102C]
    assert len(ok) == 1, "aiguillage 620630 introuvable"
    o = ok[0].off
    assert struct.unpack_from(">8H", img, o) == (0x102C, 0x0103, 0xD040, 0x323B, 0x0006, 0x4EFB, 0x1002, 0x0050), \
        "aiguillage 620630 : octets inattendus"
    tab = o + 0x0E
    w = [0x102C, 0x0103, 0x0C00, 0x0028, 0x6502, 0x4200, 0xD040, 0x2F08, 0x41F9, tab >> 16, tab & 0xFFFF,
         0x3230, 0x0000, 0x205F, 0x4E75]
    assert not any(img[talon:talon + 2 * len(w)])
    struct.pack_into(">%dH" % len(w), img, talon, *w)
    if os.environ.get("MAX_AIG620630", "1") == "1":    # (2b22, essai de bissection) 0 : aiguillage d'origine
        struct.pack_into(">5H", img, o, 0x4EB9, talon >> 16, talon & 0xFFFF, 0x4E71, 0x4E71)
    tot = sum(s["sites"] for s in SPECS)
    log("tables agrandies : %d LEA redirigés ; constantes de rangée %d (+4 de 967bf0) ; LEA $50 -> $60 : %d ; "
        "MOVEQ #39 -> #47 : %d ; aiguillage 620630 : talon $%x" % (
        tot, sum(len(s.get("cst", [])) for s in SPECS), len(LEA_50), len(MOVEQ_39), talon))
    for r in rapport: log("ATTENTION " + r)
    return talon + 2 * len(w)

def journal(W):
    with open(os.path.join(W, "max_agrandies.txt"), "w") as f:
        f.write("ps2     genre     e  copie   taille  LEA  ptr_données  rôle\n")
        for s in SPECS:
            f.write("%06x  %-7s %3d  %06x  %6d  %3d  %-12s %s\n" % (s["ps2"], s["kind"], s["e"], s["nouveau"], s["taille"],
                    s.get("sites", -1), ",".join("%x" % x for x in s.get("ptr_donnees", [])) or "-", s["role"]))

# ------------------------------------------------------------------------------------------------ recensement (analyse)
def plage(t):
    e = t["e"]; n = t["n"]
    if t["kind"] == "rel16": return t["region"]
    if t["kind"] == "multi": return 2 * 40 * e
    return n * e

def recense(img, its, T, data, code_max, code_org, W):
    E = []
    for t in TABLES:
        p = int(t["ps2"], 16); a = T.addr_to_68k(p) & 0xFFFFFF
        E.append((a, a + plage(t), p, t))
    E.sort()
    deb = [x[0] for x in E]
    def cherche(v):
        k = bisect.bisect_right(deb, v) - 1
        if k >= 0 and E[k][0] <= v < E[k][1] + 8: return E[k]
        if k + 1 < len(E) and E[k + 1][0] - 8 <= v < E[k + 1][0]: return E[k + 1]
        return None
    R = defaultdict(list); BRUIT = defaultdict(int)
    P = [(p, p + plage(t), t) for _, _, p, t in E]; P.sort(); dp = [x[0] for x in P]
    offs = [it.off for it in its]
    def instr(k):
        i = bisect.bisect_right(offs, k) - 1
        return its[i] if i >= 0 else None
    for k in range(0x1000, T.DATA_BASE - 3, 2):
        v = ((img[k] << 24) | (img[k + 1] << 16) | (img[k + 2] << 8) | img[k + 3]) & 0xFFFFFF
        if v < 0x80000: continue
        x = cherche(v)
        if not x: continue
        it = instr(k)
        op = (img[k - 2] << 8) | img[k - 1]
        if (op & 0xF1FF) not in (0x41F9, 0x207C, 0x203C): BRUIT[x[2]] += 1; continue
        R[x[2]].append("code %06x op %04x (instr %06x %s) [%+d]" % (k, op, it.off if it else 0, (it.mn[:40] if it else "?"), v - x[0]))
    for k in range(0, len(code_max) - 3, 2):
        v = struct.unpack_from(">I", code_max, k)[0] & 0xFFFFFF
        if v < 0x80000: continue
        x = cherche(v)
        if x: R[x[2]].append("codeMAX %06x [%+d]" % (code_org + k, v - x[0]))
    base = T.CODE_END_RT
    w = array.array('I', bytes(data[:len(data) & ~3]))
    for k, v in enumerate(w):
        if v < 0x600000 or v > 0xA00000: continue
        i = bisect.bisect_right(dp, v) - 1
        if i >= 0 and P[i][0] <= v < P[i][1] + 8:
            R[P[i][0]].append("donnée %06x [%+d]" % (base + 4 * k, v - P[i][0]))
    with open(os.path.join(W, "agrandi_recensement.txt"), "w") as f:
        for a0, a1, p, t in sorted(E, key=lambda x: x[2]):
            L = R[p]
            f.write("table %06x (68K %06x) %s e=%d n=%d : %d réf. (bruit %d)\n" % (p, a0, t["kind"], t["e"], t["n"], len(L), BRUIT[p]))
            for l in L: f.write("   " + l + "\n")
    print("MAX : recensement des références des %d tables -> agrandi_recensement.txt" % len(E))
