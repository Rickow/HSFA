# INJECTION-FORK — décors widescreen dans le programme TRADUIT (fork `sfa3hx`, cœur FBNeo HSFA)

Dossier : `<workspace>/work/decors_ws/injection_fork/`. Rien n'a été modifié dans les fichiers partagés
(`src/hsfa`, `work/mame*`, ROM graphique, plans du banc, `github/`). Construction faite avec une **copie**
d'`untranspile` (`untranspile/`, seul changement : `banques.py` accepte `BANQUES_OUT`) et `TRAVAIL=trav/`.
Cœur FBNeo : **worktree local** `fbneo-decors/`, branche `decors-ws` (partie de `widescreen`), un commit local, rien de poussé.

## 1. Résumé

- **Injection portée et validée de bout en bout** sur le décor `$0C` (temple de Sodom), avec le PSD de test
  (remplissage miroir, `reimport/test_0C`) :
  - **fork MAME** (fenêtre 448 simulée par défilement ±32, comme l'essai arcade) : bandes **identiques à l'aperçu de
    l'outil (0 px hors sprites/HUD)**, vue 4:3 **identique au témoin** ; rendu 448 hors ligne des plans seuls depuis le
    relevé : **0 / 7 168 px** d'écart sur chaque bande ;
  - **cœur FBNeo widescreen (vrai 448×224)**, construit sur la branche locale : 48 captures aux butées, bande gauche
    24/24 exactes, bande droite 20/24 exactes + 4 pendant une super de Cammy où la caméra monte de 3 à 16 px
    (**exactes après recalage vertical**) ; **vue 4:3 identique au témoin sur les 48** ;
  - 3 parties Arcade complètes (Ryu, Sodom sur le temple injecté, perso `0B`) jusqu'à la fin : fins conformes
    (captures 79/79, 46/46, 53/54).
- **Méthode** : on n'injecte pas les blocs arcade (les données du portage PS2 diffèrent : listes, super-tuiles), on
  convertit la carte étendue de `reimport.py` en **codes locaux du fork** et on **reloge** listes, bibliothèques et
  palettes dans un **bloc externe** (`ext_c80000.bin`, 429 Ko) ; le programme ne change que par **18 opérandes de
  `LEA`** (54 octets). SFA3 passe en **mode « bases de plans »** comme Upper (`HSFA_PLANS=300,340,3a0`).
- **Trois découvertes qui corrigent REIMPORT.md** :
  1. scroll3 : la routine (arcade `$1FC70`, ro3 `$639A`/`$660E`) ne copie que **31** palettes et force **`$7F` au
     blanc** → `$7F` n'est jamais utilisable (le test `pal_reloge` l'utilisait : 547 px faux, vérifié) ;
  2. les palettes « libres » doivent être calculées sur les **tilemaps complètes** du décor (données du programme), pas
     sur le relevé : `$7A` (le seul emplacement « libre » du décor `$0C` selon REIMPORT §5.4) sert à 14 cases au-dessus
     de la course, `$57` à 2 cases (rangée 55). **Sans relogement, le décor `$0C` n'a aucune palette libre** ; avec
     relogement : 14 (`$3C-$3F`, `$58-$5F`, `$7D-$7E`). Table pour les 32 décors : `palettes_libres_ro3.json` ;
  3. anneau scroll1 (§7C) : le correctif proposé (`$FFA0`) va dans le mauvais sens. Mesure sur le fork : en reculant,
     jusqu'à 3 colonnes de 8 px périmées dans la bande droite (25-30 % des images à 6-8 px/image) ; corrigé par
     **`$FFC0 → $FFE0`** aux mots `+0` et `+8` de la table (ro3 `$9C1E0`, arcade `$18BA6`) : **0 colonne fausse** à
     2, 6 et 8 px/image dans les deux sens.
- **Étape « décors » intégrable** : `etape_decors.py` (PSD rempli → ROM corrigée + bloc externe + région graphique +
  zip FBNeo), 14 s pour un décor, validée par les mêmes essais (§8).

## 2. Fichiers

| Fichier | Rôle |
|---|---|
| `etape_decors.py` | **étape « décors »** : `hsfa_plans.py` (ro3, `VIDE15=1`) → `reimport.py` par décor (palettes sûres) → `injection_fork.py` → option `--anneau`, option `--zip` |
| `injection_fork.py` | carte(s) étendue(s) de `reimport.py` → codes locaux, blocs/listes/palettes relogés, opérandes `LEA`, vérification (0 écart exigé) ; plusieurs décors en une passe (`--decor-spec DOSSIER:0C+28`) |
| `py/blocs_tr.py` | format des données de décor du programme traduit ; `depuis_carte()` repère adresses et sites dans `carte_image.txt` par les **adresses PS2** (ro3 et ro5) |
| `py/palettes_libres.py` | emplacements de palettes sûrs par décor (tilemaps complètes), relogés / en place → `palettes_libres_ro3.json` |
| `py/image.py` | image programme 4 Mo ↔ fichiers `sz3ud.03c…` (mots échangés) |
| `py/verif_format.py` | contrôle du format traduit contre l'arcade (via `plan1/plan2/f312`) |
| `lua/essai_fork.lua` | essai fork : partie, Ryu, décor forcé, caméra aux butées, captures ±32, relevé FRM0 ; `PALREF` (attente de palettes nominales), `FRMTOUT`/`ALLER_RETOUR`/`VITESSE` (anneau) |
| `lua/garde_tournee.lua` | `tournee.lua` + relevé des valeurs écrites dans `$FF8100` |
| `mame/lance.sh` | `cps2f sfa3hx`, `nice 19`, nvram/cfg/state/snap dans `mame/<NOM>/`, jamais `-state` |
| `py/compare_essai.py`, `py/rendu448_fork.py`, `py/rendu_plans_dy.py`, `py/anneau.py` | comparaisons fork (bandes vs aperçu, rendu 448 hors ligne en mode base, rendu par plan à caméra déplacée, anneau en mouvement) |
| `fb/hsfa_decor.c` (+ binaire) | lanceur libretro sans fenêtre (copie de `hsfa_run.c`) + scénario de l'essai via la RAM libretro |
| `py/paquet_decor.py`, `py/paquet_tables.py` | zips `sfa3hsfa.zip` mode base / mode tables (copie locale de `paquet_fbneo.py`) |
| `py/compare_fb.py` | essai FBNeo 448 : bandes vs aperçu (recalage vertical automatique), 4:3 vs témoin |
| `fbneo-hsfa-decors.patch` | portage FBNeo (commit `682b2bb` de la branche locale `decors-ws`) |
| `paquet_fbneo-decors.diff` | modification proposée de `paquet_fbneo.py` (non appliquée) |
| `sorties/<test>/` | sorties de l'outil : `roms/sfa3hx/`, `ext/` (bloc + liens + `ext_liste.txt`), `hsfa_plans_decor.bin`, `tuiles/` + `hsfa_gfx.txt`, `rapport_fork.json` |
| `captures/` | planches avant/après (§6) |

Construction ro3 de référence : `trav/` (md5 `sz3ud.03c` = `f2f46b7e…`, identique à `work/mame/roms_tr` du 2026-10-10).

## 3. Où le programme traduit lit les données de décor

Les **listes, bibliothèques de blocs, super-tuiles et palettes** sont des **données du module PS2**, rangées dans
l'image programme traduite (zone de données à partir de `$94000`). Les **tuiles** viennent des **fichiers graphiques**
du portage : mémoire de décor `e256` (MWo3, vue en 8×8 pour scroll1 et en 16×16 pour scroll2) et conteneur 32×32
`e312` (scroll3).

| Donnée | Image ro3 | Adresse PS2 (constante) | Sites `LEA abs.L` (adresse de l'instruction ; opérande à +2) |
|---|---|---|---|
| type scroll1 (mot, octet faible) | `$18C9F0` | `0x67C630` | `$024D86` (non relogé) |
| listes scroll1 / 2 / 3 | `$18CA30` / `$18CB5C` / `$18CD8C` | `0x67C670` / `0x67C79C` / `0x67C9CC` | `$024DA2` / `$0251EC` / `$0252F2` |
| blocs scroll1 | `$107670` (94 blocs) | `0x5F72B0` | `$024EDA $025012 $0250C4 $0250DC` |
| super-tuiles | `$10A570` (**2 377**, arcade 2 482) | `0x5FA1B0` | `$024FB0 $025058 $0250F0` |
| blocs scroll2 | `$12F7B0` (146) | `0x61F3F0` | `$025296` |
| blocs scroll3 | `$14ADB0` (réels `$00-$8A`) | `0x63A9F0` | `$02538A` |
| palettes scroll1 / 2 / 3 | `$1619D0` / `$165EB0` / `$16CD10` | `0x651610` / `0x655AF0` / `0x65C950` | `$6366,$65DA` / `$6380,$65F4` / `$639A,$660E` (deux variantes de routine) |
| table de l'anneau scroll1 | `$9C1E0` (8 mots) | — | `$024F5E`/`$024F6C` (via `LEA $9c1e0`/`$9c1e2`) |

Upper (ro5), relevé dans `work/mame_ro5/carte_image.txt` : listes `0x747F30/0x7480D4/0x748344` (type `0x747EE0`),
blocs `0x69B830`, super-tuiles `0x69F3B0`, s2 `0x6CF5F0`, s3 `0x6EF3F0`, palettes `0x70E560/0x7147E0/0x71D420` ;
`blocs_tr.depuis_carte(..., "ro5")` retrouve les 18 sites. Non essayé (§9).

**Format** (vérifié : cases du décor `$0C` reconstruites et converties en codes arcade par `plan1/plan2/f312` :
s1 8 122/8 192, s2 4 096/4 096, s3 toutes sauf la tuile vide) :
- mots (codes, indices de super-tuiles, palettes 0RGB, tables de décalages) : ordre naturel, comme l'arcade ;
- octets (listes, attributs des blocs s2/s3) : le code traduit lit l'octet `k` à l'adresse `k ^ 1` (paires échangées
  dans l'image) ; le type scroll1 est l'octet faible du mot ;
- super-tuile : **long PS2, moitiés échangées** : mot `+0` = attribut, `+2` = code ;
- codes **locaux** : s1 = indice 8×8 de `e256`, s2 = mot du bloc **+ `$1600`** = indice 16×16 de `e256`, s3 = indice
  `e312` sans ajout ;
- la routine copie **128 octets** de liste (et non 4/8/16/64) ;
- **les données PS2 diffèrent de l'arcade** : liste scroll1 du `$0C` = `0,8,9,10,0,8,9,10` (arcade
  `0,$40,$0B,$0C,0,8,9,10`), super-tuiles renumérotées. Palettes identiques. → on part toujours des données traduites.

## 4. Tuiles neuves : SFA3 en mode « bases de plans »

`hsfa_plans.py` avec `MODULE=ro3` et **`HSFA_PLANS_VIDE15=1`** (sinon la tuile 32×32 vide de `e312`, code 0, utilisée
832 fois par le `$0C` en palette `$7F`, devient opaque) : 65 536 tuiles 8×8 (`$3000000`), 35 328 16×16
(`$3400000`), 4 096 32×32 (`$3A00000`), 12 Mo. `HSFA_PLANS=300,340,3a0`, `HSFA_GFX=…hsfa_plans.bin@3000000`.
Contrôle : mode base contre mode tables actuel, fork et FBNeo : **1 pixel** diffère (une tuile du sol dont la donnée PS2
diffère d'un pixel de la tuile arcade choisie par `banques.py` ; le mode base montre la donnée PS2).

Codes locaux neufs (le fork range les vues 8×8, 16×16 et 32×32 dans des **copies séparées** : réécrire la vue 8×8 ne
touche pas scroll2) :

| Plan | Utilisés par les bibliothèques | Codes neufs | Place |
|---|---|---|---|
| scroll1 | ≤ `$5514` | `$6000`-`$FFFF` | 40 960 |
| scroll2 | `$1610`-`$8276` (vue de 35 328) | `$8A00`-`$BFFF` (avant la zone 32×32) | 5 632 |
| scroll3 | < `$1000` (`e312` = 4 096) | `$1000`-`$3FFF` fork ; **`$1000`-`$2FFF` FBNeo** (région de 64 Mo) | 12 288 / 8 192 |

Chaque case nouvelle de la carte étendue est rendue en pens depuis la région arcade corrigée, cherchée (4 retournements)
dans la mémoire de décor du fork (test miroir : 45/116/15 cases reprises, 14/6/0 tuiles neuves, comme l'arcade), sinon
écrite au code suivant. Sorties : `hsfa_plans_decor.bin` (copie complète) et `tuiles/*.bin` + `hsfa_gfx.txt`
(`fichier@décalage`, à charger après `hsfa_plans.bin`).

## 5. Bloc externe : relogement des données de décor

`ext_c80000.bin` (`$C80000` : base fixe du fork, libre en ro3 ; mots gros-boutistes, servi par `HSFA_EXT`,
`banc_mem.lua` et `paquet_fbneo.py` via `ext_liste.txt`). Disposition (étape du §8) :

| Zone | Adresse | Contenu |
|---|---|---|
| listes s1 / s2 / s3 | `$C80000` / `$C802A4` / `$C80644` | table + toutes les listes (+128 o), décalages inchangés ; à la fin, une **liste propre** par décor injecté (et décor lié) |
| blocs s1 | `$C80E44` | 94 d'origine + neufs à partir de `$5E` |
| blocs s2 | `$C83DC4` | 146 d'origine + neufs à partir de `$92` |
| blocs s3 | `$C9F6C4` | 256 + neufs au-delà du plus grand bloc cité (`$8B`, `$8F`) |
| super-tuiles | `$CAB6C4` | 2 377 + neuves dédoublonnées (9) |
| palettes s1 / s2 / s3 | tables `$CD4B60` / `$CDCBE0` / `$CE4C60` | table au milieu (décalages signés), **32 palettes complètes par décor** (1 Ko) ; palettes neuves dans le bloc du décor |

Taille : 429 Ko pour 32 décors (dont 96 Ko de palettes, 192 Ko de bibliothèques s2 réservées). Le programme : 18
opérandes `LEA` (§3). Vérification intégrée : tilemaps recomposées depuis l'image corrigée + bloc externe et rendues avec
la région du fork = carte étendue (cases nouvelles), cases d'origine, autres décors (90 plans) et palettes inchangés.

**Palettes sûres** (`py/palettes_libres.py`) : emplacement 0-31 non utilisé par **aucune case des tilemaps complètes**
du décor (et de ses décors liés), jamais `$7F` en scroll3. `injection_fork.py` refuse une palette neuve qui ne l'est
pas (`--forcer-palettes` pour passer outre). `etape_decors.py` passe cette liste à `reimport.py --palettes-libres`.

**Décors liés** (mêmes listes et palettes) : `$00/$2E`, `$08/$24`, `$0C/$28`, `$22/$26`, `$2A/$3C/$3E` (+ `$14` pour
s1/s3). Sans relogement, l'extension du `$0C` passait aussi au `$28` par la liste partagée ; ici chaque décor a sa liste,
et `--decor-spec …:0C+28` étend les deux.

## 6. Essais

Scénario commun : partie, Ryu, décor forcé `$0C` (prise sur `$FF8100`), caméra aux deux butées (X des joueurs imposés,
traduction : `+$12`), PSD de test de `reimport/`.

### 6.1 Fork MAME (`cps2f sfa3hx`, ROM corrigée, `HSFA_EXT`, `HSFA_GFX`, `HSFA_PLANS`)

Le pilote MAME rend en 384 : fenêtre 448 **simulée** (défilement X des 3 plans décalé de ±32 px, comme l'essai arcade)
et **rendu 448 hors ligne** (relevé FRM0 + région du fork en mode base). Captures prises seulement quand les palettes
de décor sont nominales (`PALREF` : la super de Chun-Li assombrit le décor au début).

| Essai | Bande gauche MAME vs aperçu (hors sprites/HUD) | Bande droite | Rendu 448 hors ligne (plans seuls) | 4:3 vs témoin |
|---|---|---|---|---|
| miroir (`test_0C`) | 0 / 3 509 px | 0 / 3 980 px | 0 / 7 168 et 0 / 7 168 | identique |
| couleurs altérées + `$7A` (`test_0C_pal`) | 0 | 0 | 0 / 0 | identique (mais `$7A` est prise hors course, §1) |
| 17 palettes dont `$7F` (`test_0C_pal_reloge`) | **316** | 0 | **547** / 0 | identique — les 547 px sont tous en `$7F`, forcée au blanc |
| 14 palettes sûres (`reimport_tests/test_0C_pal_sur`) | 0 | 0 | 0 / 0 | identique |
| étape complète (miroir, `+28`, anneau) | 0 | 0 | 0 / 0 | identique (témoin avec le même correctif d'anneau) |

### 6.2 Cœur FBNeo widescreen, vrai 448×224

Cœur construit sur la branche locale (§7), lanceur `fb/hsfa_decor` (scénario par la RAM libretro), 24 captures par butée.

| Essai | Bande gauche vs aperçu | Bande droite vs aperçu | 4:3 vs témoin |
|---|---|---|---|
| miroir | 24/24 exactes (≈7 000 px comparés) | 20/24 exactes ; 4 pendant la super de Cammy, exactes après recalage (caméra montée de 3, 6, 13, 16 px) | 48/48 identiques |
| étape complète | idem | idem | 48/48 identiques |
| 14 palettes sûres | idem | idem | 44/48 : les 4 images de la super montent la caméra sur des cases **de la course** jamais vues par le relevé, que le test « perturbé » a recolorées (`test_synthetique --perturber` réencode les cases nulles du pilote) ; le test miroir n'en a aucune |

Mode tables (production actuelle) contre mode base : 1 px (§4).

### 6.3 Parties Arcade complètes (fork, ROM injectée, `garde_tournee.lua`)

Ryu (`00`) : 4 manches, fin 79 captures (réf. 79) ; Sodom (`06`, combats sur le temple injecté) : 7 manches, 46 (réf. 46) ;
`0B` : 6 manches, 53 (réf. 54, tolérance ±1). Valeurs écrites dans `$FF8100` : `$00-$3A` seulement (jamais au-delà des 32
entrées des tables relogées). Ces trois parties ont tourné avec une version intermédiaire (blocs s3 neufs `$07/$51`) ;
relance de Sodom avec la version finale (`$8B/$8F`, `sorties/etape_miroir`) : 7 manches, fin 46 captures (réf. 46).

### 6.4 Anneau scroll1 en mouvement (REIMPORT §7C)

`essai_fork.lua` (`FRMTOUT=1 ALLER_RETOUR=1 VITESSE=v`) relève chaque image d'allers-retours complets ; `py/anneau.py`
compare chaque colonne d'anneau visible dans la fenêtre 448 à la tilemap complète attendue (affichage t = registres
t-1 + VRAM t).

| Vitesse caméra | Sans correctif : bande droite en reculant | Avec `$9C1E0`/`$9C1E8` = `$FFE0` |
|---|---|---|
| 2 px/image | 1 colonne (8 px) fausse sur 28 / 548 images | 0 |
| 6 px/image | 1 à 3 colonnes sur 36 / 182 | 0 |
| 8 px/image | 1 à 3 colonnes sur 42 / 137 | 0 |

En avançant, et dans la vue 4:3 : 0 dans tous les cas. Le correctif (composition à gauche à −32 au lieu de −64) touche
tous les décors à anneau : à valider sur les autres. Arcade : mêmes mots `$18BA6` et `$18BAE`.

### Captures (`captures/`)

`fork_{gauche,droite}_avant_apres.png` (fork, défilement ±32 : témoin | injection), `fbneo448_{gauche,droite}_avant_apres_apercu.png`
(FBNeo 448 : témoin / injection / aperçu de l'outil), `fork_bande_*_mame_apercu_ecarts.png` (bande MAME | aperçu |
écarts), `fork_rendu448_horsligne_*.png`, `fbneo_super_camera_montee_3809.png` (image de la super : témoin, miroir,
palettes, écarts).

## 7. Cœur FBNeo : portage fait (branche locale `decors-ws`), reste à faire

Commit `682b2bb` (`fbneo-hsfa-decors.patch`, 150 lignes) :
- `cps_hsfa.cpp` : le mode « bases de plans » (registres `$804200-$804205`, bases écrites à la 1re image,
  `nCpsGfxScroll`) vaut pour **tout jeu dont la config donne `plans=`**, SFA3 compris ; la prise VRAM de renumérotation
  ne sert plus qu'à SFA3 sans `plans=` (états sauvegardés : `Raw90` seulement dans ce cas) ; `hsfa_gfx.bin`
  facultatif ;
- `d_cps2.cpp` : `sfa3hsfa` : région graphique de 64 Mo, `hsfa_gfx.bin` facultatif (`BRF_OPT`).
- Aucun changement pour le bloc externe : `paquet_fbneo.py` met déjà dans `hsfa_ext.bin` toute base de `ext_liste.txt`.

Reste :
1. reporter le commit sur `master` (cœur 4:3), `widescreen` et `flux` (le worktree `fbneo-hsfa-ws` est sur `flux` avec
   des changements en cours : non touché), reconstruire Linux + Android ;
2. `paquet_fbneo.py` : appliquer `paquet_fbneo-decors.diff` (si `work/mame/decors/` existe : ROM, `ext/`, `plans=`,
   `hsfa_gfx.bin` = `hsfa_plans_decor.bin` en `+$1000000`) ;
3. compatibilité : un zip « décors » sur un ancien cœur garde la 4:3 juste mais montre des tuiles fausses dans les
   bandes (renumérotation par tables) ; un ancien zip sur le nouveau cœur marche comme avant ;
4. Android : SFA3 passe de 32 à 64 Mo de région graphique (comme Upper).

## 8. Recommandation : étape « décors » de la construction

`etape_decors.py`, après `mame_test.py`, entrée = **PSD rempli par l'utilisateur** :

```
cd <workspace>/work/decors_ws/injection_fork
../venv/bin/python etape_decors.py --psd <PSD> --decor 0C=../out/decor0C_temple_cloche+28 [--decor ...] \
    --travail <workspace>/work/mame --sortie <workspace>/work/mame/decors --anneau --zip
```

1. `hsfa_plans.py` (`MODULE`, `HSFA_PLANS_VIDE15=1`) ;
2. par décor : palettes sûres (tilemaps complètes, décors liés compris) → `reimport.py --zone 448 --palettes-libres …` ;
3. `injection_fork.py` sur tous les décors en une passe (adresses et sites repérés dans `carte_image.txt` par les
   adresses PS2 : valable après toute reconstruction ; vérification, code de sortie ≠ 0 si écart) ;
4. `--anneau` : table de l'anneau corrigée (motif cherché dans l'image) ;
5. `--zip` : `sfa3hsfa.zip` du cœur (mode base).

Intégration proposée : variable `DECORS=<PSD>` de `mame_test.py` (ou de `valide_tout.sh`) qui lance cette étape sur
`P['travail']` après l'écriture des ROM ; le banc et `nonreg.sh` passent alors en mode base pour SFA3
(`HSFA_PLANS=300,340,3a0 HSFA_GFX=…/decors/hsfa_plans_decor.bin@3000000 HSFA_EXT=…/decors/ext -rompath …/decors/roms`) ;
`paquet_fbneo.py` prend `decors/` s'il existe. Sans PSD, rien ne change.

## 9. Ce qui reste

- **Autres décors** : exporter les 28 décors dans le PSD (pilote `DECORS-WS`), puis une passe de l'étape. Penser aux
  décors liés (§5). Capacités : 162 numéros de blocs s1, 110 s2, 117 s3, 63 000 super-tuiles, 40 960 / 5 632 / 8 192
  codes de tuiles : suffisant pour les 32 décors.
- **Course verticale du PSD** : l'export ne couvre que −16/+5 px. Une super (Cammy) monte la caméra de 16 px : le haut
  des bandes montre alors des cases hors PSD (contenu d'origine des blocs). Exporter une course Y plus grande (+32 px en
  haut) avant de peindre.
- **Fork** : `HSFA_EXT` ne lit que des bases fixes (`$C80000` convient pour ro3) ; lire `ext_liste.txt` comme
  `banc_mem.lua`/`paquet_fbneo.py` serait plus souple (Upper : `$C80000` est déjà sa fin de données).
- **Upper (ro5)** : adresses relevées (§3) ; à faire : export des décors d'Upper sur le fork (le pilote travaille sur
  l'arcade ; les décors neufs d'Upper n'y sont pas), codes libres (`e353` : vue 16×16 de 42 496 → `$A600-$BFFF` ;
  `e525` : 4 576 → `$11E0+` ; plafond s1 à mesurer sur ses super-tuiles), base du bloc externe (`$E00000` côté FBNeo ;
  fork à étendre), ajout de `$1C00` en s2.
- **Corrections à reporter dans `REIMPORT.md`** (non modifié ici) : §5.4 (31 palettes + `$7F` blanc en scroll3 ;
  emplacements libres d'après les tilemaps complètes : `$7A` n'est pas libre) ; §5.5 (format traduit : octets `^1`,
  super-tuiles `(attr, code)`, sites = adresses d'instruction, données PS2 différentes de l'arcade) ; §7C (`$FFE0`, pas
  `$FFA0`, et c'est le côté droit qui se périme en reculant).

## 10. Pièges

- Toujours `HSFA_PLANS_VIDE15=1` pour ro3 en mode base.
- Liens `ext_*.bin` : chemins absolus (un lien relatif cassé faisait perdre le fichier 289 à `$A04000` → partie
  différente) ; `injection_fork.py` le vérifie maintenant.
- Le hasard du programme traduit dépend des cycles : comparer chaque essai à un témoin construit avec les mêmes
  correctifs de code (ex. anneau).
- Les tests `--perturber` de `reimport` modifient aussi des cases de la course jamais relevées : écarts attendus quand la
  caméra sort de la course enregistrée.
