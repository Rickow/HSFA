#!/usr/bin/env python3
"""relit_blocs.py — relecture d'un lot « HSFADC01 » (convertit_decors.py) : reconstruit <jeu>_decors.json et
<jeu>_anims.json DEPUIS LE LOT SEUL (+ la table des chaînes descriptives, non greffée) et les compare aux JSON d'entrée
(égalité profonde). Reconstruit aussi les bibliothèques (bib_s2/bib_s3, bib_s1/cel_s1 pour SFA2) pour les blocs utilisés.

Usage : relit_blocs.py sfa1|sfa2 BLOCS ENTREES  -> code 0 si l'aller-retour est exact.
Module : Lot(jeu, dossier_blocs) -> .decors (dict), .anims (dict), .bib (dict plan -> {n° d'origine: [(code, attr)…]}),
         .obj (banque OBJ : code relatif -> pixels), .pixels_desc(cle) …"""
import os, sys, json, struct
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from format_zone import Lecteur, TAG, tlv_lit, decode

MOTEURS = {0: "sprite", 1: "tuiles_s1", 2: "tuiles_s2", 3: "tuiles_s3", 4: "palette"}
SFA1_ADD_S2, SFA1_ADD_S3, SFA1_ADD_OBJ = 0xD400, 0x3D00, 0x400


class Lot:
    def __init__(self, jeu, dossier, entrees=None):
        self.jeu = jeu; j1 = jeu == "sfa1"
        data = open(os.path.join(dossier, "%s_lot.bin" % jeu), "rb").read()
        self.chaines = json.load(open(os.path.join(dossier, "%s_annexe_chaines.json" % jeu)))
        self.obj_bin = open(os.path.join(dossier, "%s_obj.bin" % jeu), "rb").read()
        assert data[:8] == b"HSFADC01"
        # base : déduite du pointeur de fin (étiqueté) et de la taille
        L0 = Lecteur(data, 0)
        fin = L0.u32(0x10) & 0xFFFFFF; self.base = fin - len(data); L = self.L = Lecteur(data, self.base)
        self.famille = L.u16(10); self.nb = L.u16(12); self.obj_code = L.u32(0x14)
        self.ajout = {1: L.u16(0x18), 2: L.u16(0x1A), 3: L.u16(0x1C)}
        ns = L.u16(0x20); self.sec = {}
        for i in range(ns):
            o = 0x24 + 8 * i; self.sec[data[o:o + 4].decode()] = L.ptr(o + 4)
        self.data = data
        self.renum_inv = None
        if not j1:
            r = json.load(open(os.path.join(entrees, "renum.json")))   # bijection publiée avec la famille (sfa2_plans.bin)
            self.renum_inv = {p: {v: int(k) for k, v in r[p].items()} for p in r}
        self.lit()

    # ---------------------------------------------------------------- codes
    def code_orig(self, plan, cf):
        if self.jeu == "sfa1": return (cf - (SFA1_ADD_S2 if plan == 2 else SFA1_ADD_S3)) & 0xFFFF
        return self.renum_inv["s%d" % plan][cf]

    def table_dec(self, nom, taille):
        """table d'Upper : nb décalages s16 -> blocs de taille fixe"""
        L = self.L; s = self.sec[nom]
        return [self.data[s + L.s16(s + 2 * i):s + L.s16(s + 2 * i) + taille] for i in range(self.nb)]

    def lit(self):
        L = self.L; d = self.data; j1 = self.jeu == "sfa1"; S = self.sec
        D = tlv_lit(d[S["ANXD"] + 4:S["ANXD"] + 4 + L.u32(S["ANXD"])], self.chaines)
        A = tlv_lit(d[S["ANXA"] + 4:S["ANXA"] + 4 + L.u32(S["ANXA"])], self.chaines)
        dec = D["decors"][:self.nb]
        # ---- plans
        s = S["BNUM"]; n = [L.u16(s + 2 * i) for i in range(3)]; o = s + 6; union = {}
        for p in (1, 2, 3):
            union[p] = list(d[o:o + n[p - 1]]); o += n[p - 1]
        self.union = union
        for i, e in enumerate(dec):
            for p in (1, 2, 3):
                t = L.u16(S["TYPE"] + 6 * i + 2 * (p - 1))
                if t != 0xFFFF: e["type_s%d" % p] = t
            ln = d[S["LLEN"] + 4 * i:S["LLEN"] + 4 * i + 4]
            for p in (1, 2, 3):
                if ln[p - 1] or (p > 1) or "type_s1" in e:
                    lst = self.table_dec("LST%d" % p, 128)[i]
                    k = ln[p - 1]
                    if p == 1 and "type_s1" not in e: continue
                    e["liste_s%d" % p] = [union[p][b] for b in lst[:k]]
                    if p == 2 and ln[3]: e["liste_s2_suite"] = [union[2][b] for b in lst[k:k + ln[3]]]
        hexs = lambda b: "".join("%04x" % x for x in struct.unpack("<%dH" % (len(b) // 2), b))
        for p in (1, 2, 3):
            if "PAL%d" % p in S:
                for e, b in zip(dec, self.table_dec("PAL%d" % p, 1024)): e["pal_s%d" % p] = hexs(b)
        if j1:
            for e, b in zip(dec, self.table_dec("PLOB", 256)): e["pal_obj24"] = hexs(b)
            for e, b in zip(dec, self.table_dec("PLO0", 512)): e["pal_obj0"] = hexs(b)
        else:
            for e, b in zip(dec, self.table_dec("PLOB", 224)): e["pal_spr"] = hexs(b)
            for i, e in enumerate(dec): e["cpsb"] = ["$%04X" % L.u16(S["CPSB"] + 4 * i + 2 * k) for k in range(2)]
        so = S["OBJS"]
        for i, e in enumerate(dec):
            o = so + L.s16(so + 2 * i); n_ = L.u16(o)
            for k, ob in enumerate(e["objets"]):
                ob["brut"] = struct.pack(">8H", *struct.unpack_from("<8H", d, o + 4 + 16 * k)).hex()
            assert n_ == len(e["objets"])
        # bibliothèques (blocs utilisés), en (code d'origine, attr)
        self.bib = {}
        for p, nt in ((2, 256), (3, 64)):
            s = S["BIB%d" % p]; t = 3 * nt; self.bib[p] = {}
            for i, b in enumerate(union[p]):
                o = s + t * i
                codes = [(L.u16(o + 2 * k) + self.ajout[p]) & 0xFFFF for k in range(nt)]
                attrs = list(d[o + 2 * nt:o + 3 * nt])
                self.bib[p][b] = [(self.code_orig(p, c), a) for c, a in zip(codes, attrs)]
        if not j1:
            s = S["CNUM"]; nc = L.u16(s); cels = [L.u16(s + 2 + 2 * i) for i in range(nc)]
            self.cel = {}
            for i, c in enumerate(cels):
                o = S["CEL1"] + 64 * i
                self.cel[c] = [(self.code_orig(1, (L.u16(o + 4 * k) + self.ajout[1]) & 0xFFFF), L.u16(o + 4 * k + 2)) for k in range(16)]
            self.bib[1] = {b: [cels[L.u16(S["BIB1"] + 128 * i + 2 * k)] for k in range(64)] for i, b in enumerate(union[1])}
        # ---- animations
        cible = {}       # décalage dans le lot -> (genre, clé)
        # blocs
        blocs = {}; o = S["BLOC"]; fin = S["COUL"]
        while o < fin:
            o = (o + 3) & ~3
            if o >= fin or L.u32(o) == 0: break
            k = "0x%06X" % L.u32(o); lig, col, m0, p, n_ = L.u16(o + 4), L.u16(o + 6), L.u16(o + 8), d[o + 10], L.u16(o + 12)
            pr = [(self.code_orig(p, L.u16(o + 14 + 4 * i)), L.u16(o + 16 + 4 * i)) for i in range(n_)]
            if j1: blocs[k] = dict(lignes=lig, colonnes=col, mot0=m0, codes=[c for c, a in pr], attrs=[a for c, a in pr])
            else: blocs[k] = dict(mot0=m0, lignes=lig, colonnes=col, paires=[[c, a] for c, a in pr])
            cible[o] = k; o += 14 + 4 * n_
        # entrées de palette
        ent = {}; o = S["PALE"]; fin = S["DESC"]
        while o < fin:
            o = (o + 3) & ~3
            if o >= fin or L.u32(o) == 0: break
            k = "0x%06X" % L.u32(o); n_ = L.u16(o + 4); v = []
            for i in range(n_):
                q = o + 8 + 16 * i; c = L.ptr(q + 8)
                coul = [L.u16(c + 2 * j) for j in range(16)]
                if j1: v.append(dict(dest="$%X" % L.u16(q), plan="s%d" % L.u16(q + 12), pal=L.u16(q + 14), banque=L.u16(q + 2),
                                     source="0x%06X" % L.u32(q + 4), couleurs=coul))
                else: v.append(dict(dest=L.u16(q), banque=L.u16(q + 2), source=L.u32(q + 4), couleurs=coul))
            ent[k] = v; cible[o] = k; o += 8 + 16 * n_
        # descripteurs
        desc = {}; o = S["DESC"]; fin = S["SEQS"]; self.desc_obj = {}
        while o < fin:
            o = (o + 3) & ~3
            if o >= fin or L.u32(o) == 0: break
            k = "0x%06X" % L.u32(o); t = L.u16(o + 4); n_ = L.u16(o + 6); nm = L.u16(o + 14)
            sp = [(L.u16(o + 16 + 8 * i), L.u16(o + 18 + 8 * i), L.s16(o + 20 + 8 * i), L.s16(o + 22 + 8 * i)) for i in range(n_)]
            self.desc_obj[k] = sp
            if j1:
                e = dict(type=t, total=L.u16(o + 8), pos=L.u16(o + 10))
                if L.u16(o + 12) != 0xFFFF: e["attr"] = L.u16(o + 12)
                e["codes"] = [(self.obj_orig("obj", c) - SFA1_ADD_OBJ) & 0xFFFF for c, a, x, y in sp]
                e["attrs"] = [a for c, a, x, y in sp]; e["xy"] = [[x, y] for c, a, x, y in sp]
                q = o + 16 + 8 * n_
            else:
                q = o + 16 + 8 * n_; mots = [L.u16(q + 2 * i) for i in range(nm)]; q += 2 * nm
                ss = []
                for c, a, x, y in sp:
                    b = "e226" if c & 0x8000 else "e249"
                    s_ = dict(code=self.obj_orig(b, c & 0x7FFF), attr=a, x=x, y=y)
                    if c & 0x8000: s_["banque"] = "e226"
                    ss.append(s_)
                e = dict(type=t, mots=mots, sprites=ss)
            desc[k] = e; cible[o] = k; o = q
        # séquences
        adr_cadre = {}
        def seq(o):
            n_ = L.u16(o); code = L.u16(o + 2); val = L.u32(o + 4); cadres = []
            for i in range(n_):
                q = o + 8 + 16 * i; c = L.ptr(q + 4)
                f = {}
                if not j1 and L.u32(q + 12): f["adr"] = "0x%06X" % L.u32(q + 12)
                f["duree"] = L.u16(q)
                f["drap" if j1 else "drapeaux"] = L.u16(q + 2)
                f["ptr"] = cible[c]
                if code & 0x100: f["dx"] = L.s16(q + 8); f["dy"] = L.s16(q + 10)
                cadres.append(f)
            an = dict(cadres=cadres)
            c0 = code & 0xFF
            if c0 == 0: an["reprise"] = val
            elif c0 == 1: an["fin"] = ["boucle", val]
            elif c0 == 2: an["fin"] = ["saut", ("saut", L.ptr(o + 4))]
            elif c0 == 3: an["fin"] = ["tenu"]
            for i in range(n_):
                if "adr" in cadres[i]: adr_cadre[o + 8 + 16 * i] = cadres[i]["adr"]
            return an
        s = S["TABL"]; tables = {}; noma = S["NOMA"]; ia = 0
        for tk in A["tables"]:
            t = A["tables"][tk]; q = s + 16 * len(tables)
            org = "0x%06X" % L.u32(q); m = MOTEURS[d[q + 4]]; na = L.u16(q + 6); pp = L.ptr(q + 8)
            if j1:
                t["ro1"] = org; t["taille_cadre"] = L.u16(q + 12)
            else:
                t["ro2"] = org; t["moteur"] = m
            t["anims"] = {}
            for i in range(na):
                t["anims"][str(L.u16(noma + 2 * ia))] = seq(L.ptr(pp + 4 * i)); ia += 1
            tables[tk] = t
        if not j1:
            s = S["LPAL"]
            for i, lk in enumerate(A["listes_palette"]):
                assert "0x%06X" % L.u32(s + 8 * i) == lk
                l = seq(L.ptr(s + 8 * i + 4)); A["listes_palette"][lk]["cadres"] = l["cadres"]; A["listes_palette"][lk]["fin"] = l["fin"]
        # sauts : pointeur -> adresse d'origine du cadre visé
        def corrige(x):
            if isinstance(x, list) and len(x) == 2 and x[0] == "saut" and isinstance(x[1], tuple): x[1] = adr_cadre[x[1][1]]
        for t in A["tables"].values():
            for an in t["anims"].values(): corrige(an.get("fin"))
        # tables par adresse de table (pour SOU0)
        tadr = {}
        for i, tk in enumerate(A["tables"]): tadr[s0 := S["TABL"] + 16 * i] = tk
        st = []; s = S["SOU0"]; n_ = L.u16(s)
        for i in range(n_):
            q = s + 4 + 8 * i
            if j1: st.append(dict(table=tadr[L.ptr(q + 4)], anim=L.u16(q), a=L.u16(q + 2)))
            else: st.append(dict(anim=L.u16(q), table=tadr[L.ptr(q + 4)]))
        if j1:
            A["blocs_tuiles"] = blocs; A["palettes"] = ent; A["descripteurs"] = desc; A["classe06"] = st
        else:
            A["blocs"] = blocs; A["entrees_palette"] = ent; A["descripteurs"] = desc; A["classe0"]["sous_types"] = st
            s = S["FIXE"]
            for i, k in enumerate(A["cadres_fixes"]):
                q = s + 12 * i; assert "0x%06X" % L.u32(q) == k
                c = A["cadres_fixes"][k]; c["duree_ro2"] = L.u16(q + 4); c["drapeaux_ro2"] = L.u16(q + 6); c["ptr"] = cible[L.ptr(q + 8)]
            A["sinus_gen"]["valeurs"] = [L.s16(S["SINU"] + 2 * i) for i in range(256)]
        self.decors = D; self.anims = A

    def obj_orig(self, banque, c):
        """code relatif de la banque OBJ -> code d'origine : par la table des rangées (ORNG) rangée en fin de banque OBJ"""
        r, k = divmod(c, 16); b, ro_ = self.rangs[r]; assert b == banque, (b, banque); return 16 * ro_ + k

    @property
    def rangs(self):
        if not hasattr(self, "_rangs"):
            s = self.sec["ORNG"]; n = self.L.u16(s); ban = ("obj" if self.jeu == "sfa1" else "e249", "e226")
            self._rangs = [(ban[self.L.u16(s + 4 + 4 * i)], self.L.u16(s + 6 + 4 * i)) for i in range(n)]
        return self._rangs


def charge(jeu, dossier, entrees):
    return Lot(jeu, dossier, entrees)


def main():
    jeu, B, E = sys.argv[1:4]
    lot = charge(jeu, B, E)
    D0 = json.load(open(os.path.join(E, "%s_decors.json" % jeu))); A0 = json.load(open(os.path.join(E, "%s_anims.json" % jeu)))
    ok = True
    for nom, x, y in (("decors", lot.decors, D0), ("anims", lot.anims, A0)):
        eq = x == y
        print("%s_%s.json : aller-retour %s" % (jeu, nom, "EXACT (égalité profonde)" if eq else "DIFFÉRENT"))
        if not eq:
            ok = False
            for k in y:
                if x.get(k) != y[k]:
                    print("  clé différente :", k)
                    if isinstance(y[k], dict):
                        for kk in list(y[k])[:400]:
                            if x[k].get(kk) != y[k][kk]: print("    ", kk, str(x[k].get(kk))[:200], "|", str(y[k][kk])[:200]); break
                    elif isinstance(y[k], list):
                        for i, (a, b) in enumerate(zip(x[k], y[k])):
                            if a != b:
                                for kk in b:
                                    if a.get(kk) != b[kk]: print("    ", i, kk, str(a.get(kk))[:150], "|", str(b[kk])[:150])
                                break
    # bibliothèques : blocs utilisés identiques aux fichiers d'entrée
    for p, nom, nt in ((2, "bib_s2.bin", 256), (3, "bib_s3.bin", 64)):
        bib = open(os.path.join(E, nom), "rb").read(); n = 0
        for b, paires in lot.bib[p].items():
            ref = [struct.unpack_from(">HH", bib, 4 * nt * b + 4 * k) for k in range(nt)]
            assert ref == paires, (p, b); n += 1
        print("bibliothèque s%d : %d blocs identiques" % (p, n))
    if jeu == "sfa2":
        b1 = open(os.path.join(E, "bib_s1.bin"), "rb").read(); c1 = open(os.path.join(E, "cel_s1.bin"), "rb").read()
        for b, cels in lot.bib[1].items():
            assert cels == [struct.unpack_from(">H", b1, 128 * b + 2 * k)[0] for k in range(64)]
            for c in cels: assert lot.cel[c] == [struct.unpack_from(">HH", c1, 64 * c + 4 * i) for i in range(16)]
        print("bibliothèque s1 : %d blocs, %d cellules identiques" % (len(lot.bib[1]), len(lot.cel)))
    # EFFT / PARA contre les sources (SFA1 : decors.json ; SFA2 : effets.json, parallaxe.json)
    L = lot.L; n = 0; bad = 0
    for i, d in enumerate(D0["decors"][:lot.nb]):
        q = lot.sec["EFFT"] + 16 * i; t, div, k = lot.data[q], lot.data[q + 1], L.u16(q + 2); seg = [L.u16(q + 4 + 2 * j) for j in range(4)]
        if jeu == "sfa1":
            ef = D0["effets"].get(d["effet"]); att = (0, 0, 0, [0] * 4) if ef is None else (1, 0, ef["k"], [ef["haut"], 0, 0, 0])
            pa = [(1, 1, 0, 1, d["gest_s2"]["init_x"], 1 if d["gest_s2"]["mode"] == "charlie" else 0),
                  (int(d["gest_s3"]["pente_x"].split("/")[0]), int(d["gest_s3"]["pente_x"].split("/")[1]), 0, 1, d["gest_s3"]["x0"], d["gest_s3"]["y0"])]
            plans = (2, 3)
        else:
            Ef = json.load(open(os.path.join(E, "effets.json")))[d["val"]]; PX = json.load(open(os.path.join(E, "parallaxe.json")))[d["val"]]
            if "k" in Ef: att = (2, 1 if Ef["division"] == "asr" else 0, Ef["k"], (Ef["segments"] + [0] * 4)[:4])
            elif Ef.get("adresse") == "$1DD48": att = (3, 0, 0, [0] * 4)
            else: att = (0, 0, 0, [0] * 4)
            def fr(x): a, _, b = x.partition("/"); return int(a), int(b or 1)
            pa = [(*fr(PX[pl]["pente"]), 1 if PX[pl]["arrondi"] == "ceil" else 0, 1 if PX[pl]["ecart_max"] == 0 else 0, PX[pl]["decalage"], 0) for pl in ("s1", "s3")]
            plans = (1, 3)
        n += 1; bad += (t, div, k, seg) != att
        for pl, v in zip(plans, pa):
            r = lot.sec["PARA"] + 24 * i + 8 * (pl - 1)
            n += 1; bad += (lot.data[r], lot.data[r + 1], lot.data[r + 2], lot.data[r + 3], L.s16(r + 4), L.s16(r + 6)) != v
    print("EFFT / PARA : %d entrées contrôlées contre les sources, %d écart(s)" % (n, bad)); ok &= bad == 0
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
