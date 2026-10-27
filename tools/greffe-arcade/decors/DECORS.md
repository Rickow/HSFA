# Décors

Étude en lecture seule (étape 7 de la greffe Arcade, 2026-10-10). Rien n'a été modifié hors de
`work/greffe_arcade/decors/`. MAME n'a pas été lancé. Calculs en `nice -n 19`.

**Conventions**
- `ro5` = Upper, `ro9` = Hyper, `ro3` = SFA3.
- Code : adresses **fichier** du module. Données : adresses **exéc.** (= fichier + `0x1F0000`).
- « Image » = programme 68K traduit (`carte_image.txt` du 2026-10-10 : `work/mame`, `work/mame_ro5`, `work/mame_ro9`).
  Ces adresses changent à chaque reconstruction.
- Décor = valeur de `$100(A5)` (`$FF8100`) = numéro × 2.
- Recensement des accès : `lh/sh` de `$100(A5)` par la base A5 (`sites_a5.py`). Tous les `lh …,0x100(rX)` du code
  sont couverts. Upper : **69 sites dans 62 routines**. Hyper : **40 sites dans 39 routines**.

---

## 1. Inventaire : les décors d'Upper dans Hyper

### 1.1 Ce qu'Hyper possède

Hyper n'a que **4 numéros de décor** (`$100` = 0, 2, 4, 6) et **3 agencements**. Toutes ses tables par décor ont
4 entrées. Seules les palettes ont des variantes.

| `$100` | listes s1 / s2 / s3 | palettes A (s1) / B (s2) / C (s3), selon `$C178` = 0 / 8 / `$10` / `$18` | origine |
|---|---|---|---|
| 0 | `+$08` / `+$08` / `+$08` | A : `$20` ×4 ; B, C : `$20` / `$420` / `$20` / `$420` | neuf (ZERO, Grande Muraille) |
| 2 | `+$0C` / `+$18` / `+$48` | A : `$20` ×4 (= décor 0) ; B, C : `$820` ×4 | neuf (ZERO 2 / ALPHA, chute d'eau) |
| 4 | `+$10` / `+$28` / `+$88` | A : `$420` / `$820` / `$C20` / `$1020` ; B, C : `$C20` / `$1020` / `$1420` / `$1820` | **décor `$4E` d'Upper** (ZERO 3), 4 couleurs |
| 6 | = décor 4 | A : `$420` ; B, C : `$C20` (= décor 4, variante 0) | = `$4E` d'Upper sans variante ; non atteint par les tables vues |

- Les tables A `0x660240`, B `0x661E60` et C `0x664280` ont **16 entrées**, indexées par **`$100 + $C178`**.
- Les variantes ne changent **que les palettes**. Listes, blocs et gestionnaires sont indexés par `$100` seul.
- Donc « neige » et « ciel d'orage » (ZERO 3) sont très probablement deux variantes de couleur du décor 4. Le
  décor rouge et le décor vert d'ETATS-HYPER §6 aussi. À confirmer en forçant `$C178`.
- **Choix du décor par version** : `0xA49E0` (homologue du choix Arcade d'Upper) lit `T_5B6220[$103]`.
  - `T_5B6220` (exéc. `0x5B6220`, 128 octets, id étendu) : ids `$00-$2F` → 2, `$30-$3F` → 0, `$40-$7F` → 1.
  - Puis `$174 = 2 × valeur` : ZERO 3 → 4, ZERO → 0, ZERO 2/ALPHA → 2.
  - `0x96690` (init de match) : `$100 = $174`, puis `$C178 = ($C178 + 8) & $18`.
- Attraction : `0x98590` et `0xA05C0` posent `$100 = T_5B5CB0[$C314]` et `$C178 = T_5B5CC0[$C314]` (8 couples).

### 1.2 Données du module (tables par décor)

Liste complète : `tables_par_decor.tsv` (rôle, routines, tables, nombre d'entrées, adresse arcade d'Upper).

| groupe | Upper (40 entrées, `$00-$4E`) | Hyper |
|---|---|---|
| palettes s1 / s2 / s3 | `0x70E560` / `0x7147E0` / `0x71D420` ; 2 routines de chargement par plan | A `0x660240` (2 sites) / B `0x661E60` (1) / C `0x664280` (1) ; 16 entrées |
| type s1, listes s1 / s2 / s3 | `0x747EE0`, `0x747F30` / `0x7480D4` / `0x748344` | `0x695FF0`, `0x695FF8` / `0x696010` / `0x696048` ; 4 entrées |
| bibliothèques s1 / super-tuiles / s2 / s3 | `0x69B830` (119 blocs) / `0x69F3B0` (3 081) / `0x6CF5F0` (170) / `0x6EF3F0` | `0x63DA20` (6) / `0x63DD20` (177) / `0x640960` (17) / `0x643C60` |
| ordre des plans, gestionnaires s1 / s2 / s3, init X/Y, CPS-B, effet | `T_6147B0`, `T_614850`, `T_6149B0`, `T_614AD0`, `T_614600`/`T_6146A0`, `T_614CD0`, `T_6135A0` (+ `T_6134E0`/`T_613530`) | `T_5C50D0`, `T_5C50E0`, `T_5C5100`, `T_5C5180`, `T_5C50B0`/`T_5C50C0`, `T_5C51F0`, `T_5C9E30` (+ `T_5C9E00`/`T_5C9E08`) ; 4 entrées |
| couleur de ROUND | `T_6112D0` + `0x73E330` / `0x73E630` | `T_5C87D0` + `0x690800` / `0x690B00` : **40 entrées, identiques** |
| bornes `$40/$44`, init joueurs | constantes (toutes les entrées égales) | idem : rien à faire |
| palettes des sprites de décor (`$90C1E0`) | `0x707D10` (`0x4AA60`, `0x4B930`) | **absent** |
| objets de décor, objet par décor, animations des objets | `T_950CE0` (`0x4C1B0`), `0x740B70` (`0x105C70`), `0x971E70` (`0xFDC10`) | **absent** |
| positions (décor précédent `$172`), animations par décor, masques | `0x196F50`, `0x198A00` (`$C0A00400`), `0x199530`, `0x199DA0`, `0x371920` (`$3F60BDB3`) | **absent** (aucun lecteur de `$172`) |
| musique par décor (VERSUS), cas `$14`/`$04` | `0x139AD0` (`T_613380`, `T_613350`) | **absent** |
| défilement du décor dans les scènes Arcade | `0x2CAC0` (`T_60B400`) | **absent** (avec les scènes) |

Présence des blocs de données d'Upper dans le module Hyper (`donnees_decor.py`, recherche d'octets) :
- palettes s1 / s2 / s3 : **1 bloc sur 35** (celui de `$4E`) ;
- palettes de sprites, listes s1 et s3, objets, animations : **0** ;
- listes s2 : 2 blocs, par coïncidence ;
- bibliothèques : 11 blocs s1 sur 119, 4 super-tuiles sur 3 081, 7 blocs s2 sur 170.

⟹ **Les données de décor d'Upper ne sont pas dans Hyper**, sauf celles de `$4E` (palettes).

Code de décor d'Upper (`code_decor.py`, `exact_groupes.py`) :
- sous-arbres des tables et routines par décor : **239 routines, 75 Ko de MIPS** ;
- **72 Ko sans copie exacte** dans Hyper (adresses masquées) ; en couverture K = 12 : 14 Ko absents, 18 Ko modifiés ;
- exemples : 16 gestionnaires scroll1 et 14 gestionnaires scroll3 contre 3 et 4 dans Hyper ; 9 effets par décor
  contre 2.
- Ce code s'ajoute aux ≈ 100 Ko de l'étude Upper/Hyper (§1.2 de l'étude : les tables de plus de 24 entrées n'y
  étaient pas suivies).

### 1.3 Graphismes

| mémoire | SFA3 | Upper | Hyper |
|---|---|---|---|
| décor (MWo3, vues 8×8 et 16×16) | e256 : 4,5 Mo, 35 328 tuiles 16×16 | e353 : 5,4 Mo, 42 496 | **e546 : 2,9 Mo, 23 296** |
| conteneur 32×32 (scroll3) | e312 : 4 096 | e525 : 4 576 | **e548 : 896** |
| `hsfa_plans.bin` du fork (bases `300,340,3a0`) | — | `mame_ro5/` : 12,8 Mo | `mame_ro9/` : 10,9 Mo (e546 + e548) |

- e546 n'est pas un sur-ensemble d'e353 : 196 tuiles 16×16 communes en tête, puis un autre contenu.
- 41 % des tuiles 16×16 d'Upper existent quelque part dans e546, mais ce ne sont pas celles des décors (écrans communs).
- Mesure par décor (`tuiles_decor.py`) : listes → blocs → super-tuiles → codes locaux, contenus cherchés dans e546
  et e548. Les blocs communs à tous les décors (s1 0, s2 0, s3 `$00`, `$43-$4E` : rangée haute commune) sont exclus.
- Contrôle : les 32 décors SFA3 d'Upper sont à 99,8-100 % dans e256 ; les 3 agencements d'Hyper à 100 % dans e546.
- Résultat : **aucun décor d'Upper n'est dans Hyper, sauf `$4E` (99-100 %)**. Les autres sont à 0-6 % par plan
  (tuiles banales), au plus 20 % (scroll1 de `$1E`) et 11 % (scroll3 de `$30`).
- Place à prévoir pour `$00-$4C` (`capacite.py`) : scroll1 **22 566** tuiles 8×8 neuves, scroll2 **14 330**
  tuiles 16×16, scroll3 **3 122** tuiles 32×32.

### 1.4 Décor par décor

« gfx » = part des tuiles propres au décor présentes dans Hyper. « données partagées » : décor d'Upper aux mêmes
palettes et listes (ou aux mêmes listes seulement). Noms : groupe de l'export DECORS-WS ; persos : ids d'Upper
(noms de `0x626120` décalés d'un rang à partir de `$15`, recoupé par Evil Ryu → `$2E`, Juli/Juni → `$2A`, ROUND de
R.Mika et Cody, Shin Akuma → données d'Akuma ; ids `$12-$14` non tranchés).

| décor | export DECORS-WS | persos qui y mènent (Upper, `T_61BE10`) | données dans Hyper | gfx s1 / s2 / s3 dans Hyper | pal. s1 Upper | listes s1 / s2 / s3 Upper | données partagées |
|---|---|---|---|---|---|---|---|
| `$00` | Ryu/Evil Ryu | Ryu, id12, id14, id26 | non | 1 / 0 / 1 % | `0x70E5B0` | `0x747F80` / `0x748124` / `0x748394` |  |
| `$02` | Ken | Ken | non | 1 / 2 / 0 % | `0x70E5F0` | `0x747F84` / `0x748134` / `0x7483D4` |  |
| `$04` | Akuma | Akuma | non | 0 / 0 / 3 % | `0x70E910` | `0x747F8C` / `0x748144` / `0x748414` |  |
| `$06` | Charlie | Charlie | non | 1 / 2 / 0 % | `0x70E9D0` | `0x747F90` / `0x748154` / `0x748454` |  |
| `$08` | Chun-Li/Chun-Li (variante) | Chun-Li | non | 1 / 1 / 0 % | `0x70ED70` | `0x747F98` / `0x748164` / `0x748494` |  |
| `$0A` | Adon | Adon | non | 1 / 1 / 0 % | `0x70F0D0` | `0x747FA0` / `0x748174` / `0x7484D4` |  |
| `$0C` | Sodom/Sodom (variante) | Sodom | non | 1 / 1 / 0 % | `0x70F410` | `0x747FA8` / `0x748184` / `0x748514` |  |
| `$0E` | Guy | Guy | non | 1 / 1 / 4 % | `0x70F790` | `0x747FB0` / `0x748194` / `0x748554` |  |
| `$10` | Birdie | Birdie | non | 3 / 1 / 2 % | `0x70FA50` | `0x747FB8` / `0x7481A4` / `0x748594` |  |
| `$12` | Rose | Rose | non | 1 / 2 / 0 % | `0x70FCF0` | `0x747FC0` / `0x7481B4` / `0x7485D4` |  |
| `$14` | M.Bison | — (Bison final : `$174 = $14`) | non | 2 / 2 / 0 % | `0x70FFD0` | `0x747FC8` / `0x7481C4` / `0x748614` |  |
| `$16` | Sagat | Sagat | non | 1 / 2 / 0 % | `0x70FFF0` | `0x747FCC` / `0x7481D4` / `0x748654` |  |
| `$18` | Dan | Dan | non | 1 / 2 / 0 % | `0x7101D0` | `0x747FD0` / `0x7481E4` / `0x748694` |  |
| `$1A` | Sakura | Sakura | non | 1 / 3 / 0 % | `0x710590` | `0x747FD8` / `0x7481F4` / `0x7486D4` |  |
| `$1C` | Rolento | Rolento | non | 2 / 1 / 4 % | `0x710950` | `0x747FE0` / `0x748204` / `0x748714` |  |
| `$1E` | Dhalsim | Dhalsim | non | 20 / 1 / 0 % | `0x710C90` | `0x747FE4` / `0x748214` / `0x748754` |  |
| `$20` | Zangief | Zangief | non | 2 / 1 / 0 % | `0x710CD0` | `0x747FE8` / `0x748224` / `0x748794` |  |
| `$22` | Gen/Gen (variante) | Gen, id13 | non | 2 / 0 / 6 % | `0x710DD0` | `0x747FF0` / `0x748234` / `0x7487D4` |  |
| `$24` | Chun-Li/Chun-Li (variante) | — | non | 1 / 1 / 0 % | `0x70ED70` | `0x747F98` / `0x748164` / `0x748494` | $08 |
| `$26` | Gen/Gen (variante) | — | non | 2 / 0 / 6 % | `0x710DD0` | `0x747FF0` / `0x748234` / `0x7487D4` | $22 |
| `$28` | Sodom/Sodom (variante) | — | non | 1 / 1 / 0 % | `0x70F410` | `0x747FA8` / `0x748184` / `0x748514` | $0C |
| `$2A` | Balrog/Juli/Juni | M.Bison, Juli, Juni, id27 | non | 2 / 2 / 0 % | `0x710FF0` | `0x747FC8` / `0x748244` / `0x748614` |  |
| `$2C` | Cammy | Cammy | non | 2 / 1 / 0 % | `0x711010` | `0x747FF8` / `0x748254` / `0x748814` |  |
| `$2E` | Ryu/Evil Ryu | EvilRyu | non | 0 / 0 / 3 % | `0x711150` | `0x747F8C` / `0x748144` / `0x748414` | listes=$04 |
| `$30` | E.Honda | E.Honda | non | 2 / 3 / 11 % | `0x711210` | `0x747FFC` / `0x748274` / `0x748854` |  |
| `$32` | Blanka | Blanka | non | 2 / 1 / 0 % | `0x7115D0` | `0x748004` / `0x748284` / `0x748894` |  |
| `$34` | R.Mika | R.Mika | non | 2 / 1 / 2 % | `0x711650` | `0x74800C` / `0x748294` / `0x7488D4` |  |
| `$36` | Cody | Cody | non | 1 / 0 / 2 % | `0x711A10` | `0x748014` / `0x7482A4` / `0x748914` |  |
| `$38` | Vega | Vega | non | 2 / 0 / 1 % | `0x711AD0` | `0x74801C` / `0x7482B4` / `0x748954` |  |
| `$3A` | Karin | — | non | 1 / 2 / 0 % | `0x711B10` | `0x748024` / `0x7482C4` / `0x748994` |  |
| `$3C` | Balrog/Juli/Juni | — | non | 2 / 2 / 0 % | `0x710FF0` | `0x747FC8` / `0x748244` / `0x748614` | $2A |
| `$3E` | Balrog/Juli/Juni | — | non | 2 / 2 / 0 % | `0x710FF0` | `0x747FC8` / `0x748244` / `0x748614` | $2A $3C |
| `$40` | neuf (Upper) | Guile | non | 1 / 1 / 1 % | `0x711ED0` | `0x74802C` / `0x7482D4` / `0x7489D4` |  |
| `$42` | neuf (Upper) | Fei-Long | non | 3 / 1 / 3 % | `0x7122D0` | `0x7480AC` / `0x7482E4` / `0x748A14` |  |
| `$44` | neuf (Upper) | DeeJay | non | 1 / 1 / 0 % | `0x7126D0` | `0x7480B4` / `0x7482F4` / `0x748A54` |  |
| `$46` | neuf (Upper) | T.Hawk | non | 2 / 0 / 2 % | `0x712AD0` | `0x7480BC` / `0x748304` / `0x748A94` |  |
| `$48` | neuf (Upper) | ShinAkuma | non | 0 / 0 / 3 % | `0x712ED0` | `0x747F8C` / `0x748144` / `0x748414` | listes=$04 |
| `$4A` | neuf (Upper) | Balrog, EX-Balrog | non | 0 / 1 / 0 % | `0x712F90` | `0x7480C0` / `0x748314` / `0x748AD4` |  |
| `$4C` | neuf (Upper) | Karin | non | 2 / 2 / 0 % | `0x713390` | `0x7480C4` / `0x748324` / `0x748B14` |  |
| `$4E` | neuf (Upper) | (attraction / VERSUS) | **oui** : décor 4/6 d'Hyper | **99 / 100 / 100 %** | `0x713790` | `0x7480CC` / `0x748334` / `0x748B54` |  |

Lecture :
- **Manquent dans Hyper : 39 décors sur 40**, données et graphismes. Seul `$4E` y est (décors 4 et 6).
- Les 32 décors `$00-$3E` sont ceux de SFA3 (graphismes à 99,8-100 % dans e256).
- Les décors propres à Upper sont `$40` Guile, `$42` Fei-Long, `$44` Dee Jay, `$46` T.Hawk, `$48` Shin Akuma (listes
  d'Akuma, palettes propres), `$4A` Balrog et EX Balrog, `$4C` Karin, `$4E` (attraction ; = ZERO 3 d'Hyper).
- Upper a changé 3 entrées de la table de SFA3 (`0x593690`) : Balrog `$2A → $4A`, Evil Ryu `$00 → $2E`,
  Karin `$3A → $4C`.
- Où les trouver dans Upper :
  - données : tables ci-dessus (module `ro5`) ;
  - tuiles : e353 / e525, déjà rangées dans `work/mame_ro5/hsfa_plans.bin`.

---

## 2. Choix du décor en Arcade greffé

### 2.1 Chaîne d'Upper (mode Arcade)

1. `0x24EA30` (préparation du combat, rival) appelle **`0x24F020`** avec `D0` = perso adverse (`$103` de sa
   structure). `0x24F020` est aussi appelée par `0x250700`, `0x250EF0` et `0x251320` (recherche de l'adversaire).
2. `0x24F020` (arcade `≈ $B81C`) :
   - `$172 = $100` (décor précédent), en `0x24F2A8` ;
   - `0x251950` : `D0 = T_61BE10[D0]` (exéc. `0x61BE10`, fichier `0x42BE10`, 40 octets) ;
   - `$174 = 2 × D0`, en `0x24F2F4` ; puis `CLR.B $110` ;
   - cas spéciaux : `$114 = 5` → `$174 = $14` (Bison final, `0x24F49C`, `0x24F710`) ; rival
     `T_61B6D0[perso]` → `$174`, `$110 = $FF` (`0x24F980`) ; tests de `$C39F`, `$169`, `$AD`, `$87F1`.
3. `0x2489E0` (scène 4, défi intercalé) : `$100 = $174 = $2A` ou `$14` selon `T_61B680`.
4. `0x2615D0` (init de match Arcade, arcade `$90A8`) : **`$100 = $174`** en `0x261B30`.
5. Scènes Arcade : `0x2EE80` pose `$100 = $FF007A` (cas `$30 → $18`) ; `0x2CAC0` fait défiler le décor
   (`T_60B400`).
6. Lecteurs de `$100` : §1.2.

### 2.2 Homologues dans Hyper

| rôle | Upper | Hyper | état |
|---|---|---|---|
| préparation du combat (rival) | `0x24EA30` | `0xA43F0` | identique, vivante (appelée en `0x318E38`) |
| choix du décor | `0x24F020` | `0xA49E0` | apparentée (52 %) : même structure ; tests d'Arcade retouchés (`$C39F` retiré, `CMP.B $87F1,$115` remplacé par `CMPI.W #$1A,$114`) |
| perso → décor | `0x251950` + `T_61BE10` (40) | `0xA5CF0` + `T_5B6220` (128, versions) | table remplacée |
| décor du rival | `T_61B6D0` | `T_5B6030` | identique (valeur `$0A` → `$174 = $14` : déborde des tables à 4 entrées) |
| défi intercalé | `0x2489E0` + `T_61B680` | — | absent |
| init de match | `0x2615D0` (`$100 = $174`) | `0x96690` (`$100 = $174` en `0x96C20` ; rotation `$C178` en `0x96C34`/`0x96C48`) | remplacée |
| nouveau challenger | `0x258450` : `$100 = 2 × $103` | `0x31D6A0` quasi identique | **débordement** possible (ids jusqu'à `$7F`) |
| VERSUS (choix du décor) | `0x25F570` : `$100 = $172 = $174 = $C314` | `0x321220` identique | — |
| attraction | `0x263C10`, `0x26F680` (`T_61C110`, 40) | `0x98590`, `0xA05C0` (`T_5B5CB0`/`T_5B5CC0`, 8) | modifiées |

Variables :
- `$100` décor courant, `$174` décor du combat suivant, `$110` drapeau rival : communs aux deux jeux.
- `$172` (décor précédent) : écrit par Hyper, jamais lu (le lecteur d'Upper `0x196F50` est absent).
- `$C178` : propre à Hyper (11 accès : `0x96690`, `0x60570`, `0x61180`, `0x61240`, `0x61300`, `0x626E0`, `0x98590`,
  `0xA05C0`).
- `$C314` : décor du VERSUS et de l'attraction.
- `$DC/$DD`, `$C38C` : intro et attraction d'Upper seulement. Pas utiles à l'Arcade.

### 2.3 Articulation proposée

**Numérotation unique** (tables étendues, comme `ext_c80000` de SFA3) :
- `$00-$4E` : décors d'Upper, **numéros inchangés**. Le code hérité compare `$100` à `$38`, `$1E`, `$14`, `$04`, `$30`
  (Hyper garde `$38` et `$1E`). Garder les numéros garde ces cas.
- `$50-$72` : décors SFA2 (règle `$50 + s` de DECOR-SFA2, inchangée).
- `$78` / `$7A` / `$7C` : ZERO 3, ZERO, ZERO 2 d'Hyper (aujourd'hui 4, 0, 2). `$78` reprend les données de `$4E`.
- Variantes de couleur : entrées supplémentaires des **seules** tables A/B/C, à `$100 + $C178` (`$80…$94`).
  - Les sites `ADD.W $C178(A5),D0` restent tels quels. Les tables A/B/C passent à 75 entrées, les autres à 63.

**`$C178`** :
- ne tourner que pour les décors d'Hyper : en `0x96C34`/`0x96C48`, `si $100 ≥ $78 : rotation, sinon CLR.W $C178` ;
- le mettre à 0 à l'entrée de l'Arcade si l'init greffée est celle d'Upper (`0x2615D0` n'y touche pas).
- Sans cela, `$100 + $C178` tombe sur un autre décor (pas de 8 = 4 décors).

**Table perso → décor : une seule table de 128 octets**, indexée par l'id étendu (`$103` de l'adversaire) :
- ids `$00-$27` (ZERO 3) : valeurs de `T_61BE10` (décors d'Upper) ;
- ids `$30-$3F` (ZERO) : `$7A` (Grande Muraille), en attendant des décors SFA1 ;
- ids `$40-$7F` (ZERO 2 / ALPHA) : décor SFA2 du perso quand il est importé, sinon `$7C` (chute d'eau).
- Elle remplace `T_61BE10` (40 entrées, déborde au-delà de `$27`) et `T_5B6220`. Pas besoin de `$116` ici.

**Où brancher** :
- en Arcade, la routine greffée d'Upper `0x24F020` (ou `0xA49E0` d'Hyper, déjà vivante, avec ses tests d'Arcade
  rétablis) lit la table de 128 octets ;
- le crochet du tirage SFA3/SFA2 (`$4A428` dans SFA3) se pose sur l'écriture de `$174` : `0x24F2F4` (greffé) ou
  `0xA4A68` (Hyper) ;
- en VERSUS, Hyper garde son choix par version (valeurs de `T_5B6220` renumérotées `$78/$7A/$7C`, plus
  `T_5B5CB0` pour l'attraction).

**À corriger en même temps** :
- `0x31D6A0` (`$100 = 2 × $103`) : passer par la table, sinon `$100` va jusqu'à `$FE` ;
- `T_5B6030` (rival) : `$14` devient valable une fois les tables étendues (Bison final) ;
- trampolines d'alias SFA2 (« `$100 ≥ $50` → `$100 − $50` ») : les limiter à `$50-$72`.

**Alternative minimale** (sans les décors d'Upper) : garder les décors d'Hyper en Arcade (choix par version). Aucun
changement de table, mais l'Arcade perd ses décors par adversaire.

---

## 3. Compatibilité avec les chantiers faits sur SFA3

### 3.1 Injection widescreen (INJECTION-FORK : 18 `LEA`, bloc externe, 32 palettes par décor)

Les sites se retrouvent dans les trois modules **par l'adresse PS2 de la constante** dans `carte_image.txt`
(`sites_injection.py`, méthode de `blocs_tr.depuis_carte`). Pour ro3, on retrouve exactement les 18 sites
d'INJECTION-FORK §3.

| donnée | SFA3 (image) | Upper (image) | Hyper : va MIPS → image |
|---|---|---|---|
| type s1 (non relogé) | `$024D86` | `$02DFBA` | `0x313AC4` → `$07867E` |
| listes s1 / s2 / s3 | `$024DA2` `$0251EC` `$0252F2` | `$02DFD6` `$02E40C` `$02E4EA` | `0x313B00` `0x315814` `0x315C74` → `$07869A` `$078AD0` `$078B9C` |
| blocs s1 (4) | `$024EDA…$0250DC` | `$02E0FE…$02E314` | `0x314154` `0x3149B8` `0x314ED8` `0x314F7C` → `$0787C2` `$07890E` `$0789C0` `$0789D8` |
| super-tuiles (3) | `$024FB0…$0250F0` | `$02E1E8…$02E328` | `0x3147C0` `0x314C94` `0x315010` → `$0788AC` `$078954` `$0789EC` |
| blocs s2 / s3 | `$025296` / `$02538A` | `$02E4A6` / `$02E572` | `0x315B2C` / `0x315F6C` → `$078B58` / `$078C24` |
| palettes s1 / s2 / s3 | 2 + 2 + 2 | 2 + 2 + 2 (+ 2 sprites) | A `0x605B8`, `0x611C8` ; B `0x61288` ; C `0x61348` → `$009234` `$00942C` / `$00944A` / `$009468` |
| anneau scroll1 | `$9C1E0` (mots +0, +8) | `T_6145F0` (`0x14FF50`) | `T_5C5230` (`0x3144C0`) : mêmes valeurs `$FFC0` |
| **total relogeable** | **18** | **20** | **16** |

Ce qui change pour Hyper :
- **Palettes à variantes** : un décor d'Hyper a jusqu'à 4 blocs par plan. Une palette neuve doit être écrite dans
  chaque variante, avec la couleur de la variante.
- `0x3E3A0` vise directement les palettes du décor 0 (`0x660260`, `0x661E80`, `0x6642A0` ; image `$004A8A` `$004A98`
  `$004AA6`). Les laisser pointer sur les données d'origine.
- Codes locaux libres (mode « bases de plans ») : scroll2 `$5B00-$BFFF` (26 368 places) ; scroll3 `$380` et au-delà.
  Scroll1 : la vue 8×8 d'e546 (93 184 tuiles) remplit les 65 536 codes. Les décors d'Hyper n'utilisent que `≤ $3D8E`,
  mais les autres écrans restent à recenser.
- Bloc externe : `$C80000` est pris dans Hyper (`ext_c84000` = fichier 547 jusqu'à `$D0B188` ; `ext_940000` jusqu'à
  `$BCE200`). Libre : `$BCE200-$C83FFF` (≈ 720 Ko) ou à partir de `$D0C000`.
- `HSFA_PLANS_VIDE15` vaut déjà 1 pour ro9.

### 3.2 Import SFA2 (DECOR-SFA2 : 58 correctifs, numéros `$50+`, tables à 58 entrées)

Répartition des 58 correctifs de `import/essai_alea/rapport.json` (détail : `correctifs_sfa2_hyper.tsv`) :

| où | correctifs ro3 | Hyper |
|---|---|---|
| **sites d'Hyper** | 31 : bibliothèques 9, type s1 1, listes 3, palettes 6, CPS-B 2, ROUND 2, tables de sauts 4 (ordre des plans, gestionnaires s1/s2/s3), effet 1, animation de palettes 2, sélection 1 | **28 sites** : bibliothèques 9, type 1, listes 3, palettes **4** (A ×2, B, C), CPS-B 2 (`T_5C51F0/F2`), ROUND 2 (seulement au-delà de `$4E`), tables de sauts 4 + effet 1 (+ tables de mots `T_5C50B0`, `T_5C50C0`, `T_5C9E00`, `T_5C9E08`), animation de palettes 1 (`0x38D510`), sélection 1 (`0xA4A68` ou site greffé) |
| **code d'Upper à greffer** (absent d'Hyper) | 13 : palettes de sprites 2, objets 2, positions 2, ordre des plans (fins) 1, animations par décor 2, animations d'objets et données par décor 2, masques 2 | **13 sites**, à poser sur le code greffé (§1.2), comme sur Upper |
| **inutiles** | 13 : types s2/s3 2, longs `$40/$44` 6, init joueurs 5 | **13** : constantes dans Upper et Hyper |
| à refaire | musique 1 | Hyper n'a pas de musique par décor (`0x139AD0` absent) ; crochet à placer sur son choix de musique (non étudié) |

Pour Hyper, les tables étendues n'ont pas 58 entrées mais 63 (75 pour A/B/C), selon la numérotation du §2.3.

### 3.3 Factorisation

**Oui : un seul outil, paramétré par module.**
- Les sites se trouvent par adresse PS2 dans `carte_image.txt` ; seules les constantes changent.
- Il faut seulement réécrire les adresses d'image codées en dur de `construit.py` (SFA2) en recherches par constante,
  comme le fait `injection_fork.py`.

| constante | ro3 (SFA3) | ro5 (Upper) | ro9 (Hyper) |
|---|---|---|---|
| type s1, listes s1 / s2 / s3 | `0x67C630`, `0x67C670` / `0x67C79C` / `0x67C9CC` | `0x747EE0`, `0x747F30` / `0x7480D4` / `0x748344` | `0x695FF0`, `0x695FF8` / `0x696010` / `0x696048` |
| blocs s1, super-tuiles, blocs s2, blocs s3 | `0x5F72B0`, `0x5FA1B0`, `0x61F3F0`, `0x63A9F0` | `0x69B830`, `0x69F3B0`, `0x6CF5F0`, `0x6EF3F0` | `0x63DA20`, `0x63DD20`, `0x640960`, `0x643C60` |
| palettes s1 / s2 / s3 ; sprites | `0x651610` / `0x655AF0` / `0x65C950` ; — | `0x70E560` / `0x7147E0` / `0x71D420` ; `0x707D10` | `0x660240` / `0x661E60` / `0x664280` ; — |
| entrées par table ; index des palettes | 32 ; `$100` | 40 ; `$100` | 4 ; **`$100 + $C178`** (16) |
| ajout au code s2 (vue 16×16) | `$1600` | `$1C00` | **`$1000`** |
| mémoire de décor ; 32×32 | e256 ; e312 (4 096) | e353 ; e525 (4 576) | e546 ; e548 (896) |
| codes libres s1 / s2 / s3 | `$6000+` / `$8A00-$BFFF` / `$1000+` | à mesurer / `$A600-$BFFF` / `$11E0+` | à mesurer / `$5B00-$BFFF` / `$380+` |
| bloc externe | `$C80000` | `$E00000` (FBNeo) | `$D10000` (ou `$BD0000`) |
| anneau scroll1 | `$9C1E0` (image) | `T_6145F0` | `T_5C5230` |
| `carte_image.txt` | `work/mame` | `work/mame_ro5` | `work/mame_ro9` |
| décors liés | `$00/$2E`, `$08/$24`, `$0C/$28`, `$22/$26`, `$2A/$3C/$3E` | `$08/$24`, `$0C/$28`, `$22/$26`, `$2A/$3C/$3E` ; listes seules `$04/$2E/$48` | `4/6` |

Le cas d'Hyper ajoute deux paramètres : le pas des variantes (`$C178`, 4 × 8) et la liste des sites qui visent
directement un bloc de palettes (`0x3E3A0`).

---

## Plan

1. **Numérotation et choix du décor** (petit, sans graphisme) :
   - table perso → décor de 128 octets ; crochet `$174` (`0xA4A68`, puis le site greffé) ;
   - `$C178` conditionnel en `0x96C34`/`0x96C48` ; `T_5B6220` et `T_5B5CB0` renumérotés `$78/$7A/$7C` ;
   - correctif de `0x31D6A0`.
   - Contrôle : VERSUS d'Hyper inchangé (mêmes décors, mêmes variantes).
2. **Données** : tables étendues dans le bloc externe d'Hyper (`$D10000`).
   - Upper `$00-$4E` + Hyper `$78-$7C` (+ variantes A/B/C).
   - Bibliothèques fusionnées : blocs d'Hyper renumérotés après ceux d'Upper (s1 119 + 6, s2 170 + 17 : tient sur
     un octet ; s3 à vérifier, Upper cite jusqu'au bloc 156).
   - Sites : 16 `LEA`, 5 tables de sauts (trampolines), 4 tables de mots, CPS-B (2 lectures), ROUND (2).
3. **Graphismes** : relogement des codes dans `hsfa_plans.bin` d'Hyper (méthode d'`injection_fork.py`).
   - scroll2 : 14 330 tuiles dans `$5B00-$BFFF` ; scroll3 : 3 122 tuiles à partir de `$380` (reste sous 64 Mo) ;
   - scroll1 : 22 566 tuiles. D'abord recenser les codes scroll1 d'Hyper hors décors. S'il manque de la place :
     bases de plans par famille (mémoires d'Upper rangées sous `$3000000`, bases écrites au chargement du décor ;
     à vérifier dans le cœur FBNeo, qui écrit aujourd'hui les bases à la 1ʳᵉ image).
4. **Code de décor d'Upper** (≈ 75 Ko, 239 routines) avec la greffe MIPS (étape 0f de l'étude) :
   - gestionnaires et effets manquants, objets de décor et leurs palettes, positions, animations, masques, musique
     par décor ;
   - les tuiles des objets de décor (emplacement 1) sont à reloger comme celles de scroll2.
5. **Validation contre Upper** :
   - chaque décor `$00-$4C` forcé par `$FF8100` : plans au pixel près contre Upper (`compare_plans.py`) ;
   - puis une partie Arcade complète par perso ZERO 3 : même décor par adversaire qu'Upper.
6. **Ensuite seulement** : widescreen (`etape_decors.py` avec les constantes ro9) et SFA2 (`construit.py`
   réécrit par constantes), sur la numérotation du §2.3.

Limites :
- Les variantes `$C178` = couleurs : déduit des tables, pas vu à l'écran.
- Noms des ids `$12-$14` non tranchés.
- Code par décor : borne haute (graphe approché, profondeur 3), et la copie exacte sous-estime la présence.
- Codes scroll1 libres d'Hyper : à mesurer.

---

## Fichiers (`work/greffe_arcade/decors/`)

Interpréteurs : `python3` système, ou `<workspace>/venv/bin/python3` (numpy) pour `gfx_cmp.py`,
`tuiles_decor.py` et `capacite.py`. Lancer en `nice -n 19`.

| script | rôle | sortie |
|---|---|---|
| `sites_a5.py [DEP…]` | accès A5 (`$100`, `$172`, `$174`, `$C178`, `$DC`, `$110`), partenaire et couverture | `sites_a5.tsv` |
| `lecteurs.py MOD` | traduction 68K autour des accès, constantes PS2 | `lecteurs_ro5.txt`, `lecteurs_ro9.txt` |
| `consts.py MOD VAL…` | sites MIPS d'une constante 32 bits | — |
| `homol_const.py VAL…` | constante d'Upper → routine → partenaire → constante homologue | — |
| `donnees_decor.py` | blocs de données par décor d'Upper, présence dans Hyper ; tables d'Hyper | `donnees_decor.tsv` |
| `biblio.py` | bibliothèques de blocs, présence | — |
| `gfx_cmp.py` | mémoires de décor e256 / e353 / e546, conteneurs 32×32 | `gfx_cmp.txt` |
| `tuiles_decor.py` | tuiles par décor et par plan, présence dans Hyper et SFA3 | `tuiles_decor.tsv`, `tuiles_decor.txt` |
| `capacite.py` | tuiles neuves à loger pour `$00-$4C` | `capacite.txt` |
| `gestionnaires.py` | tables de sauts par décor : cibles, partenaires | `gestionnaires.tsv` |
| `routines_exactes.py`, `code_decor.py`, `exact_groupes.py` | code de décor d'Upper, copies exactes, couverture | `routines_exactes.txt`, `code_decor.tsv`, `code_decor_exact.tsv` |
| `inventaire.py` | tableau décor par décor | `inventaire_decors.tsv`, `inventaire_decors.md` |
| `sites_injection.py` | sites `LEA` des données de décor par module (carte d'image) | `sites_injection.tsv` |
| `tables_tsv.py` | tables par décor Upper → Hyper ; 58 correctifs SFA2 → Hyper | `tables_par_decor.tsv`, `correctifs_sfa2_hyper.tsv` |
| `ecrit_doc.py` | assemble ce document (gabarit `DECORS.gabarit.md` + tableau) | `DECORS.md` |
