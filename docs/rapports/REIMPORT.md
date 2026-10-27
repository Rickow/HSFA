# REIMPORT — image → tuiles CPS2 (décors widescreen, plus tard images MAX)

Dossier : `<workspace>/work/decors_ws/reimport/`. Rien n'a été modifié ailleurs : les fichiers du pilote
(`out/`, `py/`, `lua/`, `gfx/`, `rec2/`, `work/`) sont lus, et `py/cpsgfx.py`, `py/recio.py`, `py/psdwriter.py` sont
importés. Venv : `../venv`. MAME : `mame/lance.sh` (nice 19, nvram/cfg/state/snapshot dans `reimport/mame/`, jamais
`-state`).

## 1. Résumé

- **Outil** `reimport.py`. Il lit le PSD du pilote, vérifie la zone d'origine, découpe et quantifie les tuiles
  (palette existante, sinon palettes neuves par k-moyennes, avec tramage en option) et déduplique avec les
  retournements X/Y contre toute la ROM. Il encode ensuite au format de la région `:gfx` de MAME, qui est aussi celui
  du fork. Il produit la carte du monde étendue, les blocs d'octets, les palettes et les aperçus. **Recomposition
  depuis les tuiles encodées = image quantifiée : 0 px d'écart**, dans tous les tests.
- **Format des données de décor de SFA3 établi** (désassemblage) et **validé** : la carte d'origine est reconstruite
  depuis les bibliothèques de blocs du programme, case par case. scroll1 2906/2906, scroll3 192/192, scroll2 737/743 ;
  les 6 écarts sont les cases animées, déjà signalées par le pilote.
- **Injection de bout en bout réussie sur MAME `sfa3ud` standard** (Lua, sans toucher aux fichiers ROM). Les tuiles
  vont dans la région gfx ; un bloc de décor neuf par côté et par plan, la liste du décor modifiée et une palette neuve
  vont dans le programme. Dans une fenêtre élargie simulée (défilement décalé de ±32 px), les deux bandes affichées
  par le jeu sont **identiques au pixel à l'aperçu de l'outil** (0 px d'écart hors sprites et HUD). La vue 4:3 est
  identique au témoin.
- **Deux contraintes découvertes** :
  1. **Palettes.** Le bloc de palettes de chaque décor est plus court que 32. La routine copie toujours 32 palettes, et
     les emplacements « non utilisés » sont en fait les premières palettes du décor suivant. Pour le décor $0C, un
     seul emplacement est vraiment libre ($7A). Sans relogement, un contenu aux couleurs nouvelles se dégrade (essai :
     RMS 56).
  2. **Bibliothèques de blocs presque pleines** pour scroll1/scroll2 (5 et 10 numéros libres dans l'arcade). Le
     numéro de bloc tient sur un octet. Toutes les bases sont des constantes `lea abs.L`, donc relogeables vers un
     bloc externe du fork (§6).

## 2. L'outil

| Fichier | Rôle |
|---|---|
| `reimport.py` | outil principal (PSD → tuiles, palettes, carte étendue, blocs, aperçus, contrôle) |
| `cpsenc.py` | format de la région `:gfx` : encodage/décodage 8/16/32 px, adresse par code, couleurs CPS2 (vérifié contre `py/cpsgfx.py` sur 1800 tuiles, aller-retour octet pour octet) |
| `blocs.py` | données de décor du programme arcade : listes, bibliothèques de blocs, super-tuiles, palettes (§5) |
| `injection_prog.py` | carte étendue → blocs de décor neufs, listes et palettes dans le programme 68000 ; vérification |
| `blocs_libres.py` | numéros de blocs libres (arcade, ro3, ro5) → `blocs_libres.json` |
| `test_synthetique.py` | copie du PSD avec remplissage miroir des bandes (`--perturber` : couleurs altérées), puis l'outil |
| `lua/essai_injection.lua`, `essai_compare.py`, `essai_rendu.py` | essai MAME et comparaisons |
| `tests.sh` | tous les tests (`MAME=1` : avec l'essai MAME) |
| `re/dis.sh ADR NB` | désassemblage 68000 de `sfa3ud_prog.bin` (unidasm) |

### Usage

```
cd <workspace>/work/decors_ws
venv/bin/python reimport/reimport.py --psd <PSD retouché> --sortie <dossier> \
    [--groupe '$0C'] [--export out/decor0C_temple_cloche] [--decor 0C] \
    [--tramage aucun|ordonne] [--force-tramage 24] [--seuil 6] \
    [--palettes-animees exact|jamais|toujours] [--retouches ignorer|reencoder] [--zone tout|448|512] \
    [--palettes-libres 7A,7D,…] [--libres debut-fin,…]
venv/bin/python reimport/injection_prog.py --sortie <dossier> [--decor 0C]        # programme arcade
```

### Étapes

1. **PSD** (psd-tools). Groupe de décor (motif `--groupe`), sous-groupe par plan (`(scroll1`/`(scroll2`/`(scroll3`).
   Tous les calques du sous-groupe sont fusionnés en mode normal, avec visibilité et opacité, sauf les calques d'aide
   du pilote (« à combler », « animations », « VRAM hors course »). L'utilisateur peut donc peindre sur des calques
   ajoutés au sous-groupe. Opaque = alpha ≥ 128.
2. **Zone d'origine.** Pour chaque case d'origine (`carte_tuiles.json`), le rendu (ROM + palette de référence) est
   comparé au PSD. Les retouches sont rapportées par case et en px (`rapport.json`, `monde_*_ecart.png` en magenta).
   Par défaut l'origine est conservée ; avec `--retouches reencoder`, la case est réencodée.
   - Cases `null` du pilote que le PSD montre pourtant : ce sont les cases « complétées par colonne composée », que
     le pilote dessine mais ne met pas dans `carte_tuiles.json`. Si le programme les contient à l'identique (lignes du
     canevas), l'outil les **reprend des données de décor** au lieu de les réencoder (décor $0C : 566/153/32 cases
     selon le plan).
3. **Découpage** sur la grille du monde (8/16/32 px, origine `origine_dans_canevas_psd`). Une case reste vide
   (code blanc du décor) si elle n'a aucun pixel opaque, nouvelle sinon. Lignes hors canevas (jamais visibles) :
   prolongation de la dernière ligne. `--zone 448|512` limite l'encodage à la bande voulue.
4. **Quantification** : pen 15 = transparent, au plus 15 couleurs par tuile.
   - Erreur de chaque tuile contre chaque palette utilisée du plan. Palette animée : seulement si la tuile y est
     exacte (défaut `exact`), ce qui permet de prolonger une lanterne qui clignote ; jamais modifiée.
   - Si l'erreur RMS dépasse `--seuil` : palettes neuves dans les emplacements libres, c'est-à-dire non utilisés, non
     animés et **propres au bloc du décor** (§5.4). Les tuiles sont regroupées par k-moyennes (histogrammes de
     couleurs), chaque palette de groupe est un k-moyennes pondéré des pixels, puis il y a réaffectation (Lloyd).
     Le nombre de palettes croît jusqu'à passer le seuil.
   - Couleurs neuves = couleurs CPS2 de **luminosité F seulement** : le jeu range les palettes de décor en 0RGB et les
     charge avec `or.l #$F000F000`.
   - Tramage ordonné (Bayer 4×4, coordonnées monde, `--force-tramage`) en option. À couleur égale, le plus petit pen.
5. **Déduplication** des 4 retournements :
   - d'abord contre **toutes** les tuiles adressables du plan dans la ROM, à pens canonisés par palette (deux pens de
     même couleur sont équivalents) ; les codes déjà utilisés par le décor sont préférés ;
   - puis entre tuiles neuves.
   - scroll1 : la moitié d'un code 8×8 dépend de la parité de colonne. Une tuile neuve paire et une impaire partagent
     un même code (gauche/droite).
6. **Allocation et encodage** dans les places libres de la région :
   - par défaut, le bourrage `$FF` de fin du quart des plans `$FF3000-$FFFFFF` pour scroll2/scroll3 (scroll3 pris par
     la fin) ;
   - pour scroll1, adressable seulement sous `$C00000`, les séries de 8 blocs de 64 o ou plus entièrement à `$FF` ;
   - moins tout code vu dans le relevé `rec2/full.rec` (cache `cache/codes_releve.json`).
   - Capacité totale : 74,8 Ko, soit environ 337 codes scroll1 / 575 scroll2 / 109 scroll3. scroll2 et scroll3
     partagent les mêmes octets.
   - `--libres` permet d'imposer d'autres places, par exemple une zone externe du fork.
7. **Sorties** :
   - `carte_etendue.json` : par plan, grille `[code, palette, flipX, flipY, prio, attr, origine o/n/r/v]`, code
     blanc, palettes neuves. Les attributs hors palette/flip (priorité) viennent de la case connue la plus proche
     sur la même ligne.
   - `table_codes.json` : code → décalage dans la région, cases servies.
   - `palettes_nouvelles.json` : mots CPS2.
   - `blocs/blk_<décalage>.bin`, `blocs.json`, `hsfa_gfx.txt` (forme `fichier@décalage` pour `HSFA_GFX`).
   - `injection.lua`, `rapport.json`.
8. **Contrôle et aperçus** :
   - recomposition de tout le monde étendu depuis une copie de la région **corrigée par les blocs** = image quantifiée
     (doit faire 0 px) ;
   - origine intacte ;
   - erreur de quantification (RMS, max, % exact, erreurs de transparence) ;
   - images `monde_<plan>_{psd,quantifie,recompose,ecart}.png`, `tuiles_neuves_<plan>.png` ;
   - `apercu_448_{gauche,droite}.png` (+ `_avant`, + 512) : 3 plans dans l'ordre CPS-B, aux deux butées de caméra,
     Y nominal.

## 3. Résultats des tests (décor $0C)

| Test | Cases nouvelles s1/s2/s3 | Réutilisées ROM s1/s2/s3 | Tuiles neuves → octets | Palettes neuves | Erreur RMS s1/s2/s3 | Recompo. |
|---|---|---|---|---|---|---|
| PSD d'origine (`test_psd_origine`) | 0/0/0 | — | 0 | — | 0 | 0 px |
| Miroir (`test_0C`) | 59/122/15 | 45/116/15 | 14+6+0 → 1,2 Ko | — | 0/0/0 (exact) | 0 px |
| Miroir + couleurs altérées (`test_0C_pal`), palettes propres seulement | 94/147/15 | 2/26/0 | 90+113+15 → 25 Ko | $7A | 56/30/15 | 0 px |
| Idem + tramage, palettes relogées supposées (`test_0C_pal_reloge`, `--palettes-libres 3C-3F,57-5F,7A,7D-7F`) | 94/147/15 | 1/1/0 | 93+140+15 → 28 Ko | 17 | 15/13/14 | 0 px |

Lecture :
- Miroir exact : scroll3 est entièrement servi par des tuiles d'origine retournées en X, sans tuile neuve.
- Remplissage aux couleurs inédites : sans relogement des palettes, l'outil retombe sur la palette existante la plus
  proche, et cela se voit. Avec 17 palettes disponibles (pas de tramage : RMS 8-11 ; tramage : 13-15), le résultat
  est correct.
- Capacité : un décor fortement retouché consomme environ 25 Ko. La place libre de la ROM arcade (75 Ko) ne suffira
  pas pour 28 décors → la région étendue du fork est nécessaire (§6).

## 4. Essai MAME de bout en bout (`MAME=1 tests.sh` ; résultats dans `essai/`)

`lua/essai_injection.lua`, `sfa3ud` standard :
1. À l'image 1, écriture des blocs de tuiles dans la région `:gfx`. Les tuiles sont décodées à la demande et ces
   codes ne sont jamais encore dessinés, donc aucun cache à invalider.
2. Écriture du correctif programme dans la région `:maincpu`. Relu par le bus : `$0191B2 = 4B08`, l'ordre des octets
   est bon.
3. Partie, Ryu, décor forcé `$FF8100 = $0C`, combat. Le décor est chargé **avec** les données corrigées.
4. Caméra aux deux butées. Captures normales, puis décalées : prise d'écriture sur `$80410C/$804110/$804114`, ±32 px
   pendant 12 images. MAME montre alors exactement la bande qu'un écran 448 afficherait de ce côté. Relevé FRM0 des
   images capturées.

| Essai | Bande gauche (MAME vs aperçu outil, hors sprites/HUD) | Bande droite | Vue 4:3 vs témoin |
|---|---|---|---|
| `inj` (miroir) | 0 / 4900 px | 0 / 5265 px | identique |
| `pal` (couleurs altérées + palette $7A) | 0 / 4900 px | 0 / 5265 px | identique |

Images :
- `essai/{temoin,inj,pal}_{1..4}.png` : 1/3 = butées, 2/4 = décalées ; dans le témoin, les bandes sont noires ;
- `essai/planche_essai.png`, `essai/bande_*_mame_vs_apercu.png`.

Correctif programme du test miroir : 1 532 octets, dont 4 blocs neufs (s1 `$4B`, s2 `$54`, s3 `$8B`/`$8F`), 4 octets
de liste et des super-tuiles neuves en fin de ROM.

## 5. Format des données de décor (SFA3 arcade `sfa3ud_prog.bin`)

Décor `d` = `$100(A5)` (mot, = décor×2 = `$FF8100`). Chargement au début du combat. Routines `$18902` (scroll1),
`$18DA4` (scroll2), `$18F56` (scroll3) : copie de la liste du décor en RAM (`-$5EB4/-$5E2E/-$5DAE(A5)`), puis
composition.

### 5.1 scroll1 (8 px, anneau de 512 px)

- **Type** : octet `[$19106 + d + 1]`. 0 = 4 blocs composés une fois ; 1/2 = anneau composé selon la caméra
  (`$189AE` : masques de colonne/rangée `$189C4`, type 2 = grille 4×2 blocs, colonne bouclée modulo 4).
- **Liste** : `$19146 + mot[$19146 + d]`, 4 ou 8 octets. Bloc de 256×256 px ; indice = colonne + 4×rangée.
- **Bloc n** : `$367494 + n×$80`. 64 mots = indices de **super-tuiles**, colonne par colonne (8×8 super-tuiles).
  Capacité 94 blocs (jusqu'aux super-tuiles).
- **Super-tuile i** : `$36A394 + i×$40`. 16 × (code, attr), mots, colonne par colonne (4×4 tuiles de 8 px). Indice
  sur 16 bits ; 2 482 places jusqu'à `$391014`, toutes prises (max `$9B1`). En revanche `$36A394 + i×$40` atteint la
  **fin libre de la ROM** (`$3C8540-$3FFFFF`, 228 Ko de `$FF`) : super-tuiles neuves à partir de `i = $1787`
  (`$3C85D4`).
- Anneau : colonne à composer = caméra + décalage, table `$18BA6` (−`$40` à gauche, `$1A0` à droite).

### 5.2 scroll2 (16 px, tilemap 1024×1024 statique)

- **Liste** `$19272 + mot[$19272 + d]` : 16 octets, 4×4 blocs de 256 px.
- **Bloc n** `$391014 + n×$300` : 256 mots code (**+ `$6C00`**), puis 256 octets attr ; entrée k = colonne k>>4,
  rangée k&15. Capacité 146 blocs.
- L'attribut tient sur **8 bits** (priorité : bit 7 seulement).

### 5.3 scroll3 (32 px, tilemap 2048×2048 statique)

- **Liste** `$194A2 + mot[…]` : 64 octets, 8×8 blocs.
- **Bloc n** `$3AC614 + n×$C0` : 64 mots code (**+ `$B00`**), puis 64 octets attr ; entrée k = colonne k>>3,
  rangée k&7.

Routines de bloc : `$18CDC` (s1), `$18F20` (s2), `$190D2` (s3). Mêmes bibliothèques pour les fins (`$26A22`, tables
`$26CC4`/`$26D48`), l'écran `$73C0` (tables PC-relatives `$7404/$7458/$74BC`) et des appels à numéro immédiat
(`$4BF4…`, `$BD06…`, `$1E260…`, `$1ED30…`, `$259F6…`).

Bornes caméra : non codées dans ces données. Elles viennent du moteur de caméra (`$290(A5)` selon les notes MAX ;
non requises ici puisque les bornes restent `$0C0-$240`).

### 5.4 Palettes de décor (`$1FC38`/`$1FC54`/`$1FC70` → copie `$1FD9C`)

- Tables scroll1 `$33C474`, scroll2 `$340954`, scroll3 `$3477B4` : **mot signé `[table + d]`** → bloc de palettes
  0RGB (32 o par palette), copié vers `$90C400/$90C800/$90CC00` avec `or.l #$F000F000`.
- La copie prend toujours **32 palettes**, mais le bloc d'un décor est souvent plus court. Pour $0C : scroll1 28
  ($20-$3B), scroll2 23 ($40-$56), scroll3 29 ($60-$7C).
- Les emplacements « non utilisés » du pilote ($3C-$3F, $57-$5F, $7D-$7F) **sont les palettes du décor suivant** :
  les écrire casserait ce décor. Pour $0C, seul **$7A** est libre. `blocs.palettes_bloc()` le calcule ;
  `injection_prog.py` refuse d'écrire hors du bloc propre.
- Pas de place libre à ±32 Ko des tables : un relogement passe par la constante `movea.l #table` (§6).

### 5.5 Traductions (fork `sfa3hx`, cœur FBNeo HSFA)

Même code (traduit), données du **portage PS2** :
- octets échangés par paire : le jeu de numéros est le même ;
- codes de tuiles **locaux** : `e256`/`e312` pour SFA3, `e353`/`e525` pour Upper.

| | ro3 (SFA3) | ro5 (Upper) |
|---|---|---|
| types / listes s1 | `$18C9F0` / `$18CA30` | `$1DE220` / `$1DE270` |
| listes s2 / s3 | `$18CB5C` / `$18CD8C` | `$1DE414` / `$1DE684` |
| blocs s1 / super-tuiles | `$107670` / `$10A570` | `$131B70` / `$1356F0` |
| blocs s2 (ajout au code) | `$12F7B0` (+`$1600`) | `$165930` (+`$1C00`) |
| blocs s3 | `$14ADB0` (code local `e312`, sans ajout) | `$185730` (`e525`) |
| tables des plans des fins (pointeurs PS2, longs à moitiés échangées) | `$0948A0` / `$094930` | `$0A1A40` / `$0A1AF0` |
| sites `LEA base.L` (carte) | s1 `024EDA 025012 0250C4 0250DC`, st `024FB0 025058 0250F0`, s2 `025296`, s3 `02538A` | s1 `02E0FE 02E24A 02E2FC 02E314`, st `02E1E8 02E290 02E328`, s2 `02E4A6`, s3 `02E572` |

Images lues : `work/mame/roms_tr/sfa3ud` et `work/mame_ro5/roms_ro5/sfa3ud`, en lecture seule ; les fichiers
`sz3ud.03c…sz3.10b` sont concaténés avec les octets échangés.

## 6. Blocs libres (SFA3 et Upper) — réponse à la question de la session MAX

`blocs_libres.py` → `blocs_libres.json`. Sources des numéros utilisés : listes de tous les décors, fins (2 tables),
écran `$73C0`, appels à numéro immédiat.

| Bibliothèque | Arcade : capacité / utilisés / **libres** | ro3 | ro5 (Upper) |
|---|---|---|---|
| scroll1 (blocs) | 94 / 89 / **5** (`4B 4C 4D 56 5D`) | 94 / 76 / 18 | 119 / 98 / 21 |
| scroll2 | 146 / 136 / **10** (`54-5B 82 84`) | 146 / 131 / 15 | 170 / 149 / 21 |
| scroll3 | 256 / 151 / **105** (`8B 8F 91-9E A0-A6 A9-BF C1-CF D1-DF E1-F4 F6-FE`) | 256 / 151 / 105 | 256 / 227 / 29 |
| super-tuiles scroll1 | 2 482 / toutes (max `$9B1`) ; fin de ROM libre : ≈ 3 500 de plus | — | — |

Fiabilité :
- Les chiffres arcade sont sûrs.
- Ceux de ro3/ro5 sont **prudents**. La lecture des listes de fins y est heuristique : quelques numéros hors capacité
  (ro3 s2 `$B4/$F4` ; ro5 plusieurs) montrent des listes mal découpées. Les numéros « utilisés » sont donc surestimés
  et les libres sous-estimés, surtout pour ro5 scroll3.
- Seuls les appels directs des 3 routines sont recensés. Un écran qui calculerait un numéro autrement serait
  manqué ; aucun n'a été vu.

**Peut-on étendre ?** Oui.
- Toutes les bases sont des **constantes `lea abs.L`** :
  - arcade, bloc s1 `$18B2A $18C34 $18CCC $18CE6`, super-tuiles `$18BE6 $18C74 $18CFA`, s2 `$18F30`, s3 `$190E2`
    (adresse de l'opérande long) ;
  - traductions : sites du tableau §5.5.
- Les reloger vers une copie étendue dans un bloc externe du fork (`$A00000-$CFFFFF`, `HSFA_EXT`) donne **256
  numéros par bibliothèque**, d'abord les blocs d'origine puis les neufs. Le numéro reste un octet (`andi.l #$ff`).
- Au-delà de 256, il faut une base par décor : petit correctif de code, base = table[`$100(A5)`], ou une liste de
  blocs sur 16 bits.
- Les super-tuiles sont déjà indexées sur 16 bits (65 536 possibles).
- Palettes : reloger les 3 constantes `movea.l #table` (`$1FC3C+2`, `$1FC58+2`, `$1FC74+2`) vers une copie
  table + blocs de 32 palettes complets par décor (±32 Ko autour de la table) → tous les emplacements non utilisés
  deviennent libres.
- Pour les fins MAX, ce sont les mêmes bibliothèques ; c'est la liste de la fin (`-$5156`) qui nomme les blocs.

## 7. Plan d'injection

**A. MAME standard (fait, essai).** Il faut :
- les blocs de tuiles dans `:gfx` (`injection.lua`) ;
- le correctif des données de décor (`injection_prog.lua` / `prog_patch.json`). Pour chaque position de liste
  touchée : bloc neuf = copie du bloc courant + cases nouvelles, à un numéro libre ; la liste est modifiée en place.
  Les cases « vides » gardent le contenu du programme ; les cases déjà identiques sont sautées.

Grâce au bouclage des tilemaps, **un seul bloc neuf par côté et par plan** suffit pour le décor $0C :
- scroll2 : 1024 px, l'extension droite retombe en colonne 0 ; un bloc pour les deux côtés (position 12) ;
- scroll3 : positions 56 et 60 ;
- scroll1 : position 4 de la grille 4×2 bouclée.

`sfa3ud_prog_corrige.bin` = image complète corrigée. Remise en fichiers ROM (`sz3ud.03c…`, octets échangés) et
« shuffle » graphique inverse : non faits, inutiles pour le fork et pour Lua.

**B. Fork `sfa3hx` / cœur FBNeo HSFA (programme traduit).** Mêmes structures, aux adresses du §5.5, avec codes
**locaux**. Recommandation, la plus simple et sans prise :
1. **Tuiles** :
   - soit l'option `--libres` sur une zone de la région étendue livrée par `HSFA_GFX=…,blk@décalage`
     (`hsfa_gfx.txt`), avec ajout des codes aux tables de renumérotation `plan1/plan2/f312` (ro3) ;
   - soit, mieux, passer ro3 en **mode base** comme Upper (`hsfa_plans.py` ; registres `$804200`) et ranger les
     tuiles neuves après la mémoire de décor locale. Les codes locaux libres y sont nombreux, par exemple
     16×16 au-delà du nombre de tuiles de `e256`.

   Il faut alors un mode `--espace base` dans `cpsenc.offset` (déjà prévu : paramètre `base`) et une table « code
   local » en sortie.
2. **Blocs et listes** : reloger les bibliothèques (sites `LEA`) et les tables de listes et de palettes dans un bloc
   `HSFA_EXT` étendu, généré à partir de l'image traduite + `injection_prog.py` adapté aux adresses ro3/ro5
   (l'ajout au code vaut `$1600`/`$1C00` et non `$6C00` ; s3 sans ajout).
3. **Palettes** : relogement des 3 tables (§6) → 32 palettes par décor.

**C. Anneau scroll1 en mouvement (non testé).**
- À l'arrêt aux butées, la composition couvre les 32 px : 0 px d'écart.
- En déplacement, la marge composée mesurée par le pilote est de 24 à 56 px à droite : une colonne de 8 px peut
  manquer brièvement en 448.
- Correctif proposé (hypothèse, à valider en mouvement) : table `$18BA6`, `$FFC0` → `$FFA0` (gauche) et `$01A0` →
  `$01C0` (droite, mot `$18BB2`). La composition est directionnelle : l'anneau de 512 px tient 15 colonnes de 32 px
  visibles + 1 d'avance.

## 8. Limites et pièges

- **Palettes** :
  - n'utiliser que les emplacements propres au décor (§5.4) ;
  - luminosité F imposée ;
  - pas de palette neuve animée (les palettes animées ne sont jamais modifiées, seulement réutilisées si exactes).
- **Places libres arcade** :
  - fin du quart `$FF3000-$FFFFFF` + séries `$FF` sous `$C00000` (scroll1) ; on suppose qu'aucun autre écran ne
    s'en sert comme tuile blanche ;
  - vérifié seulement contre le relevé du décor $0C ;
  - pour la production : région étendue du fork.
- **Blocs** :
  - l'attribut est sur 8 bits dans les blocs scroll2/3 (priorité réduite au bit 7) : l'outil le vérifie ;
  - les listes de décor peuvent être partagées : celle du $0C (scroll1, décalage `$68`) sert aussi au décor `$28`,
    qui hérite donc de l'extension. En production, utiliser une liste propre dans le bloc externe.
- **Cases animées de scroll2** : la carte du pilote garde la variante majoritaire ; l'injection ne touche pas aux
  blocs d'origine.
- **PSD** : mode de fusion normal seulement ; pas de masque de calque.
- **Contenu de référence** : `gfx/gfx_region.bin` (vidage MAME du pilote). Les codes de tuiles sont ceux de l'arcade
  (§7B pour le fork).
