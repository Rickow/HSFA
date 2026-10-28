# Reprise — état du projet

> **2026-10-04 : commencer par `docs/ETAT-DES-LIEUX.md` (état, commandes, pièges) et `docs/INDEX-HANDOFF.md`
> (index par thème).** Les sections R§0-R§8 ci-dessous sont anciennes ; certaines valeurs y sont fausses
> (cases de registres, base d'exécution) : l'index signale ce qui est dépassé.
>
> Document de reprise. À lire **en premier** si la conversation est perdue,
> compressée, ou si l'on revient après une interruption.
> Dernière mise à jour : 2026-09-26.

---

## 0. En une page

**Cible** : Street Fighter Alpha Anthology (PS2, `SLUS-21317`, CRC `72CE7A78`).

| Chantier | État |
|---|---|
| Mode Arcade (Hyper) | ✅ livré |
| Widescreen 16:9 natif | ✅ livré |
| Tout débloqué | ✅ livré |
| Cross-stage PS2 | 🚧 bloqué sur un diagnostic live |
| « Voie B » : Upper+Hyper sur FBNeo | 🚧 méthode prouvée, outillage démarré |

**Deux fils actifs et indépendants** : le cross-stage PS2 (court terme) et la
voie B (long terme). Ils ne se bloquent pas l'un l'autre.

---

## 1. Le fait structurant : l'Anthology est une RECOMPILATION STATIQUE

Ce n'est ni de l'émulation, ni un portage écrit à la main. Le code 68000 d'origine
a été **traduit mécaniquement** en MIPS R5900, avec le **fichier de registres 68K
mappé sur des emplacements fixes du scratchpad PS2**.

**Preuves mesurées sur les 9 jeux (`ro1`..`ro9`)** :
- **50-53 %** de tous les accès scratchpad tombent dans 64 octets :
  `0x70001100-0x7000113f` = 16 emplacements = `D0-D7` + `A0-A7`.
- Ces emplacements sont lus/écrits en **trois largeurs** (`.B`/`.W`/`.L`) de façon
  systématique — le modèle d'opérandes du 68K. Aucun compilateur MIPS natif ne fait ça.
- Les **flags** sont émulés en mémoire : `0x70001150` (dernier résultat, test Z)
  et `0x70001158` (signe, N).

**Mapping des registres** (déduit puis confirmé par les données) :
```
A0=0x70001100  A1=0x1104  …  A5=0x1114  A6=0x1118 (frame pointer, le plus chaud)
D0=0x70001120  D1=0x1124  D2=0x1128  D3=0x112c
RES=0x1150   NFLG=0x1158
```
A7 n'apparaît pas : la pile 68K est mappée sur la pile MIPS native.

**Conséquence** : le jeu d'arcade d'origine est de fait la *source* de la version
PS2, et le MIPS remonte au 68K quasi instruction par instruction.

---

## 2. Carte de l'état de jeu (vaut pour zero3, zero5 ET zero9 — même moteur)

```
A5 = 0xb88000          base de l'état de jeu (le « dispatch » cartographié jadis)
P1 = 0xb88400          structure joueur 1   (A5+0x400)
P2 = 0xb88800          structure joueur 2   (A5+0x800)
0xb88916               personnage P2        (A5+0x916 = P2+0x116)
0xb84178               variable de stage    (A5-0x3e88)
```
Les offsets vont par paires P1/P2 espacées de 0x400 (`+0x51a`/`+0x91a`, etc.).
⚠️ Il existe en réalité **quatre** entités à 0x400 d'écart (0x400/0x800/0xc00/0x1000).

**Sites qui écrivent la variable de stage** (trouvés via les accès `-0x3e88(reg)`) :
`0x2527e8`, `0x286c34` et `0x286c48` (le « cycleur », avance de 8 en 8),
`0x288758` (char-select), `0x290840` (descripteur versus).
**Lecteurs** : `0x25059c`, `0x2511ac`, `0x25126c`, `0x25132c` (constructeurs de décor).

**Tables de stage** : `0x660240` (A) et `0x661e60` (B), **8 octets par stage =
4 variantes u16** (la variante vient de `[0xb88100] ∈ {0,2,4,6}`) — d'où des **IDs
multiples de 8**. Les entrées sont des **offsets relatifs à la base de table**.
**Hyper n'a que 4 stages natifs : IDs 0, 8, 16, 24.**

---

## 3. Cross-stage PS2 — où ça bloque

**Mécanisme compris** (capturé en direct sur le v7 Blanka qui rendait) :
le jeu ne lit PAS les graphismes de tuiles dans la banque au moment du dessin.
Ils vivent dans un **contexte de couche** contenant des tuiles **32×32 compressées**,
monté au chargement. Patcher la banque après le load n'atteint jamais le GPU.

**La solution qui marche** : **repointer le contexte de couche**
(`[0x1dc2f4]` = `[0x1dc078+0x44]`, ainsi que `+4` et `+8`) vers notre propre
paquet de tuiles **déjà décompressées**. Le cave doit le réécrire **chaque frame**
(le build du jeu les remet).

**Format du contexte à construire** :
```
+0x20  base_tile (0)
+0x24  count
+0x28  recoff (0x30)
+0x30  table de records u32, un par tuile :
         0                -> tuile VIDE
         offset, bit31=0  -> « clean » : le drawer utilise ctx+offset TEL QUEL
         offset, bit31=1  -> « dirty » : le jeu DÉCOMPRESSE d'abord
données  blocs de 0x200 o = tuile 32×32 (taille native de la couche SCR3 sur CPS2)
```

**Décompresseur porté et validé** : `tools/lz148778.py` (portage de `FUN_148778`,
LZ : byte de contrôle MSB→LSB, bit=0 littéral, bit=1 back-ref
offset=`(b>>4)+1` longueur=`(b&0xf)+2`). **Vérifié octet pour octet** contre un
bloc lu en direct dans le jeu qui rendait.

**Statut** : paquet Chun-Li construit (560/560 tuiles, taï-chi inclus), ISO et pnach
produits, **mais le pnach « tourne sans effet »**. Trois causes possibles, à
départager par **une capture live de dix secondes** :
1. le paquet ne se charge pas (magic absent à `0x1580000`) ;
2. le repoint ne tient pas (le build le réécrit plus tard) ;
3. le gate (`[0xba8000]==0x63d`) ne se déclenche jamais.

⚠️ **Leçon** : le live PINE sur un stage déjà cassé ne prouve rien — il faut un
**vrai chargement** pour que tout s'emboîte.

---

## 4. Voie B — Upper + modes de Hyper sur FBNeo

**Pourquoi FBNeo et pas CPS2** : la CPS2 plafonne à **32 Mo de graphismes**
(mesuré : xmvsf/vsav2/mvsc/hsf2/SFA3 sont tous à 32,0 Mo) et **SFA3 les occupe
déjà** ⟹ zéro marge pour les 5 persos d'Upper sur vrai matériel. Un **fork FBNeo**
avec région graphique étendue lève la contrainte, tout en gardant ce qui motive le
projet : légèreté sur handheld Android + shaders RetroArch.

**Identification des jeux** : `ro1..ro9 = zero1..zero9`.
- `ro3` = SFA3 arcade (©1998) — **31 persos**
- `ro5` = **Upper** (©1998, 8,06 Mo) — **36** = les 31 + **GUILE, FEI-LONG, DEE-JAY,
  T.HAWK, SHIN AKUMA**
- `ro9` = **Hyper** (©2006, 9,93 Mo) — **roster identique à Upper** ⟹ Hyper
  n'ajoute **aucun personnage**, son apport = ~1,9 Mo de données (movesets).

⚠️ Pour lire un roster : trouver la **table de noms** (chercher `ZANGIEF`, dumper
±700 o autour). **Ne pas** tester une liste de noms fournie à la main — erreur commise,
qui avait fait conclure à tort « Upper n'ajoute que Guile ».

**Ce qui est préservé, ce qui ne l'est pas** :
- ✅ **Son Z80 : verbatim.** Le Z80 CPS2 de SFA3 (`sz3.01`) est trouvé octet pour
  octet à l'**offset 0x100** de `ro3_usa_z80.bin`. **Le son ne demandera rien.**
- ❌ **Graphismes : ré-encodés** pour le GS (0/12 sondes haute-entropie de la gfx
  CPS2, brute et désentrelacée, dans les 6 conteneurs de ro3). Les conteneurs
  `roN_usa_gfx_*.bin` commencent par une **table d'offsets** (ex. `e352` :
  `00000600 00000030 … 00000bc0 0000eca0`) — format à reverser.

---

## 5. Le rétro-traducteur (chantier 1)

Outillage dans `tools/untranspile/` (voir son README pour le détail).

**Grammaire du recompilateur**, mesurée sur ro3 (589 445 tokens normalisés) :

| Séquence MIPS | Sens 68K | Occurrences |
|---|---|---|
| `dsll32` → `dsra32` → `st.L RES` | extension `.W` + set flags | 10 429 |
| `ld.L RES` → `beq`/`bne` | branchement sur Z | 9 398 |
| `st.L NFLG` → `beq` | branchement sur N | 3 350 |
| `ld.W Dn` → `dsll32` → `dsra32` | lecture registre en `.W` | 3 566 |
| `addiu` → `sd` … `ld.L A6` | prologue (A6 = frame pointer) | — |
| `ld` → `addiu` → `jr` | épilogue | — |

**Ancre validée** : `MIPS 0x201fa8 ↔ 68K 0x009350`.
```
MIPS : addiu a0,zero,0x6 ; lw v1,0x1114(=A5) ; sh a0,312(v1)
68K  : 3b7c 0006 0138        MOVE.W #$0006, $0138(A5)
```
40/40 constantes alignées **dans l'ordre**. Le 68K montre `1b40 xxxx`
(`MOVE.B Dn,(d16,A5)`) ⟹ **l'original utilise bien A5 comme base**, confirmé des deux côtés.

**L'ordre des fonctions est préservé par grappes** :
`MIPS 0x2014b0→0x201b2c→0x201fa8` ↔ `68K 0x091d8→0x09292→0x09350`.
Pas monotone globalement (blocs réarrangés) mais monotone localement ⟹ **quelques
ancres + interpolation** suffisent, pas besoin d'apparier chaque fonction.

**⚠️ L'oracle n'est pas exact à l'octet.** Le MIPS de l'ancre contient un
`TST.B $-3e64(A5)` + saut **absent du 68K CPS2**, alors que ses voisines matchent
exactement. `A5-0x3e64` est dans les globales de compilation (voisin de la variable
de stage). ⟹ **Capcom a ajouté du code propre à la compilation.** Ne jamais exiger
un match 100 % : trier les écarts entre *bugs du traducteur* et *modifications réelles*.

**Correctif appliqué** : inclure les **déplacements de load/store** dans les
signatures (en excluant `0x1000-0x11ff`, qui est le fichier de registres = plomberie
du recompilateur, pas du 68K). Effet : **11 → 20 ancres**, signatures jusqu'à
57 constantes.

**Grappes monotones confirmées** (`clusters.py`) :
```
MIPS 0x1c8114 → 0x1d6eb4 → 0x1dd6a0 → 0x1e56dc → 0x1e97c8
68K  0x027804 → 0x029766 → 0x02a518 → 0x02b412 → 0x02bcd8

MIPS 0x201b2c → 0x201fa8 → 0x208c48 → 0x20bb24 → 0x20e008
68K  0x009292 → 0x009350 → 0x009fdc → 0x00a522 → 0x00a9c2
```

### ⛔ Ce qui bloque le passage à l'échelle — et le correctif

Deux tentatives d'élargissement ont échoué, pour une même raison de fond :

1. **Interpolation entre ancres** (`clusters.py`) : rend peu, parce que le
   découpage en fonctions est peu fiable **des deux côtés** (9 219 « fonctions »
   MIPS pour 3 161 côté 68K — le MIPS sur-découpe par `jr ra`, le 68K par `RTS`
   multiples). Les comptes ne s'alignent pas.
2. **Chaînage de k-mers** (`chain.py`, sans découpage) : ne trouve que ~23
   empreintes rares. Cause : côté 68K on extrait **tous** les mots de la plage
   `0x100-0xfffe`, donc les **opcodes** (`1b40`, `3b7c`…) polluent le flux. Les deux
   suites ne sont pas comparables terme à terme.

> ⚠️ Noter aussi : **seul le 1er Mo du 68K est du CODE** (c'est la zone chiffrée,
> celle qui a des tables XOR). Au-delà = données. `chain.py` restreint désormais à
> `0..0x100000`.

### ✅ Verrou levé — carte à 26,7 %

**`tools/untranspile/m68k.py`** : décodeur de **longueur** 68000 (ne désassemble pas ;
calcule la taille de chaque instruction et classe ses mots d'extension en
`imm`/`disp`/`abs`). Validé sur la fonction ancrée : **0 opcode inconnu**, et les
opérandes extraits sont exactement `0006 imm / 0138 disp / 0005 imm / 014c disp /
0001 imm / 0400 disp …`.

Effet sur le chaînage :

| | avant | après |
|---|---|---|
| empreintes rares appariées | 23 | **1 392** |
| plus longue chaîne | 6 pts | **496 pts** |

**Deuxième correctif — extraction ITÉRATIVE** : les blocs étant *réordonnés*, une
seule plus-longue-sous-suite-croissante n'en capture qu'un. On extrait une chaîne,
on retire ses points, on recommence (26 passes).

| | une seule LIS | itératif |
|---|---|---|
| blocs colinéaires | 6 | **46** |
| couverture zone code 68K | 3,7 % | **26,7 %** (279 818 o) |

⚠️ Relâcher la tolérance d'ambiguïté **n'aide pas** (le bruit fragmente les blocs) —
garder `AMB=4`.

**Carte exportée** : `tools/untranspile/map_ro3_sfa3.json` (46 blocs avec leurs points).

**Contrôle de cohérence** : l'ancre validée indépendamment (`MIPS 0x201fa8 ↔
68K 0x9350`) tombe bien dans le plus gros bloc (357 pts, `MIPS 0x1ff098..0x20eb00 ↔
68K 0x008baa..0x00ab82`). Les ratios d'expansion des blocs ≥10 points ont une
**médiane de 6,9×**, conforme à la valeur théorique (~6,7×).

### ✅ Traducteur d'idiomes — prototype à 75 % d'identité binaire

**`tools/untranspile/translate.py`** : simulation symbolique légère (on suit ce que
contient chaque registre MIPS : un immédiat, `A5+offset`, la valeur d'un registre 68K)
puis ré-émission de l'instruction 68000, **encodée en octets**.

Testé sur la fonction ancrée (`MIPS 0x201fa8` → `68K 0x9350`) :
**48/64 mots identiques (75 %)**, les **20 premiers strictement identiques** :

```
produit : 3b7c 0006 0138 3b7c 0005 014c 1b7c 0001 0400 1b7c 0001 0800 7000 1b40 0559 1b40 0959 …
réel    : 3b7c 0006 0138 3b7c 0005 014c 1b7c 0001 0400 1b7c 0001 0800 7000 1b40 0559 1b40 0959 …
```

#### ⚠️ Correction du mapping des registres (établie par vérité terrain)

Le MIPS fait `sw zero,0x1124` puis `lb a0,0x1124`, et le 68K correspondant dit
`MOVEQ #0,D0` puis `MOVE.B D0,…` ⟹ **`0x1124` = D0, pas D1**. Cohérent avec
l'analyse statistique : `0x1120` n'apparaît **pas** dans les emplacements chauds.

```
A0-A7 = 0x70001100-0x111c     (0x1120 = inutilisé)     D0-D7 = 0x70001124-0x1140
```

#### Bug à ne pas refaire

Le dictionnaire des `lui` doit être **invalidé** dès qu'un registre est réécrit par
autre chose. Sans ça, un `sb a0,0(v1)` où `v1` contient A5 depuis longtemps est capté
par la mauvaise branche. Symptôme : zéro instruction émise, ou déplacements à `0000`.

#### Idiomes restant à implémenter

Première divergence au mot 46 : le 68K réel contient
`082d 0000 00ac` (`BTST #0,$00ac(A5)`) + `660c` (`BNE +12`), puis `422d 0c01`
(`CLR.B`). Il manque donc : **BTST**, les **branchements conditionnels** (la
grammaire des flags est déjà cataloguée), et **CLR** (le 68K préfère `CLR.x` à
`MOVE.x #0` dans certains cas).

#### BTST + branchements implémentés (81 %)

L'idiome est net :
```
lb v1,172(v1)          ; lit [A5+0xac]
dsll32/dsra32          ; extension de signe
andi a0,v1,0x1         ; masque de bit -> le numéro de bit est ici
sw a0,RES ; lw v1,RES ; bne
```
→ `BTST #0,$00ac(A5)` + `BNE`. Encodages : `BTST #imm,(d16,A5)` = `082d bit disp` ;
`BNE`/`BEQ` = `6600`/`6700` (déplacement à résoudre en seconde passe, cf. ci-dessous).

Passage de **75 % à 81 %** d'identité binaire.

### ⛔ Limite de principe : la recompilation est LOSSY

Deux cas donnent un MIPS **rigoureusement identique** :
```
addiu v1,v1,0xc01 ; sb zero,0(v1)   ->  le 68K disait  CLR.B   $0c01(A5)
addiu v1,v1,0xc02 ; sb zero,0(v1)   ->  le 68K disait  MOVE.B #0,$0c02(A5)
```
`CLR.B` et `MOVE.B #0` étant sémantiquement équivalents, le recompilateur a émis le
même code. **Le choix d'origine n'est pas récupérable — l'information n'existe plus.**

⟹ **L'identité binaire à 100 % est impossible par construction.** Ce n'est pas un
défaut d'implémentation, et c'est sans conséquence : on vise une traduction
**correcte d'Upper**, pas une reproduction de SFA3.

> Choix retenu : émettre `MOVE.x #0` plutôt que `CLR.x`. Sur 68000, `CLR` fait un
> **read-modify-write** — inoffensif sur de la RAM, mais potentiellement dangereux
> sur un registre matériel. `MOVE #0` n'a pas cet effet de bord.

### ⭐ Base d'exécution — indispensable pour résoudre les appels

Les cibles de `jal` sont des **adresses d'exécution**, pas des offsets de fichier.

```
offset_fichier = adresse_exécution − 0x1f0008
```

Trouvée empiriquement : c'est le seul décalage pour lequel les cibles d'appel les
plus fréquentes tombent sur un `jr ra` précédent (= vrai début de fonction). Vérifié
sur la cible la plus appelée, qui donne un prologue net :
`addiu sp,sp,-0x10 ; sd ra,0(sp) ; sw zero,D0 ; lw a0,A0`.

> ⚠️ **Rectification d'une fausse piste** : sans cette base, les cibles semblaient
> pointer vers une zone « bibliothèque d'exécution » en `0x3e0000+` qui se
> désassemblait en charabia. Cette zone n'existe pas — c'était l'artefact du mauvais
> décalage. Ce sont du code de jeu normal.

**Résultat** : sur les 8 plus gros blocs, **1 635 appels sur 1 701 (96 %)** se
résolvent en adresse 68K via la carte. Les cibles tombent dans le voisinage immédiat
de l'appelant (une fonction appelle ses voisines), ce qui confirme la cohérence.

> Penser à forcer les adresses 68K **paires** (mots de 16 bits) après interpolation.

### Couverture du traducteur — 99 %

Mesurée par `tools/untranspile/coverage.py` sur les 12 plus gros blocs
(121 618 instructions MIPS) : **99,0 % absorbées** par les idiomes traités.
Ne restent que les accès 128 bits de l'EE (`lq`/`sq`, 0,8 %) — plomberie du
recompilateur, sans contrepartie 68K.

**Arithmétique registre-registre** implémentée. L'idiome :
```
lb v1,D0 ; lb v0,D1 ; addu v1,v1,v0 ; sb v1,D0   ->   ADD.B D1,D0
```
Encodage : `<base> | dst<<9 | taille<<6 | src`, avec
`ADD=0xd000, SUB=0x9000, AND=0xc000, OR=0x8000, EOR=0xb100` et
taille `B=0, W=1, L=2`. Vérifié : `ADD.B D1,D0` → `d001`.

### ⭐ Tables de données — le problème est plus simple qu'il n'y paraît

Motif rencontré :
```
lh v0,D0 ; dsll32/dsra32 ; sll v1,v0,1
lui v0,0x59 ; addiu v0,0x3a20      ; adresse de TABLE (0x593a20)
addu v0,v1,v0 ; lw v0,0(v0) ; jalr v0   ; dispatch par table de sauts
```

Première réaction : « il faut cartographier les données comme on a cartographié le
code ». **C'est faux.** Pour *traduire*, on n'a pas besoin de retrouver l'adresse
d'origine d'une table côté 68K — on **génère notre propre disposition**. Il suffit de :

- **copier verbatim** les tables de valeurs ;
- **réécrire** les tables de pointeurs avec les adresses 68K traduites (via la carte).

La relocation porte sur **notre sortie**, pas sur un appariement avec l'original.

`tools/untranspile/tables.py` repère les adresses construites par `lui`+`addiu` et
classe chaque table. Sur les 8 plus gros blocs : **60 tables distinctes —
11 de POINTEURS (à réécrire), 48 de VALEURS (à copier)**.

Exemple vérifié : la table `0x593a20` contient bien des pointeurs de code
(`0x3ef390`, `0x3f0190`…) qui retombent dans la région cartographiée, tandis que
`0x5939e0` ne contient que des valeurs (0 pointeur sur 16).

> Disposition du module : **code** en `0x2xxxxx-0x6xxxxx`, **données** en `0x85xxxx`
> (fin du module).

### ✅ Chaîne complète de bout en bout

```
MIPS  ->  traducteur d'idiomes  ->  assembleur 2 passes  ->  octets 68000
```

**`tools/untranspile/assemble.py`** : assembleur deux passes.
- *Passe 1* — placement : chaque instruction 68K émise retient l'adresse MIPS dont
  elle provient ; on construit la table `adresse_MIPS -> offset_68K`.
- *Passe 2* — résolution : les branchements (émis avec une cible symbolique) reçoivent
  leur déplacement, en forme courte 8 bits si elle rentre, sinon en forme 16 bits.

Testé sur la fonction ancrée : **27 instructions placées, 68 mots, 1 seul branchement
non résolu** (sa cible sort de la plage traduite — normal).

```
+0000  [mips 00201fbc]  MOVE.W #$6,$0138(A5)   3b7c 0006 0138
+0018  [mips 00202030]  MOVEQ #$0,D0           7000
+001a  [mips 00202048]  MOVE.B D0,$0559(A5)    1b40 0559
```

### 🏗️ Architecture d'une traduction complète

1. **Code** → traduit en 68000 (traducteur d'idiomes, 99 % de couverture).
2. **Tables de valeurs** → copiées telles quelles.
3. **Tables de pointeurs** → réécrites avec les adresses 68K de notre disposition.
4. **Seconde passe de placement** → résolution des déplacements de branchement et
   des adresses absolues, comme un assembleur deux passes.
5. **Graphismes** → chantier séparé (voir ci-dessous).
6. **Son** → rien à faire (Z80 verbatim).

---

## 8. Chantier graphique — état

**Format de tuile établi.** Le conteneur `ro5_usa_gfx_e352.bin` (3,89 Mo) commence par
un en-tête contenant des **sous-tables d'offsets**. À partir du mot 12 (`+0x30`) on
trouve une suite d'offsets espacés **exactement de 0x20** — soit une tuile 8×8 4bpp.

En rendant la zone `0x3d370` en **4bpp PACKÉ** (2 pixels par octet, *pas* le planaire
CPS2), on obtient une **police parfaitement lisible** :
`0123456789abcdef`, `abcdefghijklmnopqrstuvwxyz`, `ABCDEFGHIJKLMNOPQRSTUVWXYZ`.

> ⟹ **Tuiles : 0x20 octets, 4bpp packé.** La conversion vers le planaire CPS2 est
> donc un transform simple et entièrement défini (fonction déjà écrite lors des essais
> d'appariement).

**Ce qui reste.** Les sondes à `0x100000`, `0x200000` et `0x300000` rendent du bruit :
le gros du conteneur n'est **pas** stocké en clair. Très probablement **compressé** —
ce qui est cohérent avec le moteur, dont on possède déjà le décompresseur
(`tools/lz148778.py`, validé octet pour octet).

### ✅ CHANTIER GRAPHIQUE RÉSOLU

**Structure du conteneur** (`tools/untranspile/gfx.py`) :

```
+0x00   petit en-tête (12 mots)
+0x30   TABLE DE TUILES — un mot de 32 bits par tuile :
          valeur 0    -> tuile absente
          bit31 = 0   -> offset d'une tuile BRUTE      0x20 o  (8x8,   4bpp packé)
          bit31 = 1   -> offset d'une tuile COMPRESSÉE 0x80 o  (16x16, 4bpp packé)
                         (masquer le bit 31 pour obtenir l'offset)
puis    zone de données
```

> C'est **exactement la convention du contexte de couche** rencontrée côté PS2 :
> bit 31 = donnée compressée. Le moteur est cohérent avec lui-même.

**Compression** : celle du moteur (`tools/lz148778.py`, déjà validée octet pour octet).

**Comment la taille 0x80 a été établie** — test d'auto-cohérence, pas une supposition :
pour chaque entrée, la longueur compressée réelle est connue (écart jusqu'à l'entrée
suivante). On cherche la taille de sortie qui fait consommer **exactement** ce nombre
d'octets. Résultat : **0x80 sur 12/12 entrées testées**, sans aucune ambiguïté
(0x20 et 0x40 consomment trop peu, 0x100+ trop).

`0x80` = 128 octets = **16×16 en 4bpp**, la taille native des sprites CPS2.

**Validation** : les tuiles décompressées rendent des **fragments de sprites
reconnaissables** (membres, bottes, mains, plis de vêtements).

**Rendement, zéro échec** :

| Conteneur | Tuiles extraites |
|---|---|
| `ro5_usa_gfx_e352` (Upper) | 62 465 |
| `ro5_usa_gfx_e354` (Upper) | 40 928 |
| `ro5_usa_gfx_e387` (Upper) | 65 279 |
| `ro3_usa_gfx_e255` (SFA3)  | 56 156 |

**168 672 tuiles pour Upper** = son jeu de sprites complet.
*(`e353` et `e389` ne rendent que quelques entrées — structure différente, à examiner ;
non bloquant.)*

**Conversion vers CPS2** : les pixels sont en **4bpp packé** (2 px/octet, nibble bas =
pixel gauche), alors que la CPS2 est en **planaire**. `gfx.packed_to_planar()` fait la
conversion — c'est un transform entièrement défini, sans inconnue.

### Reste à faire sur le traducteur

- **Déplacements de branchement** : émis avec une cible symbolique (adresse MIPS).
  Il faudra une **seconde passe de placement** pour les résoudre, comme un assembleur.
- Autres idiomes : arithmétique (`ADD`/`SUB`/`CMP`), appels (`JSR`/`BSR` depuis
  `jal`), `MOVEM` (prologues/épilogues), modes d'adressage indirects.

---

## 6. Prochaines étapes, dans l'ordre

1. **Rétro-traducteur** — inclure les déplacements dans les signatures pour élargir
   les ancres, exploiter l'interpolation par grappes, puis écrire le traducteur
   d'idiomes et le valider fonction par fonction sur ro3 (en tolérant les
   modifications de compilation).
2. **Format graphique** — reverser le conteneur `e352` (table d'offsets + codec des
   entrées) jusqu'à afficher un sprite reconnaissable d'Upper.
3. **Fork FBNeo** — région graphique étendue au-delà de 32 Mo.

En parallèle, court terme : **diagnostic live du cross-stage PS2** (une capture
suffit à départager les trois causes).

---

## 6bis. Propagation par graphe d'appels — journal d'une correction

Tentative d'élargir la carte en exploitant le graphe d'appels : si une fonction MIPS
cartographiée appelle N fonctions dans un ordre donné, sa jumelle 68K appelle N
fonctions dans le même ordre. Séquence des résultats, **instructive** :

| Étape | Résultat | Verdict |
|---|---|---|
| 1. Propagation naïve | ×4,1 — 1 232 paires | chiffre flatteur |
| 2. Validation par échantillon | **43 % de paires douteuses** | le chiffre était creux |
| 3. Ajout d'une vérification | 4 acceptées sur 1 890 | la méthode semblait morte |
| 4. Diagnostic sur l'ancre connue | **l'extracteur 68K était faux** | ce n'était pas la méthode |
| 5. Après correction | 0 appel des deux côtés sur l'ancre | extraction enfin juste |

**Deux bugs dans l'extracteur d'appels 68K** :
1. Sur opcode inconnu, je **resynchronisais octet par octet** → des données étaient
   lues comme des instructions → faux appels en masse (25 appels dans une fonction
   qui n'en a aucun). Correctif : **s'arrêter** sur opcode inconnu.
2. J'utilisais une **fenêtre de taille fixe**, qui débordait sur les fonctions
   suivantes. Correctif : utiliser les **bornes réelles** de chaque fonction.

### ⭐ La cause racine : le découpage en fonctions du MIPS

Même corrigé, la propagation ne rendait rien. Raison : **les amorces étaient fausses**.
Elles venaient d'un « recalage » d'un point de la carte sur le début de fonction
l'englobant — ce qui n'a de sens que si les découpages correspondent. Or :

```
MIPS découpé par « jr ra »        : 9 219 « fonctions »   <- sur-découpage x3
MIPS découpé par cibles de « jal » : 2 788 fonctions       <- vrais débuts
68K découpé par RTS                : 3 161 fonctions
```

Une fonction 68K a souvent **plusieurs points de sortie** ; chaque `jr ra` du MIPS
recompilé était compté comme une fin de fonction. **Les cibles de `jal` sont, par
définition, de vrais débuts de fonction** — et le compte s'aligne alors avec le 68K
(2 788 contre 3 161, l'écart correspondant aux fonctions jamais appelées directement).

⟹ **Toujours utiliser `mips_functions_by_calls()`**, pas le découpage par `jr ra`.

### ⚠️ CORRECTION DE MÉTRIQUE — les chiffres de couverture étaient gonflés

Les blocs **se chevauchent** dans l'espace 68K (35 sur 80 pour k=3). Additionner leurs
étendues comptait donc plusieurs fois les mêmes octets. La vraie mesure est l'**union**
des intervalles.

| Carte | Chiffre annoncé (somme) | **Couverture réelle (union)** |
|---|---|---|
| k=4 (l'ancienne référence) | 26,7 % | **17,3 %** |
| k=3 (nouvelle) | 48,5 % | **27,7 %** |

> Le « 26,7 % » cité pendant toute la session était **surcompté 1,5×**.
> `chain.py` rapporte désormais l'union, et affiche le facteur de surcomptage.

**Le progrès reste réel** : passer de `k=4` à `k=3` fait gagner **17,3 % → 27,7 %**
(+60 %), pour un simple changement de paramètre. Validation de la carte k=3 :
l'ancre validée à la main y est contenue ✓ ; les ratios d'expansion ont une médiane
de 6,3 (théorie ~6,7) avec 5 % d'aberrants ✓.

### Bilan : l'élargissement de la carte reste OUVERT

Avec le bon découpage, l'appariement par constantes passe de 359 à **1 215 fonctions
à signature riche**, mais le nombre de paires solides ne monte pas (**16** contre 20).
Et deux d'entre elles sont manifestement fausses (192 o de MIPS appariés à 5 430 o de
68K, sur 6 constantes seulement) — **relever le seuil de constantes** pour les filtrer.

| Méthode | Couverture réelle (union) |
|---|---|
| Chaînage de k-mers, k=3 (`chain.py`) | **27,7 %** — meilleur résultat |
| Chaînage de k-mers, k=4 | 17,3 % |
| Propagation par graphe d'appels (`propagate.py`) | ~0 après vérification |
| Chaînage au niveau fonction (`fchain.py`) | 33 paires ; chaînes non colinéaires, inexploitable |

> `fchain.py` est conservé comme trace : malgré le bon découpage, le filtre de taille
> et une sélection de candidats élargie, la vérification par constantes ne valide que
> 33 paires sur 1 346 candidates. La plupart des fonctions n'ont pas de signature
> assez distinctive — c'est pourquoi le chaînage au niveau des **constantes** reste
> supérieur : il n'exige pas que chaque fonction soit identifiable.

**Pistes non essayées** pour aller plus loin :
- élargir la sélection de candidats dans `rosetta2.py` (actuellement les 6 meilleurs
  d'un index inversé — probablement trop étroit) ;
- exploiter la **taille relative** des fonctions comme filtre (le ratio d'expansion a
  une médiane de 6,9× et une faible dispersion : une paire à 0,0× ou 0,3× est fausse) ;
- chaîner au niveau des **fonctions** plutôt que des constantes (LIS sur les index de
  fonctions, en exploitant la colinéarité déjà démontrée).

## 7. Pièges rencontrés (à ne pas rejouer)

- **Correspondances binaires** : toujours **filtrer par entropie** avant de conclure.
  Des sondes de 128 o ont « matché » sur des zones répétitives et fait croire à une
  correspondance CPS2↔Anthology qui n'existe pas.
- **Dumps et variable de stage** : comparer des dumps par leur ID de stage **ne
  marche pas** — la plupart viennent d'essais où l'ID était *forcé* (la variable
  change, le décor chargé non). Vérifié : banque et contexte identiques sur 4 dumps
  d'IDs différents.
- **Scans lourds** : l'utilisateur joue sur la même machine. Toujours `nice -n 19`.
  Un scan capstone re-découpant son tampon à chaque reprise est **quadratique** —
  décoder par champs de bits à la place.
- **Noms de fichiers** : `anthology_extract/*_prog68k.*` sont **mal nommés** (label
  d'une session ancienne) — leur contenu est du **MIPS**, pas du 68K.
- **Identité git** : toujours committer en **pseudonyme**
  (`Rickow <30348240+Rickow@users.noreply.github.com>`). Une config globale est
  désormais posée, mais vérifier `git config user.email` avant le premier commit.

---

## Carte MIPS↔68K : chaînage colinéaire, métrique honnête, et une impasse (session suivante)

### 1. Le vrai défaut des chaînages précédents : LIS ≠ colinéarité

`chain.py`, `fchain.py` et le premier `xsearch.py` utilisent une **LIS** (plus longue
sous-suite croissante). Une LIS n'impose que l'**ordre** : deux points aux deux bouts du
binaire le respectent. D'où des « blocs » à ratio d'expansion 50× qui traversent tout le
binaire (`xsearch.py` affichait « 67 % » ; `fchain.py` « 170 % »).

**`chain2.py`** remplace la LIS par un **chaînage à contrainte locale** (comme les
aligneurs de génomes) : deux ancres ne se suivent que si le ratio local
`Δmips/Δ68k ∈ [3 ; 12]` et `Δmips ≤ 0x20000`. Il fusionne les ancres k=3 et k=4.
Tous les ratios obtenus sont plausibles (min 3,3 / **médiane 6,4** / max 11,6).

### 2. Deux mesures de couverture, et seule la seconde compte

| Mesure | Définition | Valeur (`map_chain2.json`) |
|---|---|---|
| **Étendue** (union des blocs) | de la 1re à la dernière ancre de chaque bloc | 46,0 % |
| **Utilisable** | union des segments **entre deux ancres consécutives** (Δmips ≤ 0x800, ratio ∈ [2 ; 16]) | **4,2 %** (1 822 segments) |

> Interpoler linéairement d'un bout à l'autre d'un bloc est **faux** : le taux d'expansion
> varie localement (une instruction 68K → 2 à 20 instructions MIPS). Vérifié :
> à des positions interpolées sur tout un bloc, l'identité d'opcodes retombe au niveau
> du bruit (10 % contre 5 % au témoin, 14 % des sondes au-dessus).
>
> ⟹ **`translate.mips_to_68k()` interpole désormais PAR MORCEAUX** entre les deux ancres
> qui encadrent l'adresse, et **s'abstient** (renvoie `None`) si le segment est trop long
> ou de ratio invraisemblable. Sur l'ancre manuelle : prédit `0x934c` pour `0x9350` réel
> (2 mots d'écart).

**Tous les chiffres antérieurs (26,7 %, 27,7 %, 46 %) sont des ÉTENDUES.** La couverture
réellement exploitable pour traduire est de l'ordre de **4 %**. Le facteur limitant est
la **densité d'ancres** : 2 260 ancres pour 1 Mo de code 68K.

### 3. Vérificateur indépendant (`verify.py`) — fiable, mais seulement là où le traducteur parle

Principe : traduire le MIPS en 68000, comparer les **opcodes** émis aux opcodes réels à
l'endroit prédit, **avec un témoin** (mêmes mesures à des offsets tirés au hasard).

- Sur l'ancre connue `MIPS 0x201fa8 ↔ 68K 0x9350` : **96 %** contre témoin médian 0 %,
  p95 4 % ⟹ le vérificateur discrimine parfaitement.
- Sur les ancres de la carte : 12 % contre 11 % au témoin ⟹ **non concluant**, et on sait
  pourquoi : hors des blocs étudiés, le traducteur n'émet qu'**une quinzaine d'opcodes
  par fenêtre de 0x600 octets**, dont **46 % sont `4eb9` (JSR) et `4e75` (RTS)**, présents
  partout. 52 opcodes distincts seulement.
- Correctif : ne scorer que les opcodes **informatifs** (`verify.BANAL` exclut JSR/RTS).

**✅ RÉSULTAT APRÈS CORRECTIF — la carte est validée par un signal indépendant :**

| | Identité d'opcodes informatifs | Témoin (hasard) |
|---|---|---|
| Ancre manuelle | 96 % | médiane 0 %, p95 4 % |
| Ancres de `map_chain2.json` (38 sondes) | **médiane 25 %, moyenne 29 %** | **médiane 0 %, moyenne 5 %** |

**22/38 sondes (58 %) nettement au-dessus du témoin.** Mais **52 sondes sur 90** n'ont
pas pu être évaluées : le traducteur y émet moins de 6 opcodes informatifs. Les ancres
sont donc majoritairement justes ; l'identité modérée (25 % contre 96 % sur l'ancre) et
les sondes inévaluables pointent vers la même cause : **le traducteur**, pas la carte.

Contre-vérification par le signal réciproque (`xcheck.py`, recouvrement de constantes
dans des fenêtres appariées) : ancres de la carte **57 %** contre témoin **6 %**.
(Pas totalement indépendant — c'est le signal qui a construit la carte — mais la fenêtre
mesurée est bien plus large que les k-mers d'origine.)

### 4. Impasse documentée : la densification par opcodes (`densify.py`)

Idée : le signal d'opcodes est mauvais chercheur global (opcodes peu variés ⟹ une
empreinte se retrouve partout) mais pourrait marcher **dans une fenêtre déjà encadrée**
par deux ancres fiables. Alignement LCS des opcodes dans chaque fenêtre.

| Filtre | Ancres ajoutées | Couverture utilisable |
|---|---|---|
| aucun (opcodes isolés acceptés) | +5 471 (×3,4) | 8,0 % |
| suites ≥ 2 opcodes consécutifs | +239 | 4,2 % |
| suites ≥ 3 | +29 | 3,8 % |

Les ancres ajoutées sans filtre ne passent la contre-vérification qu'à **29 %** (contre
57 % pour les ancres d'origine) : c'étaient surtout des appariements d'opcodes isolés
banals. Dès qu'on exige de la spécificité, **le gain disparaît**. ⟹ **Le 8,0 % était
creux ; la densification par opcodes ne marche pas avec le traducteur actuel.**

### 5. Conclusion : le verrou s'est déplacé

Le goulot n'est plus l'alignement — c'est le **traducteur hors des blocs étudiés** : il
émet trop peu d'opcodes, et surtout les banals. Le « 99 % de couverture d'idiomes » était
mesuré sur les 12 plus gros blocs, choisis parce qu'ils étaient bien compris. Tant que le
traducteur ne produit pas un flux d'opcodes riche partout, (a) on ne peut pas densifier
la carte par opcodes, (b) on ne peut pas vérifier la carte hors de ces blocs, et (c) on ne
produit de toute façon pas de 68000 exécutable ailleurs.

**Prochaine étape logique** : mesurer le taux d'émission du traducteur sur TOUT le
binaire (et non sur les blocs choisis), lister les idiomes MIPS non reconnus par
fréquence, et les ajouter du plus fréquent au moins fréquent.

---

## Recensement du traducteur et quatre corrections de fond (session suivante)

### 1. `census.py` : ce que le traducteur rate vraiment, sur tout le binaire

Critère : toute instruction 68000 laisse un **effet** visible dans le MIPS (store vers
un slot de registre, store mémoire, branchement, appel). Un effet sans instruction 68K
émise à cet endroit = une instruction **manquée**. Classé par type et par base
d'adressage, c'est la liste de travail du traducteur.

**Premier recensement : 25,8 % des effets traduits** (et non 99 % : ce chiffre ne valait
que sur les 12 blocs étudiés). Ordre des manques : écritures de Dn 21 %, stores
`(d16,A6)` 17,8 %, `beq` 14 %, `jalr` 10,9 %, stores base inconnue 9,2 %, écritures
d'An 7,4 %, stores `(d16,A4)` 4,3 %…

### 2. Généralisation A5 → An (tout registre d'adresse)

A5 était codé en dur (`Sym('a5', disp)`). Généralisé en `Sym('an', (n, disp))`, avec
encodeurs `enc_move_imm_an`, `enc_move_dn_an`, `enc_btst_an`, `enc_clr_an`
(`(d16,An)` = mode 5 ; A5 redonne exactement 1b7c/3b7c/2b7c/1b40|n/082d).
La ROM confirme la priorité : `MOVE (d16,A6)` = **10 405** occurrences contre 2 407
pour A5. Résultat : **25,8 % → 36,5 %** ; sondes évaluables par `verify.py` 38 → 81,
identité médiane 27 % contre 4 % au témoin (les nouveaux opcodes A6 sont bien ceux
de la ROM).

### 3. Idiomes sur Dn + invalidation de l'état suivi

- `MOVE.x (d16,An),Dn` : lecture `[An+disp]` puis store vers un slot D.
- `ANDI/ORI/EORI.x #imm,Dn` et `ADDQ/SUBQ/ADDI` (forme courte si |v| ≤ 8).
- **Vérifié octet pour octet dans la ROM** : `302d 051a 0240 f70f` (`MOVE.W $051a(A5),D0 ;
  ANDI.W #$f70f,D0`) trouvé à 2–4 octets de la position prédite.
- **Correctif de sûreté** : un registre MIPS écrasé perd désormais la lecture mémoire
  qu'il portait (`dest_reg()`), et une instruction non traitée invalide sa destination.
  Sans ça, de faux `MOVE (d16,An),Dn` pouvaient être émis.

### 4. ⚠️ Les bornes de la zone de code étaient fausses

Tous les outils scannaient `0xb000..0x30b000`. L'**en-tête** du module ro3 dit :
`'MWo3' | 4 | 0x1f0000 (base) | 0x393c40 (taille du code) | …`. Vérifié par la densité
de `lui rX,0x7000` : premier à `0xac`, dernier à `0x393c1c`.
⟹ **on ne scannait que 84 % du code.** Constantes centralisées : `mips.CODE0/CODE1`
(et `mips.code_bounds(buf)` lit l'en-tête). Plus aucun outil n'a de bornes en dur.

### 5. ⚠️ La base d'exécution était fausse de 8 octets : c'est `0x1f0000`

`0x1f0008` (documenté plus haut) est **faux**. Sur les 10 824 appels, la cible tombe
sur un prologue `addiu sp,sp,-X` (ou un `lui 0x7000`) dans **65 à 89 %** des cas avec
`0x1f0000`, dans **0 %** avec `0x1f0008`. L'ancienne vérification regardait la cible la
plus appelée : avec `0x1f0008` elle tombe sur les **2 `nop` d'alignement** (fonctions
alignées sur 16 octets) et le prologue apparaissait 2 instructions plus loin.
`0x1f0000` est aussi la base écrite dans l'en-tête. Corrigé dans `translate.py`,
`funcs.py`, `tables.py`, `propagate.py`. **Aucun pnach n'en dépendait.**

### 6. Les « stubs » sont des veneers 68K, pas du code natif

106 fonctions sans aucun accès au banc de registres, du type
`addiu sp ; sd ra ; lui/addiu v0,X ; jalr v0 ; [lui/addiu v0,Y ; jalr v0] ; ld ra ; jr ra`,
appelées par 1 282 sites. Comparaison avec la ROM (site `0x4d7c0`) : là où le MIPS fait
`jal stub`, la ROM a `BSR`, et la cible du BSR (`0x7ad2`) contient
`JSR $1c0ba ; JMP $1c126`. **Un stub est la recompilation d'un tel veneer**, avec des
`jalr` vers des adresses constantes (dans ro3, du code recompilé normal).

⟹ nouveaux idiomes :
- `lui+addiu` → `Sym('const')` ; **`jalr` vers une constante → `JSR (xxx).L`**.
- **Appel terminal** (appel immédiatement suivi de `ld ra ; addiu sp ; jr ra`) →
  **`JMP (xxx).L`**, et le `jr ra` n'est plus traduit en RTS. Justifié par la ROM :
  `JMP` = 5 559 occurrences contre **55** `JSR/BSR ; RTS`.
- Le veneer se traduit en `JSR $1c0b8 ; JMP $1c124` contre `JSR $1c0ba ; JMP $1c126` dans
  la ROM : structure et opcodes exacts, adresses décalées d'un mot (précision de la
  carte aux points d'entrée). **Sans importance pour une traduction réelle** (Upper,
  Hyper) : les cibles y seront symboliques et résolues par notre assembleur. Les
  adresses exactes de SFA3 ne servent qu'à la validation.

> Leçon : le classement « natif = < 1 % de `lui 0x7000` » était contaminé par ces
> veneers (du 68K recompilé qui ne touche aucun registre). Les 248 « fonctions
> natives » sont à re-trier : veneers d'un côté, vrai code ajouté par le portage de
> l'autre.

### 7. Crochets ajoutés par le portage

Site `0x1c7b1c` : `jal 0x571900` entre `MOVE.W $051a(A5),D0` et `ANDI.W #$f70f,D0`, alors
que dans la ROM ces deux instructions sont **consécutives**. La fonction (fichier
`0x381900`, vraie fonction native) remplace le quartet bas de D0.W via une table en
`0x5ac030`. C'est un **crochet du portage** (probablement un remappage d'entrées), à
**supprimer** dans une traduction vers CPS2. Recensement complet des crochets : à faire.

### 8. Bloc de données copié tel quel

ROM `0xcc900..0xdc900` (62 720 o, 6 % du 1er Mo) se retrouve **verbatim** dans ro3 à
`0x3f29a6..0x4029a6` (décalage constant `+0x3260a6`), avec trois petits trous
(probablement des tables de pointeurs réécrites). C'est une ancre exacte pour la carte
des données. Ces 6 % du « premier Mo de code » sont en fait des données.

### 9. Appels, appels terminaux et retours : maintenant cohérents avec la ROM

Surproduction initiale constatée (`JSR` +42 %, `RTS` +34 %, `JMP` +19 % vs la ROM). Causes
identifiées une par une, **toutes vérifiées contre la ROM** :

| Cause | Correctif |
|---|---|
| Duplication de code par le recompilateur | seulement **3 %** du code (copies ≥128 instructions) : pas la cause |
| Décodeur 68K qui sous-compterait la ROM | non : bruts ≈ décodés (RTS 3 826/3 790) ; les 90 587 mots indécodables sont surtout `0xffff` (remplissage) |
| `jalr` calculé (table de sauts) terminal → faux `RTS` | le `jr ra` est absorbé : **1 546** faux RTS supprimés |
| appel suivi d'un saut vers l'**épilogue commun** (16 % des appels) | c'est aussi un appel terminal → `JMP`, saut absorbé (`tail_branch`) |

Répartition des appels MIPS : continue ensuite 42,7 % / retour immédiat 36,0 % / saut vers
épilogue 16,0 % / saut ailleurs 5,4 %. Les « vrais appels » (continue + saut ailleurs) =
**11 918 contre 11 408 JSR+BSR dans la ROM (+4 %)**.

**Un appel terminal est un GOTO.** Distance 68K site→cible mesurée sur 1 492 cas placés :
18 % **0–16 o** (la routine *enchaîne* sur la suivante : aucune instruction dans l'original),
45 % **branchement court** (BRA), 37 % **loin** (vrai JMP). Le choix rien/BRA/JMP dépend de
la position de la cible **dans la disposition de sortie** ⟹ c'est à l'**assembleur**
(`assemble.py`) de le faire ; le traducteur émet `JMP`.

Bilan : `JSR` 12 096 (ROM 11 408) · `RTS` 3 484 (ROM 3 826) · `JMP`/goto 10 407 (ROM : JMP
5 559 + indirects 1 565 + BRA inter-blocs + enchaînements).

**RECENSEMENT : 25,8 % → 36,5 % → 44,9 % → 49,0 %** des instructions 68K traduites.

Restant (ordre) : `beq` 20,5 % · écritures Dn 16,3 % · stores base inconnue 14,4 % ·
stores A6 12,5 % · écritures An 8,7 % · `bne` 6,4 % · `bgez`+`bltz` 7,3 % (tests du flag N).
⟹ **prochain chantier : les branchements conditionnels** (≈ 34 % des manques) — il faut
identifier l'instruction qui positionne les flags (`RES`=Z à 0x1150, `NFLG`=N à 0x1158).


### 10. Écritures d'An : le recompilateur CONVERTIT les adresses (68K → hôte PS2)

Les slots An contiennent des **adresses hôtes PS2**, pas des adresses 68K. Chaque chargement
d'un registre d'adresse s'accompagne d'une conversion. Idiome de `MOVEA.W d16(An),Am`
(vérifié : ROM `3c6e 0038` = `MOVEA.W $38(A6),A6`, puis le `BSR` suivant tombe **exactement**
sur `0x27b3e`) :

```
lh (d16,An) ; extension ; andi 0xffff ; sw -> Am    ; Am = mot etendu a zero
lh Am ; extension ; bgez +32                        ; mot negatif (0x8000..0xffff = RAM 68K 0xFFxxxx) ?
lw Am ; lui 0x90 ; addu ; sw -> Am                  ;   -> Am += 0x900000
```

Ce `bgez` n'est **pas** un Bcc 68K : il est absorbé (`movea_fixup`). Autres idiomes ajoutés :
`LEA d16(An),Am`, `MOVEA.L An,Am`, `ADDQ/SUBQ.W #q,An` (la ROM préfère `.W` : 132 contre 83),
`ADDA.W/.L Dn,Am` et `LEA (An,Dn),Am` (taille d'après le chargement du slot D, suivie par
`ldsize`). Correctif : `dsll32/dsra32` (extension de signe) propagent désormais aussi la
valeur symbolique. Reste : `MOVEA.L #adr,Am` (constante hôte → adresse 68K : exige la carte
des données).

### 11. Drapeaux et branchements conditionnels — ⚠️ `0x1158` est la RETENUE, pas N

Modèle mesuré :
- `RES` (0x1150) = résultat de la dernière opération ⟹ **Z** (`beq/bne` sur RES) et **N**
  (`bltz/bgez` sur RES = `BMI/BPL`).
- **`0x1158` = retenue C** (−1/0, calculée par `sltu` dans les CMP/SUB). La note antérieure
  « NFLG = signe (N) » était **fausse**. `bltz/bgez` sur 0x1158 = `BCS/BCC`.
- Un `CMP` apparaît ainsi (ex. `CMPI.B #$0c,D0 ; BNE`) : sauvegarde de l'opérande dans
  0x1158, `RES ← D0−12`, puis `sltu ; beq ; addiu −1 ; sw 0x1158 ; b ; sw zero,0x1158` —
  ce `beq` interne **n'est pas** un Bcc 68K. (CMP : pas encore traduit.)
- `TST.x` émis seulement si la valeur testée a été **lue sans être déplacée** ; si un `MOVE`
  a déjà été émis pour elle (`moved`), c'est lui qui a posé les drapeaux.

**Validation contre la ROM** (opcode présent à ±16 o de la position prédite / témoin au hasard) :
`TST.B` 74 %/17 % · `TST.W` 71 %/5 % · `BEQ` 64 %/19 % · `BNE` 68 %/16 % · `BPL` 45 %/5 % ·
`BMI` 32 %/6 % · `BCS` 33 %/11 % · `BCC` 38 %/7 %.
**Sens du branchement** (Bcc de la ROM dont la CIBLE correspond à la nôtre) : `BEQ` 79 %,
`BNE` 75 % de même sens ; pour `BPL/BMI/BCS/BCC`, la condition spécifique trouvée est la nôtre
et les inversions sont rares (6/3/0/2 cas).

### 12. Deuxième crochet du portage — dans la fonction ancrée elle-même

`MIPS 0x201fc4..0x201fec` : `TST.B $c19c(A5) ; BNE` qui saute `MOVE.W #5,$14c(A5)`. Dans la
ROM, `MOVE.W #6,$138(A5)` et `MOVE.W #5,$14c(A5)` sont **consécutifs et inconditionnels**.
C'est un ajout de l'Anthology, qui lit une variable en `A5−0x3e64` (voisine de la variable de
décor `A5−0x3e88`) — probablement une zone d'options du portage. ⟹ la fonction « ancre »
n'est pas du SFA3 pur ; à retirer pour une cible CPS2. Avec le crochet d'entrées de
`0x1c7b1c`, deux crochets sont maintenant connus : un **recensement systématique** est à faire.

### 13. Robustesse

`census.py`, `verify.py` et `xsearch.py` avalaient les exceptions en silence (une tranche en
erreur devenait « rien de traduit » sans prévenir). Ils les signalent désormais. Contrôle :
traduction de toute la zone de code (`0x20..0x393c40`) par tranches de 0x4000 : **0 erreur**,
103 464 entrées produites.

**RECENSEMENT : 25,8 → 36,5 → 44,9 → 49,0 → 52,8 (écritures d'An) → 62,2 % (branchements).**
Restant : écritures Dn 22,3 % · stores base inconnue 19,4 % · `beq` 17,8 % (dont les `beq`
internes aux CMP, qui ne sont pas des Bcc) · stores A6 16,9 % · slots « s » 7,0 %.
**Prochain chantier : traduire les `CMP`** (absorbe les `sltu ; beq` internes et donne leur
comparaison aux Bcc), puis les stores à base inconnue.

### 14. Comparaisons (CMP/CMPI) et correctif de l'instantané des sources

Idiome : `andi #ff|#ffff` (**extension à zéro** à la taille de l'opérande — ce n'est PAS
un `ANDI` 68K), puis soustraction (`addiu −imm` ou `subu`), extension, `sw RES`, puis le
calcul interne de la retenue (`carry_block`, absorbé). Le `CMP` est émis **au moment du Bcc
qui consomme les drapeaux**. Exemples produits : `CMPI.B #$c,D0 ; BNE`, `CMPI.B #$1,$c000(A5) ;
BEQ`, `CMP.W $01ca(A5),D0 ; BGT`. `bgtz/blez` sur RES = `BGT/BLE`.
**Validation ROM** : `CMPI.B` 51 %/7 % · `CMPI.W` 61 %/2 % · `CMP.W` 40 %/5 % · `CMP.B` 42 %/2 % ·
`BGT` 42 %/0 % · `BLE` 31 %/0 %.

**Bug corrigé** : l'invalidation de la destination (ajoutée plus tôt) s'exécutait AVANT
la lecture des sources ; quand destination = source (`andi v1,v1,0xff`, très fréquent),
l'information était perdue. Désormais un **instantané des sources** (`SM`, `SL`) est pris
avant l'invalidation. Le `andi 0xffff` du MOVEA et l'extension à zéro sont unifiés (`zx`).

**RECENSEMENT : … → 62,2 → 65,4 %.** Restant : écritures Dn 24,3 % · stores base inconnue
21,2 % · stores A6 18,5 % · `beq` 11,0 % · slots « s » 7,7 %.

### 15. Copies mémoire, arithmétique en place, et l'aiguillage d'état Capcom

- **`MOVE.x d16(An),d16(Am)`** (lecture puis écriture via une autre base). Vérifié : la paire
  `196e 007e 000d 196e 0079 0079` existe **consécutivement** dans la ROM (2 fois).
- **Arithmétique en place** : lecture, `addiu`, réécriture à la **même** adresse ⟹
  `ADDQ/SUBQ/ADDI/SUBI.x #v,d16(An)` (ex. `SUBQ.B #1,$3b(A6)` = `532e 003b`, présent dans la
  ROM). L'instruction pose elle-même les drapeaux : pas de TST, retenue interne absorbée.
- **`MOVE.x Dm,Dn` / `Am,Dn`** (copie de registre).

**⭐ L'aiguillage d'état Capcom** — **1 558** occurrences dans la ROM, **97 %** sous la forme
exacte :
```
102e 0004    MOVE.B 4(A6),D0          ; numero d'etat
323b 0006    MOVE.W tbl(PC,D0.W),D1   ; decalage lu dans la table
4efb 1002    JMP    tbl(PC,D1.W)
tbl:         dc.w h0-tbl, h1-tbl, ...
```
Le recompilateur a remplacé la lecture de table par une **copie D0→D1**, puis un saut par
**sa propre** table de pointeurs u32 (`lh D1 ; sll 1 ; lui/addiu table ; addu ; lw ; jalr`).
Le traducteur suit `scaled` → `tblidx` → `tblent` et, au `jalr`, **remplace la copie** par
`MOVE.W tbl(PC,D0.W),D1` et émet `JMP tbl(PC,D1.W)` — sortie : `102e 0004 323b 0006 4efb 1002`,
**mot pour mot** la forme de la ROM. La table (cibles MIPS) est mise dans `translate.TABLES`
pour que l'**assembleur** reconstruise les `dc.w`.

⚠️ **Longueur des tables** : lire « tant que l'entrée pointe dans le code » débordait (27 au lieu
de 4) — les tables du recompilateur sont **bout à bout**. Borne correcte : la table suivante
**référencée par le code** (`data_refs()` : 3 726 adresses de données construites par
`lui+addiu`). Vérifié : `0x591300` et `0x591360` sont bien d'autres débuts d'aiguillage.

**RECENSEMENT : … → 65,4 → 72,6 %.** Restant : écritures Dn 29,2 % · stores base inconnue
26,8 % · `beq` 13,7 % · slots « s » 9,7 % · stores A6 9,0 %.

### 16. ⭐ La zone de code contient DEUX processeurs : Z80 puis 68000

Les slots `0x7000_1000..0x103f` (octets appariés, `lhu` sur les paires, adressage
`lw base ; addiu d ; lb` = `(IX+d)`) sont le **banc de registres du Z80** (son QSound),
recompilé lui aussi. Frontière nette, **sans entrelacement** :

| Processeur | Fichier ro3 | Accès au banc de registres |
|---|---|---|
| Z80 (son) | `0x20..0x22b00` | 8 644 (slots 0x10xx), dernier à 0x22ae8 |
| **68000 (jeu)** | **`0x22b00..0x393c40`** | 200 774 (slots 0x11xx), premier à 0x22b0c |

Le Z80 n'a **pas** à être retraduit : sa ROM d'origine est déjà verbatim dans l'Anthology.
`mips.CODE0` vaut désormais `0x22b00` (`mips.Z80_0/Z80_1` pour le Z80).

### 17. Lectures de tables de valeurs indexées, opérations Dn en place

- `lui/addiu table ; addu Dn ; lb/lh 0(...)` ⟹ **`MOVE.x tbl(PC,Dn.W),<dst>`** (`x23b` + mot
  d'extension). Table enregistrée dans `translate.DATA_TABLES` (à **copier telle quelle**).
- lecture mémoire, `addu/subu/and/or/xor` avec Dn, réécriture au même endroit ⟹
  **`ADD/SUB/AND/OR/EOR.x Dn,d16(An)`**.

**⭐ Passage entier reproduit** (ROM `0x2038c`) :
```
traduction : 0240 000f  123b 0000  102d 0526  b02d 0926  6700  6400  d32d 0527
ROM        : 0240 000f  123b 001a  102d 0526  b02d 0926  670c  6406  d32d 0527
```
Identique aux **déplacements près** (résolus par l'assembleur) — y compris un `CMP` suivi de
**deux** branchements sur les mêmes drapeaux.

Autre crochet probable : `MOVE.B $c112(A5),D0` (A5−0x3eee, même zone que `$c19c`) et la table
`0x5840a0` n'existent **nulle part** dans la ROM.

### 18. Recensement : un artefact de mesure corrigé

9 933 `sd ra,0(sp)` (prologues MIPS) étaient comptés comme « écritures mémoire 68K, base
inconnue ». Tous les stores via `sp` (16 087) sont des sauvegardes de registres MIPS
(ra, s0-s7) : aucun n'est une écriture 68K. Exclus.

**RECENSEMENT (zone 68K seule, sans les prologues) : 82,2 %.**
Restant : **écritures Dn 48,9 %** · `beq` 19,3 % · stores A6 10,2 % · écritures An 7,6 %.

### 19. Opérations vers Dn, SWAP

- **`ADD/SUB/AND/OR.x d16(An),Dn`** (`dmem`), **`SUB/SUBI/SUBQ.x src,Dn`** (soustraction réécrite
  dans le registre : c'est un SUB et **pas** un CMP ; c'est lui qui pose les drapeaux,
  `last_sub`), **`SWAP Dn`** (`(bas<<16)|(haut>>16)`, reconnu par motif `is_swap`).
- Aiguillage : la copie D0→D1 est désormais remplacée **sur place** (elle apparaissait sinon
  comme « manquée » au recensement).
- **Vérifié dans la ROM** : `MOVE.W 4(A3),D0 ; ADD.W 4(A2),D0` = paire consécutive (4 endroits) ;
  `MOVE.W $2dc(A1),$2ea(A1)` à `0x2301e` puis `SUB.W $2dc(A1),D0` à `0x23024` (**juste après**) ;
  `OR.B $8a(A5),D0` présent ; `SWAP D1` 26 fois.

**RECENSEMENT : 84,7 %.** Restant : écritures Dn 40,5 % · `beq` 22,4 % · stores A6 11,9 % ·
écritures An 8,9 %.

### 20. Deuxième variante de CMP/SUB : les drapeaux EXACTS

2 165 blocs (439 en .B, 1 726 en .W, 7 après un `addu`). Le recompilateur calcule C et V
exactement puis **négative RES si V** — le signe de RES vaut alors **N⊕V**, c'est-à-dire le
résultat d'une comparaison **signée** :
```
r = a - b ; andi r,0xff|0xffff                  (taille)
C = bit de signe de (~a&b)|(~a&r)|(b&r)         -> beq sC (interne)
V = bit de signe de (a&~b&~r)|(~a&b&r)          -> beq sV (interne)
RES = r ; si V : RES = -RES
```
`exact_flags()` reconnaît le bloc au `subu`, absorbe les branchements internes, protège les
`sw RES` internes (`keep_pend`) et met un CMP en attente marqué « signé » : `bltz/bgez/bgtz/blez`
sur RES deviennent **`BLT/BGE/BGT/BLE`**. Réécrit dans Dn ⟹ `SUB`.
Validation (séquence exacte CMP + Bcc dans la ROM, **zones d'origine seulement**) : 37 % (29/78)
contre 64 % pour les autres CMP — **partiellement validé** : quand le CMP est trouvé, le
branchement est le bon ; l'écart restant vient des opérandes de certains cas. À revoir.

### 21. ⭐ Carte des zones : code d'origine / code AJOUTÉ par l'Anthology (`hooks.py`)

Deux critères indépendants par zone de 64 Ko : densité d'**ancres** de la carte, et part des
**variables A5 étrangères** (déplacements `(d16,A5)` que la ROM n'utilise **jamais** : la ROM en
utilise 1 883 distincts ; `$c19c`, `$c112`, `$9eb0`, `$c000`, `$8c31`, `$c018`… n'en font pas partie).

| Zone ro3 | Ancres | Var. A5 étrangères | Lecture |
|---|---|---|---|
| `0x050000`, `0x180000`, `0x380000–0x39ffff` | 0–2 | **63–79 %** | code du **portage** (ses variables d'options) |
| `0x190000–0x1bffff` | **0** | 0–10 % | manipule les variables du jeu mais **absent des 4 Mo de la ROM** (vérifié) : code 68K non d'origine |
| `0x020000–0x040000` | 40–149 | 38–48 % | mélange : code d'origine + nombreux crochets |
| le reste | nombreuses | 0–12 % | code d'origine |

Conséquences : (1) **toute validation contre la ROM doit exclure ces zones** (la variante
signée tombait à 12 % à cause d'elles) ; (2) pour un portage CPS2, ces zones et les crochets
qui y renvoient sont à **retirer** ; (3) pour Upper (sans ROM de référence), l'ensemble des
variables A5 de SFA3 peut servir de référence approchée (Upper dérive de SFA3).

**RECENSEMENT : 86,7 %** (`beq` 91 %). Restant : écritures Dn 46,8 % · stores A6 13,7 % ·
`beq` 10,4 % · écritures An 10,3 %.

---

## Assembleur, test de bout en bout, et le problème ouvert de la disposition mémoire

### 22. Assembleur réécrit (`assemble.py`) — placement itératif

L'ancien insérait les mots d'extension des branchements longs **après** placement, sans
recalculer : tout ce qui suivait était faux. Le nouveau fait une **relaxation** (choix
optimistes → vérification → allongement → jusqu'à stabilité) et prend les décisions qui
reviennent à l'assembleur : appel terminal = `BRA` / **rien** (enchaînement) / `JMP.L` ;
appel = `BSR` / `JSR.L` ; aiguillage = table émise **juste après** le `JMP` (`dc.w cible−table`).

### 23. Test de bout en bout (`e2e.py batch`) : traduire → assembler → comparer à la ROM

Sur 250 fonctions **d'origine** (zones de crochets et fonctions à variables A5 étrangères
exclues), localisées par la carte + recherche locale :

| Mesure | Valeur |
|---|---|
| **Fonctions reproduites à 100 % octet pour octet** | **16** (22 à 30 mots, branchements résolus) |
| Identité par position (médiane) | 24 % |
| **Identité par alignement LCS (médiane)** | **58 %** (quartiles 46 / 67 %) |

La mesure par position est dure : une instruction manquante décale tout le reste.
**Premières divergences** (liste de travail) : `MOVEQ/MOVE #imm,Dn` non émis (seul `MOVEQ #0`
l'est) · branchement long inversé (`BEQ loin` compilé en `bne` par-dessus un saut : à
refusionner en `Bcc` inversé) · aiguillage en **appel** (`323b 000c 4ebb 1008` = `JSR` par table,
table placée après l'instruction suivante) · adressage indexé `d8(An,Dn.W)` · `CLR` vs `MOVE #0`
· cibles d'appel décalées d'un mot (précision de la carte ; validation seulement).

### 24. ⚠️⚠️ PROBLÈME OUVERT DE CORRECTION : la disposition mémoire du recompilateur

Le recompilateur ne range **pas** la mémoire 68K à l'identique. Exemple (ROM `0x8e52c`) :

| ROM 68K | Traduction (déplacements hôtes) |
|---|---|
| `MOVE.W $4a(A6),$10(A6) ; CLR.W $12(A6)` | `MOVE.W $48(A6),$12(A6) ; MOVE.W #0,$10(A6)` |
| `TST.B $12(A5)` | `TST.B $13(A5)` |
| `MOVE.B #2,4(A6)` | `MOVE.B #2,4(A6)` (identique) |

Modèle : une case utilisée en **long** est stockée en long natif PS2 (petit-boutiste) ⟹ ses mots
sont à **XOR 2**, ses octets à XOR 3 ; une case **mot** ⟹ octets à XOR 1 ; une case **octet**
⟹ identique. **Mesure** (`layout_probe.py`, 1 159 paires instruction émise ↔ ROM, 105 fonctions) :
octets XOR0 92 % ; **mots XOR2 dans 44 % des cas sur A6** ; longs toujours XOR0.

**Règles de prédiction évaluées** (`layout_rule.py`) :

| Règle | Octets | Mots | Longs | Global |
|---|---|---|---|---|
| aucune correction | 92 % | 71 % | 100 % | 86,4 % |
| « long si les accès long dominent » (meilleure) | 93 % | **79 %** | 100 % | **89,0 %** |
| même règle, statistiques locales à la fonction | 92 % | 78 % | 100 % | 88,4 % |

**Non élucidé** : le même couple (registre, déplacement) a des dispositions **différentes** selon
le code (ex. `$18(A6)` : 121 accès long + 204 mot, correct = XOR0 dans les fonctions testées,
XOR2 ailleurs). A6 pointe vers des structures de types différents. La vraie règle est
probablement **par zone de RAM** (ou issue d'un suivi de pointeurs par le recompilateur).

**Pourquoi c'est bloquant** : sur un build CPS2, un déplacement mal converti fait lire/écrire la
**mauvaise moitié** d'un mot — ce n'est pas un défaut d'identité, c'est un bug du jeu. Aucune
règle n'est appliquée dans le traducteur tant que le mécanisme n'est pas compris (89 % ne
suffit pas pour du code exécutable).

**Pistes** : (1) classer par **zone de RAM absolue** plutôt que par (registre, déplacement) — il
faut savoir vers quelle zone pointe A6 à chaque site (suivi des chargements de A6 : `LEA $FFxxxx`,
listes d'objets) ; (2) chercher dans le code du moteur PS2 (hors ro3) une **table de disposition**
consultée par le recompilateur/l'émulateur ; (3) observer la RAM en direct via PINE (PCSX2) :
écrire une valeur connue et voir où elle apparaît.

### 25. Session en direct (PCSX2 + PINE) et état du problème de disposition

**Image 68K reconstruite en lieu PERSISTANT** : le scratchpad temporaire avait été vidé (et
avec lui `sfa3_prog.bin`). Reconstruite dans **`<workspace>/work/cps2/sfa3_prog.bin`**
(`sfa3u.zip` : `sz3u.03c/04c` XOR `sz3ux.03c/04c`, + `sfa3.zip` : `sz3.05c..10b`, puis échange
des octets de chaque mot ; contrôle SP=`00ff8000`, PC=`0000091e`). Tous les outils y pointent.

**Lecture en direct du banc de registres** (`0x70001100..`) : A5 = `0x00908000` ⟹ la RAM 68K
`$FF0000..$FFFFFF` est à **`0x900000..0x90FFFF`** côté PS2 (le `+0x900000` du MOVEA). En-tête
`MWo3` vu en `0x1f0000` (= SFA3 chargé).

**Indice décisif en RAM vivante** : les pointeurs de routine (valeurs égales à des cibles
d'appel de la ROM) sont stockés en **long natif petit-boutiste** (34 cas) — et **tous** à des
positions **2 mod 4**, jamais alignées sur 4. ⟹ la permutation est **relative au champ** (un
long commence où il veut, alignement 2 suffit sur 68K), pas un « XOR 2 » sur l'adresse. La
mesure précédente l'avait masqué (elle éliminait les différences > 3 exprimées en XOR) :
remesurée en **différence signée** : mots A6 = 100 identiques, **57 à −2, 23 à +2**.

**Règles évaluées sur 1 163 paires (aucune n'est suffisante)** :

| Règle | Octets | Mots | Global |
|---|---|---|---|
| aucune correction | 92 % | 70 % | 86,1 % |
| relative au champ, statistiques MIPS | 56 % | 78 % | 64,9 % |
| largeurs du code 68K, globales | 48 % | 54 % | 52,5 % |
| largeurs du code 68K **de la routine** (marge 0x400) | 89 % | 81 % | 87,2 % |

**Conclusion** : le même (registre, déplacement) désigne des champs de largeurs différentes
selon le **type d'objet** pointé par A6. Le recompilateur a donc disposé la mémoire avec une
connaissance du type (pas des largeurs locales). **Piste suivante** : inférer le type par
**familles d'aiguillage** (les routines d'une même table d'état `TABLES` traitent le même type
d'objet) et prendre les largeurs à l'échelle de la famille ; sinon, analyse dynamique.

**Piste alternative, pour la cible réelle (fork FBNeo)** : on n'est pas obligé de retrouver la
disposition d'origine. On génère un NOUVEAU programme 68K ; seuls comptent les accès de
largeurs mêlées au même endroit. Il faudra quand même savoir quels accès se recouvrent.

### 26. Familles d'objets (option 1) et nettoyage de la mesure

**`families.py`** : 1 982 tables d'aiguillage → **474 familles** (routines d'une même table +
routine qui aiguille, sous-états fusionnés), 80 % des routines couvertes (8 490 / 10 631),
taille médiane 7.

**⚠️ La mesure elle-même était bruitée.** L'appariement LCS associe parfois deux instructions
voisines de même opcode (`MOVE.W $18(A6)` ↔ `MOVE.W $1a(A6)`), fabriquant de faux ±2 et de
faux 0. Filtre « **paires sûres** » : instructions précédente ET suivante identiques mot pour
mot des deux côtés. Sur 414 paires sûres :

| | inchangés | décalés |
|---|---|---|
| octets | 263 | 7 |
| **mots** | 95 | **19** (−2 : 13, +2 : 6) |
| longs | 30 | 0 |

⭐ **Sur les paires sûres, aucun (registre, déplacement) n'est à la fois décalé et non décalé** :
la disposition est **cohérente par emplacement**. Les mots décalés sont exactement les moitiés
de champs longs : A6 `$10↔$12`, `$14↔$16`, `$20↔$22`, `$40↔$42`, `$48↔$4a` (positions/vitesses
16.16 des objets), A1/A2 `$10↔$12`.

**Mais la disposition dépend de ce que pointe le registre** : A4 `$10/$12/$14/$16` sont
**non décalés**, alors que les statistiques globales A4 y montrent des accès long. Vérifié : dans
ces fonctions A4 pointe sur des **tableaux d'enregistrements de 8 octets** écrits mot par mot
(`MOVE.W D2,$6(A4)`, `$e`, `$16`, `$1e`… — probablement un tampon vidéo / table de sprites),
une structure différente des objets joueurs. Pas de rotation 16 bits après les `lw` (A4 ou A6) :
les longs sont lus bruts.

**Règles sur paires sûres** : aucune correction 93,7 % · « long domine » par FAMILLE **94,0 %**
(mots 85 %) · global 86,5 %. Les familles aident peu parce qu'elles ne couvrent que A6.

**Prochaine étape (la vraie solution)** : **inférer ce que pointe chaque registre d'adresse** à
chaque accès — (1) A6 dans les routines d'objets : la famille/le pool d'objets ; (2) les autres
An : suivre leur **provenance** dans la fonction (`LEA $adresse` = constante `lui/addiu` → zone
connue : RAM objets, tampons vidéo, tables) ; puis apprendre la disposition **par (zone, décalage)**.

### 27. Zones pointées, validation en jeu, et une idée qui contourne le problème

**`regions.py`** (provenance inter-procédurale de chaque An : constante → zone, copie, pointeur
chargé, paramètre ; arêtes d'appel `jal`, `jalr` constant et tables d'aiguillage ; A5 = RAM) :
zones hôte identifiées — **`0x90xxxx` RAM 68K**, **`0x91..0x94xxxx` mémoire vidéo CPS2 émulée**,
**`0x58..0x88xxxx` données ROM relogées**. Résultat : la zone **ne discrimine pas** (mots décalés
et non décalés sont tous deux en RAM).

**Validation EN JEU (PCSX2, objets joueurs en `0x908400` / `0x908800`)** :
```
P1 +10 : 0000 0220   -> X entier = 0x220 dans le 2e mot  (long natif)
P2 +10 : 0000 02e0   -> X entier = 0x2e0
P1 +14 : 0000 0028   -> Y entier = 0x28 (sol)
P1 +1c : 73b8 006d   -> POINTEUR HÔTE 0x006d73b8 (données du module), long natif
```
⟹ positions 16.16 et pointeurs = **longs natifs** (mots décalés), confirmé en mémoire réelle.

**Hypothèse H2 (calcul vs copie)** : un long est natif quand le code **calcule** avec (vitesse
ajoutée, pointeur) ; une **copie brute** (`lw`→`sw`) ne prouve rien. Explique `$18(A6)` (121 copies,
0 calcul, non décalé) et `$10/$14/$40/$48` (calculs, décalés). Mais échoue sur A4 et `$0c/$50`
⟹ **91,8 %** au mieux (sans correction 93,7 %). La décision du recompilateur est **par champ** et
n'est pas entièrement récupérable par statistiques statiques.

**⭐ IDÉE QUI DISSOUT LE PROBLÈME** : dans un **fork** de FBNeo, rien n'oblige la mémoire du 68K à
être gros-boutiste. Si la RAM (et les données) du 68K sont servies avec la **sémantique du PS2**
(chaque accès octet/mot/long lu en petit-boutiste à l'adresse donnée), alors on traduit chaque
accès **avec son déplacement hôte tel quel** et le comportement est **exactement** celui du MIPS :
plus aucune inférence de disposition. Mieux : toutes les zones hôte tiennent dans les 16 Mo
d'adresses du 68K (données `0x58..0x88xxxx`, RAM `0x90xxxx`, vidéo `0x91..0x94xxxx`) ⟹ la carte
mémoire du fork peut **reproduire celle du PS2**, et les pointeurs hôtes (`$1c`, conversions MOVEA
`+0x900000`) restent valides sans relocation. Coût : le programme produit n'est plus un
programme CPS2 « standard » — il exige le fork (ce qui est déjà la cible choisie).

### 28. ⭐ Le traducteur appris sur SFA3 se transpose à Upper et à Hyper

**En-têtes** : les trois modules ont le même format (`MWo3`, base `0x1f0000`) ; code : SFA3
`0x393c40`, Upper `0x41acc0`, Hyper `0x3bf140` ; 68K à partir de `0x22b00` (SFA3, Upper) et
`0x22de0` (Hyper), Z80 avant.

**Parenté du code** (`modcompare.py`, ressemblance de chaque fonction avec la plus proche de
SFA3, k-grammes d'instructions normalisées ; une première version sous-estimait tout — le
numérateur ne comptait que les k-grammes rares) :

| Ressemblance avec SFA3 | Upper | Hyper |
|---|---|---|
| ≥ 90 % | 28,5 % | 17,3 % |
| 70–90 % | 15,0 % | 14,2 % |
| 40–70 % | 29,9 % | 31,4 % |
| < 40 % (nouveau) | 26,6 % | 37,1 % |

Identique mot pour mot : Upper 22,9 % du code de SFA3 ; Hyper 11,2 % de SFA3 mais 28,6 % d'Upper
⟹ filiation **SFA3 → Upper → Hyper**.

**Recensement** (`MODULE=ro5|ro9 census.py`) : **SFA3 86,7 % · Upper 85,2 % · Hyper 83,8 %** —
malgré 27–37 % de code nouveau ⟹ c'est le **même recompilateur**, les règles apprises sur SFA3
valent pour les trois. Écarts propres à Upper/Hyper : `bgez` 57 % (SFA3 86 %) et écritures d'An
63 % (SFA3 77 %) ⟹ idiomes plus fréquents dans le code nouveau, à ajouter.

**Ce qui ne se transpose pas** : le « corrigé » (la ROM arcade) n'existe que pour SFA3. Pour
Upper/Hyper, la validation directe ne couvre que le code quasi identique à SFA3 ; le reste se
valide par les règles et par l'essai en jeu. La disposition mémoire par champ ne se transpose
pas non plus ⟹ d'où l'intérêt de la mémoire « façon PS2 » dans le fork (§27).

### 29. ⭐ Décision : mémoire en « mode CPS2 » par une recette universelle

**Correction de cap** (validée avec l'utilisateur) : le « problème de disposition mémoire » n'est
bloquant que si l'on veut retrouver les adresses **d'origine** (identité octet pour octet avec la
ROM). Pour un jeu **qui fonctionne**, il suffit que le 68K voie la mémoire **comme le code PS2 la
voit** (petit-boutiste). Recette **universelle**, sans connaissance des champs :

| Accès PS2 (adresse hôte h) | Traduction 68K |
|---|---|
| mot | même adresse h |
| octet | h XOR 1 |
| long | même adresse + `SWAP` des deux moitiés |

Vérifiée sur le cas réel (X écrit en long puis relu en mot à `+$12` : on retombe sur la partie
entière). Marche aussi pour les longs à 2 mod 4, et pour les trois jeux. Coût : un `SWAP` par
accès long — sauf copies mémoire→mémoire et immédiats (pré-échangés à la traduction), gratuits.
Restent à traiter : (1) les **zones matérielles** (vidéo/palettes/sprites) où le matériel CPS2
attend le format d'origine — règle à établir une fois sur SFA3 ; (2) la **conversion des
adresses** de la carte PS2 vers la carte CPS2 (RAM `$FF0000`, données en ROM) — les constantes
suffisent, sauf les pointeurs rangés dans les tables de données.

### 30. Upper et Hyper : même machine que SFA3, décalée

| Module | RAM 68K émulée | Vidéo CPS2 émulée |
|---|---|---|
| SFA3 | `0x900000` | `0x91–0x94xxxx` |
| Upper | `0xa00000` | `0xa1–0xa4xxxx` |
| Hyper | `0xb80000` | `0xb9–0xbcxxxx` |

Même nombre d'adresses constantes par sous-zone (vidéo `0x92`/`0xa2` : 410/411 ; `0x93`/`0xa3` :
43/43…). Base confirmée par deux méthodes (fin des données dans l'en-tête arrondie à `0x80000` ;
`lui X ; addu` de la conversion d'adresse, > 1 280 fois). ⟹ **le pilote CPS2 de FBNeo peut
afficher Upper et Hyper**. `translate.RAM_HI` est désormais propre à chaque module
(`ram_hi_of(buf)`) — auparavant `0x90` en dur, ce qui faisait échouer la conversion des MOVEA
sur Upper/Hyper (écritures d'An 63 %, `bgez` 57 %).

**Variables globales (A5)** : SFA3 72 % arcade / 26 % Anthology ; **Upper 72 % variables de
l'arcade SFA3** / 15 % Anthology / 13 % nouvelles (198) ; **Hyper 77 %** / 6 % / 18 % (147). Les
nouvelles sont toutes en `$c0xx–$c3xx` (`$c200`, `$c140`, `$c32c`…), la zone des variables
d'options de l'Anthology ⟹ zone des ajouts, à trier (nouveauté Upper / couche Anthology).

### 31. Ce qui pourrait être « branché » de Hyper dans Upper (`transplant.py`)

Classement des fonctions de Hyper par rapport à Upper : **communes 28,6 %** (identiques) ·
**modifiées 38,4 %** (≥ 70 % de ressemblance) · **propres à Hyper 33,1 %**. Les fonctions
modifiées/propres reliées par des appels forment des **composants** :

| Taille | Fonctions (propres) | Points de branchement | Dépendances communes | Var. A5 (absentes d'Upper) |
|---|---|---|---|---|
| 1 029 216 o | 374 (208) | 68 | 254 | 82 (4) |
| 181 744 o | 103 (65) | 17 | 90 | 369 (17) |
| 106 160 o | 24 (20) | 2 | 11 | 25 (0) |
| 86 880 o | 37 (26) | 2 | 22 | 7 (0) |
| 46 896 o | 14 (9) | 1 | 18 | 4 (0) |
| 43 056 o | 15 (12) | 1 | 18 | 0 (0) |

- **Point clé : Hyper n'utilise presque aucune variable globale absente d'Upper** (4 pour le plus
  gros composant, 17 pour le second, 0 pour la plupart) ⟹ au niveau des données globales, la
  compatibilité est excellente.
- **158 composants n'ont que 1 ou 2 points de branchement** (39,8 % du code propre/modifié) : des
  blocs quasi autonomes, qui s'appuient sur du code déjà présent dans Upper.
- Le **plus gros composant** (1 Mo, 68 points de branchement, 254 dépendances) ressemble au
  moteur de jeu modifié en profondeur — probablement là où vivent les versions/modes de combat.
  Le second (182 Ko, 369 variables, 17 nouvelles) a le profil des menus / de la sélection.
- **À faire** : étiqueter chaque composant (ce qu'il fait). Pistes : les variables nouvelles
  (candidates pour « version / mode choisi »), les tables indexées par personnage (36 entrées),
  et l'observation en jeu (quelles données changent quand on choisit un mode).

### 32. Recette « mode CPS2 » intégrée au traducteur — et prouvée

**Commutateur** `translate.MEMMODE` (variable d'environnement `MEMMODE`) :
- `hote` (défaut) : déplacements PS2 bruts — pour les outils qui comparent à la ROM arcade.
  **Non-régression vérifiée** : 2 194 instructions sur trois zones, identiques à avant.
- `cps2` : la recette. **Principe : en mémoire les longs sont rangés moitiés échangées, dans les
  registres ils sont justes ; on échange au passage mémoire ↔ registre.**

| Cas | Traduction en mode `cps2` |
|---|---|
| octet | adresse XOR 1 (appliquée à la création de l'accès : tout en profite) |
| mot | inchangé |
| `MOVE.L #imm,mem` | immédiat pré-échangé (gratuit) |
| `MOVE.L mem,mem` | inchangé (gratuit) |
| `MOVE.L mem,Dn` | + `SWAP Dn` |
| `MOVE.L Dn,mem` | `SWAP Dn` ; `MOVE.L` ; `SWAP Dn` |
| `ADD/SUB/AND/OR/EOR.L`, `ADDQ/ADDI.L` en place | `MOVE.L Dt,-(SP) ; MOVE.L mem,Dt ; SWAP ; op ; MOVE SR,-(SP) ; SWAP ; MOVE.L Dt,mem ; MOVE (SP)+,CCR ; MOVEM.L (SP)+,Dt` (indicateurs préservés, Dt ≠ source) |
| `TST.L` suivi d'un test de signe | `TST.W` sur le mot haut (à `+2`) |

Coût mesuré sur SFA3 (5 612 accès longs) : 35 % gratuits, 44 % +1/+2 `SWAP`, 21 % opérations en
place (surtout `ADD.L` position += vitesse).

**Preuve** (`test_recette.py`) : deux mémoires simulées côte à côte (PS2 petit-boutiste avec
lb/lh/lw/sb/sh/sw ; 68K gros-boutiste avec la recette), 200 000 opérations aléatoires qui se
chevauchent (octets dans des mots, mots dans des longs, longs à 2 mod 4) : **99 962 lectures,
0 écart**. Cas réel (X écrit en long à `+$10`, relu en mot à `+$12`) : `0x220` des deux côtés.

**Correctif** au passage : `BTST` sur un bit d'un MOT lu en mémoire visait le mauvais octet
(`BTST` mémoire = octet) ⟹ bit ≥ 8 → octet `h`, bit − 8 ; bit < 8 → octet `h+1` (`btst_target`).

**Conséquence pour la sortie** : les données du module copiées dans la ROM produite devront avoir
les **octets de chaque mot de 16 bits inversés** (LE16 → BE16).

**Reste** : règle des zones matérielles (vidéo/palettes/sprites) ; conversion des adresses
constantes carte PS2 → carte CPS2 (`MOVEA.L #`, `LEA`) ; accès via A7 (pile 68K) ; `CMP.L` sur
mémoire ; hypothèse « base An paire » pour les octets (à surveiller sur les parcours d'octets).

### 33. Effet de la base RAM par module sur Upper et Hyper

| Module | Avant (`0x90` en dur) | Après (`ram_hi_of`) |
|---|---|---|
| SFA3 | 86,7 % | 86,7 % |
| **Upper** | 85,2 % | **86,7 %** |
| **Hyper** | 83,8 % | **85,6 %** |

Écritures d'An : Upper 63 → 77 %, Hyper 63 → 79 % ; `bgez` : 57 → 88 %. **Upper est désormais
traduit au même niveau que SFA3.** Manques restants (les trois modules) : écritures Dn (~45 %
des manques), `beq` (15–19 %), stores A6 (~14 %).

**Hyper → Upper, piste 1 (variables propres à Hyper, 28)** : quasi toutes dans le composant n°1
(menus/sélection), dont `$c178` = variable du décor ; champs **par joueur** écrits par ce composant
(`+$d2`, `+$117` pour P1/P2) ; le moteur (composant n°0) **lit seulement** un octet `+$67` sur quatre
entités (`$0467`, `$0867`, `$0c67`, `$1067`) ⟹ candidat « version / mode du personnage ». À vérifier
en jeu (changer la version d'un personnage dans Hyper et observer ces octets).

### 34. Carte des adresses PS2 → CPS2

Le traducteur émet désormais `LEA $adresse.L,An` pour les adresses constantes (avant : ignorées).
En mode `cps2`, elles passent par `translate.ADDRMAP` / `addr_to_68k`.

| Zone PS2 (relative à la base RAM du module) | CPS2 | Comment on le sait |
|---|---|---|
| `+0x00000..+0x0ffff` | RAM de travail `$FF0000` | évident (A5 = base+0x8000 = `$FF8000`) |
| `+0x20000..+0x4ffff` | **mémoire vidéo `$900000–$92FFFF`** | mêmes adresses aux mêmes fréquences : `90c360↔92c360` (22/22), `90c380↔92c380` (19/19), `90c800↔92c800`, `908000↔928000`… |
| `+0x10000..+0x1ffff` | ? (quelques adresses : `0x912000`, `0x918000`) | non résolu |
| données du module | **notre** placement (`DATA_BASE`) | les adresses d'origine ne sont pas réutilisables : `addr_probe.py` montre que l'outil de portage a **réorganisé les tables une par une** (décalages différents dans une même zone) |

**Accès matériels** : la ROM utilise en adresse absolue `$804000` (entrées, 72×), `$66xxxx` (RAM
annexe), `$618000` (QSound), `$400000` (sorties), `$708000` (sprites)… Le MIPS n'a quasiment
**aucune** constante équivalente ⟹ le portage passe par ses **fonctions natives** pour
manettes/son/sprites. C'est là que se fera le raccordement avec FBNeo (à étudier : les 170
fonctions natives, `native_split.json`).

### 35. La couche « matériel » du portage

- Les accès matériels de la ROM (`$804000` entrées, `$618000` QSound, `$708000` sprites, `$400000`
  sorties) ne sont **pas couverts par la carte** ; le MIPS n'a presque aucune constante équivalente.
- Appels vers des fonctions hors code recompilé : **241 fonctions** appelées ; la plupart **sans
  argument venant des registres 68K et sans valeur rendue** ⟹ elles agissent directement sur la
  mémoire émulée. Beaucoup sont des **relais** (12 instructions, `jalr` vers une adresse du module) mal
  classés par `native_split.json` ; quelques vraies fonctions natives dans la zone `0x38xxxx`
  (ex. `0x3893c0`, `0x38c3f0`) appellent le moteur PS2 (`0x14b3e0`, `0x150270`… avec des immédiats en
  argument : probablement son / système).
- ⭐ **Routines VIDÉES par le portage** (corps = `jr ra`) : **SFA3 113 (380 appels), Upper 142
  (467), Hyper 66 (293)**. Pour une version CPS2, il faudra **remettre les routines d'origine**.
  Identification dans la ROM SFA3 encore **fragile** (peu de sites couverts par la carte, 1 à 3 votes) ;
  les rares routines retrouvées ne sont pas des accès matériels (ex. `$02a7ea` : minuterie
  d'animation `SUBQ.B #1,$32(A6)`) ⟹ le portage a peut-être vidé aussi des routines d'affichage qu'il
  refait nativement. **Ne pas conclure** avant une identification solide.

**Ce qui reste pour « faire tourner SFA3 converti »** : (1) cette couche matériel (routines vidées à
restaurer, appels au moteur à remplacer) ; (2) les idiomes manquants (~13 %) ; (3) assemblage complet
avec placement des données (`DATA_BASE`, octets de chaque mot inversés) et tables ; (4) FBNeo.

### 36. Valeurs immédiates, décalages, NEG, forme `(An)` : 86,7 → 92,6 %

Ajouts (tous vérifiés dans la ROM par séquence exacte) :
- **`MOVEQ #v,Dn` / `MOVE.x #v,Dn`** (seul `#0` était traduit) — ex. `MOVEQ #2,D0`.
- **`LSL/LSR/ASR.x #n,Dn`** — la ROM préfère **LSL** à ASL (LSL.W 677 contre ASL.W 63) ; ex.
  `MOVE.B $72(A4),D0 ; LSR.B #1,D0` présent 4 fois.
- **`NEG.x Dn`** (`subu rd,zero,rt`) — ROM : NEG.L 744, NEG.W 537 ; ex. `TST.B $b(A6) ; BNE ; NEG.L D0 ;
  NEG.L D1` présent 5 fois.
- **`0(An)` → `(An)`** partout (`zero_disp_short`, appliqué à toute la sortie, suites d'instructions
  comprises) : la ROM utilise la forme courte (`NEG.W D0 ; MOVE.W (A2),D1` présent, forme `0(A2)`
  absente). Branchements, MOVEQ et décalages exclus ; tests unitaires sur MOVE/CMPI/BTST/TST.

**Recensement SFA3 : 86,7 → 92,6 %** (écritures Dn 70 → 95 %). **Bout en bout** : 18 fonctions
identiques à 100 % (contre 16), LCS médiane 61 % (contre 58 %). Premières divergences dominantes :
`JSR/JMP` — en partie un artefact de VALIDATION (cible convertie par la carte, décalée de quelques
octets), à corriger dans `e2e.py` en calant sur le vrai début de routine de la ROM.

### 37. Corrections guidées par les premières divergences (`diverge.py`)

Validation améliorée (sans toucher à la traduction) : dans `e2e.py`, les cibles d'appel hors de
la fonction sont calées sur le vrai début de routine de la ROM le plus proche (±16 o), et
l'assembleur emploie la forme **relative** (`BSR`/`BRA`) vers l'extérieur quand elle porte, comme
un assembleur classique et comme l'original (5 201 BSR pour 6 207 JSR dans la ROM).

Corrections de traduction :
- **`CLR.x` au lieu de `MOVE.x #0`** (ROM : `422c 01e5` = `CLR.B $1e5(A4)`).
- **Branchement long inversé** refusionné par l'assembleur : `Bcc` qui saute par-dessus un saut
  inconditionnel ⟹ `B(cond inverse)` vers la cible du saut (on produisait `6602 602c`, la ROM a
  `6744`) ; cible comparée à la **première instruction émise** à partir d'elle.
- **Aiguillage en APPEL** (`JSR tbl(PC,D1.W)`, `4ebb`) quand il n'est pas terminal ; la table est
  posée **après la prochaine rupture** (saut/RTS) et les déplacements `d8` sont calculés (plus de
  `0006` figé). Reproduit exactement `323b 000c 4ebb 1008 4ef9 …` de la ROM.

**Bout en bout** : LCS médiane **68 %** (quartiles 59 / 80 %) contre 65 % ; ≥ 90 % : 27 fonctions ;
identité pondérée 20,8 % (17,7 %). Reste en tête : chargement de pointeur `MOVEA.L mem,An`,
post-incrément `(An)+` et boucles `DBRA`, adressage indexé `d8(An,Dn)`.

⚠️ Rappel : **le scratchpad est vidé entre les sessions** — tous les outils sont désormais dans
`scripts/untranspile/` (dont `diverge.py`).

### 38. ⚠️ Deux bugs de CORRECTION corrigés (adresse décalée, boucles manquantes) + `(An)+`, `DBRA`

Boucle de remplissage (ROM `3e3c 001f 7200 2cc1 51cf fffc 4e75` = `MOVE.W #$1f,D7 ; MOVEQ #0,D1 ;
MOVE.L D1,(A6)+ ; DBRA D7 ; RTS`), MIPS :
```
lw a1,A6 ; addiu a0,a1,4 ; sw a0,A6     A6 += 4
sw a2,0(a1)                             ecriture via l'ANCIENNE valeur de A6
lh D7 ; addiu -1 ; sh D7 ; bgez boucle  D7 -= 1, reboucle si >= 0
```
1. **Bug d'adresse** : un registre MIPS gardant l'ancienne valeur de An était encore pris pour
   « An » après modification ⟹ `ADDQ.W #4,A6 ; MOVE.L D1,(A6)` = écriture **4 octets trop loin**.
   Correctif : quand An change d'une quantité connue, les registres qui gardent l'ancienne valeur
   sont **recalés** (`d → d − delta`, soit `-4(A6)`, juste) ; sinon **invalidés**.
2. **Boucle manquante** : le `bgez` de fin de boucle n'était pas traduit (la boucle aurait fait
   un seul tour). ⟹ **`DBRA Dn,boucle`** (`SUBQ.W #1,Dn` puis `bgez` sur la valeur décrémentée ;
   la `SUBQ` est absorbée). Différence de sémantique assumée : `bgez` (≥ 0) contre `DBRA` (≠ −1),
   identiques pour un compteur de départ ≥ 0.
3. **Formes de la ROM** : `ADDQ.W #s,An` + accès de taille s à `-s(An)` ⟹ **`(An)+`** ; `SUBQ.W #s,An`
   + accès à `(An)` ⟹ **`-(An)`** (`merge_postinc`, passe finale).
   ⟹ **la boucle ressort mot pour mot identique à la ROM.**

⚠️ **Limite connue en mode `cps2`** : un parcours d'OCTETS par `(An)+` rend An impair ; la recette
« octet = XOR 1 sur le déplacement » suppose une base paire ⟹ ces parcours ne fusionnent pas et
restent à traiter spécifiquement (compter leur fréquence avant).

Mesures : recensement 92,8 % ; bout en bout **20 fonctions identiques, 33 ≥ 90 %**, LCS médiane 69 %
(quartiles 60 / 82 %).

### 39. Longs 32 bits, tables de longs, pointeurs, adressage indexé : 93,9 %

- **`MOVE.L #const32,mem`** (`lui+ori/addiu` : en mode cps2, adresse PS2 convertie puis valeur
  échangée).
- **Tables de longs** : `MOVE.L T(PC,Dn.W),mem|Dn`, y compris l'**entrée voisine** (`addiu +4` sur
  l'adresse de table). ROM : `2d7b 001a 0040 2d7b 0018 0048` ⟹ nous `2d7b ···· 0040 2d7b ···· 0048`
  (les `d8` dépendent du placement des tables, fait à l'assemblage).
- **`MOVEA.L d16(An),Am`** (pointeur chargé de la mémoire) ; en mode cps2 : remise en ordre par
  `EXG Am,D0 ; MOVE SR,-(SP) ; SWAP D0 ; MOVE (SP)+,CCR ; EXG Am,D0` (indicateurs préservés).
- **Adressage indexé `d8(An,Dn.W/.L)`** : lecture vers Dn, vers la mémoire, écriture, `CLR`, et
  `LEA d8(An,Dn),Am`. ROM `3230 1000` = `MOVE.W 0(A0,D1.W),D1` reproduit à l'identique.
  ⚠️ En mode cps2, un **octet indexé** a une parité d'adresse inconnue (dépend de Dn) : signalé
  `[OCTET INDEXE ... A TRAITER]` dans le mnémonique au lieu d'être traduit faux.
- Robustesse : une forme d'`an_d` à 4 éléments faisait planter 5 tranches — **détecté par le
  recensement** (qui signale désormais les erreurs), corrigé, 0 tranche en erreur sur toute la zone.

Mesures : **recensement 93,9 %** ; bout en bout 20 identiques, **34 ≥ 90 %**, LCS médiane 70 %
(quartiles 61 / 83 %).

### 40. Dernier lot : 93,9 → 95,3 % — et un 3e bug de correction

- **`lui + ori`** (valeur 32 bits en deux moitiés) reconnu comme `lui + addiu` ⟹ `MOVE.L #v,mem`,
  `MOVE.L #v,Dn` / `MOVEQ`, `LEA #adresse,An` : **+1,1 point d'un coup** (motif n°1 des manques).
- ⚠️ **Bug de correction** : l'effacement d'un registre D (`sw zero,Dn`) était SUPPRIMÉ quand le
  traducteur « croyait » déjà le registre nul — souvenir qui **débordait d'une fonction à l'autre**
  (ex. `MOVEQ #0,D2` en début de fonction disparaissait ⟹ valeur périmée). Désormais toujours émis
  (`MOVEQ #0` / `CLR.W Dn` / `CLR.B Dn` selon la taille).
- **`NEG.x` en mémoire** (en place ; cps2 long : séquence avec `NEG.L Dt`) — ROM : `NEG.L $40(A4) ;
  NEG.L $48(A4)` présent tel quel.
- **Masquage 24 bits** (`dsll32 8 ; dsrl32 8`) = ajout du **recompilateur** (le 68K ignore seul les
  8 bits hauts ; `ANDI.L #$ffffff` : 2 occurrences dans toute la ROM) ⟹ absorbé.

**Recensement 95,3 %** ; bout en bout **21 identiques**, 34 ≥ 90 %, LCS médiane 70 % (62 / 83 %).

**Ce qui reste (~4,7 %) est une longue traîne de formes rares** (≈ 50 cas chacune sur 145 000) :
comparaison avec un registre d'adresse (`CMPA`), indicateurs recalculés via des temporaires sur la
**pile MIPS** (code multi-précision / ADDX), comparaisons où la case « retenue » `0x1158` sert de
stockage temporaire de l'opérande, écritures des slots `0x1120`/`0x1144`. Rendement décroissant :
à traiter au cas par cas quand ils se manifesteront à l'exécution.

### 41. Comprendre les derniers cas : SFA3 / CPS2 / recompilateur PS2 (95,8 %)

**Ce que le code 68K de SFA3 utilise** (décodage de la ROM) : `CMPA` 693, `SUBX`/`ADDX` 558,
arithmétique **décimale** `ABCD/SBCD/NBCD` ~225 (scores, chrono), `MOVE ↔ SR` / `ORI #$2600,SR`
~110 (masque d'interruptions), `MOVE USP`, `TRAP #14/#15`, `RTE`. Le décodage LINÉAIRE du 1er Mo
est pollué par les données (mots `0000` = « ORI ») ; un parcours récursif (`reach.py`) s'arrête vite
car SFA3 appelle ses routines **via des pointeurs en RAM** (`JSR (A0)`).
⟹ **comparaison à armes égales** (`opclass_e2e.py`) : sur les fonctions localisées, compter les
familles dans la ROM et dans NOTRE traduction de la même fonction. Totaux quasi égaux (1 882 / 1 907).
Faux déficits identifiés (`unmatched.py`) : les « opérations de bit » et une partie des « ORI »
manquants sont les **entrées des tables d'aiguillage** (`01xx`/`00xx`) dont les valeurs changent avec
la mise en page. Excédents d'appels/RTS : appels vers les **routines vidées / crochets du portage**
(étape 2).

**Le recompilateur PS2 range des temporaires sur SA pile** quand une fonction manipule trop de
valeurs (`sw x,284(sp)` … `lw y,284(sp)`) : le traducteur fait désormais **suivre les valeurs à
travers la pile** (y compris dans le reconnaisseur de drapeaux exacts). ⟹ `CMPI.B #$10,D1` = `0c01 0010`
reconstitué alors que ses opérandes transitent par la pile.

Ajouts : `CMPI.L` codé en **addition de l'opposé** (`lui/ori −imm ; addu`) ⟹ `0cae 0202 0202 0004`
identique à la ROM ; opérations de bit en mémoire `BSET/BCLR/BCHG #b,d(An)` et `ORI/ANDI/EORI.x
#imm,d(An)` ; `BTST #b,Dn` ; `MOVEA.L Dn,Am`.

**Cases spéciales du banc de registres** (non encore élucidées, à ne pas deviner) : `0x114c` se
comporte comme un **pointeur de pile** (empilements `lw 0x114c ; addiu −4 ; sw ; sw x,0(…)`),
`0x1144` comme un **compteur** (7, 3, 15… décrémenté), `0x1120` reçoit un pointeur (`A5+$400`) juste
avant l'appel d'une fonction du portage (**paramètre**). L'identification par la ROM (`gapprobe.py`)
n'a donné que 9 fonctions alignées : insuffisant.

**Recensement 95,8 %** ; bout en bout 21 identiques, 34 ≥ 90 %, LCS médiane 71 %.

### 42. Adressage absolu, CMPA, EXG (4e bug de correction) : 96,1 %

- **Adressage absolu `(xxx).L`** : base = constante `lui` (et non un registre d'adresse) ⟹
  `MOVE/CLR/TST.x …,$adresse.L` ; en mode cps2, adresse convertie par la carte (octet : XOR 1,
  l'adresse étant exacte). Ex. `lui 0x93 ; sh zero,-13312` = `CLR.W $90CC00.L` (mémoire vidéo).
  Adresse hors carte (variables du portage `0x88xxxx`, moteur PS2 `0x1axxxx`) ⟹ signalée comme
  **crochet** au lieu d'être traduite.
- **`CMPA.W/.L <ea>,An`** (ROM : 693) : soustraction dont l'opérande est un registre d'adresse ; taille
  .W si le résultat est étendu sur 16 bits. `CMPA.W A1,A0` = `b0c9` (présent dans la ROM).
- ⚠️ **Bug de correction : `EXG An,Am`** — `lw x,A6 ; lw y,A1 ; sw y,A6 ; sw x,A1` était traduit en
  `MOVEA.L A1,A6` seul (la 2e écriture, qui passe par « l'ancien A6 », était jetée) ⟹ A1 n'était
  jamais mis à jour. Désormais **`EXG`** (`c34e` = `EXG A1,A6`, présent 3 fois dans la ROM).
- Retenue interne **après une opération en place** (`ADD.L D0,$44(A6)` — 123 fois dans la ROM —
  puis relecture dans RES et `sltu` contre l'opérande sauvegardé dans `0x1158`) : absorbée.

**Recensement 96,1 %.**

### 43. Grande passe d'idiomes : 97,5 % (SFA3), 97,6 % (Upper), 97,2 % (Hyper) + 2 bugs de correction

**Outils** : `missclust.py` (regroupe TOUS les manques par signature, hors code natif),
`natmiss.py` (sépare les manques du code recompilé de ceux du **code natif du portage** :
fonctions C PS2 sans banc de registres 68K ; ~1 100 manques = 20 %, à NE PAS traduire, le fork
FBNeo les remplace par le vrai matériel), `show.py VA` (MIPS + traduction côte à côte).

**Idiomes ajoutés (chacun vérifié dans la ROM)** :
- `CMPI #k,Dn` codé en addition de l'opposé ; retenue calculée par `slt` (octets) ; bloc de
  retenue **toujours** absorbé après une écriture de RES (le recompilateur le produit même
  quand aucun Bcc ne lit C).
- `BTST/BSET/BCLR/BCHG Dn,<ea>` : masque `1 << (Dn & 7)` construit par `sllv` (`nor` pour BCLR).
  ROM : `01e9 026e` = `BSET D0,$26E(A1)` présent.
- `MOVE.W An,d16(Am)` (les 16 bits bas d'une adresse hôte et de l'adresse 68K coïncident).
  ROM : `3b4e a32a 3b4e a32e 3b49 a32c 3b49 a330` ; nous : mêmes opcodes, même ordre,
  déplacement A5 différent (`$8B90…` : la zone de variables A5 est réorganisée par le portage).
- `MOVEA.W Dn,An` (+ conversion hôte absorbée), `MOVEA.L d8(An,Dn.W),Am`.
- `ADDA.W d8(An,Xn),Am` (table de décalages relatifs, `d8f4 0000` ×5 dans la ROM) et
  `ADD/SUB/AND/OR.x d8(An,Xn),Dn` (`d070 1000` ×11).
- Rotations `ROR/ROL.B/.W #k,Dn` (`(x>>k)|(x<<(w-k))`) : `302d 0128 ee58` ×8 dans la ROM, identique.
- Inversion d'octets d'un mot (`(x&$FF)<<8 | x>>8`) : `MOVE.W` + `ROR.W #8` (voir règle ci-dessous).
- Constante 32 bits chargée par un `lui` seul (vitesses 16.16) : `2d7c fffc 0000 0040` ×8, identique.
- Lecture absolue → mémoire `MOVE.L $abs.L,d16(An)` (la ROM a `MOVE.L d16(PC),…` : constantes
  placées juste après la fonction ; à convertir en PC-relatif à l'assemblage, étape 3).

⚠️ **Bug de correction n° 5 : le « masque 24 bits » n'en était pas un.** `dsll32 8 ; dsrl32 8` sur
un Dn était absorbé comme « masquage d'adresse ajouté par le recompilateur ». C'est en fait le
`ANDI.L #$FFFFFF00,Dn` du jeu (27 sites MIPS ↔ 28 dans la ROM : état d'objet `$0200xx00` dont on
isole les 3 octets hauts, `MOVE.L 4(An),D0 ; ANDI.L ; CMPI.L #$02001000,D0`). Désormais émis
(`ANDI.L #$00FFFFFF` sur la valeur octets-inversée, voir règle).

⚠️ **Bug de correction n° 6 : immédiats négatifs tronqués.** `addiu r,zero,-1 ; sw r,…` donnait
`MOVE.L #$0000FFFF` au lieu de `#$FFFFFFFF` (valeur gardée sur 16 bits). Idem `ANDI.L` avec un
masque négatif. Corrigé à la source (valeur signée sur 32 bits, masquée par taille à l'émission).

**Règle du recompilateur sur les champs (éclaire la disposition mémoire)** :
- champs manipulés en ARITHMÉTIQUE (vitesses `$40/$44/$48(A6)`) : rangés en natif, les
  constantes MIPS sont celles de la ROM ;
- champs d'ÉTAT lus octet par octet (`4(A6)` = état/sous-état, `$202(A6)`) : rangés octet par
  octet, le recompilateur INVERSE les constantes à la compilation (`MOVE.W #$000A` → `sh $0A00`,
  `CMPI.L #$02000000` → `addiu -2`). En circuit fermé notre traduction reste cohérente
  (on reproduit les valeurs du MIPS) ; pour FBNeo, les zones lues par le MATÉRIEL devront être
  vérifiées une à une (règle des régions matériel, en attente).

**Cases spéciales élucidées** : `0x1144` = **compteur de boucle interne du recompilateur**. Il
fusionne des `MOVEM.L D0-D6/A1,-(A0)` répétés (effacement de la mémoire vidéo, ROM `$1F7E4` :
`MOVEQ #31,D7 ; LEA $92A000,A0 ; MOVEM.L … ×N`) en une boucle décomptée dans `0x1144`. Ce n'est
pas un registre du jeu. `0x1154` : 50 écritures, 5 lectures (candidat : drapeau X).

**e2e (300 fonctions)** : 28 identiques à 100 % (23 avant), médiane LCS 73 % (71 %).

### 44. Piste Street Fighter III (décompilation PS2) : le recompilateur applique un TYPAGE PAR CHAMP

Source : décompilation *correspondante* (matching) de SF III 3rd Strike PS2, prolongée en portage
natif (projet `crowded-street/3sx`, cloné dans `work/sf3-decomp`). Même éditeur, même époque que
l'Anthology, mais code SH-2 du CPS3 **réécrit en C** (pas une recompilation).

**Convention mémoire Capcom sur PS2 (petit-boutiste), `src/structs.h`** :
```c
typedef struct { s16 l; s16 h; } LoHi16;
typedef union  { s32 sp;  LoHi16 real; } Reg32SpReal;                // vitesses, accélérations (MVXY)
typedef union  { s32 cal; struct { s16 low; s16 pos; } disp; } XY;   // positions (xyz[3])
```
Un 32 bits en virgule fixe 16.16 est rangé en natif ; sa **partie entière est à +2** sur PS2,
à +0 sur l'arcade (gros-boutiste). C'est exactement l'« échange de moitiés relatif au champ »
mesuré sur l'Anthology (§ recette mémoire) : le recompilateur ne suit pas une règle globale,
il applique un **type par champ** (u8 / s16 / s32 / s32-dont-on-lit-la-moitié), comme les
structures C des portages natifs de Capcom. D'où :
- champ **s32** lu aussi en mot (position : `MOVE.W $10(A6),D0` = partie entière) → lecture
  hôte à `d+2` ;
- champ **tableau d'octets** lu d'un coup en long (`routine_no` : `4(A6)` = `02 00 10 00`,
  `CMPI.L #$02001000`) → octets rangés à leur place, la lecture 32 bits petit-boutiste donne
  la valeur inversée ⟹ le recompilateur **inverse la constante** (`addiu -$00100002`), cf. §43 ;
- champ **s16** : natif, même adresse ; constantes identiques à la ROM.

**Même lignée de moteur (CPS2 → CPS3)** : la structure `WORK` de SF3 donne les NOMS des champs
d'objet de SFA3 : `routine_no[]` (état ; incrément de 2 car tables de sauts en mots, cf.
`ADDQ.B #2,5(A6)`), `xyz[3]` (positions), `mvxy` = `a[2]` vitesses puis `d[2]` accélérations.
Vérifié sur SFA3 : `$40(A6)` vitesse X (`#$FFFC0000` = -4,0), `$44` vitesse Y (`#$00090000` = +9,0),
`$48` accélération X (`#$500`), `$4C` accélération Y (ROM `2d7c ffff 7800 004c` = gravité -0,53).

**Méthode de 3SX pour relire l'arcade** (`src/arcade/*`, `src/test/test_runner_compare.c`) :
AUCUNE règle globale ; taille d'élément déclarée par section de données (`section_element_sizes`)
et lecture champ par champ (`be16`, `be32`, `SDL_ReadS16BE`). Leur « statcheck » compare l'état du
portage à des vidages de RAM arcade, par décalages explicites (`PLW_OFFSET`, `WORK_XYZ_OFFSET`…),
l'équivalent de notre validation PINE/PCSX2.

**Conséquence pour nous** : il faut une **carte des types par champ** (au minimum pour les
structures d'objet A6/A4 et les variables A5). Elle se mesure statiquement (tailles d'accès MIPS
par déplacement) et se nomme grâce à SF3.

**Mesure sur le binaire (outils `fieldmap.py`, `fieldtype_rom.py`)** — accès MIPS par déplacement
de la structure d'objet A6, puis relation entre chaque constante longue écrite par le MIPS et la
constante de la ROM au même champ :

| champ A6 | accès MIPS | constantes : MIPS ↔ ROM | type |
|---|---|---|---|
| `$04..$07` | ~5 000 octets, 663 écritures `.L`, 49 lectures `.L` | **35/35 octets inversés** | `u8 routine_no[4]` |
| `$10`+`$12` | 793 `.L` + 1 369 `.W` à **+2** | 7/7 natives | `XY` position X (`pos` à +2) |
| `$14`+`$16`, `$18`+`$1A` | idem | 5/5 natives | positions Y, Z |
| `$40..$4E` | `.L` + `.W` à +2 | 189/194 natives (5 coïncidences) | `mvxy` a[2], d[2] |
| `$60` | `.L` | 1/33 | pointeur (adresses hôte) |

⟹ Le typage par champ est **reconstructible** et vérifiable contre la ROM. Piste pour la suite :
un mode de traduction « typé » où, pour un champ connu, on émet la forme de la ROM
(mot entier d'une position = `d` et non `d+2` ; constante d'un `u8[4]` remise à l'endroit ;
pas de `SWAP`). La mémoire 68K produite serait alors **la vraie disposition CPS2**, sans recette
ni conversion — ce qu'il faut pour FBNeo (matériel et tables de données).

**Le modèle typé, formalisé et mesuré (`typed_rule.py`)** — c'est ce que produirait un compilateur
C petit-boutiste qui range chaque champ selon son type :

| type du champ | accès octet | accès mot | accès long |
|---|---|---|---|
| `u8` | même adresse | – | – |
| `s16` | adresse XOR 1 | même adresse | (s16[2] : moitiés échangées) |
| `s32` | adresse XOR 3 | adresse XOR 2 (partie entière hôte = F+2) | même adresse, valeur native |
| `u8[4]` lu en long | même adresse | – | même adresse, valeur **inversée** |

Le type d'un champ se déduit (1) de la relation des constantes longues avec la ROM
(`const_evidence.json` : natif ⇒ s32, octets inversés ⇒ u8[4], moitiés ⇒ s16[2]), sinon (2) des
tailles d'accès (octets dominants ⇒ u8[4] ; mots à F+2 > 1,5 × mots à F ⇒ s32 ; mot s16 si les
accès mot pèsent ≥ 10 % des accès octet de la paire).

Évaluation sur les 1 163 paires (accès MIPS ↔ accès ROM) mesurées pendant l'étude de la disposition :

| règle | octets | mots | longs | global |
|---|---|---|---|---|
| même adresse (identité) | 92 % | 70 % | 100 % | 86,1 % |
| ancienne « relative au champ » (tout long ⇒ s32) | 56 % | 78 % | 100 % | 64,9 % |
| **modèle typé (accès seuls)** | 95 % | 91 % | 100 % | **94,2 %** |
| **modèle typé + constantes ROM** | 96 % | 92 % | 100 % | **95,1 %** |

L'ancienne règle échouait parce qu'elle prenait `routine_no` (octets écrits en long) pour un s32.
Échecs restants : registres de base qui pointent vers des structures DIFFÉRENTES selon les
fonctions (A4 `$0/$2/$4/$8`, A2 `$12`) et quelques champs ambigus (`$3B` : tantôt octet, tantôt
moitié d'un s16). Il faudra une carte par TYPE D'OBJET (et non par registre) pour les derniers %.

**Mode de traduction TYPÉ (`MEMMODE=type`, bases typées `TYPE_REGS`, défaut `5,6`)** — premier essai :
- déplacements convertis selon le type du champ (`mconv(disp, taille, An)` → `typed_rule.predict_typed`) ;
- constante longue écrite dans un `u8[4]` / `s16[2]` remise à l'endroit (forme ROM) ;
- valeur lue d'un `u8[4]` suivie jusqu'aux registres D (`revd`) : `ANDI.L`/`CMPI.L` avec les
  constantes de la ROM (`#$FFFFFF00`, `#$02000000`) au lieu des constantes inversées du MIPS ;
- paire d'octets lue en mot (idiome d'inversion) : simple `MOVE.W` (la ROM n'a pas de `ROR.W #8`).

Exemple, fonction MIPS `0x6C110` désormais **identique octet pour octet** à la ROM :
`222E 0004 0281 FFFF FF00 0C81 0200 0000 67xx 2D7C 0200 0000 0004 4E75`.

| e2e, 300 fonctions | hôte | typé (A0-A6) | **typé (A5, A6)** |
|---|---|---|---|
| fonctions ≥ 90 % | 38 | 44 | **47** |
| identité pondérée | 24,2 % | 24,2 % | **25,4 %** |
| médiane LCS | 73 % | 75 % | **75 %** |
| fonctions améliorées / dégradées vs hôte | – | 69 / 30 | **63 / 7** |

Typer A0–A4 dégrade : ces registres pointent selon les fonctions vers des structures DIFFÉRENTES
(objet, sprite, liste…) et un même déplacement hôte (ex. `$14.W`) n'a pas le même type partout. Il
faudra typer par **provenance du pointeur** (d'où vient A4 : pool d'objets, tampon de sprites…).

**Pourquoi c'est la bonne cible pour FBNeo** : en mode typé, la mémoire 68K produite est la VRAIE
disposition CPS2 (celle de la ROM) et les registres contiennent les vraies valeurs. La « recette
universelle » (octet XOR 1, `SWAP` des longs) ne rendait juste que les champs `s16` : elle donnait
une mémoire = image PS2 lue en mots (longs à moitiés échangées, octets déplacés), cohérente en
circuit fermé seulement. **La recette reste valable comme filet de sécurité** là où le type est
inconnu, mais l'objectif devient le typage complet.

**Suite du chantier « types »** : (1) carte des variables A5 par adresse (pas d'ambiguïté) ;
(2) provenance des pointeurs A0–A4 ; (3) tables de données typées par élément, comme 3SX
(`section_element_sizes`), pour produire des données gros-boutistes exactes.

### 45. Graphismes : l'Anthology contient la ROM graphique CPS2 de SFA3 EN ENTIER (réponse au constat MAX §5)

Le document MAX (§5, « Constat transmis à HSFA ») mesurait 12 % de recoupement entre les tuiles
de l'Anthology et la CPS2. **Faux négatif**, deux causes :
1. l'Anthology stocke les **valeurs BRUTES** de la ROM CPS2 ; FBNeo affiche `15 − brute`
   (`Separate(255 − x)`). La comparaison « même forme » forçait `0 → 0`, or le transparent vaut
   15 d'un côté et 0 de l'autre ⟹ aucune tuile ne pouvait correspondre ;
2. seuls `e255`–`e257` étaient testés, et `gfx.py` lisait les tuiles non compressées sur 0x20
   octets (8×8) au lieu de 0x80 (16×16).

**Format des conteneurs (`tools/untranspile/anthgfx.py`)** : 3 enregistrements
`(premier_index, nombre, position_table, 0)`, un par taille (8×8, 16×16, 32×32). Table : 0 = tuile
vide ; bit 31 = compressée (lz148778) ; sinon non compressée. 4 bpp linéaires, quartet bas à gauche.
Correspondance CPS2 : 16×16 `m` → tuile `m` ; 32×32 `m` → 4 tuiles 16×16 à partir de `4m`
(lignes de 32 px = 2 lignes de 16) ; 8×8 `m` → 8 lignes à partir de la ligne `8m`, **dupliquée dans
les deux moitiés** de la ligne de 16 px. Index relatifs au quart de ROM du conteneur.

**Carte SFA3 (`ro3`)**, vérifiée tuile à tuile sur la ROM `sz3.13m`–`20m` :

| quart CPS2 (65 536 tuiles) | source | couverture exacte |
|---|---|---|
| 0 | banques de sprites des persos `e258`–`e285` (DATA, chargées à la demande) | 64 294 (1 201 vides) |
| 1 | `e255` (8×8 : 0–0x2C00, 32×32 : 0x2C00–0x6C00, 16×16 : 0x6C00–0xE000) + banques | 65 092 (2 076 vides) |
| 2 | `e257` | **65 536 / 65 536** |
| 3 | `e286` | **65 536 / 65 536** |

**68 tuiles non vides sur 262 144 absentes, 0 tuile mal placée.** `e288` (8 Mo) = échantillons
QSound (octets signés), `e313` et `e256` = autres formats (à voir), `e314`–`e345` = conteneurs
`MOMO` (image + palette par perso : portraits).

**Banques de persos** : chaque banque est un SOUS-ENSEMBLE des tuiles CPS2 dans l'ordre
d'utilisation (croissant par morceaux), numéroté à partir de 0. Le portage doit donc tenir une table
« code CPS2 → tuile de banque » : **à trouver, c'est elle qui placera les tuiles NOUVELLES d'Upper
et d'Hyper**.

**Outil `tools/untranspile/cps2rom.py`** : ROM graphique CPS2 ⇄ tuiles en valeurs brutes, dérivé du
chargement FBNeo puis inversé. Décodage identique à FBNeo (2 000/2 000), **aller-retour exact sur
les 32 Mo**. Permet d'écrire les fichiers `.13m`–`.20m` d'une ROM graphique.

**Banques de sprites : comment le portage désigne une tuile (vidage `ee_std`, code natif PS2)**

Le moteur de sprites natif (`0x1D2DC0`) lit la table des objets CPS2 (copie en `0x70002000`,
8 octets par objet, fin `$8000`). Pour chaque tuile il appelle **`0x1D3510(emplacement, code)`** :
```
conteneur = ctx->banque[emplacement]        // ctx = *(0x1DC078) = 0x1DC2B0 ; +48 + 4×emplacement
pour chaque enregistrement (premier, nombre, table) du conteneur :
    si premier ≤ code < premier + nombre : renvoyer table[code − premier]
```
L'**emplacement = bits 13-15 du mot X de l'objet** (`X >> 13`, 7 = objet ignoré). Emplacements
chargés dans le vidage :

| emplacement | conteneur | rôle probable |
|---|---|---|
| 0 | 0x6430 tuiles (`e254`) | sprites communs |
| 2 | 0x1750 tuiles (`e258`) | perso joueur 1 |
| 3 | 0x2480 tuiles (`e264`) | perso joueur 2 |
| 4 | 0x510 tuiles | autre banque |
| 5 | 32×32, 0x1000 (`e312`) | décor |

⟹ **Le portage a modifié le jeu** : le 68K recompilé écrit un **numéro local à la banque** et un
**numéro d'emplacement** (bits hauts de X, qui portent la priorité sur la vraie CPS2), et non le
code CPS2 global. Les frames d'animation de la ROM (triplets position/code/attributs, 482 suites
repérées) sont absentes telles quelles du programme de l'Anthology, y compris avec les numéros
locaux : leur format a aussi été converti (à retrouver).

**Conséquence pour FBNeo** : pour les tuiles de banque, il faut (1) choisir un emplacement global
dans la ROM graphique pour chaque banque (notre choix, par ex. à la suite des quarts indexés) et
(2) retraduire, dans la routine 68K qui construit la liste d'objets, `(emplacement, local)` →
`base[banque chargée] + local`, en rendant aux bits hauts de X leur rôle de priorité. **Prochaine
étape graphique** : localiser cette routine (traducteur + e2e contre la routine d'origine de SFA3).

**Upper (`ro5`)** : même architecture. 28 banques de persos identiques ou presque à SFA3
(`e360` = `e263`, `e361` = `e264`…), **4 banques quasi entièrement nouvelles `e383`–`e386`**
(les nouveaux persos : 65 à 123 tuiles connues sur 6 000 à 8 000), 2 à moitié nouvelles
(`e381`, `e382`), `e354` (GFX, ~30 000 tuiles nouvelles), `e387` = quart 3 d'Upper (moitié identique
à SFA3, moitié modifiée). La numérotation d'Upper diffère de celle de SFA3 : c'est bien la ROM
graphique d'Upper qu'il faut construire, pas celle de SFA3.

### 46. Les « versions » d'Hyper : un octet de drapeaux testé dans ~1 300 sites (réponse à MAX §10)

L'octet `+$67` soupçonné n'est PAS propre à Hyper : SFA3 et Upper l'utilisent autant (A6 : 38/45/38
accès). Comparaison des déplacements de la structure joueur entre `ro3`, `ro5` et `ro9` :

| champ | SFA3 | Upper | Hyper |
|---|---|---|---|
| `$D3(A6)` | 3 | – | **1 282** |
| `$D3(A4)` | 0 | 0 | 112 |
| `$116/$117(A6)` | 0 | 0 | 127 / 28 |
| `$D3` dans la ROM SFA3 d'origine | **absent** | | |

- `$117(A6)` = variante choisie ; recopiée dans `$D3(A6)` à l'initialisation du joueur
  (`MOVE.B $117(A6),$D3(A6)`, 2 sites), remise à 0 ailleurs, `BSET #3` à un endroit ;
- **transmise aux objets enfants** : `MOVE.B $D3(A6),$D3(A4)` (projectiles, effets) ;
- lue comme **champ de bits** : `BTST #n,$D3(A6)` + branchement, 8 bits utilisés
  (bit 4 : 397, bit 0 : 303, bit 1 : 180, bit 3 : 168, bit 7 : 121, bit 2 : 49, bit 5 : 37, bit 6 : 16).

⟹ Les versions d'Hyper sont **pilotées par du CODE réparti dans tout le moteur** (branchements
sur des drapeaux, hérités par les projectiles), pas par de simples tables de données. Réponse à
la question ouverte de l'étude MAX (§10) : **l'architecture A (base CPS2) reste la bonne** ; porter
Hyper dans le moteur C de MAX obligerait à reproduire ~1 300 embranchements. Pour greffer des
éléments d'Hyper dans Upper, il faudra emporter `$D3/$116/$117` et leurs points de test.
Signification exacte de chaque bit : à établir en jeu (PINE), en choisissant chaque version.

*Carte d'adresses (`translate.py`, `ADDRMAP`) : ajout de la **mémoire d'objets** — hôte base RAM +
`0x10000` → `$700000` (page 1), + `0x12000` → `$708000` (page 2). Lue par le moteur de sprites natif
via `*(ctx+208)` ; recopiée vers `0x70002000` selon le bit de page (`ctx+232`). Le code
d'intégration du portage y écrit directement (`MOVE.L #$80008000` = fin de liste, en `0x910000` et
`0x912000`).*

### 47. ⚠️ Correction : les « routines VIDÉES » sont presque toutes des RTS partagés

§35 annonçait 113 routines vidées par le portage dans SFA3 (142 Upper, 66 Hyper), « à restaurer ».
Classement de chaque appel (`emptied.py`) :

| module | fonctions `jr ra` | toujours appelées en FIN de parcours | au milieu | mixtes |
|---|---|---|---|---|
| SFA3 | 114 | **107** | 4 | 3 |
| Upper | 143 | **125** | 11 | 7 |
| Hyper | 67 | **61** | 2 | 4 |

- « En fin de parcours » (appel aussitôt suivi du retour) = **`Bcc`/`BRA` vers un `RTS` partagé** dans
  la ROM : le recompilateur découpe ce `RTS` en fonction et y fait un appel terminal. Vérifié par
  alignement sur la ROM : les 4 routines localisées pointent sur un simple `4E75` (ex. mips `0xB3230`
  → ROM `$7CB70`, 4 sites sur 4, tous des `BEQ/BCS/BNE` vers ce `RTS`).
- Parmi les 7 cas restants de SFA3 : du code d'intégration du portage (zone `0x39xxxx`) et au
  moins une **routine vide d'origine** (mips `0x20E420` → ROM `$AAA6` = `RTS` déjà dans la ROM).

⟹ **Le portage n'a pratiquement PAS vidé de routines du jeu.** La couche matériel à reconstruire
pour FBNeo se limite aux accès que le portage a redirigés (mémoire d'objets, entrées, son, vidéo :
§35, §45), pas à des routines disparues. Traduction : un appel terminal vers une fonction
`jr ra` = un `RTS` (à simplifier dans le traducteur).

### 48. Retouches matérielles du portage : exemple de la mémoire d'objets, et conception FBNeo des sprites

**Exemple (fin de liste d'objets)** :
- ROM `$1B146` : `CMPI.L #$1C62F5A8,D0 ; MOVEA.L #$708020,A0 ; MOVE.L #$80008000,(A0)+ ×2 ; TST.B $95(A5) ;
  BNE ; EORI.B #1,$94(A5) ; ST $95(A5) ; MOVEQ #1,D0 ; JSR $1370`
- Anthology (mips `0x89494`) : `LEA $910000,A0` (adresse HÔTE) ; `TST.B $9621A0.L` (drapeau de page du
  portage) ; `BEQ` ; `LEA $912000,A0` ; `MOVE.L #$80008000,(A0)+ ×2 ; TST.B $95(A5) ; …`
⟹ le portage a remplacé l'accès matériel (page d'objets choisie par le matériel CPS2) par un choix
explicite d'adresse hôte. Ces retouches se repèrent automatiquement : constantes d'adresse dans les
zones de la carte (`0x91xxxx`, `0x96xxxx` = variables du portage, `0x88xxxx` = crochets).
*(À faire : le traducteur doit rendre `LEA $910000` → `MOVEA.L #$708020` ; il ne traite pas encore
l'écriture dans un registre A d'une constante chargée par un `lui` seul.)*

**Conception proposée pour les sprites dans le fork FBNeo** (à valider) : plutôt que de réécrire
toutes les frames converties par le portage (codes locaux de banque), **garder le schéma du
portage dans le fork** :
1. ROM graphique = quarts indexés (codes globaux) + **banques de persos rangées à la suite**, chacune à
   une base connue ;
2. les appels natifs du portage qui chargent une banque dans un emplacement (appels « hors carte »)
   deviennent des écritures vers un **registre propre au fork** (emplacement → base de banque) ;
3. le rendu des objets du fork lit `X >> 13` comme emplacement et ajoute la base : code global =
   `base[emplacement] + code local`.
Avantages : aucune donnée d'animation à retrouver ni à reconvertir ; valable pour les persos
nouveaux d'Upper et d'Hyper (banques `e383`–`e386`) sans table de correspondance. Inconvénient : ce
n'est plus une CPS2 standard (fork obligatoire, ce qui est déjà le cas).

*Traducteur : registre A chargé d'une constante `lui` seule → `LEA abs.L` ; en mode cps2, `$910000` →
`$700000`, `$912000` → `$708000` (la ROM écrit toujours en `$708020` et laisse le matériel choisir la
page : règle des pages à fixer avec le fork). Appel terminal vers une fonction `jr ra` → `RTS` (§47).
Recensement SFA3 : 97,6 % (141 412 / 144 912).*

### 49. Upper NE TIENT PAS dans une ROM graphique CPS2 standard ⟹ fork obligatoire

Tuiles uniques de tous les conteneurs (équivalents 16×16 : 32×32 = 4, 8×8 = ½) :

| module | 8×8 | 16×16 | 32×32 | total | limite CPS2 (code 18 bits = 262 144) |
|---|---|---|---|---|---|
| SFA3 | 22 377 | 227 063 | 4 092 | 254 620 | tient |
| Upper | 1 388* | 266 027 | 4 533 | **≈ 284 850** | **dépasse d'au moins 22 700 (~9 %)** |

\* les 8×8 d'Upper sont en partie ailleurs (`e353`, autre format) : le dépassement réel est plus grand.
58 000 tuiles d'Upper sont absentes de SFA3. ⟹ Une version « CPS2 standard » d'Upper (jouable sans
modification dans FBNeo/MAME/Fightcade) est **impossible sans retirer du contenu**. Le fork FBNeo
est obligatoire ; le schéma de banques du §48 ne coûte donc rien en compatibilité, et rien en
performance (une lecture de table et une addition par objet, ~900 objets au plus par image ; le
« chargement » d'une banque = écrire une base, toute la ROM graphique étant en mémoire).

### 50. Défrichage d'Hyper : l'encodage des versions, décodé statiquement

Fonction ajoutée par Hyper (mips `0x321BA0`, écrite avec la case temporaire `0x1144` — code ajouté,
non traduit pour l'instant) :
```
t = $102(A6)                     identifiant étendu « perso + version »
$116(A6) = table_A[t]            perso de base      (données hôte $5C5300)
$117(A6) = table_B[t]            drapeaux de version (données hôte $5C2490)
$D3(A6)  = $117(A6)              copie de travail, héritée par les projectiles (§46)
```
Les tables sont des `u8` rangés octet par octet (conforme au modèle typé §44). Décodage :

| `$102` | `$117` | persos (`$116`) | version |
|---|---|---|---|
| `$00`–`$24` | `$10` (bit 4) | 37 : roster SFA3/Upper + variantes (`$12`→`$04` Chun-Li, `$14`→`$06`, `$25`→`$15`) | **ZERO 3** |
| `$30`–`$3C` | `$01` (bit 0) | 13 (`$00`–`$0C`) : roster de SFA1 (10 + 3 cachés) | **ZERO** |
| `$40`–`$5F` | `$22` (bits 1, 5) | 21 | **ZERO 2** |
| `$60`–`$7F` | `$06` (bits 1, 2) | 21 | **ZERO 2 ALPHA** |

- **bit 3** ajouté pour exactement 7 persos : `$00` Ryu, `$01` Ken, `$04` Chun-Li, `$0A` M.Bison,
  `$0B` Sagat, `$0F` Dhalsim, `$10` Zangief = les versions **« EX » façon SF2** d'Alpha 2 Gold.
- bit 1 = famille ZERO 2 (commun aux deux) ; bit 5 = ZERO 2 d'origine ; bit 2 = ZERO 2 ALPHA.
- **bits 6 et 7** : absents de ces blocs mais testés (16 et 121 fois) ; `BSET #3,$D3(A6)` en un
  point ⟹ autres réglages (mode spécial ?) : **à confirmer en jeu** (PINE : lire `$102/$116/$117/$D3`
  pour chaque choix de version).

Nombre de tests par bit (§46) : bit 4 (ZERO 3) 397, bit 0 (ZERO) 303, bit 1 (ZERO 2) 180, bit 3 (EX)
168, bit 7 121, bit 2 (ALPHA) 49, bit 5 37, bit 6 16. ⟹ Pour greffer une version d'Hyper dans Upper,
on sait maintenant **quel bit porte quelle version** et donc quels sites de test emporter.

### 51. Table « perso → banque de sprites » ; Hyper puise dans SFA1, SFA2 et Upper

Chaque module a, dans ses données, une **table u16 indexée par identifiant de perso** donnant le
numéro d'entrée `X_DATA.BIN` de la banque de sprites (suivie d'une table des portraits `MOMO`) :

| module | position (octet du fichier) | contenu |
|---|---|---|
| SFA3 `ro3` | `0x3AC0B0` (hôte `$59C0B0`) | ids `$00`–`$1F` → `e258`–`e285` ; variantes → banque du perso de base (`$12`→`e262` Chun-Li, `$14`→`e264` Sodom, `$17` Evil Ryu→`e258` Ryu) |
| Upper `ro5` | `0x438320` | idem → `e355`–`e382`, puis **`$20` Guile → `e383`, `$21` Fei-Long → `e384`, `$22` Dee Jay → `e385`, `$23` T.Hawk → `e386`**, `$24` Shin Akuma → `e357` (Akuma), `$25` → `e373` (Balrog) ; `$1E/$1F` Juli/Juni → `e381/e382` (les banques « à moitié nouvelles » : devenus jouables) |
| Hyper `ro9` | `0x3BF1B0` | indexée par `$102` (perso + version, §50) |

**Hyper n'a AUCUNE banque graphique propre** (son groupe `e544`–`e552` n'en contient pas) :

| version (ids `$102`) | banques chargées |
|---|---|
| ZERO 3 (`$00`–`$2F`) | **Upper** `e355`–`e386` |
| ZERO (`$30`–`$3F`) | **SFA1** `e208`–`e220` (13 persos) |
| ZERO 2 et ZERO 2 ALPHA (`$40`–`$7F`) | **SFA2** `e229`–`e248` (banques communes) |

⟹ La ROM graphique d'Hyper pour le fork = banques de SFA1 + SFA2 + Upper (+ décors et communs) :
très au-delà des 32 Mo de la CPS2 ; le schéma de banques (§48) s'impose et convient tel quel
(l'identifiant `$102` → banque se relit dans la table ci-dessus).
Banques des persos de SFA3 : `$00` Ryu e258, `$01` Ken e259, `$02` Akuma e260, `$03` Charlie e261,
`$04` Chun-Li e262, `$05` Adon e263, `$06` Sodom e264, `$07` Guy e265, `$08` Birdie e266, `$09` Rose e267,
`$0A` M.Bison e268, `$0B` Sagat e269, `$0C` Dan e270, `$0D` Sakura e271, `$0E` Rolento e272, `$0F` Dhalsim
e273, `$10` Zangief e274, `$11` Gen e275, `$15` Balrog e276, `$16` Cammy e277, `$18` E.Honda e278, `$19`
Blanka e279, `$1A` R.Mika e280, `$1B` Cody e281, `$1C` Vega e282, `$1D` Karin e283, `$1E` Juli e284, `$1F`
Juni e285 (noms : roster de l'étude MAX, `tools/max/pl_mapping.json`).

### 52. Hyper a été produit par une version PLUS RÉCENTE du recompilateur

Même test d'état que SFA3 (`CMPI.L #2,D1 ; BEQ`), mais dans Hyper le code MIPS diffère :
- opérandes dans des **registres alloués** (`s0`–`s4`) au lieu d'aller-retours par les cases ;
- retenue C et débordement V calculés par **formules complètes** (`nor/and/or`, puis masque du bit
  de signe `lui $8000` / `andi $80/$8000`) ;
- `sw r,RES` puis **négation de RES si V** (RES porte N⊕V : comparaisons signées directes).

Reconnu par `full_flags_block()` : `subu` (destination Dn **ou mémoire**, source immédiate, constante
32 bits, Dn ou mémoire) → `CMP`/`CMPI`, 3 branchements internes absorbés, comparaison marquée
« signée exacte ». Ajout : `ori rX,zero,imm` = immédiat non signé. Exemples : `CMPI.W #$D000,D1`,
`CMPI.L #$40202,4(A6)` (mode typé : `#$02020400`, l'état de `routine_no` tel que Capcom l'écrit).

Recensement : **SFA3 97,6 % · Upper 97,7 % · Hyper 97,3 %**.

### 53. Les cases spéciales élucidées : deux registres SUPPLÉMENTAIRES « A8 » et « D8 »

Banc de registres du recompilateur (scratchpad `0x7000_1100`) :

| case | rôle | preuve |
|---|---|---|
| `0x1100`–`0x111C` | A0–A7 | |
| **`0x1120`** | **A8** : registre d'adresse supplémentaire | reçoit un `MOVEA.W` suivi de la conversion d'adresse hôte (`bgez` + base RAM `$B80000`, Hyper `0x2F6CC`) |
| `0x1124`–`0x1140` | D0–D7 | |
| **`0x1144`** | **D8** : registre de données supplémentaire | compteur des boucles `MOVEM` fusionnées (SFA3), temporaire du code ajouté d'Hyper (`0x321BA0`) |
| `0x114C` | autre temporaire (rare) | |
| `0x1150` | RES (Z/N) · `0x1154` : X ? · `0x1158` : C | |

Fonctions qui les utilisent (et, entre parenthèses, celles où AUCUN registre 68K du même type n'est
libre dans la fonction) : SFA3 D8 85 (10), A8 39 (3) · Upper D8 98 (10), A8 54 (3) · Hyper D8 111 (8),
A8 84 (4), `0x114C` 18 (3).

**Conception de la traduction** (à réaliser avec l'assemblage complet) : le 68000 n'a pas ces
registres. Dans chaque fonction, attribuer à A8/D8 un registre 68K du même type non utilisé par la
fonction, **sauvegardé/restauré sur la pile** autour de sa durée de vie (le code Capcom ne préserve pas
les registres par convention : un registre « libre » ici peut être vivant chez l'appelant). Pour les
compteurs de boucle, une variable en RAM suffit (`SUBQ.W #1,var ; BCC boucle` ≡ `DBRA`). Les ~15
fonctions sans registre libre : sauvegarde d'un registre non utilisé dans la portée concernée.

### 54. A8/D8 traduits par « registre prêté » : SFA3 97,8 % · Upper 97,9 % · Hyper 97,6 %

`extra_regs.py plan` découpe chaque usage de A8 (`0x1120`) / D8 (`0x1144`) en **durées de vie** (une
écriture qui ne dérive pas d'une lecture récente de la même case en ouvre une nouvelle), étend la
zone aux retours de boucle et aux sorties proches (le test d'un `DBRA` porte sur la valeur gardée
dans un registre MIPS, après le dernier accès), puis n'accepte que les zones SÛRES :
- aucun appel (`jal`/`jalr`) ni `jr` à l'intérieur ;
- entrée et sortie uniques (aucun branchement extérieur vers l'intérieur hors du début, aucun
  intérieur vers l'extérieur hors de l'instruction suivante, aucun extérieur vers celle-ci) ;
- un registre 68K du même type inutilisé dans toute la fonction (A5 jamais prêté).
Traduction : `MOVE.L Rk,-(SP)` au début, accès à la case = `Rk`, `MOVE.L (SP)+,Rk` sur la première
instruction utile après la zone (cible des sorties). Exemple SFA3 `0x29414` : `MOVE.L D6,-(SP) ;
MOVEQ #31,D6 ; … ; DBRA D6 ; MOVE.L (SP)+,D6`.

| module | zones traduites | refus : pas de registre libre | appel dedans | entrées/sorties multiples |
|---|---|---|---|---|
| SFA3 | 147 | 19 | 7 | 21 |
| Upper | 177 | 19 | 14 | 29 |
| Hyper | 296 | 25 | 12 | 38 |

Les refus restent non traduits (et signalés par le recensement) : aucune traduction risquée.
Désactivable par `EXTRA_REGS=0`.

### 55. Programme ENTIER assemblé ; la couche matérielle du fork = ~80 sites d'appel

**Assemblage complet (`link.py`)** : tout le code recompilé d'un module traduit et assemblé comme une
seule unité (appels entre fonctions = nos propres adresses, relaxation BSR/JSR) :

| module | éléments | code 68K produit | temps | non résolus | cibles externes |
|---|---|---|---|---|---|
| SFA3 | 122 772 | **0,50 Mo** | 10 s | 465 | 71 fonctions du moteur PS2 (681 appels) |
| Upper | 135 116 | 0,55 Mo | 12 s | 488 | 71 (682) |
| Hyper | 122 516 | 0,50 Mo | 14 s | 451 | 67 (610) |

Correctif d'`assemble.py` : une cible INTERNE trop lointaine pour un `BSR` (±32 Ko) passait en
`JSR` absolu en demandant l'adresse à la fonction « externe » ⟹ non résolue. Elle prend maintenant
notre propre adresse (non résolus SFA3 : 10 947 → 465). Images : `work/cps2/roN_traduit.bin`.

**Correctif de `natmiss.py`** (détection du code natif) : les **relais** (petites fonctions
`JSR X ; JMP Y` ou `jalr` vers une constante du module) et les fonctions vides (`RTS` partagés) étaient
comptés comme du code C. Fonctions natives SFA3 : 262 → **43**.

**Points de raccordement du fork (`hooks_fork.py`)** : appels du jeu recompilé vers du code natif —
**SFA3 : 83 sites vers 48 cibles** (33 dans le moteur PS2, 15 natives du module), Upper 71 sites / 38,
Hyper 66 / 42. Nature (d'après le code 68K appelant et les arguments) :
- initialisation et système : `LEA $908000,A5` puis moteur `0x104720`/`0x10D870` ; attente d'image
  (`SUBQ.W #1,$6(A5) ; BNE` → natif `0x583B20`) ;
- copie / effacement mémoire : moteur `0x118A60` (taille `$3000`), `0x118C18` (taille `$30`) ;
- son et entrées : moteur `0x14A980`, `0x14B3A0`–`0x14B630`, `0x155xxx`, `0x1CAxxx`–`0x1CDxxx`
  (tests `BTST #n,$C018/$C019(A5)` = état des manettes juste avant) ;
- variables du portage : `$88xxxx` (crochets), `$96xxxx` (drapeaux, dont la page d'objets `$9621A0`).
Liste complète : `hooks_fork_ro3.json` (cible → sites). **C'est toute la surface de contact entre le
jeu traduit et la plateforme** : le reste du programme est du 68K autonome.

**Données** : la section de données du module fait 3,1 Mo (SFA3 : hôte `$583C40`–`$88C700`) ; code +
données dépassent les 4 Mo de ROM programme CPS2 ⟹ le fork projettera de la ROM supplémentaire dans
une zone libre de l'espace 68K (ex. `$A00000`–`$FEFFFF`, ~6 Mo).

### 56. Images programme complètes (code + données + tables) — SFA3 tient dans 4 Mo

`build_rom.py` (mode mémoire cps2) : vecteurs à `$0`, code traduit à `$1000`, **données du module**
juste après (mots remis en gros-boutiste, cohérent avec la recette cps2), variables du portage
projetées dans une **RAM propre au fork** (`PORT_RAM = $F00000` : `$88xxxx` sous la RAM et `$96xxxx`
après la vidéo). Bornes lues dans l'en-tête de CHAQUE module (`set_module_bounds`).

| module | code (avec tables) | données | fin | 4 Mo CPS2 |
|---|---|---|---|---|
| SFA3 | 0,58 Mo | 3,17 Mo | `$39EAC0` | **tient** |
| Upper | 0,63 Mo | 3,76 Mo | `$4384C0` | dépasse de 0,2 Mo |
| Hyper | 0,57 Mo | 6,00 Mo | `$64B0C0` | ROM étendue nécessaire |

Accès absolus restés hors carte : ~15 par module (variables du moteur PS2). Images :
`work/cps2/roN_programme.bin`.

**Tables de données relatives au PC** (`MOVE.x T(PC,Dn.W),…`) : 1 389 références vers 1 352 tables
dans SFA3 (≈ une table par routine, comme la ROM). Elles restaient avec un déplacement nul et leur
contenu dans les données, hors de portée. Désormais **hébergées** : comme Capcom, après la
prochaine rupture (`JMP`/`RTS`/`BRA`) si le déplacement 8 bits porte, sinon juste après
l'instruction, sautées par un `BRA`. Contenu borné par la table suivante référencée, converti
(octets tels quels, mots/longs en mots gros-boutistes). Vérifié : la première table
(`00 00 00 04 01 01 01 04 …`) existe telle quelle dans la ROM, juste après un `JMP` — même
disposition. Correctif au passage : `data_refs`/`read_jump_table` utilisaient la fin de code de
SFA3 pour tous les modules.

### 57. Points d'entrée et registres matériels : le portage « mirroité » à l'envers

**Chiffrement CPS2 et vues de la ROM** : la ROM programme est chiffrée pour les lectures dans
l'espace « programme » seulement, sur `$000000`–`$0BFFFF` environ (au-delà, vue brute = vue
déchiffrée). `sfa3_prog.bin` est la vue déchiffrée (instructions ET lectures relatives au PC — d'où
les tables de Capcom placées derrière le code, chiffrées avec lui). Les lectures de données
ordinaires (vecteurs d'exception…) voient les octets BRUTS. Vecteurs d'origine : reset SP `$FF8000`,
PC **`$91E`** (vue déchiffrée) ; **IRQ2 (balayage vertical) `$1198`**, **IRQ4 `$14E`** (vue brute).
Le fork tournera sans chiffrement.

**Rappels du moteur vers le module** (contexte `ctx` = `$1DC2B0`) : `ctx+4` → jeu `0x926B0`,
`ctx+0x10` → jeu `0x2EF30`, `ctx+8/0xC/0x14` → natives, `ctx+0x28/0x2C` → `0x380F40/0x380E70`.
**`0x926B0` = la routine de reset `$91E` portée** : mêmes écritures, mais vers des variables du
portage au lieu des registres CPS2 (les tests mémoire `LEA 6(PC),A4 ; BRA` sont remplacés par un appel).

**Registres CPS2 ↔ variables du portage** (alignement des suites (valeur, adresse) des deux
routines, 22 écritures appariées) :

| CPS2 | portage | | CPS2 | portage |
|---|---|---|---|---|
| `$400002`–`$40000A` | `$962184`–`$96218C` | | `$80410C` / `$80410E` | `$962118` / `$96211A` |
| `$804040` | `$962198` | | `$804122` | `$96212E` (CPS-A : +`$0C`) |
| `$8040A0` | `$96219A` | | `$804166` / `$804170` | `$962146` / `$962150` (CPS-B : −`$20`) |
| **`$8040E0`** (bascule de page des objets) | **`$9621A0`** | | | |

Table `HWREG` du traducteur (modes cps2/typé) : ces accès sont **rendus aux vrais registres**.
Ex. mode cps2, `0x926B0` : `CLR.W $8040A0 ; MOVE.W #$807D,$400002 ; MOVE.W #$2461,$400004 ; …` —
comme la ROM. Les autres variables `$9621xx` (52 adresses dans SFA3) se relieront de la même
façon en alignant d'autres routines matérielles (interruptions, défilement).

### 58. Le portage « dé-porté » : registres CPS2, QSound, balayage vertical

**Carte complète des variables matérielles du portage** (décalages relatifs à la base RAM, IDENTIQUES
dans SFA3, Upper et Hyper — 41 des ~52 variables de la zone reliées) :

| portage (base RAM +) | CPS2 | rôle |
|---|---|---|
| `$60000`–`$61FFF` | **`$618000`–`$619FFF`** | mémoire partagée QSound (commandes `$618001`…`$61801F`, état `$619FFB`–`$619FFF`) ; confirmé par alignement `$960021` ↔ `$618021` |
| `$62100`+4k (k = 0…5), **longs** | `$804100`+2k, **mots** | bases des plans CPS-A (objets, 3 plans, défilement de lignes, palette) : ÉLARGIES par le portage |
| `$62118`–`$6212F` | `$80410C`–`$804123` (+`$0C`) | CPS-A : défilements X/Y, contrôle vidéo |
| `$62146`, `$62150` | `$804166`, `$804170` (−`$20`) | CPS-B : couches, palette |
| `$62184`–`$6218C` | `$400002`–`$40000A` | sorties |
| `$62198`, `$6219A`, `$621A0` | `$804040`, `$8040A0`, `$8040E0` | dont la bascule de page des objets |
| `$62190`–`$6219E` | *entrées (à confirmer)* | octets lus/écrits (valeurs par défaut `$FF`) |

**Registres élargis** : ROM `MOVE.W $40(A5),$804102` (valeur = adresse >> 8, ex. `#$9000` pour
`$900000`) ↔ portage `MOVE.L $BF44(A5),$962104` (adresse hôte 32 bits, variables du jeu élargies
aussi : `MOVE.L #$920000,$BF30(A5)`). Traduction (modes cps2/typé) :
`MOVE.L D0,-(SP) ; MOVE.L src,D0 [; SWAP] ; LSR.L #8,D0 ; MOVE.W D0,$8041xx ; MOVEM.L (SP)+,D0`
(`MOVEM` ne touche pas aux drapeaux : ceux du `MOVE.W`, comme l'original).

**Résultat sur le gestionnaire de balayage vertical porté** (IRQ2, ROM `$1198`) traduit en mode cps2 :
`MOVE.B $95(A5),$8040E1` (bascule de page, `13ED …`) ; **`LEA $FF8000,A5` = `4BF9 00FF 8000`,
identique à la ROM** ; puis `$804102`, `$804104`, `$804106`, `$804108` dans l'ordre de la ROM.

### 59. PREMIÈRE EXÉCUTION RÉELLE : le programme traduit tourne dans MAME ; le noyau de tâches

**Banc d'essai (`mame_test.py`, MAME 0.285 installé)** : l'image SFA3 traduite (mode cps2) remplace le
programme du jeu Phoenix non chiffré `sfa3ud` (graphismes et son d'origine ; `phoenix.key` = 20 × `$FF`,
reconstituée par son CRC). Témoin (programme Phoenix d'origine) : logo CAPCOM à l'image 900.
Outils : scripts Lua (`trace.lua` : PC/SR/SP toutes les 60 images, capture ; `dbgtrace*.lua` : trace
instruction par instruction via le débogueur, `-debug -debugger none`) ; `carte_image.txt` (adresse
68K → va MIPS → mnémonique) pour lire les traces.

**Ce qui marche** : amorçage 68K reproduisant la boucle native du portage (moteur `0x1CB764` : reset
`ctx+4` une fois, puis `ctx+16` à chaque image) ; la routine de reset TRADUITE s'exécute (effacement de
la RAM, de la vidéo, des objets, registres CPS2) ; **1 800 images sans plantage**, la tâche d'image
traduite appelée à chaque interruption.

**Trois leçons, corrigées ou documentées** :
1. Le reset efface TOUTE la RAM de travail. La ROM appelait l'effacement par `LEA 6(PC),A4 ; BRA` (retour
   dans A4) justement pour survivre à la perte de la pile ; le portage en a fait un appel classique (sa
   pile de retour est celle du MIPS). ⟹ **la pile 68K du jeu traduit doit vivre HORS de la RAM du jeu**
   (essai : `$664000` ; fork : RAM propre).
2. Le reset repositionne A7 : dans le portage la case A7 est morte (pile = pile MIPS). Traduite, elle
   déplaçait notre vraie pile ⟹ les écritures dans A7 (case `0x111C`, 3 accès) sont absorbées.
3. **Le noyau multitâche de Capcom a été remplacé par des FILS D'EXÉCUTION PS2.** La tâche d'image fait
   `SleepThread` (`0x103500` = `syscall $32`) / `WakeupThread` (`0x103510` = `syscall $33`) ; la création
   de tâche du jeu (mips `0x2F730`) remplit un `ThreadParam` (entrée = A0, pile `$2000`, priorité) et
   appelle `CreateThread` (`0x1033E0`, `syscall $20`). SFA3 d'origine a son propre noyau 68K (tâches à
   piles séparées, commutation par échange de SP). ⟹ **Pour la cible CPS2, remettre le noyau de tâches
   d'origine** (création, commutation, attente d'image) à la place de ces appels système. C'est le
   prochain verrou pour voir le jeu s'afficher (écran noir pour l'instant : la logique du jeu tourne
   dans ces tâches jamais lancées).

Bug du traducteur repéré au passage : dans une zone A8 (mips `0x2EC8C`), les écritures passant par A8
manquent (à corriger).

### 60. Le noyau multitâche d'origine de SFA3, localisé — et le plan pour le remettre

**Ordonnanceur (ROM, désassemblé avec capstone)** :
```
$1110  CLR.B -$7B9C(A5)                 ; drapeau « image arrivée »
       LEA   -$7DA4(A5),A0 ; MOVE.W #$F,D0   ; 16 tâches de $20 octets
$111C  MOVE.W #$2600,SR ; TST.B -$7B9C(A5) ; BNE $1110   ; image arrivée : on recommence
       MOVE.B (A0),D1 ; CMPI.B #4,D1 ; BCC $1142        ; tâche prête (état >= 4) : la lancer
       MOVE.W #$2000,SR ; LEA $20(A0),A0 ; DBRA D0,$111C
       JSR $1414 ; BRA $1110
$1142  PEA $112E(PC) ; MOVE.W D0,-(A7) ; MOVE.L A0,-(A7)
       MOVE.L A7,-$7BA4(A5) ; MOVE.L A0,-$7BA0(A5)      ; pile de l'ordonnanceur, tâche courante
       EXT.W D1 ; MOVEA.L $1156(PC,D1.W),A1 ; JMP (A1)  ; saut selon l'état
$1166  MOVEA.L -$7BA4(A5),A7 ; MOVEA.L (A7)+,A0 ; MOVE.W (A7)+,D0 ; RTS   ; retour à l'ordonnanceur
$1170  (reprise)  MOVE.B #8,(A0) ; MOVE.L 4(A0),-(A7) ; MOVE.W 2(A0),-(A7) ; MOVEA.L 8(A0),A1 ; MOVE A1,USP ; RTE
$1184  (1er lancement) MOVE.B #8,(A0) ; MOVEA.L 4(A0),A1 ; MOVEA.L $C(A0),A4 ; MOVE A4,USP ; MOVE.W #0,SR ; JMP (A1)
```
Les tâches tournent en **mode utilisateur**, chacune sur sa pile (USP, préparée en `+$C`).

**API par instructions TRAP** (vecteurs lus dans la vue brute) :

| TRAP | adresse | rôle | équivalent porté |
|---|---|---|---|
| #0 | `$1306` | créer : D0 = emplacement, A0 = entrée, D1 → `+$10`, D2 → `+$12`, état `$0C00` | mips `0x2F730` + `CreateThread` |
| #1 | `$1326` | terminer la tâche courante (efface `+$10..+$1F`, état 0) → `$1166` | `0x2F8E0` + `ExitThread` |
| #2 | `$134A` | tuer la tâche D0 | `0x2F9B0` + `DeleteThread` |
| #3 | `$137C` | attendre : état = D0 \| `$100` (D0≠0) ou `$200`, sauve USP → `+8`, SR → `+2`, PC → `+4` → `$1166` | `0x2FB80`/`0x2FCF0` + `Wakeup`/`SleepThread` |
| #4–#7 | `$13A6`…`$13FC` | (à décoder) | |

Le portage a gardé la LOGIQUE de ces routines (ex. `0x2FB80` : `MOVE.W #$100,D1 ; TST.B D0 ; BNE ;
MOVE.W #$200,D1 ; OR.W D1,D0` = TRAP #3 mot pour mot) mais remplacé la commutation de contexte par
des fils PS2. La table des tâches est déplacée (ROM `-$7DA4(A5)` = `$FF025C` ; portage `$8184(A5)` =
`$FF0184`, zone A5 réorganisée) et ses champs suivent le modèle typé (`+$10`/`+$12` échangés = s32).

**Plan pour faire tourner le jeu traduit** (prochaine étape) :
1. Relever la disposition exacte de la table des tâches du portage (état, SR, PC, USP, pile initiale).
2. Écrire en 68K un noyau équivalent à celui de la ROM mais sur la table du portage (ordonnanceur
   au premier plan, lancement/reprise en mode utilisateur par USP, TRAP #0–#3).
3. Dans l'image traduite, remplacer le corps des 6 fonctions noyau portées (`0x2ED20` répartiteur,
   `0x2F730`, `0x2F8E0`, `0x2F9B0`, `0x2FB80`, `0x2FCF0`) par des appels à ce noyau ; l'IRQ2 ne fait plus
   que la partie « balayage vertical » et lève le drapeau d'image.
4. Piles des tâches hors de la RAM du jeu (RAM propre au fork ; essai MAME : `$660000`).
Pour Upper/Hyper, même noyau (moteur commun) : à vérifier sur leurs fonctions équivalentes.

### 61. Le jeu traduit démarre dans MAME avec un noyau de tâches reconstruit

**Noyau 68K (`kernel68k.py`, mini-assembleur vérifié par désassemblage capstone)** : remplace les fils
PS2 par un noyau coopératif calqué sur celui de Capcom (§60), sur la table des tâches DU PORTAGE
(A5+`$8184`, 16 × `$20`, état = octet +1 en vue cps2 ; tâche courante A5+`$8388`, long à moitiés
échangées). Mode superviseur, une pile par tâche (`$380` octets) hors de la RAM du jeu.
Transposition GÉNÉRIQUE des appels système PS2 (pas des fonctions du portage) :

| appel PS2 | noyau |
|---|---|
| `CreateThread` `0x1033E0` | CRÉER (D0 = emplacement×`$20`, A0 = entrée : l'API de TRAP #0) |
| `SleepThread` `0x103500` (depuis une tâche) | CÉDER : sauve registres et pile, retour à l'ordonnanceur |
| `ExitThread` / `ExitDeleteThread` | FINIR |
| `WakeupThread`, `StartThread`, `DeleteThread`, … | sans effet |

Ordonnanceur au premier plan (parcourt les 16 tâches, état ≥ 4 = prête, recommence à chaque image) ;
IRQ2 = fonction de balayage vertical portée (`0x2F2B0`) + drapeau d'image. Amorçage : reset porté →
initialisation portée (`0x2ED20`, crée la 1re tâche en `$1E0`) → ordonnanceur.

**Corrections trouvées en exécutant** :
- **Pointeurs de code** : une entrée de tâche (`LEA $2737A0,A0`) est un pointeur vers une fonction
  jamais appelée par `jal`. Débuts de fonction = PROLOGUES `addiu sp,-16 ; sd ra,0(sp)` (9 933).
  Relocalisés vers NOS adresses : dans le code (`LEA`/`MOVE.L #`, élément `codeptr` de l'assembleur) et
  dans les DONNÉES (10 190 mots de 32 bits : tables de routines).
- **Sauvegarde/restauration des registres dans le bloc de tâche** (`0x2FF00` / `0x30130`, émulation
  d'un banc de registres PARTAGÉ entre fils : helpers MIPS prenant l'adresse dans `a0`) : rendues sans
  effet (notre noyau garde les registres de chaque tâche sur sa pile).
- **Aiguillages « table de BRA.S »** (47 dans SFA3) : `JSR T(PC,D0.W)` sans lecture de table devant =
  forme d'origine avec une table de `BRA.S` ; hébergée comme telle (`BRA.S` → tremplin `JMP abs.L`).
- **Mot aux octets inversés vers la mémoire** (`ROR.W #8,Dk ; MOVE.W Dk,… ; ROR.W #8,Dk`) : l'état
  d'attente d'une tâche n'était pas écrit.
- **TST d'un octet indexé** (`TST.B 1(A1,D0.W)` avant `BNE`) : manquait, le test « emplacement libre »
  portait sur des drapeaux au hasard.
- **Octets indexés en mode cps2** : déplacement XOR 1 en supposant l'index PAIR (vrai pour les
  structures et tables de mots de Capcom ; limite connue pour les index impairs).

**Résultat (MAME, image 100)** : tâches créées, lancées, mises en attente et reprises (tâche 15 prête,
tâche 3 en attente d'une image, pile sauvée) ; la palette est écrite en mémoire vidéo (`$90C000`).
Écran encore noir : les plans de décor (`$908000`–`$91BFFF`) restent vides, et le mot de mode du jeu
(`$FF8000`) tourne en boucle `2 → 0 → 4` (période 150 images) au lieu de progresser `0 → 4 → 6 → 8 → C
→ 10` comme le témoin. **Prochaine étape** : suivre la séquence d'attraction (minuterie déplacée par la
réorganisation de la zone A5) pour trouver ce qui la réinitialise ; outils prêts (`etat.lua`,
`mode.lua`, `vram.lua` : état des tâches, variables, remplissage de la vidéo, comparés au témoin).

### 62. Entrées CPS2 reliées ; diagnostic de la boucle d'attraction

**Entrées** (routine d'entrées de la ROM `$1460` ↔ interruption de balayage portée : mêmes destinations
A5, `$58/$59/$5C/$5D/$62/$66/$68/$1C4/$1C5`) — le portage range des valeurs DÉJÀ INVERSÉES :

| portage (base RAM +) | CPS2 | inversion |
|---|---|---|
| `$62190` | `$804000` (joueur 1) | NOT |
| `$62191` | `$804001` (joueur 2) | NOT |
| `$62192` | `$804010` (système) | — |
| `$62193` | `$804011` (boutons 4-6) | NOT |
| `$62194` / `$62195` | `$804020` / `$804021` | NOT |
| `$62196` (mot) | `$804030` | — |

Traduction : lecture du vrai port + `NOT.x` ; correspondance octet EXACTE (pas de XOR 1, relevée
octet à octet des deux côtés — `BYTE_EXACT`).

**Diagnostic de l'écran noir** (point d'observation MAME sur le mot de mode `$FF8000`, `watch.lua`) :
- images 17–31 : la séquence d'initialisation fait passer le mode par 2, 4, 6, 8, 0 ;
- à partir de l'image 35 : BOUCLE de 3 images — `$6328` (mips `0x46BF0`, `ADDQ.W #2,(A5)`) avance
  le mode 0 → 2 → 4, puis la tâche d'attraction est relancée depuis son entrée `$617C` (mips `0x468B0`)
  qui remet `(A5)` à 0 ;
- sur 400 images : 3 créations de tâche mais **189 fins** : la fonction d'entrée de la tâche se
  termine (appel terminal puis `RTS` sur l'adresse de FINIR empilée au lancement). Sur PS2 un fil qui
  se termine MEURT ; notre FINIR ne marque pas la tâche comme morte, et l'ordonnanceur la relance.
**À trancher** : vraie fin de tâche (alors FINIR doit mettre l'état à 0 comme TRAP #1) ou boucle
principale de tâche mal traduite (un retour en arrière traduit en appel terminal). Point de départ :
la tâche d'entrée `$617C` et son appel terminal final.

**Essai tranché (fin de séance)** : FINIR marque désormais le fil comme TERMINÉ dans le noyau (pile
sauvée = −1, relance ignorée tant qu'il n'est pas recréé : sémantique exacte d'un fil PS2 terminé ;
l'état visible par le jeu reste intact). La boucle disparaît, mais le mode reste **bloqué à 4** : le
témoin, lui, arme alors une minuterie (`$95` en `$FF8002`) et passe au mode 6. ⟹ La tâche
d'attraction NE DEVRAIT PAS se terminer : **sa boucle d'attente est court-circuitée dans la
traduction** (piste : l'appel terminal `JMP $1BDE4` (mips `0x46C90` → `0x27EED0`) qui clôt le pas du
mode 4, et la façon dont le portage enchaîne les pas d'état d'une tâche — à comparer à la ROM).
Contrôle : le mini-assembleur du noyau est vérifié par désassemblage à chaque modification (il a
attrapé un `MOVEQ` sur le mauvais registre).

### 63. Boucle de diagnostic outillée ; six corrections ; premier écran (logo CAPCOM)

**Outils** (`tools/untranspile/`) :
- `diag.py [N] [--nobuild]` : reconstruit l'image, lance MAME, repère la PREMIÈRE exception (chaque
  vecteur boucle sur sa propre adresse `$A00+2v`), relance avec une trace autour de cette image et
  affiche les N dernières instructions, chacune avec son adresse MIPS et le mnémonique traduit
  (`carte_image.txt`). Une exécution = un bug localisé.
- `watch.py ADRESSE [taille] [images]` : point d'observation MAME, écritures → PC 68K → va MIPS.

**Corrections, dans l'ordre où la boucle les a trouvées** (l'image atteinte avant la faute passe
19 → 39 → 629 → 731) :
1. **Branchements inconditionnels** (`beq zero,zero`) jamais traduits : chaque boucle d'une tâche
   (tâche 15 de service, boucle d'attraction) perdait son retour en arrière. Désormais `BRA`.
2. **Aiguillage « même registre »** (`MOVE.W T(PC,D0.W),D0 ; JSR T(PC,D0.W)`) : la lecture de table
   insérée était prise pour une table de DONNÉES (règle `dtab` testée avant `tblref`). Ordre corrigé.
3. **Réalignement du portage** : `lw r,An ; addiu r,r,3 ; addiu t,zero,-4 ; and ; sw An` =
   `An ← (An+3) & ~3` avant la lecture d'un long dans un flux de données (40 sites dans SFA3). Le
   portage a aligné sur 4 octets les longs de ses tableaux ; nos données SONT les siennes, on garde
   donc ce réalignement (drapeaux préservés : `MOVE SR,-(SP) … MOVE (SP)+,CCR`).
4. **Tables d'aiguillage partagées** : plusieurs aiguillages voisins lisent la même table MIPS ;
   chacun héberge sa copie, dont les entrées sont relatives À CETTE copie. La lecture `MOVE.W` et les
   entrées visaient la DERNIÈRE copie. Chaque lecture vise maintenant la copie de son `JSR`/`JMP`
   (et un hôte n'accueille qu'une seule table).
5. **Tableaux de structures** : les champs `+0/+2/+4/+6` d'un tableau à pas de 8 sont référencés
   séparément ; la copie hébergée du champ `+2` s'arrêtait à la référence suivante (2 octets !) et
   l'index lisait dans le code. Nouvelle forme ABSOLUE, toujours exacte :
   `MOVE.L An,-(SP) ; LEA données.L,An ; MOVE.x 0(An,Xi),<dst> ; MOVEA.L (SP)+,An` (registre
   emprunté hors de ceux de l'instruction ; octets : adresse XOR 1, index pair).
6. **Pointeurs PS2 BRUTS dans les données** (ex. `0x5C8784` dans la table des listes de sprites) :
   seuls les pointeurs de CODE étaient relocalisés (critère sûr : prologue). Pour les pointeurs de
   données, le repérage statique n'est pas sûr : 64 207 longs tombent dans la plage des données,
   contre 22 000 à 33 000 dans des plages voisines de même largeur (paires de s16 : bruit), et la ROM
   d'origine ne sert pas de corrigé car le portage a CONVERTI ces données (codes de tuiles Anthology :
   `0x00A0D220`…). Banc MAME : **conversion à l'exécution** — après chaque `MOVEA.L` venant de la
   mémoire ou d'un Dn, `JSR CONV_An.W` (routines en `$400`, drapeaux préservés) ramène une valeur des
   plages PS2 (données, variables du portage, RAM, objets, vidéo, QSound) vers la carte 68K. Nos
   adresses MATÉRIELLES CPS2 portent l'octet haut `$01` (ignoré par le bus 24 bits) pour ne jamais être
   confondues avec une adresse PS2 de la même plage (`$700000`, `$804000`, `$900000` y tombent).
   **Cible finale (fork)** : plan mémoire IDENTITÉ — les données du module aux MÊMES adresses que
   sur PS2 (`0x583C40–0x88C700` pour SFA3), la RAM aussi visible à sa base PS2 ; plus aucune
   conversion, coût nul, exact par construction. Limite connue du banc : une comparaison entre un
   pointeur brut rangé en RAM et une constante convertie.

**Résultat** : la séquence d'introduction tourne ; **à l'image 600 le code traduit affiche le logo
CAPCOM** (retourné verticalement, décors en tuiles erronées — attendu : les codes de tuiles sont ceux
de l'Anthology, pas ceux des ROM graphiques CPS2 de MAME). Faute suivante à l'image 731 dans le
constructeur de listes de sprites (mips `0x108010`) : les enregistrements y portent des références
Anthology (`0x00A0D220`) lues comme pointeurs ; c'est la couche graphique modifiée par le portage
(§45, §48) — à traiter avec la correspondance des tuiles.

### 64. Retours partagés, soustraction doublée : 1 800 images sans faute

La ROM d'origine sert de corrigé exact pour le constructeur de listes de sprites (mips `0x108010` ↔
ROM `$22500`, trouvé par la signature `ANDI.W #$3FF,D0 ; ANDI.W #$3FF,D1 ; OR.W $D0(A6),D0`) :
- **Retour partagé absorbé** : `BEQ fin … JMP T(PC,D0.W) ; fin: RTS` (ROM `$2250E`→`$22544`). Le
  `jr ra` qui suit un saut indirect était « absorbé » (pas de RTS émis) alors qu'il est AUSSI la cible
  d'un branchement : le branchement tombait sur l'instruction émise suivante (le cas 0 de
  l'aiguillage). Un retour absorbé reste désormais un `RTS` dès que lui ou son épilogue
  (`ld ra`, `addiu sp`) est cible d'un branchement : **880 sites** dans SFA3.
- **Soustraction émise deux fois** (`SUB.W D5,D7 ; SUB.W D5,D7`) : le chemin « arith » émettait sans
  s'arrêter, puis le chemin « bloc exact » (drapeaux complets) émettait à nouveau. Plus aucun doublon
  sur tout le module.
- Au passage : le portage a ÉTENDU l'aiguillage des enregistrements de sprites (4 cas dans la ROM,
  types ≥ 8 → `RTS` ; 10 dans le portage). Le type `0x12` y réutilise le cas 0 avec un pointeur de
  positions vers le TAS PS2 (`0x00A0D220`, hors module) : ajout propre à l'Anthology, sans effet dans
  l'arcade (ROM : `RTS`) — c'est bien la table du portage qui l'envoie vers `RTS` (entrée 9).
- La ROM a `ORI.W #$6000,D1` après les masques de coordonnées ; le portage ne l'a pas (bits de
  taille/priorité gérés par son moteur de sprites) — à rétablir avec la couche matérielle.

**Résultat** : recensement 98,1 % inchangé ; **aucune exception sur 1 800 images** ; l'introduction
affiche une scène bleue (image 250) puis le texte CAPCOM (retourné verticalement, tuiles de fond
erronées) qui reste affiché jusqu'à l'image 2 000. Prochaines pistes : comparaison au témoin image par
image, retournement vertical, avancée de la séquence d'attraction.

### 65. L'attraction avance ; numérotation des tuiles de plan du portage ; banc visuel

**Corrections du traducteur** (toutes trouvées par comparaison au témoin MAME, mêmes images) :
1. **Résultat natif du portage** : `jal f ; beq/bne v0,zero` teste une valeur rendue par une fonction
   PS2 (le code 68K traduit ne rend jamais rien dans `v0`). Le portage y a greffé des attentes (fin du
   mode C de l'attraction : `0x393B20` = « moteur occupé ? », on réessaie à l'image suivante) ; la
   traduction réessayait à l'infini. Règle : `v0` supposé nul (comportement arcade). Mode `$10` atteint.
2. **Registre prêté D8/A8 local à la zone** : le registre prêté est sauvé/restauré autour de la zone,
   il suffit donc qu'il soit libre DANS la zone. Le recompilateur avait replié les 8 `MOVEM.L` déroulés
   du remplissage `$92A000` en une boucle interne sur D8, perdue (1 long par tour au lieu de 16) :
   19 zones de plus traduites ; `$924000`/`$928000` identiques au témoin.
3. **`LEA T(PC,Dn.W),Am` sur une table de données** (`addu r,sext16(Dn),T ; sw r,Am`) : n'était pas
   traduit, Am gardait une valeur périmée (ex. table des réglages par région → A0 → `$96(A5)` =
   retournement d'écran : le logo CAPCOM était à l'envers). → `LEA données.L,Am ; ADDA.W Dn,Am`.
4. **Flux d'octets `(An)+` en mode cps2** : l'adresse vue par le 68K est `An XOR 1`, dont la parité
   ALTERNE à chaque octet ; `ADDQ #1 ; MOVE.B -2(An)` n'était juste qu'une fois sur deux. Séquence
   exacte à l'exécution (bascule du bit 0 via la pile, accès `(An)`, rebascule, `ADDQ.L #1`, `TST.B`) :
   72 sites.

**Numérotation des tuiles de plan (mesurée : même écran, mêmes registres CPS-A/CPS-B)** :

| plan | registre de base | code portage → code CPS2 |
|---|---|---|
| scroll1 (8×8) | `$804102` | identique |
| scroll2 (16×16) | `$804104` | `+$5600` (100 % sur l'écran QSound, ~97 % dans l'intro) |
| scroll3 (32×32) | `$804106` | `+$B00` pour le vide ; la ROM elle-même ajoute `$B00` aux tables d'images (`ADDI.W #$B00` en `$190F4`), le portage non |

Les conteneurs Anthology suivent EXACTEMENT la numérotation CPS2 (vérifié au pixel : 8×8 `m` ↔
quart 1, 32×32 `$1343` ↔ CPS2 `$1343`). **Écart propre au portage** : l'image « VIRTUAL AUDIO / QSound »
(scroll3) est décalée de `−$F` dans les DONNÉES du portage (`$834` au lieu de `$843`) — le contenu de
cet écran a été modifié par l'Anthology (comme l'écran de version, supprimé : les gestionnaires du
démarrage ont été réécrits en `ADDQ #2 ; JMP`, sans minuterie). Ce n'est pas une erreur de traduction.

**Banc visuel** (`mame/banc.lua`) : prise d'écriture MAME sur la mémoire vidéo qui applique ces
décalages (bases suivies sur les registres CPS-A) = ce que fera le fork ; captures `SNAPS=…`, avec
`-video none` (la fenêtre bloquait MAME). Outils : `dumpv.lua`/`dumpv2.lua` (vidéo + registres +
A5 à des images données), `cpsa.lua`/`cpsalog.lua` (écritures CPS-A/CPS-B, avec PC), `greffe.lua`
(injecter une mémoire vidéo dans le témoin : test décisif « la différence est-elle dans la VRAM ? »),
`vcount.lua` (écritures vidéo par image).

**État** : aucune exception sur 1 800 images ; la séquence de modes suit le témoin (écrans de
démarrage retirés par le portage) ; écran QSound et logo CAPCOM reconnaissables ; l'intro affiche
ses bandes, tuiles encore fausses. Écarts restants : table `ADDA.W` depuis une table (1 site),
`ADDA.W D8` sans registre prêté, numérotation fine de scroll3.

### 66. L'intro va jusqu'au bout (modes `$10` → `$12` → `$14`) ; sept corrections

Méthode inchangée : comparaison au témoin sur des états équivalents (mêmes modes/étapes, décalage
constant de −215 images car les écrans de démarrage sont supprimés par le portage), puis la ROM
d'origine comme corrigé pour chaque divergence.
1. **Octet signé d'une table rangé en mot** (`lb ; sh D0`) : non traduit (D0 périmé → étape de l'intro
   fausse). → `MOVE.B T(PC,Dn.W),D0 ; EXT.W D0`.
2. **Durée de vie du registre prêté D8** : la zone se fermait au dernier ACCÈS à la case, alors que la
   valeur lue vit encore dans des registres MIPS dérivés (extension de signe, adresse de table) : le
   68K restaurait D7 avant de s'en servir comme index. Zone étendue à la dernière utilisation des
   valeurs dérivées (suivi de contamination).
3. **Retours partagés, suite** : les `BRA` (ex-`beq zero,zero`) comptent aussi comme branchements vers
   un épilogue absorbé : **3 030** retours partagés au lieu de 880 (un `BRA` vers la fin de fonction
   tombait dans la fonction suivante : A1 jamais posé → écriture vidéo dans la RAM → pile écrasée).
4. **Drapeaux rendus à l'appelant** : `TST.B x(A5) ; RTS` (ROM `$77A2`, fin de fondu ; l'appelant fait
   `BSR ; BNE`) n'était pas émis. Deux causes : l'opération en place précédente (`ADD.W` sur la même
   adresse, mais en MOT, et suivie de 4 `JSR`) était crue suffisante → `flags_set` mémorise la taille
   et est effacé par tout appel ; et un test en attente devant `jr ra` est émis avant le `RTS`.
5. **Octet indexé à index impair** (`MOVE.B D0,2(A1,D2.W)` avec D2 = numéro de joueur 0/1) : le
   XOR 1 du déplacement supposait l'index pair → écriture dans le mot voisin (index de scène
   `$8C28` ← 1 → saut hors table). Séquence exacte à l'exécution (114 sites) :
   `MOVE.L An,-(SP) ; LEA d(An,Xn),An ; bascule du bit 0 via la pile ; <instr> (An) ; MOVEA.L (SP)+,An`.
6. `diag.py` : fenêtre réglable (`MAXF=4000`).

**État** : l'intro « Triumph or Die » se déroule jusqu'au bout (étapes 1 → `$3B`, fondu final,
compte à rebours), puis modes `$12` et `$14` comme le témoin. Faute suivante à l'image 2 551 (mode
`$14`, démonstration avec personnages) : la passe de rendu dessine l'objet joueur `$FF8400` alors que
son pointeur d'animation `$1C(A6)` est nul — l'initialisation du joueur (ROM `$27B98`, portage mips
`0x1C9A84`, étendue par l'Anthology : tests de version `$C001(A5)`) ne s'exécute pas encore ; les
drapeaux d'objet valent `$0101` au milieu de l'image et `$0001` à la fin (à suivre).

### 67. Mode `$14` (démonstration) : table de pointeurs d'objets vers An

- **`MOVEA.L T(PC,Dn.W),An`** (ROM `$27776` : table des objets joueurs → A6) : le `lw` indexé vers un
  registre A n'avait pas de traduction (seul le cas Dn existait) ; A6 restait périmé et les tests
  d'objet portaient sur un autre objet → l'initialisation du joueur (ROM `$27B98`, portage
  `0x1C9A84`) était sautée. 30 sites. Forme absolue + remise en ordre du long + conversion du
  pointeur (assembleur).
- Outil `mame/tapw.lua` : prise d'écriture sur une plage (toutes les écritures, masque, PC) — plus sûr
  que le point d'observation du débogueur ; `objh.lua` : en-têtes d'objets image par image.
- Rappels de méthode (erreurs commises puis corrigées) : `-$7178(A5)` = `$FF0E88` (déplacement
  NÉGATIF) ; une écriture relevée à « l'image N » (compteur Lua) a lieu PENDANT l'image N+1 ; la
  disposition A5 du portage = ROM − `$254` dans cette zone ; champs u8 : le portage les garde à la
  même adresse, notre XOR 1 les permute de façon cohérente (`$400` actif ↔ `$401` init).

**État** : l'initialisation du joueur s'exécute (image 2 542). Faute à l'image 2 544 : l'objet joueur
lit son script `$230(A6)` (copié de `$220`) encore nul ; le témoin ne le pose que 3 images après
l'initialisation (ROM `$32748`) et ne lit le script qu'ensuite. Prochaine étape : comparer la machine
d'états de l'objet (`$4(A6)`, `$200(A6)`) image par image entre les deux exécutions.

### 68. Démonstration (mode `$14`) : EXT, longs non alignés, tables à trous

- **`EXT.W` / `EXT.L` n'étaient pas traduits du tout** : `lb r,Dk ; dsll32/dsra32 24 ; sh r,Dk` =
  `EXT.W Dk` ; `lh r,Dk ; (16) ; sw r,Dk` = `EXT.L Dk` (octet → long : les deux). **274 sites** ; ex.
  ROM `$F3DA0` `MOVE.B $3(A6),D1 ; EXT.W D1 ; LSL.W #2,D1` : l'octet haut périmé de D1 entrait dans
  l'index d'une table de pointeurs par personnage. Recensement SFA3 : **98,4 %**.
- **Longs non alignés** : le recompilateur écrit/lit un long 68K à un déplacement pair non multiple de
  4 avec `swl/swr` (`lwl/lwr`) — 80 + 30 paires, jamais traduites (ex. `MOVE.L (A0),$32(A6)`, ROM
  `$2A774`). Les paires sont remplacées en amont par un `sw`/`lw` synthétique.
- **`MOVE.L An,d(Am)` en mode cps2** (long rangé moitiés échangées) : n'était pas traduit (pointeur
  d'animation `$1C(A6)` jamais écrit) → `MOVE.W An,d(Am) ; EXG D0,An ; SWAP D0 ; MOVE.W D0,d+2(Am) ;
  SWAP D0 ; EXG D0,An` (le SWAP final redonne les drapeaux du `MOVE.L`).
- **Tables d'aiguillage à trous** : une entrée nulle (cas inutilisé) arrêtait la lecture ; et quand la
  table finit par un trou juste avant la table suivante référencée, le portage indexe au-delà
  (T_587150 : 3 cas, 0, puis l'index 8 dans T_587160) → la lecture continue dans ce cas précis
  (l'extension systématique coûtait 100 Ko et 619 renvois hors de portée : écartée).

**État** : la démonstration démarre (objets joueurs initialisés, animations, scripts de personnage).
Faute suivante image 2 569 : index d'aiguillage `$9(A6) − 8` négatif pour un objet (ROM `$1B4F4`,
`$8(A6) ≥ 8` attendu) — divergence d'état d'objet à suivre avec `objs.lua`.

### 69. PERFORMANCE : le surcoût de la recette cps2 est mesurable ; conception du bus « octets XOR 1 » du fork

**Mesure** (trace d'une image, même scène) : dans l'intro, la version traduite garde de la marge
(17 000 lignes sur 19 000 dans la boucle d'attente du noyau). Dans la démonstration (mode `$14`), le
témoin garde encore ~20 % d'attente (sa boucle `$112C` tourne 960 fois par image) ; la version
traduite n'en a plus : la minuterie de démo (`+$A`, `$4B0`) ne descend qu'une image sur trois.
Point chaud : la copie de blocs de tuiles (256 tours par appel) dont le flux d'octets `(A2)+` coûte
~108 cycles par octet avec la séquence exacte du §65 (bascule de parité via la pile), contre 8 pour
`MOVE.B (A2)+,D1`. Autres surcoûts de la recette cps2 : `SWAP` autour des accès longs, conversion
de pointeurs `JSR CONV_An` (banc MAME), formes absolues des tables, octets indexés exacts.

**Conception retenue pour le fork (coût nul, exact par construction)** :
1. **Bus « octets XOR 1 »** : pour la RAM de travail et la ROM de données, le fork présente les accès
   OCTET à l'adresse XOR 1 (les accès mot/long restent natifs). Le code traduit utilise alors les
   déplacements d'octet MIPS TELS QUELS : plus de XOR statique, plus de séquences à l'exécution
   (flux `(An)+`, index impairs, tables d'octets), exact quelle que soit la parité. Coût : une porte
   XOR dans les gestionnaires de lecture/écriture octet de FBNeo.
2. **Plan mémoire identité** des données (§63) : plus de `JSR CONV_An`.
3. En réserve : surcadençage du 68000 (option FBNeo existante).
Le banc MAME (matériel figé) garde les séquences exactes : correct mais plus lent dans les scènes
chargées (ralentissements visibles, logique inchangée). Prochaine étape côté traducteur : un mode
`MEMMODE=fork` qui émet les octets sans XOR (et les longs sans SWAP si le bus du fork échange aussi
les moitiés), à valider dans le fork.

### 70. PREMIER DÉCOR DE COMBAT : la démonstration d'attraction tourne (4 000 images sans faute)

Dernier verrou levé : **octet lu via `lh`** (le recompilateur charge le demi-mot entier puis garde
l'octet bas avec `sb`) : non traduit → le compteur de la boucle des objets joueurs (ROM `$27766`,
`MOVE.B -$4FDE(A5),D0`) n'était jamais chargé, seul le joueur 2 était initialisé. L'octet bas d'un
demi-mot petit-boutiste est l'octet MIPS de même adresse → `MOVE.B (d XOR 1)(An),Dk` (5 sites).

**Résultat** (captures `demo_sfa3_traduit_2800.png` et sa grille, retirées du dépôt : images du jeu) : aucune
exception sur 4 000 images ; séquence de modes identique au témoin (démarrage, QSound, CAPCOM, intro
« Triumph or Die », démonstration) ; **le décor du combat de démonstration s'affiche** (mur aux dragons,
escalier, arbres, sol) avec le banc visuel (décalages de plans §65). Restent : les **personnages**
(tuiles des banques Anthology : numérotation par banque, §48 — à faire dans le fork), quelques
tuiles de plan fausses, et la lenteur (§69) dans les scènes chargées.

Bilan de la séance de diagnostic (§63-§70) : 30 classes de défauts du traducteur corrigées, chacune
trouvée par comparaison au témoin puis confirmée sur la ROM d'origine ; toutes générales (valables
pour Upper et Hyper, même recompilateur ou son successeur).

**Complément §70 — compteur lu en demi-mot, comparé en octet** : le portage range certains compteurs
octets de la ROM en DEMI-MOT (`ADDQ.W #1,$9EDC(A5)`) et les relit via `lh` + extension 24 bits.
La comparaison `CMPI.B #4` portait sur l'octet HAUT (`$9EDC`, toujours 0) : la boucle des objets
joueurs tournait jusqu'à `$400` au lieu de 4 → démonstration 12× trop lente. `enc_cmp` : opérande
mémoire lu en demi-mot et comparé en octet → adresse XOR 1 (octet bas). La démo tourne maintenant à
½ vitesse (coût des flux d'octets exacts, §69), se termine à l'image 4 954, et la boucle d'attraction
continue (modes `$16`, `$18`) ; aucune exception sur 8 000 images.

### 71. Appels indirects par registre ; branchements conditionnels lointains

- **`JSR (An)` / `JMP (An)`** (`lw r,An ; jalr r`) : **n'étaient pas émis du tout** — le traitement
  générique de `jalr` ne faisait que la comptabilité des retours. 23 sites, dont le gestionnaire des
  objets de la carte du monde (ROM `$336F6` : `MOVEA.L table(PC,D0.W),A0 ; JSR (A0)`), d'où la carte
  figée (mode `$18`). Ces routines d'objets, désormais appelées, ont révélé le défaut suivant.
- **`Bcc.W` hors de portée** : la fusion « Bcc par-dessus un saut » (§62) peut viser une fonction
  lointaine ; le déplacement 16 bits débordait EN SILENCE (ex. `BNE` à −43 Ko → saut au milieu d'un
  `JMP abs.L`). La relaxation vérifie maintenant la portée des `Bcc.W` : forme lointaine
  `B(inverse)cc.S +6 ; JMP abs.L` (`BRA` lointain → `JMP abs.L`). **87 branchements** concernés.

**État** : faute suivante image 738 (constructeur de listes de sprites, après réalignement) — à suivre.

### 72. Registres supplémentaires D8/A8 hors zone et pile privée `0x114C` (analyse)

Code AJOUTÉ par le portage (cas étendus des listes de sprites, mips `0x100700`) : pas d'équivalent
ROM ; écrit dans un dialecte 68K étendu (registre D8) ; D8 y est un COMPTEUR DE BOUCLE qui traverse
un appel, sauvegardé/restauré sur une **pile privée** (case `0x114C` utilisée comme pointeur de pile :
`lw ; addiu -4 ; sw ; sw valeur,0(...)` = empiler, l'inverse = dépiler). Recensement SFA3 : 30 paires
empiler/dépiler sur cette pile (A0–A6, D0–D8), dont la moitié dans le code propre du portage
(`0x3803xx`), le reste dans le jeu (`0x34560` A0, `0x101550` A1, `0x125CCC` D0/D1, `0x100740` D8…).
Le prêt de registre (§54) ne peut pas couvrir une durée de vie qui traverse un appel ; ici la zone ne
couvrait que le décrément, et la comparaison lisait le D7 restauré (boucle infinie / faute).
**Plan** : (1) pile privée → vraie pile 68K (`MOVE.L Rn,-(SP)` / `MOVE.L (SP)+,Rn`, paires équilibrées
dans la fonction) ; (2) D8/A8 hors zone → DOMICILE MÉMOIRE fixe (banc : RAM annexe `$663900`),
accès routés vers les traitements d'adresse absolue.

**§72 réalisé** :
- **Pile privée `0x114C` → pile 68K** : les paires empiler/dépiler (`lw/addiu ∓4/sw` sur la case
  `0x114C` + `sw/lw 0(...)`) deviennent `MOVE.L Rn,-(SP)` / `MOVE.L (SP)+,Rn` (D8 : sa variable).
- **Domicile mémoire de D8** : `$FF07F0` (`$87F0(A5)`, zone RAM vérifiée inutilisée en jeu — piles de
  tâches de la ROM, remplacées par celles de notre noyau). Hors zone prêtée, tout accès à D8 devient
  un accès `d16(A5)` (lectures, écritures, arithmétique en place, comparaisons : traitements existants).
  Les zones prêtées de D8 sont conservées (index de table, DBRA) mais SYNCHRONISÉES : à l'entrée le
  registre prêté est chargé depuis le domicile, à la sortie il y est rendu (drapeaux préservés).
  Variable `D8_HOME` (`none` = ancien comportement). A8 (base d'adressage) garde les zones seules.
- Recensement SFA3 : **98,5 %**. La boucle de sprites étendue du portage (image 738) passe.
**État** : faute image 1 008 (intro) : un objet de la liste d'affichage a un partenaire `$2C` = `$4840`
(`MOVEA.W` → adresse de code, pas un objet `$FFxxxx`) — à suivre.

### 73. D8 : boucles et pile privée corrigées ; question ouverte sur le code ajouté par le portage

Corrections :
- **Extension de zone jusqu'au branchement** : le suivi de contamination s'arrêtait AVANT le
  branchement qui lit la valeur dérivée (DBRA sur D8 : `lh D8 ; addiu -1 ; sh D8 ; bgez`) → le `DBRA`
  émis portait sur le registre déjà restauré (boucle d'effacement de 65 536 tours, RAM balayée).
- **DBRA sur D8 à domicile mémoire** : `SUBQ.W #1,$87F0(A5) ; BPL` (test de signe d'une valeur
  modifiée en place : `bgez/bltz` → `BPL/BMI` sur les drapeaux de l'opération).
- **Sauvegarde du registre prêté à D8 dans une case FIXE** (`$87F8(A5)`) et non plus sur la pile :
  la pile privée (§72) s'entrelaçait avec la sauvegarde de zone (LIFO rompu : D7 et la pile décalés).
- **Test en attente sur le registre prêté** : redirigé vers le domicile de D8 à la fermeture de zone.
- **`CMPI #k` redondant après `ADDQ/SUBQ` sur le même Dn** (RES = la valeur déjà rangée) : supprimé,
  les drapeaux de l'opération suffisent (une itération de moins sinon). Mémoire invalidée dès qu'une
  autre instruction est émise.

**Question ouverte (image 744)** : les enregistrements de sprites du portage utilisent des commandes
ÉTENDUES (ex. `$18` → cas 12 de l'aiguillage `T_58BBA0`, gestionnaire ajouté `0x100700`, sans
équivalent ROM). Ces gestionnaires ajoutés utilisent D6 et A3 (`MOVE.W (A0)+,D6 … DBRA D6`,
`LEA $56(A6),A3 ; (A3)+`) SANS les sauvegarder, alors que la boucle d'affichage de la ROM qui les
appelle compte avec D6 et parcourt la liste avec A3 → compteur écrasé, lecture au-delà de la liste,
objet mort dessiné (`$1C` = 0). Le même code MIPS aurait le même conflit sur PS2 : soit ces
gestionnaires sont appelés par un chemin qui sauve les registres (non identifié), soit la
traduction d'un de leurs prologues perd une sauvegarde (pile privée sous une forme non reconnue ;
une seule écriture `0x114C` non reconnue, dans le code propre du portage, `0x3819A4`). À trancher
en traçant l'exécution PS2 (PCSX2) de cette même scène, ou en relevant tous les chemins d'appel de
`0x100700`.

### 74. Réponse à §73 par PCSX2 : le DBRA du recompilateur n'est pas celui du 68K

Test dans PCSX2 (débogueur : arrêt en `0x002F0700` = entrée du gestionnaire étendu, lecture du banc
de registres `0x70001100`, point d'arrêt d'écriture sur D6 `0x7000113C`) :
- à l'entrée du gestionnaire ajouté, l'état PS2 est IDENTIQUE au nôtre (A0/A3/D6) : la traduction
  est juste jusque-là ; le gestionnaire écrase bien D6 sur PS2 aussi (sortie D6 = `$0000FFFF`) ;
- la boucle d'affichage de la ROM survit malgré tout car le **DBRA du recompilateur** est
  « décrémenter, boucler si ≥ 0 » (`addiu -1 ; bgez`), et non « boucler tant que ≠ -1 » : avec
  D6 = `$FFFF` après le gestionnaire, la boucle SORT (valeur négative) au lieu de refaire 65 536 tours.

Correction (`translate.py`) : le « DBRA » MIPS devient `SUBQ.W #1,Dn ; BPL` (402 sites), sauf si les
drapeaux sont relus ensuite (`flags_read_first` : lecture de RES/N avant toute réécriture, dans la
suite ou à la cible) — alors vrai `DBRA` (0 site dans SFA3). La faute passe de l'image 744 à 1 299.

### 75. Ressources chargées par le code natif, setjmp/longjmp, et trois corrections de traduction

**Tables d'animation natives (image 1 299)** : le portage a sorti de la ROM des tables d'animation.
Une fonction native du module (`0x383700(i)`, `0x3837d0(perso)`) décompresse un fichier de
`X_DATA.BIN` (MWo3) à l'adresse **fixe `0xA75000`** et range ce pointeur en `$BE48(A5)`. Les fichiers
(290–311 : intro, écran 1, un par personnage) contiennent des pointeurs absolus déjà posés pour
`0xA75000`. `assets_natifs.py` les décompresse, les range bout à bout à une base virtuelle
(`0xA80000`, pointeurs relogés), et la conversion de pointeurs `$400` projette cette plage sur le bloc
(94 Ko après les données, `$399B00`) ; les appels natifs deviennent des talons 68K
(`MOVE.L #ptr,$BE48(A5)`). Index lus : site d'appel (0 ou 1) et octet `$132(A5)` (perso).

**Frames de sprites à adresse fixe** : ~17 000 pointeurs des données du module visent
`0xA04000`–`0xA73D34` = **fichier 289** (MWo3, 458 Ko : frames de tous les personnages), chargé une
fois à adresse fixe. Il ne tient pas dans les 4 Mo de ROM programme : projeté tel quel en `$A04000`
(identité, hors des plages de conversion). Banc MAME : tap de lecture sur la plage non projetée
(`mame/banc_mem.lua`, chargé par `diag.py`, `watch.py`, `trf.lua` — l'utiliser aussi dans les scripts
ponctuels, sinon l'exécution diverge). Fork : ROM supplémentaire à cette adresse.

**Appels vers les fonctions natives DU MODULE** : l'assembleur les traitait comme internes
(`label()` rend l'instruction traduite SUIVANTE) → ces appels exécutaient des fragments de C
« traduits ». Paramètre `native` d'`assemble()` (liste de `hooks_fork_ro3.json`) : cibles externes.

**setjmp / longjmp du recompilateur** : `0x119F48` = setjmp, `0x119FA0` = longjmp(tampon, 1). Un
`Bcc/BRA` 68K vers une AUTRE fonction (ex. `BNE $30BC8` depuis `$321AE`) : l'entrée de la cible fait
`setjmp(tampon)`, le saut devient `longjmp(tampon, 1)` — qui désempile les appels MIPS en trop, comme
le `BRA` d'origine. 3 tampons (`0x88CE50`, `0x88CF20`, `0x88CFF0`), 6 sites
(`hooks_fork.setjmp_sites`). Banc : talons 68K (setjmp : SP et retour dans un tampon en `$663890` ;
longjmp : restaure SP, réécrit le retour, `RTS`). Le talon RTS de repli faisait exécuter la suite
du longjmp (sous-aiguillage de fin de script avec un index de commande → saut au milieu d'une
instruction → objet joueur 2 libéré dans le mauvais groupe → compteur de liste `$6ECC` écrasé).

**Corrections de traduction** :
- **Bloc de drapeaux exact** (recompilateur récent) : toute écriture de même taille dans le Dn
  destination, jusqu'à 0x40 octets après, était prise pour le résultat du `subu` → `SUB`. Or
  `CMP.W D1,D2 ; BCC ; MOVE.W D1,D2` (bornage) écrit une AUTRE valeur. `derives_from()` vérifie que le
  registre écrit dérive du résultat du `subu`. 37 sites corrigés (dont l'index d'action `$205` = −6
  de l'image 2 607).
- **Tables d'aiguillage « BRA.S »** : un aiguillage était classé « table de BRA.S » (forme sautée
  dedans) dès que l'instruction IMMÉDIATEMENT précédente n'était pas la lecture `MOVE.W T(PC,Dn),Dm`.
  Les interpréteurs de flux du portage intercalent `MOVE.B 1(A0),D0 ; ADDQ.W #2,A0` → table émise en
  trampolines mais lue comme offsets. Recherche sur 4 instructions : 3 aiguillages corrigés
  (`0x754BC`, `0x75C8C`, `0x7BAFC`) ; aucune table BRA.S véritable dans SFA3.

**Outils** : `diag.py` détecte aussi un PC hors du code (≥ `$400000`) en fin d'image (code 99) ;
`mame_test.py` : `patch_call` (redirection d'un appel externe, `JSR abs.L` ou `BSR.W`).

**État** : faute image 2 613 (démo, joueur 1). Un interpréteur de flux ajouté par le portage
(`0x7BA40`, commande de script `0x71EA8`) lit en `(A0)+` un sous-index aberrant (`$D60E`) ; le
flux est lu exactement comme sur PS2 (offsets d'octets vérifiés) → c'est le pointeur de flux ou
l'état qui diffère en amont. Reste aussi : les tables de pointeurs de code vers des fonctions
atteintes seulement par table (ex. `0x67FA78`, par perso) ne sont pas relogées (`is_code_ptr` ne
connaît que les cibles de `jal`).

### 76. Adresses de code converties à l'usage ; fin de code réelle ; drapeaux de comparaison rendus — cycle d'attraction complet

**Relocation statique des pointeurs de code abandonnée** : `mame_test.py` relogeait tout long des
données égal à un début de fonction. Faux positifs massifs : `0x00400000` (paires de mots de script
`0000 0040`) 257 fois isolé → scripts corrompus (sous-index `$D60E` de l'image 2 613). Nouveau
modèle, exact : **les adresses de code restent PS2 en mémoire** (données ET constantes `CODE_x` émises
par le code) et sont converties **à l'usage** : `JSR conv_An ; JSR/JMP (An)` (routine
`kernel68k.build_code_conv` en `$3FF000`, dichotomie sur une table triée PS2 → 68K en `$3E0000` :
12 174 débuts = cibles de `jal` + prologues connus + longs des données visant un prologue, un
`jr ra` ou un `lui rX,0x7000`). Adresse hors `[0x212B00, fin de code)` (déjà 68K) : inchangée.
Le noyau convertit l'entrée d'une tâche au lancement. (Coût : une dichotomie par appel indirect ;
le fork pourra fournir une table directe.)

**Fin de code réelle** (`code_end_translate`) : l'en-tête de ro3 (+12 = `0x393C40`) coupe la
dernière fonction (délai de branchement, `ld ra`, `addiu sp`, `jr ra` au-delà) → après son dernier
appel l'exécution tombait dans le vide. La traduction va jusqu'au `jr ra` qui suit (`0x393C54`) ; les
données gardent la frontière de l'en-tête (conversion des pointeurs). Upper et Hyper : non concernés.

**Comparaison rendue à l'appelant** : `MOVE.B $2C9(A6),D0 ; CMP.B $B(A6),D0 ; RTS` (ROM `$2AAB2`,
prédicat : l'appelant boucle sur BNE) perdait son `CMP` : la recherche de la dernière écriture de RES
avant `jr ra` s'arrêtait aux branchements INTERNES du calcul de retenue (absorbés). Corrigé :
24 prédicats de plus (surtout `CMP.W`) — la tâche d'attraction ne tourne plus en rond (image 5 594).

**Résultat** : cycle d'attraction complet (modes `$00`→`$32`, identiques au témoin, décalage ~300
images dû au mode `$26` du portage plus court), puis second tour. Faute image 14 167 (second tour,
mode `$26`) : objet `$BA80` (type `$37`, gestionnaire mips `0x1808E0`) dont l'animation démarre sur
une base fausse (`$373AD4`, suite de mots et non une frame ; commande de sprite impaire).

### 77. Cinq pertes silencieuses de traduction — attraction stable sur 40 000 images

Toutes trouvées en remontant des fautes du second tour d'attraction (mode `$26` du portage) :
- **Division longue du recompilateur récent** (mips `0x8E7E0`, `ADD.L D3,D3 ; ADDX.L D0,D0 ;
  CMP.L D2,D0 ; BCS ; SUB.L D2,D0 ; ADDQ.L #1,D3`) : `ADDX` perdu (motif `lw X ; andi 1 ; +Dn ; +Dm ;
  sw`, `addx_at`, case X `0x1154`) et `CMP.L` perdu (bloc de drapeaux exact en 32 bits : masque de
  signe par `and` avec un registre `lui 0x8000`, variante ajoutée à `exact_flags` ; +5 `CMP.L`).
  Quotient faux → base d'animation fausse (objet `$BA80`, image 14 167).
- **Domicile de D8 empilé sous sa forme mémoire** : `MOVE.L $87F0(A5),-(SP)` empilait le long à
  moitiés échangées, dépilé tel quel dans le registre prêté → `SUBQ.W` sur la mauvaise moitié (compteur
  d'enregistrements décrémenté un tour sur deux, image 14 184). Empilage/dépilage mot à mot en valeur
  réelle.
- **OU d'un mot à octets inversés en mémoire** : `$14(A5) |= swap16(D1)` (bit « arrivé » des objets de la
  variante B, mips `0x1848D0`) perdu → la variante B ne se terminait jamais (blocage image 15 798).
  `ROR.W #8,Dk ; OR/AND/EOR.W Dk,mem ; ROR.W #8,Dk` (symbole `bsmem`).
- **Copie mémoire → adresse indexée** : `MOVE.x d16(Am),d8(An,Dn)` non traduite — le corps entier du
  tampon circulaire des traînées (mips `0x1EF220`, `$8E94(A5)`) était perdu (15 sites) → objet de
  type `$22` sans animation (image 27 953).
- (§76 bis) comparaisons rendues à l'appelant : déjà décrites.

**Résultat** : aucune exception sur 40 000 images ; cycles d'attraction réguliers (~7 800 images),
variantes A et B du mode `$26` en alternance. Captures : logo, combat de la jungle, carte du monde,
écran du mode `$26`, second combat (tuiles des persos et de l'Anthology illisibles : banques du fork).

**Écarts de durée restants avec le témoin (ROM d'arcade)** : mode `$10` +287 images, `$18`/`$2E`
+210, `$1E` 1 image au lieu de 210 (le +210 de `$18` égale le manque de `$1E` : réaménagement du portage
ou traduction ?), `$26` propre au portage. À trancher par une trace PS2 de l'attraction.

### 78. Revue des écritures mémoire perdues — et le SON revient

Revue méthodique des écritures mémoire non traduites du code de jeu (`missclust.py`, zone du portage
`0x380000+` exclue par `MAXVA` ; `showmiss.py va` montre le MIPS et la traduction d'un manque) :
217 → 117. Faux manques repérés : entrées de tranche du recensement (`…b00`, contexte perdu) et
pré-décréments absorbés. Motifs ajoutés :
- copies vers l'absolu depuis une lecture indexée ou absolue, et vers l'indexé depuis l'absolu ou
  l'indexé ; **RAM QSound `$96xxxx` → `$618xxx` en correspondance octet EXACTE** (octets impairs, comme
  la ROM : port `0x96001F` = `$61801F` ; le XOR 1 envoyait tout sur l'octet pair) ;
- opération logique avec un masque en registre (`addiu -2 ; and` = `BCLR`) ; `ANDI` d'un seul bit
  réécrit en place ; opération logique entre deux lectures mémoire (via D0 sauvé) ;
- `SUBI`/`SUBQ` en place après extension à zéro (`andi $FFFF`) ; `SUB.x Dk,mem` ; addition en place d'une
  constante chargée par un `lui` seul (`ADDI.L #$FFFE0000`) ;
- accès indexés à déplacement 16 bits (`d16(An,Dn)`, lecture et écriture : adresse calculée dans An
  sauvé, octet XOR 1 à l'exécution) ;
- case du banc de registres adressée par `ori rX,rL(=lui 0x7000),off` (passe `slot_ori`) ;
- `CMPI #k,abs.L` (valeur absolue étendue à zéro ; instantané `SAB` : l'information de lecture
  absolue était effacée avant le traitement quand source = destination).

**Son** : la routine d'envoi des commandes vers QSound ne s'exécutait jamais — son test de la boîte
aux lettres (`CMPI.B #$FF,$61801F` : Z80 prêt) était perdu, le `BNE` suivant sautait toujours. Corrigé
(et adresses QSound exactes) : **la traduction joue la musique et les effets** (enregistrement MAME
`-wavwrite`, énergie comparable au témoin). Recensement : 98,6 %.

### 79. Vérification du son : protocole QSound conforme, une extension de signe en trop

Enregistrements MAME (`-wavwrite`, mixage interne) déterministes au bit près. Comparaison des
commandes envoyées au Z80 (écritures `$618001`–`$61801F`, points d'observation) avec le témoin :
- routage octet → port identique à la ROM (`$3130`–`$3166` : octet 0 du long → `$618007`, etc. ; notre
  rangement des longs à moitiés échangées donne bien les mêmes octets) ;
- **correctif** : `ori rX,zero,$FF05 ; sw → D1` était ré-étendu en signe (`MOVE.L #$FFFFFF05`) au lieu de
  `$0000FF05` (ROM `$3210`) → octets `$618007/$618009` à `FF` au lieu de `00` ; 6 sites ;
- séquences conformes : `FF00`, `FF05/00A0`, `FF07/002F`, `FF07/0001`, musique de démo `0101` au même
  point du cycle. Différences dues au contenu d'attraction du portage : pas de jingle d'intro `0103`,
  musique de stage `0024` (témoin `001A`) ; **à vérifier** : l'effet `0223` (table de sons du
  personnage, ROM `$3914`) demandé 71 fois toutes les 8 images par l'état 7 du joueur 1 pendant la démo
  (panoramique D2 décroissant) — une seule fois dans le témoin. **Écoute (utilisateur) : le son est bon** —
  titre puis combat de démo, rien ne manque ; l'effet répété est plausible (pas d'un personnage).

### 80. Partie jouable : crédit, menu, sélection, combat — et ses défauts

Banc : `mame/jeu.lua` (séquence d'entrées `INPUTS="début-fin:PORT:Champ;…"` fusionnées par champ, journal
des modes, captures `SNAPS`), `diag.py` accepte la même variable `INPUTS`. Comparaison systématique avec
le témoin (ROM d'arcade, mêmes entrées décalées) : états `$8000/$8004/$8008/$800C`, sous-état `$10`,
champs des joueurs ; écritures repérées par taps Lua (`install_write_tap` + `cpu.state["PC"]`), points
d'arrêt conditionnels (`bpset adr,cond,{logerror …;g}` posés à la 1re image, `-oslog`).

**Entrées et écran-titre** (première moitié) :
- correspondance des ports d'entrée (`HWREG`) : le portage range le mot d'entrée petit-boutiste, les
  octets sont croisés (`0x62195`↔`$804020`, `0x62194`↔`$804021`, `0x62190`↔`$804001`…) ; `nor` du
  portage = `NOT` de la ROM (`NOT.x Dn` / `NOT.x mem`), plus d'inversion ajoutée (`INPUT_INV` vide) ;
- « drapeaux déjà posés par l'opération en place » : faux après `BSET/BCLR/BCHG/BTST` et à un point
  de jonction (`TST.B $A9(A5)` du menu de l'Anthology perdu) ;
- table d'octets indexée absolue (`dtab` cps2) : adresse EXACTE calculée à l'exécution (XOR 1 de
  l'adresse, pas de l'index supposé pair : faute sur le caractère `$DA` de l'écran de sélection) ;
- lecture indexée périmée après l'écriture du registre d'index (`MOVE.B d8(An,Dk),Dn` puis `Dn` réécrit).
Menu de l'Anthology (curseur `$C001`, validation Bouton 1) → mode 2 (partie) atteint.

**Couche manette du portage** : la routine portée de la ROM `$1B096` (mips `0x891A4`) copie `$51A`→`$51C`
(mot précédent) puis appelle le **natif `0x381410`** (adresse construite `lui 0x57 ; addiu 0x1410 ; jalr`,
J1 en `JSR`, J2 en `JMP` terminal) qui écrit le nouveau mot `$11A` du joueur. Remplacé par deux talons
68K par site (A8, la structure joueur, n'est pas transmis) : `MOVE.B $62(A5),D0 ; MOVEQ #0,D1 ;
LSR.B #n,D0 ; ROXR.W #1,D1 ; OR.W $58/$5C(A5),D1 ; MOVE.W D1,$51A/$91A(A5)` (Start → bit 15).
`patch_call` traite aussi `JMP abs.L`/`BRA.W`. La routine post-balayage du noyau (qui écrivait trop
tôt, avant la copie : aucun front montant) est supprimée.

**Quatre défauts du traducteur trouvés en jouant** :
1. **Test de bit différé relu après réécriture** : `andi 0x80` d'un octet mémoire est gardé en
   symbole jusqu'au `Bcc`, mais l'octet est réécrit entre-temps (ROM `BCLR #7,$11A(A0) ; BEQ`) → le BTST
   relisait la nouvelle valeur : bit « Start maintenu » perdu, curseur de sélection insensible. Si
   l'écriture est le `BSET/BCLR/BCHG` du même bit → forme de la ROM (Z = ancien bit) ; sinon `BTST ;
   MOVE SR,-(SP)` avant l'écriture et `MOVE (SP)+,CCR` après (12 sites sûrs).
2. **A8 paramètre d'appel** : `LEA table,A8 ; JSR f` où `f` (mips `0xDBEF0`/`0xDBF70`, copie
   « `TST.W (A8) ; BMI ; MOVE.W (A8)+,(A0)+ ; BRA` ») lit A8 en entrée : le prêt de registre (§54)
   s'arrêtait à l'appel, la boucle perdait TST/copie/incrément et ne sortait jamais (blocage de
   l'intro des personnages). → **domicile mémoire de A8** (`$87E0(A5)`, long à moitiés échangées,
   variable `A8_HOME`) synchronisé aux bords des zones prêtées (`MOVEM` + `MOVE SR/CCR` : drapeaux
   intacts) ; une zone peut commencer à une tête de boucle placée avant le premier accès, et un retour
   de boucle INTERNE saute le code d'ouverture (`T.ZONE_OPEN`, `assemble.target`).
3. **`MOVE.L An,d(An)`** (registre rangé dans la mémoire qu'il désigne : chaînage
   « `ADDQ #8,A0 ; MOVE.L A0,-4(A0)` » d'une image d'animation construite en RAM, mips `0xB87A0`) :
   exclu de la forme cps2 (l'`EXG` écrasait la base) et perdu sans bruit → pointeur de commandes nul,
   répartiteur de script (mips `0x1020AC`) hors table, erreur d'adresse. Forme par D0.
4. (outil) `diag.py` ratait les erreurs d'adresse : l'IRQ2 continue de tourner pendant la boucle du
   talon, le PC vu en fin d'image n'y est plus. L'IRQ2 du noyau note le PC d'un talon interrompu
   (`$A00`–`$A80`) dans `EXCMARK` (`$6638F0`), que `diag.py` lit.

**Progression** (entrées : crédit, Start, Bouton 1 toutes les 200 images) : écran-titre → menu →
sélection (curseur, validation) → écran VS → intro des personnages (65 images, comme le témoin) →
« Round 1 / Fight » (`$12C` 1→4) → **combat** (`$8008=6`, `$800C=6`) → fin de manche au temps
(`$800C=8`). Attraction toujours stable (20 000 images sans exception). Graphismes des personnages et
de l'Anthology illisibles (banques de tuiles du moteur natif : à faire pour le fork).

**Défauts ouverts** :
- **le CPU (joueur 2) ne combat pas** : il avance de quelques pixels (`$812` 2E0→2B6) puis s'immobilise ;
  dans le témoin il bouge sans cesse et met K.O. le joueur 1 en ~900 images. Manche finie au temps,
  vies intactes → manche nulle (`$15A=1`, `$10D=$FF`) ;
- la fin de manche nulle ne progresse pas : l'état 8 attend `$10B == T[$138]` (bits posés par chaque
  joueur à la fin de sa pose, ROM `$341DC`), aucun joueur ne passe en pose de fin (`$x04` reste `0200`)
  — chemin « temps écoulé / nul » sans équivalent dans le témoin enregistré (qui finit par K.O.).

### 81. Boucle de jeu complète : de l'attraction au combat en deux manches, et retour

**Reproductibilité du banc** (piège majeur) : MAME réécrit l'EEPROM CPS2 (`~/.mame/nvram/sfa3ud/eeprom`) à
chaque sortie, et ce fichier est **partagé** entre la référence (ROM) et la traduction : chaque lancement partait
d'un état différent (durée de l'écran VS, réglages…). → EEPROM mise de côté (`~/.mame/nvram_sauvegarde/`) et
dossier rendu non inscriptible : chaque lancement part de l'EEPROM par défaut. Par ailleurs `-debug` décale le
minutage (fautes et aléa de l'IA à d'autres images) : un point d'arrêt se pose dans un lancement `-debug`
dont on relit d'abord la chronologie dans le même mode. **Fusion des entrées** (`jeu.lua`, `diag.py`) : un objet
champ Lua est recréé à chaque accès, la fusion par objet échouait (dernière écriture arbitraire) → clé « port|champ ».

**Défauts du traducteur trouvés en jouant** (tous génériques ; nombre de sites corrigés) :
1. `MOVE.L An,d8(Am,Dn)` (registre d'adresse rangé à une adresse indexée, long échangé par Dt) — perdu : le
   script d'IA (ROM `$30BBA`) ne sauvait plus sa position, le CPU recommençait sans fin sa 1re commande (3).
2. Drapeaux rendus à l'appelant aussi devant un `BRA` vers l'épilogue (`jr ra`) : test de sol
   `CMP.W $64(A6),D0` après la physique (mips `0x3649F8`) — les personnages traversaient le sol (5).
3. Immédiat de comparaison découpé en deux `addiu` (`-$8000 ; -$7FFF` = `CMPI.W #$FFFF`) : fin de liste
   de sprites perdue → erreur d'adresse en fin de manche (30).
4. **Encodage de `EOR Dn,Dm` inversé** (le champ registre de `EOR` est la SOURCE) : résultat rangé dans le
   mauvais registre — signe de la division logicielle faux, glissement des portraits de l'écran VS (65).
5. **A8 traversant un appel** : durée de vie découpée de part et d'autre des appels (le domicile `$87E0`
   reproduit exactement la case `0x1120`) ; zone refermée juste après sa dernière instruction quand un
   branchement extérieur vise l'épilogue ; `EXG` reconnu quand l'autre registre est A8 prêté. Code AJOUTÉ par
   le portage à l'écran VS (mips `0x1FA230` : ordonne deux objets par adresse) (zones +7).
6. **États de suivi périmés d'une fonction à l'autre** : `moved_d` (MOVE Dx,Dy récent), `moved` (lecture
   mémoire déjà copiée), `flags_set` — valables seulement tant que rien d'autre n'est émis. Ils supprimaient
   des `TST` (dont `TST.W D0` de `$AF50` : détection d'appui pour sauter l'écran VS) (77 + 37).
7. **Opérandes LONGS en mémoire (mode cps2, moitiés échangées)** : `ADD/SUB/OR.L d16(An),Dn`, `CMP(A).L`,
   `CMPI.L #v,d16(An)` opéraient sur la forme échangée → temporaire `MOVE.L ; SWAP ; op ; MOVEM` (drapeaux
   intacts). Gravité de l'intro des personnages (J2 tombait de 97 pixels par image) (182).
8. **Appels système PS2** (numéros lus dans `SLUS_213.17`) : `0x103410` ExitThread, `0x103420`
   ExitDeleteThread, `0x103430` **TerminateThread(tid)** — tue un AUTRE fil ; il était traité comme « finir la
   tâche courante » : en fin de partie, la tâche principale se tuait elle-même. → RTS (le portage a déjà
   marqué l'emplacement libre).
Aussi : test de bit différé relu après réécriture (§80), `MOVE.L An,d(An)` (§80).

**Résultat** (crédit, Start, Bouton 1 toutes les 200 images) : attraction → menu → sélection → écran VS (glissement
des portraits, saut par bouton ; chronologie = témoin +200 images exactement) → intro des personnages → manche 1
(K.O. par le CPU, IA active : déplacements, sauts, coups) → manche 2 → fin de match → écran de continuation →
retour au titre → attraction. **20 000 images sans exception**, avec et sans entrées. Durées des manches proches
du témoin (aléa de l'IA). Reste : graphismes des personnages et de l'Anthology (banques du moteur natif).

### 82. Sprites des banques dans le banc MAME : les personnages s'affichent

**Correction du §45/§48 (vérifiée dans le code natif `0x1D2DC0` et le vidage `ee_std`)** : l'**emplacement de
banque** d'un objet est dans les bits 13-15 de **Y** (là où la ROM met les bits 16-17 du code), pas de X.
X >> 13 reste la **priorité CPS2** (le moteur natif dessine en deux passes : priorités 0-6, puis 7 seule).
Emplacements (table `$59C1B8` par joueur, vidage) : 0 = `e254` (communs), 2/3/6/7 = joueurs 1-4 (banque du perso,
table `$59C0B0` : `0x102` = e258 Ryu…), 4 = fichier « graphismes » de la paire chargée avec l'animation
(`0x383700`/`0x3837D0`, ex. 457), 5 = `e312` (32×32). Le marqueur de fin du portage est `X = Y = $8000` (code et
attributs quelconques) ; la liste est construite en plusieurs fois (plusieurs marqueurs par image).

**Banques réorganisées** : une banque est un sous-ensemble des tuiles CPS2 rangé AUTREMENT (continuité
`code+1` ≈ 55-65 %) ; les objets multi-blocs suivent l'arithmétique CPS2 (`local + x + 16y`) dans la numérotation
LOCALE. Le banc ne peut donc pas convertir un objet d'un bloc : il l'**éclate en tuiles 16×16** (formule de
rendu CPS2, retournements compris) et convertit chacune. Vérifié hors ligne : la liste réelle du PS2 (`ee_std`)
et la liste brute de la traduction se rendent proprement avec cette logique.

**Outils** : `banques.py` (venv : numpy) — tables « tuile locale → code CPS2 » par CONTENU dans la ROM `sz3.13m-20m`
(98-99,7 % retrouvées ; parmi les tuiles identiques, celle qui prolonge la suite), `banques.py tout` écrit
`work/mame/banques/f<N>.bin` et `carte.txt` (perso → banque, pointeur d'animation `$BE48` → fichier graphique).
`mame/banc_sprites.lua` (chargé par `jeu.lua`, `SPRITES=0` pour le couper) : prise d'écriture sur `$700000-$70FFFF`,
**copie des mots écrits par le jeu** (la plage `$700000` est en ÉCRITURE seule dans MAME, et l'éclatement repart de
la liste BRUTE à chaque marqueur), éclatement, écriture de la liste convertie. `X_DATA.BIN` extrait de l'ISO locale
(`7z`, lecture seule) dans `work/xdata/`.

**Défaut du traducteur trouvé au passage** : **moitié haute d'un registre D** (case `+2`, `lh/sh $112E` = mot haut
de D2) — forme des `MOVE.L` découpés par le recompilateur (constructeurs de listes d'objets : `MOVE.L (A0)+,D2`
charge code:attributs ; `OR`/`ADD` sur le mot haut) — traitée comme le mot bas : le code de tuile était écrasé
par l'attribut. → pseudo-instructions `SWAP Dn` autour du groupe (72 sites).

**Résultat** : combats affichés avec les vrais sprites (Ryu, Adon, M. Bison, Sodom…), boule de feu, traînées, herbe
de premier plan ; 20 000 images sans exception (attraction et partie), boucle de jeu complète intacte. Restent :
tuiles de plan fausses (haut de l'écran : `banc_plans.lua`), emplacements 1/5/6/7 non câblés dans le banc,
palettes chargées par le natif à vérifier, et pour le fork la mise en œuvre du schéma de banques (§48, avec Y).

### 83. Plans, HUD, chrono et bannières : l'écran de combat complet

**Plans (scroll1-3)** : les cartes de tuiles du portage contiennent des indices LOCAUX — scroll1/2 dans la mémoire
de tuiles de décor `e256` (MWo3 décompressé, `ctx+$34`, linéaire 4 bpp), scroll3 dans `e312` (32×32). Tables par
contenu : `banques.py plans` → `plan1.bin` (8×8) et `plan2.bin` (16×16), `banques.py 312` → `f312.bin`. Code MAME =
indice ROM − début du quart du plan : scroll1 `−$20000`, scroll2 `−$10000`, scroll3 `−$4000`. `mame/banc_plans.lua`
convertit les mots de code des cartes (bases suivies par les écritures `$804102-7`).

**Emplacements de sprites** : 1 = `e256` (objets du HUD, la ROM y met `ORI #$2000`), table `plan2`. **Correction du
§82** : 6/7 ne sont pas les joueurs 3/4 mais des conteneurs « de classe » réaffectés à chaque image (documentation
du patch widescreen). La liste est construite par morceaux et garde des RESTES d'écrans anciens (trame de l'écran
VS en plein combat) : le banc ne retient qu'une entrée dont X a été écrit dans les 3 dernières images.

**Défauts du traducteur corrigés** :
- **long rangé dans l'ordre naturel** : le portage assemble `SWAP(Dn)` dans un registre MIPS temporaire puis le
  range (`lw ; lui $FFFF ; and ; srl 16 ; andi` + `lw ; andi ; sll 16` → `or` → `sw`) — c'est un `MOVE.L Dn,(An)`
  SANS échange (ROM `$21982 MOVEM.L D0-D1,(A2)`, constructeurs du HUD). Les rangements étaient perdus (20 sites).
- **aides du recompilateur** (hors du code traduit, talons RTS jusqu'ici) : `0x570360` = `MOVEM.L masque,-(SP)`,
  `0x5706C0` = `MOVEM.L (SP)+,masque` (masque au format prédécrément, bit 15 = D0, à inverser), `0x570A20` =
  `ANDI #imm,CCR`, `0x570D00` = `ABCD` d'un octet sur adresses PS2 (octet 68K = adresse XOR 1) : forme registre
  (`ABCD Dy,Dx`, arguments = cases des registres) ou mémoire (`ABCD -(A0),-(A1)` sur (adresse^1)+1, drapeaux
  préservés autour pour la chaîne de retenues). La conversion binaire→BCD du chrono (`$BA54/$BA58`) était vide :
  **chrono figé à « 00 »**. Les autres cibles `0x57xxxx` (`0x571A00`, `0x5738D0`…) sont des fonctions natives.
- **masque 32 bits `lui ; ori` sur un registre D** : `ANDI.L #$F000F000,D4` de la copie de palette (luminosité)
  était perdu → anciennes couleurs mêlées : **bande sombre des bannières absente**. Seul `$F000F000` est accepté
  (`MASQUES_OK`) : les autres (`ANDI.L #$03FF03FF` / `ORI.L #$E0002000` des constructeurs du HUD…) cassent l'affichage
  du banc — à étudier (`MASQ_OK=tous` pour essayer).
- **`ADDA.W T(PC,Dn.W),An`** (table de mots indexée ajoutée à un registre d'adresse) : perdu. Choix de la variante
  de palette de « ROUND » selon le décor (`$100(A5)`, table `$588BF0`) — 6 sites. La couleur des lettres dépend du
  décor (décor de Cody : vert ; décor de R. Mika : données rouges). **À confirmer sur la ROM d'origine dans le décor
  de R. Mika.**

**Banc de sprites : écritures brutes détournées** : le jeu construit parfois sa liste sur deux images ; MAME
affichait alors la page en cours d'écriture (codes LOCAUX bruts → HUD et bannière en tuiles parasites, images
5545-5560 de la partie de test). La prise d'écriture range le mot brut dans la copie fantôme et rend à la place le
mot CONVERTI déjà en place : la mémoire d'objets ne contient plus que des listes converties.

**Résultat** : HUD complet (barres de vie et de garde, noms, A-ISM, jauges), chrono qui décompte (96 → 78, 99 au
round 2), compteurs de coups, bannières « ROUND 2 » / « FIGHT » / « PERFECT » avec bande sombre ; 20 000 images sans
exception (attraction et partie). Restent : score non vérifié (J1 ne marque pas dans la partie de test ; l'addition
passe désormais par `ABCD`), blocs faux dans le décor par moments (plans), masques 32 bits du HUD, `JOIN IN` /
`MAX` / `CHARGE` absents de la barre du bas.

### 84. Couleurs des bannières vérifiées, tous les masques 32 bits, portraits (zone dynamique de l'emplacement 1)

**Couleur de « ROUND » = fidèle à l'arcade** : la ROM fait `MOVEA.L #$35F414,A0 ; MOVE.W $100(A5),D0 ; ADDA.W
T(PC,D0.W),A0` (`$7CB98`, table par décor `$7CBAC`, palettes `$35F114`/`$35F414` = tables A/B du portage
`0x6742B0`/`0x6745B0`) : décor de Cody (+`$2C0`) vert, décor de R. Mika (+`$2A0`) rouge. Séquence des écritures
identique (A au début du round, B en fin, A au suivant). Le « gris » vu chez nous = lettres rouges TRAMÉES en
damier (pseudo-transparence de l'arcade, identique dans la référence) sur le décor clair.

**Masques 32 bits** : tous acceptés (`ORI.L #$E0002000` / `ANDI.L #$03FF03FF` des constructeurs du HUD compris) ;
la casse attribuée au §83 venait du banc (pages à moitié écrites, corrigé). 52 sites ; 20 000 images sans exception.

**Portraits (écran de présentation, écran VS)** : les objets sont émis (emplacement 1) mais avec des codes LOCAUX
dans `$0000-$157F` — zone qui ne contient PAS de tuiles 16×16 dans e256 (données 8×8 de scroll1). Les données du
portage elles-mêmes portent ces codes (ex. `$0BB0:$0700` à `0x5D968C`, portrait de Ryu) : le portage REMPLIT cette
zone à l'affichage de ces écrans. Relevé (Ryu J1, R. Mika J2) : `local i = ROM $16C00 + i`. `banques.py plans`
remplit ainsi les trous de `plan2` sous `$1580` → portraits corrects. **Descripteur des fichiers graphiques** :
`[[0x1DC040]]`, entrées de 12 o (`+$14` type, `+$16` fichier, `+$18` destination ; emplacement k = entrée k+1),
recopiées chaque image dans `ctx+$30..$4C` (`0x1D05E8`) ; SFA3 = e254/e256/…/e312 ; chargement initial
`FUN_1C94A0`. **Non résolu** : le code qui remplit la zone dynamique et son étendue — les bandes latérales de
l'écran de présentation (codes `$28A0…`) attendent aussi `ROM $16C00 + i` (texte `$194A0`) alors qu'en combat
`$1580+` est la partie statique de e256 (HUD). Il faut un vidage EE pris sur l'écran de présentation / VS.

### 85. Portraits et bandes de l'écran de présentation : un `ADDI.L` perdu (correction du §84)

**Vidage PS2 de l'écran de présentation** (état PCSX2 fourni par l'utilisateur, RAM EE + scratchpad) : l'emplacement 1
y contient e256 **inchangé** (`ROM = local + $15600` dès `$1600`) — il n'y a PAS de zone dynamique. La liste d'objets
écrite par le jeu (`0x910000`, pages d'objets = RAM `$FF0000` + `$10000`) porte `$21B0` pour le portrait de Ryu et
`$3EA2…` pour les bandes « STREET FIGHTER ALPHA 3 », là où la traduction écrivait `$0BB0` / `$28A2`. Même objet
(`$FFBD00` ↔ `0x90BD00`, même pointeur de définition `$1C` = `0x5D94B4`), même commande (`$0008` → entrée 4 de la
table des constructeurs `$58BBA0`), même constructeur (`0xFE140`) : il y fait `lui r3,$1600 ; addu r4,r4,r3`
(`0xFE6F8`) = **`ADDI.L #$16000000,D1`**, perdu par le traducteur (constante 32 bits chargée par un `lui` seul,
ajoutée à un registre D : 10 sites — `+$1600` dans 3 constructeurs, `+$180`, `+$10`, `+$8`…). Corrigé ; la règle
« zone dynamique » du §84 (remplissage de `plan2` sous `$1580`) n'était qu'une compensation et est retirée.

**Outils** : un état PCSX2 se lit sans y toucher (copie, puis `eeMemory.bin` / `Scratchpad.bin` / `Screenshot.png`
extraits du zip zstd). Descripteur des fichiers graphiques `[[0x1DC040]]` confirmé (SFA3 : e254/e256/…/e312/e313).

### 86. Blocs dans le décor au K.O. : `MOVEA.W An,Am` perdu (allocateur d'objets)

**Symptôme** : au K.O., bande de blocs bleus/noirs dans le décor (plans). Vidage PS2 de l'écran « PERFECT » (état
PCSX2 n° 2 de l'utilisateur) : rien de tel, bandeau « KNOCK OUT » seul. **Cause** : les bases des plans sont des
POINTEURS PS2 32 bits rangés à `$FF3F30-$FF3F5F` (`$BF30(A5)`, déplacement signé ; PS2 : `0x920000` / `0x934000` /
`0x928000` / `0x92E000` / `0x92C000` = `$900000` / `$914000` / `$908000`…), copiés chaque VBL vers les registres
CPS-A (« registre CPS-A élargi » : `MOVE.L ; LSR.L #8 ; MOVE.W`). Chez nous, trois d'entre eux étaient ÉCRASÉS par un
objet rempli en `$FF3F00` : l'appelant de l'allocateur d'objets (mips `0x336358`) fait `MOVEA.W A4,A3` puis
`MOVEA.W A4,A2` (`lh` case A4 ; extension de signe ; `andi $FFFF` ; `sw` case Am + conversion d'adresse
`+$900000`), forme qui n'était pas traduite → A2/A3 périmés. **Corrigé** : motif reconnu → `MOVEA.W An,Am`
(+ `movea_fixup`), 29 sites. Conséquence visible : le déroulé de la partie de test change (l'adversaire devient
Adon) ; K.O., citation du vainqueur et bannières propres ; 20 000 images sans exception.

**Barre du bas (reste)** : le PS2 affiche « LV3 GO! » ; chez nous les jauges sont émises (`$3C90…`) mais pas le
texte/niveau (`$3C92`, `$3C96`, `$3C98`) — la jauge de super de J1 semble ne pas se remplir (à étudier).

### 87. Jauge de super et barre du bas : `BTST` rendu à l'appelant

**Symptôme** : barre du bas sans « LV3 GO! / MAX » (PS2 : « LV3 GO! » dès le début du combat). Champ : mot `+$11E`
de la structure joueur (68K), plafonné à `$90`. Référence : remplissage de 2/image en début de combat (ROM `$9B96`,
si `$102(A5)` = 0, joueur actif, `$F0` nul). Chez nous : seulement +1 par coup reçu (`$11F` = 18 à l'image 6500).
**Cause** : le portage conditionne ce remplissage par une petite fonction (`0x57A4B0` : `lb $C1A5(A5) ; andi $10 ;
sw RES ; jr ra` = `BTST #4,$C1A4(A5)` rendu à l'appelant, suivi d'un `BEQ`). Le test en attente `btst` n'était pas
géré par `flags_to_caller` (seulement tst/cmp) → fonction réduite à `RTS`, `BEQ` sur des drapeaux quelconques.
**Corrigé** : `btst` émis devant le RTS ; 67 fonctions concernées. Jauges pleines « LV3 GO! » puis « MAX » comme le PS2.

### 88. Score affiché, flash de palette retiré (états PCSX2 n° 2 et 3 : score 0 / 3 300)

**Score** : long BCD à `$FF8510` (`+$110` de la structure joueur ; PS2 `0x908510` = `$00003300` dans l'état n° 3,
même disposition que chez nous). Partie de test offensive (J1 avance + frappe toutes les 12 images) : le score
s'accumulait bien en RAM mais l'affichage restait « 0 ». **Cause** : la conversion en chiffres (mips `0xDBFF0`)
fait `ROL.L #4,D0` à chaque chiffre (`sll 4 | srl 28` sur un `lw` de la case D0) ; `rot_of` ne gérait que les
rotations 8/16 bits → rotation perdue, toujours le chiffre des unités. **Corrigé** : rotations 32 bits (≤ 8 ou
complément ≤ 8) ; 15 sites (`ROL.L #4` du score/chrono, `ROR.L #8` d'un traitement octet par octet…).

**Écran tout blanc en pleine partie** (même partie offensive) : la base de palette (`$BF54(A5)` → `$80410A` à
chaque VBL, rechargée depuis `$BF40`) restait sur la palette du flash (`$9280`). Le test de retour compare
`$BF40` à l'adresse PS2 `$0092C000` : `CMPI.L` gardait la constante PS2 alors que la mémoire contient l'adresse
68K marquée (`$0190C000`). **Corrigé** : dans `enc_cmp` (long mémoire contre immédiat), une constante adresse
est convertie comme dans `MOVE.L #const` (3 sites, tous sur `$BF40`). Résultat : score 1 700 → 10 200 (retenue
BCD), « FIRST ATTACK », « COUNTER HIT », manche gagnée par J1, palette normale.

### 89. Visualiseur d'état PS2 dans MAME : 27 décors vérifiés contre les captures PCSX2

**États fournis par l'utilisateur** (mode training de l'Anthology, Ken contre Sakura) : les 26 décors accessibles
+ la carte du monde « NEXT STAGE » ; copiés dans `work/etats_ps2/` (RAM EE, scratchpad et capture extraits dans `ee/`).

**Outil** : `visu_rom.py` construit `roms_vis` (programme 68K minimal : `MOVE #$2700,SR ; BRA.S *`) et `mame/visu.lua`
injecte un état et laisse MAME rendre l'image — c'est exactement la conversion qu'aura à faire le fork :
- RAM de jeu PS2 `0x900000-0x90FFFF` → `$FF0000` (mot à la même adresse) ;
- bases CPS-A = pointeurs PS2 32 bits du portage à `0x903F44…` (scroll1, scroll2, scroll3, défilement de lignes,
  palette ; `0x92xxxx` → `$90xxxx`) ; registres de défilement/vidéo `+0x62118…` → `$80410C…` ; couches `+0x62146` →
  `$804166` ; palettes `+0x62150` → `$804170` ; **décalages d'objets `+0x62184…` → `$400002…`** ; banque d'objets
  `+0x621A0` → `$8040E0` ; base de palette écrite en dernier (déclenche la copie) ;
- mémoire vidéo `0x920000-0x94FFFF` → `$900000` (codes de plans convertis par `banc_plans.lua`) ;
- liste d'objets du moteur natif = scratchpad `0x2000` ; **fin = PREMIER marqueur** `X=Y=$8000` (au-delà : restes
  de listes plus longues des images précédentes, ex. logo du titre) ; convertie par `banc_sprites.lua`.

**Résultat** : les 27 rendus correspondent aux captures (décors, personnages, HUD, palettes, carte du monde).
Couverture des tables : seuls manquent des graphismes RETOUCHÉS par l'Anthology, absents de la ROM arcade —
chrono « ∞ » du training (`$3C1F/$3C3F`, emplacement 1), 16 tuiles 8×8 du décor de Ryu (`$4BE6…`), 4 tuiles 16×16
de Charlie, une tuile 32×32 de la variante de Karin (`$D4E`, carré gris) — non reproductibles dans le banc (le fork lit
e256/e312 directement). À voir : deux plaques blanches en bas de l'écran sur le décor de Rolento (priorité ?).
Différence attendue d'une image sur les poses : la capture PCSX2 montre la liste précédente.

### 90. Manche bloquée au « TIME OVER » : long rangé octet par octet (bswap32), drapeaux de SUBI en place

**Symptôme** (partie offensive longue, 60 000 images) : contre Chun-Li, le chrono atteint « 00 » et la manche ne se
termine jamais. Reproduit en forçant le chrono à 1 (`$FF8109` référence / `$FF8108` traduction) : référence = mode
`$800C` 8 → `$A` à l'image 4607 ; traduction bloquée en 8. Le mode 8 attend que les deux personnages aient fini leur
pose de fin (ROM `$29E0C` : `BSET D0,$10B(A5)` par joueur). **Cause** : la pose « temps écoulé » (ROM `$2ACA0`) range
le nouvel état par `MOVE.L D1,$4(A6)` ; le portage, pour ce champ lu OCTET PAR OCTET, construit `bswap32(D1)` (4
masques/décalages) puis `sw` — forme perdue → état jamais posé. **Corrigé** : `bswap32_or` (évaluation symbolique de
l'arbre de `or` sur une valeur test) → rangement : octets PS2 = Dn gros-boutiste, mémoire 68K = octets PS2 XOR 1, donc
chaque moitié à octets inversés (`ROR.W #8 ; SWAP ; ROR.W #8 ; SWAP`, puis restauration) — 3 sites. Attention : le
portage a sa propre numérotation d'octets dans ces structures (ROM `$6(A6)` lu en `$7`, `$102` en `$103`…), d'où cette
forme et pas un `MOVE.L` naturel. Au passage : `SUBI` en place suivi d'un test (`SUBI.W #$48,$11E(A0) ; BPL`) émettait un
`CMPI` parasite (mauvaise condition) → `last_sub` (11 sites). Résultat : « TIME OVER », marque « T », manche suivante ;
3 × 20 000 + 60 000 images sans exception.

**Connu, non corrigé** : `LEA $129(A6),A0 ; ADDA.W D0,A0 ; MOVE.B D0,(A0)` (tableau des résultats de manche) — octet
écrit avec une inversion fixe (`$0001(A0)`) alors que la parité dépend de D0. **Natif `0x571900`** (nettoyage des
directions opposées, table `$59C030`) : identité en pratique avec un vrai joystick. Outils : entrées périodiques
`debut-fin%periode,duree:PORT:champ` (jeu.lua, diag.py), image programme déchiffrée `work/cps2/sfa3ud_prog.bin`.

### 91. Gen bloqué en l'air (manche sans fin) : fusion de branchements de l'assembleur

**Symptôme** (partie offensive longue) : contre Gen, après un saut près du bord, Gen ne retombe jamais (Y décroît
sans fin), la manche ne se termine plus même au « TIME OVER ». **Cause** (assembleur, pas traducteur) : la fusion
« Bcc qui saute par-dessus un saut inconditionnel → branchement inverse » absorbait un saut qui était AUSSI la cible
d'un autre branchement. Site : sous-état 4 de Gen (ROM `$570AA` : `JSR $2AA08 ; BHI en l'air ; sinon atterrissage`) ;
le MIPS fait `bltz C → atterrissage ; bne RES → en l'air ; sinon atterrissage` ; après fusion du `bne` avec le saut
d'atterrissage, la cible du `bltz` se résolvait sur l'élément suivant (le saut « en l'air ») → atterrissage seulement
en cas d'égalité exacte. **Corrigé** (`assemble.py`) : pas de fusion si le saut est la cible d'un branchement — 14
fusions refusées. Méthode : trace ordonnée des PC (prise en lecture sur l'espace `opcodes`, A6 = joueur) dans le cas
normal et le cas bloqué ; attention, A6 vaut `$00FF8800` (LEA) ou `$FFFF8800` (MOVEA.W). 3 × 20 000 + 60 000 images
sans exception ; la partie longue enchaîne Guy, Cody, Sakura, Sodom, Gen, classements, attraction.

**Reste** : rectangle pâle derrière les personnages sur le décor de Gen quand la caméra est au bord droit.

### 92. Objets du décor figés (rectangle pâle chez Gen) : mot à octets inversés lu en mémoire ; EORI traduit en BCHG

**Symptôme** : sur le décor de Gen, caméra au bord droit, un rectangle pâle derrière les personnages (le PS2 montre
des carcasses suspendues). Les plans et les registres de défilement sont identiques au PS2 (visualiseur §89) ; la
différence vient des objets du décor (`$FFC300…$FFC7FF`, emplacement 1) : chez nous tous restent en routine 0, avec le
même pointeur d'animation (`+$1C`), et dessinent une image par défaut. **Fausse piste écartée** : le fichier 289
chargé à `$A04000` (`assets_natifs.FIXES`) n'est PAS propre au décor — identique octet pour octet dans les 31
sauvegardes PS2 (tous décors).

**Cause 1** (traducteur) : l'apparition des objets du décor (ROM `$1A5E8`, table par décor `$100(A5)`) fait
`MOVE.W (A1),$2(A4)` (routine/sous-routine). Le portage, pour ce champ, range `bswap16` du mot lu
(`lh ; andi $FF ; sll 8 | lh ; andi $FF00 ; sra 8 ; or ; sh`) — forme perdue → routine jamais posée.
**Corrigé** : `bswap16_mem` (évaluation symbolique 64 bits de l'arbre sur une valeur test, deux feuilles `lh d(An)` de
la même adresse) → `MOVE.B d+1(As),D(Ad) ; MOVE.B d(As),D+1(Ad)` (aucun registre de travail) — 1 site. Les objets
s'animent (danseurs du décor de Chun-Li, carcasses de Gen) ; plus de rectangle pâle.

**Cause 2**, révélée par la divergence de la partie longue : Chun-Li, au mur gauche, enchaîne des sauts de mur et
monte sans fin (sous-état `$0A`/`$02`), « TIME OVER » bloqué. ROM `$2861A` : `EORI.B #1,$B(A6) ; BEQ` (inverser le
sens, puis négation des vitesses selon le RÉSULTAT). Traduit `BCHG #0,$A(A6) ; BEQ` : Z = ancien bit → condition
inversée, rebond vers le mur. **Corrigé** : quand RES reçoit le résultat d'une opération logique en place émise sous
forme de bit (`BSET/BCLR/BCHG`), `TST.B` avant le branchement (une quinzaine de sites ; les formes « Z = ancien bit »
de la ROM passent par un BTST différé, non touchées).

Outil : `force_stage.lua` (`FS0/FS1/STG` : remplace l'écriture de `$FF8100` → décor imposé, `SUIVI=1` journal des
décors) ; ex. `STG=22` sur la 2e manche de la partie offensive → décor de Gen à l'image 14196. Méthode : comparaison
des structures d'objets (vidage RAM ↔ sauvegarde PS2), prise d'écriture sur `$FFC400` (créateur `pc`), trace des
blocs exécutés avec A6 = objet (seul le dessin tournait).

### 93. Test du câblage des commandes (arcade ↔ traduction) ; provocation sur tout nouvel appui (BTST rendu à l'appelant)

**Outil** : `mame/commandes.lua` + `untranspile/commandes.py`. Partie à 2 joueurs (6 pièces — la ROM arcade du banc
demande 2 pièces/crédit —, Start J1 puis J2 répétés jusqu'à ce que le bit « en jeu » soit posé : `$A8(A5)` ROM /
`$A9(A5)` traduction ; boutons de sélection tant que le combat n'a pas commencé). T0 = combat stable (mode `$800C` = 6,
états `$4 = 2` et `$7 = 2` pendant 30 images). Puis 21 actions pour J1 et pour J2, une toutes les 90 images : 6 boutons,
bas + 6 boutons, sauts (neutre / avant / arrière / + B6), marche avant / arrière, quart de cercle avant + P, dragon + P,
quart arrière + K (les champs MAME : `IN0` directions et B1-B3, `IN1` B4-B6, sauf `P2 Button 6` sur `IN2`). Journal
par image, NORMALISÉ dans la numérotation ROM (octets d'état `$4-$7` échangés par mot dans la traduction, X/Y en
`$12/$16` au lieu de `$10/$14`), mot d'entrées `$11A`, tours de jeu (écritures de `$51C`). Le comparateur résume chaque
action en suite d'états (états d'UNE image ignorés) + déplacement X/Y.
```
REF=1 OUT=ref.txt mame sfa3ud -rompath roms    ... -autoboot_script commandes.lua
      OUT=tr.txt  mame sfa3ud -rompath roms_tr ... -autoboot_script commandes.lua
commandes.py ref.txt tr.txt
```
**Câblage physique** : bon (mot `$11A` identique : `$0100` B1, `$0008` haut…). La couche manette native (§80) et la
copie `$51A → $51C` (ROM `$1B096`) sont conformes. **Piège du test** (pas un défaut) : la traduction n'accepte Start
que sur l'écran de sa propre machine d'états de menu (variables Anthology `$C010/$C012(A5)` = nouveaux appuis
J1/J2 | `$8000` si Start, ROM du portage `$FB86` ; l'entrée en jeu `BSET #0/#1,$A9(A5)` en dépend) : un Start trop
tôt est perdu → J1 reste « joueur console » (`$125` ROM = 1, traitement des entrées sauté, Ryu joue seul).

**Défaut corrigé** : ROM `$2E0CC` `MOVE.W $378(A6),D0 ; BTST #15,D0 ; RTS` (nouvel appui sur Start → provocation,
état `$0E`, coup `$0C`) traduit `MOVE.W ; RTS` : le `andi $8000 ; sw RES` en fin de fonction (`pend = btst_dn`)
n'était pas rendu à l'appelant → TOUT nouvel appui déclenchait la provocation (poing faible de Ryu…).
`flags_to_caller` accepte `btst_dn` → `BTST #b,Dn` devant le RTS (5 sites). Résultat : 35 actions sur 42 identiques à
l'arcade ; 4 marches plus courtes (performance, ci-dessous) ; 3 avec un état transitoire de 2 images en plus (cadence).

**Reste (performance, pas câblage)** : en vitesse « turbo » le jeu fait 4 tours de logique pour 3 images quand il
reste du temps processeur ; arcade 133,3 % de tours/image, traduction 125,6 % (code plus lourd) → marche ~10 % plus
courte sur une même durée. Le banc MAME ne permet pas d'accélérer le 68K par script ; pour le fork FBNeo :
surcadençage du 68K (ou réduire le coût des séquences de conversion d'adresses / échanges de longs).

### 94. Plantage à l'image 50 153 : entrées de table d'aiguillage hors de portée 16 bits (assembleur)

**Symptôme** (partie offensive longue, après §93) : instruction illégale (vecteur 4 → talon `$A08`), joueur 2 =
personnage `$1C`. **Méthode** :
- les captures « PC sous `$400` » ne finissaient jamais : `pc=$10` vu à l'entrée du talon est l'adresse du VECTEUR 4,
  pas une destination de saut ;
- la capture a été déclenchée à l'entrée du talon (`$A00-$A7F`), avec une prise sur l'espace `opcodes` posée à
  l'image K−1 seulement (rapide) ;
- dernière instruction : `MOVE.B $85(A6),D0 ; MOVE.W T_5995C0(PC,D0.W),D1 ; JSR T_5995C0(PC,D1.W)` (ROM `$677FC`),
  index 0 (valide), saut au milieu d'une autre routine (`$777AC`).

**Cause** : `assemble.py` écrivait chaque entrée en `(cible − table) & $FFFF` sans contrôle ; l'entrée 0 vise une
routine commune (mips `0x3CE600` = ROM `$2A7EA`) à plus de 32 Ko → débordement silencieux.

**Corrigé** : les entrées hors de portée passent par un tremplin `JMP abs.L` rangé après la table (l'entrée vise le
tremplin, la taille de la table en tient compte ; calcul itéré avec la mise en page). **29 entrées** concernées dans
tout le module (`mame_test.py` les compte). 3 × 20 000 + 60 000 images ; test des commandes inchangé (35/42, §93).

### 95. Format des frames de sprites de l'Anthology (lu dans la routine d'affichage)

Pour la conversion des persos MAX (étude parallèle `sfa3max-psp-widescreen/work/re/frames289`), détail dans
`docs/FRAMES-Anthology.md` :
- **u16 TYPE en tête**, aiguillage par la table `0x58BC30` (16 entrées) ;
- frames serrées au mot près, réalignement `(A0+3) & ~3` avant le pointeur ;
- type 2 (14 421 frames) = `type, T = total des tuiles 16×16, n−1, [align], ptr fichier 289, n × (code, attr)` ;
- types `12/18-1E` = frame vide (garde de Ryu en fichier `0x4DB32A`, précédée d'une frame vide en `0x4DB328`).

### 96. Bonne ROM de référence ? Phoenix `sfa3ud` = USA 980904 d'origine ; l'Anthology suit la 980904

Question de l'utilisateur : les tests partent-ils de la bonne ROM ? Rappel des rôles :
- la traduction (`roms_tr`) ne garde de `sfa3ud` que les graphismes, le son et le matériel ; le programme est
  entièrement celui du PS2 traduit ;
- la ROM `sfa3ud` sert de référence (désassemblage, `REF=1` du test des commandes).

**Phoenix ↔ original** (`sfa3u.zip`, `sz3u.03c/04c` + tables `sz3ux`) : chaque mot de `sz3ud.03c/04c` est soit le mot
d'origine DÉCHIFFRÉ (code, 467 635 mots), soit le mot BRUT (données lues hors espace « opcodes », 56 614 mots).
Seules exceptions : 39 mots autour de `$922` (retouche de démarrage des Phoenix). `sz3.05c..10b` identiques à
l'européenne 980904 (`sfa3.zip`).

⚠ `work/cps2/sfa3_prog.bin` (§25, outils `verify/e2e/diverge`) est l'original ENTIÈREMENT déchiffré : ses données
de la zone chiffrée (`$000000-$0BFFFF`) sont fausses (112 843 octets). Pour les tables de données, utiliser
`sfa3ud_prog.bin`.

**Révision de l'Anthology** (`untranspile/revision.py`, `SFZ3JR2=` dossier de `sfz3jr2dl`) : 250 fonctions du module
traduites, cherchées dans le code USA 980904 et Japon 980629 :
- 237 également proches ;
- 13 plus proches de l'USA (ex. mips `0x2548B0`, `0x313BA0` : 100 % contre 95 %) ;
- 0 plus proche du Japon.

⟹ le module `ro3_usa` suit la révision 980904 ; la Phoenix est la bonne référence.

### 97. Octet via un registre d'adresse de parité inconnue (après `ADDA Dk,An`) : adresse exacte à l'exécution

**Défaut connu depuis §90** : ROM `LEA $128(A6),A0 ; ADDA.W D0,A0 ; MOVE.B D0,(A0)` (tableau des résultats de
manche). Le MIPS calcule `A0 = A6 + $129 + D0` puis `sb 0(A0)` ; l'octet PS2 X est en 68K à X XOR 1. La traduction
figeait `MOVE.B D0,$0001(A0)` (juste si A0 impair seulement) → mauvais octet pour les manches d'index pair.

**Corrigé** (`byte_after_adda`, même recette que `byte_index_exact` §66) : après un `ADDA.W/L Dk,An` et jusqu'à la
réaffectation de An (LEA / MOVEA) ou une rupture, tout accès OCTET `d16(An)` (source ou destination, sans annotation
spéciale) devient :
```
MOVE.L An,-(SP) ; LEA d_mips(An),An ; MOVE.L An,-(SP) ; EORI.B #1,3(SP) ; MOVEA.L (SP)+,An ; <instr> (An) ; MOVEA.L (SP)+,An
```
Le résultat est juste quelle que soit la parité ; l'instruction pose elle-même les drapeaux, MOVEA ne les touche
pas. **70 accès** concernés dans le module (`mame_test.py` les compte).

**Résultat** : test des commandes à **42/42 suites d'états identiques à l'arcade** (contre 35) ; seuls 5 écarts
de distance restent (marche, dragon : cadence turbo §93). 3 × 20 000 + 60 000 images sans exception.

### 98. Performance : conversion des adresses de code par HACHAGE (cadence arcade retrouvée)

**Mesure** (`mame/profil.lua` : lectures de l'espace `opcodes` par bloc de 256 octets, 300 images de combat, test des
commandes) :
- arcade : 9,9 M lectures, dont 3,2 M dans la boucle d'attente ;
- traduction : 9,3 M, presque sans attente (code ~36 % plus lourd) ;
- premier poste : la conversion des adresses de code PS2 avant chaque `JSR/JMP (An)` (§76, `$3FF000`) =
  1,32 M (14 %), dichotomie de ~13 tours sur 12 174 débuts de fonction ;
- puis la conversion des pointeurs de données (`$400`, ~8 %).

**Changement** (`kernel68k.build_code_conv(hash_addr=…)`, `build_hash`) : table de hachage en ROM, 16 384 entrées
de 8 octets (128 Ko en `$3C0000`, zone libre vérifiée ; l'assertion sur la fin des données vise désormais
`$3C0000`), sondage linéaire, clé 0 = vide. Indice `((k >> 2) ^ (k >> 8)) & $3FFF` (choisi par mesure : décalage
seul = 7 à 28 sondages en moyenne ; ce mélange = 2,4) :
```
MOVE.L A0,D2 ; MOVE.L D2,D3 ; LSR.L #6,D3 ; EOR.L D2,D3 ; LSR.L #2,D3 ; ANDI.L #$3FFF,D3 ; LSL.L #3,D3
```
La dichotomie reste disponible : `CODECONV_DICHO=1`.
⚠ Première version fausse : restauration `MOVEM.L (SP)+` avec le masque `$040C` (D2-D3/**A2**) au lieu de `$020C`
(A1 = bit 9 en post-incrément) → A2 écrasé, A1 non rendu ; erreur d'adresse en attraction (image 2 621) alors que le
test des commandes passait. Toujours relancer les TROIS diagnostics.

**Résultat** :
- conversion de code 1,32 M → 0,28 M ; la boucle d'attente du noyau réapparaît (~1,4 M) ;
- cadence turbo 133,2 % de tours/image (arcade 133,3 %, avant 125,9 %) ;
- **test des commandes : 42/42 actions identiques à l'arcade, distances comprises.**

Piste suivante si besoin (fork) : la conversion des pointeurs de données (`$400`).

### 99. Persos MAX dans le banc : banque d'Eagle, bloc de données à adresse fixe (EN PAUSE)

Choix de l'utilisateur : le **schéma de banques du fork** (§48/§82). Le fork rangera chaque banque à la suite de la
ROM graphique (`code global = base + local`). Le banc MAME (32 Mo, pleins : 7 734 tuiles 16×16 libres seulement)
est une étape intermédiaire.

**Banc** : `untranspile/banques_max.py plNN [--sacrifier 262,280]` (entrées : `~/.cache/sfa3max/converti/plNN/`,
convertisseur de la session MAX).
- **Tuiles** : posées dans les tuiles libres, puis dans les tuiles EXCLUSIVES des banques sacrifiées (persos absents du
  test, ici Chun-Li `e262` et R. Mika `e280`) ; les tuiles déjà présentes à l'identique sont réutilisées.
  - Eagle : 24 544 tuiles, 10 236 réutilisées, 14 299 posées.
  - Sorties : `roms_max/sfa3ud/sz3.13m-20m` (lancer MAME avec `-rompath "roms_max;roms_tr"`) et la table
    `banques/plNN.bin`.
  - Piège corrigé : `plan1.bin` / `plan2.bin` commencent aussi par « pl ».
- **Données** : positions + frames de type 2 dans `ext_<base>.bin`, à adresse FIXE (`$B00000` + `$40000` par perso),
  servies par `banc_mem.lua` (tous les blocs). Une adresse hors des plages converties traverse la conversion des
  pointeurs inchangée.
- **Banque imposée** : `banc_sprites.lua` accepte `BANQUE_J1` / `BANQUE_J2`.
- **Démonstration** : `MAX_DEMO=plNN` dans `mame_test.py` redirige les longs des données qui visent les 20 frames de
  Ryu de la correspondance de la session MAX (`test_banc/frames_test.json`, 87 pointeurs).
  - Résultat : Eagle propre en garde et en marche (forme, blocs, positions, animation).
  - Les actions dont toutes les frames ne sont pas redirigées sont déchirées (attendu).
- **Reste** :
  - palettes : `palettes_cps2.bin` de la session MAX ; base CPS-A `$80410A` = `$90C0` → `$90C000` ; les objets de J1
    utilisent la palette 0, ceux de J2 la palette 5 ; `banc_palettes.lua` inachevé, ne pas écrire en mémoire depuis
    une prise ;
  - la réponse aux questions MAX (tables par perso, mots A/B/C) est dans `work/notes/reponse-hsfa-collisions.md`.

### 100. Intro : persos et slogans figés (mot à octets inversés lu dans une table INDEXÉE)

**Symptôme** (vu par l'utilisateur) : intro avec toujours Ryu, toujours « BORN TO FIGHT », bandeaux vides.

**Diagnostic** : la RAM de l'arcade pendant l'intro donne `$FFBA3C` = perso du panneau (25, 24, 28, 22, 27, 26, 29,
1 : Blanka, Honda, Vega…) et `$FF80DC` = tirage écrit par ROM `$4DC2` / `$5AB0`
(`MOVE.W table(PC,D0.W),$DC(A5)`) ; dans la traduction, `$DC` n'était jamais écrit.

**Cause** : le MIPS (`0x4AEEC`, `0x4E7DC`) range `bswap16` d'un mot lu dans une table de DONNÉES indexée par `D0.W`
(`lui/addiu table ; addu D0 ; lh 6(…)`). §92 ne reconnaissait que les sources `d(An)`.

**Corrigé** : `bswap16_mem` reconnaît aussi `constante + Dk.W (+ d)` et émet :
```
MOVE.L An,-(SP) ; LEA table.L,An ; ADDA.W Dk,An ; MOVE.B 1(An),$DC(A5) ; MOVE.B (An),$DD(A5) ; MOVEA.L (SP)+,An
```
2 sites.

**Résultat** :
- portraits et slogans variés comme sur l'arcade ;
- 3 × 20 000 + 60 000 images sans exception ;
- test des commandes : 42/42 suites d'états identiques (2 marches à 2-3 px près, cadence).

**Reste dans l'intro (banc)** : panneau des flammes et poses finales = emplacement 4 avec `$BE48` = 0 (fichier
graphique chargé par le natif, non émulé ici : 804 tuiles écartées) et palettes chargées par le natif.

### 101. Menu de sélection des modes (ARCADE, VERSUS, SURVIVAL, DRAMATIC BATTLE, TRAINING…) : affiché

**Référence** : sauvegarde PCSX2 `menu_modes` (titre + un libellé à la fois en bas, navigation haut/bas, « ® » à
côté du logo). Objets PS2 :
- `$FFBB00` = effet `$78` (libellé), X `$C0`, Y `$30`, `$1C` = `0x88C300 + 4 × curseur` ;
- `$FFBB80` = effet `$76` (« ® »).

Les entrées de libellé (fichier `0x69C320…`, `{000A, n, n−1, 001F, ptr X, lettres 0x0200|(car|0x80)}`) sont des
frames de **type `$0A`** (code + `$1600`, emplacement 1) ; le curseur est `$C001(A5)`.

**Défaut 1 (traducteur)** : la création `MOVE.L #$00780001,(A4)` (drapeau 1 | type `$78`) était prise pour une
ADRESSE de données et convertie (`$03C10029` → effet `$29`). Règle : une constante IMPAIRE n'est jamais convertie
en adresse de données. Dans la plage des données, il y a 5 constantes impaires sur 4 871, toutes des en-têtes
d'objet : `$00780001` ×1, `$00760001` ×4.

**Défaut 2 (classement natif)** : `natmiss` découpe les fonctions sur les seules cibles de `jal`. Une routine
atteinte par une table de sauts (états des effets) héritait des traits de la fonction précédente, parfois du C
natif. Elle était alors classée « natif du module » → talon `RTS`, entrée de table d'aiguillage à 0, saut dans la
table, instruction illégale.
- `mame_test.native_at` recalcule le critère sur [entrée, premier `jr ra`].
- 4 fonctions retraduites : `0x383C90` (état 1 du libellé), `0x392FD0` (état du « ® »), `0x38DFF0`, `0x38EC10`.
- Les vraies natives restent : manette `0x381770`, remappage `0x381900`, chargeurs `0x383700`/`0x3837D0`, C sans
  cases de registres.

**Banc** : après le premier Start, le jeu est sur l'écran-titre du portage ; un second Start valide le mode.

**Résultat** :
- libellés et « ® » comme sur PS2 ;
- TRAINING : sélection J1 / adversaire / ism → carte → VS → combat (écran « STREET FIGHTER ALPHA3 » sur fond
  vert avant le combat : palette à vérifier) ;
- 3 × 20 000 + 60 000 images sans exception ; commandes : 42/42 suites d'états identiques.

Outil de diagnostic : `BANC_SANS_AGE=1` (`banc_sprites.lua`) désactive le filtre des entrées anciennes.

### 102. Modes console : aiguillage par index BRUT, DRAMATIC BATTLE à 3, OPTION/EXIT natifs PS2

**Sauvegardes PCSX2** (`etats_ps2/`) : `menu_versus`, `menu_survival`, `menu_dramatic`, `menu_training`, `menu_option`
(libellés), `dramatic_selection`, `dramatic_jeu`. L'emplacement 6 annoncé « exit » était une ancienne sauvegarde
d'entraînement.

**Défaut (traducteur)** : l'aiguillage des modes du portage (mips `0x485A4`) lit l'octet `$C000/$C001` (curseur) et
le multiplie par 4 (`sll 2`, table de longs `0x5854A0`). Les aiguillages Capcom, eux, ont un index déjà doublé
(`sll 1`). La traduction émettait `MOVE.W T(PC,D0.W)` sans doubler :
- curseur impair : lecture à une adresse impaire, faute d'adresse (DRAMATIC BATTLE) ;
- curseur pair : mauvaise entrée.

**Corrigé** : échelle 4 → `ADD.W Dix,Dix` avant la lecture de la table, dans le registre d'arrivée (forme à deux
registres : `MOVE.W Dsrc,Dix ; ADD.W Dix,Dix ; MOVE.W T(PC,Dix.W),Dix`, éléments séparés pour l'assembleur).
1 site.

**Banc** : emplacements de banque 6/7 = joueurs 3/4 (structures `$FF8C00` / `$FF9000`, octet perso `+$103`) câblés dans
`banc_sprites.lua`. Le DRAMATIC BATTLE affiche les trois persos (Ryu + Ken contre Adon), comme sur PS2.

**OPTION et EXIT = code natif de l'exécutable PS2** :
- OPTION crée une tâche (mips `0x383E20`) qui appelle à chaque image `0x118A60`, hors du module (menu d'options de
  l'Anthology, affichage propre) ;
- EXIT appelle `0x1CAC80` (retour au menu général) ;
- dans le banc : écran noir. Pour le fork, il faudra réécrire l'écran d'options en relevant les variables qu'il règle
  (sauvegardes PS2 avec des réglages différents).

Diagnostics : 3 × 20 000 + 60 000 images sans exception ; commandes : 42/42 suites d'états identiques.

**Correctif (même jour)** : la capture de l'utilisateur (Ken contre Dan) montrait une copie bleue de Dan derrière lui.
Les emplacements 6/7 ne sont plus pris que si la structure joueur 3/4 est ACTIVE (`$FF8C01` / `$FF9001`) ; sinon,
comme avant, les objets d'emplacement 6/7 sont écartés. À confirmer sur le combat de l'utilisateur.
**Son de l'intro** : la commande « morceau de l'intro » (`FF07 0001`) part 2 images après le fondu (`FF05 00A0`),
contre 37 sur l'arcade (le Z80 se déclare prêt tout de suite : plus de musique à fondre) ; démarrage du portage sans
test de la RAM son ni commande `01 03` (envoyée par l'arcade à l'image 136). À préciser avec l'utilisateur.

### 103. Intro calée sur la musique ; bannières et portraits de l'intro ; diagnostic du « ghosting » en combat

**Symptômes (utilisateur)** : la musique de l'intro s'arrête avant les images ; sprites cassés dans l'intro ; effet de
fantôme sur les personnages en combat.

**1. Synchronisation de l'intro : le portage remplace la musique par une table de ticks.**
- Mesure (`_scene.lua`, valeur `$FF8016` par image) : 1 822 images de la scène 1 à la scène 46, contre 1 719 sur
  l'arcade. Les gels de ticks aux changements de scène sont identiques des deux côtés (`_stall.lua`) : c'est le NOMBRE
  de ticks par scène qui diffère (+2 à +6).
- L'arcade (ROM `$4CE8`) copie à chaque tick le **repère de musique** que le Z80 écrit en RAM partagée (`$618021`)
  dans `$B(A5)` ; le script de l'intro (`$4D98`) avance quand ce repère atteint le seuil de la scène. À l'init
  (`$4CCE`), elle efface le repère.
- Le portage (musique différente sur PS2) lit une table de ticks à la place (`0x5855C0`, index `$C18E(A5)`), réglée
  pour sa musique : sur la musique arcade, les scènes prennent du retard.
- **Corrigé** (`mame_test.py`) : la routine `0x4A830` lit de nouveau `$618021` ; le premier tick après l'init
  (index `$C18E` = 0) efface le repère. Résultat : les 46 changements de scène tombent à ±1 image de l'arcade.
- Au passage, recopies de tilemaps de l'intro réécrites à la main (`0x10DD50`, `0x10E200` : flux d'octets lus un à
  un au lieu de l'échange par la pile), comme le remplissage `0x898E0` : moins de gels (1 918 → 1 806 images avant la
  vraie correction).

**2. Bannières de l'intro en tuiles parasites (banc).** Le jeu écrit une tilemap AVANT de pointer le registre de base
dessus (début de l'intro : tuiles en `$914000` alors que scroll2 vaut encore `$904000`). `banc_plans.lua` ne
renumérotait que les écritures tombant dans un plan actif. **Corrigé** : il garde la valeur brute du portage de chaque
mot de code et reconvertit toute la zone du plan quand sa base change. scroll1/2/3 identiques à l'arcade (codes).

**3. Portraits blancs (Birdie, Sagat, Sodom…) : octet haut d'un registre.**
- L'écran des portraits attend `$FF8017 = $3F` (6 bits posés par 6 objets : `BSET` de `index × 2 + $3C(objet)`).
  Dans la traduction, `$15` (bits 4, 2, 0 deux fois) : le paramètre `$3C` valait 0 pour tous. Le fondu des palettes
  de scroll2 (`$91E800`, blanc → portrait) n'était jamais lancé.
- Création des objets (mips `0x4CC2C`) : `lh` du paramètre dans la case de D1 (`0x1128`), puis `lb 0x1129` = octet
  HAUT du mot. C'est le **seul accès octet à +1 d'une case de registre dans tout le module** : retouche du portage,
  dont la table `0x585750` garde les octets de l'arcade. La traduction faisait `MOVE.B D1` (octet bas).
- **Corrigé** : seul lecteur de la table → les octets du paramètre sont échangés dans l'image (`mame_test.py`).
  Les numéros de scène sont maintenant ceux de l'arcade (`003E/003F/0003` au lieu de `0014/0015/0001`).
- Les mots des bannières diffèrent encore de l'arcade : tirage aléatoire (`$FF80AE`, état différent), pas un défaut.

**4. « Ghosting » en combat : dépassement du temps image en vitesse turbo (pas le banc).**
- En turbo, le jeu fait 4 ticks pour 3 images. Sur l'image à deux ticks :
  - arcade : tick (ligne ~8), tick (~70), liste d'objets finie vers la ligne 208 ;
  - traduction : tick (~12), tick (~114), liste finie vers la ligne **60 de l'image suivante**.
- La copie matérielle de la liste au retour de trame prend alors une liste à moitié réécrite : l'image suivante montre
  l'ancienne pose (suite nouveau / ancien / nouveau à chaque changement d'animation). Le défaut est identique sans
  `banc_sprites.lua` : ce n'est pas le banc.
- En vitesse normale (un tick par image), la liste finit vers la ligne 216 : pas de fantôme.
- La traduction est ~1,55 fois plus lente que l'arcade sur ces images. Profil d'un combat (`_prof_f.lua` via
  `commandes.lua`, 600 images) :

  | part | adresse 68K | rôle |
  |---|---|---|
  | 12,2 % | `$24484` (mips `0x105814`) | émetteur de frames type 08 (décor en sprites) |
  | 8,7 % | `$400` | conversion des pointeurs de données |
  | 6,5 % | `$22540` (mips `0xF7328`) | table de défilement par ligne (`ADD.L` sur long échangé) |
  | 2,9 % | `$3FF000` | (talons) |

- Lecture de long avec post-incrément émise en `ADDQ.W #2,An ; SWAP ; MOVE.W -2(An) ; SWAP ; MOVE.W (An)+` au lieu
  de `MOVE.L (An)+` : 17 sites, surtout dans les émetteurs de sprites.
- **Pistes** :
  1. surcadencer le 68K : MAME avec `-cheat` (curseur « Overclock CPU » du menu Tab, non testé ici, l'API Lua de MAME
     0.285 ne l'expose pas) ; fork FBNeo (`nBurnCPUSpeedAdjust` du pilote CPS) ;
  2. accélérer le code traduit (judas sur les longs, boucles chaudes) : il faut gagner ~35 % sur les images turbo.
- **Premier judas** (`translate.py`, `merge_long_postinc`) : `ADDQ.W #2,An ; SWAP Dm ; MOVE.W -2(An),Dm ; SWAP Dm ;
  MOVE.W (An)+,Dm` → `MOVE.L (An)+,Dm` (jamais si un branchement vise l'intérieur, ni devant un Bcc) : 34 sites,
  liste finie ~11 lignes plus tôt par image (turbo : ligne ~49 de l'image suivante au lieu de ~60). `LONG_POSTINC=0`
  le désactive.
- Autres gisements relevés : conversion `$400` (jusqu'à 13 `CMPA.L` en chaîne, ordre fixe) ; opérations sur long
  échangé (`MOVE.L D7,-(SP) … MOVE.W SR,-(SP) … MOVE.W (SP)+,CCR ; MOVEM.L (SP)+,D7` même quand les drapeaux sont
  morts). Estimation : 12-15 % au total, insuffisant seul → surcadençage recommandé pour le fork.

Diagnostics (sans le judas) : 3 × 20 000 + 60 000 images sans exception ; commandes 42/42 identiques, cadence turbo
133,2 % (arcade 133,3 %).
Avec le judas : 3 × 20 000 + 60 000 images sans exception ; commandes 42/42 identiques, cadence turbo 133,3 %
(5 359 tours en 4 019 images, comme l'arcade).

**5. Correctif du fantôme dans le banc (retour de l'utilisateur : « toujours du ghosting »).**
- Lecture directe des mémoires internes de MAME (`objram1` / `objram2`, partages Lua) : la CPS2 échange ses deux
  banques d'objets à chaque retour de trame, côté arcade comme côté traduction. L'arcade écrit une liste complète
  dans chaque image ; la traduction, en turbo, commence la liste avant le retour de trame et la finit après (une
  moitié dans chaque banque, ex. entrées `0-$6B` puis `$6C-$104`), et une image sur trois n'a pas de liste.
- `OBJ_BASE` (`$400000`) vaut `$7000` sur l'arcade et 0 dans la traduction, mais le forcer (`$7000` ou `$7080`) ne
  change rien : fausse piste.
- **Corrigé** (`banc_sprites.lua`) : la liste complète convertie (au marqueur de fin) est écrite dans les DEUX
  banques physiques (`objram1` et `objram2`). L'affichage montre toujours la dernière liste complète : marche de Ryu
  sans retour en arrière ni mélange. Le fork fera de même (verrouillage de la liste à son marqueur de fin).
  `BANC_UNE_BANQUE=1` rend l'ancien comportement.
- Reste, sans fantôme : en turbo, certaines images répètent la précédente (la traduction rend 2 listes pour 3 images
  quand l'arcade en rend 3) ; le surcadençage ou l'accélération du code le corrigeront.

**Outils** (`work/mame/`) :
- `_scene.lua` (scènes), `_stall.lua` (ticks / gels / attente par image), `_qm.lua` (repère de musique) ;
- `_gdump.lua` (RAM graphique + registres CPS-A suivis par prise), `_wpal.lua` (écritures de palettes) ;
- `_finpos.lua` (ligne de fin de liste et des ticks), `_prof_o.lua` (profil des seules images en retard).

### 104. Performance en combat : conversions, longs échangés, réécritures à la main

Objectif : que l'image turbo (2 ticks + rendu) tienne dans une image, comme sur l'arcade (liste finie vers la ligne
208). Mesure (`_finpos.lua` : ligne de fin de liste) : ligne ~60 de l'image SUIVANTE au départ (§103).

**Outils** : `_prof_ph.lua` (profil par phase : « logique » = du tick `$FF8081` à la première écriture d'objets,
« rendu » = ensuite) ; `_conv.lua` (histogramme des pointeurs convertis) ; `_bcd.lua` (injection de valeurs à l'entrée
d'une routine, lecture du résultat : comparaison ancienne / nouvelle traduction).

**Changements** (tous vérifiés : test des commandes 42/42, captures identiques à l'arcade sur le décor) :
1. **Conversion des pointeurs de données** (`kernel68k.build_conv`) : recherche dichotomique au lieu d'une chaîne de
   13 `CMPA.L` ; accès directs pour « sous la première plage » et « au-delà de la dernière » (`$FFxxxx` : RAM 68K déjà
   convertie, 15 % des appels, qui traversaient toute la chaîne). Simulation de la nouvelle routine sur toutes les
   bornes : mêmes résultats.
2. **Opérations sur long échangé** (`translate.drop_dead_sr`) : la sauvegarde `MOVE SR … MOVE CCR` (+ `MOVEM` de
   restauration) est retirée quand l'instruction suivante écrase N, Z, V, C sans les lire (liste blanche : MOVE hors
   MOVEA, MOVEQ, TST, CLR, CMP/CMPI/CMPA/EOR, ADDQ/SUBQ hors An) ; X reste celui de l'opération (SWAP et MOVE n'y
   touchent pas). 1 674 sites. `DROP_SR=0` le désactive.
3. **Table de défilement par ligne** (mips `0xF72D8`, ~260 écritures par appel) : accumulateurs gardés en registre au
   lieu d'un aller-retour mémoire par entrée ; remplissages par longs.
4. **Binaire → BCD** (mips `0x89A10`, scores) : chaque `ABCD` était émulé (~15 instructions : adresses PS2 à l'octet
   inversé, pile) ; réécrit avec de vrais `ABCD Dy,Dx` (déplacements -7,-8,-5,-6,-3,-4,-1,-2). Vérifié par injection
   de 10 valeurs (dont `$FFFFFFFF`, `$7FFFFFFF`, 999 999) : résultats identiques à la traduction d'origine.
   Accumulateur en `$FF3A54` (`-$45AC(A5)`).
5. `mame_test.py` : `MAINS=n` limite la liste des routines réécrites à la main (diagnostic) ; défaut = toutes.
6. **Talons de conversion** (données `$400`, code `$3FF000`) : les cas « inchangé » (sous / au-delà des plages)
   sont testés dans le talon de chaque registre, sans `BSR` vers le cœur ni `EXG`.

**Résultat** : liste de l'image turbo finie vers la ligne ~23 de l'image suivante (60 → 49 → 40 → 35 → 27 → 23) ;
images normales : ligne ~186. Le correctif du banc (§103, liste écrite dans les deux banques) évite déjà les fantômes ;
ce qui reste = une image répétée sur trois en turbo.

**Profil restant (phase logique)** : dispersé, aucun poste au-dessus de 5 % — copie de palettes avec luminosité
(mips `0xE6468`, boucle de 16 mots), conversions (`$400` + `$3FF000`, ~10 % à elles deux après allègement), copie de
mots jusqu'au négatif avec registre A8 prêté (mips `0xDBEF0`), etc. Gagner encore ~10 % demanderait des réécritures
hors place (pas de place pour dérouler les boucles sur place) ou un traitement générique des registres prêtés (A8/D8).
Pour le fork : surcadençage modéré du 68K (FBNeo `nBurnCPUSpeedAdjust`, ~115-120 % suffiraient d'après la mesure).

Diagnostics (version finale du §104) : 3 × 20 000 + 60 000 images sans exception ; commandes 42/42 identiques, cadence
turbo 133,3 %.

### 105. Palettes des persos MAX dans le banc (agent dédié, bac à sable `work/mame_max/`)

- Méthode : les 30 palettes du perso MAX (`palettes_module.bin`, format du module : `0x0RGB`, luminosité 0, mot 15 =
  numéro) remplacent celles d'un perso du jeu dans le bloc de données (table fichier `0x451230`, Ryu en `0x451270`),
  avant l'inversion des mots de l'image. Le moteur copie lui-même son groupe de 5 (`((ism + 1) × 2 + $129) × 5`) :
  aucune prise Lua. `mame_test.py` : `MAX_PAL=plNN` (défaut = `MAX_DEMO`), `MAX_PAL_ID` (défaut 0). `banc_palettes.lua`
  devient inutile.
- Vérification (`verif_palettes.lua` + `compare_palettes.py`, lecture seule des palettes `$90C000`) : Eagle groupe 10
  (poing) et 15 (pied) à 80/80 mots sur 41/41 relevés ; Ken intact ; journal de combat identique. Sur la ROM arcade,
  Ryu/Ken ont exactement les palettes du module (J1 = 0-4, J2 = 5-9).
- Pour étendre aux IDs `$26-$29` : la table `0x451230` est lue par 12 sites ; décalages SIGNÉS 16 bits (±32 Ko) ;
  32 entrées collées au bloc de Ryu → déplacer table + palettes (42 entrées + 32 blocs tiennent : `0x7854`). Seconde
  table par perso à étendre : `0x457B70` (palettes d'effets, 24 par perso ; lue en `0x01C894` et `0x037D30`).
- Limites : remplacement de l'ID 0 (Ryu partout) ; ism ±1 non relevés ; Ingrid (48 palettes) refusée.

### 106. Fin de l'intro : palettes perdues (traducteur) et sprites des emplacements 2-4 (banc)

**Symptôme (utilisateur)** : « problème de palette à la fin de l'intro ». Comparaison image par image avec l'arcade
(intro synchronisée, décalage fixe de 507 images) : M. Bison (flammes, gros plan) et Akuma de dos en fausses couleurs ;
Blanka, E. Honda, Ken (et leurs images rémanentes) absents.

**1. Traducteur : `MOVEA.L abs.L,An` perdu.** L'arcade charge les pointeurs de palettes par `MOVEA.L $339838.L,A0`
puis `MOVEA.L $33979C.L,A0` (ROM `$5F3A`/`$5F52`). MIPS : `lui ; addiu ; addiu ; lw ; sw 0x1100` (mips `0x4FF10`).
La lecture absolue était bien repliée (`absread`), mais aucun cas ne la rangeait dans un registre **A** : A0 gardait
la valeur de la routine précédente → couleurs lues dans une table de tuiles (`f7b8 f7bc f7c0…`). Corrigé : nouveau cas
`MOVEA.L abs.L,Am` + remise en ordre du long ; la conversion du pointeur suit d'elle-même (`dptr_fix`). 8 sites dans
le module (`mame_test` : « MOVEA.L abs.L,An retrouves »). Palettes de la scène de M. Bison identiques à l'arcade.

**2. Banc : emplacement 4 quand `$BE48` = 0.** Les objets de Ken/Blanka/E. Honda de l'intro sont dans l'emplacement 4
(graphismes du couple chargé par le natif `0x383700(0)` : table `0x59C1B0`, entrée 0 = graphismes 456, animation 310).
Pendant l'intro `$BE48` vaut 0 : le banc n'avait aucun fichier pour l'emplacement 4 et écartait ces objets.
`banc_sprites.lua` : `$BE48 = 0` → fichier 456 (`BANC_GFX_INTRO`). Vérifié : codes 4d → `08A2`, 54 → `0CC6`, comme la
liste d'objets de l'arcade. 16 captures de l'intro plus proches de l'arcade, aucune moins proche.

**Aussi dans le banc** : `BANC_OMBRE` (liste brute du jeu, lecture seule, diagnostic).
⚠ Piège de méthode : une prise d'écriture installée AVANT `banc_sprites.lua` voit la liste CONVERTIE (le banc
renvoie le mot converti) ; lire `BANC_OMBRE` pour la liste du jeu.

Diagnostics (§106) : 3 × 20 000 + 60 000 images sans exception ; commandes 42/42 identiques, cadence turbo 133,3 %.

### 107. Passe d'audit : écritures de registre qui ne produisaient AUCUNE instruction

Demande de l'utilisateur : repasser sur l'ensemble avec les cas particuliers rencontrés. Le défaut du §106
(`MOVEA.L abs.L,An` perdu) appartient à une famille : une écriture MIPS dans une case de registre 68K
(`sw/sh/sb 0x1100-0x1144`) qu'aucun cas du traducteur ne reconnaît sort du bloc sans rien émettre — en silence
(le compteur « non résolus » ne la voit pas).

**Outil** : `translate.py` relève ces sorties (`CHUTES`) ; `mame_test.py` écrit `work/mame/chutes.json`
(`va, instruction, case, sorte du symbole source, lecture absolue/mémoire/indexée`). Le compteur imprimé par la
construction (« écritures de registre tombées sans traduction ») doit rester stable ; toute hausse = régression.

**Résultat** : 71 sites au départ (142 entrées : deux passes de traduction). Corrigés :
- `ADDA.W d(An),Am` (tables à décalages relatifs Capcom : `lh` + extension de signe + `addu An`) : 4 sites
  (`translate.adda_mem`) ;
- module `dn_alu.py` (sorties des blocs D et A) :
  - `OP.x T(PC,Dk),Dn` (ADD/SUB/AND/OR d'une valeur de table, avec décalage éventuel `T + index + d`) — forme
    absolue de l'assembleur (`dtab`, taille lue aussi sur ADD/SUB/AND/OR) ; en long : SWAP autour (AND/OR seulement) ;
  - décalages variables `LSL/ASR/LSR Dm,Dn` (`sllv/srav/srlv`) ;
  - `ADDI/ANDI/ORI #c,Dn` (constante `lui/ori`, que le traducteur prenait pour une adresse de table) ; `ADDI` d'une
    chaîne d'`addiu` (`+$7FFF +1`) ; `ANDI.L #$1FFFF` (`dsll32 15 / dsrl32 15`) ;
  - `ADD.x Dn,Dn` ; `MULS.W #10/#40,Dn` (`x*5 << s`) ;
  - `SUBA.L Dk,Am` ; `LEA d16(An),Am ; ADDA.W Dk,Am` (décalage hors d8) ; `ADDA.L` d'un mot à octets inversés
    (code d'animation, mips `0x276048` / `0x2776E0`) via D0 sauvé.
  `DN_ALU=0` désactive le module.
- Restent 28 sites : 4 légitimes (`An ← An`), 17 dans les zones de code propre au portage (`0x190000-0x1BFFFF`,
  `0x380000-0x39FFFF` : menus natifs), 7 dans le jeu avec registres virtuels (D8 `0x1144`, `s3`) ou retour de la
  fonction native `0x571900` (remappage des touches) — à reprendre si un symptôme y mène.

Diagnostics (§107) : 3 × 20 000 + 60 000 images sans exception ; commandes 42/42 identiques ; intro inchangée (captures).

**Audit des écritures MÉMOIRE** (`AUDIT_MEM=1 mame_test.py` → `work/mame/mem_miss.json` : `sw/sh/sb/swl/swr` dont la va
n'apparaît dans aucun élément de la sortie, cases de registres exclues). 789 sites : 741 dans les zones de code du
portage (`0x380000-0x39FFFF`, `0x50000-0x5FFFF`), 48 dans le jeu. Corrigés par insertion à leur place
(`dn_alu.mem_fix`, après la traduction de la fonction) : 9 sites —
- long d'une structure `+= somme d'addiu` (`$7FFF + $2001` = `$A000`, …) : `$10(A6)` (mips `0x135FE4`), `$48(A6)`
  (`0x13D60C`), `$14(A6)` (`0x1C3F94`), `$8(A4)` (`0xF8C9C`) + masque `ANDI.L #$1FFFFFF` (`0xF8CB4`) ;
- `EORI.L #$10000,$BF30(A5)` (`0x1F991C`) ;
- couleurs constantes à une adresse non alignée de la RAM de palettes (`swr/swl`, palette 25, `0x451FC`/`0x45EFC`) ;
- `ANDI.W #$F000,$90C27C.L` (`0x69584`).
Puis les copies d'un octet signé de table vers une structure (positions X/Y d'une table : `0x1F65FC`, `0x1F6634` ;
`$14C(A5)` : `0x200FAC`) : `MOVE.L Dt,-(SP) ; MOVE.B T(PC,Dk.W),Dt ; EXT.W ; MOVE.W Dt,d(An) ; MOVEM.L (SP)+,Dt`
(l'assembleur rend la table en forme absolue avec le XOR 1 des octets ; vérifié sur le code émis). Diagnostics
propres, commandes 42/42. Restent dans le jeu : registres virtuels D8/A8 (6), et le code d'initialisation / contexte du portage
(`0x2EBxx-0x30114`, `0x926C0-0x92908`).

Diagnostics (audit mémoire) : 3 × 20 000 + 60 000 images sans exception ; commandes 42/42 ; intro inchangée.

### 108. Upper (`ro5`) dans le banc : profils par module, données coupées, premiers pas de l'intro

**Profils** (`profils.py`, `MODULE=ro3|ro5`) : adresses de reset / tâche / init / VBL, sauvegarde des registres,
crochets natifs, sites manette, aides du recompilateur (`translate.AIDES_RECOMP`), pointeur d'animation native
(`$BE48` / `$C0BC`), correctifs (repère musique, table des objets de l'intro, palettes), routines à la main, dossier
de travail (`work/mame` / `work/mame_ro5`) et de sortie (`roms_tr` / `roms_ro5`). Garde-fou : avec `ro3`, la ROM
reconstruite est **identique octet pour octet** à celle d'avant le paramétrage (empreintes md5).
`assets_natifs.py` : valeurs ro5 (natifs `0x4112D0` / `0x4113A0`, tables `0x628460` / `0x628470`, 40 persos,
fichier fixe 390 en `$B04000`, base de chargement `$B83000`, base virtuelle `$C00000`).

**Programme CPS2 limité à 4 Mo** : les données d'Upper (3,76 Mo) n'y tiennent pas avec le code et les tables de
conversion. `translate.DATA_SPLIT` / `DATA_EXT` : la fin du segment de données (`$908000-$9A0180`, 0,62 Mo) est
projetée en `$C80000` (traducteur + conversion à l'exécution), écrite dans `ext_c80000.bin` et servie par
`banc_mem.lua` (`BANC_DIR` = dossier du module). Le fork y mettra de la ROM. SFA3 n'est pas concerné (tout tient).

**Premiers lancements** (`MODULE=ro5 XDATA=<X_DATA.BIN> mame_test.py`, puis MAME avec
`-rompath work/mame_ro5/roms_ro5`, `BANC_DIR=work/mame_ro5/`) : 0 non résolu, le jeu démarre sans exception.
- Repère musique désactivé pour ro5 : la ROM son de SFA3 ne produit pas les repères d'Upper (l'intro restait en
  scène 0) ; l'intro suit la table de ticks du portage.
- Intro, 1re faute (erreur d'adresse) : les fichiers d'animation de l'intro d'Upper (522/523) supposent un chargement
  en **`$B83800`** (table en `+0x31C`, comme ro3), pas `$B83000` → `assets_natifs.LOAD_SITE`. Site `0x4CC04` : talon
  dynamique (fichier choisi par `($8C21(A5) >> 2) & 1`, `SITES_DYN`). Talons natifs d'Upper déplacés après
  l'amorçage (`$940`, la zone `$810-$900` débordait).
- 2e faute (image 1386, scène `0x0A00`) : un objet de type `$23` créé avec un sous-index `$13` (mips `0x1CB9D4`)
  arrive dans un gestionnaire à 4 états (`JMP T(PC,D1.W)`, mips `0x72AF4`) → saut impair. À suivre.

**Banc, au passage** : `banc_sprites.lua` lisait le pointeur d'animation native en `$FFBE48` ; `$BE48(A5)` est un
déplacement SIGNÉ → **`$FF3E48`** (Upper : `$C0BC(A5)` → `$FF40BC`, variable `BANC_PTR_ANIM`). L'emplacement 4 suit
maintenant les animations natives (intro inchangée : le défaut du §106 tombait juste par coïncidence).

### 109. Décisions de stratégie (2026-10-04)

Décidé avec l'utilisateur :
- **Plateforme** : un **fork de MAME** sert d'outil intermédiaire (banc de développement et de validation), avant le
  cœur **FBNeo** final (Android / RetroArch). Le fork MAME = un jeu dérivé de `sfa3ud` dans `cps2.cpp` qui rend en
  natif ce que font aujourd'hui les scripts Lua : ROM programme étendue (bloc `$C80000` d'Upper, §108) et ROM
  graphique étendue, emplacements de banques des sprites / plans (`banc_sprites.lua`, `banc_plans.lua`), données
  servies par `banc_mem.lua`, liste d'objets verrouillée à son marqueur de fin (ghosting, §103), surcadençage
  (~115-120 %, §104). On garde tout l'outillage Lua, le débogueur et la comparaison avec la ROM arcade. Les mêmes
  extensions seront reportées dans FBNeo une fois le format stabilisé.
- **Ordre** : **Upper (`ro5`) d'abord**, puis **MAX**, Hyper (`ro9`) en dernier.
- **Roster** : MAX ⊃ Upper (pas l'inverse). Upper sur le moteur arcade donne tout le roster de MAX sauf les 4
  persos propres à MAX (Eagle, Maki, Yun, Ingrid) → à porter depuis la PSP dans les 2 places de remplissage d'Upper
  (`$26` / `$27`) + 2 places à créer en agrandissant les tables de 40 entrées.
- **Le reste de MAX** (modes et contenus hors persos) : écarté pour l'instant (« gourmandise » selon l'utilisateur).
  Sauvegarde côté CPS2 : seulement l'EEPROM 93C46 (128 octets : réglages) ; un mode à progression demanderait de la
  NVRAM ajoutée par le fork.
- **En attente de l'utilisateur** : fins des 4 persos MAX — convertir les images PSP en tuiles + plans CPS2, ou
  d'abord réutiliser des fins existantes (comme Upper pour `$24-$27`). Réponse à relayer à la session MAX
  (SendMessage « Street Fighter Alpha Max widescreen reconstruction » ; notes = référence, message = sonnette).

Reprise technique : faute Upper image 1386 (scène `0x0A00`), objet type `$23` créé avec sous-index `$13` (mips
`0x1CB9D4`, 68K `$41896`) → gestionnaire à 4 états (mips `0x72AF4` : `MOVE.B $2(A6),D0 ; ADD ; MOVE.W
T_60dd20(PC,D0.W),D1 ; JMP`) → saut impair. Commandes utiles :
`MODULE=ro5 XDATA=<hsfa>/work/xdata/X_DATA.BIN nice -n 19 python3 mame_test.py` puis MAME `sfa3ud
-rompath work/mame_ro5/roms_ro5` avec `BANC_DIR=<hsfa>/work/mame_ro5/`. Garde-fou `ro3` : md5 de `sz3ud.03c` =
`a85138517ff8a19ff74e03d2cfae4c03`. Diagnostics de non-régression `ro3` : `MAXF=20000 diag.py 30 --nobuild` (×3 dont
entrées et partie offensive 60000), commandes 42/42 (5359 tours / 4019 images, 133,3 %).

### 110. Partie Arcade complète jusqu'à la fin ; fins noires (base des palettes non convertie)

**Décision de l'utilisateur (fins MAX)** : pour l'instant, les 4 persos MAX **réutilisent des fins existantes**
(comme Upper pour `$24-$27`) ; convertir les fins PSP en tuiles + plans CPS2 = en fin de projet. Relayé à la session
MAX. Consigne : finir ce qui reste à voir sur SFA3 avant Upper.

**Outil** `mame/tournee.lua` (REF=1 ROM arcade / traduction) : partie Arcade à 1 joueur jusqu'au bout. J1 a une vie
infinie ; en combat, la vie du CPU est ramenée à 1 et J1 lance des boules de feu (dégâts en garde) → K.O. rapide.
Vie = mot `+$50` (et `+$52`, affichage) de la structure joueur (`$FF8400` / `$FF8800`, max `$90`, trouvé par
`commandes.lua DUMPBASE=FF8800 DUMPREL=…`). Journal : modes `$FF8000/2/4`, `$FF800C`, décor `$FF8100`, persos ;
captures toutes les `SNAPP` images (`-snapshot_directory`) ; arrêt sur exception ; `SAVEAT`/`SAVENAME` = état MAME.
⚠ `-state` en ligne de commande bloque sur l'écran d'avertissement des sommes de contrôle : charger l'état depuis
Lua (`manager.machine:load(nom)` à la 2e image). ⚠ Ne jamais `pkill -f`/`pgrep -f` avec un motif présent dans la
ligne de commande du shell (tue le shell) : `ps -C mame`.

**Résultat** : la traduction joue la partie entière sans exception (10 combats, rival, Bison, fin de Ryu, générique,
GAME OVER), même déroulé que l'arcade (adversaires tirés au hasard, différents ; séquence de fin `$000A` : 11 764
images arcade / 11 762 traduction). **Mais** les scènes de fin (dialogue final de Bison, fin du perso) étaient
presque noires : contours sombres, ni cadre ni texte.

**Cause** : registre de base des palettes `$80410A` = `$93C0` / `$9400` au lieu de `$91C0` / `$9200`. L'arcade forme
les deux tampons de palettes de la fin par décalage (ROM `$25E8E` : `MOVEQ #0,D1 ; MOVE.W #$91C0,D1 ; LSL.L #8,D1 ;
MOVE.L D1,$AE9E(A5)`, idem `$9200` → `$AEA2(A5)`) ; le portage fait de même avec les adresses PS2 (`addiu 0x93C0 /
0x9400 ; sll 8`, mips `0x27A94` / `0x27AD0`) et la traduction gardait la constante PS2.

**Corrigé** (`translate.vram_shift_const`) : `MOVEQ #0,Dn ; MOVE.W #imm,Dn ; LSL.L #8,Dn` dont `imm << 8` tombe dans
la mémoire vidéo PS2 (base + `$20000`..`$4FFFF`) → `MOVE.L #adresse CPS2 marquée,Dn` (marque `HW_TAG` `$01xxxxxx` :
2 des 4 sites passent ensuite par `MOVEA.L D1,A1 ; JSR CONV_A1`, qui ne doit pas reconvertir). 4 sites (`0x27A90`,
`0x27ACC`, `0x2C3BC`, `0x2C440` ; compteur imprimé ×2 car deux passes de traduction). Jamais si un branchement vise
l'intérieur de la suite. Fins affichées comme l'arcade (comparaison image à image, décalage 3 335 images).

**Non-régression** : `untranspile/nonreg.sh` (3 diagnostics + test des commandes, référence `work/mame/cmd_ref.txt`) :
3 × sans exception, 42/42, 133,3 %.

### 111. Les fins de tous les persos (ids `$00`-`$1F`) : conformes à l'arcade

`tournee.lua` gagne de quoi aller droit à la fin avec n'importe quel perso :
- **`PERSO=hh`** : perso de J1 imposé pendant les 120 premières images de l'écran de sélection (`$FF8000 = 2`,
  `$FF8004 = 2`), dans **J1 `+$102`** (perso sous le curseur ; le curseur `+$11` seul ne suffit pas : `+$102` n'est
  recalculé qu'au déplacement) ; `CURSEUR=n` écrit `+$11`. Le premier bouton n'est appuyé qu'après.
- **`FORCE="Lff8540=ffffffff"`** (à la manche `FORCEC`, défaut 1) : **masque des adversaires battus**, long J1
  `+$140` (un bit par identifiant de perso). La ROM (`$BA62`) cherche le prochain adversaire dans la liste
  `$FF0F82` en sautant les bits à 1, jusqu'à la limite `$14C(A5)` ; tout à 1 → après le 1er match, Bison puis la
  fin. `$FF8115` (= index dans la liste), `$8137`, `$816D` sont des dérivés (les forcer ne change rien).
  `FORCE` accepte aussi des octets (`ff8137=8`).
- `SNAPFIN=1` : captures seulement pendant la séquence de fin (`$FF8004 = $000A`) ; `DUMPC`/`DOUT` : vidages de la
  RAM au début des manches listées.

Série : 32 persos × (arcade, traduction), `NF=24000` (Guy : 40 000, il gagne au temps faute de boule de feu),
8 en parallèle. Les 64 parties vont au bout sans exception ; nombres de captures de fin identiques (±1) ;
planches arcade | traduction : mêmes scènes, palettes, textes pour tous (écarts = phase des captures).
⇒ Les fins sont prêtes à être réutilisées pour les persos MAX (§110).

**Structure joueur, octets libres** (question de la session MAX) : prise d'écriture sur `$FF8400-$FF93FF`, 4 parties
complètes, écritures non nulles pendant les combats seulement → grands blocs jamais écrits : `$380-$3FF` (mais
`$380-$397` écrit par 3 `MOVEM.L` à ROM `0x6EFD2`, relevé par la session MAX), `$300-$36F`, `$156-$17F`…
Vérification statique MIPS (ro3 et ro5 : accès mémoire et calculs d'adresse `addiu` de déplacement
`0x3F0-0x3F3`) : aucun. **Retenu par la session MAX : PSP `0xAA` → `$3F0` (octet), PSP `0x1EA` → `$3F2` (mot).**

### 112. Modes console dans la durée : SURVIVAL plantait (index brut d'une table de pointeurs)

`tournee.lua MODE=n` (traduction) : curseur du menu de l'Anthology imposé pendant le menu (`$FF8000 = 4`), puis le
2e Start valide. Le curseur est l'**octet `$FF4001`** (relevé en descendant dans le menu : mot `$FF4000` = 0, 1,
2…), pas `$FF4000`. `SNAP0` = première image capturée. Modes : 0 ARCADE, 1 VERSUS (sélection à 2 joueurs), 2
SURVIVAL, 3 DRAMATIC BATTLE, 4 TRAINING.

**SURVIVAL : erreur d'adresse au premier combat** (image ~2 150). Mips `0x1F1D24` (code propre au portage) :
`lb $C19C(A5) → D1 ; lh D1 ; sll 2 ; + table 0x5930A0 ; lw → A3`. L'index est BRUT (×4 dans le MIPS) ; la traduction
émettait `MOVEA.L T(PC,D1.W),A3` sans l'échelle (chez Capcom, l'index d'une table de longs est déjà multiplié).
**Corrigé** (même règle que le §102 pour les mots) : quand la lecture de table de pointeurs vient d'un `sll 2`,
`MOVE SR,-(SP) ; MOVEM.L Dk,-(SP) ; ADD.W Dk,Dk ×2 ; MOVEA.L T(PC,Dk.W),Am ; MOVEM.L (SP)+,Dk ; MOVE (SP)+,CCR`
(Dk rendu intact : le MIPS décale dans un temporaire). 2 sites (`0x1F1D50`, `0x1F1E60`). SURVIVAL : 17 manches
d'affilée sans exception, adversaires enchaînés, compteur de victoires. VERSUS, DRAMATIC, TRAINING se lancent.

**Ouvert : balayage vert « STREET FIGHTER ALPHA3 »** entre deux combats de SURVIVAL (et avant le combat en TRAINING,
§101) : logo et triangles « A » en vert (palette 30 : `$F0D0` / `$F0C0`). Absent en mode Arcade (l'arcade passe de
la victoire à la réplique sans balayage) → transition ajoutée par le portage, sans référence arcade. À trancher
avec une sauvegarde PCSX2 prise pendant cette transition.

Non-régression : 3 × sans exception, 42/42, 133,3 %.

### 113. Étude SFA2 (agent) : décors ajoutables plus tard, sur le fork

Livrable (hors dépôt) : `work/carto_sfa2/CARTE-sfa2.md` + scripts. Résumé :
- Modules SFA2 : `ro2` (Zero 2, porte les ressources X_DATA `e224-e252` ; `e251` = 4 Mo d'échantillons QSound),
  `ro8` (SFA2 occidental), `ro4` (Zero 2 Alpha / Alpha 2 Gold), `ro6` (Alpha 2 Gold + Cammy) : mêmes 20 décors.
  Source la plus simple : l'arcade déchiffrée (`sfa2u`, vidée par MAME).
- **Même moteur de décors que SFA3** (3 plans, cartes grille/blocs/tuiles, listes d'objets) : formats convertibles.
  Les 20 décors SFA2 sont absents de SFA3 (aucun graphisme repris).
- **Blocage** : la zone des tuiles de plans (8 Mo fixes de la ROM graphique CPS2) est pleine à 99,7 % dans SFA3 →
  le fork doit avoir un **registre de base par plan** (comme les banques de sprites, §48). ≈ 17 tables par décor à
  allonger ; règle de choix du décor à ajouter (SFA3 : décor = perso adverse).
- Coût : ≈ 3,3 Mo de ROM graphique pour les 18 décors de persos ; ½ à 1 jour par décor une fois la chaîne en place.
- Musiques SFA2 : difficile (programme Z80 + 4 Mo d'échantillons, ~12,7 Ko libres dans la ROM Z80 de SFA3 → fork son).
  Persos : rien à ajouter (Hyper a déjà les versions SFA2).
- Premier pas proposé, après Upper : greffer un décor (Ryu) dans le banc SFA3 en Lua (registre de base prototypé
  dans `banc_plans.lua`).

**Résolu (§112)** : le balayage vert « STREET FIGHTER ALPHA3 » est **normal** (confirmé par l'utilisateur sur PS2 ;
état PCSX2 copié : `work/etats_ps2/survival_transition.p2s`, empreinte `72CE7A38`). Fin de la passe SFA3 →
reprise d'Upper (`ro5`, faute image 1386, §108).

### 114. Upper : l'attraction tourne en boucle (12 000 images sans exception)

`diag.py` suit `MODULE` (profils : dossier de travail, ROM de sortie, `BANC_DIR`) ; scripts Lua communs dans
`work/mame`. Deux fautes corrigées, toutes deux dans du code du recompilateur RÉCENT (style Hyper) :

1. **Image 1386 (objet $23, état $13)** : « si / sinon » sur `A8` — `A8 = T1 (0x6283 90) ; si $8D17(A5) : A8 = T2 ;
   MOVE.W 0(A8,D0.W),$12(A6) ; MOVE.B 2/3(A8,D0.W)…` (mips `0x1CB854`-`0x1CB920`). Le planificateur des registres
   prêtés (`extra_regs.plan`) voyait deux durées de vie ; le `BEQ` qui saute la 2e écriture entre dans la 2e →
   zone refusée → lectures perdues (`D0` = état de l'objet faux). **Corrigé** : fusion de deux durées de vie
   consécutives quand un branchement parti de la 1re atterrit dans la 2e (`MERGE_IFELSE`, 6 fusions ro3, 15 ro5).
2. **Image 2603 (pile épuisée)** : la fonction mips `0x227BD0` se rappelle elle-même tant que
   `0x23B520` (« `MOVE.B $2C8(A6),D0 ; CMP.B $A(A6),D0 ; RTS` ») dit « différent ». Le CMP était perdu : la forme
   « drapeaux exacts » du recompilateur récent (`subu ; andi ; nor/and/or ; andi 0x80 ; RES = -RES si V`) écrit
   RES loin du `subu` ; `flags_to_caller` exigeait ±8 octets. **Corrigé** : accepte aussi une écriture de RES du
   bloc exact (`keep_pend`). Drapeaux rendus à l'appelant dans ro5 : 92 → 118 (ro3 : 143, inchangé).
   Outil : trace du débogueur avec `{tracelog "SP=%X ",sp}` (les prises d'opcodes voient la prélecture : SP
   trompeur).

Résultat : attraction d'Upper en boucle (CAPCOM, intro, démos de combat, retour), 12 000 images sans exception.
Graphismes illisibles : la ROM graphique est celle de SFA3 → prochain chantier = banc graphique d'Upper (banques
`e351`/`e355-e386`, plans `e352/e354/e387`). ro3 : non-régression verte.

### 115. Banc graphique d'Upper (avec la ROM graphique de SFA3) ; limite → fork MAME

`banques.py` suit `MODULE` (ro5 : communs `e351`, décor `e353`, persos `e355-e386`, table perso → banque
`0x628320` × 40, 3 sites natifs) et écrit dans `work/mame_ro5/banques/` (toujours contre la ROM SFA3 du banc).
`banc_sprites.lua` / `banc_plans.lua` : dossier des tables `BANC_BANQUES`. Lancement Upper :
`BANC_BANQUES=<hsfa>/work/mame_ro5/banques/ BANC_PTR_ANIM=FF40BC BANC_GFX_INTRO=456 BANC_DIR=<hsfa>/work/mame_ro5/`
+ `-rompath work/mame_ro5/roms_ro5`.

Couverture dans la ROM graphique de SFA3 : persos communs 75-99 % ; Juli/Juni `e381/e382` ~50 % ; **Guile, Fei-Long,
Dee Jay, T.Hawk (`e383-e386`) : 67 à 126 tuiles sur 6 400-8 400** ; fichiers natifs `e419-e454` ~12 %, intro
`e455-e457` > 90 % ; décor : plan1 47 283 / 169 984, plan2 30 055 / 42 496. Il manque ≈ 5-6 Mo de tuiles, la ROM
graphique CPS2 (32 Mo) est pleine → **le banc Upper complet exige le fork MAME** (§109) : région graphique
étendue (ex. 64 Mo, bit 15 du mot Y de l'objet = bit 18 du code de tuile) + ROM programme pour le bloc `$C80000`.

Résultat (captures) : attraction d'Upper lisible — logo, portraits de l'intro, démos (décors de Chun-Li, Blanka…),
classement des scores avec HWK / GIL. Restes : blocs de décor manquants (magenta), couleurs ternes d'un perso de démo
(palettes d'Upper : profil `palettes=None`), plan scroll3 (équivalent de `e312` non identifié).

### 116. Fork MAME `sfa3hx` : ROM graphique de 128 Mo ; les nouveaux persos d'Upper s'affichent

Sources MAME 0.285 (`git clone --depth 1 --branch mame0285`) dans `<hsfa>/mame-fork/mame`, binaire réduit au pilote
CPS2 (`make SUBTARGET=cps2f SOURCES=src/mame/capcom/cps2.cpp TOOLS=0 USE_QTDEBUG=0 …` ; Qt absent → `USE_QTDEBUG=0`) :
`mame-fork/mame/cps2f`. Patch et mode d'emploi : `tools/mame-fork/`. Jeu `sfa3hx` (clone de `sfa3ud`) :
- région `gfx` de 128 Mo ; `HSFA_GFX` chargé en `$2000000` après le réordonnancement (format interne : 128 o / tuile,
  ligne = 8 o, 4 octets = plans bit 0..3, pixel x au bit 7-x ; vérifié 263/263 contre un vidage de la région) ;
- code d'objet : `+ (X & $0C00) << 8` (bits 18-19) — X & $3FF seul sert à la position ; Y bit 15 = marqueur de fin ;
- `$A00000-$CFFFFF` en ROM remplie depuis `HSFA_EXT/ext_<adresse>.bin` (prévu pour remplacer `banc_mem.lua`) ;
- `HSFA_CLOCK` : échelle d'horloge du 68000 (MAME : 0,7375, « hack » des attentes RAM non émulées).
Les messages « Driver mmancp2u… 1 errors » au lancement = validation de pilotes absents du binaire réduit (sans effet).

`hsfa_gfx.py` (MODULE=ro5) : tuiles des banques absentes de la ROM SFA3 → dédoublonnées, codes `$40000+`,
`work/mame_ro5/hsfa_gfx.bin` (**49 984 tuiles, 6,1 Mo**) ; tables étendues dans `work/mame_ro5/banques_hx/` (celles de
`banques/` restent valables pour MAME stock). `banc_sprites.lua` : bits 16-17 → Y, 18-19 → X 10-11.
Lancement : `HSFA_GFX=<hsfa>/work/mame_ro5/hsfa_gfx.bin BANC_BANQUES=<hsfa>/work/mame_ro5/banques_hx/ BANC_PTR_ANIM=FF40BC
BANC_GFX_INTRO=456 BANC_DIR=<hsfa>/work/mame_ro5/ cps2f sfa3hx -rompath work/mame_ro5/roms_fork` (lien `sfa3hx` → `roms_ro5/sfa3ud`).

Résultat : Dee Jay (contre Dhalsim) et Guile (contre Blanka) dessinés dans les démos d'Upper. Restent : palettes
(Dhalsim, Blanka, Guile aux couleurs fausses) et plans de décor — confiés à un agent (`work/agent_pal_ro5/`). Agents en
cours aussi : son d'Upper (`work/agent_son_ro5/`), mise en route d'Hyper (`work/agent_ro9/`), index du journal
(`work/agent_doc/`).

### 117. Documentation remise à plat

`docs/INDEX-HANDOFF.md` (index par thème, numéros de ligne, sections dépassées signalées) et `docs/ETAT-DES-LIEUX.md`
(état, commandes exactes, variables d'environnement, pièges encore vrais). Corrections relevées :
- l'empreinte md5 de `sz3ud.03c` citée au §109 est périmée depuis les correctifs §110-§114 : référence actuelle
  `9248db4e562fadc28e00bebba27dbfea` — **remplacée au §121 par `239141f3…`** (garde-fou : ro3 reconstruit avec `MODULE=ro3` doit la redonner tant que le
  traducteur ne change pas) ;
- `nonreg.sh` ne couvre que SFA3 (ro3) : pas encore de non-régression pour Upper ;
- EEPROM du fork : `~/.mame/nvram/sfa3hx` en lecture seule, comme `sfa3ud` ;
- extension du code d'objet du fork = bits 10-11 de X (§116), et non le bit 15 de Y envisagé au §115 (marqueur de fin).

### 118. Son d'Upper : la boîte aux lettres QSound était perdue ; le Z80 d'Upper n'a pas les musiques

Étude par agent : `work/agent_son_ro5/SON-ro5.md` (+ `gen_son.py`, copié dans les outils).
- Données son d'Upper **brutes** dans X_DATA : Z80 = entrée **388** (294 912 o = région `audiocpu`), QSound = **389**
  (8 Mo = région `qsound`, fichiers ROM = mots échangés) ; même format que SFA3 (287/288 : `gen_son.py ro3` redonne
  `sz3.01/02/11m/12m` d'arcade octet pour octet). `gen_son.py ro5` → ROM son d'Upper (tiennent dans les régions).
- **Le Z80 d'Upper n'a AUCUNE musique** (commandes `0001`-`002F` muettes, instruments absents ≈ 1,8 Mo) : bruitages et
  voix de SFA3 + 101 sons propres (`05`/`0A` 60-96, `06` C0-F5). Sur PS2, la musique d'Upper vient d'ailleurs.
- **Défaut du traducteur** (vraie cause de l'intro bloquée en scène 0 au §108) : le test « Z80 prêt »
  `CMPI.B #$FF,$61801F` (mips ro5 `0xCE174`-`0xCE234`, forme « drapeaux exacts » du recompilateur récent) était
  perdu → `BNE` sur des drapeaux périmés → aucune commande son. **Corrigé** : la lecture ABSOLUE est propagée par
  `dsll32/dsra32` et acceptée comme opérande `('abs', taille, adresse)` d'une comparaison exacte. Upper envoie
  `FF00`, `FF05/00A0`, `FF07`, puis les musiques et bruitages.
- **Banc (option B)** : ROM son de **SFA3** + repère de musique d'Upper `musique=(0x5081c, 0x5098c, 0xc38e)` (profil
  ro5) → l'intro d'Upper suit la musique (agent : repères `01`→`3B` à 2 images de ro3). Les sons propres à Upper
  (voix `0A61`-`0A75` des démos…) restent muets.
- **Fork, plus tard (option C)** : ROM hybride Z80 d'Upper + musiques de SFA3 → région `qsound` de 16 Mo (marche à
  suivre dans SON-ro5.md §… ; `audiocpu` 0x50000 suffit, 0x2A000-0x4FFFF libre).
- ro3 inchangé octet pour octet (md5 `9248db4e…`), non-régression verte.

### 119. Upper : palettes justes (pas de défaut), plan 32×32 = `e525` ; besoin du fork : base par plan

Étude par agent : `work/agent_pal_ro5/PALETTES-PLANS-ro5.md` (+ scripts, planches).
- **Palettes** : table moteur d'Upper en fichier **`0x5072B0`** (exéc. `0x6F72B0`), **40 décalages SIGNÉS** (T.Hawk `$23`
  et Shin Akuma `$24` ont leur bloc avant la table ; `$25/$26/$27` reprennent Balrog, Ryu, Juli), 30 palettes par
  perso ; palettes d'effets `0x510540`. **Règle changée par Upper** : groupe = couleur (0-5), et non
  `(ism+1)×2 + couleur` (68K `$037D1C`). Le Dhalsim « terne » de la démo = sa vraie couleur n° 4 (palettes 20-24,
  identiques à l'arcade) : **pas de défaut**. Profil ro5 `palettes=0x5072B0` ; `mame_test` (MAX_PAL) lit 40 entrées
  signées sous ro5. À confirmer : C natif du portage traduit à tort en 68K (mips `0x406CC0`, `0x407990`, écrans console).
- **Plan scroll3** : conteneur **`e525`** (= `e312` + 504 tuiles insérées en `$D59-$F50`), 4 576 tuiles dont 4 015 dans la
  ROM SFA3 ; `banques.py` (ro5) l'écrit sous le nom `f312.bin`. Blocs magenta disparus (titre, décors).
- **Tuiles de plan absentes de la ROM SFA3 : 1,29 Mo** (8×8 : 6 254 = 0,38 Mo ; 16×16 : 5 401 = 0,66 Mo dont 2 358
  objets de l'emplacement 1 — polices, kanji, plaques, portraits ; 32×32 : 518 = 0,25 Mo). Décors neufs de l'intro à
  `$FF8100` = `$40/$42/$44/$46/$4A` (hypothèse : Guile, Fei-Long, Dee Jay, T.Hawk, Balrog).
- **Fork (à faire)** : la CPS2 lit les trois plans dans une seule fenêtre fixe de 8 Mo (quart 1 de la ROM graphique ;
  scroll3 masqué `& $3FFF`), pleine dans SFA3. Il faut **un registre de base par plan** (ex. `$804200-$804205`,
  unité 64 o = `(BASE << 16) + (code << décalage)`, BASE = 2 par défaut, tilemap invalidée au changement).
  Option recommandée : ranger les mémoires de décor d'Upper telles quelles dans la ROM étendue (≈ 9,2 Mo, ordre
  local) → bases constantes, plus de tables de renumérotation ni de prise sur les tilemaps. La zone de tuiles remplie
  à l'exécution (§84) demandera une région graphique inscriptible. Même besoin pour les décors de SFA2 (§113).

Résultat au banc (fork) : écran titre avec le logo, décors des démos propres, classement avec D-J / HWK / GIL. Reste :
cartouche du titre en aplat blanc (objets ?), tuiles de plan neuves (fork).

### 120. Fork : une base par plan ; les mémoires de décor d'Upper rangées telles quelles

Pilote (`cps1.h` / `cps1_v.cpp` / `cps2.cpp`, patch `tools/mame-fork/`) : registres **`$804200-$804205`** = base de
scroll1 / scroll2 / scroll3 en unités de 64 Ko de la région graphique (0 = mappage CPS d'origine, comportement
inchangé pour les autres jeux) ; avec une base, le code brut de la tilemap est un indice LOCAL :
`élément = (base << 16) / taille + code` (64 o pour 8×8 — deux moitiés, choisies par la parité de colonne —, 128 o
pour 16×16, 512 o pour 32×32) ; tilemap invalidée au changement de base. `HSFA_GFX` = liste `fichier[@décalage]`.

`hsfa_plans.py` (MODULE=ro5) → `work/mame_ro5/hsfa_plans.bin` (12,8 Mo, chargé en `$3000000`) : mémoire de décor `e353`
vue en 8×8 (65 536, en `$3000000`, base `$300`) et en 16×16 (42 496, en `$3400000`, base `$340`), conteneur 32×32 `e525`
(4 534, en `$3A00000`, base `$3A0`). Objets de l'emplacement 1 : `banques_hx/plan2.bin` = `$68000` + indice local.
`banc_plans.lua` : `HSFA_PLANS=300,340,3a0` → écrit les bases et n'installe AUCUNE prise (plus de renumérotation).
Lancement Upper complet :
`HSFA_PLANS=300,340,3a0 HSFA_GFX=<travail>/hsfa_gfx.bin,<travail>/hsfa_plans.bin@3000000 BANC_BANQUES=<travail>/banques_hx/
BANC_PTR_ANIM=FF40BC BANC_GFX_INTRO=456 BANC_DIR=<travail>/ cps2f sfa3hx -rompath <travail>/roms_fork`.
Rendu identique à la méthode par tables (§119) → les tuiles de décor neuves d'Upper sont désormais atteignables.
Ouvert : cartouche du titre d'Upper (62 objets de l'emplacement 1, codes `$1E2C-$1F96`, tuiles présentes à 72 % de
couleur 15) en aplat blanc → palette ou couche manquante ; à comparer avec un état PCSX2 de l'écran titre d'Upper.

### 121. Upper : logo du titre et objets communs ; deux défauts du traducteur ; Hyper démarre

**Emplacement 0 d'Upper** : `banc_sprites.lua` figeait la banque commune sur `e254` (SFA3) → pour Upper (`e351`), TOUS
les objets de l'emplacement 0 étaient écartés (logo du titre, textes…). `BANC_COMMUN=351` pour Upper. Méthode : état
PCSX2 de l'écran titre d'Upper (`work/etats_ps2/upper_titre.p2s`, menu ARCADE ; `upper_titre_start.p2s`, PRESS START),
module identifié par comparaison du code en RAM (ro5 464/464) ; objets, tilemaps, défilements, registres de plans
et palettes identiques au banc → seule différence = objets non dessinés. Mémoire de décor PS2 (`0xD35800`) =
`e353` statique octet pour octet ; table des emplacements en `0x1DC2E4` (emplacement 0 `0xBC7000`, 1 `0xD35800`).
Logo d'Upper désormais identique à la capture PS2. **Démos d'Upper sans barres de vie = normal** (utilisateur).

**Deux défauts du traducteur** (trouvés par l'agent Hyper, `work/agent_ro9/MISE-EN-ROUTE-ro9.md`) :
- `extra_regs.plan` (`BACK_AFTER`) : retour de boucle venant d'APRÈS une zone de registre prêté et visant
  l'instruction qui suit la zone → la restauration était rejouée à chaque tour (pile déséquilibrée, domicile de A8
  écrasé). Zone refermée avant l'étiquette (A8 et D8). Défaut latent aussi dans SFA3 (mips `0x1F1800`) et Upper.
- `byte_streams_pre` : `SUBQ.W #1,An ; MOVE.B 1(An),<ea>` (flux d'octets décroissant) → adresse exacte à l'exécution.
ROM SFA3 changée : **md5 `sz3ud.03c` = `239141f30d0fe15b2524b63eb80372e4`** ; non-régression verte ; Upper 12 000 images.

**Hyper (`ro9`)** : profil ajouté (points d'entrée identiques à Upper, MIPS masqué ; aucun chargeur natif de tables
d'animation ; fichier fixe 547 en `$C84000` ; fin des données en bloc externe **`$940000`** via `data_ext`, marqué
`$01000000` dans la conversion), `hooks_fork_ro9.json`, travail `work/mame_ro9`. `banc_mem.lua` lit aussi
`BANC_DIR/ext_liste.txt` (blocs externes écrits par `mame_test.py`). `MODULE=ro9` : 12 000 images sans exception ;
l'agent est allé jusqu'aux combats TRAINING (4 versions de persos). Pas de démo d'attraction : l'écran-titre attend
Start (à confirmer sur PS2). Prochain : banques graphiques d'Hyper (SFA1 208-220, SFA2 229-248, Upper 355-386, table
`0x5AF1B0` × 128), VERSUS à 2 joueurs, 126 écritures de registre tombées. ⚠ MAME sans `-nvram_directory` partage
l'EEPROM `sfa3ud` : en parallèle, utiliser un dossier NVRAM par essai.

### 122. Upper jouable de bout en bout : Bison, fins des nouveaux persos

Partie Arcade complète (`tournee.lua`, fork `sfa3hx`) avec Ryu, Guile, Fei-Long, Dee Jay, T.Hawk : combats, fin du perso,
générique, GAME OVER, nouvelle partie — sans exception. Les 4 modes de sélection d'Upper (NORMAL / MAZI / SAIKYO /
CLASSIC) passent la conversion (choix et enchaînement vérifiés ; effets en combat non vérifiés). Défauts corrigés :

1. **`daddu` = copie de registre** (fonction SPECIAL `0x2D`, 583 / 559 / 802 sites dans ro3 / ro5 / ro9, toujours avec
   `zero`) : décodé comme `addu` (`mips.py`). **Copies suivies** (`addu/or rd,rs,zero`) : `rd` hérite de tout ce que l'on
   sait de `rs` (valeur symbolique, lectures mémoire / absolue / indexée, taille) ; `zero+zero` = constante 0
   (`translate.py`, `COPIES=0` pour couper). Sans cela, l'opérande d'un CMP « drapeaux exacts » était perdu.
   Signature d'audit : `BRA (cible +$10)` précédé d'un bloc `subu/nor/andi 0x80` sans comparaison émise : 18 → 4 dans ro5.
2. **Épilogue `lq`** : le BRA vers l'épilogue rend les drapeaux à l'appelant aussi quand l'épilogue restaure des registres
   (`lq …,sp` / `ld ra` / `addiu sp`) avant `jr ra`. C'est le « test de sol » du §80 (`MOVE.W $16(A6),D0 ; CMP.W $64(A6),D0`)
   en version Upper (mips `0x3DEDB4`) : Bison volait sans fin (Psycho Crusher / téléportation), la manche ne finissait
   jamais. ro5 : 118 → 126 drapeaux rendus ; ro3 : 143 → 146.
3. **Chargeurs d'animation natifs d'Upper** (`assets_natifs.py`, `mame_test.py`) :
   - **`LOAD_BASE` = `$B83800`** (tous les fichiers d'animation d'Upper ; `$B83000` était repris de SFA3 : pointeurs
     internes faux → liste de sprites démesurée, pile écrasée, saut dans les données) ;
   - **chargeur de FIN** `0x4114A0` (homologue de ro3 `0x3837D0($132)`), table `0x6283C0` (gfx 391-418 / anim 458-485),
     index = **octet bas de D8** (domicile `$87F1(A5)`) : talon dédié, site `0x272D50` ;
   - chargeur par perso `0x4113A0` : index = résultat de la native `0x2141A0`(joueur) = table `0x60AD90` (identité sauf
     variantes ; ⚠ `lui 0x61 ; addiu 0xAD90` = `0x60AD90`, immédiat signé) → talons par joueur, 6 sites ;
   - `banques.py` : paires du chargeur de fin dans `carte.txt` (graphismes de l'emplacement 4) ; ROM étendue d'Upper
     régénérée : **55 979 tuiles** (au lieu de 49 984).
ro3 : md5 `sz3ud.03c` = `de6dbf67b0f425eac495d4a079645ac7`, non-régression verte. Les `hooks_fork_ro3/ro5.json` sont
désormais publiés (le dépôt ne pouvait pas reconstruire SFA3 / Upper sans eux, relevé par l'agent d'architecture).
Restent : 4 blocs « drapeaux exacts » non reconnus dans ro5 (`0x4FF38`, `0x500DC`, `0x263984`, `0x263A80`), la couleur du
perso sur la carte du monde, les effets des modes MAZI / SAIKYO / CLASSIC.

### 123. Documentation d'architecture et carte des symboles

- **`docs/OUTILS.md`** (agent d'architecture) : pipeline complet (schéma), une fiche par script actif (rôle, entrées /
  sorties, variables, fonctions, §), scripts historiques, banc Lua, fork, formats de données, recettes (ajouter un
  module, traiter une faute, ajouter une banque), relevé de 24 incohérences code / journal. Nouveau
  `tools/untranspile/README.md` (français) qui y renvoie. Propositions de docstrings : `work/agent_archi/docstrings-a-ajouter.md`
  (non appliquées : à faire au fil de l'eau).
- **`docs/SYMBOLES.md` + `tools/symboles/`** (agent des symboles) : `symboles_ro3.csv` = 10 246 symboles de SFA3 (fonctions,
  variables A5, champs joueur / objet, tables, registres) avec leurs adresses dans les TROIS espaces (68K arcade, MIPS,
  68K traduit) quand elles sont établies ; 6 302 fonctions avec les trois adresses ; noms tirés du journal et du code.
  `construire.sh` / `annoter.py` régénèrent la carte annotée (`work/agent_symboles/carte_annotee_ro3.txt`, hors dépôt :
  listing dérivé du jeu). Corrections apportées au journal par le code : TRAP #4-#7 du noyau décodés ; entrée arcade de
  la tâche d'attraction = `$4036` (les « ROM $617C / $6328 » du §62 étaient des adresses de l'image traduite) ;
  `joueur_init` = `$27BAE` ; émetteur de frames 08 = `$21992`. Esquisse pour Upper : `work/agent_symboles/symboles_ro5_esquisse.csv`.
- Incohérences relevées et corrigées depuis : `hooks_fork_ro3/ro5.json` publiés (§122) ; `0x1158` = retenue C (le
  README publié disait N). Restent notées dans `OUTILS.md` : le fork ne lit `HSFA_EXT` que pour 7 adresses fixes (Hyper
  `$940000` / `$C84000` non servis par le fork), `nonreg.sh` ne couvre que ro3.

### 124. Comparaison exacte sur un octet indexé ; carte du monde d'Upper à vérifier

- **Opérande `d8(An,Dn)`** accepté par les comparaisons « drapeaux exacts » (`_src_ea` / `enc_cmp` ; octet indexé marqué
  `[index pair suppose]` → adresse exacte à l'exécution par `byte_index_exact`). Upper mips `0x4FED4` :
  `CMP.B 2(A1,D2.W),D0` rétabli. Blocs non reconnus restants dans ro5 : 3 (dont `0x263918` : comparaison des octets
  perso `$102` de deux structures, dont une par **A8 hors zone de registre prêté** → demanderait un temporaire ;
  probablement la couleur alternative d'un combat miroir). ro3 inchangé (md5 `de6dbf67…`).
- **Carte du monde d'Upper** : sur l'arcade et dans la traduction de SFA3, portrait du perso à gauche + sprite en couleurs ;
  dans Upper au banc : pas de portrait, sprite en silhouette vert-bleu. Objets de la carte = emplacements 0 et 1
  seulement (aucun objet de portrait) ; mémoire de décor PS2 identique au fichier `e353` ; les chargeurs natifs par
  perso / de fin écrivent leurs graphismes en `ctx+$48` (emplacement 6, `0x1495800` sur PS2). Table des emplacements
  PS2 (`ctx` = `0x1DC2B0`) : 0 `0xBC7000`, 1 `0xD35800`, 2 `0x1356800`, 3 `0x13F6000`, 4 `0xB87000`, 5 `0x1265800`,
  6 `0x1495800`, 7 `0x1535000`. **À trancher avec un état PCSX2 de la carte d'Upper.**

### 125. Upper : le mode Arcade allait droit à Bison (BTST à bit dynamique rendu à l'appelant)

États PCSX2 de l'utilisateur (ISO de travail, module ro5 vérifié identique 1 003/1 003) : `upper_carte` (NEXT STAGE,
Evil Ryu → Vega), `upper_histoire_04` (écran d'histoire entre deux combats : grande illustration de Ryu + texte),
`upper_histoire_05` (NEXT STAGE, Japon, Karin). Sur PS2 `$114(A5)` = 1 (2e adversaire) ; dans le banc, 9 = la limite
`$14C` dès le début → Bison puis la fin (et jamais d'écran d'histoire).
**Cause** : la recherche du prochain adversaire d'Upper (mips `0x250F88`-`0x2510E0`, liste en `$C0C0(A5)`, masque des
battus étendu : `+$140` long + **`+$144` mot** pour les ID 32-39) appelle `0x251CC0` = `CMPI.B #$20,D1 ; BCC ; BTST
D1,D2 | BTST D1,D3 ; RTS` (bit dynamique, drapeaux rendus à l'appelant). `flags_to_caller` ignorait le test en attente
`btst_dyn` → BNE sur des drapeaux périmés → la boucle courait jusqu'à la limite. **Corrigé** (type `btst_dyn` accepté,
`BTST Dn,<ea>` émis devant le RTS / le BRA vers l'épilogue). Drapeaux rendus : ro5 126 → 135, ro3 146 → 153.
Résultat : parcours Arcade normal (Adon, …), écran d'histoire avec l'illustration du perso, NEXT STAGE, VS ; 9 manches
en 16 000 images sans exception. ro3 : md5 `75afdfff9ba77f2652ed83da371e9241`, non-régression verte.
À vérifier : teinte de l'illustration d'histoire (paraît plus sombre que la capture PS2 : fondu ou palette).

### 126. Upper : Adon sans fin (drapeaux rendus écrasés par l'épilogue partagé), échanges de registres par la pile

- **Symptôme** (après §125) : en Arcade, le combat gagné, la carte renvoie toujours vers le **même** adversaire (Adon
  pour Ryu) ; en SURVIVAL idem. Le balayage des fins avec `FORCE=Lff8540=ffffffff` tournait aussi en rond (masque forcé
  ignoré).
- **Cause** : `0x251CC0` (« adversaire battu ? ») = `CMPI.B #$20,D1 ; BCC ; BTST D1,D2 ; BRA fin | BTST D1,D3 ; fin: RTS`.
  Le test rendu à l'appelant du chemin qui TOMBE dans l'épilogue était émis à l'adresse du `jr ra` ; or l'épilogue du
  recompilateur récent commence par des restaurations (`lq ..,sp`, `ld ra`, `addiu sp`) sans traduction : le BRA de
  l'autre chemin (cible = 1re restauration) atterrissait sur ce `BTST D1,D3` → pour les ID < 32, bit de `+$144` (vide)
  → jamais battu. **Correctif** (`FTC_AVANT`, défaut 1) : quand une instruction de l'épilogue est cible d'un
  branchement, le test rendu est placé à l'adresse de l'instruction qui PRÉCÈDE les restaurations ; les BRA tombent sur
  le RTS. ro5 : 94 cas, ro3 : 96. (Essai écarté : BRA → RTS direct ; casse les zones A8/D8 qui restaurent la pile.)
- **Liste des décors de SURVIVAL** (`0x2505E8-0x2506C4` : `D8 = (A8)+ ; si T[D8+$50] = 0 : (A2)+ = (A3)+`) :
  - zone A8 refusée (retour de boucle à 0xC0 octets du dernier accès > 0x40) → lecture `(A8)+` perdue.
    `extra_regs.LOOP_EXT` (défaut 0x100) : zone acceptée (ro3 +1, ro5 +1). Option `PARTIAL_LIVE` (sb/sh ne coupent
    pas une durée de vie) laissée à 0 : moins de zones, et D8 a déjà son domicile `$87F0`.
  - `byte_streams` reconnaît le flux `(A4)+` même avec une ouverture de zone D8 intercalée entre ADDQ et MOVE.B.
  - **valeur de table seulement testée** (`lb` d'une table indexée → RES) : rien n'était émis (`TBL_TST`) →
    `MOVE.L Dk,-(SP) ; MOVE.B T(PC,Dn.W),Dk ; MOVEM.L (SP)+,Dk` (MOVEM ne touche pas CCR ; trois entrées : l'assembleur
    reconnaît la lecture de table à son 1er mot). Seulement si aucun registre 68K n'a été écrit depuis la lecture
    (sinon `D0 = T[D0]` : drapeaux déjà posés et index changé — 1re version : SFA3 plantait, mips `0x187BE8`).
    ro3 8, ro5 8.
- **Division par zéro / erreur d'adresse en combat** (balayage : persos 01, 04, 05, 07, 09, 0c…) : aiguillage de
  script d'objet `0x145448` sur un pointeur en RAM (`$FFB200`, commande impaire). Origine : `0x3BBD8` échange `A1`/`A6`
  autour de l'appel de `0x2486B0` **par un temporaire de la pile MIPS** (`tmp = A1 ; A1 = A6 ; A6 = tmp`), traduit
  `MOVEA.L A6,A1 ; MOVEA.L A1,A6` → le joueur `$FF8400` perdu, l'objet `$FFAB00` traité en joueur (`ADD.B D8,$2CC(A6)`
  écrit dans l'objet voisin `$FFAD80`). La détection d'EXG existante évaluait la valeur de la 2e écriture AVANT sa
  relecture depuis la pile : `_spill_an` (`EXG_PILE`, défaut 1) suit le temporaire. ro5 ≈ 58, ro3 18.
- Méthode de trace d'un plantage déterministe : `-debug` change le déroulement (autre adversaire) → `SAVEAT`/`SAVENAME`
  de `tournee.lua` sans débogueur, puis rechargement (`manager.machine:load`) sous `-debug -debugger none` et
  `trace ...,{tracelog "D0=%X A0=%X A1=%X A6=%X ",d0,a0,a1,a6}` ; prise d'écriture Lua pour trouver l'écrivain.
- **Aiguillage à index déjà ×4** (`SW_X4`) : `LSL.W #2,D0 ; JSR T(PC,D0.W)` d'origine (table de BRA.W) ; le
  recompilateur lit sa table de pointeurs sans `sll` (échelle 1) ; la table de mots reconstruite veut 2·i →
  `LSR.W #1` avant la lecture (Upper mips `0x1003F0`, perso 0x21 : D0 = 8 → 5e entrée, erreur d'adresse). ro5 2, ro3 0.
- **Coupure des données au début d'un bloc de perso** (profil `blocs=(0x61A100, 32)`, `mame_test.coupe`) : contre
  Bison/Juli-Juni, erreur d'adresse sur un pointeur d'animation `0x8E4BE4 + $45E4 = 0x8E91C8` calculé à
  l'exécution (table + décalage 16 bits) de part et d'autre de la coupure `0x8E7000` (§108 : fin des données en bloc
  externe `$C80000`) → converti avec le décalage de la zone principale (`$37F508`, données d'autre chose).
  Coupure placée au début du bloc le plus haut sous la limite : `0x8E4AE0` (bloc externe 767 648 octets).
- **Comparaison exacte à constante `lui` seule** (`LUI_IMM`) : `lui s2,5` (= #$50000, mot bas nul, pas d'`ori`)
  n'était pas reconnu comme immédiat → bloc exact long abandonné (`BRA` interne parasite + `BPL` sur drapeaux
  périmés). Vega (Upper mips `0x383710`, `CMPI.L #$50000,$40(A6) ; BGE`) restait accroché au grillage après un
  TIME OVER, la manche ne finissait jamais. ro5 20, ro3 4.
- **`tournee.lua`** : adversaires = toutes les structures joueur actives (`$FF8800`, `$FF8C00`, `$FF9000`) — le combat
  contre **Juli et Juni** (J2 inactif) n'était jamais détecté (nuls sans fin). Ce n'était pas un défaut du jeu.
- **Audit des blocs exacts perdus** (`translate.EXACT_MISS` → `<travail>/audit_exacts.txt`) : bloc « drapeaux
  exacts » reconnu mais opérande inconnu = comparaison perdue sans trace (cas de Vega). Avant : ro5 **49** (uniques),
  ro3 1. Corrigés (`CONST_OP`) : constante 32 bits `lui+ori/addiu` (40 blocs longs d'Upper, ex. `CMPI.L
  #$A2C000,$C040(A5)` → `#$190C000`, adresse vidéo marquée, cohérente avec les écritures du pointeur) ; `sw zero` et
  `lui` seul rangés sur la pile MIPS (`CMPI.B #0`, `CMPI.L #$20000`). Restent ro5 **5** : `0x1D0EA4` (`CMPI.L #-1` sur
  un long indexé `(A0,D0.W)`), `0x261CE0` (temporaires 128 bits `sq`/`lq`), `0x263918` / `0x263A14` / `0x26D97C`
  (lectures **A8 hors zone** : combat miroir…). ro3 : 0.
- Non-régression SFA3 verte (3 × aucune exception, 42/42, 133,3 %), md5 `61c2279b6f25264903c52f1e19fd2843`.
- **Validation** : balayage des 40 fins d'Upper sur le fork (`tournee.lua`, `PERSO=00..27`, 90 000 images, sans
  `FORCE`) : **38/40 fins atteintes et terminées**. Restent : Guy `07` (gagne au temps, 16 manches en 90 000 images :
  durée, pas un blocage) et `22` : division par zéro à l'image 84 636, **dans la 2e partie après sa fin**, au début
  d'un combat contre `$21` sur le décor `$42` : l'objet `$FFC780` (type `$25`, créé par `$FFDE00` via `0x6ACE`) lit
  `[+$1C]+4` comme pointeur de script ; `+$1C` = `0x973304` (table par décor `0x971E70` + `$1494`, routine d'animation
  à entrées multiples `0x2C84A0`-`0x2C85C0`) où il n'y a que des paires de coordonnées (`0x0110/0x00C0`).
  **Corrigé au §128** (lecture signée étendue perdue) ; états MAME conservés : `work/etats_mame/sfa3hx/z22.sta` (image 84 600, recharger depuis Lua avec
  `work/etats_mame/trace_depuis_etat.lua` adapté) et `z02.sta` (Vega, avant correctif). NB : les adresses entre
  crochets des `JSR`/`JMP` de `carte_image.txt` (« `JMP $021174.L [mips 002edc10]` ») peuvent être périmées (calculées
  par `mips_to_68k` sur la carte précédente) ; la cible réelle est résolue par l'assembleur — lire les mots de la ROM.
- SFA3 : balayage des 32 fins refait (`FORCE`, comme §111) : 32/32 sans exception, nombres de captures = arcade (±1),
  planche arcade | traduction identique.

### 127. Son d'Upper : ROM son hybride (option C du §118) — musiques de SFA3 + sons propres d'Upper

Travail par agent : `work/agent_son_ro5/hybride/RAPPORT-option-C.md` (+ journaux, WAV, `essais.sh`).
- **Construction** (`tools/untranspile/gen_hybride.py`, + `z80son.py`, utilise `gen_son.py`) : même pilote Z80 dans
  les deux jeux (pointeurs linéaires 24 bits, sauts relatifs). Z80 d'Upper tel quel ; bloc des 44 musiques de SFA3
  (133 624 o, même alignement modulo 16 Ko) copié dans la zone libre d'Upper (banque 15 comprise) ; tables de
  programmes 0-2 et 114 échantillons de SFA3 ajoutés (banque +`$80`), nouvelle table de pointeurs de programmes en
  `$6B10` ; code : 5 octets (`$1919`, `$0907`, `$0913` — ce dernier reproduit l'échantillon parasite de SFA3 au départ
  des musiques, origine des adresses « `80AD` » du §118). QSound : e389 (Upper) en 0-8 Mo, e288 (SFA3) en 8-16 Mo.
  Sorties `hx3.01`, `hx3.02` (0x28000), `hx3.11m`-`hx3.14m` (mots échangés).
- **Fork** : région `qsound` de 16 Mo pour `sfa3hx` ; `init_hsfa` charge la ROM hybride si **`HSFA_SON=<dossier>`**,
  sinon la moitié haute recopie la basse (comportement inchangé). Patch `tools/mame-fork/` régénéré.
- **Vérifié** : les 44 musiques `0001`-`002F` écrivent au QSound les mêmes valeurs dans le même ordre qu'avec le Z80 de
  SFA3 (banque +`$80`) ; repère `$618021` `01`@447 … `3B`@1865, `00`@2044 (= option B) ; 153 commandes `05`/`0A` 60-96
  et `06` C0-F5 + 49 `0B` C0-F5 actives et identiques au Z80 d'Upper (voix `0A61`-`0A75` audibles, muettes en
  option B ; `0BE2`-`0BF2` dans la 2e démo) ; vérification statique des 3 072 commandes. WAV : niveau de l'intro égal
  à l'option B, voix 0 → présentes. Session principale : `nonreg_ro5.sh` vert avec le fork recompilé, et parties
  Arcade complètes (Ryu, Vega) avec `HSFA_SON` sans exception.
- **Restes** : décalages de 1 à 3 µs des écritures QSound par rapport à l'option B (historique Z80 différent ;
  corrélation 0,99) ; place libre du Z80 presque épuisée (~14,8 Ko en banque 15, zone fixe `$718D-$7FFF`) ; seules les
  commandes `0B` C0-F5 balayées dans `0Bxx`. Écoute de l'utilisateur à recueillir.

### 128. Upper : plantage du perso `$22` corrigé (lecture signée étendue perdue) ; SURVIVAL, VERSUS, entraînement vérifiés

- **Plantage `$22`** (ouvert au §126 : division par zéro / erreur d'adresse, décor `$42`, objet `$FFC780`) : l'index
  d'animation de l'objet valait `$FF`. Mips `0x413270` : `lb [$10D(A5)] ; dsll32/dsra32 ; sh D0` = `MOVE.B $10D(A5),D0 ;
  EXT.W D0` — **rien n'était émis** (le rangement d'une lecture mémoire dans un registre D ne gérait que les tailles
  égales et l'octet lu en mot) ; D0 gardait le `$FF` de `MOVE.B $124(A5),D0 ; OR.B $135(A5),D0`, puis `ADD.B $2(A6),D0`
  → entrée `$1FE` de la table d'animation (= 0) → `+$1C` = début de la table (coordonnées) lu comme script.
  **Corrigé** (`EXT_MEM`, défaut 1) : lecture signée (`lb`/`lh`, vérifiée sur l'instruction d'origine) plus étroite que
  le rangement → `MOVE` + `EXT.W` (+ `EXT.L`). ro5 4 cas, ro3 0 (md5 inchangé `61c2279b…`). Le perso `$22` passe
  l'image 84 636 et va à 95 000 sans exception ; `nonreg_ro5.sh` vert.
- **Guy `$07`** avec 180 000 images : fin atteinte et terminée → **Upper : 40/40 fins**.
- **SURVIVAL** (menu `MODE=2`, `MODE_ADR=FF4201`) : adversaires dans l'ordre de la variante 1 de la table `0x61B7A0`
  (05, 08, 11, 0B, 06, 0E, 1B, 07, 01, 04, 03, 09, 0C, 00, 02, 0F, 10…), un décor par adversaire, sans exception
  (30 000 images) — l'« Adon toujours » d'avant était le défaut du §126.
- **Mode 3** : combats successifs, J2 = Ken (partenaire ?), décors variés, sans exception. **Mode 4** = entraînement
  (chrono infini, Ryu contre Ken) : fonctionne.
- **VERSUS** (`MODE=1`) : `tournee.lua` gagne **`VS=1`** (pièce 2, Start J2 seulement à l'entrée du mode — plus tard,
  sur l'écran de sélection, il fait tourner le curseur aléatoire —, appuis J1 et J2 ; ⚠ les boutons de J2 sont sur
  le port **`:IN0`** comme ceux de J1). Validé sur SFA3 traduit (Ryu contre Akuma) puis Upper (Ryu contre Ken, avec la
  ROM son hybride) : sélection des deux joueurs, combat, écran suivant, sans exception.

### 129. MAX : Eagle dans Upper sur le fork (tuiles étendues de la session MAX)

- **Montage** (copie isolée `work/mame_max5`, les ROM d'Upper validées restent intactes) :
  - tuiles neuves MAX `~/.cache/sfa3max/fork/max_gfx.bin` (session MAX, codes `$4DAAB`-`$5C06B`) chargées juste après
    celles d'Upper : `HSFA_GFX=<ro5>/hsfa_gfx.bin,<max_gfx.bin>@26D5580,<ro5>/hsfa_plans.bin@3000000` ; table
    `pl26_hx.bin` copiée en `banques_hx/pl26.bin`, `BANQUE_J1=pl26` ;
  - bloc de frames d'Eagle : `MODULE=ro5 TRAVAIL=work/mame_max5 banques_max.py pl26 --fork` (pas de pose de tuiles,
    seulement le bloc) en **`$D40000`** (Upper : `$B04000-$B7DF4C` est déjà un bloc de frames du jeu ; MAX =
    `$D40000/$D80000/$DC0000/$E00000`, ajoutés à la liste fixe de `banc_mem.lua`) ;
  - `MAX_DEMO=pl26` sous ro5 : la correspondance de la session MAX est en adresses ro3 ; le bloc des frames de Ryu
    d'Upper a la même disposition à **+`$D75EC`** (codes de tuiles différents) → 15/20 frames retrouvées (en-tête
    identique) ; la session MAX a fourni ensuite la correspondance d'Upper complète
    (`~/.cache/sfa3max/converti/pl26/test_banc/frames_test_ro5.json`, 20/20, et `frame_map_ro5_ryu.json` : 391 frames
    PSP de Ryu ↔ ro5, note `max-frames-ryu-upper.md`), utilisée en priorité → **89 pointeurs redirigés** ;
  - palettes (`MAX_PAL`) : le bloc de l'ID 0 (Ryu) est partagé avec `$26` dans Upper → avertissement au lieu d'erreur.
- **Résultat** : `demo_max.lua` (marche avant/arrière, accroupi, garde, coup léger) : **Eagle propre**, couleurs justes,
  dans le décor d'Adon ; poses non redirigées déchirées (attendu) ; aucune exception. Planche :
  `work/notes/eagle_upper_fork_2026-10-04.png`. Session MAX prévenue.
- Lancement : `BANQUE_J1=pl26 PERSO=00 … BANC_BANQUES=work/mame_max5/banques_hx/ BANC_DIR=work/mame_max5/ cps2f sfa3hx
  -rompath work/mame_max5/roms_fork -autoboot_script demo_max.lua` (+ `HSFA_GFX` ci-dessus).
- **Suite** : vraie place `$26` (code et scripts d'animation d'Eagle traduits par la session MAX, boîtes de
  collision), puis Maki, Yun, Ingrid (`$27` + 2 places à créer).

### 130. Sorties latérales des zones A8/D8 (combat miroir) ; portraits MAX d'Eagle raccordés (NON TESTÉ) — ÉTAT À LA PAUSE

- **Sorties latérales** (`extra_regs.LATERAL`, `LATERAL=0` = ancien comportement) : une zone de registre prêté (A8/D8)
  dont un branchement sort ailleurs que par sa fin était refusée → lectures A8/D8 perdues (« lectures A8 hors zone »,
  ex. Upper `0x263918`/`0x263A14`, comparaison des persos `+$102` de deux structures = combat miroir). Désormais
  acceptée ; `translate` réécrit chaque sortie émise en `B<cond inverse> suite ; <restauration, drapeaux préservés> ;
  BRA cible` (`_zone_restore_ws`, compteur `LATERAL_REW`). Branchements internes vers `after` (aussi atteint de
  l'extérieur) traités de même + fermeture anticipée (Upper `0x26D8DC`). Sorties non émises par la traduction (gardes
  absorbées) : sans effet (pas de saut 68K). Zones : ro3 158 → 175, ro5 187 → 205. `audit_exacts.txt` : ro5 **2**
  restants (`0x1D0EA4` `CMPI.L #-1` sur long indexé ; `0x261CE0` temporaires 128 bits `sq`/`lq`), ro3 0.
  `DBG_PLAN=lo-hi` (extra_regs) affiche les refus de zone.
- **Validation** : `nonreg.sh` vert (3 × aucune exception, 42/42, 133,3 %), md5 ro3 **`f67bb0abc3d4da0ee9e027e608e341a3`** ;
  `nonreg_ro5.sh` vert. ⚠ **À FAIRE À LA REPRISE** : balayages complets des fins (SFA3 32, Upper 40) interrompus à la
  pause (SFA3 : 00-05 OK, le reste non fait) — relancer (`scratchpad` vidé : recréer `un.sh` d'après §111 / §126).
- **Portraits MAX (session MAX : `work/notes/max-portraits.md` §6)** : tuiles `~/.cache/sfa3max/fork/max_portraits_gfx.bin`
  (2 033 tuiles, 4 persos, code `$5C06C` = `@2E03600`), tables `p26..p29_portraits_hx.bin`, paquets
  `~/.cache/sfa3max/converti/plXX/portraits.*` (320×160 et 128×224, poses + entrée de `0x484C00` remplacée).
  `mame_test.py` : **`MAX_PORTRAITS=plNN`** (ro5, copie de travail seulement) : frames de type 8 + bloc de palettes
  de portrait (copie de celui de Ryu, 4 premières remplacées) en bloc externe **`$D60000`** ; table des palettes
  `0x53BDF0` et poses de `0x484C00` redirigées pour l'ID (`$26` = 38) ; `banques_hx/plan2.bin` de la copie prolongé :
  index locaux `$A60C + k` → global `$5C06C + k` (code de frame = index − `$1600`). Construit dans `work/mame_max5`
  (`MAX_DEMO=pl26 MAX_PORTRAITS=pl26`, 20 poses redirigées) — **pas encore lancé ni vérifié à l'écran**. Pour tester :
  ajouter `<max_portraits_gfx.bin>@2E03600` à `HSFA_GFX` (avec `max_gfx.bin@26D5580`), écran de sélection /
  victoire avec J1 = `$26` (Yun `$28` et Ingrid `$29` : table `0x484C00` limitée à 40 ID). Points à surveiller signalés
  par la session MAX : T des portraits PSP > maxima d'Upper (saturation possible), portrait vertical PSP 128×256.

### 131. Reprise : balayages des fins (outil permanent) ; portraits d'Eagle justes à l'écran

- **`balayage_fins.sh ro3|ro5 [persos]`** (nouveau, `tools/untranspile/`) : une partie Arcade par perso jusqu'à sa fin,
  en parallèle (`P`, 3), sorties dans `work/balayages/<module>_<date>/` (`res.txt`), plus de dépendance au scratchpad.
  ro3 : `FORCE` comme §111, comparaison aux captures de fin de l'arcade (`work/balayages/ref_sfa3_captures.txt`).
  ro5 : sans `FORCE`, 90 000 images (Guy `07` : 180 000).
- **SFA3 après §130** (md5 `f67bb0ab…`) : **32/32 fins**, captures = arcade (±1). Upper : balayage lancé (voir
  `work/balayages/ro5_*/res.txt`).
- **Portraits MAX — vérifiés à l'écran** (copie `work/mame_max5`, `MAX_DEMO=pl26 MAX_PORTRAITS=pl26`, J1 = `$26`,
  `HSFA_GFX=…,max_gfx.bin@26D5580,max_portraits_gfx.bin@2E03600,…`) : sélection (128×224) et victoire (320×160)
  **justes** (formes et couleurs). Captures : `work/notes/eagle_portrait_selection_upper.png`,
  `eagle_portrait_victoire_upper.png`. Deux corrections :
  - le rendu des frames de type 8 ajoute **`$1C00`** au code (mips `0x1414A4`, `ADDI.L #$1C000000`), pas `$1600` :
    code de frame = index local d'emplacement 1 − `$1C00` (avant : tuiles de Ryu, portrait « en charpie ») ;
  - **palettes du portrait de sélection** : routine **`0x56E9C`** (68K) : source = `$1BB4E0` (PS2 exéc. `0x7251A0`) +
    table de MOTS `[perso $3D(A6)]` + variante `$55(A6)` × `$80` (6 variantes × 4 palettes), copiées à partir de la
    palette d'objets `$0C(A6)` (copieur `0x1A024`). Décalages 16 bits → **déviation** : `LEA $1BB4E0,A0 ; ADD.W
    (A0,D0.W),D1 ; ADDA.W D1,A0` → `JSR stub` (stub dans le trou entre la fin du code et `DATA_BASE`) : pour
    `D0 = 2 × ID` → bloc `$D60880` (6 variantes ; si le paquet n'a que 4 palettes, répétées). La table `0x53BDF0`
    (pointeurs u32, blocs de `$600`) sert à d'autres écrans (victoire) : redirigée aussi.
- Restent pour `$26` : nom et textes (ceux de Ryu), petit sprite d'aperçu de la sélection (frames de Ryu), bandeaux
  128×48 / 96×48 (poses 6-11 / 18-23, redirigés, non vus), 6 variantes de couleurs (demandées à la session MAX).
  Session MAX informée. Yun `$28` / Ingrid `$29` : tables limitées à 40 ID (`0x484C00`).
- **Variantes de couleurs** (session MAX, `plXX/portraits_palettes_variantes.bin`, 24 palettes, index `4v + r`, et
  `portraits.json` → `128x224.variantes.palette_du_fichier_vers_r`) : bloc de sélection = pour chaque variante, les 4
  palettes du fichier avec la palette `4v + r` à la place de sa palette d'origine `f` (attributs inchangés ; Eagle
  2 → 0, 3 → 1). Variante 0 vérifiée ; les autres (choix au bouton) non vues. Ingrid (`f` = 3, 4, 5) : `f ≥ 4`
  dépasse les 4 palettes copiées par variante → remappage des attributs (demandé à la session MAX).

### 132. Audit « code perdu » : écritures de registre sans traduction (`chutes.json`)

Relevé `CHUTES` (§107, `<travail>/chutes.json`, chaque cas compté deux fois) : **SFA3 28 → 12, Upper 42 → 13** cas uniques.
Méthode : contexte MIPS de chaque cas, regroupement par motif, **sondes d'exécution** Lua (`install_read_tap` sur
l'espace des opcodes aux adresses 68K des cas) pendant l'attraction + une partie Arcade (Ryu, Guile) pour savoir
lesquels s'exécutent. Corrections (toutes `=0` pour l'ancien comportement) :
- **`MULS` — perte SILENCIEUSE** : `mult rd,rs,rt` du R5900 écrit `rd` ; non suivi, `rd` gardait sa valeur d'avant →
  `MOVE.L D2,D0` émis au lieu de `MULS.W D2,D0` (SFA3 `0x107898`…, 6 sites/module, pas même dans les chutes).
  Symbole `mul` → `MULS.W`/`MULU.W` (opérande registre ou mot mémoire). Les `mult`/`div` sans `rd` (`0x38xxxx`) sont du
  C du portage (divisions « magiques »), hors traduction.
- `MEMSHIFT` : `Dn.W = (long mémoire >> 8)` (6/module) → `MOVE.L ; SWAP ; ASR.L #8`, mot haut gardé par la pile.
- `TBLOP` : `Dn op= T(PC,Dk.W).L` (OR/AND/ADD, table longue à moitiés échangées) ; + **`D8_EARLY`** (extra_regs) :
  fermeture anticipée aussi pour les zones D8 (sauvegarde fixe) → SFA3 `0x1F3118` `LSL.W #2` et `OR.L` rétablis
  (site **exécuté** en combat). Zones : ro3 175 → 180, ro5 205 → 210.
- `LOGIC_ZERO` : `and rd,rs,zero` = 0 (Upper `0x14FF28`, **exécuté** à l'attraction), `xor/or` avec constante `lui`
  seule (`EORI.L #$10000,D8`, Upper `0x259228`, **exécuté**).
- `ROT` : rotations 16 bits décomposées (`(x>>n)|(x<<(16−n))`) → `ROR.W`/`ROL.W Dn,Dk` (2/module).
- `D8HI` : mot haut de D8 prêté (case `0x1146`) dans sa zone → `SWAP ; ADDA.W ; SWAP` (1/module).
- `TBLMEM` : table indexée par un champ mémoire signé (Upper `0x3AE5D4`… : `D0 = T[$1FF(A6)]`, **9 sites**, code des
  persos ajoutés d'Upper, jamais atteint par mes parties) ; `TBLMASK` : `T[(Dn & k) × s]` ; `BIGSHIFT` : décalages > 8 en
  tranches (`LSL.L #8 ; LSL.L #4`) ; `ABSEXT` : mot absolu signé rangé en long (`MOVE.W abs ; EXT.L`).
- **Sans effet (laissés)** : copies `An = An` (4/module) ; remappage des boutons du portage (`0x381900` SFA3 / `0x240A0`
  Upper, `(x & $FFF0) | T[x & $F]`, table remplie à l'exécution d'après la config ; D0 inchangé = identité, test des
  commandes 42/42).
- **Restent (documentés)** : fonctions **C du portage** qui manipulent les registres 68K avec des variables locales
  de la pile MIPS ou des registres hôtes `s0`/`s3` (SFA3 `0x2F114`, `0x3887B8`, `0x388800`, `0x38A0CC`, `0x3927E0`,
  `0x392A10` ; Upper `0x32694`, `0x4069E8`, `0x406A30`, `0x406D70`, `0x407E18`, `0x410C00`, `0x410E30`) : jamais
  atteintes par les sondes (écrans console / options du portage, cf. §119) ; une traduction juste demanderait de
  réécrire leur logique C en 68K.
- Vérification d'autres pertes silencieuses : seules `lwl/lwr` (pré-passe) et des codes natifs écrivent un registre
  inconnu de `dest_reg`.
- Non-régression SFA3 verte, md5 **`ed39a9103283dc43f33ff8783362bab4`** ; Upper reconstruit (`88487c7b…`), `nonreg_ro5.sh` vert.
  Balayage Upper juste avant (ROM du §131) : **40/40 fins**. Balayages complets relancés après §132 (`work/balayages/`).

### 133. Hyper au fork : banques propres, balayage des modes et des versions (agent)

Rapport : `work/agent_ro9/BANQUES-ET-MODES-ro9.md` (+ planches `work/agent_ro9/banques_modes/planches/`, reconstruction
`banques_modes/construire.sh`, scénario `banques_modes/lua/hyper.lua`, `balayage.sh`).
- Fichiers graphiques d'Hyper (descripteur `[[0x1DC040]]` du vidage EE) : communs **e545** (emplacement 0), décor
  **e546**, 32×32 **e548**, frames **e547** en `$C84000`. Banque par `$102` : `0x5AF1B0` (le chargeur natif `0x22B00` passe
  par `0x5AF420` mais aboutit à la même banque). Fichiers 314-344 = conteneurs `MOMO` (voix ?).
- ROM étendue d'Hyper (`work/mame_ro9/hsfa_gfx.bin`, 67 906 tuiles = celle d'Upper octet pour octet en tête + 11 927
  propres à Hyper) ; `hsfa_plans.bin` bases `300,340,3a0`. Lancement : `BANC_COMMUN=545 HSFA_PLANS=300,340,3a0
  HSFA_GFX=…/mame_ro9/hsfa_gfx.bin,…/mame_ro9/hsfa_plans.bin@3000000 BANC_BANQUES=…/mame_ro9/banques_hx/
  BANC_PTR_ANIM=FF40BC BANC_DIR=…/mame_ro9/ cps2f sfa3hx -rompath …/mame_ro9/roms_fork`.
- **Modes** : menu VERSUS / TRAINING / OPTION / EXIT (`$FF4201`, cycle 1 → 4 → 5 → 6) ; TRAINING et VERSUS 2 joueurs OK ;
  entrées 0/2/3 (ARCADE/SURVIVAL/DRAMATIC) forcées → VERSUS (`$FF80A9 = 3`).
- **Persos × versions** (113 `$102` en TRAINING, 0 exception) : tout ce que la grille permet de choisir est propre
  (ZERO 13/13, ZERO 2, ALPHA dont 7 EX, ZERO 3 36/38 dont Guile, Fei-Long, Dee Jay, T.Hawk, Shin Akuma, EX Balrog ;
  écran VS, portraits, HUD par version). Illisibles hors grille : `$12`, `$14`, `$58-$5C` (EX en ZERO 2), `$5E` — leurs
  tables de géométrie/animation retombent sur Ryu ZERO 3 (données du jeu, ni banc ni traducteur).
- Corrigé : haut des décors ZERO 2 / ZERO 3 (tuiles 32×32 vides en pen 0 → pen 15, `hsfa_plans.py`
  `HSFA_PLANS_VIDE15`, par défaut pour ro9 ; à évaluer pour le 32×32 d'Upper e525). Scripts partagés : `banques.py`
  (entrée ro9), `hsfa_gfx.py` (`HSFA_GFX_BASE`), ro3/ro5 inchangés.
- Restent : états PCSX2 d'Hyper pour trancher couleurs ZERO 3, 4e décor, choix des EX ; son d'Hyper (pas de Z80 dans
  son groupe X_DATA) ; audit des 114 chutes de ro9 ; `tournee.lua` à adapter (repères de phase d'Hyper).

### 134. Pistes « paradigmes » : réponse de la session MAX (PSP)

- Le code PSP de SFA3 MAX est du **C réécrit** compilé MIPS (ABI normale, objets en `a0`, aucun banc de registres 68K
  émulé) : correspondances un pour un seulement pour le moteur commun. Sa rosette donne **~150 paires de fonctions
  arcade 68K ↔ PSP** (`~/CLAUDE CODE/sfa3max-psp-widescreen/work/re/rosette_code/api_arcade_psp.json`, `tableau_api.md`)
  → pour nommer des routines du moteur (ex. `$2A770` chargement du pas, `$2A7EA` avance, `$1C2C8`/`$1C368` réservoirs
  d'objets, `$1B4D0` affichage si à l'écran, `$38E4` voix ; globale `$10B(A5)` « pose de victoire terminée » (bit par
  joueur), compteurs de réservoirs `$6EB6-$6EBC(A5)`).
- Fonctions C du portage PS2 du §132 : peu probable que le PSP aide (interfaces console propres) ; sauf logique de jeu
  (mode, réglage) → à lui soumettre au cas par cas.
- Au-delà de 40 ID : les tables PSP par perso ont **42-44 entrées**, IDs MAX `$26-$29` dans le même ordre (ex. voix
  `0x23A6D8`, 44 pointeurs) ; champ `$E` (plan de caméra) ×4 côté arcade ; structure d'état PSP `0x39C9E0` (+`0x39` = 1 en
  entraînement). La session MAX a un PPSSPP sans affichage avec débogueur WebSocket (`work/re/ppsspp/ppdbg.py`) et peut
  lire des valeurs en jeu sur demande.
- En cours (agents) : couverture arcade → traduction (`work/agent_couverture/`), recherche web
  (`work/agent_web/`), cœur FBNeo libretro Android (`work/fbneo/`).

### 135. Recherche web : ce qui existe ailleurs (agent)

Rapport : `work/agent_web/RECHERCHE-WEB.md` (code cloné : `work/agent_web/sfa3_support/`).
- Développeur de l'Anthology : Capcom Production Studio 2. **Aucune documentation publique** du recompilateur 68K→MIPS ni
  des formats MWo3 / X_DATA / prog68k ; aucun désassemblage public de SFA3/SFA2/Hyper (seulement SFA1 / SFZ, Grego) ;
  aucun hack CPS2 ajoutant les persos d'Upper ou de MAX.
- **CPS2 Turbo** (Zero800), déjà dans FBNeo officiel (`Cps2Turbo`, pilote `sfz3mix`) et HBMAME (`cps2t.cpp`) : 68K 32 MHz,
  Z80 16 MHz, programme 6 Mo, sorties `$400000` → `$665000`, gfx 64 Mo, QSound 16 Mo, Z80 512 Ko, 416×234, musique en WAV
  par la boîte `C080/C081` ; **bit 15 de Y = bit 18 du code** (= proposition du §115). Base possible pour le cœur FBNeo
  (FBNeo ne mappe que `$000000-$3FFFFF` en programme).
- **`sfa3_support.lua`** (0xZERO3) : RAM et boîtes de collision de SFA3 (joueur `+$1C`, `+$90..+$A0`, `+$C8..+$CB`,
  `+$102`, `+$32F` ; boîte d'attaque de 32 o, champs nommés ; frame `+4` gfx, `+9` boîte) ; couvre aussi la PS2 et la
  **version GBA d'Upper (Eagle, Maki, Yun, même format de boîtes)**. `cps2-hitboxes.lua` (dammit) : formats SFA1/2/3.
- Grego : Final Fight porté sur carte SFA3 réelle (pilote son Z80 de SFA3 + nouvelle QSound = même principe que notre
  ROM son hybride) ; désassemblage SFZ `sfzch_cps15` ; tests DMA CPS2.
- PalMod : palettes SFA3 dans `sz3.09c` dès `0x2C0D2` (6 variantes × 5 palettes) ; adresses d'Upper NAOMI.
- pnach PCSX2 de l'Anthology : `0x1DC2B0` = 1 quand l'émulateur CPS2 tourne ; blit final vers `0x1499B8-0x149F30`.
- Pages non lues (anti-robot / 403) : TCRF Anthology/Upper (à ouvrir à la main), MobyGames, StrategyWiki, wiki PCSX2.

### 136. Cœur FBNeo libretro HSFA (agent) : SFA3 et Upper sans MAME

Livrables `work/fbneo/` (`LISEZMOI.md`, `RAPPORT-fbneo.md`, `paquet_fbneo.py`, `tests/`) ; code dans le clone
`<workspace>/fbneo-hsfa` (commit local `2b57422`, pas de push) : nouveau `src/burn/drv/capcom/cps_hsfa.cpp` + crochets
dans `cps*.cpp` actifs seulement pour les pilotes **`sfa3hsfa`** (SFA3) et **`sfa3uhsfa`** (Upper).
- Reproduit le banc : blocs externes `$A00000-$EFFFFF` (mappage dédié), plans (renumérotation SFA3 / bases `$804200`
  d'Upper), **`banc_sprites.lua` porté en C++**, ROM graphique 64 Mo + code étendu par les bits 10-11 de X, son (Upper :
  ROM hybride 16 Mo), IRQ du Z80 à 250 Hz comme MAME ; états de sauvegarde incluent l'état du banc.
- Archives complètes par jeu (`sfa3hsfa.zip` 23 Mo, `sfa3uhsfa.zip` 35 Mo) reconstruites par `paquet_fbneo.py` depuis
  `work/…` (pas besoin de recompiler le cœur après une nouvelle traduction) ; `*_sources.txt` = md5/dates.
- Cœurs : `fbneo_hsfa_libretro_android.so` (arm64-v8a, NDK r28c) et `fbneo_hsfa_libretro.so` (Linux x86_64).
- Validation sur PC (lanceur libretro sans fenêtre `hsfa_run`, mêmes entrées que `jeu.lua`) : SFA3 journal d'attraction
  identique image par image sur 8 000 images ; Upper 599/676 captures identiques au pixel (toutes après l'image 1656) ;
  niveaux sonores équivalents.
- Écarts : tirage aléatoire du programme traduit sensible au compte de cycles du 68000 (adversaire/démo différents de
  MAME, décalages de 1-2 images) ; QSound simplifié de FBNeo ; OPTION/EXIT écran noir (comme MAME). `Cps2Turbo` regardé,
  non repris (format différent du fork).
- Non testé sur console (Anbernic RG477M / Retroid Pocket Nova) : retours de l'utilisateur attendus.

### 137. Audit « code perdu » d'Hyper ; nouveaux motifs ; RÉGRESSION du §132 corrigée (fins de SFA3)

- **Hyper** (ro9, reconstruit avec le traducteur courant) : chutes **57 → 10** cas uniques, blocs exacts perdus **1 → 0**.
  Restent : 2 remappages de boutons (`jal 0x2141B0`, sans effet), 1 copie `An = An`, 7 sites de fonctions C du portage
  (registres hôtes `s3`/`s6` : `0x28F44`, `0x28FFC`, `0x290B4`, `0x3F014`, `0x370090`, `0x3B5BA8`, `0x3B5F10`). Sondes
  (scénario TRAINING de l'agent, 4 persos/versions) : seuls la comparaison `0x96A04` et les remappages s'exécutent.
- Nouveaux motifs (tous `=0` pour l'ancien comportement) :
  - `SPILL_Q` : temporaires 64/128 bits `sq`/`lq`, `sd`/`ld` sur la pile suivis comme les 32 bits (Hyper `0x96A04`,
    Upper `0x261CE0` : opérande de comparaison exacte perdu). Upper : 1 bloc exact restant (`0x1D0EA4`).
  - `dn_alu._lin` : **multiplication par constante décomposée** (`sll/addu/subu` d'un Dn.W étendu signé ou non) →
    `MULS.W`/`MULU.W #k` (Hyper : 41 sites, ×6, ×40, ×120…) ; `ANDAND` : masques `andi` successifs combinés ; opérandes
    `andi $FFFF` du `mult` → `MULU.W` (Hyper `0x51EC8`, `0x54DAC`).
  - **`SHIFT_MR` — perte SILENCIEUSE** : la lecture mémoire suivait TOUT `sll/sra` (pas seulement les extensions 16/24) →
    `MOVE.W x,x` émis à la place d'un décalage (SFA3 `0x7E674`, Hyper `0x5A41C`, Upper `0x8F0E0`, D8 servi par son
    domicile) ; + `MEMSHL` : `LSL.W d(An)` ×k (décalage d'un mot mémoire sur place).
  - `TBLBYTE` : octet bas d'un mot de table → `Dn.B` (3 sites Hyper) ; `An = table + mot mémoire` → `LEA ; ADDA.W`.
- **Régression du §132 (`MEMSHIFT`)** révélée par le balayage des fins de SFA3 : **exception à la fin de chaque fin**
  (CHK / division par zéro). Bisection (`MEMSHIFT=0` → fins OK). Les 12 sites (SFA3 `$BF40`, Upper `$C140`) font
  `D = (pointeur vidéo >> 8)` puis `LSL.L #8` puis `MOVEA ; JSR CONV` = alignement d'un pointeur sur 256 ; le pointeur
  est stocké converti et marqué (`$0190C000`) ; garder l'ancien mot haut de Dn (sémantique `sh` exacte) perdait le
  marqueur `$01` → `$0090C000` pris pour une adresse PS2 et converti. **Correctif** : valeur décalée entière
  (`MOVE.L ; SWAP ; ASR.L #8`) → `$0190C000` après le `LSL` (`MEMSHIFT_GARDE=1` = ancien choix). NB : avant le §132,
  D0 restait 0 (palettes lues à l'adresse 0 : faux mais sans plantage).
- Leçon : **la non-régression ne couvre pas les fins** ; après tout correctif du traducteur, relancer aussi
  `balayage_fins.sh`. Le zip FBNeo de SFA3 du §136 avait la ROM fautive (`ed39a910…`) → à refaire.
- SFA3 reconstruit : md5 **`3e2efaf71c0e13d53ea3cabfb051adb0`**, non-régression verte ; balayages en cours.
- Balayages des fins avec ces ROM : SFA3 **32/32** `fin=finie`, captures identiques à l'arcade ±1 ; Upper **40/40**
  (ROM `1e0b6976…`).

### 138. Zones d'ombre (1) : écritures mémoire perdues, profil des adaptateurs

**Tri des écritures mémoire « sans trace »** (`AUDIT_MEM=1`, `mem_miss.json`) : SFA3 770, Upper 649. Hors du C du
portage (`0x38xxxx-0x39xxxx`, `0x40xxxx-0x41xxxx`) : SFA3 38, Upper 140. Classement (contexte MIPS `show.py`, arcade
`agent_couverture/site_arcade.py` + `montre.py`, octets de la ROM) :
- **Vraies pertes, corrigées** (toutes `IDXRMW=0` pour revenir en arrière) :
  - **lecture-modification-écriture d'un octet/mot INDEXÉ** (`lb x,d(An+Dn) ; op ; sb`) : seule la forme `d16(An)` était
    reconnue → `ANDI.B #$7F,(A0,D0.W)` (arcade `$023288`) et `ADDQ.B #1,(A0,D0.W)` (arcade `$0232F8`) perdus dans
    SFA3 **et** Upper (compteurs/drapeaux par index de `$25A`/`$280` de la structure). Émis `ADDQ/SUBQ/ADDI/ANDI/ORI/EORI
    #k,d8(An,Dn)` ; `byte_index_exact` accepte maintenant les opérations immédiates (extension APRÈS l'immédiat).
  - **`m1 += m2` / `m1 -= m2` entre deux lectures mémoire** (`mem2` ne connaissait que ET/OU/OU exclusif) : Upper
    `0x1EC4F0` `$2A4(A5) += $44(A6)` (position de défilement), `0x153F24` `$50(A6) += $7C(A6)`, `0x419BC0`
    `$14(A6) += $44(A6)` ; SFA3 `0x7E694` / Upper `0x8A620` `ADD.B $100(A6),D8` (D8 servi par son domicile : invisible
    pour l'audit, qui écarte les cases de registres). Émis `MOVE.L D0,-(SP) ; MOVE.x m2,D0 [; SWAP] ; ADD/SUB ;
    MOVEM.L (SP)+,D0` (drapeaux de l'opération gardés ; long échangé via `inplace_long`).
  - **registres CPS-A élargis chargés par un `lui` SEUL** (`$920000`) : bases objets `$804100` et scroll1 `$804102` de
    la fonction d'initialisation vidéo (SFA3 `0x92734`/`0x92740`/`0x9283C`/`0x92848`, Upper `0xCEDF4…`) perdues.
  - **base des objets CPS2 `$400000`** (pointeur PS2 en `0x962180`, `OBJBASE=0` pour revenir) : ajoutée à `WIDEREG` →
    `MOVE.W #$7000,$400000` exactement comme l'arcade (`$091E`, `$0BC8`), et par image `$BF58(A5)>>8` au lieu d'un
    `MOVE.L` vers l'adresse hôte `$962180`. (Rappel §103 : forcer `$400000` ne changeait rien dans le banc.)
  - **Upper : décor courant `$DC(A5)`** (arcade `$4DC2`, `$5AB0` : `MOVE.W (T,PC,D0.W),$DC(A5)`, lu ~30 fois : `$DC`
    décor, `$DD` suivant) : la table (identique à l'arcade, convertie en `$0A2E40`) est désignée par **A8 prêté** dans
    Upper et par une constante dans SFA3 → `bswap16_mem` reconnaît maintenant `An + Dk.W` (`anidx`) : `MOVEA.L An,At ;
    ADDA.W Dk,At ; MOVE.B 1(At),$DC ; MOVE.B (At),$DD` (sites `0x51038`, `0x54C70`). **Avant : `$DC` jamais écrit par
    ces deux routines dans Upper.**
  - **valeur de table indexée par un CHAMP MÉMOIRE rangée en MÉMOIRE** (`tblmemval` ne visait que les registres D) :
    SFA3 `0x7E6BC` / Upper `0x8A648` `MOVE.B T(PC,D8.W),D8` (D8 servi par son domicile, suite de `LSL.W #1,D8 ; ADD.B
    $100(A6),D8`) ; Hyper `0x2F5ED0` `MOVE.B T(PC,D8.W),$70(A6)`, `0x8F128` ; conversions `$117(A5)` ↔ `$C12A`/`$C32A(A5)`
    des écrans console (SFA3 `0x38AA08…`, Upper `0x408638…`, Hyper `0x29758…`, `0x3B4148…`). Émis `MOVE.L D0,-(SP) ;
    MOVE.x champ,D0 [; EXT.W] ; MOVE.x T(PC,D0.W),dest ; MOVEM.L (SP)+,D0` (octets : adresse exacte à l'exécution).
- **Propres au portage (laissés)** : pointeurs hôtes chargés de `0x19E438-0x19E448` (`lui $1A`, structures du
  programme PS2 : copies d'options, pointeurs de tampons), `0x1DC078` (Upper), manette `$A62190…`, vidage des cases du
  recompilateur dans un tampon (écran de plantage : SFA3 `0x3009C…`, Upper `0x3366C…`), fonctions C (`s0-s7`, cadre de
  pile), adresses hôtes `$76E770…`.
- **Faux positifs** : paires `swr/swl` déjà rendues par un seul `MOVE.L` (`0x45204`, `0x45F04`).
- **Pièges d'assertion de Capcom** : arcade `$032AFE ADDQ.L #1,$1.w` et `$073B02 MOVE.L #-1,$1.w` (erreur d'adresse
  volontaire sur une commande de script invalide) ; le PS2 écrit sans dommage à l'adresse 1 → non traduits (comme PS2).
- Restent après correction : SFA3 762, Upper 636 (tous classés ci-dessus).

**Profil des adaptateurs** (`work/mame/_prof_adapt.lua` chargé par `_prof_tour.lua` après `tournee.lua` : mots
d'opcodes lus par adresse, images de combat `$FF800C=6` seulement ; analyse `prof_an.py` : désassemblage `unidasm`,
classement par instruction). Ryu, 4 manches :

| par image de combat | arcade | SFA3 traduit | Upper traduit |
|---|---|---|---|
| attente (boucle d'ordonnanceur / `$663888`) | 29,9 % | 32,0 % | 26,5 % |
| travail (mots lus hors attente) | 23 317 | 23 157 | 24 505 |
| dont conversions (talons `$400` + `$3FF000` + appels) | — | 13,1 % | 12,6 % |
| dont longs échangés (`SWAP`, `MOVE SR/CCR`, pile) | — | 6,7 % | 7,3 % |
| dont octets XOR 1, registres prêtés A8/D8 | — | 0,5 % | 0,6 % |

Lecture : en combat normal, la traduction a la **même marge que l'arcade** ; les adaptateurs pèsent ~20-22 % du travail
(~15 % de l'image). Un réagencement des données (pointeurs relogés statiquement, RAM en ordre 68K) les supprimerait et
réglerait les images répétées du turbo (§104) sans surcadençage. Il ne réduit PAS la charge de l'hôte d'un émulateur
(le 68000 est émulé à cadence fixe, boucle d'attente comprise) : sur petite machine (RGB10X), le coût est la vidéo
CPS2, le QSound et le 68000 à 12 MHz, pas l'efficacité du code traduit. Points chauds : construction de la liste
d'objets (`$023500-$024400` SFA3, ~36 % du travail, comme `$21000-$21900` à l'arcade).
- Fausse piste pour le hasard : `JSR $1414` de la boucle d'attente arcade ne fait que `D0=$20`.
- **Hyper** (traducteur §138 complet, dossier d'essai) : 34 sites rétablis ; pertes restantes 583, toutes classées
  (C du portage rangé en tête du module `0x22000-0x2FFFF`, groupes connus de SFA3, pièges d'assertion `0x8BBC4`,
  `0x2F43E4`, pointeur hôte `0xA6760`).

**Validation du §138** (traducteur complet, ROM SFA3 `d57d087b…`, Upper `2810c539…`) : non-régression verte pour les
deux (SFA3 : 3 diagnostics, 42/42 commandes, 133,3 % ; Upper : attraction + 3 parties jusqu'à la fin) ; balayage des
fins SFA3 **32/32** (captures = arcade ±1) ; balayage Upper en cours au moment de l'écriture. Archive FBNeo
`sfa3hsfa.zip` reconstruite avec cette ROM.

### 139. Zones d'ombre (2) : hasard, Upper face à l'arcade, adresses MAX, index et son d'Hyper, cœur widescreen

Rapports d'agents (dossiers `work/agent_*`, non publiés : données de jeu et chemins locaux) ; synthèse :

- **Hasard** (`agent_hasard/HASARD.md`) : un seul générateur, arcade `$01BDA6` = traduction `$0114DC` (mêmes
  instructions), graine mot `$FF80AE` (`$01C3` au départ, période 43 534), `h' = (3·s >> 8) & $FF`, `l' = l + h'`.
  N'avance qu'aux appels (217 sites ; ni l'attente ni l'IRQ). Divergence MAME/FBNeo : l'intro est calée sur la musique
  (compteur Z80 `$618021`) et ses particules tirent 51 nombres/image (`$5DE6` arcade, `$8622` traduction) → une image
  de plus dans FBNeo = ~100 tirages d'écart ; s'y ajoutent les tours perdus par débordement et l'IA conditionnée par
  `($80,A5) & 3`. Comportement d'origine : **laissé tel quel** (décision de l'utilisateur).
- **Upper face à l'arcade** (`agent_upper_ecarts/ECARTS-UPPER.md`, réalignement 46,3 %) : 509 écarts = 250 changements
  d'Upper (palettes : `$128` = index complet ; sélection ; animations renumérotées Adon +3, Guy −3, R.Mika −1, Zangief
  −$E ; bonus d'IA par perso supprimé), 172 portage/recompilateur, 73 tables étendues, 12 champs déplacés (`$145`→`$121`,
  `$37F`→`$1FF`, `$32F` supprimé, masque `$140` long → 48 bits ; RAM : records `$FF23BE` 35 × 16 o, décalages +`$240`),
  2 inexpliqués. Pièges pour les ids `$26-$29` : pseudo-ids `$28-$2C` (musique) et `$28/$29` (variantes Vega/Chun-Li
  des tables ID×8), borne `CMPI.B #$26` de la grille. Lire les données arcade dans `sfa3ud_prog.bin`.
- **Adresses du moteur arcade utilisées par MAX** (`agent_max_upper/ADRESSES-MAX-UPPER.md`, `correspondances.tsv`) :
  113 vérifiées dans Upper ; ~105 identiques, ~10 modifiées (seuils de jauge `$123`, effacements, voix par table),
  2 absentes (`$2D5E2` 1re manipulation, `$2E700`). `$32F` : 9 écritures, aucune lecture dans toute l'arcade
  (variable morte, retirée par Upper). Caméra `$290(A5)` = `$292(A5)` dans l'image (moitié haute d'un long). Sauts :
  `$2BE6A` choisit par ism 3 tables de 64 o par perso ; Upper 40 entrées, `$28/$29` imposent 42 et un déplacement.
  ⚠ Les adresses image changent à chaque reconstruction : se référer aux va MIPS.
- **Index d'Hyper** (`agent_hyper_index/INDEX-HYPER.md`, `ids_102.tsv`, `btst_d3.tsv`) : `$102 = grille[$116×4 + $5D]`
  (`0x31AAA0`) ; Start maintenu → grille secrète `0x5C5420` (EX, Shin Akuma, EX Balrog, Chun-Li SF2, Sakura bis).
  Bits `$D3` : 0 ZERO (341 tests), 1 ZERO 2 (190), 2 ALPHA (87), 3 EX (183), 4 ZERO 3 (467), 5 ZERO 2 d'origine (38),
  7 mode secret ZERO 3 (`$15E = $81`), 6 jamais posé. 45 tables par `$102` (+ 47 par `$116`). Attaques de 32 → 40
  octets dans Hyper (`+$20` = version). Custom combo par version (`0x2D1F10`). Écran de mode ZERO 3 (`0x31B890`) :
  4 curseurs + 4 avec Start (`$15A`, `$131`, `$15E`, `$122`). Bogue probable : 3 tables d'Upper de 40 entrées lues par
  `$102` ≥ `$28`. 437 variables A5 (Upper 613 : ARCADE/SURVIVAL/DRAMATIC retirés).
- **Son d'Hyper** (`agent_hyper_son/SON-HYPER.md`) : sur PS2, **ni Z80 ni QSound** (le Z80 recompilé est mort) ; un
  pilote C natif lit la boîte `$618001-$618019` et une table de `0x1200` commandes (identique ro3/ro5/ro9) ; musique
  = flux ADX de `Y_DATA.BIN` (AFS, 588 flux) ; bruitages/voix = banques Sony e313-e346 de SFA3 (voix SFA3 pour toutes
  les versions). Musique par version : ZERO 3 `0x01-0x33`, ZERO `0x41-0x4D` (= SFA1 arcade), ZERO 2 `0x51-0x63`
  (= SFA2 arcade), ALPHA `0x2C1-0x2FC`, variantes `0x180-0x1F7`. **Défaut d'Upper** : musiques de Guile, Fei-Long,
  Dee Jay, T.Hawk (`0x30-0x35`) muettes avec la ROM hybride du §127. Recommandation : lecteur de flux ADX dans le
  fork/FBNeo (217 flux, 696 Mo). Bruitages et voix d'Hyper déjà couverts par la ROM hybride d'Upper.
- **Cœur FBNeo HSFA widescreen** (`work/fbneo/widescreen/`, branche locale `widescreen` de `fbneo-hsfa-ws`) : pilotes
  HSFA en 448×224 16:9 sous `-DHSFA_WS`, même nom de pilotes (zips inchangés), cœur distinct « FinalBurn Neo HSFA
  Widescreen ». Validé sur PC (`hsfa_run`) : centre identique au pixel au 4:3 (520 captures), déroulé identique,
  état sauvegardé OK. Défauts : bande de 32 px aux butées de caméra (SFA3), objets coupés à la limite 4:3, écrans hors
  combat incomplets ; sans rapport : blocs blancs dans l'usine de Zangief (Upper, aussi en 4:3).
- **Décors widescreen** : projet d'export des décors en PSD (un dossier par décor, un calque par plan) pour agrandissement
  par l'utilisateur, puis réimportation en tuiles ; l'export à un instant de la tilemap (`sfa3-widescreen-android`,
  `stage00.psd`) est faux (anneau recomposé) → balayage de caméra et recollage par plan (pilote en cours).
- **Réorganisation des données** : architecture dans `docs/ARCHI-Reorganisation-Donnees.md` (carte des types unique,
  étapes réversibles A-G, oracle = RAM arcade).
- Balayage Upper avec la ROM §138 (`2810c539…`) : **40/40** `fin=finie`. Archive `sfa3uhsfa.zip` reconstruite.

### 140. Code C du portage : aiguilleurs par table de longs, tests `lb ; bne r,zero` (fin de match VERSUS d'Hyper)

Constat (agent des états d'Hyper, `work/agent_hyper_etats/ETATS-HYPER.md`) : la scène de fin de match VERSUS d'Hyper
(`A5+4 = $E`) tournait sur un écran noir (`A5+8` +2 toutes les 7 images), le TRAINING perdait des tests. Cause : du code
**C du portage** (temporaires, aucune case de registre) que le traducteur, qui suit les registres 68K, n'exprimait pas.
- **Aiguilleur C** (`c_dispatch`) : `lw x,A5 ; lh y,d(x) ; ext ; sra k1 ; sll k2 ; lui/addiu T ; addu ; lw ; jalr` →
  `MOVE.L D7,-(SP) ; MOVE.x d(An),D7 ; ANDI/LSL (index de table de mots) ; MOVE.W T(PC,D7.W),D7 ; JSR T(PC,D7.W) ;
  MOVEM.L (SP)+,D7` (forme Capcom, table de mots reconstruite par l'assembleur). 2 sites par module : SFA3 `0x38F2A4`,
  `0x391330` ; Upper `0x40CFA4`, `0x40F750` ; Hyper `0x2D584` (fin de match), `0x3B43B0` (TRAINING).
- **Test C** : `lb/lh/lw r,mem ; bne/beq r,zero,T` (sans case RES) → `TST.x mem ; Bcc`. ~100 sites par module, presque
  tous dans les écrans console ; un dans le code de jeu de SFA3 (`0x1F6DF8`, `TST.B $100(A6)` devant un appel natif).
- Interrupteur `CDISP=0` (ancien comportement) ; compteur dans `mame_test.py`. Effet de bord : la fin du code grandit, les
  données passent de `$93000` à `$94000` (SFA3), relogées par l'assembleur.
- Hyper : l'écran **RESULT** de VERSUS s'affiche (victoires/défaites par perso) puis attend le menu à curseur (`$C316`,
  sous-état `$A`) ; `tournee_hyper.lua` ne sait pas encore y répondre.
- Validation (ROM SFA3 `a51fe745…`, Upper `19636150…`, Hyper `e19d8fa4…`) : SFA3 non-régression verte (3 diagnostics,
  42/42, 133,3 %) ; Upper, partie VERSUS d'Hyper et balayages des 72 fins : **en cours à l'écriture** (tâche de fond
  `chaine140.sh` ; résultats dans `work/balayages/ro3_*` et `ro5_*` les plus récents). **À vérifier en reprise.**

### 141. Chantiers lancés le 2026-10-07 (agents en cours à la fin de la session)

| chantier | dossier (`work/…`) | livrable attendu |
|---|---|---|
| outil de réimportation de tuiles (PSD → tuiles CPS2, palettes, dédoublonnage ; format des données de décor ; blocs libres SFA3/Upper) | `decors_ws/reimport/` | `REIMPORT.md` |
| lecteur de flux musique ADX (fork, puis FBNeo ; `Y_DATA.BIN`) : musiques d'Hyper et 4 musiques muettes d'Upper | `agent_flux/` | `FLUX.md`, patchs |
| passe de conversion du code MAX (disposition arcade → image Upper, par `champs_types_upper.tsv`) | `agent_conv_max/` | `CONV-MAX.md`, `convertit_max.py` |
| réorganisation des données, étape A (journal des conversions, comparaison RAM arcade, `disposition.lua`) | `agent_reorg_A/` | `ETAPE-A.md` |
| blocs blancs de l'usine de Zangief (Upper) | `agent_zangief/` | `ZANGIEF.md` |

Terminés ce jour (rapports dans `work/`) : voix MAX dans une copie de la ROM son (`agent_voix_max/VOIX-MAX.md` : 134
voix, commandes `$02A4-$05FC` côté 1, +$500 côté 2 ; pièges QSound : adresses signées $7FFF/$8000, lecture dans
l'ancienne banque ; `paquet_fbneo.py` pointe encore sur la ROM hybride sans voix) ; typage des 212 champs MAX
(`agent_typage_max/`) ; complément des adresses MAX ; états et EX d'Hyper ; son d'Hyper ; pilote d'export de décor
(`decors_ws/DECORS-WS.md`, `out/decors_sfa3.psd`, décor `$0C` exact au pixel).

Suite logique : valider §140 → publier ; export de tous les décors SFA3 dans le même PSD ; balayage long d'Hyper
(`tournee_hyper.lua`, répondre au menu `$C316`) ; intégration MAX (tables à 42 entrées, pseudo-ids `$28/$29`, borne
`$26` de la grille, fins en données : script arcade + anim + banque, table de scripts `0x60B860` d'Upper) ; widescreen
moteur (objets coupés à la limite 4:3, écrans hors combat). En attente de l'utilisateur : retours console (cœurs 4:3 et
widescreen), PSD dans Photoshop, écoutes (son hybride d'Upper, musiques d'Hyper, voix MAX), état PCSX2 d'Hyper ZERO 3,
décision sur l'historique Git.

**Mise à jour de fin de session (§141).**
- **Usine de Zangief (Upper) : diagnostic fait** (`work/agent_zangief/ZANGIEF.md`). La tuile scroll3 32×32 de code 0
  est opaque dans `hsfa_plans.bin` d'Upper : `hsfa_plans.py` ne range les tuiles vides de `e525` en pen 15 que pour
  ro9 (`HSFA_PLANS_VIDE15`). Cela touche 16 décors d'Upper ; c'est une régression du §120. **Correctif à appliquer**
  (pas fait : validation en cours sur les fichiers d'Upper) :
  `VIDE15 = os.environ.get("HSFA_PLANS_VIDE15", "1" if profils.NOM in ("ro5", "ro9") else "0") == "1"`, puis régénérer
  `hsfa_plans.bin` (`MODULE=ro5 hsfa_plans.py`) et `sfa3uhsfa.zip`. Vérifié à l'image sur 35 décors : 16 corrigés,
  aucun dégradé. Le décor forcé `$2C` est illisible, mais pour une autre cause, non étudiée.
- **Agents arrêtés faute de crédit**, travail partiel sur disque :
  - réimportation de tuiles : format des blocs établi par désassemblage, validation en cours ;
  - flux ADX : arrêté pendant les essais Z80 de coupure de musique ;
  - conversion MAX ;
  - étape A.
  À relancer depuis leurs dossiers (§141).

### 142. Reprise du 2026-10-10 : retours console, correctifs, chantiers aboutis

**Retours de l'utilisateur (cœur FBNeo HSFA sur RetroArch Android, ROM §138)** : SFA3 et Upper tournent sans plantage.
Défauts signalés :
- bandeaux à la mauvaise vitesse (lesquels : à préciser par l'utilisateur) ;
- Sakura : boules à 42 coups (SFA3 et Upper ; amusant, à garder éventuellement en option cachée, Start maintenu) ;
- Akuma : la super boule (Messatsu Gou Hadou) se déclenche mais la boule ne part pas (SFA3 et Upper) ;
- Upper : tuiles de décor manquantes sur presque tous les décors.
Les deux défauts de coups sont confiés à un agent (`work/agent_coups/COUPS.md` attendu).

**Correctifs et validation**
- Tuiles d'Upper : `hsfa_plans.py` range désormais les tuiles 32×32 vides d'`e525` en pen 15 aussi pour ro5
  (`HSFA_PLANS_VIDE15`, défaut ro5+ro9). C'était le défaut des « tuiles manquantes » (aplats de couleur 0 sur 16
  décors, `docs/rapports/ZANGIEF.md`). `hsfa_plans.bin` d'Upper : md5 `eba15871…` (identique à la copie vérifiée à l'image).
- §140 : SFA3 32/32 fins (ROM `a51fe745…`) ; Upper : non-régression verte ; Hyper : VERSUS sans exception, écran RESULT
  atteint. Balayage des 40 fins d'Upper en cours à l'écriture ; puis reconstruction de `sfa3uhsfa.zip`.

**Chantiers aboutis** (rapports dans `docs/rapports/`, outils dans `tools/`)
- **Étape A** de la réorganisation : journal des conversions (224 cases ROM de pointeurs de code = ~32 % des appels de
  talons ; 21 pointeurs vers la RAM PS2 = 2,2 M appels), oracle RAM traduction ↔ arcade (82 % des variables A5
  comparables identiques), accesseur `disposition.lua` (lecture par adresse arcade, 262/262).
- **Lecteur de flux ADX** (fork + FBNeo, branche locale `flux`) : musiques absentes du Z80 jouées depuis le
  `Y_DATA.BIN` de l'utilisateur ; Upper : 4 musiques muettes réparées ; Hyper : ZERO / ZERO 2 / ALPHA. DIP « PS2 music ».
  Cœur Android widescreen + flux envoyé à l'utilisateur (non essayé sur appareil).
- **Réimportation de tuiles** : PSD → tuiles CPS2 (palettes, dédoublonnage avec miroirs, encodage) ; format des données
  de décor établi (listes `$19146/$19272/$194A2`, bibliothèques `$367494/$391014/$3AC614`) ; essai MAME de bout en bout
  exact au pixel. Contraintes : palettes de décor quasi pleines (relogement de 3 constantes pour en avoir 32) ; 75 Ko
  libres dans la ROM graphique arcade. Blocs libres et extension : `blocs_libres.json` (réponse à la session MAX).
- **Conversion du code MAX** : 7 550 réécritures, 115/115 appels moteur résolus, vasm sans erreur ; 2 761/2 870
  instructions identiques à ce qu'Upper a produit. La session MAX produit ses frames F26-F29 en disposition arcade,
  codes LOCAUX à la banque du perso, dans les blocs externes `$D40000 + $40000·k`.

**En cours** : ROM son propre à Hyper avec les voix de SFA1/SFA2 par version (`work/agent_son_hyper_rom/`), défauts de
coups Sakura/Akuma (`work/agent_coups/`). À faire ensuite : porter l'injection de décor au fork/FBNeo (plan au §7B de
`REIMPORT.md`), export de tous les décors dans le PSD, balayage long d'Hyper, intégration MAX (places `$26-$29`).

### 143. Coups de Sakura / Akuma corrigés ; script de construction depuis l'ISO ; stratégie fixée

**Deux pertes du traducteur, trouvées par les retours console** (`docs/rapports/COUPS.md`, mêmes entrées scriptées sur
l'arcade et la traduction) :
- `TAILBR` : un retour « s'il n'y a plus rien à faire » (saut vers la fin de fonction après un appel terminal rendu en
  `JMP`) était supprimé alors qu'il était CIBLE de branchements ; ils retombaient sur l'instruction suivante. Super boule
  d'Akuma (arcade `$038B2E`) et de Dan : le coup s'arrêtait avant le lancer. 6 sites SFA3, 5 Upper, 3 Hyper.
- `LUIDN` : une constante `lui` seule rangée dans un registre de DONNÉES (masque `$800000` des types d'objets qui ne
  décomptent pas leurs touches, arcade `$024CFA` ; plafond de vitesse `$900000`) était prise pour une adresse PS2 et
  convertie. Boules jamais détruites : Sakura dans Upper (« 42 coups »), Rose dans les deux jeux. 3 sites par module.
- Résultat : Akuma 4/8 coups (niv. 1/3), Dan 3/5, Sakura 3/5 et 1, Rose 1 = arcade. `TAILBR=0` / `LUIDN=0` = ancien.
- Validation (`valide_tout.sh`, nouvel outil de validation complète) : ROM SFA3 `f2f46b7e…`, Upper `0485973b…`, Hyper
  `69b2ac41…` ; SFA3 non-régression verte (42/42, 133,3 %) et **32/32 fins** ; Upper non-régression verte, fins en cours
  (32/40 bonnes à l'écriture) ; Hyper VERSUS sans exception.

**Script de construction depuis l'ISO** (`tools/build/hsfa_build.py`, `docs/rapports/BUILD.md`) : reproduit à l'identique
(md5) les ROM programme de SFA3, Upper et Hyper, les blocs, tables, graphismes étendus, ROM son et table de flux, et le
zip d'Upper, depuis l'ISO de l'utilisateur, en 4 min 30 ; reprise par étapes, empreintes. Dépend encore de la ROM
graphique arcade SFA3 (voie « ISO seule » en cours) ; zips à rendre déterministes ; archive d'Hyper après son pilote FBNeo.
Outils d'extraction publiés : `tools/extraction/` (extract_anthology.py, mwo3_codec.py, table_son.py).

**Autres résultats** (rapports dans `docs/rapports/`) :
- `CARTE-MODULES.md` : tous les modules identifiés (ro1 SFA, ro2 Zero 2, ro4 Zero 2 Alpha, ro6 Zero 2 Dash avec Cammy,
  ro7 Pocket Fighter, ro8 SFA2, b = menu) ; traducteur à 98-99 % sur tous ; base RAM mal calculée par l'outillage pour
  5 modules ; Hyper n'emprunte aucun code, seulement des banques de sprites (e208-e220, e229-e248) et les musiques ALPHA.
- `INJECTION-FORK.md` : injection de décors widescreen dans le programme TRADUIT de SFA3 (bloc externe, 18 `LEA`,
  32 palettes par décor), validée au fork et dans un cœur FBNeo 448 ; étape `etape_decors.py` (PSD → zip).
- `SON-HYPER-ROM.md` : voix SFA1/SFA2 par version d'Hyper (prototype 144/218 voix, validé au fork).
- `VOIX-MAX.md` §9 : voix MAX renumérotées (v2) pour ne gêner aucun des trois jeux (conflit avec Cammy ALPHA).
- Conversion MAX : frames F26-F29 converties en blocs externes `$D40000 + $40000·k` (`convertit_frames.py`).

**Décisions de l'utilisateur (2026-10-10)** :
- Produit final = base **Upper** (mode Arcade, fins) + **MAX** + spécificités d'**Hyper** greffées (versions, mécaniques,
  écran de mode, ressources). Hyper n'a pas de mode Arcade ; son patch Arcade PS2 n'est pas à porter.
- Son : garder les voix d'origine par version (tout), pas d'écriture dans des « zones mortes », agrandir la capacité.
- Décors : en mode Arcade, tirage par perso adverse entre son décor SFA3 et son décor SFA2 (SFA1 écarté) ; essai sur le
  décor de Ryu en cours.
- **Validation §143 terminée** : Upper **40/40 fins** (ROM `0485973b…`), SFA3 32/32 (`f2f46b7e…`). Archives FBNeo
  refaites en mode strict (`HSFA_STRICT=1` : seulement les fichiers attendus ; `SOURCE_DATE_EPOCH` pour des zips
  déterministes) ; Upper avec les tuiles 32×32 vides corrigées.
- **Hyper dans FBNeo** (`docs/rapports/FBNEO-HYPER.md`, `tools/fbneo-hsfa/hyper-*.patch`) : pilote `sfa3hhsfa` (mécanismes
  d'Upper, blocs externes `$940000-$EFFFFF`, musique en flux « All tracks » par défaut) ; même déroulement que le fork sur
  une tournée VERSUS de 13 000 images ; états identiques. Défaut noté au fork : en TRAINING, saut à `$000001` vers
  l'image 2945 (perte de traduction à chercher).

### 144. Décision voie B (base Hyper) ; tout le contenu MAX converti ; décors, son d'Hyper, ROCKNIX, ISO seule

**Décision de l'utilisateur (2026-10-10, remplace « base Upper » du §143)** : le produit final part du module **Hyper**
(ro9), auquel on greffe la couche du **mode Arcade d'Upper** au niveau MIPS (« ro9 augmenté »), Upper servant d'oracle
(40/40 fins). Étude (`docs/rapports/ETUDE-UPPER-HYPER.md`) : 90 % des instructions d'Upper se retrouvent dans Hyper ;
voie A (Upper + versions d'Hyper) ≈ 34 000 instructions et toute la section de données d'Hyper ; voie B ≈ 3 350
instructions de cœur (≤ 260 Ko) et 0,1-0,3 Mo de données. Points durs de B : 109 variables A5 du mode Arcade retirées
par Hyper (table de relogement), lectures de `$102` à passer par `$116`. MAX : intégré d'abord sur Upper puis transposé
(98/120 adresses moteur identiques dans Hyper). Préparation de la greffe en cours (`work/greffe_arcade/`).

**MAX : tout le contenu converti vers l'image d'Upper** (`docs/rapports/CONV-MAX.md` §8-§9) : code de combat et de fin,
acteurs de fin, données, frames, animations de combat (`ANIM_26-29`) et de fin (`FIN_ANIM_26-29`), voix ; 0 non résolu,
121/121 adresses moteur, vasm 0 erreur ; un bloc externe par perso (`$D40000 + $40000·k`, rempli à ~76 %). Tables
d'Upper à déplacer et agrandir à l'intégration : `T_619b50` (banques d'acteurs, 40) et `T_61a100` (homologue de
`$DD412`, 32). Voix MAX v2 renumérotées sur des commandes libres dans les trois jeux.

**Décors** :
- export de TOUS les décors de SFA3 dans `decors_sfa3.psd` (26 groupes, 32 numéros, exact au pixel ; course Y réelle
  16 px vers le haut ; zones « décor qui s'arrête » ; phases de défilement animé) — `DECORS-WS.md` §9 ;
- essai d'import du décor de Ryu de SFA2 dans SFA3 traduit (`DECOR-SFA2.md`) : identique au pixel à `sfa2u`, nouveau
  décor `$50`, tirage par perso SFA3/SFA2 (3 modes), musique SFA2 par le lecteur de flux ; ≈ 2 jours pour les 17 autres
  sans leurs objets en sprites ; verrou : place des tuiles scroll2.

**Son d'Hyper** (`SON-HYPER-ROM.md` §11-§13) : la ROM QSound de 16 Mo est pleine (0,27 Mo récupérable proprement) →
**rejeu** : un 2ᵉ QSound rejoue les sons de SFA1/SFA2 tels que leurs pilotes Z80 les écrivaient (1 323 sons, données lues
dans les fichiers de l'utilisateur), validé son par son ; redirection par version dans le programme traduit
(0x6AE614, `$08C2AE`) essayée de bout en bout. Décision : sons SFA1/SFA2 et musique DANS le zip du jeu (portage FBNeo en
cours).

**Cœurs** : ROCKNIX / RGB10X (aarch64, glibc ≤ 2.38, 4:3 et 16:9, notice et système EmulationStation) — `ROCKNIX.md`.
**Construction depuis l'ISO seule** (`BUILD.md`) : `rom_iso.py` reconstruit la ROM graphique depuis l'ISO (4 fichiers sur 8
identiques à l'arcade ; suffisante pour la chaîne HSFA) ; zips déterministes (`SOURCE_DATE_EPOCH`), liste stricte
(`HSFA_STRICT`) ; `hsfa_gfx.py` rendu idempotent ; `banques.py` : fenêtre des plans (`HSFA_PLANS_FENETRE`).
**Historique GitHub réécrit** (accord de l'utilisateur) pour en retirer une adresse e-mail et des chemins locaux ;
dépôt privé ; avant publication : vérification complète ou dépôt neuf.

### 145. Hyper corrigé (jauge, TRAINING) et voix SFA1/SFA2 ; zips « tout dans le jeu » ; préparation de la greffe

**Intégré au traducteur** (validé par `valide_tout.sh`) :
- `CMPMM` (`DEFAUTS-HYPER.md`) : un `CMP` mémoire-mémoire (D8 servi par son domicile contre un champ) était perdu sans
  trace. Dans Hyper, la jauge de super n'avait plus de plafond : glitch de la barre du P2 en S-ISM, plantage en
  TRAINING. Confirmé corrigé sur console par l'utilisateur.
- Redirection des voix d'Hyper par version (`SON-HYPER-ROM.md` §13) :
  - module ro9 corrigé (70 mots, `tools/son-hyper/correctif_module_ro9.tsv`) ;
  - bloc de données `$E70000` (`HSFA_SON_DONNEES`) ;
  - `profils.py` lit `EXTRACT_MODULES`.
  `valide_tout.sh` construit Hyper ainsi par défaut (`SON_HYPER=0` pour l'ancien Hyper).

**Validation** :
- ROM : SFA3 `568cef19…`, Upper `a296538f…`, Hyper `a37df09c…` ;
- nonreg SFA3 : 42/42, 133,3 % ;
- nonreg Upper : OK ;
- VERSUS d'Hyper : aucune exception ;
- 32 fins SFA3 = arcade ±1 ;
- 40 fins Upper `fin=finie`.

**FBNeo** :
- branche `rejeu` (2ᵉ QSound qui rejoue les sons SFA1/SFA2 ; `REJEU-FBNEO.md`, `tools/fbneo-hsfa/0001-…patch`) ;
- `paquet_fbneo.py` met dans le zip d'Hyper `hsfa_flux.bin` (musique ADX, 695 Mo), `hsfa_rejeu.bin` et leurs tables,
  STOCKÉS et lus sur place : le zip d'Hyper (708 Mo) suffit seul ;
- essai du scénario de référence avec la ROM officielle : mêmes décisions du rejeu, dans le même ordre ;
- cœurs livrés : Android arm64 et ROCKNIX aarch64, 4:3 et 16:9.

**Retours console** de l'utilisateur :
- Sakura et Akuma OK, jauge d'Hyper OK ;
- correct sur RGB10X, aucun problème sur RG477M ;
- reste : texte « STREET FIGHTER ALPHA » qui défile mal pendant le gros A avant et après les combats (agent
  `agent_bandeau_A`) ; léger glitch des grands portraits avant les combats (agent `agent_portraits`).

**Voie B** (`GREFFE-PREPARATION.md`, `GREFFE-DECORS.md`) :
- scènes `A5+4` / `A5+8` nommées ;
- cœur à greffer : 530 routines, 287 Ko de MIPS, environ 9 950 instructions 68K ;
- table A5 : 36 relogés dans `$FF43BE-$FF4C8F` ;
- règle `$102` → `$116` ;
- zone d'accueil : le Z80 recompilé d'Hyper, 142 Ko, insuffisant pour tout ;
- prototype : 0 non résolu, 68K identique à Upper hors A5 relogés ;
- 39 décors d'Upper sur 40 absents d'Hyper.
Suite : `greffe_arcade` étape 2.

**MAX** : explosion = `$2E50A0` n° 5 (`EXPLOSION.md`). `$1A` des acteurs (`BANQUE-1A.md`) :
- persos MAX : posé par la partie commune `$4B`, il suffit de propriétaires distincts dans `T_61c0e0[$26..$29]` ;
- décor de fin : `$8000` ;
- explosion : `$0000`.

**En cours** :
- réorganisation des données, étape B (pointeurs de code, `agent_reorg_B`) ;
- greffe étape 2 ;
- bandeau du gros A ;
- portraits.
Reste : intégrer le rejeu au fork MAME (`rejeu-sur-fork-flux.patch`).

### 146. Glitch du grand portrait au face-à-face d'Upper : chargement différé de l'emplacement 4

**Symptôme** (`PORTRAITS.md`) :
- 5 images de tuiles de l'écran VS (fichier 457) à la place du grand portrait, quand le dialogue d'avant le
  1ᵉʳ combat se ferme ;
- vu dans Upper uniquement ; SFA3 et Hyper sont propres.

**Cause** : le jeu demande le fichier suivant (MIPS `0x25D6B4`) avant de quitter le portrait. Sur PS2, cette lecture
est mise en file : les tuiles restent en place quelques images. Le banc et le cœur, eux, changeaient de table tout de
suite. La traduction est conforme : même ordre que le MIPS, même durée que l'arcade.

**Correctif** : le nouveau fichier de l'emplacement 4 attend qu'aucun objet de cet emplacement ne soit plus affiché,
avec 10 images au plus.
- Banc : `BANC_LAT4` / `BANC_LAT4_MAX`.
- Cœur : `HSFA_LAT4`, `lat4=` dans la configuration du zip ; patch `tools/fbneo-hsfa/0002-…`, commit `3bc21ed` sur la
  branche `rejeu`.

**Validation** :
- portrait intact comme en arcade ;
- 797 captures FBNeo sur 797 identiques ailleurs ;
- avec `=0`, identique à l'ancien comportement ;
- la taille des états de sauvegarde change.

### 147. Texte du gros A (FLUXEA) ; écran de victoire ; options ; étape B ; greffe étape 2 ; dépôt réorganisé

- **Gros A** (`BANDEAU-A.md`) : les lignes « STREET / FIGHTER / ALPHA3 » traversaient l'écran pendant le balayage.
  - Cause : `MOVE.B (A3)+,$E(A4) ; MOVE.B (A3)+,$F(A4)` était traduit en `ADDQ #1,A3 ; MOVE.B -2(A3)`, ce qui n'est
    juste que si A3 est impair. La vitesse prenait donc l'octet voisin.
  - Nouvelle passe `byte_streams_ea` (`FLUXEA`) : 16 sites dans SFA3 et Upper, 12 dans Hyper. Positions identiques à
    l'arcade image par image.
  - Validation complète verte : ROM SFA3 `b62d489e`, Upper `efde8593`, Hyper `6a1cdd44`.
- **Écran de victoire** (`VICTOIRE.md`) : la réplique est conforme. « PRESS START » clignote, comme le veut le portage.
  L'utilisateur garde le comportement PS2.
- **OPTION / EXIT** (`OPTIONS.md`) : le §102 se trompait, `0x118A60` est un `memcpy`.
  - L'écran d'options est du code C du portage, dessiné par le GS. Sa recopie des réglages vers la RAM du jeu était
    perdue.
  - Désormais : retour au menu (`OPTION_RETOUR` / `EXIT_RETOUR`), et réglages en options du cœur FBNeo (patch `0003`).
  - Adresses : difficulté `$FF80A1`, dégâts `$FF80A0`, chrono `$FF80A3`, vitesse `$FF80A2`, manches `$FF80DF` /
    `$FF80DE`.
- **Réorganisation, étape B** (`ETAPE-B.md`) : tables de pointeurs de code relogées (`RELOGE_CODE` / `NATIF` /
  `RAM`).
  - Gain : −43 % d'appels de talons, −46 % de mots de conversion par tour. En combat turbo, 0,955 liste d'objets par
    image contre 0,667.
  - Piège : la cadence turbo. Une accélération partielle déplaçait la fin de l'image et faisait perdre une image ; les
    3 interrupteurs ensemble passent.
- **Greffe, étape 2** (`GREFFE-ETAPE2.md`) : l'Arcade d'Upper tourne dans Hyper augmenté et enchaîne 3 combats contre
  la liste d'Upper, à l'identique.
  - Plantage au K.O. du 3ᵉ combat, analysé avec la session MAX : la valeur `0x840688` est fausse dès la table (segment
    copié incomplet ou pointeur non relogé).
  - Règle : le combat reste celui d'Hyper. Les formats de combat d'Upper et d'Hyper sont identiques (97,5 % des
    animations) ; seuls diffèrent le bloc par perso (3, 6 ou 9 lignes) et `$2B8` (3 sous-tables de 48).
- **Effets de Vega** (`EFFETS-UPPER.md`) : objets attachés (classes `$13` / `$14`), table `T_60D480` = arcade `$B1910`.
  La table des blocs par perso d'Upper est `T_749838`.
- **Dépôt réorganisé** : `src/hsfa`, `scripts/`, `docs/{guide,architecture,reference,methodes,journal,rapports}`,
  `patches/`, `legacy/`. Publication par `publier.sh`, hors du dépôt.
- **Validation parallélisée** : `valide_tout.sh` lance les étapes en même temps (environ 1 h contre 3 h ;
  `PARALLELE=0` pour l'ancien enchaînement).

### 148. Étape B et OPTION/EXIT intégrés et validés

- **Traducteur** : étape B activée par défaut (`RELOGE_CODE` / `RELOGE_NATIF` / `RELOGE_RAM` à 1 dans `assemble.py`) ;
  OPTION et EXIT ramènent au menu (`OPTION_RETOUR` / `EXIT_RETOUR`).
- **Validation complète verte** :
  - ROM : SFA3 `7e22b1ec`, Upper `1908ec9e`, Hyper `964943b1` ;
  - nonreg SFA3 42/42 à 133,3 % (5 358 tours au lieu de 5 359 : un tour de retard à l'image 3 834, cf. `ETAPE-B.md`) ;
  - 32 fins SFA3 ±1 ;
  - 40 fins Upper ;
  - VERSUS d'Hyper sans exception.
- **`valide_tout.sh` parallélisé** : environ 1 h au lieu de 3 h (`PARALLELE=0` pour l'ancien enchaînement).
- **Hyper, bloc par perso et `$2B8`** (`work/agent_bloc_hyper/BLOC-HYPER.md`) :
  - ligne = table[`$102`] + 16 × isme ; table `0x6A7A94`, `0x6A7C94` (`$F0` < 0) ou `0x6A7D54` (`$123` = 2) ;
  - `$2B8` : index = n + 48 × s, s étant choisi par le dernier coup reçu (ZERO 3, version ancienne, custom combo) ;
  - jeux de boîtes ajoutés par perso (aucune boîte de corps, une seule boîte) ;
  - recette pour les persos MAX aux places 38-41 : 3 lignes, 3 tables, `$2B8` à 144 entrées.

### 149. Musique d'Hyper : origine des flux identifiée, plan partitions + compression

Session d'étude hors dépôt (2026-10-14 au 16), intégrée depuis une session cloud. Détail et plan :
`docs/rapports/PLAN-SON-HYPER.md`.
- **Banc Z80** (`tools/son-hyper/mesure_boucles.py`, `pilote.py`, `parcours.py`) : les pilotes son d'origine (SFA1
  v1.05A, SFA2 v1.05C, SSF2 v1.04) tournent dans un émulateur Z80 ; intro et boucle mesurées par morceau
  (`mesures_z80.tsv`). Calibrage : un flux de l'Anthology dure « intro + une boucle » (3 % près, 24/32).
- **Jeu de flux A (Y553-586) = *Super SF2* arcade** : 25/34 à ≤ 1 %, 32/34 à ≤ 2,5 % (`variantes_ssf2.tsv`). B, C et
  les 19 flux longs ne sont pas SSF2. SSF2, SSF2T et *Hyper SF2* ont la même musique.
- Hypothèses (wikis japonais) : C = arrangement 3DO (SHADALOO-B), B = *SF2'* CPS-1 (titres bleus), longs = *Final
  Fight* console. ALPHA = arrangement PlayStation / Saturn enregistré, sans partition.
- **Correction** : `0x30-0x36` (persos d'Upper) ne sont pas en QSound ; seuls les 44 flux marqués `q` le sont.
- **Plan** : retirer les flux `q` du paquet ; SFA1, SFA2 et SSF2 en partitions sur une « carte musique » (recommandé :
  pilotes d'origine plutôt que conversion en v1.71) ; Vorbis pour le reste. ≈ 696 Mo → ≈ 90 Mo.
- Rien n'a été exécuté sur des données de jeu dans cette session : les scripts et les TSV viennent de la session d'étude.
- **Reprise du 2026-10-16** : banc Z80 reproduit depuis les zips (SFA1 et SFA2 identiques ligne pour ligne ; SSF2T =
  SSF2 sauf `02`). **Banc CPS-1** (`banc_cps1.py`) : *SF2'* et *Final Fight* mesurés (`mesures_cps1.tsv`) ; aucune
  concordance avec les jeux B et longs, même à un autre tempo. B et longs : pas de partition connue, identification à
  l'oreille.

### 150. Flux musique en Ogg Vorbis dans le cœur FBNeo ; cœurs Windows ; phase 1 du son d'Hyper

Session cloud du 2026-10-16, sans données de jeu (détail : `docs/rapports/PLAN-VORBIS.md`, « État au 2026-10-16 »).
- **Cœur** : patchs 8 `0004-HSFA-stb_vorbis.patch` (stb_vorbis 1.22, API mémoire, `-DHSFA_FLUX_VORBIS`) et 9
  `0005-HSFA-flux-musique-Ogg-Vorbis.patch` (`hsfa_flux.h` : une entrée de l'AFS peut être un Ogg Vorbis ; boucle
  `LOOPSTART` / `LOOPEND` ; anneau de 2,7 s ; état inchangé, 124 octets). Le fork MAME reste en ADX.
- **Banc** `tools/flux/tests/lance_tests.sh` : 23 contrôles bons sur Linux, Windows (Wine) et ARM64 (QEMU) ; boucle
  et rechargements d'état exacts à l'échantillon.
- **Encodeur** : `tools/flux/fluxtool.cpp` + `flux_ogg.py`, branchés dans `paquet_fbneo.py` (`HSFA_FLUX_FORMAT=ogg`,
  cache `<work>/flux_ogg/`, contrôle par flux).
- **Phase 1** : le zip d'Hyper n'embarque plus les flux des codes `q` (ZERO 3 déjà en QSound) ; `HSFA_FLUX_ZERO3=1`
  pour les garder.
- **Windows** : `tools/windows/build_win.sh` (MinGW-w64, `LIBS=-static`), notice, frontaux de test `charge.c` /
  `joue.c` ; SFA3 arcade tourne sous Wine dans les deux cœurs.
- **À faire chez l'utilisateur** : zip d'Hyper en Vorbis, un match comparé à l'ADX (journal `HSFA_FLUX_LOG`), puis
  Vorbis par défaut ; mesure sur la RGB10X.
- **Carte musique, étape 1** (`PLAN-PARTITIONS-HYPER.md`) : rendu hors ligne des 32 morceaux ZERO / ZERO 2 par leurs
  pilotes d'origine (`tools/son-hyper/rendu_partitions.py`) ; tous bouclent nettement sauf SFA1 `07` ; la boucle du
  banc est fausse pour `03`, `04`, `08`, SFA2 `11`.
- **Récapitulatif de la session cloud et liste ordonnée des essais à faire en local** :
  `docs/journal/SESSION-CLOUD-2026-10-16.md`.

### 151. Carte musique : partitions SFA1 / SFA2 d'Hyper par leurs pilotes d'origine (patch 10)

Session cloud du 2026-10-16 (détail : `docs/rapports/PLAN-PARTITIONS-HYPER.md`, « État »).
- `hsfa_musique.h` : 2ᵉ Z80 qui fait tourner le pilote d'origine (photo après démarrage, restaurée à chaque morceau),
  3ᵉ QSound sur la ROM du rejeu, fondus PS2, état en un bloc. Patch 10 `0006-HSFA-carte-musique.patch` (Zet n° 1,
  aiguillage carte → flux → Z80 principal) ; `paquet_fbneo.py` : `HSFA_PARTITIONS=1`.
- Bancs (`tools/son-hyper/tests/lance_tests_carte.sh`) : tous bons avec le Z80 de test et avec le Z80 de FBNeo ;
  sortie conforme au rendu hors ligne (0,98) et identique d'un Z80 à l'autre à l'oreille (0,998).
- À faire en local : zip d'Hyper avec `HSFA_PARTITIONS=1` et cœurs Android / ROCKNIX avec les patchs 1-10, puis
  matchs en version ZERO / ZERO 2.

### 152. Hyper : tous les flux en Ogg ; pistes réellement jouées ; 2ᵉ code confirmé

Session cloud du 2026-10-16 (détail : `docs/journal/SESSION-CLOUD-2026-10-16.md` §6, fin).
- Décision de l'utilisateur : tous les flux d'Hyper en Ogg Vorbis (zip 201 Mo). La phase 1 (thèmes ZERO 3 rejoués en
  QSound) n'est plus appliquée que sur `HSFA_FLUX_SANS_Q=1` (174 Mo).
- Le zip ne contient que les 216 flux demandables par les tables du 68K (sur 588 dans `Y_DATA.BIN`) : rien du lecteur
  de musique ni des autres modules.
- Le 2ᵉ code (`$C3B6`) est la musique de vie basse des variantes : `0181 -> Y554` puis `0192 -> Y571`, vu en jeu.
  `tournee.h` choisit l'ISM (`.iX` / `.iA` / `.iV`).

### 153. Cœurs ROCKNIX avec les patchs 1 à 10, exécutés sous émulation ARM

Session cloud du 2026-10-16 (détail : `docs/rapports/ROCKNIX.md` §7).
- Cœurs `fbneo_hsfa` / `fbneo_hsfaws` aarch64 refaits (Vorbis + carte musique), glibc ≤ 2.38.
- Premier passage sur ARM (`qemu-aarch64`) : VERSUS d'Hyper piloté, mêmes musiques qu'au PC, son à ±1 près.
- Kit `tools/rocknix/essai_son/` : à lancer par SSH sur la RGB10X pour la vitesse réelle.

### 154. Tournée complète d'Hyper (151 VERSUS) dans le cœur FBNeo

- `tools/fbneo-hsfa/essais/tournee_complete.py` : 151 matchs bons sur 151, musiques conformes aux tables du 68K.
- 122 codes sur 216 entendus ; jamais obtenus : variante B (`$122`), EX (`$15F`), jingles ZERO 3 hors VERSUS.
- Script Android `tools/android/build_android.sh` écrit (lancé ensuite, §155).

### 155. Cœurs Android avec les patchs 1 à 10

- `tools/android/build_android.sh` (NDK r28c) : `fbneo_hsfa_libretro_android.so` et `fbneo_hsfa_ws_libretro_android.so`
  construits et contrôlés (dépendances, exports, Vorbis, alignement 16 Ko). Non exécutés sur Android.

### 156. Modes cachés de la sélection d'Hyper et musiques B / EX

- Menu des modes : curseur `P+$5C` ; Start tenu + ← / → : S-ISM (`$5C` 6, 5, 7, 4 pour NORMAL, MAZI, SAIKYO, CLASSIC).
- CLASSIC et Saikyo S-ISM (`$15F`) → table « EX » ; Mazi S-ISM (`$123`=02) → variante B. Start tenu à la version →
  persos EX. 194 codes sur 216 entendus en jeu (`SON-HYPER.md` §2.3).
- Outils : `tournee.h` (`.m`, `.e`, `.v`), `tournee_complete.py --z3`, `joue_linux` `HSFA_RAM_DUMP`.

### 157. Patch 11 : roulette de la sélection d'Hyper sur la touche Pièce

- `0007-HSFA-roulette-touche-piece.patch` : `$D3` (roulette) d'après la touche Pièce du joueur, sur la grille
  seulement ; Start reste au jeu (EX, EX Balrog, S-ISM). Détail : `ETATS-HYPER.md` §1.1, `LISEZMOI-hyper.md`.
- Cœurs Windows / ROCKNIX / Android / Linux refaits avec les patchs 1-11 (paquet `hsfa-coeurs-2026-10-16b.zip`).
- Pilote : `.r` (Select tenu à la validation), `.g` (Start tenu) ; `tournee_complete.py --roulette`.

### 158. Cris de dégâts / K.O. d'Hyper (versions ZERO, ZERO 2, ALPHA) pris sur l'arcade

- Signalé par l'utilisateur (Ryu ALPHA 1 en J2). Les cris `$4000 + 8v + n` venaient de la DTW (§5 de SON-HYPER-ROM) :
  SFA1 Ryu `0165`/`0166` au lieu de `0167`, K.O. et cris de ZERO 2 / ALPHA parfois restés SFA3.
- Mesure sur les arcades : `tools/son-hyper/mesure_cris_arcade.py` → `cris_arcade.tsv` ; correctif
  `tools/son-hyper/corrige_cris.py` (table du rejeu seulement, aucune retraduction), appliqué par `paquet_fbneo.py`.
- À faire : Akuma, Bison, Dan de SFA1 (déduits, non mesurés) ; rôle des `n` 5 et 6.

### 159. Voix « par pas » d'Hyper (ZERO, ZERO 2, ALPHA) vérifiées et corrigées sur l'arcade

- `compare_voix_arcade.py` (gestes identiques depuis un état sauvé, frontal `HSFA_GESTES`), `marque_voix.py` (codes
  marqueurs dans les tables `$E6` → code SFA3 d'origine de chaque voix), `fusionne_voix_arcade.py` →
  `voix_arcade.tsv` (131 codes : 112 justes, 6 faux, 12 SFA3 gardés à tort, 1 conflit).
- `corrige_voix.py` : tables du bloc de la redirection dans `hsfa_ext.bin`, sans retraduction ; appliqué par
  `paquet_fbneo.py` ; `gen_redirection.py` lit `voix_arcade.tsv`. Détail : `SON-HYPER-ROM.md` §4.3.

### 160. Voix d'Hyper : supers, persos cachés de SFA1, rôle des cris

- `compare_voix_arcade.py --super` (jauge remplie par un prélude) et `--poke` (frontal `HSFA_POKE` : perso de SFA1
  forcé par `$FF84A2`) ; `marque_voix.py --super`. Cris : `n` 3 = projeté, 5 = garde brisée (`T_V2_V`).
- `voix_arcade.tsv` : 158 codes ; `cris_arcade.tsv` : Akuma, Bison, Dan mesurés (Dan = cris de Ryu). Versions EX
  sans référence arcade. Détail : `SON-HYPER-ROM.md` §4.3.

### 161. SFZ2 Alpha comme référence des versions ALPHA et EX d'Hyper

- `sfz2al.zip` : son et Z80 identiques à SFA2 ; ALPHA = SFA2 sauf Rose (`0305`, déjà juste dans Hyper) ; EX : tout
  juste sauf la projection HK d'Akuma EX `$74` (table du module : à la retraduction). `compare_voix_arcade.py --start`.


### 162. PILE_LUI : comparaisons perdues (temporaire de pile pris pour la constante d'un `lui`) ; v149

**Défaut** (trouvé par la greffe, `docs/rapports/GREFFE-ETAPE3.md` et suite) : un temporaire de pile qui recevait une
valeur LUE EN MÉMOIRE était pris pour la constante d'un `lui` périmé du même registre.
- Cas type : `lui v1,0x7000 ; lw a0,A5(v1) ; lh a0,$138(a0) ; dsll32/dsra32 v1,a0 ; sw v1,408(sp)`.
- La comparaison devenait `CMP #$70000000,#6` et n'était pas émise : le `Bcc` lisait les drapeaux de l'appelant.
- Les fonctions à prologue `sq` (temporaires sur la pile) sont celles qui y sont exposées.

**Correctif** : `PILE_LUI` (défaut 1, `=0` → ancien comportement), 8 lignes de `translate.py`.
- SFA3 inchangée.
- Upper : 7 comparaisons rétablies, par exemple `CMPI.W #$6,$0138(A5)` en `0x269488`, `CMPI.W #$90/#$30,$011E(A6)` en `0x0BE014` / `0x351758`, `CMPI.B #$44,$0147(A5)` en `0x18408C`.
- Hyper : 26 sites, du code de combat compris, dont le K.O. en `0x9DF4C`.

**Validation v149** : ROM SFA3 `7e22b1ec`, Upper `7898814c`, Hyper `cb9b37b9`.
- nonreg 42/42 à 133,3 % ;
- 32 fins SFA3 ±1 ;
- 40 fins Upper ;
- VERSUS d'Hyper sans exception.

**Organisation** :
- traducteur sous git local (étiquettes `v148`, `v149`) ;
- références figées par version, avec les md5 ;
- `scripts/validation/nonreg_coeur.sh` : non-régression du cœur FBNeo (captures, journaux, son) contre un cœur de référence, en environ 20 s.

### 163. VRAM_TABLE : décor de Cammy ($2C) sans son plan du dessus ; v150

**Défaut** (`DECOR-CAMMY.md`) : dans le décor de Cammy, scroll2 disparaissait vers l'image 20 de chaque manche, emportant
le moulin, la maison, les murets et le sol.
- Le code en cause : `MOVE.W T_614a60(PC,D0.W),D7 ; LSL.L #8 ; ANDI.L #$FFFFFF ; MOVE.L D7,$C134(A5)`.
- La table contient des adresses vidéo hôte PS2 décalées de 8, que personne ne convertissait.
- Même site dans SFA3 (ro3 0x111698).

**Correctif** : règle `VRAM_TABLE` (conversion bornée à l'exécution après l'`ANDI`). Balayage des 40 décors d'Upper :
seul `$2C` avait ce défaut.

**Validation v150** : ROM SFA3 `6230bba0`, Upper `36fc4f37`, Hyper inchangée `cb9b37b9`.
- nonreg 42/42 ;
- 32 fins SFA3 ±1 ;
- 40 fins Upper : 3 balayages interrompus en cours de route (journaux arrêtés vers l'image 30 000, sans exception), qui vont au bout une fois rejoués seuls ;
- VERSUS d'Hyper OK.

### 164. Persos MAX dans Upper : lots 2b4 à 2b9 (retours console)

Détail : `docs/rapports/INTEGRATION-MAX-UPPER.md` (§8.6-8.13) ; outils : `tools/integration-max/upper/`.

- **Collisions d'ID d'Upper** : `$27` = emplacement 39 (variante Juli/Juni), `$28`/`$29` = pseudo-ID de Vega et de
  Chun-Li X. Yun et Ingrid prennent donc `$2D` et `$2E`.
- **Cris** : table des bases de cris par ID = PS2 0x613490 (cri = base + 0..8, côté 2 +`$500`), 0x613440 = base + 5 ;
  blocs MAX dans une ROM son régénérée.
- **Portraits de victoire** : 0x72BDF0[ID] = 6 couleurs × 8 palettes ; les groupes 1-5 sont à remplir aussi.
- **Portrait de Ryu (bande noire)** : les poses ≥ 32 de 0x674C00 sont une bande PARTAGÉE A[pose − 32 + ID] ; ne jamais y
  écrire.
- **Bio** : illustration native par perso 0x628470 → `$37AF00` → `$C0BC(A5)` ; texte 0x960090 + 0x61C0C0.
- **Entrées (`MAX_ENTREES`)** : Upper ne tient pas « juste appuyé » (`$378`) à jour pendant les spéciaux ; le front
  `$370 & ~précédent` est recalculé une fois par image (poings bits 8-10, pieds bits 12-14) dans `$3F6-$3FA` (libres).
  Débloque la course de Maki (glissade, bond, chope).
- **Effets MAX (`EFFET_W`)** : gestionnaire, puis `move.b #$10,$9(a6)` (classe d'affichage `$10` au lieu de `$18`, qui
  refait l'animation par type), puis `$19D9A`. Particules et étoiles d'Ingrid.
- **Contres** : 11-14 routés vers `CONTRE_MAX_xx` depuis l'aiguillage `$40D4` ; accès arcade → image
  (`$5F`→`$5E`, `$25D`→`$25C`, `$5D`→`$5C`, `$55`→`$54`).
- **Fins** : scène 1108 = 4 jeux de palettes (a5 OBJ, a6-a8 scroll1-3), seul a5 est remplacé par des « images » de
  palettes MAX, et un x9 suit chaque x5 ; emplacement 4 = fichier fusionné (table du modèle, puis tuiles FD, codes FD
  décalés de N) ; plans du modèle, sauf Maki (plans vides). Homologue d'Upper de `$81522` = 0x960180 (classe `$48`).
- **Témoin Ryu PSP** (même chaîne de conversion que les 4) : la conversion n'ajoute pas d'échelle, 344/391 frames
  identiques à Ryu d'Upper, et les écarts restants sont des retouches de dessin PSP.
- **Ouvert** : décors gris-vert de quelques scènes de fin ; accélérations de Maki au coup de pied après le bond (spécial
  10) et décalage de la chope ; comparaison d'échelle avec une capture PPSSPP (Eagle contre Ken, en garde).

### 165. Greffe Arcade sur Hyper (voie B) : étapes 4 à 6

Détail : `docs/rapports/GREFFE-ETAPE4.md`, `GREFFE-ETAPE5.md`, `GREFFE-ETAPE6.md`.

- Étape 5 : 59 fins sur 85 combinaisons sélectionnables vont au bout (durée à ±2,2 % d'Upper).
- Étape 6 :
  - `PTR_BAS` (conflit 18/0E résolu, 0x2C510 greffée), `FE_TABLE`, `ANIM_GREFFE` (cœur de pose d'animation d'Upper),
    `PLANS_CONT` ;
  - CONTINUE conforme en durée et en fond (chiffre et texte encore absents) ;
  - GAME OVER : fond violet, sans les lettres.
- Restent : persos 05, 15, 17, 19, 1B-1D, 21, 22 et une version de 06 / 0F / 11 ; décor du boss en scène 1 des fins
  (chantier des décors).

### 166. Persos MAX dans Upper : lots 2b10 à 2b15, transparence dans le cœur

Détail : `docs/rapports/INTEGRATION-MAX-UPPER.md`, `docs/rapports/TRANSPARENCE*.md`, `docs/architecture/coeur-fbneo.md`.

- **Échelle** : la PSP dessine Eagle, Maki et Yun (et leurs tirs / effets, et l'aperçu de sélection des 4) avec des
  cases de 32 texels sur 38 px (×19/16), ancre X ×12/10 (octet +0x57 du sprite, recopié de +0xAB). Mesuré au pas de
  pixel sur captures PPSSPP (3,95 contre 3,33 pour Ken), puis trouvé dans FUN_0000D2A8 / CD84. Conversion étirée
  (racine v2) ; boîtes inchangées.
- **Maki** : table de sauts `$34A` non posée (envol), table des projections 0x7495B8 par perso, natifs étendus à 48
  colonnes.
- **Bandeaux et noms** : « WINNER:<nom> » vertical = animation de 0x966740 indexée par la table d'octets T_616850
  (frames $0C à aligner sur 4 octets) ; frise 1P / 2P 0x9620B8… ; colonne de la carte du monde = frames $0A des listes
  0x967F2A ; bio : table ID → fichier 0x60AD90 (40 octets) étendue à 48.
- **Fins** : opA = vitesse de défilement des plans (pas un décalage, comme sur PSP) ; x9 d'image entière à 30 palettes
  (OBJ 30-31 réservées au texte) ; fenêtre de texte = acteur PSP $4F/04 → Upper $49/00 anim $5D (sinon le
  remplissage magenta du plan 3 apparaît).
- **Transparence** : la PSP dessine des effets MAX en additif, décidé par objet (+0xAA). Cœur : patch 0010 (registres
  par palette OBJ `$804220-$80423F`, mode des objets marqués `$804240`, bit 12 du mot X de la liste brute) ; table RAM
  `$FF7F00` (un octet par emplacement d'objet) écrite par le code MAX ; EFFET_W et les enveloppes de tirs posent le
  bit 12 dans `$18(A6)`, que les écrivains du mot X recopient. Patch 0011 : ombres translucides comme sur PSP (palette
  0x14 + codes de tuiles d'ombre).
- **Ouvert** : couleurs de certaines scènes de fin (acteurs $4B à banque perso : `$D`), invités en mosaïque, effets de
  Maki à vérifier (spéciaux 4, 6, 9).

### 167. Tableau des coups d'après le guide BradyGames (pour tester les coups d'Hyper)

- Guide « Street Fighter Alpha Anthology » de l'utilisateur (PDF scanné, 291 pages) transcrit en entier et mis en
  tableau, une ligne par coup (jeu, mode, perso, ISM / version, type, nom, manipulation en flèches, boutons, conditions,
  page). Flèches relues à 300 dpi ; lancers / spéciaux / supers / alpha counters de SFA1, SFA2/Gold et SFA3 confrontés à
  SuperCombo Wiki : 90 coquilles du guide corrigées (forme imprimée gardée dans `conditions`), 9 lignes « à tester ».
- Outils et méthode : `tools/guide-coups/` (README). Texte protégé : PDF, transcription et tableau hors dépôt ; tableau
  envoyé à l'utilisateur et à la session « HSFA PS2 CPS2 » pour les essais.

### 168. Ce que la recherche du livre apporte au projet

- Recherche documentaire du livre (11 axes, sources EN/JA, MAME/FBNeo/HBMAME, guide BradyGames) relue pour HSFA :
  `docs/rapports/recherche/` (README = synthèse priorisée ; A persos cachés et modes, B révisions / bugs / régions,
  C technique et méthode pour une 1.0). Protocoles seulement, rien n'a été lancé.
- Points saillants : l'Anthology n'offre pas la révision 980904 de `sfa3ud` et la conclusion du §96 est à refaire
  Japon contre Japon ; sens des S-ISM SHADALOO A-D ; `$58/$59` probablement défauts PS2 ; test CFC2 pour MAX (Bison,
  R. Mika contre Eagle/Maki/Yun/Ingrid) ; QSound FBNeo = superctr (`coeur-fbneo.md` corrigé) ; Zer0-NexuS a les voix
  de Cammy (`X_0333`) ; FBNeo/HBMAME acceptent une CPS-2 fictive (voie vers Fightcade).

### 169. Sondes de la recherche : modes d'Hyper, test CFC2 sur Upper + MAX

Détail : `docs/rapports/recherche/D-SONDES.md` ; outil : `tools/sondes-recherche/banc_coups.py` (un geste contre une
liste d'adversaires, Upper / Hyper / arcade, vie de J2 ou trajectoire de J1). Construction : `sfa3uhsfa.zip` du
2026-10-18 (`e0a969d0…`).

- Hyper : Mazi = 1 manche (33/33) ; S-ISM rose réservée aux 12 persos de *SF2'* ; Bison en S-ISM rouge : `$15C = $80`,
  mais rien de visible au super, Final Bison non confirmé.
- **Head Press de Bison** : il touche les 4 MAX. La table par adversaire `0x623E50` est étendue à 3 × 48 dans
  `hsfa_ext.bin` et c'est elle qui est lue (vérifié en la faussant). `tables_par_id.json` la classe pourtant `simple`.
- **Skull Diver de Bison** : il rate **Ingrid et Sakura**, mais touche tous les autres. Hyper Z3 et l'arcade touchent
  Sakura. L'arc ne s'adapte pas à Sakura dans Upper+MAX. Ce n'est ni `0x623E50` ni `0x622D10`. Upper sans MAX
  (zip du 2026-10-07, avant §143 et §162) rate aussi Sakura : ce n'est **pas une régression MAX**, et les correctifs
  `LUIDN` / `PILE_LUI` ne l'ont pas réglé. Reste à voir sur PCSX2, puis point d'arrêt mémoire au banc MAME.
- Piège : Upper part en X-ISM et l'arcade en A-ISM ; les dégâts 13 contre 10 viennent de l'ISM.
- Touches (patch 11) : les bancs n'appuient sur Start J2 qu'avant la grille.

### 170. Matrice des coups : Hyper Z3 contre SFA3 d'arcade

Détail : `docs/rapports/recherche/D-SONDES.md` §3 ; outil : `tools/sondes-recherche/banc_matrice.py` (tous les spéciaux /
supers / lancers du tableau BradyGames, 4 essais en parallèle, environ 25 min pour 812 essais).

- 203 coups joués, 2 distances, A-ISM, jauge pleine (mot `+$21C` = `$1B0` ; `+$11E` = `$90` est la taille d'un niveau).
- 226 dégâts égaux, 24 écarts, dont 22 **reproduits** avec les deux calages.
- Candidats principaux :
  - Killer Bee Assault de Cammy (plongeon qui rate ; cause trouvée au §171, autre que celle du Skull Diver de Bison) ;
  - Hissho Burai Ken de Dan (la super ne part pas) ;
  - enchaînements coupés : Fuji Oroshi de Honda, Tiger Genocide de Sagat, supers de Balrog.
- Réserve : l'arcade est en 980904, l'Anthology en 980727. Il faut les ROM japonaises pour séparer révision et
  traduction.
- Pièges du banc :
  - le début de manche d'Hyper dépend de la paire de persos ;
  - l'intro de Karin dans Hyper rend la main plus tard (geste à + 450) ;
  - le son de chaque essai pesait 10 Mo et a rempli le disque (`/dev/null` maintenant).

### 171. Killer Bee Assault de Cammy : aide `roxr`, `EXG` et `BCLR` perdus (Hyper, Upper)

Détail : `docs/rapports/recherche/D-SONDES.md` §4 ; outils : `tools/sondes-recherche/` (README).

- **Symptôme** (matrice, §170) : Hyper 0 contre arcade 60. L'angle vers l'adversaire vaut 0 au lieu de `$1D`. Cammy
  part tout droit vers le haut et passe dans le sous-état de raté `$16`.
- **Cause** : la fonction de visée (arcade `$05DAEE`, Hyper `$4BA8E`, Upper `$67792`) a trois pertes :
  - `ROXR.B #1,D6` ×4 passe par l'aide `roxr` du recompilateur, traduite en talon vide (`$104E` / `$1042`) ;
  - `EXG D2,D3` devient deux `MOVE` ;
  - `BCLR #0,D6 ; BNE` devient `ANDI` puis `BTST`.
- **Preuve** : une rustine d'essai sur une copie d'Hyper donne 60 aux deux distances, avec des angles identiques à
  l'arcade. La matrice refaite ne change que ces deux lignes (24 → 22 écarts).
- **Déjà décrit** dans l'index par `agent_defauts_banc` : règles `EXG_PILE_D`, `AIDE_ROXR`, `BITOP_DN`, « v150 ».
  Mais ces règles sont **absentes de `src/hsfa/`**, et les archives d'Hyper (2026-10-11) et d'Upper (2026-10-18) ont
  le défaut. À verser au dépôt, puis tout reconstruire et valider.
- **Même famille** : 4 autres `EXG` perdus dans Hyper (arcade `$5850C`, `$187DC` ×2, `$18822`) et 20 paires dans
  Upper (`paires_exg.py`). Les corps des aides `sbcd` et `abcd` sont appelés 4 fois chacun (Upper `$592DC`, `$226C8` ;
  Hyper `$8B374`) : ajouts / retraits BCD à vérifier en mode Arcade.
- **Bison contre Sakura dans Upper** : autre cause. Les vitesses sont les mêmes contre Ryu et Sakura, et les `EXG`
  corrigés n'y changent rien.
- **Outils du banc** :
  - sonde de PC dans le cœur FBNeo (`sonde_pc_fbneo.diff` : PC, adresse et valeur de chaque accès 68K dans une plage) ;
  - déchiffreur CPS2 (`dechiffre_cps2.c`), pour lire le programme de l'arcade ;
  - frontal : 16 captures au plus par essai (la trace se fait par lots).

### 172. Point d'étape transverse du 2026-10-21

Détail : `docs/rapports/POINT-ETAPE-2026-10-21.md`. Il repose sur une passe sur tout le dépôt (quatre lectures
croisées et un audit des noms cités contre le code).
- **Code en retard sur le savoir** : les règles du §171, les aides `roxr`/`sbcd`, les interrupteurs de la greffe 4-6,
  les crochets `MAX=1`, le paquet ro9a et des options du cœur sont décrits, mais absents du dépôt.
- **Toutes les archives en circulation sont antérieures à au moins un correctif connu.**
- **`valide_tout.sh` ne tourne pas depuis le dépôt seul** : `$S` n'est pas défini, et il dépend de `work/`.
- **Conflit latent** : `$FF7F00` (transparence MAX contre drapeau de la greffe).
- **Décisions à prendre** :
  - D1 : IDs MAX dans Hyper ;
  - D2 : `$FF7F00` ;
  - D3 : `$3A0000` ;
  - D4 : choix du décor de l'Arcade greffée ;
  - D5 : jauges à 50 % ;
  - D6 : Vorbis par défaut ;
  - D7 : oracle de SFA3 (980904 ou 980727).
- **Ordre de marche proposé** : verser les correctifs, reconstruire et valider une fois pour tous, trancher D1-D3,
  verser les rapports restés dans `work/`.
- **Transmission pour la reprise** (fusion sans écrasement, §173 = prochaine section libre, consigne par session) :
  `docs/journal/TRANSMISSION-2026-10-21.md`.

### 173. v151 : six règles du traducteur issues du banc des coups

Détail : `docs/rapports/DEFAUTS-BANC.md` (§5a, §7b), sites par module : `DEFAUTS-BANC-SITES.md`. Étiquette git `v151` du
traducteur (fusion de la branche `defauts-banc`), références `work/references/v151`.

| règle | défaut | effet |
|---|---|---|
| `RETAG24` | `ANDI.L #$00FFFFFF` des « fantômes » de super efface l'étiquette `$01` des pointeurs du bloc externe `$940000` | supers d'Hyper ZERO / ZERO 2 / ALPHA : exceptions au talon `$A08` (98 / 133) → 0 |
| `EXG_PILE_D` | `EXG Dx,Dy` perdu (temporaire de pile ou registre MIPS) | `paires_exg.py` : 0 paire en long |
| `AIDE_ROXR`, `BITOP_DN` | aide `roxr` du recompilateur réduite à un talon vide ; `BCLR` testé après effacement | Killer Bee Assault de Cammy = 60, comme l'arcade (§171) |
| `COUPE_BLOCS` | la coupure des données ro9 tombait au milieu du bloc d'Evil Ryu | Evil Ryu ALPHA |
| `CMPDMEM` | `CMP` « registre moins mémoire » perdu quand le résultat ne va que dans RES (5 sites SFA3) | objet des arcs du Kikosho de Chun-Li : 18 → 144 images |

**Validation** : SFA3 `e0f1cfdc`, Upper `0b8ecca2`, Hyper `39985037` ; valide_tout sans ECART (fins SFA3 32/32, Upper 40/40,
VERSUS d'Hyper) ; bancs : Hyper 92,3 % → 98,9 % (exceptions 316 → 0), ro3 KO 63 → 59, ro5 KO 258 → 257, aucune
régression ; tous les interrupteurs à 0 = v150. Bloc externe d'Hyper +23 Ko (fin `$BD8AF0`), le paquet passe.

**Restent** : les grands arcs du Kikosho restent invisibles en SFA3 et Upper alors que l'objet vit le bon temps
(rendu : palettes 3/4, codes `$5009-$5016`) ; aide `sbcd` non traduite (rien n'en dépend) ; lancers aériens = portage ;
Alpha Counter = artefact du banc.

### 174. Outils MAX : passation, oracle PPSSPP, comparateur de traces, audit des tables par id

- **Passation de la session MAX** : `max/notes/SAVOIR-MAX.md` ; 27 pièges dans `AGENTS.md` ; contrôle de la passation
  contre son historique (37 manques, 43 lignes d'index) ; ses scripts PPSSPP et générateurs d'index versionnés
  (`max/outils/ppsspp`, `max/outils/index`).
- **Oracle PPSSPP** (`tools/ppsspp-banc/`, PPSSPP-BANC.md) : PPSSPPHeadless 1.20.3 officiel + patch (images exactes,
  états, son, débogueur sur 127.0.0.1, trace des appels) ; `psp_debug.py` (classe Banc), scénarios MAX ; reproductible à
  l'octet. Ids PSP : Eagle 0x26, Maki 0x27, Yun 0x28, Ingrid 0x29 ; RAM des données = 0x08804000 + 0x2D4F30 + VA.
- **Comparateur de traces** (`trace_appels.py`) : fonctions `psp_` appelées sur PSP et dans Upper MAX (MAME), alignées ;
  première divergence. Retrouve seul les défauts connus (super d'Ingrid psp_1c5228, onde de Yun psp_1c19e0).
- **Audit des tables par id** (`docs/rapports/AUDIT-TABLES-ID.md`) : 177 tables d'Upper indexées par id ; 8 défauts
  visibles (dialogues, RESULT, parcours, combat secret, carte, valeurs physiques, visage HUD), 58 latents ; les listes
  rel16 recopiées perdaient leur marque de fin (intro de Yun suivie de celle d'Ingrid) → contrôle `marques.py`.
- **Organisation** : échanges intégration ↔ session MAX dans un fichier commun (hors dépôt) ; banc de non-régression MAX
  obligatoire avant livraison ; le scratchpad d'une session est effacé entre deux sessions.
- **Décisions** (25/10) : persos MAX adversaires CPU comme sur PSP ; carte : « INGRID » (« ? » seulement dans sa fiche).

### 175. Banc MAX mode B (oracle PSP), crochets MAX=1 et greffe versés au dépôt

- **Banc mode B** (`tools/banc-max-psp/`, BANC-PSP.md, RESUME-PSP.md) : chaque coup est joué sur SFA3 MAX PSP (PPSSPP,
  J2 piloté par un point d'arrêt sur la routine d'entrée 0x55650) et dans Upper MAX (MAME), puis comparé tour par tour
  (verdicts IDENTIQUE / PROCHE / DÉCALÉ / MUR / DIFFÉRENT / NC). Correspondances : octets d'état PSP = octets Upper ÷ 2 ;
  X, Y, vie dans les mêmes unités ; la PSP joue 4 tours pour 3 images (compteur 0x092E51C6) ; boutons LP carré, MP
  triangle, HP L, LK croix, MK rond, HK R. Les 5 normaux d'Eagle contre Ryu sont identiques.
- **Premiers écarts** (221 essais) : les prises de Mika sur Maki se comportent comme sur Ryu (aucun défaut propre à Maki) ;
  Eagle prend 1 point de plus sur PSP (Flying / Shooting Peach, Rainbow Hip Rush) ; HK debout de Yun : 2 touches sur PSP,
  1 dans Upper ; demi-tour arrière + pied : Yun se téléporte de +153 px en 1 tour dans Upper ; contre QCB+P d'Ingrid :
  victime lancée droit en l'air sur PSP, au sol dans Upper ; contre QCB+K : Upper reste ~100 tours en pose.
- **Piège** : deux PPSSPP qui partagent le même dossier memstick se bloquent (débogueur muet) → un dossier par processus.
- **Crochets MAX=1** (`tools/integration-max/upper/`, MAX1.md) : instantané d'`integre_max.py`, `agrandit_max.py`,
  `max_cache.py`, du diff de `mame_test.py` et des scripts de construction ; traducteur MAX à jour dans
  `tools/integration-max/conversion/`. La fusion dans `src/hsfa/` attend que les défauts MAX soient stables.
- **Greffe Arcade** (`patches/traducteur/greffe-arcade-v151.patch`, `tools/greffe-arcade/ETAPES-4-7.md`, entrée `ro9a`
  de `paquet_fbneo.py`) : en pause ; le balayage sur la base v151 régresse (fins 04, 09, 03).

### 176. Lot MAX 2b23 : plantages $A08, contres ratés, persos MAX en CPU

- **Plantages $A08** : la réaction 36 aiguillait avec `$55 = $10`, hors des 8 entrées de `$503A0` (contre QCB+P d'Ingrid,
  croisé Ingrid / Akuma) → `$55 = 8`. Super MP d'Ingrid : le niveau de super `$248` (PSP) est tenu ×2 par l'arcade et
  Upper (`$249` image, lu par `$316C6`) ; corrigé à la source (champ ajouté aux ETATS de la traduction).
- **Contres MAX ratés** : `COUP_NORMAL` était figé à l'adresse v149 (`$23A3C`, devenue un tirage aléatoire en v151) ; le
  vrai coup normal v151 est `$3FBE`, appelé par le dispatcher des contres `$3FA4`. `prepare_max` relève maintenant ces
  adresses natives dans l'image, avec assertion (`CONTRE_DECLENCHE` = `$8BAC(A5)` aussi). **Règle** : aucune adresse
  native figée dans les sources MAX sans relève.
- **Persos MAX en adversaires CPU** : l'IA native (`$DCD4` → `$F5DC` → rappel par perso → `BSR $ED48`) garde son
  pointeur de script en A0 ; les rappels PSP l'écrasaient → enveloppe qui sauve A0. L'IA PSP est un interpréteur à part
  (0x732C0, 149 opcodes) avec des données par perso : non portée, les MAX CPU jouent les scripts natifs.
- **Banc MAX max23** (REFS v151) : natifs identiques sauf Rolento X, fins 35/35, croisés 64/64, Arcade MAX 4/4 avec des
  MAX en CPU, 0 défaut. 8 à 10 MAME en parallèle : environ 1 h 40 au lieu de 4 h.
- **Contrôles CFC2** (bugs corrigés par Capcom en septembre 2025) : le Skull Diver de Bison touche les 4 MAX ; il rate
  Sakura déjà dans Upper v151 sans MAX (défaut natif, à traiter côté traducteur). La Sardine's Beach saisit les 4 MAX.
- **Ouvert** : super d'Ingrid (dégâts, flammes, étincelles), lancer vertical du contre QCB+P (9ᵉ variante de `$503A0`),
  onde et demi-tour + K de Yun (spécial reconnu par la table des manips au lieu du rappel +0x40), Eagle +1 dégât sous Mika.

### 177. Lot MAX 2b24 (en pause) : Yun, Ingrid, Eagle, IA et dialogues des MAX ; release publique v0.1

- **Yun** : l'onde du Kobokushi n'attaque pas sur PSP (tir de sous-type 2 qui annule les projectiles) ; les boîtes des
  tirs étaient échangées par `tir()` → dégâts 16 / 18 comme la PSP, plus de touche à 128 px. Demi-tour arrière + K
  (Zenpou-tenshin, saisie par la fiche 47) : le retour de `$1BD5C` est un pointeur (A3), pas D0 → plus de téléportation.
- **Ingrid** : supers LP 24 / MP 36 / HP 48 comme la PSP (dégâts et feu portés par l'orbe `pshl22`) ; lancer vertical
  du contre QCB+P par prolongement des tables T1-T3 (sans crochet dans `$503A0`) ; contres exacts (`atemi_disable`).
- **Eagle sous Mika** : la défense par victime était masquée par `& $1F` (ids ≥ $20) → plus d'écart.
- **IA des MAX** : l'interpréteur IA de la PSP est celui de l'arcade (version Upper) → scripts PSP convertis au format
  d'Upper ; la condition 40 (aléa ajouté par la PSP) est ajoutée (crochets `$DEE6`, `$F944`). Dialogues Arcade des MAX
  ajoutés (tables de répliques et de scénarios agrandies).
- **Banc** (max32, partiel) : natifs identiques, fins 35/35, croisés 46/64 OK à l'arrêt ; reste croisés, Arcade MAX, zip.
- **Méthode Capcom** (`docs/rapports/recherche/G-METHODE-CAPCOM-MAX.md`) : noms CvS2 / CFE des fonctions des 4 MAX ;
  chaque défaut se lit d'abord dans la donnée que désigne la phase Capcom (fiche, tir), avant le code.
- **Release publique v0.1** : dépôt neuf https://github.com/Rickow/HSFA (SFA3 / Upper / Hyper depuis l'ISO, cœurs,
  patcheurs PS2) ; ce dépôt-ci reste le dépôt de travail. v0.2 : table du rejeu d'Hyper recréée depuis l'ISO.
