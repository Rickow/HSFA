# Greffe de la couche Arcade d'Upper dans Hyper (voie B) — étape 6

État au 2026-10-18. Pour reprendre : lire d'abord `ETAT.md`, puis ce fichier, qui fait suite à `GREFFE-ETAPE5.md`.

## 1. Constructions et balayages

| construction | contenu | balayage |
|---|---|---|
| `ro9a5b_fige` (étape 5) | — | f7 : 59/85 |
| **`ro9a6_fige`** (= e8g, `6de3578c…`) | PTR_BAS, FIN_J complet (0x2C510 greffée), ANIM_GREFFE, PLANS_CONT, banc corrigé | f8 : voir `traces/tableau_f8.md` |
| e8l (`83552909…`) | + FE_TABLE + affichage d'Upper complet (`AFFICHAGE_UPPER=1 DESSIN_UPPER=1`) | essais h4 ; balayage complet à faire |

- Outils :
  - `outils/balayage_liste.sh CONSTRUCTION PREFIXE` balaie les 85 combinaisons sélectionnables
    (`donnees/combinaisons_selectionnables.txt`) ;
  - `outils/pile_plantage.sh CONSTRUCTION PREFIXE PERSO [V]` donne la pile décodée au plantage.
- Banc : avec `PERDRE`, `tournee_arcade.lua` n'appuie plus sur aucune touche après le 1er combat. Avant, Start pendant
  la défaite était pris pour l'arrivée d'un 2e joueur, et l'écran de défaite était sauté.

## 2. Correctifs

- **PTR_BAS** : un pointeur de code à moitié basse < `$100` n'est accepté que dans une table.
  - Exemple : le flux de palettes de la fin du perso `$18` contient `$0020 $002A`, qu'on prenait pour une entrée de
    routine.
  - Le conflit 18/0E est **résolu** : 0x2C510 est greffée, et 18 comme 0E aboutissent.
- **FE_TABLE** : un pointeur à moitié basse `$FExx` est accepté dans une table (voisin de même moitié haute).
  - Exemple : la table de scènes de la fin du perso `$21` (`$0099FE18`…) n'était pas relogée.
- **ANIM_GREFFE** : le cœur de pose d'animation d'Upper (0xC8000-0xC97FF, 0xCE4F0, 0x139750) est greffé, au lieu des
  homologues d'Hyper.
- **PLANS_CONT** : pour CONTINUE et GAME OVER, scroll1 prend la base d'Upper, scroll2 et scroll3 celle d'Hyper. Upper
  réutilise à ces écrans le décor du combat déjà en VRAM, et ici ce combat était celui d'Hyper. CONTINUE montre donc
  le décor grisé, comme dans Upper.
- **Essais écartés** :

| interrupteur | effet | pourquoi il est écarté |
|---|---|---|
| `J_NON_INJ` (362 routines à homologue partagé) | répare 05 | casse 00, 08, 0E, 18 |
| `EFFACE_FIN`, `DECOR_BOSS_FIN` | posent le décor du boss d'Upper | tuiles fausses : il manque les bases de plans par décor |
| `REUTIL_STRICT` | — | bloc trop grand |

## 3. Échecs restants (pistes par perso)

| perso | état et piste |
|---|---|
| 05 | Upper 0x1724E0 → Hyper 0x388910 ; non réglé par ANIM_GREFFE |
| 15, 1C, 1D, 22 | moteur de dessin/animation d'Hyper sur des objets d'Upper ; avec l'affichage d'Upper (e8l), plantages ailleurs |
| 17 | objet `$5E00` traité par le moteur d'Hyper 0x39F90 (boucle principale d'Hyper) |
| 19 | copie d'Upper 0xC85EC : table d'animation lue dans les fichiers anim natifs, avec un décalage impair ; le fichier anim de fin du perso `$19` est sans doute mal choisi |
| 1B | va bien plus loin avec l'affichage d'Upper (33 827) |
| 21 | table de scènes réglée (FE_TABLE) ; plante ensuite dans le dessin d'Hyper 0x3A2230 (sans affichage d'Upper) |
| 06 Z, 0F A, 11 Z2 | plantent avant la fin, en combat : à vérifier dans Hyper seul |

## 4. Écrans

- **CONTINUE** :
  - la durée est conforme (2 548 images ; Upper 2 550) et le fond aussi (décor du combat grisé) ;
  - il reste : le chiffre figé sur « 0 », le texte « CONTINUE? n » et les barres de scroll1 ;
  - piste : l'objet `$1E` (type `$0D`) est créé, puis se libère lui-même au bout de 74 images (état 0x17BC90),
    alors que dans Upper il reste en vie.
- **GAME OVER** :
  - Upper : fond violet, gros « GAME OVER » et « TRY AGAIN » ;
  - ro9a : violet, mais des bandes de tuiles fausses et pas de lettres ;
  - Upper ne redessine pas les plans à cet écran ; il affiche ce qui reste de CONTINUE.
- **Scène 1 des fins** : le décor du boss d'Upper n'est pas en VRAM. Le poser exige les bases de plans par décor
  d'Upper, c'est-à-dire le chantier des décors.
