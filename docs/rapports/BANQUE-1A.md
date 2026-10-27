# Champ `$1A` des acteurs de fin et banques graphiques (arcade, Upper traduit, persos MAX)

Agent `agent_banque_1a`, 2026-10-10. Question posée par la session MAX (intégration d'Eagle, Maki, Yun et Ingrid en
`$26`-`$29` d'Upper, `ro5`).

## 0. Réponse courte

| frames affichées par l'acteur | valeur de `$1A` | qui la pose |
|---|---|---|
| frames du **perso MAX** (`F2x_n` via `FIN_ANIM_2x`, codes locaux à sa banque) | **`$4000`** si le perso MAX est J1, **`$6000`** s'il est J2 (`$C000` / `$E000` pour J3 / J4) | **personne côté MAX** : la partie commune `$4B` la pose déjà (Upper image `$47760` `JSR $31E9C`). Côté HSFA : 3 entrées par perso dans des tables (§3.1) |
| frames `FD..` du décor de fin MAX (`BANQUE_1A_DECOR_FIN`) | **`$8000`** (emplacement 4) | le code MAX (`fin_pas118`, déjà écrit) avec le symbole = `$8000` ; côté HSFA, une entrée par fin dans la table du chargeur de fin et dans `carte.txt` (§3.2) |
| explosion `EXPLO_PAS` (`FIN118X`, frames de `$2E50A0` n° 5) | **`$0000`** (emplacement 0 = banque commune), et non `$6000` | source MAX : `dc.w $6000` → `$0000` (ou un symbole HSFA), et `EXPLO_PAS` relogé sur la copie d'Upper (§3.3) |

Le tableau ci-dessous donne la règle de conversion. Sur la PS2 (et donc dans Upper traduit), `$1A` ne donne pas les
bits hauts du code de tuile : ses bits 13-15 désignent l'**emplacement de banque** (`$2000 × n`).

| arcade (`$1A` = bits 16-17 du code CPS2) | PS2 / Upper traduit (`$1A` = emplacement × `$2000`) |
|---|---|
| `T[$7F]` (table par perso `$2FC94`) | emplacement du **joueur** qui a ce perso : `$4000` J1, `$6000` J2 |
| `#$6000` (fenêtre `$30000`, sprites communs) | `$0000` : emplacement 0, banque commune `e351` |
| `#$2000` (fenêtre `$10000`) | `$2000` : emplacement 1, mémoire de décor `e353` |
| — | `$8000` : emplacement 4, graphismes de fin chargés avec `$C0BC(A5)` (acteurs d'Upper au sous-type ≥ `$80`) |

**Correction d'une prémisse de la question.** La partie commune `$4B` **pose** `$1A`. Elle le fait dans son état 0,
par `JSR $2FC88` en arcade et par `JSR $31E9C` dans Upper traduit. La routine `$AA630` ne le pose pas (sauf le
préambule ajouté par Upper pour les sous-types ≥ `$80`).

## 1. Arcade SFA3 : comment un acteur `$4B` obtient la banque de son perso

C'est une **table par perso**, lue à l'initialisation de l'acteur. Les adresses sont dans `work/cps2/sfa3_prog.bin`
(vue des opcodes), désassemblées avec `unidasm`.

- **Partie commune `$A7562`** : table d'états en `$A756E`.
  - État 0 (`$A7576`) : l'acteur attend que `$78(A6)` ≤ `$1C8(A5)`.
  - Initialisation (`$A7586`) : `$4 += 2`, `$26 = 0`, `$E = 0`, puis `BSR $AA5D2`. Ensuite :
    - si `$76(A6) ≠ 0` : `JSR $AADAC` (acteur lié à un joueur) ;
    - sinon : **`$A75B0 MOVE.B $7F(A6),D0 ; $A75B4 JSR $2FC88`**, puis `MOVE.B $70(A6),D0 ; BSR $AA630`.
  - Puis aiguillage par sous-type (`$A75C6`, table `$A75D4`).
- **`$2FC88`** : `EXT.W D0 ; ADD.W D0,D0 ; MOVE.W $2FC94(PC,D0.W),$1A(A6) ; RTS`. La table **`$2FC94`** (32 mots,
  indexée par l'id du perso) contient :

```
00 0000  01 0000  02 0000  03 0000  04 0000  05 4000  06 4000  07 4000
08 0000  09 2000  0A 0000  0B 4000  0C 0000  0D 4000  0E 4000  0F 0000
10 4000  11 0000  12 0000  13 0000  14 4000  15 4000  16 4000  17 0000
18 0000  19 6000  1A 6000  1B 6000  1C 6000  1D 6000  1E 4000  1F 4000
```

  32 sites appellent `JSR $2FC88`. Parmi eux : `$A75B4`, les variantes `$4F` (`$AA942`, `$AAA5A`, `$AB0D2`, `$AB3E8`,
  `$AB434`, `$AC244`-`$AC3EA`), et des créateurs dans `$75430`-`$B2A4A`.
- **`$AA630`** ne touche pas `$1A` : `D1 = $7F(A6)×4 ; MOVEA.L $AA63C(PC,D1.W),A0 ; JMP $1B6E0`. La table `$AA63C`
  donne l'animation par perso ; c'est l'homologue de `T_619b50`.
- **Rendu** : 8 routines font `OR.W $1A(A6),D1` sur le mot Y (`$20FFE`, `$2106E`, `$21126`, `$211BE`, `$21606`,
  `$21640`, `$21690`, `$216DC`). La CPS2 calcule `code = mot code + ((Y & $6000) << 3)` (MAME `cps2.cpp` l. 940),
  donc `$6000` donne `$30000`.
- **Valeurs constantes** : 174 `MOVE.W #imm,$1A(A6)` (104 × `$6000`, 68 × `$2000`, 2 × `$0000`). Exemple :
  l'explosion `$A07DC` (`MOVE.W #$6000,$1A(A6)`, puis `$A0814 MOVEQ #5 ; LEA $2E50A0`).

**Relevé à l'exécution** (MAME `sfa3ud`, copie des ROM) : les acteurs `$4B` naissent avec `$1A = 0`. Après leur
initialisation, ils portent `T[$7F]` :
- fin de Blanka : `7F=19 → 6000`, Sakura `7F=0D → 4000`, Dan `7F=0C → 0000` ;
- fin d'Adon : `7F=05 → 4000` ;
- fin de Ryu : `7F=00/0A → 0000`.

Fichiers : `releve_arc_19.txt`, `releve_arc_05.txt`, `releve_arc_00.txt`.

## 2. Upper traduit (`ro5`, banc MAME / fork)

### 2.1 Mécanisme PS2 : des banques chargées par emplacement

L'objet du portage a la forme X, Y, code local, attributs. Les **bits 13-15 de Y** désignent l'emplacement de banque
(§82, §83), et le code de tuile est **local** à cette banque. Le moteur natif en tient la table (§124, `ctx` =
`0x1DC2B0`). Contenu des emplacements :

| emplacement | contenu (Upper) | chargé par |
|---|---|---|
| 0 | banque commune `e351` | démarrage |
| 1 | mémoire de décor `e353` (HUD, `plan2`) | décor |
| 2 / 3 | banque du perso de J1 / J2 : table `0x628320[perso]` (`e355`-`e386`, 40 entrées) | chargeur par perso `0x4113A0` |
| 4 | graphismes du couple (gfx, anim) dont l'animation est en `$C0BC(A5)` = `$FF40BC` | chargeur de fin `0x4114A0`, table `0x6283C0` (gfx 391-418 / anim 458-485), index = n° de fin |
| 6 / 7 | joueurs 3 / 4 | |

**Le choix de l'emplacement (`$1A`) a été réécrit par le portage.** C'est la routine homologue de `$2FC88` : MIPS
`0x16BE90` (PS2 `0x35BE90`), image traduite `$31E9C`. Elle est appelée par la partie commune `$4B` traduite (image
`$4775C MOVE.B $7E(A6),D0 ; $47760 JSR $31E9C`, MIPS `0x1EFEE8`) :

```
D0 = T_61c0e0[perso]                       ; « propriétaire » de banque (variantes -> perso de base)
si T_61c0e0[$FF8503 (J1 +$102)] = D0 : D1 = $4000
sinon si T_61c0e0[$FF8903 (J2)]   = D0 : D1 = $6000
sinon si T_61c0e0[$FF8D03 (J3)]   = D0 : D1 = $C000
sinon si T_61c0e0[$FF9103 (J4)]   = D0 : D1 = $E000
sinon D1 = 0
MOVE.W D1,$1A(A6)                          ; image $31F66
```

Preuve MIPS : `lb $502(A5)`, puis `lui 0x62 ; addiu 0xC0E0` (= `0x61C0E0`).

`T_61c0e0` (PS2 `0x61C0E0`, image `$B2420`, octets XOR 1) :

```
00-11 identité, 12→04, 13→11, 14→06, 15, 16, 17→00, 18-23 identité, 24→02, 25→15, 26→00, 27→1E,
puis 8 octets à 0 (bourrage, image $B2448-$B244F), table suivante T_61c110.
```

La même routine existe dans les trois modules :

| module | routine MIPS | table | image traduite | appelants MIPS |
|---|---|---|---|---|
| SFA3 `ro3` | `0x125C80` | `T_58c950` | `$289CA` | 14 |
| Upper `ro5` | `0x16BE90` | `T_61c0e0` | `$31E9C` | 14 |
| Hyper `ro9` | `0x2E7F70` | `T_5b5bb0` (128 entrées, indexée par `$102` = perso + version) | `$71D42` | 4 (la partie commune `$4B` n'existe pas dans Hyper) |

**`$AA630` d'Upper** (image `$4B52A`, MIPS `0x20E444`) :
- `TST.B $2(A6)` (sous-type) ; si le bit 7 est à 1 : `MOVE.W #$8000,$1A(A6)` (`$4B530`), `A0 = $C0BC(A5)`,
  puis `JMP $AFA58` ;
- sinon, corps arcade avec `T_619b50[$7E]` (`$4B54E`).

Upper traduit compte 13 `MOVE.W #$8000,$1A(A6)` : ce sont les acteurs de fin que le portage a ajoutés.

**Conversion des constantes** (comptage statique, puis vérification à l'exécution) :
- arcade `$E000→$18 ; $6000→$1A` 40 fois ↔ Upper `$E000→$18 ; CLR $1A` 41 fois ;
- `#$6000` 104 ↔ `CLR.W` 117 ;
- `#$2000` 68 ↔ 66.

### 2.2 Reproduction par le banc (et FBNeo)

`banc_sprites.lua` relit la liste brute du jeu. Pour chaque objet, il prend la table de l'emplacement `(Y >> 13) & 7`,
éclate l'objet en tuiles 16×16 et convertit chaque code local en code global :
- codes `$40000+` pris dans `hsfa_gfx.bin` (fork) ;
- bits 16-17 du code → Y 13-14, bits 18-19 → X 10-11.

Tables utilisées :
- e0 = `BANC_COMMUN` (351) ;
- e1 = `plan2` (`banques_hx/plan2.bin`, écrit par `hsfa_plans.py`) ;
- **e2 / e3 = `perso[$FF8503]` / `perso[$FF8903]`** : lignes `perso id fichier` de `banques_hx/carte.txt`, tirées de
  `0x628320` × 40 ; `$26` et `$27` → 355 ;
- **e4 = `anim[mem:read_u32($FF40BC)]`** : lignes `anim ptr gfx`, tirées des paires des chargeurs, dont la table de
  fin `0x6283C0` × 40 ;
- e6 / e7 = J3 / J4 si leur structure est active.

FBNeo (`cps_hsfa.cpp`, `HsfaEmplacements`) fait exactement la même chose à partir de `hsfa_tab.bin`. `HsfaPerso[256]`
et `HSFA_MAXFILE` 4096 imposent des numéros de fichier numériques.

Le chargeur de fin est un talon (`mame_test.py`, `afin`, site `0x272D50`) :
- `index = $87F1(A5)` ;
- `CMPI.W #40 ; BCC` : **au-delà de 40 entrées, `$C0BC` n'est pas écrit** (l'emplacement 4 garde l'ancien
  fichier) ;
- sinon `MOVE.L table[index],$C0BC(A5)`.

### 2.3 Relevé de la RAM des acteurs pendant une fin (fork `sfa3hx`, copie des ROM)

`releve_fin.lua` charge `tournee.lua` puis, pendant `$FF8004 = $000A`, relève toutes les 20 images :
- le réservoir `$FFB000` (32 × `$80`) ;
- `$FF40BC` ;
- les persos de J1 et J2.

Fin de **Guile** (`$20`, absent de l'arcade ; `releve_ro5_20.txt`) :
- `7F=20 → 1A=4000` (J1 = Guile, emplacement 2) ;
- `7F=0A → 6000` (Bison = J2, emplacement 3 ; en arcade, Bison vaut `0000`) ;
- `7F=03/04` avec un sous-type `80/81/9C/CE` → `8000` (emplacement 4) ;
- `$C0BC` = `9AF000C1` → `anim … 415` dans `carte.txt` ;
- la liste brute contient 9 à 11 objets de l'emplacement 4 par image.

Fin de **Ryu** (`releve_ro5_00.txt`) :
- `7F=00 → 4000`, `7F=0A → 6000`, Ken `7F=01 → 8000` ;
- `$C0BC` = `000000C0` → gfx 391.

Fin de Ryu, **arcade et Upper face à face**, mêmes acteurs de décor (classe / sous-type) :

| acteurs | arcade | Upper |
|---|---|---|
| `49/00`, `49/01`, `49/03`, `49/1F`, `4F/01`, `4F/02`, `4F/0F`, `4F/11-13` | `1A=6000` | `1A=0000` |
| `4E/00`, `4F/04` | `2000` | `2000` |

Le relevé confirme donc la conversion `$6000 → $0000`.

## 3. Ce qu'il faut pour un perso MAX en `$26`-`$29`

### 3.1 Frames du perso (banque gfx du perso MAX, emplacement 2/3)

- **Valeur** : `$4000` si le perso MAX est J1, `$6000` s'il est J2. Elle n'est pas constante, donc **le code MAX ne
  doit pas écrire `$1A`** pour ces frames.
- **Qui la pose** : la partie commune `$4B` (`$31E9C`), à condition que l'acteur ait `$76 = 0` et `$7F` = id MAX.
  C'est déjà le cas des fils créés par le code MAX (`clr.b $76(a4)`, `move.b $7f(a6),$7f(a4)`), qui naissent à
  l'état 0.
- **À fournir par HSFA (« entrée par banque » à côté de `T_619b50`)** :
  1. **`T_61c0e0[$26..$29]` : propriétaires distincts.** Aujourd'hui `$26→00` et `$27→1E`. Pour `$28/$29`, la table
     lit le bourrage (`00`), ce qui confond le perso MAX avec Ryu, Evil Ryu ou Juli. Exemples d'erreur :
     - perso MAX en J2 avec un Ryu en J1 ;
     - acteur de Ryu dans la fin de Yun, qui reprend des scènes de Ryu.

     **Pas besoin de déplacer la table** : `$26/$27` sont en place et `$28/$29` tombent dans le bourrage. Octets de
     l'image (XOR 1) : `$26`→`$B2447`, `$27`→`$B2446`, `$28`→`$B2449`, `$29`→`$B2448`.

     Contrainte : le compteur par perso `$C26C(A5) + côté×40 + propriétaire` (image `$5A1C4`, `MULS.W #40`) exige un
     propriétaire < `$28`. Proposition : **Eagle `$26`, Maki `$27`, Yun `$24`, Ingrid `$25`**. Les valeurs `$24`/`$25`
     ne servent de propriétaire à personne, car Shin Akuma → `02` et `$25` → `15`.
  2. **Table perso → banque** (`0x628320`, 40 entrées). Dans le banc et FBNeo : lignes **`perso 38..41 N`** dans
     `carte.txt` / `hsfa_tab`, avec `N` numérique < 4096, `f<N>.bin` (local → code étendu) et les tuiles dans
     `hsfa_gfx.bin`. Les lignes `$26/$27` actuelles (→ 355) sont à remplacer.
  3. `T_619b50` à 42 entrées → `FIN_ANIM_26..29` (déjà relevé dans CONV-MAX §9).
- **Précaution** : la partie commune ne pose `$1A` qu'à l'initialisation. Un acteur qui passe des frames `FD..`
  (`$8000`) à des frames du perso doit rétablir `$1A`. Il peut rappeler `$31E9C` avec `D0 = $7F`, un symbole à
  exporter car l'adresse change à chaque construction, ou recopier une valeur sauvegardée.

### 3.2 Emplacement 4 : frames `FD..` du décor de fin (`BANQUE_1A_DECOR_FIN`)

- **Valeur : `BANQUE_1A_DECOR_FIN equ $8000`.** C'est le même schéma que les acteurs de fin d'Upper (`$AA630`,
  bit 7). La valeur est constante et ne dépend pas du côté, donc **le code MAX la pose** (`fin_pas118`, déjà écrit) ;
  HSFA définit le symbole.
- **Le contenu de l'emplacement 4 est l'affaire d'HSFA** : une entrée par fin MAX.
  1. Agrandir la table du talon de fin (`afin` dans `mame_test.py`, issue de `0x6283C0`) à **42 entrées**. Pour
     `$26-$29`, il faut un pointeur unique ; aujourd'hui l'index ≥ 40 laisse `$C0BC` intact. Valeur conseillée :
     `swapped(FIN_ANIM_2x)`. C'est une vraie table d'animations, au format `$AFA58`, et elle traverse `CONV_An`
     inchangée. Un acteur d'Upper au sous-type ≥ `$80` lirait ainsi une table valide.
  2. Une ligne **`anim <read_u32($FF40BC)> <N_fin>`** par fin MAX dans `carte.txt` / `hsfa_tab`, plus
     `f<N_fin>.bin` : la tuile locale `i` = la `i`-ième tuile de
     `~/.cache/sfa3max/converti/plXX/fin/decor/tuiles.bin`, avec les codes dans `hsfa_gfx.bin`. Tailles : Eagle
     1 843, Maki 389, Yun 608, Ingrid 1 336 tuiles.
- Pendant une fin MAX, l'emplacement 4 ne contient que ce décor : tout acteur d'Upper au sous-type ≥ `$80` y
  afficherait n'importe quoi. Les fins MAX n'en créent pas.

### 3.3 Explosion (`FIN118X`, Maki et Yun)

`dc.w $6000` (« comme l'arcade `$A0814` ») est **faux dans Upper** : `$6000` y désigne l'emplacement 3, c'est-à-dire
la banque du perso de J2. La valeur juste est **`$0000`** (banque commune `e351`), comme pour les 40 sites arcade
« `$6000` » qu'Upper a rendus en `CLR` (§2.1, §2.3).

`EXPLO_PAS` doit en outre viser la **copie d'Upper** du pas `$2E565C` : ses frames ont des codes locaux à `e351`. Ce
n'est pas l'adresse arcade. Responsable : la source MAX (`acteurs_fins_main.s`, table `FIN118X`), de préférence avec
un symbole HSFA (`BANQUE_1A_COMMUN equ 0`) ; HSFA reloge `EXPLO_PAS`.

### 3.4 Base finale Hyper (`ro9`, voie B)

**Ce qui ne change pas** : la même routine existe (`0x2E7F70`, image `$71D42`). Les valeurs de `$1A` restent les
mêmes (`$4000`/`$6000` pour le perso, `$8000` pour le décor de fin, `$0000` pour l'explosion), car la sémantique des
emplacements vient du même moteur de portage.

**Ce qui change :**
- **Table de propriétaires** : `T_5b5bb0` (128 entrées, indexée par `$102` = perso + version). `[$26..$29]` existe
  déjà (bloc ZERO 3 `$00-$2F`, `$28-$2F` = 0). On écrit en place des propriétaires distincts. `$26-$29` sont libres
  dans Hyper (propriétaires utilisés : `00-23`, `1E`, `30-3C`, `40-52`, `60-72`, `7E`). Il reste à vérifier les
  autres usages (MIPS `0x2D8B0`, `0x2D928` avec `+$28`, `0x2EDA0`, `0xA1F38`). Si le compteur d'Upper (`$C26C`,
  40 par côté) est greffé, il débordera de toute façon avec les versions d'Hyper.
- **Banques par perso** : table `0x5AF1B0` × 128 (`carte.txt` de ro9 : `$26-$2F` → 355). Ajouter `perso 38..41 N`
  pour le pilote `sfa3hhsfa`.
- **Absents d'Hyper, à greffer (lot « fins » de la voie B)** :
  - la partie commune `$4B` (le seul appelant `$4B` d'Upper, `0x1EFEE8`, n'a pas d'homologue) ;
  - `$AA630` (« nouvelle » dans ETUDE-UPPER-HYPER §4.1) et `T_619b50` ;
  - le chargeur de fin `0x4114A0` et la table `0x6283C0`. Hyper n'écrit jamais `$C0BC`. Le talon se greffe tel quel,
    avec les entrées MAX.
- **Banc et FBNeo d'Hyper** :
  - `BANC_PTR_ANIM=FF40BC` et des lignes `anim`, aujourd'hui **0** dans `work/mame_ro9/banques_hx/carte.txt` ;
  - fichiers de fin 391-418 et décors MAX dans la ROM graphique étendue ;
  - emplacement 0 = `e545` (`BANC_COMMUN=545`) : vérifier que les frames de l'explosion existent dans `e545` et
    reloger `EXPLO_PAS` sur la copie d'Hyper.

## 4. Fichiers de ce dossier

- `releve_fin.lua` : relevé des acteurs et des emplacements pendant la fin, chargé après `tournee.lua` (lecture seule
  de la RAM).
- `lance.sh arc|ro5 PERSO [NF]` : lancement sur les **copies** des ROM (`roms_arc/`, `banc_ro5/`), avec des dossiers
  nvram et cfg temporaires et sans `-state`.
- `releve_arc_{00,05,19}.txt`, `releve_ro5_{00,20}.txt` : relevés ; `out_*.txt` : journaux de `tournee.lua` (toutes
  les parties ont atteint leur fin).
- `ro5_prog.bin` : programme traduit d'Upper remis bout à bout (ROM du 2026-10-10 19:01, `sz3ud.03c`
  `a296538f…`), pour `unidasm`.
