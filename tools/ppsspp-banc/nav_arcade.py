#!<workspace>/venv/bin/python3
"""Portage de work/re/ppsspp/nav_arcade.py : démarrage -> début d'une partie ARCADE avec le perso donné, en images exactes, sans fenêtre.
Usage : nav_arcade.py <perso : eagle|maki|yun|ingrid|ken|ryu|ID hexa> [etat_sortie.ppst] [capture.png]"""
import os, sys
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ICI)
from psp_debug import Banc
import scenarios_max as sc, sfa3max
perso = sys.argv[1]
with Banc.lancer() as b:
    n = sc.aller_arcade(b, perso)
    j1, _ = sfa3max.adresses_joueurs(b)
    print("combat d'Arcade atteint, perso J1 = %#x, empreinte RAM %s" % (b.lire8(j1 + 0x152), b.empreinte_ram()))
    if len(sys.argv) > 2 and sys.argv[2] != "-": print("état :", b.etat_sauver(sys.argv[2]))
    if len(sys.argv) > 3: b.capture(sys.argv[3]); print("capture :", sys.argv[3])
