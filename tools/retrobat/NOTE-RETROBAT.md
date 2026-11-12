# HSFA sous RetroBat (Windows) — note, NON ESSAYÉE

RetroBat est la variante Windows de l'interface de Batocera (même EmulationStation, lanceur `emulatorLauncher.exe`
propre à RetroBat). Rien n'a été essayé sur une vraie installation : ce qui suit vient de la doc officielle
(wiki.retrobat.org) et du code officiel de RetroBat (dépôts RetroBat-Official/retrobat, /emulatorlauncher,
/emulationstation).

## Où vont les fichiers

| Quoi | Où (dans le dossier de RetroBat) | Source |
|---|---|---|
| Cœurs `fbneo_hsfa_libretro.dll`, `fbneo_hsfaws_libretro.dll` (dossier `windows/` du lot) | `emulators\retroarch\cores\` | `LibRetro.Generator.cs` : `retroarch\cores\<cœur>_libretro.dll` (réglable par la clé `retroarch.cores`) |
| `.info` des deux cœurs | `emulators\retroarch\info\` | facultatif pour RetroBat (le lanceur ne le vérifie pas, contrairement à Batocera) ; RetroArch s'en sert pour le nom affiché |
| `es_systems_hsfa.cfg` (fourni ici) | `emulationstation\.emulationstation\` | `SystemData::loadAdditionnalConfig` : tout `es_systems_<nom>.cfg` y est ajouté à la liste officielle |
| Les cinq jeux, sans les renommer | `roms\hsfa\` | `<path>~\..\roms\hsfa</path>` |
| `gamelist.xml` (noms lisibles, facultatif) | `roms\hsfa\` | |

Pas de partition en lecture seule ici : les fichiers copiés restent. Une mise à jour de RetroBat ne touche pas
`roms\` ni les `es_systems_<nom>.cfg` ajoutés ; elle ne remplace pas non plus un cœur au nom inconnu de ses serveurs
(`Installer.CoreHasUpdateAvailable` ne trouve pas `fbneo_hsfa` dans sa liste de versions et ne fait rien).

**Ne nommez pas le fichier `es_systems_custom.cfg`** : sous ce nom il remplace toute la liste des systèmes.

## Commande et cœur par défaut

Le fichier `es_systems_hsfa.cfg` reprend la commande du système `fbneo` du modèle officiel de RetroBat :
`"%HOME%\emulatorLauncher.exe" -gameinfo %GAMEINFOXML% %CONTROLLERSCONFIG% -system %SYSTEM% -emulator %EMULATOR% -core %CORE% -rom %ROM%`.
Sous RetroBat, l'interface passe elle-même le cœur au lanceur (`-core %CORE%`) : le premier cœur ou celui marqué
`default="true"` (`fbneo_hsfa`, 4:3) sert par défaut ; `fbneo_hsfaws` (16:9) se choisit par jeu dans les options
avancées du jeu de l'interface (Émulateur / Cœur).

## Points à vérifier lors d'un essai réel

1. Le système « Street Fighter Alpha HSFA » apparaît (il faut au moins un jeu dans `roms\hsfa\`).
2. Le jeu démarre avec `fbneo_hsfa` ; sinon lire `emulationstation\.emulationstation\es_launch_stdout.log`
   (message `[ERROR] Core is not installed.` = mauvais nom ou mauvais dossier de cœur).
3. En 16:9, désactiver les décors (bezels) pour ce système (options avancées du système, « Décorations » : aucune),
   comme sous Batocera où le décor 4:3 écrase l'image du cœur 16:9.
4. Hyper : mode Versus seulement (deux manettes) ; Hyper + Arcade : mode choisi au titre avec gauche / droite.

Le cœur Windows (`.dll`, MinGW, liaison statique) ne dépend pas de la glibc : le problème de version rencontré avec
le cœur Linux ne se pose pas sous Windows.
