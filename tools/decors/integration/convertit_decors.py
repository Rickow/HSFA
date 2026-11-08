#!/usr/bin/env python3
"""convertit_decors.py — convertisseur COMMUN SFA1 / SFA2 -> lot « HSFADC01 » prêt à poser dans la zone des décors de
la greffe ro9a (rien n'est branché : ce lot est une donnée ; voir RAPPORT.md §B pour ce que la greffe devra faire).

Usage : convertit_decors.py sfa1|sfa2 ENTREES SORTIE [--base 0x537300] [--obj-code 0x...] [--ajout-s2 0x1C00]
  ENTREES : dossier qui contient <jeu>_decors.json, <jeu>_anims.json, bib_*.bin, (cel_s1.bin), pixels_obj.npz, renum.json (sfa2)
  SORTIE  : <jeu>_lot.bin (à poser en --base, adresse 68K de la zone), <jeu>_obj.bin (banque OBJ des sprites de décor,
            format MAME/FBNeo, à poser dans la région graphique à l'adresse --obj-code × 128), <jeu>_annexe_chaines.json
            (chaînes descriptives, NON greffées : rôles, adresses arcade… ; servent à l'aller-retour), <jeu>_lot.txt (carte).

Lot = en-tête + sections (voir SECTIONS) ; ORDRE PS2 (petit-boutiste), pointeurs étiquetés $01xxxxxx (format_zone.py).
Partie « plans » au format des tables par décor d'Upper (moteur d'Upper greffé dans ro9a) ; partie « animations » au
format commun HSFADC (moteurs neufs à écrire dans la greffe), rythme par table (0 = par image, 1 = par tic, 2 = une image
sur deux)."""
import os, sys, json, struct, argparse, copy
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from format_zone import Ecrivain, TAG, tlv_ecrit, encode

MOTEURS = {"sprite": 0, "tuiles_s1": 1, "tuiles_s2": 2, "tuiles_s3": 3, "palette": 4}
FAMILLE = {"sfa1": 4, "sfa2": 3}
# rythme des tables (RAPPORTS §5) : SFA1 tout par tic ; SFA2 par image, sauf classes $23, $4B, C$17, C$19 (par tic) et
# $4A (une image sur deux). Le rythme dépend de la CLASSE qui joue la table, pas de la table : rangé par classe (CLAS).
RYTHME_CLASSE_SFA2 = {"A23": 1, "A4B": 1, "C17": 1, "C19": 1, "A4A": 2}
SFA1_ADD_S2, SFA1_ADD_S3, SFA1_ADD_OBJ = 0xD400, 0x3D00, 0x400


def ro(s): return int(s, 16) if isinstance(s, str) else s


class Convertisseur:
    def __init__(self, jeu, E, base, ajout, obj_code):
        self.jeu = jeu; self.E = E; self.base = base; self.ajout = ajout; self.obj_code = obj_code
        self.D = json.load(open(os.path.join(E, "%s_decors.json" % jeu)))
        self.A = json.load(open(os.path.join(E, "%s_anims.json" % jeu)))
        self.w = Ecrivain(base); self.sections = []
        self.renum = json.load(open(os.path.join(E, "renum.json"))) if jeu == "sfa2" else None
        # SFA2 : $24 / $26 (décors 18-19, non repris : hors de la famille de tuiles) restent dans l'annexe
        self.nb = 18 if jeu == "sfa2" else len(self.D["decors"])

    # ------------------------------------------------------------------ codes de tuiles (famille de plans)
    def code_famille(self, plan, code):
        if self.jeu == "sfa1":
            return (code + (SFA1_ADD_S2 if plan == 2 else SFA1_ADD_S3)) & 0xFFFF
        return self.renum["s%d" % plan][str(code)]

    # ------------------------------------------------------------------ banque OBJ (rangées de 16 tuiles conservées)
    def banque_obj(self):
        z = np.load(os.path.join(self.E, "pixels_obj.npz"))
        if self.jeu == "sfa1":
            cles = [("obj", int(c)) for c in z["codes"]]; px = z["pixels"]
        else:
            cles = [(str(b), int(c)) for b, c in zip(z["banque"], z["codes"])]; px = z["px"]
        self.tuiles = dict(zip(cles, px))
        rangs = sorted({(b, c >> 4) for b, c in cles})
        self.rang = {r: i for i, r in enumerate(rangs)}          # (banque, rangée d'origine) -> rangée de la banque OBJ
        blob = bytearray()
        vide = np.full((16, 16), 15, np.uint8)
        for (b, r) in rangs:
            for k in range(16):
                blob += encode(self.tuiles.get((b, 16 * r + k), vide))
        self.obj_bin = bytes(blob); self.rangs = rangs
        return blob

    def code_obj(self, banque, code):
        """code de tuile d'origine (déjà en numérotation OBJ) -> code relatif à la banque OBJ (u16)"""
        return 16 * self.rang[(banque, code >> 4)] + (code & 15)

    # ------------------------------------------------------------------ sections
    def section(self, nom):
        self.w.aligne(16); self.w.etiquette(("sec", nom)); self.sections.append(nom)

    def table_decalages(self, nom, blocs):
        """table d'Upper : nb × s16 (décalage depuis le début de la table) puis données ; blocs identiques partagés"""
        self.section(nom); t0 = self.w.ici(); pos = self.w.ici()
        for _ in blocs: self.w.u16(0)
        self.w.aligne(4); vus = {}
        for i, b in enumerate(blocs):
            if b not in vus:
                vus[b] = self.w.ici() - t0; self.w.octets(b)
            d = vus[b]; assert d < 0x8000, (nom, d)
            self.w.poke16(pos + 2 * i, d)

    def plans(self):
        D = self.D; dec = D["decors"][:self.nb]; w = self.w; j1 = self.jeu == "sfa1"
        # numérotation dense des blocs (union des listes des décors repris) : indice de bibliothèque -> n° d'origine (BNUM)
        union = {p: sorted({b for d in dec for b in d.get("liste_s%d" % p, []) + (d.get("liste_s2_suite", []) if p == 2 else [])})
                 for p in (1, 2, 3)}
        self.dense = {p: {b: i for i, b in enumerate(union[p])} for p in (1, 2, 3)}
        for p in (1, 2, 3): assert len(union[p]) <= 256, p
        self.section("BNUM")
        for p in (1, 2, 3):
            w.u16(len(union[p]))
        for p in (1, 2, 3):
            for b in union[p]: w.u8(b)
        # TYPE : types s1/s2/s3 par décor ($FFFF = plan absent : SFA1 n'a pas de scroll1 de décor)
        self.section("TYPE")
        for d in dec:
            for p in (1, 2, 3): w.u16(d.get("type_s%d" % p, 0xFFFF))
        # LST1/2/3 : listes (n° denses), 128 o chacune (la routine d'Upper copie 128 o) ; longueur réelle dans LLEN
        self.section("LLEN")
        for d in dec:
            for p in (1, 2, 3): w.u8(len(d.get("liste_s%d" % p, [])))
            w.u8(len(d.get("liste_s2_suite", [])))
        for p in (1, 2, 3):
            blocs = []
            for d in dec:
                L = [self.dense[p][b] for b in d.get("liste_s%d" % p, [])]
                if p == 2 and "liste_s2_suite" in d: L += [self.dense[2][b] for b in d["liste_s2_suite"]]
                assert len(L) <= 128
                blocs.append(bytes(L) + bytes(128 - len(L)))
            self.table_decalages("LST%d" % p, blocs)
        # bibliothèques (format d'Upper) : s1 128 o (64 n° de cellule), cellule 64 o (16 × (code, attr)) ; s2 768 o
        # (256 codes puis 256 attr octets) ; s3 192 o (64 codes, 64 attr) ; code rangé = code famille − ajout du moteur
        if not j1:
            b1 = open(os.path.join(self.E, "bib_s1.bin"), "rb").read(); c1 = open(os.path.join(self.E, "cel_s1.bin"), "rb").read()
            cels = sorted({struct.unpack_from(">H", b1, 128 * b + 2 * k)[0] for b in union[1] for k in range(64)})
            self.cel_dense = {c: i for i, c in enumerate(cels)}
            self.section("BIB1")
            for b in union[1]:
                for k in range(64): w.u16(self.cel_dense[struct.unpack_from(">H", b1, 128 * b + 2 * k)[0]])
            self.section("CNUM")
            w.u16(len(cels))
            for c in cels: w.u16(c)
            self.section("CEL1")
            for c in cels:
                for i in range(16):
                    code, at = struct.unpack_from(">HH", c1, 64 * c + 4 * i)
                    w.u16((self.code_famille(1, code) - self.ajout[1]) & 0xFFFF); w.u16(at)
        for p, nom, nt in ((2, "bib_s2.bin", 256), (3, "bib_s3.bin", 64)):
            bib = open(os.path.join(self.E, nom), "rb").read(); taille = 4 * nt
            self.section("BIB%d" % p)
            for b in union[p]:
                paires = [struct.unpack_from(">HH", bib, taille * b + 4 * k) for k in range(nt)]
                for code, at in paires: w.u16((self.code_famille(p, code) - self.ajout[p]) & 0xFFFF)
                for code, at in paires:
                    assert at <= 0xFF, (p, b, at); w.u8(at)
        # palettes : 1 Ko par plan (32 palettes, mots 0RGB tels quels, luminosité 0 : le moteur fait OR $F000)
        def mots(h): return b"".join(struct.pack("<H", int(h[4 * i:4 * i + 4], 16)) for i in range(len(h) // 4))
        for p in (1, 2, 3):
            if all("pal_s%d" % p in d for d in dec):
                self.table_decalages("PAL%d" % p, [mots(d["pal_s%d" % p]) for d in dec])
        # palettes OBJ des objets de décor (telles quelles : SFA2 7 palettes ; SFA1 8 (24-31) + 16 (0-15))
        if j1:
            self.table_decalages("PLOB", [mots(d["pal_obj24"]) for d in dec])
            self.table_decalages("PLO0", [mots(d["pal_obj0"]) for d in dec])
        else:
            self.table_decalages("PLOB", [mots(d["pal_spr"]) for d in dec])
            self.section("CPSB")
            for d in dec:
                for v in d["cpsb"]: w.u16(int(v[1:], 16))
        # objets : par décor n puis enregistrements de 16 o (8 mots LE ; = « brut » mot à mot)
        blocs = []
        for d in dec:
            b = struct.pack("<H", len(d["objets"])) + bytes(2)
            for o in d["objets"]:
                r = bytes.fromhex(o["brut"]); b += b"".join(struct.pack("<H", x) for x in struct.unpack(">8H", r))
            blocs.append(b)
        self.table_decalages("OBJS", blocs)
        self.effets_parallaxe(dec)

    def effets_parallaxe(self, dec):
        """EFFT : rowscroll par décor, 16 o : type u8 (0 = constant +$C0, 1 = sol SFA1 [base $3D8 + 24 lignes, « haut »
        lignes en dégradé, 216 − haut constantes], 2 = sol SFA2 [segments bas / haut / constant / remontée], 3 = vague
        (sinus de Gen, SINU)), division u8 (0 signée, 1 asr), k u16, 4 × u16 (SFA1 : haut ; SFA2 : segments), u16 0.
        PARA : par décor et par plan s1 / s2 / s3, 8 o : pente num u8, dén u8, arrondi u8 (0 bas, 1 haut), exact u8
        (1 = formule lue / écart 0), décalage ou X0 s16, Y0 ou mode s16 (SFA1 s2 : 1 = foule de Charlie). Valeurs MESURÉES
        par les agents d'extraction (effets.json, parallaxe.json de SFA2 ; gest_s2 / gest_s3 / effet de SFA1)."""
        w = self.w; j1 = self.jeu == "sfa1"
        if not j1:
            E = json.load(open(os.path.join(self.E, "effets.json"))); PX = json.load(open(os.path.join(self.E, "parallaxe.json")))
        self.section("EFFT")
        for d in dec:
            if j1:
                e = d["effet"]; ef = self.D["effets"].get(e)
                if ef is None: w.u8(0); w.u8(0); w.u16(0); seg = []
                else: w.u8(1); w.u8(0); w.u16(ef["k"]); seg = [ef["haut"]]
            else:
                e = E[d["val"]]
                if "k" in e: w.u8(2); w.u8(1 if e["division"] == "asr" else 0); w.u16(e["k"]); seg = e["segments"]
                elif e.get("adresse") == "$1DD48": w.u8(3); w.u8(0); w.u16(0); seg = []
                else: w.u8(0); w.u8(0); w.u16(0); seg = []
            seg = list(seg) + [0] * (4 - len(seg))
            for v in seg[:4]: w.u16(v)
            w.u16(0); w.u16(0)
        self.section("PARA")
        def frac(t):
            n, _, dd = t.partition("/"); return int(n), int(dd or 1)
        for d in dec:
            if j1:
                w.u8(0); w.u8(0); w.u8(0); w.u8(0); w.s16(0); w.s16(0)                      # pas de scroll1 de décor
                g = d["gest_s2"]; w.u8(1); w.u8(1); w.u8(0); w.u8(1); w.s16(g["init_x"]); w.s16(1 if g["mode"] == "charlie" else 0)
                g = d["gest_s3"]; n, dd = frac(g["pente_x"]); w.u8(n); w.u8(dd); w.u8(0); w.u8(1); w.s16(g["x0"]); w.s16(g["y0"])
            else:
                x = PX[d["val"]]
                for pl in ("s1", "s2", "s3"):
                    if pl == "s2": w.u8(1); w.u8(1); w.u8(0); w.u8(1); w.s16(0); w.s16(0); continue
                    q = x[pl]; n, dd = frac(q["pente"])
                    w.u8(n); w.u8(dd); w.u8(1 if q["arrondi"] == "ceil" else 0); w.u8(1 if q["ecart_max"] == 0 else 0)
                    w.s16(q["decalage"]); w.s16(0)

    # ------------------------------------------------------------------ animations
    def animations(self):
        A = self.A; w = self.w; j1 = self.jeu == "sfa1"
        tables = A["tables"]
        # cibles : blocs de tuiles, entrées de palette (+ couleurs), descripteurs
        blocs = A["blocs_tuiles"] if j1 else A["blocs"]
        plan_bloc = {}
        for tk, t in tables.items():
            m = t.get("moteur") or ("tuiles_s2" if tk == "tuiles_s2" else "palette" if tk == "palettes" else "sprite")
            if m.startswith("tuiles"):
                for an in t["anims"].values():
                    for f in an["cadres"]: plan_bloc[f["ptr"]] = int(m[-1])
        self.section("BLOC")
        for k, b in blocs.items():
            w.aligne(4); w.etiquette(("cible", k)); p = plan_bloc[k]
            w.u32(ro(k)); w.u16(b["lignes"]); w.u16(b["colonnes"]); w.u16(b["mot0"]); w.u8(p)
            if j1:
                paires = list(zip(b["codes"], b["attrs"]))
                w.u8(0); w.u16(len(paires))
                for c, a in paires: w.u16(self.code_famille(p, c)); w.u16(a)
            else:
                w.u8(0); w.u16(len(b["paires"]))
                for c, a in b["paires"]: w.u16(self.code_famille(p, c)); w.u16(a)
        # couleurs (32 o, dédoublonnées)
        entrees = A["palettes"] if j1 else A["entrees_palette"]
        coul = {}
        for v in entrees.values():
            for e in v: coul.setdefault(tuple(e["couleurs"]), len(coul))
        self.section("COUL")
        for c, i in coul.items():
            w.etiquette(("coul", i))
            for x in c: w.u16(x)
        self.section("PALE")
        for k, v in entrees.items():
            w.aligne(4); w.etiquette(("cible", k)); w.u32(ro(k)); w.u16(len(v)); w.u16(0)
            for e in v:
                if j1:
                    w.u16(int(e["dest"][1:], 16)); w.u16(e["banque"]); w.u32(ro(e["source"]))
                    w.ptr(("coul", coul[tuple(e["couleurs"])])); w.u16({"s1": 1, "s2": 2, "s3": 3}[e["plan"]]); w.u16(e["pal"])
                else:
                    w.u16(e["dest"]); w.u16(e["banque"]); w.u32(e["source"])
                    w.ptr(("coul", coul[tuple(e["couleurs"])])); w.u16(0); w.u16(0)
        # descripteurs : type, n sprites résolus (code OBJ relatif à la banque, attr, x, y), puis mots d'origine (SFA2)
        self.section("DESC")
        for k, d in A["descripteurs"].items():
            w.aligne(4); w.etiquette(("cible", k)); w.u32(ro(k)); w.u16(d["type"])
            if j1:
                n = len(d["codes"]); w.u16(n); w.u16(d["total"]); w.u16(d["pos"])
                w.u16(d["attr"] if "attr" in d else 0xFFFF); w.u16(0)
                for c, a, (x, y) in zip(d["codes"], d["attrs"], d["xy"]):
                    w.u16(self.code_obj("obj", (c + SFA1_ADD_OBJ) & 0xFFFF)); w.u16(a); w.s16(x); w.s16(y)
            else:
                sp = d["sprites"]; w.u16(len(sp)); w.u16(0); w.u16(0); w.u16(0xFFFF); w.u16(len(d["mots"]))
                for s in sp:
                    b = s.get("banque", "e249")
                    w.u16(self.code_obj(b, s["code"]) | (0x8000 if "banque" in s else 0)); w.u16(s["attr"]); w.s16(s["x"]); w.s16(s["y"])
                for m in d["mots"]: w.u16(m)
        # séquences : en-tête 8 o (n cadres, fin, valeur) + cadres de 16 o
        #   cadre : durée u16, drapeaux u16, cible (ptr), dx s16, dy s16, origine u32 (adresse ro ; 0 si inconnue)
        #   fin : 0 = reprise au cadre n° valeur (SFA1), 1 = boucle au cadre n°, 2 = saut (valeur = ptr vers un cadre),
        #         3 = tenu ; bit 8 : cadres à dx/dy (tuiles SFA2)
        self.section("SEQS")
        adr_cadre = {}
        def seq(cle, an):
            w.aligne(4); w.etiquette(cle)
            fin = an.get("fin"); dxy = any("dx" in f for f in an["cadres"])
            w.u16(len(an["cadres"]))
            if fin is None: code, val = 0, an["reprise"]
            elif fin[0] == "boucle": code, val = 1, fin[1]
            elif fin[0] == "saut": code, val = 2, None
            elif fin[0] == "tenu": code, val = 3, 0
            else: raise ValueError(fin)
            w.u16(code | (0x100 if dxy else 0))
            if code == 2: self.sauts.append((w.ici(), fin[1])); w.u32(0)
            else: w.u32(val)
            for i, f in enumerate(an["cadres"]):
                if "adr" in f: adr_cadre[f["adr"]] = (cle, i, w.ici())
                w.u16(f["duree"]); w.u16(f["drap"] if j1 else f["drapeaux"])
                w.ptr(("cible", f["ptr"]) if f["ptr"] in self.cibles else None)
                if f["ptr"] not in self.cibles: self.ptr_bruts.append((w.ici() - 4, f["ptr"]))
                w.s16(f.get("dx", 0)); w.s16(f.get("dy", 0)); w.u32(ro(f.get("adr", 0)))
        self.cibles = set(blocs) | set(entrees) | set(A["descripteurs"]); self.sauts = []; self.ptr_bruts = []
        for tk, t in tables.items():
            for ak, an in t["anims"].items(): seq(("seq", tk, ak), an)
        if not j1:
            for lk, l in A["listes_palette"].items(): seq(("lpal", lk), l)
        for pos, cible in self.sauts:
            assert cible in adr_cadre, cible
            cle, i, p = adr_cadre[cible]; struct.pack_into("<I", w.b, pos, TAG | (self.base + p))
        assert not self.ptr_bruts, self.ptr_bruts[:5]
        # TABL : par table 16 o : origine, moteur u8, rythme u8, n anims u16, ptr vers les ptr de séquences, taille du cadre
        self.section("TABL")
        for tk, t in tables.items():
            m = t.get("moteur") or ("tuiles_s2" if tk == "tuiles_s2" else "palette" if tk == "palettes" else "sprite")
            w.etiquette(("table", tk))
            w.u32(ro(t.get("ro1") or t.get("ro2"))); w.u8(MOTEURS[m]); w.u8(1 if j1 else 0); w.u16(len(t["anims"]))
            w.ptr(("tptr", tk)); w.u16(t.get("taille_cadre", 0)); w.u16(0)
        for tk, t in tables.items():
            w.etiquette(("tptr", tk))
            for ak in t["anims"]: w.ptr(("seq", tk, ak))
        # NOMA : n° d'animation de chaque séquence (clés du JSON : « 0 », « 1 »… ; contrôle de l'ordre)
        self.section("NOMA")
        for tk, t in tables.items():
            for ak in t["anims"]: w.u16(int(ak))
        if not j1:
            self.section("LPAL")      # listes de palettes (canaux sans table de tête) : origine, ptr séquence
            for lk in A["listes_palette"]: w.u32(ro(lk)); w.ptr(("lpal", lk))
            # CLAS : classe -> rythme (0 image, 1 tic, 2 une image sur deux) ; SOUS : sous-types de la classe 0
            self.section("SOU0")
            st = A["classe0"]["sous_types"]; w.u16(len(st)); w.u16(0)
            for s in st: w.u16(s["anim"]); w.u16(0); w.ptr(("table", s["table"]))
            self.section("FIXE")      # cadres fixes (posés par le gestionnaire, hors tables)
            for k, c in A["cadres_fixes"].items():
                w.u32(ro(k)); w.u16(c["duree_ro2"]); w.u16(c["drapeaux_ro2"]); w.ptr(("cible", c["ptr"]))
            self.section("SINU")      # sinus de Gen (256 mots)
            for v in A["sinus_gen"]["valeurs"]: w.s16(v)
        else:
            self.section("SOU0")      # sous-types de la classe $06 : table, anim, a
            st = A["classe06"]; w.u16(len(st)); w.u16(0)
            for s in st: w.u16(s["anim"]); w.u16(s["a"]); w.ptr(("table", s["table"]))

    def classes(self):
        """CLAS : rythme par classe (SFA2) ; SFA1 : tout par tic"""
        self.section("CLAS")
        if self.jeu == "sfa2":
            cl = self.A["classes"]; self.w.u16(len(cl)); self.w.u16(0)
            for k in cl:
                self.w.u8(ord(k[0])); self.w.u8(int(k[1:], 16)); self.w.u8(RYTHME_CLASSE_SFA2.get(k, 0)); self.w.u8(0)
        else:
            self.w.u16(0); self.w.u16(0)

    # ------------------------------------------------------------------ reste (annexe TLV : nombres dans le lot)
    def reste(self):
        D = copy.deepcopy(self.D); A = copy.deepcopy(self.A)
        for d in D["decors"][:self.nb]:
            for k in ("type_s1", "type_s2", "type_s3", "liste_s1", "liste_s2", "liste_s3", "liste_s2_suite", "pal_s1", "pal_s2",
                      "pal_s3", "pal_spr", "pal_obj24", "pal_obj0", "cpsb"):
                d.pop(k, None)
            for o in d["objets"]: o.pop("brut")
        for t in A["tables"].values():
            t.pop("anims"); t.pop("moteur", None); t.pop("taille_cadre", None); t.pop("ro1", None); t.pop("ro2", None)
        for k in ("blocs_tuiles", "palettes", "descripteurs", "classe06") if self.jeu == "sfa1" else ("blocs", "entrees_palette", "descripteurs"):
            A.pop(k)
        if self.jeu == "sfa2":
            for l in A["listes_palette"].values(): l.pop("cadres"); l.pop("fin")
            A["classe0"].pop("sous_types")
            for c in A["cadres_fixes"].values():
                for k in ("duree_ro2", "drapeaux_ro2", "ptr"): c.pop(k)
            A["sinus_gen"].pop("valeurs")
        chaines = []
        tD = tlv_ecrit(D, chaines); tA = tlv_ecrit(A, chaines)
        self.section("ANXD"); self.w.u32(len(tD)); self.w.octets(tD)
        self.section("ANXA"); self.w.u32(len(tA)); self.w.octets(tA)
        self.chaines = chaines

    # ------------------------------------------------------------------ assemblage
    def construit(self):
        w = self.w
        w.octets(b"HSFADC01"); w.u16(1); w.u16(FAMILLE[self.jeu]); w.u16(self.nb); w.u16(1 if self.jeu == "sfa1" else 0)
        w.ptr(("fin",)); w.u32(self.obj_code); w.u16(self.ajout[1]); w.u16(self.ajout[2]); w.u16(self.ajout[3]); w.u16(0)
        pos_n = w.ici(); w.u16(0); w.u16(0)
        pos_dir = w.ici()
        for _ in range(40): w.octets(b"\0" * 4); w.u32(0)          # répertoire : 40 × (nom 4 o, ptr)
        self.banque_obj()
        self.section("ORNG")      # banque OBJ : rangée -> (banque d'origine 0 = obj/e249, 1 = e226 ; rangée d'origine)
        self.w.u16(len(self.rangs)); self.w.u16(0)
        for b, r in self.rangs: self.w.u16(1 if b == "e226" else 0); self.w.u16(r)
        self.plans(); self.animations(); self.classes(); self.reste()
        w.aligne(16); w.etiquette(("fin",))
        assert len(self.sections) <= 40
        w.poke16(pos_n, len(self.sections))
        for i, s in enumerate(self.sections):
            w.b[pos_dir + 8 * i:pos_dir + 8 * i + 4] = s.encode()
            w.fix.append((pos_dir + 8 * i + 4, ("sec", s)))
        return w.fin()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jeu", choices=("sfa1", "sfa2")); ap.add_argument("entrees"); ap.add_argument("sortie")
    ap.add_argument("--base", default=None, help="adresse 68K du lot dans la zone (défaut : plan de place)")
    ap.add_argument("--obj-code", default=None, help="1er code OBJ de la banque des sprites de décor (adresse graphique / 128)")
    ap.add_argument("--ajout", default="0,0x1C00,0", help="ajout du moteur d'Upper au code des plans s1,s2,s3 (DECORS.md §2)")
    a = ap.parse_args()
    PLAN = {"sfa1": (0x537300, 0x4D50000 // 128), "sfa2": (0x550000, 0x2B50000 // 128)}   # RAPPORT §A (proposition)
    base = int(a.base, 16) if a.base else PLAN[a.jeu][0]
    obj = int(a.obj_code, 16) if a.obj_code else PLAN[a.jeu][1]
    aj = [int(x, 16) if x.startswith("0x") else int(x) for x in a.ajout.split(",")]
    C = Convertisseur(a.jeu, a.entrees, base, {1: aj[0], 2: aj[1], 3: aj[2]}, obj)
    lot = C.construit()
    os.makedirs(a.sortie, exist_ok=True)
    open(os.path.join(a.sortie, "%s_lot.bin" % a.jeu), "wb").write(lot)
    open(os.path.join(a.sortie, "%s_obj.bin" % a.jeu), "wb").write(C.obj_bin)
    json.dump(C.chaines, open(os.path.join(a.sortie, "%s_annexe_chaines.json" % a.jeu), "w"), ensure_ascii=False)
    lab = C.w.lab; secs = C.sections + ["fin"]
    lignes = ["%s : lot %d o en $%06X-$%06X (étiqueté $%08X) ; banque OBJ %d o (%d rangées de 16 tuiles), 1er code $%05X" % (
        a.jeu, len(lot), base, base + len(lot) - 1, TAG | base, len(C.obj_bin), len(C.rangs), obj)]
    for i, s in enumerate(C.sections):
        d = lab[("sec", s)]; f = lab[("sec", C.sections[i + 1])] if i + 1 < len(C.sections) else lab[("fin",)]
        lignes.append("  %s  +$%05X  %7d o" % (s, d, f - d))
    open(os.path.join(a.sortie, "%s_lot.txt" % a.jeu), "w").write("\n".join(lignes) + "\n")
    print("\n".join(lignes))


if __name__ == "__main__":
    main()
