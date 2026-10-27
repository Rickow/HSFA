# Hyper SFA (`ro9`) au fork `sfa3hx` : banques de sprites, décors, balayage des modes et des versions

> Rapport versé dans le dépôt le 2026-10-24 depuis `work/agent_ro9/BANQUES-ET-MODES-ro9.md` (copie anonymisée ; texte
> d'origine inchangé). Les chemins `work/…` et `<workspace>/…` désignent des dossiers de travail, hors dépôt. Rapport
> du 2026-10-07 (journal §133). Précédent : [MISE-EN-ROUTE-ro9](MISE-EN-ROUTE-ro9.md).

Agent `agent_ro9`, 2026-10-07. Travail dans `<workspace>/work/mame_ro9/` (construction, banques, ROM étendue) et
`<workspace>/work/agent_ro9/banques_modes/` (scripts, essais, planches). Aucune modification de `work/mame/roms_tr`,
de `work/mame_ro5/*`, du fork (pas de recompilation), de `translate.py` / `extra_regs.py`, ni de PCSX2. Aucun commit.
Au plus 2 MAME à la fois, tous en `nice -n 19`, chacun avec son `-nvram_directory`.

## 0. En bref

- **Hyper est monté au fork** :
  - ROM programme reconstruite avec le traducteur actuel ;
  - banques de sprites d'Hyper : communs `e545`, persos SFA1 208-220, SFA2 229-248 et Upper 355-386, table perso → banque
    `0x5AF1B0` × 128 ;
  - ROM graphique étendue = celle d'Upper **reprise telle quelle en tête** (mêmes codes `$40000-$4DAAA`), complétée
    par 11 927 tuiles propres à Hyper ;
  - décor `e546` et plan 32×32 `e548` rangés tels quels.
- **Résultat : les graphismes sont lisibles** : titre, menu des modes, sélection perso × version (portraits, colonnes
  ALPHA / ALPHA2 / ALPHA2G / ALPHA3, MANUAL/AUTO, modes NORMAL/MAZI/SAIKYO/CLASSIC et ism), écran VS, combats,
  barres de vie, jauges.
- **Balayage de 113 ids `$102`** en TRAINING : 0 exception, 113 combats.
  - Toutes les entrées **sélectionnables** de la grille s'affichent proprement : ZERO 13/13, ZERO 2 18/18 (+ Chun-Li
    `$52`, Shin Akuma `$54`, Evil Ryu `$57`, Sakura `$5D`, EX Zangief / Dhalsim `$55/$56`), ALPHA 31/31 (EX compris),
    ZERO 3 36/38.
  - **Illisibles** : 8 ids (`$12`, `$14`, `$58-$5C`, `$5E`). Ce sont des entrées « par défaut » : leurs tables par
    `$102` reprennent les données de Ryu ZERO 3, mais leur banque est une autre. Aucune n'est dans la grille de
    sélection : ce n'est pas un défaut du banc (§3.2).
- **Défaut corrigé (décors)** : le haut des décors ZERO 2 et ZERO 3 était un aplat gris ou bleu.
  - Cause : les tuiles 32×32 vides (`e548`, entrée 0) étaient rangées en pen 0, opaque.
  - Correction : rangées en pen 15, transparent (`hsfa_plans.py`, §4).
- **Modes** :
  - le menu affiche VERSUS, TRAINING, OPTION, EXIT (curseur `$FF4201` : 1 → 4 → 5 → 6 → 1) ;
  - les entrées 0, 2 et 3 (ARCADE, SURVIVAL, DRAMATIC) mènent bien à VERSUS (variable de mode `$FF80A9` = 3) ;
  - l'entrée 0 n'est pas un simple alias (§2) ;
  - VERSUS à deux joueurs fonctionne.

## 1. Ce qui est monté

### 1.1 Identification des fichiers graphiques d'Hyper

Je les ai lus dans le **descripteur des fichiers graphiques** `[[0x1DC040]]` (§82/§85 du HANDOFF) du vidage EE
d'Hyper `<workspace>/ee_hyper.bin`. J'ai d'abord vérifié que ce vidage contient bien le code de `ro9` :
982 016 mots sur 982 016 identiques.

| entrée | emplacement | type | fichier | destination PS2 | homologue SFA3 / Upper |
|---|---|---|---|---|---|
| 0 | 0 (communs) | 3 | **e545** (conteneur, 13 296 tuiles 16×16) | `0xD0B800` | e254 / e351 |
| 1 | 1 (décor, MWo3) | 2 | **e546** (2,98 Mo décompressés : 93 184 8×8 / 23 296 16×16) | `0xDB4000` | e256 / e353 |
| 5 | 5 (32×32) | 3 | **e548** (896 tuiles 32×32) | `0x11CB000` | e312 / e525 |
| 8 | — | 1 | e313 | | e313 |
| 10 | fichier fixe | 2 | **e547** (frames, `$C84000`) | `0xC84000` | e289 / e390 |

Les 3 « emplacements perso » (2, 3, 6, 7) sont remplis par le chargeur natif `0x22B00`.

Désassemblage (`agent_ro9/outils/dismips.py ro9 0x22b00 0x22dc0`) :
- banque = `0x5AF1B0[idx]` (u16), chargée par `0x155080` dans l'emplacement `0x5AF3B0[j]` ;
- `idx` = native `0x2142B0`(j) = `0x5AF420[$102]`. C'est l'identité, sauf pour les ids hors grille (EX → id de
  base ; `$12` → `$04`, `$14` → `$06`), avec un retour à `$12` / `$14` si l'octet `$132` du joueur est négatif ;
- **la banque obtenue est toujours égale à `0x5AF1B0[$102]`**. La table `carte.txt` indexée par `$102` (ce que fait
  `banc_sprites.lua`) est donc juste ;
- les fichiers **314-344** (`0x5AF2B0`, chargés par `0x154D20` en `0x1BC8000 + j×0x60000`) sont des conteneurs
  `MOMO`, pas des banques graphiques (probablement des voix). Ils ne sont pas nécessaires à l'affichage.

### 1.2 Fichiers produits (`<workspace>/work/mame_ro9/`)

| fichier | contenu |
|---|---|
| `roms_ro9/sfa3ud/` | ROM programme reconstruite avec le traducteur **actuel** (md5 `sz3ud.03c` = `eecc1770c4499e8eb7f2fd7bdeae9ab7`), journal `build_ro9.log` : 0 non résolu, 114 écritures tombées |
| `ext_940000.bin`, `ext_c84000.bin`, `ext_liste.txt` | blocs externes servis par `banc_mem.lua` (liste `ext_liste.txt`) |
| `ancien_20261004/` | sauvegarde de la construction du 4 octobre |
| `banques/` | tables contre la ROM SFA3 (MAME stock) : 69 banques + `f312.bin` (e548) + `plan1/plan2.bin`, `carte.txt` (128 lignes `perso`, 0 `anim`) |
| `banques_hx/` | tables étendues (fork) |
| `hsfa_gfx.bin` | ROM étendue, 8,29 Mo, 67 906 tuiles (codes `$40000-$5094F` ; préfixe = `mame_ro5/hsfa_gfx.bin` octet pour octet, 55 979 tuiles) |
| `hsfa_gfx_base_ro5.bin` | copie figée de `mame_ro5/hsfa_gfx.bin` (md5 `0dd63024…`) qui a servi de préfixe |
| `hsfa_plans.bin` | décor e546 en 8×8 (`$3000000`) et 16×16 (`$3400000`), 32×32 e548 (`$3A00000`), tuiles vides en pen 15 ; `hsfa_plans_v1.bin` = version d'avant la correction |
| `roms_fork/sfa3hx` → `../roms_ro9/sfa3ud` | rompath du fork |

Couverture des banques dans la ROM SFA3 (`banques.py`) :

| banques | tuiles trouvées dans SFA3 |
|---|---|
| SFA1 208-220 | 50 à 95 % (e216 Birdie ZERO : 50 %) |
| SFA2 229-248 | 65 à 99 % |
| Upper 355-386 | comme pour Upper (Guile, Fei-Long, Dee Jay, T.Hawk : < 2 %) |
| communs e545 | 92,7 % |

Les tuiles manquantes sont passées dans la ROM étendue :
- SFA1 : 7 879 ;
- SFA2 : 10 945, avant dédoublonnage (e232-e235 recopient e211-e214) ;
- e545 : 964 ;
- les tuiles d'Upper étaient déjà toutes dans le préfixe.

`hsfa_gfx.bin` tient sous `$3000000` (8,3 Mo < 16 Mo). `hsfa_plans.bin` reste donc en `$3000000`, avec les mêmes
bases qu'Upper (`300,340,3a0`).

### 1.3 Construction et lancement (commandes exactes)

Construction complète (reproductible) : `<workspace>/work/agent_ro9/banques_modes/construire.sh`. Elle enchaîne :
`mame_test.py` → `banques.py tout / 548 / plans` → `hsfa_gfx.py` (avec `HSFA_GFX_BASE`) → `hsfa_plans.py` → lien
`roms_fork`.

Lancement au fork (modèle d'Upper) :

```
cd <workspace>/work/mame && BANC_COMMUN=545 HSFA_PLANS=300,340,3a0 \
 HSFA_GFX=<workspace>/work/mame_ro9/hsfa_gfx.bin,<workspace>/work/mame_ro9/hsfa_plans.bin@3000000 \
 BANC_BANQUES=<workspace>/work/mame_ro9/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_DIR=<workspace>/work/mame_ro9/ \
 nice -n 19 <workspace>/mame-fork/mame/cps2f sfa3hx -rompath <workspace>/work/mame_ro9/roms_fork \
 -nvram_directory <ton dossier> -video none -sound none -nothrottle -skip_gameinfo -autoboot_script <script>.lua
```

Différences avec Upper :
- `BANC_COMMUN=545` ;
- pas de `BANC_GFX_INTRO` : `$C0BC` n'est jamais écrit dans ro9, et l'emplacement 4 n'est jamais utilisé (0 objet
  dans tous les essais) ;
- les blocs `$940000` et `$C84000` sont servis par `banc_mem.lua` via `ext_liste.txt`. Le fork ne les sert pas
  (`HSFA_EXT` : bases fixes seulement), mais ce n'est pas nécessaire.

Scénario d'essai : `banques_modes/lua/hyper.lua`, lancé par `banques_modes/lance.sh <nom>`. Variables :
- `INPUTS` (format `diag.py`) ;
- `FORCE102` / `FORCE102J2` et `FORCE_DE` / `FORCE_A` : imposent `$102` et `$116/$117` (tables `0x5C5300` /
  `0x5C2490`, décodage de `0x321BA0`) après la validation ;
- `MODE` / `MODE_ADR` (curseur du menu, défaut `FF4201`) ;
- captures : `SNAPS` (images), `SNAPVS` (après l'entrée sur l'écran VS), `SNAPC` (après le début du combat),
  `FINC` (fin n images après le combat) ;
- `WATCH` (octets ajoutés au journal) ;
- statistiques par emplacement (`OBJETS` / `RETIRES`, `RETDET`).

Le combat se détecte par A5+4 = 4, A5+8 = 6 et l'état J1/J2 = 2 : dans Hyper, A5+0 reste à 2, ce n'est pas la
phase 6 de `tournee.lua`.

Balayage : `banques_modes/balayage.sh f <ids…>`, avec 2 MAME à la fois.

## 2. Modes (menu, VERSUS, TRAINING, vestiges)

Planches `planches/menu_modes.png`, `planches/modes_0_1_3.png`, `planches/versus_2j.png`.

**Menu**
- Le curseur est en `$FF4201`. Bas : 1 VERSUS → 4 TRAINING → 5 OPTION → 6 EXIT → 1. Libellés justes.
- Comme constaté par l'agent du 4 octobre, il n'y a pas d'attraction : le titre attend Start.

**TRAINING (4)**
- Sélection J1 (perso → version ALPHA / ALPHA2 / ALPHA2G / ALPHA3 → MANUAL/AUTO), puis choix du mannequin, VS,
  combat sur un décor dont dépend la version.
- Juste.

**VERSUS (1) à 2 joueurs**
- Séquence : pièces 1 et 2, Start J1, B1 ; Start J2 à l'entrée du mode, ce qui fait tourner le curseur aléatoire
  comme dans Upper ; appuis J1 / J2 sur `:IN0`.
- Ryu ALPHA contre Cody (ZERO 3, choix de mode NORMAL/MAZI/SAIKYO/CLASSIC et d'ism affichés), décor de la Grande
  Muraille, chrono 99.
- Lisible, aucune exception.

**Entrées 0 / 2 / 3** (ARCADE / SURVIVAL / DRAMATIC), forcées par `MODE=n` (le menu ne les atteint pas) :
- toutes posent `$FF80A9 = 3` (versus) et ouvrent la même sélection que VERSUS : **les lanceurs renvoient bien à
  VERSUS** ;
- **entrées 2 et 3** : déroulé identique à l'entrée 1 (le J2 attend un 2ᵉ joueur) ;
- **entrée 0 (ARCADE)** : différence. Le J2 est choisi **automatiquement** environ 700 images après le choix de J1,
  puis combat avec chrono 99. La valeur restante du curseur (`$C201` = 0) est donc encore lue par l'écran de
  sélection (vestige ARCADE : CPU ou minuterie).
  - Sans conséquence en jeu normal : l'entrée 0 n'est pas atteignable au menu.

## 3. Balayage perso × version

Méthode :
- TRAINING ; J1 choisi normalement (Ryu ALPHA), puis `$102`, `$116`, `$117` imposés de l'image 910 à 2000. Le jeu
  ne réécrit `$102` qu'à la validation ; `$D3` est recopié de `$117` à l'initialisation du combat ;
- pour les ids ZERO 3, l'écran de mode et d'ism apparaît bien ;
- J2 = Ken ALPHA (`$31`, banque e209) choisi normalement ;
- captures à l'écran VS + 100 images et au combat + 100 / 250 / 400 / 550 images ;
- 113 ids : `$00-$25`, `$30-$3C`, `$40-$5E`, `$60-$7E` ; journaux `banques_modes/essais/f_<id>.log`.

Contrôle :
- séquences naturelles (sans forçage) de l'agent du 4 octobre (`nat_v1..v3`, planche
  `planches/naturel_versions.png`) : même rendu que les ids forcés correspondants ;
- `$102 = $41` (ZERO 2 Ken), `$63`, `$06` : mêmes valeurs qu'au 4 octobre.

Résultat global :
- **0 exception, 113/113 combats** ;
- en combat, **aucune tuile retirée dans les emplacements 1 à 7**. Les seules tuiles « retirées » sont dans
  l'emplacement 0, et ce sont des objets nuls (code 0, X = Y = 0, attributs 0 : `RETDET`) ;
- planches : `planches/{ZERO3,ZERO,ZERO2,ALPHA}_{c250,c400}.png` et `planches/VS_echantillon.png`.

### 3.1 Juste (lisible, forme et animation correctes)

| famille | ids | banques | résultat |
|---|---|---|---|
| ZERO (SFA1) | `$30-$3C` (13) | e208-e220 | tous lisibles (Ryu, Ken, Akuma, Charlie, Chun-Li, Adon, Sodom, Guy, Birdie, Rose, Bison, Sagat, Dan) |
| ZERO 2 | `$40-$51`, `$52` (Chun-Li), `$53`, `$54` (Shin Akuma), `$55/$56` (EX Zangief / Dhalsim), `$57` (Evil Ryu), `$5D` (Sakura) | e229-e248 | tous lisibles |
| ALPHA (ZERO 2 ALPHA) | `$60-$7E`, dont les 7 EX `$75-$7C` et Cammy `$7E` | e229-e248 | tous lisibles |
| ZERO 3 (Upper) | `$00-$11`, `$13`, `$15-$25` (dont Guile, Fei-Long, Dee Jay, T.Hawk, Shin Akuma, EX Balrog `$25`) | e355-e386 | tous lisibles |

Écrans associés lisibles :
- écran VS : grands portraits, plaques « ALPHA / ALPHA2 / A-ISM » ;
- HUD par version : jauges ZERO / ZERO 2 / ZERO 3, « ALPHA2 » pour les EX, MAX et ism ;
- annonce ROUND / FIGHT.

### 3.2 Faux : 8 ids illisibles, tous hors grille

| id | banque | rendu |
|---|---|---|
| `$12` Chun-Li (variante), `$14` Sodom (variante) | e359, e361 | sprite en morceaux |
| `$58-$5C` Bison, Sagat, Ken, Ryu, Chun-Li **EX en ZERO 2** | e239, e240, e230, e229, e247 | sprite en morceaux |
| `$5E` Cammy ZERO 2 | e248 | sprite en morceaux |

**Pourquoi.** Dans les tables par `$102` de géométrie et d'animation (`0x6A6BD4` / `0x6A6DD4` / `0x6A6FD4`), ces ids
portent l'entrée **par défaut** `0x6AF9CC` / `0x6AF770` / `0x6AF6E0`, celle de Ryu ZERO 3 (`$00`, données
d'Upper). On y retrouve aussi `$17`, `$26-$2F`, `$3F`, `$5F` et `$7F`.

Leurs frames sont donc celles de Ryu ZERO 3 (codes locaux de la banque e355), dessinées avec une autre banque, d'où
un dessin en morceaux.

Preuve croisée (`planches/diag_ex.png`) :
- `$5B` avec les drapeaux non EX (`$117 = $22`) reste en morceaux ;
- `$40` avec le bit EX (`$117 = $2A`) reste propre ;
- c'est donc la **donnée par `$102`** qui est en cause, pas le chemin de code EX ;
- `$17` (Evil Ryu) a la même entrée par défaut mais la banque de Ryu (e355) : il s'affiche bien.

**Conséquence.**
- Aucun de ces ids n'est dans la grille `0x5C5380`. Les EX n'existent qu'en ALPHA (`$75-$7C`, tous lisibles), plus
  Zangief et Dhalsim en ZERO 2.
- `$12` / `$14` sont des variantes internes : le chargeur les produit seulement si l'octet `$132` est négatif.
- **Pas de défaut du banc ni du traducteur** pour ces cas, sauf si l'on trouve sur PS2 une façon de les choisir.
- Comment les EX ALPHA sont choisis sur PS2 reste **inconnu** : ils ne sont pas dans la grille.

### 3.3 Points à vérifier (non tranchés faute de référence PS2)

**Couleurs.** En ZERO 3, toutes les persos ont une variante de couleur qui n'est pas celle par défaut : Ryu en gi
gris, Akuma en sarcelle, Juli et Juni toutes deux en vert sombre, Ken (J2) en violet contre Sodom ZERO 3 (`$06`).
- Même résultat en sélection naturelle (`nat_v3` : Ryu gris).
- La couleur dépend du bouton ou de l'ism. Le profil `palettes=None` n'agit pas sur ces palettes.
- Les couleurs sont cohérentes, pas aléatoires : à comparer avec un état PCSX2 d'Hyper en combat ZERO 3.

**Annonce FIGHT.** En fin d'annonce, pendant 1 à 5 images, un rectangle noir puis un trait vertical
(`planches/annonce_fight.png`) : c'est la fermeture du bandeau, code commun à SFA3 et à Upper. Probablement normal.
À comparer.

**Décors.** Les décors sont lisibles après la correction du §4 (`planches/decors_vide15.png`).
- Décor selon la version de J1 dans ces essais : Grande Muraille (ZERO), chute d'eau (ZERO 2 / ALPHA), décor
  enneigé et ciel d'orage (ZERO 3).
- Ce sont 3 des 4 décors d'Hyper ; le 4ᵉ n'a pas été vu.

**Joueurs 3 et 4** (emplacements 6 et 7) : non exercés, Hyper n'expose pas de mode à 3 ou 4.

## 4. Modifications des scripts partagés (`<workspace>/scripts/untranspile/`)

Toutes sont compatibles : ro3 et ro5 se comportent comme avant (vérifié à l'import ; les sorties par défaut sont
inchangées).

1. **`banques.py`** : ajout de l'entrée `'ro9'` dans `MOD` (`out=work/mame_ro9/banques`, `perso=0x5AF1B0`,
   `n=0x80`, `commun=545`, `decor=546`, `n_site=0`, `b32=548`). Rien d'autre.
2. **`hsfa_gfx.py`** :
   - **`HSFA_GFX_BASE=<fichier>`** (optionnelle) : une ROM étendue existante est reprise **en tête**. Ses tuiles
     sont décodées pour le dédoublonnage et gardent leurs codes ; seules les tuiles absentes sont ajoutées après.
     Le décodage est contrôlé par réencodage (assertion) ;
   - le nouveau code vaut `EXT0 + len(blob)//128`, ce qui est identique à `EXT0 + len(neuf)` sans
     `HSFA_GFX_BASE` ;
   - avertissement si la ROM dépasse 16 Mo (elle chevaucherait `hsfa_plans.bin` en `$3000000`).
3. **`hsfa_plans.py`** : **`HSFA_PLANS_VIDE15`**.
   - Les tuiles 32×32 vides du conteneur (entrée 0 de la table = « toute à 15 », `anthgfx`) sont rangées en
     **pen 15** (transparent) au lieu de zéros (pen 0, opaque).
   - Défaut : `1` pour ro9, `0` pour ro3 et ro5 (sortie inchangée).
   - **À évaluer pour Upper** (`e525`) : même défaut potentiel, si un décor y affiche le code 0.

Non modifiés :
- `profils.py` : le profil ro9 existait déjà ;
- `banc_sprites.lua`, `banc_plans.lua`, `banc_mem.lua` : ils fonctionnent tels quels avec `BANC_COMMUN=545` ;
  `carte.txt` à 128 entrées est indexé par l'octet `$FF8503` ;
- `translate.py`, `extra_regs.py`, `mame_test.py`.

Piège noté : `hsfa_gfx.py` ne refait pas une table déjà remplie. Une 2ᵉ exécution sur un `banques_hx/` existant
écrit une ROM étendue tronquée. `construire.sh` efface donc `banques_hx/` avant chaque passage.

## 5. Points restants

1. **Références PS2 d'Hyper** (états PCSX2), pour trancher :
   - les couleurs ZERO 3 (variantes, Juli / Juni, Ken violet contre Sodom) ;
   - la fermeture du bandeau FIGHT ;
   - le 4ᵉ décor ;
   - la façon de choisir les EX ALPHA.
2. **Fork** (non fait, non indispensable) : servir `$940000` et `$C84000` par `HSFA_EXT`. La liste des bases fixes
   d'`init_hsfa` est à prolonger, ou elle pourrait lire `ext_liste.txt`. Aujourd'hui, les prises Lua de
   `banc_mem.lua` suffisent.
3. **Son** : non traité. Hyper n'a pas de Z80 propre dans son groupe X_DATA (e544-e552) ; le banc utilise le son de
   SFA3 (`-sound none` ici).
4. **Écritures de registre tombées** : 114 dans la construction actuelle (126 au 4 octobre), audit §107 à faire.
5. **`tournee.lua` pour Hyper** : sa détection du combat (`$FF800C = 6`) et du titre ne correspond pas aux phases
   d'Hyper (A5+0 = 2, A5+4 = 4, A5+8 = 6). `hyper.lua` sert de base pour un balayage plus long (enchaînement de
   manches, VERSUS à 2 joueurs).

## 6. Fichiers

- `banques_modes/construire.sh`, `lance.sh`, `balayage.sh` ; `lua/hyper.lua`, `lua/vidage_video.lua` ;
  `planche.py`, `planche_fam.py`, `plans_diag.py`, `tables.py` ;
- `banques_modes/essais/` :
  - balayage `f_<id>` (journal + 5 captures chacun) ;
  - `nat_v1..3`, `mode0..3`, `menu`, `vs2j`, `vid_*`, `p_*`, `d_*`, `rect_45`, `obs_training`, `t5b` ;
- `banques_modes/planches/` :
  - `ZERO3_c250.png`, `ZERO3_c400.png`, `ZERO_c250.png`, `ZERO_c400.png`, `ZERO2_c250.png`, `ZERO2_c400.png`,
    `ALPHA_c250.png`, `ALPHA_c400.png` ;
  - `VS_echantillon.png`, `menu_modes.png`, `modes_0_1_3.png`, `versus_2j.png`, `naturel_versions.png` ;
  - `decors_vide15.png`, `diag_ex.png`, `annonce_fight.png`, `obs_training.png`, `t5b.png`.
