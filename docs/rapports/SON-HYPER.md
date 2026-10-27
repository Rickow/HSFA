# Son d'Hyper SFA (`ro9`) : cartographie PS2, commandes 68K, plan de ROM son pour le fork

Agent `agent_hyper_son`, 2026-10-07. J'ai écrit seulement dans `<workspace>/work/agent_hyper_son/`. Le reste
est resté en lecture seule. Les états PCSX2 ont été lus depuis des copies (`etats/`, venues de
`~/hsfa/pcsx2_cheats_backup/`). MAME a tourné un seul à la fois, en `nice -n 19`, avec la NVRAM et la config dans
`essais/`, sans `-state`.

Conventions d'adresses :
- « exéc. » = adresse d'exécution PS2 du module ; fichier = exéc. − `0x1F0000` dans
  `decompressed/ro9_usa_prog68k.bin`.
- « mips » = décalage fichier.
- « 68K » = adresse de `mame_ro9/carte_image.txt` (build du 2026-10-07).
- « Yn » = entrée n de **`Y_DATA.BIN`** (AFS de l'ISO, 588 flux ADX CRI, 48 kHz, à `0xAB628800` dans l'ISO).
- « en » = entrée n du manifeste X_DATA.

## 0. En bref

1. **Sur PS2, Hyper n'utilise ni Z80 ni QSound.**
   - Le Z80 recompilé (mips `0x40-0x22B00`) est du code mort : banc de registres Z80 (scratchpad `0x1000-0x103F`) à
     zéro dans tous les états, aucun appel vers lui.
   - Aucun fichier Z80 ou QSound de X_DATA (e221/222, e250/251, e287/288, e388/389, e532/533, e540/541) n'est présent
     dans l'EE, l'IOP ou la SPU2 d'un état Hyper, Upper ou SFA3.
   - Le son est géré par un **pilote natif PS2 (C) dans le module** :
     - il lit la boîte aux lettres QSound émulée (`$618001-$618019`, PS2 `0xBE0000+`) ;
     - il cherche chaque commande dans une **table de 0x1200 × 8 octets** ;
     - **musique** = flux ADX de **Y_DATA** (lib CRI ADX de l'ELF) ;
     - **bruitages et voix** = banques SCEI HD/BD sur la SPU2 (**e345**, **e346**, + une banque par perso parmi
       **e314-e344**), plus un conteneur de 64 voix ADX en mémoire (**e313**, l'annonceur).
   - **Ce sont les fichiers du groupe SFA3** (`ro3`). Hyper n'a donc pas besoin de fichier son dans son propre groupe
     (e544-e552).
2. **La table de commandes est identique, octet pour octet, dans ro3, ro5 et ro9.** C'est la carte des commandes du
   Z80 arcade de SFA3/Upper, étendue avec des musiques ADX. Les bruitages et les voix d'Hyper utilisent les **mêmes
   codes que SFA3/Upper, pour toutes les versions** :
   - les versions ZERO, ZERO 2 et ALPHA parlent avec les **voix de SFA3** ;
   - la banque est choisie par `$102` via la table exéc. `0x5AF2B0`.
3. **Musique : le 68K d'Hyper choisit un code selon le perso et la version de l'adversaire** (J2 par défaut). Il y a
   4 jeux de codes, plus des variantes :

   | version | codes | Y_DATA | origine (vérifiée par empreinte spectrale contre le Z80 arcade) |
   |---|---|---|---|
   | ZERO 3 | `0x01-0x2F` (+ `0x30-0x33` persos d'Upper) | Y1-Y51 | SFA3 (= codes du Z80 SFA3) |
   | ZERO | `0x41-0x4D` | Y56-Y68 | **SFA1 arcade** : codes Z80 SFA1 `0x01-0x0C` et `0x32` (corrélation 0,84-0,95) |
   | ZERO 2 | `0x51-0x63` | Y70-Y88 | **SFA2 arcade** : codes Z80 SFA2 `0x01-0x12` et `0x35` (0,68-0,96) |
   | ALPHA (ZERO 2 ALPHA) | `0x02C1-0x02D2`, `0x02FC` | Y170-Y187, Y229 | flux du module `ro6`, dont le Z80 n'a **aucune** musique ; ce n'est pas l'arcade SFA2 (≈ 0,5) |
   | variantes ZERO 3 et EX | `0x0180-0x01F7` | Y433-439, 460-527, 543-586 | inconnue (§2.3) |

   **Les musiques ZERO et ZERO 2 d'Hyper ne viennent pas des modules SFA1/SFA2 de l'Anthology :**
   - ce sont des flux ADX propres au jeu de codes de la famille SFA3, à l'image de la musique arcade ;
   - le module SFA1 (`ro1`) joue d'autres fichiers, Y97-Y131 (même morceaux, autre rendu, corrélation ≈ 0,6) ;
   - les modules SFA2 (`ro2`, `ro4`, `ro8`) n'ont pas ce pilote natif.
4. **Fork : faisable.**
   - Bruitages et voix : la **ROM hybride d'Upper** (`HSFA_SON`) couvre déjà tous les codes de bruitages et de voix
     d'Hyper. Je l'ai vérifié contre les balayages Z80 de l'agent ro5 : la table PS2 et le Z80 réagissent aux mêmes
     codes.
   - **Seule la musique manque** : codes ≥ `0x30`, y compris les 4 persos d'Upper.
   - Option recommandée : **lecteur de flux musique dans le fork**, qui décode les ADX de Y_DATA, comme la boîte
     `C080/C081` de CPS2 Turbo. C'est fidèle au PS2 et il n'y a aucun conflit de codes.
   - Option « tout QSound » : possible pour ZERO et ZERO 2 avec les Z80 SFA1/SFA2 et une table de traduction des
     codes. Elle demande un 2ᵉ pilote son, car les formats SFA1/2 et SFA3 diffèrent. Elle ne couvre ni ALPHA ni les
     variantes (§3).

## 1. Comment Hyper joue le son sur PS2

### 1.1 Preuves (états PCSX2 d'Hyper : Ryu–Ken ZERO 3 ; Birdie–Evil Ryu)

| constat | outil |
|---|---|
| Les états `zero9_usa.bin` sont pris en combat : `etats/hyper_a.p2s` (copie de `pcsx2_cheats_backup/SLUS…02.p2s`) et `hyper_b`/`hyper_c` (CONTROL / PACKAGE). | `p2s_extrait.py` (zstd, méthode 93) |
| 0 bloc des fichiers Z80/QSound dans l'EE, l'IOP ou la SPU2 (Hyper, Upper `upper_titre`, SFA3 `training_*`), en clair, en mots échangés, en XOR 1/2/3. | `sonde_ee.py`, `sonde2.py` |
| Banc de registres Z80 (`0x70001000-0x103F`) entièrement nul ; banc 68K (`0x1100+`) actif. | scratchpad des états |
| Aucun `jal` vers la zone Z80 recompilée (ro3, ro5, ro9). | analyse statique |
| La SPU2 contient les corps BD des banques SCEI (voir §1.3). | `sonde_bd.py`, `carte_spu2.py` |
| Tampon de flux ADX en EE `0x19E1180` ; flux identifiés par `adx_courant.py`. | Hyper : `hyper_a` = **Y10** (commande `0x000A`), `hyper_b` = **Y40** (`0x0028`) ; SFA3 = Y9 ; Upper (titre) = Y47 |

### 1.2 Pilote natif PS2 (dans ro9, identique dans ro3 et ro5)

| rôle | ro9 | ro3 | ro5 |
|---|---|---|---|
| Lecture de la boîte, acquittement `$61801F=$FF` | exéc. `0x5A9B40` (fichier `0x3B9B40`) | mips `0x39303C` | `0x41A11C` |
| Commandes `FFxx` (arrêt, fondu, volume…) | `0x5A9CA0` | | |
| Commandes `< 0x1200` | `0x5AA0E0` (test `slti 0x1200` à mips `0x3BA114`) | `0x393624` | `0x41A6E4` |
| **Table des commandes** (0x1200 × 8 o) | **exéc. `0x5CB300`** (fichier `0x3DB300`) | `0x59F9C0` | `0x628780` |
| Table type → perso | `0x5D4300` | `0x5A89C0` | `0x631780` |
| Chargement de la banque d'un perso | `0x5AA430` : `0x154D20(0, fichier, 0x1BC8000 + 0x60000×emplacement, emplacement+2)` | | |
| Table `$102` → banque son | **`0x5AF2B0`** (128 mots) | `0x59C0F0` (32) | `0x628370` (40) |

Le pilote recopie la boîte dans une structure en `0xB67BD0` :

| champ | origine dans la boîte |
|---|---|
| +0 | `$618007/9` |
| +2 | commande `$618001/3` |
| +4 | `$618005` |
| +5 | `$61800D` |
| +6 | `$61800F` (volume) |
| +7 | `$618011` |
| +8 | `$618013/15` |
| +A | `$618017/19` |

**Format d'une entrée de la table** : l'octet 0 & `0x7F` donne le type (`table_son.py` décode les trois modules ;
CSV : `table_son_ro{3,5,9}.csv`).

| type | effet | paramètres |
|---|---|---|
| 0 | rien | |
| 1 | flux ADX de Y_DATA (`0x155510` / `0x1552D0` / `0x155330`) | fid = `(o6&0x7F)<<8 \| o4`, o5 = volume |
| 2 | voix ADX en mémoire (annonceur, conteneur **e313** chargé en EE `0x1341800`) | indice o4 (0-58) |
| 3 / 4 | banque SPU2 commune 0 / 1 (`0x155C60`) | |
| ≥ 5 | banque SPU2 du perso `PERSO[type-5]`, si ce perso est dans l'un des 3 emplacements (structure `[0x19E440]+0x39`) | |

### 1.3 Fichiers chargés (identiques pour les 4 versions)

| fichier X_DATA | contenu | où (RAM SPU2, décalage dans `SPU2.bin`) |
|---|---|---|
| **e345** (MOMO/SCEI HD+BD, 928 000 o) | banque commune 0 (bruitages) | `0x015104` |
| **e346** (98 624 o) | banque commune 1 (système) | `0x0F4104` |
| **e314-e344** | banque du perso, emplacement J1 / J2 / 3ᵉ | `0x10B904` / `0x162604` / `0x1B9304` |
| **e313** (étiqueté « GFX », 2 351 780 o) | 64 voix ADX mono (annonceur) | EE `0x1341800` |
| Y_DATA | musique (flux depuis le disque) | tampon EE `0x19E1180` |

Exemples :
- Hyper Ryu–Ken ZERO 3 : emplacements = e314, e315 (persos `00 01`) ;
- Hyper Birdie–Evil Ryu : e322, e314.

Table `0x5AF2B0` (`$102` → fichier) :

| ids | fichiers |
|---|---|
| `$00-$25` (ZERO 3) | comme Upper, dont **e340-e343** = Guile, Fei-Long, Dee Jay, T.Hawk |
| ZERO `$30-$3C` | e314-e326 (= banques SFA3 des mêmes persos) |
| ZERO 2 `$40-$5E` et ALPHA `$60-$7E` | e314-e331, plus des alias |
| `$26`, `$5E`, `$7E` | **e344** (propre à Hyper par rapport à Upper, qui met e314) |

Le 3ᵉ emplacement garde e344 sans perso (`ff`) dans tous les états.

**Les groupes de fichiers propres à SFA1 (e206-e223) et à SFA2 (e224-e252) ne servent pas au son d'Hyper.**

## 2. Côté 68K d'Hyper

### 2.1 Envoi des commandes (le test de la boîte est présent)

- File de 16 o par entrée en `$5E80(A5)` = **`$FFDE80`**, indices `$6E80/$6E82(A5)`.
  - Mise en file : 68K **`$8B532`** (mips `0x386F68`). D1/D2/D3 = les 12 octets de la commande, `$80(A5)` en +13.
  - Envoi : 68K **`$8B3CE`** (mips `0x386A6C`).
- **`CMPI.B #$FF,$61801F` est présent en `$8B3EA`**, contrairement à ro5 (§118). Dans le banc, les commandes partent
  normalement.
- Ordre des écritures : `$618007`, `$618009`, `$618001`, `$618003`, `$618005`, `$61800D`, `$61800F`, `$618011`,
  `$618017`, `$618019`, `$618013`, `$618015`, puis `CLR.B $61801F`.
- Aides : `$8B5A8` (FF00), `$8B5B2` (FF05), `$8B5BC` (FF06, D0), `$8B5CC` (FF07, D0), `$8B5DC` (commande générique).
- Le code natif `0x5A9B40` est traduit par erreur en 68K vers `$927A6-$927E4` (copies `$618005… → $F009D4`,
  `JSR` vers du natif). C'est le pilote PS2 : il est à **neutraliser au fork**, où le Z80 fait ce travail.

### 2.2 Choix de la musique : 68K `$8BB68` (mips `0x38910C`) → code dans `$C3B8(A5)`, 2ᵉ code dans `$C3B6(A5)`

**Choix du joueur dont dépend la musique** :
- par défaut, A4 = **J2** (`$0800(A5)`) ;
- en VERSUS (`$C201`=1) et en TRAINING (`$C201`=4), c'est `$C3B5(A5)` qui décide : 0 → J2, > 0 → J1, < 0 → au
  hasard (`0x57E890` & 1).

**Calcul** (octets 68K ; en mémoire PS2, `$103` ↔ `0x102` à cause du XOR 1) :
- D0 = id `$103(A4)`, D1 = 0 ;
- si drapeau de version `$116` bit 3 (versions EX de ZERO 2 et d'ALPHA), ou bit 4 (ZERO 3) avec `$15F`≠0 :
  D0 = perso de base `$117`, D1 = `$D0` ;
- sinon, si id ≥ `$30` : table directe ;
- sinon (ZERO 3) : D0 = `$117`, et :
  - si `$133` < 0 : D1 = `$80`, ou `$A8` selon le test de `$122` ;
- code = **`T_5c9580`[(D0+D1)×2]**, 2ᵉ code = `T_5c97d0`[idem].

Tables (mots, exéc. ; fichier = exéc. − `0x1F0000`) :

| exéc. | indexée par | contenu |
|---|---|---|
| `0x5C9580` | id ZERO 3 `$00-$25` | `09 0A 0B 0C 0D 0E 0F 10 11 12 13 14 15 16 17 18 19 1A 0C 1A 1D 1E 1F 28 21 22 23 24 25 26 27 27 30 31 32 33 1B 1E` |
| `0x5C95E0` | ZERO `$30-$3F` | `41 42 4B 49 43 46 45 48 47 4A 4C 44 4D 41 41 41` |
| `0x5C9600` | ZERO 2 `$40-$5F` | `51 52 5B 59 53 56 55 58 57 5A 5C 54 5D 62 61 5E 5F 60 53 60 5B 5F 5E 51 … 62 51 51` |
| `0x5C9640` | ALPHA `$60-$7F` | `2C1-2D2`, alias, `2FC` (Cammy `$7E`) |
| `0x5C9680` | variante A (`$133`<0) | `0181 0180 0190 000C 0183 …` |
| `0x5C96D0` | variante B (`$A8`) | `01C5 01C4 01D4 …` |
| `0x5C9720` | EX / `$15F` | `01A3 01A2 01B2 …`, puis `01E6…` pour les ids `$18+` |
| `0x5C97D0` | 2ᵉ code | ne sert que pour les variantes : `0191-01A1`, `01B3-01C3`, `01D5-01E5` |

Liste complète des codes musique et des flux : `codes_musique_hyper.txt`.

**Vérifié au banc** (fork `sfa3hx`, ROM ro9 du 2026-10-07, `lua/son_hyper.lua`, `FORCE102/FORCE102J2` en TRAINING) :

| J1 / J2 (`$102`) | musique envoyée |
|---|---|
| 31 / 31 | `0042` |
| 01 / 31 | `0042` |
| 31 / 01 | `000A` |
| 41 / 41 | `0052` |
| 61 / 61 | `02C2` |
| 41 / 61 | `02C2` |
| 30 / 30 | `0041` |
| 40 / 40 | `0051` |
| 00 / 00 | `0009` |
| 01 / 01 | `000A` |
| 00 / 00 avec `$FF8933`=FF imposé | `0181` |
| 00 / 00 avec `$FF895F`=1 | `01A3` |

Le titre envoie `0002` ; les menus envoient `0081`, `00C0/C1`, `00D1`, `00E0` (banque commune 1) ; l'annonceur
envoie `0105`, `010E`, `011E`, `011F`. Aucune exception. Journaux : `essais/t_*.son`, `f_*.son`, `w_00_00.log`.

### 2.3 Inconnues sur la musique

- **Sens de `$133`, `$122` et `$15F`.** Hypothèse : `$133` < 0 = X-ISM, `$15F` = mode CLASSIC. Les tables de
  variantes ne remplacent que les persos venus de SF2 (Ryu, Ken, Chun-Li, Bison, Sagat, Dhalsim, Zangief…). Le test
  `$122` n'a pas eu d'effet au banc (`0181` même avec `$FF8922/23`=FF) : l'adresse ou le sens sont à revoir.
- **Origine de Y433-586** (119 flux, ≈ 380 Mo d'ADX). Ce n'est ni le Z80 SFA1, ni le Z80 SFA2, ni ro6, et aucun autre
  module que ro3/ro5/ro9 ne les référence. Extraits à écouter : `wav/y554.wav` (variante A, Ryu), `y461.wav`
  (variante B), `y495.wav` (EX).
- ~~**Rôle du 2ᵉ code `$C3B6`**~~ **résolu le 2026-10-16** (cœur FBNeo, VERSUS Ryu X-ISM contre Ryu A-ISM) : c'est
  la musique de vie basse de la variante. `0181 -> Y554` au début de la manche, puis `0192 -> Y571` quand un joueur
  est presque KO, à chaque manche.
- **`$133`** : confirmé = ISM (`$FF` = X-ISM : J2 en X-ISM donne la variante A).
- **Tournée complète du 2026-10-16** (cœur FBNeo, 151 VERSUS, `tools/son-hyper/tournee_musiques.tsv`) : toutes les
  musiques de combat conformes aux tables ci-dessus ; variante A = X-ISM ; B (`$122`) et EX (`$15F`) jamais obtenues
  par la sélection normale.
- **Modes de sélection (ZERO 3), 2026-10-16** (indication de l'utilisateur et guide BradyGames, p. 4-5 : « New ISM
  Choices », Start tenu + ← ou → sur un mode = sa 2ᵉ version, **S-ISM**) : curseur du menu en `P+$5C` ; NORMAL,
  MAZI, SAIKYO, CLASSIC = 0-3 ; leurs S-ISM = **6, 5, 7, 4** (mesuré). Effet sur la musique
  (`tools/son-hyper/tournee_modes.tsv`, 231 VERSUS : 33 persos × 7 modes) :

  | mode | RAM | musique |
  |---|---|---|
  | NORMAL, MAZI, SAIKYO | — | normale |
  | **CLASSIC** | `$15F`=01, ISM imposé | table « EX » `T_5c9720` (`01A2`-`01B2`) + 2ᵉ code (`01B3`-`01C3`) |
  | Normal S-ISM | `$123`=82 | normale |
  | **Mazi S-ISM** | `$123`=02, ISM imposé X | **variante B** `T_5c96d0` (`01C4`-`01D4`) + 2ᵉ code (`01D5`-`01E5`) |
  | **Saikyo S-ISM** | `$15F`=81, ISM imposé X | table « EX » ; n'existe que pour 12 persos (curseur jamais à 7 pour `02 03 05-09 0c-0e 11 16 17 1a 1b 1d-1f 21-23`) |
  | Classic S-ISM | `$123`=80 | normale |

  La « variante B » dépend donc du mot `$122` (octet `$123`), et la table « EX » est celle de CLASSIC.
- **Persos EX (ZERO / ZERO 2 / ALPHA)** : Start tenu à la validation de la version donne une autre fiche
  (`$102` dans `$7x` ou `$5x`, `$116` bit 3) pour les persos qui en ont une ; ceux venus de SF2 jouent alors la table
  « EX » (`tools/son-hyper/tournee_ex.tsv`, 52 VERSUS bons).
- **Bilan 2026-10-16 : 194 codes sur 216 entendus en jeu.** Jamais obtenus : `01E6`-`01EB`, `01F4`-`01F7` (fin de la
  table « EX », index ≥ `$18` : origine à trouver) et 12 morceaux ZERO 3 hors VERSUS (`0003`, `0005`-`0008`, `001B`,
  `0020`, `0029`, `002B`-`002D`, `002F` : jingles, continue, fins, menus).
- **Y440-459 (codes `0x6C-0x7F`)** : jamais envoyés par le 68K d'Hyper, inutiles.
- **ALPHA = flux de ro6** : arrangement console présumé (le Z80 de ro6 est muet pour les codes 1-0x3D). À écouter :
  `wav/y170.wav`.

### 2.4 Voix et bruitages par perso et par version

Les codes ne dépendent que du perso de base, à quelques numéros près, comme en arcade. Ils pointent tous vers la
même banque SFA3 :

| perso et version | codes observés |
|---|---|
| Ryu ZERO 3 et Ryu ZERO | `0801`, `0802` |
| Ryu ZERO 2 | `0803` |
| Ken ZERO 3 | `0821`, `0822` |
| Ken ZERO | `0822` |
| Ken ZERO 2 et Ken ALPHA | `0823` |
| communs | `02xx`, `07xx` |

Sur PS2, **aucune voix SFA1 ou SFA2 n'existe** : toutes les versions parlent SFA3.

### 2.5 Différences avec Upper (ro5)

- **Même table PS2 et même pilote.** Les banques sont les mêmes, sauf que Hyper affecte e344 aux ids
  `$26/$5E/$7E` (Upper y met e314).
- **Musique d'Upper** (table 68K exéc. `0x613380`, `MOVE.W T_613380` en 68K `$2B8CE`) : codes SFA3, plus
  **`0x30-0x35`** (Guile, Fei-Long, Dee Jay, T.Hawk… → Y48-Y54). **Ces codes sont muets avec la ROM hybride
  actuelle**, car aucun Z80 n'a de musique au-delà de `0x2F`. C'est un défaut d'Upper au fork, non relevé au §127.
  Extrait à écouter : `wav/y048.wav`.
- **Hyper ajoute** :
  - les jeux `0x41-0x4D`, `0x51-0x63` et `0x02C1-0x02FC` ;
  - les variantes `0x0180-0x01F7` ;
  - le choix du joueur suivi (`$C3B5`) ;
  - le test de boîte aux lettres correctement traduit.

## 3. ROM son d'Hyper au fork : faisabilité et plan

### 3.1 Couverture par la ROM hybride d'Upper

Comparaison des balayages Z80 de l'agent ro5 (`tab_sfa3son_mus`, `tab_upper_mus`) avec la table PS2 :

| codes | table PS2 | Z80 SFA3 | Z80 Upper |
|---|---|---|---|
| bruitages et voix | 1 017 codes non nuls | répond | répond aussi, plus 101 codes propres (`05/0A 60-96`, `06 C0-F5`) |
| voix d'annonceur `0100-013A` (ADX sur PS2) | | répond | répond |
| musique `0001-002F` | | **44 codes jouent** | rien |
| `0030-0036`, `0041-0063`, `0141-01FF`, `0280-02FC`, `11xx` | ADX seulement | rien | rien |

Les pages 07, 09, 0B-10 n'ont pas été balayées ; elles suivent la même structure dans la table PS2.

Conclusion : **la ROM hybride (`HSFA_SON`) suffit pour tous les bruitages et toutes les voix d'Hyper.** Il ne manque
que la musique hors `0x01-0x2F`. Il n'y a **aucun conflit de numéros** : les codes sont disjoints par construction (la
table PS2 est commune), et les codes musique ajoutés tombent sur des cases vides des Z80.

### 3.2 Option recommandée : flux musique dans le fork (fidèle au PS2)

- Le fork intercepte, à l'écriture de `$61801F`=0, les commandes du type 1 de la table (`table_son_ro9.csv`) **non
  couvertes par le Z80** (ou toutes, pour un son identique au PS2). Il joue le flux Y_DATA correspondant : décodeur
  ADX d'une cinquantaine de lignes (`adx.py` en est la référence ; 48 kHz stéréo, boucle dans l'en-tête), mixé avec le
  QSound. Il traite aussi `FF07` (fondu) et `FF00` (arrêt).
- **Volume nécessaire** : 217 flux, **696 Mo d'ADX**, 3 h 38 min.

  | jeu | flux | taille ADX |
  |---|---|---|
  | ZERO 3 | 48 | 133 Mo |
  | ZERO | 13 | 49 Mo |
  | ZERO 2 | 18 | 63 Mo |
  | ALPHA | 19 | 71 Mo |
  | variantes | 119 | 380 Mo |

  Plusieurs façons de livrer :
  - lire directement le `Y_DATA.BIN` de l'utilisateur (variable du type `HSFA_MUS=<Y_DATA.BIN>`) : rien à
    redistribuer ;
  - extraire seulement les flux utiles ;
  - pour FBNeo sur Android, réencoder (Opus/Vorbis ≈ 40-60 Mo).
- Pour Upper, la même interception rendrait les musiques `0x30-0x35` aujourd'hui muettes.

### 3.3 Option « tout QSound » (arcade pur, pour ZERO et ZERO 2 seulement)

- **Correspondances vérifiées** (`wav/rec_sfa1*.wav`, `rec_sfa2.wav`, `apparie_*.txt`) :
  - Hyper `0x41+k` → Z80 SFA1 `0x01+k` (k = 0-11), et `0x4D` → SFA1 `0x32` ;
  - Hyper `0x51+k` → Z80 SFA2 `0x01+k` (k = 0-17), et `0x63` → SFA2 `0x35`.
- **Obstacle** : les pilotes Z80 SFA1 et SFA2 (e221 et e250 : même génération, 94 % du code identique) diffèrent de
  celui de SFA3 (42 %). Greffer leurs séquences dans le pilote SFA3, comme le fait l'hybride d'Upper, demande de
  **convertir le format des séquences**. C'est à étudier et ce n'est pas fait.
- **Autre voie** : un 2ᵉ couple Z80 + QSound dans le fork, uniquement pour la musique, avec la ROM SFA1 ou SFA2 chargée
  selon la version et une table de traduction des codes.
- **Taille** : Z80 0x48000 o par jeu ; échantillons QSound e222 = 4 Mo, e251 = 4 Mo. Avec l'hybride (16 Mo), le total
  monte à 24 Mo de QSound.
- **Limites** :
  - ALPHA (ro6 : Z80 sans musique) et les variantes n'ont aucune source QSound : il faudrait de toute façon des flux ;
  - FBNeo n'a qu'un QSound.
- Cette option n'est donc qu'un complément « arcade » possible pour ZERO et ZERO 2.

### 3.4 Étapes proposées

1. **Fork** :
   - charger la ROM hybride (`HSFA_SON`) pour `ro9` ;
   - vérifier que le natif traduit `$927A6-$927E4` (§2.1) n'acquitte pas la boîte à la place du Z80. Sinon, le
     neutraliser (`RTS`) ou laisser le Z80 répondre ;
   - au banc, Hyper envoie bien ses commandes, et la musique ZERO 3 joue avec le son SFA3.
2. **Lecteur ADX dans le fork** :
   - table code → fid extraite de `table_son_ro9.csv` (types 1 seulement) ;
   - boucles prises dans l'en-tête ADX ;
   - même chose ensuite dans le cœur FBNeo.
3. **Écoute de l'utilisateur** : `wav/y009`, `y056`, `y070`, `y170`, `y048` (Upper) et les variantes `y554`, `y461`,
   `y495`, `y440`. Elle sert à nommer les jeux de variantes et à décider s'il faut les embarquer (380 Mo).
4. **Trancher** `$133`, `$122` et `$15F` (ism, mode) au banc, ou avec un état PCSX2 en X-ISM / CLASSIC.

## 4. Fichiers

| fichier | rôle |
|---|---|
| `p2s_extrait.py` | extrait un membre d'un état `.p2s` (zstd) |
| `sonde_ee.py`, `sonde2.py` | cherche les fichiers Z80/QSound de X_DATA dans des vidages (clair, permutations) |
| `sonde_bd.py`, `carte_spu2.py` | banques SCEI (e314-e346) présentes dans la RAM SPU2 d'un état, et leur adresse |
| `adx_courant.py` | identifie le flux Y_DATA présent dans le tampon ADX d'un vidage EE |
| `ydata_toc.py` → `ydata_toc.csv` | table des 588 flux de Y_DATA (durée, boucle) |
| `table_son.py` → `table_son_ro{3,5,9}.csv` | table native des commandes son (décodée) |
| `ou_y.py` | plages de Y_DATA référencées par chaque module |
| `adx.py` | décodeur ADX et extraction WAV |
| `empreintes.py`, `identite.py`, `apparie_arcade.py` | appariement des flux entre eux et avec un enregistrement Z80 arcade ; résultats dans `appariement.txt`, `apparie_sfa1.txt`, `apparie_sfa2.txt`, `apparie_ro6.txt` |
| `gen_son_jeu.py` | rompath `sfa3ud` avec le Z80 et le QSound de SFA1/SFA2/ro6/ro7 (`rp_sfa1/`, `rp_sfa2/`) |
| `lance.sh`, `lua/son_hyper.lua` | Hyper au fork avec journal des commandes son (`PILE=1` : PC et pile ; `FORCEOCT` : octets imposés) ; utilise `hyper.lua` de l'agent ro9 |
| `codes_musique_hyper.txt` | liste des codes musique d'Hyper → flux Y_DATA |
| `essais/` | journaux (`*.son`, `*.log`, `inj_*.txt`, `rec_*.txt`) |
| `wav/` | extraits de 15 s et enregistrements Z80 SFA1/SFA2 (~300 Mo) |

`tmp/` (190 Mo de vidages EE, IOP et SPU2 extraits), `etats/` (copies de 3 états Hyper) et `iso/` (ELF) sont
supprimables.
