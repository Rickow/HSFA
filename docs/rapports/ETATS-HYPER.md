# Hyper SFA (`ro9`) au fork `sfa3hx` : machine à états, menus, sélection des EX

Agent `agent_hyper_etats`, 2026-10-07. Tout est dans `<workspace>/work/agent_hyper_etats/`. Aucun fichier modifié
ailleurs, aucune ROM reconstruite : j'ai utilisé la construction du 7 octobre de `work/mame_ro9/` (lecture seule) et sa
`carte_image.txt`. Les MAME ont tous tourné en `nice -n 19`, avec `-nvram_directory` et `-cfg_directory` propres
(`essais/nv_<nom>`, `essais/cfg_<nom>`), jamais plus de 2 à la fois.

**Conventions.**
- Adresses MIPS : en **fichier** (comme la carte). Adresses 68K : celles de l'image du fork.
- Champs des joueurs : en **numérotation 68K**, celle de `carte_image.txt`. La PS2 et l'index statique
  (`agent_hyper_index/INDEX-HYPER.md`) numérotent l'octet `X^1`.
- Correspondance : 68K `$103` = PS2 `$102` (id étendu) ; `$117` = `$116` (perso de base) ; `$116` = `$117`
  (drapeaux) ; `$5C` = `$5D` (curseur) ; `$11A` = `$11A/$11B` (entrées) ; `$133` = `$132` (ism) ; `$123` = `$122` ;
  `$15B` = `$15A` ; `$130` = `$131` ; `$15F` = `$15E` ; `$D2` = `$D3`.
- Les variables A5 sont des mots : `A5+0` = `$FF8000`, etc.

## 0. En bref

**1. Les EX : trois mécanismes, tous vérifiés à l'image.**
- **(a) Colonne des versions.** Il faut **maintenir Start** au moment où l'on valide la version avec un bouton.
  - La routine `0x31AAA0` (68K `$079578`) teste `BTST #7,$11A(A6)`, c'est-à-dire le bit 15 de `$11A`, qui est Start.
  - Elle lit alors la grille secrète **`0x5C5420`** au lieu de `0x5C5380` : `$103 = grille[$117×4 + $5C]`.
  - On obtient ainsi les 7 EX ALPHA (`$75-$7C`), Shin Akuma (`$54/$74/$24`), Chun-Li SF2 (`$52/$72`), Sakura bis
    (`$5D/$7D`), EX Zangief et EX Dhalsim ZERO 2 (`$55/$56`), et **EX Bison et EX Sagat ZERO 2 (`$58/$59`)**.
- **(b) Persos à version unique.** Pour EX Balrog `$25`, Start doit être maintenu à la **validation du perso**
  (`0x31A048`).
- **(c) Écran de mode ZERO 3** (`0x31B890`). **Start maintenu + Gauche ou Droite** fait basculer le curseur `$5C`
  vers **4 sous-états cachés, un par mode**. C'est l'indication de l'utilisateur, et elle est exacte.
  - Libellés : NORMAL → 6 « S-ISM vert », MAZI → 5 « S-ISM bleu », CLASSIC → 4 « S-ISM rouge », SAIKYO → 7.
  - Le 7 n'a pas de libellé et donne l'EX ZERO 3 : `$D2` reçoit les bits 3 et 7. Il n'est permis qu'aux 12 persos
    de SF2 (et aux ids ≥ `$24`).
- **ZERO 2 EX `$58/$59`** : on les atteint en jeu normal, mais ils s'affichent **en morceaux**, car leurs 45 tables
  par `$102` sont celles de Ryu.
- **`$5A/$5B/$5C`** ne sont atteignables par aucun chemin : ni grille, ni table aléatoire.
- **`$12/$14`** ne sont pas des valeurs de `$103`. Ce sont les index de chargement de Chun-Li et Sodom ZERO 3 en
  **X-ism ou CLASSIC** (`$133 < 0`). Par ce chemin naturel, ils s'affichent correctement.

**2. Machine à états** : relevée par 20 traces du débogueur (une image par scène) et par les tables 68K
(§2, `essais/traces/scenes_vs.txt`).

**3. Deux défauts de traduction** trouvés au passage (§3) :
- la **scène de fin de match VERSUS** (`A5+4 = $E`, aiguilleur `0x2D550`) est absente : écran noir et `A5+8`
  augmente sans fin ;
- le gestionnaire TRAINING `0x3B4300` a perdu son aiguillage et ses tests.

**4. `tournee_hyper.lua`** enchaîne sélections et combats en VERSUS à 2 joueurs, par les seules entrées, avec des K.O.
forcés.
- Essai : 7 sélections, 14 manches, **0 exception**.
- La scène `$E` est contournée par l'option `CONTOURNE_E=1`, qui le signale au journal.

## 1. Sélection et EX

### 1.1 Entrées

Le mot `$11A` (et `$11C`, l'image précédente) est écrit par la couche manette :
- bits 0 à 3 : Droite, Gauche, Bas, Haut ;
- bits 8 à 10 et 12 à 14 : les 6 boutons (masque `$7700`) ;
- bit 15 : Start.

Les états testent les nouveaux appuis par `~$11C & $11A & $770C` (ou `$770F`).

**Piège du banc (roulette).** À chaque image de sélection, `0x316104` déplace le bit 15 vers l'octet `$D3` du joueur.
- Ce drapeau lance la **roulette aléatoire** de l'état perso (`0x319544`).
- Le bit 15 est ensuite reposé d'après `$62(A5)`, le START arcade.
- Sur PS2, le drapeau vient du bit `$0100` du moteur (natif `0x23D20`), distinct du START. Dans le banc, les deux
  viennent du même bouton : Start sur l'écran des persos fait tourner la roulette.
- Les scripts neutralisent ce drapeau (`NOROUL=1`, prise d'écriture sur `$FF84D2/$FF88D2`). À confirmer sur PS2 :
  quelle touche lance la roulette (Select ?).
- **Réglé dans le cœur FBNeo le 2026-10-16 (patch 11, `0007-HSFA-roulette-touche-piece.patch`)** : la roulette
  choisit un perso au hasard quand on **valide** avec le drapeau tenu (`$D3` = `$FF`). Le cœur écrit désormais `$D3`
  d'après la touche Pièce du joueur (Select de RetroPad, `CpsInp020[4 + j]`), et seulement sur la grille (phases
  2/2/4, état 0). Start reste celui du jeu : EX (Start tenu à la validation de la version ou du perso, EX Balrog),
  S-ISM (Start tenu + ← / →). Vérifié : Select tenu + bouton → perso au hasard ; Start tenu → perso choisi ;
  tournée de 151 VERSUS sans `HSFA_NOROUL` identique à celle avec.

### 1.2 Sous-états de sélection

Table `0x5C5620`, état en `$5(A6)`, sous-état en `$4(A6)`.

| `$5` | routine (MIPS / 68K) | rôle, variables | transition |
|---|---|---|---|
| 0 | `0x319160` / `$079126` (sous-états `0x3191D0`, `0x319430`, `0x31A660`) | **perso** : curseur X/Y = mots `$12/$16` (0..7, avec bouclage), grille 8×8 `0x5C5650` (`$3F` = traversé, `$FF` = mur, bits 6/7 = interdit à J1/J2, `$26-$29` = cases « ? ») ; aperçu de `$103` ; roulette si `$D3` ; validation : `0x321BA0` décode `$117/$116` ; perso à version unique (`0x5C5381 < 0`) : `$3D` bits 4/5, et avec **Start**, `$103 = 0x5C5420[$117×4]` | → 2 |
| 2 | `0x31A9A0` / `$079546` (`0x31AA10`, **`0x31AAA0`**, `0x31AFC0`) | **version** : `$5C` 0..3 (Haut/Bas), `$103 = 0x5C5380[$117×4 + $5C]`, cases `$FF` sautées ; validation : grille **`0x5C5420` si Start maintenu** ; ZERO 3 (`$103 < $30`) : bit 5 de `$15A`, pas de MANUAL/AUTO | → 4 |
| 4 | `0x31B1C0` / `$0796D8` (`0x31B2C0`, `0x31B560`) | **MANUAL / AUTO** : `$5C` 0/1 → `$119` ; versions anciennes : `0x31FB70` et `$15A \|= $0A` (pas d'écran de mode ni d'ism) | → 6 |
| 6 | `0x31B790` / `$0797A0` (**`0x31B890`**, `0x31C740`) | **mode ZERO 3** : `$5C` 0..7 (§1.4) ; si `$123` ou `$15F` ≠ 0 : bit 1 de `$15A` (ism imposé) | → 8 |
| 8 | `0x31C910` / `$079992` (`0x31CA20`, `0x31CFF0`) | **ism** : `$133` = −1 X, 0 A, +1 V (Haut/Bas, avec butées) | → A |
| A | `0x31D0C0` / `$079A76` (`0x31D260`, `0x31D5D0`) | **choix commun**, une fois par scène (`$12(A5)`) : `$13(A5)` 0/1 → `$117(A5) = 0x5B5BA0[$13 + $A2(A5)]` (0/6/8, sans doute la vitesse) ; sauté si `$A2(A5) < 3` (bit 2 de `$15A`, posé en `0x317050`) : jamais vu | → C |
| C | `0x31D6A0` / `$079B5E` | fini (mémorise le choix en `$C30E(A5,j)`, `$C31E`, `$C3AC`…) | — |

Remarques :
- Toutes les attentes ont une minuterie (`$3A(A6)` = `$258`, ou `$4B0` pour le perso) **seulement si
  `$C201 = 0`**. C'est le vestige ARCADE : `MODEFORCE=0` valide J2 tout seul.
- À l'entrée de la scène (`0x316EF8`), `$15A &= $3B` : les étapes déjà faites restent marquées.

### 1.3 Procédure EX exacte (banc ; PS2 : « Start » = START arcade, `$62`)

| EX | perso (grille) | version | entrées |
|---|---|---|---|
| EX ALPHA Ryu `$7B`, Ken `$7A`, Bison `$78`, Sagat `$79` | Ryu, Ken, Bison, Sagat | ALPHA (Bas ×2) | Start maintenu, puis bouton 1 |
| EX ALPHA Zangief `$75`, Dhalsim `$76` ; Sakura bis `$7D` | Zangief, Dhalsim, Sakura | ALPHA (Bas ×1 : leur colonne 0 est ZERO 2) | Start + bouton |
| Chun-Li `$7C` (Chun-Li ZERO en ALPHA) / `$72` (SF2, ALPHA) / `$52` (SF2, ZERO 2) | Chun-Li | ZERO / ALPHA / ZERO 2 | Start + bouton |
| Shin Akuma `$54` / `$74` / `$24` | Akuma | ZERO 2 / ALPHA / ZERO 3 | Start + bouton |
| EX ZERO 2 Bison `$58`, Sagat `$59` ; Zangief `$55`, Dhalsim `$56` ; Sakura `$5D` | — | ZERO 2 | Start + bouton |
| EX Balrog `$25` | Balrog (version unique) | — | Start maintenu à la validation du **perso** |
| EX ZERO 3 (`$D2` bits 3+7) | un des 12 persos de SF2 (`0x5C5510[$117] = 1`), ou id ≥ `$24` | ZERO 3, écran de mode | curseur sur SAIKYO, Start maintenu + Droite (ou Gauche) → curseur 7, puis bouton |

Persos de SF2 permis pour le curseur 7 : Ryu, Ken, Chun-Li, Bison, Sagat, Dhalsim, Zangief, Balrog, Honda, Blanka,
Vega, Guile.

Variables :
- le choix se fait dans `$103` ;
- `0x321BA0` pose `$117 = 0x5C5300[$103]` et `$116 = 0x5C2490[$103]` (`$0E` = ALPHA EX, `$2A` = ZERO 2 EX) ;
- `$D2 = $116` est recopié à l'initialisation du combat (`0x2C6C0C`). Si `$F1 < 0` (copie de `$15F = $81`),
  `BSET #3` et `BSET #7` sur `$D2`, et `$B4 = 1`.

Vérifié (essais `ex_*`, planches `ex_alpha_combat.png`, `ex_zero2_z3_combat.png`, `ex_vs.png`) :
- tous les ids attendus sont obtenus ;
- **lisibles** : `$7B`, `$7A`, `$72`, `$7C`, `$78`, `$79`, `$76`, `$75`, `$74`, `$7D`, `$52`, `$56`, `$55`, `$54`,
  `$5D`, `$24`, `$25`, et Bison / Guile / Ken en curseur 7 ;
- plaques sur l'écran VS : « ALPHA2G » pour les EX ALPHA, « ALPHA2 » pour ZERO 2 ;
- **en morceaux** : `$58` (Bison) et `$59` (Sagat).
  - Leurs 45 tables par id pointent sur Ryu `$00`, code compris (`0x6A59D4…` vidés).
  - C'est donc la donnée PS2 qui est en cause, pas le banc. À voir sur PCSX2 : bogue d'Hyper ou id détourné ailleurs ?
- **`$5A/$5B/$5C`** : absents des grilles `0x5C5380` et `0x5C5420`, et de la table aléatoire `0x5B5CD0` (qui
  contient `$54`, `$55`, `$56`, `$78-$7C`). Ils ne sont pas atteignables.

### 1.4 Écran de mode ZERO 3

Libellés relevés à l'image (`planches/libelles_modes.png`, `ecran_modes_curseurs.png`, `modes_caches_ryu.png`).

Navigation, table `0x5C54C0` :
- Haut / Bas cyclent seulement 0..3 ;
- Start + G/D (lignes +`$18`) : 0↔6, 1↔5, 2↔7, 3↔4 ;
- ligne +`$30` si `0x5C5510[$117] = 0` : 2 reste 2, et 7 donne 2.

| `$5C` | accès | champs posés (68K) | sélection | plaque VS / bas du HUD |
|---|---|---|---|---|
| 0 | visible | — | NORMAL | ism choisi (A-ISM…) / jauge ism |
| 1 | visible | `$15B = 1` | MAZI | ism / jauge, témoin « ON » à droite |
| 2 | visible | `$130 = 1` | SAIKYO | ism / jauge |
| 3 | visible | `$15F = 1`, `$133 = −1` | CLASSIC | « CLASSIC » / « CLASSIC » |
| 4 | Start + G/D depuis CLASSIC | `$123 = $80`, `$133 = 0` (→ `$122 = 2`) | aucune flèche | « **S-ISM** » rouge / jauge « SUPER », « CHARGE OK » |
| 5 | depuis MAZI | `$123 = 2`, `$133 = −1` (→ `$122 = 3`) | aucune flèche | « **S-ISM** » bleu / SUPER |
| 6 | depuis NORMAL | `$123 = $82`, `$133 = 0` (→ `$122 = 4`) | aucune flèche | « **S-ISM** » vert / SUPER |
| 7 | depuis SAIKYO (persos de SF2) | `$15F = $81`, `$133 = −1` | aucune flèche | **aucune plaque**, ni jauge ; `$D2` = `$98` (EX ZERO 3) |

- Les curseurs 3 à 7 sautent l'écran d'ism.
- Le libellé de l'écran VS vient de `0x333DCC` : `T_5C64A8[11] = $FF`, c'est-à-dire aucun libellé.
- `$15C = $80` si Bison ZERO 3 est en curseur 4 (`0x2A1FD4`) : effet visible non identifié.

## 2. Machine à états

### 2.1 Phases et scènes

Une tâche par phase, chacune aiguillant sur `A5+0`. La sélection est au §1.2.

| `A5+0 / 4 / 8 / C` | scène | aiguilleur (MIPS / 68K) | cible (MIPS / 68K) | transitions observées |
|---|---|---|---|---|
| 0 → 2 → 6 → 8 → 0 | amorçage | tâche système `0x61B84` / `$0093E4` (`T_5B41C0`) | 0 `0x61BF0` / `$00940C`, 2 et 8 `0x61C90` / `$009432` (`A5+4` : `T_5B41D8`), 4 et A `0x61F20` / `$0094B4` | images 1-52 |
| **6** | **titre** | idem, 6 → `0x62390` / `$009594` | `A5+8` : 0 `0x62430` (init., `$E = 300` jamais lu), 2 `0x624F0` (défilement ; Start → menu) | attend Start sans limite (pas d'attraction) |
| **4** | **menu des modes** | tâche menu `0x6299C` / `$0096BC` (`T_5B4230`) | 0 `0x62A10`, 2 `0x62AB0`, 4 `0x62B30` / `$00971E` (curseur `$C201`, navigation `0x5B41F0/0x5B4200`, lanceurs `0x5B4210`) | B → lanceur ; retour seul au titre après ~850 images |
| 4 (lanceurs) | VERSUS / ARCADE / SURVIVAL / DRAMATIC | entrées 0..3 → `0x62FF0` / `$00981E` | `$A9` = 3 (2 joueurs) ou 1 | → `A5+0 = 2` |
| 4 | TRAINING | entrée 4 → `0x63170` / `$009866` | | → `A5+0 = 2` |
| 4 | OPTION | entrée 5 → `0x63280` / `$009888` | tâche native `0x24AB0` (non émulée : rien ne se passe) ; **avec le bouton `$0400` de `$C214` maintenu (B3 au banc) : tâche `0x3BCCC0` = générique « STAFF »** (`A5+8 = 2`, `A5+C` 6→8→A→C→E, ~3 000 images, puis `A5+0 = 0`, retour au menu) | `planches/generique_cache_option.png` |
| 4 | EXIT | entrée 6 → `0x63430` / `$0098DE` | moteur `0x1CAC80` (sortie vers l'Anthology, talon au banc) | reste au menu |
| 2 / — | jeu | tâche jeu `0x952F8` / `$00FAC8` (`T_5B5E70`) | 0 `0x95340` (init.), 2 `0x962C0` / `$00FDA6` (`A5+4` : `T_5B5E80`), 8 `0x96330` | |
| 2 / 0 | init. du mode | `0x96330` / `$00FDC2` | init. des joueurs `0x95C84` | → `A5+4 = 2` |
| 2 / **2** | **sélection** | `0x96590` / `$00FE22` → `0x316418` / `$0789D2` (`A5+8` : `T_5C55D0`) | 0 `0x316480` / `$0789F2` (init., `A5+C` 0..6) ; 2 `0x3169B0` ; **4 `0x3182A0` / `$078F4E`** (sélection, joueurs §1.2) ; 8 `0x3204D0` / `$07A296` (attente) ; **A `0x3205D0` / `$07A2C4` = HANDICAP** (VERSUS ; `A5+C` : `0x320690`, `0x320B10`, `0x321220`, `0x321A20`) ; C `0x3219B0` / `$07A58E` ; 6 `0x318B80` / `$079024` (fin → VS) | 4 → 8 → A → C → 6 → `A5+4 = 4` |
| 2 / **4** | **VS et combat** | `0x96620` / `$00FE34` (`A5+8` : `T_5B5EA0`) | 0 `0x96690` ; 2 `0x9A2C0` / `$0107DC` ; **4 `0x9A390` / `$0107F8` = écran VS** (`A5+C` : 0 `0x9A400`, 2 `0x9A430`, 4 `0x9A570`) ; **6 `0x9A680` / `$0108A8` = combat** ; **8 `0xA08A0` / `$0114E8` = fin de match** ; A `0xA09F0` ; 10 `0x974D0` | 0 → 2 → 4 (~400 images) → 6 → 8 → `A5+4 = $E` |
| 2 / 4 / **6** / `A5+C` | manche | `T_5B5F40` ($0108B6) | 0 `0x9A980` / `$010948` (init. manche) ; 2 `0x9B350` / `$010B08` (ROUND n) ; **4 `0x9B7E0` / `$010BDC` (combat ; `A5+10` : `T_5B5F88`)** ; **6 `0x9C940` / `$010D94` (K.O. / fin de manche ; en TRAINING `JSR 0x3B4300`)** ; 8 `0x9E920` / `$0110A2` (pose de victoire) ; A `0x9F300` / `$0111EE` (« WIN », MAX COMBO, WINS) ; C `0x9FD10` ; E `0x9FDB0` (manche suivante ou fin) | VERSUS : 4 → 6 → 8 → A → C → E → 0 (manche suivante) ou `A5+8 = 8` ; TRAINING : reste à 6 après un K.O. |
| 2 / **$E** | **fin de match VERSUS** (aussi en ARCADE) | `0x965F0` / `$00FE2E` → **`0x2D550`** (aiguilleur `sll 2`, table `0x5B2CD0` : `0x2D5A0`, `0x2D620`, `0x2D710` affichage portraits `$C30E/$C30F` et victoires `$C30C/$C30D`, `0x2DA40`, `0x2DA60`, `0x2DA90` menu de curseur `$C316`, qui remet `A5+0..+14` à 0 → titre, ou reprend la sélection) | **non traduit** (§3) | écran noir, `A5+8` +2 toutes les 7 images |
| 2 / C, 6, 8, A | vestiges SFA3 | `0xA0DD0` ; 6/8/A = `RTS` | | jamais atteints |

### 2.2 Vestiges (curseur `$FF4201` forcé)

- **0 (ARCADE)** : comme VERSUS, mais J2 n'est pas rejoint ; il est validé par les minuteries (`$C201 = 0`, ~600 images
  par étape, choix par défaut Ken ZERO `$31`). Combat, puis scène `$E` (`essais/tm0.log`).
- **2 et 3** : comme VERSUS ; seul, J2 attend un 2ᵉ joueur.
- **Continue, fins, résultats d'arcade** : aucune scène atteignable (lanceurs redirigés vers `0x62FF0`).

### 2.3 Variables utiles

- `$FF80A9` : joueurs actifs (bit 0 J1, bit 1 J2 ; 3 = VERSUS, 1 = TRAINING).
- `$FF4201` : curseur du menu.
- `$FF4214` : entrées du portage.
- Joueurs `$FF8400 / $FF8800` :
  - `+1` actif ; `+5/+4` état / sous-état ;
  - `+$50/$52` vie (`$90`) ;
  - `$12` : position X en combat, curseur X en sélection.
- Victoires VERSUS : `$C30C/$C30D(A5)` (« n WINS »).

## 3. Défauts de traduction relevés (non corrigés : hors de mon dossier)

1. **`0x2D550` absent de l'image 68K.**
   - Le site `0x96600` (`jalr` vers une constante) est traduit en `JMP $2018`, qui est le **gestionnaire 0**
     (`0x2D5B8`, `ADDQ.W #2,$8(A5)`).
   - L'aiguilleur `lh 8(A5) ; sra 1 ; sll 2 ; lw 0x5B2CD0(v) ; jalr` (CARTE-ro9 §5 : « aiguillage `sll 2` »,
     `0x2D570`) n'a donc aucune instruction 68K.
   - Effet : la fin de match VERSUS ne s'affiche jamais, et on ne revient ni à la sélection ni au titre.
2. **`0x3B4300`** (TRAINING, appelé par l'état de manche 6) a perdu plusieurs instructions :
   - le test `lb $C320 ; bne` (échange J1/J2) ;
   - l'aiguillage `$C325` (`sll 2`, table `0x5DB180`, 2ᵉ site `0x3B439C` de la CARTE) ;
   - les tests `lb $C326/$C327 ; beq` devant les `BCLR/BSET $C32D` : ceux-ci deviennent inconditionnels.
3. **`0x2C440`** (appelé par `0x9C940`) : les tests sur les variables du portage (`0xB67260+$C/$D`) et sur `$8A/$8B`
   ont disparu ; le 68K commence à `BTST #0,$AD(A5)`.

Ce code ajouté d'Hyper est de style « non optimisé » : cadre `sd ra`, `lb v0 ; beq v0,zero` sans case-registre, et
`jalr` vers une table de longs. `outils/audit_cibles.py` liste les cibles d'appel sans ligne de carte
(`essais/audit_cibles.txt`, 483 cibles). La plupart sont bénignes (prologue ou idiome CMP fondu) ; les trois ci-dessus
sont vérifiées à la main.

## 4. `tournee_hyper.lua`

Lancement : `tournee.sh <nom>`, avec les variables `LISTE`, `MODEJEU`, `NF`, `SNAPM`, `CONTOURNE_E`, `MODEFORCE`,
`INPUTS`, `SNAPS`. Le script :
- passe le titre et le menu par les entrées (VERSUS 1 / TRAINING 4 ; `MODEFORCE` pour 0/2/3) ;
- pilote chaque joueur selon son état `$5`, par les entrées seulement :
  - chemin du curseur calculé avec les règles du jeu (murs, cases traversées) ;
  - version, MANUAL, mode 0..7 (Start + Droite), ism ;
  - « S » = Start maintenu (EX) ;
- valide le HANDICAP, journalise les choix (`CHOIX : $102, base, drapeaux, mode, $123, $15F, ism`) et les manches ;
- en combat : vie de J1 maintenue, adversaire à 1 PV après 60 images, J1 avance, lance des boules de feu et frappe ;
- s'arrête sur exception (comme `hyper.lua`).

Format de `LISTE` : `"J1/J2,…"`, avec `perso(hexa).famille(Z|Z2|A|Z3)[.S][.m0-7][.iX|iA|iV]`.

Scène `$E` : `CONTOURNE_E=1` remet `A5+4 = 2`, `A5+8/C/10 = 0` et les champs de sélection des joueurs (liste de
l'init. `0x95C84` + `$3D`). C'est un **contournement**, signalé au journal. Sans lui, le reliquat (`$15A`, `$15F`…)
fait sauter des étapes.

**Essai court** (`essais/tournee_vs.log`, `planches/tournee_vs.png`) : VERSUS 2 joueurs, 14 000 images.
- 7 sélections, 14 manches, **0 exception**.
- Choix obtenus : Ryu EX ALPHA / Ken ZERO ; Bison ZERO 3 curseur 7 (`$D2 = $98`) / Chun-Li SF2 ZERO 2 ;
  EX Balrog / Ryu S-ISM rouge ; Ken S-ISM bleu / Sagat EX ZERO 2 (en morceaux) ; Shin Akuma ZERO 3 / Sakura bis ALPHA ;
  EX Zangief ALPHA / EX Dhalsim ZERO 2.
- Transitions : `A5+4` 2 → 4 → `$E` ; `A5+8` 4 → 8 → A → C → 6 ; en combat `A5+C` 4 → 6 → 8 → A → C → E.

**TRAINING** (`tournee_tr.log`) : Chun-Li X-ism contre Guile, une manche. Il n'y a pas de retour à la sélection :
- le menu de pause de la PS2 est natif ;
- après un K.O., la manche reste en sous-état 6.

## 5. Captures et fichiers

**Planches**
- `planches/ex_alpha_combat.png`, `ex_zero2_z3_combat.png`, `ex_vs.png` ;
- `libelles_modes.png`, `ecran_modes_curseurs.png`, `modes_caches_ryu.png` ;
- `chunli_sodom_x.png` : `$12/$14` atteints naturellement, lisibles ;
- `tournee_vs.png`, `tournee_versus.png`, `tournee_training.png` ;
- `versus_fin_match.png` : la scène `$E` est noire ;
- `generique_cache_option.png`.

**Scripts**
- `lua/hyper.lua` : copie, avec en plus `WATCHW`, `WTAP` et `NOROUL` ;
- `lua/tournee_hyper.lua`, `lua/trace_hyper.lua`, `lua/bp_hyper.lua` ;
- `lance.sh`, `tournee.sh`, `selection.py` (séquences EX), `modes_caches.sh`.

**Outils**
- `outils/zone.py`, `tab.py`, `a68.py` ;
- `outils/table68.py` (tables 68K réelles), `aiguillages.py`, `scenes.py` (aiguillages exécutés par trace) ;
- `outils/audit_cibles.py`, `planche.py`.

**Essais** : `essais/*.log` (+ `.inputs`), `essais/traces/*.tr`, `scenes_vs.txt`.

## 6. Questions restantes

1. **PS2** :
   - quelle touche lance la roulette (bit moteur `$0100`), et laquelle sert de START pour les EX ?
   - `$58/$59` s'y affichent-ils aussi en morceaux ?
2. Sens exact de **S-ISM** (`$123` / `$122` = 2/3/4, jauge « SUPER », sans doute le style ZERO 1) et du curseur 7
   (EX ZERO 3 sans jauge).
3. L'état A (choix commun, `$A2(A5) ≥ 3`, `$117(A5)` = 0/6/8) : quelle option du menu OPTION l'active ? Est-ce bien la
   vitesse ?
4. Corriger le traducteur pour l'aiguillage `sll 2` vers une table de longs (`0x2D570`, `0x3B439C`) et pour les tests
   `lb ; beq reg,zero` du code ajouté (`0x3B4300`, `0x2C440`). Il faudra ensuite revoir la scène `$E` (menu `$C316`)
   et le TRAINING.
5. Le reliquat de `$123/$15F` d'une sélection à l'autre (le joueur garde ses étapes : `$15A &= $3B`) : est-ce le
   comportement voulu par la scène `$E` réelle ?
6. Décors : un décor rouge (EX Balrog contre Ryu) et un vert (CLASSIC). Est-ce le 4ᵉ décor, ou les variantes
   `$C178` ?
