# Interpréteur IA : SFA3 MAX (PSP, ULES00235) ↔ SFA3 arcade (sfa3ud, 68000)

Analyse statique. Arcade : code `sfa3_prog.bin` (module arc68k), données `sfa3ud_prog.bin`.
PSP : VA = décalage fichier − 0x74. Relevé statique du 2026-10-27 (session MAX).

## 0. Conclusion courte

**Même lignée, sans doute possible.** Le PSP reprend l'interpréteur arcade (version Upper : 21 sous-commandes en classe 0),
avec les mêmes 12 classes, le même ordre de sous-commandes, le même nombre d'opérandes, les mêmes champs (décalés)
et les mêmes sous-programmes. Seule l'**indexation** change : l'arcade indexe ses tables par des **décalages pairs**
(octet × 2 → `move.w tab(pc,d0.w)`), le PSP par des **indices** (× 4 → pointeurs 32 bits).

Point important : la table PSP « 81 commandes » 0x21E598 **n'est pas une seule table**. C'est 7 tables collées
(le compilateur les a rangées l'une après l'autre) :

| entrées | adresse | aiguillée par | équivalent arcade |
|---|---|---|---|
| 0-40 (41) | 0x21E598 | mot de condition (+0x1EA) dans 0x74A20 = **SI** (classe 6 sous-cmd 0) | conditions du SI `$0C00`, table rel16 $31424 (39 entrées, 0-38) |
| 41-44 (4) | 0x21E63C | 0x75F90 = classe 9, octet +0x1E8 | classe `$12`, sous-commandes 00-06 |
| 45-47 (3) | 0x21E64C | 0x76154, mot `FFxx` | `$FFxx`, table $321D4 (3 entrées) |
| 48-50 (3) | 0x21E658 | 0x76300, en-tête de script +0x1E6 | table $32264 sur `$206` |
| 51-58 (8) | 0x21E664 | 0x76400, état d'action +0x1E2 | table $3229E sur `$202` (8 actions) |
| 59-72 (14) | 0x21E684 | 0x76434, +0x1E3 quand +0x1E2 = 0 | table $322BA sur `$203` (action 0, 14 entrées) |
| 73-80 (8) | 0x21E6BC | 0x76A70, +0x1E3 quand +0x1E2 = 1 | table $32492 sur `$203` (action 1, 8 entrées) |

De même, la table « 65 routines » 0x21E488 regroupe : 0x21E488 (4 routines de créneau, par +0x1E4), 0x21E498
(**les 12 classes**, aiguillées par 0x73564 sur `octet +0x1E9 & 0xF`), 0x21E4C8 (classe 0, 21), 0x21E51C (classe 1, 8),
0x21E53C (classe 2, 4), 0x21E54C/55C/56C/57C (4 sous-tables de 4 internes à la classe 2), 0x21E58C (classe 6, 3).

## 1. Règle de conversion mot PSP → mot arcade

Les mots PSP sont des u16 petit-boutistes : octet haut = +0x1E9 = classe, octet bas = +0x1E8 = sous-commande
(l'arcade lit le même mot grand-boutiste : `$208` = classe, `$209` = sous-commande).

```
PSP 0xCCSS  (CC & 0x0F = c, SS = s)   →   arcade  ((2c) << 8) | (2s)
PSP 0xFFss                            →   arcade  0xFF(2s)
opérandes : même nombre, même ordre, mêmes valeurs (sauf cas ci-dessous)
```

Exemples vérifiés sur données réelles (Ryu Upper PS2 ↔ PSP 0x23D12C) :
`0010 0204 00c0 0010 … 0e02` (Upper) ↔ `0008 0102 0070 0008 … 0701` (PSP) : `0010`=C0 s8 ↔ `0008`, `0204 xx` ↔ `0102 xx`, `0e02` ↔ `0701`.
Lecture d'un script PSP (0x23D1A0) : `0300 2402 | 000b | 0300 4500 | 000b | ff01 ‖ 0001(en-tête) 7600 0000 0030 | 0200 4600 ff04 0001 | 0300 0500 | … | 7602 | 000b …`
(le `ff04` est le 2ᵉ opérande de `0200`, pas une commande).

Exceptions / pièges :
1. **Mots de bloc** : le PSP exige exactement `0x7600` (SI), `0x7601` (SINON), `0x7602` (FIN). L'aiguilleur ne regarde que
   `CC & 0xF` = 6, mais le saut de bloc PSP (0x75C8C / 0x75D1C) **cherche ces trois valeurs exactes mot par mot** et compte la
   profondeur en +0x1F5. L'arcade, lui, saute de façon syntaxique ($32AEE : table de longueurs par classe). Donc
   `$0C00/$0C02/$0C04` → `7600/7601/7602`, et aucun opérande ne doit valoir 0x7600-0x7602 côté PSP.
2. **Condition du SI** : le mot qui suit `7600` est un indice k (PSP) ↔ décalage 2k (arcade, `$20A`). Les opérandes de la condition sont identiques.
3. **En-tête de script** (+0x1E6 ↔ `$206`) : indice 0/1/2 (PSP) ↔ 0/2/4 (arcade).
4. Certains opérandes restent **au format arcade (pairs)** : classe 2, octet bas du 2ᵉ opérande (+0x1EC) utilisé comme `>>1` → sous-tables 0x21E54C…; même valeur des deux côtés.
5. **Classe 10 (`$14xx`, SI secondaire à nid `$255`) : supprimée côté PSP** (0x732B0 = boucle infinie `b .`). Un script arcade qui l'emploie doit être réécrit (ex. en SI de classe 6), sinon gel.
6. Ajouts PSP/Upper sans équivalent sfa3ud : classe 0 sous-commandes 19-20, conditions 39-40.

## 2. Correspondance des champs (bloc IA : PSP = arcade − 0x20)

+0x1E0..1E1 ↔ $200..201 ; +0x1E2/1E3 (état d'action, **indices**) ↔ $202/$203 (décalages) ; +0x1E4 (créneau 0-3) ↔ $204 (0,2,4,6) ;
+0x1E6 ↔ $206 ; +0x1E8 (mot de commande) ↔ $208 ; +0x1EA ↔ $20A ; +0x1EC ↔ $20C ; +0x1EE ↔ $20E ; +0x1F0/1F1 ↔ $210/$211 ;
+0x1F2 ↔ $212 ; +0x1F4 ↔ $214 ; +0x1F5 (profondeur SI) ↔ $215 ; +0x1F8 ↔ $218 ; +0x1FA (compteur) ↔ $21A ; +0x1FC ↔ $21C ;
+0x200/204/208/20C (bases de script) ↔ $220-$22C ; +0x210 (pointeur courant) ↔ $230 ; +0x220 ↔ $240 ; +0x226 ↔ $246 ; +0x235 ↔ $255.
Autres (déduits ici, cohérents avec carte_champs.json) : 0x70↔$50, 0x152↔$102, 0x173↔$123, 0x177↔$127, 0xFB↔$B9, 0x218↔$238,
0xE4↔$A4, 0x2BA↔$2CA, 0x2B8↔$2C8, 0x49↔$31, 0x4E↔$3C, 0x84↔$64, 0x16↔$14, 0x64↔$44, 0xEE↔$AC, 0x7B↔$5B, 0x16E↔$11E, 0x182↔$132.
Sous-programmes : 0x7610C ↔ $321AC (mot suivant, exécution immédiate) ; 0x75C8C ↔ $31A38/$32AEE (sauter au SINON/FIN) ;
0x72BE4 ↔ $307D0 ; 0x77BC8 ↔ $32C5C ; 0x77B9C ↔ $32C50 ; 0x75C00 ↔ $31A04 (distance) ; 0x73258 ↔ $30A66 (table de conditions) ;
0x1D368 ↔ $1BDA6 (aléa) ; 0x776B8 ↔ $32926 ; 0x777CC ↔ $3299C ; 0x771A8 ↔ $32710 (fin d'action) ; 0x771B8 ↔ $3271A ; 0x7825C ↔ $32756 ;
0x68F90 ↔ $2F256 ; 0x68CC0 ↔ $2F0D6 ; 0x7748C ↔ $3284E ; 0x77528/77504 ↔ $328B0/$3289C (gestes).
Le moteur : 0x73564 (boucle tant que compteur global 0x2975E ≠ 0) ↔ $30BC8 + rebouclage `bra $30BC8` de $321AC.

## 3. Classes et sous-commandes (mot complet)

« op » = mots d'opérandes consommés ; « suite » = enchaîne la commande suivante dans la même trame ; « action » = pose un état `$202` et rend la main.

| PSP mot | fonction PSP | arcade mot | gestionnaire | op | rôle / champs | conf. |
|---|---|---|---|---|---|---|
| 0000 | 73610 | 0000 | 30C1E | 1 | action 0/0, `$21A`←op | haute (Ghidra n'a pas rendu 73610 ; position) |
| 0001 | 7363C | 0002 | 30C32 | 0 | si adv. `$2C8`≠0 → suite, sinon action 0/1 | haute |
| 0002 | 7368C | 0004 | 30C4A | 0 | action 0/2 (test `$2C8`) | haute |
| 0003 | 736E0 | 0006 | 30C62 | 0 | action 0/3 (adv. en l'air `$31`) | haute |
| 0004 | 7373C | 0008 | 30C80 | 1 | action 0/4, `$20A`, adv. `$14/$64/$44` | haute |
| 0005 | 737E8 | 000A | 30CB8 | 0 | 68F90/2F256 → action 3/0 | haute |
| 0006 | 73880 | 000C | 30CE2 | 1 | `$21A`←op, action 0/6 ou 3/0 | haute |
| 0007 | 73928 | 000E | 30D1C | 1 | distance projectile (75C00/31A04), action 0/7 | haute |
| 0008 | 73A38 | 0010 | 30D62 | 0 | 7748C/3284E, action 0/8 | haute |
| 0009 | 73AD4 | 0012 | 30D7E | 0 | projectile propre `$238/$A4`, action 0/9 | haute |
| 000A | 73B58 | 0014 | 30D98 | 0 | 77BC8/32C5C, action 0/10 | haute |
| 000B | 73BC4 | 0016 | 30DAA | 0 | 7748C/3284E, action 0/0 (très fréquent) | haute |
| 000C | 73C30 | 0018 | 30DC0 | 0 | `$21A`=1, action 0/8 | haute |
| 000D | 73C5C | 001A | 30DD0 | 1 | `$21A`←op, action 0/8 | haute |
| 000E | 73C8C | 001C | 30DDE | 2 | `$20A,$21A`, action 0/11 | haute |
| 000F | 73D00 | 001E | 30E00 | 2 | `$20A,$21A`, action 0/12 | haute |
| 0010 | 73D60 | 0020 | 30E22 | 0 | 77B9C/32C50, action 0/13 | haute |
| 0011 | 73DCC | 0022 | 30E34 | 0 | 68CC0/2F0D6 → action 3/0 | haute |
| 0012 | 73E64 | 0024 | 30E5E | 0 | `$5B`=0, action 0/5 | haute |
| 0013 | 73E8C | (0026) | — | 0 | 72BE4 → action 6/1 | sans équivalent sfa3ud (Upper) |
| 0014 | 73F08 | (0028) | — | 0 | test adv. +0x257 | sans équivalent sfa3ud (Upper) |
| 0100-0107 | 73FBC 7402C 740A0 74148 74184 741C4 74244 742C8 | 0200-020E | 30EA0…30FD4 | 1,1,1,1,1,2,2,2 | marche/garde (états 1/0-1/7, `$3C,$211,$21A`) | haute |
| 0200-0203 | 743B0 74480 745F4 746DC | 0400-0406 | 3102C 3107E 3110E 31184 | 3 chacun | coups/gestes (`$20A/$20C/$20E`, 328B0) | haute |
| 0300/0301 | 74798 (octet 0/≠0) | 0600/0602 | 311F0 / 3121C | 1 | coup spécial (action 3/0, 3/1) | haute |
| 0400 | 748D4 | 0800 | 31274 | 1 | action 4/0 (77504/3289C) | haute |
| 0500/0501 | 77ED0 | 0A00/0A02 | 312DE / 31372 | 1 | super/isme (`$132`, jauge `$11E`) | haute |
| **7600** | 74A20 | **0C00** | 31412 | 1 + opérandes de la condition | SI (profondeur `$215`++) | certaine |
| **7601** | 75D1C | **0C02** | 31A38 | 0 | SINON → saut jusqu'à FIN | certaine |
| **7602** | 75D98 | **0C04** | 31A44 | 0 | FIN (`$215`−−) | certaine |
| 0700 | 75E10 | 0E00 | 31A5C | 0 | appel de sous-script (`$218`←`$206`, créneau 1, 7825C/32756) | haute |
| 0701 | 75E58 | 0E02 | 31A74 | 0 | idem si table de conditions (73258/30A66) | haute |
| 08xx | 75EB4 | 10xx | 31A86 | 0 | 72BE4/307D0 → action 6/0, `$214`←octet bas | haute |
| 0900-0903 | voir entrées 41-44 | 1200-1206 | 31AE6… | 2,2,0,0 | drapeaux `$240`, compteur `$246` | haute |
| 0Axx | 732B0 = **boucle infinie** | 1400-1408 | 31B34 31B38 31E8A 31E8E 31E92 | — | SI secondaire (nid `$255`, 31 conditions en $31B42) | **supprimé côté PSP** |
| 0Bxx | 760B8 | 16xx | 3217C | 1 | action 7/0 (`$E00`), `$80/$81`←op | haute |
| FF00-FF02 | voir 45-47 | FF00-FF04 | 321DA 321FC 32248 | 0 | contrôle de flux | certaine |

## 4. Les 81 entrées de 0x21E598

Notation des conditions : « V » = branche suite (0x7610C ↔ $321AC), sinon saut de bloc (0x75C8C ↔ $31A38).
Opérandes = mots lus après le mot de condition.

| # | PSP | arcade | op | comportement commun | conf. |
|---|---|---|---|---|---|
| 0 | 74A68 | SI cond 00 ($31472) | 1 | V si `$21C` ≥ op (op→`$20C`) | certaine |
| 1 | 74ACC | cond 02 ($31486) | 1 | V si op ≥ `$21C` | certaine |
| 2 | 74B30 | cond 04 ($3149A) | 0 | aléa & 1 = 0 (1/2) | certaine |
| 3 | 74B88 | cond 06 ($314AC) | 1 | jauge `$11E` ≥ op (ou =0x90 si `$123`/`$132`) | certaine |
| 4 | 74C24 | cond 08 | 0 | adversaire en l'air (`$31`=1) | certaine |
| 5 | 74C80 | cond 0A | 0 | adv. `$2C8`≠0 | certaine |
| 6 | 74CD8 | cond 0C | 0 | adv. `$2CA`≠0 | certaine |
| 7 | 74D30 | cond 0E | 0 | projectile adverse actif (`$238`,`$A4`→`+4`=… ) | haute (PSP teste +4==1, arcade ==2 : indices d'état halvés) |
| 8 | 74DA4 | cond 10 | 1 | distance du projectile adverse ≤ op | certaine |
| 9 | 74E48 | cond 12 | 1 | complément de 8 | certaine |
| 10 | 74EEC | cond 14 | 0 | 72BE4 / $307D0 ≠ 0 | certaine |
| 11 | 74F40 | cond 16 | 0 | adv. en l'air et `$3C`=1 | certaine |
| 12 | 74FC0 | cond 18 | 0 | adv. en l'air et `$3C`=0 | certaine |
| 13 | 75040 | cond 1A | 0 | adv. en l'air et `$3C`=−1 | certaine |
| 14 | 750C4 | cond 1C | 0 | 77BC8 / $32C5C ≠ 0 | certaine |
| 15 | 75118 | cond 1E | 1 | `$127` ≤ op & 0x1F | certaine |
| 16 | 75180 | cond 20 | 1 | op & 0x1F ≤ `$127` | certaine |
| 17 | 751E8 | cond 22 | 0 | pas de projectile propre (`$238`=0 et `$A4`=0) | certaine |
| 18 | 75260 | cond 24 | 1 | adv. `$50` < op | certaine |
| 19 | 752C4 | cond 26 | 0 | adv. `$50` < propre `$50` | certaine |
| 20 | 75328 | cond 28 | 0 | adv. en l'air et `$44` ≥ 0 (montée) | certaine |
| 21 | 753A8 | cond 2A | 0 | adv. au sol ou `$44` < 0 | certaine |
| 22 | 75428 | cond 2C | 1 | adv. `$14` ≤ op + `$64` | certaine |
| 23 | 75498 | cond 2E | 1 | op + `$64` ≤ adv. `$14` | certaine |
| 24 | 75508 | cond 30 | 0 | table 0x21E198 / $31804 = 0 ou 4 | haute (**divergence** : PSP lit +0xE4 du joueur, l'arcade `$A4` de l'adversaire ; index +0x15A vs `$72`>>1) |
| 25 | 755E8 | cond 32 | 0 | même table > 2 | haute (même divergence) |
| 26 | 756A8 | cond 34 | 1 | propre `$50` < op | certaine |
| 27 | 75708 | cond 36 | 0 | aléa & 3 = 0 (1/4) | certaine |
| 28 | 75760 | cond 38 | 1 | adv. `$102` (perso) = op | certaine |
| 29 | 757BC | cond 3A | 1 | propre `$102` = op | certaine |
| 30 | 75814 | cond 3C | 0 | `$5B` ≠ 0 | certaine |
| 31 | 75868 | cond 3E | 0 | isme `$132` = 0 | certaine |
| 32 | 758BC | cond 40 | 0 | `$132` ≠ 0 | certaine |
| 33 | 75910 | cond 42 | 0 | `$132` = −1 | certaine |
| 34 | 75968 | cond 44 | 0 | `$132` ≠ −1 | certaine |
| 35 | 759C0 | cond 46 | 0 | `$132` = 1 | certaine |
| 36 | 75A18 | cond 48 | 0 | `$132` ≠ 1 | certaine |
| 37 | 75A70 | cond 4A | 0 | `$5B` = 1 | certaine |
| 38 | 75AC8 | cond 4C | 0 | `$B9` ≠ 0 | certaine |
| 39 | 75B1C | (cond 4E) | 0 | adv. état 4/5/6 = 1/0/8 | **sans équivalent sfa3ud** (ajout Upper/MAX) |
| 40 | 75B94 | (cond 50) | 1 | V si op ≥ aléa & 0x1F (probabilité op/32) | **sans équivalent sfa3ud** |
| 41 | 75FC4 | 1200 ($31AE6) | 2 | si op1 < `$127` : `$240` \|= op2 ; suite | certaine |
| 42 | 76018 | 1202 ($31AF8) | 2 | si op1 < `$127` : `$240` &= ~op2 | certaine |
| 43 | 76078 | 1204 ($31B0E) | 0 | `$246` = 0 | certaine |
| 44 | 76094 | 1206 ($31B16) | 0 | `$246`++ | certaine |
| 45 | 76188 | FF00 ($321DA) | 0 | passer au créneau 1 (sous-script 7825C/32756) | certaine |
| 46 | 761D8 | FF02 ($321FC) | 0 | retour : créneau 0, `$206`←`$218`, reprise en `$220` (ou rechargement 771B8/3271A) | certaine |
| 47 | 762A4 | FF04 ($32248) | 0 | table de conditions (0x21E7A0 / $C835A) → 45 ou 46 | certaine |
| 48 | 76334 | en-tête 0 ($3226A) | — | fin d'action (771A8 / bra $32710) | certaine |
| 49 | 76350 | en-tête 2 ($3226E) | — | RAZ `$204,$215,$255`, `$206`←`$218`, relance `$220` | certaine |
| 50 | 763B4 | en-tête 4 ($32282) | — | table de conditions (0x21E820 / $C83DA) → 48 ou 49 | certaine |
| 51 | 76434 | action `$202`=0 ($322AE) | — | aiguille sur `$203` (entrées 59-72) | certaine |
| 52 | 76A70 | action 2 ($32486) | — | aiguille sur `$203` (entrées 73-80) | certaine |
| 53 | 76F28 | action 4 ($32622) | — | arcade : 3 sous-cas (0 et 2 identiques) ; PSP aplati | moyenne |
| 54 | 76F50 | action 6 ($32648) | — | 2 sous-cas sur `$203` | haute |
| 55 | 77064 | action 8 ($326A2) | — | 1 sous-cas | haute |
| 56 | 770B4 | action A ($326C2) | — | arcade 2 sous-cas, PSP un seul test | moyenne |
| 57 | 770DC | action C ($326E6) | — | teste états `$4/$6` → $32710 | haute |
| 58 | 77180 | action E ($326F8) | — | idem | moyenne |
| 59-72 | 76468 … 76A1C | action 0, `$203` = 0…1A ($322D6 $322F0 $3230A $32324 $3233C $3236C $32370 $323B0 $323EA $323FC $32416 $32428 $3244E $32474) | — | dans l'ordre : compteur `$21A` ; `$2C8`≠0 ; `$2C8`=0 ; adv. en l'air ; adv. en l'air+hauteur ; fin immédiate ; compteur+2F256 ; distance projectile ; compteur sans 32926 ; projectile propre ; 32C5C ; `$21C`/`$20A` ≥ ; < ; 32C50 | haute (14/14 alignés, mêmes sous-programmes) |
| 73-80 | 76AA4 76B34 76BC4 76C70 76C70 76CFC 76DAC 76E5C | action 2, `$203` = 0…E ($324A2 $324CE $324FA $3253A $3253A $32566 $3259E $325D6) | — | marche/garde vers la distance `$20A`/`$21C`, `$211` pour 75/80 ; doublon 76/77 ↔ doublon $3253A | haute |

## 5. Points douteux / non faits

- 0x73610 (classe 0 sous-cmd 0) non décompilé par Ghidra ; apparié par position seulement.
- Conditions 24/25 : le PSP lit `+0xE4` du joueur IA au lieu de l'adversaire (vérifié au désassembleur : `lw a2,0xe4(a1)` avec a1 = joueur). Bogue de portage probable.
- Cond 7 : l'arcade teste l'état `+4` = 2 de l'objet, le PSP = 1 (cohérent avec la division par 2 des états).
- Les 31 conditions de la classe 10 arcade ($31B42) n'ont pas été détaillées (classe absente côté PSP).
- Les états d'action (`$202/$203` ↔ +0x1E2/+0x1E3) sont aussi divisés par 2 côté PSP (ex. `$E00` ↔ 7/0, `$600` ↔ 3/0).
- Comptage arcade corrigé (cibles avant la table prises en compte) : 19, 8, 4, 2, 1, 2, 3, 2, (direct), 4, 5, 1 — inchangé pour sfa3ud ; Upper a 21 en classe 0 comme le PSP.

## 6. Conversion effective (max/outils/convert/ia_max.py, 2026-10-27)

- Tables par perso : gabarit PSP mots 12-15 (w12 4 scripts, w13 4 paires aléa/scripts, w14 n paires selon l'adversaire,
  w15 8 scripts) ↔ Upper T0 0x74C0D8, T1 0x74C178, T2 0x74C218, T3 0x74C2B8 (par ID). Sous-bloc d'Upper : 0x60 octets
  d'aléa (ordre des octets PSP) puis un décalage par script (nombre = plus grand octet d'aléa + 1), relatifs au sous-bloc.
- Règles d'opérandes relevées sur les natifs (en plus du §1) : 1er opérande doublé octet par octet pour `0501`, `0B00`
  et `0203` (paires d'indices d'action) ; `0500`, `0200`, classes 3 / 4 : opérandes inchangés.
- Contrôle `--natifs` (contenu atteint par chaque entrée, mise en page libre) : 13 natifs sur 29 identiques ; les
  autres diffèrent par des VALEURS retouchées dans Upper (ex. `0400 0813` ↔ `0816`, `0100 001e` ↔ `0200 0030`), pas par
  des règles.
- Les scripts MAX emploient massivement la **condition 40** (« vrai si op ≥ aléa & 31 », ajout PSP, Eagle 174 fois) :
  la table des conditions d'Upper (image $DEF0, T_60DF10) n'a que 39 entrées → à étendre (index 2k = $50).
