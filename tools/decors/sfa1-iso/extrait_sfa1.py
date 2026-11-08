#!/usr/bin/env python3
"""extrait_sfa1.py — décors de Street Fighter Alpha / Zero (SFA1) extraits de l'ISO de l'Anthology (USA, SLUS-21317).

Aucune ROM d'arcade : tout vient de X_DATA.BIN
  - e206 = module ro1 (« zero1_usa.bin », MWo3) : tables de décor, rangées par le recompilateur selon le modèle typé
    (octets tels quels, mots en petit-boutiste « w », longs en petit-boutiste « l ») ; adresses EXEC (= fichier +
    0x1F0000) de la carte ci-dessous, toutes référencées par le code MIPS de ro1 (constantes lui/addiu) ;
  - e207 = mémoire de tuiles de ro1 (= ROM graphique CPS2 de SFA1, pixels 4 bits bruts, ordre des tuiles 16×16).

Sorties (dossier --sortie, données de jeu : à garder hors de tout dépôt) :
  sfa1_decors.json   par décor : listes s2/s3, palettes (mots 0RGB, luminosité 0 comme dans le jeu), objets,
                     gestionnaires (formules), effet de sol, musique ; + union des blocs et des tuiles
  bib_s2.bin, bib_s3.bin   bibliothèques (ordre arcade, grand-boutiste) : bloc s2 = 256 × (code, attr) mots, s3 = 64 ×
  sfa1_plans.bin     tuiles des plans au format de la ROM graphique de MAME / FBNeo (hsfa_gfx.encode), À CHARGER EN
                     $4C40000 : scroll2 base $45A (code × 128, codes $D400-$EBFF avec les tuiles animées), scroll3
                     base $456 (code × 512, codes $3D00-$3F40), codes d'origine (aucune renumérotation)
  pixels_s2.npy / pixels_s3.npy   tuiles décodées (indices 0-15) pour le rendu hors jeu (rendu_sfa1.py)
  extraction.txt     journal (empreintes, tailles)

Usage : extrait_sfa1.py --iso SFA_Anthology.iso --sortie donnees/  [--xdata X_DATA.BIN] [--oracle DIR_ARCADE]
  --oracle : dossier contenant donnees.bin / code.bin (programme arcade sfa déchiffré, etude_decors) : contrôle octet
             par octet des tables extraites (révision ro1 ≠ sfa 950727 : écarts listés, l'ISO fait foi)."""
import os, sys, json, struct, hashlib, argparse
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
for p in (os.environ.get("HSFA_SRC", "<workspace>/github/src/hsfa"),):
    sys.path.insert(0, p)
from mwo3_codec import decompress          # décompresseur MWo3 du dépôt (LZSS)

SECTEUR = 2048
EXEC = 0x1F0000                            # adresse d'exécution de ro1 = fichier + 0x1F0000 (en-tête MWo3 : 0x1F0000)
MD5_RO1 = "b93119d8cf293ecf72310a5b5e73e765"   # groupe ro1 de X_DATA (e206-e223), hsfa_build.REF_GROUPES
N = 13
PERSOS = ["Ryu", "Ken", "Akuma", "Charlie", "Chun-Li", "Adon", "Sodom", "Guy", "Birdie", "Rose", "M.Bison", "Sagat", "Dan"]

# ---- carte des tables dans ro1 (outils/localise_ro1.py ; adresses arcade sfa entre parenthèses) --------------------
CARTE = {
    "types_s2":   0x4B4C10,   # ($1B2AE) 13 mots, rangement w
    "ofs_s2":     0x4B4C30,   # ($1B2CE) 13 mots signés w ; liste = table + décalage, 16 OCTETS tels quels (4×4 blocs)
    "types_s3":   0x4B4CDC,   # ($1B37A)
    "ofs_s3":     0x4B4CFC,   # ($1B39A) ; liste = 64 octets (8×8 blocs)
    "bib_s2":     0x47A8D0,   # ($1CDB60) bloc = 256 longs (code<<16 | attr), rangement l ; code + $D400
    "bib_s3":     0x48F8D0,   # ($1E2B60) bloc = 64 longs, rangement l ; code + $3D00
    "pal_s2":     0x4A0A10,   # ($1F20A0 + $400 n) 32 palettes, w
    "pal_s3":     0x4A7E10,   # ($1F94A0 + $400 n)
    "pal_obj24":  0x498110,   # ($1E97A0 + $100 n) 8 palettes des objets de décor (OBJ 24-31)
    "pal_obj0":   0x4948D0,   # ($1E7960 + $200 n) 16 palettes (OBJ 0-15) ; pas de $400 dans ro1 (2e moitié = autre table)
    "objets":     0x4AB210,   # ($1BCF8 décalages + enregistrements de 16 o), rangement w de toute la zone
}
ADD_S2, ADD_S3 = 0xD400, 0x3D00            # ajoutés au code du bloc par le moteur (sfa $1B0xx)

# ---- moteur de décor de SFA1 (lu dans le programme, RAPPORT §2) : constantes, pas des données de jeu --------------
# gestionnaires scroll2 ($1A39A) : tous init X=$1C0, Y=0 puis caméra standard ($1A57A) ; Charlie : base scroll2 $90C0
# et foule animée (décalage $5A(a6) = 0/$100/$200/$300 toutes les 12 images) ; Ryu/Guy : $5A = $200 si $190(A5) = 6.
GEST_S2 = {0: "std", 1: "std", 2: "std", 3: "charlie", 4: "std", 5: "std", 6: "std", 7: "std", 8: "std", 9: "std",
           10: "std", 11: "std", 12: "std"}
# gestionnaires scroll3 ($1A78E) : X0 propre à l'agencement ; X = X0 + (cam2X - $1C0 - choc)/2 ; Y = (cam2Y - choc)/2
X0_S3 = {0: 0x1A8, 7: 0x1A8, 1: 0x0C0, 3: 0x0C0, 2: 0x1C0, 4: 0x1C0, 5: 0x1C0, 11: 0x1C0, 12: 0x1C0,
         6: 0x1C0, 10: 0x1C0, 8: 0x1A0, 9: 0x1A0}
# effet ($1B624) : sol en perspective par rowscroll de scroll2 (triple tampon $916000-$917800, ligne de base $7B0/2) :
#   ligne de base + i (i = 0..23) : $C0 + i·d ; au-dessus : « haut » lignes en dégradé puis constante ;
#   d = (cam2X − $1C0) / k (division signée 16.16, $16070)
EFFETS = {"A": dict(k=88, haut=8), "C": dict(k=128, haut=40), "D": dict(k=66, haut=24), "-": None}
EFFET = {0: "A", 7: "A", 2: "A", 4: "A", 5: "C", 11: "C", 12: "C", 8: "D", 9: "D", 1: "-", 3: "-", 6: "-", 10: "-"}
MUSIQUE = [0x01, 0x02, 0x0B, 0x09, 0x03, 0x06, 0x05, 0x08, 0x07, 0x0A, 0x0C, 0x04, 0x32]   # sfa $13BB6

class Echec(Exception):
    pass

def iso_fichiers(iso):
    """{nom -> (lba, taille)} du répertoire racine ISO 9660 (même lecture que hsfa_build.py)"""
    with open(iso, "rb") as f:
        f.seek(16 * SECTEUR); pvd = f.read(SECTEUR)
        if pvd[1:6] != b"CD001": raise Echec("%s : pas d'ISO 9660" % iso)
        r = pvd[156:190]; lba, t = struct.unpack_from("<I", r, 2)[0], struct.unpack_from("<I", r, 10)[0]
        f.seek(lba * SECTEUR); rep = f.read(t)
    res = {}; o = 0
    while o < len(rep):
        n = rep[o]
        if n == 0: o = (o // SECTEUR + 1) * SECTEUR; continue
        lb, tt = struct.unpack_from("<I", rep, o + 2)[0], struct.unpack_from("<I", rep, o + 10)[0]
        nom = rep[o + 33:o + 33 + rep[o + 32]].decode("ascii", "replace")
        if nom not in ("\x00", "\x01"): res[nom.split(";")[0]] = (lb, tt)
        o += n
    return res

def entrees_xdata(lire, idx):
    """lire(off, n) sur X_DATA ; rend {i: octets} des entrées AFS demandées"""
    h = lire(0, 8)
    if h[:4] != b"AFS\0": raise Echec("X_DATA.BIN : pas une archive AFS")
    n = struct.unpack_from("<I", h, 4)[0]
    toc = lire(8, 8 * n)
    return {i: lire(*struct.unpack_from("<II", toc, 8 * i)) for i in idx}

def ouvre(a):
    if a.xdata:
        f = open(a.xdata, "rb"); base = 0
    else:
        fs = iso_fichiers(a.iso)
        if "X_DATA.BIN" not in fs: raise Echec("l'ISO ne contient pas X_DATA.BIN (pas l'Anthology)")
        f = open(a.iso, "rb"); base = fs["X_DATA.BIN"][0] * SECTEUR
    def lire(o, n):
        f.seek(base + o); return f.read(n)
    e = entrees_xdata(lire, [206, 207, 208, 223])
    # contrôle du groupe ro1 (e206-e223) comme hsfa_build : md5 de la concaténation
    h = hashlib.md5()
    toc = lire(8, 8 * 553)
    for i in range(206, 224):
        o, n = struct.unpack_from("<II", toc, 8 * i); h.update(lire(o, n))
    return e[206], e[207], h.hexdigest()

# ---- lecture typée de ro1 -----------------------------------------------------------------------------------------
class Ro1:
    def __init__(self, d): self.d = d
    def o(self, ex): return ex - EXEC
    def w(self, ex): return struct.unpack_from("<H", self.d, self.o(ex))[0]
    def sw(self, ex): return struct.unpack_from("<h", self.d, self.o(ex))[0]
    def l(self, ex): return struct.unpack_from("<I", self.d, self.o(ex))[0]
    def octets(self, ex, n): return bytes(self.d[self.o(ex):self.o(ex) + n])
    def mots_be(self, ex, n):      # région rangée w -> octets dans l'ordre arcade (grand-boutiste)
        b = self.octets(ex, n); return b"".join(b[i:i + 2][::-1] for i in range(0, n, 2))
    def longs_be(self, ex, n):
        b = self.octets(ex, n); return b"".join(b[i:i + 4][::-1] for i in range(0, n, 4))

def lit_decors(R):
    res = []
    for s in range(N):
        d = dict(decor=s, val="$%02X" % (2 * s), d4="$%02X" % (0xA0 + 2 * s), perso=PERSOS[s])
        d["type_s2"] = R.w(CARTE["types_s2"] + 2 * s); d["type_s3"] = R.w(CARTE["types_s3"] + 2 * s)
        d["liste_s2"] = list(R.octets(CARTE["ofs_s2"] + R.sw(CARTE["ofs_s2"] + 2 * s), 16))
        d["liste_s3"] = list(R.octets(CARTE["ofs_s3"] + R.sw(CARTE["ofs_s3"] + 2 * s), 64))
        d["pal_s2"] = R.mots_be(CARTE["pal_s2"] + 0x400 * s, 0x400).hex()
        d["pal_s3"] = R.mots_be(CARTE["pal_s3"] + 0x400 * s, 0x400).hex()
        d["pal_obj24"] = R.mots_be(CARTE["pal_obj24"] + 0x100 * s, 0x100).hex()
        d["pal_obj0"] = R.mots_be(CARTE["pal_obj0"] + 0x400 * s, 0x200).hex()
        a = CARTE["objets"] + R.w(CARTE["objets"] + 2 * s); objs = []
        while True:
            r = R.mots_be(a, 16)
            if r[0] >= 0x80: break
            x, y, res_, rout = struct.unpack_from(">HHHH", r, 0)
            objs.append(dict(x=x, y=y, reservoir=res_, routine="$%04X" % rout, brut=r.hex())); a += 16
        d["objets"] = objs
        d["gest_s2"] = dict(init_x=0x1C0, init_y=0, mode=GEST_S2[s])
        d["gest_s3"] = dict(x0=X0_S3[s], y0=0, pente_x="1/2", pente_y="1/2")
        d["effet"] = EFFET[s]; d["musique"] = "$%02X" % MUSIQUE[s]
        res.append(d)
    return res

def bibs(R, decors):
    b2 = sorted({b for d in decors for b in d["liste_s2"]}); b3 = sorted({b for d in decors for b in d["liste_s3"]})
    n2, n3 = max(b2) + 1, max(b3) + 1
    bib2 = R.longs_be(CARTE["bib_s2"], n2 * 1024); bib3 = R.longs_be(CARTE["bib_s3"], n3 * 256)
    return b2, b3, bib2, bib3

def codes(bib, blocs, taille, add):
    c = set()
    for b in blocs:
        for k in range(taille // 4):
            c.add((struct.unpack_from(">H", bib, b * taille + 4 * k)[0] + add) & 0xFFFF)
    return c

def encode(px):
    """tuile 16×16 (0-15) -> 128 octets au format interne de MAME / FBNeo (= hsfa_gfx.encode)"""
    px = np.asarray(px, np.uint8).reshape(16, 16); out = np.zeros((16, 2, 4), np.uint8)
    for h in range(2):
        blk = px[:, 8 * h:8 * h + 8]
        for b in range(4): out[:, h, b] = np.packbits((blk >> b) & 1, axis=1)[:, 0]
    return out.tobytes()

# ---- ANIMATIONS des objets de décor (outils/localise_anims_ro1.py, carte_anims_ro1.json ; RAPPORT §5) -------------
# Rangement ro1 : mots petit-boutistes ; pointeurs = longs petit-boutistes en adresses EXEC de ro1 ; cadres réalignés
# sur 4 o. Cadre : +0 durée (tics logiques), +2 drapeaux (octet fort ; bit 7 = fin : le long suivant = reprise), +4 ptr.
CARTE_ANIM = {
    "tuiles_s2":  (0x40A8E0, 16, [0, 1, 2, 3, 4, 5, 6]),   # ($11BCBA) classes $14 ($9 = 8) et $2E : blocs scroll2
    "palettes":   (0x4B7C60, 8, [0, 1]),                    # ($0444D4) classe $33 : cycles de palettes
    "spr_ryu":    (0x40C680, 16, [0, 1]),                   # ($10F060) $06 s0, $24
    "spr_ken":    (0x40CB50, 16, [0]),                      # ($10F526) $06 s1
    "spr_charlie": (0x40CCD0, 16, [0, 1, 2, 3, 4, 5, 6, 7]), # ($10F69E) $06 s2, $11 (1-4), $1F (créés par $1E)
    "spr_guy":    (0x40D290, 16, [0, 1, 2, 3]),             # ($10FC44) $06 s3, $16 (1-3)
    "spr_birdie_rose": (0x40D8E0, 16, [0, 1, 2, 3]),        # ($110292) $15 (0-2), $06 s4 (3)
    "spr_adon":   (0x40D210, 16, [0, 1]),                   # ($10FBDA) $06 s5 / s6 (Adon, Sagat, Dan)
    "spr_sodom":  (0x40D260, 16, [0]),                      # ($10FC20) $06 s7 (Sodom, M.Bison)
}
CLASSE06 = 0x4B5000      # ($3DD18) 8 × (long ptr table, long (anim << 16 | $A)) : sous-type de la classe $06
BANQUES_PAL = 0x3E3DA0   # ($15D3A) 4 longs : sources des cycles de palettes, sélecteur 0/4/8/12
POS_SPR = 0x40DBB0       # ($1280EC) longs : listes de positions (x, y) des descripteurs de sprites
FOULE = 0x3E3EA0         # ($1A4D2) 4 mots : Y de scroll2 de la foule de Charlie
FOULE_MIPS = 0x213704    # « li v1, période » de la foule (sfa $1A4B6 move.b #$C, $3C(a6))
LISTE_1E = 0x3EC650      # ($41CC0) objets créés par la classe $1E de Charlie (enregistrements de 16 o)
SAUTS_A = 0x4B7190       # ($41F0E) classe $1F, sous-types 0-1 : 2 mots (décalages) puis 4 × 12 o (vx, vy longs ; $A en +$B)
SAUTS_B = 0x4B71F4       # ($41FA8) classe $1F, sous-type 2 : 4 × 12 o (vx, vy longs ; $A en +8 ; attente $2C en +$A)
SAUTS_C = 0x4B7224       # ($4203A) classe $1F, 2e saut (sous-types 0-1) : 2 mots puis 4 × 12 o (vx, vy, gravité longs)
GRAVITE_MIPS = 0x3A5498  # « addiu v1, zero, -$3000 » ($41EF2 move.l #$FFFFD000, $3C(a6))
SOL_MIPS = 0x3A62F4      # « lui a0, $26 » ($42196 / $421AC : Y plafonné à $260000)
ANIM_OBJET = {           # classe -> (table, anims possibles) ; $06 : par CLASSE06 ; $14 : par sous-type
    0x14: ("tuiles_s2", None), 0x2E: ("tuiles_s2", [5, 6]), 0x33: ("palettes", None), 0x24: ("spr_ryu", [1]),
    0x11: ("spr_charlie", [1, 2, 3, 4]), 0x1F: ("spr_charlie", [5, 6, 7]), 0x16: ("spr_guy", [1, 2, 3]),
    0x15: ("spr_birdie_rose", [0, 1, 2]), 0x1E: (None, None)}

def lit_anims(R):
    tabs = {}; ptr_nom = {}
    for nom, (T, fs, anims) in CARTE_ANIM.items():
        ptr_nom[T] = nom; seqs = {}
        for i in anims:
            a = T + R.w(T + 2 * i); vus = {}; cad = []
            while a not in vus:
                vus[a] = len(cad); f = R.w(a + 2) >> 8; cad.append(dict(duree=R.w(a), drap=f, ptr="0x%06X" % R.l(a + 4)))
                a += fs
                if f & 0x80: a = R.l(a); break
            seqs[i] = dict(cadres=cad, reprise=vus.get(a))
            if seqs[i]["reprise"] is None: raise Echec("%s anim %d : reprise hors séquence" % (nom, i))
        tabs[nom] = dict(ro1="0x%06X" % T, taille_cadre=fs, anims=seqs)
    # contenus pointés
    blocs, pals, descs, poss = {}, {}, {}, {}
    banques = [R.l(BANQUES_PAL + 4 * k) for k in range(4)]
    for nom, t in tabs.items():
        for sq in t["anims"].values():
            for c in sq["cadres"]:
                p = int(c["ptr"], 16)
                if nom == "tuiles_s2" and c["ptr"] not in blocs:
                    r, cc = R.w(p + 2) + 1, R.w(p + 4) + 1
                    paires = [R.l(p + 8 + 4 * k) for k in range(r * cc)]          # colonne par colonne
                    blocs[c["ptr"]] = dict(lignes=r, colonnes=cc, mot0=R.w(p), codes=[v >> 16 for v in paires],
                                           attrs=[v & 0xFFFF for v in paires])
                elif nom == "palettes" and c["ptr"] not in pals:
                    ent = []; q = p
                    while True:
                        dst, sel, src = R.w(q), R.w(q + 2), R.w(q + 4)
                        b = banques[sel // 4] + (src & 0xFFE0)
                        ent.append(dict(dest="$%03X" % dst, plan=["obj", "s1", "s2", "s3"][dst >> 10], pal=(dst >> 5) & 31,
                                        banque=sel, source="0x%06X" % b, couleurs=[R.w(b + 2 * k) for k in range(16)]))
                        q += 6
                        if src & 1: break
                    pals[c["ptr"]] = ent
                elif nom.startswith("spr_") and c["ptr"] not in descs:
                    ty, tot, x = R.w(p), R.w(p + 2), R.w(p + 4)
                    if ty == 0:
                        n = tot; d = dict(type=0, total=tot, attr=x, pos=R.w(p + 6), codes=[R.w(p + 8 + 2 * k) for k in range(n)])
                        d["attrs"] = [x] * n
                    elif ty == 2:
                        n = x + 1; d = dict(type=2, total=tot, pos=R.w(p + 6), codes=[R.w(p + 8 + 4 * k) for k in range(n)],
                                            attrs=[R.w(p + 10 + 4 * k) for k in range(n)])
                    else:
                        raise Echec("descripteur de sprite de type %d non pris en charge (%s)" % (ty, c["ptr"]))
                    lp = R.l(POS_SPR + 4 * d["pos"])
                    d["xy"] = [(R.sw(lp + 4 * k), R.sw(lp + 4 * k + 2)) for k in range(n)]
                    descs[c["ptr"]] = d
    c06 = []
    for k in range(8):
        T = R.l(CLASSE06 + 8 * k); v = R.l(CLASSE06 + 8 * k + 4)
        if T not in ptr_nom: raise Echec("classe $06 s%d : table 0x%06X inconnue" % (k, T))
        c06.append(dict(table=ptr_nom[T], anim=v >> 16, a=v & 0xFF))
    ins = R.l(FOULE_MIPS)
    if ins >> 16 != 0x2403: raise Echec("foule de Charlie : 0x%06X n'est pas « li v1, n »" % FOULE_MIPS)
    foule = dict(periode=ins & 0xFFFF, y=[R.w(FOULE + 2 * k) for k in range(4)], ro1="0x%06X" % FOULE)
    l1e = []; a = LISTE_1E
    while True:
        r = R.mots_be(a, 16)
        if r[0] >= 0x80: break
        l1e.append(r.hex()); a += 16
    sl = lambda ex: struct.unpack_from("<i", R.d, R.o(ex))[0]
    sa = {}
    for ss in range(2):
        b = SAUTS_A + R.w(SAUTS_A + 2 * ss)
        sa[str(ss)] = [dict(vx=sl(b + 12 * j), vy=sl(b + 12 * j + 4), a=R.d[R.o(b + 12 * j + 11)]) for j in range(4)]
    sb = [dict(vx=sl(SAUTS_B + 12 * j), vy=sl(SAUTS_B + 12 * j + 4), a=R.d[R.o(SAUTS_B + 12 * j + 8)],
               attente=R.w(SAUTS_B + 12 * j + 10)) for j in range(4)]
    sc = {}
    for ss in range(2):
        b = SAUTS_C + R.w(SAUTS_C + 2 * ss)
        sc[str(ss)] = [dict(vx=sl(b + 12 * j), vy=sl(b + 12 * j + 4), gravite=sl(b + 12 * j + 8)) for j in range(4)]
    ig, isol = R.l(GRAVITE_MIPS), R.l(SOL_MIPS)
    if ig >> 16 != 0x2403 or isol >> 16 != 0x3C04: raise Echec("sauts $1F : constantes MIPS introuvables")
    sauts = dict(A=sa, B=sb, C=sc, gravite=((ig & 0xFFFF) ^ 0x8000) - 0x8000, sol=(isol & 0xFFFF) << 16,
                 ro1=dict(A="0x%06X" % SAUTS_A, B="0x%06X" % SAUTS_B, C="0x%06X" % SAUTS_C, gravite="0x%06X" % GRAVITE_MIPS, sol="0x%06X" % SOL_MIPS),
                 note="classe $1F : 1er saut A[sous-type 0-1] (gravité commune) puis 2e saut C[sous-type] (gravité de l'entrée) ; "
                      "sous-type 2 : B (balancement, vy/4 au retour) ; entrée tirée au hasard (& 3) ; vx négatif si $B = 0")
    return dict(tables=tabs, blocs_tuiles=blocs, palettes=pals, descripteurs=descs, classe06=c06,
                banques_pal=["0x%06X" % b for b in banques], foule_charlie=foule, liste_1e=l1e, sauts_1f=sauts)

def objets_anims(decors, A):
    """par objet de décor : table et animations utilisées"""
    for d in decors:
        for o in d["objets"]:
            r = int(o["routine"][1:], 16); cl, ss = r >> 8, r & 0xFF
            if cl == 0x06:
                e = A["classe06"][ss]; o["anim"] = dict(table=e["table"], anims=[e["anim"]])
            elif cl == 0x14:
                b9 = int(o["brut"][22:24], 16)        # octet $B de l'enregistrement -> $9 de l'objet
                if b9 != 8: raise Echec("objet $14 avec $9 = %d (seul 8 = scroll2 est extrait)" % b9)
                o["anim"] = dict(table="tuiles_s2", anims=[ss])
            elif cl == 0x33:
                o["anim"] = dict(table="palettes", anims=[ss])
            elif cl in ANIM_OBJET:
                t, an = ANIM_OBJET[cl]; o["anim"] = dict(table=t, anims=an)
                if cl == 0x1E: o["anim"]["cree"] = A["liste_1e"]
            else:
                raise Echec("classe d'objet $%02X inconnue" % cl)

ORG = 0x4C40000; BASE_S2, BASE_S3 = 0x45A, 0x456; FIN = 0x4D50000
# tuiles animées écrites dans scroll2 par les objets de décor (mesurées dans MAME, mame/lua/anim.lua) : Ken $EB31-$EBBF,
# Sodom $EBC0-$EBF5, Guy $EB2A-$EB30 (+ codes déjà dans les listes) -> la zone scroll2 va jusqu'à $EBFF
S2_FIN_ANIM = 0xEBFF

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--iso"); ap.add_argument("--xdata"); ap.add_argument("--sortie", required=True)
    ap.add_argument("--oracle")
    a = ap.parse_args()
    if not (a.iso or a.xdata): ap.error("--iso ou --xdata")
    os.makedirs(a.sortie, exist_ok=True)
    J = open(os.path.join(a.sortie, "extraction.txt"), "w")
    def log(m): print(m); J.write(m + "\n")
    e206, e207, mg = ouvre(a)
    log("groupe ro1 (e206-e223) : md5 %s %s" % (mg, "conforme" if mg == MD5_RO1 else "DIFFÉRENT (autre ISO ?)"))
    ro1 = bytes(decompress(e206)); gfx = np.frombuffer(bytes(decompress(e207)), np.uint8)
    if ro1[:4] != b"MWo3" or b"zero1_usa.bin" not in ro1[:0x40]: raise Echec("e206 n'est pas zero1_usa.bin")
    log("ro1 : %d o (md5 %s) ; e207 : %d o = %d tuiles 16×16" % (len(ro1), hashlib.md5(ro1).hexdigest(), len(gfx), len(gfx) // 128))
    R = Ro1(ro1)
    P = np.stack([gfx & 0xF, gfx >> 4], -1).reshape(-1, 16, 16)
    decors = lit_decors(R)
    b2, b3, bib2, bib3 = bibs(R, decors)
    open(os.path.join(a.sortie, "bib_s2.bin"), "wb").write(bib2)
    open(os.path.join(a.sortie, "bib_s3.bin"), "wb").write(bib3)
    # tuiles par décor
    tot2, tot3 = set(), set()
    for d in decors:
        c2 = codes(bib2, set(d["liste_s2"]), 1024, ADD_S2); c3 = codes(bib3, set(d["liste_s3"]), 256, ADD_S3)
        d["blocs_s2"] = len(set(d["liste_s2"])); d["blocs_s3"] = len(set(d["liste_s3"]))
        d["tuiles_s2"] = len(c2); d["tuiles_s3"] = len(c3); tot2 |= c2; tot3 |= c3
        log("%s %-8s blocs %2d/%2d tuiles16 %4d tuiles32 %3d objets %d effet %s X0s3 $%03X" % (
            d["val"], d["perso"], d["blocs_s2"], d["blocs_s3"], d["tuiles_s2"], d["tuiles_s3"], len(d["objets"]),
            d["effet"], d["gest_s3"]["x0"]))
    log("union : blocs s2 %d (0-%d), s3 %d ; tuiles 16×16 %d ($%04X-$%04X), 32×32 %d ($%04X-$%04X)" % (
        len(b2), max(b2), len(b3), len(tot2), min(tot2), max(tot2), len(tot3), min(tot3), max(tot3)))
    # tuiles : pixels (rendu) + famille au format MAME (P calculé plus haut)
    lo2, hi2 = min(tot2), max(max(tot2), S2_FIN_ANIM) + 1; lo3, hi3 = min(tot3), max(tot3) + 1
    np.save(os.path.join(a.sortie, "pixels_s2.npy"), P[lo2:hi2]);
    p3 = np.concatenate([P[4 * lo3:4 * hi3]]).reshape(hi3 - lo3, 64, 16).reshape(hi3 - lo3, 32, 32)
    np.save(os.path.join(a.sortie, "pixels_s3.npy"), p3)
    blob = bytearray(FIN - ORG)
    for c in range(lo2, hi2):
        o = BASE_S2 * 0x10000 + c * 128 - ORG; blob[o:o + 128] = encode(P[c])
    for c in range(lo3, hi3):
        o = BASE_S3 * 0x10000 + c * 512 - ORG
        blob[o:o + 512] = b"".join(encode(P[4 * c + q]) for q in range(4))
    assert BASE_S2 * 0x10000 + hi2 * 128 <= BASE_S3 * 0x10000 + lo3 * 512 or BASE_S3 * 0x10000 + hi3 * 512 <= BASE_S2 * 0x10000 + lo2 * 128
    open(os.path.join(a.sortie, "sfa1_plans.bin"), "wb").write(bytes(blob))
    log("sfa1_plans.bin : %d o à charger en $%07X ; HSFA bases scroll2 $%03X (codes $%04X-$%04X -> $%07X-$%07X), "
        "scroll3 $%03X (codes $%04X-$%04X -> $%07X-$%07X)" % (len(blob), ORG, BASE_S2, lo2, hi2 - 1,
        BASE_S2 * 0x10000 + lo2 * 128, BASE_S2 * 0x10000 + hi2 * 128, BASE_S3, lo3, hi3 - 1,
        BASE_S3 * 0x10000 + lo3 * 512, BASE_S3 * 0x10000 + hi3 * 512))
    meta = dict(source="ISO (X_DATA e206 ro1, e207)", md5_ro1=hashlib.md5(ro1).hexdigest(), carte={k: "0x%06X" % v for k, v in CARTE.items()},
                blocs_s2=b2, blocs_s3=b3, codes_s2=[lo2, hi2 - 1], codes_s3=[lo3, hi3 - 1], tuiles_s2=len(tot2), tuiles_s3=len(tot3),
                plans=dict(fichier="sfa1_plans.bin", charge_en="0x%07X" % ORG, base_s2="0x%03X" % BASE_S2, base_s3="0x%03X" % BASE_S3),
                effets=EFFETS, decors=decors)
    A = lit_anims(R); objets_anims(decors, A)
    # tuiles des sprites d'objets de décor (code OBJ = code du descripteur + $400 ; bloc nx × ny : code + x + 16 y)
    co = sorted({(c + 0x400 + x + 16 * y) & 0xFFFF for e in A["descripteurs"].values() for c, at in zip(e["codes"], e["attrs"])
                 for x in range(((at >> 8) & 0xF) + 1) for y in range(((at >> 12) & 0xF) + 1)})
    np.savez_compressed(os.path.join(a.sortie, "pixels_obj.npz"), codes=np.array(co), pixels=P[np.array(co)])
    A["tuiles_sprites"] = dict(nombre=len(co), codes=["$%04X" % c for c in co])
    json.dump(A, open(os.path.join(a.sortie, "sfa1_anims.json"), "w"), indent=1)
    log("animations : %d tables, %d séquences, %d blocs de tuiles, %d entrées de palettes, %d descripteurs de sprites ; "
        "tuiles de sprites %d ; foule de Charlie : Y %s toutes les %d tics" % (len(A["tables"]), sum(len(t["anims"]) for t in A["tables"].values()),
        len(A["blocs_tuiles"]), len(A["palettes"]), len(A["descripteurs"]), A["tuiles_sprites"]["nombre"], A["foule_charlie"]["y"], A["foule_charlie"]["periode"]))
    json.dump(meta, open(os.path.join(a.sortie, "sfa1_decors.json"), "w"), indent=1)
    if a.oracle:
        oracle(a.oracle, R, decors, bib2, bib3, b2, b3, log); oracle_anims(a.oracle, A, log)
    J.close()

def oracle(dossier, R, decors, bib2, bib3, b2, b3, log):
    """contrôle contre le programme arcade sfa déchiffré (local) : écarts = différences de révision"""
    D = open(os.path.join(dossier, "donnees.bin"), "rb").read(); C = open(os.path.join(dossier, "code.bin"), "rb").read()
    w = lambda b, x: struct.unpack_from(">H", b, x)[0]; sw = lambda b, x: struct.unpack_from(">h", b, x)[0]
    ecarts = 0
    def cmp(nom, x, y):
        nonlocal ecarts
        if x != y:
            n = sum(1 for i in range(min(len(x), len(y))) if x[i] != y[i]) + abs(len(x) - len(y)); ecarts += 1
            log("  ÉCART %s : %d élément(s) différent(s)" % (nom, n))
    for d in decors:
        s = d["decor"]
        cmp("%s liste s2" % d["val"], d["liste_s2"], list(D[0x1B2CE + sw(D, 0x1B2CE + 2 * s):][:16]))
        cmp("%s liste s3" % d["val"], d["liste_s3"], list(D[0x1B39A + sw(D, 0x1B39A + 2 * s):][:64]))
        for k, ad, n in (("pal_s2", 0x1F20A0 + 0x400 * s, 0x400), ("pal_s3", 0x1F94A0 + 0x400 * s, 0x400),
                         ("pal_obj24", 0x1E97A0 + 0x100 * s, 0x100), ("pal_obj0", 0x1E7960 + 0x200 * s, 0x200)):
            cmp("%s %s" % (d["val"], k), bytes.fromhex(d[k]), D[ad:ad + n])
        a = 0x1BCF8 + w(C, 0x1BCF8 + 2 * s)
        cmp("%s objets" % d["val"], "".join(o["brut"] for o in d["objets"]), D[a:a + 16 * len(d["objets"])].hex())
        cmp("%s types" % d["val"], (d["type_s2"], d["type_s3"]), (w(D, 0x1B2AE + 2 * s), w(D, 0x1B37A + 2 * s)))
    cmp("bib_s2", bib2, D[0x1CDB60:0x1CDB60 + len(bib2)]); cmp("bib_s3", bib3, D[0x1E2B60:0x1E2B60 + len(bib3)])
    log("oracle arcade sfa : %d table(s) différente(s)" % ecarts)

ARC_ANIM = {"tuiles_s2": 0x11BCBA, "palettes": 0x444D4, "spr_ryu": 0x10F060, "spr_ken": 0x10F526, "spr_charlie": 0x10F69E,
            "spr_guy": 0x10FC44, "spr_birdie_rose": 0x110292, "spr_adon": 0x10FBDA, "spr_sodom": 0x10FC20}

def oracle_anims(dossier, A, log):
    """parcours parallèle des tables d'animation arcade (sfa) : durées, drapeaux, reprises et contenus décodés"""
    D = open(os.path.join(dossier, "donnees.bin"), "rb").read()
    w = lambda x: struct.unpack_from(">H", D, x)[0]; sw = lambda x: struct.unpack_from(">h", D, x)[0]
    l = lambda x: struct.unpack_from(">I", D, x)[0]
    BQ = [0x1FCA00, 0x1FEC60, 0x1FF1C0, 0x1FF340]; ec = 0; n = 0
    for nom, t in A["tables"].items():
        T = ARC_ANIM[nom]; fs = t["taille_cadre"]
        for i, sq in t["anims"].items():
            a = T + w(T + 2 * int(i)); vus = {}
            for k, c in enumerate(sq["cadres"]):
                vus[a] = k; d, f, p = w(a), D[a + 2], l(a + 4); n += 1
                if (d, f) != (c["duree"], c["drap"]): ec += 1; log("  ÉCART %s %s cadre %d : durée/drapeaux" % (nom, i, k))
                if nom == "tuiles_s2":
                    b = A["blocs_tuiles"][c["ptr"]]; r, cc = w(p + 2) + 1, w(p + 4) + 1
                    mots = [w(p + 6 + 2 * j) for j in range(2 * r * cc)]
                    ok = (r, cc, w(p)) == (b["lignes"], b["colonnes"], b["mot0"]) and mots[0::2] == b["codes"] and mots[1::2] == b["attrs"]
                elif nom == "palettes":
                    ok = True; q = p
                    for e in A["palettes"][c["ptr"]]:
                        dst, sel, src = w(q), w(q + 2), w(q + 4); src0 = BQ[sel // 4] + (src & 0xFFE0)
                        ok &= ("$%03X" % dst, sel) == (e["dest"], e["banque"]) and [w(src0 + 2 * j) for j in range(16)] == e["couleurs"]
                        q += 6
                else:
                    e = A["descripteurs"][c["ptr"]]; ty, nn = w(p), (w(p + 2) if w(p) == 0 else w(p + 4) + 1)
                    if ty == 0: codes = [w(p + 8 + 2 * j) for j in range(nn)]; attrs = [w(p + 4)] * nn
                    else: codes = [w(p + 8 + 4 * j) for j in range(nn)]; attrs = [w(p + 10 + 4 * j) for j in range(nn)]
                    lp = l(0x1280EC + 4 * w(p + 6)); xy = [[sw(lp + 4 * j), sw(lp + 4 * j + 2)] for j in range(nn)]
                    ok = (ty, codes, attrs, xy) == (e["type"], e["codes"], e["attrs"], [list(v) for v in e["xy"]])
                if not ok: ec += 1; log("  ÉCART %s %s cadre %d : contenu pointé" % (nom, i, k))
                a += fs
                if f & 0x80: a = l(a)
            if vus.get(a) != sq["reprise"]: ec += 1; log("  ÉCART %s %s : reprise" % (nom, i))
    fo = A["foule_charlie"]; C = open(os.path.join(dossier, "code.bin"), "rb").read()   # $1A4D2 : zone chiffrée -> code.bin
    if fo["y"] != [struct.unpack_from(">H", C, 0x1A4D2 + 2 * j)[0] for j in range(4)] or C[0x1A4B6:0x1A4BA] != bytes([0x1D, 0x7C, 0, fo["periode"]]): ec += 1; log("  ÉCART foule de Charlie")
    if [bytes.fromhex(x) for x in A["liste_1e"]] != [D[0x41CC0 + 16 * j:0x41CC0 + 16 * j + 16] for j in range(len(A["liste_1e"]))]:
        ec += 1; log("  ÉCART liste $1E")
    sj = A["sauts_1f"]; si = lambda b, x: struct.unpack_from(">i", b, x)[0]
    att = {str(ss): [dict(vx=si(D, 0x41F0E + struct.unpack_from(">H", C, 0x41F0E + 2 * ss)[0] + 12 * j),
                          vy=si(D, 0x41F0E + struct.unpack_from(">H", C, 0x41F0E + 2 * ss)[0] + 12 * j + 4),
                          a=D[0x41F0E + struct.unpack_from(">H", C, 0x41F0E + 2 * ss)[0] + 12 * j + 8]) for j in range(4)] for ss in range(2)}
    attb = [dict(vx=si(C, 0x41FA8 + 12 * j), vy=si(C, 0x41FA8 + 12 * j + 4), a=C[0x41FA8 + 12 * j + 11],
                 attente=struct.unpack_from(">H", C, 0x41FA8 + 12 * j + 8)[0]) for j in range(4)]
    attc = {str(ss): [dict(vx=si(D, 0x4203A + struct.unpack_from(">H", C, 0x4203A + 2 * ss)[0] + 12 * j),
                           vy=si(D, 0x4203A + struct.unpack_from(">H", C, 0x4203A + 2 * ss)[0] + 12 * j + 4),
                           gravite=si(D, 0x4203A + struct.unpack_from(">H", C, 0x4203A + 2 * ss)[0] + 12 * j + 8)) for j in range(4)] for ss in range(2)}
    if attc != sj["C"] or att != sj["A"] or attb != sj["B"] or si(C, 0x41EF4) != sj["gravite"] or si(C, 0x42198) != sj["sol"]:
        ec += 1; log("  ÉCART tables de saut $1F")
    log("oracle arcade sfa, animations : %d cadres comparés, %d écart(s)" % (n, ec))

if __name__ == "__main__":
    try: main()
    except Echec as e: sys.exit("ÉCHEC : %s" % e)
