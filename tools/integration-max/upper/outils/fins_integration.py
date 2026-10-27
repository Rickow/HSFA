"""(agent_integration_max) PALIER 3 — fins des persos MAX : sources vasm (DONNÉES, disposition IMAGE) des scripts et des
acteurs de fin (session MAX : converti/plXX/fin/script_fin_XX.s, acteurs_fin_XX.s, format ARCADE) et blocs de textes.
  * script (interpréteur de fin) : mots -> tels quels (mot = même valeur dans l'image) ; TEXTE_FIN_XX = n° global du
    premier texte du perso dans la table des textes de fin d'Upper (0x68DC72, agrandie : textes MAX à la suite) ;
  * acteurs (enregistrements de 32 o) : octets 0-7 et $18-$1F échangés par paire (octets lus en XOR 1), mots 8-$17
    tels quels ; décalages de groupes et $FFFF tels quels.
Textes : textes.json [scenario_et_fin] (k-ième opcode texte du script = k-ième entrée), 2 lignes « [x] texte 0 »."""
import os, re, json, struct
import sys as _sy; _sy.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "untranspile"))
import max_cache as MC
CV = MC.CV
T_TEXTES = 0x68DC72; RB = 0x1F0000
FICHIER_RO5 = "<workspace>/anthology_extract/decompressed/ro5_usa_prog68k.bin"

def n_textes():
    b = open(FICHIER_RO5, "rb").read()
    return struct.unpack_from("<H", b, T_TEXTES - RB)[0] // 2

def bloc_texte(t):
    L = t["lignes"][:2]
    if len(L) == 1: L = L + [{"x": L[0]["x"], "texte": " "}]
    out = bytearray()
    for l in L:
        s = l["texte"].encode("ascii", "replace").replace(b"?", b"?")
        out += bytes([l["x"] & 0xFF]) + s + b"\0"
    return bytes(out)

def acteurs_image(src):
    o = []
    for l in src.split("\n"):
        m = re.match(r"^(\s*dc\.b\s+)([^;]+?)\s*(;.*)?$", l)
        if m:
            b = [x.strip() for x in m.group(2).split(",")]
            assert len(b) == 32, l
            for k in list(range(0, 8, 2)) + list(range(0x18, 0x20, 2)):
                b[k], b[k + 1] = b[k + 1], b[k]
            l = m.group(1) + ", ".join(b) + ("  " + m.group(3) if m.group(3) else "")
        o.append(l)
    return "\n".join(o)

# corrections des scripts (session MAX, 17/10 : les x9 « 0904 » ont gardé un n° de jeu de palettes PSP) :
# (perso, ligne d'origine, remplacement ou None = supprimée) ; MAX_FIN_X9=0 : sans (contrôle)
CORR_SCRIPT = {"26": [("        dc.w    $0000, $0904, $0004, $0006, $0000, $0008",
                       "        dc.w    $0000, $0904, $0004, $0016, $0000, $0008")]}   # jeu PSP 6 d'Eagle = x9 final de Zangief
# (palier 4, session MAX 18/10 nuit) x9 PSP (dest, jeu k, f, n) = palettes 8k+f… de palettes_fin_cps2.bin : un jeu NEUF par
# jeu PSP k employé, descripteur [source n° 13, mot du perso, 32·8k, 8] ; jeux ajoutés à la suite de ceux du modèle
JEUX_PSP = {"26": [0], "27": [0, 1], "2d": [0], "2e": [0]}
# (18/10 nuit, 3, session MAX) une scène (x11 « 1108 », chargeur $26710) charge 4 jeux : a5 -> OBJ (30 palettes en +$000),
# a6-a8 -> scroll1-3 (plans : jeux du MODÈLE, inchangés). Seul a5 change : jeu neuf « OBJ k » [$34, n, 32·8k, 30] ; k = jeu
# PSP de la scène, dans l'ordre des 1108 du script. Le x9 initial est retiré (écrasé par chaque scène) ; le x9 final d'Eagle
# garde $16 ; les autres x9 (Maki, jeu 1) -> jeu neuf k
K_1108 = {"26": [1, 0, 3, 3, 3, 3, 0, 1, 1, 0, 0, 0], "27": [0] * 5, "2d": [0] * 8 + [1], "2e": [0, 0, 1, 1, 1, 2, 2, 2]}
NB_OBJ = 30
RX_1108 = re.compile(r"^(        dc\.w    \$[0-9a-f]{4}, \$1108, (?:\$[0-9a-f]{4}, ){4})\$([0-9a-f]{4})(, .*)$", re.M)
def jeux_k(pid):
    """jeux PSP k employés (scènes 1108 + x9 autres que l'initial et le final d'Eagle)"""
    return sorted(set(K_1108.get(pid, [])) | set(k for k in JEUX_PSP.get(pid, []) if k))
RX_X9 = re.compile(r"^(        dc\.w    \$[0-9a-f]{4}, \$0904, \$0004, )\$([0-9a-f]{4})(, \$0000, \$0008)$", re.M)

# (18/10 nuit, 5, session MAX) IMAGES DE PALETTES prêtes : converti/plXX/fin/jeux_palettes_cps2.bin (images de 32
# palettes CPS2, 1024 o) + jeux_palettes.json (événements du script -> n° d'image). Jeux neufs par image i :
# S_i = [$34, n, $400·i, 30] (scènes 1108 : a5) et P_i = [$34, n, $400·i, 32] (x9 « $0904, 4, P_i, 0, $20 » ajouté après
# chaque x5 et x9 finaux) ; x9 initial retiré. Maki : a6-a8 -> jeu NOIR (image de zéros) pour un fond noir.
PL_FIN = {"26": "pl26", "27": "pl27", "2d": "pl28", "2e": "pl29"}
NOIR = {"27"}
RX_X5 = re.compile(r"^        dc\.w    \$[0-9a-f]{4}, \$1505, .*$")
def images_fin(pid):
    f = CV + "%s/fin/jeux_palettes.json" % PL_FIN.get(pid, "")
    if not P4 or not os.path.exists(f): return None
    return json.load(open(f))
def corrige_images(pid, s, J):
    n0 = len(jeux_modele(JEU_NEUF[pid][0])); ni = len(J["images"])
    S = lambda i: n0 + 2 * i; P = lambda i: n0 + 2 * i + 1; NR = n0 + 2 * ni
    ev = J["evenements"]
    sc = [e for e in ev if e["op"] == "scene"]; x5 = [e for e in ev if e["op"] == "x5"]; x9 = [e for e in ev if e["op"] == "x9"]
    out = []; i9 = i5 = isc = 0
    for l in s.split("\n"):
        if RX_X9.match(l) or re.match(r"^        dc\.w    \$[0-9a-f]{4}, \$0904, ", l):
            e = x9[i9]; i9 += 1
            if i9 == 1:
                out.append("; (agent_integration_max) x9 initial retiré (chaque scène recharge OBJ) : " + l.strip()); continue
            d = re.match(r"^        dc\.w    (\$[0-9a-f]{4}), ", l).group(1)
            out.append("        dc.w    %s, $0904, $0004, $%04x, $0000, $001E  ; (agent_integration_max) x9 -> image %d (30 palettes : OBJ 30-31 = texte)" % (d, P(e["image"]), e["image"]))
            continue
        m = RX_1108.match(l)
        if m:
            e = sc[isc]; isc += 1
            reste = m.group(3)
            if pid in NOIR:
                reste = ", $%04x, $%04x, $%04x" % (NR, NR, NR)
            out.append(m.group(1) + "$%04x" % S(e["image"]) + reste + "  ; (agent_integration_max) a5 (OBJ) -> image %d%s" % (e["image"], " ; a6-a8 -> jeu noir" if pid in NOIR else ""))
            continue
        out.append(l)
        if RX_X5.match(l):
            e = x5[i5]; i5 += 1
            out.append("        dc.w    $0000, $0904, $0004, $%04x, $0000, $001E  ; (agent_integration_max) après x5 : image %d (30 palettes)" % (P(e["image"]), e["image"]))
    assert (isc, i5, i9) == (len(sc), len(x5), len(x9)), "script %s : scènes %d/%d, x5 %d/%d, x9 %d/%d" % (pid, isc, len(sc), i5, len(x5), i9, len(x9))
    return "\n".join(out)

RX_OPA = re.compile(r"^(        dc\.w    \$[0-9a-f]{4}, \$0a02, \$[0-9a-f]{4}, )\$([0-9a-f]{4})$", re.M)
def corrige_script(pid, s):
    # (session MAX, 18/10) opA « $0a02, a, b » : sur arcade b = VITESSE ajoutée à chaque image aux Y des 4 plans ($2643E) ;
    # la PSP y met un décalage fixe (valeurs $FFC0 / $FFD0 gardées) -> plans qui défilent : b = 0
    if os.environ.get("MAX_FIN_OPA") != "0":
        s, k_ = RX_OPA.subn(lambda m: m.group(1) + "$0000  ; (agent_integration_max) opA : vitesse PSP $%s -> 0" % m.group(2), s)
    # (2b12) opcode texte $0034 : 2e argument = style de fenêtre du MODÈLE (Zangief $10 et $06 : 1 ; Ryu / Guy : $10). Les
    # scripts MAX gardent $10 partout -> fenêtre en rectangle MAGENTA sur les fins à modèle $10 / $06 (relevé 2b12)
    if os.environ.get("MAX_FIN_TEXTE_STYLE", "0") == "1" and pid in JEU_NEUF and JEU_NEUF[pid][0] in (0x10, 0x06):
        s = re.sub(r"(\$0034, )\$0010,", r"\g<1>$0001,", s)
    if os.environ.get("MAX_FIN_X9") == "0": return s
    J = images_fin(pid)
    if J is not None and pid in JEU_NEUF: return corrige_images(pid, s, J)
    for av, ap in CORR_SCRIPT.get(pid, []):
        assert s.count(av + "\n") == 1, "script %s : ligne introuvable %r" % (pid, av)
        s = s.replace(av + "\n", "" if ap is None else ap + "  ; (agent_integration_max) x9 corrigé (session MAX)\n")
    if pid in K_1108 and pid in JEU_NEUF:
        n0 = len(jeux_modele(JEU_NEUF[pid][0])); ks = jeux_k(pid)
        lignes = s.split("\n")
        for i, l in enumerate(lignes):                  # x9 initial (1re ligne d'x9, jeu PSP 0) : retiré
            if RX_X9.match(l):
                assert int(RX_X9.match(l).group(2), 16) == 0, "script %s : x9 initial inattendu" % pid
                lignes[i] = "; (agent_integration_max) x9 initial retiré (chaque scène 1108 recharge OBJ) : " + l.strip(); break
        s = "\n".join(lignes)
        def r(m):
            k = int(m.group(2), 16)
            return m.group(1) + "$%04x" % (n0 + ks.index(k)) + m.group(3) + "  ; (agent_integration_max) x9 jeu PSP %d -> OBJ %d" % (k, k)
        s = RX_X9.sub(r, s)
        it = iter(K_1108[pid]); nb = [0]
        def r2(m):
            k = next(it); nb[0] += 1
            return m.group(1) + "$%04x" % (n0 + ks.index(k)) + m.group(3) + "  ; (agent_integration_max) a5 (OBJ) -> jeu neuf PSP %d (a5 d'origine $%s)" % (k, m.group(2))
        s = RX_1108.sub(r2, s)
        assert nb[0] == len(K_1108[pid]), "script %s : %d scènes 1108, %d attendues" % (pid, nb[0], len(K_1108[pid]))
    return s

# JEU DE PALETTES NEUF (fin $26 : invités Guile = 4, Charlie = 5 ; session MAX, 17/10) : source n° 13 de la table des
# sources de palettes d'Upper (0x60B560, entrée 0x60B594 libre ; s > 8 -> source + mot[n]) = palettes PSP 0-7 de
# palettes_fin_cps2.bin ; jeu 24 = [s $34, n 0, déc 0, nb 8] ajouté à la liste des jeux du modèle (Zangief : 24 jeux)
# (palier 4) décors des fins MAX dans la table de classe $48 d'Upper (0x960180, homologue de l'arcade $81522, 12 entrées) :
# n° = rang ajouté ; 1er pas (decor_fin_<perso>.s, decor_nouveaux_max.md)
ND_81522 = {"ND26_4": 12, "ND27_4": 13, "ND29_4": 14}
ND_PAS = {"ND26_4": "P8_26_0", "ND27_4": "P8_27_0", "ND29_4": "P8_29_0"}
JEU_NEUF = {"26": (0x10, 0, 20), "27": (0x07, 0, 20), "2d": (0x06, 0, 20), "2e": (0x10, 0, 20)}      # (palier 4 : palettes relatives 0-19 du bloc de fin, invités compris)       # perso -> (fin modèle, 1re palette PSP, nombre)
P4 = os.environ.get("MAX_P4", "1") == "1"          # (palier 4) 0 : état du palier 3 (lot 2b6) pour les fins
if not P4:
    JEU_NEUF = {"26": (0x10, 0, 8)}
    CORR_SCRIPT = {"26": [("        dc.w    $0000, $0904, $0004, $0000, $0000, $0008", "        dc.w    $0000, $0904, $0004, $0018, $0000, $0008"),
                          ("        dc.w    $0000, $0904, $0004, $0006, $0000, $0008", "        dc.w    $0000, $0904, $0004, $0016, $0000, $0008")],
                   "27": [("        dc.w    $0000, $0904, $0004, $0000, $0000, $0008", None)],
                   "2d": [("        dc.w    $0000, $0904, $0004, $0000, $0000, $0008", None)],
                   "2e": [("        dc.w    $0000, $0904, $0004, $0000, $0000, $0008", None)]}
    ND_81522 = {}
    JEUX_PSP = {}
    K_1108 = {}

T_PAL_FIN = 0x60B5A0
def jeux_modele(m):
    """liste des jeux de palettes de la fin m (0x60B5A0[m]) : pointeurs PS2"""
    import struct as st
    b = open(FICHIER_RO5, "rb").read()
    lst = st.unpack_from("<I", b, T_PAL_FIN + 4 * m - RB)[0]
    old = []
    while True:
        v = st.unpack_from("<I", b, lst - RB + 4 * len(old))[0]
        if not (0x900000 <= v < 0xA00000): break
        old.append(v)
    return old

JEU_RANG = []
def jeu_palettes(pid, pl):
    """données FIN<pid>_PAL_DONNEES = palettes_fin_cps2.bin entier ; source n° 13 PARTAGÉE (FINMAX_PAL_SRC, s > 8 :
    A4 = source + mot[n], n = 2 × rang du perso) ; un jeu neuf [$34, n, 32·8k, 8] par jeu PSP k ; liste = jeux du modèle
    + jeux neufs"""
    if pid not in JEU_NEUF: return []
    import struct as st
    m = JEU_NEUF[pid][0]
    old = jeux_modele(m); JEU_RANG.append(pid); n = 2 * (len(JEU_RANG) - 1)
    J = images_fin(pid)
    if J is not None:                                  # images de palettes prêtes (session MAX)
        img = open(CV + "%s/fin/jeux_palettes_cps2.bin" % pl, "rb").read(); ni = len(img) // 1024
        assert ni == len(J["images"]), "fin %s : %d images, %d dans le json" % (pid, ni, len(J["images"]))
        if pid in NOIR: img += bytes(1024)
        L = ["        even", "; ---- fin $%s : %d images de palettes (session MAX) ; jeux neufs S_i / P_i en %d.. après les jeux du modèle $%02X"
             % (pid, ni, len(old), m), "FIN%s_PAL_DONNEES:" % pid]
        for k in range(len(img) // 32):
            L.append("        dc.w    " + ", ".join("$%04x" % w for w in st.unpack_from("<16H", img, 32 * k)))
        noms = []
        for i in range(ni):
            L += ["FIN%s_PAL_S%d:" % (pid, i), "        dc.w    $34, %d, $%x, 30" % (n, 0x400 * i),
                  "FIN%s_PAL_P%d:" % (pid, i), "        dc.w    $34, %d, $%x, 32" % (n, 0x400 * i)]
            noms += ["FIN%s_PAL_S%d" % (pid, i), "FIN%s_PAL_P%d" % (pid, i)]
        if pid in NOIR:
            L += ["FIN%s_PAL_NOIR:" % pid, "        dc.w    $34, %d, $%x, 32" % (n, 0x400 * ni)]; noms.append("FIN%s_PAL_NOIR" % pid)
        L += ["        even", "FIN%s_PAL_LISTE:" % pid]
        for v in old: L.append("        dc.w    $%04x, $%04x" % (v & 0xFFFF, v >> 16))
        for x in noms: L.append("        dc.w    (%s)&$ffff, (%s)>>16" % (x, x))
        return L
    pal = open(CV + "%s/fin/palettes_fin_cps2.bin" % pl, "rb").read()
    ks = jeux_k(pid) if pid in K_1108 else JEUX_PSP.get(pid, [0])
    L = ["        even", "; ---- fin $%s : %d palettes de fin MAX ; jeux neufs %s (jeux PSP %s) après les %d jeux du modèle $%02X"
         % (pid, len(pal) // 32, list(range(len(old), len(old) + len(ks))), ks, len(old), m), "FIN%s_PAL_DONNEES:" % pid]
    for k in range(len(pal) // 32):
        L.append("        dc.w    " + ", ".join("$%04x" % w for w in st.unpack_from("<16H", pal, 32 * k)))
    nbo = NB_OBJ if pid in K_1108 else 8
    for k in ks: L += ["FIN%s_PAL_JEU%d:" % (pid, k), "        dc.w    $34, %d, $%x, %d" % (n, 0x100 * k, nbo)]
    L += ["        even", "FIN%s_PAL_LISTE:" % pid]
    for v in old: L.append("        dc.w    $%04x, $%04x" % (v & 0xFFFF, v >> 16))      # longs en moitiés échangées
    for k in ks: L.append("        dc.w    (FIN%s_PAL_JEU%d)&$ffff, (FIN%s_PAL_JEU%d)>>16" % (pid, k, pid, k))
    return L

def jeu_source_max():
    """source n° 13 partagée : un mot (décalage depuis la source) par fin à jeu neuf, dans l'ordre de JEU_RANG"""
    if not JEU_RANG: return []
    return ["        even", "FINMAX_PAL_SRC:"] + ["        dc.w    FIN%s_PAL_DONNEES-FINMAX_PAL_SRC" % p for p in JEU_RANG]

def prologue_image(src):
    """prologue_max.s (session MAX) -> disposition IMAGE : en-tête de mots tel quel ; pages = flux d'octets lu par Upper en
    XOR 1 (ordre PS2) -> octets échangés par paire, étiquettes PM_n = PM_DONNEES + décalage logique ; listes omises
    (posées dans la table 0x960090 par integre_max.prologue)"""
    entete, flux, off, cur = [], bytearray(), {}, None
    for l in src.split("\n"):
        m = re.match(r"^(PM_\d+):", l)
        if m: cur = m.group(1); off[cur] = len(flux); continue
        if l.startswith("PROLOGUE_MAX_"): cur = None; continue
        m = re.match(r"^\s*dc\.b\s+([^;]+)", l)
        if m and cur: flux += bytes(int(x.strip().lstrip("$"), 16) for x in m.group(1).split(",")); continue
        if re.match(r"^\s*dc\.w\s+PM_", l) or l.startswith("PROLOGUE_MAX:"): entete.append(l)
    flux += bytes(len(flux) & 1)
    sw = bytes(b for i in range(0, len(flux), 2) for b in (flux[i + 1], flux[i]))
    L = ["        even", "; ---- prologue de l'Arcade des persos MAX (session MAX : prologue_max.s ; pages en ordre PS2)"] + entete
    L.append("PM_DONNEES:")
    for i in range(0, len(sw), 32): L.append("        dc.b    " + ", ".join("$%02x" % b for b in sw[i:i + 32]))
    L += ["%s equ PM_DONNEES+%d" % (k, v) for k, v in off.items()] + ["        even"]
    return L

def prepare(out, persos):
    """persos : [(id, pl, suffixe)] ; -> (lignes vasm, {id: {textes: [blocs], script: bool, acteurs: bool}})"""
    L = []; info = {}; base = n_textes()
    for pid, pl, suf in persos:
        d = CV + "%s/fin/" % pl
        I = info[pid] = {"script": False, "acteurs": False, "textes": []}
        sf = d + "script_fin_%s.s" % suf
        if os.path.exists(sf):
            s = open(sf).read()
            T = json.load(open(CV + "%s/textes.json" % pl))["scenario_et_fin"]
            k = max([int(x) for x in re.findall(r"TEXTE_FIN_%s\+(\d+)" % suf, s)] + [-1]) + 1
            assert k <= len(T), "%s : %d textes demandés, %d fournis" % (pl, k, len(T))
            I["textes"] = [bloc_texte(t) for t in T[:k]]; I["texte0"] = base; base += k
            L += ["        even", "TEXTE_FIN_%s equ %d" % (suf, I["texte0"]),
                  "; ---- fin $%s : script (session MAX : script_fin_%s.s, %d textes en %d-%d)" % (pid, suf, k, I["texte0"], base - 1)]
            s = corrige_script(pid, s)
            L += jeu_palettes(pid, pl); I["jeu_neuf"] = pid in JEU_NEUF
            L.append(s.replace("FIN%s_SCRIPT" % suf, "FIN%s_SCRIPT" % pid) if suf != pid else s)
            I["script"] = True
        af = d + "acteurs_fin_%s.s" % suf
        if os.path.exists(af) and (os.environ.get("MAX_FIN_ACTEURS") == "1" or os.environ.get("MAX_FINS") == "1"):
            s = acteurs_image(open(af).read())
            if suf != pid: s = s.replace("FIN%s_ACTEURS" % suf, "FIN%s_ACTEURS" % pid)
            # décors propres à la fin (ND<fin>_<n° PSP> = rang de l'entrée ajoutée aux tables globales de décor) : palier 4 ;
            # en attendant, n° 0 de la table (PROVISOIRE : le décor affiché n'est pas le bon)
            nd = sorted(set(re.findall(r"\bND[0-9a-f]{2}_\d+\b", s)))
            L += ["        even", "; ---- fin $%s : acteurs (session MAX : acteurs_fin_%s.s, disposition IMAGE)" % (pid, suf)]
            L += ["%s equ %d   ; (agent_integration_max) %s" % (n, ND_81522[n], "décor MAX ajouté à la table 0x960180 (arcade $81522)")
                  if n in ND_81522 else "%s equ 0   ; (agent_integration_max) PROVISOIRE : décor de fin au palier 4" % n for n in nd]
            L += [s]
            I["acteurs"] = True; I["nd_provisoires"] = [n for n in nd if n not in ND_81522]
            I["nd_81522"] = {n: (ND_81522[n], ND_PAS[n]) for n in nd if n in ND_81522}
    L += jeu_source_max()
    # (palier 4) PLANS VIDES des fins MAX (session MAX, 18/10 nuit) : les images des fins MAX sont des sprites FD.. ;
    # le seul x6 des 4 scripts (« $0603, 0, 1, 2 ») prend les entrées 0/1/2 de la liste de plans (0x60B700[ID]) :
    # scroll1 = 4 blocs, scroll2 = 16 blocs, scroll3 = 64 blocs -> blocs transparents (scroll1/2 : 0 ; scroll3 : $4E,
    # bloc de fond des listes d'Upper) ; même valeur dans chaque sous-liste (disposition image sans effet)
    if P4 and any(v.get("script") for v in info.values()):
        L += ["        even", "FIN_PLANS_VIDES:", "        dc.w    $0008, $000c, $001c, $0000",
              "        dcb.b   4, $00", "        dcb.b   16, $00", "        dcb.b   64, $4e", "        even"]
    # BIO : textes du prologue (session MAX : converti/prologue_max.s ; réserve PROLOGUE_MAX + listes PROLOGUE_MAX_xx)
    pf = CV + "prologue_max.s"
    if os.path.exists(pf): L += prologue_image(open(pf).read())
    json.dump({k: dict(v, textes=[t.hex() for t in v["textes"]]) for k, v in info.items()},
              open(os.path.join(out, "fins_max.json"), "w"), indent=1)
    return L
