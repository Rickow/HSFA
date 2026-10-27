# Défauts trouvés par le banc des coups : causes et correctifs (agent_defauts_banc)

Agent `agent_defauts_banc`, 2026-10-18. Tout est dans `work/agent_defauts_banc/`. Traducteur : worktree
`untranspile/` (branche `defauts-banc` depuis `v150`, rien de commité, aucune étiquette). Références lues :
`work/references/v150`, `work/banc_coups` (copié dans `banc/`, `banc/resultats_v150` = résultats de référence).
Version finale = `b_r6/` (6 règles) : SFA3 `e0f1cfdc`, Upper `0b8ecca2`, Hyper `39985037`. Validation au §7b : bonne pour v151.

## 0. En bref

| défaut | cause | règle (interrupteur) | sites ro3 / ro5 / ro9 |
|---|---|---|---|
| 1. supers Hyper Z/Z2/A : `$A08` | TRADUCTEUR : étiquette `$01` d'un pointeur 68K effacée par un masque 24 bits | `RETAG24` | 0 / 0 / 33 |
| (1b) Evil Ryu ALPHA ne rend plus la main avec RETAG24 | TRADUCTEUR : coupure des données d'Hyper au milieu d'un bloc de perso, déplacée par la croissance du code | `COUPE_BLOCS` | 0 / 0 / coupure $8D3410 |
| 2. lancers aériens sans atterrissage | PORTAGE : bits d'options `A5+$C176` testés avant l'atterrissage arcade, à 0 sur PS2 | — | — |
| 3. Alpha Counter une image plus tard | BANC : ordre J1/J2 tiré au hasard à chaque tour, graines différentes | — (banc : `GRAINE`) | — |
| 4. Killer Bee Assault arrêté (`$16`) | TRADUCTEUR : 3 pertes dans la routine de visée | `EXG_PILE_D`, `AIDE_ROXR`, `BITOP_DN` | 19/19/5, 4/4/4, 3/4/3 |
| 5. octets de pas d'animation | DONNÉE DU MODULE PS2 (image traduite = module) | — | — |
| 6. arcs du Kikosho de Chun-Li (SFA3) | TRADUCTEUR : CMP « Dn − mémoire » perdu (symbole `dmem` vers RES seul) | `CMPDMEM` | 5 / 0 / 0 |

Tous les interrupteurs à 0 (RETAG24, EXG_PILE_D, AIDE_ROXR, BITOP_DN, COUPE_BLOCS) : ROM = v150 à l'octet
(`b_z0b/` : SFA3 `6230bba0`, Upper `36fc4f37`, Hyper `cb9b37b9`).
Construction finale `b_r5/` (5 règles) : SFA3 `3e3ff5b3f713df977d4982fcaa62d205`, Upper `0b8ecca29f27ec91ca0b7dfb8dc24cee`,
Hyper `39985037a221508180179e54e3ccd55d` (`b_r5/MD5_03c.txt`). Tous à 0 = v150 (`b_z0c`). Précédente : `b_r4/`
(SFA3 `5ec2c28a`, Upper `5d49adb4`, Hyper `9edc9f31`), avant l'extension d'EXG_PILE_D.
Règle seule (les autres à 0), `essais/seules/md5.txt` : RETAG24 → `6230bba0 / 36fc4f37 / b0344758` ;
EXG_PILE_D → `a67a7ccd / 2d4aa6ec / ba8951d8` ; AIDE_ROXR → `27ac023e / a5a20d8c / 8cbf8f22` ; BITOP_DN → `893b4d0b / 3f7f4fe5 / c1d086fb`.
Diffs : `diffs/01-retag24.patch` … `05-coupe-blocs.patch` (cumulés, s'appliquent dans l'ordre sur v150 avec `git apply`,
résultat = worktree, vérifié) ; `diffs/00-complet.patch` ; sites par module : `diffs/SITES.md`.

## 1. Défaut 1 — supers d'Hyper (versions ZERO / ZERO 2 / ALPHA) : `RETAG24`

Trace (`essais/adon_tr/tr.txt`, Adon Z Jaguar Revolver, débogueur `trace` depuis l'image 22) :
- objet fantôme du super (A6 = `$FFBF80`) : `MOVEA.L $1C(A6),A0` = `$009E0FB0` → `JSR $400` (CONV) le prend pour une
  adresse PS2 (plage `[$8D9000,$B67200)` → +`$1067000`) → `$A47FB0` : mauvaise donnée → pointeur de trame = 6 →
  `MOVE.W (A0)+,D0 ; JMP (PC,D0)` → `DIVS` / illégale → `$A0A` / `$A08` / `$A0C`.
- l'animation de J1 est un pointeur 68K ÉTIQUETÉ `$019E0FB0` (bloc externe `$940000` des données d'Hyper, animations
  SFA1 / SFA2 ; les animations ZERO 3 sont en ROM `< $400000`, d'où « ZERO 3 passe »).
- écrivain (mips fichier `0xA2E10`, img `$011DA4`) : `MOVE.L $1C(A0),(A1,D0)` puis `MOVE.B $A(A0)` dans l'OCTET FORT du
  pointeur (historique des poses `$FF0E94`, pas de 8) ; lecteur (mips `0x3246AC`, img `$07AFE2`) :
  `ANDI.L #$00FFFFFF,D1 ; MOVE.L D1,$1C(A6)`. Idiome arcade (adresses 24 bits + drapeau), qui efface l'étiquette `$01`.

Règle `RETAG24` (`translate.py` `retag_seq`, branche `mask24` ; `mame_test.py` `plages_conv` (factorisation des plages
de CONV, ROM inchangée) et `plages_retag` → `T.RETAG_FN`) : après `ANDI.L #$00FFFFFF,Dn`, si Dn tombe dans un bloc 68K
ÉTIQUETÉ par CONV (bloc externe des données quand le profil a `data_ext`, bloc du son) ET dans une plage que CONV
convertit, `ORI.L #$01000000,Dn` (drapeaux du ANDI gardés par `MOVE SR / MOVE CCR`). Plages Hyper :
`$940000-$B94000, $BA0000-$BD3F00` ; SFA3 et Upper : aucune (ROM identiques).
Limite connue : une adresse PS2 BRUTE de `[$940000,$B67200)` remasquée serait réétiquetée à tort. Sonde des 33 sites
(`lua/sonde_masque.lua`, `outils/masq.py`, Adon Z, Sagat A, Chun-Li Z2) : seuls 4 sites vus, valeurs ROM ou
`$01`+bloc externe (jamais d'adresse PS2 brute).
Résultat : banc Adon Z 6 supers KO → OK ; banc ro9 partiel (§7) : 280 variantes en exception → 0.

## 1b. Evil Ryu ALPHA et la coupure des données d'Hyper : `COUPE_BLOCS`

Sur `b_r3`, 9 variantes d'Evil Ryu A (Shoryu Ken, Tatsumaki, Messatsu Go Shoryu) OK en v150 « ne rendaient plus la main ».
Rejoué : b_base OK, b_r1 (RETAG24 seul) KO, alors qu'aucun site RETAG24 n'est atteint (sonde vide). Cause : les octets
ajoutés font passer la base des données de `$94000` à `$95000`, donc la coupure des données (`lim & ~$FFF`, profil
sans `blocs`) recule de `$8D9000` à `$8D8000` ; elle tombe dans le groupe d'Evil Ryu ZERO 2 / ALPHA
(`0x8D3410-0x8E025F`, lignes `$2B0-$2BC`) : table en image, pas visés par décalage 16 bits en bloc externe. La coupure
v150 était déjà dans ce groupe (fragile, juste chanceuse).
Règle `COUPE_BLOCS` (`mame_test.coupe`, profil ro9 `blocs_lignes` = les 3 tables de BLOC-HYPER §0) : comme Upper (§126),
coupure au début d'un groupe — plus petit pointeur des lignes d'un id, qui ne tombe dans l'intervalle d'aucun autre id —
ici `$8D3410`. Le bloc externe `ext_940000.bin` grandit de 23 536 o (2 722 544 o) : **à vérifier pour le paquet FBNeo**
(trous / taille du bloc). Evil Ryu A : OK=45 comme v150. Les deux autres « régressions » (Blanka Z3X, Birdie Z3A) et
celles vues ensuite (R. Mika Z3X, Rose Z2) passent en rejouant : aléa d'Hyper (turbo).

## 2. Défaut 2 — lancers aériens : PORTAGE (non corrigé)

- Chun-Li Ryusei Raku : fin du lancer (mips `0x48BEE0`) = aide `0x572090` = `BTST #1,$C176(A5)` ; bit 1 → atterrissage
  arcade (`JMP $02BD78`, `02000604` 4 tours), bit 0 → `Y = sol`, neutre immédiat. L'arcade sfa3ud fait l'atterrissage
  sans test. Gen (lancer aérien générique) : même test, bit 2 (aide `0x5720C0`, site `0x540800`).
- `A5+$C174-$C177` = octets d'options du portage, testés bit à bit par la famille d'aides `0x572000-0x5721B0` ; aucun
  `sb/sh` MIPS ne les écrit (code natif ?). Ils valent **0 dans les 40 captures PS2 de SFA3** (`work/etats_ps2/ee`,
  RAM `0x904170-0x90417F`) : la console n'atterrit pas non plus. Comportement du portage, pas de la traduction.
- Charlie (Flying Buster Drop ←) : autre symptôme (accroupi `02000800` un tour plus tard) = famille du défaut 3.

## 3. Défaut 3 — Alpha Counter : ARTEFACT DU BANC (non corrigé)

- La garde de proximité (`$0C`) est décidée par le code de J1 en lisant l'animation de J2 (`$02AC10…`, `$02AC98`).
- L'ordre de traitement des joueurs est TIRÉ À CHAQUE TOUR : arcade `$0277F2 JSR $01BDA6` (hasard, graine A5+`$AE`),
  `ANDI.W #$3C`, table → `(A5-$4FDC)` ; `$02776C` charge A6 = J1 ou J2. Selon l'ordre, J1 réagit au même tour que J2 ou
  au suivant.
- Les graines diffèrent entre arcade et traduction, et même entre deux arcades (avec / sans `-debug`) après le même
  chargement d'état (`essais/ack_*`). Avec `-debug`, l'arcade donne le résultat de la traduction.
- Avec `GRAINE` imposée à chaque tour (`lua/banc_trace.lua`, tap `$FF851C`) : arcade = traduction, pour deux graines
  (garde au tour 8 ou 9). Proposition pour le banc : imposer la graine dans `banc_coups.lua` (même point).

## 4. Défaut 4 — Killer Bee Assault de Cammy : TRADUCTEUR, 3 règles

Routine de visée arcade `$05DAEE` (SFA3 mips ≈ `0x4493B0`, Upper `0x4B27D0`, Hyper `0x3E7CC0`) ; traces
`essais/kbt_*`, `kbt2_tr`, comparaison par tour `essais/kb2_ref` / `kb3_tr` (GRAINE=1234) :
1. **`EXG_PILE_D`** : `tmp = D2 ; D2 = D3 ; D3 = tmp` par la pile MIPS (`sw 160(sp)`) rendu `MOVE.L D3,D2 ; MOVE.L D2,D3`.
   Règle : au `MOVE.L Dm,Dn`, si un `sw` dans les 4 suivantes écrit la case de Dm depuis un temporaire de pile qui
   contenait l'ancien Dn → `EXG Dm,Dn`, 2e écriture absorbée (comme `EXG_PILE` pour An, §126).
   **Extension (b_r5)** : le contrôle `paires_exg.py` de la session cloud (HANDOFF §171, `tools/sondes-recherche/`)
   trouvait encore 17 / 12 / 2 paires `MOVE.L Dy,Dx ; MOVE.L Dx,Dy` sur b_r4 : le temporaire peut être un REGISTRE MIPS
   (`lw s3,D0 ; lw a0,D1 ; sw a0,D0 ; sw s3,D1`, Hyper mips `0x31388C`, arcade `$5850C`). La règle accepte aussi ce cas
   (registre dont la valeur suivie est l'ancien Dn, non réécrit entre-temps). Sites : SFA3 19, Upper 19, Hyper 5.
   Après : 0 paire `.L` ; il reste une paire `MOVE.W D2,D1 ; MOVE.W D1,D2` (Upper `$037FF4`, Hyper `$08095C`), fidèle
   au MIPS (`lh v1,D2 ; sh v1,D1 ; lh v1,D1 ; sh v1,D2`, la 2e copie relit D1 : pas un EXG perdu).
2. **`AIDE_ROXR`** : aide du recompilateur `roxr` (SFA3 `0x570AA0`, Upper `0x213240`, Hyper `0x213500`) traduite comme
   une fonction ordinaire (seuls ses branchements restaient : D6 restait 0). Ajoutée à `profils.py` `aides` et à
   `aide_recomp` : `ROXR.B #n,Dn` quand a0 = case d'un registre D et a1 = constante 1-8.
3. **`BITOP_DN`** : `RES = Dn & bit ; Dn &= ~bit ; bne RES` (= `BCLR #b,Dn ; BNE`) : le `BTST` rendu au branchement lisait
   le bit déjà effacé. Règle : opération immédiate and / or / xor sur Dn avec un `btst_dn` en attente sur le même bit →
   `BCLR` / `BSET` / `BCHG #b,Dn` (Z = ancien bit).
Après les trois : états de J1 / J2 et X identiques à l'arcade tour par tour sur tout l'essai (seule la dernière ligne
manque, fin du journal).

## 5. Défaut 5 — octets de pas d'animation : DONNÉE DU MODULE PS2 (non corrigé)

`outils/anim_donnee.py` : pour chaque KO « animation différente » de ro3, pas lu dans la ROM sfa3ud, dans le module PS2
et dans l'image traduite v150 : image = module partout (hors pointeur de trame 4-7) ; module ≠ arcade :
Akuma Jigoku-guruma (octet 3), Charlie Dash VC (octet 1 : `$80`), E. Honda Hyakuretsu Harite (octet 10), Sagat
Tiger Raid (octets 0, 8, 9, 14). Chun-Li Sen'en Shu est un DÉCALÉ (pas un octet de pas).

## 5a. Kikosho de Chun-Li (SFA3) : `CMPDMEM` (trouvé par le banc des coups, mission 3)

- Arcade `$803F2` : `MOVE.L $4(A4),D0 ; ANDI.L #$FFFFFF00,D0 ; CMP.L $44(A6),D0 ; BEQ ; MOVE.B #4,$4(A6)` (l'objet
  d'effet `$FFBF00` s'éteint quand l'état de Chun-Li change). Dans ro3 (mips `0x128984`, image `$0290A8`) le `CMP.L`
  était perdu : le `subu` « D0 − mémoire » donne le symbole `dmem`, traité seulement s'il a été émis (last_sub).
- Règle `CMPDMEM` (`translate.py`, écriture de RES) : `dmem` de soustraction non émis → comparaison en attente
  `('cmp', Dn, mémoire)`, rendue au branchement (même chemin que les CMP ordinaires, longs à moitiés échangées compris).
- Sites : SFA3 5 (mips `0x89080` CMP.L (A0),D0 ; `0xA55DC` CMP.L $6A(A6),D1 ; `0x1289D4` et `0x1481D4` CMP.L $44(A6),D0
  (Kikosho et une routine d'effet sœur, arcade ≈ `$08B30C`) ; `0x35B748` CMP.L $1F8(A6),D0) ; Upper et Hyper 0 (leur
  recompilateur produit une autre forme ; Kikosho d'Upper déjà correct : objet 143 images comme l'arcade).
- Vérifié (`essais/kiko/`, `OBJLOG=FFBF00`) : objet d'effet vivant 143 images (arcade 143, v150 18, b_r6 144) ;
  Kikoken inchangé et identique à l'arcade. Upper (v150 et b_r6) : objet vivant 143 images ; Hyper Z3 : 108-109 images
  (turbo, = 143 tours) ; Kikoken d'Upper / Hyper identique v150 / b_r6.
- **MAIS les grands arcs bleus restent absents à l'écran** (image 70 du Kikosho : `essais/kiko/planche_kikosho_upper.png`,
  arcade / Upper v150 / Upper b_r6 / SFA3 b_r6) : dans SFA3 b_r6 comme dans Upper (v150 et b_r6), seules les petites
  étincelles apparaissent. CMPDMEM corrige une vraie perte (durée de vie de l'objet) mais n'est PAS la cause de
  l'absence des arcs : il reste un défaut de rendu ou de données de cet objet (sprites palettes 3/4, codes
  $5009-$5016 selon le banc des coups), commun à SFA3 et Upper. Le banc MAX avait raison pour Upper ; ma phrase
  « Upper déjà correct » ne vaut que pour la durée de vie de l'objet.

## 5b. Décors SFA3 signalés par l'utilisateur (ancien zip)

Banc MAME (`outils/decor.sh`, copie de `agent_decor_cammy/lua/decor.lua` : décor forcé par `$FF8100`, partie Arcade de
Dan ; captures aux images 60 / 150 / 300 du combat, puis toutes les 40 images sur 1 200) :
- **b) décor de Cammy (`$2C`)** : complet en v150 et b_r5 (moulin, maison, sol), comme l'arcade
  (`decors/planche_decor_2C.png`). C'était bien le défaut corrigé par `VRAM_TABLE` en v150 (site SFA3 `0x111698`) :
  l'ancien zip est antérieur à v150.
- **a) ciel du décor de Ryu (`$00`)** : pas de bande anormale en v150 ni b_r5 sur 54 captures (`planche_r5_00b.png`),
  ciel identique à l'arcade (`planche_arc_00b.png`, `cmp_ciel.png` : mêmes stries de nuages). Le balayage des 32 décors
  d'agent_decor_cammy donnait déjà `$00` complet (corrélation 0,98 / 0,93). Non reproduit au banc MAME : défaut d'un
  ancien zip ou propre au cœur FBNeo (changement de banque graphique, §146). Il faudrait une capture du zip actuel
  dans le cœur pour aller plus loin.

## 6. Découvertes annexes (non corrigées)

- Aide `sbcd` du recompilateur (SFA3 `0x570BB0`, Upper `0x213350` ; absente d'Hyper) : NON TRADUITE (talon vide, comme
  roxr) ; 4 appels (SFA3 mips `0x3FA1A4-0x3FA234`, arcade `$00A26C` : 4 × `SBCD -(A0),-(A1)`, routine système
  `$00A0AA` cas 0, sélecteur `($10,A5)`, nombre BCD de 4 octets `$13C/$138(A6)`). Aucun coup du banc ni aucune fin des
  balayages n'en dépend (fins = arcade) : non corrigée, conformément à la consigne. À traiter comme `abcd` le jour où un
  écran l'utilise.
- Birdie Murderer Chain (Hyper Z2 / A) « ne rend pas le contrôle » (`02000e0c`) : déjà en v150, non étudié.

## 7. Validation (construction `b_r4`)

- Interrupteurs : tous à 0 → v150 à l'octet ×3 (`b_z0b`) ; chaque règle seule : `essais/seules/md5.txt`.
- Non-régression SFA3 (`b_r3`, ROM identique à b_r4) : 3 × aucune exception (20 000 / 20 000 / 60 000 images),
  42 actions / 0 différente, 5 358 tours en 4 019 images (133,3 %), comme v150 (contrôle `essais/cmd_base`).
- Upper (`b_r3` = b_r4) : aucune exception sur 20 000 images ; persos 00 / 04 / 02 : 28 / 25 / 34 manches, `fin=finie`.
- VERSUS d'Hyper, balayages SFA3 (32) et Upper (40) sur b_r4 : voir §7b.
- Banc (tous persos, `essais/bilan_ro{3,5,9}.txt`, `outils/bilan.py`, contre `banc/resultats_v150`) :
  - ro9 : variantes OK 3 842 → 4 158, KO 348 → 32, exceptions 316 → **0**, régressions 0 (après rejeu des aléas) ;
    taux par coup 92,3 % → **98,9 %** ; KO restants : Murderer Chain de Birdie, Chohatsu Densetsu de Dan… (déjà en v150) ;
  - ro3 : OK 2 382 → 2 393, KO 63 → 60, DÉCALÉ 20 → 12, régressions 0 ; Killer Bee Assault OK (sans graine imposée) ;
  - ro5 : OK 2 105 → 2 119, KO 258 → 255, DÉCALÉ 121 → 110, régressions 0 ; Killer Bee Assault OK.

## 7a. Paquet FBNeo d'Hyper (COUPE_BLOCS : bloc externe +23 Ko)

`paquet_fbneo.image_ext` (dépôt, appelé sur `b_r6/ro9`, `HSFA_STRICT=1` et `0`, plage d'Hyper `$940000-$EFFFFF` de
5,75 Mo) : blocs `$940000` (2 722 544 o, fin `$BD8AF0`) et `$C84000` (553 352 o), aucun débordement ni chevauchement ;
image `hsfa_ext.bin` de 6 029 312 o, taille fixe attendue par `d_cps2.cpp` inchangée.

## 7b. Validation finale

**b_r4** (avant l'extension d'EXG_PILE_D ; `validations/b_r4_20261018-2028/`, `essais/valide_r4.log`) :
- VERSUS d'Hyper : 1 sélection, 2 manches, pas d'exception ;
- balayage SFA3 : 32 / 32 `fin=finie`, captures = arcade ±1 (aucun « ECART ») ;
- balayage Upper : 40 / 40 `fin=finie` (aucun « ECART ») ;
- bancs : voir §7 (0 régression, Hyper 98,9 %).

**b_r6** (FINALE, 6 règles ; `validations/b_r6_20261024-1713/`, `essais/valide_r6.log`, `essais/bilan_ro*_r6.txt`) :
- non-régression SFA3 : 3 × aucune exception, 42 actions / 0 différente, 5 358 tours / 4 019 images (= v150) ;
- Upper : aucune exception ; persos 04 / 00 / 02 : 26 / 28 / 34 manches, `fin=finie` ; VERSUS d'Hyper : 2 manches ;
- balayages : SFA3 32 / 32 (captures = arcade ±1), Upper 40 / 40 `fin=finie`, aucun « ECART » ;
- bancs contre v150 (travaux interrompus par la pause rejoués) : **0 régression** sur les trois modules ;
  ro9 OK 3 842 → 4 158, KO 348 → 32, exceptions 316 → 0 (taux par coup 98,9 %) ; ro3 OK 2 382 → 2 393, KO 63 → 59,
  DÉCALÉ 20 → 13 ; ro5 OK 2 105 → 2 119, KO 258 → 257, DÉCALÉ 121 → 108. Killer Bee Assault : 60 = arcade.
- `paires_exg.py` : 0 paire `.L` ; tous les interrupteurs à 0 : v150 ×3 (`b_z0d`) ; paquet FBNeo d'Hyper : §7a.

**Verdict : b_r6 = v151, OUI.** Restes connus, hors v151 : arcs du Kikosho (SFA3 et Upper, cause de rendu à
chercher), aide `sbcd` non traduite, lancers aériens (portage), Alpha Counter (banc).

## 8. Fichiers

- `untranspile/` (worktree, règles), `diffs/`, `outils/{construit.sh,valide.sh,lance.sh,masq.py,anim_donnee.py,arbres_regles.py}`,
  `lua/{banc_trace.lua,sonde_masque.lua}` (trace TRF/TR0/TRSTOP, TAPLOG, GRAINE), `banc/` (copie du banc),
  `b_base`, `b_z0c`, `b_r1`, `b_r3`, `b_r4`, `b_r5` (constructions), `decors/` (captures), `essais/`, `validations/`, `re_ajouts/` (15 lignes).
