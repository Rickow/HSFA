# Réutilisation des tuiles graphiques de *Alpha 3* : essai ciblé (2026-11-10)

Question : en réutilisant mieux les tuiles (miroirs, découpage des images sur une autre grille, morceaux plus petits),
peut-on gagner assez de place pour faire tenir Upper dans les 32 Mo d'une CPS-2 standard (il dépasse d'au moins 9 %,
HANDOFF §49) ?

Données : ROM `sfa3` de l'utilisateur (hors dépôt). Outil : `tools/sondes-recherche/tuiles_cps2.py` (décodage d'après
le pilote CPS-2 de MAME, contrôlé par une planche d'aperçu : personnages lisibles) et `tuiles_cps2_detail.py`.

| mesure | tuiles 16×16 | gain |
|---|---|---|
| emplacements de la ROM graphique | 262 144 (189 vides) | — |
| contenus uniques exacts | 250 442 | référence |
| uniques au miroir près (H, V, HV) | 249 444 | **0,40 %** |
| contenu retrouvé ailleurs hors de la grille de 16 px | 14 151 tuiles | **5,65 %** au plus |
| … dont tuiles d'au moins 64 pixels et 3 couleurs | 9 942 | 3,97 % |
| quarts 8×8 uniques (équivalent 16×16) | 170 971 | 31,7 % (borne théorique) |

Lecture :
- **Miroirs** : presque rien (0,4 %). Capcom dédoublonnait déjà ses tuiles retournées dans la ROM d'arcade.
- **Autre découpage** : une tuile sur vingt environ a son contenu exact ailleurs, décalé. C'est une borne haute et
  approximative : la recherche suppose que des codes consécutifs (rangées de 16 tuiles) sont voisins dans le dessin, et
  un nouveau découpage d'une image change aussi ses autres tuiles. Gain réaliste : quelques %.
- **Morceaux de 8×8** : un tiers de gain, mais la CPS-2 ne dessine pas d'objets en 8×8 (seul le plan de texte l'est).
  Inutilisable sur le matériel.
- **Rapiéçage** (une image = une autre + quelques tuiles par-dessus) : non mesuré, il faut les tables d'images du jeu.

Conclusion : miroirs et redécoupage réunis donneraient de l'ordre de 4 à 6 %, moins que les 9 % qui manquent à Upper,
et ce chiffre de 9 % est lui-même un minimum. Sans perte, Upper ne tient pas dans 32 Mo ; il faudrait en plus le
rapiéçage (non mesuré, coûteux en objets et en réécriture de la routine de dessin) ou des sacrifices de contenu.

## Complément : tuiles identiques « à la palette près »
Une palette ne change que les couleurs des indices, pas la forme des zones : deux tuiles ne peuvent se partager que si
elles ont exactement le même découpage en zones (mêmes pixels groupés), seules les couleurs différant. Mesure
(`tuiles_cps2_palette.py`, indice transparent fixé) : 245 152 formes uniques contre 250 442 tuiles, soit **2,1 %** au plus.
Et chaque tuile ainsi partagée demande une palette réordonnée à elle (or un personnage utilise une palette pour toutes ses
tuiles, et la carte n'a que 32 palettes d'objets à l'écran) : gain réel bien inférieur. En moyenne, une tuile n'utilise
que 6,3 couleurs sur 16.
