# Patchs de l'ISO PS2 : tout débloqué et widescreen 16:9

Deux outils pour jouer à *Street Fighter Alpha Anthology* elle-même, sur PS2 ou sous PCSX2. Ils lisent **votre** ISO
USA (`SLUS-21317`) et écrivent une **copie** patchée : la source n'est jamais modifiée. Ils ne contiennent aucune
donnée de jeu (seulement des adresses et des mots MIPS d'origine / patchés). Python 3 seul, sans dépendance.

| Outil | Effet | Usage |
|---|---|---|
| `unlock_patcher.py` | **tout débloqué** : SFA3 Upper et Hyper Street Fighter Alpha disponibles sans carte mémoire (Select sur l'écran de choix de version), tous les persos | `python3 unlock_patcher.py SOURCE.iso [DEST.iso]` |
| `sfa_anthology_ws_patcher.py` | **widescreen 16:9 natif** (rendu 448 px, décor prolongé des deux côtés, action et HUD centrés) **+ tout débloqué** | `python3 sfa_anthology_ws_patcher.py SOURCE.iso [DEST.iso]` |

- `DEST` par défaut : `SOURCE [Unlocked].iso` ou `SOURCE [Widescreen].iso`. Il faut environ 4,7 Go libres.
- Le widescreen comprend déjà le tout-débloqué : inutile d'enchaîner les deux. Il accepte une ISO d'origine ou déjà
  débloquée.
- Chaque mot est contrôlé avant d'être écrit (valeur d'origine attendue), le module recompressé est relu et comparé
  octet à octet. En cas d'erreur, la copie est supprimée et rien n'est laissé à moitié patché.
- Sortie reproductible : deux passes sur la même source donnent la même ISO (même md5).
- Ensuite, en 16:9 : régler PCSX2 (ou le téléviseur / la console) sur un rapport 16:9.

## Ce qui est modifié

- **Tout débloqué** : dans le module commun `e203` de `X_DATA.BIN` (compressé MWo3), 4 lectures de l'octet de
  déverrouillage remplacées par la constante `0xFF` (`0x1C8E58`, `0x1C8E74`, `0x1C8E90`, `0x1C8EAC`).
- **Widescreen (v10)** : 3 mots de `SLUS_213.17` (largeur 384 → 448) ; dans `e203`, le tout-débloqué, des tampons de
  décor relogés en RAM libre, des couches de décor élargies et 7 petites routines (« caves ») qui recentrent la vue :
  lecture du décor 32 px plus à gauche, sprites et HUD 32 px plus à droite. Détail :
  [legacy/docs/PROJET-Anthology-Widescreen-Tiles.md](../../legacy/docs/PROJET-Anthology-Widescreen-Tiles.md) §3.

## Limites connues

- **Widescreen** : validé en jeu sur Upper et Hyper. Le module patché est commun à tous les jeux du disque : les
  autres jeux (ZERO, ZERO 2, ALPHA 2…) n'ont pas été vérifiés décor par décor. Défauts relevés : quelques écrans hors
  combat décalés (sprites +32 px là où il ne faut pas), un petit bout de ciel répété au bord extrême de certains
  décors, apparition possible d'objets aux bords (élimination calculée pour le 4:3).
- **CRC** : le widescreen modifie `SLUS_213.17`, donc le CRC du jeu dans PCSX2 passe de `72CE7A78` à `72CE7A38`. Les
  cheats et patchs `.pnach` écrits pour `72CE7A78` (dont ceux de [legacy/pnach](../../legacy/pnach/README.md)) ne
  s'appliquent plus à l'ISO 16:9, et ses sauvegardes d'état PCSX2 portent l'autre CRC. Le tout-débloqué seul ne
  touche que `X_DATA.BIN` : CRC inchangé.
- Seule l'ISO USA (`SLUS-21317`) est reconnue. Une autre version, ou une ISO déjà modifiée autrement, est refusée.
- Version d'origine du tout-débloqué : [legacy/tools/unlock_patcher.py](../../legacy/tools/unlock_patcher.py), qui
  patche l'ISO **en place** (sans copie). Préférer celle-ci.
