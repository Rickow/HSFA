# Passe de conversion du code MAX : disposition ARCADE SFA3 → image traduite d'UPPER (ro5)

Session « conversion MAX », 2026-10-07 puis 2026-10-10 (reprise). Tout est dans `<workspace>/work/agent_conv_max/`.
Sources MAX lues en lecture seule : `sfa3max-psp-widescreen/work/re/rosette_code/` (état du 07/10 14:49, `commandes_voix_max.s`
du 07/10 15:19 : les corrections annoncées sont bien là — plus de `$7788(A5)`, plus d'accès mot/long en `$101`, plus de
copie `$82.L → $3D4`, type PSP des projectiles déplacé de `$22` à `$FF`). Pas de MAME.

## 0. En bref

**État au 2026-10-10 19 h (acteurs de fin terminés côté MAX, §8 ; blocs externes avec animations, §9).** Les
chiffres des §3-§5 sont ceux du 07/10.

- **`convertit_max.py`** : 9 fichiers de code (dont `acteurs_fins_max.s` et `acteurs_fins_main.s`), 7 de données.
  - Code : **8 442 réécrites**, **1 598 inchangées**, **0 NON RÉSOLUE**, 100 AVERTISSEMENTS (dont 18 « `$AA630` modifiée
    par Upper »).
  - Adresses du moteur : **121 résolues, 0 non résolue** ; contrôle carte ↔ image 121/121.
- **Assemblage du code** : vasm **0 erreur** (133 650 o ; 544 avertissements « bra hors portée → jmp », déjà là).
- **Blocs externes** (`convertit_frames.py`, §9) : `ext_d40000.bin` … `ext_e00000.bin` = frames + animations de combat +
  animations de fin, un binaire par bloc de $40000, 0 chevauchement, symboles conformes à `symboles_*_max.s`.
- **Validation contre Upper** : 3 207 comparables, 3 047 identiques, 36 différentes (les 34 du §5 + `$17BE0`, §8.4).
  Acteurs seuls contre le code d'acteurs d'Upper (`--acteurs`) : 300 comparables, 258 identiques, 42 séquences au
  même déplacement, **0 différente**. Pas de 20 o : 119 pas de Ryu consécutifs conformes octet à octet (§9).

Chiffres du 07/10 (avant les acteurs) :

- **`convertit_max.py`** convertit les 7 fichiers de code et les 5 fichiers de données lus par le moteur d'Upper.
  - Code : 6 816 instructions avec accès mémoire typé ou appel au moteur examinées. **5 407 réécrites** (dont 794
    références au moteur), **1 404 vérifiées inchangées** (déplacement et valeur identiques), **5 NON RÉSOLUES**
    (laissées telles quelles et signalées).
  - Données : 2 143 blocs convertis au format PS2 de l'image.
  - Adresses du moteur : 115 résolues, 0 non résolue.
- **Assemblage** : `tout_max_upper.s` s'assemble avec vasm (68000) **sans erreur** (121 736 o). Seuls les symboles
  d'images `F26_n…F29_n` manquent encore, comme dans les sources d'origine (valeurs factices pour l'essai).
- **Validation contre Upper** : 2 870 instructions MAX existent telles quelles dans l'arcade et y sont alignées à
  l'image. **2 761 sont converties exactement comme Upper l'a fait**, 61 séquences ont le même déplacement. Les 34 restantes
  correspondent à 4 formes, toutes expliquées (§5) : ce sont des sites où Upper s'écarte de sa propre règle majoritaire.
- **Contrôle carte ↔ image** : les 115 adresses résolues tombent sur la bonne instruction dans l'image actuelle (115/115).
  L'image a été reconstruite le 07/10 à 15:20 : **les 115 adresses diffèrent toutes de `correspondances.tsv`** (13 h 45).
  C'est pourquoi la passe résout tout par va MIPS à chaque lancement.

## 1. Relancer (après chaque reconstruction d'Upper ou modification des sources MAX)

```
cd <workspace>/work/agent_conv_max && ./relance.sh
```
`relance.sh` enchaîne trois étapes :
1. `convertit_max.py` relit la `carte_image.txt` du moment et les ROM `roms_ro5/sfa3ud`, convertit les sources et
   régénère `sortie/adresses_upper.s`. Ce fichier contient les `UP_xxxxx equ $adresse` et les routines `CONV_A0..A6`,
   trouvées par motif dans l'image.
2. `valide_contre_upper.py` refait la comparaison avec `realign.pkl`.
3. vasm assemble le tout.

Un avertissement s'affiche si la carte et les ROM ont plus de 2 min d'écart (reconstruction en cours).
Options : `--sources`, `--sortie`, `--carte`, `--roms`, `--sans-image`.
**Les sources converties ne s'éditent pas** : corriger la source MAX ou les tables de décision, puis relancer.

Sorties (`sortie/`) :

| fichier | contenu |
|---|---|
| `*.s` | sources converties. Chaque ligne changée porte `; conv : <règle> \| arcade : <original>` |
| `adresses_upper.s` | `UP_xxxxx equ` résolus (va, statut, nom) + adresses CONV_An |
| `tout_max_upper.s` | concaténation prête à assembler (même ordre que `assembler.sh`, `adresses_upper.s` en tête) |
| `journal.tsv` | une ligne par réécriture / inchangé / avertissement / non résolu (fichier, ligne, règle, original, converti) |
| `non_resolus.tsv`, `validation.tsv`, `controle_image.txt`, `stats.json`, `asm.log` | |

Tables de décision (modifiables, dans ce dossier) :
- `types_complement.tsv` : champs mesurés ici, absents du TSV de typage.
- `bases_forcees.tsv` : genre d'un registre à une étiquette ou à `fichier:ligne`, avec sa justification.
- `correspondances_complement.tsv` : 3 adresses du moteur absentes de `correspondances.tsv`.

## 2. Principe et règles appliquées

**Invariant** : les registres contiennent toujours la **valeur logique (arcade)**. Seule la mémoire typée suit la
disposition de l'image :
- une lecture d'un champ dont la disposition diffère est remise en ordre dans le registre ;
- une écriture est remise en disposition image juste avant le stockage.

Toute l'arithmétique sur registres reste donc celle de l'arcade (cas « valeur lue puis manipulée » de TYPAGE §2.1).

**Base de chaque accès.** Un flux de données par fichier (CFG, point fixe) suit le genre de chaque registre :
- objet ;
- A5 ;
- pile ;
- table MAX ;
- pas d'animation ;
- entrée d'attaque ;
- caméra ;
- pointeur PS2 brut ;
- objet + k ;
- constante.

Ce suivi s'appuie sur :
- les chargements (`movea.w $36(a6)` → objet, `movea.l $1c` → pas, `lea LBL` → table, `lea $400(a5)` → joueur…) ;
- les appels :
  - allocateurs `$1C1C8…` : A4 = objet, seuls A0/A4 changent (vérifié au désassemblage) ;
  - `$1BD68` : A3 = caméra ;
  - fonctions MAX « feuilles » : seuls les registres qu'elles écrivent changent ;
  - autres appels : A0-A3 et D0-D7 deviennent inconnus.
- les annotations de `traduire.py` (« pointeur d'objet »), sauf si la valeur est une adresse calculée objet + k.

Une base inconnue n'est **jamais devinée** : l'accès est laissé tel quel et signalé.

| champ (TYPAGE-MAX §2 + compléments) | octet | mot | long |
|---|---|---|---|
| u8 | `d XOR 1` | 2 u8 : même adresse, valeur `ror.w #8` | 4 u8 : même adresse, octets échangés dans chaque mot |
| s16, champ MAX seul (libre) | `d` | `d` | `d` |
| s32 en F | `F + (k XOR 2)` | haut F → F+2, bas F+2 → F | `F`, valeur SWAP |
| pointeur `$1C/$60/$88/$A0` | — | — | SWAP ; lu vers An : `MOVEA.L ; EXG Dk,An ; MOVE SR ; SWAP ; MOVE CCR ; EXG ; JSR CONV_An.w` (idiome de l'image, ex. `$51F6A`) |
| mixte `$AC` | u8 / u8 / s16 | | octets échangés dans le mot haut (MAX ne fait que `tst.l`) |
| A5 | TSV (13 variables, sans relogement) | `$290.W → $292` | `$290.L` = s32 (SWAP), partie entière en `$292` |

Comment chaque instruction est traitée quand la valeur doit être permutée :

| cas | réécriture | drapeaux |
|---|---|---|
| `move #imm,champ` | immédiat permuté (`#$01000420 → #$12004`, `#$ffffa000 → #$a000ffff`, étiquette : `((X>>16)&$ffff)\|((X&$ffff)<<16)` évalué par vasm) | N seul peut différer → si N est lu ensuite : passage par registre |
| `move Dn,champ` / `move champ,Dn` | `SWAP/ROR Dn ; MOVE ; SWAP/ROR Dn` / `MOVE ; SWAP/ROR` | exacts avec SWAP ; `tst` ajouté après `ror.w` si les drapeaux servent |
| copie champ → champ | même disposition : copie brute ; sinon passage par registre | |
| lecture-modification-écriture (`add/sub/addq/neg…` sur s32) | `MOVE.L Dk,-(SP) ; MOVE.L champ,Dk ; SWAP ; OP ; [MOVE SR,-(SP)] ; SWAP ; MOVE.L Dk,champ ; [MOVE (SP)+,CCR] ; MOVEM.L (SP)+,Dk` (= idiome de l'image, `$51F08`, SR gardé si les drapeaux servent) | exacts |
| `andi/ori/eori #imm` | masque permuté | N seul |
| `tst` / `cmpi` | Z seul utilisé : tel quel / immédiat permuté (`cmpi.w #$0200,$4(a6)` → `#$2`, cf. ADRESSES §3) ; sinon lecture par registre | exacts |
| `clr`, `not` | inchangés (invariants) | |

L'utilisation des drapeaux est calculée en avant (branches, Scc, DBcc, X). Un `RTS` est compté comme un lecteur, car les
fonctions MAX renvoient leurs drapeaux. Une passe finale annule les paires `SWAP Dn ; SWAP Dn` suivies d'un MOVE
(76 cas).

**Appels au moteur** :
- arcade → va MIPS (`correspondances.tsv` + complément) → adresse image prise dans la carte du moment ;
- émis sous forme de symbole `UP_xxxxx` (`jsr (UP_2A7EA).l`, `dc.l UP_2D5EA` dans `TAB_MANIPS`).

Les routines **modifiées par Upper** donnent un AVERTISSEMENT dans le journal : `$2AEBC` ×21, `$2E7F2` ×19, `$2ECD8` ×8,
`$2E3FE` ×6, `$2E636` ×5, `$369C`, `$2E8C0`, `$2E4C2`, `$2E3E0`, `$1C206`. Leur détail est dans ADRESSES-MAX-UPPER §2/§7.

Complément d'adresses (`correspondances_complement.tsv`, vérifiées au désassemblage) :
- `$2E646` → va `0x15ebc8` (1re instruction après l'étiquette `0x15eb70`, `TST.B $3F(A6)` = arcade `tst.b $3e`) ;
- `$32A4` → va `0xce9c0` et `$3938` → va `0x139780` : trouvées par les sites d'appel homologues dans `$2A770`
  (arcade `$2A7B4/$2A7D4` ↔ image).

**Données lues par le moteur** (`tables_explicites_*.s`, `donnees_projectiles_max.s`), converties au format de l'image.
Chaque format a été **mesuré dans cette session** en comparant octet à octet des tables arcade et leur copie dans l'image :

| données | format image | mesure |
|---|---|---|
| pas d'animation `P_` (20 o) | octets `$0-$3` et `$8-$13` échangés par mot ; long `$4` (image) SWAP ; pas de reprise (bit 7 de l'octet `$1`) : long `$14` SWAP | Ryu, arcade `$146402` ↔ image `$231BC0` (3 animations) |
| attaques `A_` (32 o, table `$A0`) | mots `$0-$7` natifs, octets `$8-$1F` échangés par mot | Ryu `$10082E` ↔ image (5 entrées) ; cohérent avec l'image (arcade `move.b $e(a3)` → `(A3+$E) XOR 1`) |
| index de boîtes `TABS_` (`$88`, 4 o) | octets échangés par mot | Ryu, Ken, Akuma, Sagat (`$DD092[id]`, 64 o chacun) |
| boîtes `B_` (`$90-$9C`) | mots natifs | Ryu, Ken, Akuma (`$100256` brut en `$1E2FDE`) |
| en-tête `TABP_` (5 mots relatifs) | natifs | ADRESSES §7 (`$3323A`) |
| `TAB_` (listes de pointeurs lues par le code MAX), `donnees_max.s`, `donnees_sauts_max.s` | inchangés (lus seulement par MAX) | TYPAGE §3.4 |

Conséquence pour le code : les accès MAX par `$1C` (pas) ou `$A0` (attaques) suivent ces formats. Par exemple
`move.b 11(a0)` devient `$a(a0)`, et `btst #7,$f(a3)` devient `$e(a3)`.

## 3. Cas signalés par l'analyse : ce qui a été fait

| cas | traitement |
|---|---|
| `$272.B → $273` | appliqué (`btst d1,$273(a6)`, psp_d014c) |
| `$3D4` | La source a changé : écriture longue du n° de joueur, puis relecture de l'octet `$3D7`. MAX est seul à lire ce champ, donc **identité** (`$3D4` libre). La ligne « u8[4] hérité de `$82` » du TSV visait l'ancien code et est ignorée. |
| unions `$20`, `$28-$2E` | s16 (pointeurs mot) chez joueur et objets : inchangés. Aucun accès octet MAX à `$28-$2F` : sinon il serait NON RÉSOLU, faute de type octet. |
| union `$6C.L` | Lu en u8[4] (disposition joueur, parent `$36`) : `move.l $6c(a1),d3` devient lecture + octets échangés par mot ; 10 AVERTISSEMENTS « à confirmer » |
| union `$74` | Écritures de zéro (`psp_raz_alloc`) : invariantes. **`move.l #3,$74(a6)` (Ingrid ×2) : NON RÉSOLU.** |
| `$22` | Plus aucun accès dans les sources. Le type PSP est en `$FF` : mesuré **libre** dans Upper (aucun accès MIPS A0-A6 en hôte `$FC-$FF`), donc identité. |
| accès impairs `$101.W/.L` | Disparus des sources. La passe signalerait tout accès mot/long impair (« erreur d'adresse 68000 »). |
| `$7788(A5)` | Disparu. Les deux sites lisent `$290(A5).L` (Eagle), traité en s32 (SWAP). |
| `$32F` | Plus d'écriture. `psp_66890` saute en `$2E422` → `UP_2E422`. |
| champs absents du TSV | `$2C0.B` (psp_5df68) et `$2CF.B` (psp_66ae8) mesurés u8 (q.py : `$2C0 → $2C1` 8/8, `$2CF → $2CE` 4/4), dans `types_complement.tsv` |

## 4. Les 5 cas NON RÉSOLUS du 07/10 (disparus des sources depuis ; 0 NON RÉSOLU le 10/10 à 19 h)

1. **`brouillon_ingrid.s` l. 2789 et 3113 : `move.l #$3, $74(a6)`.**
   - `$74` est ambigu : s32, u8[4] ou pointeur selon l'objet (TYPAGE §3.1).
   - MAX ne relit jamais `$74`. Seul compte donc ce qu'en lit le moteur d'Upper pour ces objets (PSP 0x94).
   - Ensuite, prendre identité / SWAP (`#$30000`) / octets par mot (`#$300`) et l'écrire dans `types_complement.tsv`.
2. **`brouillon_eagle.s` l. 5197, `brouillon_maki.s` l. 4411, `brouillon_yun.s` l. 5132 : boucle « clr.l » de 72 longs
   à partir de `objet + $350`.**
   - `traduire.py` l'annote « pointeur d'objet », mais `$350` est l'offset **PSP** des fiches de manipulation.
   - En 68K, la boucle efface `$350-$46F` : elle **déborde de la structure joueur** (`$400`) sur le joueur suivant.
   - C'est une erreur de la source, indépendante de la conversion : les fiches arcade sont en `objet + $180..$1E8`
     (cf. `psp_63708`, `lea -$1d0(a4)`). À corriger dans `traduire.py` ou à la main.

## 5. Validation (`valide_contre_upper.py`, `sortie/validation.tsv`)

**Méthode.** Pour chaque instruction MAX présente telle quelle dans la ROM arcade (`arc.pkl`) :
- on cherche ses sites arcade appariés à l'image (`realign.pkl`, 83 709 paires) ;
- on compare la forme majoritaire produite par Upper à la sortie de la passe.

**Résultat** : 2 870 instructions comparables (308 formes distinctes).

| verdict | nombre |
|---|---|
| identiques | 2 761 |
| séquence au même déplacement | 61 |
| séquence non comparable | 14 |
| différentes (4 formes) | 34 |

Les 4 formes différentes :
- **`move.b #1,(a4)` / `$0(a4)` / `$0(a6)`** (3 formes, sites arcade `$337DA`, `$33C1E`, `$274F0`). Upper y écrit l'octet
  image `$0`, alors que le TSV mesure `$0.B → $1` sur 310/315 sites.
  - **Contrôle décisif** : la boucle des projectiles d'Upper (arcade `$32EFA` → image `$1BF42`, va `0xd3948`) teste
    `TST.B $0001(A6)`. La règle `$0.B → $1` est donc la bonne pour les projectiles MAX.
  - Ces 3 sites sont des écarts propres à Upper (la « minorité $0 ×5 » du TSV).
- **`move.l #$20000,$40(a6)`** (1 site, arcade `$4C96E`) : Upper a changé la valeur (`#$fffe` = `−$20000` échangé).
  C'est une modification de jeu, pas une règle de disposition.

**Routine entière** : `psp_cf1b4` (vitesses/accélérations) converti contre le début de l'homologue arcade `$2AA08`
(image va `0x23afa8`). On retrouve la même suite :
`MOVE.L $40(A6),D0 ; SWAP D0 ; MOVE.L D7,-(SP) ; MOVE.L $10(A6),D7 ; SWAP D7 ; ADD.L D0,D7 ; SWAP D7 ; MOVE.L D7,$10(A6) ; (SP)+`.
Seules différences : un SWAP de plus et `MOVEM` pour restaurer D7, qui gardent les drapeaux exacts. Le SR est
sauvé avant le `RTS`.

**Autres preuves :**
- Les immédiats longs SWAP sont mesurés par TYPAGE sur 200+ sites par champ (`$40` : SWAP ×205).
- `cmpi.w #$0200,$4(a6) → #$0002` = ADRESSES §3.
- Les données ont été mesurées octet à octet (§2).

## 6. Points d'attention pour l'intégration

1. **`bases_forcees.tsv`** (13 lignes, toutes justifiées par un commentaire de la source ou par le code appelant) :
   - arguments de table : `psp_cfd9c` / `psp_cfb6c` D0 = table MAX ;
   - `psp_raz_alloc` A4 = objet ;
   - `psp_66ae8` : D0 = victime, D1 = adresse PS2 d'une entrée d'attaque (`$A0 + $20k` chez les 4 appelants). La passe
     y insère un **`JSR CONV_A3`** après `movea.l d1,a3` ;
   - `psp_63708` D0 = fiche ;
   - `psp_78408` A0 = joueur ;
   - `psp_cec94` l. 209 A0 = table.
2. **`psp_66ae8` est fragile.**
   - A2 (victime) sert après `bsr psp_78408`, qui appelle `$32A4` / `$3938`. La source dit elle-même que psp_78408
     « devra préserver A2/A3 ». À vérifier maintenant que les voix sont branchées.
   - Les appelants Eagle font `move.w $38(a6),d0`, puis la fonction fait `movea.l d0,a2` : le mot haut de D0 n'est pas
     garanti. Chez Maki (l. 4091), D0 n'est même pas posé avant l'appel.
3. **Symboles d'images `F26_n…F29_n`** (pas `+4`) :
   - ils sont rangés SWAPés, comme les pointeurs d'image d'Upper ;
   - leur valeur doit être une adresse que le moteur sait lire : une adresse d'image < `$60ACC0` traverse CONV inchangée.
4. **Tout le code et les données MAX** doivent rester sous `$60ACC0` dans l'image (sinon CONV les « convertirait »).
5. **`$FF` libre** et zone `$330-$3FF` : mêmes réserves que TYPAGE §4 (copies / remises à zéro par blocs non mesurées).
6. **Registres de travail** des séquences : surtout D7, empilé et restauré ; D0 pour les `EXG` avant CONV.
   Aucun opérande relatif à la pile n'entre dans ces séquences (sinon : NON RÉSOLU).

## 7. Fichiers

- Scripts : `convertit_max.py` (passe complète), `valide_contre_upper.py` (validation, `--acteurs`), `convertit_frames.py` (blocs externes, §9), `controle_pas_ryu.py` (règle des pas), `relance.sh`.
- Tables : `types_complement.tsv`, `bases_forcees.tsv`, `correspondances_complement.tsv`.
- Sorties : `sortie/`.

## 8. Acteurs de fin (`acteurs_fins_max.s`, `donnees_acteurs_fins.s`, 2026-10-10)

Source : session MAX, `rosette_code/acteurs_fins_max.s` (version de 18 h 06, 104 étiquettes `acteur_`, disposition
ARCADE) et `donnees_acteurs_fins.s` (tables `TABD_` lues seulement par MAX : recopiées telles quelles). Objet = A6 =
acteur du réservoir `$1C2C8` ; A4 = acteur tout juste créé ; A1 = acteur lié (`movea.w $36(a6),a1`).
Résultat pour ce fichier : **879 réécrites, 183 inchangées, 18 AVERTISSEMENTS (`$AA630`), 19 NON RÉSOLUES** (§8.5),
contre 432 NON RÉSOLUES au premier essai.

### 8.1 Registre A4 (164 cas au départ) : correction du suivi de registres

A4 n'était pas « de genre inconnu » : après `jsr $1C2C8` la passe pose bien A4 = objet. Mais les étiquettes de
branchement de `traduire.py` dans ce fichier s'appellent `AL_…`/`AT_…` (et non `L_…`) : elles étaient prises pour des
**entrées de fonction**, où tous les registres repartent inconnus. Correction dans `convertit_max.py` : `LOCALES =
('L_', 'T_', 'AL_', 'AT_')` (une étiquette locale reste une entrée si elle est citée hors branchement). Plus aucun cas
A4 ; aucune déclaration dans `bases_forcees.tsv` n'a été nécessaire.

### 8.2 Carte des champs d'un acteur (base « acteur », `types_complement.tsv`)

Les objets acteurs ne suivent pas forcément la carte joueur. Dans `acteurs_fins_max.s`, la passe emploie donc un
modèle **« acteur »** (`FICHIERS_ACTEURS`, `OCT['acteur']`) : la carte « objet » du TSV, plus les champs propres aux
acteurs ci-dessous. Ces champs ne vont pas dans la carte « objet » des autres fichiers (`$74` y reste une union).

Méthode : `paires_recs.pkl` (agent_typage_max) restreint aux sites arcade du code d'acteurs **`$A5000-$AD000`**
(classes `$48-$50`), plus les accès MIPS ro5 restreints au code d'acteurs (va `0x1DF000-0x221000`, méthode de
`stats_ro5.py`).
- **Champs déjà typés** employés par les acteurs MAX : tous recontrôlés sur le code d'acteurs, même déplacement image
  partout (`$0.L` octets/mot 201 immédiats, `$2→$3`, `$3→$2`, `$4→$5`, `$5→$4` 419, `$B→$A`, `$C→$D`, `$D→$C`,
  `$E→$F`, `$10/$14.W→+2`, `$10/$14/$40/$44/$48/$4C.L` SWAP, `$18`, `$1C` pointeur, `$32-$35` XOR 1, `$36`, `$3A/$3B`
  (66 et 25 sites au même octet), `$3C→$3D`, `$59→$58`, `$5B→$5A`, `$5F→$5E`, `$64`, `$67→$66`, `$6B→$6A`,
  `$70→$71` 62).
- **Ajoutés** :

| champ | type | image | preuve (code d'acteurs) |
|---|---|---|---|
| `$9` | u8 | `$8` | 33/33 sites ; MIPS hôte `$009` octets seuls ; 127 immédiats identiques |
| `$72`, `$74` | s16 | même | 33/33 et 21/21 sites ; MIPS mots |
| `$76` | u8 | `$77` | 1/1 site (`$A759C`) ; MIPS octets seuls |
| `$78-$7F` | u8 ×8 | `d XOR 1` | `$79→$78` 158, `$7A→$7B` 64, `$7E→$7F` 41, … (100 %) ; `$78.W` → `$78` (14) ; `$78.L`/`$7C.L` → même déplacement (12/12, octets échangés par mot) |
| `$5C-$5E`, `$60-$63` | **union selon la classe** : non typés exprès | — | classe `$4B` : `$5C.L`/`$60.L` = pointeurs RAM (`$AA13C` `#$FF3C14` → image `#$3A1000FF` ; relus par `CONV_A1`/`CONV_A0` en `$AA756`), `$5E.W` index ; classe `$49` : `$60-$63` = 4 compteurs u8 ; classe `$4F` : aucun accès |

`$20/$22` (sauvegarde X/Y de MAX) : accès en mots, s16 → identité (comme « libre »). Pas de changement.

### 8.3 Variables A5 (`types_complement.tsv`, base « A5 » ; perm. : `s32` long = SWAP, `u8[2]` = octets inversés)

**Bloc des variables de fin décalé de +2 dans Upper** (mesuré, pas seulement `$1C8 → $1CA`) :

| arcade | type | image (brut) | preuve |
|---|---|---|---|
| `$1C6.B` n° de fin | u8 | `$1C9` | 3 sites (`$25E9A` → `MOVE.B $1C9(A5)`) ; MIPS hôte `$1C8` octets |
| `$1C7.B` | u8 (déduit) | `$1C8` | jamais accédé (arcade ni Upper) |
| `$1C8.W` repère | s16 | `$1CA` | 59 sites (x3 `$27338` → `$2F78`) ; MIPS hôte `$1CA` mots ×300 |
| `$1C8.B` / `$1C9.B` | octets du s16 | `$1CA` / `$1CB` | déduits |
| `$1CA.B` événement | u8 | `$1CD` | 2 sites (`$25E22`, `$2736A`) ; MIPS hôte `$1CC` octets |
| `$1CA.W` | u8[2] (déduit) | `$1CC`, octets inversés | l'arcade ne lit `$1CA` qu'en octet |
| `$1CC.W` | s16 | `$1CE` | 1 site + MIPS hôte `$1CE` mots |

Plans : ombres `$22-$2C.W` s16 identité (12-22 sites chacune) ; accumulateurs `$210/$214/$290/$294/$310/$314` s32 16.16
(mot haut → +2, 2 à 18 sites ; `$312.W → $310` 4 sites ; long = SWAP). Scène demandée : zone relogée de `-$2E9E` :
`-$50FA/-$50F8/-$50F6.W` → `-$7F98/-$7F96/-$7F94` (2 sites chacun), `-$5107.B` → `-$7FA6` (4 sites, brut `$805A`).
`$6EB9.B` → `$6EB8` (36 sites). `$2ECA`, `$3362`, `$32BB` : **inconnus** (§8.5).

### 8.4 Appels au moteur (`correspondances_complement.tsv`, 5 ajouts, méthode d'ADRESSES-MAX-UPPER)

Homologue = cible des sites d'appel arcade alignés (étiquette MIPS « fichier XXXX ») puis 1re instruction dans
`carte_image.txt` ; corps comparé :

| arcade | va MIPS | statut | remarque |
|---|---|---|---|
| `$1B0C4` | `0xc5790` | identique | intégration des vitesses (8 instr. + RTS, comparées) |
| `$1B4EC` | `0xc67c4` | identique | liste d'affichage (`MOVE.B #1,(A6)` = `$1` arcade) |
| `$1B692` | `0xc8184` | identique | avance d'animation (ancre de realign) |
| `$82F20` | `0x176f80` | identique | création de 3 objets enfants (corps entier comparé) |
| `$AA630` | `0x20e444` | **modifiée par Upper** | préambule ajouté : `TST.B $2(A6)` (= sous-type `$3`) ; bit 7 → table d'animations globale `$C0BC(A5)`, `$1A = $8000` ; sinon corps arcade (va `0x20e48c`). Sous-types MAX < `$80` : chemin arcade. 18 AVERTISSEMENTS |

Candidats relevés mais **non ajoutés** (pas appelés par la source actuelle ; début du corps seulement comparé) :
`$AA5D2` → `0x20e1f0`, `$AA756` → `0x20e9a0` (⚠ 6e instr. : arcade `$0(A6)`, Upper `$1C(A6)`), `$AAB44` → `0x210908`,
`$A888E` → `0x1fbabc`, `$A997C` → `0x206590` (⚠ `$0(A6)` / `$48(A6)`), `$A7196` → `0x1eea18`, `$A71CC` → `0x1eec48`,
`$A7202` → `0x1eee94`, `$A723C` → `0x1ef134`, `$AA83C` → `0x20eef0` (étiquette `0x20eee0` ; l'autre cible alignée,
`0x20e530`, est un faux appariement).

Validation (`valide_contre_upper.py --acteurs`, sortie `validation_acteurs.tsv`) : sites arcade restreints au code
d'acteurs → 297 comparables, 258 identiques, 39 séquences au même déplacement (lectures s32 + SWAP, pointeur `$1C` +
CONV), **0 différente**. En validation globale, 1 forme de plus diffère : `move.b #4,$3a(a6)` (1 seul site, `$17BE0`,
code de plans : Upper y écrit `$3B`), alors que les 66 sites d'acteurs gardent `$3A`.

### 8.5 Les 19 NON RÉSOLUES du premier passage = erreurs de la source MAX — **toutes corrigées par la session MAX (19 h)**

Version de 18 h 40 : plus aucune des lignes ci-dessous (ni `$2ECA/$3362/$32BB`, ni mot impair, ni lecture octet de
`$1C8`) ; `psp_1d96c/psp_1da64` passent maintenant par `$1B6EE` ; la position privée `$4F/$19` est en `$5C.L/$60.L` (§8.8).
Historique :

1. **`$2ECA(a5)`, `$3362(a5)`, `$32BB(a5)`** (l. 3109-3142, `acteur_1d80b0`, 6 lignes) : jamais accédées par l'arcade
   ni par Upper. Elles viennent de la fenêtre générale `GLOB_A5` de `traduire.py` (PSP `0x80B0C2`, `0x80B55A`,
   `0x80B4B3`), non vérifiée. Comparées à `$29` (= n° d'Ingrid) et à `$7F` : sans doute le n° de perso / de fin
   (`$1C6(A5)` ou `$102` du joueur ?). À établir et remplacer.
2. **`$5C-$5E` / `$60-$63`** (l. 2800-2894, `acteur_1d749c`/`acteur_1d7560`, classe `$4F` sous-type `$19`, 10 lignes) :
   position 16.16 PSP (`$5C += $40`, `$60 += $44`, `$5E.B`/`$62.W` comparés à `$72`/`$74`). Les champs PSP `0x5C/0x60`
   ne sont pas dans la carte `ACTEUR` de `traduire.py` (repli sur la carte joueur). Dans les acteurs arcade, `$5C-$63`
   est une union (pointeurs RAM en classe `$4B`, compteurs en `$49`). Utiliser `$10/$14` si c'est la position, ou
   déclarer un stockage propre (alors : ligne « libre » dans `types_complement.tsv`).
3. **Mots à adresse impaire** : `cmp.w $7b(a6),d0` (l. 2480 et 2921 ; PSP `0x50`, demi-mot, mappé sur l'octet `$7B`) et
   `cmp $3b(a6),d0` (l. 1810, taille par défaut .w) → erreur d'adresse 68000.

Autres points de la source, convertis fidèlement mais suspects :
- `acteur_1d96c` et `acteur_1da64` : `move.l d3,$1c(a6)` écrit un nombre dans le pointeur de pas d'animation ; les
  octets `$1C6-$1C9(A5)` recopiés dans `$32-$35` ; `$1CA.W` comparé à lui-même. Traduction littérale d'un PSP « pose
  l'animation » ? L'équivalent arcade est `$AA630` (D0 = n° d'animation).
- **Lectures octet de variables mot** : `$1C8.B` (l. 646, 658) et `$1C9.B` (l. 2360, 3161) lisent l'octet fort / faible du repère en
  gros-boutiste ; le PSP lisait l'octet faible (`+2` petit-boutiste) → sans doute `$1C9(a5)` voulu. De même
  `move.w $1ca(a5)` lit l'événement (octet) et l'octet `$1CB` : `move.b $1ca(a5)` voulu ?

### 8.6 Effacement des fiches (`moteur_max_main.s`, `psp_1b9544`) — résolu

**19 h** : la source efface `$180-$1CF` et `$1D8-$1EF` (elle épargne `$1D0-$1D7`, champs d'Upper). Règle ajoutée
(`ZONES_RAZ`, `verifie_raz`) : `lea d(a6),An ; moveq #n,Dk ; clr.l (An)+ ; dbra` est laissé tel quel si la boucle reste
dans sa zone ; seule l'écriture de zéros y est admise. Preuve : aucun accès aligné (`paires_recs.pkl`) ni MIPS hôte à
cheval sur `$180/$1D0/$1D8/$1F0` ou déplacé hors de sa zone. `lea $10(a4),a4` sur une fiche (fiche suivante, 16 o) :
admis. Historique (17 h) :

La remise à zéro des fiches vise maintenant `objet + $180..$1EF` (28 longs). Effacer à zéro est invariant si aucun champ
ne franchit les bornes de la zone dans l'image : **vérifié** sur `paires_recs.pkl` (aucun accès aligné de `$180-$1EF`
vers l'extérieur ni l'inverse). Mais Upper a des champs nouveaux en `$1D5/$1D7` (ECARTS, CARTE-ro5) et l'arcade y a
des champs de travail des persos (`$1D0-$1D8`, code `$41xxx-$50xxx`). Pour un perso MAX, ils sont à lui. Si on
l'accepte, il faut une règle « effacement de zone » dans la passe (pas encore écrite).

### 8.7 Changements de la passe

- `convertit_max.py` : `LOCALES` (étiquettes `AL_`/`AT_`) ; modèle d'objet par fichier (`FICHIERS_ACTEURS`,
  `OCT['acteur']`) ; variables A5 du complément (`A5C`, déplacements négatifs `-$xxxx`, permutation selon le type) ;
  remarque des correspondances complémentaires reprise dans les AVERTISSEMENTS.
- `valide_contre_upper.py --acteurs` ; `relance.sh` l'appelle.
- Tables : `types_complement.tsv` (+7 lignes acteur, +33 lignes A5), `correspondances_complement.tsv` (+5).

### 8.8 Compléments du 2026-10-10 19 h (version finale des acteurs)

- Nouveaux fichiers : `acteurs_fins_main.s` (code, modèle « acteur ») et `donnees_fins_t12c.s` (enregistrements de
  32 o lus SEULEMENT par le code MAX : recopiés tels quels).
- **Fonctions MAX à effet déclaré** (`APPELS_MAX`) : `fin_t12c` (seul A0 change, A0 = table MAX), `fin_pas110`,
  `fin_pas118`, `fin_pos_4f05` (seul D7 change), d'après leur en-tête relu.
- **Modèle par classe** : les instructions atteintes UNIQUEMENT depuis les entrées d'une classe (en-tête « classe $4F
  sous-type $19 -> acteur_1d6588 », graphe suite + branchements + tables `dc.l`) prennent le modèle `acteur_4F` (pour A6).
  `acteur_4F` = « acteur » + **`$5C-$67` MAX seul (identité)** : ni la classe `$4F` ($AAE04-$AC15E), ni la classe `$48`,
  ni le générateur ($2750E, MIPS va 0x2A000-0x2A800), ni le moteur générique ($1B000-$1C400 : seul `$1BF68` touche
  `$5D/$5E/$67`, sur les structures JOUEURS) n'y accèdent, ni dans l'arcade ni en MIPS. `$5F` reste u8 (→ `$5E`) pour les
  autres classes (compteur de la classe `$4B`, qui peut venir d'un acteur créé par Upper).
- **Réservoir d'acteurs `$3000(A5)`** : même base dans Upper (`$1C0C0 lea $3000(a5),a6` ↔ image `$1AA6A`), objets de
  `$80` (`lea $80(a0),a0` admis en modèle acteur) ; `+0` actif → `$1`, `+2` classe → `$3`, `+3` sous-type → `$2`
  (`cmpi.w #$4f05,2(a0)` → `#$054f`). Mots `$40-$57` de l'acteur `$4F/05` : même déplacement dans l'image (12 sites
  alignés `$AAFC2-$AB046`) → accès indexé de `fin_pos_4f05` déclaré identité (`bases_forcees.tsv`, étiquette
  `fin_pos_4f05.trouve`).
- `$214/$294/$314.W` (add.w, décalage vertical) → `+2` (partie haute s32, mesuré) ; `-$50F8` → `-$7F96`.
- **`$1B6EE`** (queue de `$1B6E0`) → va `0xc85d0` (image `$19FE4`, `MOVE.L A0,$1C(A6)` puis `MOVE.L (A0),$32(A6)`) ;
  les appels arcade alignés passent par le trampoline `$AFA92`. Ajouté au complément (identique).
- Boîtes `+$114` → `movea.l $1c(a6),a0 ; $9(a0)` : règle du pas, octet u8 XOR 1 → `$8(a0)` (comme `tables_explicites`).
- ⚠ `bases_forcees.tsv` : les clés `moteur_max_main.s:<ligne>` ont été recalées (+11 après l'ajout de `psp_1d96c`) ;
  à revoir à chaque modification de ce fichier (préférer une étiquette).

## 9. Blocs externes : frames + animations de combat + animations de fin (`convertit_frames.py`)

Entrées (session MAX, disposition arcade) : `frames_<p>.s` (org `$D40000/$D80000/$DC0000/$E00000`), `anims_<p>.s`
(+`$20000`) et `fin_anims_<p>.s` (+`$30000`). **Un assemblage vasm par bloc** (`sortie/bloc_XXXXXX.s` → `ext_XXXXXX.bin`,
`$40000` o, de l'org des frames à la fin) : vasm comble les trous de zéros et refuse tout chevauchement ; le script
vérifie la taille, le début du binaire et que **tous les symboles `F2x_n`, `ANIM_2x*`, `FIN_ANIM_2x` assemblés valent
ceux de `symboles_frames_max.s` / `symboles_anims_max.s`** (que le code MAX emploie).

| contenu | règle image | mesure |
|---|---|---|
| frames | mots natifs ; « dc.l » → moitiés échangées | recette §29 (inchangé) |
| `ANIM_xx`, `ANIM_xx_2B4/_2B8/_2BC`, `FIN_ANIM_xx` (mots relatifs) | **mots natifs** | image `$AFA58` = arcade `$1B6E0` : `MOVE.W 0(A0,D0.W),D0 ; ADDA.W D0,A0` ; table `$2B0` de Ryu en image `$2319C0` : mêmes écarts que l'arcade `$146218` |
| `ANIM_xx_PTRS` (12 longs) | longs à moitiés échangées | Ryu, homologue du bloc `$1461E8` en image `$231990` (`B650 0079` = PS2 `$0079B650`) |
| pas `P2x_n`, `FP2x_n` (20 o, reprise en `+$14`) | `permute_bloc('pas')` : octets `$0-$3`/`$8-$13` échangés par mot, frame `+$4` et reprise SWAP | `controle_pas_ryu.py` : 119 pas de Ryu (arcade `$146402`) conformes octet à octet à l'image (`$231BB8`), 1 904 octets hors pointeurs ; arrêt sur une durée modifiée par Upper |

`dcb.b n,v` (pas vides) est développé. Bilan (19 h) : Eagle 1 168 + 111 blocs de pas, Maki 1 162 + 223, Yun 1 505 + 281,
Ingrid 1 087 + 108 ; 12 longs `PTRS` chacun ; 0 NON RÉSOLU (`sortie/journal_blocs.tsv`) ; blocs remplis à 76-77 %.

**Pour l'intégration** (tables d'Upper à étendre, adresses de l'image actuelle) :
- **`T_619b50`** (PS2 `0x619B50`, image `$AFE90`, lue par `$AA630` en va `0x20e500`) : banques d'animations des
  acteurs, **40 longs** (`$00-$27`, moitiés échangées) ; `$28` et suivants sont d'autres données (`0x3FF3A0`…). Pour
  `$26..$29` → `FIN_ANIM_26..29`, il faut une table de **42 entrées** : **déplacer la table** (et la référence
  `T_619b50(PC,D1.W)` de `$AA630`), pas l'écrire sur place. Actuellement `$24-$27` = banque de Ryu par défaut.
- **Homologue de `$DD412`** = **`T_61a100`** (PS2 `0x61A100`, image `$B0440`, lue en va `0x220388`) : **32 longs**
  (`$00-$1F`, Ryu = `$0079B650`), suivis d'une autre table (`$20` : `0x00C00050`…). `$26..$29` → `ANIM_2x_PTRS` exige
  aussi une table déplacée et agrandie (au moins 42 entrées). Arcade : `$DD412` a 32 entrées (`$20` = autres données).
- Les adresses `$D60000…` des blocs sont > `$C3FC50` : elles traversent `CONV_An` inchangées (rangées SWAPées).
