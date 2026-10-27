#!<workspace>/venv/bin/python3
"""Portage de work/re/ppsspp/tournee_psp.py (partie jouée jusqu'à la fin, captures périodiques), en images exactes et sans fenêtre.
Usage : tournee_psp.py <perso> <dossier> [images=3000] [période en images=120]    (ou --etat f.ppst pour partir d'un état d'Arcade)"""
import argparse, os, sys
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ICI)
from psp_debug import Banc
import scenarios_max as sc
ap = argparse.ArgumentParser()
ap.add_argument("perso"); ap.add_argument("dossier"); ap.add_argument("images", nargs="?", type=int, default=3000)
ap.add_argument("periode", nargs="?", type=int, default=120); ap.add_argument("--etat")
a = ap.parse_args()
with Banc.lancer(etat=a.etat) as b:
    if not a.etat: sc.aller_arcade(b, a.perso)
    out = sc.tournee(b, a.dossier, a.images, a.periode)
    print(len(out), "captures dans", a.dossier)
