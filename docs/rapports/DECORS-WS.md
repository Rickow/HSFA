# DECORS-WS — Pilote d'export d'un décor SFA3 (CPS2) en PSD à calques, pour le widescreen

Dossier : `<workspace>/work/decors_ws/` (rien n'a été modifié ailleurs).
Décor pilote : **décor `$0C` = Sodom** (ID perso 6) — le **temple à cloche** du premier essai `stage00`
(cloche, arbre, lanternes, balustrade rouge, étals, ville au fond). Le décor de Ryu (`$00`) est un autre
décor (coucher de soleil, pagode). Planche des 28 décors forcés : `cap/planche_decors.png`.

---

## 1. Méthode

1. **Atteindre un combat** (`lua/explore.lua`) : ROM arcade `sfa3ud` (MAME 0.285 standard,
   `-rompath <workspace>/work/mame/roms`), pièces, Start, J1 = Ryu (`+$102` = 0), **décor forcé** par
   prise d'écriture sur `$FF8100` (= décor × 2, valeur `$0C`), vies maintenues. Un état est sauvegardé
   par Lua (`manager.machine:save`, jamais `-state` en ligne de commande) : `sta/sfa3ud/combat_0C.sta`.
2. **Balayer la caméra** (`lua/rec.lua`) : on recharge l'état puis on impose à chaque image les X des deux
   joueurs (`$FF8400+$10` et `$FF8800+$10`, mots ; écart ±`$60`) le long du trajet
   centre → `$100` (gauche, maintien 135 images) → `$400` (droite, maintien 135) → `$280`, 2 px/image,
   975 images. Pendant les maintiens J1 saute (Haut) pour faire monter la caméra.
   Relevé de **chaque image** dans `rec2/full.rec` (76 Mo) : registres CPS-A (64 o, partage MAME
   `:cps_a_regs`), CPS-B (64 o, `:cps_b_regs`), palette MAME (pens 0-`$BFF`, `:palette`), RAM vidéo
   `$900000-$90FFFF` (tilemaps, table rowscroll, source palette).
3. **Captures de contrôle** : la même séquence (déterministe) est rejouée 4 fois avec un plan seul
   (`ISO=1/2/3`, layer control CPS-B `$804166` réécrit à la volée) ou les 3 plans (`ISO=0`), sprites
   supprimés (écritures objram `$700000-$70FFFF` remplacées par `$FF00`) ; écran 384×224 toutes les
   4 images (`rec2/scr_*.bin`, 244 captures par passe).
4. **Rendu hors ligne** (`py/cpsgfx.py`) depuis la région `:gfx` vidée par Lua (`gfx/gfx_region.bin`,
   32 Mo ; ≠ `<workspace>/work/cps2/sfa3_gfx_region.bin`, qui n'est pas la région MAME de ce jeu de
   ROM), en reprenant exactement le pilote MAME (`cps1_v.cpp`) :
   - dispositions `cps1_layout8x8/8x8_2/16x16/32x32` (plans `{24,16,8,0}`, bit `0x80>>n`) ; scroll1 : jeu
     8×8 gauche/droite selon la **parité de colonne** (`tile_index & 0x20`) ;
   - code physique = `gfxrom_bank_mapper` table `mapper_cps2` : `(0x20000 + (code<<s & 0x1FFFF)) >> s`,
     s = 0/1/3 (scroll1/2/3), scroll3 `code & 0x3FFF` → **les tuiles de plans sont à +8 Mo** dans la région ;
   - balayage tilemap `tilemapN_scan`, attribut : palette `attr&0x1F` (+`$20/$40/$60`), flipX `0x20`,
     flipY `0x40`, groupe de priorité `(attr>>7)&3` ; **pen 15 = transparent** ;
   - écran : X tilemap = sx + 64 + scrollX (+ rowscroll de la ligne pour scroll2), Y = sy + 16 + scrollY ;
     rowscroll : `scroll2x + other[(ligne_brute + reg $20) & $3FF]` si `videocontrol & 1`.
5. **Recollage** (`py/build_world.py`) : pour chaque image et chaque plan, **seule la partie visible**
   (fenêtre 384×224, composée à coup sûr) est recollée dans une grille « monde » (coordonnées tilemap
   déroulées par continuité) : par case, code + attributs (palette, flips, priorité), avec comptage des
   variantes (= tuiles animées). Complément : cases des **colonnes visibles** situées hors de la fenêtre
   verticale (le jeu compose la colonne entière : 0 incohérence avec les cases vues) ; 70 cases scroll1,
   25 scroll2, 0 scroll3.
6. **Export** (`py/export_decor.py`) : PSD + PNG + ACT + JSON (§5). Écrivain PSD : `py/psdwriter.py`.

## 2. Variables / registres utilisés

| Quoi | Où | Valeur sur ce décor |
|---|---|---|
| décor | `$FF8100` (décor×2) | `$000C` |
| X joueurs | `$FF8410`, `$FF8810` (mot) | imposés |
| vies | `+$50/$52` | `$90` |
| bases plans | CPS-A `$804102/04/06` | `$9000` / `$9040` / `$9080` → `$900000` / `$904000` / `$908000` |
| table rowscroll | CPS-A `$804108` (« other ») | tourne sur `$90E0/$90E8/$90F0/$90F8` (4 tampons) |
| palette | CPS-A `$80410A` | `$90C0` → RAM palette `$90C000` |
| scroll X/Y | CPS-A `$80410C…$804116` | voir §4 |
| décalage rowscroll | CPS-A `$804120` | = scroll2 Y |
| video control | CPS-A `$804122` | `$000F` (bit 0 = rowscroll scroll2 actif) |
| ordre/activation plans | CPS-B `$804166` | `$1E0E` → bas→haut : **scroll2, scroll3, scroll1** (sprites en dessous, prio CPS2) |

**Synchronisation** (établie par mesure) : l'image affichée à l'image *t* = registres CPS-A/B relevés à
*t−1* + RAM vidéo et palette MAME relevées à *t* ; la palette MAME de *t* = RAM palette relevée à *t−1*
(copie au vblank). La variable caméra en RAM n'a pas été nécessaire (les registres de défilement suffisent).

## 3. Contrôle d'exactitude

| Contrôle | Résultat |
|---|---|
| Rendu hors ligne d'un plan (VRAM + registres de l'image) vs capture MAME du plan isolé, 3 plans × 97 images (1ʳᵉ passe) | **0 px d'écart** |
| Composite des 3 plans (ordre CPS-B) vs capture MAME sans sprites, 97 images | **0 px d'écart** |
| **Écran recomposé depuis l'image MONDE** + registres de l'image vs capture MAME du plan isolé, 3 plans × 242 images (passe finale) | scroll1 **0**, scroll3 **0**, scroll2 **0 hors cases animées** (5 014 px, tous dans les 6 cases animées : le monde garde la variante majoritaire) |
| Cohérence colonnes composées / cases vues | 0 incohérence |
| Mots palette CPS2 → RGB (formule MAME) vs palette MAME | 1536/1536 |
| Relecture PSD (psd-tools 1.24) : arbre, visibilités, pixels des 3 calques de plans = PNG | identiques ; composite psd-tools ≈ fusion interne (écart ≤ 3/255, arrondis alpha) |

Scripts : `py/verif_iso.py`, contrôle intégré à `py/export_decor.py` (→ `out/decor0C_temple_cloche/controle.json`),
`py/verif_psd.py`.

## 4. Dimensions et course caméra (décor `$0C`)

- **Parallaxe : aucune** — les 3 plans défilent à la même vitesse (pente 1,00) : scroll2X = scroll3X − `$C0`,
  scroll1X ≡ scroll3X (mod 512). Course caméra X = **384 px** (scroll3X `$0C0`→`$240`),
  Y = **21 px** (16 px vers le haut aux sauts, 5 px vers le bas aux secousses : Y écrit `$FF05` etc. = +5 modulo).
- Monde vu en 4:3 = **768 × 245 px** par plan (coordonnées tilemap X 256→1024 pour les trois ; scroll2
  inclut le rowscroll constant +`$C0`).

| Plan | Tuile | Tilemap | Monde exporté (tilemap px) | Grille JSON | Nature |
|---|---|---|---|---|---|
| scroll1 | 8 px | 512 px **anneau** (recomposé) | X 192-1088, Y 256-504 | 112 × 31 | avant-plan (lanternes, guirlandes, statues, enseigne) |
| scroll2 | 16 px | 1024 px, **statique** | X 192-1088, Y 768-1024 | 56 × 16 | fond (façades, ville, sol) |
| scroll3 | 32 px | 2048 px, **statique** | X 192-1088, Y 1792-2048 | 28 × 8 | plan médian (cloche, arbre, balustrade, bannières) |

Anneau scroll1 : marge composée mesurée ≈ **56-64 px à gauche**, **24-56 px à droite** de la vue
(selon le sens de déplacement) — cohérent avec le modèle RING (~58-62 px). Les plans scroll2/3 ne
bougent pas en VRAM (seules 6 cases scroll2 changent : animation).

**Canevas PSD : 896 × 245** = 64 + 384 (course) + 384 + 64 ; origine = écran à l'extrémité gauche, Y haut de course.

### Zones à combler (identiques pour les 3 plans, faute de parallaxe)

| Cible | Gauche (x canevas) | Droite (x canevas) | Hauteur | px / plan |
|---|---|---|---|---|
| **448×224** (core FBNeo-WS) | 32 → 64 (**32 px**) | 832 → 864 (**32 px**) | 245 lignes | 15 680 |
| 512×224 (option) | 0 → 64 (64 px) | 832 → 896 (64 px) | 245 lignes | 31 360 |

Définition : rectangle de course (X × Y, toute combinaison) élargi de 32/64 px, moins le contenu connu.
Aucun trou à l'intérieur de la course 4:3 (0 px). Au milieu de la course rien ne manque : le manque
n'apparaît qu'aux deux extrémités.

Ce que montre aujourd'hui le core 448 dans ces bandes (calque « VRAM hors course ») : scroll2/3 →
rien (transparent → noir) ; scroll1 → **contenu d'anneau recyclé** (ex. statue « 天中殺 » et lanternes du
bord gauche du monde réapparaissant à droite) = faux. Confirme le défaut de l'ancien `stage00.psd`.

## 5. Fichiers produits

- **`out/decors_sfa3.psd`** (2,2 Mo, RVB 8 bits, RLE) — un groupe par décor :
  ```
  [G] SFA3 — décor $0C (Sodom) — temple à cloche
        NOTES (lire) — sol à plat, animations, légende          (masqué, texte en pixels)
    [G] repères (masqué)
          cadres 4:3 / 16:9 aux deux extrémités (blanc 384, cyan 448, magenta 512, jaune = course)
          repère sprites (persos, HUD, objets de décor en sprites — hors export)   (masqué)
          grille scroll1 (8 px) / grille scroll3 (32 px) / grille scroll2 (16 px)   (masqués)
    [G] avant-plan (scroll1 8 px) — lanternes, guirlandes, statues
          à combler 448×224 — scroll1 (cible core)              (rouge)
          à combler 512×224 — scroll1 (option)                  (orange, masqué)
          animations — scroll1 : … palettes cycliques $21…$34   (masqué)
          avant-plan (scroll1 8 px) — …                         (image monde, échelle 1, couleurs réelles, pen 15 = transparent)
          VRAM hors course — scroll1 : … (NON fiable, info)      (masqué)
    [G] plan médian (scroll3 32 px) — … (même structure)
    [G] fond (scroll2 16 px) — façades, ville, sol — SOL EXPORTÉ À PLAT (rowscroll) (même structure)
  ```
  Pour d'autres décors : ajouter un groupe frère au même niveau (le canevas devra couvrir le plus grand décor).
- `out/decor0C_temple_cloche/` :
  `plan_scroll{1,2,3}.png` (calques monde), `apercu_decor.png` (3 plans), `apercu_zones.png` (zones + cadres),
  `apercu_psd_fusion.png`, `apercu_relu_psdtools.png` (relecture), `apercu_vram_hors_course_et_sprites.png`,
  `palettes_scroll{1,2,3}_XX-YY.act` (2 × 16 palettes de 16 couleurs par plan, 256 entrées, index
  transparent 15), `palettes.json` (mots CPS2 bruts + RGB de référence + toutes les versions des palettes
  animées), `carte_tuiles.json` (par plan : origine monde, position dans le canevas, grille
  `[code, palette 0-31, flipX, flipY, groupe prio, attr brut]` ou `null`, tuiles animées avec variantes,
  zones à combler), `controle.json`.
- Scripts : `mame.sh` (lanceur : `nice -n 19`, `-nvram_directory`/`-cfg_directory`/`-state_directory`/
  `-snapshot_directory` locaux), `lua/explore.lua`, `lua/rec.lua`, `lua/dump_gfx.lua`, `py/recio.py`,
  `py/cpsgfx.py`, `py/build_world.py`, `py/world_render.py`, `py/export_decor.py`, `py/psdwriter.py`,
  `py/verif_iso.py`, `py/verif_psd.py` ; venv `venv/` (numpy, Pillow, psd-tools).
  Reproduire : `./mame.sh lua/rec.lua` (cf. variables en tête), puis
  `venv/bin/python py/build_world.py rec2/full.rec work/monde.pkl && venv/bin/python py/export_decor.py && venv/bin/python py/verif_psd.py`.

## 6. Sol rowscroll, animations

- **Sol** : le rowscroll de scroll2 est actif (`$804122` bit 0) mais la table donne **+`$C0` sur toutes les
  lignes, à toutes les images** → aucune perspective sur ce décor ; scroll2 est exporté à plat en
  coordonnées tilemap (décalage inclus). Le code gère un rowscroll variable par ligne (coordonnée monde
  par ligne) ; pour un décor à vraie perspective, l'image « à plat » ne s'alignera plus avec les autres
  plans qu'à une ligne près (prendre la valeur médiane, ce que fait l'export).
- **Tuiles animées** : 6 cases scroll2 (colonnes 11-13, lignes 6-7 de la grille JSON ; canevas x 176-224,
  y 96-128), 3 phases (codes `$D8F3-$D8F8`, `$D8F9-$D8FD`, `$A25A-$A26C`), ~1/3 du temps chacune.
- **Palettes cycliques** : scroll1 `$21-$34` (18 palettes, 2 à 12 versions : lanternes/lumières),
  scroll2 `$4D`, `$56`, scroll3 `$77`, `$7C` (2 versions). Repérées en cyan dans les calques « animations ».
- **Éléments en sprites** (hors export, repère seulement) : la vue sur la ville dans l'embrasure centrale
  et le panier/lanternes suspendus sont des sprites → trou noir dans les plans à cet endroit.

## 7. Réimportation (À FAIRE — description seulement)

- **Par plan, par tuile** : découper l'image peinte sur la grille du plan (8/16/32 px, alignée sur
  l'origine `origine_dans_canevas_psd`) ; chaque tuile ≤ **15 couleurs opaques + pen 15 transparent**,
  et toutes ses couleurs dans **une seule palette** de 16 parmi les **32 palettes du plan**
  (scroll1 `$20-$3F`, scroll2 `$40-$5F`, scroll3 `$60-$7F`) ; réutiliser d'abord les palettes existantes
  (quantification vers la palette la plus proche), n'en créer que dans les slots libres (ici scroll1 : `$3C-$3F`
  non utilisées dans la course, scroll2 : `$57-$5F`, scroll3 : `$7A`, `$7D-$7F`) et **ne pas toucher aux palettes animées**.
- **Dédoublonnage** avec retournements X/Y (attr `0x20/0x40`) contre les tuiles existantes de la ROM puis
  entre nouvelles tuiles ; encodage dans la disposition CPS2 (plans `{24,16,8,0}`, +8 Mo, `code_physique`
  dans le JSON) ; espace libre à trouver dans la région gfx (et ROM `sz3.13m…` correspondantes, avec le
  « shuffle » CPS2 inverse de `cps2_gfx_decode`).
- **Tilemaps** : scroll2/3 sont statiques et larges (1024/2048 px) ; ici le monde occupe X 256-1024
  → **à droite il n'y a plus de place** (scroll2 : colonne 64 = bord de la tilemap 1024 ; scroll3 : 2048,
  marge OK) ; à gauche, colonnes 0-15 (scroll2) / 0-7 (scroll3) libres. Il faudra donc soit réécrire
  les données de construction du décor (où le jeu écrit ces tilemaps au chargement), soit décaler.
  scroll1 est un **anneau de 512 px recomposé** : les nouvelles colonnes doivent être ajoutées aux
  **données sources** que le jeu lit pour recomposer (pas à la VRAM), et la marge composée (~24-64 px)
  doit couvrir 32 px (448) de chaque côté → probablement élargir la fenêtre de composition dans le code.
- Bornes caméra inchangées (`$0C0-$240`) ; le core 448 actuel affichera alors les colonnes ajoutées.

## 8. Limites

- Un seul décor ; trajet caméra = X complet (bornes atteintes et tenues) mais **Y limité à ce que
  produisent les sauts de Ryu et les secousses** (−16/+5 px) : une course verticale plus grande
  (super-sauts, autres persos) n'est pas couverte ; les zones à combler couvrent 245 lignes.
- Contenu VRAM hors course (bandes) non validé par définition : fourni masqué, pour information.
- Image monde = palette de la **dernière image** et variante **majoritaire** des tuiles animées.
- Les sprites de décor ne sont pas exportés (repère seulement, deux images).
- Décor forcé par `$FF8100` (adversaire Birdie) : décor complet et cohérent à l'écran, mais pas le
  chemin « naturel » du mode arcade.
- MAME signale des checksums inattendus pour `sz3ud.03c`/`sz3ud.04c` (programme) dans le rompath
  imposé ; sans effet visible sur les graphismes (région gfx vidée de cette session).
- PSD : notes rendues en pixels (pas de calques texte) ; vérifié avec psd-tools, pas ouvert dans Photoshop/GIMP.

---

## 9. Export complet (2026-10-10) — tous les décors dans `out/decors_sfa3.psd`

**Résultat** : `out/decors_sfa3.psd` (59,8 Mo, 1280 × 320, RVB 8 bits, RLE) = **26 groupes, un par jeu de données**
couvrant les 32 numéros de décor `$00-$3E` (liés : `$00/$2E`, `$08/$24`, `$0C/$28`, `$22/$26`, `$2A/$3C/$3E` ;
`$14` a son propre groupe, sa note rappelle qu'il partage scroll1/scroll3 avec `$2A` — vérifié : cartes s1/s3
identiques, aucune autre paire identique). Seul le 1er groupe est visible ; cocher l'œil des autres.
Remplace le PSD du pilote (le dossier `out/decor0C_temple_cloche/` du pilote est conservé tel quel, il sert à
`reimport/`). Par décor : `out/decors/decor<ID>/` (`plan_scroll{1,2,3}.png`, `apercu_decor.png`, `apercu_zones.png`,
`palettes_*.act`, `palettes.json`, `carte_tuiles.json`, `controle.json`). Synthèse : `out/decors/recap.json`,
**`out/decors/RECAP.md`** (tableau : décor, perso, canevas, ordre, parallaxe, rowscroll, course, zones 448/512,
palettes utilisables, animations, contrôle), **`out/decors/planche_decors.png`** (planche contact : aperçu | zones).

### Contrôles (tous les décors)

| Contrôle | Résultat |
|---|---|
| Écran recomposé depuis l'image MONDE vs capture MAME du plan isolé (3 plans × 203 images par décor, 4 modes de caméra) | **0 px hors cases animées**, 26/26 |
| Composite 3 plans (ordre CPS-B) vs capture MAME sans sprites | **0 px hors cases animées**, 26/26 (y compris les images des phases secondaires) |
| Cohérence colonnes composées / cases vues ; trous dans la course réelle | 0 / 0 partout |
| Relecture psd-tools (`py/verif_psd_tous.py`) : 26 groupes, calques de plans == PNG au pixel (alpha compris) | **RELECTURE OK** |
| `$0C` régénéré (la course Y a changé) vs export du pilote | 2906/743/192 cases identiques ; seules diffèrent les versions de référence des palettes cycliques (`$21…$33`, `$56`, `$7C`) |

### Course verticale élargie

- `lua/rec_all.lua` (via `capture_decor.sh`, `batch_tous.sh`) : trajet X butée → butée en Y naturel (sauts),
  puis **`haut`** (Y des deux joueurs forcés à +`$100`) → la caméra monte à sa **butée naturelle**, mesurée sur
  `$FF82A4` (décalage caméra Y, + = haut) : **16 px pour les 26 jeux de données** (le jeu plafonne : la super de Cammy
  et les super-sauts ne peuvent pas dépasser) ; puis **`cup`** (caméra imposée à butée + 32 = **48 px**) et **`cdn`**
  (−16 px), aux deux butées X. Vers le bas : 0 en jeu hors secousses (≤ 5 px observés).
- Export : **Y réelle −16/+0, exportée −48/+16** (+21 sur `$0E`, `$2C`, `$36` : secousse pendant `cdn`).
  Zones : rouge = 448 dans la course réelle ; rose = marge Y caméra forcée ; orange masqué = 512 ;
  **bleu = « décor qui s'arrête »** : dans la fenêtre 448/512 caméra forcée comprise, hors course 4:3 réelle, aucun
  plan opaque (haut des décors, parfois bas) → à peindre sur le plan du fond (`plan_du_fond` dans `controle.json`).
- Y nominal = caméra au repos (`$FF82A4` = 0) ; sans cela le sens s'inversait sur la moitié des décors.

### Particularités découvertes et traitées

1. **Animation par défilement** (`$14`, `$2A`, `$20`, `$2C`) : le jeu fait sauter le registre de défilement entre des
   zones de la tilemap (ex. `$14` scroll3 : X +`$400`, Y +`$100…$700`, 11 phases ; scroll1 2 phases ; `$2C` scroll2 4
   phases ; `$20` scroll3 3 phases). `py/build_world.py` décompose le défilement en caméra continue + phase (sauts
   ≥ 24 px hors changement de mode de caméra, arrondis à 64/16/8 px) ; toutes les phases sont relues à chaque image
   (plans statiques en VRAM). Export : calque principal = phase la plus fréquente, **calques masqués « phase k »**
   par plan (même géométrie : à étendre comme le principal), `phases_defilement` dans `carte_tuiles.json`.
   L'ancien recollage avait produit un monde de 38 400 × 99 584 px (pickle de 11,7 Go, écrasé depuis).
2. **Défilement automatique** (`$1C` Rolento, scroll1 = train qui passe, ~2 px/image) : bande déroulée de 3 664 px,
   périodique sur **512 px** (= tilemap entière) → repliée sur une période + 576 px (`export_tous.replier`) ;
   parallaxe notée « auto » ; rien à combler en X pour ce plan.
3. **Rowscroll variable** (sol en perspective, et ciel qui dérive sur `$14/$2A`) : plan exporté en coordonnées
   tilemap (« à plat ») ; les zones sont calculées ligne par ligne. Les cases complétées par colonne composée sont
   **découpées** à ce qui peut s'afficher (course + caméra forcée + 512) : plus de tuiles parasites loin du sol.
4. **Parallaxe** : chaque plan est calé sur l'écran de la butée gauche ; ses zones à combler sont dans ses propres
   coordonnées (un plan lent, ex. ciel de `$00`/`$2C` à 0,2-0,25, a donc ses bandes au milieu du canevas).

### Notes par décor (calque « NOTES (lire) », masqué)

Décors liés, ordre CPS-B, parallaxe, rowscroll, course réelle/exportée, **palettes utilisables** (relogé fork/FBNeo
par plan, et en place arcade) lues dans `injection_fork/palettes_libres_ro3.json` (tilemaps complètes, décors liés
compris, `$7F` jamais en scroll3), animations (tuiles, palettes cycliques, phases de défilement, défilement auto),
légende des zones. Même information dans `RECAP.md` (liste complète des palettes en fin de fichier).

### Reproduire

```
./batch_tous.sh 00 02 … 3A          # capture (5 MAME par décor) + build_world ; 0C déjà fait
venv/bin/python py/build_world.py recs/<ID>/full.rec work/monde_<ID>.pkl     # (re)recollage seul
NPROC=4 nice -n 19 venv/bin/python py/export_tous.py [--decors 00,0C] [--psd …]  # ~6 min pour les 26
venv/bin/python py/verif_psd_tous.py && venv/bin/python py/recap_md.py
```
Disque : `recs/` ≈ 12 Go (relevés + captures, nécessaires pour refaire l'export), `work/monde_*.pkl` ≈ 130 Mo.

### Limites

- Le calque principal d'un plan animé garde la variante majoritaire des cases et la palette d'une image de
  référence (Y nominal, hors flash) ; phases de défilement : `reimport.py` ne traite aujourd'hui que le calque
  principal (les phases seront à réinjecter de la même façon, zones de tilemap décalées de `decalage_tilemap_px`).
- Décors forcés par `$FF8100` (J1 Ryu) : chemin non « naturel » du mode arcade ; `$38`/`$3A` (Vega, Karin) sont des
  décors complets et cohérents à l'écran.
- Les noms de perso des groupes suivent l'ordre des ID (`$xx/2`), pas forcément le propriétaire « officiel » du décor.
- Sprites de décor non exportés (repère seulement).
