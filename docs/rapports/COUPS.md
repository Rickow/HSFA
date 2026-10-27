# Coups défectueux : boules de Sakura à « 42 coups », super boule d'Akuma qui ne part pas

Agent `agent_coups`, 2026-10-10. Tout est dans `<workspace>/work/agent_coups/`. Aucun fichier partagé n'a été modifié.
Le traducteur corrigé est une **copie** : `agent_coups/untranspile/`.

## 0. En bref

Il y a deux pertes distinctes dans le traducteur. Les deux touchent SFA3, Upper et Hyper.

| défaut | cause dans la traduction | règle (interrupteur) |
|---|---|---|
| Super boule d'Akuma (Messatsu Gou Hadou, **hcb hcb + P**) : le flash a lieu, la boule ne part pas | `BEQ rts` devenu `BEQ JMP $2BAF2` : un saut terminal absorbé, qui était aussi la cible d'un branchement, n'a rien émis. Le branchement tombait sur l'instruction suivante. | `TAILBR` (`=0` : ancien) |
| Boules de Sakura à 20-40 coups (**Upper**) ; Soul Spark de Rose à ~20 coups (**SFA3 et Upper**) | `MOVE.L #$800000,D1 ; BTST D0,D1` (types d'objets sans décompte de touche) : la constante `lui` seule a été prise pour une adresse PS2 et convertie en `$3103C0` (SFA3) ou `$296340` (Upper). | `LUIDN` (`=0` : ancien) |

Ces deux règles ont aussi corrigé la **super boule de Dan** (Shinkuu Gadoken), cassée de la même façon que celle d'Akuma, ainsi
que d'autres sites listés au §4.

## 1. Reproduction (MAME, entrées scriptées identiques)

Outils, tous dans `agent_coups/` :
- `coups.lua` : partie VERSUS à deux joueurs. J1 = `PERSO`, J2 = `PERSO2`, passif. La jauge de J1 est forcée (`$11E = $90`)
  et ses vies sont maintenues. J2 est repositionné 30 images avant chaque action (`DIST`) et sa vie est remise à `$90`
  toutes les 150 images. Les manipulations sont données dans `ACTS="r:manip:bouton,..."` (`qcf`, `qcfqcf`, `hcbhcb`,
  `hcf`, `chdu`…), et `MASH` sert pour le martèlement. Le journal contient, par image, l'état des joueurs, la vie de J2,
  les compteurs de combo (J1 `$329`, J2 `$5E`, trouvés par différence de RAM) et le vidage brut des objets actifs des
  réservoirs `$FF9400` / `$FFA000` (12 × `$100`). Options : `SNAPREL`, `DUMPAT` (RAM brute) et `PTRAT` (données d'animation).
- `run.sh NOM ref|tr140|up140|<dossier>` : lance l'arcade (`roms/`, `REF=1`), SFA3 traduit (`mame sfa3ud`) ou Upper
  (`cps2f sfa3hx`, avec les options de `nonreg_ro5.sh`). Les `-nvram/-cfg_directory` sont propres à chaque lancement.
- `resume.py log` donne, par action, les coups (baisses de vie de J2), le combo maximal et les objets.
  `obj.py log ref|tr [champs]` donne les champs des objets image par image.
- `sonde.lua` : `coups.lua` plus un journal des écritures (PC) sur des plages (`SONDE_ADR`, `SONDE_R0/R1`).
- `conv_dn.py` : recensement grossier des constantes converties.

Les ROM testées sont des copies figées des ROM actuelles (§140) : `tr140/` (SFA3) et `up140/` (Upper). Une reconstruction
de contrôle avec le traducteur copié et les deux règles coupées (`b3_old`, `b5_old`) redonne ces ROM **octet pour octet**.
Les défauts sont donc antérieurs au §140 : la ROM du §138 testée sur console les avait aussi.

Ids : Akuma `$02`, Dan `$0C`, Sakura `$0D`, Rose `$09`. Mesures avec J2 = Ryu, ism A, distance `$50`/`$60` :

| coup | arcade | SFA3 §140 | Upper §140 | SFA3 corrigé | Upper corrigé |
|---|---|---|---|---|---|
| Akuma hcb hcb + LP (niv. 1) | objet `$0206`, **4** coups | **pas d'objet**, 0 | pas d'objet, 0 | 4 | 4 |
| Akuma hcb hcb + HP (niv. 3) | 8 coups | 0 | 0 | 8 | 8 (combo 8) |
| Dan qcf qcf + LP / HP | 3 / 5 coups | **0 / 0** | — | 3 / 5 | — |
| Sakura qcf qcf + LP / HP (Shinku Hadoken) | 3 / 5 | 3 / 5 | **26 / 24+ (combo 27, 13 HIT à l'écran)** | 3 / 5 | 3 / 5 |
| Sakura qcf + LP / HP (Hadoken) | 1 / 1 | 1 / 1 | **5-6** | 1 / 1 | 1 / 1 |
| Rose hcf + LP / HP (Soul Spark) | 1 / 1 | **18 / 16** | **19 / 17** | 1 / 1 | 1 / 1 |

Dans Upper, les « 26 » de Sakura sont un plancher : J2 tombait à zéro et sa vie n'est remise à `$90` que toutes les
150 images. En partie réelle, le projectile touche à **chaque image** pendant ~85 images, d'où les « 42 coups » vus sur
console. Dans SFA3, les boules de Sakura étaient justes : par chance, le masque converti n'y contient pas le bit 13
(voir §3).

Captures (r = images depuis le début du combat) :
- `planche_akuma.png` : arcade « 4 HIT » ; SFA3 §140, rien (Akuma revenu en garde) ; SFA3 corrigé « 4 HIT » ; Upper
  corrigé (boule partie, 3e coup à l'image).
- `planche_sakura.png` : arcade « 3 HIT » ; Upper §140, « 3 HIT » puis « 13 HIT » ; Upper corrigé, « 2 HIT » puis
  « 3 HIT » avec Ryu projeté, comme à l'arcade.

## 2. Akuma (et Dan) : saut terminal absorbé qui était aussi une cible

**Constat.** On compare la RAM de J1 entre l'arcade et la traduction, avec une image de décalage. Elle est identique
jusqu'au sous-état `$06` du coup (`$4.l = $02001006`). La sonde montre ensuite que l'arcade lance l'objet (`$038B4E
addq.b #1,(A4) ; move.w #$206,$2(A4)`). La traduction, elle, repasse à l'image suivante en `$4.l = $02000000` par
`$2BAF2` (retour en garde), alors que `$33` n'est pas négatif.

Code arcade (sous-état `$06`, `$038B2E`) :
```
jsr $2a7ea ; tst.b $33(A6) ; bmi $38bbe ; tst.b $35(A6) ; beq $38bbc ; ... ; bsr $38bc4
$38BBC: rts
$38BBE: jmp $2baf2
```
MIPS (ro3, `show.py 2d3900`) :
```
02d36e8  beq v1,zero,+556     (-> 0x2d3914)    ; TST.B $35 ; BEQ rts
02d390c  jal 0x4c3940                          ; BSR $38BC4 (appel terminal -> JMP)
02d3914  beq zero,zero,+24    -> 0x2d392c (ld ra ; addiu sp ; jr ra)   = le RTS $38BBC
02d391c  lui/addiu/jalr 0x3d8cb0               ; JMP $2BAF2
```
`tail_branch` reconnaît `jal ; beq zero,zero → épilogue`. Il émet un `JMP` et **absorbe** le `beq` sans rien émettre.
Or ce `beq` est aussi la **cible** des deux `BEQ` (« `$35` = 0 » et « réservoir plein »). Une cible se résout sur la
première instruction émise à partir d'elle, ici le `JMP $2BAF2`. Tant que l'évènement d'animation n'a pas posé `$35`,
le coup se termine donc à la première image du sous-état, avant le lancer.

C'est la même famille que le §64 (`jr ra` absorbé mais cible : `epilogue_is_target`) et que le §91 (saut fusionné mais
cible). Ce cas-ci n'était pas couvert.

**Correctif (`TAILBR`).** Les `beq` absorbés par un appel terminal sont notés (`tail_abs`). Si l'un d'eux est dans
`br_targets`, on émet un **`RTS`** à sa place. Sa sémantique est exacte : la cible du `beq` est l'épilogue `ld ra /
addiu sp / jr ra`. Ce `RTS` n'est jamais atteint en séquence, puisque le `JMP` le précède. Compteur : `sauts terminaux
absorbes gardes en RTS` (chaque site compte deux fois, une par passe).

## 3. Sakura (Upper) et Rose : masque `$800000` pris pour une adresse

**Constat.** Dans Upper, l'objet de Sakura touche à chaque image, sans geler (`$DC`), sans décompter `$50` et sans
passer en état `$04`. La sonde sur `$FF9F04` montre que l'arcade passe par la routine de touche des projectiles
(`$024CFA`) :
```
move.l #$800000,D1 ; move.b $2(A6),D0 ; btst D0,D1 ; bne rts      ; type 23 : pas de décompte
addq.b #1,(A6) ; move.l #$2020000,$4(A6) ; subq.w #1,$50(A6) ; bpl rts ; move.l #$4000000,$4(A6)
```
Dans la traduction, le même code porte `MOVE.L #$3103c0,D1` (SFA3, 68K `$005AF4`, va `0x41cb0`) et `MOVE.L #$296340,D1`
(Upper, 68K `$005EBE`, va `0x47000`). Le MIPS a pourtant un **`lui a0,0x80` seul** (`show.py` partiel rend bien
`$800000`). Dans la traduction complète, `lui_only` classe `$800000` comme « const » : il tombe dans la plage des
données du module (`CODE_END_RT ≤ v < DATA_END_RT`). La branche « `sw` d'une const dans Dn » le convertit alors par
`addr_to_68k` : `DATA_BASE + ($800000 − $583C40)` = `$3103C0` pour SFA3.

Conséquence : pour les types d'objets dont le bit est mis dans le faux masque, une touche n'est **jamais décomptée**.
L'objet traverse et retouche à chaque image. Le type 23, qui devait l'être, ne l'est plus.
- SFA3 `$3103C0` : types `$06 $07 $08 $09 $10 $14 $15` → **Soul Spark de Rose** (vérifié), Sakura épargnée ;
- Upper `$296340` : types `$06 $08 $09 $0D $0E $10 $13 $15` → **Sakura** (Hadoken et Shinku Hadoken), **Rose** (vérifié),
  et probablement Rolento (`$0E`) ;
- Hyper : même site (va `0x5c9d0`), converti lui aussi ; la ROM corrigée porte bien `MOVE.L #$800000,D1`. Non testé en jeu.

Un deuxième site du même genre est corrigé par la même règle : `$900000` → `MOVE.L #$FF0000,D1` (SFA3, va `0x363c60` /
`0x368080`), `#$1C9B520` (Upper), et converti aussi dans Hyper (va `0x154c84`). C'est le plafond d'une vitesse verticale vers l'adversaire :
arcade `$047B68` / `$048660`, `cmpi.l #$900000,D1 ; bls ; move.l #$900000,D1 ; asr.l #5,D1 ; add.l D1,$44(A6)`. Le
`CMPI` était juste, le `MOVE` non : quand le plafond s'applique, la vitesse est fausse. D'après l'ordre du code des
persos (types créés `$08` en `$44BD2`, `$0B` en `$4A83E`), c'est Rose `$09` ou M.Bison `$0A`. Le cas n'a **pas** été
déclenché en jeu : le Head Press de Bison est identique sur les 3 ROM, mais il n'atteint pas le plafond.

**Correctif (`LUIDN`).** `lui_dn_usage` cherche le premier usage de la case Dn (`lw` de la case) dans les 40 instructions
suivantes. On regarde ce que devient la valeur lue dans les 6 instructions d'après :
- **adresse** : base d'un accès mémoire, copie vers An, `jalr`, ou `addu` dont le résultat sert de base ;
- **valeur** : opération arithmétique ou logique (`and` du `BTST`, `sra` de l'`ASR`…) ;
- **inconnu** : sinon (appel, écrasement), et l'ancien comportement est gardé.

On ne convertit plus une constante `lui` seule (16 bits bas nuls) dont l'usage est « valeur ». Résultat : **3 sites par
module** (SFA3, Upper, Hyper), exactement ceux décrits plus haut. Aucun autre n'est touché.

## 4. Autres coups touchés par les mêmes pertes

`TAILBR` (sites rétablis : SFA3 6, Upper 5, Hyper 3) :

| va ro3 | arcade | quoi | effet de la perte |
|---|---|---|---|
| `0x2d3914` | `$038BBC` | Akuma, Messatsu Gou Hadou | boule jamais lancée (**vérifié, corrigé**) |
| `0x355df8` | `$04BB7A` | Dan, Shinkuu Gadoken (objet `$0C02`) | idem (**vérifié, corrigé**) |
| `0x11b9d0` | `$02EA38` | routine commune `$2EA06` (martèlement : appelée par Ken `$3738E`, Chun-Li `$3B85C/$3B8AA`, `$42D6A`, `$44972`, Rose `$469E4`) | si `$378` ≠ 0 et `$379` = 0 : passe dans la branche `$2EA3A` (test de commande `$C94DA`, `$2AE/$2AD`, animation avancée) au lieu de `rts`. Coups de pied éclair de Chun-Li martelés : **pas d'écart observé** |
| `0x2c4b84` | `$040288` | perso `$06`/`$07` (zone entre `$3F2DA` et `$44BD2`) : `tst.b $33 ; bmi` → le `rts` après `jsr $2a7ea` | tombait sur la suite (`cmpi.b #4,$82 …`, sortie du coup) ; non testé |
| `0x32ddd0` | `$063346` | zone `$63xxx` (`jsr $2a838`, objet `$38(A6)`) | tombait sur `move.b #4,$7(A6)` ; non testé |
| `0x39206c` | — | C du portage (écrans console) | sans effet (RTS juste après) |

Upper : `0x160c90` (= `$2EA06`), `0x345b84` (Akuma, **corrigé à l'image**), `0x3cfab8` (Dan), `0x3a4920` (= `$63346`),
`0x41048c` (C du portage). Hyper : `0x21c050`, `0x2d8400`, `0x3b530c`.

`LUIDN` : les 3 sites du §3 par module.

## 5. Correctif proposé

Fichiers :
- `agent_coups/correctif_translate.diff` (118 lignes) : `TAILBR`, `tail_abs`, `LUIDN`, `lui_dn_usage` ;
- `agent_coups/correctif_mame_test.diff` : deux compteurs imprimés.

Pour l'appliquer :
1. `patch -d <workspace>/scripts/untranspile < agent_coups/correctif_translate.diff`, et de même pour `mame_test` ;
2. reconstruire ro3, ro5 et ro9 ;
3. lancer `nonreg.sh` et `nonreg_ro5.sh`, **plus** `balayage_fins.sh` (leçon du §137) ;
4. reconstruire les zips FBNeo.

Cœur du diff :
```python
# translate.py, avant le cas 'saut inconditionnel interne, absorbe'
if m=='beq' and ins.va in absorbed and TAILBR and ins.va in tail_abs and ins.va in br_targets:
    TAILBR_N[0]+=1
    out.append((ins.va,"RTS  [saut terminal absorbe, cible d'un branchement]",[RTS])); i+=1; continue
# branche 'sw' d'une const dans Dn
if a68 is not None and LUIDN and isinstance(v,int) and (v & 0xffff)==0 \
   and lui_dn_usage(ins_list, i, ins.imm & 0xffff)=='val':
    LUIDN_LOG.append((ins.va, v, a68)); a68=None
```

## 6. Vérification (ROM reconstruites dans `agent_coups/b3_new`, `b5_new`, `b9_new`)

- **Égalité avec l'arcade** : voir le tableau du §1. Écarts de ±1 image sur l'instant des coups, comme partout dans la
  traduction.
- **Contrôle** : `TAILBR=0 LUIDN=0` redonne exactement les ROM actuelles (SFA3 et Upper).
- Construction : `non resolus 0`. Chutes inchangées (SFA3 24, Upper 26).
- **Non-régression partielle** (la validation partagée tournait, je l'ai limitée) :
  - `commandes.lua` sur SFA3 corrigé : **42 actions, 0 différente**, 5359 tours en 4019 images (133,3 %) ;
  - `tournee.lua` SFA3 Akuma, 60 000 images : 30 manches, sans exception ;
  - `tournee.lua` Upper Sakura, 60 000 images : 25 manches, sans exception.
- **Pas faits** : diagnostics `diag.py` (ils écrivent dans `work/mame`), `nonreg_ro5.sh` complet, balayages des fins,
  essai d'Hyper en jeu, et M.Bison/Rose dans le cas « plafond `$900000` atteint ».

Fichiers : `out/<essai>/log.txt` (journaux), `out/V_*` (essais de vérification), `planche_akuma.png`,
`planche_sakura.png`, `b3_new/carte_image.txt` / `b5_new/carte_image.txt` (sites marqués `saut terminal absorbe`).
