"""Comportements d'ACTEURS DE FIN ajoutés pour les fins MAX : traduction PSP -> 68K (DISPOSITION ARCADE), 2026-10-10.
Tables PSP des sous-types : classe $4B 0x2B2358, $4F 0x2B2A00, $49 0x2B2158 (convert/README.md § Acteurs des fins).
Contexte de traduction « acteur » (traduire.CTX["acteur"]) : objet = A6 (carte ACTEUR), 2e argument PSP = état de la
fin (globales A5 $1C6+), fonctions du moteur d'acteurs reliées par api_acteurs.json (appris_acteurs.py).
Sorties : acteurs_fins_max.s (fonctions + table sous-type -> label en tête), donnees_acteurs_fins.s (tables PSP lues).
Fermeture : toute fonction psp_X appelée et définie nulle part ailleurs est traduite à son tour.
Usage : python acteurs_fins.py"""
import os, re, sys, collections
import traduire as T
ICI = os.path.dirname(os.path.abspath(__file__))
ENTREES = [("4B", 0x52, 0x1D3844), ("4B", 0x53, 0x1D3BB8), ("4B", 0x54, 0x1D3DFC), ("4B", 0x55, 0x1D4008),
           ("4B", 0x56, 0x1D4370), ("4B", 0x57, 0x1D48AC), ("4F", 0x19, 0x1D6588), ("49", 0x2D, 0x1C9704),   # (2026-10-18) $49/$2B-$2C retirés : bouche-trous de la table PSP, aucun acteur MAX ne les emploie, et $2C heurte le sous-type 44 d'Upper
           ("49", 0x2E, 0x1C970C)]
AUTRES = ("moteur_max_main.s", "acteurs_fins_main.s")      # routines écrites à la main : appelées telles quelles. Tout le reste est retraduit
# en contexte acteur (les ébauches des persos ont pu traduire les mêmes adresses dans le contexte du perso) et
# renommé acteur_X pour ne pas entrer en conflit avec leurs étiquettes psp_X.


def definis_ailleurs():
    s = set()
    for f in AUTRES:
        s |= {int(x, 16) for x in re.findall(r"^psp_([0-9a-f]+):", open(os.path.join(ICI, f)).read(), re.M)}
    return s


def post(l):
    """lignes non résolues -> commentaires (le fichier doit s'assembler) ; lecture d'un champ sans objet -> 0"""
    m = re.match(r"^(\s*)move\.[bwl]\s+<sans objet>, (d[0-7])$", l)
    if m: return "%smoveq   #0, %s          ; (lecture d'un champ PSP sans objet sur l'arcade : 0)" % (m.group(1), m.group(2))
    m = re.match(r"^\s*move\.l\s+\$f0([0-9a-f]{2})\(a5\), (d[0-7])$", l)          # registre de rendu PSP lu (16.16)
    if m: return ("        move.w  $%s(a5), %s          ; ombre de défilement (partie entière)\n        swap    %s\n"
                  "        clr.w   %s" % (m.group(1), m.group(2), m.group(2), m.group(2)))
    m = re.match(r"^\s*move\.l\s+(d[0-7]), \$f0([0-9a-f]{2})\(a5\)$", l)          # registre de rendu PSP écrit
    if m: return ("        swap    %s\n        move.w  %s, $%s(a5)          ; ombre de défilement (partie entière)\n"
                  "        swap    %s" % (m.group(1), m.group(1), m.group(2), m.group(1)))
    m = re.match(r"^\s*; ⚠ À COMPLÉTER : \?\? (-\$50f8\(a5\)) <- .*<jonction (d[0-7])> \+ <jonction \2>\) \+ #\$2b3ec", "        ; ⚠ À COMPLÉTER : " + l.strip()) if "2b3ec" in l else None
    if m: return ("        move.l  %s, d7\n        bsr     fin_pos_4f05          ; tableau PSP 0x2B3EC = champs $40-$57 de l'acteur $4F/05\n"
                  "        move.w  d7, %s" % (m.group(2), m.group(1)))
    m = re.match(r"^(\s*)(bsr|bra|jmp|jsr)\s+psp_1d9b0$", l)                      # avance des pas de 8 o (+$118)
    if m: return "%s%s     $1b6b6.l          ; avance d'un pas de 8 o (PSP 0x1D9B0)" % (m.group(1), "jmp" if m.group(2) in ("bra", "jmp") else "jsr")
    m = re.match(r"^\s*move\.w\s+\?\?fin_0xa0, (d[0-7])$", l)                # état de fin +$A0 : décalage vertical
    if m: return ("        moveq   #0, %s          ; état de fin PSP +$A0 = décalage vertical des 3 plans, appliqué puis "
                  "remis à 0 à chaque image (0x1DA534)" % m.group(1))
    m = re.match(r"^\s*move\.w\s+(d[0-7]), \?\?fin_0xa0$", l)
    if m: return "\n".join("        add.w   %s, $%x(a5)          ; Y du plan %d (accumulateur arcade)" % (m.group(1), o, k + 1)
                           for k, o in enumerate((0x214, 0x294, 0x314)))
    if "$f0" in l and "(a5)" in l and not l.lstrip().startswith(";"): return "        ; ⚠ À COMPLÉTER (rendu) : " + l.strip()
    if "??" in l and not l.lstrip().startswith(";"): return "        ; ⚠ À COMPLÉTER : " + l.strip()
    return l


def donnees_t12c():
    """petite table d'acteurs [4] (état de fin PSP +$12C) des fins MAX -> enregistrements 68K de 32 o : mots +0..+6
    (décalages X/Y, masques aléatoires X/Y, lus en lh) petit -> gros boutiste ; octets +8..+$1F tels quels (+$B, +$D,
    +$10, +$14 lus en lbu). Nombre = jusqu'au début de la table suivante de la même fin."""
    import struct
    sys.path.insert(0, os.path.join(ICI, "..", "convert"))
    import rosette_donnees as R
    img = R.eboot(); U = lambda a: struct.unpack_from("<I", img, a)[0]
    L = ["; enregistrements +$12C des fins MAX (petite table d'acteurs [4]) — acteurs_fins.py", "FIN_T12C_VIDE:",
         "        dcb.b   32*8, 0"]
    for f in (0x27, 0x28):
        t = U(R.T_ACTEURS_PSP + 4 * f); v = [U(t + 4 * k) for k in range(6)]; a = v[4]
        n = (min(x for x in v if x > a) - a) // 32
        L.append("FIN_T12C_%02X:                ; EBOOT %#x, %d enregistrements" % (f, a, n))
        for k in range(n):
            r = img[a + 32 * k: a + 32 * k + 32]
            o = b"".join(struct.pack(">h", struct.unpack_from("<h", r, 2 * j)[0]) for j in range(4)) + r[8:]
            L.append("        dc.b    " + ", ".join("$%02x" % x for x in o))
    open(os.path.join(ICI, "donnees_fins_t12c.s"), "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    T.MODE_MAX = True; T.CTX["acteur"] = True; T.API.update(T.api_acteurs()); T.DONNEES.clear()
    ailleurs = definis_ailleurs(); faits = set(); a_faire = [f for _, _, f in ENTREES]; corps = []
    while a_faire:
        f = a_faire.pop(0)
        if f in faits or f in ailleurs: continue
        L = T.traduire_tout(f); bloc = []; garder = True
        if not any(l.startswith("psp_%x:" % f) for l in L):              # traduire_tout n'étiquette pas la racine
            L = ["psp_%x:" % f] + L
        for l in L:
            m = re.match(r"^psp_([0-9a-f]+):", l)
            if m:
                g = int(m.group(1), 16); garder = g not in faits and g not in ailleurs; faits.add(g)
            if garder: bloc.append(post(l))
        corps += bloc
        appeles = {int(x, 16) for x in re.findall(r"\bpsp_([0-9a-f]+)\b", "\n".join(bloc))}
        a_faire += sorted(appeles - faits - ailleurs)
    racines = {f for _, _, f in ENTREES}
    while True:                                   # fonctions émises que plus rien n'appelle (appelant écrit à la main)
        blocs, cour = {}, None
        for l in corps:
            m = re.match(r"^psp_([0-9a-f]+):", l)
            if m: cour = int(m.group(1), 16)
            blocs.setdefault(cour, []).append(l)
        refs = collections.Counter()
        for f, ls in blocs.items():
            for x in re.findall(r"\bpsp_([0-9a-f]+)\b", "\n".join(l for l in ls if not re.match(r"^psp_", l))):
                if int(x, 16) != f: refs[int(x, 16)] += 1
        morts = [f for f in blocs if f is not None and f not in racines and not refs[f]]
        if not morts: break
        corps = [l for f, ls in blocs.items() if f not in morts for l in ls]
    emis = {int(x, 16) for x in re.findall(r"^psp_([0-9a-f]+):", "\n".join(corps), re.M)}
    nom = lambda m: ("acteur_" if int(m.group(1), 16) in emis else "psp_") + m.group(1)
    corps = [re.sub(r"\bpsp_([0-9a-f]+)\b", nom, l) for l in corps]
    corps = [re.sub(r"\b([LJTP])_(?=[0-9a-z])", r"A\1_", l) for l in corps]      # étiquettes locales : AL_, AJ_, AT_, AP_
    tete = ["; comportements d'ACTEURS DE FIN ajoutés pour les fins MAX — acteurs_fins.py, DISPOSITION ARCADE",
            "; objet = A6 (réservoir $1C2C8) ; état de la fin = globales A5 ($1C6-$1D5 : repère $1C8, événement $1CA)",
            "; table sous-type -> label :"]
    tete += [";   classe $%s sous-type $%02X -> acteur_%x" % (c, s, f) for c, s, f in ENTREES]
    open(os.path.join(ICI, "acteurs_fins_max.s"), "w").write("\n".join(tete + corps) + "\n")
    donnees_t12c()
    n_d = T.ecrire_donnees(os.path.join(ICI, "donnees_acteurs_fins.s"))
    print("fonctions : %d ; lignes à compléter : %d ; tables de données : %s" % (
        len(faits), sum(1 for l in corps if "À COMPLÉTER" in l), n_d))
