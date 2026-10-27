# Convertisseur PSP (SFA3 MAX) → formats de l'Anthology / CPS2 — prototype (2026-10-03)

`convert_max.py` : `python3 convert_max.py [pl26 pl27 pl28 pl29]` (variables d'env : `source hsfa/env.sh && source hsfa/env_max.sh`).
Sorties dans le cache, **hors dépôt** (données dérivées du jeu) : `~/.cache/sfa3max/converti/<pl>/`
- `bank.bin` : tuiles 16×16, 4 bpp linéaire, quartet bas à gauche, **valeurs brutes CPS2** (format des conteneurs de
  l'Anthology). Case PSP `j` → bloc 2×2 aux codes locaux `b, b+1, b+16, b+17`, `b = 32·(j // 8) + 2·(j % 8)`.
- `frames.json` : frames de **type 2** (`T` = somme des tuiles, objets `(dx, dy, code local, attributs CPS2)` ;
  attributs = `0x1100` (bloc 2×2) | `0x20` miroir H | `0x40` miroir V | sous-palette).
- `scripts.json` : pas `(contrôle = durée | 0x8000 si dernier, n° de frame, mot A, mot B)` ; mots A/B lus dans la
  **table des jeux de boîtes**, repérée par sa signature (u32 `0xFFFFFFFF` puis l'entrée 0 `01 00 03 00 …`).
- `sections/sNN.bin` : sections de l'entrée PSP `[6]` (tables arcade à recopier telles quelles).

## Validation : aller-retour sur Ryu (`roundtrip_ryu.py`)
Les données PSP de Ryu passent dans le convertisseur, puis sont comparées aux vraies données de l'Anthology (ro3, e258) :
- frames : **341 / 394 identiques (87 %)** en pixels + positions + miroirs (363 ≥ 0,9) ; budget `T` cohérent 471/471 ;
- scripts : 867 pas appariés, **81 % identiques** (durée + fin 87 %, mots de collision 92 %) ; une partie des écarts vient
  de l'appariement avec les scripts d'Evil Ryu (mêmes frames, autres boîtes).

## Ingrid : fusion des moitiés (même jour)
Les scripts désignent la pose par sa **moitié haute** (rangs consécutifs) ; la moitié basse de même rang l'accompagne
(687 paires de même ancre). Le convertisseur fusionne chaque paire en **une frame de type 2** (objets du haut en
sous-palette 0 + du bas en sous-palette 1) et renumérote les scripts (`remap`) : 1 126 frames au lieu de 1 813.
Rendu depuis la sortie convertie : correct (`ingrid_fusion.png`) ; la dernière paire (rang 686) n'est pas une pose.

## Scripts rangés dans l'EBOOT (`eboot_scripts.py`, même jour)
Chaque perso a AUSSI des tables de scripts dans l'EBOOT, utilisées par son module de code (pointeurs relogés + paires
`lui/addiu`) : Ryu 12 tables, Eagle 4, Maki 5, **Yun 4 dont `0x2A9EC4` = 272 scripts**, Ingrid 5 ; le moteur commun en a
243 (3 901 scripts). Même format de pas (5 × u16). **Yun range l'essentiel de ses animations ici** (3 394 pas), d'où un
`[6]` plus maigre. Chez Eagle, Maki, Ingrid, ces tables ne contiennent presque que des scripts d'un pas : **à vérifier**
(effets d'une frame ou faux positifs). Export : `scripts_eboot.json`.

## Résultats par perso MAX
| perso | tuiles | frames | scripts (pas) | table des boîtes | pas avec collisions |
|---|---|---|---|---|---|
| Eagle `pl26` | 24 544 | 723 | 501 (1 716) | `0x3354` | 1 548 |
| Maki `pl27` | 23 360 | 727 | 699 (1 721) | `0x32F4` | 1 649 |
| Yun `pl28` | 27 360 | 870 | 504 (626) + **EBOOT 380 (3 394)** | **non trouvée** (index jusqu'à 1 202) | 0 |
| Ingrid `pl29` | 33 696 | 1 126 (fusionnées) | 401 (1 323) | `0x3050` | 1 274 |

Rendu d'Eagle **depuis la seule sortie convertie** (banque brute + frames type 2) : correct (`eagle_converti.png`).

## Limites connues
- **Yun** : scripts trouvés dans l'EBOOT ; **table des jeux de boîtes non trouvée** (sa section 7 de `[6]` ressemble à de la
  géométrie brute : les index pourraient viser directement des boîtes).
- Découpage des scripts PSP heuristique (faux pas possibles) ; champ « drapeau » des pas PSP et octet haut du mot de
  contrôle Anthology (numéro d'étape) non exploités.
- La table des boîtes n'est trouvée par signature que chez 21 persos sur 43 (entrée 0 différente chez les autres).
- Pas encore de **pointeurs** : frames et scripts sont référencés par numéro ; la mise en mémoire (adresses, fichier des
  positions façon 289, tables par perso étendues) relève de l'injection, à faire avec HSFA.

## Paquet de test pour le banc MAME d'HSFA (2026-10-03)
- `test_banc.py` → `~/.cache/sfa3max/converti/pl26/test_banc/` : banque COMPACTE (166 cases → 672 tuiles, codes ≤ 667),
  20 frames d'Eagle mises en face de 20 frames de Ryu (garde, accroupi, marches, poing faible), palettes CPS2 `0xFRGB`
  (palette CPS2 `[r]` = PSP `[r + 1]`, `[15]` = transparent).
- `rendu_test_banc.py` → `test_banc_rendu.png` : rendu depuis les fichiers du paquet seuls (contrôle : correct).
- Note pour HSFA : `work/notes/max-test-injection-eagle.md` (adresses Ryu, limites du test).
- Mesure : frames d'Eagle = 8-12 objets 2×2, celles de Ryu = 2-9 objets (blocs plus grands) ⟹ frames converties plus
  longues ; à terme, fusionner les cases voisines en blocs plus grands réduirait objets et `T` (piste d'optimisation).

## Palettes (2026-10-04) — `palettes_max.py`
- PSP [2] → module : couleur `[r]` = PSP `[r+1]`, 5→4 bits, `0x0RGB`, mot 15 = n° de palette. **Ryu : 30/30 identiques**
  au module (fichier `0x451270`).
- Table moteur : fichier `0x451230` (PS2 `0x641230`), 32 décalages u16 relatifs par ID, 0x3C0 o (30 palettes) par perso,
  groupe = ((ism+1)·2 + `$129`)·5 palettes, 5 copiées ; 6 `LEA` dans la traduction ⟹ 10e table par perso à étendre.
- Sorties `plXX/palettes_module.bin` et `palettes_cps2.bin` (banc). Ingrid = 48 palettes : schéma à étudier.
- Résultat du banc HSFA (§99) : Eagle propre en garde et en marche avec la banque et les frames converties.

## Tables d'animation par coup (2026-10-04) — `tables_anim.py`, sortie `plXX/animations.json`
- `[6]` : l'en-tête (67 u32) donne des décalages **relatifs à 0x208**. Le moteur PSP pointe `objet+0x1A0` sur `&T[3]` :
  `T[3]`=`$2B0`, `T[4]`=`$2B4`, `T[5]`=`$2B8`, `T[6]`=`$2BC` (tables u32 de numéros de pas, fin `0xFFFFFFFF`),
  `T[7]` = jeux de boîtes (12 o = mots A, B, C), `T[10]` = octets par normal/ism. Script = `[6] + 0x208 + 10 n`.
- Pas → module : contrôle = `(drapeau << 16) | durée` ; fin = bit 15 OU bit 14 (`0x4001…`).
- Ryu vs module `0x48DA78` : numéros d'animation alignés, contrôle 193/195, A/B/C 1 034/1 034 pas.
- Eagle 176, Maki 207, Ingrid 203, Yun 272 animations, toutes lisibles. Yun : gabarit EBOOT `0x2AD6DC` (4 tables + scripts dans l'EBOOT), boîtes en `[6]+0x208` (1 203 entrées).
- Corrigé au passage : `sections/sNN.bin` (décalage 0x208 manquant), table des boîtes = `T[7] + 0x208`, mot C ajouté.

## Textes (2026-10-04) — `textes_max.py`, sortie `plXX/textes.json` + `textes.txt`
- `winXX_e.pac` entrée 5 = 8 citations ; `opXX_e.pac` entrées 3/4 = bio / fiche ; `endXX_e.pac` entrée 14 = scénario + fin.
- Enregistrements 0x80 : `[total] ([position] texte 0)…` ; le module enchaîne `[position] texte 0` (positions identiques).
- Fichiers extraits (lecture seule de la copie locale de l'ISO, 7z) dans `~/.cache/sfa3max/data/textes/`.

## Graphismes pour le fork MAME d'HSFA (2026-10-04) — `gfx_fork.py`
- Sorties `~/.cache/sfa3max/fork/` : `max_gfx.bin` (58 866 tuiles neuves, format interne MAME, à concaténer après
  `hsfa_gfx.bin` d'Upper : codes `$4C340-$5A931`), `plXX_hx.bin` (local → global ; transparente → code `$0`).
- Réutilisation : ROM SFA3, puis Upper, puis autre perso MAX. Contrôle 108 960 / 108 960 tuiles identiques.
- Convention : brut 15 = transparent (tuile la plus fréquente de la ROM = FBNeo 0 = brut 15).
- Régénéré après HSFA §122 (fins d'Upper ajoutées) : Upper = 55 979 tuiles → MAX 58 817 tuiles, codes `$4DAAB-$5C06B`,
  fin à l'octet `$2E03600` (< mémoire de décor `$3000000`) ; contrôle 108 960 / 108 960.

## Sprites des écrans PSP (2026-10-04, en cours) — `ecrans.py`
- `op/select/end…_e.pac` contiennent des trios frames / tuiles / palettes au format des persos (types `0x01…`,
  `0x02…`, `0x04…`), MAIS **une case = UNE tuile 16x16** (et non 2x2) ; attributs : bit 7 miroir H, bit 6 miroir V,
  bit 5 toujours posé, **bits 0-4 = palette relative à une base** (non encore établie).
- `op26_e.pac` (Eagle) : 14 frames = bio : bandeaux, nom « EAGLE », portrait en 3 couches (buste, tête et bras,
  contours ; palettes 0/1/2 + base). Rendu géométrique correct (`op26_rendu.png`) ; couleurs : base à trouver (jeux de 3
  palettes, aplats stylisés : art de bio, pas les portraits de combat).
- `select_e.pac` : 1 200 frames, 9 809 tuiles, 1 705 palettes = portraits de sélection / VS de tous les persos
  (cible probable pour la CPS2) ; `end26_e.pac` entrées 11-13 = trio de sprites de la fin, 1-10 = images PVR.
- Côté moteur (inventaire HSFA) : portraits = SPRITES (table de 66 poses × ID, ro5 `0x484C00`, entrées {frame,
  attributs}), tuiles dans un fichier « MOMO » par perso (Upper : e340-e343), palettes par pointeurs (`0x53BDF0`).
- **Portrait de victoire** (`winXX_e.pac`, entrées de types 1/2/3 = frames / tuiles / palettes) : **case = 2x2 tuiles**
  (32x32, comme les persos ; détecté par l'index max × 4 = nombre de tuiles), palettes 16 couleurs (48), base 0 ;
  morceaux assemblés à la position `origine − (a, c & 0xFFFF)` (champs d'ancrage de l'en-tête). Eagle :
  `eagle_victoire_psp.png` (3 morceaux : corps, autre partie, yeux = calque d'animation probable).
  ⟹ même conversion CPS2 que les frames des persos (4 bpp, palettes 16 couleurs) : pas de réduction de couleurs.
- `msel_e.pac` entrées 7/8/9 : même format (types 7/8/9) — probablement les portraits de sélection : à examiner.
- Inventaire des sprites d'écrans PSP (Eagle) :
  - `winXX_e.pac` (types 1/2/3) : **grand portrait de victoire**, 16 couleurs, couleurs justes en base 0 ;
  - `rkXX.pac` : le même grand portrait (frames 0-2, 194 palettes = jeux de couleurs) + petite animation en pied avec
    ombre (frames 3-60 ; classement / World Tour ?) ;
  - `opXX_e.pac` : bio stylisée (aplats) ;
  - `select_e.pac` (commun) : interface (VS, CONTINUE, GAME OVER, décors), poses d'Ingrid (9×8), et **morceaux de
    visages** (frames 592-704, bandes 8×3 / 6×3 à superposer : visages de la grille / bandeaux) ;
  - `msel_e.pac` (types 7/8/9) : menu des modes (textes, bandes « yeux » 6×1, étiquettes de noms).

## Portraits attendus par le moteur (Upper) — `portraits_upper.py` (2026-10-04)
- Table ro5 `0x484C00` : 66 poses (u16 décalages) × 40 ID × `{u32 attributs, u32 ptr frame}` ; frames de **type 8** :
  `u16 type, u16 T, u16 n-1`, puis n × `(u16 code, u16 attributs CPS2, s16 x, s16 y)` (bandes de tuiles) ; le
  constructeur ajoute `$1600` au code ; emplacement 1 : code ROM = code + `$1600` + `$15600` (HSFA §85).
- Familles de poses (rendu de Ryu, `portraits_upper_00.png`) et source PSP de MÊME TAILLE :

| poses | taille | contenu | source PSP |
|---|---|---|---|
| 12-17, 30-31 | 320×160 | grand portrait | portrait de victoire `winXX_e.pac` |
| 0-5, 24-29 | 128×224 | portrait vertical | ? (à trouver) |
| 6-11 | 128×48 | bandeau du visage | `select_e.pac` frames 8×3 (2 calques, c = 0x10018 / 0x18) |
| 18-23 | 96×48 | petit bandeau | `select_e.pac` frames 6×3 (idem) |
| 32-64 | 96×16 | bandes d'yeux | `msel_e.pac` frames 6×1 — **inutiles** pour un nouveau perso (invalides chez Guile) |

- Reste : quelle frame / base de palette de `select_e` appartient à Eagle (suivre le code PSP de la sélection),
  source du portrait vertical, puis conversion (tuiles CPS2, frames type 8, palettes) et essai au fork.
- `portraits_max.py` : portraits des 4 persos (`plXX/portraits.bin|json|_palettes.bin`) : 320×160 (victoire,
  `winXX_e.pac`) + 128×224 (sélection, `select_e.pac` jeu 2 ; bases de palettes Eagle 1240, Maki 1264, Yun 1288,
  Ingrid 1312), coordonnées centrées d'Upper. `portraits_fork.py` : `max_portraits_gfx.bin` + `pXX_portraits_hx.bin`
  (codes $5C070…, sans dédoublonnage). `rendu_portraits.py` : contrôle depuis les paquets (`portraits_max_paquet.png`). Bandeaux 128×48 / 96×48 = recadrages
  du vertical (comme Upper), fenêtres `BANDEAUX` dans `portraits_max.py`.
  Lancer avec `source ~/hsfa/env.sh; source ~/hsfa/env_max.sh` (numpy du venv, `SFA3MAX_EBOOT`, `ANTHOLOGY_DIR`).
## Fins des persos MAX (2026-10-07, premier examen) — `fins_max.py`, sorties `~/.cache/sfa3max/converti/plXX/fin/`
- `endXX_e.pac` : entrée 0 = **carte 64 × 192 cases u32** (3 plans de 64 × 64, tuiles 16×16) ; case = drapeaux << 24 |
  GBIX << 8 | tuile, `0x1700` = vide ; drapeaux `0x80` posée, `0x10` miroir H, `0x20` miroir V, `0x40` bords (à établir).
  Entrées GBIX/PVRT = planches 256×256 de 16×16 tuiles : format 1 = ARGB1555 **linéaire**, format 5 = 4 bpp (masques,
  dégradés). **Tuiles 16 bits : 99 % à ≤ 16 couleurs** (tuiles à palette dépliées) → conversion CPS2 sans perte.
- Décors : plan 1 lignes 32-47 = grande image 384×256 (décor du perso) ; ensuite bandeaux 384×128 (24×8 cases), puis
  bandes en 4 bpp (fenêtres / dégradés, palette à trouver). Eagle et Ingrid partagent leurs bandeaux (Bouddha, anneau
  dans la forêt, crâne robot, Terre, hangar) ; Yun reprend des scènes de la fin de Ryu (Charlie en avion, salle de
  contrôle) → **une partie des tuiles existe sans doute déjà dans la ROM** (à apparier comme `gfx_fork.py`).
- Sprites animés : trio `0x1000019/0x2000019/0x4000019` au format des écrans (`ecrans.Ecran(..., ti=(11,12,13))`).
- **Script de scène (`0x20000`) = script de fin ARCADE réencodé** : retrouvé dans la ROM SFA3 (Ryu, fin `end00`,
  alignement difflib) ; écarts systématiques : en-tête de pointeurs remplacé, opcode `0x11` longueur +1 (`1108` → `1109`)
  avec un mot ajouté (`0002`/`0001`), pointeur arcade → position/paramètres dans la carte (`0000 0000 1824 0606`).
- Animations des sprites `0x20001-0x20005` : pas PSP (10 o) + attributs (12 o) = pas de 20 o du module (comme les persos).
- Côté Upper : chargeur de fin `0x4114A0`, table `0x6283C0` (index = n° de fin, `$26` → fichiers de Ryu, `$27` → `$1E`) ;
  fichier anim (sections de pas 20 o + frames type 2) + banque gfx (emplacement 4). Décors : plans de défilement.
- Reste à faire : sémantique de l'opcode `0x11` (et des autres) côté arcade, palettes des tuiles 4 bpp, appariement des
  tuiles avec la ROM, format exact attendu par Upper pour un script de fin neuf.

### Moteur de fin ARCADE (sfa3ud, 2026-10-07 ; trouvé par prise de lecture MAME sur le script de Ryu)
⚠ `hsfa/work/cps2/sfa3_prog.bin` = vue OPCODES (données brouillées) : lire les données dans la ROM `sfa3ud` (fichiers
`sz3ud.03c…sz3.10b` concaténés puis octets échangés par paire ; copie : `~/.cache/sfa3max/sfa3ud_donnees.bin`).
- **Init** `$25E10` : n° de fin = `$1C6(A5)` ; tables par fin (33 entrées) : paramètres `$26ED4` (3 mots : temps des
  événements `$1CC` → `-$5138/-$5134/-$5132`), palettes `$26BBC` (→ `-$515A`), plans `$26CC4` (→ `-$5156`), scripts
  `$26DCC` (→ `-$512E` ; Ryu `$3167BE`) ; variantes `$26C40/$26D48/$26E50` si `$90(A5)` ≠ 0.
- **Interpréteur** `$26FB8` : instruction = `[attente][opword][args]`, nb d'args = `opword & $F` (copiés en `-$5126…`),
  attente → `-$512A`. Exécution `$27220` : classe = bits 4-6 de l'opword (0 → `$27256`, 1 → `$27436`, 2/3 → `$274D6/8`) ;
  classe 0 : sous-opcode = quartet bas de l'OCTET HAUT (table `$27268`), quartet haut de l'octet haut → `-$5103`.
- Opcodes classe 0 vus : `x1` scène (args : défilement scroll1/2/3 = `XXYY` en unités de 16 px, X = octet haut, Y = octet
  bas signé ; a4 = indice de paire de registres de priorité/couches `$272DA` → `$32/$3A(A5)` ; a5-a8 → `-$50F0…`) ;
  `x6` **charge les plans** (`$273A4` → `$26A22`) : args = indices dans la table `-$5156` → listes d'octets = numéros
  de BLOCS : scroll1 4 blocs (`$18CDC`, bibliothèque `$367494`/`$36A394`), scroll2 16 blocs de 16×16 tuiles (`$18F20`,
  `$391014` + n×`$300` : 256 codes + 256 attributs, code + `$6C00`), scroll3 64 blocs de 8×8 tuiles 32 px (`$190D2`,
  `$3AC614` + n×`$C0`, code + `$B00`) ; `x9` **palettes** (`$273EC` → `$266BC`) : a1 = destination (0/2 tampons de fin,
  4 = base courante, 6 = `$90C000`), a2 = n° de jeu dans `-$515A`, a3 = 1re palette, a4 = nombre ; `x3` (1 arg, suite
  croissante : lancement d'animation ?) ; `x2/x4/x7/x8/xA/xB` à établir. Classe 3 `0034` : texte (`0010 00C0 n n`).
- PSP : même bytecode ; `0x11` porte un arg de plus ; les plans sont DÉJÀ déroulés dans la carte (entrée 0) et les
  positions de `0x11` sont celles de la carte PSP (images remballées : Ryu arcade `185C/305C/505C/005C` ↔ PSP
  `1824/0014/0034/0024`). Correspondance plans PSP ↔ scroll1/2/3 à établir (code PSP de l'opcode `0x11`).
- **Calage des scènes (2026-10-10)** : outils `mame_fin.lua` (captures + vidages VRAM, VIDAGE=1), `plans_vram.py`,
  `caler_fin.py`, `calage_arcade.py`. **scroll2** : arcade, case en haut à gauche de l'écran = (X, 49 − Y) (unités 16 px,
  plan 64×64, Y = octet bas de l'argument) ; PSP, case = (X′, 104 + Y′) dans la carte (plan scroll2 PSP = lignes 64-127) ;
  vérifié sur le cockpit (1812 ↔ 1801), la salle de contrôle (0009 ↔ 0008) et 2031 ↔ 0010. Blocs arcade : rangés par
  lignes (4×4), tuiles par colonnes dans le bloc (balayage MAME tilemap1_scan). **scroll3 : non calé** — PSP : plan C
  (lignes 128-191) en cases de 32 px lues dans les textures au pas de 16 px (draw32), surtout en 4 bpp (fonds lignes de
  vitesse / tourbillons, palette par les opcodes x9) ; le rendu du vidage $918000 sort incohérent (base de plan ou
  double tampon à revoir).
- **scroll3 des fins = effets de DÉFILEMENT PAR LIGNE** (2026-10-10) : le plan reconstruit depuis les blocs ROM
  (`$26CC4` → blocs 78/70-72/67/68/76/77/123…) est identique au vidage $918000, mais aucune fenêtre ne colle aux
  captures (score majoritaire ≤ 0,44, et le meilleur est indépendant de X) : les lignes de vitesse / tourbillons sont
  des bandes horizontales déformées ligne par ligne (cf. HSFA « défilement par ligne » F72D8). Côté PSP, d'où les bandes
  d'UNE case de 32 px en 4 bpp. ⇒ Pour les fins MAX, scroll3 = effets génériques : à rapprocher par contenu des bandes
  des fins d'arcade (même texture → mêmes blocs arcade et même argument a3), plutôt que par une formule de position.
- **Effets des fins MAX = effets d'arcade** : 100 % des cases 4 bpp du plan C des fins MAX (Eagle 280, Maki 144, Yun 144,
  Ingrid 280) existent à l'identique dans les fins PSP des persos d'arcade (surtout Ryu `end00`, puis `03`, `06`, `04`)
  ⇒ scroll3 = blocs et arguments a3 de ces fins d'arcade, rien à importer ; seules les illustrations en couleurs directes
  (scroll2 et images du plan C) sont neuves. ⚠ Le plan C contient aussi des images 16 px en couleurs directes (Eagle :
  crâne, Terre, hangar) : rôle exact du plan C (scroll1 ?) à confirmer.

### Fin d'Eagle : conversion « sur modèle » (2026-10-10)
- **Fins MAX ≈ fins d'arcade remaniées** : le plan scroll2 PSP d'Eagle est celui de Zangief (`end10`) aux mêmes places
  (Bouddha 184/190 cases, crâne 168/168, anneau 144/218 ; Terre en partie ; le hangar diffère mais n'est montré par
  aucune scène d'Eagle) ; ses fonds scroll3 sont ceux de Zangief (captures MAME `mame_fin/f10`).
- Les illustrations PSP ne sont PAS les tuiles arcade au pixel près (Bouddha introuvable dans les tuiles scroll1/2/3
  de la ROM, et 41 palettes de 16 couleurs) : on ne convertit pas les images, on **reprend les plans et palettes
  arcade de la fin modèle**.
- Scène arcade : a5-a8 = jeux de palettes chargés par la scène ($26710) ; x5 (5 args) = événement + mêmes 4 jeux.
- `convertir_fin.table_modele(fin)` : alignement script PSP ↔ ROM de la fin modèle -> {scène / x5 / x9 PSP : arcade} ;
  `convertir_avec_modele("26", 0x10)` : 99 instructions, les 8 scènes distinctes d'Eagle toutes résolues (anneau
  2010→0001, Psycho Drive 2008/0038→2009/0819, Bouddha 0001→0020/2010, crâne 0018→0809/0039, Terre 0026→202B,
  ciel rouge 0043→00F0/004E, éclair 0004→00F0/000D, vitesse 1814→00F0/282C) ; 2 x5 reprennent les palettes de la
  scène précédente. Sortie : `converti/pl26/fin/script_fin_26.s` (textes : `TEXTE_FIN_26 + k`).
- Pour la place $26 : tables de fin palettes ($26BBC) et plans ($26CC4) -> entrées de Zangief ($10) ; script -> ce
  fichier. **Reste : les acteurs** (repères x3 0x12…0x99 = acteurs d'Eagle, Guile, Bison : sprites PSP 0x1000019/
  0x2000019/0x4000019 + sections 0x20001-0x20005) et leurs palettes (x9 PSP : jeux à ajouter à la table de Zangief).
- Outils : `dictionnaire_fins.py` (dictionnaire tuile PSP -> arcade, appariement par voisinage de codes : utile pour
  repérer les réutilisations, pas pour convertir), `lance_fins.sh` (captures MAME parallèles avec vidages plans +
  palettes ; région :gfx = `hsfa/work/decors_ws/gfx/gfx_region.bin`, ⚠ PAS `cps2/sfa3_gfx_region.bin`).
- ⚠ Le diagnostic « scroll3 = défilement par ligne » plus haut reposait sur un rendu avec la mauvaise région gfx :
  à revoir (sans conséquence pour Eagle : fonds repris tels quels de Zangief).

### Acteurs des fins (2026-10-10) — `rosette_donnees.py` (table de correspondances arcade ↔ PSP)
- **Arcade** : générateur `$2750E` ; table `$275DA` (variante `$2765E` si `$90(A5)`) = par fin, décalages de groupes
  (nb = 1er décalage / 2), groupe indexé par `$1CA(A5) − 1` (posé par x5) ; enregistrements de 32 o jusqu'à un type
  ≥ $80 : +0 type (classe d'acteur $48-$50), +1 sous-type, +2 → $B, +3 → $70 (animation), +4 → $18, +5 → $9,
  +6 → $D, +7 → $76, +8/+A X/Y, +C/+E → $72/$74, +$10-$16 vitesses → $40/$44/$48/$4C, +$18 long → $78 (repère de
  début, de fin…), +$1C long → $7C ; objets du réservoir $1C2C8.
- **PSP** : mêmes enregistrements dans l'EBOOT, zone 0x2B3A38-0x2C6xxx ; table maîtresse **0x2B34B0** (42 pointeurs,
  fin $00-$29) -> petite table {[0] liste des pointeurs de groupes, [1] fin de liste, …}. Fins MAX : $26 0x2C4A38,
  $27 0x2C4FF0, $28 0x2C56D8, $29 0x2C5E44.
- Règle PSP -> arcade (`vers_arcade`) : octets 0-7 identiques sauf +4 = (v & 7) << 5 ; mots +8..+$17 petit -> gros
  boutiste ; +$18..+$1F identiques. Écarts résiduels = retouches de position PSP (Y −16, X −192…, sans règle).
  Appariement par suite de repères : 177/217 groupes d'arcade retrouvés, 1 266 enregistrements.
- **Fins MAX : uniquement des classes d'acteurs arcade** ($48/$49/$4A/$4B/$4E/$4F/$50) ; (type, sous-type) absents
  de l'arcade : Eagle 4B/52 ; Maki 4B/53, 4F/19, 49/2D ; Yun 4B/53-57, 4F/19, 49/2E ; Ingrid aucun.
- Sorties : `converti/plXX/fin/acteurs_fin_XX.s` (FINXX_ACTEURS : table de décalages + groupes, fin $FFFF ; Eagle 11
  groupes / 67 acteurs, Maki 3/35, Yun 3/37, Ingrid 5/46). Le n° d'animation (+3) reste celui de la PSP : la table
  d'animations de la fin (fichier anim) sera construite dans le même ordre.
- Reste : animations des acteurs ($70 -> pas, frames ; PSP 0x20002-0x20005 + trio 0x1000019/0x2000019/0x4000019),
  palettes des sprites, sous-types absents.
- **Classes d'acteurs** (aiguillage arcade `$3333C`, longs par type d'objet) : $48 → $A5AB8, $49 → $A6284,
  $4A → $A7464, $4B → $A7562, $4C → $AA90C, $4D → $AAA14, $4E → $AACAC, $4F → $AAE04, $50 → $AC15E.
  Classe $4B : animation commune via $AA630 ($70), puis comportement par sous-type ($3) : table `$A75D4` = 78
  sous-types (0-$4D). Dans Upper, la variable de repère est **$1CA(A5)** (arcade $1C8) et la table d'animations de
  $48/sous-type passe de $81522 (ROM) à $CFB6A0 (données du module, PS2 0x960180) : animations GLOBALES (pas dans
  le fichier de fin).
- **PSP, classe $4B** : table des sous-types en **EBOOT 0x2B2358** (trouvée par corrélation des tailles de gestionnaires
  avec l'arcade, ρ = 0,90) : 88 sous-types (0-$57) ; $4E-$51 = ajouts (Upper ?) ; **$52-$57 = comportements ajoutés
  pour les fins MAX** : $52 0x1D3844, $53 0x1D3BB8, $54 0x1D3DFC, $55 0x1D4008, $56 0x1D4370, $57 0x1D48AC (code C ->
  à traduire en 68K avec traduire.py, contexte « acteur de fin », objet du réservoir $1C2C8). Même travail à faire
  pour 4F/19 (Maki, Yun) et 49/2D-2E (Maki, Yun).
- **Comportements ajoutés (2026-10-10)** : tables PSP des sous-types : $4B 0x2B2358 (88), $4F 0x2B2A00 (+$19 → 0x1D6588),
  $49 0x2B2158 (49 ; $2D → 0x1C9704, $2E → 0x1C970C). Traduits (contexte acteur de traduire.py : CTX["acteur"],
  ACTEUR, FIN_GLOB, api_acteurs.json appris par rosette_code/appris_acteurs.py) dans `rosette_code/acteurs_fins_max.s`
  (93 fonctions ; 45 lignes « ⚠ À COMPLÉTER » : champs de la structure de fin PSP 0x87FCB0 au-delà de +$10, couches
  0xA46Axx, tables +0x12C). **assembler.sh : 6 erreurs** restantes : psp_1d80b0, psp_1d7f18 (au-delà de la profondeur
  de traduction) et TABD_2b2b34/2c34/2c60/2c68 (tables de données à émettre comme donnees_max.s).
- **acteurs_fins.py (2026-10-10, suite)** : générateur reproductible (fermeture des appels, étiquettes `acteur_X` /
  `AL_` pour ne pas heurter les ébauches des persos, tables -> `donnees_acteurs_fins.s`) ; **assembler.sh : 0 erreur**.
  Ajouts au contexte acteur de traduire.py : couches PSP 0xA46A20+0x98k (+8 X, +$C Y, 16.16) = accumulateurs arcade
  $210/$214, $290/$294, $310/$314 ; registres de rendu PSP 0x80F8D0/0x80F970/0x80FA10 (+$10/+$14) = ombres en mots
  $22-$2C (partie entière, réécriture par acteurs_fins.post) ; état de fin +$70/$72/$74 et +$90/$92/$94 = -$50FA/
  -$50F8/-$50F6, +$6B = -$5107 (scène demandée par un acteur) ; champs d'acteur 0x20/0x22 -> $20/$22 (jamais employés
  en arcade) ; sous-type des acteurs ($48-$50) BRUT. Bouche-trous $49 $2B/$2C = PSP 0x1C96B4 (table PSP).
  **Reste 25 lignes** : pointeurs de l'état de fin PSP +$110/+$114/+$118/+$12C (tables propres à chaque fin, entrées
  de la petite table d'acteurs) -> à rendre par une table 68K indexée par $1C6 ; +$A0 ; globales 0xA4CED0/4,
  0xA3E7C9 (compteur de réservoir), 0x39CA3E.
- **Animations des acteurs (2026-10-10)** : $AA630 -> banque = table de longs `$AA644`[$7F] (n° de perso : la banque d'un
  perso EST sa table d'animations de combat, Ryu $146218, pas de 20 o) puis `$1B6E0` (D0 = $70). Fins MAX : banques
  38-41 = persos MAX (numérotation PSP = ordre de animations.json, à condition que l'homologue Upper de $AA644 reçoive
  $26-$29 -> tables maîtresses des persos MAX, côté HSFA). Persos d'arcade : la PSP a renuméroté leurs animations ;
  `rosette_donnees.table_anims()` (vote sur les acteurs appariés) traduit 124 acteurs MAX ; 30 sans correspondance
  (Guile/Fei-Long banques 32/33, à apprendre sur les fins d'Upper ; quelques isolés), marqués ⚠ dans acteurs_fin_XX.s.
- État de fin PSP : +$10C/+$120/+$124/+$128/+$12C = petite table d'acteurs [0]-[4] ; +$110/+$114/+$118 = tables de
  pas construites au chargement depuis les sections 0x20001-0x20005 (pas de 10 o / 8 o) : les 25 lignes « ⚠ À
  COMPLÉTER » de acteurs_fins_max.s lisent ces animations PROPRES À LA FIN -> à traiter avec leur conversion.
