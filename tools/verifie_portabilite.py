#!/usr/bin/env python3
"""verifie_portabilite.py -- controle automatique de portabilite (Windows) du code de construction ; Python pur, aucune
donnee : il ne lit que les sources .py du depot.

  python3 tools/verifie_portabilite.py [--liste] [--regle R] [--genere-exceptions]
  --liste               affiche chaque occurrence (fichier:ligne regle detail), exceptions comprises
  --genere-exceptions   ecrit sur la sortie le fichier d'exceptions des occurrences ACTUELLES (point de depart)

Perimetre : scripts/, src/hsfa/, tools/ (hors tools/sondes-recherche/ ; max/ n'est pas dans le perimetre).
Regles (ticket #2 et pieges Windows, docs : PIEGES_WINDOWS) :
  lien     os.symlink / os.link / Path.symlink_to / Path.hardlink_to hors de src/hsfa/liens.py
           (Windows sans droit : WinError 1314 ; liens.lien fait jonction ou copie)
  maison   os.path.expanduser / Path.home() (Windows : USERPROFILE, pas HOME)
  genere   chemin colle dans du code Python genere sans repr() ni « / » : modele de code avec une valeur entre
           guillemets (« "%s" », « '{x}' », « "{}".format ») sans !r / %r ; ou generateur a marques @XX_YY@ (fige.py)
           sans conversion « \\ » -> « / » (« C:\\Users » = SyntaxError, « \\t » = tabulation)
  encodage open() / Path.read_text / write_text en mode texte sans encoding= (Windows : cp1252)
  perso    chemin personnel absolu dans le code (chaine ou commentaire) : /home/..., C:\\Users..., /run/<support amovible>/...
  environnement  liste de variables gardees pour un environnement « propre » (contient "PATH" et "HOME") sans
           "USERPROFILE", "TEMP" ou "TMP" (Windows : « ~ » non developpe, dossier temporaire = C:\\Windows : l'exe
           PyInstaller ne s'y extrait pas sans droit) ni « _PYI_* » s'il relance sys.executable (non verifiable ici)

Exceptions : tools/verifie_portabilite_exceptions.tsv, une ligne par (regle, fichier) : nombre d'occurrences tolerees
et justification. Echec si une regle trouve PLUS d'occurrences qu'admis dans un fichier (nouveau code) ; un nombre
inferieur est signale (« a reduire ») sans echec : on part de l'existant, puis on reduit.
Code de sortie : 0 propre, 1 occurrences non admises.
"""
import argparse, ast, io, os, re, sys, tokenize
from collections import Counter, defaultdict

ICI = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.normpath(os.path.join(ICI, ".."))
RACINES = ["scripts", "src/hsfa", "tools"]
EXCLUS = ["tools/sondes-recherche/", "tools/verifie_portabilite.py"]   # ce fichier : ses motifs se trouveraient eux-memes
EXCEPTIONS = os.path.join(ICI, "verifie_portabilite_exceptions.tsv")
REGLES = ("lien", "maison", "genere", "encodage", "perso", "environnement")
LIENS_OK = {"src/hsfa/liens.py"}

PERSO = re.compile(r"/home/|/run/med[i]a/|[A-Za-z]:(?:\\\\|\\|/)Users\b", re.I)
MARQUE = re.compile(r"@[A-Z][A-Z0-9]*_[A-Z0-9_]+@")
CODE = re.compile(r"\bimport\b|sys\.path|os\.path|\bopen\(|^\s*[A-Za-z_][A-Za-z0-9_]*\s*=\s*['\"]", re.M)
GUILLEMET_PCT = re.compile(r"""(["'])%s\1""")
GUILLEMET_FMT = re.compile(r"""(["'])\{[^{}!]*\}\1""")


def fichiers():
    for r in RACINES:
        for d, ds, fs in os.walk(os.path.join(DEPOT, r)):
            ds[:] = sorted(x for x in ds if x not in ("__pycache__", ".git"))
            for f in sorted(fs):
                if not f.endswith(".py"): continue
                rel = os.path.relpath(os.path.join(d, f), DEPOT).replace(os.sep, "/")
                if any(rel.startswith(e) if e.endswith("/") else rel == e for e in EXCLUS): continue
                yield rel


def _nom(n):
    """« os.path.expanduser » pour un ast.Attribute / Name"""
    if isinstance(n, ast.Name): return n.id
    if isinstance(n, ast.Attribute):
        b = _nom(n.value); return (b + "." if b else ".") + n.attr
    return ""


def _mode(c):
    m = c.args[1] if len(c.args) > 1 else next((k.value for k in c.keywords if k.arg == "mode"), None)
    if m is None: return "r"
    if isinstance(m, ast.Constant) and isinstance(m.value, str): return m.value
    return None                                  # mode calcule : inconnu


def examine(rel, src):
    """liste (ligne, regle, detail)"""
    occ = []
    try:
        arbre = ast.parse(src, rel)
    except SyntaxError as x:
        return [(x.lineno or 0, "syntaxe", "non analysable : %s" % x.msg)]
    noeuds = list(ast.walk(arbre))
    exclusions = {id(c) for n in noeuds if isinstance(n, ast.Compare)
                  for o, c in zip(n.ops, n.comparators) if isinstance(o, ast.NotIn)}
    # generateur a marques (fige.py, fige35.py) : une marque @XX_YY@ en constante ET un « .replace(variable, ...) »
    # (les modeles eux-memes ne remplacent que des constantes ; les appelants ne font que donner les valeurs)
    generateur = MARQUE.search(src) and any(
        isinstance(n, ast.Call) and _nom(n.func).endswith(".replace") and n.args and isinstance(n.args[0], ast.Name)
        for n in ast.walk(arbre))
    for n in ast.walk(arbre):
        if isinstance(n, ast.Call):
            f = _nom(n.func); kws = {k.arg for k in n.keywords}
            if f in ("os.symlink", "os.link", "symlink") or f.endswith((".symlink_to", ".hardlink_to")):
                if rel not in LIENS_OK: occ.append((n.lineno, "lien", f))
            elif f in ("os.path.expanduser", "expanduser", "path.expanduser") or f.endswith("Path.home"):
                occ.append((n.lineno, "maison", f))
            elif f in ("open", "io.open", "builtins.open") and None not in kws and "encoding" not in kws:
                m = _mode(n)
                if m is None or "b" not in m: occ.append((n.lineno, "encodage", "open mode %s" % (m or "?")))
            elif f.endswith((".read_text", ".write_text")) and "encoding" not in kws and None not in kws:
                occ.append((n.lineno, "encodage", f.rsplit(".", 1)[1]))
            elif f.endswith(".format") and isinstance(n.func.value, ast.Constant) and isinstance(n.func.value.value, str):
                s = n.func.value.value
                if GUILLEMET_FMT.search(s) and CODE.search(s): occ.append((n.lineno, "genere", "\"{}\".format"))
        elif isinstance(n, (ast.Tuple, ast.List, ast.Set)) and id(n) not in exclusions:   # pas « k not in (...) »
            v = {e.value for e in n.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)}
            if {"PATH", "HOME"} <= v:
                manque = [x for x in ("USERPROFILE", "TEMP", "TMP") if x not in v]
                if manque: occ.append((n.lineno, "environnement", "variables gardees sans %s" % ", ".join(manque)))
        elif isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mod) and isinstance(n.left, ast.Constant) \
                and isinstance(n.left.value, str):
            s = n.left.value
            if GUILLEMET_PCT.search(s) and CODE.search(s): occ.append((n.lineno, "genere", "'\"%s\"' % ..."))
        elif isinstance(n, ast.JoinedStr):
            parts = n.values
            for i, v in enumerate(parts):
                if isinstance(v, ast.FormattedValue) and v.conversion != ord("r"):
                    av = parts[i - 1] if i else None; ap = parts[i + 1] if i + 1 < len(parts) else None
                    if isinstance(av, ast.Constant) and isinstance(ap, ast.Constant) and str(av.value)[-1:] in "'\"" \
                            and str(ap.value)[:1] == str(av.value)[-1:] and str(av.value)[-1:] \
                            and CODE.search("".join(str(p.value) for p in parts if isinstance(p, ast.Constant))):
                        occ.append((n.lineno, "genere", "f-string \"{...}\"")); break
    if generateur and not re.search(r"""replace\(\s*(['"])\\\\\1\s*,\s*(['"])/\2\s*\)|replace\(os\.sep""", src):
        occ.append((1, "genere", "marques @XX_YY@ remplacees sans « \\ » -> « / »"))
    try:
        for t in tokenize.generate_tokens(io.StringIO(src).readline):
            if t.type in (tokenize.STRING, tokenize.COMMENT) or getattr(tokenize, "FSTRING_MIDDLE", -1) == t.type:
                for l, ligne in enumerate(t.string.splitlines() or [""]):
                    m = PERSO.search(ligne)
                    if m: occ.append((t.start[0] + l, "perso", "%s : %s" % ("commentaire" if t.type == tokenize.COMMENT
                                                                            else "chaine", m.group(0))))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return occ


def lit_exceptions():
    ex = {}
    if os.path.exists(EXCEPTIONS):
        for l in open(EXCEPTIONS, encoding="utf-8"):
            if not l.strip() or l.startswith("#"): continue
            c = l.rstrip("\n").split("\t")
            ex[(c[0], c[1])] = (int(c[2]), c[3] if len(c) > 3 else "")
    return ex


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--liste", action="store_true")
    ap.add_argument("--regle")
    ap.add_argument("--genere-exceptions", action="store_true")
    a = ap.parse_args()
    tout = {}
    for rel in fichiers():
        src = open(os.path.join(DEPOT, rel), encoding="utf-8", errors="surrogateescape").read()
        tout[rel] = [o for o in examine(rel, src) if not a.regle or o[1] == a.regle]
    compte = Counter((r, rel) for rel, occ in tout.items() for (_l, r, _d) in occ)
    if a.genere_exceptions:
        print("# regle\tfichier\tnombre\tjustification")
        for (r, rel), n in sorted(compte.items()): print("%s\t%s\t%d\t%s" % (r, rel, n, "A JUSTIFIER"))
        return 0
    ex = lit_exceptions(); mauvais = []; a_reduire = []
    if a.liste:
        for rel, occ in sorted(tout.items()):
            for l, r, d in sorted(occ): print("%s:%d\t%s\t%s" % (rel, l, r, d))
    for k, n in sorted(compte.items()):
        admis = ex.get(k, (0, ""))[0]
        if n > admis: mauvais.append((k, n, admis))
    for k, (admis, _j) in sorted(ex.items()):
        if a.regle and k[0] != a.regle: continue
        if compte.get(k, 0) < admis: a_reduire.append((k, compte.get(k, 0), admis))
    par_regle = defaultdict(lambda: [0, 0])
    for (r, rel), n in compte.items():
        admis = min(n, ex.get((r, rel), (0, ""))[0]); par_regle[r][0] += n - admis; par_regle[r][1] += admis
    print("verifie_portabilite : %d fichiers .py ; par regle (non admises / admises par exception) : %s"
          % (len(tout), ", ".join("%s %d/%d" % (r, *par_regle[r]) for r in REGLES + ("syntaxe",) if r in par_regle)))
    for (r, rel), n, admis in mauvais:
        print("ECHEC %s %s : %d occurrence(s), %d admise(s)" % (r, rel, n, admis))
        for l, rr, d in sorted(tout[rel]):
            if rr == r: print("    %s:%d  %s" % (rel, l, d))
    for (r, rel), n, admis in a_reduire:
        print("a reduire : %s %s : %d au lieu de %d admises (mettre a jour %s)" % (r, rel, n, admis,
                                                                                  os.path.basename(EXCEPTIONS)))
    return 1 if mauvais else 0


if __name__ == "__main__":
    sys.exit(main())
