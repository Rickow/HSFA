# Hyper SFA (`ro9`) : jauge de super qui « disparaît » (VERSUS, J2 S-ISM) et exception en TRAINING

Agent `agent_hyper_defauts`, 2026-10-10. Tout est dans `<workspace>/work/agent_hyper_defauts/`. Aucun fichier partagé
modifié : le traducteur corrigé est une **copie** (`untranspile/`) ; `src/hsfa/translate.py` est inchangé
(md5 `b0e2d2e0…` avant et après). MAME : `nice -n 19`, `-nvram_directory`/`-cfg_directory`/`-snapshot_directory`
propres (`essais/{nv,cfg,snap}_<nom>`), jamais `-state`, au plus 4 instances à la fois.

## 0. En bref

**Les deux défauts ont une seule et même cause** : le **plafond de la jauge de super** est perdu dans la traduction.

- Le code d'Hyper (mips `0x2DDF3C`) fait `D8 = $90` (ou `$30` en AUTO) puis `CMP.W $11E(A6),D8 ; BCC ; MOVE.W D8,$11E(A6)`.
- D8 n'existe pas en 68K : il est servi par son **domicile `$87F0(A5)`**. La comparaison devient donc
  **mémoire contre mémoire**. Aucune forme 68K ne le permet : `enc_cmp` rendait `None`, et l'appelant n'émettait
  **rien, sans trace** (ni chute, ni `audit_exacts.txt`). Le `BCC` relisait des drapeaux périmés.
- Conséquence : la jauge **dépasse `$90`** (jusqu'à `$A6`, `$EC`… en TRAINING, où elle se recharge toute seule).
- Les routines d'affichage lisent des tables indexées par la jauge. Au-delà de `$90`, elles lisent hors table :
  - **Défaut 1** : la barre S-ISM affiche un carré orange puis plus rien. On voit aussi « LV 7/8/E » en ZERO, une
    barre pointillée en A-ISM et un niveau « 9 » en ALPHA2G.
  - **Défaut 2** : dans la routine de jauge ZERO, `MOVEA.L $0B0100(A0,D0.W)` lit `$00010000`, d'où `A0 = 1`, puis
    `MOVE.W (A0)+,D2` déclenche une **erreur d'adresse**. Le « PC empilé = `$000001` » du rapport FBNEO-HYPER est en
    réalité l'**adresse fautive** du cadre d'erreur d'adresse : il n'y a pas eu de saut à 1.

**Correctif** : nouvelle règle **`CMPMM`** (défaut 1, `CMPMM=0` = ancien comportement). Une comparaison mémoire contre
mémoire passe par un temporaire D0 sauvé sur la pile, puis `MOVEM` (qui ne touche pas aux drapeaux) :
`MOVE.L D0,-(SP) ; MOVE.W $87F0(A5),D0 ; CMP.W $11E(A6),D0 ; MOVEM.L (SP)+,D0`.

| | sites |
|---|---|
| Hyper | 3, dont les 2 plafonds de jauge |
| SFA3 | 1 |
| Upper | 3 |

**Vérifié à l'image** :
- la jauge reste à `$90` et affiche « SUPER / CHARGE OK » des deux côtés ;
- le TRAINING tient 20 000 images sans exception (il plantait à l'image 2945) ;
- la tournée VERSUS de 13 000 images donne 7 sélections et 12 manches, avec les mêmes choix. Les seules différences
  à l'image sont les jauges du bas, qui sont maintenant correctes.

Les différences SFA3 et Upper sont expliquées au §5. Deux d'entre elles sont vérifiées à l'image dans Upper, et ce
sont des **corrections** :
- **SURVIVAL** : le décor de la dernière étape ;
- **DRAMATIC BATTLE** : la couleur du boss.

**En plus** (§6), le recensement de **toutes** les comparaisons que le traducteur n'émet pas trouve une 2ᵉ famille de
pertes. Une lecture mémoire rangée sur la pile MIPS y est prise pour la constante de base `lui 0x7000`.
- Effets :
  - Hyper : 23 CMP perdus et 4 `CMPI #0` faux, dont `CMPI.W #$90,$11E(A6)` et `CMPI.W #$90,$50(A0)` ;
  - Upper : 10 ;
  - SFA3 : 0.
- Règle d'essai **`CMPX`**, **désactivée par défaut** (non validée, à décider).

## 1. Reproduction (fork `sfa3hx`, ROM actuelle `69b2ac41…`)

Outils (dans le dossier) :
- `lance.sh <nom> [dossier ROM]` : Hyper au fork. Modèle `agent_hyper_etats/lance.sh` ; ROM `b9_base` = reconstruction
  de contrôle, identique octet pour octet à `work/mame_ro9`.
- `lua/partie.lua` : copie de `tournee_hyper.lua`, avec en plus un mode **`SUPERJ=1|2`**. En combat, ce mode :
  - ne force plus de K.O. et maintient les deux vies ;
  - force la jauge `$11E` du joueur à `JAUGE` jusqu'à `JFIN` ;
  - écrit la jauge une fois avec `JSET="r:val"` ;
  - injecte les manipulations `SACTS="r:qcfqcf:1,…"`, de la même façon que `agent_coups/coups.lua`, pour J1 ou J2 ;
  - prend les captures `SNAPREL` et écrit le journal par image `LOGREL`/`WLOG`.
- `d1.sh <nom> <LISTE> <SUPERJ> [ROM]` : scénario du défaut 1 :
  - super à r=520 avec la jauge forcée à `$90` ;
  - boules de feu ;
  - jauge écrite à `$80` à r=690, puis remontée par les coups ;
  - 2ᵉ super à r=1000 ;
  - boules de feu.
- `lua/sonde.lua` : journal des écritures (PC, valeur) sur des plages. `lua/trace.lua` : trace du débogueur
  (`-debug -debugger none`) à partir d'une image. `lua/couv.lua` : points d'arrêt compteurs, lus dans le journal de
  la console du débogueur. `lua/vie.lua` : journal des vies et de variables, écritures forcées (`WRK`).

**Défaut 1** : Ken ZERO contre Ryu ZERO 3 en curseur 4 (`$123 = $80`, S-ISM rouge), joueur 2 (`essais/v_z.log`).
- Avant la super, la jauge forcée à `$90` affiche « SUPER / CHARGE OK » ;
- la super part, la jauge passe à 0, puis remonte avec les coups : `$80`, `$84`, `$89`, `$8D`, puis **`$92`, `$96`,
  `$9A`, `$9B`**, sans s'arrêter à `$90`.
- La sonde montre un seul écrivain, 68K `$0709CA` `ADD.W D0,$011E(A6)` (mips `0x2DDE20`), et aucune écriture du
  plafond.
- **Dès `$91`**, la barre S-ISM de J2 montre un petit carré orange, un trait blanc et un fond brun, puis plus rien
  d'utile : c'est le symptôme console.
- La même chose arrive côté J1 (`d1_j1m4`), et aux autres affichages :
  - Ken ZERO affiche « LV 7 / 8 / E » au lieu de 3 ;
  - Ken A-ISM affiche une barre pointillée ;
  - ALPHA2G affiche le niveau « 9 ».
- Hyper recharge aussi la jauge d'elle-même (`0x2A65B4`, `BTST #0,$81(A5)`, +1 par image). Dans une partie normale,
  sans rien forcer, la jauge déborde donc vite. La tournée de référence le montre (`planches/tournee_hud_avant_apres.png`,
  rangées 3-4 : J2 S-ISM rouge, exactement le symptôme décrit).
- J2 est plus touché dans le cas de l'utilisateur, sans doute à cause de son style de jeu. Les deux côtés sont
  atteints.

**Défaut 2** : TRAINING, `LISTE="00.Z3/01.Z" MODEJEU=4`.
- Exception reproduite à l'**image 2945**, à l'identique, avec ou sans débogueur (`essais/tr_base.log`, `tr_dbg`).
- La sonde de `$FF891E` (`essais/tr_sonde.log.sonde`) donne la jauge du mannequin (Ken ZERO) : `$9F`, `$A0`… jusqu'à
  **`$A6` à l'image 2944**. Celle de J1 est à `$EC`.
- Trace (`essais/tr.trace`, fin) de la routine de jauge des versions anciennes (mips `0x3B87D4`, 68K `$09297E`) :

```
09297E ext.w D0            ; D0 = octet lu dans la table A3[jauge] = $62 (hors table pour jauge > $90)
092986 lsl.w #2,D0         ; $188
092988 lea   $0B0100,A0
0929AE movea.l (A0,D0.w),A0   ; long $00010000 (au-dela de la table de pointeurs)
0929B2..BA swap/exg       ; remise en ordre du long -> A0 = $000001 ; JSR $400 (conversion : < $5AF140, inchangee)
0929D0 move.w (A0)+,D2     ; lecture d'un mot a l'adresse IMPAIRE 1 -> erreur d'adresse -> vecteur $A06 (BRA *)
```

## 2. Cause dans le traducteur

MIPS (`show.py 2ddf3c`, avant le correctif) :

```
02ddecc  addiu a0,zero,0x90 ; sh a0,0x1144(ctx)    MOVE.W #$90,$87f0(A5)      (D8 a domicile)
02ddf04  lb 280(A6) ; beq                          TST.B $0119(A6) ; BEQ
02ddf0c  addiu a0,zero,0x30 ; sh a0,0x1144(ctx)    MOVE.W #$30,$87f0(A5)
02ddf20  lh v1,286(A6) ; ext16 -> t0               (rien)
02ddf30  lh v1,0x1144(ctx) ; ext16 -> a2           (rien)     D8, reecrit en lh $87F0(A5)
02ddf3c  subu v1,a2,t0 ; calcul C/V exact ...      (rien)     <- CMP.W $11E(A6),D8 PERDU
02ddfe8  bgez C                                    BCC
02de000  sh a0,286(A6)                             MOVE.W $87f0(A5),$011e(A6)
```

- `exact_flags` reconnaît bien le bloc de soustraction. Les deux opérandes sont connus :
  - `dst = ('mem','W',$87F0,5)` ;
  - `src = ('mem','W',$11E,6)`.
- `pend = ('cmp', …)` est donc posé, et `EXACT_MISS` reste vide.
- Au branchement, `r = enc_cmp(...)` rend `None` pour mémoire contre mémoire, et `if r: out.append(...)` n'émet rien.
- Outil de recensement : `outils/cmp_perdus.py VA0 VA1` et `outils/cmp_perdus_tout.py` (tout le module) listent les
  `enc_cmp → None`. Avant correctif, toutes les comparaisons mémoire contre mémoire concernent le domicile de D8.

Homologues : SFA3 `$027C0E` et Upper `$0310D6` emploient `CMPI.W #$90,$011E(A6) ; BCS ; MOVE.W #$90` (constante,
traduit correctement). Hyper a remplacé la constante par un maximum variable (AUTO : `$30`) tenu en D8.

## 3. Correctif (`correctif_translate.diff`, `correctif_mame_test.diff`)

Dans `enc_cmp`, avant les autres formes :

```python
if CMPMM and dst[0]=='mem' and src[0]=='mem' and dst[3]!=7 and src[3]!=7:
    CMPMM_N.append((size,dst,src))
    if size=='L' and MEMMODE=='cps2':   # longs a moities echangees : valeurs reelles par SWAP
        return [0x48e7,0xc000, 0x2028|dst_an,dst_d, 0x4840, 0x2228|src_an,src_d, 0x4841, 0xb081, 0x4cdf,0x0003], ...
    return [0x2f00, MOVE.x d(An),D0, CMP.x d(Am),D0, 0x4cdf,0x0001], "CMP.x src,dst  [memoire-memoire, par D0 sauve]"
```

Cette forme couvre les deux appelants de `enc_cmp` : le branchement en ligne et les drapeaux rendus à l'appelant.
- Interrupteur : `CMPMM=0`, qui redonne exactement les ROM actuelles (contrôle : SFA3 `f2f46b7e…`, Upper `0485973b…`,
  Hyper `69b2ac41…`) ;
- compteur imprimé par `mame_test.py` : « comparaisons memoire-memoire par un temporaire ».
- Pour appliquer : `patch -d <workspace>/scripts/untranspile < correctif_translate.diff`, de même pour
  `correctif_mame_test.diff`. Le diff contient aussi l'essai `CMPX` du §6, **désactivé par défaut** : sans lui, les ROM
  sont identiques à `CMPMM` seul (vérifié par md5).

ROM produites (`b9_new`, `b3_new`, `b5_new`, `non resolus 0`) :

| module | `sz3ud.03c` | sites |
|---|---|---|
| Hyper | `1996ece943d251253339b54bedcafce1` | 3 |
| SFA3 | `568cef19769e97eca1983fc034384e60` | 1 |
| Upper | `a296538feff3d9a5317b1609bfb594c0` | 3 |

## 4. Vérification (Hyper)

| essai | ROM actuelle | ROM corrigée |
|---|---|---|
| Défaut 1, J2 S-ISM rouge (`v_z` / `n_z`) | jauge `$92-$9B`, barre en morceaux puis vide | jauge plafonnée à **`$90`**, « SUPER / CHARGE OK » qui clignote ; 2ᵉ super ; recharge normale (`planches/defaut1_jauge_j2.png`) |
| Même scène côté J1 (`d1_j1m4` / `n_j1`) | même débordement | plafonnée, identique en miroir |
| J1 ZERO / ALPHA / S-ISM rouge contre J2 S-ISM rouge (`v_z`, `v_a`, `v_m4`) | débordement des deux côtés | — |
| TRAINING Ryu Z3 / Ken ZERO, 20 000 images (`v_tr_base` / `v_tr_new`) | **EXCEPTION image 2945** | **FIN 20000**, aucune exception |
| Tournée VERSUS FBNEO-HYPER (13 000 images, `CONTOURNE_E=1`) | 7 sélections, 12 manches | **mêmes 14 choix**, 7 sélections, 12 manches, aucune exception. Captures : 14 sur 19 identiques ; les 5 autres ne diffèrent que dans les jauges du bas (`planches/tournee_hud_avant_apres.png`) |
| VERSUS de `valide_tout.sh` (20 000 images) | 2 manches, écran RESULT | idem |

Note sur le cas S-ISM bleu et vert (curseurs 5 et 6) : ils empruntent la même routine d'ajout. Leur jauge débordait
de la même façon, d'où le symptôme dans la tournée (`01.Z3.m5`), et elle est corrigée de la même façon.

## 5. SFA3 et Upper : chaque différence

Hors décalage d'adresses, la carte de SFA3 ne diffère que par **une** instruction, et celle d'Upper par **trois**
(diff de `carte_image.txt` avec `CMPMM=0`).

| module | va mips (68K) | code | avant | vérification |
|---|---|---|---|---|
| SFA3 `0x20A884` (`$04E7EE`) / Upper `0x26DA38` (`$059474`) | recharge des vies en tête de manche, partie ajoutée par le portage pour la 3ᵉ structure quand `$C19D(A5)` est posé (code du DRAMATIC). La partie J1 est l'homologue exact de l'arcade `$A2C6` `cmp.w ($50,A6),D6 ; beq` | `CMP.W $50(A4),D8 ; BEQ` | `BEQ` sur des drapeaux périmés (`TST.W $50(A4)`) : la recharge ne s'arrête pas au maximum, ou s'arrête tout de suite | **non atteint** : arcade 1 joueur, DRAMATIC (3 matchs), ni la routine arcade `$A2BE` dans une partie arcade (compteurs du débogueur, `essais/cv3*.couv`, `cvref.couv`). La sémantique est celle de l'arcade |
| Upper `0x24F6FC` (`$054C7C`) | choix du décor de l'étape suivante : arcade `$B82C` `tst.b $14b(A0) ; beq ; cmpi.w #$1a,$114(A5) ; bne ; move.w #$14,$174(A5)`. Upper compare avec `$14D(A5)` (nombre d'étapes, `$20`) | `CMP.B D8,$115(A5) ; BNE` | `BNE` toujours pris : décor `$14` jamais imposé | **SURVIVAL** (`$14A = $FF`, J1 forcé à « tout battu ») : dernière étape `$114 = $20`, décor **`$00` → `$14`**, comme dans la logique de l'arcade (`planches/upper_survival_derniere_etape.png`) |
| Upper `0x27342C` (`$05A44C`) | DRAMATIC : si J1 et J2 ont le même perso, couleur du boss `$D29 = T_61C420[$529×8 + $929]` | `CMP.B $903(A5),D8 ; BNE` | drapeaux de `MOVE.B $503,D7` : le `BNE` dépendait de l'id de J1 = 0. Avec Ryu + Ken (ids différents), le boss Adon était recoloré | DRAMATIC Ryu + Ken : avant `$D29 = 1` (Adon orange), après `$D29 = 0` (couleur par défaut), conforme au MIPS (`planches/upper_dramatic_couleur.png`) |

Hyper, 3ᵉ site : `0x5186C` (`$0075EC`), `CMP.W $50(A6),D8 ; BCS`, seuil de vie 48 ou 40 (code de l'IA).
`0x2A6930` (`$0695D2`), `CMP.W $11E(A6),D8 ; BNE ; JSR 0x388390` : effet « jauge pleine » de la recharge
automatique.

**Non-régression faite** (dossiers `b3_new`, `b5_new`) :
- SFA3, `commandes.lua` : **42 actions, 0 différente**, 5 359 tours en 4 019 images (133,3 %) ;
- Upper, les 3 parties Arcade de `nonreg_ro5.sh` (Ryu 28 manches, Chun-Li 23, Akuma 33) : **toutes `fin=finie`**.

**Non fait** :
- `diag.py` (il écrit dans `work/mame`) ;
- les balayages des fins (`balayage_fins.sh`, environ 3 h). Ils sont à lancer au moment d'appliquer le correctif aux
  dossiers partagés (leçon du §137).

## 6. Autre famille trouvée : lecture mémoire rangée sur la pile prise pour `lui 0x7000` (essai `CMPX`, défaut 0)

`cmp_perdus_tout.py` recense ce que `enc_cmp` refuse **encore** après `CMPMM` :

| module | CMP refusés |
|---|---|
| SFA3 | 0 |
| Upper | 10 |
| Hyper | 23 |

Presque tous ont pour minuende `('imm', $70000000)` :
- dans le code « non optimisé » d'Hyper, `lh a0,80(a1) ; dsll32/dsra32 v1 ; sw v1,212(sp)` range une **lecture
  mémoire** sur la pile ;
- `v1` porte encore l'ancien `lui v1,0x7000` (base du contexte) ;
- la branche « constante rangée sur la pile » (§126) le prend pour la constante `$70000000`, avant la lecture mémoire.

Le CMP est alors perdu, ou devient un faux `CMPI #0`, la constante tronquée. 4 sites d'Hyper sont dans ce cas, par
exemple `0x35690` `CMPI.B #$0,D0` au lieu de `CMP.B $6(A6),D0`. S'y ajoutent 4 `CMP.x Dn,mem` (minuende en mémoire
contre un registre), qui n'ont pas de forme 68K.

Essai `CMPX=1` :
- la constante de pile n'est pas prise si le registre porte une lecture mémoire ;
- `CMP Dn,mem` passe par un temporaire.

Résultat : 0 refus dans les trois modules, et SFA3 est **identique à l'octet**. Sites (`cmpx_sites_ro9.txt`,
`cmpx_sites_ro5.txt`), par exemple :
- Hyper : `CMPI.W #$90,$50(A0)` (vie pleine ?), `CMPI.W #$90/#$30/#$48,$11E(A6)` (seuils de jauge),
  `CMPI.B #$2,$239(A6)` ×4, `CMPI.B #$7,$C201(A5)` ;
- Upper : `CMPI.W #$90,$11E(A6)` (`0xBE014`), `CMPI.W #$1D00,$12(A3)`, `CMP.W D0,$12(A6)` ×2 (`0x41570C`).

Contrôle léger : la tournée VERSUS d'Hyper avec `CMPX=1` (`t_tour_x`) donne un journal et 19 captures **identiques**
à `CMPMM` seul. **Pas validé plus loin** (Upper : 10 sites à expliquer). Je recommande d'en faire un chantier : ce sont
des tests de jauge et de vie du code ajouté d'Hyper.

## 7. Fichiers

- `untranspile/` : copie du traducteur avec `CMPMM` (et `CMPX` en essai) ; `translate.py.avant`,
  `mame_test.py.avant` ; `correctif_translate.diff` (49 lignes), `correctif_mame_test.diff` ;
- ROM : `b9_base` (contrôle = ROM actuelle) ; `b9_old`, `b3_old`, `b5_old` (`CMPMM=0` = ROM actuelles) ; `b9_new`,
  `b3_new`, `b5_new` (corrigées) ; `b9_x`, `b5_x`, `b3_x` (essai `CMPX`) ;
- scripts : `lance.sh`, `d1.sh`, `sfa3.sh`, `sfa3d.sh`, `upper.sh`, `valide.sh` ; `lua/partie.lua`, `sonde.lua`,
  `trace.lua`, `couv.lua`, `vie.lua` ; `outils/planche.py`, `cmp_perdus.py`, `cmp_perdus_tout.py`
  (`cmp_perdus_ro*.txt`, `cmpx_perdus_ro*.txt`) ;
- planches :
  - `planches/defaut1_jauge_j2.png` (avant/après, bas de l'écran, r = 860…1220) ;
  - `planches/tournee_hud_avant_apres.png` ;
  - `planches/defaut2_exception_training.png` (image de l'exception) ;
  - `planches/upper_survival_derniere_etape.png` ;
  - `planches/upper_dramatic_couleur.png` ;
- essais : `essais/*.log` (journaux), `essais/tr.trace` (trace de l'exception), `essais/valide.txt` (non-régression).
