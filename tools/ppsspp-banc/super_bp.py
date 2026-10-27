#!<workspace>/venv/bin/python3
"""Portage de work/re/ppsspp/super_bp.py : joue une manipulation image par image avec points d'arrêt d'EXÉCUTION sur des fonctions du module
(adresses VA de code) et relève a0-a3, v0, ra à chaque passage ; forçages `VA:reg=valeur`.
Usage : super_bp.py [--etat f.ppst] "right:20 down:3 down+right+square:3" 5DE80,1DC32C [5DE80:v0=1 ...]
Sans --etat : Eagle contre Ken depuis etats/combat_eagle_ken.ppst."""
import argparse, os, sys
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ICI)
from psp_debug import Banc
import scenarios_max as sc
ap = argparse.ArgumentParser()
ap.add_argument("--etat", default=os.path.join(ICI, "etats", "combat_eagle_ken.ppst")); ap.add_argument("seq"); ap.add_argument("bps")
ap.add_argument("forcages", nargs="*")
a = ap.parse_args()
bps = [int(x, 16) for x in a.bps.split(",") if x]
fo = []
for f in a.forcages:
    va, rv = f.split(":"); reg, v = rv.split("="); fo.append((int(va, 16), reg, int(v, 0)))
with Banc.lancer(etat=a.etat) as b:
    for r in sc.points_arret(b, a.seq, bps, fo):
        print("image %d : pc=%#x a0=%#x a1=%#x a2=%#x v0=%#x ra=%#x%s" % (r["image"], r["pc_va"], r["a0"], r["a1"], r["a2"], r["v0"], r["ra_va"],
              "  forcé %s=%d" % r["force"] if "force" in r else ""))
