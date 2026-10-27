# Greffe du mode Arcade d'Upper dans Hyper (voie B) — étape 3 : combat d'Hyper, partie complète, données, visuels

Agent « greffe_arcade », 2026-10-11 puis 2026-10-17 (reprise après une interruption). Suite de `GREFFE-ETAPE2.md`.

**Périmètre.**
- Écritures seulement dans `work/greffe_arcade/`.
- Le traducteur partagé, `work/mame*` et le fork n'ont pas été modifiés ; `max/` n'a pas été lu.
- MAME toujours lancé en `nice -n 19`, avec nvram et cfg propres à chaque trace, sans `-state` ni `pkill`.
- Aucun commit.

**Conventions** : celles des étapes 1 et 2.
- `ro5` = Upper, `ro9` = Hyper.
- Adresses MIPS en **fichier**, données en **exécution**.
- `$102` (PS2) = `$0103` (68K) = id étendu. `$116` (PS2) = `$0117` (68K) = perso de base.

---

## 0. En bref

1. **Plantage au K.O. du 3ᵉ combat : réglé, par la règle « combat = Hyper ».**
   - La cause n'était pas le K.O. lui-même. La sous-table de combat d'Upper était copiée en entier, et sa suite
     `0x2654B0` faisait tourner **à chaque image de combat** le moteur d'objets d'Upper `0x16CA80` (avec sa table des
     types) et le moteur de décor d'Upper sur les objets d'Hyper. L'objet fils de J2 recevait ainsi des données d'Upper.
   - S'ajoutaient de faux pointeurs relogés dans les données copiées : la table `T_6139A4` est faite de paires de mots
     signés (`$FF25,$0083`), pas de pointeurs.
2. **Partie complète atteinte, comme Upper** (§3) :
   - Ryu ZERO 3 : 10 adversaires, dans le **même ordre** que l'oracle Upper ; boss, **FIN** (scène A), **GAME OVER**,
     sortie, titre, puis nouvelle partie.
   - Défaite : écran **CONTINUE** de 2 540 images (comme Upper) ; continue accepté (retour à la sélection, 6 fois de
     suite) ou refusé (GAME OVER).
   - Versions d'Hyper : **Ryu ALPHA** (`$60`) et **Chun-Li ZERO 2** (`$44`) jouent la partie entière jusqu'à la fin et
     au GAME OVER. **Ken ZERO** (`$31`) et **Sakura ZERO 3** font 10 combats et le boss, puis **plantent pendant la fin**
     (§7, à reprendre).
3. **Données (§5).**
   - Les pointeurs sont **prouvés** par le journal des conversions d'Upper : 44 parties, les 40 persos, défaites et
     continue compris, soit **30 580 cases prouvées**.
   - Les faux pointeurs sont filtrés : longs impairs, paires de mots signés.
   - Les tables de pointeurs et les tables de décalages 16 bits (citations) sont suivies en entier.
   - Une contrainte nouvelle est mesurée : côté 68K, le bloc doit finir **avant `$F00000`** (RAM du portage du fork).
     Le risque restant est chiffré au §5.4.
4. **Visuels (§6).**
   - Corrects : écran VS (portraits et noms, adversaire à jour), couleurs des portraits, citation de victoire, palettes de
     la fin.
   - Infrastructure en place : bascule des **bases de plans du fork** (`$804200`). Les plans d'Upper sont chargés en
     `$4000000` et utilisés pendant les écrans de la couche Arcade.
   - Restent faux : le fond de la présentation et de la carte (le planisphère d'Upper n'est jamais dessiné dans Hyper),
     les plans des images de la fin, et le fond des écrans CONTINUE et GAME OVER.
5. **VERSUS d'Hyper.**
   - Mêmes 21 sélections, 40 manches et états, aucune exception.
   - Seul écart : la pose de victoire de 3 manches dure **une image de plus ou de moins**, le même écart qu'à l'étape 2.
     Le démarrage est identique à la référence.
6. **Traducteur.**
   - Le diff cumulatif `diffs/03-greffe-traducteur-actuel.patch` s'applique au traducteur partagé actuel.
   - Il a été fusionné avec FLUXEA, l'étape B (`RELOGE_*` à 1) et `OPTION_RETOUR` / `EXIT_RETOUR`.
   - Sans les variables de la greffe, il redonne la ROM de référence **`964943b1…`** (avec ou sans `LEATAB_AJOUTE`), et
     la carte et les blocs ext sont identiques. Le témoin d'Upper redonne `1908ec9e…` (`u5_temoin6`, carte et ext identiques).

---

## 1. Constructions et références

| objet | md5 / état |
|---|---|
| traducteur partagé (`src/hsfa`) | inchangé depuis le 2026-10-11 14:45. Copie figée : `fusion/actuel/` |
| ROM Hyper de référence (traducteur actuel, son et voix) | `964943b1390e435142126b561df2ff0f` (`constructions/ref9_actuel`, = `work/mame_ro9`) |
| ROM Upper de référence | `1908ec9edb6ad844835c4d022362c01c` (`constructions/ref5_actuel`) |
| témoins de la copie fusionnée `untranspile3/`, sans greffe | `temoin4`, `temoin5`, `temoin6` (finale) et `temoin5_lea0` (`LEATAB_AJOUTE=0`) : **`964943b1…`**, carte et ext identiques. `u5_temoin4` : `1908ec9e…` |
| constructions figées des traces (oracle) | `fige/ro5` `a296538f…`, `fige/ro9` `a37df09c…` : intactes (vérifiées le 2026-10-17) |
| **Hyper augmenté, étape 3 (figé)** | **`constructions/ro9a3_fige`** : `sz3ud.03c` `217fc51c03d1c0a581d95a1c00029700`, `sz3ud.04c` `e9cea74e…` ; module, bloc, ext et carte dans `ro9a3_fige/md5.txt` |

La construction `ro9a3_fige` comporte :
- **1 937 routines greffées**, soit 694 Ko de MIPS : zone Z80 `[0x17D0, 0x22B00)` (136 Ko) et 2ᵉ zone `[0xE10000, 0xE99870)` (558 Ko) ;
- 1 228 routines renvoyées à Hyper, 8 natives et **11 routines synthétiques** ;
- un bloc de données de **1 897 512 o** ;
- 109 lectures de `$102` passées à `$116` et 25 patchs de points d'entrée et de code.

---

## 2. Combat = Hyper (mission 1)

### 2.1 Diagnostic

| image | constat | cause |
|---|---|---|
| combats 1 à 3 (étape 2) | décor « cassé » (cascade magenta), objets du combat traités par le code d'Upper | sous-table `T_61C2A0` d'Upper copiée ; **`0x265440` → `0x2654B0` à chaque image** : moteur d'objets `0x16CA80` (table des types d'Upper), décor `0x151B80`, `0x13D820`… |
| K.O. du 3ᵉ combat | objet fils de J2 → `0x840688` (milieu des frames de Sakura) | tables copiées `0x6139A4/0x613BA0` : paires de mots signés relogées comme pointeurs ; réglé au §5 |

### 2.2 Ce qui est fait (`etape3/force3.py`, `etape3/greffe3.py`)

| point | Upper | devient |
|---|---|---|
| sous-états 1 à 6 du combat (`A5+C` = 2…C), K.O. compris | `0x266280`, `0x2679D0`, `0x268AB0`, `0x26BD50`, `0x26CB60`, `0x26DFB0` | **Hyper** `0x9B350`, `0x9B7E0`, `0x9C940`, `0x9E920`, `0x9F300`, `0x9FD10` (l'état 0 `0x9A980` l'était déjà) |
| suite de chaque image de combat | `0x2654B0` | **Hyper `0x9A6F0`** |
| état 7, fin de match (`A5+C = E`) : enchaînement Arcade | `0x26E900` | talon **`etat7`** : il appelle d'abord les suites Arcade du K.O. d'Upper (`0x26B7C0` dernier combat et fin, `0x26B0B0` joueur battu, `0x272EB0`), puis, si `$0104`, `$014B` ou `$015C` est posé (match décidé), `0x26E900` d'Upper (prochain adversaire `0x250EF0`, fin `0x2712E0`), sinon (match nul) `0x9FDB0` d'Hyper |
| K.O. d'Hyper `0x9C940` | appel de `0x9D240` (comptage des victoires) | talon **`ko_compte`** : en Arcade, `0x269340` d'Upper (victoires, masque des battus, dernier combat, chargeur de fin), sinon `0x9D240` |
| init de match `0x2615D0` → `0x272D80` (ids des joueurs par `T_61C160`, 40 entrées) | id `$31` → 0 (Ryu) | talon **`remap_ids`** : `$13` → `$11` seulement. Pour les adversaires CPU, `$117 = $103` et `$116 = $10`, posés **dès l'init** : les écrans Arcade lisent le perso de base avant que l'init du joueur d'Hyper ne le calcule |
| écran VS (4/4) | `0x2651C0`, `0x265310` d'Upper | restent ceux d'Upper (portraits et noms). Leur **préparation du décor passe par Hyper**, par appelant : `0x4B270`/`0x60A20`, `0x151B80`/`0x30EC10`, `0x4C1B0`/`0xAC050` |
| entrée dans le combat | — | talon **`vs_decor`** : décor borné aux décors d'Hyper (`CMPI.W #8,$100` → 4 : rival et Bison en `$14`) ; en-têtes des 7 emplacements d'objets `$5000-$5C00` remis à zéro (sinon l'emplacement `$5C00`, que le combat d'Hyper réutilise, gardait le type 1 d'un texte d'Upper) |

**Défaut du traducteur contourné.**
- Le premier test de `0x269340` (`CMPI.W #6,$0138(A5)`) est calculé par des temporaires de pile et **perdu à la
  traduction** : le `BEQ` lisait les drapeaux de l'appelant. Upper ne passe que par chance.
- La copie greffée reçoit à la place la forme standard du même test, prise dans `0x26E900` (`CMP138=1`).
- Le même défaut peut toucher d'autres fonctions à prologue `sq`. **Il est à signaler au traducteur.**

---

## 3. Partie complète (mission 2)

### 3.1 Corrections nécessaires, dans l'ordre où elles ont été trouvées

| symptôme | cause | correction |
|---|---|---|
| pas d'adversaire suivant | `0x269340` prenait la branche du combat à 3 (test perdu, §2.2) | forme standard du test |
| plantage à l'étape 8 (rival, décor `$14`) | table à 4 entrées du décor d'Hyper | talon `vs_decor` |
| fin : scène A quittée aussitôt | aiguilleur de la scène A `0x2A300` apparié au tri avec `0x5DA40` (aiguilleur d'objets d'Hyper) | **greffé** |
| fin : plantage, interpréteur d'animation | relais `0x137170` (tâche Arcade) → « homologue » `0x1DBFE0` (code de perso d'Hyper) | règle **`TRI_PETITES`** : une petite routine (< 256 o) renvoyée à Hyper par le tri doit être *équivalente* (13 routines passent à la greffe). Aussi greffés : `0x2FB40`, `0x10D030`, `0x17EEF0`, `0x1E3C70`, `0x1E5170`, `0x1EFF50` (aiguilleurs à tables, `etape3/tri_tables.py`) |
| défaite : blocage | `0x26B0B0` rend le joueur battu inactif (`$0101 = 0`) dès le K.O. ; les états 4-6 d'Hyper l'attendent | suites Arcade du K.O. appelées au début de l'état 7 |
| défaite : citation qui déborde sur l'objet `$5E00` | (a) emplacement `$5C00` resté de type 1 ; (b) texte du CPU hors des données copiées (citation de Blanka en `0x680D00` = base `0x67E2A0` + décalages) | (a) `vs_decor` ; (b) **tables de décalages 16 bits sur deux niveaux** (§5.2) |
| CONTINUE sauté (accepté sans Start) | relais `0x136D50` (tâche Arcade) → « homologue » `0x24A90` (règle j) : J1 passait au sous-état 4 | greffé |
| démo de démarrage d'Hyper passée par la scène 4 d'Upper | les aiguillages testaient `$C201` (curseur du menu), qui vaut 0 au démarrage | **drapeau « partie Arcade »** : octet `$FF00(A5)` = `$FF7F00` (zone libre), posé par `depart_arcade`, effacé à la sortie (scène C) |
| versions (`$31`, `$60`…) : Ryu à la place de Ken ; palette du portrait lue à `T[$60]` | lectures de `$102` dans le code greffé ; table `T_61C160` | **toutes les lectures de `$102`** du code greffé passent à `$116` (109 sites : INDEX, CMP, COPIE, AUTRE ; seules les ÉCRITURES gardent `$102`) ; talon de chargement par joueur sur `$117` (`mame_test.py`) |
| fin : écran noir | adresses des tampons de palettes « formées par décalage » (`MOVE.W #$A3C0,D1 ; LSL.L #8`) restées en page RAM d'Upper | 4 sites `addiu $A0xx-$A7xx` + `sll 8` → `+$1800` (`PAGES_RAM`) |
| fin de Sakura : saut hors du code | moteur d'objets `$5000-$5C00` (`0x1196E0`) renvoyé à Hyper `0x3A45F0` (table des types d'Hyper) | greffé |

### 3.2 Résultats (construction `ro9a3_fige` = `e4g` ; variante d'adversaires d'Upper imposée, `outils/oracle_ro9a.sh`)

| partie | trace | résultat |
|---|---|---|
| Ryu ZERO 3, victoires | `e4g_ryu` (34 000 im.) | 10 adversaires `19 0C 0D 1B 09 1C 0B 1D 01 0A` = **oracle Upper `u_or`** ; FIN (scène A) 18 387 → 21 568 ; GAME OVER 21 568 → 21 676 ; sortie, titre, nouvelle partie |
| Ryu ZERO 3, défaites, continue | `e4g_perdu` (20 000 im.) | 6 × (pose du CPU → CONTINUE 2 540 im. → Start → sélection → combat) |
| Ryu ZERO 3, défaite, sans continue | `e4g_go` | CONTINUE 3 166 → 5 714 (compte complet) → **GAME OVER** → sortie (5 927) → titre → nouvelle partie |
| **Ryu ALPHA** (`$60`) | `e4g_ryuA` | 10 adversaires, FIN 17 167, GAME OVER 20 349, sortie, nouvelle partie (37 manches) |
| **Chun-Li ZERO 2** (`$44`) | `e4g_chunZ2` | 10 adversaires (`02 1A 09 0B 08 0E 1C 18 16 0A`), FIN 19 932, GAME OVER 24 543, sortie |
| **Ken ZERO** (`$31`) | `e4g_kenZ` | 10 adversaires, boss, FIN 15 657, puis **plantage à 22 028** (§7) |
| Sakura ZERO 3 | `e4g_sakZ3` | 10 adversaires, FIN 19 102, puis **plantage à 22 255** (§7) |
| VERSUS d'Hyper (non-régression) | `e4g_vs` contre `ref9_vs` | 21 sélections, 40 manches, mêmes états, aucune exception ; démarrage identique ; 3 poses de victoire décalées d'une image |

Durées comparées à Upper (oracle `u_or`, Ryu) :
- scène A : **3 181 images** contre 11 774 ;
- GAME OVER : 108 contre 134 ;
- CONTINUE : 2 548 contre 2 540.

La fin est donc écourtée : elle suit l'affichage, encore faux (§6).

Le script de partie (`lua/tournee_arcade.lua`) appuie sur des boutons hors combat. Il écourte donc la pose de victoire
(Upper : 365 images avec citation), ce qui n'est **pas** un défaut de la greffe. `SCENEA_PASSIF=1` ne touche à rien
pendant la fin ; `NOCONT=1` ignore le continue.

Captures :
- **`traces/planche_etape3_entre_combats.png`** : présentation, VS Ryu-Blanka, combat, pose de victoire avec citation,
  carte, VS Ryu-Dan ;
- `traces/planche_etape3_continue_gameover.png` ;
- `traces/planche_etape3_fin.png` ;
- références Upper : `traces/planche_u_vues.png`, `planche_u_fin.png`, `planche_fin.png`.

---

## 4. Décisions du plan : règles ajoutées

1. **Combat = Hyper** (§2), interrupteur `COMBAT_HYPER=1`.
2. **`TRI_PETITES`** : une petite routine renvoyée à Hyper par le tri (règle d) doit être équivalente.
   - L'étendre aux relais « non vus en Arcade » (règle j) ferait passer le plan de 1 850 à 2 535 routines. Ces cas sont
     donc traités un par un (`0x136D50`).
3. **Aiguilleurs à table** (`etape3/tri_tables.py`, `etape3/audit_aiguilleurs.py`) : une routine renvoyée à Hyper dont
   la table de pointeurs de code ne correspond pas à celle de l'homologue doit être greffée.
4. **Moteur de plans d'Upper** (`0x14E000-0x160000`, `MOTEUR_PLANS_UPPER=1`).
   - La règle « équivalente » ne compare que les 64 premiers octets des tables. Le chargeur s2 `0x1515C0` lisait ainsi les
     listes d'Hyper (codes + `$1000` au lieu de + `$1C00`).
   - Ces routines ne sont appelées que par du code greffé. Elles passent toutes à la greffe (26 routines).
5. **Par appelant** (`PAR_APPELANT_HYPER`) : une même routine d'Upper va à Hyper pour certains appelants (préparation du
   décor depuis l'écran VS) et à sa copie pour les autres.
6. **Affichage des objets** : celui d'Hyper (`0x392270`) partout.
   - L'essai avec celui d'Upper (`AFFICHAGE_UPPER=1`) rend les portraits invisibles.

---

## 5. Données (mission 3)

### 5.1 Preuve dynamique des pointeurs

- `lua/journal_conv_u.lua` est une copie de `agent_reorg_A/outils/journal_conv.lua`, avec en plus une prise sur le bloc
  `$C80000`. Il relève chaque appel des talons de conversion de données (`CONV_An`) et la case ROM d'où vient la valeur.
- `lua/donnees_conv.lua` le combine avec `tournee_greffe.lua`.
- Parties journalisées (`outils/journaux_conv.sh`) :
  - les 40 persos d'Upper, chacun sur une partie entière avec la fin (`traces/uc2_XX`, `uc_00`, `uc_0d`) ;
  - 3 parties perdues avec continue et GAME OVER (`ucp_00`, `ucp_0d`, `ucg_04`).
- `etape3/preuve_ptrs.py` en tire **30 580 cases prouvées** (`donnees/pointeurs_prouves.txt`), sans aucune incohérence
  entre la valeur journalisée et le module.

### 5.2 Nouvelles règles de copie et de relogement (`etape2/donnees2.py`, interrupteurs ; sans eux : comportement de l'étape 2)

| interrupteur (défaut de `greffe3.py`) | règle |
|---|---|
| `PREUVES` (= `pointeurs_prouves.txt`) | une case prouvée est un pointeur. Sa cible est suivie même si Upper ne l'a jamais lue |
| `FILTRE3=1` | un long non prouvé et hors des constantes du code n'est pas un pointeur s'il est **impair** ou si sa moitié basse vaut `$FE00-$FFFF` (paire de mots signés : `T_6139A4`) |
| `OU3=1` | pour reloger, la région **copiée** qui contient la cible est cherchée d'abord, puis la plage réutilisée chez Hyper. Avant : les plages réutilisées, plus denses, masquaient la région ; 1 146 pointeurs prouvés n'étaient pas relogés, dont `T_60B560[6] = 0x70E560` |
| `TABLES_PTR=1` | un segment fait à 75 % au moins de pointeurs (4 longs au minimum) est une table : toutes ses cibles sont suivies |
| `DECALAGES16=1`, `PLAFOND_DEC=$D200` | un segment qui commence par une **table de décalages 16 bits** est copié jusqu'au plus grand décalage. La table compte au moins 8 mots ; son 1ᵉʳ mot vaut sa taille (40 persos : `$50`). Le 2ᵉ niveau est suivi (citations : `0x67E2A0` → perso → 8 textes) |
| `ECART_REGION=$200` | écart maximal entre deux segments fusionnés en une région (avant : `$400`). Il économise 130 Ko |
| `SEG_REFS=0` | copie de chaque base visée par le code jusqu'à la constante suivante : essayée, mais trop grande pour le 68K (§5.3) |

### 5.3 Place

- **Côté 68K**, le bloc externe propre `$D10000` doit finir **avant `$F00000`**, où commence la RAM du portage du fork.
  Cela laisse 2 031 616 o.
- Un bloc de 2,29 Mo l'a recouverte : le démarrage d'Hyper en était modifié et le VERSUS décalé.
- `greffe3.py` le vérifie maintenant par une assertion.
- Côté PS2, il reste 2,36 Mo.
- Bloc actuel : **1 897 512 o**, soit 130 Ko de marge.
- Pour aller plus loin, il faudra une 2ᵉ fenêtre 68K, par exemple `$C30000-$C83FFF` (≈ 344 Ko libres derrière
  `ext_940000`), avec un `GRF_Y` en deux morceaux dans le traducteur.

### 5.4 Risque restant (`ro9a3_fige`)

| catégorie | nombre | lecture |
|---|---|---|
| longs relogés **prouvés** | 16 132 | sûrs |
| longs relogés non prouvés | 14 486 | candidats : pair, moitié haute `$60-$B0`, moitié basse `≥ $200`. Sur l'ensemble des 30 618 longs relogés, 9 608 visent une donnée qu'Upper lit hors des manches (`etape3/audit_ptrs.py`). Pour les autres, un faux positif fausse une coordonnée ou un mot ; un vrai pointeur non prouvé est simplement hors couverture |
| longs laissés **non prouvés** | 8 093 | ne ressemblent pas à des pointeurs ou visent des données jamais copiées |
| longs laissés **prouvés** | **1 130** | cible non copiée : surtout des **données de combat** (frames des persos, par ex. Sakura `0x839550` ; positions du fichier 390), atteintes par des régions prolongées jusqu'aux lectures voisines. Le code greffé ne s'en sert pas puisque le combat est celui d'Hyper. Aucun n'a fait planter les parties du §3 |
| cases prouvées hors des régions copiées | 13 318 | données de combat d'Upper (non nécessaires) |

Limites :
- La preuve ne vaut que pour les cases lues **directement** avant un talon de conversion. Une copie dans la RAM (cases
  RAM du journal) n'est pas reliée à sa case ROM.
- Les parties journalisées couvrent les 40 persos d'Upper en victoire, et quelques défaites.
- Non couvert : les citations de défaite contre **chaque** adversaire, que les tables de décalages couvrent statiquement ;
  les combats contre un 2ᵉ joueur (« new challenger ») ; les combats spéciaux (`$C39F`, Shin Akuma…).

---

## 6. Visuels de la couche Arcade (mission 4)

| écran | état |
|---|---|
| **écran VS** | correct : portraits et noms (Ryu - Blanka, puis Ryu - Dan), adversaire à jour. Défaut de l'étape 2 : `$116/$117` de l'adversaire, lus avant l'init d'Hyper |
| **palettes des portraits** | correctes, couleurs d'Upper (Blanka jaune et bleu comme dans Upper). Le défaut de l'étape 2 venait de l'id du perso (§3.1) |
| **pose de victoire et citation** | correcte (« Sometimes the most important battle is the battle within… ») ; décor d'Hyper derrière |
| présentation, carte, NEXT STAGE | widgets d'Upper visibles (colonne des adversaires, bandeau du nom). **Fond faux** (voir ci-dessous) |
| CONTINUE, GAME OVER | chiffres et lettres visibles, fond faux (plans d'Upper absents de la VRAM) |
| fin | palettes correctes depuis `PAGES_RAM`. Les plans sont incomplets : le texte est en scroll1 dans `$900000` au lieu de `$910000`, les codes s3 sont différents, `$91C000` est vide. **La fin est écourtée** (3 181 images contre 11 774) |

**Bases de plans du fork** (registre `$804200-$804205`, lu et écrit par le 68K, `cps2.cpp`) :
- `lance_ro9a.sh` charge les **plans d'Upper** (`mame_ro5/hsfa_plans.bin`) en `$4000000`, en plus de ceux d'Hyper en
  `$3000000`. Bases d'Upper : `400,440,4A0`.
- La copie du traducteur mappe l'adresse PS2 « RAM + `$7FF00..$7FF04` » (libre dans ro5 et ro9) sur ce registre
  (`HSFA_GREFFE_PLANS=1`).
- Talons `plans_auto` : à chaque image de la scène 4 en Arcade, plans d'Upper pour l'init, la présentation, la carte, le
  face-à-face et le VS ; plans d'Hyper à l'entrée dans le décor, en combat et pendant la pose de victoire.
- Talons `plans_s6`, `plans_s8`, `plans_sA` : plans d'Upper pendant CONTINUE, GAME OVER et la fin ; retour aux plans
  d'Hyper en quittant vers la sélection (0) ou la sortie (C).
- Les scènes 0 et C d'Hyper ne reçoivent aucun talon : le VERSUS garde son minutage.
- Contrôle : Upper avec ses plans en `$4000000` et ses bases `400,440,4A0` s'affiche normalement
  (`traces/u_plans4`).
- **FBNeo** : le cœur devra accepter les écritures du 68K dans ce registre et charger les deux fichiers de plans. Il les
  écrit aujourd'hui une seule fois, à la 1ʳᵉ image.

**Ce qui manque pour les fonds** (VRAM comparée à Upper, `lua/vram.lua`, `lua/vram2.lua`) :
- Le planisphère de la présentation et de la carte est un tilemap en `$914000-$91FFFF`. Upper le dessine pendant **son**
  attraction et **sa** sélection : `0x5EFB0` vers les images 1 300-1 920, et les chargeurs s2/s3 `0x1515C0`/`0x151A00`
  vers 1 976-1 985. Hyper n'exécute ni l'une ni l'autre ; la présentation se contente de basculer les bases sur un
  tampon vide.
- Il faut appeler ces dessins depuis la greffe à l'init du mode Arcade, une fois le décor de la sélection d'Upper
  identifié. C'est le prochain chantier visuel.
- Fin : comparer les registres de bases CPS-A (`$804102-$804106`, non relisibles ; à tracer par écriture) et les
  tampons `$8008/$800C(A5)` (tables `T_60B5A0`, `T_60B700`).

Les **décors de combat** d'Upper (`decors/DECORS.md`) n'ont pas été abordés : le combat reste sur les décors d'Hyper.

---

## 7. Ce qui bloque / reste à faire

1. **Fin de Ken ZERO** (plantage à l'image 22 028).
   - Une commande de script de fin (`0x319D0`) crée un acteur en `$809E(A5)` : `MOVE.B D0,(A4)` pose `$FF009F = 1`.
   - `0x2C920` lit ensuite **`MOVE.W $0001(A4)`**, un mot à adresse impaire, d'où l'erreur d'adresse.
   - Upper passe le même code sans planter. Il faut comparer les deux parties de cette fin (même perso, script de
     `$87F1`) : soit une forme de traduction propre au mot, soit une autre branche.
2. **Fin de Sakura** (plantage à l'image 22 255), dans le moteur de fin `0x2E2B0`. `A4` est un pointeur faux lu dans les
   tables de la fin : données à vérifier comme au §3.1 (`ptr_anim.py`, `preuve_ptrs.py`).
3. **Visuels** (§6) : fond de la présentation et de la carte (dessins de l'attraction et de la sélection d'Upper), plans
   de la fin, CONTINUE et GAME OVER. Ensuite seulement : les décors de combat d'Upper.
4. **Traducteur partagé** : le test perdu en tête des fonctions à prologue `sq` (§2.2) et les adresses « formées par
   décalage » des tampons vidéo (§3.1). Ce sont des défauts généraux, contournés dans la greffe.
5. **VERSUS** : un décalage d'une image sur 3 poses de victoire, déjà vu à l'étape 2. La cause probable est le cycle de
   plus pris par les talons du K.O. ; non mesurée.
6. **Place 68K** : 130 Ko de marge. Au-delà, il faut une 2ᵉ fenêtre du bloc (§5.3).

---

## 8. Diffs (`diffs/`)

- **`03-greffe-traducteur-actuel.patch`** (399 lignes) : toute la copie du traducteur (préparation, étapes 2 et 3)
  contre le traducteur partagé **actuel**.
  - Fusion à 3 voies. La base est l'état du 2026-10-10, reconstitué en défaisant le patch 02 sur la copie.
  - Un seul conflit, dans `assemble.py` (étape B / `extra=`), résolu à la main.
  - Vérifié : il s'applique sans reste à une copie de `src/hsfa`, et le résultat est identique à
    `untranspile3/`.
  - Fichiers : `mips.py`, `translate.py`, `assemble.py`, `mame_test.py`, `extra_regs.py`, `profils.py`,
    `assets_natifs.py`.
  - Ajouts de l'étape 3, tous inactifs sans les variables `HSFA_GREFFE_*` :
    - registre des bases de plans (`HSFA_GREFFE_PLANS`) ;
    - talon de chargement par joueur sur le perso de base `+$117`.
- `01-leatab-ajoute.patch` (étape 2) est inclus dans le 03.
- **Interrupteurs à 0** : sans `GREFFE_C0`, `GREFFE_Z2` ni `HSFA_GREFFE_*`, la ROM est **`964943b1…`**, et la carte et
  les blocs ext sont identiques (`constructions/temoin6`). C'est vrai aussi avec `LEATAB_AJOUTE=0`.

## 9. Outils de l'étape 3

| outil | rôle |
|---|---|
| `etape3/greffe3.py` | construction (copie de `greffe2.py`) : combat = Hyper, 11 talons (`scene4_mode`, `depart_arcade`, `fin_selection`, `ko_compte`, `etat7`, `vs_decor`, `remap_ids`, `plans_auto`, `plans_s6/8/A`), patchs (`CMP138`, `PAGES_RAM`, `$102` → `$116`), règles du plan (`TRI_PETITES`, `MOTEUR_PLANS_UPPER`, par appelant), données (§5.2), assertion de place 68K. `PLAN_SEUL=1`, `BLOC_SEUL=1` |
| `etape3/force3.py` | décisions imposées de l'étape 3 |
| `etape3/relogement_a5_v3.py` | table A5 recalculée pour l'ensemble greffé (`donnees/relogement_a5_v3.pkl`) |
| `outils/construit_e3.sh NOM ["VARS"]` | plan → table A5 → module → traduction (`untranspile3/`) |
| `etape3/preuve_ptrs.py`, `audit_ptrs.py` | pointeurs prouvés (journal des conversions) ; classement des longs relogés |
| `etape3/audit_aiguilleurs.py`, `tri_tables.py`, `pourquoi.py` | aiguilleurs mal appariés ; chaîne des parents d'une routine greffée |
| `lua/journal_conv_u.lua`, `donnees_conv.lua`, `outils/journaux_conv.sh` | journaux des conversions d'Upper (par perso, en parallèle) |
| `lua/sonde.lua`, `surv.lua`, `vram.lua`, `vram2.lua` | registres à l'entrée d'une adresse ; écritures journalisées (PC, registres, pile) ; vidage de la VRAM et des sprites |
| `lua/tournee_arcade.lua` (ajouts) | `NOCONT`, `SCENEA_PASSIF`, `SNAPSC`, `JVARS`, `SURV_N` |
| `lua/tournee_greffe.lua` (ajout) | `SNAPS` |
| `outils/oracle_upper.sh` | partie oracle dans Upper (même variante d'adversaires) |
| `outils/lance_vs.sh` | avec `CONTOURNE_E=1` (écran RESULT) |
| `outils/lance_ro9a.sh` | avec les plans d'Upper en `$4000000` (`PLANS_UPPER=1`) |
| `fusion/` | base reconstituée, copie figée du traducteur actuel, essai d'application du patch |
| `untranspile3/` | copie fusionnée du traducteur (étape 3) |

## 10. Prochaines étapes

1. Fins de Ken ZERO et de Sakura (§7.1-2), puis les 40 fins et les 4 versions, en balayage, comme le balayage des fins
   d'Upper.
2. Fond de la présentation et de la carte : appeler les dessins du planisphère d'Upper à l'init de l'Arcade. Puis les
   plans de la fin, de CONTINUE et de GAME OVER.
3. Remonter au traducteur partagé les deux défauts du §7.4.
4. Rival, « new challenger » (J2 en cours d'Arcade), Shin Akuma et combats spéciaux : journaux des conversions sur ces
   parcours.
5. Décors de combat d'Upper (`decors/DECORS.md`), une fois la couche Arcade complète.
