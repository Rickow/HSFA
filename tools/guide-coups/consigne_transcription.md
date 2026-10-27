# Consigne de relevé des commandes (guide BradyGames « Street Fighter Alpha Anthology », PDF scanné)

Le guide est un texte protégé. On n'en relève **que les commandes des coups et la page où elles figurent**. On ne
recopie ni paragraphe, ni légende, ni encadré, ni conseil de stratégie, et on ne les paraphrase pas non plus.

Images des pages (130 dpi) : `$GUIDE/p/p-NNN.png` (NNN = page du PDF, sur 3 chiffres).
Agrandissement à 300 dpi d'une zone : `$GUIDE/zoom.sh <page> <x0> <y0> <x1> <y1>`. Les coordonnées sont en fractions
0-1 de la page. Le script affiche le chemin du PNG à lire avec l'outil Read. Exemple : `zoom.sh 30 0.08 0.36 0.53 0.82`.

Pour chaque page du lot, dans l'ordre :
1. Lis l'image de la page (Read).
2. Repère les tableaux de coups (Throws, Special Attacks, Super Combos, Alpha Counters, Custom Combos, commandes
   système) et les secrets à manipulation, comme le déblocage d'un perso. Le reste de la page est ignoré.
3. Agrandis chaque ligne de commande avec `zoom.sh` et lis les flèches sur l'image agrandie. Les flèches sont
   petites : ne devine pas, vérifie au zoom, surtout les diagonales (↘ bas-avant, ↙ bas-arrière, ↗ haut-avant,
   ↖ haut-arrière).
4. Écris les lignes du tableau des coups selon `consigne_tableau.md` : jeu, mode, perso, ISM, type, nom du coup,
   manipulation, boutons, conditions résumées en quelques mots de français, page.

Notation des commandes (Unicode) : → ← ↓ ↑ ↘ ↙ ↗ ↖ ; boutons tels qu'imprimés (LP MP HP LK MK HK, Punch, Kick, P, K).
Une charge s'écrit `← (charge) →`. Une notation spéciale (360°, flèche de combo) se reproduit au plus près, avec une
explication entre crochets si besoin. Un mot illisible s'écrit `[illisible]`.

Sortie : `$GUIDE/csv/<lot>.csv` uniquement, avec le format de `consigne_tableau.md`. Pas de fichier de texte de page.
À la fin, réponds seulement : le nombre de pages traitées, et les pages où une lecture reste douteuse (avec le mot ou
la flèche en cause).
