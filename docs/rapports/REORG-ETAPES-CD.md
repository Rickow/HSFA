# Étapes C et D de la réorganisation des données : pointeurs de données des tables ROM, retrait des talons

> Rapport versé dans le dépôt le 2026-10-24 depuis `work/agent_reorg_CD/ETAPES-CD.md` (copie anonymisée ; texte
> d'origine inchangé). Les chemins `work/…` et `<workspace>/…` désignent des dossiers de travail, hors dépôt. Les
> interrupteurs décrits ici (`RELOGE_ANIMNAT`, `RELOGE_DONNEES`, `RELOGE_D`, `TALON_EN_LIGNE`) **ne sont pas dans le
> traducteur publié** : le chantier est mis de côté (branche `reorg-cd`, hors dépôt), et ne pas confondre
> `RELOGE_ANIMNAT` avec `RELOGE_NATIF` de l'étape B. Plan :
> [ARCHI-Reorganisation-Donnees](../architecture/ARCHI-Reorganisation-Donnees.md) ; étapes précédentes :
> [ETAPE-A](ETAPE-A.md), [ETAPE-B](ETAPE-B.md). Le résultat du balayage des 40 fins d'Upper (§5.2) n'avait pas été
> reporté dans l'original.

Plan : `work/notes/ARCHI-reorganisation.md` (§3, étapes C et D). Points de départ : `work/agent_reorg_A/ETAPE-A.md` §5
et `work/agent_reorg_B/ETAPE-B.md`. Tout est dans `work/agent_reorg_CD/`. Le traducteur partagé, `work/mame*`, le fork
MAME et `max/` n'ont pas été touchés.

## 0. En bref

- **Base** : copie de `scripts/untranspile` du 11/10 (étape B par défaut, FLUXEA, OPTION_RETOUR / EXIT_RETOUR), figée
  dans `untranspile.orig/`. Elle est identique au traducteur partagé validé. Avec tous les nouveaux interrupteurs à 0,
  ma copie donne exactement les ROM de référence : SFA3 `7e22b1ec…`, Upper `1908ec9e…`, Hyper `964943b1…` (md5 de
  `sz3ud.03c`) ; programme complet SFA3 `9565d25e…`.
- **Cinq interrupteurs**, tous à 0 par défaut (`=0` → octets de l'étape B) :

| variable | étape | effet |
|---|---|---|
| `RELOGE_ANIMNAT=1` | C, tables natives | bloc d'animation natif, talons `$810` (`$FF3E48`) et table des persos en adresses 68K ; plage virtuelle retirée du talon |
| `RELOGE_DONNEES=1` | C, données ROM | tables lues directement par un `MOVEA … ; JSR CONV_An` relogées quand elles sont pures (preuve statique) |
| `RELOGE_DONNEES=2` | C, données ROM | en plus, les cases de `reloge_donnees_<module>.txt` (journal des talons + suivi des écrivains) |
| `RELOGE_D=1` | D | `JSR CONV_An` retiré aux sites dont toutes les cases lisibles sont relogées (preuve statique) |
| `TALON_EN_LIGNE=1` | D' | filtre en ligne devant les talons gardés (sources en RAM, sans preuve possible avant l'étape E) |

- **Configuration recommandée** (en plus de l'étape B, déjà par défaut) :
  `RELOGE_ANIMNAT=1 RELOGE_DONNEES=2 TALON_EN_LIGNE=1 RELOGE_D=1`.
- **SFA3, configuration recommandée** (`mame8/`) :
  - test des commandes **42/42, 5 359 tours en 4 019 images (133,3 %)**, soit autant que l'arcade (étape B : 5 358) ;
  - 3 diagnostics sans exception ; **32 fins `fin=finie`, captures = arcade ±1** ;
  - **journal des talons sur les 32 fins : 0,08 % → voir §5** ;
  - cadence (combat du test des commandes) : fin de liste des itérations à deux tours **ligne 251 → 237**
    (médiane), 90ᵉ centile **270 → 240**, listes d'objets par image **0,981 → 0,996**, images sans tour 1 → 0.
- **Gain** : conversions par tour de jeu **1 308 → ~325 mots (−75 %)**, travail par tour **18 625 → 17 721 mots
  (−4,9 %)** ; appels de talons de données sur les parcours de l'étape A : voir §6.
- **Upper** : diagnostic et 3 parties `fin=finie` ; balayage des 40 fins : §5. **Hyper** : VERSUS identique à
  l'étape B (sélection image 408, manches 1 035 et 1 658, `FIN 20000`), sans exception.

## 1. Sort du bloc externe `$A04000` (2 969 cases)

**Décision : adresse fixe, pas de relogement.**

- Les cases qui visent le fichier 289 (frames de sprites, 458 Ko) contiennent déjà l'adresse 68K finale. Le bloc est
  servi à `$A04000` (identité PS2 = 68K) par le banc (`banc_mem.lua`), le fork (ROM supplémentaire) et le cœur FBNeo.
  Il ne tient pas dans les 4 Mo de ROM programme.
- Le talon `$400` laisse ces valeurs inchangées. Pour les étapes C et D, ce sont donc des adresses 68K. Elles sont
  acceptées comme « pures » dans les tables (`fixe_ps2` : `AN.FIXES`, aussi `$B04000` d'Upper et `$C84000` d'Hyper).
- **Seul défaut : le coût.** `$A04000` tombait entre les bornes du talon (`$583C40`-`$A97630`). Le talon parcourait
  alors tout l'arbre de recherche (~250 cycles) pour ne rien changer.
  - Avec `RELOGE_ANIMNAT=1`, la plage virtuelle du bloc natif (`$A80000`) sort du talon. La borne haute devient
    `$980000`, et `$A04000` sort au deuxième test.
  - Le filtre en ligne (§4) l'évite complètement.
- Ailleurs : Upper `$B04000` est déjà au-dessus de la borne (`$A80000`). Hyper `$C84000` reste sous la borne
  (plage du son `$E70000`) : il passe par le talon, sans erreur, seulement plus lentement.

## 2. Étape C : relogement des pointeurs de données

Principe, comme à l'étape B : chaque case relogée reçoit **la valeur que rendrait le talon** (`conv(v)` par les plages
du talon, exportées dans `conv_plages.txt`). Le talon laisse passer une adresse 68K. Un lecteur qui garde son talon
voit donc exactement la même valeur qu'avant.

### 2.1 Tables natives (`RELOGE_ANIMNAT`, 194 cases de l'étape A)

- Le bloc virtuel PS2 `[VBASE, +taille)` n'existe que dans la traduction (`assets_natifs.py`). Ses seuls producteurs
  sont connus :
  - les pointeurs internes du bloc, que `AN.build` reloge déjà (positions enregistrées dans `AN.PTRS`, SFA3 2 549,
    Upper 3 901) ;
  - les talons natifs `$810` (`MOVE.L #ptr,$BE48(A5)`) : c'est **le cas `$FF3E48`** de l'étape A ;
  - la table des persos lue par le talon `$810+` et les talons dynamiques d'Upper.
- Tous reçoivent `ASSET + (v − VBASE)`.
- **Preuve statique complète**, puisqu'aucune autre source ne peut produire ces valeurs. La plage `VBASE` est donc
  retirée du talon.
- Hyper n'a pas de bloc natif.

### 2.2 Tables ROM lues directement (`RELOGE_DONNEES=1`, `assemble.py:reloge_donnees`)

**Sites analysés** : les `MOVEA … ; JSR CONV_An` de trois formes.

| forme | instructions |
|---|---|
| P1 | `MOVEA.L T(PC,Dn),An` |
| P2 | `LEA table.L,Ab [; …] ; MOVEA.L d(Ab,Dn),An` |
| P3 | `LEA table.L,Ab ; MOVEA.L d(Ab),An` ou `(Ab),An` |

**Définitions de Ab** : on remonte le flot de contrôle comme à l'étape B (`defs`). Un élément qui n'utilise Ab que
comme base d'accès mémoire ne le change pas (`_modifie`, plus fin que le « cite Ab » de l'étape B). Toutes les
définitions doivent être des `LEA $….L,Ab [PS2 p]`.

**Table pure** : la suite maximale de cases pures qui part de `p`.
- Une case est pure si elle vaut 0, une adresse que le talon convertit, ou une adresse de fichier fixe.
- La suite va au moins jusqu'à la table suivante référencée par le code, et au-delà tant que les cases restent pures.
  Exemple : `LEA 0x855690`, `0x855694` et `0x855698` lisent la même table de palettes à trois décalages.
- Taille maximale : 4 Ko.
- Hypothèse de l'étape B : **l'index ne sort pas de la table**. La case qui suit la suite est hors des plages du
  talon, donc le talon y était déjà sans effet.
- Pour P3, seule la case lue est exigée.

**Résultat** :

| module | sites de lecture directe | relogeables | tables | cases isolées | cases relogées |
|---|---|---|---|---|---|
| SFA3 | 551 | 68 | 51 | 5 | 1 026 |
| Upper | 557 | 67 | 50 | 5 | 1 216 |
| Hyper | 430 | 37 | 38 | 0 | 2 032 |

Refus SFA3 : 365 bases inconnues (lecture d'un champ RAM, entrée externe…), 95 tables non pures (tables suivies de
données : `0x5c703c` lit des enregistrements de 8 octets au milieu d'une zone de 28 Ko), 22 lectures avec incrément.

### 2.3 Cases vues par le journal et sources des copies (`RELOGE_DONNEES=2`)

- `untranspile/reloge_donnees_<module>.txt` : une ligne par case, avec son adresse PS2 et sa valeur PS2.
  - `mame_test.py` vérifie que la valeur du fichier du module est celle du journal, sinon il ignore la case.
  - Il reloge seulement les valeurs que le talon convertit.
- **Sources de la liste** :
  1. **Journal des talons** (`journal_conv.lua`) : cases d'origine en ROM de données du module dont la valeur PS2 a été
     convertie. C'est la preuve dynamique qu'elles sont lues comme pointeurs (`outils/liste_cases.py`). Les prises de
     lecture couvrent aussi les blocs de fin de données (Upper `$C80000`, Hyper `$940000`).
  2. **Suivi des écrivains** (`suivi_ecrivains.lua` de l'étape A, `outils/liste_suivi.py`) : pour les cases RAM qui
     recevaient encore des pointeurs PS2, la case ROM source de la copie.
     - Exemples : `MOVE.L $36b19c.L,$b130(A5)` ; enregistrements par perso copiés en `$2B0-$2BC(A6)`
       (`LEA 0x67da78 ; MOVEA.L 0(A0,D0.W),A0 ; MOVE.L (A0)+,$2B0(A6)…`) ; `MOVE.L T_84f5f0(PC,D0.W),$58(A6)` ;
       `T_8505f0` ; `T_586860` / `T_5868c0` / `T_586910` → `$40(A6)`.
     - Une fois la source relogée, la case RAM reçoit d'elle-même une adresse 68K, comme l'étape A l'avait prévu.
- **Couverture SFA3**, en trois tours de journal :
  - attraction, tournée de Ryu et commandes : 5 210 cases ;
  - 32 tournées et modes 1 à 4 sur la construction de contrôle : 15 921 ;
  - balayages des fins de la construction finale + suivi des écrivains sur 32 tournées et 4 modes : **18 132 cases**.
- Upper : 17 823 cases (40 tournées et modes 1 à 4). Hyper : 1 088 (6 parties VERSUS et entraînement).
- **Sûreté.** Les lecteurs gardent leur talon. Une case non vue reste donc convertie à l'exécution, comme aujourd'hui :
  la liste ne sert qu'à la vitesse et au journal vide. Le risque résiduel est une comparaison entre un pointeur relogé
  et un pointeur brut de même cible. Aucune n'a été vue (commandes, fins, parties).
- **Liste par module dans le traducteur.** Elle dépend du module, pas de la disposition : adresses et valeurs PS2.
  Elle reste donc valable quand le code change de taille.

### 2.4 Pointeurs RAM (amorce de B) et vidéo

- `RELOGE_RAM` de l'étape B est inchangé : 6 tables, 24 cases.
- Les autres pointeurs vers la RAM ou la vidéo sont relogés par 2.2 et 2.3, par la même fonction `conv`.
  Exemple : `T_58ace0`, pointeurs vidéo → `$01900000+`.

## 3. Étape D : retrait des talons (`RELOGE_D=1`)

**Preuve statique** :
- Le site est P1, P2 ou P3 (§2.2), et toutes les définitions de la base sont des `LEA` de tables pures.
- **Toutes les cases lisibles** sont relogées ou déjà hors des plages du talon. Le talon y est donc l'identité : on
  peut le retirer.
- Hypothèse unique, celle de l'étape B : l'index reste dans la table.

**Sites libérés** :

| module | sites | répartition |
|---|---|---|
| SFA3 | 68 | 11 P1, 49 P2, 8 P3 |
| Upper | 67 | |
| Hyper | 37 | |

Sur les parcours de l'étape A, les 68 sites de SFA3 faisaient 179 507 appels sur 3,97 M (4,5 %), tous avec des valeurs
PS2 avant C.

**Ordre 68K des tables de données : abandonné.** L'essai, avec le mécanisme `natif` de B, cassait l'attraction. Des
tables étendues au-delà de la référence suivante ont d'autres lecteurs, et des tables qui se chevauchent avaient des
états différents. Le gain était négligeable (~100 cycles par image). Les tables de données gardent l'ordre échangé, et
les lecteurs libérés gardent la remise en ordre.

**Ce qui n'est pas prouvable sans l'étape E : les sources en RAM.** C'est 93 % des appels restants.
- `$1C(A6)`, `$8388(A5)`, `$BBE0(A5)`, `$41C`/`$81C(A5)` (champs `$1C` des joueurs par A5)…
- Une preuve statique demande de connaître tous les écrivains du champ. Trois obstacles :
  1. Le même déplacement désigne des champs différents selon la structure. `$1C(A4)` reçoit `MOVE.W #$50` ;
     `$41C(A5)` est le `$1C` du joueur 1.
  2. Les copies génériques (`MOVE.L (A0),(A1)` déroulé en `$57FF4…`, `MOVE.L -4(A0),(A1)` en `$9316C…`) écrivent
     n'importe où.
  3. **Des pointeurs sont copiés par moitiés** (`MOVE.W -2(A3),-2(A4)` vers `$FFD854` : suivi des écrivains).
     L'hypothèse « un pointeur n'est jamais construit par mots » est donc fausse.
- Il faut le typage de la RAM par provenance (étape E). Ces talons restent, avec le filtre en ligne du §4.
- **Mesure.** Après C, le journal y voit 0,08 % de valeurs PS2 sur les fins (§5). Avant C : 2,1 % sur le même
  parcours, et 26 % des appels de données sur les parcours de l'étape A.

## 4. Étape D' : filtre en ligne (`TALON_EN_LIGNE=1`)

- **Forme.** Devant chaque talon gardé :
  `CMPA.L #debut,An ; BCS.S suite ; CMPA.L #fin,An ; BCC.S suite ; JSR CONV_An ; suite:`.
- **Pourquoi c'est exact.** `[debut, fin)` contient toutes les plages du talon, et le talon est l'identité hors de cet
  intervalle. Le filtre ne change donc aucune valeur.
- **Coût.**
  - Adresse 68K de ROM (sous `$583C40`) : 24 cycles au lieu de ~88.
  - RAM `$FFxxxx`, matériel `$01…`, bloc fixe : 46 au lieu de ~106.
  - Valeur PS2 : 44 de plus. Il n'en reste presque plus.
- **Condition : drapeaux morts.** `CMPA` écrase N, Z, V, C (pas X). Le talon, lui, les préservait : un `MOVEA` peut
  se trouver dans le créneau d'un branchement. On pose donc le filtre seulement si l'instruction suivante écrase
  N, Z, V, C sans les lire.
  - Instructions qui écrasent : MOVE, MOVEQ, TST, CLR, CMP(I/A), ADD/SUB(Q/I) hors An et hors X, AND/OR/EOR(I),
    MUL/DIV, NEG/NOT/EXT, SWAP, décalages et rotations.
  - Éléments traversés sans effet : MOVEA, LEA, ADDA/SUBA, PEA, EXG, autres lectures à talon, zones de registre
    prêté (`MOVE SR … MOVE CCR ; MOVEA (SP)+`).
  - Sauts suivis : sauts inconditionnels vers `label()`.
  - Appel d'une fonction traduite : drapeaux morts (une fonction traduite ne lit pas les drapeaux reçus).
  - `RTS` est laissé : « drapeaux rendus à l'appelant », §66/§126.
- **Couverture** : SFA3 513 talons sur 533 ; Upper 520 / 540 ; Hyper 383 / 400.
- **Restent sans filtre** : `$BBE0(A5)` suivi d'un `RTS` (~5 appels par image), `BTST #6,(A0)`, `JMP (A0)`.

## 5. Validations

Constructions finales (dossier de travail de `mame_test.py`, construites par `scripts/construit.sh`) :

| module | dossier | md5 `sz3ud.03c` | programme entier | données |
|---|---|---|---|---|
| SFA3 | `mame9/` | `4cfbb5fb216591f2ddfeea465d9477a9` | `84bea2d72f088ebeb792b0fc8b676867` | `$96000` |
| Upper | `mame8_ro5/` | `ae50a19883933fe49160d20c58f007f6` | `3da80777bd51fbcc2a9b2ad255612ea2` | `$A3000` |
| Hyper | `mame9_ro9/` | `e5db334234f60bf5fce2825b1af9f131` | `d1e0d6517ef71b4f8725d0fb85e8ec5f` | `$96000` |

Tous les interrupteurs à 0 (copie finale) : SFA3 `7e22b1ec…`, Upper `1908ec9e…`, Hyper `964943b1…`, c'est-à-dire les
ROM de référence du traducteur partagé validé.

### 5.1 SFA3 (`mame9/`, liste v5)

- **Non-régression** (`scripts/nonreg_B.sh`) : 3 diagnostics (20 000 sans entrée, 20 000 avec entrées, 60 000
  offensive) **sans exception** ; test des commandes **42 actions, 0 différente, 5 359 tours en 4 019 images (133,3 %)**.
- **32 fins** (`scripts/balayage_B.sh`, journal chargé) : **32/32 `fin=finie`, captures = arcade ±1 pour les 32**
  (`balayages/mame9_*/res.txt`).
- **Journal des talons**, avec le journal chargé dans les mêmes parties :

| parcours | images | appels des talons de données | valeurs PS2 vues |
|---|---|---|---|
| 32 fins | 784 000 | 5 248 799 | **2 752 (0,05 %)** |
| modes : attraction, commandes, VERSUS, SURVIVAL, mode 3, entraînement | 146 800 | 548 602 | **637 (0,12 %)** |

  - Talon de code : 122 487 appels, tous avec des adresses 68K (`$40(A6)`, site RAM de l'étape B) plus le noyau.
  - **Ce qui reste.** Les valeurs PS2 restantes viennent de cases ROM jamais vues avant ce dernier parcours :
    frames d'animation `4(A0)` de `$FC52C` et quelques copies vers la RAM pendant SURVIVAL. Elles sont converties à
    l'exécution par le talon gardé : le comportement est exact.
  - Un tour de plus (journal → liste) les ferait disparaître. Je ne l'ai pas fait, pour ne pas livrer une ROM non
    validée (§9).
- **Évolution du journal sur les fins**, d'un palier à l'autre :
  - `mame6` (liste v2) : 114 439 valeurs PS2 (2,1 %) ;
  - `mame7` (v3, suivi des écrivains) : 4 439 ;
  - `mame9` (v5) : 2 752.
- Les paliers intermédiaires `mame6`, `mame7` et `mame8` ont eux aussi passé les commandes à 42/42 à 133,3 % et
  les 3 diagnostics. `mame6` et `mame7` ont aussi fait 32/32 fins ±1.

### 5.2 Upper (`mame8_ro5/`, liste v2)

- **Non-régression** (`scripts/nonreg_ro5_B.sh`) : diagnostic de 20 000 images **sans exception**.
  Parties sur le fork : Chun-Li 04 27 manches, Ryu 00 28, Akuma 02 33, toutes **`FIN fin=finie`**.
- **40 fins** : [BALAYAGE_RO5]
- **Journal sur la tournée de Ryu** (40 000 images, fork) :
  - talons de données 2 134 181 → 293 282 appels (−86 %) ;
  - valeurs PS2 511 520 → 3 303 ;
  - base : construction avec les interrupteurs à 0, c'est-à-dire l'étape B.
- **Cadence** (`scripts/fork_cad.sh`, tournée de Ryu, images 4 000 à 14 000, vitesse normale) :
  - fin de liste des itérations à un tour : ligne 183 → **171** (médiane) ;
  - listes par image 0,991 → 0,992 ;
  - images sans tour 76 → 78.
  - Les parties divergent (le hasard dépend du temps processeur) : seule la ligne de fin par itération est comparable.
- **Palier intermédiaire** `mame7_ro5/` (liste v1, sans la règle des enregistrements) :
  - même non-régression (26 / 28 / 32 manches, `fin=finie`) ;
  - 16 fins balayées, toutes **`fin=finie`** (`balayages/ro5_mame7_ro5_*`).
  - Ce balayage a été arrêté au profit de la construction finale.

### 5.3 Hyper (`mame9_ro9/`)

- **Partie VERSUS** (`scripts/hyper_vs_B.sh`, comme `valide_tout.sh`) : sélection image 408, manches images 1 035 et
  1 658, `FIN 20000`, **sans exception**. C'est **identique** à l'étape B et aux paliers `mame7_ro9` / `mame8_ro9`.
- **Journal** : 6 parties VERSUS (paires de persos `00…23`, familles A/Z/Z2/Z3, options) et l'entraînement,
  260 000 images.
  - Talons de données : 3 485 578 → **308 664 appels (−91 %)**.
  - Valeurs PS2 : 416 453 → **318 (0,10 %)**.
  - Base : construction avec les interrupteurs à 0.

## 6. Gain mesuré (SFA3)

**Appels de talons sur les parcours de l'étape A** (attraction 20 000 images, tournée de Ryu 40 000, test des
commandes ; 66 800 images) :

| | talons de données | dont valeurs PS2 converties | talons de code |
|---|---|---|---|
| étape B (`mame1c`) | 3 972 331 | 1 094 930 | 5 325 |
| **C + D + D' (`mame8`)** | **175 232 (−95,6 %)** | **971** | **68** |

Avant l'étape B, il y en avait 7,03 M. Il reste 17 sites actifs, tous des talons sans filtre ou dont le filtre
laisse passer la valeur :
- `$BBE0(A5)` suivi d'un `RTS` : 154 068 appels, soit **88 %** du reste ;
- `$1C(A6)` suivi de `BTST` ;
- `MOVEA.L D0,A1` suivi d'un `RTS` : valeurs matérielles ;
- `$BA44` / `$BA48(A5)` ;
- les copies `$2B0-$2BC` encore PS2 (426 + 268 valeurs).

**Mots d'opcodes lus par tour de jeu**, profil du test des commandes (`runs/prof_cmd_B.lua`, `outils/prof_an.py`,
3 750 images de combat, 4 999 tours) :

| par tour | étape B | C + D + D' |
|---|---|---|
| talon de données `$400` | 1 198 | 4 |
| `JSR` vers les talons | 110 | 18 |
| filtre en ligne | — | 303 |
| **total des conversions** | **1 308** | **325 (−75 %)** |
| travail par tour | 18 625 | **17 720 (−4,9 %)** |
| attente (boucle du noyau) | 26,3 % | **30,9 %** |

**Cadence turbo** (test des commandes, combat, images 2 700 à 6 800, `outils/cadence.py`) :

| | étape B | C + D + D' |
|---|---|---|
| listes d'objets par image | 0,981 | **0,996** |
| images sans tour | 1 | **0** |
| fin de liste, itération à 1 tour (médiane) | ligne 170 | **160** |
| fin de liste, itération à 2 tours (médiane / 90ᵉ centile) | 251 / 270 | **237 / 240** |
| itérations à 2 tours dans la fenêtre 255-269 | 68 | **19** |
| tours du test des commandes | 5 358 | **5 359 (= arcade)** |

**Ligne de fin d'image obtenue.**
- L'itération turbo à deux tours finit en médiane à la **ligne 237** : 14 lignes plus tôt qu'à l'étape B, et
  **18 lignes avant la fenêtre** où le jeu perd une image (≈ 260-267, IRQ2 à la ligne 5 de l'image suivante).
- Le 90ᵉ centile passe de 270 (dans ou après la fenêtre) à **240**.
- Il reste des phases lourdes, J2 qui marche en arrière vers l'image 1 760 et vers 3 710 du combat, qui finissent aux
  lignes 250-261. Le jeu y garde ses tours : 0 image sans tour sur 4 100.
- Pour la petite console, le jeu dispose d'environ 5 % de temps 68000 en plus par image. La charge de l'hôte, elle,
  ne change pas : l'émulateur simule le 68000 à cadence fixe (ARCHI §5).

## 7. Paliers et cadence turbo

Chaque palier a été contrôlé par le test des commandes et par `outils/cadence.py` (combat, images 2 700 à 6 800) :

| palier | interrupteurs (en plus de B) | commandes | tours | 2 tours : médiane / 90ᵉ c. | fenêtre | listes/image |
|---|---|---|---|---|---|---|
| B (`mame1c`) | — | 42/42 | 5 358 | 251 / 270 | 68 | 0,981 |
| natif (`mame2n`) | `RELOGE_ANIMNAT` | **41/42** | 5 355 | 249 / 261 | 38 | 0,982 |
| C données (`mame3`) | + `RELOGE_DONNEES=2` (liste v1) | **41/42** | 5 354 | 244 / 251 | 43 | 0,987 |
| filtre (`mame4`) | + `TALON_EN_LIGNE` | 42/42 | 5 358 | 237 / 241 | 17 | 0,996 |
| D (`mame5`) | + `RELOGE_D` | 42/42 | 5 359 | — | — | — |
| v2 / v3 / v4 / v5 (`mame6`…`mame9`) | idem, listes enrichies | 42/42 | 5 359 | 237 / 240 | 19 | 0,996 |

**Le piège de l'étape B s'est reproduit deux fois** : paliers natif et C seuls.
- Le jeu, un peu plus rapide, fait finir l'itération turbo à deux tours dans la fenêtre.
  Exemple (palier natif, combat image 3 606, J2 qui marche en arrière) : `T11 T97 F260`, puis image suivante sans
  tour. À l'étape B : `F261` puis `T6` débordant sur l'image suivante. Le jeu y perdait 1 à 4 tours, d'où
  « marche arrière J2 dx=76 au lieu de 80 ».
- Ce ne sont pas des fautes de traduction : il n'y a pas d'exception et le journal est propre. C'est la course de
  cadence du §4 de l'étape B.
- Le filtre en ligne fait passer de l'autre côté (14 lignes de plus). **Les interrupteurs C et D' vont donc
  ensemble** : `RELOGE_ANIMNAT=1 RELOGE_DONNEES=2 TALON_EN_LIGNE=1 RELOGE_D=1`.
- Palier intermédiaire du filtre (première version, sans suivre sauts ni appels : 379 talons sur 590) :
  42/42 mais 5 355 tours.

## 8. Fichiers

**Diffs contre `scripts/untranspile`** (dans `diff/`, format `patch -p3` comme l'étape B ; `scripts/diffs.sh` les
régénère) :
- à appliquer **sur le traducteur partagé actuel**, qui contient déjà l'étape B (RELOGE_* à 1), FLUXEA et
  OPTION_RETOUR / EXIT_RETOUR : `cd scripts/untranspile ; for f in …/diff/*.diff ; do patch -p3 < $f ; done` ;
- sur un traducteur sans B : appliquer d'abord `work/agent_reorg_B/diff/{assemble,mame_test,diag}.py.diff`, puis
  `work/agent_options/diffs/traducteur_option_exit.diff`, puis ceux-ci ;
- vérifié : la copie figée `untranspile.orig/` + les 6 diffs = `untranspile/`.

| diff | contenu |
|---|---|
| `assemble.py.diff` | `reloge_donnees` (C et D), `enregistrements`, `_modifie`, `talon_en_ligne` (D'), `conv_ps2` / `fixe_ps2` |
| `mame_test.py.diff` | `RELOGE_ANIMNAT` ; export des plages du talon (`conv_plages.txt`) ; relogement des cases ; `etapeC_donnees.txt` |
| `assets_natifs.py.diff` | `AN.PTRS` (positions des pointeurs internes du bloc natif) |
| `reloge_donnees_ro3/ro5/ro9.txt.diff` | listes de cases, nouveaux fichiers |

**Sorties de construction** :
- `conv_plages.txt` : plages du talon `$400` ;
- `etapeC_donnees.txt` : tables, cases isolées et sites D ;
- journal de construction : lignes `etape C (natif)`, `etape C (donnees)` et `etape D'`.

**Scripts** (`scripts/`) :

| script | rôle |
|---|---|
| `construit.sh <ro3\|ro5\|ro9> <dossier> [VAR=…]` | construction d'une variante, md5 du programme entier |
| `cmdcad.sh <dossier> <nom>` | **contrôle de palier** : test des commandes + relevé de cadence (`CAD_F0/CAD_F1`) + résumé |
| `nonreg_B.sh`, `balayage_B.sh` | SFA3 : 3 diag + commandes ; 32 fins (`SCRIPT=runs/tournee_j.lua` : journal en même temps) |
| `nonreg_ro5_B.sh`, `balayage_ro5_B.sh` | Upper (fork) ; idem |
| `hyper_vs_B.sh` | VERSUS d'Hyper |
| `journal_tout.sh <dossier> <étiq.> [parcours]` | journal des talons SFA3 : attraction, commandes, 32 tournées, modes 1-4 |
| `journal_fork.sh <ro5\|ro9> …` | idem sur le fork ; `SUIVI_CASES=…` : suivi des écrivains |
| `suivi_tout.sh` | suivi des écrivains SFA3 (32 tournées + modes) |
| `fork_cad.sh`, `lance.sh` | cadence d'Upper ; MAME standard isolé |
| `diffs.sh` | diffs contre la copie figée |

**Outils** (`outils/`) :
- `sites.py` : bilan du journal par site et par classe de valeur, avec les plages du dossier ;
- `liste_cases.py` : cases ROM du journal → liste ;
- `liste_suivi.py` : sources ROM des copies vers la RAM → liste ;
- `table.py` : inspection d'une table ;
- `cadence.py` : ajout du 90ᵉ centile et de la fenêtre 255-269 ;
- `prof_an.py` : catégorie « filtre en ligne » ; fichier temporaire dans `tmp/` ;
- `journal_conv.lua` : prises sur les blocs `$C00000-$EEFFFF` et `$930000-$9FFFFF` ;
- `suivi_ecrivains.lua` : copie de l'étape A.

**Données** :
- `journaux/` : journaux bruts (`j5*` contrôle, `j8*`/`j9*` final, `suivi*`), relevés `cad_*`, profils `profC_*` ;
- `resultats/` : bilans JSON par site, listes successives `liste_*.txt`, profils `prof_c1/c5/c8.txt` ;
- `balayages/`.

**Dossiers de construction** :
- `mame0` : SFA3 tout à 0 ;
- `mame1c` : étape B ;
- `mame2n` … `mame9` : paliers du §7 ;
- `mame5c`, `mame5_ro5c`, `mame5_ro9c` : contrôle (`RELOGE_CODE=2`, `RELOGE_D=0`, journal) ;
- `mame5_ro5_0`, `mame5_ro9_0` : Upper et Hyper avec les interrupteurs à 0 ;
- `mame7_ro5`, `mame8_ro5` : Upper ;
- `mame7_ro9` … `mame9_ro9` : Hyper.

## 9. Limites et suite

- **Couverture des listes.** La liste par module vient de parcours. Une case jamais lue garde sa valeur PS2, et son
  talon la convertit : c'est exact, seulement plus lent. Les journaux finaux en montrent 0,05 % (fins SFA3), 0,12 %
  (modes SFA3), 0,10 % (Hyper).
  - Chaque nouveau parcours journalisé peut compléter la liste : `liste_cases.py … --ajoute
    untranspile/reloge_donnees_<m>.txt`.
  - Une case ajoutée change la ROM : refaire au moins `cmdcad.sh` et `nonreg_B.sh`.
- **Hyper** : les parties VERSUS n'ont fait qu'une sélection chacune (6 paires). Les autres persos d'Hyper ne sont
  couverts que par la règle statique.
- **Étape D sur la RAM : impossible sans l'étape E** (§3). Le filtre en ligne en récupère l'essentiel du coût.
  `$BBE0(A5)` (drapeaux vifs à cause du `RTS`, ~5 appels par image) est le dernier poste notable. Pour le libérer,
  il faudrait savoir quelles fonctions rendent des drapeaux à leur appelant.
- **Ordre 68K des tables de données** : abandonné (§3).
- **Disposition.** Les données commencent maintenant en `$96000` (SFA3, Hyper) et `$A3000` (Upper). Le bloc
  d'animation natif est en `$39EB00` (SFA3). Tout outil qui coderait une adresse de données en dur doit la relire dans
  `carte_image.txt`. Aucun outil du banc ne le fait pour les zones touchées.
- **Comparaisons de pointeurs** : un pointeur relogé comparé à un pointeur brut de même cible serait vu différent.
  Rien de tel dans les validations. Le risque baisse à mesure que la liste se complète.
- **Suite** : étape E (RAM typée). Elle seule permet de prouver les champs `$1C(A6)`, `$8388(A5)`… et de retirer les
  derniers talons, ainsi que les échanges de moitiés de longs (≈ 965 mots par tour, le premier poste d'adaptation
  restant).
