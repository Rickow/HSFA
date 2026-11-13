# FinalBurn Neo HSFA autonome (Windows) — guide

**English: [installation-fbneo-autonome-windows.md](installation-fbneo-autonome-windows.md)**

Version **d'essai**, jointe à la v0.1.9 (pré-version) et à la v0.1.10 (même version) ; voir `CHANGELOG.md`.
FinalBurn Neo pour Windows 64 bits, sans RetroArch, avec les pilotes et les réglages du cœur HSFA. Il lance les **mêmes archives de jeu** que le cœur libretro (`sfa3hsfa.zip`, `sfa3uhsfa.zip`,
`sfa3umhsfa.zip`, `sfa3hhsfa.zip`, `sfa3hahsfa.zip`, construites par le script du projet depuis vos disques).

## 1. Deux programmes

| programme | image | équivalent RetroArch |
|---|---|---|
| `fbneo64.exe` | 4:3 de la borne (384 × 224) | cœur `fbneo_hsfa` |
| `fbneo64ws.exe` | 16:9 (512 × 224, décor élargi) | cœur `fbneo_hsfaws` |

Le 16:9 est un choix fait à la compilation du cœur (comme les deux cœurs libretro) : il y a donc deux programmes.
Chacun a son fichier de réglages (`config\fbneo64.ini`, `config\fbneo64ws.ini`) ; ils peuvent partager le même dossier,
les mêmes archives et les mêmes réglages de jeu (`config\games\`).

Ce sont des FinalBurn Neo complets : tous les autres jeux de FBNeo fonctionnent comme dans la version officielle.

## 2. Installation

1. Décompresser le dossier où vous voulez (pas besoin d'installer). Il faut Windows 10 ou 11, 64 bits.
2. Mettre les archives HSFA, **telles que le script les a construites** (ne pas les recompresser : la musique et le
   rejeu sont lus directement dans l'archive, stockés sans compression), dans le dossier `roms\` à côté du programme,
   ou indiquer leur dossier dans *Misc → Configure ROM paths…*.
3. Lancer `fbneo64.exe` (ou `fbneo64ws.exe`), *Game → Load game…* (F6), chercher « HSFA ». En ligne de commande :
   `fbneo64ws.exe sfa3hhsfa` (fenêtre : ajouter `-w`).

Nom des jeux : `sfa3hsfa` (SFA3), `sfa3uhsfa` (Upper), `sfa3umhsfa` (Upper MAX), `sfa3hhsfa` (Hyper),
`sfa3hahsfa` (Hyper + mode Arcade d'Upper).

FBNeo signale en temps normal les ROM dont le CRC n'est pas celui de la borne. Pour les jeux HSFA (reconstruits depuis
le disque à chaque construction), une ROM trouvée par son nom et de la bonne taille est acceptée sans message,
comme dans le cœur RetroArch.

## 3. Réglages

### Options HSFA du jeu (= « options du cœur » de RetroArch)

*Input → Set dipswitches…* (Ctrl+F5), une fois le jeu lancé. Mêmes noms et **mêmes valeurs par défaut** que dans
RetroArch : musique PS2, ombres transparentes (PSP), provocation sur Select, sang (rouge par défaut), saut des boucles
d'attente (activé), réglages de l'écran OPTION (difficulté, temps, etc.). Ils sont gardés par jeu dans
`config\games\<jeu>.ini`. Comme dans RetroArch, le sang et certains réglages s'appliquent au chargement ou à la remise
à zéro (*Game → Reset game*).

### 16:9 (`fbneo64ws.exe`)

*Video → HSFA widescreen* :

- **Widescreen edges** : *Raw* (par défaut depuis le patch 0031 : l'image dessinée par le jeu, vue libre façon PSP),
  *Stage-locked view* (vue calée sur le décor, HUD fixe), *Mirror*, *Repeat*, *Black* — mêmes rendus que l'option
  « Widescreen edges » de RetroArch. Un `fbneo64ws.ini` écrit par une version précédente garde son choix
  (`nHsfaWsEdges 0` = vue calée) : choisir *Raw* dans le menu ;
- **Screen format (fill height)** : *Off* (par défaut, 16:9 entier, 512 px), 4:3, 3:2, 14:9 (448 px), 16:10, 5:3, 16:9 :
  pour un écran moins large que 16:9, l'image remplit la hauteur et les côtés sont rognés (centrés).

Ces deux choix sont gardés dans `config\fbneo64ws.ini` (`nHsfaWsEdges`, `nHsfaFormat`). Dans `fbneo64.exe` (4:3) le
menu est grisé.

Conseillé : *Video → Stretch → Correct aspect ratio*, pour garder la forme des pixels de la borne.

### Son

FBNeo pour Windows sort en 44 100 Hz par défaut, RetroArch en 48 000 Hz : *Audio → Plugin options → 48000Hz
samplerate* donne la même chose que le cœur RetroArch. L'interpolation se règle dans le même menu.

### Manette

*Input → Map game inputs…* (F5). La touche Pièce (Coin) sert aussi, comme dans RetroArch, à la roulette de la
sélection (Hyper, Upper) et à la provocation en combat (option « Taunt on Select »).

## 4. Musique PS2 et rejeu des voix

Rien à régler : les musiques en flux (`hsfa_flux.bin`) et, si l'archive en contient, le rejeu des voix et bruitages
SFA1 / SFA2 d'Hyper (`hsfa_rejeu.bin`, `hsfa_rejeu_table.txt`) sont lus dans l'archive du jeu, comme dans RetroArch.
L'archive doit être un `.zip` (pas `.7z`) et son chemin ne doit contenir que des caractères de la page de codes de
Windows (ex. pas de caractères chinois dans un système français).

## 5. Sauvegardes

- La sauvegarde de la borne (EEPROM : réglages, records) est gardée automatiquement par FBNeo à la sortie du jeu
  (`config\games\<jeu>.fs`, comme pour tout jeu CPS-2).
- États : *Game → Save states…* (Ctrl+F10 / Ctrl+F9, emplacements F8 / F11). Ils contiennent aussi les zones HSFA
  du cœur (transparence des objets d'Upper / Hyper, patch 0010 ; QSound, objets, palette, 16:9, patch 0029) : après un
  chargement, l'image et le son reprennent exactement comme sans chargement. Depuis le patch W06, c'est vrai aussi du
  rembobinage (*Game → Rewind*) et du run-ahead (*Video → RunAhead*).
- Les états de RetroArch et ceux de FBNeo autonome **ne sont pas interchangeables** (formats différents des deux
  frontaux). Un état fait avec `fbneo64.exe` ne doit pas être rechargé dans `fbneo64ws.exe`, et inversement.

## 6. Limites connues

- Windows seulement pour l'instant (64 bits). La version 32 bits n'a pas été essayée.
- Musique ou rejeu **hors archive** : comme le cœur RetroArch (`<system>/fbneo/hsfa/`), le programme cherche
  `Y_DATA.BIN`, `anthology.iso` ou `ydata.txt` (musique), `X_DATA.BIN` ou `xdata.txt` (rejeu) et les tables
  `hsfa_flux_table.txt` / `hsfa_rejeu_table.txt` dans **`support\hiscores\hsfa\`** (patch 0030). Inutile avec les
  archives construites par le script, qui contiennent tout.
- La boîte « À propos » indique le compilateur de la machine de construction (Linux), pas celui de l'exécutable.

## 7. Licence

FinalBurn Neo et ses modifications HSFA suivent la licence FinalBurn Neo (texte complet : `LICENSE-FBNeo.txt`) :
pas de vente, pas de dons, sources des modifications publiques (patchs du projet). Autres composants (stb_vorbis,
QSound HLE) : `NOTICE.md`. Aucune ROM n'est fournie : les jeux sont reconstruits depuis vos propres disques.
