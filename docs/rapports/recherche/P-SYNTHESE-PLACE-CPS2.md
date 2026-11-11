# Synthèse : faire tenir Upper (et Hyper) sur une CPS-2 (discussion du 2026-11-10)

## Le problème
- Poids des jeux (ROM d'après MAME) : graphismes 56 % de *Zero*, 73 % de *Zero 2*, 72 % de *Zero 3* (32 Mo, le plafond de la
  carte) ; sur PS2, Hyper est à 94 % de musique enregistrée (696 Mo d'ADX). Schéma : hors dépôt.
- Upper dépasse la ROM graphique d'au moins 9 % (≥ 22 700 tuiles 16×16, HANDOFF §49). Le surplus vient surtout des
  personnages ajoutés (Guile seul ≈ 1 Mo) ; tous ses décors ne font que ≈ 7 200 tuiles de plus qu'*Alpha 3*. Figer les
  animations de décor ne suffirait donc pas seul.

## Les leviers sans perte, mesurés sur la ROM d'*Alpha 3* (`M-REUTILISATION-TUILES.md`)
| levier | gain | sur vraie carte |
|---|---|---|
| miroirs (H, V, HV) | 0,4 % | oui |
| tuiles identiques à la palette près | < 2,1 % | oui, mais une palette par tuile, 32 palettes d'objets |
| redécoupage des images sur une autre grille | 4 à 6 % au plus | oui, routine de dessin à réécrire |
| rapiéçage (image = autre image + tuiles par-dessus) | non mesuré | oui, plus d'objets, routine à réécrire |
| morceaux de 8×8 | ≈ 32 % | non : objets en 16×16 seulement |
Réunis, ils restent sous les 9 % nécessaires.

## Ce qui est impossible sur une CPS-2 non modifiée
- Compression : les puces vidéo lisent les tuiles directement en ROM ; pas de mémoire vidéo de tuiles où décompresser.
- « Soft mod » : le 68000 ne voit pas la ROM graphique et aucun registre ne change la taille ou l'adressage des tuiles.
- Pointer sur une partie de tuile, fenêtre par objet, transparence réglable : rien de tout cela n'existe. Le programme choisit
  seulement quelle tuile, où, avec quelle palette et quel retournement. Seul levier par couleur : les masques de priorité
  des plans de décor (ordre devant / derrière, pas transparence).
- Au-delà de 32 Mo : inaccessible (essai sur MvC à 148 Mo, 2026 ; les émulateurs masquent les adresses).
- Une ROM ne peut pas « simuler » une puce quand le 68000 n'est pas sur le chemin des données (cas des graphismes CPS-2) ;
  les émulateurs reproduisent les puces spéciales dans leur propre code, pas dans la ROM.

## La vraie solution : des banques par combat (« mapper »)
- Un combat n'utilise que deux personnages, un décor et les éléments communs. Solution éprouvée ailleurs : mappers NES,
  *Super Street Fighter II* Mega Drive (seul jeu sous licence à commuter des banques), cartouches Neo Geo « Giga Power ».
- Capcom l'a fait pour l'*Anthology* PS2 (banques de personnages chargées dans des emplacements, HANDOFF §48) ; notre cœur
  FBNeo reprend ce schéma (registre emplacement → base de banque).
- Où loger la « puce » : dans l'émulateur (fait), dans un cœur FPGA (MiSTer : le cœur CPS-2 de Jotego, code public GPL,
  jeux en SDRAM, extensible comme notre FBNeo), ou sur une vraie carte B neuve (flash + petit circuit de banques écrit par
  le 68000 ; à concevoir et fabriquer). Le programme, lui, est prêt.
- Recherches générales : `N-PARADIGMES-LIMITES-ROM.md` ; inventaire détaillé de la CPS-2 : `O-CPS2-POSSIBILITES.md` ; techniques d'optimisation d'images : `Q-OPTIMISATION-IMAGES.md`.
- Apports de `O-` : numéro de tuile d'objet sur 18 bits (= 32 Mo exactement) ; liste de 1 024 objets ; espace
  `A00000-EFFFFF` libre côté 68000 et connecteurs de cartes filles sur la carte B (une carte à banques est plausible,
  câblage **vérifié le 2026-11-10** : CN5/CN6 portent tout le bus graphique de 32 Mo, CN7 le bus du 68000 ; une carte fille à
  banques branchée sur les deux est faisable sur le papier, voir l'annexe de `O-`) ; le 19e bit de tuile du fork (bit 15 du mot Y) marque la fin de liste sur la vraie carte : non
  transposable.

## À mesurer ensuite (session du projet, rien de lancé)
0. **Tuiles jamais affichées** : journaliser les numéros de tuiles dessinés (parties scriptées, toutes les fins, tous les
   coups) et compter celles que le jeu n'utilise jamais. Seule piste sans perte qui pourrait couvrir les 9 %.
1. Taille du pire combat d'Upper et d'Hyper (deux personnages + décor + commun) : si elle tient dans 32 Mo, le schéma de
   banques suffit sans perte.
2. Pour un Upper sans banques : tuiles d'Upper avec miroirs, puis tuiles des animations de décor et de chaque personnage
   ajouté, pour chiffrer les sacrifices.
3. Pour un jour : proposer à Jotego une extension de son cœur MiSTer sur nos spécifications.

Pour le livre (si retenu) : encadré « le mapper de *Super Street Fighter II* Mega Drive et les banques de l'*Anthology* »
au chapitre 12 ; schéma du poids des jeux au chapitre 7 ou 12.
