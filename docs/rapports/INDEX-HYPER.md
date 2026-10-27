# Index statique d'Hyper Street Fighter Alpha (module `ro9`)

Agent « index Hyper », 2026-10-07. **Lecture seule** de l'existant : rien n'a été modifié en dehors de
`<workspace>/work/agent_hyper_index/`. Pas de MAME, pas de PCSX2. Calculs lourds en `nice -n 19`.

**Conventions**
- `fichier` = décalage dans `ro9_usa_prog68k.bin` ; `exéc.` = fichier + `0x1F0000`. Code en `fichier`, données en `exéc.`.
- **Champs en numérotation PS2**, celle du MIPS. Les octets y portent le **même numéro que dans l'arcade**
  (`$102` = identifiant, comme dans `sfa3_support.lua`). La traduction 68K et `carte_image.txt` affichent ce numéro XOR 1.
- « routine » : découpage fin de la carto (`GRAIN=routine`, 10 168 routines).
- Les classes (identique / modifiée / apparentée / nouvelle) viennent de `carto_ro9/comparaison_ro9_routine.pkl`.
- Les noms de champs de jeu viennent de `agent_web/sfa3_support/sub/*.lua` (en numérotation arcade = PS2), de
  `PERSOS-COMBAT.md` et de `agent_symboles/symboles_ro3.csv`.

**Sommaire**
0. En bref
1. Identifiants étendus `$102`
2. Bits de version `$D3`, `$117`, `$132`, et les 1 445 tests
3. Les tables par `$102` et le format de la zone nouvelle
4. Systèmes de jeu par version
5. Variables A5, RAM et champs propres à Hyper
6. Inconnues et points à vérifier en jeu
7. Fichiers produits

---

## 0. En bref

1. **`$102` = id étendu** (perso × version), 0..`$7F`.
   - Il est choisi à la validation de la colonne de version : `$102 = grille[$116×4 + $5D]`
     (routine `0x31AAA0`, nouvelle).
   - Grille normale : `0x5C5380`. Si **Start est maintenu** (bit 15 de `$11A`, testé `BTST #7,$11B`), c'est la
     **grille secrète `0x5C5420`**.
   - ⟹ **C'est ainsi qu'on choisit les EX, Shin Akuma, EX Balrog, Chun-Li SF2 et Sakura bis.** Ce point était
     marqué inconnu dans `BANQUES-ET-MODES-ro9.md` §3.2.
   - `0x321BA0` décode ensuite : `$116 = 0x5C5300[$102]`, `$117 = $D3 = 0x5C2490[$102]`.
2. **`$D3`** = drapeaux de version de travail, recalculés à l'initialisation de combat (`0x2C6BE0`).
   - bit 0 ZERO ; bit 1 famille ZERO 2 ; bit 2 ZERO 2 ALPHA ; bit 3 EX ; bit 4 ZERO 3 ; bit 5 ZERO 2 d'origine.
   - **bit 7 (nouveau)** : posé **avec** le bit 3 par le code quand `$F0 < 0`, c'est-à-dire avec le mode secret
     ZERO 3 `$15E = $81` (curseur 7 de l'écran de mode).
   - **bit 6** : jamais posé, ni par une table ni par le code ⟹ ses 16 tests sont des branches mortes ou un
     réglage externe.
   - `$117` reste la version « vraie » (50 tests directs, dont 37 du bit 4).
3. **Les 1 445 `BTST $D3`** : 1 004 sont dans le **code des persos** (Ryu 95, Bison 74, Ken 73, Akuma 71…) et 441
   dans le moteur.
   - Sujets dominants : physique 387, état du coup 152, entrées 144, animation 141, orientation 124,
     custom combo 95.
4. **45 tables indexées par `$102`**, et non 30 (§3).
   - Les 13 tables de **code** renvoient, pour les versions anciennes, aux routines du perso en ZERO 3 : 71 ids sur 77.
     Les 6 autres (`$57`, `$58`, `$59`, `$5A`, `$5C`, `$5E`) tombent sur Ryu.
   - Les tables de **données** de géométrie et d'animation sont propres à chaque version (zone nouvelle).
   - **3 tables Upper à 40 entrées** (`0x6AF640`, `0x6AF668`, `0x6AF6B8`) sont lues par `$102` dans des routines
     identiques à Upper. ⟹ **débordement pour les ids ≥ `$28`** (bogue probable d'Hyper).
5. **Format de la zone nouvelle** : identique à SFA3/Upper (pas de 20 o, frames type 2, boîtes de 8 o), **sauf les
   enregistrements d'attaque, qui passent de 32 à 40 octets dans Hyper.**
   - Toutes les versions sont concernées, ZERO 3 compris : 15 sites `×40`, le MIPS calcule `idx×5×8`.
   - Les 8 octets ajoutés (`+$20..+$27`) sont nuls en ZERO 3 et remplis en ZERO / ZERO 2 / ALPHA. Ils sont lus par
     le moteur de coups (`+$20`, `+$23`, `+$24`).
6. **Mécaniques par version** : le custom combo est choisi dans `0x2D1F10` (nouvelle).
   - ZERO 3 : V-ism, `$11E ≥ $48` et P+K de même force.
   - ZERO 2 : niveau 1 (`$30`) et une combinaison de 3 boutons.
   - ALPHA : `$4400` (HP+HK).
   - ZERO, EX et bit 6 : interdit.
   - Jauge affichée selon la version (`0x3B7320`, nouvelle : rien pour ZERO 3 et EX).
   - Garde auto (`$118` → `$32F`, 10 en ZERO).

---

## 1. Identifiants étendus `$102`

Fichier complet : **`ids_102.tsv` / `ids_102.json`** (128 lignes). Colonnes : version, perso de base, nom, `$117`,
bits, banque X_DATA, fichier MOMO, id de chargement natif, présence dans les deux grilles.

### 1.1 Plages

| ids | version (écran US) | `$117` | banques (`0x5AF1B0`) | MOMO (`0x5AF2B0`) |
|---|---|---|---|---|
| `$00-$25` | ZERO 3 (ALPHA3) | `$10` | 355-386 (Upper) | 314-344 |
| `$26-$2F` | remplissage (= Ryu Z3) | `$10` | 355 | 314 |
| `$30-$3C` | ZERO (ALPHA) | `$01` | 208-220 (SFA1) | id de base |
| `$3D-$3F` | remplissage (= Ryu ZERO) | `$01` | 208 | 314 |
| `$40-$5F` | ZERO 2 (ALPHA2) | `$22` ; `$2A` pour `$55,$56,$58-$5C` (EX) | 229-248 (SFA2) | id de base |
| `$60-$7F` | ZERO 2 ALPHA (ALPHA2G) | `$06` ; `$0E` pour `$75,$76,$78-$7C` (EX) | 229-248 | id de base |

Particuliers :
- `$12` (Chun-Li X), `$13` (Gen 2ᵉ style), `$14` (Sodom X), `$17` (Evil Ryu), `$24` (Shin Akuma), `$25` (EX Balrog).
- ZERO 2 : `$52` (Chun-Li tenue SF2, banque 247), `$53` (Gen 2ᵉ style), `$54` (Shin Akuma), `$57` (Evil Ryu),
  `$5D` (Sakura bis), `$5E` (Cammy), `$5F` (remplissage).
- ALPHA : `$72`, `$73`, `$74`, `$77`, `$7D`, `$7E` (Cammy), `$7F` (remplissage).
- Gen bascule de style par `BCHG #1,$102` (`0x2C5198`, `0x2C5548`) : `$11↔$13`, `$51↔$53`, `$71↔$73`. Les variantes
  ZERO 2 / ALPHA sont reposées par `0x1DC2B0` (`#$51/$71/$53/$73`, `$116 = $11/$13`).
- Id de chargement `0x5AF420` (natif `0x22B00` / `0x2142B0`) : il ramène EX et variantes à l'id de base, mais la banque
  reste toujours `0x5AF1B0[$102]` (cf. BANQUES §1.1).

### 1.2 Calcul de l'id (sélection)

| étape | routine (fichier) | ce qui se passe |
|---|---|---|
| entrée de l'écran (VERSUS `$C200 = 1`, TRAINING `= 4`) | `0x316E50` (nouvelle) | `$102 = $C30E(A5,joueur)` (dernier choix), puis normalisation : `$13→$11`, `$24→$02`, `$54→$42`, `$74→$62`, `$25→$15` ; décodage `0x321BA0` ; puis **`$102 = $116`** : pendant la sélection, `$102` est le perso du curseur, comme dans SFA3 |
| curseur de version `$5D` (0..3) | `0x31AAA0` (nouvelle) `0x31AD4C-0x31ADE4` | aperçu : `$102 = $116 + …`, puis `0x321BA0` |
| **validation** | `0x31AAA0` `0x31AE78-0x31AF38` | `A0 = 0x5C5380`, ou `0x5C5420` si `BTST #7,$11B` (Start tenu) ; `$102 = A0[$116×4 + $5D]` ; `CLR $132` ; `JSR 0x321BA0` |
| variante (homologue d'Upper) | `0x319430` `0x31A048-0x31A078` | même test Start : `MOVE.B T_5c5420(PC,D0.W),$102(A6)` |
| choix aléatoire | `0x98DA0` (nouvelle, homologue de `port_202B70`) | tirage 0..63 masqué par `T_5B5D90/94` → `$102` |
| décodage | `0x321BA0` (nouvelle) | `$116 = T_5C5300[$102]` ; `$117 = T_5C2490[$102]` ; `$D3 = $117` |
| combat | `0x2C6BE0` (modifiée, homologue de `fonc_02BDD6`) | `$D3 = T_5C2490[$102]` ; si non EX et `$F0 < 0` : `BSET #3` et `BSET #7` ; `$B5 = 1` si EX |

**Les grilles** (38 lignes × 4 octets, indexées par `$116`) :
- chaque ligne est la liste des versions disponibles, dans l'ordre ZERO, ZERO 2, ALPHA, ZERO 3, terminée par `$FF` ;
- `$5D` est un **rang dans cette liste**, pas un numéro de version : la ligne de Sakura `4D 6D 0D FF` n'a pas de
  colonne ZERO.

| ligne | grille normale `0x5C5380` | grille Start `0x5C5420` |
|---|---|---|
| Ryu `$00` | `30 40 60 00` | `30 40 7B 00` (ALPHA → **EX Ryu**) |
| Ken `$01` | `31 41 61 01` | `31 41 7A 01` |
| Akuma `$02` | `32 42 62 02` | `32 54 74 24` (**Shin Akuma** en ZERO 2, ALPHA et ZERO 3) |
| Chun-Li `$04` | `34 44 64 04` | `7C 52 72 04` (colonne ZERO → **EX Chun-Li ALPHA** ; ZERO 2 et ALPHA → tenue SF2) |
| M.Bison `$0A` / Sagat `$0B` | `3A 4A 6A 0A` / `3B 4B 6B 0B` | `3A 58 78 0A` / `3B 59 79 0B` (**EX en ZERO 2 et en ALPHA**) |
| Sakura `$0D` | `4D 6D 0D FF` | `5D 7D 0D FF` |
| Dhalsim `$0F` / Zangief `$10` | `4F 6F 0F` / `50 70 10` | `56 76 0F` / `55 75 10` (EX) |
| Balrog `$15` | `15` | `25` (EX Balrog) |
| Cammy `$16` | `7E 16` | `7E 16` |
| Evil Ryu `$17` | `57 77 17` | `57 77 17` |

Présence dans les grilles (`ids_102.json`) :
- **hors des deux grilles** : `$12 $13 $14 $53 $5A $5B $5C $5E $5F $73 $7F` (plus le remplissage) ;
- **seulement avec Start** : `$24 $25 $52 $54 $55 $56 $58 $59 $5D $72 $74 $75 $76 $78 $79 $7A $7B $7C $7D`.
- ⚠ **Correction de BANQUES §3.2** : `$58` (EX Bison ZERO 2) et `$59` (EX Sagat ZERO 2) **sont sélectionnables**
  (Start + colonne ZERO 2).
  - Or leurs tables de géométrie et d'animation sont celles « par défaut » (Ryu ZERO 3). On aura donc à l'écran le
    sprite en morceaux observé au banc.
  - Soit c'est un vrai défaut du jeu PS2, soit l'écran empêche ce choix d'une autre façon. **À vérifier sur PCSX2.**

### 1.3 Entrées des tables par `$102`, par id (résumé ; détail dans `tables_102.tsv`)

| famille de tables | ZERO 3 (`$00-$25`) | ZERO / ZERO 2 / ALPHA (77 ids) |
|---|---|---|
| 13 tables de **code** (`0x6A59D4`…`0x6A7894`, `0x6AD614`) | propres | **= ZERO 3 du perso de base** pour 71 ; « défaut » Ryu pour `$57 $58 $59 $5A $5C $5E` ; IA propre pour `$79 $7A $7B` (`0x6AD614`) |
| géométrie `0x6A6BD4`, `0x6A6DD4`, `0x6A6FD4` | Upper | propres (zone nouvelle 69/77) ; partages entre ZERO 2 et ALPHA d'un même perso, et entre EX et normal (`$50=$55`, `$70=$75`…) ; défaut Ryu pour `$58 $59 $5A $5C $5E` |
| animations `0x6A7A94` | Upper | propres (65) ; défaut pour `$58 $59 $5A $5C $5E` ; `$4D=$5D`, `$6D=$7D` |
| vitesses `0x6A7E14` / sauts `0x6A8614` | Upper | = ZERO 3 du perso de base pour 61 / 66 ; propres : marche `$53 $75 $76 $79`, sauts `$34 $71 $73` |
| sons par pas `0x6AE614` | Upper | = ZERO 3 (70), propres `$78 $7E` |
| effets du pas `0x6AE814` | Upper | **un seul pointeur pour toutes les versions anciennes** |
| IA (scripts) `0x6AD814…0x6ADE14` | Upper | propres 16-18, partagés 59-61 |
| octets `0x5B5C30` (nombre de couleurs), `0x5C5550` (masque de couleur) | | = ZERO 3 (52), partagés (25) |
| `0x6669CC` (mot → `$120(A5)`) | | propres 54 |

---

## 2. Bits de version : `$D3`, `$117`, `$132`

### 2.1 Qui écrit (`ecritures.py`)

| champ | écrit par (fichier) | valeur |
|---|---|---|
| `$102` | `0x31AAA0`, `0x319430`, `0x316E50`, `0x98DA0`, `0x1DC2B0`, `BCHG #1` (`0x2C5160`, `0x2C5330`), Gen `0x1C73D0…0x1CA960` (`#$11/#$13`), `0xA43F0` / `0xA5CA0` (identiques à Upper : table de rival `0x5B61F0`, vestige du mode arcade) | §1.2 |
| `$116` | `0x321BA0` (table `0x5C5300`), `0x1DC2B0` (Gen) | perso de base |
| `$117` | `0x321BA0` seulement | `0x5C2490[$102]` |
| `$D3` | `0x321BA0` et `0x2A1AD8` (copie de `$117`), **`0x2C6C4C`** (table), `0x2C6CE4` (`BSET #3`), `0x2C6D1C` (`BSET #7`), `0x95E10` (remise à 0), `0x390FD4` (création d'objet : 0), `0x390CC8` / `0x390E28` (héritage `$D3(A6) → $D3(A4)`) | |
| `$132` (ism : −1 X, 0 A, +1 V) | `0x319430` (`T_5C5690[curseur]`), `0x31B890` (écran de mode), `0x31AAA0` (`CLR`), `0x991A0` (codes de l'arcade), `0xA43F0`, `0x31CA20` | |

Le **bit 6 n'est écrit nulle part**. On a vérifié les écritures larges sur `$D0-$D3` : seul `MOVE.W #$E000,$D0` existe,
qui ne touche pas `$D3`.

### 2.2 Signification et comptes

| bit | sens | posé par | tests `$D3` | dans le moteur / les persos | tests `$117` |
|---|---|---|---|---|---|
| 0 | ZERO (SFA1) | table | 341 | 85 / 256 | 6 |
| 1 | famille ZERO 2 (ZERO 2 et ALPHA) | table | 190 | 46 / 144 | 3 |
| 2 | ZERO 2 ALPHA (Gold) | table | 87 | 56 / 31 | 1 |
| 3 | EX (7 persos × 2 versions) ; **aussi posé avec le bit 7** | table + `0x2C6CE4` | 183 | 50 / 133 | 2 |
| 4 | ZERO 3 | table | 467 | 152 / 315 | **37** |
| 5 | ZERO 2 d'origine (pas ALPHA) | table | 38 | 10 / 28 | 1 |
| 6 | **jamais posé** | — | 16 | 8 / 8 (supers, CC, provocation `0x2D29F0`) | 0 |
| 7 | **mode secret ZERO 3 `$15E = $81`** (« EX forcé ») | `0x2C6D1C` | 123 | 34 / 89 | 0 |

- **`$117` sert quand il faut la version vraie**, `$D3` pouvant avoir reçu les bits 3 et 7. Exemple : `0xA5FC4`,
  routine `$BC06` d'Upper, `BTST #4,$117`.
- `$D3` est hérité par les objets enfants : 118 tests sur `$D3(A4)`, 41 sur A3.
- Comparaisons d'identité : `CMPI.B #,$116` = 82 dans ro9 (0 dans ro5) ; `CMPI.B #,$102` = 117 (130 dans ro5).
  Accès à `$116` : 209 (contre 6). `$132` : 535 (547 dans Upper).

### 2.3 Classement des 1 445 tests (`btst_d3.py` → `btst_d3.tsv`, `btst_d3_sites.json`, `btst_d3_bilan.txt`)

Pour chaque site, le script relève :
- le bit, le registre et le sens du branchement ;
- la routine, sa classe et son partenaire ro3 (avec son symbole) ;
- le **propriétaire** : code d'un perso, d'après les bornes des 13 tables de code par `$102`, sinon moteur ;
- un **sujet**, tiré des champs touchés dans une fenêtre de −6/+14 instructions.

Le sujet est **heuristique** : la première règle qui s'applique l'emporte.

| sujet | total | b0 | b1 | b2 | b3 | b4 | b5 | b6 | b7 |
|---|---|---|---|---|---|---|---|---|---|
| physique (vitesses `$40-$4E`, position, sol `$64`, `$2D0/$2D4`, largeur `$A6`) | 387 | 123 | 52 | 12 | 26 | 113 | 12 | 1 | 48 |
| état et coup en cours (`$04-$07`, force `$80-$83`, `$A9-$AB`) | 152 | 25 | 32 | 7 | 18 | 52 | 4 | 0 | 14 |
| entrées et commandes (`$11A-$11D`, `$378-$37B`, tampons `$190-$1F0`) | 144 | 42 | 31 | 4 | 17 | 37 | 3 | 1 | 9 |
| animation (`$1C`, `$2B0-$2BC`, `LEA` vers la zone nouvelle) | 141 | 25 | 13 | 25 | 9 | 51 | 1 | 0 | 17 |
| orientation et posture (`$2C8/$2C9` → `$0B`) | 124 | 32 | 4 | 1 | 29 | 40 | 3 | 5 | 10 |
| autre | 98 | 13 | 4 | 15 | 23 | 26 | 6 | 6 | 5 |
| custom combo / V-ism (`$B9` cc_flg, `$BB`, `$BC`) | 95 | 4 | 35 | 1 | 16 | 33 | 1 | 1 | 4 |
| collisions et attaques (`$A0`, `$88-$9C`, `$C0-$CF`, `$E6`, `$67`) | 71 | 27 | 6 | 2 | 5 | 23 | 4 | 0 | 4 |
| invulnérabilités et minuteries (`$250-$25F`, `$23F`, `$D6`) | 59 | 20 | 3 | 6 | 4 | 23 | 1 | 0 | 2 |
| jauge de super (`$11E`, `$115`, `$120/$121`) | 54 | 7 | 4 | 3 | 15 | 21 | 2 | 2 | 0 |
| adversaire et objets (A4) | 34 | 10 | 2 | 4 | 2 | 16 | 0 | 0 | 0 |
| IA (`$200-$22F`) | 20 | 3 | 0 | 1 | 6 | 4 | 0 | 0 | 6 |
| vie / dégâts (`$50-$53`) | 19 | 3 | 1 | 2 | 0 | 12 | 0 | 0 | 1 |
| ism (`$132`) | 18 | 2 | 0 | 1 | 9 | 4 | 1 | 0 | 1 |
| palette / affichage | 10 | 4 | 1 | 1 | 1 | 2 | 0 | 0 | 1 |
| étourdissement (`$2CB-$2CF`) | 10 | 0 | 1 | 2 | 1 | 5 | 0 | 0 | 1 |
| garde (`$24B-$24E`, `$118`, `$32F`, `$297`) | 9 | 1 | 1 | 0 | 2 | 5 | 0 | 0 | 0 |

**Répartition par perso** (code des persos, 1 004 tests) : Ryu 95, Bison 74, Ken 73, Akuma 71, Dan 58, Zangief 55,
Dhalsim 52, Charlie 49, Chun-Li 48, Guy 44, Sagat 42, Shin Akuma/variantes 41, Adon 38, Rolento 36, Rose 35,
Cammy 34, Sodom 30, Birdie 29, Gen 24, Sakura 22, Balrog 12, Blanka 12, Vega 12, Honda 8, Guile 7,
Fei-Long, Dee Jay, T.Hawk 1.
⟹ Les tests suivent exactement **les persos présents dans plusieurs versions**. Les persos ZERO 3 seuls n'en ont
que quelques-uns, venus des chemins communs.

**Bornes du code par perso dans ro9** (fichier, d'après les 13 tables de code) :

| perso | début | perso | début | perso | début |
|---|---|---|---|---|---|
| Ryu | `0xAC350` | Ken | `0xC2D80` | Akuma | `0xD25F0` |
| Charlie | `0xE8FA0` | Chun-Li | `0xF6500` | Adon | `0x104DB0` |
| Sodom | `0x111E90` | Guy | `0x120110` | Birdie | `0x131510` |
| Rose | `0x13EDB0` | Bison | `0x14E8D0` | Sagat | `0x15EF30` |
| Dan | `0x16BE10` | Sakura | `0x17C9B0` | Rolento | `0x18C990` |
| Dhalsim | `0x1A0BC0` | Zangief | `0x1B3070` | Gen | `0x1C6D30` |
| Balrog | `0x1DC5D0` | Cammy | `0x1E5000` | Honda | `0x1F84B0` |
| Blanka | `0x204B60` | R.Mika | `0x212600` | Cody | `0x225320` |
| Vega | `0x235170` | Karin | `0x2445C0` | Juli | `0x24EC80` |
| Juni | `0x25E860` | Guile | `0x2716F0` | Fei-Long | `0x279BE0` |
| Dee Jay | `0x285770` | T.Hawk | `0x28DC20` | Shin Akuma, `$12`, `$14` (suppléments) | `0x295C50`–`0x2A0000` |

**Exemples** :
- custom combo : `0x2D1F68…0x2D28C8` (§4) ;
- gardes : `0x2C6E7C` (garde auto selon ZERO) ;
- jauges : `0x3B74D0` (jauge affichée selon la version) ;
- ism / secret : `0x2A2404` (l'init de manche passe par `0x6A71D4` sauf si `$EC` ou X-ism) ;
- animation : `0x652E0` (sélecteur à 4 `LEA`, CARTE §2.3) ;
- physique : `0x2F00EC`, `0x305FA4` (projectiles : vitesses `T_5C3BF0` / `T_5C4C50` selon le bit 7) ;
- moteur de coups : `0x4DF1C` / `0x4DF4C` (bits 4 et 3 sur la contre-attaque `$C7`).

**Bit 7** : surtout la physique des projectiles (`0x2EF040`, 13 tests, nouvelle), les supers et la marche (`0x2BB310`).

Les routines du moteur les plus riches en tests (`btst_d3.json`) :

| routine | tests | sujet |
|---|---|---|
| `0x2EF040` (nouvelle) | 13 | projectiles, ism, bit 7 |
| `0x3B67E0` (nouvelle) | 8 | collisions |
| `0x2BB310` (homologue de `$2AB04`) | 7 | |
| `0x2F5A80` | 7 | |
| `0x3B7320` (nouvelle) | 7 | jauges |
| `0x305D10` | 6 | |
| `0x2D1F10` (nouvelle) | 5 | custom combo |
| `0x2B7BF0`, `0x2B8520` | 5 chacune | |

---

## 3. Les tables par `$102` et la zone de données nouvelle

### 3.1 Inventaire (`ids_tables.py` → `tables_102.json` / `.tsv` ; `scan_tables102.py` → `scan_tables102.json`)

La recherche est exhaustive :
- on part de toute constante de données dont l'index dérive d'un `MOVE.B $102/$116(An),Dk`, avec suivi du registre ;
- on ajoute les lectures natives (`0x5AF1B0`, `0x5AF2B0`, `0x5AF420`) et les tables atteintes par `$2D0/$2D4`.

Le compte de « 30 » de la carte ne retenait que la forme `MOVE.B $102 ; LEA ; (A0,Dk)`. Les homologues ro3 viennent
de `tables_homologues.py`, par les sites, ro5 → ro9 puis ro3 → ro9.

| exéc. | fichier | élt | n | rôle | homologue ro3 (fichier) |
|---|---|---|---|---|---|
| `0x5C5300` | `0x3D5300` | 1 | 128 | perso de base → `$116` | nouvelle |
| `0x5C2490` | `0x3D2490` | 1 | 128 | drapeaux → `$117` / `$D3` | nouvelle |
| `0x5AF420` | `0x3BF420` | 1 | 128 | id de chargement natif | `0x3AC050` |
| `0x5B5C30` | `0x3C5C30` | 1 | 128 | nombre de couleurs (modulo de `$128`) | ? |
| `0x5C5550` | `0x3D5550` | 1 | 128 | masque `AND` de `$128` | ? |
| `0x5C2410` | `0x3D2410` | 1 | 128 | n° d'animation (fin de manche au temps ?) | ? |
| `0x5AF1B0` | `0x3BF1B0` | 2 | 128 | banque de sprites | `0x3AC0B0` |
| `0x5AF2B0` | `0x3BF2B0` | 2 | 128 | fichier MOMO | `0x3AC130` |
| `0x6A54A0` | `0x4B54A0` | 2 | 128 | décalages → octet par coup normal | `0x48D050` |
| `0x6A5618` | `0x4B5618` | 2 | 128 | décalages → masque par normal (`$371`) | `0x48D0D8` |
| `0x666800` | `0x476800` | 2 | 128 | IA, tirage | `0x6593C0` |
| `0x6669CC` | `0x4769CC` | 2 | 128 | → `$120(A5)` | `0x67D4CC` |
| `0x672590` | `0x482590` | 2 | 128 | palettes (3ᵉ table) | `0x46F950` |
| `0x6A57D4` | `0x4B57D4` | 4 | 128 | normaux → `$23F` / `$292` | `0x48D178` |
| `0x6A59D4` … `0x6A69D4` (pas `0x200`) | `0x4B59D4`… | 4 | 128 | **CODE** : normaux, spéciaux 1 et 2, état 4 ×2, état 8, état `$0A` (commun), intro `$0E`, état `$10` | `0x48D1F8`…`0x48D5F8` |
| `0x6A6BD4` | `0x4B6BD4` | 4 | 128 | géométrie : 3 ptr (ism A +0, X +4, V +8) → en-tête → `$90…$A0` | `0x48D678` |
| `0x6A6DD4` | `0x4B6DD4` | 4 | 128 | jeux de boîtes → `$88` | `0x48D6F8` |
| `0x6A6FD4` | `0x4B6FD4` | 4 | 128 | → `$C0` | `0x48D778` |
| `0x6A71D4` | `0x4B71D4` | 4 | 128 | **CODE** init de manche | `0x48D7F8` |
| `0x6A7494` / `0x6A7694` / `0x6A7894` | | 4 | 128 | **CODE** commandes, prise au sol, prise aérienne | `0x48D8F8` / `0x48D978` / `0x48D9F8` |
| `0x6A7A94` | `0x4B7A94` | 4 | 128 | animations : 12 ptr (ism A +0, X +16, V +32) → `$2B0`, `$2B8`, `$2B4`, `$2BC` | `0x48DA78` |
| `0x6A7C94` | `0x4B7C94` | 4 | 48 | animations si `$F0 < 0` (mode `$15E = $81`) | nouvelle |
| `0x6A7D54` | `0x4B7D54` | 4 | 48 | animations si `$123 = 2` (`$122 = $80`) | nouvelle |
| `0x6A7E14` | `0x4B7E14` | 8 | 128 | vitesses de marche via `$2D0` (ism A et versions anciennes) | `0x48DAF8` |
| `0x6A8614` | `0x4B8614` | 64 | 128 | sauts via `$2D4` | `0x48DDF8` |
| `0x6AD614` | `0x4BD614` | 4 | 128 | **CODE** IA : lancement d'un spécial | `0x48FA78` |
| `0x6AD814` / `0x6ADA14` / `0x6ADC14` / `0x6ADE14` | | 4 | 128 | IA : scripts `$204`, variante, `$C6`, `$21F` | `0x48FAF8`… |
| `0x6AE614` | `0x4BE614` | 4 | 128 | sons par pas → `$E6` | `0x48FE78` |
| `0x6AE814` | `0x4BE814` | 4 | 128 | effets liés au pas → `$264` | `0x48FEF8` |
| **`0x6AF640`** | `0x4BF640` | 1 | **40** | index → `T_5C1550` (après garde brisée, `0x2AD130`) | `0x48FFC0` |
| **`0x6AF668`** | `0x4BF668` | 1 | **40** | index → `T_5C1590` (`0x2ADF40`) | `0x48FFE0` |
| **`0x6AF6B8`** | `0x4BF6B8` | 1 | **40** | octet retiré de `$2CB` (récupération d'étourdissement, `0x2B1C80`) | `0x490020` |

⚠ **Débordements probables (bogues d'Hyper)** :
- **`0x6AF640`, `0x6AF668`, `0x6AF6B8`** : 40 octets, lus par `$102` (`MOVE.B $102 ; LEA ; MOVE.B 0(A0,D0)`) dans
  `0x2AD130`, `0x2ADF40`, `0x2B1C80`, routines **identiques à Upper**.
  - Les ids `$30-$7F` lisent les tables suivantes, puis l'en-tête de géométrie par défaut `0x6AF6E0`.
  - Sur 77 ids anciens, 16 / 6 / 0 tombent sur la valeur du perso de base.
- **`0x5B61F0`** (table de rival, 40 entrées + 8 zéros, lue par `0xA5CA0`, identique à Upper) : même cas, mais c'est
  un vestige du mode arcade.

**Tables indexées par `$116`** (perso de base, 38-40 entrées, comme Upper) : 47 tables, liste dans
`scan_tables102.json`. Les principales :
- `0x6A73D4` positions de projection (4 sites), `0x6AE014` objets attachés, `0x6AE214` / `0x6AE414` effets ;
- `0x6AF5F0` → `$2CD` (stun_max, ÷2 si `$EB`) ; `0x6AF618` → `$24C` (guard_max, ±8 selon l'ism, −24 pour Cody V,
  ÷2 si `$EB`) ; `0x6AF690` → `$158` ; `0x6A5784` → `$A6` (demi-largeur) ;
- `0x6A8214` / `0x6A8354` / `0x6A8494` et `0x6AA614` / `0x6AB014` / `0x6ABA14` : marche et sauts **ZERO 3** ism V,
  ism X, et mode `$F0 < 0` (cf. §4.3) ;
- `0x5C1750` / `0x5C17F0` (`$116`, ou `$102−$40/−$60` selon le bit 5 en `0x2B8134`), `0x5C18C0-0x5C1900`,
  `0x5C19A0`, `0x5C2510`, `0x5C3800`, `0x63ACB4…0x63D7EC` (moteur de coups), `0x6AEA14` / `0x6AEE14`.

⚠ **Une troisième indexation existe** : le **rang dans la version**, `$102 − $40`, et encore `− $20` si ALPHA. On
l'a vue en `0x2B8134` (`T_5C17F0`) et `0x2C8480` (`0x6AF214`, 32 décalages u16). Ces tables ont 32 entrées par
version ZERO 2.

### 3.2 Format des enregistrements de la zone nouvelle (`formats.py`, `attaques.py`, `att40.py`)

On parcourt, pour les 113 ids, les blocs d'animation (`0x6A7A94`), leurs tables, les scripts de pas et les frames,
ainsi que la géométrie (`0x6A6BD4`) et ses sous-tables. Couverture de la zone `0x8AF140-0xB0F140` :
- 2,49 Mo, dont 48 % de zéros ;
- **79,6 % des octets non nuls** sont typés par ce parcours : pas 42 %, frames 29 %, attaques 7 %, tables
  d'animation 1,4 %, boîtes 1,3 % (sur la zone entière) ;
- le reste (≈ 263 Ko non nuls) est atteint par d'autres chemins : projectiles et objets des `LEA` du code
  (CARTE §2.3), effets…

| niveau | format (numérotation PS2) | SFA3 / Upper | Hyper, versions anciennes : constat |
|---|---|---|---|
| bloc d'animation | 12 × u32 : ism A, X, V × (`$2B0`, `$2B8`, `$2B4`, `$2BC`) | idem | ZERO : les 3 ism visent les mêmes 4 tables. Tables en zone nouvelle : ZERO 144/156, ZERO 2 300/384, ALPHA 372/384 |
| table d'animation | u16 décalages relatifs au début de la table, index = n° d'animation ; tables d'un perso contiguës | idem | ZERO 11 943 entrées, ZERO 2 33 722, ALPHA 34 208 ; entrées 0 = absentes ; quelques entrées non alignées sur 4 (fin de table mal bornée par l'heuristique) |
| **pas** (20 o, alignés sur 4) | `+0` durée (→ `$32`), `+1` drapeaux (bit 7 reprise suivie d'un pointeur, bit 6 fin avec enchaînement), `+2/+3` → `$34/$35`, `+4` ptr frame, `+8` jeu de boîtes, `+9` attaque, `+A` → `$C0` (son, `$C7`), `+B` décalage Y, `+D` propriété de garde, `+E` effet → `$264`, `+F` priorité, `+10` point de prise | idem (`max-pas-68k-natif.md`, `sfa3_support` ANIMATION) | ZERO 10 397 pas (1 667 reprises), ZERO 2 33 316, ALPHA 31 700 : **même format** |
| frame | u16 type ; type 2 = `T`, `n−1`, alignement, ptr fichier de positions, `n × (code, attr)` | idem (`FRAMES-Anthology.md`) | type 2 = 99,97 % (ZERO 10 282 / 10 285) ; `T` = Σ(l×h) exact 100 % ; **ptr de positions tous dans `0xC80000-0xD0FFFF`** (fichier e547 en `$C84000`) |
| en-tête de géométrie | 5 × u16 relatifs → `$90`, `$94`, `$98` (corps, 8 o), `$9C` (poussée, 8 o), `$A0` (attaques) | idem | ZERO 1 524 / 1 350 / 855 / 348 boîtes, etc. ⚠ L'en-tête ZERO 3 de Ryu d'Hyper a **plus de boîtes de corps** qu'Upper (`[10,922,1706,2298,2434]` contre `[10,530,1042,1426,1514]`) |
| boîte de corps | 8 o : x, y, rx, ry (s16 LE) | idem | idem ; lecteurs `idx×8` (`0x41604`…) |
| **attaque** | **40 octets dans Hyper** : `+0..7` boîte (x, y, rx, ry), `+8` puissance, `+9` recul, `+A` vecteur, `+B` direction, `+C` étourdissement, `+D` mouvement, `+E` touche, `+F` son, `+10` arrêt, `+11` jauge, `+12` dégâts en garde, `+14` effet, `+15` garde, `+16` icône, `+17` finish, `+18` ajustement, `+19` désactivation, `+1B` jongle, `+1C` temps au sol, **`+20..+27` nouveaux** | **32 octets** (ro3 et ro5 : `LSL.W #5`) | ro9 : `idx×5×8` (`0x80950-0x8096C`, 15 sites `×40`). Ryu ZERO 3 : les 32 premiers octets sont ceux d'Upper, `+$20..+$27` = 0 |

Les 8 octets ajoutés d'Hyper (`attaques.json`, enregistrements non vides) :

| octet | ZERO 3 | ZERO | ZERO 2 | ALPHA | lu par (fichier) |
|---|---|---|---|---|---|
| `+$20` | 0 (98 %) | `2` (97 %) | **`$82`** (99 %) | **`$C2`** (84 %) | `0x413CC` (`TST` / `BPL` → bit 7 = famille ZERO 2), `0x42FA4` (→ `$328` de la victime), `0x4346C`, `0x2D6D70` (`BEQ` : choix `0x4F760` / `0x4F3D0`), `0x4CDD0` (→ `$2CE`) |
| `+$21` | 0 | 2/1/0/4 | 2/1/0/4 | 2/0/1/4 | ? |
| `+$22` | 0 | 0, 2, 3, 9 | 0, `$0D`, 2, 3 | idem | ? |
| `+$23` | 0 | 0 | 0, 2, 6, 4 | idem | `0x41540` (comparé à un compteur `$280+$5A` de la victime) |
| `+$24` | 0 | 0 | **`$50-$52`** | `$50-$52` | `0x432A0` (→ `$29F` de la victime à la place de `+$0A`, si `+$20 < 0` et `$3E`) |
| `+$25…$27` | 0 | rares | 3 à 10 | idem | ? |

Les champs `+$08..+$1F` gardent les noms de `sfa3_support.lua`, mais leurs **distributions diffèrent** selon la
version : ZERO / ZERO 2 ont « vecteur » ≈ 76-81 (contre 12 en ZERO 3) et « mouvement » ≈ 48-52 (contre 15). Les
données anciennes réutilisent ces champs avec d'**autres plages de valeurs** : nouvelles trajectoires et réactions.
**À confirmer** en lisant les consommateurs.

### 3.3 Sélecteurs par version (rappel de CARTE §2.3)

32 routines font des `LEA` vers la zone nouvelle avec au moins 2 `BTST $D3`. Elles servent aux objets et projectiles,
avec 4 adresses (ZERO 3, ZERO, ZERO 2, ALPHA) et parfois `CMPI.B #$44/$64,$102(A4)` (Chun-Li). Exemples :
`0x652E0`, `0x659D0`, `0x67470`, `0x677D0` et les objets `0x2EF040`, `0x305D10`. Ceux-ci posent aussi `$60` et `$88`
**en dur** selon le bit 7 : `#$66AAC8` / `#$66B394`, `#$670A98` / `#$670BCC` / `#$B0D4F0`.

---

## 4. Systèmes de jeu par version : où le code choisit

### 4.1 Écran de mode ZERO 3 et champs de mode (`0x31B890`, apparentée à `$23D02`)

Le curseur `$5D` vaut 0..3 en visible. **Start le fait basculer vers 4..7** (navigation `T_5C54C0`, +`$18`) ; des
lignes particulières existent pour `$102 ≥ $24` et pour certains `$116`.

| curseur | champs posés | lus en combat (`0x2A1630`, nouvelle) |
|---|---|---|
| 0 | rien | — |
| 1 | `$15A = 1` | `$EC` (ex. `0x2A2404` : pas d'init de perso spéciale) |
| 2 | `$131 = 1` | `$EB` : **garde (`$24C`) et étourdissement (`$2CD`) divisés par 2** (`0x2C6F18`, `0x2C71F0`) |
| 3 | `$15E = 1`, `$132 = −1` (X-ism imposé) | `$F0 = 1` |
| 4 (Start + 3) | `$122 = $80`, `$132 = 0` | `$123 = 2` (`0xA5F40`, routine `$BC06` reprise) → animations `0x6A7D54`, jauge exigée `$90` (`0x2DA6F4`) |
| 5 (Start + 1) | `$122 = 2`, `$132 = −1` | `$123 = 3` |
| 6 (Start + 0) | `$122 = $82`, `$132 = 0` | `$123 = 4` |
| 7 (Start + 2) | `$15E = $81`, `$132 = −1` | `$F0 < 0` ⟹ **`$D3` reçoit les bits 3 et 7**, `$B5 = 1`, animations `0x6A7C94`, marche et sauts `0x6A8494` / `0x6ABA14` |

Les mêmes champs (`$131`, `$15E`, `$122`) sont posés par les codes secrets de l'arcade (`port_202B70`, homologue
`0x991A0`). Ce sont les **modes cachés de SFA3** (MAZI, SAIKYO, CLASSIC…). **Le libellé de chaque curseur reste à
lire à l'écran.**

### 4.2 Custom combo, V-ism et jauges

- **Activation** (`0x2D1F10`, nouvelle, rend −1 si activé) :
  - ZERO, bit 6 ou EX → refus ;
  - ZERO 3 → `$132 = +1` (V-ism), `$11E ≥ $48`, appui `$11/$22/$44` (P+K de même force) ;
  - ZERO 2 → `$11E ≥ $30`, puis combinaison de `$379 & $77` (2P+1K / 2K+1P, via table) ;
  - ALPHA (bit 2) → `$11E ≥ $30` et `($378|$37A) & $4400 = $4400`.
- **Pendant le CC** : `$B9` (cc_flg) testé par les bits 1 et 4 (`0x47B10`, `0x2A5CE8`, `0x2C8738` : vidange de
  `$11E` sauf si `$C32C(A5)` bit 1 ou 4).
- **Seuil de super** : `0x2DA6F4`.
  - `$90` si `$123 ≥ 2` ;
  - sinon `$30` hors ZERO 3 (`BTST #4`) ou en ism A ;
  - en ZERO 3, X-ism → `$90` ;
  - en ZERO 3, V-ism → `$48`.
- **Affichage de la jauge** (`0x3B7320`, nouvelle) :
  - rien si ZERO 3 ou EX : le HUD Upper reste ;
  - sinon jauge ancienne, avec un graphisme ZERO à part (`0xB66A30`) ;
  - tient compte de `$118` (AUTO).

### 4.3 Physique, garde, étourdissement (`0x2C6BE0`, init de combat)

- `$2CD` (stun_max) = `0x6AF5F0[$116]`, ÷2 si `$EB`.
- `$24C` (guard_max) = `0x6AF618[$116]` ±8 selon l'ism (−24 pour Cody V), ÷2 si `$EB`.
- `$158` = `0x6AF690[$116]` ; `$A6` = `0x6A5784[$116]`.
- **Marche et sauts** :
  - `$F0 < 0` → tables `0x6A8494` / `0x6ABA14` (40 entrées) ;
  - sinon `0x6A7E14` / `0x6A8614` (128 entrées, par `$102`). C'est le cas des versions anciennes et de l'ism A en
    ZERO 3 ;
  - ZERO 3 X → `0x6A8354` / `0x6AB014` ;
  - ZERO 3 V → `0x6A8214` / `0x6AA614`.
- **Garde automatique** : `$32F` est remis en service par Hyper. Upper l'avait supprimé (ECARTS §8.1).
  - `$32F = 0`, ou `$FF` si `$118` (AUTO choisi), ou **`$0A` si ZERO** ;
  - testé en `0x2BB538` (bit 3) et `0x56734`.
- **Récupération de garde et d'étourdissement** : `0x2AD130`, `0x2ADF40`, `0x2B1C80`. Tables à 40 entrées lues par
  `$102` (débordement, §3.1).

### 4.4 Autres mécaniques repérées

- **Contre-attaque / alpha counter** (`$C7`, `0x4DF1C`) : bits 4 et 3.
- **Provocation** (`0x2D29F0`, `provocation_test_start`) : bits 6, 3 et 4.
- **Init de manche** (`0x2A1630`) :
  - EX → `JSR 0x2A2390` ;
  - sinon init normale.
- **Init spéciale du perso** (`0x2A23C0`) : `$BC = 1` et appel de `0x6A71D4` **sauf** si le bit 3, `$EC` ou X-ism.
- **Projectiles** (`0x2EF040`, `0x2F10D0`, `0x305D10`) : vitesses, géométrie et durée de vie selon les bits 0, 2, 5
  et 7.
- **IA** (`0x7C1A0`, `0x80D50`, `0x85724`) : bits 3 et 7.

---

## 5. Variables A5, RAM et champs propres à Hyper

### 5.1 Variables A5 (`vars_hyper.py` → `vars_hyper.json` / `.tsv`, d'après `carto_ro9/vars_a5.py`)

**Moins de variables** : 437 déplacements A5 distincts dans ro9, contre 613 dans Upper et 609 dans SFA3. Les modes
ARCADE, SURVIVAL et DRAMATIC ont été retirés.

Déplacements absents d'Upper :

| A5 | CPS2 | accès / écritures | lu ou écrit par | remarque |
|---|---|---|---|---|
| `$C178` | `$FF4178` | 11 / 5 | `0x96690`, `0x60570`, `0x61180` | variante de décor (4 × 4, CARTE §3) |
| `$C3A1`, `$C3A4`, `$C3AA-$C3AD` | `$FF43A1…` | 11 / 7… | `0x3B47D0`, `0x3B45E0`, `0x3B2FC0`, `0x2F8F0` | bloc décalé (ci-dessous) |
| `$C3B0`, `$C3B2`, `$C3B4-$C3B8` | | 2-8 | `0x388AC0`, `0x389700`, `0x98590`, `0x28C30` (nouvelles) | ? |
| `$C3BA`, `$C3BB`, `$C3BC` | | 5-6 lectures | `0x29140…0x293E0` (natives du portage) | réglages lus par le portage ? |

**Décalages ro3 → ro9 différents de ro3 → ro5** :
- bloc `$C190-$C19B` (ro3) : **+`$212`** dans ro9 (`$C3A2-$C3AD`), contre +`$202` dans Upper ;
- `$C175` / `$C1A7` → `$C372`, contre `$C373` dans Upper ;
- `$6EBA` → `$6EB8` ; `$6E8C` → `$6E88` (votes faibles).

Les règles +`$200` (`$C0xx-$C1xx`) et `$BE48 → $C0BC` de la carte restent valables.

Variables du mode (rappel) :
- `$C200` (`$FF4200`) : mode (1 VERSUS, 4 TRAINING, 7) ;
- `$C201` : curseur du menu ;
- `$80A9` (`$FF80A9`) : mode de jeu ;
- `$C30E(A5,joueur)` : dernier perso choisi ;
- `$C32C` (bits 1 et 4) : drapeaux qui suspendent la vidange de la jauge pendant le CC.

### 5.2 Zones RAM (`carto_ro9/zones_ram.py`, relancé)

Ro9 utilise 40 constantes sous la RAM, toutes différentes de celles de ro3. Constantes propres à ro9 :
- 5 en RAM de travail (`+0x0`, `+0x2B`, `+0x40`, `+0x42`, `+0xEC`) ;
- 11 en vidéo CPS2 (`+0x25000…0x2E400`, dont la zone palettes `+0x2C29C…0x2C38E`, utilisée par la jauge
  `0x3B7320`).

QSound (24/25) et registres émulés (43/43) sont communs.

### 5.3 Champs de structure (A6) propres à Hyper (`champs_a6.py` → `champs_a6.tsv`)

| champ | ro9 (écritures) | Upper | rôle |
|---|---|---|---|
| `$D3` | 1 278 (6) | 3 | drapeaux de version de travail |
| `$116` / `$117` | 132 / 28 (A6 seul) | 6 / 0 | perso de base / version |
| `$123` | 130 | 11 | ism étendu (§4.1), beaucoup plus testé |
| `$32F` | 9 (2) | 0 (8 dans SFA3) | garde automatique |
| `$B5`, `$B6`, `$B7`, `$B8` | 2, 8, 8, 1 | 0 | `$B5` = EX ou CLASSIC ; `$B6/$B7` décomptés dans `0x2A2B40` |
| `$EB`, `$EC`, `$F0` | | | copies de `$131`, `$15A`, `$15E` (modes) |
| `$F3-$FE` | `$FA` 28 (27), `$FC` 26… | 0 | **bloc neuf**, écrit dans le code des persos (`0xBD9B0`, `0xCF320`, `0xE6620`…) |
| `$69` | 15 (8) | 0 | ? |
| `$260`, `$261`, `$262` | 28, 40, 19 | 0 | code des persos : `$260 = 1`, `$261` compteur |
| `$292`, `$293` | 14, 21 | 0 / 4 | |
| `$2A2`, `$2A3`, `$318` | 3-4 | 0 | |

Champs d'Upper absents d'Hyper : `$7A-$7F`, `$105-$110`, `$134-$17C`, avec A6 = autre objet. Ce sont des objets
du mode arcade, de l'attraction et des fins, retirés d'Hyper.

Champs de mode et de sélection (joueur) : `$5D` (curseur de version ou de mode), `$118` (AUTO), `$122`, `$131`,
`$15A`, `$15E`, `$132`, `$11A/$11B` (entrées ; Start = bit 15).

---

## 6. Inconnues et points à vérifier

1. **Libellés de l'écran de mode** : quel curseur 0..7 correspond à NORMAL, MAZI, SAIKYO, CLASSIC et aux variantes
   Start (§4.1) ? Il faut aussi la sémantique exacte de `$122` (`$80/2/$82`), `$123 = 2/3/4`, `$15A`, `$131` et `$15E`.
   À vérifier par PINE/PCSX2 en lisant `$5D`, `$122`, `$123`, `$131`, `$15A`, `$15E` et `$D3`.
2. **Bit 6 de `$D3`** : jamais posé statiquement. Est-il posé par une native, un code de triche du portage ou un
   état sauvegardé ? Sinon, 16 branches mortes.
3. **EX ZERO 2 `$58` / `$59`** : présents dans la grille Start, mais leurs données sont celles par défaut. Défaut réel
   du jeu, ou choix bloqué ailleurs (droits, déblocage) ? Il faut aussi savoir si `$5A/$5B/$5C/$5E` sont
   atteignables.
4. **Octets `+$20..+$27` des attaques** : sens de `+$21`, `+$22`, `+$25…$27` ; `+$20` est une famille et des
   drapeaux, `+$24` vaut `$50-$52`. Sens aussi des champs `vecteur` et `mouvement` dans les données anciennes.
5. **Débordements** `0x6AF640`, `0x6AF668`, `0x6AF6B8` (récupérations de garde et d'étourdissement des versions
   anciennes) : bogue réel ou chemin jamais pris ? À observer : `$2CB` après une chute en ZERO.
6. **Nouveaux champs** `$F3-$FE`, `$260-$262`, `$69`, `$B6/$B7`, `$292`, `$2A2/$2A3`, `$318` : mécaniques propres aux
   versions anciennes (charge, enchaînements ZERO, chain combos ?), non identifiées.
7. **Tables d'octets** `0x5C2410` (n° d'animation), `0x5B5C30` / `0x5C5550` (couleurs) : rôle exact.
8. **20 % des octets non nuls de la zone nouvelle** ne sont pas typés (projectiles et objets atteints par des `LEA`).
9. **Ryu ZERO 3 d'Hyper** a plus de boîtes de corps qu'Upper : données ZERO 3 retouchées par Hyper ?
10. **Sujets du §2.3** : heuristique par champs. Les 98 « autre » et les tests du code des persos méritent une
    lecture au cas par cas (outil : `voir.py` / `ctx.py`).

---

## 7. Fichiers (`<workspace>/work/agent_hyper_index/`)

| fichier | contenu |
|---|---|
| `INDEX-HYPER.md` | ce rapport |
| `ids_102.json` / `.tsv` | 128 ids : version, base, nom, `$117`, banque, MOMO, id de chargement, grilles |
| `tables_102.json` / `.tsv` | 45 tables × 128 ids : valeur, zone (code / Upper / nouvelle), relation (propre, = ZERO 3 de base, défaut, partagée, débordement) |
| `scan_tables102.json` | recherche exhaustive des tables indexées par `$102` / `$116` (index, écart à la suivante, accès) |
| `tables_homologues.json` | 98 tables de combat ro3/ro5 → homologue ro9 |
| `btst_d3.tsv`, `btst_d3_sites.json`, `btst_d3.json`, `btst_d3_bilan.txt` | 1 445 tests classés |
| `formats.json`, `formats_couverture.tsv` | statistiques des pas, frames, boîtes ; typage de la zone nouvelle |
| `attaques.json` | champs des enregistrements d'attaque de 40 o par version |
| `vars_hyper.json` / `.tsv`, `champs_a6.tsv` | variables A5 et champs A6 propres à Hyper |

Scripts (interpréteur `<workspace>/venv/bin/python3`, `nice -n 19`) :
- `lib.py` (accès au module, aux caches de `carto_ro9`, aux symboles ro3) ;
- `voir.py VA` (routine traduite, JSR résolus), `ctx.py VA [av ap]`, `grep68.py REGEX [av ap] [mod]`,
  `ecritures.py [champs]` ;
- `ids_tables.py`, `scan_tables102.py`, `index_tables.py`, `tables_homologues.py` ;
- `btst_d3.py`, `formats.py`, `attaques.py`, `att40.py`, `vars_hyper.py`, `champs_a6.py`.
