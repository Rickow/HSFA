#!/usr/bin/env python3
"""fabrique.py -- l'executable unique du constructeur pour le systeme courant (PyInstaller, un seul fichier).

  fabrique.py --natifs BIN [--depot DEPOT] [--dist DIST] [--nom NOM]
  BIN   : hsfa_oggenc, fluxtool, libchdr de natifs.py pour CE systeme
  DEPOT : copie propre du depot a embarquer (defaut : ce depot ; en CI, le checkout)
Python : celui qui lance ce script, avec requirements-constructeur.txt (pip install --require-hashes).
Ensuite : <dist>/<nom> --auto-test (numpy, libchdr, signal d'essai de hsfa_oggenc, fluxtool).
"""
import argparse, os, subprocess, sys
ICI = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--natifs", required=True)
ap.add_argument("--depot", default=os.path.normpath(os.path.join(ICI, "..", "..")))
ap.add_argument("--dist", default=os.path.join(ICI, "dist"))
ap.add_argument("--travail", default=os.path.join(ICI, "build"))
ap.add_argument("--nom", default="hsfa-constructeur")
a = ap.parse_args()
env = dict(os.environ, HSFA_DEPOT=os.path.abspath(a.depot), HSFA_BIN=os.path.abspath(a.natifs), HSFA_NOM=a.nom)
subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--distpath", a.dist,
                "--workpath", a.travail, os.path.join(ICI, "hsfa_constructeur.spec")], check=True, env=env)
exe = os.path.join(a.dist, a.nom + (".exe" if os.name == "nt" else ""))
subprocess.run([exe, "--auto-test"], check=True)
print(exe)
