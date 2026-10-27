#!/usr/bin/env python3
"""localiser.py -- copie locale EXECUTABLE du depot : remplace les chemins `<workspace>/...` par ceux de votre poste.

Le depot publie les scripts avec des chemins anonymises (`<workspace>/work/mame`, `<workspace>/anthology_extract`...).
Ce script recopie le depot dans un dossier de votre choix en remplacant ces chemins selon vos variables
d'environnement (HSFA_WORKSPACE, HSFA_EXTRACT, HSFA_WORK, HSFA_XDATA... : voir config.example.env et
src/hsfa/hsfa_config.py). Le depot lui-meme n'est jamais modifie.

Usage :
  source config.env                       # vos chemins (copie de config.example.env)
  python3 scripts/localiser.py DOSSIER_SORTIE [--lua]
    --lua : copie aussi les scripts Lua du banc (src/hsfa/mame/*.lua) dans $HSFA_WORK/mame, ou MAME les lance
            (-autoboot_script tournee.lua depuis ce dossier). Les fichiers existants sont gardes en .orig.
Le dossier de sortie contient alors src/hsfa (traducteur), scripts/, tools/ : lancer les outils depuis LA.
"""
import os, shutil, subprocess, sys

ICI = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.abspath(os.path.join(ICI, ".."))
sys.path.insert(0, os.path.join(DEPOT, "src", "hsfa"))
import hsfa_config                                           # noqa: E402

TEXTE = (".py", ".sh", ".lua", ".md", ".txt", ".json", ".tsv", ".cfg", ".info", ".xml", ".h", ".c", ".diff", ".patch")


def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        print(__doc__); return 2
    sortie = os.path.abspath(sys.argv[1])
    if os.path.commonpath([sortie, DEPOT]) == DEPOT:
        sys.exit("la sortie doit etre hors du depot")
    hsfa_config.workspace()                                  # echoue proprement si HSFA_WORKSPACE manque
    fichiers = subprocess.run(["git", "-C", DEPOT, "ls-files"], capture_output=True, text=True,
                              check=True).stdout.split("\n")
    n = m = 0
    for f in filter(None, fichiers):
        src, dst = os.path.join(DEPOT, f), os.path.join(sortie, f)
        if os.path.islink(src) or os.path.isdir(src):
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if f.endswith(TEXTE):
            t = open(src, encoding="utf-8", errors="surrogateescape").read()
            # dans la copie, les outils publies sont ceux de la COPIE (pas du depot d'origine)
            t2 = hsfa_config.localise(t).replace(DEPOT, sortie)
            open(dst, "w", encoding="utf-8", errors="surrogateescape").write(t2)
            m += t2 != t
        else:
            shutil.copy2(src, dst)
        shutil.copymode(src, dst); n += 1
    print("%d fichiers copies dans %s, %d localises" % (n, sortie, m))
    if "--lua" in sys.argv:
        banc = os.path.join(hsfa_config.chemin("work"), "mame")
        os.makedirs(banc, exist_ok=True)
        for f in sorted(os.listdir(os.path.join(sortie, "src", "hsfa", "mame"))):
            if f.endswith(".lua"):
                d = os.path.join(banc, f)
                if os.path.exists(d) and not os.path.exists(d + ".orig"):
                    shutil.copy2(d, d + ".orig")
                shutil.copy2(os.path.join(sortie, "src", "hsfa", "mame", f), d)
        print("scripts Lua du banc copies dans", banc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
