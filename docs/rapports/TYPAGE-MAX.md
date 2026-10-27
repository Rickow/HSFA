# Typage des 212 champs utilisés par le code MAX, dans la disposition d'Upper (ro5)

Session « typage MAX », 2026-10-07. Lecture seule de l'existant ; tout est dans `<workspace>/work/agent_typage_max/`.
Pas de MAME. Entrée : `sfa3max-psp-widescreen/work/re/rosette_code/champs_utilises_max.tsv` (212 lignes).
Sortie machine : **`champs_types_upper.tsv`** (base, depl_arcade, taille, occ, type, depl_image_upper, transfo_valeur,
reloge_A5, confiance, preuve).

**Conventions** : *arcade* = déplacement 68K de la ROM SFA3 (`sfa3ud`) ; *hôte* = adresse vue par le MIPS d'Upper
(`ro5_usa_prog68k.bin`) ; *image* = déplacement dans l'image 68K traduite d'Upper (recette §29 : mot hôte h → image h,
octet hôte h → image h XOR 1, long hôte h → image h avec moitiés échangées). `va` = décalage fichier dans ro5.

---

## 0. En bref

1. **Mesure directe, pas seulement le modèle** : en plus des comptes d'accès MIPS par déplacement (méthode §44), j'ai
   relevé sur l'alignement Upper ↔ arcade (`realign.pkl`, 83 709 instructions alignées) **chaque instruction arcade
   `d(An)` appariée à son instruction de l'image Upper**, y compris dans les trous de même longueur. On lit donc
   directement « arcade `d`.taille → image `d'` » sur des centaines de sites (ex. `$7.B` → image `$6` 2 555/2 557 fois).
   Les immédiats appariés donnent la transformation de valeur (SWAP, octets échangés, bswap16).
2. **Les trois exemples sont confirmés** : caméra `$290(A5).W` → image `$292` (18/18, s32) ; `$102.B` → image `$103`
   (320/320, u8) ; `$32F.B` → image `$32E` (u8 : ro3 l'écrit en `sb` hôte `$32F`). **Mais `$32F` n'existe plus dans
   Upper** (ro5 : aucun accès ; ECARTS §8) : ne pas l'écrire.
3. Bilan des 212 lignes : **150 mesurées**, 17 déduites, 2 ambiguës, 43 inconnues (40 champs jamais accédés par
   Upper + `$7788(A5)` + 2 erreurs d'adresse impaire). 119 lignes ont un déplacement image ≠ arcade (presque toutes
   des octets u8 : XOR 1). Types : 108 u8, 29 s16, 12 s32 (positions, vitesses, caméra), 4 u8[4], 4 pointeurs PS2,
   2 u8[2] lus en mot, 1 s16[2], 1 mixte, 40 libres.
4. **Aucun relogement A5** pour les variables de MAX : toutes sont dans `$FF8000–$FFF1C0` (zone identique ro3/ro5,
   aucune entrée de la table de relocalisation d'Upper ne les couvre). `$7788(A5)` (= `$FFF788`) n'est utilisée ni
   par l'arcade ni par Upper : probablement une globale PSP mal traduite (Eagle `psp_1b70f8`).
5. **Zone `$332–$3F3` des joueurs : libre dans Upper.** Aucun accès MIPS (A0–A6), aucun accès A5 absolu aux
   structures joueur `$FF8400/8800/8C00/9000` + `$330–$3FF` sauf `$370–$37E` (déjà connus), aucune constante
   `0xA08xxx` qui y pointe. **`$362` et `$3F3` : pas de collision.** (`$362(A5)` = `$FF8362` est une globale
   d'Upper lue en mot, mais c'est une autre adresse que le champ objet `$362`.) Dans l'arcade, seuls des restes de
   débogage (`$1C942–$1C978`, affichage de `$330/$332–$334`) y touchent.
6. **Collisions et pièges à corriger** (§3) : `$272` (doit aller en image `$273`, sinon il écrase l'octet `$273`
   d'Upper) ; `$3D4` reçoit une copie brute de `$82.L` (doit hériter du u8[4]) ; `$22.B` (type d'objet PSP écrit
   dans un champ que des routines d'objets d'Upper lisent en mot) ; deux accès à adresse impaire (`$101.W`,
   `move.l $101(a0),$3d4(a6)`) qui font une erreur d'adresse sur 68000.

---

## 1. Méthode

| étape | script | sortie |
|---|---|---|
| accès MIPS de ro5 par (case registre A0–A6, déplacement hôte, taille, sens) ; base = `lw 0x1100+4n` (+`addiu`) ; `MODULE=ro3` possible | `stats_ro5.py` | `stats_ro5.pkl`, `stats_ro3.pkl` |
| accès de la ROM arcade par (registre, déplacement, taille) sur le désassemblage complet (`agent_symboles/_cache/arc.pkl`) | `arc_stats.py` | `arc_stats.pkl` |
| **appariement des opérandes** `d(An)` sur l'alignement Upper↔arcade de `agent_upper_ecarts/realign.pkl` (ancres, LCS, et trous de même longueur à même mnémonique ; seules les instructions image qui ont une va MIPS dans `carte_image.txt`) ; relation des immédiats (`identique`, `SWAP`, `octets/mot`, `bswap16`, `neutre` = valeur palindrome, `autre` = adresse convertie) | `paires_align.py` | `paires_align.pkl`, `paires_recs.pkl`, `imm_align.pkl` |
| classement automatique : déplacement image majoritaire → type (octet : image = d⊕1 ⇒ u8, = d ⇒ octet de s16, autre ⇒ s32 ; mot : = d ⇒ s16 ou u8[2], = d+2 / d−2 ⇒ s32 ; long : immédiats + sous-accès) ; code arcade `< $1C000` (plans, défilement) exclu pour la base « objet » | `classer.py` | `classer.txt`, TSV brut |
| corrections vérifiées à la main (33 lignes : pointeurs, unions, champs sans alignement, erreurs, tables MAX) | `finaliser.py` | **`champs_types_upper.tsv`** |
| outils de lecture | `q.py REG:DEP:TAILLE`, `voir.py REGS DEB FIN`, `brut.py` | |

Bases : « objet » = A6+A4+A1 ; « A5 » = A5 ; « pas d'animation » = A0+A1 ; « pointeur a0/a3 » relus dans le code MAX
(voir §3.4). Confiance : **mesuré** = ≥ 3 sites alignés et ≥ 80 % d'accord ; **déduit** = peu de sites, ou type tiré des
voisins / des accès MIPS sans site aligné ; **ambigu** = le type dépend de la structure ; **inconnu** = jamais accédé ou
accès impossible.

Pourquoi l'alignement plutôt que `typed_rule.py` seul : le modèle typé prédit 94–95 % des paires ; l'alignement donne
le déplacement réellement employé par Upper à chaque site, et sépare les provenances par adresse arcade (plans `< $1C000`,
moteur joueur `$1C000–$33F00`, persos `$33F00–$80000`, objets/effets `≥ $80000`).

---

## 2. Règles de conversion à appliquer (arcade → image Upper)

Notation : `d` = déplacement arcade ; `F` = début du champ long.

| type du champ (Upper) | octet | mot | long | valeur |
|---|---|---|---|---|
| **u8** | `d XOR 1` | (mot sur deux u8) `d` | (quatre u8) `d` | mot : **octets inversés** ; long : **octets échangés dans chaque mot** (`$02060000` → `$06020000`) |
| **s16** | `d` (inchangé) | `d` | (s16[2]) `d` | aucune |
| **s32** en F | `F + (k XOR 2)` pour l'octet `F+k` | partie haute `F` → `F+2` ; partie basse `F+2` → `F` | `F` | long : **SWAP** (moitiés échangées) ; mot/octet : aucune |
| **pointeur 32 bits** (`$1C`, `$60`, `$88`, `$A0`) | – | – | `F` | **SWAP** ; une lecture servant d'adresse doit faire comme l'image : `MOVEA.L ; [remise en ordre] ; JSR $400` (CONV_An). Une adresse 68K hors `[$60ACC0,$C3FC50)` traverse CONV inchangée, mais doit être rangée SWAPée |
| **champ MAX seul** (jamais accédé par Upper) | `d` | `d` | `d` | aucune (l'image est une mémoire 68K ordinaire ; seul MAX lit ces champs) |

Compléments :
1. **Valeur lue puis manipulée** : si MAX lit un long typé dans un registre puis en prend un octet ou fait de
   l'arithmétique (ex. `move.l $6c(a1),d3 ; subq.l #1,d3 ; move.b d3,$6c(a6)`), appliquer la transformation
   inverse juste après la lecture et la transformation directe juste avant l'écriture. Une simple copie
   mémoire → mémoire entre deux champs DE MÊME TYPE n'a besoin d'aucune transformation.
2. **Champ libre voisin d'un champ d'Upper** (même mot) : suivre le type du voisin, sinon on écrase le voisin. Cas
   unique ici : `$272` → image `$273`.
3. **Champ libre qui reçoit une copie brute d'un champ typé** : il hérite du type de la source (`$3D4` ← `$82.L`).
4. **Tests de nullité** (`tst.l`, `clr.l`) : indifférents à la disposition (seul le déplacement compte).
5. **Données lues par le moteur d'Upper** via ces pointeurs (pas d'animation `$1C`, géométrie `$60`, boîtes `$88`,
   attaques `$A0`) : elles doivent être au format PS2 de l'image (octets du pas en XOR 1 : `$8↔$9`, `$12↔$13`…),
   même si elles viennent de la ROM MAX.
6. **A5** : pas de relogement pour ces 13 variables. Ne pas appliquer la table de relocalisation d'Upper (elle ne
   couvre que des déplacements négatifs / la zone `$FF2F84–$FF41A7` et les trous `$8C61-$8C79`, `$9EA4`).

---

## 3. Cas délicats

### 3.1 Champs dont le type dépend de la structure (unions)

| champ | joueur / objet (ce que MAX doit utiliser) | autre emploi dans Upper | preuve |
|---|---|---|---|
| `$20.W` | s16, image `$20` (9/9 dans le code d'objets, ex. `$85B74`) | partie haute d'un s32 dans les **structures de plan** (code `< $1C000`) → image `$22` (11×) | `q.py A6:20:2` |
| `$28/$2A/$2C/$2E.W` | **s16, pointeurs mot** (joueur : A4 `$20F0C–$20F58`, `movea.w`) → image identique, valeur native | dans quelques effets (`$B3C80–$BBC48`) ces octets sont des **u8** (`$28.B` → image `$29`) ; l'allocation (`$1C226…`) les remet à zéro en longs | 73/73, 56/56, 39/39, 21/21 |
| `$22.B` | octet fort d'un s16 → image `$22` | **collision** : Upper lit `$22.W` dans ses routines d'objets (ex. `$85B7A`) ; MAX y écrit le type d'objet PSP (`move.b #$2b,$22(a4)`) | 1 site aligné + 11 mots |
| `$10/$12/$14.W` | s32 : `$10`→`$12`, `$12`→`$10`, `$14`→`$16` (1 054/1 071, 75/85, 1 151/1 161) | minorités « identité » : A4 = sous-structure (`LEA $7E(A6),A4`, `$B3F96`…), pas un objet | |
| `$50.W`, `$52.W` | s16 (181/187, imm. identiques ×31) | partie de s32 dans les plans (6×) | |
| `$6C.L` | u8[4] chez les joueurs (`$6C–$6F` → image `$6D/$6C/$6F/$6E`) | pointeur (`MOVEA.L`) chez un perso (`$6F088`) ; long hôte `$6C` | **ambigu** |
| `$74.L` | ? | copie d'une position s32 (`MOVE.L $14,$74`), pointeur converti (`CONV_A0`), octets u8 (`$74.B`, `$26214`) | **ambigu** : décider selon l'objet MAX qui l'emploie (`move.l #3,$74(a6)`, `move.l d7,$74(a4)`) ; si seul MAX le lit en long, n'importe quelle convention cohérente marche |
| `$AC.L` | mixte : u8 `$AC` (→`$AD`), u8 `$AD` (→`$AC`), s16 `$AE` | | MAX ne fait que `tst.l` : sans risque |

### 3.2 Champs sans site aligné (type déduit des voisins et des accès MIPS)

| champ | type | image | raison |
|---|---|---|---|
| `A5 $14E.B` | octet fort d'un s16 | `$14E` | arcade `$14E.W` ×7 ; MIPS `lh/sh` ×7, aucun octet |
| `$82.L` | u8[4] | `$82`, octets échangés dans chaque mot | `$82`,`$83`,`$84`,`$85` tous u8 (1 075, 60, 48 sites ; `$84.W` imm. bswap16 ×14) |
| `$A4.L` | s16[2] | `$A4` | `$A4.W` 95/95, `$A6.W` ; MAX : `clr.l` seulement |
| `$110.L` | s32 / pointeur | `$110`, SWAP | Upper ne fait que des copies longues (`MOVE.L $110,$138`) |
| `$272.B` | u8 libre | **`$273`** | voisins u8 `$270/$271/$273` ; à l'image `$272` on écraserait l'octet arcade `$273` (`$28B2A`) |
| `$27D.B` | octet faible de `$27C.W` | `$27D` | `$27C.W` (`$2F8FC`) |
| `$2A6.B` | octet fort de `$2A6.W` | `$2A6` | `$2A6.W` 19/19, `$2A7.B` → image `$2A7` 15/15 |

### 3.3 Erreurs dans le code MAX

- **`$101.W` ×4** (base objet) et **`move.l $101(a0),$3d4(a6)`** (Yun l. 4072, « pointeur a0 ») : accès mot/long à
  une adresse impaire → **erreur d'adresse** sur 68000. Dans Upper, `$101` est un **u8** (→ image `$100`, 178/178).
- **`$3D4`** : `move.l $82(a6),$3d4(a6)` puis `move.b $3d4(a6),$82(a6)`. En laissant `$3D4` « libre » (identité),
  l'octet relu serait l'arcade `$83`, pas `$82`. Donner à `$3D4` la disposition u8[4] de `$82` : `$3D4.B` → image
  **`$3D5`**, `$3D4.L` → `$3D4` sans transformation (copie).
- `$32F` (déjà signalé par ADRESSES-MAX-UPPER) : supprimé dans Upper.

### 3.4 Bases « pointeur a0 / a3 »

Relues dans le code MAX : ce ne sont pas toutes des tables.
- `$2.W(a0)`, `$4.L(a0)` : **tables assemblées par MAX** (`TAB_VOIX_MAX`, `TAB_SONS_CLES`, `moteur_max_main.s`) →
  gros-boutistes, **aucune conversion**.
- `$14.W`, `$5F.B`, `$25D.B` (a0 « pointeur d'objet ») et `$55.B` (a0 = `$400(A5)+$400k`, structures joueur) →
  **règles des champs d'objet** : image `$16`, `$5E`, `$25C`, `$54`.
- `$10.W(a3)` : A3 = caméra du plan rendue par `$1BD68` → s32, image **`$12`** (114/114, mesuré sur `$1B4D0`).

### 3.5 Pas d'animation (A0/A1 depuis `$1C(A6)`)

Octets du pas = u8 rangés un par un (§44) : `$1`→`$0`, `$8`→`$9`, `$9`→`$8`, `$B`→`$A`, `$12`→`$13`, `$13`→`$12`
(mesuré, mais A0/A1 toutes provenances confondues). Le pointeur `$1C` est une adresse PS2 (SWAP + `CONV_A0`).

---

## 4. Champs libres (jamais accédés par Upper) — 40 lignes

`$332, $336, $33A, $33E (.W), $342.L, $34A.L, $34E.B, $356/$358/$35A/$35C (.W), $35F, $361–$367 (.B),
$3C0–$3D8 (.L, et $3C0.B), $3D4 (voir §3.3), $3E0–$3E9 (.W/.B), $3EC.L, $3F2 (.W/.B), $3F3.B`.
Disposition : **identité** (mêmes déplacements, valeurs 68K). Valable **pour les structures joueur (taille `$400`)** ;
ne pas employer ces déplacements sur des objets fils plus petits.

Contrôles faits : MIPS ro5 A0–A6 sans aucun accès en `$330–$36F` ni `$398–$3FF` (seuls `$370–$37E` et des écritures
longues `$380–$394`) ; A5 absolu : seulement `$770–$77E` / `$B70–$B7E` ; aucune constante `0xA08000+$400k+$330…$3FF`.
Non vérifiable statiquement : copies ou remises à zéro de blocs entiers de la structure joueur (boucles `(An)+`).

---

## 5. Inconnues

1. **`$7788(A5)`** : ni arcade ni Upper ; à recontrôler côté traduction PSP → 68K.
2. **Unions** `$6C.L`, `$74.L` : le type dépend de l'objet ; à trancher avec le rôle exact du champ dans le code MAX.
3. **`$22` des objets fils** : vérifier qu'aucune routine d'Upper appelée sur un objet MAX ne lit `$22.W`.
4. Remises à zéro par blocs de la zone `$332–$3F3` à l'initialisation d'un round : non mesurées.
5. Trois champs à 1–2 sites alignés seulement, cohérents avec u8 : `$244.B`, `$296.B`, `$2C7.B`.
6. Les données au format PS2 pointées par `$1C/$60/$88/$A0` : si MAX garde ses propres tables pour le moteur commun
   d'Upper, elles doivent être converties (hors du périmètre de ce typage).
