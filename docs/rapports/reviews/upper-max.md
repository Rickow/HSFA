# Upper MAX on translator v161 and critical review of the MAX integration (2026-11-11)

**Summary (English).** Work and review of agent `revue_upper_max` (11/11). Part A moves Upper MAX to translator v161;
part B (sub-agent, `revue_B/REVUE.md`) reviews the MAX integration statically on the max55 build: 16 findings.
Workshop: `<workspace>/work/revue_upper_max/`.
- **Part A, merged (journal §220)**: `integre_max.py` no longer reads hard-coded image addresses (sites found by unique
  pattern and decoded jumps, cross-checked with the MIPS va of the build map); finding **A4 / B1 (critical)**: two `JSR $1B6B6` (arcade address)
  left in the MAX code of the ending actors (Maki's and Yun's endings) now target va `0xC8304`; `prepare_max.py` stops on
  any unresolved engine address; the `prog_upper_v160` step is gone. Proofs: max55 byte for byte with the v161
  switches at 0, same 739 va modified on v160 and v161, max57 bench green (controls in `upper_max/controle/`).
- **Part B, majors**: B2 Yun `tst.b $32d(a1)` reads the wrong byte; B3 unresolved conversions did not stop the build;
  B4 table `0x615940` and B5 Arcade masks differ from the PSP; B6 seven provisional ending stages; B7 effect palettes
  cut at 30. Minors B8-B13 (rows not set, defaults without PSP reading, data read from comments, reserves not
  checked, permanent warnings); notes B14-B16.
- **Since then** (see [upper-max-arbitrations.md](upper-max-arbitrations.md)): B3 merged (commit `54d43f8`: blocking,
  26 justified exceptions); B4 / B5 / B7 prepared behind `MAX_615940_PSP`, `MAX_MASQUES_PSP`, `MAX_PALE_PLEINES`
  (default 0, to bench).
- **Still open**: B2 (one-byte fix proposed, bench trial; Yun's line still admitted in `non_resolus_admis.tsv`), bench
  of the three switches, B6 (MAX session), B8-B13; note A6: 242 bytes of margin before the data base `$A1000`.
- **Tools kept**: [`tools/reviews/upper-max/`](../../../tools/reviews/upper-max/) (review B checks + arbitration tools).

---

## Original text (French, kept as is)

> Kept as written in the workshop. Only changes: personal paths written `<workspace>/...`, workshop folders written `<workspace>/work/...`. Paths such as `outils/…`, `sorties/…`, `essais_demain/…`, `constr/…` are relative to the review's workshop folder (above); the tools kept are in `tools/reviews/` (see the summary).


<!-- source: <workspace>/work/revue_upper_max/RAPPORT.md -->

## File `<workspace>/work/revue_upper_max/RAPPORT.md`

# RAPPORT — revue_upper_max (11/11) : Upper MAX en v161, intégration sans adresse d'image en dur ; revue de l'intégration

Base v161 = candidat **a6** (`<workspace>/work/v161/fige/a6`, Upper 03c `ac053140`). Base v160 = 03c `3a9b7fd9`.
Clone : `depot/` (branche `umv161`). Constructions : `constr/` (outil `outils/um.sh`). Détail de la partie B : `revue_B/REVUE.md`.

## A. Upper MAX en v161

### A1. Ce qui bouge entre les cartes v160 et v161 a6 (`cartes_v160_v161a6.txt`, `outils/compare_cartes.py`)
- 130 975 va MIPS communes, 19 va de plus en v161 ; le décalage change 94 fois.
- Rien ne bouge avant l'image `$4C5E` (va `0x3C42C`) ; ensuite le code glisse par paliers (+16 à `$4C5E`, +142 à `$6B66`,
  +410 à `$113E8`, +576 à `$31D9A`, ≈ +600 vers `$52000`) ; fin du code d'Upper `$A0B8C` -> `$A0EB8` (+`$32C`).
- Les DONNÉES de l'image (`$A1000`-`$36FFFF`, tables `T_xxxxxx`) et les blocs externes ne bougent pas ; seuls leurs
  pointeurs vers le code changent de valeur.
- Sites que l'intégration lisait en dur (v160 -> v161 a6) : interpréteur de l'IA `$DEE6` -> `$DF74` (suite `$ED48` -> `$EDD6`,
  saut `$E432` -> `$E4C0`, aléa `$1A720` -> `$1A8BA`), saut de bloc `$F944` -> `$F9D2` (fin `$FB60` -> `$FBEE`), prises
  `$52A28 / $52AA2 / $52ABE` -> `$52C86 / $52D00 / $52D1C` (lecteur `$52A32` -> `$52C90`), dialogues `$588A6 / $5957C` ->
  `$58AF8 / $5986E`, lecteur du lancer `$525A2` -> `$52800`.

### A2. Dépendances de l'intégration aux positions (relevé complet de `integration_2b31/`)
| genre | où | état |
|---|---|---|
| adresse arcade -> va MIPS -> image | `conv/convertit_max.py` (correspondances*.tsv, carte relue à chaque préparation) | sûr ; **1 trou : `$1B6B6`** (A4) |
| va MIPS de la carte (`it.va`) | aiguillages d'acteurs / secondaires, `AIG_VA`, `hooks_fork`, agrandissement des tables | sûr |
| adresse PS2 d'une table -> `addr_to_68k` + recherche des `LEA` (compte attendu) | `agrandit_max.py`, `lea_abs`, tables par id | sûr (échec si le compte diffère) |
| motif unique dans l'image (échec si 0 ou 2) | citation, réactions 34-36, flammes, portraits, défense par victime, palette propre, COUP_NORMAL / CONTRE_DECLENCHE (`prepare_max.py`), CONV_An | sûr |
| **adresse d'image en dur** | `talon_cond40` (10 adresses), `talon_prises` (4), `talon_dialogues` (4), `lancer_vertical` (3 tables + liste morte `pat`) | **corrigé** (A3) |
| carte de la préparation = carte de la construction | `integre_max.py` (`_carte_md5`) | sûr (échec sinon) |
| tailles / réserves | code MAX `$3A0000` (+`$20000`), talons `$370000`-`$3A0000`, blocs `ext_*` | indépendant du traducteur tant que le code d'Upper finit avant les données (`$A0EB8` < `$A10F6` : 574 o de marge, contrôlée par le traducteur) |

### A3. Corrections (dans `ag/untranspile/integre_max.py`, `ag/outils/prepare_max.py`, `ag/conv/`)
- `_va_image`, `_sites`, `_site_unique`, `_cible`, `_recoupe` : un site est trouvé par motif, ses cibles par décodage des
  sauts, et chaque adresse est RECOUPÉE avec la va MIPS que la carte lui donne (échec nommé sinon).
- `talon_cond40`, `talon_dialogues` : repris de l'essai b45 de la session MAX.
- `talon_prises` : le motif « ADDI.B #$E0,D3 ; MOVEQ ; BSR lecteur » a 5 sites (3 voulus + 2 « sol avant-arrière ») ;
  les 3 voulus sont ceux des va `0x240E38` / `0x24146C` / `0x241594` (un et un seul chacun, MOVEQ attendu, même lecteur).
- `lancer_vertical` : adresses des 3 tables lues dans les `LEA` du lecteur (contrôle : contenu = EBOOT, ordre croissant).
- `prepare_max.py` : **une adresse du moteur non résolue arrête la construction** (A4).
- `um_prog.py --env VAR=VAL` (développement) ; traducteur v161 reporté dans `ag/untranspile` (`git apply` du diff de
  `src/hsfa`, 4 fichiers, sans rejet).

### A4. CONSTAT (critique, trouvé par la partie B, confirmé) : `JSR $1B6B6`, adresse arcade restée dans le code MAX
- 2 sites (image `$3B4E50`, `$3B58F2`, acteurs de fin ; le 2e est branché : sous-type `$4F/$19`, fins de Maki et de Yun).
- C'est une dépendance à la position : en v160 le saut tombe au milieu de la routine va `0xD0440` ; en v161 a6 il tombe
  ailleurs (`$1B6B6` = va `0xCFA1C`, « OR.L D0,D7 » d'une copie de longs). Aucun contrôle ne le voyait (octets identiques).
- Vraie cible : arcade `$1B6B6` = va `0xC8304` (corps comparé en entier, `<workspace>/work/v161/outils/arcdis.txt` l. 33407 contre la
  carte) = image `$19FAC` (v160) / `$1A146` (v161 a6).
- Correction : 1 ligne dans `ag/conv/correspondances_complement.tsv` -> « 122/122 adresses du moteur ». Écart mesuré :
  4 octets de `sz3.10b` (les 2 opérandes), sur v160 comme sur v161. `CONV_SANS_ADRESSES=1B6B6` redonne l'ancien code.

### A5. Preuves
- **(a) base v160 -> max55 à l'octet** : `constr/a1_v160` (avant le correctif `$1B6B6`) et `constr/b1_v160s` (code final +
  `CONV_SANS_ADRESSES=1B6B6`), interrupteurs v161 à 0 (`outils/zero.txt`) : les 8 ROM programme, les 14 `ext_*.bin` et
  `max_plus_gfx.bin` = `<workspace>/work/banc_coups/max55` (03c `bf562ec3`, 04c `d0271433`, `ext_e80000` `c9e28d68`). Avec le correctif
  (`b1_v160`) : 4 octets de `sz3.10b` seulement.
- **Équivalence mécanique v160 / v161** (`depot/tools/integration-max/upper_max/controle/`) :
  - `equiv_integration.py` (`constr/equiv_a1.txt`) : 739 va MIPS modifiées par l'intégration des deux côtés, **0 d'un seul côté** ;
    1 site aux octets différents = le JSR vers le talon de fin de code (`$A0B90` / `$A0EC0`) ;
  - `equiv_pointeurs.py` (`constr/equiv_ptr_a1.txt`) : hors code d'Upper, 28 931 + 32 (`ext_b80000`) + 639 (`ext_e80000`)
    pointeurs relogés de même va, **0 octet inexpliqué** ; 12 blocs externes et `max_plus_gfx.bin` identiques ;
  - `litteraux_figes.py` (`constr/litteraux_b1_dropsr.txt`) : plus aucune adresse absolue non relogée dans le code MAX
    (1 faux positif : `MOVE.L #$18000,D5`, une constante) ; sur l'ancien code il trouve bien les 2 `JSR $1B6B6`.
- **Essais négatifs** : `outils/essai_controles.py` (motif absent, en double, saut inattendu, va différente, adresse hors
  carte : 5 échecs nets) ; base v160 + traducteur v161 : « la carte de cette construction … n'est pas celle de la préparation ».
- **(c) `hsfa_build.py --jeux uppermax` depuis les deux ISO, dans le clone, sans étape `prog_upper_v160`**
  (`outils/iso.sh`, `constr/iso`, 5 min 20 s) : Upper 03c `ac053140` (= a6) ; Upper MAX : 23 fichiers = `constr/b1_v161`
  (03c `5e1430ee`, 04c `83de84d6`, 10b `8c255f0a`, `ext_e80000` `f5a78aa5`) ; `sfa3umhsfa.zip` md5 `2fa507af`.
- **(b) banc MAX** sur `<workspace>/work/banc_coups/max57` (= copie figée max55 + programme, blocs et carte de `b1_v161`), référence Upper
  v161 a6 (`REFS=<workspace>/work/v161/fige/a6`), 2 MAME par `lance_emu` (agent `umv161`) : **VERT** (18 h 07 - 19 h 27, `<workspace>/work/banc_coups/banc_max57.log`, `<workspace>/work/banc_coups/resultats_max/max57/`) :
  - natifs (105 TSV) : IDENTIQUE 3062 / RALENTI 61 / DIFFÉRENT 5 = les 5 Rolento X connus, mêmes lignes et mêmes causes que max55
    (max55 : 3061 / 62 / 5) ;
  - défauts MAX 0 (12 séries, 1 020 coups) ; croisés 64/64 OK ; Arcade 4/4 « fin=finie » (Eagle 42, Maki 48, Yun 47, Ingrid 42 manches) ;
  - contre les 106 TSV de max55 : 89 identiques à l'octet ; 10 TSV de coups natifs diffèrent par 18 lignes, toutes « même jeu
    tour par tour » (RALENTI qui change d'une image, dans les deux sens : cadence de v161) ; 4 TSV MAX : 4 coups dont le
    « retour » bouge d'UNE image, dégâts et effets identiques ; croisés : 2 lignes (8 / 9 manches) ; Arcade : Yun 47 (48), Ingrid 42 (40) ;
  - non fait : étape `fins` (Arcade des natifs, ≈ 3 h), `frame_data` MAX, capture des fins de Maki / Yun après le correctif `$1B6B6`
    (leur Arcade finit, l'image n'a pas été regardée).
- Cœur et empaquetage : aucune adresse d'image d'Upper MAX (le saut des boucles d'attente cherche sa signature ;
  `paquet_fbneo.py upper_max` ne lit que des fichiers).

## B. Revue de l'intégration (détail, preuves et corrections : `revue_B/REVUE.md` ; analyse statique sur la construction = max55)

| n° | gravité | constat (établi sur pièces ; effet en jeu à mesurer sauf mention) | à qui |
|---|---|---|---|
| B1 | critique | 2 `JSR $1B6B6` = adresse ARCADE laissée dans le code MAX (acteur de fin `$4F/$19`, fins de Maki / Yun) | **corrigé ici** (A4) |
| B2 | majeur | Yun : `tst.b $32d(a1)` non converti (lit l'octet image `$32D` au lieu de `$32C`, « en l'air depuis un saut » de l'adversaire) | intégration : 1 ligne de `conv/types_complement.tsv`, lot d'essai |
| B3 | majeur | les « NON RÉSOLU » de la conversion (31, puis 29 après B1) n'arrêtent pas la construction ; le rapport en annonçait 16 « voulus » | intégration : liste blanche (les adresses du moteur sont déjà bloquantes depuis A3) |
| B4 | majeur | table `0x615940` (position d'un objet lié, par id) : PSP `0x2205E8` a des valeurs pour les 4 MAX ; Upper MAX garde (-37, 84) pour Eagle / Maki et (0, 0) pour Yun / Ingrid | intégration ou session MAX |
| B5 | majeur | masques de l'Arcade : `0x61B540` (combat secret) = 0 pour les 4 MAX (PSP : 1 pour Eagle et Yun) ; `0x61B510` = 1 pour Eagle (PSP 0) | intégration ou session MAX |
| B6 | majeur | 7 décors de fin « PROVISOIRES » (`equ 0`) : Yun 1, Ingrid 6 | session MAX (donnée de `max/`) |
| B7 | majeur (effet = hypothèse) | palettes d'effets coupées à 30 sans message (`integre_max.py`, talon des effets) : 6 perdues pour Eagle / Maki / Yun, 42 pour Ingrid | intégration + session MAX |
| B8-B13 | mineur | 2e rangée de `0x620E30` non posée ; `T_61BE40[Ingrid]` = 0 (PSP `$FF`) ; ≈ 20 tables par id laissées au défaut sans relevé PSP (dont le bloc IA de 128 o : Maki = Juli / Juni) ; données relues dans des commentaires de `.s` sans contrôle de compte ; `lancer_vertical` écrit `$830` o dans une fenêtre vérifiée de `$800` ; pas de contrôle global de chevauchement des blocs externes (`$E40000` plein à 97 %) ; avertissements permanents jamais traités | voir REVUE |
| B14-B16 | note | pertes connues et gardées ; correspondance des ids PSP ↔ Upper écrite à 5 endroits ; contrôles sans défaut (prises = EBOOT, défense par victime, IA, son, 23 tables = PSP, aucun `except` large) | — |

Pour la session MAX (rien n'a été modifié dans `max/` ni `tools/max/`) :
- B6 : fournir les 7 décors de fin provisoires (`decor_fin_*.s`, Yun 1, Ingrid 6) ;
- B4 / B5 / B8 / B10 : relevés PSP à ajouter à `tables_id_max.s` (valeurs PSP dans `revue_B/compare_psp2.tsv`, tables non posées dans `revue_B/non_posees.tsv`) ;
- B1 (facultatif) : `max/outils/rosette_code/acteurs_fins.py:40` pourrait appeler `psp_1d9b0` (copie MAX de la routine) au lieu de `jsr $1b6b6.l`.

Constat propre à la partie A (note) : A6 — marge de 242 octets entre la fin du code d'Upper v161 (+ talon de sélection des
palettes, `$A0F0E`) et la base des données `$A1000` ; au-delà, `mame_test.py` recule la base de `$1000` et TOUTES les données de
l'image glissent. Exercé le 11/11 sur deux bases d'essai faites avec le traducteur v161 (`outils/base.sh`) :
`LONG_POSTINC=0` (fin du code `$A0F6A`, données en place) et `DROP_SR=0` (fin du code `$A250E`, données +`$2000`) : l'intégration
passe sans échec, modifie les mêmes 739 va, et toute différence hors code est un pointeur relogé (`constr/equiv_x_lpi.txt`,
`equiv_x_dropsr.txt`, `equiv_ptr_x_dropsr.txt` : 0 inexpliqué). Contrôle statique : ces bases n'ont pas été jouées.


<!-- source: <workspace>/work/revue_upper_max/revue_B/REVUE.md -->

## File `<workspace>/work/revue_upper_max/revue_B/REVUE.md`

# Revue de l'intégration MAX dans Upper (partie B)

Sous-agent de `revue_upper_max`, 2026-11-11. Lecture et analyse statique seulement : aucun MAME, aucune construction,
rien de modifié dans le dépôt ni dans `max/`. « Établi » = prouvé sur pièces (source, journal de la construction,
image construite, EBOOT PSP) ; l'effet en jeu reste à confirmer au banc, sauf mention contraire.

Matière :
- outils : `depot/tools/integration-max/upper_max/` (`um_prog.py`, `regen_max.py`, `integration_2b31/ag/…`, `son/`),
  `depot/max/` ;
- construction lue : `<workspace>/work/revue_upper_max/constr/t0_v160/` (= lot **max55** à l'octet : 03c `bf562ec3`, 04c `d0271433`,
  `ext_e80000.bin` `c9e28d68`) ; les constats valent donc pour max55 ;
- EBOOT PSP : `<workspace>/work/v161/construction/sortie_v161b/cache/psp/BOOT.BIN` (VA = décalage − 0x74) ; module ro5 décompressé ;
- outils écrits : `revue_B/outils/` (liste en fin de document) ; sorties : `revue_B/*.tsv`, `*.txt`.

Adresses : « image » = image 68K d'Upper (v160, banc de référence) ; « va » = 2e colonne de `carte_image.txt` ;
PS2 = adresse du module ro5 (données : image = PS2 − `0x569CC0`).

## En bref

| n° | gravité | constat | à qui |
|---|---|---|---|
| B1 | **critique** | le code MAX contient 2 `JSR $1B6B6` (adresse ARCADE non convertie) : saut au milieu d'une routine d'Upper ; un site est atteint par l'acteur de fin `$4F/$19` (fins de Maki et de Yun) | intégration (1 ligne de correspondance) |
| B2 | **majeur** | `tst.b $32d(a1)` de Yun non converti : lit l'octet image `$32D` au lieu de `$32C` (champ « en l'air depuis un saut » de l'adversaire) | intégration (1 ligne de typage) |
| B3 | **majeur** | 31 conversions « NON RÉSOLU » et 1 adresse du moteur non résolue n'arrêtent pas la construction ; le rapport en annonce 16, « toutes voulues » | intégration |
| B4 | **majeur** | table `0x615940` (position d'un objet lié, par id) : la PSP a des valeurs pour les 4 MAX, Upper MAX garde un bouche-trou (Eagle, Maki) ou (0, 0) (Yun, Ingrid) | intégration ou session MAX |
| B5 | **majeur** | masques de l'Arcade `0x61B540` / `0x61B510` : Eagle et Yun diffèrent de la PSP (mise en scène du combat secret et du combat `$13E = $A`) | intégration ou session MAX |
| B6 | **majeur** | 7 décors de fin « PROVISOIRES » (`equ 0` : « le décor affiché n'est pas le bon ») : Yun 1, Ingrid 6 | session MAX + intégration |
| B7 | **majeur** | palettes d'effets tronquées à 30 : 6 perdues pour Eagle, Maki, Yun, 42 pour Ingrid (hypothèse sur l'effet) | intégration + session MAX |
| B8 | mineur | `0x620E30`, 2e rangée non posée : 0 pour Eagle / Maki, valeur de Ryu pour Yun / Ingrid | session MAX (relevé) |
| B9 | mineur | `T_61BE40[Ingrid]` = 0 (Ryu), PSP `$FF` | intégration |
| B10 | mineur | 20 tables par id où les 4 MAX gardent la valeur par défaut sans relevé PSP (dont le bloc IA de 128 o : Maki = bloc de Juli / Juni) | session MAX (relevés) |
| B11 | mineur | données portées par des COMMENTAIRES de `.s` et relues par expressions régulières, sans contrôle de compte | intégration + session MAX |
| B12 | mineur | réserves : fenêtre libre de `$800` pour `$830` octets écrits sans contrôle ; pas de contrôle global de chevauchement des blocs externes (bloc `$E40000` plein à 97 %) | intégration |
| B13 | mineur | avertissements permanents jamais traités (« ATTENTION 60ad90 », 103 « AVERTISSEMENT ») : ils masquent les vrais | intégration |
| B14 | note | pertes connues et gardées (intros croisées, réaction 36, contres 10 / ≥ 15, musiques, cris muets, « FROM » d'Ingrid) | décision du porteur |
| B15 | note | correspondance des ids PSP ↔ Upper écrite à 5 endroits ; relogement de pointeurs par plage de valeurs | intégration |
| B16 | note | contrôles faits, rien à signaler (prises, défense par victime, rangées, IA, son, 23 tables = PSP) | — |

---

## Constats

### B1 (critique, établi) — `JSR $1B6B6` : adresse arcade laissée telle quelle dans le code MAX

- **Où** : `prep/conv/acteurs_fins_max.s:1764` (routine `acteur_1d66b0`) et `:2691` (`acteur_1d7e70`), produits par
  `max/outils/rosette_code/acteurs_fins.py:40` (« `jsr $1b6b6.l ; avance d'un pas de 8 o (PSP 0x1D9B0)` »).
  `convertit_max.py` les marque « ⚠ CONV NON RÉSOLU : appel moteur $1B6B6 : adresse arcade $1B6B6 absente des
  correspondances » et laisse l'instruction (`um_prog.log` l. 20 : « 121/122 adresses du moteur »).
- **Preuve dans l'image construite** (`outils/img.py`) : `4EB9 0001 B6B6` en `$3B4E50` et `$3B58F2` ; aucun autre saut
  à adresse littérale ne reste dans `tout.s` (`grep` des `jsr` / `jmp` à adresse littérale non convertie).
- **Où mène ce saut** : dans l'image d'Upper, `$1B6B6` est le milieu de la routine va `0xD0440`
  (`carte_image.txt` l. 23997-24024) : `BEQ` ; `MOVE.B $11(A6),D0` ; `MOVE.B T_610208(PC,D0.W),D1` (index non borné) ;
  `LEA 0(A6,D1.W),A4` ; `JSR $2DD78` ; `SUBQ.B #1,$13(A6)` ; `ADDQ.B #1,$11(A6)` ; écrit `$13(A6)` ; peut faire
  `ADDQ.B #2,$4(A6)` et remettre `$10(A6)` / `$12(A6)` à 0. Sur un acteur de fin, `$12` est le mot X et `$4` l'état.
- **La vraie cible** : arcade `$1B6B6` = `532E 0032 6622 206E 001C …` (`SUBQ.B #1,$32(A6)` ; `BNE` ; `MOVEA.L
  $1C(A6),A0` …) = image **`$19FAC`**, va **`0xC8304`** (`SUBQ.B #1,$33(A6)` ; `BEQ` ; `MOVEA.L $1C(A6),A0` …), 0x58
  avant `$1A004` = `UP_1B6EE` déjà connu. Le moteur MAX a aussi sa copie (`psp_1d9b0`, `tout.s:3913`).
- **Atteint ?** `acteur_1d7e70` est l'entrée 25 de la table `AJ_2b2aa8` de `acteur_1d6588`, que `integre_max.py:642`
  branche sur le sous-type MAX `$19` de la classe `$4F` (`ACTEURS_MAX`). Tant que `$1CA(A5)` < `$78(A6)`, l'acteur
  exécute le `JSR` à chaque image. Le commentaire de `integre_max.py:635-636` dit que ce sous-type sert aux fins de
  Maki et de Yun. `acteur_1d66b0` (sous-type natif 1 de la PSP) n'est pas branché : son site est mort.
- **Effet possible** : l'animation de l'acteur `$4F/$19` n'avance pas (image figée) et ses champs `$10-$13` / `$4`
  sont modifiés par du code étranger (position, état). Les fins « finissent » au banc de jour (35/35), ce qui ne dit
  rien de l'image. À vérifier : capture des fins de Maki et de Yun, sonde sur `pc = $1B6B6` avec `A6` = acteur `$4F`.
- **État du dossier** : `docs/rapports/INTEGRATION-MAX-UPPER.md` l. 247-248 le classait « voulu … `$1B6B6` des acteurs
  de fin = palier 3 », et l. 498 dans les « à faire ». Les paliers 3 et 4 sont branchés ; ce point est resté.
- **Correction** (intégration) : une ligne dans `ag/conv/correspondances_complement.tsv` :
  `$1B6B6 | avance d'un pas de 8 o | 0xc8304 | identique | …` ; contrôle : « 122/122 adresses », plus de `4EB9 0001 B6B6`.
  Change le code MAX : lot d'essai + fins de Maki / Yun. Côté session MAX (facultatif) : `acteurs_fins.py:40`
  pourrait appeler `psp_1d9b0`.

### B2 (majeur, établi) — Yun : `tst.b $32d(a1)` lit le mauvais octet de l'adversaire

- **Où** : `prep/conv/brouillon_yun.s:1601` (routine PSP `0x1BC300`, après `cmpi.l #1,$3c8(a6)` ; `movea.w $38(a6),a1`) :
  « ⚠ CONV NON RÉSOLU : champ objet $32D.b non typé ». L'instruction suivante est convertie (`$270` → `$271`),
  celle-ci non : elle garde le déplacement ARCADE.
- **Preuve** : `re/connaissances/champs.tsv:651` : « psp_objet +$32D, psp:+$305, **img:+$32C**, compteur moteur "en
  l'air depuis un saut" » ; `tout.s:17865` porte `tst.b $32d(a1)`. Dans l'image, `$32D` est l'octet arcade `$32C`.
- **Historique** : `max/notes/SAVOIR-MAX.md:159` (« branche jamais prise contre un natif (psp_1bc300 de Yun) : c'est
  le champ MOTEUR arcade $32D (image Upper $32C) ») : la session MAX a corrigé le CHAMP à la source, mais le
  convertisseur de l'intégration ne connaît pas son type, donc l'octet lu reste faux.
- **Effet possible** : le test « adversaire en l'air depuis un saut » de ce coup de Yun porte sur un autre octet
  (branche prise ou non au hasard de ce champ voisin). À vérifier : sonde de `$32C/$32D` de l'adversaire à ce site.
- **Correction** (intégration) : une ligne dans `ag/conv/types_complement.tsv` : `objet  $32D  1  u8  $32C  mesuré
  (champs.tsv, MAX.md R16)`. Contrôle : la ligne devient « conv : objet $32D.b u8 -> $32C ».

### B3 (majeur, établi) — les conversions non résolues n'arrêtent pas la construction

- **Où** : `ag/outils/prepare_max.py:763-764` : « conversion : %s réécrites, %s NON RÉSOLUES, %s/%s adresses du
  moteur » est un simple `print`. `convertit_max.py:950-951` laisse l'instruction d'origine avec un commentaire.
- **Mesure** (`non_resolus_t0_v160.tsv`) : **31** NON RÉSOLU, 1 adresse du moteur absente, 103 AVERTISSEMENT.
  Le rapport d'intégration (l. 247) en annonce 16, « tous voulus ». Tri des 31 :
  - 2 = B1 (`jsr $1b6b6.l`), 1 = B2 (`$32d(a1)`) : **défauts** ;
  - 10 = code mort des intros croisées (`cmpi.b #id,$102(a1)` ×5, `movea.l 0(a0,d0.w),a0` ×5, derrière le `bra`
    posé par `prepare_max.py:606-620`) ;
  - 3 = `CONTRE_DECLENCHE(a5)` (symbole résolu ensuite, `prepare_max.py:502-504`, contrôlé par un `assert`) ;
  - 15 = fonctions écrites à la main en disposition image ou invariantes (`$2a1(a6)` ×4 de `psp_cf560`, `clr.l` ×2,
    accès mot ×2, `gestionnaires_main.s` ×4, `$103(a0)`, `lea $14(a0)`, `ifnd`).
- **Risque** : toute nouvelle source de la session MAX peut ajouter un accès non typé ; il passera comme B2, sans
  bruit (les octets non convertis sont lus à l'adresse voisine).
- **Correction** (intégration) : liste blanche versionnée des non-résolus admis (fichier, texte de la ligne, raison) ;
  `prepare_max.py` échoue pour tout autre, et pour toute adresse du moteur non résolue.

### B4 (majeur, établi ; effet à vérifier) — `0x615940` : positions des 4 MAX absentes

- **Table** : `T_615940`, 42 entrées (dx, dy), lue en image `$33982` (va `0x175FF0`) par un objet dont `$36(A6)` est le
  joueur : `X = $12(joueur) ± dx`, `Y = $16(joueur) + dy` ; entrées 40 / 41 = pseudo-id de Vega (masque, griffe).
- **PSP** : homologue `0x2205E8`, entrées 0-`$25` identiques à Upper (38/38). La PSP y a INSÉRÉ les 4 MAX et repoussé
  Vega : `[$26]` (-40, 96), `[$27]` (32, 80), `[$28]` (-16, 72), `[$29]` (-18, 77), `[42]` (36, 96), `[43]` (-38, 113).
- **Upper MAX** (`ext_e80000.bin`, copie `$E80B40`) : Eagle et Maki (-37, 84) = le bouche-trou d'origine d'Upper ;
  Yun et Ingrid **(0, 0)** (`agrandit_max.py` : table « ajoutée », aucune valeur posée ; `tables_id_max.s` ne la
  contient pas).
- **Effet possible** : l'objet lié (à identifier : routine image `$3392E`, table d'états `T_615a80`) apparaît aux
  pieds de Yun / Ingrid au lieu de ~75 px plus haut, et décalé pour Eagle / Maki (Maki : 69 px en X).
- **Correction** : poser les 4 couples PSP (lecture directe de l'EBOOT `0x2205E8 + 4 × id PSP`, comme pour
  `0x2190C8`), ou les ajouter à `tables_id_max.s` (session MAX). Pas de changement pour les natifs.

### B5 (majeur, établi ; effet à vérifier) — masques de l'Arcade `0x61B540` / `0x61B510`

- **Code** : préparation du combat d'Arcade, image `$53B3C-$53BE0` (va `0x249324-0x249658`) : selon `$13E(A5)`
  (2 = combat secret, 8, `$A`), appel d'une des 3 fonctions `$53C26` / `$53BE2` / `$53C04`, qui rendent l'octet
  `[id]` de `T_61b540` / `T_61b4e0` / `T_61b510` ; non nul → `$162(A5) = $FF`. `$162(A5)` est relu en `$58D30`,
  `$58E4E`, `$59966` (`BPL` : négatif → autre enchaînement, `$C(A5) = 8`).
- **PSP** : 4 tables de **42** octets à la suite : `0x20B64C` (combat secret, déjà à l'index), `0x20B676`, `0x20B6A0`,
  `0x20B6CA`. Entrées MAX (`$26-$29`) :

  | table Upper | homologue PSP (natifs égaux) | PSP Eagle, Maki, Yun, Ingrid | Upper MAX |
  |---|---|---|---|
  | `0x61B540` (combat secret) | `0x20B676` (29/38) | 1, 0, 1, 0 | **0, 0, 0, 0** |
  | `0x61B4E0` (`$13E` = 8) | `0x20B6A0` (36/38) | 1, 1, 1, 1 | 1, 1, 1, 1 |
  | `0x61B510` (`$13E` = `$A`) | `0x20B6CA` (35/38) | 0, 1, 1, 1 | **1**, 1, 1, 1 |

  L'alignement de `0x20B676` (9 natifs retouchés sur PSP) est confirmé par la suite des 4 tables et par le sens :
  les deux MAX à 1 sont ceux qui ont un combat secret dans `0x20B64C` (Eagle `$15`, Yun `$1E`).
- **Effet possible** : mise en scène autour du combat secret d'Eagle et de Yun, et du combat `$13E = $A` d'Eagle,
  différente de la PSP (enchaînement avec ou sans la séquence sautée par `$162 < 0`). À vérifier : Arcade d'Eagle et
  de Yun jusqu'au combat secret, sonde de `$FF8162`.
- **Correction** : poser `T_61b540[$26] = [$2D] = 1` et `T_61b510[$26] = 0` (`pose()` de `integre_max.donnees`, ou
  lecture de l'EBOOT) ; natifs inchangés.

### B6 (majeur, établi) — 7 décors de fin provisoires

- **Où** : `ag/outils/fins_integration.py:260-266` : un décor de fin sans entrée dans `ND_81522` reçoit
  « `equ 0 ; PROVISOIRE : décor de fin au palier 4` » (commentaire l. 260 : « le décor affiché n'est pas le bon »).
- **Mesure** (`banc/construction.log` l. 46-47, `prep/fins_max.json`) : Yun `ND28_114` ; Ingrid `ND29_123`,
  `ND29_125`, `ND29_126`, `ND29_127`, `ND29_128`, `ND29_41`. Eagle et Maki : aucun.
- **Effet** : dans la fin de Yun (1 scène) et surtout d'Ingrid (6), un acteur de décor de classe `$48` affiche
  l'entrée 0 de `0x960180` au lieu de l'image MAX. Recoupe le piège « décor des fins » d'`AGENTS.md` (règle
  `ND<fin>_<n>` « préparée, non appliquée »).
- **Correction** : session MAX (pas `P8_xx` de ces 7 décors) puis `ND_81522` côté intégration, comme `ND26_4`.

### B7 (majeur ; troncature établie, effet = hypothèse) — palettes d'effets coupées à 30

- **Où** : `integre_max.py:1303` (`N = 0x3C0`) et `:1314` : `corps["max" + p] = d[:N]` — tout fichier plus long est
  coupé sans message ; même fonction pour les palettes du corps et d'effets.
- **Mesure** : `palettes_effets_module.bin` = 36 palettes (Eagle, Maki, Yun) et **72** (Ingrid) ; au-delà de 30, les 6
  (resp. 42) palettes sont non nulles et 3 (resp. 2) seulement existent déjà dans 0-29. Corps : Ingrid a un fichier
  `_upper` de 30 (prévu) ; il n'y a pas de `palettes_effets_module_upper.bin`.
- **Ce qui manque pour conclure** : `max/notes/max-palettes.md` §4 dit « nombre réellement utilisé par perso MAX :
  inconnu (≤ 36) ». Upper garde plus de 30 palettes d'effets pour Chun-Li (31), Sodom et Vega (37) : le moteur sait
  donc en lire davantage.
- **Effet possible** : un effet MAX qui demande une palette 30-35 (Ingrid : 30-71) lit le bloc suivant de la zone.
- **Correction** : au minimum un `assert` / message quand `len(d) > N` ; puis relevé par la session MAX des n° de
  palette d'effet réellement demandés par les objets MAX, et bloc de taille réelle (comme Sodom / Vega).

### B8 (mineur, établi ; effet = hypothèse) — `0x620E30`, 2e rangée non posée

- **Où** : `integre_max.py:337` (`rangs = (0,)`) ; lecteur image `$80100-$80112` (va `0x3552B4-0x355330`) : mot
  `[2 × id de l'ADVERSAIRE (+ $50)]` → `$6A(A6)`, rangée choisie par `JSR` (va `0x2144A0`).
- **Mesure** : rangée 0 posée (72, 58, 52, 55 = PSP `0x2947D8`) ; rangée 1 : Eagle **0**, Maki **0** (zéros d'origine
  des places `$26/$27`), Yun / Ingrid 54 (Ryu). Natifs : rangée 1 entre 43 et 79.
- **Effet possible** : `$6A` nul quand l'adversaire est Eagle ou Maki et que la 2e rangée est choisie.
- **Correction** : session MAX : relever la 2e rangée PSP (elle n'est pas à `+$50` de `0x2947D8`) ; en attendant,
  recopier la rangée 0 des MAX dans la rangée 1 vaut mieux que 0.

### B9 (mineur, établi) — `T_61BE40[Ingrid]`

`integre_max.py:413-414` pose `DECOR_MAISON` dans `T_61BE10` ET `T_61BE40`. PSP : `0x20B3A8[$29]` = 0 (accord), mais
`0x20B604[$29]` = **`$FF`** (homologue de `T_61BE40`, 35/38 natifs égaux ; Eagle 8, Maki 7, Yun 33 identiques).
Effet : dans le mode où `$C3A4(A5) ≠ 0` (va `0x441AA8`), Ingrid a le décor de Ryu au lieu du cas `$FF`. Correction :
`T_61BE40[$2E] = $FF` après avoir lu ce que fait `$FF` au lecteur (va `0x441AA8`).

### B10 (mineur, liste établie ; écarts = hypothèse) — tables restées à la valeur par défaut

`outils/non_posees.py` (sortie `non_posees.tsv`) compare, dans la copie agrandie, l'entrée de chaque MAX à la valeur
par défaut (origine d'Upper pour `$26/$27`, entrée 0 = Ryu pour `$2D/$2E`). `outils/compare_psp2.py`
(`compare_psp2.tsv`) aligne ce qu'il peut sur l'EBOOT : **23 tables sont égales à la PSP** pour les 4 MAX (jauges
`0x74C680/A8/D0/F8`, `0x697FE0`, `0x699458/80`, `0x615AC0`, `0x615CA0`, `0x616180`, `0x617290`, `0x6180F0`,
`0x61A840`, `0x61AAD0`, `0x61B680`, `0x61B6D0`, `0x61BD60`, `0x620E30` rangée 0, `0x6132E0`, `0x615790`, `0x60C680`,
`0x61B4E0`). Restent **sans homologue PSP trouvé** et à la valeur par défaut pour les 4 MAX :

| table | rôle (cartographie) | valeur des MAX |
|---|---|---|
| `0x661EF0` | IA : 128 o par perso (`$209`, `$212`, `$24B`) | Eagle = bloc commun ; **Maki = bloc de Juli / Juni** (place `$27` d'origine) ; Yun, Ingrid = bloc de Ryu (que seul `$20` partage) |
| `0x6989E0`, `0x698EE0` | moteur de coups, octet [id × 32 + aléa] | ligne (id & `$1F`) : Sodom, `$07`, `$0D`, `$0E` |
| `0x6993E0`, `0x699408`, `0x699430` | seuils comparés à la vitalité, octet du moteur de coups | Ryu |
| `0x74C3F8`, `0x74C498` | positions d'apparition d'effets par id propriétaire | pointeur de Ryu (Maki : celui de la place `$27`) |
| `0x74C720`, `0x74C748` | octet → `$159` ; octet retiré de `$2CA` | Ryu (Maki : 0 pour `0x74C720`) |
| `0x61AA30`, `0x617BE0`, `0x615380`, `0x61B650`, `0x748CA8` | divers (`$270`, routine `0x8BF10`, `$147(A5)`, demi-largeur) | Ryu |
| `0x61BBC0`, `0x61BDB0`, `0x622D10`, `0x622DB0` | enregistrements du mode Arcade, adversaire spécial, (dx, dy) selon l'id adverse | `$26/$27` : zéros ou places d'origine ; `$2D/$2E` : Ryu |

La PSP a prolongé à 42 les tables qu'on retrouve (B4, B5, B9) : il est probable qu'elle ait aussi des valeurs MAX
pour celles-ci, rangées autrement (le bloc IA de 128 o y est dédoublonné : 2 copies du bloc commun en `0x21E8A0` /
`0x21EB20`, pas de table de 40 × 128). Correction : session MAX — étendre `tables_id_max.py` à ces tables (accord
sur les natifs, puis entrées `$26-$29`) ; priorité au bloc IA de Maki et aux deux tables du moteur de coups.

### B11 (mineur, établi) — données relues dans des commentaires

- `integre_max.py:325` : les valeurs par id viennent des COMMENTAIRES de `tables_id_max.s`
  (`; 0x… (genre)[$id] = valeur (…)`) ; `:316-317` : les choix de dialogues viennent de lignes
  `; 0x61B580[(8 - 8) / 2 * 40 + $26] = 154` ; `:184`, `:213`, `:236`, `:262`, `:791`, `:840` : `dc.l` / `dc.b` relus
  par expression régulière dans 6 autres sources.
- Mesure du jour : 96 lignes « `[$xx] =` » sur 96 reconnues, 20 choix de dialogues sur 20 : rien n'est perdu
  AUJOURD'HUI. Mais un changement de forme côté session MAX retire des valeurs sans erreur : `:214` `if not m:
  continue`, `:327` (valeur « aucune »), `:332` (« probable » hors liste) ; seul un compte paraît dans le journal
  (« 100 valeurs posées »). `:1174` : `lig[r_][i_] = v_` accepte un rang négatif (dernière rangée) sans le dire.
- Correction : comptes attendus vérifiés par `assert` (par perso actif : 24 tables, 5 choix de dialogues, 4 bandeaux
  WINNER…), rang de dialogue borné à 0-2 ; à terme, un JSON à côté du `.s` (session MAX).

### B12 (mineur, établi) — réserves et débordements non contrôlés

- `integre_max.py:1453-1454` : `lancer_vertical` cherche une fenêtre libre de `$800` puis écrit `$150 + $B0 + $630` =
  **`$830`** octets (journal : `$3B8000` → `$3B8830`), par `img[a:a + n1] = …` sans `assert not any(...)` (seul talon
  dans ce cas). Aujourd'hui la suite est libre (`talon_cond40` commence en `$3B8830`).
- Les boucles `while any(img[z_:z_ + N]): z_ += 0x10` (`:1434-1494`) n'ont pas de borne : seul le `assert fin_ <=
  0x3C0000` final arrête. Marge actuelle : `$3B8C90` sur `$3C0000` (29 Ko).
- Blocs externes (construction lue) : `$E40000` (Eagle) **97 %**, `$D68000` (IA) 95 % (5 Ko libres), `$E00000` 94 %,
  `$C80000` → `$D46A50` puis portraits en `$D60000`. Chaque famille a son contrôle (`convertit_frames.py:210`,
  `prepare_max.py:856-865`, `integre_max.py:956`), mais ni `$C80000` contre `$D60000`, ni le bloc `$E80000`
  (`agrandit_max.ecrit`, aucun plafond ; 54 % de `$80000`) ; aucun contrôle global « les blocs de `ext_liste.txt`
  ne se chevauchent pas et tiennent sous `$F00000` ».
- Correction : fenêtre de `lancer_vertical` calculée (`sum` aligné) + `assert not any` ; un contrôle global des blocs
  à la fin de `integre_max.image()` (10 lignes).

### B13 (mineur, établi) — avertissements permanents

- `construction.log` l. 87 : « MAX : ATTENTION 60ad90 … AUCUN lecteur trouvé » à chaque construction (la table est
  lue par un talon natif qui ignore les id ≥ `$28` : `agrandit_max.py:42-44`) ; la pose `integre_max.py:166` pour Yun /
  Ingrid n'a donc aucun lecteur.
- 103 « AVERTISSEMENT » de la conversion, dont plus de 90 « routine modifiée par Upper » (le code MAX, traduit d'un moteur
  proche de SFA3, appelle des routines qu'Upper a changées) : aucun état « revu / admis ».
- Effet : un avertissement nouveau ne se voit pas. Correction : les faire taire par une liste d'admis datée, échouer
  sur les nouveaux (même mécanisme que B3).

### B14 (note) — pertes connues et gardées

À confirmer par le porteur comme décisions (rien n'est caché, tout est commenté dans le code) :
- **intros croisées retirées** pour les 4 MAX (`prepare_max.py:606-620` : Eagle contre `$10` / `$0B`, Maki contre
  `$0E`, Yun contre `$21`, Ingrid contre `$19`) : blocage avant le combat sinon ;
- **réaction PSP 36** : variante `$10` de `$54` ramenée à 8 (`integre_max.py:1053-1055`) ; Upper n'a que 8 variantes ;
- **contres** : types 10 et ≥ 15 → coup normal (`integre_max.py:709-727`) ;
- **musiques** : « choix provisoire » (`integre_max.py:436-438` : Eagle = Birdie, Maki = Guy, Yun = Gen, Ingrid = Rose) ;
- **cris** : rôle 4 muet pour les 4 MAX, rôle 6 muet pour Maki, Yun, Ingrid (`son/gen_son_max.py:43-48`) ;
- **Ingrid** : origine « FROM » = position de Ryu sur la carte (`integre_max.py:353`) ; attaque plongeante
  `0x623E50` = valeurs « proches » et non PSP (choix documenté, `MAX_623E50`) ;
- **provisoires encore actifs** : `move.b #impair,$9(a4)` ×3 dans les acteurs de fin (`prepare_max.py:477-483`).

### B15 (note) — fragilités de forme

- La correspondance id PSP ↔ id Upper est écrite à 5 endroits (`integre_max.py:287` `PSPID`, `:361` `MAXIDS`, `:368`
  `PSP2UP`, `:1119` `ID_PSP`, `persos_max.json` « suffixe ») : une seule table suffirait.
- `integre_max.py:55-57` et `:73-75` (bios, fichiers de fin) relogent « tout mot de 32 bits aligné dont la valeur
  tombe dans le fichier » : une donnée qui ressemble à un pointeur serait relogée. Non mesuré ; à borner par les
  tables de pointeurs connues du format.
- `integre_max.py:70` : modèle de fin sans fichier (Maki, `$07`) → « conteneur = 1er », repli muet.
- `tables_par_id.json` : `0x697FE0` déclarée 40 × 32 alors que 80 rangées existent jusqu'à `0x6989E0` ; sans effet
  (aucun autre lecteur : `defense_victime.txt`), mais les rangées `$20-$27` d'origine sont écrasées en place.

### B16 (note) — contrôles faits, rien à signaler

- **Prises** (`talon_prises`) : les 5 masques PSP relus (`0x213F68` … `0x213F80`) donnent exactement les bits posés
  (sol KK : les 4 ; air PP : Eagle, Maki ; air KK : Yun, Ingrid) ; `0x213F6E` / `74` n'ont aucun bit ≥ `$20` ;
  `0x213F86` n'est pas un 6e masque (2 octets de bourrage puis la table des joueurs `0x213F88`).
- **Défense par victime** : `0x2190C8` = `0x697FE0` sur les 38 natifs ; lignes MAX = PSP ; deux seuls sites `ANDI #$1F`.
- **Tables à rangées non déclarées** (`rangees.txt`) : 3 candidates, 3 faux positifs (autre table ou pointeurs derrière).
- **Recensement indépendant** des lectures par `$103` (`recense_id.txt`, heuristique étroite) : 41 tables vues, 2
  inconnues, toutes deux non indexées par l'id.
- **IA** : `max/outils/convert/ia_max.py` lève une erreur sur toute commande ou condition inconnue et se contrôle
  sur les 29 natifs ; le talon de la condition 40 fait bien « opérande ≥ aléa & 31 → suite ».
- **Son** : `gen_voix_max.py` / `gen_son_max.py` contrôlent chaque zone, voie et numéro par `assert`.
- **Aucun `except`** dans les outils de l'intégration ; `regen_max.py` ne lit de `mame_ro5` que des données
  graphiques (banques, plans, `ext_b04000.bin`) : indifférent à la version du traducteur (v160 / v161).

---

## Ordre de traitement proposé

1. B1 et B2 : deux lignes de TSV côté intégration, un lot d'essai, banc MAX + captures des fins de Maki / Yun.
2. B3 : liste blanche des non-résolus (empêche le retour de B1 / B2).
3. B4, B5, B9 : 9 valeurs à poser depuis l'EBOOT ; essai en Arcade (Eagle, Yun).
4. B7 (assert d'abord), B6, B8, B10 : demandes à la session MAX (`<workspace>/work/echanges/MAX.md`).

## Outils (créés, dans `revue_B/outils/`)

| outil | rôle |
|---|---|
| `img.py` | charge l'image 68K d'une construction (ROM, octets échangés), références absolues à une plage |
| `non_posees.py` | entrées MAX des tables agrandies : posées ou à la valeur par défaut (`non_posees.tsv`) |
| `compare_psp2.py` | aligne chaque table par id sur l'EBOOT (numpy : `<workspace>/venv/bin/python`) et compare les entrées MAX (`compare_psp2.tsv`) ; `compare_psp.py` = 1re version, par motifs |
| `defense_victime.py` | rangées `$20-$2F` des 3 tables de défense, table PSP `0x2190C8` |
| `rangees.py` | tables déclarées à 1 rangée dont la place vaut k × (n × e) |
| `recense_id.py` | recensement indépendant des tables lues après un `$103` |
| `ia_128.py` | cherche une table d'index PSP pour le bloc IA de 128 o (rien trouvé) |

Index : `revue_B/re_ajouts/max_psp.tsv` (5 lignes), `ro5.tsv` (4 lignes) ; aucun doublon ; `verifie.py` 0 erreur sur
une copie (`revue_B/verif_re/`).
