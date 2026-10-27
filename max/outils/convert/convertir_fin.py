"""Conversion d'un script de fin PSP (endXX_e.pac, entrée 0x20000) vers le format ARCADE (interpréteur $26FB8).
Règles établies en alignant les 32 fins d'arcade (ROM sfa3ud, table $26DCC) sur leurs fins PSP (2026-10-10) :
  - scène x1 : opword PSP 1109 (9 args) -> 1108 (8 args, le 9e PSP est retiré) ; positions a1-a3 = fonction `pos` ;
    a4 PSP = masque de couches (octet haut : bit 0 cache scroll3, bit 1 scroll2, bit 2 scroll1) -> a4 arcade (paire de
    registres de couches $272DA) = 0 (valeur de toutes les fins d'arcade) ;
  - x4 : PSP 2 args -> 1 arg = 2 × 1er arg PSP (0402 (3, 1) -> 0401 (6) ; 1402 (10, 0) -> 1401 (20)) ;
  - texte 0034 : PSP (16, 192, 0, 0) -> arcade (16, 192, n, n), n = n° GLOBAL de la table des textes de fin (la fin 1
    commence à 45, la 3 à 76) : base + k, k = n° de ligne dans l'ordre du script (base fixée à l'intégration) ;
  - fondus x2 : A200 -> 4200, F200 -> 5200 ; D200 / C200 (ajouts PSP) retirés ;
  - insertions PSP retirées (option `psp_seul`) : palettes 0904 de jeu >= `pal_max`, 0A02 (0, FFC0) avant une scène.
Usage : python3 convertir_fin.py valider   (reconvertit les fins d'arcade et mesure la concordance avec la ROM)"""
import sys, os, difflib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import script_fin as S


def convertir(ins, pos=None, pal_max=None, base_texte=0):
    """ins = [(off, att, op, args)] PSP -> [(att, op, args)] arcade ; pos(a1, a2, a3) -> (a1, a2, a3) ou None"""
    out = []; k_texte = 0; notes = collections.Counter()
    for _, att, op, args in ins:
        cl = (op >> 4) & 7; sous = (op >> 8) & 0xF
        if op == 0x1109:
            a = list(args[:8])
            if pos: a[0], a[1], a[2] = pos(a[0], a[1], a[2])
            a[3] = 0
            out.append((att, 0x1108, tuple(a))); continue
        if cl == 0 and sous == 4 and op & 0xF == 2:
            out.append((att, op - 1, (2 * args[0],))); continue          # arcade = 2 × arg PSP (durée)
        if op == 0x0034:
            out.append((att, op, (args[0], args[1], base_texte + k_texte, base_texte + k_texte))); k_texte += 1; continue
        if op in (0xA200, 0xF200):
            out.append((att, {0xA200: 0x4200, 0xF200: 0x5200}[op], args)); continue
        if op in (0xD200, 0xC200):
            notes["fondu PSP retiré %04X" % op] += 1
            if att and out: out[-1] = (out[-1][0] + att,) + out[-1][1:]   # garder la durée
            continue
        if pal_max is not None and cl == 0 and sous == 9 and len(args) > 1 and args[1] >= pal_max:
            notes["palettes PSP retirées"] += 1
            if att and out: out[-1] = (out[-1][0] + att,) + out[-1][1:]
            continue
        out.append((att, op, tuple(args)))
    return out, notes


def valider():
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
    for (_, att, op, args), (att2, op2, args2) in zip([x for x in psp if x[2] not in (0xD200, 0xC200)], base):
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
    return out, manques


def ecrire_s(ins, nom, fichier, base_texte_sym=None):
    """script arcade -> source 68K (mots gros-boutistes) ; textes : base symbolique optionnelle"""
    L = ["; script de fin %s (format arcade, interpréteur $26FB8) — généré par convertir_fin.py" % nom, "%s:" % nom]
    for att, op, args in ins:
        a = ["$%04x" % x for x in args]
        if op == 0x0034 and base_texte_sym: a[2] = a[3] = "%s+%d" % (base_texte_sym, args[2])
        L.append("        dc.w    $%04x, $%04x%s" % (att, op, (", " + ", ".join(a)) if a else ""))
    open(fichier, "w").write("\n".join(L) + "\n")
