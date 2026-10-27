#!/usr/bin/env python3
"""verifier_imports.py -- verifie que chaque import Python du depot se resout depuis l'emplacement ACTUEL du fichier.

Pour chaque fichier .py suivi par git :
  1. compilation (py_compile, sans ecrire de .pyc) ;
  2. analyse statique (ast) des imports absolus (`import x`, `from x import y`, `__import__("x")`) ;
  3. resolution de chaque module dans : la bibliotheque standard, les dependances tierces (requirements.txt et
     dependances facultatives connues), le dossier du fichier, puis les dossiers ajoutes a sys.path par le fichier
     (sys.path.insert / append / sys.path[:0] = [...], expressions os.path.* sur __file__ evaluees).

Les chemins de l'espace de travail sont ecrits `<workspace>/...` dans le depot. Ils sont projetes sur le depot
par la table CORRESPONDANCES ci-dessous (la meme que scripts/localiser.py et que publier.sh) ; un chemin
`<workspace>/work/...` designe un dossier de travail NON publie : un module trouve seulement la est classe
« externe » (dependance a l'espace de travail, pas une erreur du depot).

Usage : python3 scripts/qualite/verifier_imports.py [--detail] [--json FICHIER]
Code de sortie : 1 si une compilation echoue ou si un import est introuvable (classe « ECHEC »).
"""
import ast, json, os, py_compile, subprocess, sys, tempfile

RACINE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

# <workspace>/... -> dossiers du depot : table partagee scripts/correspondances.tsv (prefixe le plus long d'abord).
def charge_correspondances():
    t = {}
    for l in open(os.path.join(RACINE, "scripts", "correspondances.tsv"), encoding="utf-8"):
        if l.startswith("#") or not l.strip():
            continue
        src, dst = l.rstrip("\n").split("\t")
        t.setdefault(src, []).append(dst)
    return sorted(t.items(), key=lambda kv: -len(kv[0]))


CORRESPONDANCES = charge_correspondances()

TIERS = {           # module importe -> paquet (requirements.txt) ; None = facultatif, hors requirements
    "numpy": "numpy", "capstone": "capstone", "PIL": "pillow",
    "zstandard": None, "pyghidra": None, "jpype": None, "matplotlib": None, "psd_tools": None, "scipy": None, "z80": None,
    "ghidra": None,     # API de script de Ghidra (legacy/tools/decomp.py s'execute DANS Ghidra)
}


def projette(chemin, fichier):
    """chemin litteral -> liste de dossiers du depot (absolus) ; [] si dossier de travail non publie.
    '.' (dossier courant) = dossier du fichier : ces scripts se lancent depuis leur dossier."""
    if chemin in (".", "./"):
        return [os.path.dirname(fichier)]
    if not chemin.startswith("<workspace>"):
        return [chemin]
    for pre, cibles in CORRESPONDANCES:
        if chemin == pre or chemin.startswith(pre + "/"):
            reste = chemin[len(pre):].lstrip("/")
            res = [os.path.normpath(os.path.join(RACINE, c, reste)) for c in cibles]
            return [r for r in res if os.path.isdir(r)]     # copie non publiee -> [] (externe)
    return []


class Evaluateur(ast.NodeVisitor):
    """evalue (au mieux) les expressions de chemin d'un module : constantes, __file__, os.path.*, variables"""

    def __init__(self, fichier):
        self.f = fichier
        self.vars = {"__file__": fichier}
        self.chemins = []          # dossiers ajoutes a sys.path : (valeur evaluee ou None, texte source)

    def val(self, n):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            return n.value
        if isinstance(n, ast.Name):
            return self.vars.get(n.id)
        if isinstance(n, ast.JoinedStr):
            return None
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
            a, b = self.val(n.left), self.val(n.right)
            return a + b if isinstance(a, str) and isinstance(b, str) else None
        if isinstance(n, ast.Call):
            nom = ast.unparse(n.func)
            args = [self.val(a) for a in n.args]
            if any(a is None for a in args):
                # os.environ.get("X", defaut) -> defaut
                if nom.endswith("environ.get") and len(n.args) == 2:
                    return self.val(n.args[1])
                return None
            fin = nom.split(".")[-1]
            if nom.endswith("environ.get") and len(args) == 2:
                return args[1]
            try:
                if fin == "dirname": return os.path.dirname(args[0])
                if fin in ("abspath", "realpath"): return os.path.abspath(args[0]) if not args[0].startswith("<") else args[0]
                if fin == "normpath": return os.path.normpath(args[0])
                if fin == "join": return os.path.join(*args)
            except Exception:
                return None
        return None

    def visit_Assign(self, n):
        v = self.val(n.value)
        for t in n.targets:
            if isinstance(t, ast.Name) and v is not None:
                self.vars[t.id] = v
            if isinstance(t, ast.Subscript) and ast.unparse(t.value).endswith(".path"):   # sys.path ou alias (_s.path)
                if isinstance(n.value, (ast.List, ast.Tuple)):
                    for e in n.value.elts:
                        self.chemins.append((self.val(e), ast.unparse(e)))
        self.generic_visit(n)

    def visit_Call(self, n):
        nom = ast.unparse(n.func)
        if nom.endswith(".path.insert") and len(n.args) == 2:                       # sys.path ou alias (_s.path)
            self.chemins.append((self.val(n.args[1]), ast.unparse(n.args[1])))
        elif nom.endswith(".path.append") and len(n.args) == 1:
            self.chemins.append((self.val(n.args[0]), ast.unparse(n.args[0])))
        self.generic_visit(n)


def imports(arbre):
    """[(module de tete, ligne, facultatif)] ; facultatif = dans un try dont un except attrape ImportError"""
    res = []

    def facultatif(pile):
        for t in pile:
            for h in t.handlers:
                txt = ast.unparse(h.type) if h.type is not None else "Exception"
                if any(k in txt for k in ("ImportError", "ModuleNotFoundError", "Exception")):
                    return True
        return False

    def parcours(n, pile):
        if isinstance(n, ast.Try):
            for c in n.body:
                parcours(c, pile + [n])
            for c in n.handlers + n.orelse + n.finalbody:
                parcours(c, pile)
            return
        if isinstance(n, ast.Import):
            for a in n.names:
                res.append((a.name.split(".")[0], n.lineno, facultatif(pile)))
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            res.append((n.module.split(".")[0], n.lineno, facultatif(pile)))
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "__import__" \
                and n.args and isinstance(n.args[0], ast.Constant):
            res.append((str(n.args[0].value).split(".")[0], n.lineno, facultatif(pile)))
        for c in ast.iter_child_nodes(n):
            parcours(c, pile)

    parcours(arbre, [])
    return res


def existe_module(nom, dossier):
    return os.path.isfile(os.path.join(dossier, nom + ".py")) or \
        os.path.isfile(os.path.join(dossier, nom, "__init__.py")) or \
        os.path.isdir(os.path.join(dossier, nom)) and any(
            x.endswith(".py") for x in os.listdir(os.path.join(dossier, nom)))


def verifie_shell():
    """scripts/**/*.sh : les fichiers appeles par $S/ (dossier du script), $U/ ou `python3 x.py` apres `cd $U`
    (src/hsfa) et `-autoboot_script x.lua` (banc : src/hsfa/mame) doivent exister dans le depot"""
    import re
    res = []
    shs = subprocess.run(["git", "-C", RACINE, "ls-files", "scripts/*.sh"], capture_output=True, text=True,
                         check=True).stdout.split()
    for f in shs:
        t = open(os.path.join(RACINE, f), encoding="utf-8").read()
        d = os.path.dirname(os.path.join(RACINE, f))
        refs = [(m, os.path.join(d, m)) for m in re.findall(r"\$S/([\w.-]+)", t)]
        refs += [(m, os.path.join(RACINE, "src/hsfa", m)) for m in re.findall(r"\$U/([\w.-]+\.py)", t)]
        refs += [(m, os.path.join(RACINE, "src/hsfa", m)) for m in re.findall(r"python3 ([\w.-]+\.py)", t)]
        refs += [(m, os.path.join(RACINE, "src/hsfa/mame", m)) for m in re.findall(r"-autoboot_script ([\w.-]+\.lua)", t)]
        for m, c in refs:
            res.append((f, m, os.path.exists(c)))
    return res


def main():
    detail = "--detail" in sys.argv
    sortie_json = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    fichiers = subprocess.run(["git", "-C", RACINE, "ls-files", "*.py"], capture_output=True, text=True,
                              check=True).stdout.split()
    stdlib = set(sys.stdlib_module_names)
    bilan = {"compilation_ko": [], "fichiers": 0, "imports": 0, "ok_local": 0, "ok_stdlib": 0, "ok_tiers": 0,
             "facultatif_absent": [], "externe": [], "echec": [], "exception_max": []}
    tous_modules = {}
    for f in fichiers:
        tous_modules.setdefault(os.path.splitext(os.path.basename(f))[0], []).append(f)
    infos = {}   # fichier -> (arbre, dossiers propres, externes)
    with tempfile.TemporaryDirectory() as tmp:
        for f in fichiers:
            chemin = os.path.join(RACINE, f)
            bilan["fichiers"] += 1
            try:
                py_compile.compile(chemin, cfile=os.path.join(tmp, "x.pyc"), doraise=True)
            except py_compile.PyCompileError as e:
                bilan["compilation_ko"].append("%s : %s" % (f, str(e).splitlines()[-1]))
                continue
            arbre = ast.parse(open(chemin, encoding="utf-8", errors="replace").read())
            ev = Evaluateur(chemin)
            ev.visit(arbre)
            dossiers, externes = [os.path.dirname(chemin)], []
            for v, txt in ev.chemins:
                if v is None:
                    continue
                proj = projette(v, chemin)
                if proj:
                    dossiers += proj
                else:
                    externes.append(v)
            infos[chemin] = (arbre, dossiers, externes)

    def localise(mod, dossiers):
        for d in dossiers:
            for c in (os.path.join(d, mod + ".py"), os.path.join(d, mod, "__init__.py")):
                if os.path.isfile(c):
                    return c
            if os.path.isdir(os.path.join(d, mod)) and existe_module(mod, d):
                return os.path.join(d, mod)
        return None

    def effectifs(chemin, vus):
        """dossiers de recherche effectifs : les siens + ceux qu'ajoutent (a l'import) les modules locaux importes"""
        arbre, dossiers, externes = infos[chemin]
        d, e = list(dossiers), list(externes)
        for mod, _, _ in imports(arbre):
            c = localise(mod, dossiers)
            if c and c in infos and c not in vus:
                vus.add(c)
                d2, e2 = effectifs(c, vus)
                d += [x for x in d2 if x not in d]
                e += [x for x in e2 if x not in e]
        return d, e

    for chemin, (arbre, _, _) in infos.items():
        f = os.path.relpath(chemin, RACINE)
        dossiers, externes = effectifs(chemin, {chemin})
        for mod, ligne, fac in imports(arbre):
            bilan["imports"] += 1
            if mod in stdlib or mod == "__future__":
                bilan["ok_stdlib"] += 1
            elif localise(mod, dossiers):
                bilan["ok_local"] += 1
            elif mod in TIERS:
                if TIERS[mod]:
                    bilan["ok_tiers"] += 1
                else:
                    bilan["facultatif_absent"].append("%s:%d %s (dependance facultative)" % (f, ligne, mod))
            elif externes:
                bilan["externe"].append("%s:%d %s (dans %s)" % (f, ligne, mod, ", ".join(externes)))
            elif fac:
                bilan["facultatif_absent"].append("%s:%d %s (import protege par try)" % (f, ligne, mod))
            else:
                ailleurs = tous_modules.get(mod, [])
                bilan["exception_max" if f.startswith(("max/", "tools/max/")) else "echec"].append("%s:%d %s%s" % (f, ligne, mod,
                                      (" (existe ailleurs : %s)" % ", ".join(ailleurs)) if ailleurs else ""))
    print("Fichiers .py : %d ; compilation en echec : %d" % (bilan["fichiers"], len(bilan["compilation_ko"])))
    print("Imports : %d ; resolus : %d locaux, %d bibliotheque standard, %d tiers (requirements.txt)"
          % (bilan["imports"], bilan["ok_local"], bilan["ok_stdlib"], bilan["ok_tiers"]))
    print("Externes (dossier de travail non publie) : %d ; facultatifs absents : %d ; ECHEC : %d"
          % (len(bilan["externe"]), len(bilan["facultatif_absent"]), len(bilan["echec"])))
    print("Exception volontaire max/ et tools/max/ (session MAX, non modifies, chemins resolus a l'execution par "
          "paths.py ou le dossier courant) : %d imports non resolus statiquement" % len(bilan["exception_max"]))
    for k in ("compilation_ko", "echec") + (("externe", "facultatif_absent", "exception_max") if detail else ()):
        for l in bilan[k]:
            print("  [%s] %s" % (k, l))
    sh = verifie_shell()
    ko = [r for r in sh if not r[2]]
    print("Scripts shell (scripts/) : %d references de fichiers, %d introuvables" % (len(sh), len(ko)))
    for f, m, _ in ko:
        print("  [shell] %s : %s introuvable" % (f, m))
    bilan["shell_ko"] = ["%s : %s" % (f, m) for f, m, _ in ko]
    if sortie_json:
        json.dump(bilan, open(sortie_json, "w"), indent=1, ensure_ascii=False)
    return 1 if bilan["compilation_ko"] or bilan["echec"] or ko else 0


if __name__ == "__main__":
    sys.exit(main())
