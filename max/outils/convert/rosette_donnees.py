"""Table de correspondances DONNÉES arcade (ROM sfa3ud) <-> PSP (EBOOT, endXX_e.pac) — 2026-10-10.
Recherche une fois pour toutes ce qui se faisait à la main : pour chaque bloc arcade connu, son équivalent PSP et la
transformation des champs. Sortie : ~/.cache/sfa3max/rosette_donnees.json.
Blocs traités (v1) : acteurs des fins (table $275DA : par fin, décalages de groupes, enregistrements de 32 octets
jusqu'à un mot négatif ; générateur $2750E ; repères de début / fin en +$18 / +$19).
Usage : python3 rosette_donnees.py acteurs"""
import os, sys, struct, json, collections
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
ROMD = os.path.expanduser("~/.cache/sfa3max/sfa3ud_donnees.bin")
SORTIE = os.path.expanduser("~/.cache/sfa3max/rosette_donnees.json")
T_ACTEURS = 0x275DA          # variante $2765E si $90(A5) != 0
NB_FINS = 33


def rom(): return open(ROMD, "rb").read()


def eboot():
    os.environ.setdefault("SFA3MAX_EBOOT", __import__("os").environ["SFA3MAX_EBOOT"])
    from relocs import img
    return img


def groupes_arcade(b, fin, table=T_ACTEURS):
    """-> [(adresse du groupe, [enregistrements de 32 o])]"""
    t = struct.unpack_from(">I", b, table + 4 * fin)[0]
    n = struct.unpack_from(">H", b, t)[0] // 2
    out = []
    for g in range(n):
        a = t + struct.unpack_from(">H", b, t + 2 * g)[0]; rec = []
        while struct.unpack_from(">h", b, a)[0] >= 0 and len(rec) < 200:
            rec.append(b[a:a + 32]); a += 32
        out.append((t + struct.unpack_from(">H", b, t + 2 * g)[0], rec))
    return t, out


def chercher_suite(img, recs, cle=(0x18, 0x19), pas=32):
    """position PSP du 1er enregistrement : mêmes octets `cle` à pas constant (au moins 3 enregistrements)"""
    if len(recs) < 2: return None
    sig = [bytes(r[k] for k in cle) for r in recs]
    p = -1
    while True:
        p = img.find(sig[0], p + 1)
        if p < 0: return None
        d = p - cle[0]
        if d >= 0 and all(img[d + i * pas + cle[0]: d + i * pas + cle[0] + len(cle)] == s for i, s in enumerate(sig[:min(len(sig), 12)])):
            return d


def comparer_champs(paires):
    """stats par octet / par mot : identique, octets échangés, écart constant"""
    st = {}
    for o in range(32):
        eq = sum(1 for a, p in paires if a[o] == p[o])
        st["o%02x" % o] = round(eq / len(paires), 3)
    mots = {}
    for o in range(0, 32, 2):
        A = [struct.unpack_from(">H", a, o)[0] for a, p in paires]; P_le = [struct.unpack_from("<H", p, o)[0] for a, p in paires]
        P_be = [struct.unpack_from(">H", p, o)[0] for a, p in paires]
        d = collections.Counter((pp - aa) & 0xFFFF for aa, pp in zip(A, P_le))
        mots["m%02x" % o] = {"=BE": round(sum(x == y for x, y in zip(A, P_be)) / len(A), 3),
                            "=LE": round(sum(x == y for x, y in zip(A, P_le)) / len(A), 3),
                            "LE-BE écart dominant": "%+d (%d %%)" % ((d.most_common(1)[0][0] ^ 0x8000) - 0x8000,
                                                                    100 * d.most_common(1)[0][1] // len(A))}
    return st, mots


def acteurs():
    b = rom(); img = eboot(); res = {"fins": {}, "paires": []}
    for fin in range(NB_FINS):
        try: t, G = groupes_arcade(b, fin)
        except Exception as e: continue
        lignes = []
        for ga, recs in G:
            d = chercher_suite(img, recs)
            lignes.append({"arcade": "%06X" % ga, "n": len(recs), "psp": None if d is None else "%06X" % d})
            if d is not None:
                for i, r in enumerate(recs): res["paires"].append((fin, r.hex(), img[d + 32 * i: d + 32 * i + 32].hex()))
        res["fins"]["%02X" % fin] = {"table": "%06X" % t, "groupes": lignes}
    paires = [(bytes.fromhex(a), bytes.fromhex(p)) for _, a, p in res["paires"]]
    if paires: res["champs"], res["mots"] = comparer_champs(paires)
    json.dump(res, open(SORTIE, "w"), indent=1)
    tr = sum(1 for f in res["fins"].values() for g in f["groupes"] if g["psp"]); tot = sum(len(f["groupes"]) for f in res["fins"].values())
    print("groupes d'acteurs arcade retrouvés dans l'EBOOT : %d / %d ; %d enregistrements appariés" % (tr, tot, len(paires)))
    return res


# ---------------- acteurs PSP -> format arcade ----------------
T_ACTEURS_PSP = 0x2B34B0      # EBOOT : 42 pointeurs (fin $00-$29) -> petite table {[0] liste des groupes, [1] fin de liste, …}


def groupes_psp(img, fin):
    U = lambda a: struct.unpack_from("<I", img, a)[0]
    t = U(T_ACTEURS_PSP + 4 * fin); L = U(t); fin_liste = U(t + 4); grp = []
    for k in range((fin_liste - L) // 4):
        v = U(L + 4 * k)
        if not 0x2B0000 <= v < 0x2D0000: break
        recs = []; a = v
        while not img[a] & 0x80 and len(recs) < 100: recs.append(img[a:a + 32]); a += 32   # fin : type >= $80 (bmi)
        grp.append(recs)
    return grp


def vers_arcade(r):
    """enregistrement PSP (32 o) -> arcade : octets 0-7 tels quels sauf +4 = (v & 7) << 5 ; mots +8..+$17 petit -> gros
    boutiste ; +$18..+$1F tels quels (repères, octets). Le n° d'animation (+3) reste celui de la PSP (table d'animations
    de la fin à construire dans le même ordre)."""
    o = bytearray(r[:8]); o[4] = (r[4] & 7) << 5
    for k in range(8, 0x18, 2): o += struct.pack(">H", struct.unpack_from("<H", r, k)[0])
    return bytes(o + r[0x18:0x20])


def acteurs_max(fin):
    img = eboot(); G = groupes_psp(img, fin)
    return [[vers_arcade(r) for r in g] for g in G]


def table_anims():
    """(banque $7F, n° d'animation PSP) -> n° arcade, voté sur les acteurs appariés des fins d'arcade (la PSP a renuméroté
    les animations des persos d'arcade ; banques >= $26 = persos MAX : numérotation PSP gardée)"""
    r = json.load(open(SORTIE)); vot = collections.defaultdict(collections.Counter)
    for f, a, p in r["paires"]:
        a = bytes.fromhex(a); p = bytes.fromhex(p)
        if a[0x1F] == p[0x1F]: vot[(a[0x1F], p[3])][a[3]] += 1
    return {k: v.most_common(1)[0][0] for k, v in vot.items()}


# ---------------- animations par CONTENU (2026-10-10) ----------------
# Repli quand le vote (banque, n° PSP) ne donne rien : l'animation n de la fin PSP (+$110 = pas 0x20001 indexés par
# 0x20003) est comparée aux animations de la banque arcade $AA644[banque] : signature temporelle (durées, fin, reprise),
# motif relatif des frames (écarts de n° PSP = écarts de rang des pointeurs arcade), ancrage absolu (frame PSP ->
# pointeur arcade appris sur les paires des fins d'arcade). Validation croisée par fin (classe $4B, banques < $20) :
# contenu juste 118 / 142 (erreurs : banque 10, où la PSP remplace des animations par une image fixe).
PAC_FIN = os.path.expanduser("~/.cache/sfa3max/data/textes/end%02x_e.pac")
_pacs, _ordre = {}, {}


def anim_fin_psp(fin, n):
    from plpac import split
    if fin not in _pacs: _pacs[fin] = {t: d for t, d in split(open(PAC_FIN % fin, "rb").read())}
    D = _pacs[fin]; idx = struct.unpack_from("<%dH" % (len(D[0x20003]) // 2), D[0x20003])
    if n >= len(idx) or idx[n] == 0xFFFF: return None
    out, v = [], idx[n]
    for k in range(80):
        d, fl, fr, ec, col = struct.unpack_from("<5H", D[0x20001], 10 * (v + k))
        out.append((fr, d & 0xFF, (d >> 8) & 0xC0, (ec - 0x10000 if ec >= 0x8000 else ec) if d & 0x8000 else None))
        if d & 0xC000: break
    return out


def anim_arcade(b, bank, m):
    L_ = lambda a: struct.unpack_from(">I", b, a)[0]
    base = L_(0xAA644 + 4 * bank); a = base + struct.unpack_from(">h", b, base + 2 * m)[0]; out = []
    for k in range(80):
        d, fl, fp = b[a + 20 * k], b[a + 20 * k + 1], L_(a + 20 * k + 4)
        out.append((fp, d, fl & 0xC0, (L_(a + 20 * k + 20) - (a + 20 * k)) // 20 if fl & 0x80 else None))
        if fl & 0xC0: break
    return out


def _sig(s): return tuple((d, fl, rep) for _, d, fl, rep in s)


def _rangs(b, bank):
    if bank not in _ordre:
        e = set()
        for m in range(120):
            try: e |= {x[0] for x in anim_arcade(b, bank, m)}
            except Exception: pass
        _ordre[bank] = {fp: i for i, fp in enumerate(sorted(e))}
    return _ordre[bank]


def ancres(b, paires):
    A = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for fin, bank, n, m in paires:
        s = anim_fin_psp(fin, n)
        if not s: continue
        a = anim_arcade(b, bank, m)
        if len(a) == len(s):
            for x, y in zip(s, a): A[bank][x[0]][y[0]] += 1
    return {k: {pf: c.most_common(1)[0][0] for pf, c in d.items()} for k, d in A.items()}


def par_contenu(b, fin, bank, n, anc):
    """-> (n° arcade, score) ou (None, 0)"""
    s = anim_fin_psp(fin, n)
    if not s or bank >= 0x20: return None, 0
    o = _rangs(b, bank); kn = anc.get(bank, {}); best = None
    for m in range(100):
        try: a = anim_arcade(b, bank, m)
        except Exception: continue
        if _sig(a) != _sig(s): continue
        sc = 1
        if all(y[0] in o for y in a) and tuple(o[y[0]] - o[a[0][0]] for y in a) == tuple(x[0] - s[0][0] for x in s): sc += 2
        sc += 3 * sum(1 for x, y in zip(s, a) if kn.get(x[0]) == y[0]) - 3 * sum(1 for x, y in zip(s, a) if x[0] in kn and kn[x[0]] != y[0])
        if best is None or sc > best[1]: best = (m, sc)
    return best if best and best[1] > 0 else (None, 0)


# ---------------- banques d'animations d'UPPER (2026-10-10) ----------------
# Base d'intégration = Upper (ro5) : table des banques des acteurs T_619b50 (PS2 0x619B50, 40 longs), module
# ANTHOLOGY_DIR/decompressed/ro5_usa_prog68k.bin, petit-boutiste, fichier = adresse PS2 − 0x1F0000. Pas de 20 o
# (mêmes octets que l'arcade, pointeur de frame en petit-boutiste). Banques 32/33 = persos d'Upper.
UPPER = os.path.join(os.environ.get("ANTHOLOGY_DIR", "anthology_extract"), "decompressed/ro5_usa_prog68k.bin")
X_UP = 0x1F0000
_up, _rup = {}, {}


def anim_upper(bank, m):
    if not _up: _up["b"] = open(UPPER, "rb").read()
    U = _up["b"]; L_ = lambda a: struct.unpack_from("<I", U, a - X_UP)[0]
    base = L_(0x619B50 + 4 * bank); a = base + struct.unpack_from("<h", U, base + 2 * m - X_UP)[0]; out = []
    for k in range(80):
        p = a + 20 * k; d, fl = U[p - X_UP], U[p - X_UP + 1]
        out.append((L_(p + 4), d, fl & 0xC0, (L_(p + 20) - p) // 20 if fl & 0x80 else None))
        if fl & 0xC0: break
    return out


def _rangs_up(bank):
    if bank not in _rup:
        e = set()
        for m in range(130):
            try: e |= {x[0] for x in anim_upper(bank, m)}
            except Exception: pass
        _rup[bank] = {fp: i for i, fp in enumerate(sorted(e))}
    return _rup[bank]


def direct_upper(fin, bank, n):
    """animations de la banque Upper de même signature ET même motif de frames que l'animation n de la fin PSP"""
    s = anim_fin_psp(fin, n)
    if not s or len(s) < 2: return []           # une image fixe seule : motif sans valeur (frame absolue inconnue)
    o = _rangs_up(bank); out = []
    for m in range(130):
        try: a = anim_upper(bank, m)
        except Exception: continue
        if _sig(a) == _sig(s) and all(y[0] in o for y in a) and \
           tuple(o[y[0]] - o[a[0][0]] for y in a) == tuple(x[0] - s[0][0] for x in s): out.append(m)
    return out


# (2026-10-11) INVITÉS DES FINS MAX : la PSP range les images des persos invités d'une fin dans le pac de COMBAT du
# perso MAX qui la possède (Charlie et Guile de la fin d'Eagle = pl26 frames 667-683 ; Fei-Long de la fin de Yun = pl28
# frames 786-806 ; trouvé en rendant ces frames après une observation PPSSPP : pendant la fin, seuls endcom / endXX /
# winXX sont ouverts). Les animations absentes d'Upper prennent donc la banque du perso MAX (FIN_ANIM_xx, n° PSP gardé,
# frames F%02X_n déjà converties). (fin, banque PSP, n° PSP) -> banque arcade
# Drapeau « PALETTE PROPRE » (demande HSFA, 2026-10-11) : octet +4 de l'enregistrement, bit 0 (jamais posé dans les
# 1 688 enregistrements d'arcade : l'arcade n'y emploie que les bits 5-7) ; recopié par le générateur en $18, bit 0.
# Posé : l'acteur garde le jeu de palettes chargé par les x9 du script de fin (pas de copie de la palette du joueur).
PALETTE_PROPRE_BIT = 0
INVITES = {(0x26, 3, 6): 0x26,      # Charlie, fin d'Eagle : boucle 681-682-683-682 (12 chacune)
           (0x28, 33, 20): 0x28}    # Fei-Long, fin de Yun : 13 pas, frames 801-806


def paires_4b():
    r = json.load(open(SORTIE))
    return sorted({(f, bytes.fromhex(a)[0x1F], bytes.fromhex(p)[3], bytes.fromhex(a)[3]) for f, a, p in r["paires"]
                   if bytes.fromhex(a)[0] == 0x4B and bytes.fromhex(a)[0x1F] == bytes.fromhex(p)[0x1F] and bytes.fromhex(a)[0x1F] < 0x20})


# ---------------- acteurs de DÉCOR propres aux fins MAX (2026-10-10) ----------------
# Classes arcade de décor : n° d'animation = entrée d'une table GLOBALE (pas de 8 o, avance $1B6B6 / $1B6F8). Les images
# propres aux fins MAX (decor_fins_max.py : FIN118_xx, frames FD%02X_n) y sont AJOUTÉES par HSFA (option a) ; l'enregistrement
# porte un n° SYMBOLIQUE ND%02X_n (fin, n° PSP) que l'intégration définit (= rang de la nouvelle entrée).
TABLE_DECOR = {(0x48, 0x01): "$81522 (mots relatifs, pas de 8 o en $50(A6))",
               (0x49, 0x00): "$2F4284 (mots relatifs, pas de 8 o)", (0x49, 0x11): "$2F4284 (mots relatifs, pas de 8 o)",
               (0x4A, 0x00): "$301FA2[$BB(A5)+2] (liste d'images : n = rang du pas de 8 o)",
               (0x4E, 0x00): "$301FA2 liste $E / $F (selon $90(A5)) (n = rang du pas de 8 o)"}
NOUVEAUX = {}
POSES = {}                                    # ID Upper -> (fin, anim PSP) des poses finales du générique ($4E/00)


def ecrire_poses(fichier):
    """pas de 8 o des poses finales (à mettre au rang ID des listes $E / $F de $301FA2), copie du pas +$118 de la fin"""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rosette_code"))
    import decor_fins_max as DF
    L = ["; poses finales du générique des persos MAX (acteur $4E/00 : $301FA2 liste $E / $F, rang = ID) — rosette_donnees.py",
         "; pas de 8 o (durée, drapeaux bit 6 = fin, 2 octets, frame) copié du pas PSP de +$118 ; frames FDxx_n = décor de la",
         "; fin (decor_fin_<perso>.s, codes LOCAUX de la banque graphique de fin) ; mettre le MÊME pas dans les listes $E et $F", ""]
    for uid, (fin, n) in sorted(POSES.items()):
        D, F, g, T, idx = DF.lire(fin); S = DF.pas8(D, idx); d, fl, fr, ec = S[idx[n]]
        L += ["MAXPOSE_%02X:            ; fin $%02X, anim PSP %d -> pas %d (P8_%02X_%d), frame %d" % (uid, fin, n, idx[n], fin, idx[n], fr),
              "        dc.b    $%02x, $%02x, $%02x, $%02x" % (d & 0xFF, d >> 8, fl & 0xFF, fl >> 8), "        dc.l    FD%02X_%d" % (fin, fr)]
    open(fichier, "w").write("\n".join(L) + "\n")


def decor_label(fin, n):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rosette_code"))
    import decor_fins_max as DF
    idx = DF.lire(fin)[4]
    return ("P8_%02X_%d" % (fin, idx[n])) if n < len(idx) else None


def ecrire_nouveaux(fichier):
    L = ["# Nouvelles entrées des tables GLOBALES d'animations de décor (fins MAX) — rosette_donnees.py", "",
         "Chaque symbole ND<fin>_<n° PSP> est à définir à l'intégration (= rang de l'entrée ajoutée dans la table) ;",
         "le label désigne le 1er pas de 8 o (decor_fin_<perso>.s, frames FD.. à codes locaux de la banque gfx de fin).", "",
         "| symbole | table (homologue Upper) | label du 1er pas | acteurs |", "|---|---|---|---|"]
    for (sym, table, lab), n in sorted(NOUVEAUX.items()): L.append("| %s | %s | %s | %d |" % (sym, table, lab, n))
    open(fichier, "w").write("\n".join(L) + "\n")


def ecrire_acteurs_s(fin, fichier):
    """groupes d'acteurs au format du générateur $2750E : table de décalages (mots) puis enregistrements, fin = $FFFF"""
    G = acteurs_max(fin); nom = "FIN%02X_ACTEURS" % fin; TA = table_anims(); B = rom(); ANC = ancres(B, paires_4b())
    L = ["; acteurs de la fin $%02X (format arcade, générateur $2750E) — rosette_donnees.py" % fin, "%s:" % nom]
    L += ["        dc.w    %s_G%d-%s" % (nom, g, nom) for g in range(len(G))]
    for g, recs in enumerate(G):
        L.append("%s_G%d:" % (nom, g))
        for r in recs:
            r = bytearray(r); note = ""
            if (r[0], r[1], r[3]) == (0x4F, 0x04, 0x5D):
                # (2026-10-18, rectangles magenta des fins) FOND DE LA FENÊTRE DE TEXTE : la PSP le dessine par sa classe
                # $4F/04 (anim $5D), l'arcade et Upper par $49/00 anim $5D en (192, 128) (1er acteur de chaque groupe de
                # Zangief : arcade $32324C, Upper 0x924A92) ; sans lui, le bas du plan 3 (palette 127 entièrement magenta)
                # apparaît sous le texte. Enregistrement arcade repris, repères +$18..+$1F de la PSP gardés.
                r = bytearray(bytes.fromhex("4900015de0000100" "00c00080" + "00" * 12) + r[0x18:0x20])
                L.append("        dc.b    " + ", ".join("$%02x" % x for x in r) + "      ; fenêtre de texte : PSP $4F/04 -> arcade $49/00 anim $5D")
                continue
            if r[0x1F] == fin and r[0] == 0x4B and not r[4] & (1 << PALETTE_PROPRE_BIT):
                # (2026-10-18, Ingrid / Maki / Yun aux couleurs fausses, relevé HSFA b16) acteur dessiné avec les frames
                # du perso MAX lui-même : sur PSP, FUN_001D4C48 lui donne l'emplacement de sprites du JOUEUR (+0x56 =
                # celui du joueur dont le perso = +0x49 = +$1F) -> palette de COMBAT du joueur, pas les palettes de fin
                # (+6 = +0xD = 0). Même drapeau « palette propre » que les invités.
                r[4] |= 1 << PALETTE_PROPRE_BIT
                L.append("        dc.b    " + ", ".join("$%02x" % x for x in r) + "      ; perso MAX lui-même (banque $%02X, anim %d) : palette du joueur (PSP : emplacement du joueur)" % (fin, r[3]))
                continue
            if 0x20 <= r[0x1F] < 0x26 and r[0] == 0x4B:
                # (2026-10-18, mosaïques des invités, relevé HSFA b16) persos AJOUTÉS par Upper (Guile $20, Fei-Long $21,
                # Dee Jay $22, T.Hawk $23) : leurs tuiles ne sont pas dans la ROM CPS2 ni chargées par la fin modèle ->
                # invité dessiné avec les frames du pac du perso MAX (FIN_ANIM n° = anim PSP), comme Charlie
                b0, n0 = r[0x1F], r[3]; r[0x1F] = fin; r[4] |= 1 << PALETTE_PROPRE_BIT
                L.append("        dc.b    " + ", ".join("$%02x" % x for x in r) + "      ; invité AJOUTÉ par Upper (banque PSP $%02X, anim %d) : frames du pac du perso MAX -> banque $%02X, FIN_ANIM n° %d" % (b0, n0, fin, n0))
                continue
            if (r[0], r[1]) == (0x4E, 0x00) and r[3] in (0x70, 0x71):
                # (2026-10-24, pose finale du générique : Ingrid violette à rectangles rouges, lot 2b21) PSP $4E/00 anim
                # $70 / $71 = animation 112 / 113 de +$118 de la fin (Ingrid : pas 30, frame FD29_76 = Ingrid en vol, vue
                # sur PPSSPP) ; l'arcade et Upper lisent $301FA2 liste $E / $F au rang +3 = ID du perso (natifs :
                # « 4e 00 00 ID ») -> +3 = ID Upper du perso MAX, pas de pose fourni dans pose_generique_max.s ; anim $71
                # (Yun : 2e image, autre groupe) -> rang ID + $10 (rangs libres au-delà des 40 ID d'Upper)
                uid = {0x26: 0x26, 0x27: 0x27, 0x28: 0x2D, 0x29: 0x2E}[fin] + (0x10 if r[3] == 0x71 else 0)
                assert POSES.get(uid, (fin, r[3])) == (fin, r[3]), (fin, uid); POSES[uid] = (fin, r[3]); n0 = r[3]; r[3] = uid
                L.append("        dc.b    " + ", ".join("$%02x" % x for x in r) + "      ; pose finale du générique : PSP $4E/00 anim %d -> rang $%02X des listes $E / $F de $301FA2 (MAXPOSE_%02X)" % (n0, uid, uid))
                continue
            if r[0x1F] < 0x26:
                k = (r[0x1F], r[3])
                D = direct_upper(fin, k[0], k[1]) if r[0] == 0x4B else []
                if D and TA.get(k) not in D:            # correspondance EXACTE sur Upper : l'emporte sur le vote
                    r[3] = D[0]; note = "      ; anim PSP %d -> Upper %d (banque %d, contenu identique%s)" % (
                        k[1], D[0], k[0], "" if TA.get(k) is None else ", vote %d écarté" % TA[k])
                elif k in TA: r[3] = TA[k]; note = "      ; anim PSP %d -> arcade %d (banque %d)" % (k[1], r[3], k[0])
                else:
                    m, sc = par_contenu(B, fin, k[0], k[1], ANC) if r[0] == 0x4B else (None, 0)
                    if m is not None:
                        r[3] = m; note = "      ; anim PSP %d -> arcade %d (banque %d, par contenu, score %d)" % (k[1], m, k[0], sc)
                    elif (fin, k[0], k[1]) in INVITES:
                        r[0x1F] = INVITES[(fin, k[0], k[1])]
                        r[4] |= 1 << PALETTE_PROPRE_BIT      # drapeau « palette propre » (symboles_externes_max.s)
                        note = "      ; invité (banque PSP %d) : images dans le pac du perso MAX -> banque $%02X, FIN_ANIM n° %d" % (k[0], r[0x1F], k[1])
                    elif k[0] >= 0x20 or r[0] == 0x4B: note = "      ; ⚠ anim PSP %d de la banque %d : absente d'Upper (animation propre à la PSP)" % (k[1], k[0])
                    elif (r[0], r[1]) in TABLE_DECOR and decor_label(fin, k[1]):
                        sym = "ND%02X_%d" % (fin, k[1]); lab = decor_label(fin, k[1])
                        NOUVEAUX[(sym, TABLE_DECOR[(r[0], r[1])], lab)] = NOUVEAUX.get((sym, TABLE_DECOR[(r[0], r[1])], lab), 0) + 1
                        txt = "        dc.b    " + ", ".join(sym if j == 3 else "$%02x" % x for j, x in enumerate(r))
                        L.append(txt + "      ; décor propre à la fin : n° symbolique (table %s), 1er pas %s" % (TABLE_DECOR[(r[0], r[1])].split()[0], lab))
                        continue
                    elif (r[0], r[1]) == (0x4F, 0x19): note = "      ; anim PSP %d gardée : acteur MAX (fin_pas118 / FIN118X, explosion = EXPLO_PAS)" % k[1]
                    elif r[0] != 0x4B: note = "      ; ⚠ anim PSP %d (classe $%02X, banque %d) : sprites propres au pac de la fin" % (k[1], r[0], k[0])
                    else: note = "      ; ⚠ anim PSP %d de la banque %d sans correspondance arcade" % (k[1], k[0])
            L.append("        dc.b    " + ", ".join("$%02x" % x for x in r) + note)
        L.append("        dc.w    $ffff")
    open(fichier, "w").write("\n".join(L) + "\n")
    return len(G), sum(map(len, G))


if __name__ == "__main__" and sys.argv[1:2] == ["acteurs_max"]:
    for f in (0x26, 0x27, 0x28, 0x29):
        d = os.path.join(os.path.expanduser(os.environ.get("SFA3MAX_CACHE", "~/.cache/sfa3max")), "converti", "pl%02x" % f, "fin"); os.makedirs(d, exist_ok=True)
        print("fin $%02X : %d groupes, %d acteurs" % ((f,) + ecrire_acteurs_s(f, os.path.join(d, "acteurs_fin_%02x.s" % f))))
    ecrire_nouveaux(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rosette_code", "decor_nouveaux_max.md"))
    ecrire_poses(os.path.join(os.path.expanduser(os.environ.get("SFA3MAX_CACHE", "~/.cache/sfa3max")), "converti", "pose_generique_max.s"))

if __name__ == "__main__" and sys.argv[1:] == ["acteurs"]:
    r = acteurs()
    print("octets identiques (part des enregistrements) :", {k: v for k, v in r.get("champs", {}).items()})
    for k, v in r.get("mots", {}).items(): print(" ", k, v)
