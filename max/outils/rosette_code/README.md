# Rosette du code : API moteur et champs objet, C du PSP (SFA3 MAX) ↔ 68K arcade (SFA3, `sfa3ud`)

2026-10-04. But : préparer le portage du code d'Eagle, Maki, Yun et Ingrid (C/MIPS du PSP) vers le 68K, en apprenant
la correspondance sur les persos présents des deux côtés : **les 26 persos de SFA3** (pas besoin d'attendre Upper
dans MAME, contrairement au plan initial qui passait par Guile).

Sources : EBOOT PSP (`tools/max`, modules par perso via `modules.py`) ; programme arcade déchiffré
`hsfa/work/cps2/sfa3_prog.bin` (68K gros-boutiste, 4 Mo).

## 1. Méthode

1. **Code arcade des persos** (`arc68k.py`, `rosette.py`) : 20 tables de 32 longs indexées par l'ID (`$102(A6)`, en
   `0xDCB12…0xDF892`) donnent les points d'entrée de chaque perso ; les régions sont rangées dans l'ordre des ID
   (Ryu `0x33F00-0x35A74`, Ken `0x35A74-…`). Désassemblage récursif (capstone) avec tables de saut Capcom
   (`MOVE.W tab(PC,Dn),Dm ; JMP tab(PC,Dm)`). Ryu : 1 506 instructions, 93 % de sa région.
2. **Appels moteur et arguments constants** (`appels.py`) : 68K `MOVEQ/MOVE #n,D0-D3` avant `JSR/JMP/BSR` externe ;
   PSP `ori/addiu aK,zero,n` autour du `jal`. **Les constantes immédiates du code ne survivent PAS au portage C**
   (essai de `rosetta.py` d'HSFA : 0-5 correspondances), **mais les arguments des appels, si** (numéros d'animation,
   d'attaque, de son…).
3. **Appariement des cibles** (`rosette.py`) : Jaccard pondéré des arguments → paires ; routines appariées par les
   sites d'appel ancrés ; alignement (LCS) des suites d'appels dans chaque paire → nouvelles paires ; itéré.
   Fait **pour chacun des 26 persos** indépendamment, puis **vote** (`consensus`).
4. **Champs objet** (`champs.py`) : dans 865 paires de routines (API + gestionnaires des 26 persos), suites d'accès
   `d(A6)` (68K) et `d(a0 et copies)` (PSP), alignées (taille + lecture/écriture) ; vote des couples de décalages ;
   **chaîne croissante de poids maximal** (l'ordre des champs est conservé).

## 2. Résultats

**API moteur : 45 paires sûres + 16 par interpolation** (`api_moteur.json`, tableau ci-dessous).
- Contrôle indépendant 1 : soutien en passe 1 (chaque perso vote seul) : la plupart 5/5 à 26/26.
- Contrôle indépendant 2 : **l'ordre des adresses est conservé** (5 inversions locales sur 44 voisins) ⟹ le C a été
  écrit dans l'ordre du source d'origine ; d'où l'**interpolation** : entre deux paires sûres, autant de fonctions
  de chaque côté ⟹ appariées dans l'ordre (16 ajouts, nombres d'appels cohérents : 65↔71, 58↔63, 22↔22…).
- Couverture des appels moteur : Ryu 65 % (carte sûre seule), **Eagle 35 %**, Maki 33 %, Yun 27 %, Ingrid 16 % ;
  ~50 % des appels des 4 persos MAX visent des utilitaires qu'AUCUN perso arcade n'appelle (cf. étude §8.3).

**Champs de la structure objet/joueur : le C recopie la structure 68K, décalée par zones** (`champs_votes.json`) :

| 68K | PSP | écart | exemple de soutien |
|---|---|---|---|
| `$001-$00E` | `0x001-0x00E` | +0 | `$007` : 440/550 votes |
| `$010-$014` | `0x012-0x016` | +2 | positions X/Y en 32 bits : **demi-mots inversés** (petit-boutiste) : `$10` entier ↔ `0x12`, `$12` fraction ↔ `0x10` |
| `$018` (`$1C`) | `0x018` (`0x1C`) | +0 | `$1C` = pointeur du pas d'animation (lu dans `0x5D63C`) |
| `$031-$035` | `0x049-0x04D` | +0x18 | `$032` = décompte de durée du pas |
| `$03C-$03F` | `0x04E-0x051` | +0x12 | |
| `$040-$067` | `0x060-0x087` | +0x20 | `$040` : 146/200 |
| `$080-$0A0` | `0x0C0-0x0E0` | +0x40 | `$082` (force) : 95/160 |
| `$0A9-$0BC` | `0x0EB-0x0FE` | +0x42 | |
| `$0CC-$0CE` | `0x104-0x106` | +0x38 | `$0CE` : 84/129 |
| `$0DE` | `0x11A` | +0x3C | |
| `$0EB` | `0x134` | +0x49 | |
| `$101-$132` | `0x151-0x182` | +0x50 | `$102` = ID ? (à vérifier), `$132` = ism ↔ `0x182` |
| `$211-$25D` | `0x1F1-0x23D` | −0x20 | |
| `$290-$2C9` | `0x280-0x2B9` | −0x10 | `$2A0`, `$2C8` |

- Accès aux champs traduisibles directement : **Ryu 84 %, Eagle 82 %, Maki 81 %, Yun 77 %, Ingrid 72 %**.
- Restent : `0x52`-`0x5F` (champs ajoutés par le C ; `0x5C` = pointeur 32 bits, probablement l'adversaire, `$38(A6)`
  en mot dans le 68K — hypothèse), `0x334`-`0x340` (extension PSP), et les bords de zones.
- Les tables de données du perso passent par un pointeur `0x1A0` (PSP) : `+0` / `+4` / `+12` = tables d'animation
  ↔ `$2B0` / `$2B4` / `$2BC` (68K).

## 3. Tableau de l'API moteur

| arcade 68K | PSP | méthode | soutien | rôle (lu dans le 68K) |
|---|---|---|---|---|
| `00369c` | `078614` | arguments+alignement | 16/18 | son/voix propre au perso (table de bits par ID) |
| `0038e4` | `078408` | arguments+alignement | 7/13 |  |
| `01bd5c` | `01d330` | arguments+alignement | 14/21 | table choisie par `$E` (côté/sens) |
| `01bda6` | `01d368` | arguments+alignement | 5/5 |  |
| `01c1c8` | `01ed2c` | arguments+alignement | 2/2 |  |
| `01c2c8` | `01eeac` | arguments+alignement | 5/7 |  |
| `020674` | `033098` | arguments+alignement | 21/25 | réaction console/son ? (`$AC(A5)`, `$125`) |
| `02068c` | `0330d8` | arguments+alignement | 21/23 | idem, selon la force `$82` (pose `$216`) |
| `02a708` | `05d63c` | arguments+alignement | 25/25 | lancer l'animation n (table `$2B0`) → pas courant `$1C` |
| `02a710` | `05d674` | arguments+alignement | 12/13 | lancer l'animation n (table `$2BC`) + octets par perso/ism → `$23E`, `$293` |
| `02a758` | `05d6ec` | arguments+alignement | 26/26 | lancer l'animation n (table `$2B4`) |
| `02a75e` | `05d724` | arguments+alignement | 2/2 |  |
| `02a7ea` | `05d848` | arguments+alignement | 21/24 | avancer l'animation (décompte `$32`, pas suivant) |
| `02a838` | `05da14` | arguments+alignement | 6/6 |  |
| `02a8c6` | `05dbcc` | arguments+alignement | 2/3 |  |
| `02aa08` | `05e004` | arguments+alignement | 9/15 |  |
| `02aebc` | `05f114` | arguments+alignement | 8/10 |  |
| `02b1fc` | `05fa50` | arguments+alignement | 6/6 |  |
| `02e3e0` | `06666c` | arguments+alignement | 4/4 |  |
| `02e3fe` | `0666d4` | arguments+alignement | 20/24 | déclenchement d'un coup (`$32F` = n), selon l'état `$4/$6` |
| `02e5d4` | `066c80` | arguments+alignement | 2/2 |  |
| `02e636` | `066e04` | arguments+alignement | 23/24 | déclenchement d'un coup (variante, teste l'adversaire `$38`) |
| `02e6ec` | `067058` | arguments+alignement | 2/2 |  |
| `02e714` | `067100` | arguments+alignement | 4/4 |  |
| `02e720` | `067164` | arguments+alignement | 2/2 |  |
| `02e7f2` | `067144` | arguments+alignement | 24/25 | prise : adversaire (`$38`) mis en état projeté, attaque n de la table `$A0` |
| `02e96c` | `0676a8` | arguments+alignement | 2/2 |  |
| `02e970` | `06768c` | arguments+alignement | 15/18 | prise (variante), attaque n de la table `$A0` |
| `02ea06` | `067880` | arguments+alignement | 3/6 |  |
| `02ea7a` | `067954` | arguments+alignement | 8/9 |  |
| `02ef6c` | `068a2c` | arguments+alignement | 22/26 |  |
| `02f52c` | `069440` | arguments+alignement | 21/22 | pose `$291`=1, `$2A0`=10 puis neutre |
| `02f53c` | `069468` | arguments+alignement | 14/15 |  |
| `02f6f8` | `069b2c` | arguments+alignement | 2/2 |  |
| `02f9be` | `069dcc` | arguments+alignement | 10/12 |  |
| `02fa36` | `069ec8` | arguments+alignement | 8/8 |  |
| `02fcd4` | `06a294` | arguments+alignement | 5/5 |  |
| `0804da` | `079144` | arguments+alignement | 15/17 | création d'un objet fils (projectile/effet) A4 |
| `0805c0` | `078c68` | arguments+alignement | 2/2 |  |
| `080668` | `078d7c` | arguments+alignement | 4/4 |  |
| `080b70` | `079d30` | arguments+alignement | 15/16 | création d'un objet fils lié à l'attaque n (table `$A0`) |
| `080e8e` | `07a14c` | arguments+alignement | 8/9 |  |
| `082e36` | `07bd2c` | arguments+alignement | 22/22 |  |
| `082f74` | `07c034` | arguments+alignement | 2/2 |  |
| `097cd6` | `07e3e0` | arguments+alignement | 2/2 |  |
| `02a770` | `05d75c` | interpolation (ordre) | - |  |
| `02a7f0` | `05d900` | interpolation (ordre) | - |  |
| `02a83c` | `05da38` | interpolation (ordre) | - | lancer l'animation n d'un AUTRE objet (A4) |
| `02a8ca` | `05dbe8` | interpolation (ordre) | - |  |
| `02a98c` | `05dedc` | interpolation (ordre) | - |  |
| `02af7a` | `05f2c4` | interpolation (ordre) | - |  |
| `02b0c4` | `05f748` | interpolation (ordre) | - |  |
| `02e5f0` | `066d10` | interpolation (ordre) | - |  |
| `02e614` | `066d68` | interpolation (ordre) | - |  |
| `02f728` | `069b94` | interpolation (ordre) | - | force du poing pressé (boutons `$378|$37A`, bits 0-2 → 0/2/4) |
| `02f74c` | `069be8` | interpolation (ordre) | - | force du pied pressé (bits 4-6 → 0/2/4) |
| `02f770` | `069c3c` | interpolation (ordre) | - |  |
| `02f796` | `069c78` | interpolation (ordre) | - | remise à l'état neutre (efface/positionne `$D6`, `$AB`, `$2A0`, `$BA`, `$E2`, `$E4`…) |
| `02f980` | `069d68` | interpolation (ordre) | - | lecture d'une combinaison de boutons (`$378|$37A & $7700`) |
| `02faae` | `069fc4` | interpolation (ordre) | - |  |
| `02fb96` | `06a17c` | interpolation (ordre) | - |  |

## 4. Traducteur MIPS -> 68K (2026-10-04) — `traduire.py`

Exécution symbolique par bloc de base du MIPS PSP, émission 68K avec les deux tables ci-dessus et des règles apprises :
- objet `a0` (+ copies) = `A6` ; arguments `a1-a3` = `D0-D2`, **arité** par fonction (`arite.py`, 276 fonctions) ;
- **numéros d'état `$4-$7` : PSP n = 68K 2n** (tables de mots) ; appel suivi de l'épilogue = `JMP` ;
- longs dans la zone `$10-$14` : même décalage (l'écart +2 ne vaut que pour les demi-mots, petit-boutiste) ;
- tailles 68K usuelles par champ (`tailles68.py`) : le C a élargi certains compteurs (`$1FE` octet ↔ `0x334` long) ;
- tests de bits (`andi` → `BTST`), comparaisons (`slt*` → `CMPI` + `BLT/BGE/BCS/BCC`), créneaux de délai et
  branchements « likely », fusion des états aux étiquettes ;
- champs/fonctions inconnus appris par alignement avec la vérité arcade (`apprendre.py` → `appris.json`, ex.
  `0x52` → `$3A` 18/18) ; fonctions PSP sans équivalent → sous-routines traduites à leur tour ; son PSP (`0x6A3CC`,
  table `0x217FD8`) → marqueur `SON` (correspondance des numéros de son = chantier son).

**Validation** (`evaluer.py`, 820 paires de gestionnaires des 26 persos, vérité = routines arcade) : 28 traductions
**identiques**, 49 à ≥ 0,9 de ressemblance, médiane 0,48 ; 12 % de lignes non traduites (« ?? »).
Les écarts restants : C restructuré (inlining, ordre des blocs), expressions complexes, accès par d'autres pointeurs
(adversaire, globales), tables de saut d'états (`jalr`) pas encore traduites.

**Ajouts du même jour** :
- tables de saut d'états (`jalr` sur `table[état×4]`) → `MOVE.B $n(A6),D0 ; MOVE.W J(PC,D0.W),D1 ; JMP/JSR J(PC,D1.W)`
  + table `dc.w` (l'état 68K vaut déjà 2n) ; fin de table = adresse suivante référencée par le code ;
- **pointeurs** : PSP `0x5C` = `$38(A6)` adversaire (79 votes), `0x58` = `$36` (2 votes) ; l'objet pointé suit la même
  carte de champs (`MOVEA.W $38(A6),A1 ; … $5F(A1)`) ;
- **globales** : `$n(A5)` = adresse PSP − `0x8081F8` (36 votes) ; retour de fonction = `D0` ; `NEG` ;
- apprentissage cumulatif (`appris.json`, `apprendre.py` fusionne).
Évaluation : 28 identiques, 52 à ≥ 0,9, **8 %** de lignes non traduites.

**Persos MAX** (`brouillons.py`) : ébauches `brouillon_eagle.s` / `maki` / `yun` / `ingrid` (module + utilitaires
appelés + gestionnaires des tables de saut) : lignes traduites **81 % / 84 % / 79 % / 72 %** (29/46/64/19 tables de saut). **Premier gestionnaire porté et relu** : `eagle_premier_portage.s`
(EBOOT `0x1B4F94`, début d'un coup normal : animations 12/13/14 de `$2BC` selon la force `$82`).

**Ajouts (suite, même jour)** :
- **champs « ×2 »** mesurés sur les paires (≥ 3 votes) : `$4-$7` (routines), **`$80`, `$82` (force), `$AA`, `$2A0`,
  `$2C4`**, et le sous-type d'objet (octet `$3`). Règles : constante écrite/comparée ×2 ; **valeur utilisée comme
  nombre (argument, calcul) = champ / 2** (l'arcade : `move.b $82,d0 ; lsr.b #1,d0 ; jsr $2EF6C`, 78 sites) ;
  copie entre champs ×2 telle quelle ; valeur ordinaire écrite dans un champ ×2 : doublée ;
- **création d'objet** : PSP `0x1EEAC(type, sous-type)` -> nouvel objet = arcade `JSR $1C2C8` (-> A4, Z si échec) +
  `MOVE.L #$0100ttss,(A4)` (sous-type ×2) ; propriétaire PSP `0x58` = `$36` (`MOVE.W A6,$36(A4)`) — vérifié identique
  à la routine arcade `0x69D76` ;
- arguments reçus `a1-a3` = `D0-D2` ; tailles : lecture = min(PSP, 68K), écriture octet/mot = taille PSP ;
- **mode de repli** : toute expression (+ − & | ^ décalages, comparaisons via `Scc`) calculée dans `D3-D7` (code juste
  mais moins idiomatique), signe des chargements suivi (`lbu/lhu` non signés) ;
- **champs propres à MAX** (jamais utilisés par les persos arcade) : `0xAA`, `0x1EA` → à loger dans des octets libres
  de la structure 68K (choix à faire avec l'outil d'injection).
Évaluation : 28 identiques, 53 à ≥ 0,9, **4 %** de lignes non traduites. Ébauches : Eagle **88 %**, Maki **89 %**,
Yun **86 %**, Ingrid **81 %**.

**Nouvelle organisation des ébauches (`brouillons.py`)** :
- seules les fonctions du **module du perso** sont traduites (`brouillon_<perso>.s`) : **Eagle 96 %, Maki 94 %,
  Yun 90 %, Ingrid 85 %** de lignes traduites ;
- les **147 fonctions du moteur PSP** appelées sans équivalent arcade connu (16,5 Ko, 68 partagées) ne sont plus
  traduites récursivement : leurs conventions diffèrent (a0 n'y est pas toujours un objet). Inventaire
  `api_a_fournir.md/.json` ; **84 se traduisent proprement** (`moteur_max_auto.s`, 861 appels : enveloppes de
  fonctions connues, ex. `0xCFA6C` = `JMP $2A710` ; `0xCFEC8`, 225 appels, « avancer l'animation sauf fin ») ;
  **63 sont à écrire à la main** (11,7 Ko) ; `moteur_max_main.s` = fonctions écrites à la main (1re : `0xCFEC8`, variante compacte) ;
- **champs propres à MAX logés** : PSP `0xAA` → `$3F0` (octet), `0x1EA` → `$3F2` (mot) — mesure HSFA (jamais écrits
  en combat) + code arcade (aucun accès d(An) à `$3F0-$3F3`) + ro3/ro5 vérifiés par HSFA (aucun accès) ; ⚠ `$380-$397` est écrit (`MOVEM` en `0x6EFD2`) ;
- corrigé : créneau de délai du `jr ra`, retour `D0` mal formé (`op68`), affichage des valeurs ;
- pas d'animation lus via `$1C` : octets PSP → 68K (`+1` bits 15/14 → `+2`, etc.) ; valeur de retour placée dans `D0`
  avant `RTS` ; extension de signe exacte (`sll/sra 24/16` après calcul) ; `BTST` sur le bon octet (gros-boutiste) ;
- limites connues : boucles (ex. recopie du gabarit à l'init, code propre au PSP), fonctions dont a0 n'est pas un objet.

**Allocation de la structure joueur pour les persos MAX (confirmée par HSFA dans ro3 et ro5, 2026-10-04)** :

| PSP | 68K | nature |
|---|---|---|
| `0xAA` | `$3F0` (octet) | champ propre à MAX |
| `0x1EA` | `$3F2` (mot) | champ propre à MAX |
| `0x334`…`0x34C` (7 longs) | `$3C0`…`$3D8` | variables de travail PROPRES À CHAQUE PERSO (union C : rangement différent par perso ; chez Ryu `0x334` = `$1FE`) |
| `0x2FA`, `0x2FC` (mots), `0x305` (octet) | `$3E0`, `$3E2`, `$3E4` | idem (Maki, Yun) |

⚠ `$380-$397` est écrit par l'arcade (`MOVEM` en `0x6EFD2`). Prolongements de zones trouvés par vote différentiel
(`differentiel.py`) : `0xE4` → `$A4` (4/4), `0x2BA` → `$2CA`. Ébauches : **Eagle 97 %, Maki 95 %, Yun 92 %, Ingrid 85 %** ;
moteur : 88 fonctions auto (877 appels), **59 à écrire** (11 Ko).
Champs encore inconnus (`champs_inconnus.txt`) : surtout `0x88-0xAF` (`0x8B` 57 emplois, `0xA4`, `0x8C`, `0x8E`, `0xAB`…),
`0x1A0+n` (structure perso PSP), `0x28`, `0x30`, `0x56` : peut-être propres au portage, peut-être lus par le moteur à un
emplacement précis → pas alloués au hasard ; à trancher avec le moteur arcade (ou au banc).

**Moteur PSP : écriture à la main commencée (`moteur_max_main.s`)** — 2026-10-04 :
- `psp_cfec8` (225 appels, avancer l'animation sauf fin), `psp_cf5d8` (45, au-dessus du sol : Y + octet haut du mot A
  du pas courant < `$64`) ; fiches des fonctions bloquées (`cfd9c`, `cfb6c` : tables de scripts passées par adresse =
  données EBOOT à convertir ; `1f24c` : bloc de globales `0xA3E000…` sans équivalent) ;
- règles nouvelles : PSP `0xEA` = `$AA` (×2 ; arcade `0x346B4`), PSP `0x128` = entrée de boîtes courante → mots A/B/C du
  pas 68K (`$1C` → `+8/+12/+16`, octets inversés) ; globales PSP hors A5 → `??glob_…` (apprentissage possible :
  une seule apprise, `0xA3E7C3` → `$6EB9(A5)`, 2 votes : pas assez pour le bloc) ;
- bilan : **89 fonctions moteur traduites automatiquement, 2 à la main (270 appels), 56 à écrire (316 appels, 10,8 Ko)**.

**Pas d'animation en 68K natif (vérifié sur la ROM arcade, 2026-10-04)** : 20 octets = durée, drapeaux de fin (bit 7
reprise via `+$14`, bit 6 fin), mot drapeau (bas, haut), pointeur de frame (long BE), puis les 12 octets A/B/C **dans
l'ordre du PSP** (les octets de boîtes PSP se retrouvent tels quels dans la ROM). ⟹ correction : octets du pas lus via
`$1C` = mêmes décalages que le PSP (et non +1 → +2) ; `psp_cfec8` corrigé (`btst #6,1(a0)`), `psp_cf5d8` (octet `11(a0)`).
**Tables passées par adresse** (`tables_explicites.py`) : 3 tables (Eagle 1, Yun 1 de 170 scripts, Ingrid 1 avec
frames renumérotées) converties en données 68K (`tables_explicites_<perso>.s`), référencées `#TAB_xxxxxx` par le
traducteur ; `psp_cfd9c` porté (chargement du pas par `$2A770`). Moteur : 90 auto, 3 à la main (286 appels),
54 à écrire (297 appels). `psp_cfb6c` (9 appels) emploie un autre format d'enregistrement (objets fils, `0x1D96C`) : à étudier.

**Objets fils et reprises (2026-10-04)** :
- `+6` d'un pas PSP = **écart signé vers le pas suivant** ; reprise = dernier pas + écart (Ryu : 166/166 vs module) ;
  `animations.json` a un champ `reprise` (la plupart ≠ 0) ;
- **petits pas des objets fils** (8 o : durée, drapeaux, 2 octets, frame u16, écart s16 ; chargés par `0x1D96C`, avancés
  par `0x1D9B0`) ; `tables_explicites.py` convertit les deux formats en pas 68K de 20 o, étiquette par pas, reprise
  exacte : 7 tables, 273 scripts (boîtes A/B/C des petits pas à zéro : ⚠ projectiles à vérifier) ;
- portés (équivalences à valider au banc) : `cfb6c`, `1d9b0`, `cfde0`, `cfb90` → moteur : 89 auto, **7 à la main
  (358 appels), 51 à écrire (245 appels, 10,2 Ko)**.

**Suite (même jour)** :
- les petits pas (8 o) servent aux **effets attachés à leur propriétaire** (chez Ryu : X/Y recopiés du propriétaire,
  animation choisie par un octet du mot C de son pas = « position d'objet attaché ») — pas de collision ; les projectiles
  passent par les pas standards (avec boîtes) ⟹ boîtes à zéro cohérentes pour les petits pas ;
- tables de saut à index décalé (`lw x,-8(r)`) reconnues (`0x1D5C4`, aiguillage par type d'objet `$8`) ;
- fiche `psp_1ef54` (allocation dans le réservoir d'effets, équivalent arcade à confirmer) ;
- inventaire : 156 fonctions moteur (les cibles d'aiguillages s'y ajoutent) : 92 auto, 7 à la main, **57 à écrire
  pour seulement 219 appels**.

**Valeurs aux jonctions (2026-10-04)** : traduction en deux passes (`traduire_trad`). La 1re relève, à chaque étiquette,
les registres MIPS **vivants** (lus avant d'être réécrits ; un `jal` ne lit que ses arguments selon l'arité) dont la
valeur diffère selon le chemin ; la 2e les recopie dans un registre de jonction **fixe par registre MIPS** (`D5`, `D6`,
`A2`, `A3`) sur chaque chemin, **avant** le test du branchement. Ex. `0xCF5D8` traduit juste (= version manuelle).
Allocations propres aux persos MAX (`HORS_MAX` : union de travail, `0xAA`, `0x1EA`) séparées : `MODE_MAX = False` pour
l'évaluation sur les persos arcade. Évaluation : 25 identiques, 47 ≥ 0,9 (code parfois plus long que l'arcade, mais
juste), 4 % non traduit. Ébauches : **Eagle 97 %, Maki 96 %, Yun 93 %, Ingrid 86 %** ; moteur : 95 auto, 7 à la main,
**54 à écrire (198 appels, 9,9 Ko)**.

**Suite (2026-10-04, après la publication)** :
- traduits en plus : comparaison `a < b` entre deux opérandes (`MOVE a,D0 ; CMP b,D0 ; BLT/BCS`), décalages par
  registre (`sllv/srlv/srav`), accès via un pointeur d'objet reçu / renvoyé / calculé (`MOVEA.L …,A0` + carte des
  champs), constantes de comparaison masquées à la taille (`#$FF` et non `#$FFFFFFFF`) ;
- **globales propres au PSP** : le bloc `0x39C9E0…` est une structure d'état du PSP (modes/options), pas une copie de la
  zone A5 ; seules **18 adresses** sont consultées par le code MAX → fiche `globales_psp.md`, valeurs à fixer au banc ;
- ébauches : **Eagle 97 %, Maki 96 %, Yun 94 %, Ingrid 90 %** ; moteur : 103 auto, 7 à la main,
  **46 à écrire (166 appels, 8,8 Ko)**.

**Champs : prolongements de zones et allocation (2026-10-04)** :
- prolongements vérifiés sur la vérité arcade (8 paires améliorées, 0 dégradée) : PSP `0x88-0x9F` → `$68-$7F`
  (paire `$2EF6C` : `tst.b $68` ↔ `lb 0x88`), `0x134-0x13F` → `$EB-$F6`, `0x23E-0x26F` → `$25E-$28F` ; puis
  `tester_ecarts.py` (essai de chaque écart de zone par champ, retenu si ≥ 1 paire améliorée et 0 dégradée) :
  `0x53` → `$3B`, `0x119` → `$DD`, `0x26` → `$26` ;
- 24 champs sans équivalent trouvé (C restructuré ou propres à MAX : `0x28/0x2C/0x30/0x34` longs, `0x56`, `0xA4`,
  `0xAB`…) logés pour les persos MAX en `$332-$367` (`HORS_MAX` ; HSFA : libre dans ro5, et ro3 écrit `$330(A6)` en `$44460` d où le décalage ; si le
  moteur arcade lit l'un d'eux sous un autre nom, le banc le montrera) ;
- ébauches : **Eagle 99 %, Maki 98 %, Yun 96 %, Ingrid 95 %** ; moteur : 108 auto, 7 à la main, **41 à écrire
  (154 appels, 8 Ko)**.

## 4. Suite

- Étendre l'API : utilitaires « MAX seulement » (~50 % des appels des 4 persos) : les comparer au 68K par leur corps
  (ce sont peut-être des séquences que le 68K écrit en ligne) ; nommer les fonctions restantes (lecture du 68K).
- Compléter les champs : types (taille, signe) et zones de bord ; vérifier `$102`/`$103` (ID) et `$38` ↔ `0x5C`.
- Traducteur : expressions composées, champs encore inconnus (`0xAA`, `0xAB`, `0xE4`…), globales hors A5 (`0x39C9E0`) ;
  valider un gestionnaire dans le banc ; sons (n° PSP → arcade).

## 5. Reproduire

```
source hsfa/env.sh ; source hsfa/env_max.sh ; cd work/re/rosette_code
python tout.py                      # API (votes sur 26 persos, 3 passes) + champs + rapport (~20-40 min)
python rosette.py                   # Ryu seul, passe 1
python cote_a_cote.py 2a708:5d63c   # une paire : 68K puis MIPS
```
Sorties : `api_arcade_psp.json` (paires sûres), `votes_passe1.json` (soutien indépendant), `champs_votes.json`
(votes et chaîne des champs), `api_moteur.json` + `tableau_api.md` (avec rôles et interpolées).

**Portage du moteur, reprise (2026-10-07)** :
- `brouillons.py` : les fonctions du module d'un AUTRE perso MAX (Maki → module de Yun, Yun → module d'Ingrid) ne sont
  plus comptées « à écrire » (déjà traduites dans l'ébauche de ce perso).
- **Réservoirs d'objets** appariés par le code de type écrit dans `$8` (PSP × 4 = arcade) et les volumes d'appels :
  allocations `0x1EE74/1EEAC/1EF1C/1EF54/1EEE4` = `$1C278/$1C2C8/$1C318/$1C368/$1C3AC`, libérations
  `0x1F19C/1F1C8/1F220/1F24C/1F1F4` = `$1C28E/$1C2DE/$1C32E/$1C37E/$1C3C2` ; compteurs `0xA3E7C2-C6` → `$6EB8-$6EBC(A5)`.
  Allocation traduite : JSR, en-tête (type seul si le sous-type n'est pas fourni), `psp_raz_alloc` (remises à zéro de
  l'allocateur PSP `0x1EFE4` qui tiennent dans un objet arcade de `$80`). ⚠ Objets fils arcade = `$80` octets (PSP
  `0xC0`) : les champs HORS_MAX (`$332-$367`) ne valent que pour la structure joueur ; types d'effets = numéros PSP à
  raccorder.
- **Corrigé** : écriture via un autre pointeur d'objet (A4, A0, A1) à la taille PSP (`sb` → `move.b`) ; avant, la taille
  usuelle du champ 68K (ex. `move.l #1,$0(a4)` écrasait type et sous-type).
- **Sons** : `0x78408` n'est PAS `$38E4` (code absolu PSP contre index dans la table de voix du perso) → point d'entrée
  unique `psp_78408` (muet, chantier sons) ; `cee0c`, `cec94` (répliques + durées, tables `TAB_VOIX_26/27/28`),
  `cee5c` (sons par clé) portés à la main.
- `6a638`/`6ab48` (construction à l'init de l'espace de travail PSP `0x1A0`) : rien à faire en 68K (données statiques).
- **Rosette ciblée sur Ryu** (`rosette_cible.py`, `rosette_ryu.py`, idée de l'utilisateur) : les fonctions restantes
  n'ont pas d'équivalent arcade un pour un (le C du PSP regroupe test + action ; l'arcade a un prédicat et fait l'action
  en ligne) ; mais Ryu sert à identifier les GLOBALES : `0x39CA67` = `$10B(A5)` « pose de victoire terminée » (2 BSET
  par perso arcade, 2 appels de `0x24C04` chez Ryu PSP) → `psp_24c04` porté.
- bilan : **23 fonctions à écrire (70 appels, 4,7 Ko)** ; 92 auto, 14 à la main. Évaluation inchangée (25 identiques,
  47 ≥ 0,9). Rien n'est assemblé (aucun assembleur 68K installé) : syntaxe à valider.

**Partie profonde (2026-10-07, suite) : rosette par champs témoins + PPSSPP** :
- **Entrées** (PPSSPP + routine arcade $27AAC) : PSP 0x2F0/0x2F8/0x2FA/0x2FC = arcade $370/$378/$37A/$37C. Directions
  identiques, boutons codés autrement. Les anciennes cartes étaient fausses (0x2F0 → $38, 0x2F8 → $34, 0x2FA/0x2FC
  logés comme variables de Maki/Yun). Persos MAX : miroir au format PSP (`psp_entrees`, $3E0/$3E2/$3E6/$3E8, à appeler
  à chaque image) ; évaluation arcade : constantes de boutons converties (`conv_boutons`).
- **Méthode du champ témoin** : un champ propre à une mécanique (ex. fenêtre d'annulation 0x27E) se retrouve dans une
  table arcade aux mêmes valeurs ($25204), d'où la routine arcade qui la lit, puis la routine équivalente entière.
  Résultats :
  - 0x67B1C = **$2EB06** (annulation de coup normal), avec 0x67CB8 = $2EB8C, 0x5FA9C = $2B216, 0x67E08 = $2EC0A,
    0x67D68 = $2EBBE ; tables $DC9EA/$DCA72 identiques au PSP sur les 32 persos, nulles pour MAX ;
  - 0x67E50 = $2EC28 (poing faible + pied faible) ;
  - 0x68380 ≈ $2EE2A (contre-alpha : le PSP y ajoute les tests que l'arcade fait dans chaque perso) ;
    0x67468 = $2E8C0 (enveloppe) ;
  - points 0x33058/0x331F8/0x33130 = $2065C/$2070A/$206AE, 0x32E60 = $2055C ;
  - globales : 0x818305 = $10D, 0x39CA06 = $8A, 0x39CA19 = $AC (mode) ; champs : 0x27E = $28E, 0x10E = $D6 ;
    0x318 = options de console (long nul $3EC) ; 0x330 lu comme nul (à revoir).
- Bilan : **15 fonctions à écrire (28 appels, 3 Ko)** ; 93 auto, 17 à la main ; évaluation inchangée.

**Suite (2026-10-07)** :
- 0x60740 = **$2BB26** (retour en garde ; 0x60494 = $2B828, 0x6331C = $2BB5A, 0x6929C = $2F490) ; 0x66BB4 ≈ $2E4C2
  (état de saisie de la victime en A1, enveloppe) ; 0x66AE8 (saisie) écrite à la main ; zones +$10 : PSP 0x270-0x27F
  et 0x2B0-0x2BF.
- **Traducteur corrigé** :
  - numéros d'état (×2) écrits ou comparés via un pointeur d'objet ;
  - arguments D0-D2 relus après un appel : sauvegarde MOVEM sur la pile seulement si un écrasement précède une
    relecture (copies croisées comprises), sinon registres.
  Évaluation : 25 identiques, 47 ≥ 0,9.
- Reste **12 fonctions (20 appels)**, dont deux sous-systèmes :
  - (a) **reconnaissance de manipulations du PSP** (0x63708 / 0x64220, appelés par Yun 2 et Maki 1 ; fiche de progression
    + étapes d'entrée + marges d'options), sans équivalent un pour un dans l'arcade (le test arcade $30A66 est un simple
    bit de table) ;
  - (b) **effets d'Ingrid** (réservoir 0x94 o, gestionnaire global 0x1DC32C…).

**Reconnaissance des manipulations (2026-10-07, PPSSPP + rosette)** :
- PSP : 0x63708(objet, fiche, n°) (et 0x64220, variante « pressions ») = la machine de l'arcade : fiche de 8 octets par
  manipulation (PSP objet + 0x350..0x3B8 = arcade $180..$1E8, décalage $1D0), automate à états (octet 0), étape (octet 1),
  minuterie (octet 4) ; déf. = table 0x2178C8[n°] (table de rechange 0x217C1C pour un réglage console, inutile).
- Arcade : entrées $2D5E2 + 8k (`LEA déf.(pc),A3 ; BRA tronc`) : $2D7E6 (ordinaire), $2D900 (pressions, = 0x64220),
  $2DBBA (charges, préfixe durée $3C), $2DCFE (martèlement) ; appel `lea $1xx(a6),a4 ; jsr entrée ; bne` (D0 = −1).
- `mouvements.py` : 46 / 48 déf. PSP identiques à une déf. arcade (0x2000 = tenue <-> $80, 0x400 <-> $10, boutons
  0x4070 / 0x8380 / 0xD3F0 <-> $0F00 / $F000 / $FF40) ; les 2 restantes (n° 12, 33) ne servent à aucun perso MAX.
  Toutes les manips MAX (n° 1-6, 17, 18, 20, 23, 24, 26-29, 32) tombent sur une déf. arcade unique et le bon tronc.
- Le test PSP 0x63C30/0x63794 (« touches raccourcis » assignables de la console) n'a pas d'équivalent : omis.
- `psp_63708` / `psp_64220` écrites à la main (pont vers les entrées arcade, `TAB_MANIPS`) : reste **10 fonctions
  (17 appels)**.

**Projectiles et objets fils (2026-10-07, suite)** :
- Routines communes PSP ↔ arcade (appariées sur le code) : renvoi 0x72744 = **$33120** (Soul Reflect : gel $125/$15C(A5),
  demi-tour, 2 images, vitesses inversées, $44 = table[$72], étincelle $979FA), 0x72678 = $330C4, disparition 0x725C0 =
  $33074, avancer l'animation 0x728F0 = $33210 ; 0x7284C = $331D0 seulement avec la table par perso $3327A étendue.
- Objets projectiles arcade = $100 octets (allocation **$1C1C8 → A4**, réservoir du camp ; boucle $32EFA, aiguillage
  **$32F46[$2 = n° du perso]**). Traducteur : 0x1ED2C est désormais une ALLOCATION (avant : appel à valeur de retour, faux
  chez Eagle / Yun / Ingrid), en-tête $0 = 1, $2 = n° du perso MAX.
- Carte des champs des objets fils = carte joueur, sauf (`PROJ`, contexte `proj_fn()` = routines des familles d'objets
  du module, + objets neufs A4) : 0xFF → **$BD** (classe au choc de projectiles $24E10, ×2 vérifié sur tous les persos),
  0x158/0x15A/0x15B → $70/$72/$73 ; 0xAA/0xAB/0x56/0xA4 (attributs d'affichage PSP) et 0x164 (table d'animations par
  objet) omis ; liens Ingrid 0x28/0x2C/0x30/0x34 → pointeurs 16 bits $28/$2A/$2C/$2E, 0x54 → $20 (octets libres d'après
  le code des projectiles arcade : à valider au banc).
- Familles d'objets d'Ingrid (table du module 0x2B1EA0 : type → routine) : 0x2D/0x2E → 0x1C7840 (projectiles, 26
  sous-types), 0x35 → 0x1C7260, 0x36 → 0x1C6E58, 0x37 → 0x1C8874, 0x3A → 0x1C8F10 (effets $1C368) ; 60 routines.
- En-tête des allocations : sous-type BRUT dans $3 (les aiguillages traduits doublent l'index eux-mêmes ; avant : ×2,
  soit ×4 au total).
- À fournir par l'intégration : $32F46 (et $3327A si besoin) pour $26-$29, routines arcade des types d'objets MAX.
- **Traducteur, suite** : chaînes de pointeurs d'objets (propriétaire $36, adversaire $38, liens 16 bits, additions de
  constantes aplaties) ; tables de données PSP constantes indexées → `TABD_<adresse>` recopiées en gros-boutiste dans
  `donnees_max.s` (⚠ marque les longs qui ressemblent à des pointeurs PSP) ; table des joueurs 0x213F88[k] = arcade
  $FF8400 + $400 k ($156/$158(A5)). Lignes non traduites : Eagle 56→46, Maki 57→32, Yun 154→128, Ingrid 181→108.
- `fpu.py` : désassemblage avec le coprocesseur flottant. Seule routine flottante des 4 modules : Ingrid 0x1C70D8
  (orbite, cos/sin tabulés 0x1C7514/0x1C75BC) → `psp_1c70d8` à la main en virgule fixe (tables `TAB_ORBITE_X/Y`).
- `brouillons.py` saute les fonctions de module écrites à la main.
- **Dernières fonctions moteur (2026-10-07)** — plus aucune « à écrire » (91 auto, 29 à la main) :
  - saisies : `psp_cf3e8` (Eagle) = 3 conditions MAX + **$2E3E0** (= 0x6666C) ; `psp_66890` (Yun, saisie
    multi-adversaires PSP) = chemin joueur **$2E422** de $2E3FE ; `psp_672dc` (Yun) = **$2E7F2** (= 0x67144, victime =
    adversaire $38) ;
  - `psp_cf644` (Yun) = `psp_cf5d8` + décalage ; `psp_5df68` (Maki) = début d'attaque enchaînée, rappel n° 17 de la
    table de rappels du perso (PSP *(0x1A0) : 39 entrées recopiées depuis Eagle 0x2A3198, Maki 0x2A6268, Yun 0x2AD6DC,
    Ingrid 0x2B1EE0 ; choix par $102 = n° de perso) + 0x77E00 / 0x5FD4C traduites ;
  - neutralisées (visuel / statistique PSP, documenté) : effets de décor d'Ingrid 0x1DC32C / 0x1F338 / 0x1CAF0C
    (objets de 0x94 o de type 13 gérés par la structure du décor 0x87FCB0), record de combo 0x6F35C.
- Traducteur : 0x10E = champ moteur $D6 (la liste d'allocation MAX le réattribuait en $362) ; 0x1E2/0x1E3 → $362/$3F3.
- **Objets des 4 persos** : tables (type PSP, routine) Eagle 0x2A3174, Maki 0x2A6248, Yun 0x2AD6B0, Ingrid 0x2B1EA0
  (`types_objets`) → racines du contexte objet fils (157 routines) ; en-tête d'allocation : sous-type BRUT pour ces types
  MAX, ×2 pour les types du moteur. Projectiles ($1C1C8) : Eagle 0x2B, Yun 0x2C, Ingrid 0x2D/0x2E (`psp_fils_26/28/29`
  pour $32F46) ; Maki : objets $1C368 seulement. Aucun accès hors objet dans les routines d'objets fils.

**Assembleur et traduction (2026-10-07, suite)** :
- **vasm** compilé depuis ses sources (`~/outils/vasm/vasmm68k_mot`, options `-m68000 -spaces`) ; `assembler.sh` assemble
  tout (main, auto, 4 ébauches, tables, données) en un binaire d'essai et regroupe les erreurs. Code écrit à la main :
  0 erreur ; ensemble : 82 erreurs = les 82 lignes « ?? » restantes (418 au départ).
- Traducteur : multiplications / divisions (MULS/DIVS 16 bits), boucles (états des sauts arrière dans les jonctions ;
  test évalué dans D7 avant les recopies de jonction), copies mémoire → mémoire (source en D3 d'abord), étiquettes de
  tables de saut uniques et index calculés, entrées sans prologue (s0 = objet), pointeurs mots ($36/$38/$A4, liens),
  pas courant d'un autre objet (0x128 / 0x1C via $1C), table des joueurs dans les chaînes.
- Initialisations des 4 persos à la main (sans la recopie de la table de rappels PSP) ; famille d'objets « effets de
  décor » d'Ingrid (66 routines, type 13) marquée morte (`mortes()`).
- Reste : physique des sauts (PSP 0x2C0/0x2C4 → tables 0x22C1C6… par style de jeu, posées par 0x6099C) ; registres non
  suivis (<a1>, <s1>…), quelques globales (0x39CA2A/3D/3E, 0x807A50), liens d'objets de Yun/Ingrid (sw … 40-48(aN)).
- `adresses_arcade_max.txt` : 108 adresses arcade (SFA3) utilisées, à vérifier dans Upper (note HSFA §8).
- Suite : décalages 16/24 isolés, jonctions tolérant les chemins sans valeur (registre indéfini selon les conventions
  d'appel MIPS), index de table complexes (D3/D4 sauvés) → **68 lignes « ?? »** (Eagle 16, Maki 9, Yun 16, Ingrid 27),
  longue traîne de cas isolés : globales 0x39CA2A/3D/3E et 0x807A50, liens d'objets d'Ingrid (sw … 40-48(aN)),
  chaînes via 0x124 / 0x30 du propriétaire, pile (<sp>), physique des sauts d'Eagle (0x2C4, attend HSFA).
- Suite (même jour) : décalages 16/24 ; jonctions itérées jusqu'à stabilité (passes successives, mêmes registres) ;
  créneaux « likely » traduits avec l'état des registres du saut ; famille « cycle de palette du décor » d'Ingrid
  (0x1C9024) morte ; **PSP 0x16A = boutons TENUS au format PSP → $3E0** (miroir ; avant : octet $11A, tests des pieds
  bits 8-9 toujours faux) via `PRIORITE_MAX` ; **0x39CA2A lue comme 0** (`GLOB_ZERO` : PPSSPP, nulle dans tout le mode
  arcade) → **30 lignes « ?? »** : physique des sauts d'Eagle (7, attend HSFA), fragment de switch d'Eagle 0x1B6234
  (registres du parent), n° d'image PSP du pas du propriétaire (Ingrid 0x1C8C30 / 0x1C8F9C, numérotation PSP),
  tableau local sur la pile (Maki 0x1BB1A4), table 0x20188A (Maki), pointeurs 0x124 du propriétaire (Yun), liens
  d'objets d'Ingrid via a1/a2 (0x1C87AC, 0x1C8CE0, 0x1C8DF0), champ 0x38 d'un objet (Eagle 0x1B3904 / 0x1B3B1C).
- PPSSPP : les appuis doivent durer en temps RÉEL (`rt.py`) ; en pas émulé (`pas.py`) le jeu ne les voit pas.

**Assemblage complet (2026-10-07, fin de journée)** : **0 ligne « ?? »** dans les 4 ébauches ; `assembler.sh` : plus que
des symboles d'images `F26_n`…`F29_n` indéfinis (fournis par la conversion graphique : index de frames.json du perso).
- Traducteur : liens 16 bits du joueur ($332/$336/$33A/$33E, `LIENS_JOUEUR`) ; nouvel objet A4 dans les chaînes ;
  pointeur de table au format PSP + index (`PTR_TABLES` : 0x2C4 → $34A) ; tableaux locaux constants sur la pile (table
  en ROM) ; lectures de constantes en données en lecture seule ; voix 0x124 lue nulle ; sauts à condition constante
  et code mort ; cas de `switch` internes en étiquettes locales (corps de routine étendu aux cas, alias `psp_x equ L_x`) ;
  tables de saut en ADRESSES LONGUES (`lea tab(pc)` + `movea.l` : cibles lointaines, ±32 Ko) ; fermeture transitive
  des fonctions moteur ; étiquettes d'images préfixées par perso (`tables_explicites.py`).
- Nouvelles correspondances : 0x686EC = $2ECD8, 0x67F84 = $2ED00, 0x682B4 = $2ED28, 0x6808C = $2EDA0, 0x6069C = $2BAF2,
  0x606CC = $2BAF8, 0x1F0F4 = $1C206, 0x72998 = $3323A, 0x670AC = $2E700 ; 0x64A34 = pont `psp_63708` (n° 39 → $2DA84) ;
  `psp_63c30` = 0 (touche raccourci) ; `psp_cf72c` + enveloppes à la main (5 arguments ; caméra 0x81F970+0x12 = $290(A5)).
- Physique : PSP 0x2C4 / 0x2C0 = tables de sauts / marche par style (0x21C3BE/0x21C8FE/0x21CE3E ; 0x21C1C6/0x21C26E/
  0x21C316) = arcade $DD792/$DDF92/$DE792 ; $DD492/$DD592/$DD692 (long arcade = mot PSP << 8 ; vérifié 32/32 persos) ;
  Eagle : $34A posé à l'init selon $132 (`donnees_sauts_max.s`) ; entrées $26-$29 au format arcade : `physique_max_arcade.json`.
- Upper (rapport HSFA) : $32F retiré de `psp_66890`, manip n° 0 ($2D5E2 supprimée) à 0, types d'objets des
  projectiles en constantes `TYPE_PROJ_*` ($32F46 est indexée par TYPE).
- Calques d'Ingrid (0x1C8C30 / 0x1C8F9C : autre moitié du corps par n° d'image PSP) : invisibles sur l'arcade, images
  fusionnées par la conversion -> `num_image_psp` neutre.
- À convertir côté données : en-têtes d'animation des projectiles écrits en adresses PSP brutes ($60/$88 :
  $2A0384/$2A032C, $2AB22C/$2AAFA6, $2AFC4C/$2AFAC8 ; arcade : 5 mots relatifs lus par $3323A).

### Corrections typage HSFA (2026-10-07)
- Caméra PSP = 0x80F970 (lui 0x81 + addiu 0xF970 **signé**) ; +0x10 = X 16.16 → `GLOB` 0x80F980/0x80F982 → $290(A5). Plus de $7788(a5).
- Offsets impairs lus en octet (taille_lecture) ; copies champ→champ : source plus large → partie basse.
- Type PSP des objets fils en $FF(A4) (Upper lit $22 en mot).

### Voix QSound (2026-10-07)
- `commandes_voix_max.s` = livraison HSFA (`hsfa/work/agent_voix_max/`, 134 `equ`, côté 1 ; côté 2 = +$500 par `$3938`) ;
  ROM son à utiliser : `HSFA_SON=<...>/agent_voix_max/roms_voix`. Assemblage inchangé (seuls les symboles F manquent).
- `SONS_COMMUNS` reste à zéro : appariement des bruitages (`sons_communs_max.s`, `appariement_bruitages.tsv`) à valider
  à l'écoute par l'utilisateur (`agent_voix_max/ecoute/`).

### Frames de combat F26_n…F29_n (2026-10-10) — `frames_max.py`
- Accord HSFA : DISPOSITION ARCADE, codes LOCAUX à la banque du perso (local → global au rendu via plXX_hx.bin), données
  dans les blocs externes du fork $D40000 / $D80000 / $DC0000 / $E00000 (256 Ko chacun ; mise en disposition image par
  convertit_max.py d'HSFA).
- Sorties : `frames_{eagle,maki,yun,ingrid}.s` (ORG du bloc, assemblables seuls ; contrôle : binaire assemblé =
  octets calculés, `~/.cache/sfa3max/frames_XX.bin`) et `symboles_frames_max.s` (`F%02X_n equ adresse`, inclus par
  assembler.sh). Toutes les frames de frames.json (723 / 727 / 870 / 1126 ; 72 / 65 / 74 / 103 Ko).
- Format : `dc.w 2, T, n−1, 0 ; dc.l POS ; n × dc.w code, attr` puis `POS : n × dc.w dx, dy` (aligné sur 4) ; frame sans
  objet = `dc.w $0012`. ⚠ Yun : n° PSP 0x8000 (gabarits EBOOT 0x21EE30 / 0x21EE68) → frame vide, à vérifier.
- **assembler.sh : 0 erreur** (tout le code MAX + frames).

### Animations de combat ANIM_26…ANIM_29 (2026-10-10) — `anims_max.py`
- Modèle arcade : init $2FC4A recopie de $DD412[perso] (3 ismes × 16 o) $2B0, $2B8, $2B4, $2BC ; Ryu = un bloc $146218
  ($2B0 = début = banque $AA644). Décalages en **mots signés relatifs au début de CHAQUE sous-table** ($2A762, $1B6E0).
- Sorties `anims_{eagle,maki,yun,ingrid}.s` (ORG $D60000 / $DA0000 / $DE0000 / $E20000 = moitié haute du bloc des
  frames) : ANIM_xx (= $2B0), ANIM_xx_2B4/_2B8/_2BC (ordre exact de animations.json), ANIM_xx_PTRS (gabarit $DD412),
  pas de 20 o (format tables_explicites ; octets de boîtes conformes à Ryu), reprise en +$14 ; pas partagés émis une
  fois. Symboles : `symboles_anims_max.s`. Contrôle : assemblé seul = `~/.cache/sfa3max/anims_XX.bin`.

### Animations des FINS MAX FIN_ANIM_26…29 (2026-10-10) — `anims_fins_max.py`
- PSP : 0x1D4C48 (homologue de $AA630) lit l'animation n dans +$110 de l'état de fin 0x87FCB0, QUELLE QUE SOIT la banque ;
  chargeur 0x1DB424 (descripteur 0x20184C) : +$110[n] = pas10 0x20001 + 10 × index 0x20003[n] ; +$114 = boîtes 0x20005 ;
  +$118[n] = pas8 0x20002 + 8 × index 0x20004[n] (images fixes des décors, n° 0-142).
- Pour la banque du perso MAX, les frames sont ses **frames de combat** (F%02X_n ; Ingrid : remap_ingrid). Banques 38-41
  employées seulement dans la fin de leur perso (vérifié sur les 42 fins).
- Intégration (HSFA) : T_619b50 d'Upper (homologue de $AA644, lue seulement par les acteurs) [$26+k] -> FIN_ANIM_26+k ;
  le combat garde ANIM_xx. Sorties `fin_anims_*.s` (ORG $D70000 / $DB0000 / $DF0000 / $E30000, 2-6 Ko), FIN_ANIM_xx dans
  symboles_anims_max.s. Yun : jeux de boîtes 872+ absents du pac -> 0 (sans effet en fin).

### Retours HSFA sur les acteurs (2026-10-10)
- Structures joueurs PSP 0x80AF70 + 0x498 k (0x213F88) -> absolu $FF8400 + $400 k (champ joueur) ; plus de $2ECA(a5).
- Position privée 16.16 des acteurs $4F/$19 (PSP 0x7C/0x80) -> $5C/$60 (libres pour la classe $4F, le moteur générique $1A000-$1D000 et $2750E ; $28-$2F exclus : moteur générique + libération $1C2DE).
- Contexte acteur : $78-$7F octets non signés ; repère lu en octet -> $1C9 ; événement -> $1CA.b ; comparaisons de
  tailles différentes -> calcul 32 bits ; copie mémoire rétrécie -> partie basse (`decaler`).
- psp_1d96c / psp_1da64 (pose du pas) écrits à la main : `jmp $1B6EE` ; drapeau PSP 0x98 omis (écrasait $78).
- Fiches de manipulation : remise à zéro sans $1D0-$1D7 (champs Upper $1D5/$1D7) ; fiche PSP 0x3A0 (Yun) déplacée en $1E0.
- **Plus aucune ligne « À COMPLÉTER »** (assembler.sh : 0 erreur). Traducteur, contexte acteur (`table_fin`, `fin_off`) :
  état de fin PSP +$12C[n] (petite table d'acteurs [4] : enregistrements de 32 o, mots +0..+6 retournés) -> `bsr
  fin_t12c` (A0, table par fin, `donnees_fins_t12c.s` : Maki 1, Yun 8) ; +$114 (boîtes du pas courant) -> octets +8 du pas
  68K ; +$110[n] -> `bsr fin_pas110` (D7 = pointeur du pas dans FIN_ANIM_xx) ; +$118[n] (images fixes du pac, non
  converties) -> `fin_pas118` = 0, pose du pas ignorée. Routines écrites à la main : `acteurs_fins_main.s`.
- +$A0 = décalage vertical des 3 plans (appliqué puis remis à 0 chaque image, 0x1DA534) -> add.w sur $214/$294/$314(A5).
- Tableau PSP 0x2B3EC (12 mots écrits par l'acteur $4F/05, lus par $4F/19) = champs $40-$57 de l'objet arcade $4F/05
  ($AAFAC, octets << 4) -> `fin_pos_4f05` cherche l'objet dans le réservoir $3000(A5) (32 × $80 ; +2 classe, +3 sous-type).
- psp_1d75c4 (effet de décor type 26, globales 0xA4CED0/4, 0x39CA3E) : neutralisé comme les effets de décor d'Ingrid.
- acteurs_fins.py retire les fonctions traduites que plus rien n'appelle (ex. 0x1F3BC, libération d'effet de décor).
- ⚠ Défaut connu du traducteur : deux tirages aléatoires successifs ($1BDA6) sont émis avant leurs usages (X et Y
  reçoivent le même tirage dans acteur_1d586c).

### Animations des acteurs ré-appariées sur UPPER + décor des fins MAX (2026-10-10)
- **Base = Upper** (ro5 : `anthology_extract/decompressed/ro5_usa_prog68k.bin`, petit-boutiste, fichier = PS2 − 0x1F0000 ;
  banques des acteurs T_619b50 = PS2 0x619B50, 40 longs ; banques 32/33 = persos d'Upper). Pas de 20 o = mêmes octets
  que l'arcade (pointeur de frame en petit-boutiste). Numéros 0-75 : même numérotation que l'arcade (65-76 signatures
  sur 76 identiques au même n°, aucun décalage global).
- `convert/rosette_donnees.py` : classe $4B -> correspondance EXACTE sur Upper (signature + motif de frames, ≥ 2 pas)
  prioritaire sur le vote (Eagle banque 10 n° 0 -> 68, Maki n° 3 -> 75, n° 4 -> 76 ; banques 32/33 -> 0 / 2) ; repli
  vote puis contenu arcade. Restent absentes d'Upper (animations propres à la PSP) : banque 33 n° 20, banque 3 n° 6.
- Avances arcade : $1B692 = pas de 20 o (classe $4B, banques de combat) ; $1B6B6 / $1B6F8 = pas de 8 o (classes de
  décor) -> dans le code d'acteurs, PSP 0x1D9B0 (avance pas8) = `jsr $1B6B6`.
- Tables GLOBALES de décor (arcade) : $81522 (classe $48/01, pas de 8 o en $50(A6)), $2F4284 (classe $49/00-$11),
  $2E50A0, $301FA2[$BB+2] (classe $4A : n = rang du pas de 8 o) et listes $E/$F (classe $4E).
- `decor_fins_max.py` : sprites propres au pac de chaque fin MAX -> `decor_fin_*.s` (frames FD%02X_n à codes LOCAUX de
  la banque gfx de fin d'Upper, emplacement 4 ; table FIN118_xx = +$118 en pas arcade de 8 o, ORG $D78000 + $40000 k ;
  contrôle : assemblé = decor.bin), tuiles / palettes dans `~/.cache/sfa3max/converti/plXX/fin/decor/` (Eagle 120
  frames / 1 843 tuiles, Maki 10 / 389, Yun 15 / 608, Ingrid 53 / 1 336). Rendu vérifié (cape, vitrail, pose d'Ingrid,
  éclat d'Eagle, calligraphie de Yun). `fin_pas118` lit FIN118_xx.
- Acteurs de décor d'arcade dans les fins MAX : n° SYMBOLIQUES ND<fin>_<n° PSP> (à définir à l'intégration = rang de
  l'entrée ajoutée) ; liste « symbole -> table -> label du 1er pas » : `decor_nouveaux_max.md`.
- Reste : n° 119 (explosion, frames 300-305 d'efct.pac, acteur MAX $4F/19 de Maki et Yun) : candidats arcade de même
  signature $2E50A0 n° 0 et n° 5 -> HSFA : n° 5 (6 frames type 6 identiques au pixel près, pas $2E565C…) -> fin_pas118 renvoie le symbole EXPLO_PAS (table FIN118X
  d'acteurs_fins_main.s ; adresse arcade $2E565C dans symboles_externes_max.s, relogée à l'intégration) et pose $1A = EXPLO_1A ($0000 dans Upper, $6000 dans l'arcade ;
  palette $16, $C de l'acteur = 0) ; les images FD.. posent $1A = BANQUE_1A_DECOR_FIN = $8000 (emplacement 4). Frames hors pac
  d'autres images fixes : inutilisées par les acteurs.
- **Substituts provisoires (choix de l'utilisateur, 2026-10-10, point toujours ouvert)** : deux animations PROPRES À LA PSP,
  absentes d'Upper (aucune suite d'images équivalente, même en ignorant les durées) : Charlie fin d'Eagle (banque 3 n° 6,
  boucle lente frames PSP 681-683) et Fei-Long fin de Yun (banque 33 n° 20, 13 pas, frames 801-806) -> garde Upper n° 0
  (`SUBSTITUTS` de rosette_donnees.py). Les n° d'images dépassent le pac de combat (Charlie 384, Fei-Long 482) : jeu
  d'images de fin chargé à l'exécution, source introuvable dans l'ISO (end, endcom, efct, op, win, rk, bd examinés ; les
  fins d'arcade emploient aussi des frames > 384 de Charlie). À faire : observation PPSSPP pendant ces fins (débogueur
  ppdbg) pour retrouver les images, puis ajout de vraies animations aux banques Upper.
  Piste HSFA pour la reprise : sur PS2 (Upper), ces frames de fin au-delà du pac de combat sont dans l'EMPLACEMENT 4
  (fichier de fin propre à chaque fin, chargeur 0x4114A0, table 0x6283C0 -> $C0BC(A5), fichiers 391-418, lignes « anim »
  de carte.txt) ; acteurs de sous-type ≥ $80, $1A = $8000, animation lue dans $C0BC (variante de $AA630, image $4B52A).
  Sur PSP, chercher l'équivalent (archive indexée par n° de fin) : points d'arrêt sceIoOpen / sceIoRead au lancement des
  fins d'Eagle et de Yun sous PPSSPP. Les vraies animations iront alors dans le fichier de fin MAX (emplacement 4,
  BANQUE_1A_DECOR_FIN), pas dans les banques de combat.
- **(2026-10-11) Substituts remplacés : INVITÉS des fins MAX.** La PSP range les images des persos invités d'une fin dans
  le pac de COMBAT du perso MAX qui la possède : Charlie et Guile de la fin d'Eagle = pl26 frames 667-683, Fei-Long de
  la fin de Yun = pl28 frames 786-806 (observation PPSSPP : pendant la fin, seuls endcom / end26 / win26 sont ouverts ;
  aucun pac de Charlie). `INVITES` (rosette_donnees.py) : banque de l'acteur -> perso MAX ($26 / $28), n° PSP gardé ->
  FIN_ANIM_26[6] (F26_681-683) et FIN_ANIM_28[20] (F28_801-806). ⚠ Palette : sur PSP, un acteur de la banque du joueur
  prend la palette du joueur (0x1D4C48) ; ces invités doivent garder la leur (à vérifier à l'intégration).
