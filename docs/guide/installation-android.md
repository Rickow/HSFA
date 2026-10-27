# Installer le cœur HSFA sur Android (RetroArch)

Le cœur « FinalBurn Neo HSFA » est un FBNeo modifié qui fait tourner les trois jeux retraduits, sans MAME ni
scripts. Il cohabite avec le FBNeo officiel (nom de fichier et options séparés). Essayé par l'utilisateur sur
Anbernic RG477M (§145).

| Cœur | Fichier | Image |
|---|---|---|
| FinalBurn Neo HSFA | `fbneo_hsfa_libretro_android.so` (arm64-v8a) | 384×224, 4:3 |
| FinalBurn Neo HSFA Widescreen | `fbneo_hsfa_ws_libretro_android.so` | 448×224, 16:9 |

Les fichiers `.so` ne sont pas dans le dépôt : ils se compilent depuis les patchs de
[patches/fbneo](../../patches/fbneo/README.md). Les jeux sont les zips produits par la
[construction depuis l'ISO](construction-iso.md) : `sfa3hsfa.zip` (SFA3), `sfa3uhsfa.zip` (Upper), `sfa3hhsfa.zip`
(Hyper).

## Installation

1. Copier le `.so` sur l'appareil (par exemple dans `Download/`).
2. RetroArch : **Menu principal → Charger un cœur → Installer ou restaurer un cœur**, puis choisir le fichier.
3. Copier les zips dans un dossier de jeux, par exemple `ROMs/hsfa/`. **Ne pas les renommer** : le nom du zip désigne
   le jeu. Ni `sfa3.zip` ni BIOS ne sont nécessaires.
4. **Charger un contenu** → le zip → le cœur **FinalBurn Neo HSFA** (ou **… Widescreen**).

En 16:9, si l'image reste en 4:3 ou paraît étirée : **Réglages → Vidéo → Échelle → Rapport d'aspect = « Fourni par
le cœur »**.

## Musiques et sons venus du disque PS2

Les musiques que le son arcade ne connaît pas (4 pistes d'Upper ; ZERO, ZERO 2 et ALPHA dans Hyper) et les voix
SFA1 / SFA2 d'Hyper viennent du disque de l'Anthology. Le cœur les cherche **d'abord dans le zip du jeu** (les archives
construites depuis le §145 les contiennent), puis dans le dossier système `fbneo/hsfa/` de RetroArch : `Y_DATA.BIN`,
ou l'ISO renommée `anthology.iso`, ou un `ydata.txt` qui donne le chemin, avec `hsfa_flux_table.txt`. Sans ces
données, le jeu marche quand même, sans ces musiques.

Réglage : **Options du cœur → DIP switches → « PS2 music (ADX streams, Y_DATA.BIN) »** : `Off`, `Missing tracks
only` ou `All tracks` (défaut pour Hyper).

## Commandes et réglages

| Manette | Jeu |
|---|---|
| Select | pièce |
| Start | Start (un 2ᵉ appui valide le mode dans le menu) |
| Y / X / L | poing faible / moyen / fort |
| B / A / R | pied faible / moyen / fort |

- Laisser « CPU clock » à 100 %.
- Les sauvegardes d'état, le retour arrière et l'anticipation fonctionnent.
- OPTION et EXIT du menu restent un écran noir (comme au banc).

## Défauts connus du 16:9

Le jeu est conçu pour le 4:3 : bandes vides aux extrémités de certains décors, objets coupés à 32 px du bord, écrans
hors combat composés pour le 4:3. Les décors widescreen injectés ([INJECTION-FORK](../rapports/INJECTION-FORK.md))
corrigent le premier point ; ils ne sont pas encore dans les cœurs livrés.

## Notices détaillées

- [LISEZMOI-coeur.md](../../tools/fbneo-hsfa/LISEZMOI-coeur.md) : SFA3 et Upper ;
- [LISEZMOI-hyper.md](../../tools/fbneo-hsfa/LISEZMOI-hyper.md) : Hyper et la musique ;
- [LISEZMOI-widescreen.md](../../tools/fbneo-hsfa/LISEZMOI-widescreen.md) : cœur 16:9.
