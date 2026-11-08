#!/usr/bin/env python3
"""releves_tsv.py -- relevés de la greffe Arcade en TABLEAUX TSV (adresses, numéros, tailles, drapeaux, étiquettes),
et reconstitution EXACTE des fichiers lus par la construction (accord du 08/11 : versionnables comme la Rosette).

  python3 releves_tsv.py exporter SRC DEST       SRC = dossier de relevés (greffe/traces, greffe/donnees, eu) -> DEST/*.tsv
  python3 releves_tsv.py reconstituer TSV DEST   TSV -> fichiers d'origine (lu.txt, ram.txt, .txt, .pkl) dans DEST
  python3 releves_tsv.py verifier SRC TSV        reconstitue dans un dossier temporaire et compare a SRC (objets egaux)

Formats (une ligne d'en-tête « # » au moins : origine et mesure) :
  - journaux texte (lu.txt, ram.txt, pointeurs_prouves.txt) : en-tête + lignes d'origine inchangées
    (lu.txt : une adresse 68K / PS2 en hexa ; ram.txt : adresse RAM, 1re / dernière image lue, 1re / dernière écrite) ;
  - analyses (.pkl) : arbre en ordre préfixe, une ligne par nœud : profondeur, type, clé, valeur.
    Types : D dict, L list, T tuple, S set, i entier (hexa), f réel (repr exact), s chaîne, b booléen, n None.
    Clés de dict : « i:HEX », « s:texte », « t:HEX,HEX » (tuple d'entiers). Aucun octet du jeu n'est accepté (bytes refusés).
Lecture seule sur SRC ; n'écrit que dans DEST.
"""
import os, sys, pickle, tempfile, shutil

ORIGINE = [   # (préfixe du chemin, origine et mesure) ; le premier qui correspond
    ("greffe/traces/u_lu", "Upper (fork MAME de travail, module ro5 traduit), lua/donnees_lues*.lua : adresses de donnees lues pendant une partie Arcade (une par ligne, hexa)"),
    ("greffe/traces/defi_lu", "Upper sous MAME, lua/donnees_lues*.lua : adresses lues pendant un defi (nouveau challenger)"),
    ("greffe/traces/objets_lu", "Upper sous MAME, journaux des objets de decor (OBJETS_DECOR) : adresses lues par perso (lu_NN)"),
    ("greffe/traces/h_", "Hyper sous MAME, carte RAM (ram_hyper.lua) : adresse RAM, 1re/derniere image lue, 1re/derniere image ecrite (-1 : jamais)"),
    ("greffe/traces/u_", "Upper sous MAME, carte RAM (tournee_greffe.lua) : adresse RAM, 1re/derniere image lue, 1re/derniere image ecrite (-1 : jamais)"),
    ("greffe/donnees/pointeurs_prouves", "journal des conversions d'Upper sous MAME (lua/donnees_conv.lua) -> etape3/preuve_ptrs.py : cases (adresses exec PS2) de pointeurs de donnees prouves"),
    ("greffe/donnees/liste_arcade", "outils/liste_arcade.py : routines d'Upper executees en Arcade et jamais en VERSUS (traces d'opcodes sous MAME), croisees avec Hyper (couv_k, inverse_ro5) ; decisions"),
    ("greffe/donnees/tri_modifiees", "etape2/tri_modifiees.py : diff par branche Upper / homologue d'Hyper et decision (garder, greffer, retoucher)"),
    ("greffe/donnees/relogement_a5", "outils/relogement_a5.py : table de relogement des variables A5 d'Upper vers Hyper (traces ram.txt + analyse statique)"),
    ("greffe/donnees/homologues", "etape2/homologues.py : homologues Upper -> Hyper par propagation (modules ro5 / ro9 de l'ISO) ; regenerable a l'octet"),
    ("greffe/donnees/ram_statique", "outils/ram_statique.py : acces statiques a la RAM de travail du module (ISO) ; regenerable a l'octet"),
    ("eu/a5", "etude_upper_hyper/a5_compare.py : variables A5 d'Upper / d'Hyper (acces, routines, tailles)"),
    ("eu/bilan_absent", "etude_upper_hyper/bilan_absent.py : etat (present / modifie / absent), zone et scene de chaque routine d'Upper"),
    ("eu/couv_k", "etude_upper_hyper/couv_k.py : part des instructions de chaque routine d'Upper couverte par Hyper (K=12) ; regenerable a l'octet"),
    ("eu/inverse_ro5", "etude_upper_hyper/inverse_ro5.py : meilleure routine d'Hyper pour chaque routine d'Upper (profils carto_ro9 du 04/10)"),
]

def origine(r):
    for p, t in ORIGINE:
        if r.startswith(p): return t
    raise SystemExit("origine inconnue : " + r)

def cle(k):
    if isinstance(k, bool): raise ValueError("cle booleenne")
    if isinstance(k, int): return "i:%x" % k if k >= 0 else "i:-%x" % -k
    if isinstance(k, str): assert "\t" not in k and "\n" not in k; return "s:" + k
    if isinstance(k, tuple) and all(isinstance(x, int) and not isinstance(x, bool) for x in k):
        return "t:" + ",".join(("%x" % x if x >= 0 else "-%x" % -x) for x in k)
    raise ValueError("cle non prise en charge : %r" % (k,))

def dcle(c):
    t, v = c.split(":", 1)
    if t == "i": return int(v, 16)
    if t == "s": return v
    if t == "t": return tuple(int(x, 16) for x in v.split(",")) if v else ()
    raise ValueError(c)

SCAL = (bool, int, float, str, type(None))
VOC = {}; VOCL = []     # vocabulaire des etiquettes repetees du tableau en cours (« @n » = n-ieme etiquette)

def vocabulaire(o):
    """etiquettes (textes) vues au moins 3 fois et d'au moins 3 caracteres -> lignes « VOC n » + une etiquette par ligne"""
    import collections
    C = collections.Counter()
    def it(x):
        if isinstance(x, str): C[x] += 1
        elif isinstance(x, dict):
            for k, v in x.items(): it(v)
        elif isinstance(x, (list, tuple, set, frozenset)):
            for v in x: it(v)
    it(o)
    VOC.clear(); VOCL[:] = [s for s, n in C.most_common() if n >= 3 and len(s) >= 3]
    VOC.update({s: i for i, s in enumerate(VOCL)})
    return ["VOC\t%d" % len(VOCL)] + VOCL

def cell(v):
    """valeur scalaire -> cellule : entier = hexa nu (signe -), « =texte », « ~reel » (repr exact), « !0/!1 », « . » (vide)"""
    if isinstance(v, bool): return "!%d" % v
    if isinstance(v, int): return "%x" % v if v >= 0 else "-%x" % -v
    if isinstance(v, float): return "~%r" % v
    if isinstance(v, str):
        assert "\t" not in v and "\n" not in v
        return "@%x" % VOC[v] if v in VOC else "=" + v
    if v is None: return "."
    raise SystemExit("type non pris en charge : %s" % type(v))

INTERDITS = set(",\t\n")

def _petite_suite(v):
    """liste / tuple de scalaires dont les textes n'ont ni virgule ni crochet : une seule cellule « [a,b] » / « (a,b) »"""
    return isinstance(v, (list, tuple)) and all(_scal(x) and not (isinstance(x, str) and (INTERDITS & set(x))) for x in v)

def cellx(v):
    if isinstance(v, list): return "[" + ",".join(cell(x) for x in v) + "]"
    if isinstance(v, tuple): return "(" + ",".join(cell(x) for x in v) + ")"
    return cell(v)

def dcellx(c):
    if c[:1] in "[(":
        el = [dcell(x) for x in c[1:-1].split(",")] if len(c) > 2 else []
        return el if c[0] == "[" else tuple(el)
    return dcell(c)

def dcell(c):
    if c[:1] == "!": return c == "!1"
    if c[:1] == "~": return float(c[1:])
    if c[:1] == "=": return c[1:]
    if c[:1] == "@": return VOCL[int(c[1:], 16)]
    if c == ".": return None
    return int(c, 16)

def _scal(o): return isinstance(o, SCAL)

def ecrire(o, p, k, L):
    """nœuds : D dict, L/T/S liste / tuple / ensemble (enfants = nœuds) ; M dict de scalaires (lignes cle, cellule) ;
    LV/TV/SV suites de scalaires (une cellule par ligne) ; R enregistrements (dict ou liste de dict a cles identiques,
    ou dict de tuples, a valeurs scalaires : en-tete des colonnes puis une ligne par enregistrement) ; X scalaire"""
    c = "-" if k is None else cle(k)
    if isinstance(o, (bytes, bytearray)): raise SystemExit("octets refuses (donnee de jeu ?)")
    if isinstance(o, dict) or isinstance(o, list):
        vals = list(o.values()) if isinstance(o, dict) else o
        cles = list(o.keys()) if isinstance(o, dict) else [None] * len(o)
        if vals and all(isinstance(v, dict) for v in vals):
            cols = list(vals[0].keys())
            if cols and all(list(v.keys()) == cols for v in vals) and all(isinstance(x, str) and "\t" not in x for x in cols) \
               and all(_scal(x) or _petite_suite(x) for v in vals for x in v.values()):
                L.append("%d\tR\t%s\t%d\t%s\t%s" % (p, c, len(vals), "D" if isinstance(o, dict) else "L", "\t".join(cols)))
                for kk, v in zip(cles, vals):
                    L.append(("-" if kk is None else cle(kk)) + "\t" + "\t".join(cellx(x) for x in v.values()))
                return
        if isinstance(o, dict) and vals and all(isinstance(v, tuple) and all(_scal(x) for x in v) for v in vals):
            L.append("%d\tR\t%s\t%d\tT" % (p, c, len(vals)))
            for kk, v in zip(cles, vals): L.append(cle(kk) + ("\t" + "\t".join(cell(x) for x in v) if v else ""))
            return
        if isinstance(o, dict) and all(_scal(v) for v in vals):
            L.append("%d\tM\t%s\t%d" % (p, c, len(o)))
            for kk, v in o.items(): L.append(cle(kk) + "\t" + cell(v))
            return
    if isinstance(o, (list, tuple, set, frozenset)) and all(_scal(v) for v in o):
        ty = {list: "LV", tuple: "TV", set: "SV", frozenset: "SV"}[type(o)]
        L.append("%d\t%s\t%s\t%d" % (p, ty, c, len(o)))
        for v in o: L.append(cell(v))           # ordre d'origine garde (ensembles compris)
        return
    if isinstance(o, dict):
        L.append("%d\tD\t%s\t%d" % (p, c, len(o)))
        for x, v in o.items(): ecrire(v, p + 1, x, L)
    elif isinstance(o, (list, tuple, set, frozenset)):
        ty = {list: "L", tuple: "T", set: "S", frozenset: "S"}[type(o)]
        L.append("%d\t%s\t%s\t%d" % (p, ty, c, len(o)))
        for v in o: ecrire(v, p + 1, None, L)
    else: L.append("%d\tX\t%s\t%s" % (p, c, cell(o)))

def lire_arbre(lignes):
    """lecture recursive : chaque nœud donne son nombre d'enfants / de lignes"""
    L = [l.rstrip("\n") for l in lignes]; pos = [0]
    VOCL[:] = []
    if L and L[0].startswith("VOC\t"):
        n = int(L[0].split("\t")[1]); VOCL[:] = L[1:1 + n]; pos[0] = 1 + n
    def ligne():
        x = L[pos[0]]; pos[0] += 1; return x
    def noeud():
        f = ligne().split("\t"); ty, c = f[1], f[2]; k = None if c == "-" else dcle(c)
        if ty == "X": return k, dcell(f[3])
        n = int(f[3])
        if ty == "D":
            d = {}
            for _ in range(n): kk, vv = noeud(); d[kk] = vv
            return k, d
        if ty in ("L", "T", "S"):
            el = [noeud()[1] for _ in range(n)]
            return k, (el if ty == "L" else tuple(el) if ty == "T" else set(el))
        if ty in ("LV", "TV", "SV"):
            el = [dcell(ligne()) for _ in range(n)]
            return k, (el if ty == "LV" else tuple(el) if ty == "TV" else set(el))
        if ty == "M":
            d = {}
            for _ in range(n):
                a, b = ligne().split("\t"); d[dcle(a)] = dcell(b)
            return k, d
        if ty == "R":
            forme, cols = f[4], f[5:]
            rows = [ligne().split("\t") for _ in range(n)]
            if forme == "T": return k, {dcle(r[0]): tuple(dcell(x) for x in r[1:]) for r in rows}
            recs = [dict(zip(cols, (dcellx(x) for x in r[1:]))) for r in rows]
            return k, ({dcle(r[0]): v for r, v in zip(rows, recs)} if forme == "D" else recs)
        raise ValueError(ty)
    r = noeud()[1]; assert pos[0] == len(L), "lignes en trop"
    return r

def fichiers(src):
    for racine, _ds, fs in os.walk(src):
        for f in sorted(fs):
            yield os.path.relpath(os.path.join(racine, f), src)

GROUPES = [("u_lu", "greffe/traces/u_lu"), ("defi_lu", "greffe/traces/defi_lu/"), ("objets_lu", "greffe/traces/objets_lu/")]

def groupe(r):
    """journal de lecture (lu.txt) -> groupe ; la construction n'en lit que l'UNION par groupe (donnees2.lu_ps2 : ensemble)
    et les NOMS (greffe.json : journaux_lecture) ; les groupes sont des interrupteurs (JOURNAUX_DEFI, OBJETS_JOURNAUX)"""
    if not r.endswith("/lu.txt"): return None
    for g, p in GROUPES:
        if r.startswith(p): return g
    return None

def plages(A, pas):
    R = []
    for a in A:
        if R and a == R[-1][1] + pas: R[-1][1] = a
        else: R.append([a, a])
    return R

def ram_plages(lignes):
    """ram.txt : adresse (mot) + 4 numeros -> plages d'adresses consecutives (pas 2) aux memes numeros"""
    R = []
    for l in lignes:
        a, *v = l.split(" "); a = int(a, 16); assert "%x" % a == l.split(" ")[0] and len(v) == 4
        if R and a == R[-1][1] + 2 and v == R[-1][2]: R[-1][1] = a
        else: R.append([a, a, v])
    return [("%x" % s if s == e else "%x-%x" % (s, e)) + "\t" + "\t".join(v) for s, e, v in R]

def ram_depuis(lignes):
    out = []
    for l in lignes:
        f = l.rstrip("\n").split("\t"); s, _, e = f[0].partition("-"); s = int(s, 16); e = int(e, 16) if e else s
        out += ["%x %s\n" % (a, " ".join(f[1:])) for a in range(s, e + 1, 2)]
    return out

def exporter(src, dest):
    n = 0; J = {}
    for r in sorted(fichiers(src)):
        s = os.path.join(src, r)
        g = groupe(r)
        if g:
            noms, ens = J.setdefault(g, ([], set())); noms.append(os.path.dirname(r))
            ens.update(int(l, 16) for l in open(s)); continue
        if r.endswith(".pkl"):
            q = os.path.join(dest, r[:-4] + ".tsv"); o = pickle.load(open(s, "rb"))
            L = vocabulaire(o); ecrire(o, 0, None, L)
            entete = ["# releve de la greffe Arcade (HSFA) : %s" % r, "# origine et mesure : " + origine(r),
                      "# format : arbre prefixe (releves_tsv.py) ; nœud = profondeur, type, cle (i:hexa, s:texte, t:hexa,hexa), nombre ; "
                      "R = enregistrements (colonnes nommees), M = cle -> valeur, LV/SV = suite de valeurs ; cellules : "
                      "hexa nu = entier, =texte, @n etiquette n du vocabulaire (VOC en tete), ~reel, !0/!1 drapeau, . vide, [a,b] liste, "
                      "(a,b) tuple",
                      "# aucun octet du jeu : adresses, numeros, tailles, drapeaux, etiquettes"]
            corps = L
        else:
            q = os.path.join(dest, r + ".tsv") if not r.endswith(".tsv") else os.path.join(dest, r)
            entete = ["# releve de la greffe Arcade (HSFA) : %s" % r, "# origine et mesure : " + origine(r),
                      "# format : lignes d'origine inchangees (adresses hexa ; ram.txt : adresse, images lue 1re/derniere, "
                      "ecrite 1re/derniere)"]
            corps = open(s).read().splitlines()
            assert open(s).read() == "".join(x + "\n" for x in corps), "fin de fichier inattendue : " + r
            if r.endswith("/ram.txt"):
                corps = ram_plages(corps)
                entete[-1] = ("# format : plages d'adresses RAM « debut-fin » (pas 2) aux memes numeros ; colonnes : adresses, "
                              "1re / derniere image lue, 1re / derniere image ecrite (-1 : jamais)")
        os.makedirs(os.path.dirname(q), exist_ok=True)
        with open(q, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(entete) + "\n"); f.write("".join(x + "\n" for x in corps))
        n += 1
    for g, (noms, ens) in J.items():
        q = os.path.join(dest, "greffe", "traces", "journaux_%s.tsv" % g); os.makedirs(os.path.dirname(q), exist_ok=True)
        with open(q, "w", encoding="utf-8", newline="\n") as f:
            f.write("# releve de la greffe Arcade (HSFA) : union des %d journaux de lecture du groupe %s\n" % (len(noms), g))
            f.write("# origine et mesure : " + origine(noms[0] + "/lu.txt") + "\n")
            f.write("# format : adresses 68K lues (hexa), triees, sans doublon, en plages « debut-fin » de pas 2 (mots) ; la "
                    "construction n'utilise que l'union (etape2/donnees2.py lu_ps2) et les noms des journaux\n")
            f.write("# journaux\t" + "\t".join(noms) + "\n")
            f.write("".join(("%x\n" % s if s == e else "%x-%x\n" % (s, e)) for s, e in plages(sorted(ens), 2)))
        n += 1
    open(os.path.join(dest, "RELEVES_TSV"), "w").write("releves de la greffe Arcade en TSV (releves_tsv.py) ; reconstituer avant usage\n")
    print("exporter : %d tableaux -> %s" % (n, dest))

def reconstituer(tsv, dest):
    n = 0
    for r in sorted(fichiers(tsv)):
        if not r.endswith(".tsv"): continue
        brut = open(os.path.join(tsv, r), encoding="utf-8").read().splitlines(True)
        lignes = [l for l in brut if not l.startswith("#")]
        txt = r[:-4]
        if os.path.basename(r).startswith("journaux_"):     # union -> 1er journal du groupe ; les autres : noms seuls
            noms = [l.rstrip("\n").split("\t")[1:] for l in brut if l.startswith("# journaux\t")][0]
            adr = []
            for l in lignes:
                s, _, e = l.strip().partition("-"); s = int(s, 16); e = int(e, 16) if e else s
                adr += ["%x\n" % a for a in range(s, e + 1, 2)]
            for i, nm in enumerate(noms):
                q = os.path.join(dest, nm, "lu.txt"); os.makedirs(os.path.dirname(q), exist_ok=True)
                open(q, "w", newline="\n").write("".join(adr) if i == 0 else "")
            n += 1; continue
        if r.endswith("/ram.txt.tsv"):
            q = os.path.join(dest, txt); os.makedirs(os.path.dirname(q), exist_ok=True)
            open(q, "w", newline="\n").write("".join(ram_depuis(lignes))); n += 1; continue
        if r.startswith(("greffe/traces/",)) or txt.endswith(".txt"):
            q = os.path.join(dest, txt); os.makedirs(os.path.dirname(q), exist_ok=True)
            open(q, "w", newline="\n").write("".join(lignes))
        else:
            q = os.path.join(dest, txt + ".pkl"); os.makedirs(os.path.dirname(q), exist_ok=True)
            pickle.dump(lire_arbre(lignes), open(q, "wb"))
        n += 1
    print("reconstituer : %d fichiers -> %s" % (n, dest))

def verifier(src, tsv):
    d = tempfile.mkdtemp(prefix="verif_releves_", dir=os.path.dirname(os.path.abspath(__file__))); bad = 0
    UC = {}
    try:
        reconstituer(tsv, d)
        for r in sorted(fichiers(src)):
            a, b = os.path.join(src, r), os.path.join(d, r)
            if r.endswith(".pkl"):
                x, y = pickle.load(open(a, "rb")), pickle.load(open(b, "rb"))
                ok = x == y and _ordre(x) == _ordre(y)
            elif groupe(r):                            # journaux : union du groupe et noms
                g = groupe(r)
                if g not in UC:
                    UC[g] = [set().union(*[set(int(z, 16) for z in open(os.path.join(base, y)).read().split())
                                            for y in fichiers(base) if groupe(y) == g]) for base in (src, d)]
                ok = os.path.exists(b) and UC[g][0] == UC[g][1]
            else: ok = open(a, "rb").read() == open(b, "rb").read()
            if not ok: bad += 1; print("  DIFFERENT : " + r)
        print("verifier : %s" % ("TOUT IDENTIQUE" if not bad else "%d differences" % bad))
    finally: shutil.rmtree(d)
    return bad

def _ordre(o):
    """empreinte de l'ordre des dict / listes (les ensembles d'entiers ont un ordre deterministe)"""
    if isinstance(o, dict): return [(k, _ordre(v)) for k, v in o.items()]
    if isinstance(o, (list, tuple)): return [type(o).__name__] + [_ordre(v) for v in o]
    if isinstance(o, (set, frozenset)): return ("set", sorted(map(repr, o)))
    return (type(o).__name__, o)

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["exporter"]: exporter(a[1], a[2])
    elif a[:1] == ["reconstituer"]: reconstituer(a[1], a[2])
    elif a[:1] == ["verifier"]: sys.exit(1 if verifier(a[1], a[2]) else 0)
    else: sys.exit(__doc__)
