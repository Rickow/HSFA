"""Conversion d'un script de fin PSP (endXX_e.pac, entrée 0x20000) vers le format ARCADE (interpréteur $26FB8).
Règles établies en alignant les 32 fins d'arcade (ROM sfa3ud, table $26DCC) sur leurs fins PSP (2026-10-10) :
  - scène x1 : opword PSP 1109 (9 args) -> 1108 (8 args, le 9e PSP est retiré) ; positions a1-a3 = fonction `pos` ;
    a4 PSP = masque de couches (octet haut : bit 0 cache scroll3, bit 1 scroll2, bit 2 scroll1) -> a4 arcade (paire de
    registres de couches $272DA) = 0 (valeur de toutes les fins d'arcade) ;
  - x4 : PSP 2 args -> 1 arg = 2 × 1er arg PSP (0402 (3, 1) -> 0401 (6) ; 1402 (10, 0) -> 1401 (20)) ;
  - texte 0034 : PSP (16, 192, 0, 0) -> arcade (16, 192, n, n), n = n° GLOBAL de la table des textes de fin (la fin 1
    commence à 45, la 3 à 76) : base + k, k = n° de ligne dans l'ordre du script (base fixée à l'intégration) ;
  - fondus x2 : A200 -> 4200, F200 -> 5200 ; D200 / C200 (ajouts PSP) retirés ; règles F1-F3 (FONDUS, ci-dessous) ;
  - insertions PSP retirées (option `psp_seul`) : palettes 0904 de jeu >= `pal_max`, 0A02 (0, FFC0) avant une scène.
Usage : python3 convertir_fin.py valider   (reconvertit les fins d'arcade et mesure la concordance avec la ROM)
        python3 convertir_fin.py ecrire    (écrit converti/plXX/fin/script_fin_XX.s des 4 fins MAX, modèles MODELES)"""
import sys, os, difflib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import script_fin as S


def psp_seul_3204(op, args):
    """(compatibilité) toujours faux : 3204 (0, 0, 0, 0) est désormais CONVERTI (règle FONDUS, voir convertir)"""
    return False


# (2026-11-13, session MAX) RÈGLE DES FONDUS x2, établie sur l'interpréteur arcade ($26206 : 0200 recopie la page et
# lance la tâche de fondu $1801 / niveau 0 ; 2200 : $1A01 / niveau $F (vers le blanc) ; 3204 a, b, c, d : charge 4 jeux
# de palettes puis $2001 / $F (depuis le blanc) ; 4200 / 5200 : SAUVENT la base des palettes $20(A5) et passent en
# $9220 / $9240 ; 6200 : RESTAURE la base sauvée) et sur les 32 fins d'arcade contre leurs scripts PSP :
#  - F1 : « 3204 (0, 0, 0, 0) » PSP (sortie du blanc sans nouveaux jeux) = « 0200 » arcade (fins 02, 07, 0B, 18, 1C, 1D) ;
#  - F2 : les F200 PSP qui le suivent jusqu'au prochain 0301 / 0034 / 2700 / 1204 / 0A02 n'existent pas en arcade ;
#  - F3 : un 6200 PSP sans 4200 / 5200 (A200 / F200 PSP) en attente n'a rien à restaurer (arcade : base sauvée périmée,
#         0 -> palettes lues en ROM, générique de Yun noir) : retiré (fins 0D, 0F, 10, 19).
# F1 pour les fins MAX (pas d'original arcade ; référence = PSP, captures PPSSPP du 13/11 : le générique final de Yun montre
# la scène en couleurs, puis en gris) : FIN_3204 = « scene » (défaut) -> 3204 <palettes de la dernière scène 1108> (sortie du
# blanc vers la scène, comme les 3204 des fins d'arcade, dont les arguments = palettes a5-a8 du 1108 précédent) ;
# « 0200 » -> règle des natifs (fondu au noir ; mesure de `valider`) ; « psp » -> gardé tel quel.
# FIN_FONDUS_PSP=1 : ancien comportement (tout gardé).
FONDUS = os.environ.get("FIN_FONDUS_PSP") != "1"
MODE_3204 = os.environ.get("FIN_3204", "scene")


SOURCES = []                                   # (13/11) index PSP de chaque instruction produite par le dernier convertir()
def _ajoute(out, i_src, x):
    out.append(x); SOURCES.append(i_src)


def convertir(ins, pos=None, pal_max=None, base_texte=0):
    """ins = [(off, att, op, args)] PSP -> [(att, op, args)] arcade ; pos(a1, a2, a3) -> (a1, a2, a3) ou None"""
    out = []; k_texte = 0; notes = collections.Counter(); SOURCES.clear()
    apres_3204 = False; base_sauvee = False
    for i_src, (_, att, op, args) in enumerate(ins):
        cl = (op >> 4) & 7; sous = (op >> 8) & 0xF
        if FONDUS:
            if op == 0x3204 and tuple(args) == (0, 0, 0, 0) and MODE_3204 == "0200":  # F1 (natifs)
                _ajoute(out, i_src, (att, 0x0200, ())); apres_3204 = True; notes["fondu F1 : 3204 nul -> 0200"] += 1; continue
            if apres_3204 and op in (0x0301, 0x0034, 0x2700, 0x1204, 0x0A02): apres_3204 = False
            if apres_3204 and op == 0xF200:                                        # F2
                notes["fondu F2 : F200 après 3204 nul retiré"] += 1
                if att and out: out[-1] = (out[-1][0] + att,) + out[-1][1:]
                continue
            if op in (0xA200, 0xF200): base_sauvee = True
            if op == 0x6200:                                                       # F3
                if not base_sauvee:
                    notes["fondu F3 : 6200 sans base sauvée retiré"] += 1
                    if att and out: out[-1] = (out[-1][0] + att,) + out[-1][1:]
                    continue
                base_sauvee = False
        if op == 0x1109:
            a = list(args[:8])
            if pos: a[0], a[1], a[2] = pos(a[0], a[1], a[2])
            a[3] = 0
            _ajoute(out, i_src, (att, 0x1108, tuple(a))); continue
        if cl == 0 and sous == 4 and op & 0xF == 2:
            _ajoute(out, i_src, (att, op - 1, (2 * args[0],))); continue          # arcade = 2 × arg PSP (durée)
        if op == 0x0034:
            _ajoute(out, i_src, (att, op, (args[0], args[1], base_texte + k_texte, base_texte + k_texte))); k_texte += 1; continue
        if op in (0xA200, 0xF200):
            _ajoute(out, i_src, (att, {0xA200: 0x4200, 0xF200: 0x5200}[op], args)); continue
        if op in (0xD200, 0xC200) or psp_seul_3204(op, args):
            notes["fondu PSP retiré %04X" % op] += 1
            if att and out: out[-1] = (out[-1][0] + att,) + out[-1][1:]   # garder la durée
            continue
        if pal_max is not None and cl == 0 and sous == 9 and len(args) > 1 and args[1] >= pal_max:
            notes["palettes PSP retirées"] += 1
            if att and out: out[-1] = (out[-1][0] + att,) + out[-1][1:]
            continue
        _ajoute(out, i_src, (att, op, tuple(args)))
    return out, notes


def valider():
    global MODE_3204
    MODE_3204 = os.environ.get("FIN_3204", "0200")       # les natifs : règle arcade (0200)
    tot = collections.Counter(); ecarts = collections.Counter()
    for fin in range(0x20):
        p = os.path.join(S.SRC, "end%02x_e.pac" % fin)
        if not os.path.exists(p): continue
        a = [(att, op, args) for _, att, op, args in S.arcade(fin)[1]]
        q = S.psp("%02x" % fin)
        pm = 1 + max([x[3][1] for x in S.arcade(fin)[1][:len(q) + 40] if (x[2] >> 8) & 0xF == 9 and (x[2] >> 4) & 7 == 0
                      and len(x[3]) > 1] or [0])
        c, _ = convertir(q, pal_max=pm)
        a = a[:len(c) + 20]
        cle = lambda x: (x[1], x[2][3:] if x[1] == 0x1108 else x[2][:2] if x[1] == 0x34 else x[2])   # positions / n° de texte ignorés
        sm = difflib.SequenceMatcher(None, [cle(x) for x in a], [cle(x) for x in c], autojunk=False)
        ok = sum(b.size for b in sm.get_matching_blocks())
        tot["instructions converties"] += len(c); tot["identiques à la ROM (positions de scène exclues)"] += ok
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != "equal":
                ecarts["%s A:%s C:%s" % (tag, " ".join("%04x" % x[1] for x in a[i1:i2])[:24],
                                         " ".join("%04x" % x[1] for x in c[j1:j2])[:24])] += 1
    for k, v in tot.items(): print("%6d %s" % (v, k))
    print("écarts restants les plus fréquents :")
    for k, v in ecarts.most_common(15): print("%6d %s" % (v, k))


if __name__ == "__main__" and sys.argv[1:] == ["valider"]:
    valider()


def table_modele(fin):
    """alignement du script PSP de la fin d'arcade `fin` sur son script ROM -> {(op PSP, args PSP): (op, args) arcade}
    pour les scènes (1109), les x5 (palettes de scène) et les x9 (palettes) ; positions et jeux de palettes compris"""
    q = [(op, args) for _, _, op, args in S.psp("%02x" % fin)]
    a = [(op, args) for _, _, op, args in S.arcade(fin)[1]][:len(q) + 40]
    norm = lambda o: 0x1108 if o == 0x1109 else o
    sm = difflib.SequenceMatcher(None, [norm(x[0]) for x in a], [norm(x[0]) for x in q], autojunk=False)
    t = {}
    for b in sm.get_matching_blocks():
        for k in range(b.size):
            (oa, aa), (oq, aq) = a[b.a + k], q[b.b + k]
            classe0 = (oq >> 4) & 7 == 0; sous = (oq >> 8) & 0xF
            if oq == 0x1109 or (classe0 and sous in (5, 9)):
                cle = (oq, aq[:4] if oq == 0x1109 else aq[1:] if sous == 5 else aq)
                t.setdefault(cle, (oa, aa))
    return t


def convertir_avec_modele(n, fin_modele, base_texte=0):
    """script PSP de la fin MAX n -> arcade, scènes / palettes reprises de la fin d'arcade modèle (même trame d'images)"""
    T = table_modele(fin_modele); out = []; manques = collections.Counter()
    base, notes = convertir(S.psp(n), base_texte=base_texte)
    psp = S.psp(n); j = 0
    for (_, att, op, args), (att2, op2, args2) in zip([psp[i] for i in SOURCES], base):
        if op2 != op and not (op == 0x1109 and op2 == 0x1108):   # instruction transformée (fondus) : prise telle quelle
            out.append((att2, op2, args2)); continue
        sous = (op >> 8) & 0xF; classe0 = (op >> 4) & 7 == 0
        if op == 0x1109:
            m = T.get((op, args[:4]))
            if m: out.append((att2, m[0], m[1])); continue
            manques["scène %s" % " ".join("%04x" % x for x in args[:4])] += 1
        elif classe0 and sous == 5:
            m = T.get((op, args[1:]))
            if m: out.append((att2, op2, (args[0],) + m[1][1:])); continue
            sc = [x for x in out if x[1] == 0x1108]
            if sc:                                   # palettes de la dernière scène convertie
                out.append((att2, op2, (args[0],) + sc[-1][2][4:8])); manques["x5 -> palettes de la scène précédente"] += 1; continue
            manques["x5 %s" % " ".join("%04x" % x for x in args)] += 1
        elif op == 0x0A02 and os.environ.get("FIN_OPA_PSP") != "1":
            # (2026-10-18, plans gris-vert / mosaïques des fins MAX) opA arcade ($2741A -> -$50CE) = VITESSE ajoutée
            # CHAQUE IMAGE aux Y des plans ($2643E, appelée par $25F92) ; la PSP y met un décalage d'écran ($FFC0 /
            # $FFD0 dès le début : Zangief PSP $FFD0 là où l'arcade a 0). Gardé tel quel, les plans défilent sans fin
            # dans leur carte -> vitesse 0 (FIN_OPA_PSP=1 : ancien comportement)
            out.append((att2, op2, (args2[0], 0))); manques["opA PSP -> vitesse 0"] += 1; continue
        out.append((att2, op2, args2))
    if FONDUS and MODE_3204 == "scene":                  # F1 (fins MAX) : 3204 nul -> palettes de la dernière scène
        sc = None
        for k, (a_, o_, g_) in enumerate(out):
            if o_ == 0x1108: sc = g_[4:8]
            if o_ == 0x3204 and tuple(g_) == (0, 0, 0, 0) and sc:
                out[k] = (a_, o_, tuple(sc)); manques["fondu F1 : 3204 nul -> palettes de la scène %s" % " ".join("%x" % v for v in sc)] += 1
    return out, manques


def ecrire_s(ins, nom, fichier, base_texte_sym=None):
    """script arcade -> source 68K (mots gros-boutistes) ; textes : base symbolique optionnelle"""
    L = ["; script de fin %s (format arcade, interpréteur $26FB8) — généré par convertir_fin.py" % nom, "%s:" % nom]
    for att, op, args in ins:
        a = ["$%04x" % x for x in args]
        if op == 0x0034 and base_texte_sym: a[2] = a[3] = "%s+%d" % (base_texte_sym, args[2])
        L.append("        dc.w    $%04x, $%04x%s" % (att, op, (", " + ", ".join(a)) if a else ""))
    open(fichier, "w").write("\n".join(L) + "\n")


# fin d'arcade modèle de chaque fin MAX (mêmes plans / palettes de scène ; Eagle : README « Fin d'Eagle »). Yun : $06
# donne le même script que $14.
MODELES = {"26": 0x10, "27": 0x07, "28": 0x14, "29": 0x10}


def ecrire_fins(conv=None):
    """converti/plXX/fin/script_fin_XX.s (FINXX_SCRIPT, textes TEXTE_FIN_XX + k) : ce que lit l'intégration"""
    conv = conv or os.path.join(os.path.expanduser(os.environ.get("SFA3MAX_CACHE", "~/.cache/sfa3max")), "converti")
    for n, m in sorted(MODELES.items()):
        ins, _ = convertir_avec_modele(n, m)
        d = os.path.join(conv, "pl" + n, "fin"); os.makedirs(d, exist_ok=True)
        ecrire_s(ins, "FIN%s_SCRIPT" % n, os.path.join(d, "script_fin_%s.s" % n), "TEXTE_FIN_%s" % n)
        print("fin $%s : modèle $%02X, %d instructions -> %s" % (n, m, len(ins), d))


if __name__ == "__main__" and sys.argv[1:] == ["ecrire"]:
    ecrire_fins()
