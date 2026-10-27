# Étude « méthode Capcom » des persos MAX (Eagle, Maki, Yun, Ingrid)

Rapport du 27/10. La tête (§0) a été écrite en premier, à la demande du coordinateur.
Données lues sur place et jamais copiées dans un dépôt : seulement des noms de symboles et des adresses.
- CvS2 PS2 US `SLUS_202.46` (md5 c3d7795d…) et JP `SLPM_650.47` : `.symtab` seule.
- CFE PS2 `SLUS_209.50` (md5 ed206e8c…) : `.symtab`, DWARF 1 et `.line`.
- EBOOT EU de MAX : md5 4b2589b6…
- La lecture des tables PSP passe par les brouillons de la session MAX (`brouillon_*.s`), en lecture seule. Ils ont été recoupés avec l'EBOOT.

## 0. En bref : préfixes et convention (établis)

| perso MAX | jeu d'origine | préfixe | preuve (résumé) | confiance |
|---|---|---|---|---|
| Eagle | CvS2 | **pl23** | noms des tests : `cmd_golf_ck` (St Andrew's **Green**, golf), `cmd_guard_ck` (Canterbury Blue), `cmd_kaiten_ck` (Manchester Black), `cmd_kisyu_ck` (Liverpool White), `cmd_tsuki_ck` (Oxford Red) ; numérotation des spéciaux = PSP | mesuré |
| Maki | CvS2 | **pl24** | `cmd_hayagake_ck`, `cmd_reppu_ck` (KKK), `cmd_delta_ck` / `cmd_delta2_ck` (Hassoukyaku), `cmd_izuna_ck` (Tengu Daoshi), `cmd_tonfa_ck` (Genko), `cmd_sp_izuna_ck` (720 = Ajaratengu) ; numérotation = PSP | mesuré |
| Yun | CvS2 | **pl2c** | `cmd_tensin_ck` (Zenpou-tenshin), `cmd_tetu_ck`, `cmd_zetu_ck`, `cmd_kyuu_ck` (Senkyutai), `cmd_tora_ck` (Kobokushi), `cmd_sp_you_ck`, `cmd_sp_ren_ck`, `cmd_sp_maha_ck` (Raishin Mahhaken) ; numérotation = PSP | mesuré |
| Ingrid | CFE | **pl22** | tests 236P / 236K / 214P / 214K (sol → spécial 3, air → spécial 7 : Sun Lower, Sun Dive) / 623K / 236236P / 214214K / 214214P (jauge ≥ 210) ; `pl22_atemi_set` (contres) ; numérotation des spéciaux et nombre de sous-états = PSP | mesuré |

Dans CFE, **pl2c reste Yun** (même identifiant que dans CvS2, code dérivé de celui de CvS2). **pl2d est Shin Akuma** (`btn_aa6dc_check`, c'est-à-dire LP LP → LK HP, et les Ashura). **pl15 est Pyron** (`sol_ck`, `orb_ck`, `warp*_ck`, `stardust_ck`). La table `pl_id_tbl` (0x2BDC50, ordre de la sélection) ne suit **pas** l'ordre des chaînes « theme of » : c'est pourquoi la piste N18 hésitait entre pl2c, pl2d et pl2e. **pl2e** n'est pas un perso : seul `pl2e_words` existe.

**Convention Capcom (commune à CvS2, CFE et MAX PSP)** :
- `plXX_init`, `_atck`, `_jatck_set`, `_win`, `_appear`, `_special_ck`, `_special`, `_nage` : un gestionnaire par rôle. Chacun est appelé par une table globale indexée par l'identifiant du perso (`pl_init_jmp`, `pl_mv05_jmp` = atck, `pl_mv08_jmp` = special, `pl_move2_jmp` = nage, `pl_move4_jmp` = win, `pl_move7_jmp` = appear, `pl_jatck_jmp`, `pl_sp_ck_jmp`). Sur PSP, ce sont les mots du **gabarit** du perso : +0x40 atck, +0x44 jatck_set, +0x48 win, +0x4C appear, +0x50 special_ck, +0x58 special, +0x60 nage.
- `plXX_special_ck` : la chaîne des tests de commande (`cmd_236p_check`… ou `cmd_<nom>_ck`). Le premier test qui réussit écrit le **n° de spécial** (mot +0x200 sur PS2, `$AA`/2 sur PSP et arcade).
- `plXX_special` : aiguillage par n° de spécial vers `plXX_spN` (N en hexadécimal : sp0…sp9, spa, spb, spc).
- `plXX_spN` : aiguillage par l'octet +7 (sous-état, ou « phase ») vers `plXX_spNM`. **M = n° de phase**, ni la force ni le bouton. La table se termine souvent par la fonction commune `pl_suki_move` (récupération), qui est **psp_cfa88** sur PSP.
- `plXX_nml_pNN` / `nml_kNN` / `sit_pNN` / `sit_kNN` / `jatckNN` : coups normaux debout P/K, accroupis P/K et sautés. L'entrée 00 lance le coup ; l'entrée 1 est la commune `pl_atck_move` (**psp_69678**) ; les entrées 02 et suivantes sont les phases propres aux coups de commande.
- `plXX_nageN` (prises), `plXX_winN` (poses de victoire), `plXX_appearN` (entrées en scène) : même principe, phase N.
- Objets du perso : `pls<XX>_*` (effets d'accompagnement) et `pshl<XX>_*` (« shell » = projectile avec test de collision), avec des sous-types `pshlXX_00/01/02`.
- **La numérotation des spéciaux est conservée telle quelle sur PSP** pour les quatre persos. La PSP ajoute des numéros en fin de liste (custom combo, contre-alpha V, etc.).

Noms d'IA croisés dans les `.symtab`, non analysés (le périmètre IA revient à la session MAX) : voir §7.

Niveaux de confiance employés partout :
- **mesuré** : au moins deux indices indépendants, l'un de structure et l'autre de contenu. Indices de structure : rang dans une table appariée, même nombre d'entrées. Indices de contenu : mêmes numéros passés au moteur, même suite d'appels moteur, même commande.
- **déduit** : un seul de ces indices, ou deux binaires Capcom concordants sans indice de contenu.
- **supposé** : rang dans une table dont le nombre d'entrées diffère, sans autre indice.

## 1. Méthode et outils (tout dans `work/etude_capcom_max/`)

Outils (`outils/`) :

| outil | rôle |
|---|---|
| `symtab.py` | symboles des ELF PS2 |
| `desas_cfe.py` | désassemblage annoté, capstone ; `mipsdis.py` saute les instructions propres à l'EE |
| `carte_speciaux.py` | chaîne « test de commande → n° de spécial », côté PS2 |
| `tables_perso.py` | tables `plXX_*_tbl` |
| `chaine_speciaux_psp.py` / `arbre_psp.py` | même lecture côté PSP, dans les brouillons de la session MAX (lecture seule ; adresses de tables recoupées dans l'EBOOT) |
| `apparier.py` | descente parallèle des tables, depuis le gabarit PSP et les tables globales `pl_*_jmp` |
| `champs_vote.py` | vote des champs |
| `ecrire_tsv.py` | écriture de `re_ajouts/max_psp.tsv` |

Données de travail (`donnees/`, hors dépôt) :
- copies des exécutables ;
- `appariements.json` (497 paires, Yun compté deux fois : CvS2 et CFE) ;
- `carte_moteur.tsv` (55 noms moteur votés) ;
- `champs_vote.tsv` ;
- `cfe/playerwork.txt` (champs DWARF).

Le projet Ghidra de la session MAX n'a pas été ouvert. On compare des **formes**, jamais des octets :
- la structure des tables d'aiguillage ;
- le nombre d'entrées ;
- les entrées communes (`pl_suki_move` = psp_cfa88, `pl_atck_move` = psp_69678) ;
- les numéros passés aux fonctions moteur (anim, fiche, sous-type de tir, voix) ;
- la suite des appels moteur, une fois la carte moteur apprise par vote.

## 2. Préfixes : preuves détaillées

**CFE.**
- La table `pl_init_jmp` (0x2B7A80, 48 entrées indexées par l'identifiant) contient 23 vrais `plXX_init` : 00, 02, 03, 04, 0A, 0B, 10-16, 18-1D, 1F, 22, 2C, 2D. Les cases vides valent `pl00_init`.
- La table `pl_id_tbl` (0x2BDC50, 23 octets) donne l'ordre de la sélection, et `pl_new_id_tbl` son inverse.
- Ingrid = **pl22**, par la chaîne `pl22_special_ck` (0x2046F0), avec n° de spécial = mot +0x200 = `pl_sp_kind` :
  - 236P → 0, 236K → 4, 214P → 2, 623K → 10 ;
  - 214K au sol → 3, en l'air → 7 (dans `cmd_jp_senpu_ck`, 0x204480) ;
  - 236236P → 6, 214214K → 8 (jauge ≥ 140), 214214P → 9 (jauge ≥ 210) ;
  - provocation → 1.
  - Soit 10 spéciaux, conformes à la liste d'E-COUPS (Sun Shot, Sun Rise, Sun Upper, Sun Lower, Sun Arch, Sun Dive, Sunburst, Sunshine, Sun Delta). Seul **pl22** possède `atemi_set` (contres).
- Contre-preuves :
  - pl2d porte `btn_aa6dc_check` (LP LP → LK HP), `cmd_421p/k` + PP/KK (Ashura), `hadou_ck`, `senpu_ck` : c'est Shin Akuma ;
  - pl2c porte 623P / 236P / 214P / 63214K / 623K + EX : c'est Yun ;
  - pl15 porte `sol_ck`, `orb_ck`, `warp*_ck`, `stardust_ck` : c'est Pyron.
- Les tables de musique « theme of X » sont rangées par série et non par identifiant : ne pas s'en servir pour deviner.

**CvS2** (US `SLUS_202.46`). Les tests de commande portent le **nom du coup** (`cmd_<coup>_ck`, fonctions statiques résolues par adresse) :

| perso | préfixe | test → n° de spécial |
|---|---|---|
| Eagle | pl23 | kaiten 214P → 0, kisyu 214K → 1, tsuki 41236K → 2, golf 623P → 3, guard 236P → 4, sp_kaiten 214214P → 5, sp_ranbu 23623P → 6, provoke → 7, gc → 8 |
| Maki | pl24 | tonfa 236P → 0, hayagake 236K → 1, izuna 41236P → 2, delta2 214P → 3, delta 214K → 10 (sol) / 3 (air), reppu KKK → 4, 236236P → 5, sp_izuna (720, `round2_p_check`) → 6, 236236K → 7, provoke → 8, gc → 9 |
| Yun | pl2c | tetu 623P → 0, zetu 236P → 1, kyuu 236K → 2, tora 214P → 3, tensin 63214K → 4, sp_ren 236236P → 5, sp_you 214214P (niv. 3) → 6, provoke → 7, **sp_maha 236236K → 8**, sp_ranbu 214214K (niv. 3) → 9, gc → 10 |

Dans CFE, Yun garde l'identifiant pl2c. Son code descend de celui de CvS2 : sur les 96 fonctions PSP de Yun appariées par les deux binaires, **93 reçoivent le même nom**.

**Correspondance avec la PSP (mesuré).** La chaîne de tests PSP (gabarit +0x50, brouillons) écrit `$AA` = 2 × n. Pour chaque perso, **la même commande donne le même n° qu'en CvS2 / CFE**. Les fonctions de commande PSP se nomment par recoupement :

| fonction PSP | commande |
|---|---|
| cefac | 236P |
| cf01c | 236K |
| cf000 | 214P |
| cefe4 | 214K (air / sol, comme Capcom) |
| cef20 | 623P |
| cef3c | 623K |
| cef74 | 41236K |
| cefc8 | 41236P |
| cf070 | 63214K |
| cef58 | 236236P |
| cf038 | 214214P |
| cf054 | 214214K |
| cef90 | 236236K |
| cf4e0 | 720 |
| cf08c | KKK / plusieurs boutons |
| cf0e0 | provocation |

La PSP **ajoute en fin de liste** les numéros propres à SFA3 :
- custom combo (`661e4`, P+K de même force) : Eagle 9, Maki 12, Yun 11, Ingrid 11 ;
- contre-alpha (`66264` + `68380`, puis le rappel +0x68 du gabarit) ;
- Ingrid 12-14 (14 = `cf08c`).

## 3. Convention Capcom (détail) et correspondance avec le gabarit PSP

| rôle Capcom (table globale) | gabarit PSP | aiguillage | contrôle de forme |
|---|---|---|---|
| `plXX_atck` (`pl_mv05_jmp`) | +0x40 | posture `atck_status` (PS2 +0x1F8 / PSP +0x80), P/K `atck_kind` (+0x1F9 / +0x81), puis +7 | Yun : np 8/8, nk 7/7, sit_p 2/2, jatck 2/2 (sit_k 3 / 5) ; entrée [1] = `pl_atck_move` = psp_69678 |
| `plXX_jatck_set` (`pl_jatck_jmp`) | +0x44 | — | `pl_atck_nml` = psp_cfa6c, avec les mêmes fiches 18-31 |
| `plXX_win` (`pl_move4_jmp`) | +0x48 | +7 | 5/5 (CvS2), 4/4 (Ingrid) |
| `plXX_appear` (`pl_move7_jmp`) | +0x4C | +7 | 3/3 (CvS2), 4/4 (Ingrid) |
| `plXX_special_ck` (`pl_sp_ck_jmp`) | +0x50 | chaîne de tests | même ordre de priorité : supers d'abord, provocation et gc à la fin |
| `plXX_special` (`pl_mv08_jmp`) | +0x58 (= +0x5C) | n° de spécial (`pl_sp_kind` +0x200 / `$AA`) | voir tableau ci-dessous |
| `plXX_nage` (`pl_move2_jmp`) | +0x60 (= +0x64) | +7 | Eagle 5/5, Yun 3/3, Maki 2 tables → 1 table de 6, Ingrid 6 → 3 |
| — | +0x68 | rappel n°26 = contre-garde | Maki : spécial 9 = `gc` Capcom (déjà dans max_psp.tsv) |
| `plXX_init` (`pl_init_jmp`) | racine du perso (hors gabarit) | — | non apparié ici |

Nombre d'entrées (sous-états, `pl_suki_move` compris) par spécial, Capcom → PSP :

| perso | Capcom | PSP |
|---|---|---|
| Eagle | 3 4 5 3 **3** 8 7 3 2 | 3 4 5 3 **4** 8 7 3 2 + 3 3 |
| Maki | 3 15 10 **10** 5 6 13 8 3 5 7 | 3 15 10 **15** 5 6 13 8 3 5 7 + 15 (= 3) 3 2 |
| Yun | 3 4 8 2 4 6 4 2 5 12 5 | **identique** + 3 2 |
| Ingrid | 3 4 4 4 6 3 4 5 **8** 11 4 | 3 4 4 4 6 3 4 5 **10** 11 4 + 3 4 2 2 |

Bilan : **41 spéciaux sur 44** ont le même nombre de phases. Les mêmes particularités se retrouvent :
- `pl_suki_move` au même rang et une entrée après lui (Eagle sp5, Maki sp1 et spa) ;
- une même fonction pour deux numéros : Ingrid 2 = 3 (CFE `pl22_sp_tbl[3] = pl22_sp2`, PSP 0x1C3CA0 deux fois).

Les trois écarts sont des coups retouchés pour MAX :
- Eagle sp4 (Canterbury Blue, garde maintenue) ;
- Maki sp3 (Hassoukyaku, qui partage des phases de Hayagake) ;
- Ingrid sp8 (Sunshine).

Autres détails de convention :
- La **phase** M est l'octet +7 (`routine_3` du DWARF ; +4 à +7 = `routine_0` à `routine_3`, comme sur arcade et PSP).
- Coquille de Capcom : la table de `pl23_sp8` s'appelle `pl23_sp7_tbl$688`.
- Objets fils :
  - `plsXX_*` : effets ;
  - `pshlXX_NN_{int,mov,move,die,ers}` : tirs à collision, un sous-type NN par tir ;
  - `efct*`, `ef_*` : effets communs.
- Réactions de la victime : `damage0` à `damageC` (table `damage_jmp_tbl`), puis `pl_dmN0…` par phase (§5.3).
- Les préfixes `em*` sont **l'IA** (« enemy »), pas des effets : voir §7.

## 4. Appariements (`re_ajouts/max_psp.tsv`, 409 lignes)

| | mesuré | déduit | supposé |
|---|---|---|---|
| Eagle (70) | 30 | 32 | 8 |
| Maki (111) | 74 | 32 | 5 |
| Yun (100) | 65 | 30 | 5 |
| Ingrid (87) | 39 | 30 | 18 |
| moteur commun (41) | 17 | 18 | 6 |
| **total 409** | **225** | **142** | **42** |

Le décompte inclut les 10 lignes faites à la main :
- Yun : `pshl2c_set` 0x1C0D04, `pshl2c_02`, `_02_int`, `_02_mov` ;
- Ingrid : `atemi_set` 0x1C3EC0 ;
- moteur : `pl_jump_set`, `catch_check`, `dm_cnt_calc`, `super_add`, `pl_atck_nml`.

Exemples de paires « mesuré » :

| PSP | nom Capcom | preuves |
|---|---|---|
| 0x1BDC70 | `pl2c_sp40` | anim 29 |
| 0x1BDCB4 | `pl2c_sp41` | `catch_check(47)`, `super_add(4)`, voix, `catch_hosei1`, anim 30 ; 4 appels sur 6 dans le même ordre |
| 0x1BDD48 | `pl2c_sp42` | `catch_out(47)`, `dm_cnt_calc`, `catch_hosei1` |
| 0x1BDB20 | `pl2c_sp30` | tir sous-type 2, `super_add(4)`, anim 21 |
| 0x1C3DB4 | `pl22_sp22` | riposte, fiche 38 |
| 0x1C50B0 | `pl22_sp97` | arguments 42, 48, 79 ; c'est le « lancer de la victime » déjà connu |
| 0x1C5228 | `pl22_sp99` | arguments 20, 52, 68 ; 6 appels sur 12 dans le même ordre |

Fonctions moteur nommées. Le rôle déjà établi dans max_psp.tsv concorde à chaque fois avec le nom Capcom :

| PSP | nom Capcom | rôle déjà indexé |
|---|---|---|
| 0xCFEC8 | `pl_char_move` | avancer l'anim |
| 0x5D6EC | `pl_char_set` | poser l'anim |
| 0xCF5D8 | `land_pos_ck` | au-dessus du sol |
| 0xCF1F4 | `pl_rate_add` | appliquer les vitesses |
| 0x5E004 | `pl_jump_sub` | $2AA08 |
| 0x67144 | `catch_out` | coup direct |
| 0x69DCC | `catch_hosei0` | projections |
| 0xCEE0C | `CpSnd_pl_vo_Req` | voix |
| 0x6069C | `pl_to_normal` | |
| 0xCFA88 | `pl_suki_move` | |
| 0x69678 | `pl_atck_move` | |
| 0x5DEDC | `pl_jump_set` | ferme la question R15 sur son rôle (« départ de saut ») |

## 5. Ce qui éclaire nos défauts

### 5.1 Yun

- **QCB+P = `pl2c_sp3` (tora = Kobokushi), mesuré.** La structure Capcom du coup :
  - `sp30` frappe avec le corps (anim 21, gain de jauge 4) ;
  - `sp30` crée aussi un « shell » de **sous-type 2** (`pshl2c_set(2)`) et un effet `pls2c_set(2)` ;
  - `sp31` fait trembler l'écran et revient au neutre.

  Le PSP fait la même chose : 0x1BDB20 → 0x1C0D04(…, 2) → table des sous-types 0x1C0DD0 [2] = 0x1C1854 = `pshl2c_02`. Il n'y a **pas d'équivalent de `pls2c_set(2)`** ; l'effet a disparu ou se trouve ailleurs (supposé).

  Le shell 02 :
  - s'initialise avec l'anim **11** (`pshl2c_02_int` = 0x1C18AC) ;
  - s'inscrit chaque image dans la liste de collisions (`Push_hitck`) ;
  - n'a que deux phases (200, 201).

  Dans CvS2, Kobokushi « annule les projectiles ». Ce shell est donc l'objet qui **annule les tirs**, sans attaque propre. C'est cohérent avec la boîte PSP 0x2AA98C « 02 00 » (aucune attaque) relevée par l'intégration.

  Conséquences pour Upper :
  - l'« onde » doit exister comme objet de tir **visible** (anim 11 du tir) et entrer en collision avec les projectiles ;
  - elle ne doit pas infliger de dégâts : les dégâts viennent du corps de `sp30`, ce que le banc a confirmé (16/16) ;
  - si elle reste invisible, regarder l'anim 11 du shell et le gestionnaire 0x1C19AC (`_02_mov`), pas la reconnaissance du coup.

  Les spéciaux qui créent un tir sont **3, 8 et 9 des deux côtés** (`pl2c_sp30` / `sp82` / `sp93` ; PSP table 0x2AD550).

- **Demi-tour arrière + K = `pl2c_sp4` (tensin = Zenpou-tenshin), mesuré.** Chez Capcom, c'est une **saisie** :
  - `sp41` : `catch_check(47)`, `ok_catch`, `pl_catch_sd`, voix ;
  - `sp42` : `catch_out(47)` puis `dm_cnt_calc` (compteur de coups).

  Aucun appel à `catch_dm_calc`, la fonction qui calcule les dégâts d'une projection ordinaire (`nage1`). Les « 0 dégât » ne sont donc pas codés dans le coup : ils viennent de la **fiche 47** appliquée par `catch_out` (PSP 0x67144(0x2F) = `$2E7F2`). Si Upper inflige des dégâts, il faut vérifier la fiche 47 convertie et le chemin `$2E7F2`, pas le gestionnaire. Le « passer derrière » est en fin de `sp42` (psp_1BDDD4, bornage ; défaut 0x1D330 déjà corrigé par l'intégration).

- **Manip n° 32 (↓ puis ↑) = drapeau de super-saut `sjump_flag`**, CFE +0x159, PSP **+0x33C**. `pl2c_nml_k06` (PSP 0x1BC300, mesuré) contient les mêmes tests de part et d'autre :
  - si `hit_flag` (PSP +0x7B) ≠ 0 et `sjump_flag` == 1 ;
  - alors `jump_flag` (+0x49) = 1 et appel de `pl_jump_set` (0x5DEDC).

  `pl2c_nml_k00` envoie le **pied moyen** en phase 6 avec `sjump_flag` remis à 0. C'est une **annulation en super-saut sur le pied moyen qui touche**.

  Dans CvS2, le super-saut (↓↑) est une mécanique générale. CvS2 n'a aucun test ↓↑ propre à Yun (`pl2c_special_ck` commence par `cmd_sp_ren_ck`). Le test PSP 0x1BC988 / 0x64220 (« commande 0x20 ») est donc **un ajout de MAX** qui recrée ce drapeau pour Yun (déduit).

- **Spécial 8, réservé à l'IA = Raishin Mahhaken** : `pl2c_sp8`, super ↓↘→×2+K, mesuré par le n° et la création de tir. Le code est présent sur PSP mais aucun test joueur n'y mène. E-COUPS ne le donne qu'à CFC2.

### 5.2 Ingrid

- **2×QCF+P = Sunburst = `pl22_sp6`**, mesuré. Il a 4 phases dans les deux jeux :
  - `sp60` : `combo_calc` ;
  - `sp61` : `pl_spcom_ef`, l'éclair de super, arguments 13 / 70 communs ;
  - `sp62` : `shl_super_time_set` ;
  - `sp63` : **`pshl22_set`**, la création de l'orbe.

  Le corps ne frappe pas : **les dégâts et le feu appartiennent au tir** (`pshl22_NN`, avec ses propres tables d'attaque). L'intégration l'a confirmé (corriger les boîtes **du tir** a rétabli les dégâts et la flamme). Pour la mise à feu, regarder la fiche portée par le tir (réaction 14 / 35, R5), pas celle d'Ingrid.

- **Contre QCB+P = Sun Upper = `pl22_sp2`**, mesuré. QCB+K (Sun Lower) réutilise la même fonction : spécial 3, PSP 0x1C3CA0 deux fois, comme `pl22_sp_tbl[3]`.
  - Le déclenchement est `pl22_atemi_set` = PSP 0x1C3EC0 (déduit : sous-état 4, anims 10 / 11).
  - La riposte est `pl22_sp22` = PSP 0x1C3DB4 (mesuré) : `ok_catch` puis `catch_out(…, 38)`. **La victime est lancée par la fiche 38**, pas par du code propre au coup.

  Le « droit en l'air » dépend donc des données : réaction 35 et lancer T1[83] → rangée $62 (R5 / R14). C'est le moteur des réactions qui doit le jouer.

- **Sun Delta (2×QCB+P) = `pl22_sp9`** : 0x1C50B0 = `sp97` (projection de la victime, `catch_dm_calc`, `pl_rate_add`) et 0x1C5228 = `sp99` (réception, tremblement, `catch_out`), mesuré.

### 5.3 Réactions : `pl_dm*` face à l'aiguillage PSP et à la 9e variante ($10)

- **CFE** : `damage_jmp_tbl` compte 13 familles (`damage0` à `damageC`). Chacune a ses phases `pl_dmN0…`. Les familles partagent parfois une entrée : `damage5` = [`pl_dm40`, `pl_dm51`, `pl_dm52`].
- **PSP** (0x59164 → table 0x21526C par +0x74) : **9 variantes** dont les tables de phases sont des **fenêtres d'un même tableau** (0x215290 à 0x21531C, qui se chevauchent). C'est l'organisation de SFA3 (arcade) et non celle de CFE : les noms `pl_dm*` ne se transfèrent pas un à un (constat mesuré).
- Ce qui se transfère, c'est la **forme** d'une famille de chute :
  - entrée (`pl_dm40` : effet d'étourdissement, puis enchaînement immédiat) ;
  - vol puis réception (`pl_dm41` : `pl_rate_add`, `land_pos_ck`, effet au sol, tremblement, son de chute, anim) ;
  - relevé ou rattrapage (`pl_dm42` / `47`, avec `sfz_down_esc_ck`, `down_esc_set`).
- La variante PSP 8 ($54 = $10, 0x5A600) a exactement cette forme :
  - [0] 0x5A634 et [1] 0x5A6B0 sont des copies de [0] 0x59AFC et [1] 0x59B78 de la variante 4 (même suite d'appels, sans la voix de K.O. 0x62D4C) ;
  - [2] et suivantes **pointent sur la suite commune** 0x59CE4… : même procédé que `damage5` qui réutilise `pl_dm40`.
- Pour Upper (déduit) : faire la 9e variante comme Capcom, c'est-à-dire une entrée et un vol propres puis un **saut dans la suite commune** d'une variante existante. C'est ce que proposait R14. Elle doit être appelée par la fiche (lancer T1/T2/T3) : aucun code propre à Ingrid n'est nécessaire.

## 6. Champs : `_PlayerWork_` (CFE) → PSP

Méthode : vote sur 497 paires. On aligne les suites d'accès (sens, taille) faits sur l'objet joueur. On ne transfère que **le nom et le sens** ; les décalages PS2 n'ont pas de sens côté PSP.

| PSP | nom Capcom (CFE) | votes (témoins) | sens / recoupement | confiance |
|---|---|---|---|---|
| +0x04-+0x07 | `routine_0`-`routine_3` | 286/344 (147) pour +7 | états ; +7 = phase | mesuré |
| +0x52 | `timer0` / `timer` | 8/9 + 5/6 | compteur | mesuré |
| +0x5C | `vs_player` | 8/11 (10) | adversaire (SAVOIR §3) | mesuré |
| +0x60 / +0x64 | `rate_x` / `rate_y` | 69/78, 27/32 | vitesses 16.16 | mesuré |
| +0x68 / +0x6C | `rate_gx` / `rate_gy` | 27/34, 10/14 | accélérations | mesuré |
| +0x49 | `jump_flag` | 21/33 (24) | en l'air (N16) | mesuré |
| +0x7B | `hit_flag` | 11/18 (12) | « coup porté » `$5B` (SAVOIR) | mesuré |
| +0x80 / +0x81 | `atck_status` / `atck_kind` | aiguillage `_atck` | posture / P ou K | déduit |
| +0x84 | `land_pos` | 3/3 | niveau du sol (SAVOIR) | déduit |
| +0xC2 | `atck_level` | 29/43 (29) | force du coup (1/2 posé par les supers) | mesuré |
| +0xEB | `pl_atck_flag` | 9/13 | remis à 0 au départ des spéciaux | déduit |
| +0xEC | `pl_sp_kind` | chaînes de tests | n° de spécial (`$AA`) | mesuré |
| +0x16E | `sp_gauge` | seuils comparés | jauge | déduit |
| +0x175 | `pl_enemy_flag` | 6/8 (8) | test de R10 | déduit |
| +0x1FC | `em_target_dist` | 8/11 + 10/15 | distance à l'adversaire (proche / loin) | mesuré |
| +0x218 | `pl_shl_cnt` | 9/10 | nombre de tirs en vol | déduit |
| +0x2B8 | `pl_stand_flag` | 7/8 + 6/7 | debout | mesuré |
| +0x2F0 | `pl_sw_buff` | 5/7 | tampon des boutons | déduit |
| +0x33C | `sjump_flag` | `nml_k06` | super-saut (manip 32) | mesuré |
| +0x4B / +0x4C / +0x4D | octets de +0xB0 (`trans`…) | 52/63, 22/27, 64/72 | non nommés dans le DWARF (union) | déduit |
| +0x0B | `chr_dir` | 17/24 | sens ? (SAVOIR donne +0x86) | supposé |
| +0xED | `pl_special_req` | 13/24 | | supposé |

Les champs de CvS2 au-delà de 0x1A0 ne suivent pas CFE (ex. CvS2 0x3B0 → PSP +0x5C = `vs_player`, alors que CFE nomme 0x3B0 `walk_rate_ptr`). Les noms ne valent donc que pour les décalages CFE. Détail complet : `donnees/champs_vote.tsv`.

## 7. Noms d'IA croisés (non analysés, pour la session MAX)

- CFE (161 fonctions) et CvS2 (174) : `em_*` = IA (« enemy ») : `em_read*`, `em_reada`, `em_mov(e)`, `em_atack`, `em_atck_re`, `em_guard_ck`, `em_guard_set`, `em_catch_ck`, `em_delta_ck`, `em_eye*`, `em_level_sub`, `em_level_set` (CvS2), `em_special_set`, `em_super3_ck`, `em_init_yu`, `em_reset0`-`2`… ;
- CvS2 seul : `cpu_here`, `CpuHereMain` ;
- les deux jeux : `CpuConfig`, `CpuHereCheck`.
- Correction de N18 : `em*` désigne l'IA ; les effets s'appellent `ef_*`.

## 8. Recommandations pour la suite (intégration Upper)

1. **Nommer avant de traduire.** Verser `re_ajouts/max_psp.tsv` dans l'index ; c'est à la session principale de décider. Quand un gestionnaire MAX se comporte mal, partir du nom Capcom (spécial, phase) pour savoir ce que la phase doit faire : saisie, tir, retour au neutre.
2. **Raisonner par familles de données, pas par code.** Plusieurs défauts viennent de **données moteur**, pas du code du perso :
   - fiches 38 / 47 ;
   - réactions 34-36 ;
   - tables de lancer ;
   - attaque portée par un tir.

   Pour chaque défaut, vérifier d'abord la fiche ou le tir que la phase Capcom désigne.
3. **9e variante de réaction** : à la manière de Capcom, une entrée et un vol propres puis un saut dans la suite commune d'une variante existante (§5.3).
4. **Ne pas chercher d'IA ou de tests de commande dans CvS2 pour les ajouts de MAX** : la manip 32, les numéros PSP ajoutés en fin de liste (custom combo, contre-alpha V, Ingrid 12-14) et les trois spéciaux retouchés (Eagle 4, Maki 3, Ingrid 8) sont propres à MAX. La PSP fait foi.
5. **Contrôles rapides** (pas d'émulateur ici) :
   - anim 11 du shell de Kobokushi visible dans Upper ;
   - dégâts de la fiche 47 = 0 ;
   - fiche 38 → réaction 35 → T1[83].
6. Pour aller plus loin : nommer les tables `pshl2c_*` / `pshl22_*` (tirs) et `pls*` (effets) avec la même descente. C'est une variante d'`apparier.py` ayant pour racines les tables des types d'objets fils (`max_tables_types_objets` 0x2A3174…).
