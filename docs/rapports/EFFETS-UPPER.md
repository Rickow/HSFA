# Effets de Vega sans frame lisible ; blocs de données des persos propres à Upper

Agent `agent_effets_upper`, 2026-10-11. Questions de la session MAX (correspondance pac PSP de SFA3 MAX ↔ données d'Upper).

Tout le travail porte sur une **copie** d'Upper prise le 2026-10-11 à 13 h 00 (`ro5/`, ROM de `work/mame_ro5` du
2026-10-11 12:48, `sz3ud.03c` md5 `efde8593…`, voir `ro5/md5_copie.txt`). Les adresses « image » valent pour **cette**
construction : elles changent à chaque reconstruction. Les adresses MIPS et PS2 ne changent pas.

Conventions :
- **image** : adresse 68K dans le programme traduit (`prog.bin`, remis bout à bout par `fait_prog.py`) ;
- **MIPS** : décalage dans `ro5_usa_prog68k.bin` (2e colonne de `carte_image.txt`) ; **PS2** = MIPS + `0x1F0000` pour le
  code, adresse virtuelle du module pour les données ;
- conversion d'une adresse de données PS2 en image : routine `CONV_A0` (image `$400` → `$4FE`). Pour la zone
  principale, image = PS2 − `0x569CC0` ; à partir de PS2 `0x8E4AE0`, image = PS2 + `0x39B520` (bloc externe `$C80000`).

## 0. Réponses courtes

**a) Les morceaux de masque et de griffe de Vega ne sont pas des effets de la table commune.** Ce sont deux **objets
attachés** au joueur, `$13` = **masque** et `$14` = **griffe**. Le principe est le même que sur PSP et en arcade. À
chaque image, l'objet lit le **mot `+$12` du pas courant du corps** et le passe par une table d'indices à 4 octets
(`T_60D480`). Il obtient ainsi un n° d'animation dans sa propre table : masque PS2 `0x655F48`, griffe PS2 `0x656CE8`.
Les frames sont des types **0** et **2** ordinaires. Elles sont rangées dans les **données communes du module**, à PS2
`0x657A90`-`0x65AC8C`, et non dans un bloc de perso. Leurs positions sont dans le fichier 390 (`$B04000`).

Pourquoi les tuiles viennent de `e351` : l'objet attaché met `$1A = 0`. L'emplacement de banque 0 est la banque
commune `e351`. Les **codes des frames sont les index locaux de `e351` tels quels** : pas de `+$1600` dans Upper.

Pourquoi la session MAX ne les trouvait pas : aucune table du joueur (`$2B0`-`$2BC`) ni aucun fichier d'animation par
perso ne pointe vers ces frames. Seules les y mènent les deux tables des objets attachés et la table des morceaux qui
tombent (PS2 `0x655E90`).

**b) `T_61A100[$20..$27]` ne sont pas des pointeurs.**
- `T_61A100` (32 longs) est l'homologue de la copie **`$ACDE0`** de `$DD412` en arcade, une table relative au PC qui
  suit le code `$ACD56`/`$ACD82`.
- Ce qui suit les 32 longs est **une autre table** : des **paires de mots (x, y)**, homologue de l'arcade `$ACE60`.
  Elle est lue par image `$4DFC8` (MIPS `0x21F798`, `LEA` PS2 `0x61A180`). `$00C00050` se lit donc `x = $0050`,
  `y = $00C0` (petit-boutiste).
- **La vraie table des blocs par perso d'Upper est `T_749838`** (PS2 `0x749838`, image `$1DFB78`, **40 longs**). C'est
  elle que lit l'initialisation du joueur (homologue de l'arcade `$2FC4A`, qui remplit `$2B0`/`$2B8`/`$2B4`/`$2BC`).

| perso | entrée de `T_749838` | adresse image (68K) | taille |
|---|---|---|---|
| Guile `$20` | `0x008F07D0` | `$C8BCF0` | `$9D80` |
| Fei-Long `$21` | `0x008FA550` | `$C95A70` | `$9EB0` |

Ces blocs sont des **données du module**. Aucun chargeur ne les remplit : ils sont dans `ro5_usa_prog68k.bin`. Comme ils
sont au-delà de la coupure `0x8E4AE0`, le traducteur les range dans `ext_c80000.bin` (bloc externe `$C80000`).

Vidages fournis : `vidages/` (§2.4).

## 1. Question a : effets de Vega dessinés depuis `e351`

### 1.1 Méthode (banc MAME, copie d'Upper)

1. `lua/effets.lua` (chargé par `lance.sh`), avec Vega en J1 (`PERSO=1C`) :
   - partie Arcade scriptée par `lua/tournee.lua` (copie, plus `SANS_KO=1` : la vie du CPU n'est pas forcée) ;
   - `ACTION=vega` : charges cristal / barcelone / écarlate / griffe aérienne, coups normaux, puis temps passifs pour
     prendre des coups ;
   - 24 000 images, 4 combats.

   Chaque image, le script relève dans la liste d'objets **brute** les objets de l'emplacement 0 dont le code est
   dans `$3C24`-`$4062` (15 396-16 482) ou `$5224`-`$5662` (+`$1600`). Une prise d'écriture sur `$700000`-`$70FFFF`
   garde, au moment où le jeu écrit le mot de code, le PC, A0-A6, D0-D7 et les champs de l'acteur A6.

   Copie de `banc_sprites.lua` : elle exporte `BANC_BUSY` pour ignorer les réécritures converties du banc.
2. `lua/anim_tap.lua` : prise d'écriture sur `$1C/$1E` (pointeur de pas) des acteurs de `$FFA000`-`$FFDFFF`. Il relève
   PC, retour en (SP) et classe, pour les pas de `$EC000`-`$EE200` et `$F1000`-`$F1500`.
3. Lecture statique : `decode_attaches.py` (tables et frames) et `scan_frames.py` (balayage des frames type 0/2 par plage
   de codes).

Résultats : `runs/vega1/` (`eff.txt` 46 445 objets, `histo.txt`, `acteurs.txt`, captures toutes les 100 images),
`runs/vega_anim/anim.txt`, `runs/attaches_decodes.txt`, `runs/frames_plage_vega.txt`.

**Ce que montre le relevé.** Tous les objets de la plage sont écrits par les deux gestionnaires de frames ordinaires.
Le PC relevé (`$2C8FA` / `$2C9A4`) est l'adresse suivant l'écriture de l'objet :
- **type 0**, image `$2C86C` (MIPS `0x13F394`) ;
- **type 2**, image `$2C900` (MIPS `0x13F934`).

Ces gestionnaires sont appelés par l'aiguillage par type de l'image `$2C80C` (MIPS `0x13F298`) : frame = long `+4` du
pas `$1C(A6)`, puis saut par la table de types `T_614460`.

Il n'y a **ni particule posée par du code, ni liste d'objets écrite à la main**.

Acteurs trouvés :

| acteur (octet +2 PS2 / +3 = perso) | réservoir | pas | codes `e351` vus | rôle |
|---|---|---|---|---|
| `$13` / `$1C` | `$FFCE80`-`$FFCF80` | `$EC54C`-`$ED00C` | 16 002-16 375 | **masque** attaché |
| `$14` / `$1C` | idem | `$ED2EC`-`$EDDB4` | 15 625-15 974 | **griffe** attachée |
| `$00` / `$1C` | `$FFB000` (32 × `$80`) | `$EC204`-`$EC27C` | 16 053-16 416 | morceaux du masque qui tombent |
| `$04` / `$00`, `$04` / `$26` | `$FFB000` | `$F122C`, `$F13DC` | 16 447-16 480 | étincelles communes (table PS2 `0x65AD80` = arcade `$2E50A0`, anims 1 et 8), pas propres à Vega |

À l'image 4 420, les objets `$13` disparaissent et des objets `$00/$1C` (codes 16 053-16 192) apparaissent : le
masque est tombé.

### 1.2 Mécanisme et homologues

| rôle | Upper image | Upper MIPS (PS2 = +`0x1F0000`) | arcade SFA3 | PSP (session MAX) |
|---|---|---|---|---|
| création des deux objets, dans l'init. du joueur Vega : `$6B=1`, `$6A=1` (68K), allocation, classe `$13` → `$28(A6)`, classe `$14` → `$2A(A6)`, copie de `$C`, `$F` et du joueur `$36` | `$89590`-`$895E4` | `0x38AAA4`-`0x38AC1C` | `$699CC`-`$69A1C` | `FUN_00183A38` |
| objet `$13` (masque) : aiguillage d'états | `$BDC2` | `0x694F4` | `$B173C` | `FUN_00183AB8` |
| état 0 : copie `$18.L`, perso `$103`→`$2`, `$C`, `$F` ; `$6D = 8` ; **`CLR.W $1A`** (arcade : `$1A` du joueur) | `$BDE0` | `0x695B8` | `$B175A` | |
| mise à jour par image (voir ci-dessous) | `$BE0E`-`$BE8C` | `0x696A4`-`0x69B04` | `$B1784`-`$B17EC` | |
| pose de l'animation : `$6A = n`, `A0 = T + T[2n]`, `$1C`, `$32` | `$BF7E` (LEA `$EC288`) | `0x6A098` | `$B18F2` (`#$2B55B0`) | |
| suivi de position (`$12`/`$16` du joueur, + `$D4`) | `$BF5C` | `0x69FF4` | `$B18D0` | |
| détachement : aléa `& 3`, création du morceau `#$1C00` (classe 0) avec décalage `T_60DA90` | `$BE8E` | `0x69B20` | `$B17EE` (`#$001C`, table `$B1880`) | |
| objet `$14` (griffe) : aiguillage | `$BFA6` | `0x6A1A4` | `$B1F10` | `FUN_00183AB8` |
| état 0 (`$6D = $20`, `CLR.W $1A`) | `$BFC4` | `0x6A268` | `$B1F2E` | |
| mise à jour par image | `$BFEC`-`$C06A` | `0x6A334`-`0x6A798` | `$B1F52`-`$B1FBE` | |
| pose de l'animation (LEA `$ED028`) | `$C132` | `0x6AC98` | `$B20A8` (`#$2B634E`) | |
| détachement : aléa `& $F`, morceau `#$1C01` (classe 1) | `$C06C` | `0x6A7B0` | `$B1FC0` (`#$011C`) | |

**Mise à jour par image** (masque ; la griffe est identique avec ses propres champs) :
1. `A4` = joueur (`$36(A6)`).
2. Si le joueur a son masque (`$6B`, arcade `$6A`) et a pris un coup (`$6E`, arcade `$6F`) :
   - `$6D`, compteur de coups, est décrémenté ;
   - à 0, tentative de détachement.
3. `A3` = pas courant du joueur (`$1C(A4)`).
4. **`D1` = mot `+$12` du pas** (le pas joueur fait 20 octets ; c'est le « mot C »). S'il vaut 0, l'objet est caché
   (`$6A = 0`, rien n'est dessiné).
5. `D0 = T_60D480[D1 × 4 + 0]`, ou `+2` pour la griffe.
6. Si `D0 ≠ $6A`, nouvelle animation. Le pas est tenu (durée `$FF`).

**Champs du joueur pour la griffe** : `$6A` (griffe présente, arcade `$6B`) et `$71` (coup reçu, arcade `$70`).

**Tables** (homologues PSP d'après le message de la session MAX) :

| table | Upper (PS2 / image) | arcade | PSP | contenu |
|---|---|---|---|---|
| index → (anim masque, anim griffe) | **`T_60D480`** = PS2 `0x60D480`, image `$A37C0`, 384 × 4 octets (indices 0-`$17F`) | `$B1910` (relative au PC, **identique mot pour mot**) | `0x28FD8C` | 2 mots par entrée ; max 344 (masque) / 345 (griffe) |
| animations du masque | PS2 **`0x655F48`**, image `$EC288` (345 anims utiles) | `$2B55B0` | `0x28EE30` | mots relatifs → pas de 8 octets |
| animations de la griffe | PS2 **`0x656CE8`**, image `$ED028` (346 anims utiles) | `$2B634E` | `0x28F0E2` | idem |
| morceaux qui tombent | PS2 `0x655E90`, image `$EC1D0` : anims 0-1 = griffe tombée (classe 1, image `$3241C`/`$324B0`), 2-4 = morceaux du masque (classe 0, image `$321CE`/`$322E2`) | (même famille, classes `$00/$1C`, `$01/$1C`) | — | |
| décalage de départ du morceau | `T_60DA90` / `T_60DAE0` (image `$A3DD0` / `$A3E20`) | `$B1880` / `$B2036` | — | (dx, dy) par perte |

**Équivalent PSP de `$8000 = rien`** : l'index 0 (objet caché). L'anim 0 des deux tables pointe aussi sur la frame vide
partagée (type `$12`, PS2 `0x657A90`).

### 1.3 Formats

**Pas d'animation** (8 octets, homologue de `$1B6E0` = image `$1A01E`) :

| PS2 | contenu | vue 68K |
|---|---|---|
| `+0` | durée | octet `+1` |
| `+1` | drapeaux | octet `+0` |
| `+4` | u32 frame (PS2) | long à moitiés échangées |

Drapeaux : bit 7 = saut au u32 de `+8` ; bit 6 = fin.

**Frame type 2** (gestionnaire `$2C900`) :
```
u16 2 ; u16 T (budget de tuiles 16×16) ; u16 n−1 ; [réalignement (A0+3)&~3] ; u32 positions (PS2, fichier 390) ;
n × { u16 code LOCAL e351 ; u16 attr CPS2 (bits 8-11 largeur−1, 12-15 hauteur−1, 5-6 miroir, 0-4 palette) }
```

**Frame type 0** (gestionnaire `$2C86C`) : une seule tuile par objet, attributs communs.
```
u16 0 ; u16 n (= T) ; u16 attr commun ; [réalignement] ; u32 positions ; n × u16 code LOCAL e351
```

**Positions** : n × (s16 dx, s16 dy) dans le fichier 390 (`ext_b04000.bin`, PS2 `0xB04000+`). Le miroir de l'acteur
(`$A`) inverse dx/dy en tenant compte de la taille du bloc. X = (dx + origine) & `$3FF` | `$18` ; Y = … | `$1A` (= 0 :
emplacement 0).

**Exemple décodé** (griffe, anim 1) :
- pas image `$0ED2F4` = PS2 `0x656FB4` : mots `00FF 0000 7A92 0065` → durée `$FF`, frame PS2 `0x00657A92` (image
  `$0EDDD2`) ;
- frame : `0002 0004 0001 CA10 00B0 3D09 1000 3D0A 1000` → type 2, T = 4, 2 objets, positions PS2 `0xB0CA10`.

| objet | code `e351` | code CPS2 (`f351`) | attributs | dx, dy |
|---|---|---|---|---|
| 1 | 15 625 (`$3D09`) | `$3BD43` | `1000` : bloc 1×2, palette 0 | −16, −109 |
| 2 | 15 626 (`$3D0A`) | `$3BD44` | `1000` : bloc 1×2, palette 0 | 0, −109 |

**Exemple type 0** (masque, anim 1) :
- frame PS2 `0x659028` (image `$0EF368`) : `0000 0005 0001 0000 CFCC 00B0 3E82 3672 3E86 3E87 3E88` ;
- 5 tuiles, attribut commun `$0001` (palette 1), codes `e351` 16 002 / 13 938 / 16 006 / 16 007 / 16 008 ;
- positions PS2 `0xB0CFCC` : (−51, −112), (−51, −96), (−35, −112), (−35, −96), (−19, −96).

Liste complète des 345 + 346 + 5 animations : `runs/attaches_decodes.txt`.

### 1.4 Couverture de la plage 15 396-16 482

Il y a 340 frames de masque, 342 de griffe et 19 de morceaux (types 0 et 2). Elles couvrent :

| objet | tuiles couvertes | plage |
|---|---|---|
| griffe | 357 | 15 396-15 988 |
| masque | 396 | 16 002-16 407 |
| morceaux | 58 | 15 983-16 428 |

Elles empruntent aussi 6 tuiles hors plage : 632, 1 537, 1 673, 9 472, 10 534, 13 938 (tuiles identiques
dédoublonnées dans `e351`).

Les tuiles **15 397-15 622** de la plage ne sont utilisées par aucune de ces tables. `scan_frames.py 15397 15622` les
retrouve dans des frames à PS2 `0x655ACC`-`0x655E18`. Ces frames appartiennent à la table PS2 `0x6495E0` (image
`$DF920`), anims 3-7, posée par un acteur de classe 6 :
- image `$333BA`, MIPS `0x173B10` ;
- n° d'anim = `T_615640[$12A(A5)]`, une valeur par **décor** (non nulle pour 7, 8, `$0C`-`$16`).

Ce sont des objets de décor qui partagent des tuiles de `e351` avec les effets de Vega, pas des effets de Vega. Quelques
tuiles en fin de plage (16 447-16 481) servent aux étincelles communes (table PS2 `0x65AD80`).

### 1.5 Homologues des tables d'effets communes citées

| arcade | Upper | comment |
|---|---|---|
| `$2E50A0` | PS2 **`0x65AD80`**, image `$0F10C0` | 280 anims, mots relatifs **identiques** aux 16 premiers ; lu par une vingtaine de sites (`LEA $0f10c0`) |
| `$2F4284` | PS2 **`0x649798`**, image `$0DFAD8` | mêmes écarts que l'arcade sur 48 mots, décalés de +2 (une entrée de plus) ; lu juste avant la routine `T_61A100` (image `$4E20C`) comme en arcade (`$ACD4A`) |
| `$81522`, `$301FA2` | non retrouvées | ce ne sont pas des tables de mots relatifs de pas ; aucun effet de Vega n'y passe |

## 2. Question b : `T_61A100` et les blocs de Guile / Fei-Long

### 2.1 Relevé (banc, `lua/blocs.lua`, 120 images après le début du 1er combat)

Fichiers : `runs/blocs_20/blocs.txt` et `runs/blocs_21/blocs.txt`.

`T_61A100` (image `$B0440`), lue en mémoire du 68K et identique au module PS2 :

| index | valeur | conversion | sens réel |
|---|---|---|---|
| `$00`-`$1F` | `0x0079B650` … `0x008E4AE0` | `$231990` … `$C80000` | blocs des 32 persos SFA3 (= `T_749838[$00..$1F]`) |
| `$20` | `0x00C00050` | `$37AF50` (bloc des animations natives, base virtuelle `$C00000`) | paire (x = `$50`, y = `$C0`) |
| `$21` | `0x00900100` | `$C9B620` (données du module) | paire (`$100`, `$90`) |
| `$22` | `0x00A00080` | `$FF0080` (RAM : la RAM d'Upper est PS2 `0xA00000`, pas `0x900000`) | paire (`$80`, `$A0`) |
| `$23`-`$2F` | `0x00B00140`, `0x009000A0`, `0x00A00150`, `0x00C80060`, `0x00A80120`, puis la même série | (sans objet) | paires (x, y) |

**Arcade** : `$ACDE0` contient 32 longs **égaux à `$DD412`**, suivis de `$ACE60` = `005000C0 01000090 008000A0 014000B0
00A00090 015000A0 006000C8 012000A8` × 2. Ce sont les mêmes paires, en gros-boutiste.

**Seul lecteur de `T_61A100`** : image `$4E27A`-`$4E2F0` (MIPS `0x2202DC`-`0x22043C`, entrée `0x220294`). C'est la
fusion par le recompilateur des deux routines arcade `$ACD56`/`$ACD82` :
- `A0 = T[$7F] ; A0 = [A0 + D8]`, avec D8 = 4 (`$2B8`) ou `$C` (`$2BC`) de l'isme 0 ;
- `A0 += [A0 + 2×$70]`.

Elle est précédée d'un test `TST.B $2(A6) ; BPL`. Un acteur au sous-type ≥ `$80` (les fins d'Upper, dont celles de
`$20`-`$25`) prend l'emplacement `$8000` et l'animation native `$C0BC(A5)` **sans lire `T_61A100`**. Les persos `$20+`
n'ont donc pas d'entrée et n'en ont pas besoin. Un perso MAX qui passerait par cette routine avec `$7F ≥ $20` lirait
des paires (x, y) : il faudrait déplacer et agrandir la table.

**Les autres lecteurs** passent par **`T_749838`** (`LEA $1DFB78`, 5 sites dans Upper, contre 11 lecteurs de `$DD412` en arcade) :
- image `$31F68` = MIPS `0x16BCEC`, initialisation du joueur (homologue de l'arcade `$2FC4A`) ;
- image `$3DBC6`, `$3EE4A`, `$45BFE`, `$4C4B0`.

### 2.2 `T_749838` (40 entrées, PS2 `0x749838`, image `$1DFB78`)

Les entrées `$00`-`$1F` sont celles de `T_61A100`. Ensuite :

| perso | entrée | conversion | remarque |
|---|---|---|---|
| `$20` Guile | `0x008F07D0` | `$C8BCF0` | |
| `$21` Fei-Long | `0x008FA550` | `$C95A70` | |
| `$22` Dee Jay | `0x00904400` | `$C9F920` | |
| `$23` T.Hawk | `0x0090D660` | `$CA8B80` | |
| `$24` Shin Akuma | `0x007B03E0` | — | 2e en-tête dans le bloc d'Akuma, + `$30` |
| `$25` Balrog (variante) | `0x0087E520` | — | bloc de Balrog + `$30` |
| `$26` | `0x0079B650` | — | Ryu |
| `$27` | `0x008D9730` | — | Juli |

Elle est suivie d'autres données (`$28` = `FFFD0000`…).

### 2.3 Où sont les blocs, qui les remplit

- **Ni RAM ni fichier chargé** : les blocs font partie des **données du module** `ro5_usa_prog68k.bin`, chargées avec
  lui (PS2 `0x8F07D0` = décalage `0x7007D0` du fichier).
- Dans la traduction, tout ce qui est à partir de PS2 `0x8E4AE0` (début du bloc de Juni, coupure du §126) est écrit par
  `mame_test.py` (`translate.DATA_SPLIT`) dans **`ext_c80000.bin`** et servi en `$C80000` :
  - banc : `banc_mem.lua` ;
  - fork : ROM `HSFA_EXT`.
- Décalages dans `ext_c80000.bin` : Guile `+$BCF0`, Fei-Long `+$15A70`.
- Le jeu les lit par `CONV_A0` (`$4FE` : PS2 `[0x8E4AE0, 0x9A0180)` → + `$39B520`).
- **RAM** : les `$2B0`/`$2B4`/`$2B8`/`$2BC` du joueur (`$FF8400` + …) contiennent les **valeurs PS2** (longs à moitiés
  échangées), converties à chaque usage.

| joueur | `$2B0` | `$2B4` | `$2B8` | `$2BC` |
|---|---|---|---|---|
| Guile (J1) | `008F0800` | `008F08D0` | `008F091C` | `008F0886` |
| Fei-Long (J1) | `008FA580` | `008FA696` | `008FA720` | `008FA652` |

### 2.4 Disposition (même schéma que `$DD412`) et fichiers

En-tête de **12 longs** = 3 ismes × (`$2B0`, `$2B8`, `$2B4`, `$2BC`), l'isme choisi par `$132` (0 → `+0`, < 0 → `+$10`,
> 0 → `+$20`). Les tables suivent l'en-tête dans le bloc (décalages depuis le début du bloc) :

| perso | `$2B0` | `$2BC` | `$2B4` | `$2B8` | particularité |
|---|---|---|---|---|---|
| Guile | `+$30` | `+$B6` | `+$100` | `+$14C` | les 3 ismes identiques |
| Fei-Long | `+$30` | `+$102` (`+$BE` pour les ismes 1 et 2) | `+$146` | `+$1D0` | |

Le reste du bloc, jusqu'au bloc suivant, contient les pas et données visés par ces tables. La table `$2B0` pointe dans
`+$30`…`+$42A8` (Guile) et `+$30`…`+$4F42` (Fei-Long).

| fichier (`vidages/`) | contenu |
|---|---|
| `bloc_20_guile_68k_C8BCF0.bin` | Guile, `$9D80` octets, **vue 68K** (mots gros-boutistes tels que lus en `$C8BCF0`, vidés par MAME ; = `ext_c80000.bin` + `$BCF0`) |
| `bloc_20_guile_ps2_008F07D0.bin` | le même bloc **en octets PS2** (petit-boutiste), tiré du module |
| `bloc_21_feilong_68k_C95A70.bin` | Fei-Long, `$9EB0` octets, vue 68K |
| `bloc_21_feilong_ps2_008FA550.bin` | idem, octets PS2 |
| `ram_FF0000_perso20.bin`, `ram_FF0000_perso21.bin` | RAM de travail `$FF0000`-`$FFFFFF` (vue 68K) 120 images après le début du combat (Guile contre `$1B` ; Fei-Long contre `$13`) |

Vérifications : chaque mot de la vue 68K est égal au mot petit-boutiste du module à la même adresse (recette §29). Le
vidage MAME est égal à l'extrait d'`ext_c80000.bin`.

## 3. Fichiers

| fichier | rôle |
|---|---|
| `lance.sh NOM SCRIPT NF "VARS"` | Upper (copie `ro5/`) sur le fork `sfa3hx` ; `nice -n 19`, nvram/cfg dans `runs/NOM/`, sans `-state` |
| `lua/tournee.lua` | copie, plus `SANS_KO`, `ACTION=vega\|passif` ; `dofile` vers ce dossier |
| `lua/banc_sprites.lua` | copie, plus le global `BANC_BUSY` |
| `lua/banc_mem.lua`, `lua/banc_plans.lua` | copies |
| `lua/effets.lua` | relevé des objets de l'emplacement 0 par plage de codes, avec le contexte CPU de l'écrivain (`PLAGES`, `EFF_OUT`, `EFF_RESUME`, `EFF_ACTEURS`, `EFF_HISTO`) |
| `lua/anim_tap.lua` | qui pose `$1C` (pas d'animation) d'un acteur (`PAS`, `ANIM_OUT`) |
| `lua/blocs.lua` | `T_61A100`, `T_749838`, `$2B0`-`$2BC`, vidages RAM et bloc (`BLOCS_OUT`, `BLOCS_DIR`) |
| `fait_prog.py` | `prog.bin`, programme traduit remis bout à bout (pour `unidasm`) |
| `decode_attaches.py [--tout]` | `T_60D480`, tables masque / griffe / morceaux, frames 0/2 décodées |
| `scan_frames.py [lo hi]` | frames 0/2 de l'image dont un code `e351` tombe dans une plage |

Les relevés sont dans `runs/`. Les captures de la partie Vega sont dans `runs/vega1/snap/`.

Exemples de lancement :
- `./lance.sh vega1 $PWD/lua/effets.lua 24000 "PERSO=1C SANS_KO=1 ACTION=vega EFF_OUT=… EFF_RESUME=… EFF_ACTEURS=… EFF_HISTO=…"` ;
- `./lance.sh blocs_20 $PWD/lua/blocs.lua 8000 "PERSO=20 SPRITES=0 BLOCS_OUT=… BLOCS_DIR=…"`.
