# Textes des persos MAX (citations, bio, fiche, scénario + fin) : extraits

Note de la session MAX, 2026-10-04. Rien n'est poussé. Outil : `sfa3max-psp-widescreen/work/re/convert/textes_max.py`.
Sorties : `~/.cache/sfa3max/converti/plXX/textes.json` (structuré) et `textes.txt` (lisible), pour pl26-pl29.

## 1. Où sont les textes côté PSP (ASCII anglais, dossier `USRDIR/eur/data`)

| famille | fichier, entrée (type) | contenu chez Eagle | équivalent module (ta note hors combat) |
|---|---|---|---|
| citations de victoire | `winXX_e.pac`, entrée 5 (`0x10002`) | 8 × 2 lignes | citations (8 par perso) — **mêmes textes que l'arcade chez Ryu** |
| biographie | `opXX_e.pac`, entrée 3 (`0x10000`) | 3-4 × 2 lignes | bios |
| fiche (PERSONAL DATA, taille, poids, groupe sanguin, mensurations, origine…) | `opXX_e.pac`, entrée 4 (`0x10004`) | 9 lignes | ? (pas vu côté module) |
| dialogues du scénario (avant le boss) + fin | `endXX_e.pac`, entrée 14 (`0x10003`) | 22-28 enregistrements | dialogues + lignes des fins |

Recoupement : 1 410 des 2 451 chaînes de la zone texte de `ro3` se retrouvent mot pour mot dans ces fichiers.

## 2. Format

- PSP : enregistrements de `0x80` octets = `[total de caractères] ([position] texte 0)…`, remplis de zéros.
- Module : mêmes lignes `[position] texte 0`, **enchaînées sans l'octet total ni le remplissage** ; octets de position
  identiques (Ryu : `0x0B`, `0x08`). Dans les fins, le module a parfois un octet `0x70` en plus devant une ligne
  (locuteur / couleur ? ton `textes.py` le sait sans doute).
- ⟹ conversion mécanique : retirer l'octet total et le remplissage ; les pointeurs/listes de lignes sont à refaire.

## 3. Pas encore fait

- **Reporté en fin de projet (décision utilisateur 2026-10-04 : réutiliser des fins existantes d'ici là).** Images des fins (`endXX_e.pac` : entrées 1-10 = images GBIX/PVRT, 11-13 = tuiles/sprites, 15-20 = données de script
  de la fin ?) : à convertir en tuiles CPS2 + tilemaps + palettes, ou à remplacer par une fin existante.
- Portraits / noms (sélection : `select_e.pac`, `msel_e.pac`) : non regardés.
