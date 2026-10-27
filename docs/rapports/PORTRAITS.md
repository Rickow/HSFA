# Glitch des grands portraits avant les combats (agent_portraits, 2026-10-11)

Retour console (cœur FBNeo HSFA) : « un léger glitch sur les portraits lors du déchargement du sprite, lors des gros
portraits avant les combats ».

Tout est dans `work/agent_portraits/`. Les fichiers partagés n'ont été que lus : traducteur, `work/mame*`, fork MAME,
cœur FBNeo de `agent_fbneo_rejeu`. Les ROM, banques, scripts Lua et l'arbre FBNeo ont été copiés ici. MAME a tourné en
`nice -n 19`, avec des dossiers nvram/cfg temporaires, sans `-state` et sans `pkill`. Aucun commit.

## 0. En bref

- **Jeu touché : Upper (ro5) seulement.** L'écran touché est le **face-à-face avec dialogue** : le grand portrait
  propre au portage PS2 (fichiers 419-454, un par perso), avant le 1er combat d'une partie. Le défaut apparaît
  quand le portrait s'efface. Il dure **5 images de tuiles parasites**, celles de l'écran VS (fichier 457) dessinées
  sous la forme du portrait. Il est reproduit à l'identique dans le banc MAME (images 2379-2383) et dans le cœur FBNeo
  (images 2722-2726).
- SFA3 (ro3) : rien. Le pointeur de l'emplacement 4 ne change pas pendant le face-à-face. Hyper (ro9) : rien,
  l'emplacement 4 n'est jamais utilisé et l'écran VS est propre.
- **Cause : le banc et le cœur, pas la traduction.** Sur la PS2, le chargeur natif ne fait que **mettre en file** la
  lecture du fichier. Les tuiles de l'emplacement 4 restent donc celles de l'ancien fichier pendant quelques images.
  Le jeu compte là-dessus : il laisse le portrait affiché 5 images après avoir demandé le fichier de l'écran VS,
  exactement comme l'arcade, où le portrait reste 5 images après le changement d'état. Le banc et le cœur, eux,
  changeaient la table de l'emplacement 4 **à la liste suivante**.
- **Correctif : chargement différé de l'emplacement 4**, dans le banc Lua et dans le cœur FBNeo. Le nouveau fichier
  attend qu'aucune liste de l'image n'ait plus d'objet de l'emplacement 4 (10 images au plus). Interrupteurs
  `BANC_LAT4=0` / `HSFA_LAT4=0` pour revenir à l'ancien comportement. Le traducteur n'est pas modifié (§3).
- Validation : le glitch disparaît (banc et FBNeo). Sur 4 tournées du banc (178 000 images, dont 3 fins), il n'y a
  **aucune autre différence** que la liste fautive de chaque sortie de face-à-face. Les captures FBNeo sont identiques
  au pixel sur 3 × 20 000 images (Upper, attraction d'Upper, SFA3). Avec `HSFA_LAT4=0`, le résultat est identique au
  pixel à l'ancien cœur.

Planche principale : `png/COMPARAISON_sortie_face_a_face.png` (arcade / banc avant / banc après / FBNeo avant /
FBNeo après).

## 1. Captures image par image

Outils : `lance.sh arc|ro3|ro5 NOM NF` (tournée Arcade, `lua/portraits.lua` : journal par image de `$FF8000-$FF800E`
et de `$FF40BC`, captures dans `[SNAP_A, SNAP_B]`), `fb.sh NOM COEUR [ZIP]` (hsfa_run, entrées de la tournée),
`outils/planche.py` / `planche_fb.py` (planches).

Déroulé, avec Ryu contre CPU (adresses 68K) :

| | arcade `sfa3ud` | Upper (banc) | SFA3 traduit |
|---|---|---|---|
| face-à-face + dialogue (`$FF8004=4`, `$FF8008=2`, `$FF800C=0`) | 2131-2281 | 2203-2377 | 2155-2305 |
| sortie (`$FF800C` 0 → 2) | 2282 | 2378 | 2306 |
| portrait encore affiché | 2282-2286 | 2378-2383 | 2306-2309 |
| écran VS (`$FF8008=4`) | 2348 | 2445 | 2372 |

- **Arcade** (`png/arc_sortie_face.png`) : à 2282, le cadre de texte se vide. Le portrait reste seul jusqu'à 2286,
  puis la carte apparaît à 2287.
- **Upper avant** (`png/ro5_sortie_face.png`) : 2378 = cadre vide, comme l'arcade. De **2379 à 2383**, on voit un
  amas de tuiles d'un autre fichier, à la place et aux couleurs du portrait. La carte apparaît à 2384. La 2e partie de
  la tournée de Blanka (après sa fin, image 58117, `png/ro5_rival_blanka_lat0.png`) montre le même défaut.
- **FBNeo avant** (`png/fb_sortie_face_avant.png`) : même chose, images 2722-2726. C'est le retour de l'utilisateur.
- Entrées du face-à-face et de l'écran VS, sorties de l'écran VS (logo vert) : identiques à l'arcade, sans défaut
  (`ro5_entree_face.png`, `ro5_entree_vs.png`, `ro5_sortie_vs.png`, `arc_*`).
- Ce n'est **pas** une image à moitié remplacée, ni la palette, ni le retard d'une image de la CPS2. Les objets sont
  ceux du portrait (mêmes positions, même palette). Seule la **table de l'emplacement 4** est déjà celle du fichier 457.

## 2. Cause

### 2.1 Ce que fait le jeu (traduit = PS2)

- La sortie du dialogue est en MIPS `0x25D6B4` (image `$5710E`) :
  `TST.B $C201(A5) ; BNE ; JSR chargeur(index 2)`. Le site `0x25d6c0` vaut index 2 = fichier 457 (`assets_natifs.py`,
  `SITES`). Viennent ensuite `0x25D6E0` : `ADDQ.W #2,$C(A5)` (sous-état 2) et la remise à zéro de `$10/$14`.
  L'ordre est donc : demande du fichier de l'écran VS, **puis** sous-état 2, pendant lequel le portrait reste listé.
- Le chargeur natif `0x4112D0` appelle le moteur `0x155080(gfx, ctx+0x48, 1)`, puis `0x154C90(0, anim, …)`, puis
  `$C0BC(A5) = ctx+0x9C`. Avec l'argument 1, `0x155080` saute à **`0x154C10`**, qui **range une requête**
  `{1, fichier, tampon}` dans une file circulaire de 128 entrées (`0x1A2440`, index `0x1A2458`), et c'est tout.
  `0x154C90` fait de même pour l'animation. Désassemblage : `outils/dis_elf.py` sur `SLUS_213.17`.
  **Sur la PS2, le fichier graphique arrive donc plus tard** (lecture du disque puis décompression). L'emplacement 4
  garde l'ancien portrait pendant ce temps.
- Mesure (`mesures/lat4_ro5*.txt`) : dans l'image de l'appel, le jeu construit **une** liste avec **51 objets de
  l'emplacement 4** (le portrait). Les 4 images suivantes, il **n'écrit pas de liste**. La CPS2 garde donc la même
  liste affichée 5 images. La liste suivante n'a plus d'objet de l'emplacement 4. La durée est celle de l'arcade.

### 2.2 Ce que faisaient le banc et le cœur

- Le talon du chargeur (`mame_test.py`) écrit `$C0BC` tout de suite, ce qui est juste pour le code du jeu.
  `banc_sprites.lua` (`suivre4()`, appelée à chaque conversion de liste) et `cps_hsfa.cpp` (`HsfaSuivre4`) en
  déduisaient **immédiatement** la table de l'emplacement 4. La liste du portrait, convertie juste après l'appel,
  recevait donc les codes globaux du fichier 457. Comme cette liste convertie reste affichée 5 images, le défaut
  durait 5 images.

### 2.3 Classement

| piste | verdict |
|---|---|
| défaut de traduction | **non** : même ordre que le MIPS, même durée d'affichage que l'arcade |
| ordre des écritures du jeu, retard d'une image de la liste CPS2 | **non** : le retard CPS2 est le même en arcade, et la liste est convertie au marqueur de fin |
| double tampon des objets | **non** : la liste convertie est la bonne, avec la mauvaise table |
| **banc / cœur : changement de banque appliqué tout de suite** | **oui** : la PS2 charge de façon asynchrone ; le banc et le cœur supposaient un chargement instantané |

### 2.4 Autres jeux

- **SFA3** (`png/ro3_sortie_face.png`, `ro3_vs.png`) : `$FF3E48` ne change pas (`605000a9`) entre la sélection et
  le combat. Le portrait de SFA3 vient des banques arcade. Rien à corriger.
- **Hyper** (FBNeo, pilote `hyper`, `png/fb_hyper_*.png`) : `$C0BC` n'est jamais écrit et l'emplacement 4 n'a aucun
  objet (`agent_ro9`). Écran VS, entrée et sortie propres. Les 2 images blanches avec des formes noires (972-973) sont
  d'origine : l'arcade a la même image (2405, 1 408 pixels sombres).

## 3. Correctif

### 3.1 Règle (banc et cœur, même logique)

- Un nouveau fichier lu par `$C0BC` / `$FF3E48` passe d'abord **en attente**. Il ne s'applique pas tout de suite,
  sauf au tout premier fichier ou si l'interrupteur est coupé.
- À chaque fin d'image, le fichier en attente devient le fichier affiché dans deux cas :
  - **aucune liste convertie pendant l'image n'a d'objet de l'emplacement 4**. Une image sans liste compte : la liste
    déjà convertie reste affichée telle quelle.
  - le **délai maximal** est atteint (10 images, réglable).
- Si le pointeur revient au fichier affiché, l'attente est annulée.
- Ce comportement imite la PS2 : la table change quand le jeu ne montre plus l'ancien contenu. Le délai maximal borne
  le cas où le jeu montrerait des objets du nouveau fichier sans laisser de trou. Ce cas n'a été vu dans aucun essai.

### 3.2 Fichiers

- **`banc_sprites_lat4.diff`** : contre `work/mame/banc_sprites.lua` (`patch -p1` depuis `<workspace>`, essai à
  blanc OK). Variables :
  - `BANC_LAT4=0` : ancien comportement ;
  - `BANC_LAT4_MAX` : délai maximal (10 par défaut) ;
  - `BANC_LAT4_LOG` : journal des demandes, attentes et chargements ;
  - `BANC_LISTE_LOG` (diagnostic) : empreinte de la dernière liste convertie de chaque image.

  Copie corrigée : `lua/banc_sprites.lua`.
- **`cps_hsfa_lat4.diff`** : contre `src/burn/drv/capcom/cps_hsfa.cpp` de l'arbre FBNeo (`patch -p1` depuis
  l'arbre). Il s'applique à `agent_fbneo_rejeu/fbneo` et, avec un décalage, à `fbneo-hsfa`. Réglages :
  - `HSFA_LAT4=0` : ancien comportement ;
  - `HSFA_LAT4_MAX` : délai maximal ;
  - entrées de configuration `lat4=` / `lat4_max=` dans `hsfa_tab`. Les variables d'environnement l'emportent.

  Trois variables d'état sont ajoutées (`nAttente4`, `nDepuis4`, `nVu4`, avec `SCAN_VAR`). **La taille des états
  change** : un état sauvé avec l'ancien cœur ne se rechargera probablement pas. Non vérifié dans RetroArch.
- **Cœurs construits sur la copie** (`livraison/`) :

  | cœur | md5 |
  |---|---|
  | `fbneo_hsfa_libretro.so` (Linux) | `3b3d34f1…` |
  | `fbneo_hsfa_libretro_android.so` (arm64, NDK r28c) | `557935ae…` |
  | `fbneo_hsfaws_libretro_android.so` (16:9) | `4788f74a…` |

  Les zips de jeu n'ont pas à être refaits : `livraison_v145` convient tel quel.
- **Traducteur : aucun changement.** Retarder l'écriture de `$C0BC` dans le talon serait faux. Le jeu lit ce pointeur
  tout de suite, pour les données d'animation de la paire et pour les acteurs de fin (`A0 = $C0BC(A5)`). Sur la PS2
  aussi, ce pointeur est posé immédiatement ; seul le contenu graphique arrive plus tard. C'est donc au rendu (banc et
  cœur) de modéliser ce retard.

## 4. Validation

### Banc MAME (fork `sfa3hx`, copie des ROM d'Upper `sz3ud.03c` `a296538f…`)

- Captures avant / après : `png/ro5_sortie_face.png` / `png/ro5_sortie_face_lat.png` (Ryu) et
  `png/ro5_rival_blanka_lat0.png` / `lat1.png` (Blanka, 2e partie). Après correctif, le portrait reste intact jusqu'à sa
  disparition, comme l'arcade.
- Non-régression par empreinte de chaque liste convertie (`mesures/l_*_{0,1}.txt`) : 4 tournées avec puis sans
  correctif. Sur 178 000 images, les seules listes différentes sont **une par sortie de face-à-face** :
  - attraction, 20 000 images : 0 liste différente ;
  - Ryu, 46 000 images, avec sa fin (fichier 391) : 1 (image 2449) ;
  - Guile `$20`, 52 000 images, avec sa fin (415) : 1 (2497) ;
  - Blanka `$19`, 60 000 images, avec sa fin (408) puis une 2e partie : 2 (2449, 58115).

  Tous les autres changements de fichier (intro 455/456, fins) se font sans attente : 0 objet de l'emplacement 4 à
  ce moment-là (`mesures/lat4_*_1.txt`).

### Cœur FBNeo (hsfa_run, zips de `livraison_v145`)

- Captures avant / après : `png/fb_sortie_face_avant.png` / `png/fb_sortie_face_apres.png`. Avec `HSFA_LAT4=0`, le
  nouveau cœur est identique au pixel à l'ancien sur toute la fenêtre.
- Non-régression, ancien cœur contre nouveau, captures toutes les 25 images sur 20 000 images : **797/797
  identiques** pour une partie d'Upper (face-à-face, combat, game over, attraction, `png/fb_nr_u_vue.png`), pour
  l'attraction d'Upper et pour une partie de SFA3 (`png/fb_nr_s_vue.png`).

## 5. Limites et suites

- **Non essayé sur console.** À faire : les cœurs de `livraison/` sur l'appareil, au face-à-face du 1er combat.
- Les emplacements 2/3 (banque du perso, lue sur l'id `$FF8503` / `$FF8903`) changent aussi tout de suite. Aucun
  défaut n'a été vu dans les captures (sélection, VS, combats). La même règle pourrait s'y appliquer si un retour le
  demande.
- Pour intégrer : appliquer les deux diffs aux fichiers partagés, puis reconstruire les cœurs (§5 de
  `agent_fbneo_rejeu/REJEU-FBNEO.md`). L'arbre `fbneo/` d'ici est une copie, avec les objets de construction, et peut
  être supprimé ensuite.
