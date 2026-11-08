#!/usr/bin/env python3
"""extrait_sfa2.py — décors de Street Fighter Alpha 2 / Zero 2 (SFA2) extraits de l'ISO de l'Anthology (USA, SLUS-21317).

Aucune ROM d'arcade : tout vient de X_DATA.BIN (méthode et lecture de l'ISO reprises de decors_sfa1/extrait_sfa1.py)
  - e224 = module ro2 (« zero2_usa.bin », MWo3) : tables de décor rangées par le recompilateur selon le modèle typé
    (octets tels quels, mots en petit-boutiste « w », longs en petit-boutiste « l ») ; adresses EXEC (= fichier +
    0x1F0000) de la carte ci-dessous (outils/localise_ro2.py, contrôle par l'arcade sfa2u) ;
  - e227 = mémoire de tuiles de décor de ro2 (MWo3, pixels 4 bits linéaires, quartet bas = pixel de gauche) :
      scroll1 : tuile 8×8 de code local c = octets 32c..32c+31 (le code des cellules du module, sans ajout) ;
      scroll2 : tuile 16×16 de code de bloc c = octets 128(c + $3600) ;
  - e226 = conteneur GFX du quart 1 de la ROM SFA2 (anthgfx) : scroll3, tuile 32×32 de code de bloc c = élément c + $900
    (identique au pixel à la ROM graphique de sfa2u : 2 287 / 2 287).
Les modules ro4 / ro6 / ro8 (Zero 2 Alpha, Alpha 2 Gold, SFA2 occidental) ont les mêmes tables (--comparer).

Sorties (dossier --sortie, données de jeu : à garder hors de tout dépôt) :
  sfa2_decors.json   par décor : types, listes s1/s2/s3, palettes (mots 0RGB tels que rangés), palettes des sprites de
                     décor, CPS-B, musique, objets ; table perso -> décor ; union des blocs et des tuiles ; constantes du
                     moteur (parallaxe, mesurée dans MAME : mame/ et RAPPORT §3)
  bib_s1.bin, cel_s1.bin, bib_s2.bin, bib_s3.bin   bibliothèques (ordre arcade, grand-boutiste) : bloc s1 = 64 mots
                     (n° de cellule), cellule = 16 × (code, attr), bloc s2 = 256 × (code, attr), s3 = 64 ×
  pixels_s1.npy (codes 8×8 0..max), pixels_s2.npy (codes de bloc lo2..hi2), pixels_s3.npy (lo3..hi3)
  sfa2_plans.bin     tuiles des plans au format de la ROM graphique de MAME / FBNeo (hsfa_gfx.encode), dédoublonnées
                     et renumérotées (codes « famille SFA2 ») ; renum.json = code d'origine -> code famille
  extraction.txt     journal (empreintes, tailles)

Usage : extrait_sfa2.py --iso SFA_Anthology.iso --sortie donnees/ [--xdata X_DATA.BIN] [--comparer]"""
import os, sys, json, struct, hashlib, argparse
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ICI)
from xdata import XData, Echec
sys.path.insert(0, os.environ.get("HSFA_SRC", "<workspace>/github/src/hsfa"))
import anthgfx

EXEC = 0x1F0000
N = 20                      # 18 décors de persos + 2 spéciaux ($24 intro, $26 falaise)
PERSOS = ["Ryu", "Ken", "Akuma", "Charlie", "Chun-Li", "Adon", "Sodom", "Guy", "Birdie", "Rose", "M.Bison", "Sagat",
          "Dan", "Sakura", "Rolento", "Dhalsim", "Zangief", "Gen", "intro ($24)", "falaise ($26)"]
MODULES = {"ro2": 224, "ro4": 348, "ro6": 526, "ro8": 543}

# ---- carte des tables dans ro2 (outils/localise_ro2.py -> carte_ro2.json ; adresses arcade sfa2u entre parenthèses)
CARTE = {
    "types_s1": 0x5620C0,   # ($1CFC4) 20 mots w : 0 statique (4 blocs), 2 (8), 4 (16), 6 (12)
    "ofs_s1":   0x5620F0,   # ($1CFF4) 20 mots signés w ; liste = table + décalage, octets tels quels
    "types_s2": 0x5621B8,   # ($1D0BC) tous 0
    "ofs_s2":   0x5621E8,   # ($1D0EC) liste 16 octets (4 × 4 blocs de 256 px)
    "types_s3": 0x562370,   # ($1D274) tous 0
    "ofs_s3":   0x5623A0,   # ($1D2A4) liste 64 octets (8 × 8 blocs)
    "bib_s1":   0x4E1220,   # ($2AD300) bloc = 64 mots w (n° de cellule, colonne d'abord)
    "cel_s1":   0x4E59A0,   # ($2B1A80) cellule = 16 longs l (code << 16 | attr), 4 × 4 tuiles 8×8 colonne d'abord
    "bib_s2":   0x505E20,   # ($2D1F00) bloc = 256 longs l ; blocs ≥ 58 renumérotés par le portage (codes de e227)
    "bib_s3":   0x52D620,   # ($2F8700) bloc = 64 longs l
    "pal_spr":  0x53CF40,   # ($275C40 + $E0 n) 7 palettes de sprites de décor (-> palettes 0-6), w
    "pal_s1":   0x5434C0,   # ($27C1C0 + $400 n) 32 palettes, w
    "pal_s2":   0x54D8C0,   # ($2865C0 + $400 n)
    "pal_s3":   0x557CC0,   # ($2909C0 + $400 n)
    "cpsb":     0x4CBFB0,   # ($1C34A) 2 mots w par décor : contrôle des plans (sans les bits d'activation), priorités
    "musique":  0x4CC870,   # ($154EE) mots w
    "perso_decor": 0x4CFBB0,  # ($7A7A) octets tels quels (32 entrées)
    "objets":   0x728780,   # ($1EB66 décalages + $1EC80 enregistrements de 16 o), rangement w de toute la zone ;
                            # décalages relatifs à la table ; fin = 1er octet (grand-boutiste) ≥ $80
}
LONG_S1 = {0: 4, 2: 8, 4: 16, 6: 12}
# VARIANTES « ALPHA » (option --variantes-alpha, ABANDONNÉE par décision de l'utilisateur du 03/11 : une seule version, ro2,
# pour ZERO 2 et ALPHA, car les différences sont hors champ — RAPPORT §1.3 ; gardée pour la preuve et pour l'avenir)
# (première décision, 03/11 : fidèle) : les versions ALPHA d'Hyper prennent les décors de
# ro4 / ro6 (Zero 2 Alpha / Alpha 2 Gold) ; ils ne diffèrent de ro2 que par les LISTES de blocs de Dan, Sakura et Gen
# (mêmes bibliothèques, mêmes tuiles, mêmes palettes : compare_versions.py). Numéros proposés hors des plages prises :
# réserve « autres variantes » $96-$9E de la règle D4.
VARIANTES = {12: "$96", 13: "$98", 17: "$9A"}      # décor SFA2 -> numéro $100 de la variante ALPHA
ADD_S2_LOCAL, ADD_S3_LOCAL = 0x3600, 0x900

class Ro:
    def __init__(self, d): self.d = d
    def o(self, ex): return ex - EXEC
    def w(self, ex): return struct.unpack_from("<H", self.d, self.o(ex))[0]
    def sw(self, ex): return struct.unpack_from("<h", self.d, self.o(ex))[0]
    def octets(self, ex, n): return bytes(self.d[self.o(ex):self.o(ex) + n])
    def mots_be(self, ex, n):
        b = self.octets(ex, n); return b"".join(b[i:i + 2][::-1] for i in range(0, n, 2))
    def longs_be(self, ex, n):
        b = self.octets(ex, n); return b"".join(b[i:i + 4][::-1] for i in range(0, n, 4))

def liste(R, plan, s):
    t = R.w(CARTE["types_s%d" % plan] + 2 * s)
    n = LONG_S1[t] if plan == 1 else (16 if plan == 2 else 64)
    tab = CARTE["ofs_s%d" % plan]
    # octets tels quels (comme les listes de ro1 ; vérifié contre sfa2u, compare_versions.py)
    return t, list(R.octets(tab + R.sw(tab + 2 * s), n))

def lit_decors(R):
    res = []
    for s in range(N):
        d = dict(decor=s, val="$%02X" % (2 * s), d4=("$%02X" % (0x50 + 2 * s)) if s < 18 else None, perso=PERSOS[s])
        for p in (1, 2, 3):
            d["type_s%d" % p], d["liste_s%d" % p] = liste(R, p, s)
            d["pal_s%d" % p] = R.mots_be(CARTE["pal_s%d" % p] + 0x400 * s, 0x400).hex()
        d["pal_spr"] = R.mots_be(CARTE["pal_spr"] + 0xE0 * s, 0xE0).hex()
        d["cpsb"] = ["$%04X" % R.w(CARTE["cpsb"] + 4 * s), "$%04X" % R.w(CARTE["cpsb"] + 4 * s + 2)]
        d["musique"] = "$%02X" % R.w(CARTE["musique"] + 2 * s)
        a = CARTE["objets"] + R.w(CARTE["objets"] + 2 * s); objs = []
        while True:
            r = R.mots_be(a, 16)
            if r[0] >= 0x80: break
            x, y, g, g5, rout = struct.unpack_from(">HHBBH", r, 0)
            objs.append(dict(x=x, y=y, groupe=g, o5=g5, routine="$%04X" % rout, brut=r.hex())); a += 16
        d["objets"] = objs
        res.append(d)
    # listes scroll2 plus longues que 16 o (écart jusqu'à la liste suivante ≥ 32) : grille de 4 × 8 blocs ; Akuma : la
    # 2e disposition (rangée 7 : blocs 128-130), affichée par le gestionnaire de scroll2 (registre Y animé), RAPPORT §5
    tab = CARTE["ofs_s2"]; ofs = sorted({R.sw(tab + 2 * s) for s in range(N)})
    for s, d in enumerate(res):
        o = R.sw(tab + 2 * s); nx = [x for x in ofs if x > o]
        if nx and nx[0] - o >= 32:
            suite = list(R.octets(tab + o + 16, 16))
            if any(suite): d["liste_s2_suite"] = suite
    return res

def variantes(X, R2, log):
    """listes ALPHA lues dans ro4 (e348) ; adresses retrouvées par le contenu des tables de ro2 (même rangement)"""
    Q = X.mwo3(348)
    if b"zero4_usa.bin" not in Q[:0x40]: raise Echec("e348 n'est pas zero4_usa.bin")
    R4 = Ro(Q); c4 = {}
    for k in ("types_s1", "ofs_s1", "ofs_s2", "ofs_s3"):
        o = Q.find(R2.octets(CARTE[k], 2 * N))
        if o < 0: raise Echec("ro4 : table %s non retrouvée" % k)
        c4[k] = o + EXEC
    c4["types_s2"] = c4["ofs_s2"] - (CARTE["ofs_s2"] - CARTE["types_s2"]); c4["types_s3"] = c4["ofs_s3"] - (CARTE["ofs_s3"] - CARTE["types_s3"])
    sauve = {k: CARTE[k] for k in c4}; CARTE.update(c4)
    try:
        res = {s: {p: liste(R4, p, s) for p in (1, 2, 3)} for s in VARIANTES}
    finally:
        CARTE.update(sauve)
    log("ro4 (e348, md5 %s) : listes ALPHA lues en %s" % (hashlib.md5(Q).hexdigest(), " ".join("%s=0x%06X" % kv for kv in c4.items())))
    return res

def bibs(R, decors):
    u = {p: sorted({b for d in decors for b in d["liste_s%d" % p] + (d.get("liste_s2_suite", []) if p == 2 else [])}) for p in (1, 2, 3)}
    nb1 = max(u[1]) + 1
    bib1 = R.mots_be(CARTE["bib_s1"], nb1 * 128)
    ncel = max(struct.unpack_from(">64H", bib1, 128 * b) for b in u[1])
    ncel = max(max(struct.unpack_from(">64H", bib1, 128 * b)) for b in u[1]) + 1
    cel1 = R.longs_be(CARTE["cel_s1"], ncel * 64)
    bib2 = R.longs_be(CARTE["bib_s2"], (max(u[2]) + 1) * 1024)
    bib3 = R.longs_be(CARTE["bib_s3"], (max(u[3]) + 1) * 256)
    return u, bib1, cel1, bib2, bib3

def codes(d, bib1, cel1, bib2, bib3):
    """codes de tuiles utilisés par un décor (codes de bloc, avant ajout) : s1, s2, s3"""
    c1, c2, c3 = set(), set(), set()
    for b in set(d["liste_s1"]):
        for cel in struct.unpack_from(">64H", bib1, 128 * b):
            for k in range(16): c1.add(struct.unpack_from(">H", cel1, 64 * cel + 4 * k)[0])
    for b in set(d["liste_s2"]) | set(d.get("liste_s2_suite", [])):
        for k in range(256): c2.add(struct.unpack_from(">H", bib2, 1024 * b + 4 * k)[0])
    for b in set(d["liste_s3"]):
        for k in range(64): c3.add(struct.unpack_from(">H", bib3, 256 * b + 4 * k)[0])
    return c1, c2, c3

def encode(px):
    """tuile 16×16 (0-15) -> 128 octets au format interne de MAME / FBNeo (= hsfa_gfx.encode)"""
    px = np.asarray(px, np.uint8).reshape(16, 16); out = np.zeros((16, 2, 4), np.uint8)
    for h in range(2):
        blk = px[:, 8 * h:8 * h + 8]
        for b in range(4): out[:, h, b] = np.packbits((blk >> b) & 1, axis=1)[:, 0]
    return out.tobytes()

def tuiles32(e226):
    """{indice 32×32 : pixels (32, 32)} du conteneur e226 (vide -> 15 partout, transparent brut)"""
    t = {}
    for k, m, p in anthgfx.tiles(e226):
        if k == 2: t[m] = p if p is not None else np.full((32, 32), 15, np.uint8)
    return t

def comparer(X, R2, log):
    """ro4 / ro6 / ro8 : mêmes tables que ro2 ? (recherche du contenu de chaque table de ro2)"""
    tailles = dict(types_s1=40, ofs_s1=40, types_s2=40, types_s3=40, bib_s1=0x60 * 128, cel_s1=0x800 * 64,
                   bib_s2=130 * 1024, bib_s3=0xA0 * 256, pal_spr=N * 0xE0, pal_s1=N * 0x400, pal_s2=N * 0x400,
                   pal_s3=N * 0x400, cpsb=4 * N, musique=2 * N, perso_decor=0x18, ofs_s2=40, ofs_s3=40)
    res = {}
    for m in ("ro4", "ro6", "ro8"):
        Q = X.mwo3(MODULES[m]); res[m] = {}
        for k, n in tailles.items():
            o = Q.find(R2.octets(CARTE[k], n))
            res[m][k] = ("0x%06X" % (o + EXEC)) if o >= 0 else None
        # zone des listes et des objets : comparées entre décalages
        for k, n in (("listes", 0x562400 - 0x5620C0 + 1300), ("objets", 0x7287F0 - 0x728780 + 2600)):
            a = CARTE["types_s1"] if k == "listes" else CARTE["objets"]
            o = Q.find(R2.octets(a, n)); res[m][k] = ("0x%06X" % (o + EXEC)) if o >= 0 else None
        log("%s : %s" % (m, " ".join("%s=%s" % (k, v or "DIFFÉRENT") for k, v in res[m].items())))
    return res

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--iso"); ap.add_argument("--xdata"); ap.add_argument("--sortie", required=True)
    ap.add_argument("--comparer", action="store_true", help="comparer les tables de ro4 / ro6 / ro8 à celles de ro2")
    ap.add_argument("--modules", action="store_true", help="écrire ro2/ro4/ro6/ro8 décompressés (pour localise_ro2 / compare_versions)")
    ap.add_argument("--anim", help="(ancien, pour comparaison seulement) relevé MAME anim_codes.json : tuiles comparées à celles des tables de l'ISO")
    ap.add_argument("--sans-anims", action="store_true", help="ne pas extraire les animations (tables d'animation de ro2, RAPPORT §5)")
    ap.add_argument("--variantes-alpha", action="store_true", help="ajouter les listes ALPHA (ro4) de Dan, Sakura, Gen ($96/$98/$9A)")
    a = ap.parse_args()
    if not (a.iso or a.xdata): ap.error("--iso ou --xdata")
    os.makedirs(a.sortie, exist_ok=True)
    J = open(os.path.join(a.sortie, "extraction.txt"), "w")
    def log(m): print(m); J.write(m + "\n"); J.flush()
    X = XData(iso=a.iso, xdata=a.xdata)
    log("groupe ro2 (e224-e252) : md5 %s" % X.md5_groupe(224, 252))
    ro2 = X.mwo3(224)
    if ro2[:4] != b"MWo3" or b"zero2_usa.bin" not in ro2[:0x40]: raise Echec("e224 n'est pas zero2_usa.bin")
    e227 = np.frombuffer(X.mwo3(227), np.uint8); e226 = X.entree(226)
    log("ro2 : %d o (md5 %s) ; e227 : %d o ; e226 : %d o" % (len(ro2), hashlib.md5(ro2).hexdigest(), len(e227), len(e226)))
    R = Ro(ro2)
    if a.modules:
        for m, i in MODULES.items(): open(os.path.join(a.sortie, m + ".bin"), "wb").write(ro2 if m == "ro2" else X.mwo3(i))
    decors = lit_decors(R)
    for s, lp in (variantes(X, R, log).items() if a.variantes_alpha else ()):
        v = json.loads(json.dumps(decors[s])); v["decor"] = len(decors); v["val"] = VARIANTES[s]; v["d4"] = VARIANTES[s]
        v["variante_de"] = decors[s]["val"]; v["perso"] = decors[s]["perso"] + " ALPHA"; v["source_listes"] = "ro4/ro6"
        for p in (1, 2, 3): v["type_s%d" % p], v["liste_s%d" % p] = lp[p]
        decors[s]["variante_alpha"] = VARIANTES[s]
        log("variante ALPHA %s de %s (%s) : listes s1 %s s2 %s (ro2 : %s / %s)" % (VARIANTES[s], decors[s]["val"], decors[s]["perso"],
            bytes(lp[1][1]).hex(), bytes(lp[2][1]).hex(), bytes(decors[s]["liste_s1"]).hex(), bytes(decors[s]["liste_s2"]).hex()))
        decors.append(v)
    u, bib1, cel1, bib2, bib3 = bibs(R, decors)
    for nom, b in (("bib_s1", bib1), ("cel_s1", cel1), ("bib_s2", bib2), ("bib_s3", bib3)):
        open(os.path.join(a.sortie, nom + ".bin"), "wb").write(b)
    P8 = np.stack([e227 & 0xF, e227 >> 4], -1).reshape(-1)
    T32 = tuiles32(e226)
    tot = [set(), set(), set()]
    for d in decors:
        c = codes(d, bib1, cel1, bib2, bib3)
        for p in range(3):
            d["tuiles_s%d" % (p + 1)] = len(c[p])
            if d["decor"] < 18 or d.get("variante_de"): tot[p] |= c[p]
        d["blocs"] = [len(set(d["liste_s%d" % p])) for p in (1, 2, 3)]
        # équiv. 16×16 (CARTE-sfa2 §2.3) : 8×8 = ½ (moitié de 64 o), 16×16 = 1, 32×32 = 4
        d["equiv16"] = len(c[0]) / 2 + len(c[1]) + 4 * len(c[2])
        log("%s %-14s types %d/%d/%d blocs %2d/%2d/%2d tuiles 8x8 %4d 16x16 %4d 32x32 %4d (équiv16 %5.0f) objets %2d "
            "CPS-B %s/%s musique %s" % (d["val"], d["perso"], d["type_s1"], d["type_s2"], d["type_s3"], *d["blocs"],
            len(c[0]), len(c[1]), len(c[2]), d["equiv16"], len(d["objets"]), d["cpsb"][0], d["cpsb"][1], d["musique"]))
    if not a.sans_anims:   # animations : tables de ro2 (carte_anims_ro2.json), tuiles animées tirées des TABLES de l'ISO
        import anims_sfa2
        AN, atiles, apix = anims_sfa2.extrait(ro2, json.load(open(os.path.join(ICI, "carte_anims_ro2.json"))),
                                              X.entree(249), log=log, e226=e226)
        anims_sfa2.objets_decor(decors, AN); anims_sfa2.ecrit(a.sortie, AN, apix)
        nanim = [0, 0, 0]
        for p in range(3):
            nv = atiles["s%d" % (p + 1)] - tot[p]; nanim[p] = len(nv); tot[p] |= nv
        log("tuiles d'animation ajoutées (tables de l'ISO) : s1 %d, s2 %d, s3 %d (sfa2_anims.json, pixels_obj.npz)" % tuple(nanim))
    if a.anim:      # ancien relevé MAME : comparaison seulement (codes de bloc arcade ; une partie = renumérotation du portage)
        A2 = json.load(open(a.anim)); hors = [0, 0, 0]
        for d in decors[:18]:
            cb = A2.get(d["val"], {}).get("codes_bloc", {})
            for p in range(3): hors[p] += len(set(cb.get("s%d" % (p + 1), [])) - tot[p])
        log("relevé MAME --anim : codes hors famille s1 %d, s2 %d, s3 %d (renumérotation / révision, RAPPORT §5)" % tuple(hors))
    D18 = decors[:18] + [d for d in decors if d.get("variante_de")]
    log("union des 18 (+ variantes ALPHA si demandées) : blocs s1 %d, s2 %d, s3 %d ; tuiles 8x8 %d (%04X-%04X), 16x16 %d (%04X-%04X), 32x32 %d (%04X-%04X)" % (
        len({b for d in D18 for b in d["liste_s1"]}), len({b for d in D18 for b in d["liste_s2"]}),
        len({b for d in D18 for b in d["liste_s3"]}), len(tot[0]), min(tot[0]), max(tot[0]),
        len(tot[1]), min(tot[1]), max(tot[1]), len(tot[2]), min(tot[2]), max(tot[2])))
    # pixels pour le rendu (tous les décors, 20)
    allc = [set(), set(), set()]
    for d in decors:
        for p, c in enumerate(codes(d, bib1, cel1, bib2, bib3)): allc[p] |= c
    hi1 = max(allc[0]) + 1
    np.save(os.path.join(a.sortie, "pixels_s1.npy"), P8[:64 * hi1].reshape(hi1, 8, 8))
    lo2, hi2 = min(allc[1]), max(allc[1]) + 1
    p2 = np.stack([P8[256 * (c + ADD_S2_LOCAL):256 * (c + ADD_S2_LOCAL) + 256].reshape(16, 16) if 256 * (c + ADD_S2_LOCAL + 1) <= len(P8)
                   else np.full((16, 16), 15, np.uint8) for c in range(lo2, hi2)])
    np.save(os.path.join(a.sortie, "pixels_s2.npy"), p2)
    lo3, hi3 = min(allc[2]), max(allc[2]) + 1
    vide = np.full((32, 32), 15, np.uint8)
    p3 = np.stack([T32.get(c + ADD_S3_LOCAL, vide) for c in range(lo3, hi3)])
    np.save(os.path.join(a.sortie, "pixels_s3.npy"), p3)
    manq3 = sorted(c for c in allc[2] if c + ADD_S3_LOCAL not in T32)
    # famille SFA2 pour la ROM graphique : tuiles dédoublonnées (pixels identiques), 18 décors
    fam = {}
    for p, nom, taille in ((0, "s1", 8), (1, "s2", 16), (2, "s3", 32)):
        vus = {}; ren = {}
        for c in sorted(tot[p]):
            if p == 0: px = P8[64 * c:64 * c + 64]
            elif p == 1: px = P8[256 * (c + ADD_S2_LOCAL):256 * (c + ADD_S2_LOCAL) + 256]
            else: px = T32.get(c + ADD_S3_LOCAL, vide).reshape(-1)
            k = hashlib.md5(np.ascontiguousarray(px).tobytes()).digest()
            ren[c] = vus.setdefault(k, len(vus))
        fam[nom] = dict(distinctes=len(vus), utilisees=len(tot[p]), renum=ren)
        log("famille %s : %d tuiles utilisées, %d distinctes (dédoublonnage exact, sans retournement)" % (nom, len(tot[p]), len(vus)))
    # sfa2_plans.bin : s1 en éléments 8×8 de 64 o (moitiés dupliquées), s2 128 o, s3 512 o (4 × 16×16 de la ROM)
    n1, n2, n3 = (fam[k]["distinctes"] for k in ("s1", "s2", "s3"))
    o1, o2 = 0, (64 * n1 + 0xFFFF) & ~0xFFFF
    o3 = (o2 + 128 * n2 + 0xFFFF) & ~0xFFFF
    blob = bytearray(o3 + 512 * n3)
    for c, i in fam["s1"]["renum"].items():
        t = P8[64 * c:64 * c + 64].reshape(8, 8); b = np.zeros((16, 16), np.uint8); b[:8, :8] = t; b[:8, 8:] = t
        blob[o1 + 64 * i:o1 + 64 * i + 64] = encode(b)[:64]
    for c, i in fam["s2"]["renum"].items():
        blob[o2 + 128 * i:o2 + 128 * i + 128] = encode(P8[256 * (c + ADD_S2_LOCAL):256 * (c + ADD_S2_LOCAL) + 256])
    for c, i in fam["s3"]["renum"].items():
        s = anthgfx.to_slots(2, T32.get(c + ADD_S3_LOCAL, vide)).astype(np.uint8).reshape(4, 16, 16)
        blob[o3 + 512 * i:o3 + 512 * i + 512] = b"".join(encode(s[q]) for q in range(4))
    open(os.path.join(a.sortie, "sfa2_plans.bin"), "wb").write(bytes(blob))
    log("sfa2_plans.bin : %d o (%.2f Mo) ; décalages s1 0x%X (%d × 64 o), s2 0x%X (%d × 128 o), s3 0x%X (%d × 512 o)" % (
        len(blob), len(blob) / 2 ** 20, o1, n1, o2, n2, o3, n3))
    json.dump({k: {"%d" % c: i for c, i in v["renum"].items()} for k, v in fam.items()},
              open(os.path.join(a.sortie, "renum.json"), "w"))
    if manq3: log("ATTENTION : %d codes scroll3 sans tuile dans e226 : %s" % (len(manq3), manq3[:10]))
    perso = list(R.octets(CARTE["perso_decor"], 32))
    meta = dict(source="ISO (X_DATA e224 ro2, e226, e227)", md5_ro2=hashlib.md5(ro2).hexdigest(),
                carte={k: "0x%06X" % v for k, v in CARTE.items()}, perso_decor=perso,
                blocs=dict(s1=u[1], s2=u[2], s3=u[3]), codes_s1=[0, hi1 - 1], codes_s2=[lo2, hi2 - 1], codes_s3=[lo3, hi3 - 1],
                famille=dict(octets=len(blob), s1=dict(decalage=o1, n=n1), s2=dict(decalage=o2, n=n2), s3=dict(decalage=o3, n=n3)),
                decors=decors)
    if a.comparer: meta["modules"] = comparer(X, R, log)
    json.dump(meta, open(os.path.join(a.sortie, "sfa2_decors.json"), "w"), indent=1)
    J.close()

if __name__ == "__main__":
    try: main()
    except Echec as e: sys.exit("ÉCHEC : %s" % e)
