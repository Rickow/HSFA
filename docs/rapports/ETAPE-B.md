# Étape B de la réorganisation des données : relogement des pointeurs de code

Plan : `github/docs/ARCHI-Reorganisation-Donnees.md`. Point de départ : `work/agent_reorg_A/ETAPE-A.md` §5.
Tout est dans `work/agent_reorg_B/`. Le traducteur partagé, `work/mame*` et `max/` n'ont pas été touchés.

## 0. En bref

- **Trois interrupteurs**, tous à 0 par défaut. À 0, les octets sont identiques à aujourd'hui (§5.1).
  - `RELOGE_CODE` : étape B proprement dite.
  - `RELOGE_NATIF` : les tables relogées sont rangées en ordre 68K.
  - `RELOGE_RAM` : amorce de l'étape C, pour les tables de pointeurs vers la RAM.
- **SFA3, avec les trois à 1** :
  - 24 tables de pointeurs de code (710 cases) relogées à l'assemblage ;
  - **22 des 23 sauts indirects `JSR/JMP (An)` deviennent directs**, sans hachage `$3C0000`/`$3FF000` ni talon de données ;
  - 6 tables de pointeurs RAM (24 cases) relogées : 7 lectures n'appellent plus le talon `$400`.
- **Upper** : 22 sauts indirects libérés sur 23, avec les mêmes tables RAM. **Hyper** : 20 sur 20.
- **Appels de talons sur les parcours de l'étape A (attraction, tournée de Ryu, commandes ; 66 800 images)** :
  - avant : 7,03 M ;
  - après : 3,98 M, soit **−43 %** ;
  - talon de code : 1,14 M → 5 325 (seuls restent le site RAM `$40(A6)` et le noyau).
- **Fluidité** (test des commandes, combat en vitesse turbo) :
  - listes d'objets rendues par image : **0,667 → 0,955** (arcade : 1,000) ;
  - l'image répétée une fois sur trois en turbo (§103-§104) disparaît presque entièrement.
- **Piège découvert : `RELOGE_CODE=1` seul ne passe pas le test des commandes** (9 actions différentes, cadence 128,6 %).
  - La cause est une course de cadence propre au portage (§4), pas une faute de traduction.
  - En étant plus rapide, l'image turbo finit juste avant le retour de trame, et le jeu y perd une image.
  - Les trois interrupteurs ensemble passent de l'autre côté de cette fenêtre : **42/42 actions identiques, 133,3 %**.
- **Configuration recommandée : `RELOGE_CODE=1 RELOGE_NATIF=1 RELOGE_RAM=1`.** Validée ainsi :
  - **SFA3** : 3 diagnostics sans exception, commandes 42/42 à 133,3 %, 32 fins `fin=finie` avec captures = arcade ±1, journal de contrôle sans valeur PS2 aux sites libérés ;
  - **Upper** : diagnostic, 3 parties et 40 fins `fin=finie`, journal de contrôle propre ;
  - **Hyper** : partie VERSUS identique à la ROM d'aujourd'hui, journal de contrôle propre.

## 1. Méthode

### 1.1 Où sont les pointeurs de code

Aujourd'hui, un saut indirect se traduit ainsi :
`MOVEA.L <table>,An ; [remise en ordre du long] ; JSR CONV_An ; … ; JSR CCONV_An ; JSR/JMP (An)`.

- Le talon de données (`$400`) laisse passer l'adresse de code PS2.
- Le talon de code (`$3FF000`) la cherche dans la table de hachage `$3C0000`.

Les 23 sauts indirects de SFA3 ont trois formes :

| forme | exemple | sites |
|---|---|---|
| P1 : `MOVEA.L T_xxx(PC,Dn.W),An` → `JSR (An)` | aiguillage d'état `$3(A6)×4`, `T_589760` (8 appels par image de combat) | 12 |
| P2 : `LEA table.L,Ab [; Bcc ; LEA autre,Ab] ; MOVEA.L 0(Ab,Dn.W),An` → `JMP (An)` | tables par perso, `$103(A6)×4`, 32 cases, pas de `$80` | 10 |
| RAM : `MOVEA.L $40(A6),A0` → `JMP (A0)` | pointeur rangé par `MOVE.L T_5899a4(PC,D0.W),$40(A6)` | 1 (laissé) |

### 1.2 Analyse, dans `assemble.py` (`reloge_code`)

Elle tourne après `classify`, sur les éléments du traducteur.

**Définitions qui atteignent An.** Pour chaque `JSR CCONV_An ; JSR/JMP (An)`, on remonte le flot de contrôle :
- chute de l'élément précédent, et branchements internes qui visent l'élément (`tgt`) ;
- fenêtre de 14 éléments au plus.

L'analyse abandonne (le site est laissé tel quel) dans les cas suivants :
- **Entrée externe dans la fenêtre** : cible de `jal`, début connu du traducteur, cible d'aiguillage ou clé du talon de code.
  - Une clé tirée des **données** ne compte comme début de fonction que si l'instruction à k−8 est `jr`, `j` ou `b`, ou si k−8 et k−4 sont des `nop`.
  - Sinon c'est une valeur fortuite. Exemple : Upper `0x2E00DC` pointe un `lui $7000` au milieu d'une fonction ; sans ce filtre, un site d'Upper était perdu.
- **Appel** (`JSR`/`BSR`/aiguillage) dans la fenêtre.
- **Élément qui cite An** sans être une définition reconnue. C'est prudent : une simple lecture par An suffit à faire abandonner.

**Définitions reconnues.** Seules les formes P1 et P2 comptent :
- P1 : `dtab` absolu sur `T_xxx`, destination An ;
- P2 : `MOVEA.L 0(Ab,Dn),An ; JSR CONV_An`, dont **toutes** les définitions de Ab sont des `LEA $….L,Ab [PS2 p]`.

**Étendue d'une table.** Elle va de son début à la **table suivante référencée par le code** (`data_refs`), comme `read_jump_table`.
- Toutes les cases doivent être des débuts de fonction connus (les clés du talon de code) ou 0. Sinon, rien n'est fait.
- C'est la structure (pas, taille) qui fixe l'étendue, et non le journal. Le journal sert de contrôle (§5.3).
- Les bornes tombent juste :
  - SFA3 : tables d'aiguillage de 2 à 124 cases, toutes bornées par la table d'aiguillage `MOVE.W T(PC)` suivante ;
  - tables par perso : 32 cases à SFA3, 40 à Upper, 128 à Hyper.

**Effet.**
- Site libre : `JSR/JMP (An)` seul.
- Écrivain P1 : plus de `JSR CONV` (`Item.nofix`).
- Écrivain P2 : `JSR CONV` retiré.

### 1.3 Relogement des cases, dans `mame_test.py`

Chaque case v d'une table relogée reçoit `lab(v − RUNTIME_BASE)`.

C'est **exactement** la valeur que le talon de code rendrait à l'exécution : la table de hachage est remplie avec la même fonction `lab` et les mêmes clés. Pour le saut, le relogement équivaut donc au talon, case par case. Une case nulle reste nulle.

Le talon de données, lui, laissait passer ces valeurs sans les changer, qu'il s'agisse d'adresses de code PS2 ou d'adresses de code 68K (`< $94000`, sous ses plages). Le retirer derrière ces tables ne change donc rien.

Les autres lecteurs d'une table relogée voient une adresse 68K là où ils voyaient une adresse PS2. Ils sont listés par l'assemblage (§3). À SFA3, un seul cas : `MOVE.L T_5899a4(PC,D0.W),$40(A6)`, relu par le site RAM `JMP (A0)`, qui garde ses deux talons. Ces talons laissent passer une adresse 68K, et le journal de contrôle confirme qu'il n'y voit plus que des adresses 68K.

### 1.4 `RELOGE_NATIF=1` : tables en ordre 68K

Si une table relogée n'est citée **que** par les écrivains de sites libérés (et leurs `LEA`) :
- ses cases sont rangées en long gros-boutiste, sans échange des moitiés ;
- la « remise en ordre du long » (`EXG/MOVE SR/SWAP/MOVE CCR/EXG`) disparaît ;
- P1 devient `LEA table.L,An ; MOVEA.L 0(An,Dn.W),An` : plus de registre de base sauvé et rendu.

Le site d'aiguillage reprend alors la forme Capcom :
`LEA $99B20.L,A0 ; MOVEA.L 0(A0,D0.W),A0 ; MOVEQ #0,D0 ; MOVEQ #0,D7 ; JSR (A0)`.

Les tables citées ailleurs restent en ordre échangé, ainsi que, par un point fixe, toutes les tables de leurs écrivains. Exemple : `T_5899a0`, qui contient `T_5899a4`.

Résultat : 23 tables sur 24 à SFA3 et à Upper, 22 sur 22 à Hyper.

### 1.5 `RELOGE_RAM=1` : amorce de l'étape C

L'étape A, §5-C, conseillait de commencer par là.

- **Tables visées.** Celles dont toutes les cases, de leur début à la table suivante référencée, pointent la RAM PS2 `[RAM_HI<<16, +$10000)`. Pour SFA3 : `T_587740`, `T_58af80`, `T_5924b0`, `T_58cbf0`, `T_58cc00`, `T_594300`.
- **Relogement.** Les cases reçoivent ce que rendrait le talon `$400` : `v − R + $FF0000`.
- **Lecteurs.** Les `MOVEA.L T(PC,Dn),An` qui les lisent n'appellent plus le talon, et passent en ordre 68K si `RELOGE_NATIF=1`.
- **Prérequis.** Cet interrupteur demande `RELOGE_CODE` ≥ 1.

### 1.6 Mode contrôle `RELOGE_CODE=2`

Mêmes tables relogées, mêmes talons de données retirés, mais on **garde** :
- le talon de code aux sauts libérés ;
- le talon `$400` aux lecteurs des tables RAM.

Le journal des talons de l'étape A (`journal_conv.lua`) y voit alors les valeurs.

## 2. Interrupteurs

| variable | 0 (défaut) | 1 | 2 |
|---|---|---|---|
| `RELOGE_CODE` | octets d'aujourd'hui | tables de code relogées, sauts directs | contrôle (§1.6) |
| `RELOGE_NATIF` | ordre échangé | tables lues seulement par les sites libérés en ordre 68K, sans remise en ordre | — |
| `RELOGE_RAM` | — | tables de pointeurs RAM relogées, sans talon | — |
| `RELOGE_DEBUG` | — | raison de chaque site refusé | — |

**Sorties de construction** :
- dans `TRAVAIL/` : `etapeB_reloge.txt` (tables, adresses 68K, ordre, sites) et `etapeC_ram.txt` ;
- dans le journal de construction : la ligne `etape B : …` ;
- dans `carte_image.txt` : les marques `[etape B …]`, `[etape C …]` et `[ordre 68K]`.

## 3. Cases relogées, sites libérés

Détail complet : `resultats/reloge_ro3.txt`, `reloge_ro5.txt`, `reloge_ro9.txt`.

| | SFA3 (ro3) | Upper (ro5) | Hyper (ro9) |
|---|---|---|---|
| tables de code relogées (cases) | 24 (710) | 24 (839) | 22 (1 995) |
| dont en ordre 68K | 23 | 23 | 22 |
| sauts indirects libérés / total | 22 / 23 | 22 / 23 | 20 / 20 |
| tables RAM relogées (cases), lectures sans talon | 6 (24), 7 | 6 (24), 7 | 6 (24), 7 |
| site laissé | `$40(A6)` `JMP (A0)` (mips `0xBFE98`) | idem (`0x100440`) | — |
| taille du code | −602 octets (données en `$93000` au lieu de `$94000`) | −610 | −574 |

**Comparaison avec le journal de l'étape A.**
- L'étape A avait vu 224 cases de code. L'étape B en reloge 710, car l'étendue vient de la structure des tables.
- Toutes les cases de code vues par l'étape A sont couvertes. Les « 114 cases vues seulement par le talon de données » étaient les mêmes cases, vues aux `MOVEA` qui précèdent les sauts.
- Les deux seuls lecteurs restants sont le site RAM (14 k appels) et le noyau (création de tâche : 68 appels).

**Références aux tables relogées hors des écrivains libérés.** Recherche dans la carte, en noms `T_`, `[PS2 …]` et adresses 68K :
- seulement `T_5899a4` (SFA3) et son homologue d'Upper ;
- plus les `LEA` de base des sites P2.

## 4. La cadence turbo : pourquoi l'étape B seule ne suffit pas

**Symptôme.** Avec `RELOGE_CODE=1` seul, le test des commandes donne **9 actions différentes** et **5 167 tours en 4 019 images (128,6 %)**, contre 5 359 (133,3 %).
- Différences : marche avant `dx=114` au lieu de 120, et états transitoires en plus.
- Le jeu est pourtant plus rapide.
- Ce n'est pas une faute de traduction :
  - aucune exception ;
  - balayage des 32 fins correct (§5) ;
  - en mode contrôle, le journal ne voit que des valeurs 68K ;
  - le mode contrôle, un peu plus rapide qu'aujourd'hui, perd déjà quelques tours (132,8 %).

**Mesure** (`runs/cadence.lua` + `outils/cadence.py`) : par image, ligne des tours de jeu (écritures `$FF851C`), des fins de liste d'objets (`$8000` en `$7000x2`) et de l'IRQ2 (`$663888`).
- La boucle de jeu fait un tour, puis s'endort une image (`sleep(1)`, compteur du TCB décrémenté par le balayage vertical porté).
- En turbo, une itération sur trois fait deux tours.

| version | tours / image | images sans tour | listes / image | fin de liste, itération à 2 tours (médiane) |
|---|---|---|---|---|
| arcade | 133,3 % | 0 | **1,000** | ligne 210 |
| aujourd'hui (`RELOGE_*=0`) | 133,3 % | 0 | 0,667 | ligne 394 (132 de l'image suivante) ; toutes les itérations font 2 tours |
| `RELOGE_CODE=1` | 126,8 % | 29 / 600 | 0,800 | ligne 270 |
| `+ RELOGE_NATIF=1` | 129,8 % | 16 / 600 | 0,902 | ligne 260 |
| **`+ RELOGE_RAM=1`** | **133,3 %** | **0** | **0,955** | **ligne 251** |

(Images 4 000 à 4 600 du test des commandes. Les lignes se comptent depuis le début de l'image où l'itération commence, 262 lignes par image.)

**Mécanisme.**
1. Quand la liste de l'itération à deux tours finit **entre les lignes ~260 et ~267** (l'IRQ2 tombe à la ligne 5 de l'image suivante), le `sleep(1)` est posé juste **après** la décrémentation du balayage vertical.
2. La tâche dort alors une image de trop, et le jeu perd un tour.
3. Aujourd'hui, la liste finit bien après (ligne ~284 et au-delà). Le jeu enchaîne sans dormir et garde 133,3 %, mais ne rend que 2 listes pour 3 images. C'est « l'image répétée » des §103-§104.
4. L'arcade finit à la ligne ~210.

**Il faut donc soit rester en retard, soit tenir dans l'image avec de la marge.**
- `RELOGE_CODE=1` seul tombe dans la fenêtre : listes finies aux lignes 256-261.
- L'ordre 68K et les tables RAM gagnent encore ~10 lignes et passent devant : lignes 245-251, maximum 259 en régime normal.
- Restent de rares itérations très en retard (maximum 458), qui expliquent les 0,955 au lieu de 1.

**Conséquence pour la suite (étapes C-D).** Toute accélération doit être vérifiée par le test des commandes **et** par `cadence.py`. Une accélération partielle peut faire retomber l'image turbo dans la fenêtre. Plus de marge (étape D) éloigne définitivement le risque.

## 5. Validations

### 5.1 Interrupteurs à 0 : octets identiques

| module | md5 `sz3ud.03c` | référence |
|---|---|---|
| SFA3 (copie, tout à 0) | `568cef19769e97eca1983fc034384e60` | = md5 demandé |
| Upper | `a296538feff3d9a5317b1609bfb594c0` | = `work/mame_ro5` du 10/10 |
| Hyper (module son, comme `valide_tout.sh`) | `a37df09c86826203cbb79bf61b8c5784` | = traducteur d'origine (copie figée `untranspile.orig/`) |

**Le traducteur partagé a bougé pendant la session** : `agent_bandeau_A`, `FLUXEA`, dans `translate.py` et `mame_test.py`.
- Les diffs s'y appliquent sans conflit (`patch -p3`).
- Traducteur actuel patché, interrupteurs à 0 : `b62d489e…`, identique au traducteur actuel non patché.
- Traducteur actuel patché, interrupteurs à 1 : même relogement (24 tables, 22 sites, 6 tables RAM), et test des commandes 42/42 à 133,3 %, listes/image 0,955.

### 5.2 SFA3

| test | `RELOGE_CODE=1` seul | **les trois à 1** |
|---|---|---|
| diag 20 000 sans entrée / 20 000 avec entrées / 60 000 offensive | aucune exception ×3 | **aucune exception ×3** |
| test des commandes | **9 différentes**, 5 167 tours (128,6 %) (§4) | **42 actions, 0 différente** ; 5 358 tours en 4 019 images (133,3 %) |
| balayage des 32 fins | 32/32 `fin=finie`, captures = arcade ±1 | **32/32 `fin=finie`, captures = arcade ±1** |

- Sur le test des commandes en configuration complète, l'écart est de 5 358 tours au lieu de 5 359. Le tour manquant vient de l'image 3 834, où une itération turbo est en retard. Toutes les actions restent identiques.
- Balayages : `balayages/mame1_*` et `balayages/mame1c_*`.

### 5.3 Journal des talons (SFA3)

Mêmes parcours que l'étape A : attraction 20 000 images, tournée de Ryu 40 000, commandes. `outils/bilan_journal.py`.

**Contrôle (`RELOGE_CODE=2`, NATIF, RAM)** :
- les 22 sauts libérés et les 7 lectures RAM ne voient **que des adresses 68K** :
  - code : 1,14 M appels ;
  - RAM : 0,98 M ;
  - **aucune valeur PS2** ;
- le site RAM `$40(A6)` ne voit plus que des adresses 68K de code (il reçoit les cases relogées de `T_5899a4`) ;
- talon de code : 68 valeurs PS2 en tout, toutes au noyau (création de tâche, constantes `CODE_x`, hors de l'étape B).

**Valeurs « code PS2 » encore vues aux talons de données** (1 938 à 5 762 sur ~4-5 M).
- Elles sont toutes **inférieures à `$3C0000`**, dans le chevauchement code PS2 / données ROM 68K signalé par l'étape A.
- Ce sont des pointeurs d'animation 68K (`$1C(A6)`) qui tombent par hasard sur une clé de fonction.
- Aucune valeur `≥ $3C0000` : 0, contre 56 604 aujourd'hui.

**Appels de talons, en configuration complète** :

| | talons de données | talons de code | total |
|---|---|---|---|
| aujourd'hui | 5 892 434 | 1 139 518 | 7 031 952 |
| `RELOGE_CODE=1` (attraction + tournée seulement) | 4 511 099 (aujourd'hui sur ces 2 parcours : 5 364 143) | 5 311 (1 027 912) | **−29 %** |
| **trois à 1** | 3 972 332 | 5 325 | 3 977 657 (**−43 %**) |

Valeurs « RAM PS2 » vues par le talon de données : 935 405 → 6 554.

### 5.4 Upper (ro5), trois à 1

- diag 20 000 images : aucune exception.
- Parties sur le fork (`nonreg_ro5_B.sh`) :
  - Chun-Li 04 : 25 manches, `FIN fin=finie` ;
  - Ryu 00 : 28 manches, `FIN fin=finie` ;
  - Akuma 02 : 34 manches, `FIN fin=finie`.
  - Même ROM avec les interrupteurs à 0 : 23 / 28 / 33 manches, `fin=finie`.
- Journal de contrôle (tournée de Ryu, 40 000 images, fork) : les 24 sites contrôlés ne voient que du 68K (code 728 k, RAM 648 k). Talon de code : 13 valeurs PS2, au noyau.
- Balayage des 40 fins : **40/40 `fin=finie`**, première fin de même durée qu'avec les interrupteurs à 0 (§5.6).

### 5.5 Hyper (ro9), trois à 1

- Partie VERSUS (`hyper_vs_B.sh`, comme `valide_tout.sh`) : sélection image 408, manches images 1 035 et 1 658, `FIN 20000`. **Identique** à la même ROM avec les interrupteurs à 0.
- Journal de contrôle : 20 sauts et 7 lectures RAM, uniquement des valeurs 68K. Talon de code : 11 valeurs PS2, au noyau.

### 5.6 Balayage des fins d'Upper

**40/40 `fin=finie`** (`balayages/ro5_mame_ro5_1c_*`, 90 000 images par perso, 180 000 pour 07).

Sur 11 persos, le nombre de captures diffère du balayage partagé du 10/10 (exemple : 0a, 47 → 23).
- Le balayage de **ma ROM avec les interrupteurs à 0** sur ces 11 persos reproduit exactement le balayage partagé. L'écart vient donc bien de la nouvelle version.
- Ce n'est pas une fin différente. **La première fin a la même durée à une image près pour les 11** :
  - 0a : 3 474 / 3 473 images ;
  - 12 : 9 946 / 9 946 ;
  - 21 : 8 852 / 8 852 ;
  - etc.
- Ce qui change, c'est le moment où elle arrive (exemple : image 40 033 contre 42 990). Les combats ne durent pas le même nombre d'images, car le hasard dépend du temps processeur.
- Selon ce moment, une deuxième partie a le temps, ou non, d'atteindre sa fin avant l'image 90 000. Dans Upper, les captures additionnent toutes les fins vues.

Cadence d'Upper (tournée de Ryu, images 4 000 à 14 000, `scripts/fork_cad.sh`) :
- vitesse normale, 103 % de tours par image ;
- listes par image : 0,984 → 0,991 ;
- images sans tour : 80 → 76 ;
- pas de fenêtre turbo à franchir sur ce parcours.

## 6. Gain mesuré

Test des commandes, même partie (42/42), 3 750 images de combat, 5 000 tours. `runs/prof_adapt_B.lua` (copie de `_prof_adapt.lua` qui compte en plus les tours) et `outils/prof_an.py`.

| mots d'opcodes lus par tour | aujourd'hui | `RELOGE_CODE=1` | trois à 1 |
|---|---|---|---|
| talon de code `$3FF000` + carte | 696 | 0 | 0 |
| talon de données `$400` | 1 571 | 1 539 | 1 198 |
| `JSR` vers les talons | 143 | 122 | 110 |
| **total des conversions** | **2 410** | 1 661 | **1 308 (−46 %)** |
| listes d'objets rendues par image | 0,667 | 0,800 | **0,955** |

**Lecture.**
- Le travail total par tour ne baisse pas, il monte même un peu (17 823 → 18 364 mots). Le temps libéré sert à **rendre les images que la traduction sautait** (+43 % de listes, dont la construction pèse ~36 % du travail).
- Côté temps, la fin de liste des itérations à deux tours avance de ~140 lignes, de la ligne 394 à la ligne 251. Les itérations à un tour finissent vers la ligne 170 (arcade : 148).
- Pour la petite console :
  - le jeu dispose de la même marge que l'arcade et ne répète plus d'image en turbo ;
  - la charge de l'hôte ne change pas (rappel ARCHI §5 : le 68000 émulé tourne à cadence fixe).

Profils bruts : `journaux/profC_r0.txt`, `profC_r1.txt`, `profC_r1c.txt`. Tournée de Ryu : `profB_*`.

## 7. Fichiers

**Diff contre `src/hsfa` (copie de travail scripts/untranspile)**, patchable fichier par fichier (`cd src/hsfa ; patch -p3 < …`) : `diff/assemble.py.diff`, `diff/mame_test.py.diff`, `diff/diag.py.diff`.
- `diag.py` : nvram/cfg temporaires dans le dossier de travail, selon la règle MAME. Ce changement n'a pas d'interrupteur, car il est sans effet sur les ROM.
- `untranspile/` : la copie modifiée. `untranspile.orig/` : la copie figée de référence (11/10, 12 h 15).

**Scripts** (`scripts/`) :

| script | rôle |
|---|---|
| `construit.sh <ro3\|ro5\|ro9> <dossier> [VAR=…]` | reconstruction d'une variante |
| `nonreg_B.sh <dossier>` | 3 diag + commandes (SFA3) |
| `balayage_B.sh <dossier>` | 32 fins SFA3 |
| `nonreg_ro5_B.sh`, `balayage_ro5_B.sh` | Upper, sur le fork |
| `hyper_vs_B.sh` | partie VERSUS d'Hyper |
| `fork_j.sh ro5\|ro9` | partie journalisée sur le fork |
| `fork_cad.sh` | cadence d'Upper sur le fork (`runs/tour_cad.lua`) |
| `lance.sh NOM DOSSIER|ref SCRIPT.lua` | MAME standard, nvram/cfg propres, nice 19 |

**Lua** (`runs/`) :
- `cadence.lua` (+ `cmd_cad.lua`) : lignes des tours, fins de liste, IRQ2 ;
- `prof_adapt_B.lua` (+ `prof_tour_B.lua`, `prof_cmd_B.lua`) ;
- `attr_j.lua`, `tournee_j.lua`, `commandes_j.lua`, `hyper_vs_j.lua` : journal de l'étape A ;
- `tcb.lua` : diagnostic de la table des tâches.

**Outils** (`outils/`) :
- `bilan_journal.py` : bilan d'un journal des talons pour un dossier de construction ;
- `cadence.py` ;
- `prof_an.py` : copie, avec le travail par tour ;
- `image.py`, `explore_tables.py`, `journal_conv.lua` (copie de l'étape A).

**Dossiers de construction** :

| dossier | module | `RELOGE_CODE` | `RELOGE_NATIF` | `RELOGE_RAM` |
|---|---|---|---|---|
| `mame/` | SFA3 | 0 | 0 | 0 |
| `mame1/` | SFA3 | 1 | 0 | 0 |
| `mame1n/` | SFA3 | 1 | 1 | 0 |
| **`mame1c/`** | SFA3 | 1 | 1 | 1 |
| `mame2/` | SFA3 | 2 (contrôle) | 0 | 0 |
| `mame2c/` | SFA3 | 2 (contrôle) | 1 | 1 |
| `mame_ro5[_1c\|_2c]/` | Upper | 0 / 1 / 2 | idem | idem |
| `mame_ro9[_1c\|_2c]/` | Hyper | 0 / 1 / 2 | idem | idem |

Le suffixe `_1c` (ou `1c`) désigne la configuration recommandée, le suffixe `_2c` (ou `2c`) le contrôle.

**Résultats** : `resultats/` (listes relogées, relevés de cadence), `journaux/`, `balayages/`, `logs/`.

## 8. Limites et suite

- **Site RAM `$40(A6)`** (SFA3 et Upper). La valeur vient de `T_5899a4`, maintenant relogée, mais il faudrait une preuve sur tous les écrivains de `$40` pour ce type d'objet. On l'a laissé : 0 appel par image de combat.
- **Noyau.** `CREER` convertit encore l'entrée des tâches (constantes `CODE_x`, 20 sites) : 68 appels sur tout le parcours. Le hachage `$3C0000` reste donc construit, sans coût mesurable.
- **Disposition.** Avec `RELOGE_RAM=1`, les données démarrent en `$93000` (code plus court). Tout outil qui coderait en dur une adresse de données ROM SFA3 doit la relire dans `carte_image.txt`. Aucun outil du banc ne le fait pour les tables touchées.
- **Lecteurs inconnus.** Le relogement suppose que les cases d'une table ne sont lues que par le code qui la cite.
  - Ce qui est vérifié : référence par nom, `[PS2]` et adresse 68K ; étendue bornée par les références du code ; valeurs toutes des débuts de fonction.
  - Ce qui ne l'est pas : un accès calculé depuis une autre table.
  - Les balayages et journaux n'en montrent aucun.
- **Cadence (§4).** Tant que l'étape D n'a pas donné plus de marge, garder les trois interrupteurs ensemble, et contrôler toute nouvelle accélération par le test des commandes et `cadence.py`.
- **Suite naturelle** : étape C (5 926 cases de pointeurs de données) puis D. La même mécanique s'applique : étendue par la structure, valeur que rendrait le talon, retrait aux sites dont toutes les définitions sont relogées, mode contrôle pour le journal.
