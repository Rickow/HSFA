#!/usr/bin/env python3
"""Releve des modules importes pendant une construction (traces mods_<pid>.txt du traçage) -> imports_embarques.py.

PyInstaller n'analyse que le point d'entree ; les scripts du depot sont embarques comme fichiers et importes a
l'execution : tout module de la bibliotheque standard ou tiers qu'ils utilisent doit etre cite dans
imports_embarques.py (que hsfa_constructeur.spec analyse).
Usage : releve_imports.py DOSSIER_TRACES DEPOT > imports_embarques.py
"""
import os, sys
traces, depot = sys.argv[1], os.path.realpath(sys.argv[2])
mods = set()
for f in sorted(os.listdir(traces)):
    if not f.startswith("mods_"): continue
    for l in open(os.path.join(traces, f)).read().splitlines()[1:]:
        nom, chemin = l.split("\t")
        if chemin != "None" and os.path.realpath(chemin).startswith(depot + os.sep): continue   # module du depot
        # copies du depot faites par la construction (cache/max_regen/depot, travail/.../outils_max) : idem
        if chemin != "None" and "/lib/python3" not in chemin and "site-packages" not in chemin: continue
        if nom.startswith(("_frozen", "__main__", "hsfa_trace", "_distutils_hack", "sitecustomize", "__mp_main__")): continue
        racine = nom.split(".")[0]
        if racine in ("__hsfa__", "pip"): continue          # pip : importe par un outil, inutile ici
        mods.add(nom)
# on garde les modules « publics » (sans composant prive) : leurs sous-modules suivent par l'analyse de PyInstaller
garde = sorted(m for m in mods if not any(p.startswith("_") for p in m.split(".")[1:])
               and all(p.isidentifier() for p in m.split(".")))     # pas _sysconfigdata__linux_x86_64-linux-gnu
print('"""Modules utilises par les scripts du depot pendant une construction (releve_imports.py) : cites ici pour que')
print('PyInstaller les embarque. Fichier genere ; ne pas modifier a la main."""')
print("# noqa: F401")
print("import importlib")
print("MODULES = [")
for m in garde: print("    %r," % m)
print("]")
print("if __name__ == '__main__':")
print("    for m in MODULES: importlib.import_module(m)")
print("# imports explicites (analyse statique de PyInstaller) ; absents sur certains systemes : ignores")
for m in garde:
    print("try:\n    import %s\nexcept ImportError:\n    pass" % m)
