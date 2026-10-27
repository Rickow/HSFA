# Hyper Street Fighter Alpha (Anthology retraduit) sur RetroArch

Ce dossier ajoute **Hyper Street Fighter Alpha** au cœur FBNeo « HSFA », qui fait déjà tourner SFA3 et SFA3 Upper.
Il n'y a besoin ni de MAME ni de scripts.

| Fichier | À quoi il sert |
|---|---|
| `fbneo_hsfa_libretro_android.so` | le cœur pour Android 64 bits (RG477M, Retroid Pocket Nova…) |
| `fbneo_hsfa_libretro.so` | le même cœur pour Linux x86_64 (PC) |
| `sfa3hhsfa.zip` | **Hyper Street Fighter Alpha** : programme traduit, graphismes, bruitages et voix |
| `hsfa_flux_table.txt` | table des musiques (code du jeu → piste du `Y_DATA.BIN`) |
| `sfa3hhsfa_sources.txt` | date et empreinte md5 des fichiers mis dans le zip |

Ce cœur remplace l'ancien cœur HSFA. Il porte le même nom et lance `sfa3hsfa.zip` et `sfa3uhsfa.zip` exactement comme
avant : le son, les images et le déroulement ont été vérifiés identiques. Les anciens zips restent valables.

## Installation

1. **Cœur** : copier `fbneo_hsfa_libretro_android.so` sur la console, puis dans RetroArch : **Menu principal →
   Charger un cœur → Installer ou restaurer un cœur**, et choisir ce fichier. Le cœur s'appelle
   **« FinalBurn Neo HSFA »**.
2. **Jeu** : copier `sfa3hhsfa.zip` à côté des deux autres jeux, par exemple dans `ROMs/hsfa/`.
   **Ne pas renommer le zip** : son nom désigne le jeu.
3. **Musique** : les musiques d'Hyper ne sont pas dans le zip. Le cœur les lit dans le disque PS2 de l'Anthology.
   - Dans le dossier **système** de RetroArch, créer le dossier `fbneo/hsfa/`. Sur Android, c'est en général
     `RetroArch/system/fbneo/hsfa/`.
   - Y copier `hsfa_flux_table.txt`.
   - Y mettre aussi **une seule** des trois sources suivantes :
     - le fichier `Y_DATA.BIN` extrait de l'ISO (1,8 Go) ;
     - l'ISO entière, renommée `anthology.iso` ;
     - un fichier texte `ydata.txt` qui contient le chemin complet du `Y_DATA.BIN` ou de l'ISO.
   - Sans ces fichiers, le jeu marche quand même. On n'entend alors que les musiques ZERO 3 (jouées par le son
     arcade) ; les musiques ZERO, ZERO 2 et ALPHA manquent (la musique précédente peut continuer à leur place).
4. **Charger un contenu** → `sfa3hhsfa.zip` → cœur **FinalBurn Neo HSFA**.

Nom affiché : « Hyper Street Fighter Alpha (HSFA, Anthology PS2 retraduit) ».

## Réglage de la musique

Dans **Options du cœur → commutateurs DIP**, le réglage **« PS2 music (ADX streams, Y_DATA.BIN) »** propose trois
valeurs :

| Valeur | Effet |
|---|---|
| `All tracks` | **valeur par défaut pour Hyper** : toutes les musiques viennent du disque PS2, comme sur la console |
| `Missing tracks only` | les musiques ZERO 3 sont jouées par le son arcade (QSound), les autres viennent du disque |
| `Off` | pas de musique du disque : seules les musiques ZERO 3 restent ; à la place des autres, la musique précédente peut continuer |

Les bruitages et les voix viennent toujours du zip, quel que soit le réglage.

## Commandes

Ce sont les mêmes que pour SFA3 et Upper (disposition par défaut de FBNeo) :

| Manette | Jeu |
|---|---|
| Select | pièce ; sur la grille des persos : roulette (cœurs du 2026-10-16 et suivants) |
| Start | Start |
| Y / X / L | poing faible / moyen / fort |
| B / A / R | pied faible / moyen / fort |

## Jouer

1. **Titre** : Select (pièce), puis Start. Il n'y a pas de démonstration : le titre attend.
2. **Menu** : VERSUS, TRAINING, OPTION, EXIT. Choisir avec Haut/Bas, valider avec un bouton.
   - OPTION et EXIT ne font rien : ce sont des écrans de la console PS2 qui n'existent pas ici.
3. **VERSUS à 2 joueurs** :
   - chaque joueur met une pièce (Select sur sa manette) ;
   - le joueur 2 appuie sur Start pour rejoindre la partie.
4. **Sélection**, dans l'ordre :
   1. le perso ;
   2. la version : ALPHA (ZERO), ALPHA2 (ZERO 2), ALPHA2G (ZERO 2 ALPHA) ou ALPHA3 (ZERO 3) ;
   3. MANUAL ou AUTO ;
   4. pour ALPHA3 seulement : le mode, puis l'ism.
5. **Fin de match** : l'écran RESULT s'affiche. Un bouton ramène à la sélection.

### Persos EX et modes cachés

- **EX choisis à l'écran de version** (EX Ryu, Ken, Bison, Sagat, Zangief, Dhalsim ; Shin Akuma ; Chun-Li SF2…) :
  **maintenir Start** et valider la version avec un bouton.
- **EX Balrog** : maintenir Start et valider le perso sur la grille (cœurs du 2026-10-16 et suivants, voir plus bas).
- **Roulette** (perso au hasard) : maintenir **Select** et valider sur la grille, comme Select sur PS2.
- **Modes cachés d'ALPHA3**, sur l'écran de mode : **maintenir Start et appuyer sur Gauche ou Droite**.
  - Depuis NORMAL, MAZI ou CLASSIC : on obtient les trois S-ISM.
  - Depuis SAIKYO : on obtient l'EX ALPHA3, réservé aux persos venus de SF2.

## Limites connues

Ce sont des défauts de la traduction ou du portage PS2, pas du cœur : le banc MAME fait exactement la même chose.

- **Roulette et Start (corrigé dans les cœurs du 2026-10-16, patch 11)** : le portage traduit lançait la roulette
  avec Start, le même bouton que celui des EX ; EX Balrog (Start maintenu sur la grille) était presque impossible à
  obtenir. Les nouveaux cœurs mettent la roulette sur **Select** (la pièce), comme sur PS2. Avec un ancien cœur,
  Start sur la grille lance toujours la roulette.
- **Cris de dégâts des versions ALPHA / ALPHA2 / ALPHA2G** (corrigé le 2026-10-16 dans la table du rejeu du zip) :
  les zips construits avant disaient d'autres cris du perso (Ryu ALPHA notamment) ; refaire le zip, ou le corriger avec
  `tools/son-hyper/corrige_cris.py <ancien zip> <nouveau zip>`.
- **EX Bison et EX Sagat en ALPHA2** s'affichent en morceaux : les données du jeu PS2 pour ces deux persos sont
  celles de Ryu.
- **TRAINING** : le jeu peut se figer pendant un combat. Au banc MAME, le programme traduit y a sauté une fois à une
  adresse nulle. Si cela arrive, utiliser **Redémarrer** dans le menu rapide de RetroArch.
- La musique qui accompagne un match VERSUS dépend d'un des deux joueurs, tiré au hasard par le jeu, comme sur PS2.

## Réglages et sauvegardes

- Laisser « CPU clock » à 100 %.
- Les sauvegardes d'état fonctionnent, y compris pendant une musique lue sur le disque.
- La lecture sur la carte SD n'a pas encore été essayée sur une console. Si la musique saccade, copier le
  `Y_DATA.BIN` dans la mémoire interne plutôt que de lire l'ISO.

## Mettre à jour après une nouvelle traduction

Sur le PC, `python3 paquet_fbneo.py hyper` reconstruit `sfa3hhsfa.zip` à partir de `work/mame_ro9/`. Il suffit
ensuite de recopier le zip : le cœur n'a pas besoin d'être réinstallé.
