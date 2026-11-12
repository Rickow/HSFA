# Critical review of the translator (v160, 2026-11-11)

**Summary (English).** Static review of the MIPS → 68000 translator v160 in two passes (agents `revue_traducteur`,
`revue_traducteur_2`), proven by reading the MIPS, the translated image and the arcade; the switch audit (E8) was done by
rebuilding (no emulator). Workshop: `<workspace>/work/revue_traducteur/`.
- **Findings**: A1 byte at fixed XOR 1 through an odd An (initials entry, custom combo freeze, P2 guard, scrolling
  text); A2 A8 accessed outside a borrowed zone = nothing emitted (MAZI ×1.5 damage bonus never applied); A3a-d lost
  comparisons (±1 px hit shake, table entry at fight 9, object waiting for state 6, "not twice the same" draw); E5 combo
  score bonus never added (ABCD between registers → empty helper); E7 P2 colour in a mirror match (Upper, Hyper);
  E7 bis Upper's type-121 object (two `CMP.W D0,$12(A6)` lost).
- **Fixed in translator v161 (journal §219)**: `A8_ENTREE`, `TST_C`, `TST_ZX`, `CMP_MEMADD` (plus `$0803A0`, missed by the
  review), `CMP_IDX`, `CMP_D8`, `CMP_MEMDN`, `PARITE_FLOT` / `PARITE_SITES`, `BCD_REG`, `AIDE_SBCD`; build guards in
  `build.log` (A8 without register, comparisons without a 68K form and helpers not inlined = build failure, Bcc on a
  callee's flags). Upper MAX follows v161 in §220, the graft (ro9a37) in §221; ro9a38 keeps v161 (§223).
- **Still open**: B1 `Scc` rendered with flag-setting `MOVE` / `CLR` (latent); B2 `ADDI` for `SUBI` (C / X inverted, no
  consumer found); B3 "native result assumed zero" has no switch; B4 rules without switch and textual markers re-read by
  `assemble.py`; E1 byte accesses of undecidable parity (needs a runtime probe); E2 unlisted C functions run as
  fragments (no effect found); E6 restart request `$F009C0` never served (check at image `$006F80`); E7 type-121 object
  not identified. E8 dead or broken switches: marked historical in [pieges §10](../../methodes/pieges-du-traducteur.md).
- **Tools kept**: [`tools/reviews/translator/`](../../../tools/reviews/translator/) (guards, audits, switch audit);
  on v161: 0 Bcc after a call and every helper inlined in the three games.

---

## Original text (French, kept as is)

> Kept as written in the workshop. Only changes: personal paths written `<workspace>/...`, workshop folders written `<workspace>/work/...`. Paths such as `outils/…`, `sorties/…`, `essais_demain/…`, `constr/…` are relative to the review's workshop folder (above); the tools kept are in `tools/reviews/` (see the summary).

# Revue critique du traducteur MIPS → 68000 (v160)

Agent `revue_traducteur`, 2026-11-11. Lecture et analyse statique seulement : rien n'est modifié dans le dépôt ni dans
`scripts/`. Aucun émulateur lancé : chaque constat « prouvé » l'est par lecture du MIPS, de l'image traduite et de
l'arcade ; l'effet en jeu reste à confirmer au banc (essai décrit à chaque fois).

Matière :
- modules `anthology_extract/decompressed/ro{3,5,9}_usa_prog68k.bin` (les adresses « mips » ci-dessous sont des
  **décalages dans le fichier** ; adresse d'exécution = + `0x1F0000`) ;
- images traduites v160 : `<workspace>/work/v160/constr/ro{3,5,9}_a/carte_image.txt` (adresses « image ») ;
- arcade : `<workspace>/work/cps2/sfa3ud_prog.bin` ;
- traducteur : `<workspace>/github/src/hsfa/translate.py` (= `<workspace>/scripts/untranspile/translate.py` aux 4 lignes de chemins anonymisés
  près ; les autres fichiers du dossier divergent de la même façon, par les chemins ; 9 fichiers n'existent que dans le dépôt).

Outils écrits : `outils/` (usage en tête de chaque script, liste dans `ETAT.md`). Sorties : `sorties/`.

Repère de lecture des adresses d'octets : l'image garde la disposition PS2 ; l'octet PS2 d'adresse X est à X XOR 1
dans l'image. Les déplacements cités sont ceux de l'image, sauf mention « arcade ».

## En bref : les constats les plus graves

1. **A3a (SFA3)** : le test `CMPI.B #0,$8(A6)` de la routine d'affichage est perdu : le tremblement de ±1 px d'un perso
   touché n'est presque jamais appliqué (arcade `$021BB8`, mips `0x107378`). Upper et Hyper sont justes.
2. **A2a (les trois jeux)** : accès à A8 hors zone = rien d'émis : le bonus de dégâts ×1,5 lié à `$EC` (mode à dégâts
   majorés) n'est jamais appliqué (arcade `$024152`). Deux autres pertes du même mécanisme dans Hyper.
3. **A1 (les trois jeux)** : octet par An impair lu ou écrit à la mauvaise adresse ; 7 routines prouvées (saisie des
   initiales, gel de coup en custom combo, garde de création d'objets de J2, texte défilant…), et une famille de
   plusieurs centaines d'accès dont la parité n'est pas décidable sans sonde.
4. **A3b, A3c, A3d (SFA3)** : trois autres comparaisons perdues (choix d'une entrée de table au combat 9 pour tous les
   persos ; attente d'un objet à l'état 6 jamais satisfaite ; tirage au hasard sans « pas deux fois le même »).
5. **B4** : `enc_cmp` qui rend `None` sans compteur, et l'absence de repli pour A8, sont des pertes silencieuses par
   construction ; `outils/drapeaux.py` et `outils/a8_hors_zone.py` peuvent servir de garde-fous après chaque construction.

Tout est prouvé par lecture (MIPS, image, arcade) ; aucun essai au banc n'a été fait.

---

## A. Constats prouvés (lecture statique)

### A1. Octet `d16(An)` à XOR 1 fixe alors que An est impair

- **Règle** : `translate.py:1436` `mconv` rend `déplacement XOR 1` pour tout accès octet, ce qui suppose An PAIR.
  L'adresse exacte à l'exécution n'est calculée que dans quatre formes : index (`byte_index_exact`, l. 946), flux
  `(An)+` collé à l'accès (`byte_streams`, `byte_streams_ea`, l. 819 et 850), flux `-(An)` (`byte_streams_pre`, l. 916),
  et « après `ADDA Dk,An` » (`byte_after_adda`, l. 984).
- **Défaut de `byte_after_adda`** (l. 1004) : l'état « An de parité inconnue » est EFFACÉ à chaque `RTS`, `JMP`, `JSR`
  et `BRA` rencontré dans l'ordre d'émission (« rupture → tout propre »). Or après un `BRA`, le code suivant est
  atteint par un branchement, avec le même An. L'oubli rend « pair » un registre qui ne l'est pas : le défaut sûr
  serait l'inverse (inconnu tant que rien ne prouve la parité).
- **Mesure** (`outils/parite_origine.py`, `sorties/parite_origine_ro*.txt`) : accès octet à XOR 1 fixe par A0-A4 :
  ro3 4 714, ro5 4 976, ro9 4 820. Origine linéaire de An : pointeur d'objet 16 bits (`MOVEA.W`, pair) 63 % ;
  `LEA pair(A5/A6)` 11 % ; **après ADDA hors règle : 72 / 72 / 48** ; **pointeur de données `MOVEA.L` : 239 / 230 /
  194** ; inconnue (argument, MOVEM, prêt) 17 à 24 %. La parité n'est décidable statiquement que pour 1 à 4 % des
  accès : la famille complète demande une sonde à l'exécution (essai en fin de constat).

Sites sûrs (An impair démontré par le code lui-même) :

| # | routine | arcade | SFA3 mips (image) | Upper / Hyper | ce qui est faux |
|---|---|---|---|---|---|
| a | saisie des initiales (curseur 0-3) | `$0087E6`-`$00889C` | `0x887b0`-`0x88e30` (`$010632`-`$0106C2`), 15 accès `x.B $0001(A1)` | Upper : même routine, mips `0x95a28` et suite (image `$0112C0`) ; absente d'Hyper | A1 = `$168(A6)` + curseur. Seul le 1er accès après l'`ADDA.W D1,A1` (`$0105EC`) est exact ; après le `BRA` de `$01062E` tous les autres sont fixes. Curseur 1 : les opérations sur la 2e lettre touchent l'octet de la 4e ; curseur 3 : elles écrivent 2 octets après le nom (champ `$16C/$16D` de l'objet). |
| b | plafond des initiales à `$2D` | `$0088A6` | `0x88fa8` (`$0106F8`) | Upper `0x96878` (`$0113E2`) | `CMPI.B #$2E,(A0)+ ; BCS ; MOVE.B #$2D,-1(A0)` : l'écriture est rendue `$fffe(A0)` ; aux tours 1 et 3 A0 est impair → `$2D` écrit dans `$167(A6)` (hors du nom) puis dans la 1re lettre. |
| c | gel de coup de la victime (table `$25328`) quand `$28D(A1)` ≠ 0 (coup reçu en custom combo) ou `$26E(A1)` ≠ 0 | `$023D52`, `$023D98` | `0x380a8` (`$004890`), `0x38480` (`$0048F0`) | Upper `0x3c418` (`$004C5A`), `0x3c7f0` (`$004CBA`) ; Hyper `0x4d858` (`$006FB6`), `0x4dc30` (`$007016`) | `MOVE.B (A0)+,D0 … MOVE.B (A0),D0` : le 2e accès lit 2 octets plus loin. La table a 4 octets identiques par entrée : sans effet quand la base est `$25328`, mais avec la base +2 (`$55(A1)` < 0) le gel de la victime vient de l'entrée SUIVANTE (n+1 au lieu de n : 1 image d'écart après division par 2 quand n est impair, ou quand n ≥ `$10`). |
| d | garde « 2 places libres » avant de créer les 2 objets `$1700/$1701` | `$07955C` | `0xa6734` (`$015758`) | Upper `0xe50e4` (`$01EBFA`), Hyper `0x303644` (`$0762FC`) | `LEA $6EB6(A5),A0 ; si J2 : LEA $6EB7(A5),A0 ; CMPI.B #2,(A0)`. Pour J2, l'image lit `$6EB8` (compteur de la 3e réserve, `$20` places) au lieu du compteur de J2. Si la réserve de J2 a moins de 2 places, l'allocateur `$01C1C8` rend la main sans poser A4 et la routine écrit dans l'objet désigné par l'ancien A4. |
| e | texte défilant ligne par ligne (fin de ligne `$7F`, fin de texte 0) | `$0B2F9C`, `$0B2FC6` | `0xd73f4` (`$01CF84`), `0xd7604` (`$01CFF4`) | Upper `0x119c40` (`$0267B0`), `0x119f10` (`$026820`) ; Hyper `0x3be380` (`$093FBC`), `0x3be650` (`$09402C`) | `MOVEA.L $54(A6),A0 ; TST.B (A0) ; BEQ ; boucle CMP.B (A0)+,D0 ; MOVE.L A0,$54(A6)` : le pointeur rangé est impair une ligne sur deux ; le `TST.B` (fixe) teste alors l'octet 2 positions plus loin : la fin de texte n'est pas vue, la boucle cherche un `$7F` au-delà. |
| f | pointeur impair rangé puis relu | `$080266` → `$0B171C` | `0x127c38` (`$028F02`) → `0x619f8` (`$00B60A`) | Upper `0x16e168` → `0x6935c` (`$00BD86`) ; Hyper `0x323448` → `0x6e2fc` (`$00B34E`) | `LEA $6B(A0),A0 ; MOVE.L A0,$40(A4)` puis, dans l'objet créé, `MOVEA.L $40(A6),A0 ; TST.B (A0)` rendu `TST.B $0001(A0)` : lit l'octet `+$6C` du parent au lieu de celui que lit la PS2 (`+$6A` en image). Condition de libération de l'objet d'effet `$1200`. |
| g | boucle de 13 octets sur deux tableaux `$60(A6)` et `$70(A6)` (comparaison quartet par quartet) | `$0AF2B6`-`$0AF2F6` | `0xc5864`, `0xc58b4` (`$01A888`, `$01A896`) | Upper `0x106418`, `0x106468` (`$023FB2`, `$023FC0`) ; pas vue dans Hyper | `MOVE.B (A0),D0 … MOVE.B (A1),D1 … MOVE.B D0,(A0)+ ; MOVE.B D1,(A1)+ ; DBRA` : les deux lectures sont fixes, les deux écritures exactes. Aux tours impairs (A0, A1 impairs) la lecture prend l'octet 2 positions plus loin que celui qui est réécrit. |

Candidats de la même famille, parité non prouvée (à trancher par la sonde) : copie de 20 champs depuis
`A0 = $359620 + mot de table` (ro3 `0x59fb4`-`0x5a170`, image `$00A6EE` ; ro5 `0x60b74` ; ro9 `0x646c4`) ; les 72 / 72 / 48
accès « après ADDA hors règle » (`sorties/parite_adda_ro*.txt`) et les 239 / 230 / 194 accès par un pointeur
`MOVEA.L` (`sorties/parite_moveal_ro*.txt`).

- **Preuve type (site a)** : MIPS `0x88a40` `lw v1,A1 ; lb v1,0(v1) ; addiu a0,v1,-1 ; lw v1,A1 ; sb a0,0(v1)` → image
  `$01067C SUBQ.B #1,$0001(A1)`. A1 = `$168(A6) + D1` (`$0105D6 LEA ; $0105E0 ADDA.W D1,A1`), D1 = `$16E(A6)` = 0..3.
  Octet PS2 visé : A1 ; octet image correct : A1 XOR 1 ; octet émis : A1 + 1, juste seulement si A1 est pair.
- **Effet possible** : (a, b) saisie du nom au classement de SFA3 et d'Upper : 2e et 4e lettres ; (c) une image de gel
  d'écart sur un coup de custom combo ; (d) corruption d'objet rare (réserve de J2 pleine) ; (e) texte défilant qui
  déborde ; (f) durée de vie d'un objet d'effet.
- **Essais** : (a) banc : aller à la saisie des initiales, curseur sur la 2e lettre, haut / bas, comparer
  `$FF8x68-$6F` de l'objet à l'arcade image par image. (c) banc des coups : coup de custom combo sur victime avec
  `$55` < 0, comparer `$5F(A1)` au tour du coup. **Sonde générale** : dans le cœur ou sous MAME, journaliser le PC de
  toute instruction octet à EA `(An)` / `d16(An)` (n ≤ 4) exécutée avec An impair, hors des séquences « adresse XOR 1 à
  l'exécution » ; une tournée + les balayages donnent la liste réelle des sites.
- **Correctif de principe** : inverser le défaut. Un accès octet par An n'utilise le XOR fixe que si la parité de An est
  PROUVÉE (An issu de `MOVEA.W`, de `LEA pair(A5/A6/A7)`, ou d'une adresse constante paire, sans `ADDQ`/flux impair
  depuis) ; sinon forme exacte (`An XOR 1` à l'exécution), y compris après un branchement. Coût : ~10 à 25 % des
  accès octet par A0-A4 passent en forme longue ; à mesurer au test des commandes.

### A2. Accès à A8 hors d'une zone prêtée : aucune instruction émise

- **Règle** : `translate.py:19` `slot_name` ne connaît la case `0x1120` (A8) que si elle est dans `ACTIVE_EXTRA`
  (zone ouverte). `translate.py:2344` donne un repli mémoire à D8 hors zone (`D8_HOME`), **rien pour A8** : hors zone,
  les `sw … A8`, les lectures par A8 et les tests qui en dépendent ne produisent rien, sans message. Les zones sont
  refusées ou coupées par `extra_regs.plan` (appel pendant la durée de vie, plusieurs entrées / sorties, pas de
  registre libre ; A8 est en plus coupée à chaque appel, l. 131-143).
- **Mesure** (`outils/a8_hors_zone.py`, `sorties/a8_hors_zone_ro*.txt`) : accès à A8 hors de toute zone :
  ro3 50, ro5 15, ro9 21. Dans le code de jeu (hors zone des aides du portage) :

| # | module, mips (image) | MIPS | image traduite | effet |
|---|---|---|---|---|
| a | ro3 `0x3a858`-`0x3a8dc` (`$004D98`-`$004D9C`) ; ro5 `0x3f20c`-`0x3f290` (`$005164`) ; ro9 `0x52118`-`0x5219c` (`$0077B2`) | `jalr 0x571b50` (= `BTST #3,$C173(A5)`) ; `bne L` ; `A8 = MOVEA.W $8B94(A5)` ; `L: TST.B $EC(A8)` ; `beq` ; `D2 += D2/2` | `JSR ; BNE ; BEQ` : le `MOVEA.W` et le `TST.B` manquent ; le `BEQ` relit le Z du `BTST` | routine de dégâts, arcade `$024152` `TST.B $EC(A6) ; BEQ ; MOVE.B D2,D0 ; LSR.B #1,D0 ; ADD.B D0,D2`. `$EC` ← `$15A` à l'initialisation (`$027BD2`) ; c'est le drapeau qui donne aussi −`$18` de défense en `$024276` (mode secret à dégâts majorés, très probablement Mazi). Dans l'image, le bonus ×1,5 de l'attaquant n'est JAMAIS appliqué quand le bit 3 de `$C173(A5)` vaut 0 (cas normal), et TOUJOURS s'il vaut 1. |
| b | ro9 `0x438ec`-`0x4390c` (`$005BCA`-`$005C00`) | `A8 = A1 + $280` ; `CLR.B (A8,D8.W)` avec D8 = `$5A(A6)` | rien entre l'ouverture et la fermeture de la zone D8 | Hyper : une case de la table `$280(A1)` n'est jamais remise à 0 (rôle de la table à identifier). |
| c | ro9 `0x36fe80`-`0x370098` (`$0882E2`-`$088308`) | `A0 = T1, A8 = T2` (deux fois, selon `BTST`) ; `CMPI.B #2,$116(A4)` ; `beq` ; `EXG A0,A8` ; appel `0x57d3b0` (pose l'animation `$1C(A6)` depuis A0) | les deux `A8 = …` et l'`EXG` manquent | Hyper : quand le perso de base (`$116`) n'est pas 2, l'objet devrait prendre l'animation de la table A8 (PS2 `0x8DFEBC` / `0x8E9C88`) ; il prend toujours celle de A0 (`0x90B036` / `0x916C1A`). |

- **Essais** : (a) banc SFA3 avec le mode à dégâts majorés actif pour J1 (`$EC` de l'attaquant ≠ 0), un coup fixe :
  comparer la vie retirée à l'arcade (attendu arcade : ×1,5). (c) Hyper : repérer l'objet (point d'arrêt image
  `$0882DA`), comparer `$1C(A6)` au vidage PS2.
- **Correctif de principe** : donner à A8 le même repli que D8 (lecture / écriture du domicile `$87E0(A5)` par un
  registre d'adresse de travail sauvé), et faire échouer la construction (ou au moins compter et lister) quand un accès
  à `0x1120` / `0x1144` ne produit rien. `outils/a8_hors_zone.py` sert de contrôle.

### A3. Comparaisons perdues : le branchement relit des drapeaux périmés

Trouvées par `outils/drapeaux.py` (classes `PERDU`, `APPEL-sans-jal`, `TAILLE x lu y`). Toutes dans **SFA3 (ro3)**,
recompilateur ancien ; Upper et Hyper ont les mêmes routines correctes (forme « drapeaux exacts »).

| # | mips (image) | MIPS | image | arcade | effet |
|---|---|---|---|---|---|
| a | `0x107378`-`0x107400` (`$024674`-`$02467A`) et `0x107580`-`0x107608` (`$0246A0`-`$0246A6`) | `MOVE.W $10(A6),D4` ; `RES = octet 8(A6)`, `C = sltu` ; `bltz C` ; `bne RES` | `MOVE.W $0012(A6),D4 ; BCS ; BNE` : le `CMPI.B #0,$9(A6)` manque | `$021BB4` `move.w $10(a6),d4 ; cmpi.b #0,$8(a6) ; bhi ; add.w $d4(a6),d4` (et `$021BE4`) | calcul de la position X d'affichage d'un objet : `$D4(A6)` = ±1 px de tremblement tant que `$27B(A6)` > 0 (`$027DCC`-`$027DE6`). Dans l'image le `BNE` suit le Z de `MOVE.W X` : le tremblement n'est ajouté que si X = 0, donc presque jamais. Upper (`$02D884`) et Hyper (`$08F23C`) ont le `CMPI.B #$0,$0009(A6)`. |
| b | `0xf5c54`-`0xf5cdc` (`$022138`-`$02213A`) | `CMPI.W #9,$114(A5) ; bne` ; `RES = D0.b` ; `bne` | `CMPI.W #$9,$0114(A5) ; BNE ; BNE` : le `CMPI.B #0,D0` manque | `$003A74` `cmpi.w #9,$114(a5) ; bne ; cmpi.b #0,d0 ; bne ; moveq #$22,d0` | choix d'une entrée de la table `$3ABA` (indexée par l'id du perso, cas spéciaux `$20`-`$24`, puis `bra $38D8`) : au combat 9, l'entrée `$22` est prise pour TOUS les persos au lieu du seul id 0 (hors Bison final, traité avant). Probablement la musique du combat. |
| c | `0x31b980`-`0x31ba24` (`$07EACE`-`$07EAD2`) | `MOVEA.W $A4(A6),A4` ; `RES = long 4(A4) − 6` ; `bne` | `MOVEA.W $00a4(A6),A4 ; BNE` : le `CMPI.L` manque, le `BNE` relit le `TST.W $A4(A6)` (≠ 0 sur ce chemin) → toujours pris | `$065EEA` `movea.w $a4(a6),a4 ; cmpi.l #$06000000,$4(a4) ; bne ; addq.b #2,$7(a6) ; moveq #$1b,d0 ; jsr $2a758` | un perso attend que l'objet `$24xx` qu'il a créé (`$065E5C`) passe à l'état 6 pour enchaîner (animation `$1B`) : dans l'image la suite n'arrive jamais par ce chemin. Coup à identifier (routine arcade `$065E4A`) ; candidat pour un « ne rend pas la main » du banc des coups de SFA3. |
| d | `0x4a030`-`0x4a0e8` (`$0073CE`-`$0073D0`) et `0x4a13c`-`0x4a1f4` (`$0073EC`-`$0073EE`) | appel ; `RES = D0.b − octet 2(A1,D2.W)` ; `bne` | `JSR ; BNE` : le `CMP.B 2(A1,D2.W),D0` manque, le `BNE` lit les drapeaux rendus par l'appelé | `$004B7A` `bsr $4bd4 ; cmp.b $2(a1,d2.w),d0 ; bne ; bsr $4bd4 ; move.b d0,$132(a6) ; move.b d0,$2(a1,d2.w)` puis `$004B90` `bsr $4ba4 ; cmp.b (a1,d2.w),d0 ; bne ; bsr $4ba4 ; move.b d0,$102(a6)` | tirage au hasard d'un décor (`$132`) et d'un perso (`$102`) avec « si c'est le même que la dernière fois, retirer une fois ». Dans l'image le `BNE` lit le Z du `MOVE.B T(PC,D0.W),D0` de l'appelé : on retire quand la valeur tirée est 0, jamais quand elle répète la précédente. Répartition faussée (l'id 0 presque jamais tiré), répétitions possibles. |

- **Mécanisme commun** : comparaison dont l'opérande n'est pas reconnu (comparaison à 0 sans `subu` ; long en mémoire
  par un An tout juste chargé ; index + déplacement en deux temps). Le test en attente n'est pas posé, rien n'est
  émis, et aucun audit ne le voit : `audit_exacts.txt` ne couvre que les blocs « exacts », `chutes.json` que les
  écritures de registre.
- **Essais** : (a) arcade et image, même coup reçu : X d'affichage du perso touché image par image pendant le
  tremblement (attendu arcade : ±1 px alterné). (b) partie Arcade jusqu'au combat 9 avec un perso d'id ≠ 0 dont
  l'adversaire n'est pas Bison final (par exemple Evil Ryu) : commande son émise au début du combat, contre l'arcade.
  (c) point d'arrêt image `$07EAD2`, contre arcade `$065EF6`.
- **Correctif de principe** : (1) traiter les trois formes ; (2) surtout un garde-fou général : à chaque branchement
  qui lit RES / C, vérifier que la dernière écriture MIPS de la case correspond au dernier poseur 68K émis (opérande
  et taille), sinon erreur de construction. `outils/drapeaux.py` fait ce contrôle après coup : sur ~16 000
  branchements par module, il ne reste que ces sites (ro5 : 0 ; ro9 : 0 hors A2).

---

## B. Fragilités sans effet prouvé

### B1. `Scc` rendu par `Bcc ; MOVE.B #$FF,ea ; BRA ; CLR.B ea`

- `outils/scc.py`, `sorties/scc_ro*.txt` : 50 / 51 / 52 sites. `Scc` ne touche pas les drapeaux ; `MOVE` et `CLR` si.
- Quand les drapeaux d'avant sont relus après : `SNE` + `BEQ/BNE` (3 par module), équivalent par chance (le Z du
  `MOVE`/`CLR` reproduit la condition). `Scc ; RTS` (5 par module) : pour la fonction ro3 `0xd1cf0` (13 appelants),
  aucun appelant ne relit RES / C ; deux fonctions appelées par pointeur (`0x13e8c0`, `0x181100`) non vérifiables.
- Faux dès qu'un `SEQ`, `SMI`, `SCS`… serait suivi d'un `Bcc` sans poseur. Correctif de principe : émettre le vrai
  `Scc` (`$50C0 | cc << 8`).

### B2. `ADDI` pour un `SUBI` du 68K d'origine

- Exemple ro3 image `$004E74` `ADDI.B #$ffffffe8,D3` pour l'arcade `$02427C` `SUBI.B #$18,D3` : même résultat, mais C
  et X inversés. `outils/retenue.py` (`sorties/retenue_ro*.txt`) : aucun `BCS/BCC` ni consommateur de X (`ADDX`,
  `ROXR`, `ABCD`) ne suit un tel `ADDI` dans les trois modules. Latent.

### B3. Hypothèse « résultat natif du portage supposé nul » (`translate.py:2305`)

- `jal f ; beq/bne v0,zero` est rendu `BRA` / rien, v0 supposé nul (§65). 25 / 27 / 24 sites. Dans 21 / 23 / 21 cas
  l'appelé est une aide du module qui calcule réellement v0 (ro3 `0x393b20` = OU de deux fonctions natives, appelée
  depuis le jeu en `0x472b4`, `0x200388`, `0x20db40` ; ro5 `0x41ab90`, 5 appels). Hypothèse connue et voulue
  (« moteur occupé ? » → jamais d'attente) ; elle n'a pas d'interrupteur et rien ne signale un nouveau site.

### B4. Pertes sans trace par construction, code mort

- `enc_cmp` (`translate.py:60`) rend `None` pour toute forme non prévue (par exemple minuende en mémoire et soustrait
  dans un registre : l'essai `CMPX`, l. 84, est resté à 0, « non validé ») ; l'appelant n'émet alors rien et ne compte
  rien. C'est le mécanisme de A3. Aucun compteur « comparaison non rendue » dans `build.log`.
- Code mort ou essais laissés à 0 : `CMPX`, `MEMSHIFT_GARDE` (« faux ici »), `PARTIAL_LIVE`, `AIG_D1_TOUS`, le mode
  `MEMMODE=type` (11 branches dans `translate.py`, `typed_rule.py`) alors que `mame_test.py:9` impose `cps2`.
- Règles sans interrupteur (non bissectables) : `byte_streams`, `byte_index_exact`, `byte_after_adda`,
  `vram_shift_const`, `swap_or`, `bswap16_mem`, `bswap32_or`, `aide_recomp` (`abcd`, `movem`), « résultat natif
  supposé nul » (B3), le repli mémoire de D8.
- Risque pour un correctif futur : `assemble.py` relit des marqueurs dans le TEXTE des mnémoniques, et plusieurs
  passes de `translate.py` aussi (`byte_index_exact` cherche « index pair suppose », `byte_after_adda` teste `'['`
  dans le texte, `vram_table_shift` une expression régulière sur `MOVE.W T_…`, `drop_dead_sr` le préfixe
  « [long echange] ») : changer un libellé change le code produit. Corriger A1 (plus de formes exactes) allonge le
  code : la coupure des données d'Hyper et les portées 16 bits bougent (précédent : `COUPE_BLOCS`).

---

## C. Vérifié et trouvé sain

- **Décodeur** (`mips.py`) : `DADDU` (fn `0x2D`) traité en `addu` : 583 / … sites, tous avec `zero` (aucune addition
  64 bits réelle). Aucun `j`, `beql`, `bnel`, `movn/movz` dans la zone 68K. `div`, `mfhi/mflo`, `slt*`, `lwc1/swc1`
  ne vivent que dans les aides du portage (connues : `abcd`, `sbcd` non traduite, `roxr`).
- **Tailles d'écriture des registres D** (`outils/tailles.py`) : `sb/sh/sw` d'une case D ↔ `.B/.W/.L` émis :
  ~29 000 écritures par module, aucun couple anormal (les écarts sont des `SWAP` de moitié haute, des `EXG` par la
  pile et des longs par post-incrément, relus un à un).
- **Opérande des tests différés** (`outils/drapeaux.py`) : ~6 700 tests mémoire et ~125 tests de registre par module
  portent bien sur l'opérande dont le MIPS a tiré RES ; hors A3, aucune taille fausse (`TST.W` « signe du long
  échangé » : toujours suivi de `BPL/BMI`, jamais d'un test de Z).
- **Écritures mémoire** (`outils/ecritures_mem.py`) : hors paires `swl/swr`, zone des aides et code C du portage,
  aucune écriture mémoire du code de jeu sans émission (les 3 restes par module sont des écritures natives vers des
  structures PS2).
- **Drapeaux rendus à l'appelant** (`outils/rendus.py`, `sorties/rendus_ro*.txt`) : 168 / 177 / 158 fonctions dont
  un appelant relit RES après le retour ; ~320 retours contrôlés par module. Les formes propres au traducteur placées
  juste avant un `RTS` gardent les drapeaux attendus : fermeture de zone D8 après `MOVEQ #0,D8` (CCR sauvé), opérations
  sur long échangé sans « drapeaux morts ». Aucun site faux trouvé (analyse linéaire : 30 % des retours, atteints par
  une étiquette, ne sont pas contrôlés).
- **Décalages variables** (`outils/decalages.py`) : sur 348 `sllv`, ~210 sont des masques de bit rendus `BTST/BSET/BCLR
  Dn,ea` (le Z du `BSET` sert de test) ; 6 `LSL`, 2 `ASR`, 4 rotations « décomposées » reprennent l'instruction
  d'origine. Rien d'anormal à la lecture d'échantillons (pas de preuve exhaustive).
- **Zones prêtées A8 / D8** (`outils/zones_conflit.py`) : 180 / 210 / 337 zones ; dans aucune le vrai registre prêté
  n'est lu ou écrit par le MIPS, aucun appel ni retour à l'intérieur, aucun chevauchement de deux zones du même
  registre. (Les sorties latérales et les tests déplacés PRETE_TEST / PRETE_CMP n'ont pas été relus un à un.)
- **Écritures des registres d'adresse** (`outils/ecritures_an.py`) : ~8 700 écritures de A0-A6 par module ; 57 / 62 /
  58 sans entrée de carte dans les 7 instructions voisines, toutes des formes fusionnées à la lecture d'échantillons
  (`(An)+` / `-(An)` absorbés, `EXG` par la pile, réalignement du portage). Pas de perte trouvée.
- **Talon `CONV`** (`kernel68k.py:154`) : garde les drapeaux (`MOVE SR` / `MOVE CCR`).
- **`drop_dead_sr`** (`translate.py:801`) : la liste blanche `_ecrase_nzvc` est correcte (instruction suivante qui
  écrase N, Z, V, C sans les lire ; X gardé).

---

## D. Angles non couverts

Voir `ETAT.md` (liste tenue à jour).

---

# 2e passe (agent `revue_traducteur_2`, 2026-11-11)

Même méthode : lecture statique (MIPS, carte de l'image v160, arcade) et, pour l'angle 8, constructions de ro3 dans une
copie de l'atelier (`<workspace>/work/revue_traducteur/copie`, sorties `constr/`), sans émulateur. Les constats sont numérotés E…
(nouveaux) ; ceux qui précisent un constat de la 1re passe le disent.

### En bref (2e passe), par gravité

1. **E5** (certain, 3 jeux) : bonus de score des enchaînements jamais ajouté (4 `ABCD` entre registres rendus par 4
   `JSR` vers un corps vide).
2. **E7** (certain, Upper et Hyper) : en match miroir de même couleur, le 2e joueur ne change pas de palette (`CMP.B
   D0,D8` non émis, le `BNE` lit les drapeaux de l'appelé).
3. **E7 bis** (certain, Upper) : objet de type 121, deux `CMP.W D0,$12(A6)` non émis : passe à l'état 6 tout de suite
   ou jamais. Sonde `REVUE_CMP_LOG` : ces 4 sites sont TOUTES les comparaisons que `enc_cmp` abandonne ; `CMPX=1` les rend.
4. **E2** (mécanisme certain, effet nul trouvé) : les fonctions C non listées dans `hooks_fork` sont exécutées sous
   forme de fragments (16 / 19 / 13 cibles), dont un à chaque coup dans la routine de dégâts.
5. **E8** : `EXTRA_REGS=0` et `D8_HOME=none` ne construisent plus SFA3 ; `PRETE_TEST`, `RETAG_BRAW`, `AIG_D1_TOUS`,
   `MEMMODE` sans effet ; `CMPX` (laissé à 0) est le correctif de E7.
6. **E1, E3, E4, E6** : tri des listes de parité (aucun nouveau site, un candidat écarté, un trou latent), non
   alignés, tables, relogements et conversions sains ; une demande de redémarrage non servie à vérifier.
Garde-fous prêts à brancher après chaque construction : `outils/bcc_apres_appel.py`, `outils/aides_appels.py`,
`outils/fragments_atteints.py`, et la sonde `REVUE_CMP_LOG`.

## E1. Angle 1 : tri des listes de parité (précise A1, AUCUN nouveau site certain)

Outils : `outils/parite_tri.py` (preuve de parité par un accès mot / long aligné du même An dans la même portée),
`outils/adda_trou.py`, `outils/flux_meme.py`, `outils/flux_ptr.py`, `outils/relectures.py`, `outils/ctx.py`.
Sorties : `sorties/parite_tri_ro*.txt`, `adda_trou_*`, `flux_meme_*`, `flux_ptr_*`.

- **Preuve automatique** (`parite_tri.py`) : sur 4 714 / 4 976 / 4 820 accès octet à XOR 1 fixe, 2 840 / 2 945 / 2 608
  ont An PROUVÉ pair sans rupture (un `.W` / `.L` aligné par le même An), 709 / 812 / 820 à travers une rupture, **0
  prouvé impair**, 1 165 / 1 216 / 1 392 sans preuve (dont pointeur d'objet `MOVEA.W` 620 / 650 / 700, pair par
  construction ; `LEA pair(A5/A6)` 169 / 180 / 134, pair). Reste réellement indécidable par cet outil : origine
  « inconnue » (argument, MOVEM, prêt) 118 / 125 / 347, ADDA 46 / 46 / 35, `MOVEA.L` 195 / 198 / 159.
- **Liste « après ADDA »** (46 / 46 / 35 sans preuve, relus un à un) : hors sites a et c déjà connus, TOUS ont un index
  pair : index × 4 / × 32 / × 40 (`LSL`, `MULS #40` d'Hyper), `ANDI #$60`, ou mot de table dont toutes les valeurs sont
  paires. Le **candidat « copie de 20 champs »** de la 1re passe (ro3 `0x59fb4`-`0x5a170`, ro5 `0x60b74`, ro9 `0x646c4`)
  est **écarté** : A0 = base paire + mot de la table PS2 `0x86F1B4` / `0x97AF24` / `0x69E74E`, dont les 16 mots valent
  `$20` ou `$2A`. De même ro3 image `$02679C` (table `T_58c600` : 0, `$1D0`, `$3A0`…, toutes paires).
- **Trou de `byte_after_adda`, latent** : la règle (l. 1028-1035) ne traite que le mode `d16(An)` ; un accès `(An)`
  (déplacement image 0, soit déplacement PS2 1) reste à XOR 1 fixe même quand An est tenu pour « de parité inconnue ».
  2 sites par module (`sorties/adda_trou_*`, ro3 image `$027DC0`, `$028012` `MOVE.B (A2),$80(A6)`, encadrés par des
  `$1(A2)`, `$3(A2)` exacts) : index × 4, donc sans effet aujourd'hui. Elle ne salit pas non plus An après `ADDA.W
  d(An),Am`, `ADDA.W T(PC,Dn),An`, `ADDQ #1,An`, `SUBA`. Correctif : même traitement pour le mode 2, ou le défaut
  inversé proposé en A1.
- **Liste « MOVEA.L »** (195 / 198 / 159 sans preuve) : 85 % viennent de `$1C(An)` (pointeur d'animation : enregistrements
  de 8 octets, avancés par `ADDQ.W #8`, relus en long), `$D8(A1)`, `$A0(A6)` (tables de 32 / 40 octets), `$A3BC(A5)`
  (base paire + mots pairs) : pairs par structure. **Pointeurs de flux** (champ relu puis rangé après une avance
  d'octets, `flux_meme.py`) : UN seul champ par module, `$54(A6)` = site e. Pointeur impair rangé par calcul
  (`flux_ptr.py`) : un seul, `$40(A4)` = site f. Les autres rangements après avance sont des flux de MOTS (`$230(A6)`,
  `$220(A6)`…, pairs).
- **Sites Upper / Hyper des routines a, e, f** (relevé demandé) :
  - a (initiales) : Upper, 15 accès `x.B $1(A1)` / `(A1)`, image `$01131C`-`$0113AC`, mips `0x95e2c`, `0x95e40`,
    `0x95f74`, `0x96004`, `0x96028` (2), `0x96174`, `0x961d8`, `0x9622c`, `0x96478`, `0x9648c`, `0x964d4`, `0x965dc`,
    `0x965fc`, `0x966e8` (origine `ADDA.W D1,A1` image `$0112CA`). Hyper : routine absente (aucun `CMPI.B #$2E,$1(A1)`).
  - e (texte défilant) : Upper image `$0267B0`, `$026820` (mips `0x119c40`, `0x119f10`, rangement `$0267D6`,
    `$026846`) ; Hyper image `$093FBC`, `$09402C` (mips `0x3be380`, `0x3be650`, rangement `$093FE2`, `$094052`).
  - f : Upper rangement image `$0323C6` (`MOVE.L A0,$40(A4)`), Hyper `$07B286` ; relectures déjà citées en A1.
- **Conséquence pour A1** : la « famille de plusieurs centaines d'accès indécidables » se réduit, à la lecture, aux 7
  routines a-g ; le reste indécidable statiquement est l'origine « inconnue » (An reçu en argument : 118 / 125 / 347
  accès). La sonde à l'exécution reste le seul moyen de fermer ce reste. Gravité des nouveaux points : aucune
  (précision) ; le trou `(An)` est latent.

## E2. Angle 9 : le code C du portage est exécuté sous forme de FRAGMENTS (mécanisme certain, effet nul trouvé)

Outils : `outils/appels_c.py`, `fragments_c.py`, `fragments_atteints.py` (lit les octets de l'image), `natif_ecrit.py`,
`natifs.py`, `cibles_natives.py`, `img.py`. Sorties : `sorties/appels_c_*`, `fragments_c_*`, `fragments_atteints_*`,
`cibles_natives_*`, `natifs_ro9_zoneC.txt`.

- **Trois sorts pour une fonction C du module** (critère `mame_test.native_at`) appelée par `jal` :
  1. **listée** dans `hooks_fork_roN.json` (« natif du module », 15 / 14 / 15 cibles) et native : l'appel va au talon
     `RTS` `$800` (vérifié dans les octets : `bsr.w $800`, `jsr $800.l`). Effet perdu par construction, résultat `v0`
     supposé nul (B3). Exemples d'Hyper : `0x22b00` (chargeur des 4 fichiers de perso, 3 sites du jeu), `0x23910`
     (256 instr., 34 écritures en RAM PS2 `0xBE2000`), `0x295a0` (1 444 instr., 35 écritures par A5 ; même fonction
     dans SFA3 `0x38a850` et Upper `0x408480`).
  2. **remplacée par le noyau** : ro3 `0x381410` (lecture des manettes) → `jsr $8a0` / `jmp $8bc` (`stub_in`).
  3. **NON listée** (16 / 19 / 13 cibles appelées depuis du code recompilé, `sorties/fragments_atteints_*`) :
     l'appel va à l'ÉTIQUETTE de la fonction C, c'est-à-dire à la première instruction que le traducteur a émise à
     partir de cette adresse. Le traducteur ne comprend du C que ce qui ressemble à du 68K (accès par A5 / A8, `jal`) ;
     il perd les locales, les registres `s0-s4`, les conditions sur ces valeurs. Le résultat est une suite de fragments
     où les deux branches d'un `if / else` se suivent.
- **Preuve (SFA3, routine de dégâts)** : mips `0x3a24c` (image `$004CB2`, juste avant `SUB.W D4,$50(A1)`) et `0x1cba54`
  (image `$0446EC`) : `jsr $923be` (aide `0x38ebe0`) → `bra $923ac` → fragment de `0x38eb00` → fragment de `0x38e730`.
  Le C fait « cumul des dégâts de la série += dégât ; plafond 999 ; maximum = max(maximum, cumul) » ; l'image exécute
  `BTST #0,$C14F(A5) ; BEQ ; BCLR ; CLR.W $C144(A5) ; MOVE.W #$3E7,$C144(A5) ; MOVE.W $C144(A5),$C146(A5) ;
  MOVE.W #$3E7,$C144(A5) ; MOVE.W #$3E7,$C146(A5) ; RTS` : les deux compteurs valent 999 après chaque coup. Homologues :
  Upper mips `0x3eb80`, `0x2254a0` (aide `0x40c8e0`) ; Hyper `0x50e50`, `0x2a48e8` (aide `0x3b38f0`, champs `$C344`,
  `$C346`, `$C34F`).
- **Effet en jeu : aucun trouvé.** Ces champs (`$C1xx(A5)` de SFA3, `$C3xx(A5)` d'Upper / Hyper : variables du mode
  Entraînement du portage) ne sont lus que par du code C lui-même non exécuté. Les autres fragments atteints depuis le
  code de jeu se réduisent à `BRA ; RTS` ou à des appels du moteur PS2 (talon `RTS`) : SFA3 `0x3838d0` (chargeur, 6
  sites du jeu), `0x38d580` ; Upper `0x4115a0` (6 sites), `0x40b1b0` ; Hyper `0x3ba5c0` (« moteur occupé ? », 6 sites),
  `0x2c3a0`. Le fragment de ro3 `0x381470` (`CLR.W $11A(A4) ; ORI.W #1 / 2 / 4 / 8 / $8000,$11A(A4)`) écrirait `$800F`
  dans un champ d'objet, mais son seul appelant est l'aide `0x381410`, remplacée par le noyau.
- **Zone C d'Hyper `0x24bf8`-`0x2fdc8`** : c'est le C des menus et du chargement d'Hyper, mêlé à quelques fonctions
  recompilées qu'il appelle (`0x266a0`, `0x278b0`, `0x2c610`, `0x2d090`…). 1 247 lignes de carte y sont émises
  (fragments). Aucun pointeur de code du code traduit n'y mène (`cibles_natives.py` : les 10 « cibles natives » par
  module sont des entrées de table non alignées, voir E4) ; seuls y entrent les `jal` ci-dessus. Verdict : **perdu par
  construction** (talon `RTS`) pour les 11 cibles listées de la zone, **fragments** pour `0x2c3a0`.
- **Risque** : rien ne distingue une fonction C « listée » d'une « non listée » à la construction ; une fonction C qui
  écrit un champ lu par le jeu, ou dont le fragment contient une écriture par un registre d'adresse resté à sa valeur
  d'appelant, agirait sans message. **Essai** : point d'arrêt MAME aux étiquettes de `sorties/fragments_atteints_*`
  pendant une tournée ; toute étiquette atteinte hors des 6 fonctions ci-dessus est à lire.
- **Correctif de principe** : à l'assemblage, toute cible de `jal` pour laquelle `native_at` est vrai va au talon
  `RTS` (ou à un talon dédié), qu'elle soit dans `hooks_fork` ou non, et la liste est écrite dans `build.log`. Gravité :
  mécanisme certain ; effet actuel nul (prouvé pour le site des dégâts, probable pour les autres).
- **Carte trompeuse** (mineur) : pour une cible native située sous la zone de jeu (Upper, Hyper), la carte écrit
  `JSR $020480.L [mips 002138e0]` alors que l'image appelle `$800` ; pour les cibles du haut elle écrit `JSR ???`.
  La carte ne permet donc pas de savoir où va un appel : lire les octets (`outils/img.py`).

## E3. Angle 6 : accès non alignés, tables de données : sains

- `outils/non_alignes.py` (`sorties/non_alignes_*`) : 110 / 113 / 77 paires `lwl/lwr` et `swl/swr`. Toutes celles du
  code de jeu sont rendues : paires adjacentes par `unaligned_pairs`, les 2 (ro9 : 1) paires séparées par une
  instruction par « écriture mémoire retrouvée », les lectures différées par le test qui suit (`CMP.L $6A(A6),D1`,
  `TST.L $36(A6)`). Les 3 paires à déplacement 1 sur la base `zero` (ro3 `0x7bb38`, `0x7bb44`, `0x9a330`) sont des
  écritures à l'adresse absolue 1 : rien d'émis (sur l'arcade : erreur d'adresse, piège de mise au point).
- Tables de DONNÉES `T(PC,Dn)` : 1 582 / 1 730 / 1 740 sites, tous en forme absolue (lecture directe dans l'image des
  données) ; aucune copie hébergée bornée (le défaut « tableau de structures tronqué » de §63 ne peut plus arriver).
  17 / 18 / 6 `LEA T(PC,Dn),An` rendus `LEA abs ; ADDA.W Dn,An` (drapeaux intacts, An « sale » pour la règle A1).

## E4. Angles 6 et 10 : tables de sauts, relogements, conversions : sains, deux fragilités

- **Tables d'aiguillage** (`outils/tables_sauts.py`, `sorties/tables_sauts_*` ; 1 989 / 2 125 / 1 646 tables) :
  `read_jump_table` (l. 177) n'exige pas une cible multiple de 4 et, après un trou (entrée nulle), franchit la borne
  « table suivante référencée » : ~650 tables par module portent un trou de bourrage PLUS la 1re entrée de la table
  suivante, et 10 par module ont une entrée fantôme (valeur de données qui tombe dans la plage de code, par exemple
  `T_59a1e0[18]` = `0x220012`). Entrées en trop, jamais indexées par un index valide : sans effet. Aucune table trop
  COURTE trouvée (44 / 50 / 48 candidates : toutes s'arrêtent sur une autre table référencée).
  8 à 18 sites par module ont un masque d'index plus large que la table (`ANDI.W #$FE`, table de 4) : comme l'arcade.
- **Étape B / C** (`assemble.reloge_code`, `natif`) : 24 / 24 / 22 tables de code et 6 tables de pointeurs RAM relogées.
  `natif()` ne cherche les autres lecteurs d'une table que dans le TEXTE des mnémoniques ; un lecteur indirect (pointeur
  vers la table rangé dans les données) lui échapperait et lirait un long en ordre 68K avec la remise en ordre.
  `outils/reloge_refs.py` (`sorties/reloge_refs_*`) : aucun long aligné des données ne pointe dans une table relogée
  (les 3 correspondances sont des valeurs fortuites, impaires ou du texte). Sain aujourd'hui ; à refaire si la liste
  des tables relogées change.
- **Talons de conversion** : le hachage du noyau (`LSR #6 ; EOR ; LSR #2`) est bien `((k>>2)^(k>>8)) & $3FFF` ; les
  deux talons laissent inchangée une valeur hors de leurs plages. Contrôle des plages de `plages_conv` pour les trois
  modules : aucune adresse 68K convertie ne retombe dans une plage PS2 (pas de double conversion possible), grâce à
  l'étiquette `$01` des blocs externes ; ce qui tient donc à la règle de remasquage 24 bits (`RETAG24`).

## E5. Angle 5 : le bonus de score des enchaînements n'est jamais ajouté (les trois jeux) — mécanisme certain

Outils : `outils/mults.py` (`sorties/mults_*`), `outils/retenue.py` (1re passe), `outils/img.py`, `outils/arc.py`.

- **Site** : SFA3 mips `0xbc628`-`0xbc6f8` (image `$01908A`-`$0190DE`, arcade `$07EAA4`-`$07EAD0`) ; Upper mips
  `0xfc4b4`-`0xfc578` (image `$022690`-`$0226E4`) ; Hyper mips `0x385930`-`0x385998` (image `$08BA74`-`$08BAC0`).
- **Arcade** : `moveq #0,d0 ; move.b $45(a6),d1 ; cmpi.b #$10,d1 ; bcs suite ; (d0 = BCD(d1-15) << 12 ; d1 = 15) ;
  suite: lsl.w #2,d1 ; add.l table(pc,d1.w),d0 ; movea.w $36(a6),a0 ; jmp $1bb44` (ajout de D0 au score du joueur A0).
  Table `$07EAD6` (= PS2 `0x589390`, identique) : 0, 0, `$300`, `$500`, `$1000`, `$1200`, `$1500`, `$2000`, `$2300`,
  `$2600`, `$3000`, `$3300`, `$3600`, `$4000`, `$4500`, `$5000` (BCD) : bonus selon le nombre de coups `$45(A6)`.
- **PS2** : le portage a remplacé l'`ADD.L` binaire par une addition BCD : `D8 = table[d1]` puis `ANDI #$EF,CCR` et
  QUATRE appels de l'aide `abcd` avec `a0 = adresse de la case D8 + k`, `a1 = adresse de la case D0 + k` (k = 0..3 :
  `ori a0,v0,0x1144+k ; ori a1,v0,0x1124+k ; jal abcd`), soit D0 = D0 + D8 en BCD sur 4 octets.
- **Image** : la règle `aide_recomp` ne reconnaît `abcd` que sur des pointeurs mémoire ; ici elle émet `JSR` vers
  l'étiquette de l'aide, où le corps C de l'aide est réduit à `BRA ; BRA ; BRA ; RTS` (image SFA3 `$09086A`, Upper
  `$1056`, Hyper `$105A` ; octets lus). Les quatre `JSR` ne font rien : **D0 garde 0** (enchaînements de 2 à 15 coups)
  ou seulement le terme `BCD(n-15) << 12` (16 coups et plus), puis l'ajout au score est appelé avec cette valeur.
- **Effet en jeu** : aucun point de bonus d'enchaînement (300 pour 2 coups … 5 000 pour 15) dans SFA3, Upper et Hyper.
  Le score seul est touché ; invisible en VERSUS si le score n'y est pas compté (`TST.B $111(A5)` / `$140(A5)` /
  `$124(A0)` à l'entrée de l'ajout).
- **Déjà entrevu** : `docs/rapports/recherche/D-SONDES.md` l. 226 (« corps de l'aide abcd appelé 4 fois, Upper `$226C8`,
  Hyper `$8B374` : ce serait un ajout BCD qui ne fait rien, à vérifier en mode Arcade »). Nouveau ici : le site de SFA3,
  l'identification (table des bonus), la forme PS2 exacte et la conséquence (D0 = 0).
- **Essai** : mode Arcade, J1, un enchaînement de 3 coups contre un adversaire en garde basse relâchée : le score doit
  monter de 500 de plus que la somme des coups (arcade) ; ou point d'arrêt image `$0190DA` (SFA3) : D0 doit valoir
  `$00000500`, il vaut 0.
- **Correctif de principe** : reconnaître la forme « `abcd` sur deux cases de registre » (`a0`, `a1` = constantes
  `0x70001124`-`0x70001147`) et émettre, pour l'octet k d'un long : `ABCD Dy,Dx ; ROR.L #8,Dx ; ROR.L #8,Dy` (ROR ne
  touche pas X ; après 4 tours les registres sont revenus en place). Garde-fou général : un `jal` vers une adresse de
  `AIDES_RECOMP` qui n'est pas rendu en ligne doit faire échouer la construction (aujourd'hui : `JSR` muet vers un corps
  vide ; même cas pour l'aide `sbcd`, non déclarée, SFA3 `0x570BB0` 4 appels en `0x20a1a4`-`0x20a234`, Upper
  `0x213350`, déjà notée dans `DEFAUTS-BANC.md` §6).
- **Gravité** : certain pour le mécanisme (lecture MIPS + octets de l'image + arcade) ; l'identification « bonus
  d'enchaînement » est probable (table et appel de l'ajout de score), à confirmer par l'essai.

### Vérifié sain dans cet angle

- **MULS / MULU** : 15 `mult` par module dont 6 (ro9 : 8) dans le code de jeu, tous rendus `MULS.W` / `MULU.W`
  (`[mult du R5900]`) ; la routine d'affichage (`MULS.W D2,D0 ; ASR.W #4,D0` … `MULS.W (A0)+,D0 ; ASR.L #8,D0`) est
  identique à l'arcade `$021C38`-`$021C7C`. Les 2 / 3 / 41 « multiplications décomposées » (`MULS.W #40,D0` d'Hyper…)
  suivent le signe du MIPS (`dsra32` → MULS, `andi $FFFF` → MULU). Les `mult/div` à HI/LO (`rd = 0`) ne vivent que
  dans le C (rien d'émis, attendu). Aucun `DIVS/DIVU` dans les images (les divisions 68K d'origine sont des boucles).
- **ROXR** (4 par module, fonction d'angle arcade `$05DAF2`) : X vient bien du `SUB.W` qui précède (le `BRA` intercalé
  va à l'instruction suivante, `EXG` et `Bcc` ne touchent pas X) ; `ROR.B #5` = `ROL.B #3`. Identique à l'arcade.
- **ADDX** (1 par module, division 32 bits arcade `$01BBBE`) : `ADD.L D3,D3 ; ADDX.L D0,D0`, identique.
- **ABCD mémoire** (15 / 15 / 12) : la séquence émise sauve SR, calcule `(An-1) XOR 1`, recharge le CCR sauvé
  (`MOVE.W $C(SP),CCR`) juste avant `ABCD -(A2),-(A3)` ; `MOVEM`, `ADDQ #2,SP`, `ADDQ.W #1,An` ne touchent pas les
  drapeaux : X et Z (collant) passent bien d'un octet au suivant. `ANDI #$EF,CCR` rendu tel quel. Le sens (octets
  croissants après `SUBQ.W #4`) est celui de la disposition PS2 ; A0 / A1 finissent comme sur l'arcade.
- **Case X (`0x1154`)** : lue par le seul traducteur aux formes ci-dessus ; aucun `SUBX`, `NEGX`, `ROXL`, `SBCD` émis.

## E6. Écritures « tombées » (`chutes.json`) relues, et demande de redémarrage non servie (à vérifier)

- `chutes.json` (12 / 13 / 10 sites distincts ; le fichier les porte en double ou en triple) : dans le code de jeu,
  - SFA3 `0x1c7b30`, `0x1c7bb8` (Upper `0x2210b0`, `0x221138` ; Hyper `0x29f660`, `0x29f6e8`) : `D0 = natif(D0)` après
    l'appel de `0x571900` (filtre des directions opposées, table `0x59C030`), remplacé par le talon `RTS` : l'historique
    des entrées `$770` / `$B70(A5)` n'est pas filtré, comme sur l'arcade (image `$043E88`-`$043EB0` = arcade `$02773A`
    sans l'appel). Sans effet avec un vrai manche.
  - SFA3 `0x19a94c`, `0x19af38`, `0x19b6f0`, `0x19cf54` : `A1 = A1` (écriture sans effet). Sain.
  - SFA3 `0x2f114` (Upper `0x32694`, Hyper `0x3f014`) : dans la fonction d'image du portage (`tache_image`, mips
    `0x2ef30`), boucle C « pour i de 0 à 15 : D0 = i × 32 ; appel de `0x2f990` (fin forcée de la tâche i, table
    `$8184(A5)`) », exécutée quand le drapeau PS2 `0x88D0C0` (image `$F009C0`) est posé ; puis `0x88D0C8 = 1`.
- **À vérifier (hors traducteur)** : ce drapeau est posé par le code de jeu traduit (SFA3 mips `0x48d2c`, image
  `$006F80`, branche du menu du portage : attente de 45 images, puis demande et fin de la tâche ; aussi `0x38bdc4`,
  `0x38be98`). La fonction d'image n'est pas appelée par le noyau reconstruit (`va_frame` n'est lu que comme
  argument), et `kernel68k.py` ne lit pas `$F009C0` : rien ne termine les 16 tâches ni ne pose `$F009C8` (testé en
  image `$0067F8`). Si cette branche du menu est atteinte, le redémarrage demandé n'a pas lieu. Supposé : à
  rapprocher des crochets `OPTION_RETOUR` / `EXIT_RETOUR`, qui traitent peut-être déjà ce chemin. Essai : point
  d'arrêt image `$006F80`.

## E7. Upper et Hyper : couleur du 2e joueur en match miroir, test « même perso » perdu — certain

Outil : `outils/bcc_apres_appel.py` (`sorties/bcc_apres_appel_*`) : Bcc de l'image placé juste après un `JSR` alors que
le MIPS recalcule RES entre l'appel et le branchement. Résultat complet : ro3 2 sites (= A3d), **ro5 1, ro9 1**
(nouveaux ; la 1re passe donnait 0 pour ces deux modules). Trouvé d'abord par l'essai `CMPX=1` de l'angle 8.

- **Site** : Hyper mips `0x31fba0`-`0x31ffd4` (image `$07A8D2`-`$07AA02`), comparaison en `0x31fc8c`-`0x31fd48` (image
  `$07A98A`) ; Upper mips `0x25dd58`-`0x25de68` (image `$0570FE`-`$05713C`). Pas d'homologue dans SFA3 ni dans l'arcade
  (routine du portage).
- **MIPS** : `BTST #1,$15A(A4) ; BEQ fin ; A8 = A6 ; JSR f ; D8.b = D0 ; A8 = A4 ; JSR f ; CMP.B D0,D8 ; BNE fin ;
  MOVE.B $129(A4),D0 ; CMP.B $129(A6),D0 ; BNE fin ; ADDQ.B #1,$129(A6) ; AND.B masque[$103(A6)],$129(A6) ;
  CMPI.B #6,$129(A6) ; BLT fin ; CLR.B $129(A6)`. `f` (Hyper `0x31ffe0`, Upper `0x25e0a0`) rend l'id de perso
  normalisé de A8 (`$103`, `$25` → `$15`, 4 → 18 et 6 → 20 si `$133` < 0). Sens : même perso ET même couleur (`$129`
  image = `$128` arcade, `joueur_couleur_palette`) → le joueur A6 prend la couleur suivante.
- **Image** : `JSR f ; MOVE.B D0,$87F1(A5) ; JSR f ; BNE fin` : le `CMP.B D0,D8` (D8 au domicile `$87F1(A5)`, minuende
  en mémoire) n'est pas émis ; le `BNE` lit les drapeaux rendus par le 2e appel de `f`, soit ceux de son dernier
  `CMPI.B #6,D0` : Z seulement si le perso de A4 a l'id 6 (et `$133` = 0).
- **Effet en jeu** : en match miroir (hors perso d'id 6) avec la même couleur choisie, la couleur du 2e joueur n'est
  PAS décalée : deux persos identiques de même palette. À l'inverse, si A4 a l'id 6, la couleur de A6 est décalée dès
  que les numéros de couleur sont égaux, même entre deux persos différents.
- **Preuve** : lecture MIPS + carte ; l'essai `CMPX=1` (interrupteur laissé à 0, « non validé ») émet à cet endroit
  `CMP.B D0,$87F1(A5) [minuende en memoire, par D1 sauve]` dans Hyper (`constr/ro9_CMPX_1/carte_image.txt`, seule
  ligne ajoutée).
- **Essai** : VERSUS Hyper, même perso (par exemple Ryu contre Ryu), même bouton de couleur pour les deux : sur PS2 le
  2e joueur change de palette ; point d'arrêt image `$07A98A` : Z doit refléter l'égalité des ids.
- **Correctif de principe** : valider `CMPX` (comparaison « mémoire − Dn » par un registre sauvé) pour ce site, ou
  rendre la comparaison à l'envers par `CMP.B $87F1(A5),D0` puisqu'un `BNE` / `BEQ` seul la consomme ; et brancher
  `bcc_apres_appel.py` en garde-fou de construction (0 site attendu hors A3d une fois corrigé).
- **Gravité** : certain (mécanisme) ; effet visible probable (dépend du bit 1 de `$15A(A4)`, mode à identifier).

### E7 bis. Liste COMPLÈTE des comparaisons que `enc_cmp` ne rend pas (sonde dans la copie), et 2 autres sites d'Upper

- **Sonde** : dans `<workspace>/work/revue_traducteur/copie/translate.py` seulement, les deux appelants de `enc_cmp` (l. 2108 et
  3789 d'origine) notent chaque retour `None` dans le fichier `REVUE_CMP_LOG` (sans effet sur la sortie : les trois
  images reconstruites sont identiques aux références, `constr/ro*_sonde`). C'est le compteur demandé en B4.
  Résultat (`sorties/cmp_perdues_ro*.txt`) : **ro3 0, ro5 3, ro9 1**, tous de la forme « minuende en mémoire,
  soustrait dans un registre D » : ro5 `0x25de68` et ro9 `0x31fd48` (= E7), et **ro5 `0x41570c`, `0x415810`**.
  (Les pertes A3 de SFA3 ont un autre mécanisme : le test en attente n'est jamais posé.)
- **Upper mips `0x415450`-`0x415874`** (image `$0A0238`-`$0A027A`) : état 1 (table `T_6285f0`, entrée 1) de l'objet de
  type n° 121 de la table des objets `T_615100` (fonction `0x604e30` ; entrée propre à Upper, nulle dans SFA3).
  MIPS : `… ; CMPI.W #$150,$16(A6) ; BGE fin ; MOVE.W $292(A5),D0 ; TST.B $3D(A6) ; BNE autre ; ADDI.W #$200,D0 ;
  CMP.W D0,$12(A6) ; BGE fin ; BRA suite ; autre: ADDI.W #$80,D0 ; CMP.W D0,$12(A6) ; BGT suite ; fin: MOVE.B
  #6,$5(A6) ; suite: …` (l'objet passe à l'état 6 quand il sort de l'écran : X contre le défilement `$292(A5)`).
- **Image** : les deux `CMP.W D0,$12(A6)` manquent ; `BGE` et `BGT` lisent les drapeaux de l'`ADDI.W` (signe de
  défilement + `$200` ou + `$80`, positif en pratique) : avec `$3D(A6)` = 0 l'objet passe à l'état 6 dès la 1re image
  de cet état ; avec `$3D(A6)` ≠ 0 il n'y passe jamais par ce test (seul reste le test `$16(A6)` ≥ `$150`).
- **Effet** : un objet d'Upper (à identifier : type 121) disparaît tout de suite dans un sens et ne se libère pas
  hors écran dans l'autre. **Essai** : point d'arrêt image `$0A025E` (Upper) ; l'objet atteint, comparer sa durée de
  vie à la PS2. **Gravité** : certain (mécanisme), effet à identifier. Même correctif que E7 (`CMPX`).

## E8. Angle 8 : les interrupteurs, par construction

Méthode : copie de l'atelier (`copie/`), `construit.sh` (comme `<workspace>/work/v160/construit.sh`), une construction à la fois
sous `nice 19`, aucun émulateur. Référence reconstruite = v160 à l'octet pour les trois modules (ro3 `9b06c7cf`, ro5
`3a9b7fd9`, ro9 `0baed6af`). 1er tour : 73 essais sur ro3 (`outils/interrupteurs.sh`) ; 2e tour sur ro9 pour les 25
sans effet ou en échec sur ro3 ; 3e tour sur ro5 pour les 9 encore sans effet (`outils/interrupteurs_liste.sh`).
Dépouillement : `outils/interrupteurs_bilan.py` → `sorties/interrupteurs_bilan_ro{3,5,9}.txt` (identique / différent,
lignes de carte changées hors adresses, compteurs de `build.log` qui bougent). Chaque essai garde
`constr/<module>_<NOM>/build.log` et `carte_image.txt`.

- **Interrupteurs cassés (la construction échoue)** : `EXTRA_REGS=0` et `D8_HOME=none` sur ro3 :
  `AssertionError: routine 898e0 : place 32 < 38` (`mame_test.py:298`) : les 5 routines réécrites à la main de SFA3
  sont posées PAR-DESSUS la routine traduite et exigent qu'elle soit au moins aussi longue. Ces deux interrupteurs ne
  peuvent plus servir à une bissection sur SFA3 (ils construisent sur ro9). Plus largement, tout changement qui
  raccourcit ces 5 routines casse la construction ; vérifié par ailleurs : aucun saut extérieur ni pointeur aligné
  n'entre au milieu de ces 5 plages.
- **Interrupteurs qui ne coupent RIEN dans les trois jeux** (image identique à la référence) :
  - `PRETE_TEST=0` : masqué par `PRETE_CMP` (v160). Avec `PRETE_CMP=0` il agit encore (ro9 : `8e4f9ef2` →
    `b8e699cf`). Le commentaire « PRETE_TEST=0 → v158 à l'octet » n'est donc vrai qu'avec `PRETE_CMP=0`.
  - `RETAG_BRAW=0` : aucun site dans ro3 / ro5 / ro9 (règle de la greffe ro9a).
  - `AIG_D1_TOUS=1` : sans effet tant que `AIG_D1_SEUL` restreint les sites (défaut `181d20,2ef020`).
  - `OBJ_MIROIR`, `SFA3_TUILES_S3` : lus par `banques.py` / `hsfa_gfx.py` (banques graphiques), hors de l'image
    programme : rien à en attendre ici.
  - `MEMMODE` : `mame_test.py:9` l'impose à `cps2` ; la variable d'environnement est sans effet et les branches
    `MEMMODE=='type'` / `'hote'` de `translate.py` (6 tests, `typed_rule.py`) sont du code mort pour la construction.
- **Compteur qui bouge sans que l'image change** : `SHIFT_MR=0` sur ro3 (8 → 0) et ro9 (15 → 0), images identiques ;
  il agit sur ro5 (2 lignes). Le compteur « décalages de lectures mémoire » ne mesure donc pas un effet.
  `CONST_OP=0` sur ro3 : image identique mais `audit_exacts.txt` passe de 0 à 2 blocs (135 sur ro9, où 18 lignes
  changent).
- **Sans site dans SFA3, actifs ailleurs** (identiques sur ro3, différents sur ro9 ou ro5) : `BYTE_PRE`, `CONST_OP`,
  `PILE_LUI`, `TBLBYTE`, `ANDAND`, `SPILL_Q`, `LOGIC_ZERO`, `EXT_MEM`, `MEMSWAPD`, `PRETE_CMP`, `RETAG24`,
  `AIG_BRANCHE`, `AIG_D1`, `COUPE_BLOCS` (ro9) ; `BIGSHIFT`, `SW_X4`, `SHIFT_MR` (ro5 seulement).
- **Tous les autres coupent** (46 essais sur 73 changent l'image de ro3) ; le bilan donne pour chacun le nombre de lignes de carte touchées (de 1
  pour `MEMSHL`, `ABSEXT`, `D8HI`, `CMPMM` à 1 860 pour `DROP_SR`). À 0, plusieurs laissent des écritures de registre
  « tombées » en plus (`TBLMASK`, `ABSEXT`, `D8HI`, `ROT`, `MEMSHIFT`, `MULS`, `TBLBYTE`, `LOGIC_ZERO`, `EXT_MEM`) :
  la valeur 0 ne rend pas une ancienne forme, elle perd du code.
- **Essais laissés à 0** : `CMPX=1` : 0 forme sur ro3, 2 formes (3 lignes) sur ro5, 1 sur ro9 : ce sont exactement
  les 4 comparaisons perdues de E7 / E7 bis ; l'essai « non validé » les corrige (à valider au banc).
  `PARTIAL_LIVE=1` (42 lignes sur ro3) et `MEMSHIFT_GARDE=1` (12 lignes, « faux ici ») changent l'image : essais
  abandonnés, à retirer ou à documenter. `AUDIT_MEM=1` : image identique, écrit `mem_miss.json` (757 écritures
  mémoire sans trace sur ro3, audit existant et non exploité dans `build.log` par défaut).
- **Règles sans interrupteur** (rappel B4, inchangé) : `byte_streams`, `byte_index_exact`, `byte_after_adda`,
  `vram_shift_const`, `swap_or`, `bswap16_mem`, `bswap32_or`, `aide_recomp`, « résultat natif supposé nul », repli
  mémoire de D8, étape B (`RELOGE_CODE` existe mais `=0` n'a pas été rejoué en v160 : ici `RELOGE_CODE=0`,
  `RELOGE_RAM=0`, `RELOGE_NATIF=0` construisent et changent l'image comme attendu).
