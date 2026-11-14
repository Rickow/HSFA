#!/usr/bin/env python3
"""(L2 des MAX dans la greffe ro9a) adaptations des SOURCES MAX pour Hyper, appliquées par prepare_max.sources() (copiée
dans l'intégration matérialisée par prep_max_ro9.py) sur le dossier src de la préparation, après la copie des sources
régénérées et du cache. Chaque motif doit être trouvé le nombre de fois attendu, sinon arrêt."""
import os, re

# sources MAX (dossier src de la préparation) : (fichier, motif regex, remplacement, nombre attendu)
SOURCES = [
    # (D10) type de projectile d'Eagle : $26 est pris dans la table d'Hyper ; $30 = 1re case de MAX_T_PROJ
    ("moteur_max_main.s", r"^(TYPE_PROJ_EAGLE\s+equ\s+)\$26\b", r"\g<1>$30   ; (L2, D10) greffe ro9a : MAX_T_PROJ", 1),
    # octet « type d'objet PSP » en $FF : écrit seulement (aucun lecteur dans le code MAX) ; dans Hyper le mot $FE est
    # employé (9 accès) : écriture retirée (un projectile fait $100 o : pas de place sûre en $3F4)
    ("brouillon_eagle.s", r"^(\s+)move\.b\s+#\$2b, \$ff\(a4\)[^\n]*$", r"\1; (L2) type PSP $2B non écrit ($FE est employé par Hyper)", 1),
    ("brouillon_yun.s", r"^(\s+)move\.b\s+#\$2c, \$ff\(a4\)[^\n]*$", r"\1; (L2) type PSP $2C non écrit ($FE est employé par Hyper)", 1),
    ("brouillon_ingrid.s", r"^(\s+)move\.b\s+#\$2d, \$ff\(a4\)[^\n]*$", r"\1; (L2) type PSP $2D non écrit ($FE est employé par Hyper)", 1),
    # (A4) arcade $80B70 (objet fils lié à l'attaque n) : n en D0 ; homologue d'Hyper 0x2EBD60 : n en D1 (appelants natifs :
    # « MOVEQ #3,D1 ; BSR », image $079920 sur ro9a39) -> D1 = D0 avant chaque appel (D0 gardé)
    ("brouillon_eagle.s", r"^(\s+)(jsr|jmp)(\s+)\$80b70\.l", r"\1move.l  d0, d1   ; (L2) Hyper 0x2EBD60 : n en D1\n\1\2\3$80b70.l", 1),
    ("brouillon_maki.s", r"^(\s+)(jsr|jmp)(\s+)\$80b70\.l", r"\1move.l  d0, d1   ; (L2) Hyper 0x2EBD60 : n en D1\n\1\2\3$80b70.l", 1),
    ("brouillon_ingrid.s", r"^(\s+)(jsr|jmp)(\s+)\$80b70\.l", r"\1move.l  d0, d1   ; (L2) Hyper 0x2EBD60 : n en D1\n\1\2\3$80b70.l", 2),
]

def adapte(src):
    for f, a, b, n in SOURCES:
        p = os.path.join(src, f); t = open(p, encoding="utf-8", errors="surrogateescape").read()
        t2, k = re.subn(a, b, t, flags=re.M)
        assert k == n, "%s : motif %r trouvé %d fois (attendu %d)" % (f, a[:60], k, n)
        open(p, "w", encoding="utf-8", errors="surrogateescape").write(t2)
    # attaques en 40 o : constantes « $A0 + 32 n » des appels de psp_66ae8 (saisies : Eagle 1, Maki 2, Yun 1, moteur 1)
    nst = 0
    for f in ("brouillon_eagle.s", "brouillon_maki.s", "brouillon_yun.s", "moteur_max_main.s"):
        p = os.path.join(src, f); t = open(p, encoding="utf-8", errors="surrogateescape").read()
        def x40(m):
            v = int(m.group(2), 16); assert v % 32 == 0, "%s : $A0 + %x" % (f, v)
            return "%s$%x%s" % (m.group(1), v // 32 * 40, m.group(3))
        t, k = re.subn(r"(addi\.l\s+#)\$([0-9a-fA-F]+)(,\s*d[0-7]\s*(?:;[^\n]*)?\n(?:\s+move\.l\s+d[0-7],\s*d1\s*\n)?\s+bsr\s+psp_66ae8\b)", x40, t)
        nst += k; open(p, "w", encoding="utf-8", errors="surrogateescape").write(t)
    assert nst == 5, "appels de psp_66ae8 : %d constantes d'attaque (5 attendues)" % nst
    # table $2B8 d'Hyper : 144 entrées (3 copies des 48, mesuré sur Ryu) ; nouvelle table ANIM_26_2B8H et gabarit
    # ANIM_26_PTRS_H AJOUTÉS à la fin de la partie « animations » du bloc (aucun symbole existant ne bouge)
    p = os.path.join(src, "anims_eagle.s"); t = open(p, encoding="utf-8", errors="surrogateescape").read()
    m = re.search(r"^ANIM_26_2B8:[^\n]*\n((?:\s+dc\.w\s+\w+-ANIM_26_2B8\s*\n)+)", t, re.M)
    e = m.group(1).replace("-ANIM_26_2B8", "-ANIM_26_2B8H"); assert e.count("dc.w") == 48, "ANIM_26_2B8 : %d entrées" % e.count("dc.w")
    g = re.search(r"^ANIM_26_PTRS:[^\n]*\n((?:\s+dc\.l\s+\w+\s*\n){12})", t, re.M)
    gh = g.group(1).replace("ANIM_26_2B8\n", "ANIM_26_2B8H\n"); assert gh.count("ANIM_26_2B8H") == 3
    t = t.rstrip("\n") + "\n; (L2, greffe ro9a) table $2B8 au format d'Hyper (144 entrées = 3 x 48) et gabarit des ismes\n" \
        "ANIM_26_2B8H:\n" + e * 3 + "ANIM_26_PTRS_H:\n" + gh
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(t)
    # attaques des PROJECTILES MAX (donnees_projectiles_max.s : blocs « A_xxx : attaques PSP … (n entrées de 32 o) ») :
    # le moteur d'Hyper les lit au pas de 40 o comme celles des joueurs -> 8 octets nuls après chaque entrée
    p = os.path.join(src, "donnees_projectiles_max.s"); L = open(p, encoding="utf-8", errors="surrogateescape").read().split("\n")
    out = []; dans = False; att = 0; nent = 0
    for l in L:
        m = re.match(r"^(A_\w+):.*\((\d+) entrées de 32 o\)", l)
        if m: dans = True; att += int(m.group(2)); out.append(l.replace("de 32 o)", "de 32 o ; (L2) 40 o pour Hyper)")); continue
        if re.match(r"^\w+:", l): dans = False
        out.append(l)
        if dans and re.match(r"^\s+dc\.b\s", l):
            assert len(l.split(";")[0].split("dc.b")[1].split(",")) == 24, "projectiles : ligne d'attaque inattendue : %s" % l
            out.append("        dcb.b   8, 0   ; (L2) Hyper : attaque de 40 o"); nent += 1
    assert nent == att and nent > 0, "projectiles : %d entrées d'attaque complétées, %d annoncées" % (nent, att)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write("\n".join(out))
    # TAB_MANIPS (moteur_max_main.s) : les talons arcade $2D6DA-$2D752 n'ont pas d'homologue simple dans Hyper (talons
    # réécrits avec des tests par perso $103 et des troncs propres) -> n° mis à 0 (« sans équivalent », psp_63708 rend 0) ;
    # aucun n'est employé par Eagle (n° 1, 3, 4, 5, 18, 23, 26 -> $2D5EA-$2D6AA, appariés par le contenu des définitions)
    p = os.path.join(src, "moteur_max_main.s"); t = open(p, encoding="utf-8", errors="surrogateescape").read()
    i = t.index("TAB_MANIPS:"); j = t.index("\n\n", i); bloc = t[i:j]
    sans = ["$2d%x" % v for v in range(0x6da, 0x753, 8)]
    nb = sum(bloc.count(x) for x in sans); assert nb == 15, "TAB_MANIPS : %d talons sans homologue trouvés (15 attendus)" % nb
    for x in sans: bloc = re.sub(r"\%s\b" % x, "0", bloc)
    t = t[:i] + bloc + "   ; (L2) n° 32-47 : talons sans homologue dans Hyper -> 0" + t[j:]
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(t)
    print("L2 : sources MAX adaptées à Hyper (type de projectile $30, attaques de 40 o, table $2B8 de 144 entrées, attaques des projectiles de 40 o : %d)" % nent)


def adapte_tout(t):
    """(L2, pas 8) tout.s : longs d'image « $LLLL0096 » = adresses d'Upper 0x96LLLL de la structure des noms (0x961AF0-
    0x969FFF) -> adresse d'Hyper (- $2C9C20, structure 0x697ED0), seulement si les 24 octets pointés sont identiques dans
    les deux modules (sinon : laissé, avis) ; aucune donnée de jeu écrite ici"""
    import re
    D = os.path.join(os.environ["L2_EXTRACT"], "decompressed") + "/"   # (prep_max_ro9 : --extract)
    r5 = open(D + "ro5_usa_prog68k.bin", "rb").read(); r9 = open(D + "ro9_usa_prog68k.bin", "rb").read(); B = 0x1F0000
    n = [0, 0]
    def rep(m):
        v = 0x00960000 | int(m.group(1), 16)
        if not 0x961AF0 <= v < 0x96A000: return m.group(0)
        h = v - 0x2C9C20
        if r5[v - B:v - B + 24] != r9[h - B:h - B + 24]: n[1] += 1; return m.group(0)
        n[0] += 1; return "dc.l    $%04X%04X   ; (L2) Hyper 0x%X (Upper 0x%X)" % (h & 0xFFFF, h >> 16, h, v)
    t = re.sub(r"dc\.l    \$([0-9A-F]{4})0096\b", rep, t)
    print("L2 : tout.s : %d pointeurs de la structure des noms passés à Hyper, %d laissés (contenu différent)" % tuple(n))
    return t
