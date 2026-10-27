# Street Fighter Alpha 3 / Upper (Anthology retraduit) sur RetroArch Android

Ce dossier contient un cœur FBNeo modifié qui fait tourner les deux jeux retraduits du projet, sans MAME ni scripts.

| Fichier | À quoi il sert |
|---|---|
| `fbneo_hsfa_libretro_android.so` | le cœur pour Android 64 bits (RG477M, Retroid Pocket Nova…) |
| `fbneo_hsfa_libretro.so` | le même cœur pour Linux x86_64 (PC) |
| `sfa3hsfa.zip` | **Street Fighter Alpha 3** (traduction de SFA3 de l'Anthology) |
| `sfa3uhsfa.zip` | **Street Fighter Alpha 3 Upper** (traduction d'Upper, son hybride) |
| `sfa3umhsfa.zip` | **Street Fighter Alpha 3 Upper MAX** (Upper + Eagle, Maki, Yun, Ingrid de SFA3 MAX ; zip, états et réglages séparés d'Upper) |

Les archives sont complètes : programme traduit, graphismes et son, données du portage. Il n'y a besoin d'aucun autre
fichier (ni `sfa3.zip`, ni BIOS).

## Installation sur la console

1. Copier `fbneo_hsfa_libretro_android.so` sur la console, par exemple dans `Download/`.
2. Dans RetroArch : **Menu principal → Charger un cœur → Installer ou restaurer un cœur**, puis choisir le fichier
   `fbneo_hsfa_libretro_android.so`. Le cœur s'affiche ensuite sous le nom **« FinalBurn Neo HSFA »**.
   Il n'écrase pas le FBNeo habituel : les deux cœurs coexistent, avec des options et des sauvegardes séparées.
3. Copier `sfa3hsfa.zip`, `sfa3uhsfa.zip` (et `sfa3umhsfa.zip`) dans un dossier de jeux, par exemple `ROMs/hsfa/`.
   **Ne pas renommer les zips** : le nom du fichier désigne le jeu.
4. **Charger un contenu** → choisir le zip → choisir le cœur **FinalBurn Neo HSFA**.
   (On peut aussi lancer le cœur d'abord, puis « Charger un contenu ».)

Noms affichés : « Street Fighter Alpha 3 (HSFA, Anthology PS2 retraduit) » et
« Street Fighter Alpha 3 Upper (HSFA, Anthology PS2 retraduit) ».

## Commandes (manette RetroArch, disposition par défaut de FBNeo)

| Manette | Jeu |
|---|---|
| Select | pièce |
| Start | Start |
| Y / X / L | poing faible / moyen / fort |
| B / A / R | pied faible / moyen / fort |

Pour démarrer : Select (pièce), puis Start. Dans le menu des modes, il faut appuyer
sur Start une deuxième fois pour valider le mode. OPTION et EXIT restent un écran noir (même chose dans MAME).

## Réglages

- Aucun réglage obligatoire. Laisser **« CPU clock » à 100 %** (même vitesse que le banc MAME). Si la console peine,
  on peut la baisser un peu, mais le jeu ralentira dans les scènes chargées.
- Les sauvegardes d'état (et le retour arrière, l'anticipation « run-ahead ») fonctionnent.
- Pas de tableau des records (hiscore) pour ces deux jeux.
- Le cœur lance aussi les autres jeux CPS1/CPS2 de FBNeo, mais il est fait pour ces deux jeux. Pour le reste, garder
  le FBNeo officiel.

## Mettre à jour après une nouvelle traduction

Sur le PC : `python3 paquet_fbneo.py` (dans ce dossier) reconstruit les deux zips à partir du dossier de travail
(`python3 paquet_fbneo.py sfa3` ou `upper` pour un seul). Il suffit ensuite de recopier les zips sur la console : le
cœur n'a pas besoin d'être réinstallé. Les fichiers `*_sources.txt` indiquent la date et l'empreinte md5 des fichiers
utilisés.
