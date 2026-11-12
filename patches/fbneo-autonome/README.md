# FinalBurn Neo HSFA autonome (Windows x64, sans RetroArch) — version d'essai

Deux programmes : `fbneo64.exe` (4:3) et `fbneo64ws.exe` (16:9 ; le 16:9 est un choix de compilation du cœur commun,
comme pour les cœurs libretro `fbneo_hsfa` / `fbneo_hsfaws`). Mêmes zips de jeux que les cœurs RetroArch.

- **Base** : FBNeo officiel `84faab7` (2026-06-02), base commune exacte (merge-base) du libretro/FBNeo `af5d3f3` des
  patchs du dépôt ; `src/burn` y est identique.
- **Chaîne** : `patches/fbneo/` dans l'ordre de son README (0001-0027 avec 0007b, 0021b, 0021c, puis 0029, 0030, 0031 et 0032),
  parties `src/burner/libretro` et fichiers générés exclus ; puis les patchs Windows de ce dossier :
  - `W01` construction (pilotes HSFA, flux Ogg) ;
  - `W02` ROM reconstruites acceptées par leur nom (CRC différents), chemin de l'archive transmis au pilote (flux, rejeu) ;
  - `W03` zones HSFA des états (registres de mélange du 0010, zone de fin du 0029) ;
  - `W04` réglages du 16:9 : menu *Video → HSFA widescreen* et `.ini` ;
  - `W05` défaut de *Widescreen edges* = *Raw* (comme le cœur libretro depuis 0031 ; un `.ini` déjà écrit garde son choix) ;
  - `W06` rembobinage (*Game → Rewind*) et run-ahead (*Video → RunAhead*) passent aussi par les zones HSFA des états
    (0010, 0029 / 0032), comme les états en fichier (`W03`) : avant, après un retour en arrière ou avec le run-ahead, son
    décalé et, pour Upper / Hyper, transparence des objets non restaurée.
- **Recette** : `construire.sh <dépôt HSFA> <dossier de travail>` (compilation croisée MinGW-w64 depuis Linux, ~15 min).
- **Réglages** : options HSFA dans les DIP de FBNeo (mêmes valeurs par défaut que les options du cœur RetroArch).
  Les états de RetroArch ne se chargent pas dans l'autonome (formats différents), et inversement.
- **Preuves** (11/11, sous Wine, parties pilotées image par image) : 5 jeux en 4:3 et 16:9, états du jeu et captures
  identiques au cœur libretro ; son identique à l'octet sauf quelques dizaines d'échantillons à ±1 sur les flux Ogg
  d'Hyper et de la greffe (décodage en flottant, autre compilateur). Pas encore essayé sur un vrai Windows.
- **Guide** : [`docs/guide/installation-fbneo-autonome-windows.md`](../../docs/guide/installation-fbneo-autonome-windows.md)
  ([English](INSTALL-EN.md)). Licence : celle de FBNeo (`patches/fbneo/LICENSE-FBNeo.txt`), sources publiées.
