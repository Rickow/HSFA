# -*- mode: python -*-
# PyInstaller : un seul executable (onefile). Lance par fabrique.py ; variables d'environnement :
#   HSFA_DEPOT   depot a embarquer (copie propre : checkout de la CI, git archive) ; defaut ../..
#   HSFA_BIN     outils natifs de natifs.py pour ce systeme (hsfa_oggenc, fluxtool, libchdr)
#   HSFA_NOM     nom de l'executable (defaut hsfa-constructeur)
import os, sys
ICI = os.path.abspath(SPECPATH)
DEPOT = os.path.abspath(os.environ.get("HSFA_DEPOT", os.path.join(ICI, "..", "..")))
BIN = os.path.abspath(os.environ.get("HSFA_BIN", os.path.join(ICI, "bin")))
# dossiers du depot lus et importes a l'execution : pas docs/, re/, legacy/, patches/ (sauf licence FBNeo)
DOSSIERS = ["scripts", "src", "tools", "max"]
SAUF = {"__pycache__", ".git"}
SAUF_TOOLS = {"android", "rocknix", "recalbox", "windows", "ppsspp-banc", "constructeur"}   # paquets d'autres cibles
FICHIERS = ["LICENSE", "NOTICE.md", "CREDITS.md", "README.md", "README.fr.md", "requirements.txt",
            os.path.join("patches", "fbneo", "LICENSE-FBNeo.txt")]
datas = []
for d in DOSSIERS:
    for r, ds, fs in os.walk(os.path.join(DEPOT, d)):
        ds[:] = [x for x in ds if x not in SAUF and not (r == os.path.join(DEPOT, "tools") and x in SAUF_TOOLS)]
        for f in fs:
            if f.endswith((".pyc", ".pyo")): continue
            datas.append((os.path.join(r, f), os.path.join("depot", os.path.relpath(r, DEPOT))))
for f in FICHIERS:
    if os.path.exists(os.path.join(DEPOT, f)):
        datas.append((os.path.join(DEPOT, f), os.path.join("depot", os.path.dirname(f)) or "depot"))
datas.append((os.path.join(ICI, "TIERS.md"), "."))
binaries = [(os.path.join(BIN, f), "bin") for f in sorted(os.listdir(BIN)) if not f.endswith(".txt")]
datas += [(os.path.join(BIN, f), "bin") for f in sorted(os.listdir(BIN)) if f.endswith(".txt")]

import ast   # imports_embarques.py doit etre du Python valide, sinon PyInstaller l'ignore EN ENTIER (sans erreur)
ast.parse(open(os.path.join(ICI, "imports_embarques.py"), encoding="utf-8").read())

a = Analysis([os.path.join(ICI, "hsfa_constructeur.py")], pathex=[ICI],
             hiddenimports=["imports_embarques", "chd_iso"], datas=datas, binaries=binaries,
             excludes=["matplotlib", "scipy", "IPython", "pytest"], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name=os.environ.get("HSFA_NOM", "hsfa-constructeur"),
          console=True, upx=False, strip=False, debug=False, runtime_tmpdir=None)
