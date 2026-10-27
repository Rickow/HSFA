# Greffe du mode Arcade d'Upper dans Hyper (voie B) — étapes préparatoires 1 à 7

Agent « greffe_arcade », 2026-10-10. Base : `work/etude_upper_hyper/ETUDE-UPPER-HYPER.md`.

**Périmètre.** Tout est dans `<workspace>/work/greffe_arcade/`. Rien n'a été modifié ailleurs. `mame_ro5`, `mame_ro9`,
`src/hsfa` et les scripts Lua de `work/mame` ont seulement été lus. MAME a toujours été lancé avec
`nice -n 19`, `-nvram_directory` et `-cfg_directory` propres, sans `-state`, sans `pkill`. Aucun commit.

**Conventions.** Comme l'étude :
- `ro5` = Upper, `ro9` = Hyper ;
- va MIPS en **fichier**, données en **exéc.** (fichier + `0x1F0000`) ;
- champs en numérotation PS2 (`$102` = `$0103` dans la traduction 68K) ;
- « routine » = grain `GRAIN=routine` de `carto_ro9` ;
- tailles en octets de MIPS, « instr. » = instructions 68K (`n68`).

---

## 0. En bref

1. **Scènes nommées** à partir de 7 parties tracées au fork : 3 gagnées, 2 perdues, 1 VERSUS en boucle (Upper) et 2 parties d'Hyper.
   - `A5+4 = 6` est le **CONTINUE**, `8` le **GAME OVER**, `A` la **fin du perso + le générique**, `C` la **sortie**.
   - Les écrans entre deux combats restent en `A5+4 = 4`. `A5+8` y vaut `0` (init du match), `2` (carte / NEXT STAGE),
     `4` (face-à-face, puis écran VS), `6` (combat) et `8` (pose de victoire + citation).
2. **Liste mesurée des routines d'Upper exécutées en Arcade** :
   - Arcade : **4 719 routines**. VERSUS : 1 703. **Arcade seulement : 3 078**, dont la plupart sont du code de persos
     adverses, présent dans Hyper.
   - **Cœur à greffer** (absent ou modifié dans Hyper, hors attraction, moteur de combat et code des persos) :
     **530 routines, 287 Ko de MIPS, ≈ 9 950 instr.**
   - Dont **absentes d'Hyper : 164 routines, 111 Ko**. Le reste (176 Ko) est modifié par Hyper : à trier par retouche ou
     par copie.
   - La fourchette de l'étude (100-260 Ko) se confirme : l'absent correspond aux 98 Ko de son cœur, le total à sa borne
     haute.
   - Fait nouveau : **109 routines du cœur (91 Ko) tournent aussi en VERSUS dans Upper**. Upper y partage par exemple
     `0x2615D0`, `0x24F9D0` et `0x250EF0`. Hyper les a remplacées par son propre déroulé VERSUS.
3. **Table de relogement A5** : **443 déplacements** utilisés par le cœur.
   - 257 sont communs (identité).
   - 7 sont décalés (blocs `$C392-$C39D` +`$10`, `$C3A7-$C3A9` +`$13`).
   - **133 sont propres à Upper et gardés tels quels** : ils sont libres dans Hyper, preuve statique et dynamique.
   - **36 sont relogés** (23 blocs, 2 235 o) dans la zone libre **`$FF43BE-$FF7FFF`** d'Hyper.
   - 8 sont des champs de structure J1/J2 et 2 sont à vérifier.
4. **Données** :
   - 198 constantes de données visées par le cœur : 22 réutilisables telles quelles dans Hyper, 176 à copier
     (≈ 104 Ko, bornes encore grossières) dans un **bloc ajouté servi par le traducteur** (exéc. `0xE80000`).
   - Fichiers de fin : gfx 391-418 (1,8 Mo compressés) et anim 458-485 (28 fichiers, 130 Ko décompressés). Les banques
     `f391-f418` et les 34 lignes `anim` de `banques_hx/carte.txt` existent pour Upper, pas pour Hyper.
5. **`$102`** :
   - **49 accès dans le code greffé** : 13 CMP, 12 INDEX, 10 COPIE, 10 ÉCRITURE, 4 à examiner ;
   - 42 accès dans les routines d'Hyper réutilisées sur le chemin.
   - Règle : lecture qui indexe une table par perso ou compare à un id de base → **`$116`** ; écriture de l'id
     (adversaire CPU, boss) → **poser aussi `$116/$117`** ; copie → garder `$102` (la version) et recopier `$116/$117`.
6. **Outil de greffe MIPS : prototype fonctionnel.**
   - Zone d'accueil : le **Z80 recompilé d'Hyper, fichier `[0x20, 0x22B00)`** (141 984 o), jamais traduit et jamais
     visé par le 68K d'Hyper. L'en-tête du module n'est pas touché (piège du mot 6).
   - Prototype : `0x250EF0` (prochain adversaire) et ses deux appelés absents d'Hyper, `0x24F9D0` et `0x24F020`.
     Soit 6 928 o de MIPS, 17 relogements A5, 16 `lui` relogés et 8 tables copiées.
   - **Assemblage complet du module augmenté : 0 non résolu.**
   - La traduction 68K de la greffe est **identique instruction pour instruction** à celle d'Upper (213 = 213),
     à part les 34 déplacements A5 relogés voulus.
   - Le reste du module ne diffère du témoin que par 113 constantes d'adresse de code (décalage dû à la greffe).
   - Le témoin, construit avec la copie du traducteur sans greffe, est **identique octet pour octet** à la construction
     de référence d'Hyper (son compris).
   - Un défaut du traducteur a été trouvé et corrigé dans la copie : une `LEA table(PC,Dn)` vers un bloc ajouté était
     perdue (§6.4).
7. **Décors** : **39 décors d'Upper sur 40 manquent dans Hyper**, données et graphismes. Seul `$4E` y est : c'est le
   décor ZERO 3 d'Hyper.
   - Il faut 40 000 tuiles de plans et ≈ 75 Ko de code de décor en plus de la greffe.
   - Plan proposé : numérotation unique (`$00-$4E` Upper, `$50-$72` SFA2, `$78-$7C` Hyper), table perso → décor de
     128 octets, `$C178` forcé à 0 hors décors d'Hyper.
   - Un seul outil d'injection paramétré par module (§7).

---

## 1. Étape 1 — scènes Arcade d'Upper

### 1.1 Traces (fork `cps2f sfa3hx`, construction d'Upper **figée** dans `fige/ro5`)

Toutes les traces suivent le modèle de `nonreg_ro5.sh`. Le script est `lua/tournee_greffe.lua`, une copie de
`tournee.lua` avec ces ajouts :
- `PERDRE=1` : J1 passif, vie à 1 ;
- `CONTINUE=1` : Start sur l'écran CONTINUE ;
- `VSBOUCLE=1` : boutons hors combat en VERSUS ;
- journal des mots `$FF8000-$FF800E` ;
- prise sur l'espace **opcodes** (mot lu → première image, par état `A5+0/+4/+8/+C`) ;
- captures par état.

| trace | partie | images | combats (manches) | scènes vues |
|---|---|---|---|---|
| `gagne00` | Ryu, gagnée | 58 000 | 21 | 2, 4, A (41 607), 8 (53 387), C (53 521) |
| `gagne04` | Chun-Li, gagnée | 70 000 | 23 | 2, 4, A (52 851), 8 (62 797), C |
| `gagne02` | Akuma, gagnée | 70 000 | 33 | 2, 4, A (38 991), 8 (41 956), C |
| `perdu00` | Ryu, perdue, CONTINUE accepté | 26 000 | 10 | 6 → 0 → 2 (×5) |
| `perdu_go` | Ryu, perdue, sans continue | 9 000 | 2 | 6 (4 433), 8 (6 981), C (7 121) |
| `versus` | VERSUS 2 joueurs en boucle | 30 000 | 29 | 2, 4, E |
| `vues00` | Ryu, captures entre les combats | 16 000 | — | — |
| `h_versus`, `h_training` | **Hyper** (`fige/ro9`), VERSUS 20 sélections / TRAINING | 40 000 / 12 000 | 39 / 1 | carte RAM et couverture |

⚠ **Piège rencontré.** `mame_ro5` et `mame_ro9` ont été reconstruits par une autre session pendant les premières traces
(18 h 58 - 19 h 02 : intégration du bloc son). La carte d'image ne correspondait plus à la ROM chargée. J'ai donc
**figé une copie** (ROM programme, `carte_image.txt`, `ext_*.bin`) dans `fige/ro5` et `fige/ro9`, avec le md5 des ROM
programme dans `md5_prog.txt`, puis j'ai tout relancé dessus.

Conseil : toute trace d'exécution doit utiliser une construction figée.

### 1.2 Noms (captures : `traces/planche_perdu.png`, `planche_fin.png`, `planche_entre_combats.png`)

| `A5+4` | gestionnaire Upper (`T_61C1E0`) | Hyper (`T_5B5E80`) | rôle mesuré | durée |
|---|---|---|---|---|
| 0 | `0x261210` | `0x96330` | init du mode | 1 image |
| 2 | `0x261470` → `0x2524B0` | `0x96590` | sélection | — |
| 4 | `0x261560`, sous-table `T_61C200` par `A5+8` | `0x96620`, `T_5B5EA0` | partie : écrans d'entre-combats **et** combats | — |
| 4 / `A5+8=0` | `0x2615D0` | `0x96690` | init du match (adversaire, décor, musique) | 1 image |
| 4 / 2 | `0x265050` | `0x9A2C0` | présentation du perso (1er combat), puis **carte / NEXT STAGE** (liste des adversaires, PRESS START) | ≈ 2 500 images |
| 4 / 4 | `0x265120` | `0x9A390` | **face-à-face** (dialogue, PRESS START), puis **écran VS** (`A5+C = 2`) et entrée dans le décor (`A5+C = 4`) | ≈ 700 |
| 4 / 6 | `0x265440` | `0x9A680` | **combat** (`A5+C` = 0…E par manche) | — |
| 4 / 8 | `0x26F930` | `0xA08A0` | **après le match** : pose de victoire et citation (`A5+C = 6`), fondu (`C`) | ≈ 400 |
| 6 | `0x2614A0` → `0x24A480` (`T_61BC60`, 5 états) | **RTS** `0x965C0` | **CONTINUE** : `A5+8` = 0/2/4 init, **6 = compte 9 → 0** (≈ 2 540 images), 8 = continue accepté → sélection | 2 540 |
| 8 | `0x2614D0` → `0x24B050` (`T_61BC80`, 6 états) | **RTS** `0x965D0` | **GAME OVER** (« TRY AGAIN »). On y arrive après un continue refusé **et** après le générique | 125-140 |
| A | `0x261500` → `0x2A300` (`$148(A5)`, `T_60B380`) | **RTS** `0x965E0` | **fin du perso + générique**. Commence par l'entrée au classement (« 1st A___ »). `A5+8=2`, `A5+C=4` | 3 000-11 800 |
| C | `0x270920` (natives `0x407EC0`, `0x4077C0`) | `0xA0DD0` | **sortie** (écran noir), puis retour à `A5+0 = 0` (titre) | 29-36 |
| E | `0x261530` → `0x40CF70` | `0x965F0` → `0x2D550` | RÉSULTAT VERSUS | — |

L'hypothèse « 6 = continue » de l'étude est confirmée. Celle du « 8 = classement » doit être précisée : 8 est l'écran
GAME OVER, commun aux deux issues. Le classement (entrée du nom) est au début de la scène A.

`donnees/scenes_routines.txt` donne, pour chaque scène, les routines qui y sont exécutées pour la première fois et la part
à greffer. Exemples : continue 60 routines (26 à greffer), game over 43 (22), fin 220 (75), carte/NEXT STAGE 160 (80).

---

## 2. Étape 2 — routines exécutées en Arcade, jamais en VERSUS (mesure)

### 2.1 Méthode (`outils/couverture.py`, `outils/liste_arcade.py`)

- Le mot lu sur l'espace opcodes donne une instruction de `carte_image.txt` (figée), puis une va MIPS, puis une
  routine.
- **Préchargement du 68000** : un mot lu dans les 4 premiers octets d'un bloc qui suit le bloc d'une autre routine ne
  compte pas.
  - Toute vraie exécution d'un bloc de 6 octets ou plus lit un mot au-delà.
  - Les routines dont tous les blocs font 4 octets ou moins sont « courtes, indécidables » (256 en Arcade seul).
- Présence dans Hyper : couverture K=12 de l'étude (absent < 50 %, modifié 50-90 %, présent ≥ 90 %) et partenaire
  `inverse_ro5`.
- Le partenaire est dit « vivant » quand il est exécuté par Hyper (`h_versus` ou `h_training`).

### 2.2 Résultats

| | routines | Ko MIPS |
|---|---|---|
| exécutées en Arcade (5 parties) | 4 719 | — |
| exécutées en VERSUS | 1 703 | — |
| **Arcade seulement** | **3 078** | — |
| … dont présentes dans Hyper (identiques, à réutiliser) | 2 119 | 603 |
| … dont moteur / persos présents (on garde Hyper) | 288 | 175 |
| … dont moteur / persos absents ou modifiés, en combat seulement (on garde Hyper) | 48 | 42 |
| … dont modifiées dont l'homologue proche tourne dans Hyper (on garde Hyper) | 20 | 7 |
| … dont **à greffer** | 421 | 197 |
| … dont natives (code C du portage) | 182 | 9 |

La décision par routine est dans `donnees/liste_arcade.tsv` : toutes les routines vues en Arcade, avec le drapeau
VERSUS, la zone arcade, la couverture, le partenaire, le partenaire vivant, les scènes et la première image. Les
règles :

| décision | règle |
|---|---|
| `REUTILISER` | présente (≥ 90 %), classe identique / identique 68K / déplacements |
| `garder Hyper (moteur/persos)` | zone arcade « code des persos » ou « moteur de combat », exécutée **seulement en combat** |
| `garder Hyper (homologue proche exécuté par Hyper)` | modifiée, partenaire quasi identique ou 70-90 %, exécuté par Hyper |
| `GREFFER` | le reste des absentes ou modifiées. `[combat seul]` = vue seulement pendant `A5+8 = 6` |

Le moteur de fin (interpréteur de scripts, arcade `$25E10-$26FB8`) est rangé par l'alignement dans « moteur de
combat ». Il tourne pourtant **hors combat**. 37 de ses routines (28 Ko) sont donc dans le cœur à greffer.

**Cœur à greffer** (`donnees/coeur_greffe.pkl` / `.tsv`) : routines `GREFFER`, attraction exclue.

| | absentes d'Hyper | modifiées par Hyper |
|---|---|---|
| Arcade seulement | 122 r., 73,9 Ko, 2 778 instr. | 299 r., 123,0 Ko, 4 335 instr. |
| partagées avec VERSUS dans Upper (« variante Arcade ») | 42 r., 37,0 Ko, 1 201 instr. | 67 r., 53,5 Ko, 1 637 instr. |
| **total** | **164 r., 110,8 Ko** | **366 r., 176,5 Ko** |

Total : **530 routines, 287 Ko, ≈ 9 950 instr.** L'attraction (démonstrations, intro), absente d'Hyper, est exclue :
184 routines, 76,5 Ko.

Par zone arcade, le cœur se répartit ainsi (`donnees/liste_arcade_zones.txt`) :
- objets / écrans `$80000+` : ≈ 150 Ko, en grande partie modifiés ;
- flux de jeu `$8000-$DFFF` : 75 Ko ;
- sélection : 21 Ko ;
- système / affichage : 14 Ko ;
- code propre à Upper : 28 Ko ;
- moteur de fin : 28 Ko.

Les routines nommées par l'étude sont toutes dans le cœur : `0x2615D0`, `0x269340`, `0x24F9D0`, `0x250EF0`, `0x2519A0`,
`0x251AC0`, `0x272B90` et `0x2A300`. Parmi elles, `0x2615D0`, `0x269340`, `0x24F9D0` et `0x250EF0` tournent aussi en
VERSUS.

### 2.3 Vérification des routines « réutilisables » (`outils/verifie_reutil.py`)

La classe « identique » de l'étude masque les constantes. Les instructions des 1 633 routines `REUTILISER` du chemin
Arcade (hors persos, moteur et attraction) ont donc été alignées une à une, et chaque constante comparée après
relogement :

| verdict | nombre |
|---|---|
| identique après relogement | **916** |
| longueur ou forme différente (partenaire inexact) | 213 |
| **douteuse** | 504 : 219 appellent un appelé qu'Hyper a modifié (souvent normal) ; **384 lisent des données différentes** |

Exemples de douteuses :
- `0x24A480` (corps de la scène 6) et `0x24B050` (scène 8) sont « identiques » à `0x62390`, mais lisent `T_61BC60` /
  `T_61BC80` d'un côté et `0x5B41E8` de l'autre ;
- `0x261210` (init du mode) diffère par trois appels.

→ Les 384 routines qui lisent d'autres données sont à greffer ou à brancher sur les tables greffées, au cas par cas
(`donnees/verifie_reutil.tsv`).

---

## 3. Étape 3 — table de relogement A5 (`outils/relogement_a5.py` → `donnees/relogement_a5.tsv`)

### 3.1 Preuve de zone libre dans Hyper

- **Statique** (`outils/ram_statique.py`) : tous les accès A5 de ro9, **LEA comprises** (`addiu` sur la base A5 ; la
  table de l'étude ne comptait que les accès mémoire), sur **tout** le code. Cela inclut le code C du portage et
  `0x28C30`. S'y ajoutent les constantes absolues de RAM. Ces dernières sont presque inexistantes : le 68K adresse la RAM
  par A5 ou par pointeur.
- **Dynamique** (`lua/ram_hyper.lua`) : prises lecture/écriture sur `$FF0000-$FFFFFF` pendant `h_versus` (20 sélections,
  39 manches, écran RESULT contourné par `CONTOURNE_E`) et `h_training`.
  - Les accès faits par les scripts Lua, pendant les rappels de fin d'image, sont exclus.
  - Est « libre » un octet jamais lu par Hyper et jamais écrit après l'image 120 (effacement du démarrage toléré).
- **Côté Upper** (`u_gagne00`, `u_perdu00`, `u_versus`, même script) : étendue réelle des tableaux, et exclusion des
  octets qu'Upper touche en Arcade quand on choisit une destination.

### 3.2 Résultat

| décision | déplacements |
|---|---|
| commun (identité) | 257 |
| propre à Upper, **libre dans Hyper** (identité) | 133 |
| décalé (portage d'Hyper) : `$C392-$C39D` → +`$10`, `$C3A7-$C3A9` → +`$13` | 7 |
| **relogé** : lu/écrit par Hyper | 20 |
| **relogé** : effacé par Hyper (écrit, jamais lu) | 9 |
| **relogé** : collision `$C388-$C3BC` (`$C391`, `$C39E`, `$C39F`, `$C3A0`, `$C3A2`, `$C3A5`, `$C3A6`) | 7 |
| champ de structure J1/J2 (`$0400-$1FFF`, voir les champs A6) | 8 |
| même mot qu'une variable d'Hyper, à vérifier (`$000D`, `$000F` = octets du sous-état `A5+C`) | 2 |

- Les 36 relogés forment 23 blocs (2 235 o), tous placés dans **`$FF43BE-$FF4C8F`**. Cette plage commence juste après la
  dernière variable du portage d'Hyper (`$C3BC`).
- La zone libre fait 15 426 o en tout ; les zones libres d'Hyper totalisent 23 474 o (`donnees/zones_libres_hyper.tsv`).
- La parité est conservée (octets impairs sur des adresses impaires).

Principaux relogements :

| Upper | contenu | → Hyper |
|---|---|---|
| `$C0C0-$C12F` | liste des adversaires (§125-§126), 112 o | `$CB2E` |
| `$AA54` | classement (records) : 1 904 o, effacé par Hyper | `$C3BE` |
| `$0244-$0398` | travail des écrans d'entre-combats, collision avec des variables d'Hyper | `$CB9E-$CC7A` |
| `$C39E`/`$C39F`/`$C3A5`/`$C3A6` | adversaire, étape, rival | `$CC80`/`$CC83`/`$CC87`/`$CC8A` |

La table complète, avec les preuves (accès statiques, octets lus, octets écrits), est dans `donnees/relogement_a5.tsv`.
Le dictionnaire `{dép. Upper: dép. Hyper}` est dans `relogement_a5.pkl`.

---

## 4. Étape 4 — données Arcade à porter

### 4.1 Constantes visées par le cœur (`outils/donnees_greffe.py` → `donnees/donnees_greffe.tsv`)

- 198 constantes de données.
- **22 réutilisables** : même contenu dans Hyper, à une adresse connue.
- **176 à copier**, ≈ 104 Ko. Les bornes sont prises jusqu'à la constante suivante, avec un plafond de 8 Ko ; elles sont
  surestimées.
- Les longs à reloger sont surestimés eux aussi (3 237) : ce sont des candidats, pas des pointeurs prouvés.

### 4.2 Tables nommées par l'étude

| table (exéc. Upper) | taille | contenu / pointeurs | référencée par | service prévu |
|---|---|---|---|---|
| scripts de fin `0x60B22C-0x60BBCF` (+ `0x60BC2C`, 539 o) | 2 467 o | 146 pointeurs de code, 344 de données | moteur de fin `0x29DE0-0x319D0` | copie, pointeurs relogés vers le moteur de fin greffé |
| table de la scène A `0x60B380` (`$148`) | 32 o | 5 pointeurs de code | `0x2A300` | copie (`T_e80xxx`) |
| listes d'adversaires `0x61B740-0x61B899` | 346 o | 4 pointeurs vers les listes | `0x24F9D0`, `0x2615D0` | copie (déjà faite par le prototype) |
| tables de scènes `0x61BC60` / `0x61BC80` | 2 × 32 o | 11 pointeurs de code | `0x24A480`, `0x24B050` | **reconstruites** : pointeurs vers les copies greffées. Les talons `A5+4 = 6/8/A` de `T_5B5E80` (RTS) sont à rebrancher |
| scènes `0x61C1E0` / `0x61C200` | 64 o | 14 pointeurs de code | `0x261560`, … | gardées dans Hyper (`T_5B5E80`, `T_5B5EA0`). Les entrées 6/8/A et la sous-table du mode Arcade sont à patcher |
| chargeur de fin `0x6283C0` | 40 × 4 o | (gfx, anim) par perso | natif `0x4114A0`, site `0x272D50` | `assets_natifs` (voir 4.3) |

### 4.3 Fichiers du disque et construction d'Hyper

- **anim 458-485** (28 fichiers, 130 Ko décompressés). Les pointeurs internes sont relatifs à `$B83800` (`LOAD_BASE` d'Upper).
  - Dans Hyper, `assets_natifs` n'a aucun chargeur : `T_FIN = None`, `VBASE = $D20000` (bloc vide).
  - À faire : profil `ro9` augmenté avec `T_FIN = 0x6283C0`, **lue dans le module d'Upper ou dans le bloc greffé**, et
    `N_FIN = 0x28`.
  - `FIN_SITES` = va **dans la greffe** du site `0x272D50`, `LOAD_BASE = $B83800` (sert seulement à reloger), et le talon
    `STUB_ANIM` pour l'appel au natif d'Upper `0x4114A0`.
  - Les tables partent dans `ablob` à `ASSET`, et la conversion des pointeurs projette `VBASE`.
  - Le talon écrit `$C0BC(A5)`. Dans Hyper, cette variable est seulement lue (4 lectures, aucune écriture) : le pointeur
    d'animation de l'emplacement 4 (`BANC_PTR_ANIM=FF40BC`) est donc libre pour ce rôle.
- **gfx 391-418** (1,8 Mo compressés, banques des fins). Elles sont dans `mame_ro5/banques_hx/f391…f418.bin`, avec
  34 lignes `anim <valeur de $FF40BC> <banque>` dans sa `carte.txt`.
  - `mame_ro9/banques_hx` n'en a aucune : seulement 128 lignes `perso`.
  - Étape à ajouter à la construction d'Hyper (`banques.py` / `hsfa_build.py`) :
    - copier les 28 banques ;
    - regénérer les lignes `anim`, car leur clé dépend de l'adresse `ASSET` de la ROM d'Hyper augmentée ;
    - fork / FBNeo : les ajouter aux fichiers d'emplacement 4 (blocs externes du pilote `sfa3hhsfa`).
  - `mame_ro9/hsfa_gfx.bin` part de la ROM étendue d'Upper (`hsfa_gfx_base_ro5.bin`, même taille) : les tuiles des fins
    y sont sans doute déjà. **À vérifier** en affichant une fin.
- **Service des données copiées** : un **bloc ajouté hors du module**, exéc. `0xE80000`, comme le bloc son
  (`SON-HYPER-ROM.md` §13).
  - Dans le ROM 68K, il est servi **à la suite du bloc son** dans `ext_940000.bin` : `$BD3F00` pour le prototype.
  - La copie du traducteur reçoit `HSFA_GREFFE_DONNEES`, `HSFA_GREFFE_X` et `HSFA_GREFFE_PTRS` (décalages des pointeurs
    de code, convertis en adresses 68K à la construction).
  - La plage est ajoutée à la conversion des pointeurs à l'exécution.
  - La plage `0xE8xxxx` suit `0xE70000` (son). Aucun `lui 0xE6-0xEA` dans ro9 ni dans ro5.
  - 71 longs des données d'Hyper tombent dans `[0xE80000, +192 Ko)`. Comme pour le son, ce sont sans doute des paires de
    mots ; à vérifier avant la construction définitive, car la conversion à l'exécution les prendrait pour des pointeurs.

---

## 5. Étape 5 — `$102` dans le code greffé (`outils/audit_102.py` → `donnees/audit_102.tsv`)

Le classement est fait sur la **traduction 68K** (cps2 : `$0103(An)`), d'après l'usage du registre lu dans les 8
instructions suivantes.

| | CMP | INDEX | COPIE | ÉCRITURE | autre | total |
|---|---|---|---|---|---|---|
| code greffé (27 routines) | 13 | 12 | 10 | 10 | 4 | **49** |
| homologues d'Hyper réutilisés (39 routines) | 27 | 0 | 14 | 0 | 1 | 42 |

L'étude estimait ≈ 27 lectures. On en compte **39** (49 accès moins 10 écritures), car le cœur mesuré est plus large.

**Règle**
1. **INDEX** (table par perso : `T_616180`, `T_61B4E0`, `T_61B680`, `ADD.W D0,D0`, `LSL`, `ADDI.W #$28` = musique ou
   décor d'adversaire) → lire **`$116`** (perso de base, 0-`$27`). C'est la correction qu'Hyper a faite sur 82 sites.
2. **CMP à une constante** (`#$06`, `#$13`, `#$1E`… : Akuma, Bison, Juli/Juni) → **`$116`**. Exception : les pseudo-ids
   `≥ $28` d'Upper (musique, ID×8) sont à garder.
3. **COPIE** (`$102 → $0132/$0133/$0147(A5)` : perso du joueur pour la scène de fin, la musique, l'écran de carte) →
   copier **`$116`** si le consommateur indexe une table à 40 entrées ; garder `$102` si c'est la version qui doit
   suivre.
   - Les 14 copies d'Hyper (`$102 → $0002(A6)`, objets fils) restent telles quelles.
4. **ÉCRITURE** (10 sites : adversaire CPU `0x2489E0`, `0x250EF0` ; boss `#$11`, `#$24`, `#$25` ; `0x2553E0`, `0x253290`) →
   poser `$102` **et** `$116` = `$117` = l'id de base. Pour une version, passer par la table d'Hyper `0x5C5300`.
   - Sinon le moteur d'Hyper, qui lit `$116/$117` (82 sites et 47 tables), verrait l'adversaire avec le perso de base
     d'avant.
   - Point à confirmer sur le code d'Hyper : qui écrit `$116/$117` à la sélection ? `SON-HYPER-ROM` §13.2 ne l'a pas
     trouvé.
5. Le **rival** `0xA5CA0` lit `0x5B61F0[$102]` (40 entrées). Il déborde pour `$102 ≥ $28` → **`$116`**. Le site est
   dans l'homologue réutilisé, côté Hyper.

---

## 6. Étape 6 — outil de greffe MIPS (`outils/greffe.py`, `outils/prototype.py`)

### 6.1 Zone d'accueil

- **Le Z80 recompilé d'Hyper, fichier `[0x20, 0x22B00)`** : 141 984 o. Le dernier accès au banc Z80 est en `0x22AE8`,
  et des fonctions C du son du portage y sont mêlées.
- Il n'est **jamais traduit** : le Z80 d'origine tourne sur la CPS2.
- `greffe.verifie_zone()` : **aucun** `jal`/`j` du 68K d'Hyper vers la zone.
  - Deux constantes, `0x2127F0` et `0x212910`, sont dans l'init **native** `0x2FA40`, qui enregistre des fonctions de
    rappel du son PS2 et n'est pas traduite.
  - Deux valeurs, `0x200001` et `0x200020`, ne sont pas des adresses.
  - 5 616 longs des données tombent dans la plage, mais aucun ne vise un prologue de fonction (ce sont des données).
- La greffe est posée à la **fin** de la zone, `[G0, 0x22B00)`, alignée sur 16 o.
- **L'en-tête n'est pas touché** :
  - mot 3 = fin du code ;
  - mot 6 = fin des données, d'où découlent la RAM du portage et `RAM_HI` (piège du mot 6) ;
  - le fichier garde la même taille.

### 6.2 Copie du traducteur (`untranspile/`, différences avec `src/hsfa`)

| fichier | changement | effet sans les variables |
|---|---|---|
| `mips.py` | `GREFFE_C0` abaisse `CODE0`. `plages_module()` / `decode_module()` ajoutent `[GREFFE_C0, 0x22B00)` **devant** la plage d'analyse du module | aucun |
| `translate.py` | `empty_funcs` et `_CODE_STARTS` décodent les deux plages. Bloc `GRF_X/GRF_LEN` servi après le bloc son. `lea_table_index` accepte les tables des blocs ajoutés (greffe et son) | aucun |
| `extra_regs.py` | analyses A8/D8 sur les deux plages (débuts, appels) | aucun |
| `mame_test.py` | `HSFA_GREFFE_DONNEES/_X/_PTRS` : bloc ajouté à `ext_940000.bin`, pointeurs de code listés convertis en adresses 68K, plage dans la conversion à l'exécution | aucun |
| `profils.py` | `MODULE_FICHIER` (module augmenté) | aucun |

**Témoin** (`constructions/b9_temoin`) : `MODULE=ro9` avec le bloc son et le module son de `agent_son_hyper_rom`.
Résultat **identique octet pour octet** à `mame_ro9` (ROM programme, `carte_image.txt`, `ext_940000.bin`). La copie
est donc neutre sans greffe.

### 6.3 Relogements (par routine ; les blocs contigus d'Upper restent contigus)

- **Branchements relatifs** : tous internes au bloc, sinon rapport `branche_externe` (0 sur tout le cœur).
- **`jal`/`j` et constantes de code** :
  - routine greffée → sa copie ;
  - aides du recompilateur → aides ro9 ;
  - sinon homologue `inverse_ro5` de classe identique / identique 68K / déplacements ;
  - sinon **non résolu** (rapport), et la routine passe à la greffe.
- **A5** (base `lw 0x1114`, accès **et** LEA) : table de l'étape 3.
- **RAM** : base `0xA00000` → `0xB80000`, et table A5 pour la RAM de travail.
- **Variables du portage** : table apprise sur les 27 constantes des routines identiques (`port_map`).
- **Données** : table de l'étape 4 (réutilisée, ou bloc `0xE80000`).
- **`lui` partagé** : même nouvelle moitié haute exigée pour toutes ses utilisations, sinon `conflit_lui` (0 sur tout le
  cœur).

### 6.4 Prototype : prochain adversaire `0x250EF0` + appelés `0x24F9D0` (choix de l'adversaire CPU) et `0x24F020`

| mesure | valeur |
|---|---|
| MIPS greffé | 6 928 o en `[0x20FF0, 0x22B00)` (deux blocs) |
| relogements | 17 A5 (`$C0C0…` → `$CB2E…`, `$C39E` → `$CC80`, `$C3A5/$C3A6` …), 16 `lui` (8 tables → `0xE80000`, 1 table réutilisée `0x58xxxx`) |
| appels | `0x251CC0` → `0xA5D40` (identique), `0x24F9D0` / `0x24F020` → copies |
| **assemblage du module augmenté** | **non résolus 0** ; reset `$4CB4`, données `$95000`, 42 tremplins (= témoin) |
| traduction 68K de la greffe contre Upper | **213 = 213 instructions** ; seules diffèrent les **34** lignes d'accès A5 relogés (`comparaison_68k.txt`) |
| reste du module contre le témoin | 130 854 lignes ; 113 diffèrent, toutes des `MOVE.L #adresse de code` (décalage dû à la greffe) |

**Défaut du traducteur trouvé** : `LEA T(PC,Dk),An` vers une table d'un **bloc ajouté** était **perdue sans traduction**
(`lea_table_index` n'acceptait que `[CODE_END_RT, DATA_END_RT)`).
- Le symptôme : 2 instructions manquantes, `chutes.json` +2.
- Corrigé dans la copie ; le même risque existe pour le bloc son.
- Il reste 2 entrées dans `chutes.json`. Elles viennent de la **première passe** d'assemblage, où `DATA_SPLIT` n'est pas
  encore connu ; l'image finale contient bien les deux LEA.

### 6.5 Essai à l'échelle (relogement seul, `donnees/essai_echelle.txt`)

| ensemble | MIPS | rapport |
|---|---|---|
| cœur **absent** (164 r.) | **113 488 o : tient dans la zone Z80** (141 984 o) | 79 A5, 267 `lui`, **96 appels non résolus** (44 nouvelles, 33 apparentées, 19 modifiées), 37 natifs, 15 homologues « déplacements » à vérifier, 0 conflit, 0 branche externe |
| cœur complet (530 r.) | 294 224 o : **ne tient pas** | 164 appels non résolus, 127 natifs |

---

## 7. Décors

Étude détaillée, avec tous les tableaux, les adresses et les scripts : **`decors/DECORS.md`** (lecture seule, sans
MAME). Résumé :

### 7.1 Inventaire : 39 décors d'Upper sur 40 manquent dans Hyper

- **Hyper n'a que 4 numéros de décor** (`$100` = 0, 2, 4, 6) et 3 agencements. Toutes ses tables par décor ont
  4 entrées.
  - Les tables A `0x660240` / B `0x661E60` / C `0x664280` (palettes s1/s2/s3) ont 16 entrées, indexées par
    `$100 + $C178`. **Les 4 variantes de `$C178` ne changent que les palettes.**
  - « Neige » et « ciel d'orage » sont donc très probablement deux couleurs du même décor 4 (à confirmer en forçant
    `$C178`).
  - Le décor 4 d'Hyper (ZERO 3) **est le décor `$4E` d'Upper**, celui de l'attraction.
- **Choix par version** : `0xA49E0`, homologue de la routine de choix d'Upper `0x24F020`, lit `T_5B6220[$103]`
  (128 octets). Cela donne ZERO 3 → 4, ZERO → 0, ZERO 2/ALPHA → 2. Ensuite `$100 = $174` dans `0x96690`, puis
  rotation de `$C178`.
- **Données du module** : 1 bloc de palettes sur 35 seulement (`$4E`), 0 liste s1/s3, 0 objet ou animation de décor,
  11 blocs s1 sur 119, 4 super-tuiles sur 3 081.
  - Absents d'Hyper : les palettes des sprites de décor `0x707D10`, les objets `T_950CE0`, les positions (`$172`), la
    musique par décor `0x139AD0` et le défilement des scènes `T_60B400`.
- **Graphismes** : Hyper a ses propres mémoires e546 (23 296 tuiles 16×16) et e548 (896 tuiles 32×32), et non
  e353/e525.
  - Les décors `$00-$4C` d'Upper n'y sont qu'à 0-6 % par plan ; `$4E` y est à 99-100 %.
  - À loger : scroll1 **22 566** tuiles 8×8, scroll2 **14 330** tuiles 16×16, scroll3 **3 122** tuiles 32×32. Elles
    sont déjà dans `mame_ro5/hsfa_plans.bin`.
- **Code de décor d'Upper** : 239 routines, ≈ 75 Ko de MIPS (72 Ko sans copie exacte dans Hyper) : 16 + 14 gestionnaires
  de plans contre 3 + 4, 9 effets contre 2.
  - Ce code **s'ajoute** au cœur de l'étape 2 : il est atteint par les tables par décor (> 24 entrées), que
    l'étude ne suivait pas, et les traces n'ont vu qu'une douzaine de décors.

### 7.2 Choix du décor en Arcade greffé

Chaîne d'Upper :
1. `0x24EA30` (rival, identique dans Hyper : `0xA43F0`) appelle `0x24F020` ;
2. `0x24F020` fait `$172 = $100`, puis `$174 = 2 × T_61BE10[perso]` (40 entrées, via `0x251950`). Cas spéciaux :
   Bison final → `$14`, rival → `T_61B6D0` ;
3. `0x2489E0` (défi intercalé) ;
4. `0x2615D0` fait `$100 = $174`.

`0x24F020` est **déjà dans la greffe du prototype** (§6.4).

Articulation proposée (détail : `DECORS.md` §2.3) :
- **numérotation unique** :
  - `$00-$4E` = décors d'Upper (numéros inchangés, car le code compare à `$38`, `$1E`, `$14`…) ;
  - `$50-$72` = SFA2 (règle de DECOR-SFA2) ;
  - `$78/$7A/$7C` = les décors d'Hyper (ZERO 3 / ZERO / ZERO 2) ;
  - variantes de couleur dans les seules tables A/B/C ;
- **`$C178`** : ne tourne que pour les décors d'Hyper (`$100 ≥ $78`) en `0x96C34`/`0x96C48`, et vaut 0 en Arcade.
  Sinon `$100 + $C178` tombe sur un autre décor ;
- **une table perso → décor de 128 octets**, indexée par l'id étendu ; elle remplace `T_61BE10` et `T_5B6220`.
  - ids `$00-$27` : décors d'Upper ;
  - ZERO : `$7A` ;
  - ZERO 2 / ALPHA : décor SFA2 importé, sinon `$7C` ;
  - **pas besoin de `$116`** ici ;
- crochet du tirage SFA3/SFA2 sur l'écriture de `$174` : `0x24F2F4` greffé, ou `0xA4A68` dans Hyper ;
- à corriger en même temps : `0x31D6A0` (`$100 = 2 × $103` : déborde jusqu'à `$FE`) et `T_5B6030` (rival).
- Alternative minimale : décors d'Hyper par version en Arcade. Rien à porter, mais on perd les décors par adversaire.

### 7.3 Chantiers SFA3 (widescreen, SFA2) et factorisation

- **Widescreen** (INJECTION-FORK) : 18 `LEA` dans SFA3, 20 dans Upper, **16 dans Hyper**, retrouvés par l'adresse PS2
  de la constante dans `carte_image.txt` (`decors/sites_injection.tsv`).
  - Pour Hyper, une palette neuve doit être écrite **dans chaque variante** de `$C178`.
  - `0x3E3A0` vise directement les palettes du décor 0.
  - Bloc externe libre : `$BCE200-$C83FFF` ou à partir de `$D0C000` ; `$C80000` est pris par le fichier 547.
- **Import SFA2** (58 correctifs) :
  - 28 sites d'Hyper (bibliothèques 9, palettes 4, tables de sauts 4 + 4 tables de mots, CPS-B 2, ROUND 2…) ;
  - **13 sur le code d'Upper à greffer** (objets, positions, animations, masques) ;
  - 13 inutiles ;
  - la musique par décor est à refaire, car Hyper n'en a pas.
  - Tables étendues à 63 entrées (75 pour A/B/C) au lieu de 58.
- **Factorisation : oui**, un seul outil paramétré par module, avec les sites trouvés par constante.
  - Les constantes par module (tables, bases de codes, ajout `$1000` au code s2 d'Hyper, mémoires, codes libres, bloc
    externe) sont dans `DECORS.md` §3.3.
  - Il faut réécrire les adresses d'image codées en dur de `construit.py` (SFA2), comme le fait déjà
    `injection_fork.py`.
  - Hyper ajoute deux paramètres : le pas des variantes `$C178` et les sites qui visent directement une palette.

### 7.4 Plan des décors (dans l'ordre)

1. Numérotation et table perso → décor (128 o), `$C178` conditionnel, correctif de `0x31D6A0`. Contrôle : VERSUS
   d'Hyper inchangé.
2. Tables par décor étendues dans un bloc externe d'Hyper (`$D10000`) et bibliothèques fusionnées.
3. Graphismes relogés dans `hsfa_plans.bin` d'Hyper (méthode d'`injection_fork.py`). Recenser d'abord les codes scroll1
   libres.
4. Code de décor d'Upper (≈ 75 Ko) par l'outil de greffe. C'est une **deuxième zone d'accueil** à prévoir, avec les
   modifiées du cœur (§8, point 1).
5. Validation contre Upper, décor par décor (`$FF8100` forcé), puis en partie Arcade.
6. Ensuite seulement : widescreen et SFA2 sur cette numérotation.

---

## 8. Prochaines étapes concrètes de la greffe

1. **Décider le sort des 366 routines modifiées du cœur** (176 Ko), avec un diff par branche entre Upper et le
   partenaire d'Hyper (outil à écrire sur la base de `verifie_reutil.py`) :
   - retouche en place (branche Arcade réintroduite dans la routine d'Hyper) ;
   - ou copie greffée.

   Tant que ce n'est pas fait, la zone Z80 suffit pour l'**absent** (111 Ko). Pour la suite, il faut une deuxième zone.
   Pistes :
   - natifs d'Hyper remplacés par des talons ;
   - code d'Hyper mort ;
   - un 2ᵉ intervalle de code au-delà du module, comme les blocs de données. Cela demande d'étendre `build_code_conv`
     à deux plages.
2. **Fermer les 96 appels non résolus** de l'absent. Pour chaque appelé nouveau, apparenté ou modifié : le greffer
   (fermeture) ou l'envoyer sur l'homologue d'Hyper après vérification.
   - **Natifs** (37) : talons, comme `assets_natifs`. Il y a le chargeur de fin `0x4114A0`, le chargeur par perso
     `0x4113A0`, et les natives de la sortie `0x407EC0` et `0x4077C0`.
3. **Bornes des données** : remplacer les bornes « jusqu'à la constante suivante » par les tailles lues dans le code
   (index maximal, boucles). Ne reloger que les pointeurs prouvés : pointeurs de code par `classe_valeur` et cibles de
   prologue, pointeurs de données par les lectures `MOVEA.L T(PC,Dn)`.
4. **Points d'entrée** (≈ 10 sites) :
   - `T_5B5E80[6/8/A]` (RTS) → talons greffés `0x2614A0`, `0x2614D0`, `0x261500`, et `T_61BC60/80` reconstruites ;
   - sous-table de la scène 4 en mode Arcade : aiguillage par mode à l'entrée de `0x96690` / `0x96620`, ou entrées
     d'une sous-table propre au mode Arcade ;
   - lanceur ARCADE du menu (`0x5B4210[0]`, homologue du lanceur d'Upper `0x4E1C0`) ;
   - appels de `0x9C940` (fin de manche) vers `0x269340` greffé.
5. **`$102` → `$116`** sur les 12 INDEX et 13 CMP du code greffé, et `$116/$117` posés aux 10 ÉCRITURES. Cela peut se
   faire dans l'outil, par patch MIPS du déplacement `0x102` → `0x116` sur les `lb` repérés.
6. **Construction d'Hyper augmenté** :
   - profil `ro9` avec `T_FIN`, `FIN_SITES` relogés et talon du natif de fin ;
   - banques `f391-f418` et lignes `anim` dans `banques_hx/carte.txt` d'Hyper ;
   - bloc `ext` de la greffe.
7. **Décors** : plan du §7.4. Le point 1 (numérotation, table perso → décor, `$C178`) peut commencer tout de suite ;
   le point 4 (75 Ko de code de décor) relève de la deuxième zone d'accueil.
8. **Oracle** : mêmes entrées scriptées sur Upper (`fige/ro5`) et sur Hyper augmenté. On compare `A5+4/+8/+C`, la suite
   des adversaires (`$C0C0` contre `$CB2E`), le rival et les fins, avec `tournee_greffe.lua`, qui sait déjà perdre,
   continuer et boucler en VERSUS.

---

## 9. Fichiers (`<workspace>/work/greffe_arcade/`)

| chemin | rôle |
|---|---|
| `GREFFE-PREPARATION.md` | ce rapport |
| `lua/tournee_greffe.lua` | partie Arcade/VERSUS avec couverture opcodes, `PERDRE`, `CONTINUE`, `VSBOUCLE`, captures par état (`SNAPETAT`, `SNAPSC`, `SNAP4`) |
| `lua/ram_hyper.lua` | carte dynamique de la RAM (lecture/écriture par mot, accès Lua exclus) autour d'un scénario quelconque (`SCENARIO`) |
| `outils/lance_traces.sh`, `lance_hyper_ram.sh`, `lance_upper_ram.sh` | lanceurs MAME (fork, construction figée, nvram/cfg propres) |
| `outils/couverture.py` | mots lus → routines (critère de préchargement) |
| `outils/liste_arcade.py`, `outils/coeur.py` | étape 2 → `donnees/liste_arcade.tsv/.pkl`, `liste_arcade_resume.txt` ; cœur → `coeur_greffe.pkl/.tsv`, `liste_arcade_zones.txt` |
| `outils/verifie_reutil.py` | vérification constante par constante des routines réutilisées → `verifie_reutil.tsv` |
| `outils/ram_statique.py` | accès RAM statiques (A5 et absolus) → `ram_statique_ro5/ro9.pkl` |
| `outils/relogement_a5.py` | étape 3 → `relogement_a5.tsv/.pkl`, `zones_libres_hyper.tsv` |
| `outils/donnees_greffe.py` | étape 4 → `donnees_greffe.tsv/.pkl` |
| `outils/audit_102.py` (+ `audit_102_mips.py`, ancienne version) | étape 5 → `audit_102.tsv` |
| `outils/greffe.py` | **outil de greffe** : zone, blocs, relogements, bloc de données |
| `outils/prototype.py [--construire]` | étape 6 → `constructions/proto/` (module augmenté, bloc, `greffe.json`, construction `b9/`) |
| `outils/compare_68k.py` | traduction de la greffe contre Upper → `constructions/proto/comparaison_68k.txt` |
| `outils/planche.py` | planches de captures |
| `untranspile/` | copie du traducteur (§6.2) |
| `fige/ro5`, `fige/ro9` | constructions figées (ROM, carte, blocs ext, md5) utilisées par toutes les traces |
| `traces/<nom>/` | `journal.txt`, `couv.txt`, `ram.txt`, captures ; planches `traces/planche_*.png` |
| `constructions/b9_temoin` | témoin (identique à `mame_ro9`) |
| `decors/` | étape 7 (sous-agent) |

**Relancer** (depuis `greffe_arcade`, tout en `nice -n 19`) :
1. `outils/lance_traces.sh …` / `lance_hyper_ram.sh` / `lance_upper_ram.sh`, si une construction change : refiger d'abord.
2. `outils/ram_statique.py`
3. `outils/liste_arcade.py`
4. `outils/coeur.py`
5. `relogement_a5.py`
6. `donnees_greffe.py`
7. `audit_102.py`
8. `verifie_reutil.py`
9. `prototype.py --construire`
10. `compare_68k.py`
