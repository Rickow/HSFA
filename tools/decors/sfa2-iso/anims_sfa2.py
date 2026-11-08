#!/usr/bin/env python3
"""anims_sfa2.py — EXTRACTION ISO des animations de décor de SFA2 (module ro2 = e224, tuiles e227 / e226, tuiles de
sprites de décor e249). N'utilise que l'ISO et les ADRESSES de outils/carte_anims_ro2.json (écrites côté oracle par
localise_anims_ro2.py, comme carte_ro2.json pour les plans). Appelé par extrait_sfa2.py --iso (ou seul :
anims_sfa2.py --iso ISO --sortie donnees/).

Moteur (lu dans le code 68K de sfa2u, RAPPORT §5) :
  cadre de 16 o (sprites, tuiles) ou 8 o (palettes) : +0 durée en IMAGES (0 = tenu), +2 drapeaux (bit 7 : fin, le long
  qui suit = cadre de reprise), +4 pointeur ; tuiles : +$C / +$E décalage X / Y ajouté à la position de l'objet.
  table de tête : un décalage (mot) par animation, relatif à SA racine (les sous-tables de sprites se chevauchent).
  bloc de tuiles : mot ignoré, lignes − 1, colonnes − 1, puis (code, attr) colonne par colonne ; code VRAM = code
  + 0 (s1), − $5C00 (s2), + $900 (s3) ; si l'objet est éteint ($1,A6 = 0) la case est vidée (code $20 / $20 / 0).
  entrées de palette (6 o) : destination (octets depuis $90C000), banque (0/4/8/12), source (& $FFE0 pour le moteur
  $18D00, & $FFFE pour le canal $6D62C ; bit 0 = dernière entrée) ; 16 couleurs, quartet de luminosité de la
  destination conservé.
  descripteur de sprite (mots) : type 0 = n, attr, position, n × code ; type 2 = cases, n − 1, position,
  n × (code, attr) ; position = indice (octets) dans la table des listes (x, y).
Rangement ro2 : mots petit-boutistes, pointeurs = longs petit-boutistes (adresses EXEC = fichier + 0x1F0000) ; bloc :
3 mots + 2 o de bourrage + longs (code << 16 | attr) ; couleur 15 des banques = n° de palette (portage, transparente).
"""
import os, sys, json, struct, hashlib, collections
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ICI)
EX = 0x1F0000
FS = {"sprite": 16, "palette": 8, "tuiles_s1": 16, "tuiles_s2": 16, "tuiles_s3": 16}
DECALAGE_VRAM = {"tuiles_s1": 0, "tuiles_s2": -0x5C00, "tuiles_s3": 0x900}

# classes d'objets de décor -> (genre, racine arcade de la table lue par le gestionnaire, rôle) ; lu dans le code 68K
# de sfa2u (gestionnaires $1E336[classe], pools A/B/C). « anims » = numéros choisis par le gestionnaire.
CLASSES = {
    "A00": ("sprite", "liste", "sprite générique : sous-type -> (animation, racine) dans la liste de la classe 0"),
    "A01": ("tuiles", "plan", "tuiles : octet +9 de l'enregistrement = plan (4 s1, 8 s2, 12 s3), sous-type = animation"),
    "A02": ("palette", 0x05B54E, "palette : sous-type = animation de la table $5B54E"),
    "A23": ("sprite", 0x21B8A6, "Rose"), "A38": ("sprite", 0x21B864, "Guy"), "A39": ("sprite", 0x06A55C, "Chun-Li : cyclistes (table locale)"),
    "A3C": ("canaux_s2", 0x21B864, "Guy : 4 canaux de tuiles s2 + sprite"), "A3D": ("sprite", 0x21B8E8, "Dan"),
    "A3E": ("sprite", 0x21B864, "Guy"), "A3F": ("tuiles", 0x23EFAE, "Sakura : tuiles s1 (animation 0)"),
    "A40": ("sprite", 0x21B930, "Rolento"), "A41": ("sprite", 0x21B930, "Rolento"),
    "A42": ("canaux_s2", 0x21B954, "Zangief : 3 canaux de tuiles s2 + 3 listes de palettes + sprites $11-$13 au signal"),
    "A43": ("sprite", 0x21B8B4, "M.Bison"), "A44": ("tuiles", 0x243910, "tuiles s3 directes (décor $24 seulement)"),
    "A45": ("sprite", 0x21B82A, "Adon"), "A47": ("sprite", 0x21B846, "Sodom"), "A48": ("sprite", 0x21B7F4, "Charlie"),
    "A49": ("listes_palette", None, "Charlie : 8 listes de palettes en parallèle (canal $6D62C)"),
    "A4A": ("sprite", 0x21B7F4, "Charlie"), "A4B": ("sprite", 0x21B982, "Gen (sous-type 0 : d abord cadre fixe tenu, cadres_fixes 0x733DAC)"),
    "A4C": ("reflet", None, "Gen : reflets des combattants (cadre du joueur en miroir vertical, palette OBJ 2/3 = palette du joueur & masque de luminosité ; clé reflets_gen)"),
    "A4D": ("sprite", "4D", "Guy / Dhalsim : table $6E308 (racine, animation) par sous-type"),
    "A4E": ("sprite", 0x21B7B6, "Ryu (pas manuel)"), "A4F": ("sprite", 0x21B7BE, "Ken"), "A50": ("sprite", 0x21B878, "Birdie"),
    "A51": ("sprite", 0x21B982, "Gen"), "A52": ("sprite", 0x21B930, "Rolento"), "A53": ("palette", 0x06E920, "Gen : palette"),
    "A54": ("sprite", 0x21B82A, "Adon"), "A55": ("palette", 0x06EA6A, "Birdie : palette"), "A57": ("sprite", 0x21B930, "Rolento"),
    "A58": ("sprite", 0x21B954, "Zangief"), "A59": ("sprite", 0x21B954, "Zangief"), "A5A": ("sprite", 0x21B954, "Zangief"),
    "A5B": ("sprite", 0x21B7BE, "Ken"), "A5C": ("sprite", 0x21B7BE, "Ken"), "A5D": ("canaux_s2", None, "Rolento : 4 canaux de tuiles s2"),
    "A5F": ("fixe", None, "Charlie : cadre unique tenu, posé par le gestionnaire (cadres_fixes 0x72E544)"), "A60": ("sprite+liste", 0x21B954, "Zangief : sprite + liste de palette $6FA16"),
    "A62": ("sprite", 0x21B8E8, "Dan"), "A64": ("sprite", 0x21B878, "Birdie"), "A67": ("sprite", 0x21B878, "Birdie"),
    "A68": ("sprite", 0x21B942, "Dhalsim"), "A69": ("sprite", 0x21B846, "Sodom"),
    "A6A": ("canaux_s2", 0x21B914, "Sakura : 1 canal s2 (anim $D en $1F0, $80) + liste de palette $7113C au même pas"),
    "A6B": ("canaux_s2", 0x21B8E8, "Dan : 2 canaux de tuiles s2 + sprite"), "A6C": ("sprite", 0x21B914, "Sakura"),
    "A6E": ("sprite+liste", 0x21B954, "Zangief : sprite + liste de palette $71580"),
    "B00": ("sprite", 0x21B7B6, "Ryu"), "B01": ("sprite", 0x21B8E8, "Dan"), "B02": ("sprite", 0x21B7EA, "Akuma"),
    "B03": ("sprite", 0x21B8B4, "M.Bison"), "B04": ("sprite", 0x21B992, "?"), "B05": ("sprite", 0x21B8A6, "Rose"),
    "C15": ("sprite", 0x21B930, "Rolento (créé)"), "C16": ("sprite", 0x21B930, "Rolento (créé, anim 6)"),
    "C17": ("sprite", 0x21B878, "Birdie (créé)"), "C18": ("sprite", 0x21B82A, "Adon (créé)"), "C19": ("sprite", 0x21B914, "Sakura (créé)"),
}
POOL = {4: "A", 12: "B"}            # octet +4 de l'enregistrement d'objet -> pool ($1EB94)


class Ro2:
    def __init__(s, b): s.b = b
    def w(s, a): return struct.unpack_from("<H", s.b, a - EX)[0]
    def sw(s, a): return struct.unpack_from("<h", s.b, a - EX)[0]
    def l(s, a): return struct.unpack_from("<I", s.b, a - EX)[0]
    def dans(s, a): return EX <= a < EX + len(s.b) - 16


def parcours(R, a, fs):
    """cadres depuis l'adresse a : liste de (adr, durée, drapeaux, ptr, mots +8..+15), fin = ('boucle', k) |
    ('tenu',) | ('saut', adr)"""
    seq = []; vus = {}
    for _ in range(4096):
        if a in vus: return seq, ("boucle", vus[a])
        vus[a] = len(seq); d, f, p = R.w(a), R.w(a + 2) >> 8, R.l(a + 4)
        ex = [R.sw(a + 8 + 2 * i) for i in range(4)] if fs == 16 else []
        seq.append((a, d, f, p, ex)); a += fs
        if d == 0: return seq, ("tenu",)
        if f & 0x80:
            a = R.l(a)
            return seq, ("boucle", vus[a]) if a in vus else ("saut", a)
    raise ValueError("parcours sans fin")


def bloc(R, p):
    nl, nc = R.w(p + 2) + 1, R.w(p + 4) + 1
    v = [R.l(p + 8 + 4 * k) for k in range(nl * nc)]
    return dict(mot0=R.w(p), lignes=nl, colonnes=nc, paires=[[x >> 16, x & 0xFFFF] for x in v])


def entrees(R, p, banques, masque):
    E = []
    for _ in range(64):
        d, b, s = R.w(p), R.w(p + 2), R.w(p + 4); p += 6
        base = banques[b // 4] + (s & masque)
        E.append(dict(dest=d, banque=b, source=s, couleurs=[R.w(base + 2 * j) for j in range(16)]))
        if s & 1: return E
    raise ValueError("entrées sans fin")


def descripteur(R, p, pos):
    t = R.w(p); spr = []
    if t == 0:
        n, at, pi = R.w(p + 2), R.w(p + 4), R.w(p + 6); lp = R.l(pos + pi)
        for k in range(n):
            spr.append(dict(code=R.w(p + 8 + 2 * k), attr=at, x=R.sw(lp + 4 * k), y=R.sw(lp + 4 * k + 2)))
        mots = 4 + n
    elif t == 2:
        cases, n1, pi = R.w(p + 2), R.w(p + 4), R.w(p + 6); lp = R.l(pos + pi)
        for k in range(n1 + 1):
            spr.append(dict(code=R.w(p + 8 + 4 * k), attr=R.w(p + 10 + 4 * k), x=R.sw(lp + 4 * k), y=R.sw(lp + 4 * k + 2)))
        mots = 4 + 2 * (n1 + 1)
    elif t == 4:     # n × (code, attr, x, y) ; code « plan » : tuile OBJ = $10000 + (code − $5C00) -> conteneur e226
        n1 = R.w(p + 4)
        for k in range(n1 + 1):
            q = p + 6 + 8 * k
            spr.append(dict(code=(R.w(q) - 0x5C00) & 0xFFFF, attr=R.w(q + 2), x=R.sw(q + 4), y=R.sw(q + 6), banque="e226"))
        mots = 3 + 4 * (n1 + 1)
    elif t == 10:    # rien n'est affiché ($12CDA : rts)
        return dict(type=t, mots=[t], sprites=[])
    else:
        return dict(type=t, mots=[R.w(p + 2 * i) for i in range(4)], sprites=None)
    return dict(type=t, mots=[R.w(p + 2 * i) for i in range(mots)], sprites=spr)


# cadres FIXES posés directement par un gestionnaire (lea du cadre, sans table d'animation) : trouvés au contrôle des
# positions contre l'OBJ de MAME (07/11, RAPPORT §7.6) ; cadre ro2 chargé par le code MIPS (lui/addiu), descripteur
# identique mot pour mot à l'arcade (type 4, tuiles « plan » e226)
CADRES_FIXES = {
    0x733DAC: dict(arcade="$06E010", desc_arcade="$06E018", classe="A4B", mips="0x451C44",
                   role="Gen $4B, sous-type 0 ($6DCAA) : Y = $28, cadre tenu (arcade : durée 0, drapeaux 0)",
                   note="ro2 : les 4 1ers octets du cadre sont partagés avec la fin d'une entrée de palette (durée lue 8, "
                        "octet 0x21) ; seul le pointeur (+4) sert : le cadre n'est pas avancé dans cet état"),
    0x72E544: dict(arcade="$06F8D4", desc_arcade="$06F8E8", classe="A5F", mips="0x3661EC",
                   role="Charlie $5F ($6F8BC) : cadre unique tenu (durée $FFF, fin)", note=""),
}

def extrait(ro2, carte, e249=None, log=print, e226=None):
    """-> (anims (dict JSON), tuiles animées {plan: set(codes ro2)}, pixels des sprites {code: (16, 16)})"""
    R = Ro2(ro2); C = carte
    banques = [R.l(int(C["banques"]["tables_ro2"][0], 16) + 4 * k) for k in range(4)]
    pos = int(C["positions"]["ro2"], 16)
    out = dict(source="ISO (X_DATA e224 ro2 ; e249 tuiles de sprites)", md5_ro2=hashlib.md5(ro2).hexdigest(),
               unite_duree="images (60 Hz) : le pas des objets de décor n'a lieu qu'une fois par image",
               banques_ro2=["0x%06X" % b for b in banques], positions_ro2="0x%06X" % pos,
               tables={}, blocs={}, entrees_palette={}, descripteurs={}, listes_palette={}, canaux_s2={},
               classe0={}, classes={k: dict(genre=v[0], table=("$%06X" % v[1]) if isinstance(v[1], int) else v[1], role=v[2]) for k, v in CLASSES.items()})
    anim_tiles = {"s1": set(), "s2": set(), "s3": set()}; codes_spr = set()
    def cadres(seq, fin, eng):
        L = []
        for (a, d, f, p, ex) in seq:
            c = dict(adr="0x%06X" % a, duree=d, drapeaux=f, ptr="0x%06X" % p)
            if eng.startswith("tuiles"):
                c["dx"], c["dy"] = ex[2], ex[3]
                k = "0x%06X" % p
                if k not in out["blocs"]:
                    out["blocs"][k] = bloc(R, p)
                    anim_tiles["s" + eng[-1]] |= {x for x, _ in out["blocs"][k]["paires"]}
            elif eng == "palette":
                k = "0x%06X" % p
                if k not in out["entrees_palette"]: out["entrees_palette"][k] = entrees(R, p, banques, 0xFFE0 if masque_moteur else 0xFFFE)
            elif eng == "sprite" and d != 0 and R.dans(p):
                k = "0x%06X" % p
                if k not in out["descripteurs"]:
                    ds = descripteur(R, p, pos); out["descripteurs"][k] = ds
                    for sp in ds["sprites"] or []:
                        at = sp["attr"]; w, h = ((at >> 8) & 15) + 1, ((at >> 12) & 15) + 1
                        codes_spr.update((sp.get("banque", "e249"), sp["code"] + i + 16 * j) for i in range(w) for j in range(h))
            L.append(c)
        return dict(cadres=L, fin=list(fin) if fin[0] != "saut" else ["saut", "0x%06X" % fin[1]])
    out["cadres_fixes"] = {}
    for a_, e in CADRES_FIXES.items():
        p = R.l(a_ + 4); k = "0x%06X" % p
        if not R.dans(p) or R.w(p) != 4: log("ATTENTION : cadre fixe 0x%06X : descripteur inattendu" % a_); continue
        if k not in out["descripteurs"]:
            ds = descripteur(R, p, pos); out["descripteurs"][k] = ds
            for sp in ds["sprites"] or []:
                at = sp["attr"]; w, h = ((at >> 8) & 15) + 1, ((at >> 12) & 15) + 1
                codes_spr.update((sp.get("banque", "e249"), sp["code"] + i + 16 * j) for i in range(w) for j in range(h))
        out["cadres_fixes"]["0x%06X" % a_] = dict(e, duree_ro2=R.w(a_), drapeaux_ro2=R.w(a_ + 2) >> 8, ptr=k)
    masque_moteur = True
    for ra, e in C["racines"].items():
        if len(e["ro2"]) != 1: log("ATTENTION : racine %s non localisée de façon unique" % ra); continue
        T = int(e["ro2"][0], 16); eng = e["moteur"]; fs = FS[eng]
        t = dict(arcade=ra, ro2="0x%06X" % T, moteur=eng, role=e["role"], anims={})
        for i in e["anims"]:
            seq, fin = parcours(R, T + R.w(T + 2 * i), fs)
            t["anims"][str(i)] = cadres(seq, fin, eng)
        out["tables"]["0x%06X" % T] = t
    masque_moteur = False
    for la, e in C["listes_palette"].items():
        a = int(e["ro2"][0], 16); seq, fin = parcours(R, a, 8)
        out["listes_palette"]["0x%06X" % a] = dict(arcade=la, role=e["role"], **cadres(seq, fin, "palette"))
    for k, e in C["canaux_s2"].items():
        if not e["ro2_pos"]: out["canaux_s2"][k] = dict(role=e["role"], ro2=None, note="absent de ro2"); continue
        pa = int(e["ro2_anims"][0], 16); pp = int(e["ro2_pos"][0], 16); n = len(e["anims"])
        out["canaux_s2"][k] = dict(role=e["role"], ro2_anims="0x%06X" % pa, ro2_pos="0x%06X" % pp,
                                   canaux=[dict(anim=ro2[pa - EX + i], x=R.w(pp + 4 * i), y=R.w(pp + 4 * i + 2)) for i in range(n)])
    c0 = int(C["classe0"]["ro2"], 16)
    out["classe0"] = dict(ro2="0x%06X" % c0, sous_types=[dict(anim=R.l(c0 + 4 * s) >> 24, table="0x%06X" % (R.l(c0 + 4 * s) & 0xFFFFFF)) for s in range(C["classe0"]["n"])])
    sg = int(C["sinus_gen"]["ro2"][0], 16)
    out["sinus_gen"] = dict(ro2="0x%06X" % sg, valeurs=[R.sw(sg + 2 * i) for i in range(256)],
                            usage="rowscroll de Gen (effet $1DD48) : 24 paires de lignes autour de la ligne +$20 ; "
                                  "décalage = (sin[(phase + $A0·k) & $1FE] >> 12) + $C0 ; phase −$10 par image")
    # pixels des sprites de décor : e249 (banque DATA, numérotation ro2)
    pix = {}
    if e249 is not None:
        import anthgfx
        vide = np.full((16, 16), 15, np.uint8)
        for nom, buf in (("e249", e249), ("e226", e226)):
            if buf is None: continue
            T16 = {m: p for k, m, p in anthgfx.tiles(buf) if k == 1}
            cs = sorted(c for b, c in codes_spr if b == nom)
            for c in cs: pix[(nom, c)] = T16.get(c) if T16.get(c) is not None else vide
            manq = [c for c in cs if c not in T16]
            if manq: log("ATTENTION : %d codes de sprites absents de %s" % (len(manq), nom))
    n = {k: len(v) for k, v in out.items() if isinstance(v, dict)}
    log("animations (ISO) : tables %d, blocs %d, entrées de palette %d, descripteurs %d, listes %d, canaux s2 %d ; "
        "tuiles animées s1 %d s2 %d s3 %d ; tuiles de sprites %d" % (n["tables"], n["blocs"], n["entrees_palette"],
        n["descripteurs"], n["listes_palette"], n["canaux_s2"], len(anim_tiles["s1"]), len(anim_tiles["s2"]),
        len(anim_tiles["s3"]), len(codes_spr)))
    out["tuiles_animees"] = {k: sorted(v) for k, v in anim_tiles.items()}
    out["defilements"] = defilements(R, log)
    out["reflets_gen"] = reflets_gen(R, log)
    return out, anim_tiles, pix


# ---- défilements propres (07/11, RAPPORT §7.8) : formules lues dans sfa2u (s1 : $1A8AA, s3 : $1B842 ; routines
# $1AE98-$1B1DE et $1BD86-$1BFDE) ; tables et immédiats lus dans ro2 (code MIPS traduit) aux adresses ci-dessous.
# Modèle commun : X = X0 + F(Δx + sol) + hi($50) ; Y = Y0 + G(Δy) + hi($54) ; reg X = ((X + $58) & m) − $40 ;
# reg Y = B − ((Y − ($14E) + $5A) & m) ; Δx = ($2A0) − ($288), Δy = ($2A4) − ($28C) (caméra s2), sol = ($398) ;
# s1 : m = $1FF, B = $100 ; s3 : m = $7FF, B = $700. Les pas des décalages propres sont PAR TIC (4 tics / 3 images),
# suspendus par le gel ($125) ; durées des tables en tics.
DEFIL_IMM = {   # nom -> (adresse ro2 EXEC, forme) ; forme : addiu | lui | lui_ori | addiu2 (addiu $7FFF + addiu 1)
    "rose_s1_pas50": (0x22326C, "addiu"), "rose_s1_butee50": (0x223320, "addiu"), "rose_s1_butee50_l": (0x223410, "lui"),
    "chunli_s3_pas50": (0x228F18, "lui_ori"),
    "rolento_s3_pas54_1": (0x2298FC, "addiu2"), "rolento_s3_seuil1": (0x229908, "addiu"), "rolento_s3_58": (0x2299E8, "addiu"),
    "rolento_s3_5a": (0x2299F8, "addiu"), "rolento_s3_pas54_2": (0x229A88, "addiu2"), "rolento_s3_seuil2": (0x229A94, "addiu"),
    "rolento_s3_attente": (0x229B74, "addiu"), "rolento_s3_signal_s1": (0x229C48, "addiu"), "rolento_s3_pas54_3": (0x229CC8, "addiu2"),
    "rolento_s3_seuil3": (0x229CD4, "addiu"), "rolento_s1_pas54": (0x223B1C, "addiu"), "rolento_s1_54_depart": (0x223B88, "lui"),
    "rolento_s1_pas54_2": (0x223C4C, "addiu"), "rolento_s1_seuil": (0x223C54, "addiu"), "rolento_s1_54_fin": (0x223D44, "lui")}
DEFIL_TABLES = {"rose_s1_oscillation_y": (0x4CBBD0, 16), "chunli_s3_cycle_5a": (0x4CBEF0, 8)}   # paires (valeur, durée en tics)
DEFIL_ATTENDU = {"rose_s1_pas50": 0x3000, "rose_s1_butee50": 0x3A0, "rose_s1_butee50_l": 0x3A00000, "chunli_s3_pas50": -0x18000,
    "rolento_s3_pas54_1": 0x8000, "rolento_s3_seuil1": 0x480, "rolento_s3_58": 0x400, "rolento_s3_5a": -0x400,
    "rolento_s3_pas54_2": 0x8000, "rolento_s3_seuil2": 0x700, "rolento_s3_attente": 0x140, "rolento_s3_signal_s1": 2,
    "rolento_s3_pas54_3": 0x8000, "rolento_s3_seuil3": 0x800, "rolento_s1_pas54": 0x4000, "rolento_s1_54_depart": 0xC00000,
    "rolento_s1_pas54_2": 0x2000, "rolento_s1_seuil": 0x100, "rolento_s1_54_fin": 0x1000000}

def defilements(R, log=print):
    def mot(a): return struct.unpack_from("<I", R.b, a - EX)[0]
    def imm(a, forme):
        w = mot(a); op = w >> 26; i = w & 0xFFFF; si = i - 0x10000 if i & 0x8000 else i
        if forme == "addiu": assert op == 9, hex(a); return si
        if forme == "lui": assert op == 0xF, hex(a); return si << 16
        if forme == "lui_ori":
            w2 = mot(a + 4); assert op == 0xF and w2 >> 26 == 0xD, hex(a); return (si << 16) | (w2 & 0xFFFF)
        if forme == "addiu2":
            w2 = mot(a + 4); assert op == 9 and w2 >> 26 == 9, hex(a); return si + ((w2 & 0xFFFF) - (0x10000 if w2 & 0x8000 else 0))
    v = {}
    for k, (a, f) in DEFIL_IMM.items():
        v[k] = imm(a, f)
        if v[k] != DEFIL_ATTENDU[k]: log("ATTENTION : défilement %s = %#x dans ro2 (0x%06X), attendu %#x" % (k, v[k], a, DEFIL_ATTENDU[k]))
    t = {k: [(R.sw(a + 4 * i), R.sw(a + 4 * i + 2)) for i in range(n)] for k, (a, n) in DEFIL_TABLES.items()}
    adr = lambda *ks: {k: "0x%06X" % DEFIL_IMM[k][0] for k in ks}
    modele = ("X = X0 + F(Δx + sol) + hi($50) ; Y = Y0 + G(Δy) + hi($54) ; reg X = ((X + $58) & m) − $40 ; "
              "reg Y = B − ((Y − ($14E) + $5A) & m) ; Δx = ($2A0) − ($288), Δy = ($2A4) − ($28C), sol = ($398) ; "
              "s1 : m = $1FF, B = $100 ; s3 : m = $7FF, B = $700 ; pas PAR TIC, suspendus si ($125) ≠ 0")
    out = dict(modele=modele, decors={
      "$08": dict(perso="Chun-Li", s1=dict(arcade="$1AADC", F="1", G="1", X0=0x1C0, Y0=0),
                  s3=dict(arcade="$1B9B4", F="1", G="1", X0=0x1C0, Y0=0, pas_50=v["chunli_s3_pas50"],
                          cycle_5a=dict(ro2="0x%06X" % DEFIL_TABLES["chunli_s3_cycle_5a"][0], paires=t["chunli_s3_cycle_5a"],
                                        sens="indice + 1 (mod 8) à la fin de chaque durée ; $5A = valeur : registre Y = bande de la tilemap (cyclistes)"),
                          ro2=adr("chunli_s3_pas50"))),
      "$12": dict(perso="Rose", s1=dict(arcade="$1ABAA", F="1/2", G="1/2", X0=0xC0, Y0=0, pas_50=v["rose_s1_pas50"],
                  butee_50=v["rose_s1_butee50"], apres_butee="$50 = butée << 16, $54 = 0, plus d'oscillation",
                  oscillation_54=dict(ro2="0x%06X" % DEFIL_TABLES["rose_s1_oscillation_y"][0], paires=t["rose_s1_oscillation_y"],
                                      sens="indice + 1 (mod 16) à la fin de chaque durée ; hi($54) = valeur (bateau)"),
                  ro2=adr("rose_s1_pas50", "rose_s1_butee50", "rose_s1_butee50_l")),
                  s3=dict(arcade="$1BABC", F="1/2", G="1/2", X0=0x1C0, Y0=0)),
      "$1C": dict(perso="Rolento", condition="manche ≥ 2 (($102,A5) ≠ 0) ; en 1re manche rien ne bouge",
                  s1=dict(arcade="$1ACFA", F="1/4", G="1/4", X0=0x40, Y0=0, pas_54=v["rolento_s1_pas54"],
                          signal="quand s3 met l'état du plan s1 ($FF8200) à 2 : $54 = %#x, base s1 = $9100, puis $54 += %#x / tic jusqu'à %#x"
                                 % (v["rolento_s1_54_depart"], v["rolento_s1_pas54_2"], v["rolento_s1_seuil"] << 16),
                          ro2=adr("rolento_s1_pas54", "rolento_s1_54_depart", "rolento_s1_pas54_2", "rolento_s1_seuil", "rolento_s1_54_fin")),
                  s3=dict(arcade="$1BB58", F="1/2", G="1/2", X0=0x1C0, Y0=0,
                          script=[dict(pas_54=v["rolento_s3_pas54_1"], jusqua=v["rolento_s3_seuil1"], puis=dict(_58=v["rolento_s3_58"], _5A=v["rolento_s3_5a"] & 0xFFFF)),
                                  dict(pas_54=v["rolento_s3_pas54_2"], jusqua=v["rolento_s3_seuil2"], puis=dict(attente_tics=v["rolento_s3_attente"])),
                                  dict(attente=v["rolento_s3_attente"], puis=dict(etat_s1=v["rolento_s3_signal_s1"])),
                                  dict(pas_54=v["rolento_s3_pas54_3"], jusqua=v["rolento_s3_seuil3"])],
                          ro2=adr(*[k for k in DEFIL_IMM if k.startswith("rolento_s3")])))})
    log("défilements propres (ISO) : Chun-Li s3, Rose s1, Rolento s1/s3 ; %d immédiats et %d tables lus dans ro2" % (len(v), len(t)))
    return out


# ---- Gen, classe $4C (07/11, RAPPORT §7.4) : REFLETS des combattants dans les flaques (sfa2u $6E036 ; une instance par
# joueur, ($3,A6) = 0 / 1). Chaque image ($6E21C) : $6E070 copie le cadre du joueur (($1C) : même image de sprite),
# X = X du joueur, Y = 2·($64) − ($14) (symétrie autour du sol), attribut ($B) | 2 (miroir vertical) ; $6E09E écrit les
# 16 couleurs de la palette OBJ 2 (J1, $90C040) / 3 (J2, $90C060) = palette COURANTE du joueur (pointeur ($D0) = sa
# palette OBJ en RAM) ET masque (mot, dupliqué) de la table [perso ($82) × 6 + couleur ($A8)] : le masque ne touche que
# le quartet de luminosité (assombrissement) ; X += ondulation[(($80,A5) + ($3,A6)) & 15] ; pas d'affichage si Y < 0.
REFLETS_MASQUES = (0x4DAA00, 24, 6)    # ro2 (sfa2u $6E0FC, lu en $6E0CC) : 24 persos × 6 couleurs, mots ; lu en ro2 0x451818
REFLETS_ONDULATION = (0x4DAB20, 16)    # ro2 (sfa2u $6E256, lu en $6E23A) : 16 octets signés ; lu en ro2 0x451A18

def reflets_gen(R, log=print):
    a, np_, nc = REFLETS_MASQUES; m = [R.w(a + 2 * i) for i in range(np_ * nc)]
    o, n = REFLETS_ONDULATION; ond = [struct.unpack_from("b", R.b, o + i - EX)[0] for i in range(n)]
    if any(x & 0x0FFF != 0x0FFF for x in m): log("ATTENTION : masques des reflets de Gen : quartets de couleur non tous à F")
    log("reflets de Gen ($4C) : %d masques (%d persos × %d couleurs), ondulation %s" % (len(m), np_, nc, ond))
    return dict(classe="A4C", arcade="$6E036", ro2_masques="0x%06X" % a, ro2_ondulation="0x%06X" % o,
                masques=[m[i * nc:(i + 1) * nc] for i in range(np_)], ondulation=ond,
                regle="palette OBJ 2 + joueur = palette OBJ courante du joueur & (masque[perso($82)][couleur($A8)] × $10001) ; "
                      "sprite = cadre courant du joueur, X = X joueur + ondulation[(($80,A5) + joueur) & 15], "
                      "Y = 2·sol($64) − Y joueur, miroir vertical ; chaque image ; rien si Y < 0",
                note_greffe="masques indexés par les persos de SFA2 (24) : dans la greffe, le joueur est un perso de SFA3, il faut une table pour ses persos")


def ecrit(sortie, an, pix):
    json.dump(an, open(os.path.join(sortie, "sfa2_anims.json"), "w"), indent=0)
    k = sorted(pix)
    np.savez_compressed(os.path.join(sortie, "pixels_obj.npz"), banque=np.array([b for b, c in k]),
                        codes=np.array([c for b, c in k]), px=np.stack([pix[x] for x in k]))


def objets_decor(decors, anims):
    """annote chaque objet de décor (enregistrement ro2) : classe, table et animation(s)"""
    c0 = anims["classe0"]["sous_types"]; rac = {t["arcade"]: k for k, t in anims["tables"].items()}
    for d in decors:
        for o in d["objets"]:
            b = bytes.fromhex(o["brut"]); cls, sub = b[6], b[7]
            cle = "%s%02X" % (POOL.get(b[4], "?"), cls); o["classe"] = cle; o["sous_type"] = sub
            g = CLASSES.get(cle)
            if not g: o["anim"] = None; continue
            if cle == "A00": o["anim"] = dict(table=c0[sub]["table"], anims=[c0[sub]["anim"]])
            elif cle == "A01":
                pl = {4: "$23EFAE", 8: "$23F110", 12: "$243910"}.get(b[9])
                o["anim"] = dict(table=rac.get(pl), anims=[sub], plan=b[9])
            elif cle == "A02": o["anim"] = dict(table=rac.get("$05B54E"), anims=[sub])
            elif isinstance(g[1], int): o["anim"] = dict(table=rac.get("$%06X" % g[1]), anims="selon le gestionnaire")
            else: o["anim"] = dict(genre=g[0], note=g[2])


if __name__ == "__main__":
    import argparse
    from xdata import XData
    ap = argparse.ArgumentParser(); ap.add_argument("--iso", required=True); ap.add_argument("--sortie", required=True)
    a = ap.parse_args()
    X = XData(iso=a.iso); ro2 = X.mwo3(224)
    sys.path.insert(0, os.environ.get("HSFA_SRC", "<workspace>/github/src/hsfa"))
    an, tiles, pix = extrait(ro2, json.load(open(os.path.join(ICI, "carte_anims_ro2.json"))), X.entree(249), e226=X.entree(226))
    ecrit(a.sortie, an, pix)
