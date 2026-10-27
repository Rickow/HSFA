# Greffe de la couche Arcade d'Upper dans Hyper (voie B) — étape 5

État au 2026-10-18. Pour reprendre : lire d'abord `ETAT.md`, puis ce fichier, qui s'appuie sur `GREFFE-ETAPE4.md`.

## 1. Résultats

| point | état |
|---|---|
| intégrité après l'incident sur `regions()` | vérifiée. Avec les interrupteurs de l'étape 5 à 0, `ro9a4_fige` se reconstruit **à l'identique** (`89f483c1`, toutes les ROM programme, bloc, module, blocs ext). |
| 1. fins de Ryu (ZERO 3, ALPHA) | **abouties**. Durée 11 780 images, comme Upper (11 780). La cause était une donnée (table d'animation coupée), pas l'aiguillage du dessin (§2). |
| 2. balayage des fins | **59 fins abouties sur les 85 combinaisons sélectionnables** (75 des 160 combinaisons perso × version ne sont pas sélectionnables dans la grille d'Hyper) ; écart de durée avec Upper dans ±2,2 % (§3). |
| 3. planisphère | **dessiné**. scroll2 et scroll3 sont identiques à Upper, cellule par cellule. Il reste quelques tuiles rouges sur scroll1 (§4). |
| 4. fonds | fins : **presque toutes justes** (Ken : énergie psycho, cockpit, image finale) ; seule la 1re scène, sur le décor du boss, est fausse. CONTINUE et GAME OVER : faux, et le compteur reste figé sur « 0 » (§5). |
| 5. données mortes | l'Arcade d'Hyper lit peu de données qui lui sont propres. Les trous de la carte 68K sont la vraie réserve (§6). |
| place | trous T1-T6 de la carte 68K branchés (`TROUS=1`) ; T1 sert déjà (`ext_410000.bin`). |

Constructions :

| nom | contenu |
|---|---|
| `ro9a5_fige` (= e7h) | Ryu abouti ; base du 1er balayage |
| **`ro9a5b_fige`** (= e7o) | + LIB_SPANS, CARTE_EFFACE, 515 exclusions de scripts, FIN_J ; `md5.txt` et `VARIABLES.txt` dans le dossier |
| e7q | + DEC_PETITES, non figée |

Rebase v150 fait : témoins Hyper `cb9b37b9`, Upper `36fc4f37` ; diff `diffs/07-greffe-traducteur-v150.patch` ; ROM de la greffe identiques entre v149 et v150.

VERSUS de ro9a5 (e7h) contre le témoin v149 : les choix sont les mêmes ; on retrouve les écarts de 48 images (déjà vus entre v148 et v149), et de 96 à certains endroits.

## 2. Correctifs de l'étape 5

- **`DEC_GRANDES=1`** (`donnees2.regions`) : grandes tables de décalages 16 bits, comme la table d'animations
  0x816160 (`w0` = `$230`, entrées vides à 0).
  - Si les cibles d'une table tombent dans une **autre** région copiée, les régions entre les deux sont fusionnées
    (trous ≤ 8 Ko).
  - Effet sur Ryu : l'animation des objets `$4B` était décalée de `$340` à cause du trou non copié. Cela suffit à
    faire aboutir sa fin, sans greffer l'affichage d'Upper.
- **`DEC_PETITES=1`** : la même règle pour les tables de `$10` à `$80` (toutes les entrées paires et ≥ `w0`). Elle
  coûte 49 Ko et n'a pas d'effet visible sur CONTINUE.
- **`LIB_SPANS`** : les 13 bases de données du moteur de plans d'Upper sont copiées d'un seul tenant jusqu'à la
  dernière lecture d'Upper. Ce sont des bibliothèques de blocs indexées (base + index × pas ; par exemple 0x6CF5F0 +
  `$86` × `$300`).
  - Effet : planisphère et fonds des fins justes.
- **`CARTE_EFFACE=1`** : avant 0x253A80, `remap_ids` appelle les effacements de la sélection d'Upper (copies de
  0xC5C10 et 0xC5C60). Effacer scroll1 par Hyper 0x38AE50 (`CARTE_S1=1`) fait planter des parties avant la fin :
  laissé à 0.
- **`LUI_ST=1`** (`outils/greffe.py`) : la valeur d'un `lui` rangée en mémoire est relogée quelle que soit la base
  (68 sites).
  - Exemple : `LEA $700000,A2` de l'affichage 0x13D820 visait `$AD6000`.
  - Effet : rend visibles les objets dessinés par l'affichage d'Upper (`AFFICHAGE_UPPER`, qui reste à 0).
- **Exclusions dans les scripts de fin** :
  - `outils/scripts_upper.sh` journalise le pointeur `$8034` d'Upper pendant chaque fin ;
  - `etape4/exclus_scripts.py` repère les longs alignés, dans les plages de script parcourues, qui seraient relogés
    (en donnée ou en code) sans preuve de conversion. Ils vont dans `donnees/ptr_exclus.txt` : 515 cases, 18 persos.
  - `PTR_EXCLUS` s'applique maintenant aussi aux pointeurs de données.
  - Persos réparés : 06, 0F, 10.
- **`FIN_J=1`** (`greffe3`) : dans le moteur de fin 0x29000-0x32000, une routine de la règle j) ne va à Hyper que si
  elle est équivalente.
  - Exemple : 0x2A3D0, gestionnaire des acteurs de fin, était envoyé sur Hyper 0x12EFC0, donc sur le moteur des
    joueurs d'Hyper.
  - Persos réparés : 08, 0C, 0E.
  - La même exigence étendue à toute la règle j) (`J_EQUIV`) double le plan (3 953 routines) et déborde : écartée.
- **`TROUS=1`** : nouvelles fenêtres 68K dans les trous de la carte (T1 `$410000`, T4, T5, T3, T2, T6). En plus, des
  morceaux PS2 `$C10000-$C2FFFF`, `$C40000-$C7FFFF` et `$D10000-$D1FFFF`.
  - Le fichier 547 d'Hyper occupe `$C84000-$D0B187` en PS2 comme en 68K : ces adresses sont à éviter.
  - Les pointeurs reçoivent l'étiquette `$01xxxxxx` par `HW_TAG` du traducteur.
  - `mame_test.py` accepte des fenêtres sous `$940000`.
  - Diff contre v149 : `diffs/06-greffe-traducteur-v149.patch`.

## 3. Balayage des fins

- Commande : `outils/balayage_fins.sh CONSTRUCTION ["persos"] ["versions"]` (P=3, `PREFIXE=`, `ARRET_FIN=1`).
- Tableau : `etape4/tableau_fins.py PREFIXE`.
- Durées d'Upper : `donnees/fins_upper.tsv`, tiré des journaux u_lu.
  - 9 persos n'ont pas de durée de référence : 04, 07, 0C, 10, 1A, 1B, 1D, 20, 23. Le journal d'Upper s'arrête avant
    la fin.
- Sur les 160 combinaisons, **75 ne sont pas sélectionnables** dans la grille d'Hyper : persos 12-14 et 24-27, et
  versions absentes pour la plupart des persos ≥ `$15`. La partie retombe alors sur un autre perso ; le tableau les
  marque.

Résultat final sur `ro9a5b_fige` (`traces/tableau_f7.md`) : **59 fins abouties sur les 85 combinaisons
sélectionnables**. Quand Upper a une durée de référence, l'écart reste dans ±2,2 %.

| perso | versions abouties | échec |
|---|---|---|
| 00, 01, 02, 03, 08, 09, 0A, 0B, 0C | Z, Z2, A, Z3 | — |
| 04 | Z, Z2, A, Z3 (pas de référence Upper) | — |
| 0D, 0E, 10 | Z2, A, Z3 | — |
| 16 | A, Z3 | — |
| 23 | Z3 | — |
| 06 | Z2, A, Z3 | Z : plante avant la fin |
| 0F | Z2, Z3 | A : plante avant la fin |
| 11 | A, Z3 | Z2 : plante avant la fin |
| 05, 15, 17, 18, 19-22 | — | plantent pendant la fin |
| 07 | — | fin jamais atteinte en 45 000 images (dans Upper non plus, journal u_lu) |

Arbitrage `FIN_J` :

- greffer 0x2C510 (copie des palettes et plans de scène, par `$8008`) répare **0E** mais casse **18** (à 21 130,
  dans 0x2E49C) ;
- `FIN_J_SAUF=2c510` (e7u) fait l'inverse : 18 aboutit en 6 993 images, exactement comme Upper, et 0E plante ;
- `ro9a5b_fige` garde le premier choix ; le défaut du code est désormais `FIN_J_SAUF=2c510` (e7u).
- Le bilan est le même dans les deux cas : la donnée lue par la copie de 0x2C510 pour 18 est à examiner.


Échecs restants et lieux :

| perso | lieu de l'échec |
|---|---|
| 05 | Hyper 0x387560 |
| 15, 1A | `4a75 …` |
| 17 | Hyper 0x39F90 |
| 19 | 2ᵉ plantage à 19 061 |
| 1B, 20 | Hyper 0x3F680, écriture `4(A1,D0)` |
| 1C, 1D | Hyper 0x399E80 |
| 1E, 22 | table d'animation d'Hyper 0x3A2370 |
| 1F | avant la fin, interpréteur d'Hyper |
| 21 | copie d'Upper 0x2E894, `MOVEA.L 0(A2,D0)` |

Presque tous ces échecs sont des objets d'Upper traités par un moteur d'objet ou d'animation d'Hyper, choisi par
homologue (règles e/j). La suite consiste à greffer, perso par perso, la chaîne fautive. La méthode est la même que
pour 0x2A3D0 : pile au moment du plantage, puis décision du plan.

## 4. Planisphère

- Mesures d'Upper faites avec l'oracle (tournee_greffe) :
  - présentation Arcade aux images 2 275-2 498 ;
  - `$32/$3A` = `$1B0E/$2461` ;
  - `$100` = `$32` ;
  - pages `$190`.
- Le planisphère est dessiné à la **sélection** d'Upper (image 1 990 : 0xC58C0, puis 0x253A80) et reste ensuite en
  VRAM.
- ro9a e7k à l'image 700 contre Upper à 2 400 :
  - scroll2 et scroll3 : 4 096/4 096 cellules identiques ;
  - scroll1 : quelques restes d'écrans d'Hyper.
- Planches : `traces/planche_e7i_vues.png` et `traces/planche_u_arc_vues.png`.

## 5. Fonds des fins, CONTINUE, GAME OVER

- Fins : `traces/planche_r5b_ken_fin.png`.
  - Correct : scènes d'Upper (énergie psycho, cockpit, image finale avec décor).
  - Faux : la 1re scène, où le décor du boss d'Upper n'est pas dessiné (le combat a utilisé le décor 4 d'Hyper).
- CONTINUE (`traces/planche_r7q_perdu.png`, Upper : `traces/planche_u_perdu.png`) :
  - correct : portrait gris, durée de l'écran ≈ Upper ;
  - le grand chiffre reste sur « 0 » ;
  - le texte « CONTINUE? n » et les bandes de scroll1 manquent ;
  - le fond porte des tuiles de texte d'Hyper.
- Objets : ce sont les mêmes que dans Upper (type `$0D`, gestionnaire greffé), sauf l'emplacement `$1E`, absent.
  Piste : la création de cet objet.

## 6. Données mortes et récupérables (point 5)

Méthode :

- `lua/lus_ro9.lua` : prises de lecture sur les données d'Hyper (image `$B3000-$3FFFFF`, ext `$940000-$C31FFF`),
  réinstallées toutes les 120 images, avec `LUS_HORS_MANCHE` ;
- `etape4/donnees_mortes.py` fait la comparaison.

Résultats :

- L'Arcade d'**Hyper seul** (témoin v149, Ryu ZERO 3, partie complète avec fin) ne lit hors des manches que
  **116 Ko** de ses données.
- **9 Ko** de ces 116 Ko ne sont jamais lus dans ro9a (Arcade de Ryu, VERSUS sur 30 000 images, attraction). Liste :
  `traces/donnees_mortes_ryu.txt`.

| ro9a | taille |
|---|---|
| `$164A00-$1654FF` | 2 816 o |
| `$166E00-$1678FF` | 2 816 o |
| `$169200-$169CFF` | 2 816 o |
| `$9A7640-$9A783F` | 512 o |
| `$9ACA40-$9ACC3F` | 512 o |
| `$9A6240-$9A633F` | 256 o |

Conclusion :

- La couche Arcade d'Hyper est petite. Ses données « mortes » valent quelques dizaines de Ko par perso (surtout les
  fins).
- Une **preuve complète** demanderait les 40 fins d'Hyper, le TRAINING et les autres modes.
- Les trous de la carte 68K (5,08 Mo) restent la réserve à utiliser.

## 7. Découvertes durables

- Les tables de décalages 16 bits (animations, blocs) obligent à garder les distances. Une copie par morceaux décale
  les cibles : il faut fusionner les régions reliées par une table, et copier d'un tenant les bibliothèques
  « base + index × pas ».
- Dans les scripts de fin, les paires de mots ressemblent à des pointeurs. On les exclut à partir des plages que le
  script d'Upper parcourt réellement.
- La règle j) « homologue non vue en Arcade » est fausse dans le moteur de fin : exiger l'équivalence.
- `tournee_arcade.lua` ne joue pas Upper ; dans Hyper, seules 85 des 160 combinaisons perso × version sont
  sélectionnables.
- L'Arcade d'Hyper lit ≈ 116 Ko de données hors des manches : il y a peu à récupérer.
