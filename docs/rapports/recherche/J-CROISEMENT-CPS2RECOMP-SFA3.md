# Croisement : ce que cps2recomp nomme dans *Alpha 3*, face à notre index (2026-11-10)

Source lue : dépôt public `tmcleroy/cps2recomp` (GPL-3), dossier `games/sfa3/` (`PROGRESS.md`, `src/sfa3.h`, `src/*.cpp`),
version du 6 novembre 2026 (commit `b9064a5`). Même programme que notre `sfa3ud` (son `sfa3u`, 980904 ; il l'a vérifié,
ticket n° 244). **Rien n'est copié dans l'index** : ce rapport liste des adresses et leur rôle, reformulé, pour une
vérification au banc. Les entrées qui seront confirmées citeront « cps2recomp » comme source.

Méthode : relevé de toutes les adresses de RAM (`$FF8000`-`$FFFFFF`) et de ROM (`$000000`-`$3FFFFF`) citées dans ces
fichiers (256 adresses distinctes), comparées à `re/connaissances/sfa3_arcade.tsv` (colonnes `adresse` et
`adresse_autres`, plages comprises) et aux champs `A5` de `re/connaissances/champs.tsv` (décalage arcade et alias
`cps2:` / `arcade:` / `img:`). Le script de relevé n'est pas versé (il lit un dépôt tiers) ; il est refaisable en une
passe.

## 1. Bilan

| statut | nombre | sens |
|---|---|---|
| connu | 141 | l'adresse est une entrée de notre index |
| dans une zone | 84 | ROM : l'adresse tombe dans une fonction ou une table que nous décrivons par une plage |
| nouveau | 31 | absente de notre index (toutes en RAM) |

Toutes ses adresses de ROM sont donc déjà couvertes par notre index, au moins comme partie d'une plage. Les 84 « dans
une zone » sont surtout des points d'entrée internes (sous-routines, cas d'un saut calculé) que nos plages englobent :
utiles pour affiner, pas urgents.

**Correction de la note §7.1 du README** : `$FF810B` (« bits de pose de fin de manche ») n'est pas absente de notre
index. Elle est dans `champs.tsv` (`ko_poses_fin_terminees`, confiance « mesuré », `BSET D0,$10B(A5)` en ROM `$29E0C`),
et cps2recomp la cite justement d'après notre index, puis l'a vue en jeu. Ses notes situent l'écriture dans la routine
`$029E10`, notre index à l'instruction `$29E0C` : même endroit. Rien à vérifier de plus.

## 2. Contradictions à trancher au banc (priorité)

| adresse | notre index | cps2recomp | vérification proposée |
|---|---|---|---|
| `$FF8097` | `ecran_retournement` (écran retourné) | mode de pièces du menu de test (lu dans l'enregistrement des réglages en `$0018F2` ; 0x12 = jeu gratuit) | changer le mode de pièces au menu de test, puis le retournement d'écran, et relever l'octet |
| `$FF810C` / `$FF810D` | `$10C` : `manche_10d` ; `$10D` : `ko_resultat_manche` | `$10C` : résultat de la manche (1 J1, 2 J2, écrit en `$009BEE`) ; `$10D` : temps écoulé (`$009C14`) | finir une manche par K.O. de chaque côté, puis au temps ; relever les deux octets |
| `$FF810A` | alias `cps2:$FF810A` de `ko_poses_fin_terminees` | images de la seconde de l'horloge (décomptées en `$009BFE`) | point d'arrêt en écriture pendant un combat ; notre ligne 660 (image d'Upper MAX : octet bas = minuterie) va dans son sens, l'alias de la ligne 75 est sans doute à retirer |
| `$FF8108` | alias `img:+$108` / `cps2:$FF8108` de `hud_chrono` | copie, prise au début d'une partie, du nombre de manches à gagner réglé sur la carte (`$008D7C`) | régler le nombre de manches au menu de test et relever l'octet en début de partie |

## 3. Adresses nouvelles (31, toutes en RAM)

Reformulées d'après ses notes ; à vérifier avant toute entrée.

- **Pièces et crédits** : `$FF8076` crédits payés non joués ; `$FF80C3` pièces comptées vers le crédit suivant ;
  `$FF8072` et `$FF807A` pièces par crédit (mises à 0101 en jeu gratuit) ; `$FF809C` drapeau de jeu gratuit. Notre
  fonction `$007BDA-$007D9D` (`arcade_credits_joueur`) parle déjà de la structure `$70(A5)` et du gratuit
  `$9C`/`$9D`/`$9E(A5)`, mais sans entrées propres.
- **Difficulté** : `$FF80BE` copie de la difficulté de l'ordinateur prise au début d'une partie (`$008D70`) ; l'option
  elle-même est notre `$FF80A0`.
- **Caméra et plans** : `$FF8280` enregistrement du plan du décor (où la caméra doit aller en +20/+24, tremblement en
  +50/+54, butées en +40-+46, de 256 à 640) ; `$FF8294` caméra en Y (notre `$FF8290` est la caméra en X) ; copies de la
  caméra en `$FF8026`, `$FF82A0`, `$FF82A8` ; plans de fond `$FF8200` (tuiles de 8 pixels) et `$FF8300` (32 pixels).
  Utile pour le 16:9 calé sur le décor.
- **Projectiles** : deux réserves de douze enregistrements de 0x100, `$FF9400` et `$FFA000`, disposés comme un joueur
  pour leurs boîtes (le test de portée de garde `$02AB24` parcourt les deux).
- **Réserves d'objets** (prises en `$01C1C8`, rendues en `$01C206`) : sept réserves `$FF9400`, `$FFA000`, `$FFAC00`
  (8 × 0x80), `$FFB000` (32 × 0x80, notre `a5_reservoir_acteurs`), `$FFC000` (16 × 0x80), `$FFC800` (16 × 0x80, notre
  `a5_reservoir_effets`), `$FFD000` (7 × 0x200) ; têtes de liste `$FFEE84`-`$FFEE90` (un mot par réserve) et compteurs
  `$FFEEB6`-`$FFEEBC` (un octet par réserve ; nous n'avions que `$FFEEB6`).
- **Panneau** (noms et visages sous les barres de vie) : un objet de la dernière réserve, en `$FFDC00` pendant un
  combat ; les noms en +56, les visages en +46.

## 4. Noms connus, précisés par ses notes

- `$FF80AC` (notre `var_00ac`) : joueurs ayant choisi personnage et ISM (bit 0 J1, bit 1 J2).
- `$FF8138` (notre `a5_mode_138`) : mode de jeu ; à 0, mode ordinaire.
- `$FF80A8` : joueurs en jeu (même sens que notre `joueur_bits_en_jeu`).

## 5. Suite

- Les quatre contradictions du §2 d'abord, puis les adresses du §3 par groupes (une partie suffit pour pièces,
  caméra et réserves), avec `re/outils/verifie.py` à chaque versement.
- Son `games/sfa3/entries.txt` (4 655 adresses atteintes par sauts calculés, relevées en jeu) recoupe nos bornes de
  routines : à comparer plus tard à nos plages, sans urgence.
