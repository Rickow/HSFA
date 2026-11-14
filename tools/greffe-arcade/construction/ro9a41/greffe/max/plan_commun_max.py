#!/usr/bin/env python3
"""(L2 des MAX dans la greffe) plan_commun_max : place des tuiles d'habillage MAX (max_portraits_gfx puis max_plus_gfx :
portraits, noms, bandeaux, HUD), partagé par fait_gfx_max.py (tuiles, tables) et la préparation / l'intégration (codes des
frames et des tables d'Hyper).

Méthode d'Upper MAX (tables seulement, aucun talon de rendu) : EMPLACEMENT 1 (plan2), comme le « plan2 prolongé » d'Upper.
plan2 de la greffe est plein (65 536 entrées : Hyper $0000-$5AFF, puis les tuiles des plans d'Upper) ; la suite
$B570-$FFFF (19 088 entrées) n'est portée par AUCUNE frame du module d'Upper (r/outils/recense_plan2_upper.py) et n'a été
dessinée dans aucun essai (recensement dynamique : 85 fins, 40 décors, VERSUS ; r/outils/libres_plan2.py ; les fins de
$21 / $22 / $23 Z3 emploient $B3D0-$B560) : non vue par 125 essais, NON PROUVÉE libre. Les tuiles MAX y sont placées
depuis P2_BASE = $D000 (en haut : 12 288 places pour 10 391 tuiles des 4 persos, 6 800 entrées intactes au-dessus de
$B560), local = P2_BASE + rang. Base déplaçable par cette SEULE constante (la préparation la lit ici). Le code porté par une frame ou une table d'Hyper vaut
local - $1000 (les routines de rendu d'Hyper ajoutent $1000). Correspondance AFFINE (rang = g - G0), ne dépend que du cache
de la session MAX (régénéré depuis l'ISO). Les aperçus de sélection vont en emplacement 0 (f545 prolongée, comme Upper).
Aucune donnée de jeu : seulement des rangs."""
P2_BASE = 0xD000
P2_FIN = 0x10000

def local(g, G0): return P2_BASE + g - G0
def code(g, G0): return local(g, G0) - 0x1000          # code d'une frame / d'une table d'Hyper (rendu : + $1000)

def plan(n_portraits, n_plus):
    """-> liste (local, source, rang) ; source = 'portraits' (max_portraits_gfx) ou 'plus' (max_plus_gfx)"""
    L = [(P2_BASE + d, 'portraits', d) for d in range(n_portraits)] + [(P2_BASE + n_portraits + d, 'plus', d) for d in range(n_plus)]
    assert P2_BASE + n_portraits + n_plus <= P2_FIN, 'plan2 : %d tuiles MAX pour %d places' % (n_portraits + n_plus, P2_FIN - P2_BASE)
    return L
