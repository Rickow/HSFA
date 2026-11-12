# Japanese Anthology (Street Fighter Zero Fighter's Generation) compared with the US disc (2026-11-12)

**Summary (English).** File-level comparison (no emulator) of the Japanese PS2 disc *Street Fighter Zero Fighter's
Generation* (SLPM-66409, v1.02) with the US *Anthology* (SLUS-21317). Workshop `<workspace>/work/anthology_jp/` (game
data there only).
- `Y_DATA.BIN` (ADX streams) is identical; in `X_DATA.BIN` 542 of 553 entries are identical: only the 10 program modules
  and `e527` differ. **No extra song or voice on the Japanese disc**: region-dependent choices are made by the code.
- Modules ro3 / ro5 / ro9: same recompiled 68K code with 10 to 13 region constants; differences are a PS2 native
  library, an added SJIS text block and, for ro3 / ro5, the arcade texts in Japanese. Addresses: ro3 unchanged on 98 %
  of its code, ro5 +112 bytes, ro9 +1,040; the sound table has the same content at another address.
- **The build refuses the Japanese ISO** (step `iso`, then `_usa` names in 161 files, module fingerprints, fixed
  addresses in the hooks and recordings). What Japan could bring: "Zero" variants (Japanese region and texts) of SFA3
  and Upper, maybe Hyper; nothing new in sound.
- **Open (user's decision, §4)**: (a) only recognise the Japanese disc in `hsfa_build.py` with a "not supported"
  message, or (b) open a "Zero 3" Japanese track (first step: short MAME bench of SFA3 translated from the Japanese
  module, against the Japanese arcade oracle 980727). The maintainer's decision of 12/11 (`docs/ATTENTES-ET-DECISIONS.md`): to
  take into account later.
- **Changes to the original text**: references to the project's private book (chapters, file names, branch) and the
  name of the download shortcut found in the archive are removed, marked « retiré au versement ». No tool kept (the
  scripts read the Japanese disc; they stay in the workshop).

---

## Original text (French, kept as is)

> Kept as written in the workshop. Only changes: personal paths written `<workspace>/...`, workshop folders written `<workspace>/work/...`, references to the private book removed (marked « retiré au versement »). Paths such as `outils/…`, `sorties/…`, `essais_demain/…`, `constr/…` are relative to the review's workshop folder (above); the tools kept are in `tools/reviews/` (see the summary).

# Anthology japonaise (*Street Fighter Zero Fighter's Generation*, PS2) : comparaison avec l'ISO US et conséquences pour HSFA

Date : 12/11/2026. Analyse de fichiers seulement (pas d'émulateur). Aucune donnée de jeu dans ce rapport : seulement
des noms, des tailles, des empreintes, des adresses et des comptes. Scripts : `scripts/` ; sorties brutes : `sorties/`.
Orientation : [retiré au versement : source privée]. Chaque point repris de cette source a été vérifié sur les
fichiers ou marqué « non vérifié ».

## 0. En bref

- L'ISO japonaise est saine et complète : SLPM-66409, v1.02, même taille et même structure que l'ISO US.
- **Y_DATA.BIN (flux ADX, 1,8 Go) est identique à l'octet.** Dans X_DATA.BIN, **542 des 553 entrées sont identiques**.
  Seuls les 10 modules de programme diffèrent (b et ro1 à ro9), plus l'entrée e527, que l'ISO US « All Unlocked »
  a modifiée.
- **Il n'y a donc pas de « chanson en plus » sur le disque japonais.** Tous ses sons, ses musiques et ses voix sont
  aussi sur le disque US, à l'octet près. La chanson du Dramatic Battle de *Zero* est un choix
  fait par le code selon la région, pas une donnée propre au disque japonais.
- Modules ro3, ro5 et ro9 : **ils ne sont pas identiques à l'octet**, mais le code 68K recompilé est le même. On
  compte de 10 à 13 écarts ponctuels, ce sont des constantes de région. Les vraies différences sont ailleurs :
  1. une bibliothèque native PS2 d'environ 300 petits blocs, commune à tous les modules ;
  2. un bloc de texte japonais SJIS ajouté aux données natives ;
  3. pour ro3 et ro5, les **textes du jeu d'arcade en japonais** (environ 54 Ko et 61 Ko, contre 9 Ko et 12 Ko de texte
     anglais). Chaque module ne contient que la langue de sa région.
- **Adresses** : ro3 garde les mêmes adresses MIPS sur 98 % de son code (décalage 0). ro5 est décalé de +112
  octets et ro9 de +1 040. La fin de la zone de code, la zone de données et la table son sont déplacées.
- **La construction actuelle refuse l'ISO japonaise** dès l'étape `iso` (`SLUS_213.17` absent). Même en forçant,
  plusieurs blocages suivent : les noms `_usa` sont attendus dans 161 fichiers du dépôt, les empreintes des modules
  diffèrent, et des adresses sont fixées dans les crochets et les relevés.
- Ce que le Japon apporte à HSFA : **des variantes « Zero » (région Japon, textes japonais) de SFA3 et d'Upper**,
  voire d'Hyper. Pas de musique ni de voix nouvelles.

## 1. L'image japonaise

| élément | valeur |
|---|---|
| archive | `Street Fighter Zero - Fighter's Generation (Japan).7z`, 1 588 506 208 o, LZMA2. Contient l'ISO et un raccourci web (112 o, non extrait ; nom retiré au versement). **Aucun fichier de sommes.** |
| ISO | 4 698 767 360 o (= ISO US), 2 294 320 secteurs de 2 048 o, ISO 9660, système `PLAYSTATION`, copyright `CAPCOM` |
| md5 / sha1 / crc32 | `a5384edba76e28656e5549a1fa579f8b` / `457312ec9d496c22435f7c2cd1a70f575f4f23a9` / `5EF8E1BB` (à rapprocher de Redump par l'utilisateur : pas de référence locale) |
| identifiant | `SLPM_664.09` (SLPM-66409), `SYSTEM.CNF` : VER 1.02, NTSC, ligne `HDDUNITPOWER = NICHDD` en plus (US : VER 1.01, sans cette ligne) |

La ligne `HDDUNITPOWER` confirme l'installation sur disque dur, réservée au Japon.

## 2. Tableau des différences, fichier par fichier

### 2.1 Racine de l'ISO

| fichier | JP (taille, md5) | US « All Unlocked » (taille, md5) | verdict |
|---|---|---|---|
| 0FLIST.DVD, 0FLIST.HDD, ATAD.IRX, DEV9.IRX, HDD.IRX, IOPRP.IMG, MODULE.BIZ, PFS.IRX, SYSDATA.BIZ | — | — | identiques |
| HDDRC1.BIN | 69 120, `16efa7b3…` | 69 120, `7268e86b…` | différent (installation HDD) |
| HDDRC2.BIN | 71 040, `d62f9135…` | 72 640, `81503cf0…` | différent |
| ELF | `SLPM_664.09` 572 352, `f4de7753…` | `SLUS_213.17` 572 352, `11e411ff…` (= référence du projet) | voir §2.2 |
| SYSTEM.CNF | 80, `77e50481…` | 57, `b28f4071…` | voir §1 |
| X_DATA.BIN | 200 310 784 (+96 256), `0a9ddb9d…` | 200 214 528, `53821dc5…` (variante All Unlocked) | voir §2.3 |
| **Y_DATA.BIN** | 1 823 404 032, `9504efda1c990ddfdf78ce5887d2d012` | **identique** (même LBA 1 403 985) | **identique** |

### 2.2 ELF

- La taille est la même et l'en-tête aussi, avec le point d'entrée en `0x100008`. Seule la **taille mémoire des 10
  segments de recouvrement** change (`0x1f0000`, un segment par module), car les modules n'ont plus la même taille.
- Code : 13 402 octets diffèrent. Une fois masqués les `jal` et les `lui`, il reste **73 blocs et 122 mots de chaque
  côté**.
- Ces écarts tiennent dans quelques fonctions :
  - VA `0x148cd4-0x148d2c` ;
  - VA `0x14b384-0x14bc18` ;
  - une zone de 16 Ko en VA `0x155a28-0x159a90`, où le code est seulement décalé de quelques instructions (97 % des
    mots se retrouvent) ;
  - quelques pointeurs, en VA `0x183ffc` et `0x18b5d0` (écart +0x20).
- Le reste du code est aux mêmes adresses. En conséquence, les modules appellent certaines fonctions de l'ELF à
  +8 octets (cas de ro2).

### 2.3 X_DATA.BIN (AFS, 553 entrées des deux côtés)

| entrée | contenu | JP | US | nature de l'écart |
|---|---|---|---|---|
| e203 | MWo3 `b_jpn` / `b_usa` (menu) | 41 718 | 41 730 | région et modification « All Unlocked » mêlées (non séparables sans l'ISO US d'origine) |
| e206 | MWo3 `ro1` (*Zero* / *Alpha*) | 1 038 830 | 1 037 144 | §2.4 |
| e224 | MWo3 `ro2` (*Zero 2* japonais) | 1 804 536 | 1 804 536 | nom interne et 3 cibles d'appel vers l'ELF (+8) : **fonctionnellement identique** |
| e253 | MWo3 `ro3` (SFA3) | 2 389 448 | 2 369 958 | §2.4 |
| e348 | MWo3 `ro4` (*Zero 2 Alpha*) | 1 863 816 | 1 847 602 | §2.4 |
| e350 | MWo3 `ro5` (Upper) | 2 869 942 | 2 834 876 | §2.4 |
| e526 | MWo3 `ro6` (*Zero 2'* / *Gold*) | 1 870 978 | 1 852 844 | §2.4 |
| e527 | graphismes ro6 | 4 068 794, entropie 7,06 | 4 068 794, entropie 0,13, autre en-tête | **c'est l'ISO US qui est modifiée** (« All Unlocked »). L'entrée JP a l'aspect d'une vraie entrée graphique : c'est sans doute l'originale. |
| e536 | MWo3 `ro7` (*Pocket Fighter*) | 1 502 390 | 1 498 996 | §2.4 |
| e543 | MWo3 `ro8` (SFA2) | 1 832 454 | 1 831 114 | §2.4 |
| e544 | MWo3 `ro9` (Hyper) | 3 505 138 | 3 502 644 | §2.4 |
| les 542 autres | graphismes, Z80, sons, banques SPU2, TIM2, données | — | — | **identiques à l'octet** |

Empreintes des groupes, au format `REF_GROUPES` de `hsfa_build.py` : `sorties/groupes_md5.txt`.

- Sur l'ISO US « All Unlocked », 8 groupes sur 10 sont conformes aux références du projet ; seuls b et ro6 ne le sont
  pas, comme l'indique `BUILD.md`.
- Sur l'ISO JP, les 10 groupes diffèrent, à cause des modules. **Sans les modules, les 10 groupes sont identiques**
  entre JP et US, sauf ro6 (e527).

### 2.4 Modules décompressés (`mwo3_codec`, base `0x1f0000`)

md5 JP (US = références du projet pour ro3, ro5 et ro9) : `sorties/modules_md5.txt`.

| module | code JP / US (écart) | données JP / US (écart) | écarts du code 68K hors bibliothèque native | bibliothèque native (blocs, mots) | données (pointeurs masqués) |
|---|---|---|---|---|---|
| b | `0xc8c0` / idem | `0x75c0` / idem | — | 6 blocs | 92 petits blocs (8 o) |
| ro1 | `0x1f1f40` / `0x1f1bc0` (+896) | +1 792 | 5 blocs, 11 mots | 294 / 1 767 | 52 blocs, 2,6 Ko (dont 1 648 o SJIS seuls JP) |
| ro2 | identique | identique | 0 | 0 | 0 |
| **ro3** | `0x394040` / `0x393c40` (+1 024) | `0x30ab40` / `0x308ac0` (+8 320) | **10 blocs, 20 mots** | 299 / 1 964 | 161 blocs. Textes d'arcade : JP environ 54 Ko non ASCII, US environ 9 Ko ASCII à 88 %, plus 3 440 o SJIS seuls JP |
| ro4 | +896 | +10 880 | — | 309 blocs au total | 2 818 blocs, environ 81 Ko |
| **ro5** | `0x41b040` / `0x41acc0` (+896) | `0x39a840` / `0x3954c0` (+21 376) | **11 blocs, 48 mots** (dont une fonction de 28 mots, seule JP, en `0x24920`) | 298 / 1 926 | 205 blocs, environ 220 Ko (textes d'arcade : JP environ 61 Ko, US environ 12 Ko) |
| ro6 | +2 816 | +11 392 | — | 325 blocs au total | 3 040 blocs |
| ro7 | +1 792 | **−17 152** | — | 307 blocs au total | 746 blocs, environ 67 Ko |
| ro8 | +896 | +1 536 | — | 302 blocs au total | 51 blocs |
| **ro9** | `0x3bf540` / `0x3bf140` (+1 024) | `0x5b8ec0` / `0x5b80c0` (+3 584) | **13 blocs, 26 mots** | 299 / 2 008 | 141 blocs, environ 5,5 Ko (surtout 3 440 o SJIS seuls JP) : **pas de texte d'arcade différent** |

**Les modules ro3, ro5 et ro9 ne sont pas identiques à l'octet.** Les écarts relevés sont de quatre sortes :

1. **Nom interne** (`roN_jpn` / `roN_usa`, octets `0x26-0x28`) : présent dans tous les modules.
2. **Constantes de région dans le code 68K recompilé** : de 9 à 12 instructions par module, avec les mêmes motifs
   dans ro1 et ro3. Exemples d'adresses dans ro3 : `0x2ed24` (valeur de région écrite, 0 en JP et 2 en US),
   `0x48324` et `0x84310` (masques), `0x153754` et `0x1ebf30` (constantes). La valeur 0 = Japon, 2 = USA de la
   région CPS-2 est **probable**, mais elle n'a pas été vérifiée en émulation.
3. **Bibliothèque native PS2** (C du portage, peu d'accès `lui 0x7000`) : environ 300 blocs et 1 800 à 2 000 mots,
   presque les mêmes dans tous les modules. Elle se trouve à la fin du code pour ro3 et ro5 (`0x380000+` et
   `0x400000+`), au début du code pour ro9 (`0x24a00-0x2c700`). On y ajoute un bloc de texte SJIS seul JP, de
   1,4 à 3,4 Ko, au début des données. Cela correspond à la liste des coups en pause, réservée au Japon. Ce lien est **probable**, pas vérifié.
4. **Textes du jeu d'arcade** (zone de données) : écarts massifs pour ro3, ro5, ro4, ro6 et ro7, presque nuls pour
   ro1, ro8 et ro9.
   - Le **texte anglais de ro3 et ro5 est absent des modules JP**, et le texte japonais absent des modules US. Sur
     des fenêtres de 32 o : 0 sur 2 404 (ro3) et 0 sur 3 089 (ro5) retrouvées.
   - Conséquence : **on ne peut pas reconstituer un module US à partir du disque JP**.

**Mêmes adresses ?** Elles ont été mesurées par alignement des mots masqués (`scripts/carte_us_jp.py`). La
correspondance US → JP couvre 99,9 % du code de chaque module ; elle est dans `sorties/carte_roN_us_jp.json`.

| module | décalage du code 68K | ailleurs |
|---|---|---|
| ro3 | **0 sur 3 681 048 o** (98 % du code du module) ; −4 sur 512 o autour de `0x2ed24` | bibliothèque de fin : +112 à +944 |
| ro5 | **+112 constant** (4,06 Mo), après la fonction ajoutée en `0x24920` | +0 avant, +944 / +208 / +688 dans la bibliothèque |
| ro9 | **+1 040 constant** (3,53 Mo), après la bibliothèque du début | +1 104 sur la fin (220 Ko) |

Table native des commandes son (`table_son.py`, 0x1200 × 8 o) : **contenu identique** dans ro3, ro5 et ro9. Elle
référence 559 flux ADX de chaque côté, sans aucun ajout ni retrait. Seule son adresse change : ro3 `0x5a0ba0` contre
`0x59f9c0`, ro5 `0x6298f0` contre `0x628780`, ro9 `0x5cc540` contre `0x5cb300`.

### 2.5 Textes, graphismes, options, contenus (points de la source privée vérifiés sur les fichiers)

| point (source) | vérification sur les fichiers |
|---|---|
| Jeux visibles et cachés différents, Hyper après 8 jeux au Japon contre 6 en Occident | Les mêmes 9 modules sont sur les deux disques. Les écarts du menu (`b`, ELF) sont compatibles avec cette différence, mais **non localisés** (b mêle région et modification All Unlocked). |
| Chanson du film dans le Dramatic Battle de *Zero*, au Japon seulement | **Aucune donnée son propre au disque JP** (Y_DATA identique, X_DATA identique hors modules). ro1 ne diffère que par 11 mots de code 68K et 2,6 Ko de données. La sélection dépend donc de la région ; la piste est aussi sur le disque US. Piste **non localisée**. Hors périmètre HSFA (ro1). |
| Illustrations du menu (prospectus japonais ou américains) | Images identiques sur les deux disques : **les deux jeux d'illustrations sont sur chaque disque**, et le code choisit. Non localisées. |
| Liste des coups en pause, au Japon seulement | Blocs SJIS seuls JP dans chaque module (1,4 à 3,4 Ko) : compatible. |
| Installation sur disque dur | **Vérifié** : `HDDUNITPOWER = NICHDD`, HDDRC1/2 différents. |
| Sang, régulation | Rien de visible dans les données (graphismes identiques). Une éventuelle différence passerait par les constantes de région. Non vérifié. |
| Personnages, modes, jeux en plus ou en moins | Aucun : mêmes modules, mêmes graphismes, même table son. |

### 2.6 Note : ISO PSP japonaise (non analysée en détail)

`Street Fighter Zero 3 Double Upper (Japan).iso` : 271 417 344 o, md5 `d2c5ac0e4398858733c619050e1a6ff9`.

- **ULJM-05082**, v1.01 ; c'est l'équivalent japonais de SFA3 MAX (ULES-00235 en Europe, utilisé par le projet).
- Données dans `USRDIR/jpn/` au lieu de `EUR/DATA/`. `BOOT.BIN` est un ELF en clair de 3 692 480 o (EU : 3 693 304),
  md5 différent.
- Fichiers des personnages MAX :
  - `pl27_j.pac`, `pl28_j.pac` et `pl29_j.pac` ont **le même md5** que les `PL27-29_E.PAC` de référence ;
  - `pl26_j.pac` (Eagle) a la même taille mais un md5 différent ;
  - il existe en plus un `pl29r_j.pac`.
- `--psp-iso` exige `ULES00235` : ce disque n'est pas accepté en l'état.

## 3. Conséquences pour HSFA

### 3.1 La construction peut-elle accepter l'ISO japonaise ?

**Non, en l'état.** Ordre des blocages dans `scripts/construction/hsfa_build.py` :

1. `e_iso` : `REF_ISO` exige `SLUS_213.17`, d'où l'échec « ce n'est pas Street Fighter Alpha Anthology (USA) ».
   Si l'on passe le dossier extrait, les 10 groupes diffèrent de `REF_GROUPES` ; il faut alors `--iso-differente`.
2. `e_afs` : le manifeste diffère (tailles). Ce n'est qu'un avertissement.
3. `e_module` : il cherche `ro3_usa_prog68k.mwo3`, or l'extraction produit `ro3_jpn_prog68k.mwo3`. Le motif `_usa`
   apparaît dans 161 fichiers de `scripts/`, `src/` et `tools/`. Le md5 diffère de `REF_MODULES`.
4. Traducteur et banc : des adresses MIPS fixes sont décalées ou changées.
   - Crochets `hooks_fork_ro3/5/9.json` (48 / 38 / 42 entrées) : 29 / 24 / 24 sont dans l'ELF et restent valides,
     sauf **4 / 0 / 3 fonctions ELF modifiées** (VA `0x14b3a0`, `0x14b460`, `0x14b420`, `0x14b3e0`). Les autres se
     décalent de +0 à +1 104, avec 1 cible sans correspondance par module.
   - Autres adresses fixes à revoir : `map_ro3_sfa3.json`, `re/allocations.tsv`, les relevés `releves_ro9a37/` de la
     greffe, et toute adresse de la zone de données (décalée).
5. Ce qui marcherait sans changement :
   - les graphismes (`banques.py`, `rom_iso.py`) : X_DATA identique hors modules ;
   - la ROM son de SFA3 (e287/e288) ;
   - le flux ADX : Y_DATA identique, et `table_son.find_tables` retrouve la table par motif.
6. Upper MAX : la PSP japonaise n'est pas acceptée (identifiant), et Eagle diffère.

Même en forçant, le résultat ne serait **pas** les jeux US actuels. Ce seraient des jeux de **région japonaise avec
textes japonais**, à valider contre un oracle japonais. Un oracle d'arcade japonais 980727 a déjà été construit [référence privée retirée au versement].

### 3.2 Contenu japonais à proposer

| contenu | intérêt | faisabilité |
|---|---|---|
| Variante « *Street Fighter Zero 3* » (et « *Zero 3↑* ») : région Japon, textes d'arcade japonais | **réel** : c'est le seul vrai apport | chaîne JP complète (§3.3) |
| Hyper « Zero » | faible : textes d'arcade identiques, seuls la région et les textes natifs changent | même chaîne |
| Musique (dont la chanson du film) | **aucun apport** : données identiques sur le disque US. Concerne *Zero* (ro1), hors périmètre. | sans objet |
| Voix | aucun apport (identiques) | sans objet |
| Réglage de région sur les jeux US actuels (constante 0 au lieu de 2) | douteux : le texte japonais manque au module US | non recommandé sans essai |

### 3.3 Effort (estimation sans promesse)

- **Accepter le disque JP comme simple « autre source » des jeux US** : impossible, car le texte anglais est absent.
  La seule solution serait un message clair d'échec (« disque japonais reconnu, non pris en charge »). Effort :
  1 à 2 heures, avec une table `REF_ISO_JP` et les empreintes ci-dessus.
- **Chaîne « Zero 3 » JP pour SFA3** :
  1. suffixe de région paramétrable (`_usa` / `_jpn`) dans la construction et les outils ;
  2. empreintes JP ;
  3. report des adresses fixes par `carte_ro3_us_jp.json` (décalage 0 sur 98 % du code : favorable) ;
  4. contrôle de la zone de données (textes plus longs, pointeurs) ;
  5. validation au banc contre l'oracle japonais.

  Ordre de grandeur : **quelques jours à deux semaines**, surtout pour la validation.
- **Upper JP** : un peu plus (décalage +112 et textes plus volumineux). **Hyper JP** : intérêt faible.

## 4. Recommandations

1. **Ne pas promettre de « chanson en plus »** : sur les fichiers, le disque JP n'apporte aucun son. Corriger la ligne
   de `docs/ATTENTES-ET-DECISIONS.md` (« une chanson en plus, à vérifier ») quand l'utilisateur le décidera.
2. Dans la construction, **reconnaître** l'ISO JP (md5 de l'ELF `f4de7753…`, X_DATA `0a9ddb9d…`) pour donner un message
   explicite au lieu de « ce n'est pas l'Anthology ». C'est une petite tâche sûre.
3. Si l'utilisateur veut des variantes japonaises, commencer par **SFA3 → « Zero 3 »** : même code 68K, mêmes adresses
   sur 98 % du code.
   - Avant tout, un essai court au banc (MAME, sous la règle 6 d'AGENTS.md) pour confirmer le sens des constantes de
     région et le rendu des textes japonais.
   - Point de vigilance pour SFA3 : le module emprunte des entrées du groupe ro5 (banques 391-412 et 456-457) ; elles
     sont identiques dans le disque JP.
4. Noter dans `docs/rapports/BUILD.md` que l'**e527 « All Unlocked » est une entrée vidée** (entropie 0,13). L'entrée
   JP semble l'originale.
5. PSP japonaise : sans objet pour HSFA tant que MAX repose sur l'ISO européenne. Seul Eagle diffère.
