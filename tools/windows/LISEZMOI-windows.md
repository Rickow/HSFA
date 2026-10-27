# Cœurs HSFA pour RetroArch sous Windows (64 bits)

Mêmes cœurs que pour Android, Linux et ROCKNIX : mêmes jeux, mêmes zips, mêmes réglages. Seul le fichier du cœur
change (`.dll` au lieu de `.so`).

Ces cœurs (patchs 0001-0014 et 0007b ; licence : `LICENSE-FBNeo.txt`, jointe) lisent les musiques d'Hyper en ADX **et** en Ogg Vorbis : les anciens zips restent valables,
et les zips construits avec `HSFA_FLUX_FORMAT=ogg` (environ 5 fois plus légers) aussi. Ils contiennent aussi la carte
musique (musiques ZERO / ZERO 2 par leurs pilotes d'origine) : elle ne s'active qu'avec un zip construit avec
`HSFA_PARTITIONS=1`.

| Fichier | À quoi il sert |
|---|---|
| `cores/fbneo_hsfa_libretro.dll` | cœur **« FinalBurn Neo HSFA »** (4:3) : SFA3, Upper et Hyper retraduits |
| `cores/fbneo_hsfaws_libretro.dll` | cœur **« FinalBurn Neo HSFA Widescreen »** (448×224, 16:9) |
| `info/*.info` | fiches des deux cœurs pour RetroArch (nom affiché, extensions) |

## Installation

1. Ouvrir le dossier de RetroArch (par exemple `C:\RetroArch-Win64\`).
2. Copier les deux `.dll` dans son sous-dossier **`cores\`**, et les deux `.info` dans **`info\`**.
   Les cœurs n'écrasent pas le FBNeo habituel : ils coexistent, avec des options et des sauvegardes séparées.
3. Copier les jeux (`sfa3hsfa.zip`, `sfa3uhsfa.zip`, `sfa3umhsfa.zip`, `sfa3hhsfa.zip`) dans un dossier de jeux.
   **Ne pas renommer les zips** : le nom du fichier désigne le jeu. Ce sont les mêmes zips que sur Android.
4. **Charger un contenu** → choisir le zip → choisir le cœur **FinalBurn Neo HSFA** (ou **Widescreen**).

Musique d'Hyper : comme sur les autres systèmes (voir `tools/fbneo-hsfa/LISEZMOI-hyper.md`). Dans le dossier
**`system\`** de RetroArch, créer `fbneo\hsfa\` et y mettre `hsfa_flux_table.txt` plus le `Y_DATA.BIN`, l'ISO renommée
`anthology.iso`, ou un `ydata.txt` contenant le chemin complet (par exemple `D:\Jeux\PS2\anthology.iso`).

Commandes et réglages : identiques aux autres systèmes (`tools/fbneo-hsfa/LISEZMOI-coeur.md`).

## Limites connues

- Le zip d'un jeu doit faire **moins de 2 Go** : la lecture des membres du zip (`cps_hsfa.cpp`) utilise encore des
  positions 32 bits sous Windows. Le zip d'Hyper fait 709 Mo, donc rien ne change aujourd'hui. Le lecteur de flux,
  lui, accepte des fichiers plus gros (ISO comprise).
- Testé sous Wine (pas encore sur un vrai Windows) : chargement des deux cœurs, puis 2 400 images de *Street Fighter
  Alpha 3* arcade (`sfa3.zip`) avec image et son ; banc du lecteur de flux (`tools/flux/tests`) compilé pour Windows :
  23 contrôles bons. Les jeux HSFA eux-mêmes n'ont pas été lancés (pas de zip HSFA dans la
  session de construction).

## Construire

Depuis Linux, avec MinGW-w64 :

```bash
apt-get install g++-mingw-w64-x86-64-posix gcc-mingw-w64-x86-64-posix
# FBNeo au commit af5d3f3, patché selon patches/fbneo/README.md, puis :
tools/windows/build_win.sh <dossier FBNeo>          # les deux cœurs ; ou ... hsfa / ... hsfaws
```

`LIBS=-static` (dans le script) est indispensable : sans lui, la DLL dépend de `libwinpthread-1.dll`, absente de
RetroArch, et le cœur ne se charge pas. Dépendances attendues : `KERNEL32.dll` et `msvcrt.dll` seulement.

Test sans Windows : `charge.c` (charge le cœur et appelle `retro_init`) et `joue.c` (charge un jeu, fait tourner N images,
compte le son, écrit la dernière image en BMP), compilés avec `x86_64-w64-mingw32-gcc` et lancés avec `wine64`.
```bash
x86_64-w64-mingw32-gcc -O2 -o joue.exe tools/windows/joue.c -lm
wine64 joue.exe fbneo_hsfa_libretro.dll jeu.zip dossier_system 2400 image.bmp
```
