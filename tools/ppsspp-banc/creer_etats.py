#!<workspace>/venv/bin/python3
"""Crée les états de départ du banc, SANS FENÊTRE, depuis le démarrage du jeu (tout est scripté, déterministe) :
  etats/selection_training.ppst  : écran de sélection de l'entraînement
  etats/combat_eagle_ken.ppst    : Eagle (J1) contre Ken (J2), manche commencée, contrôle rendu
Usage : python3 creer_etats.py [dossier_sortie] ; affiche l'empreinte RAM de chaque état (reproductibilité)."""
import os, sys, time
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
from psp_debug import Banc, plan
import sfa3max

sortie = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ICI, "etats")
t0 = time.time()
with Banc.lancer() as b:
    nav = sfa3max.NAV_SELECTION
    b.images(sum(n for _, n in nav), entrees=plan(nav))
    print("sélection atteinte, empreinte RAM", b.empreinte_ram(), "(%.0fs)" % (time.time() - t0))
    b.capture(os.path.join(sortie, "selection_training.png"))
    b.etat_sauver(os.path.join(sortie, "selection_training.ppst"))
    nav = sfa3max.NAV_EAGLE_KEN
    b.images(sum(n for _, n in nav), entrees=plan(nav))
    j = sfa3max.adresses_joueurs(b)
    ids = [b.lire(a + 0x152, 1)[0] for a in j]
    print("combat : ids joueurs", [hex(i) for i in ids], "empreinte RAM", b.empreinte_ram(), "(%.0fs)" % (time.time() - t0))
    assert ids == [0x26, 0x01], "pas Eagle contre Ken"
    b.capture(os.path.join(sortie, "combat_eagle_ken.png"))
    b.etat_sauver(os.path.join(sortie, "combat_eagle_ken.ppst"))
