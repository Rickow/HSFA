# EXPORT — décor de RYU de Street Fighter Alpha 2 (arcade `sfa2u`, décor index 0, `$FF8100 = $0000`)

Dossier : `<workspace>/work/decors_sfa2/export/` (rien n'a été modifié ailleurs ; les outils du pilote SFA3
`decors_ws/` ont été **copiés** puis adaptés ici). MAME système 0.285 (`/usr/games/mame sfa2u`), ROM
`-rompath <workspace>/work/carto_sfa2/roms`, `nice -n 19`, dossiers nvram/cfg/sta/snap propres (`mame.sh`),
`-video none -sound none -nothrottle -skip_gameinfo`, états sauvés/chargés **uniquement par Lua**, 2 MAME au plus.

Décor : **temple enneigé sous la pleine lune** — ciel, lune et montagnes (scroll3), collines enneigées (scroll1),
pin penché et sol enneigé (scroll2) ; en **sprites** : la pagode/temple de gauche, les nuages effilochés, un corbeau.

---

## 0. Résultat en bref

| | |
|---|---|
| Contrôle pixel (rendu hors ligne vs MAME, plans isolés) | **0 px** sur 497 images × 3 plans + composite 3 plans, en rendu direct ET depuis les images « monde » exportées |
| Contrôle sprites / écran complet | sprites seuls **0 px** (497 images) ; écran complet recomposé (plans + tous les sprites, priorités CPS2) **0 px** (497 images) ; 9 poses de référence : **0 px** partout |
| Ordre des plans (CPS-B layer control `$800166`) | **`$270E`** → bas→haut : **scroll3, scroll1, scroll2** |
| Parallaxe (vs scroll2) | scroll1 **3/4**, scroll3 **1/4**, en X **et** en Y (formules exactes sur 1 992/1 992 images, §3) |
| Course caméra X (registres) | scroll2 `$000-$180` (**384 px**), scroll1 `$0F0-$210` (288 px, registre mod 512), scroll3 `$0D0-$130` (96 px) |
| Course caméra Y | réelle : **16 px vers le haut** (sauts ; scroll2Y `$300→$2F0`), 0 vers le bas ; **exportée : −96 / +16 px** (caméra forcée) |
| Rowscroll | actif (`$804122 = $000F`) mais **constant +$C0** sur toute la table → pas de perspective |
| Tuiles animées / palettes cycliques | **aucune** (plans et palettes de sprites 0-6) ; seuls 42 flashes globaux (supers) |
| Objets sprites du décor | **temple** (pal. 1, 14 entrées, parallaxe 9/16), **nuages** (pal. 4, 2 objets × 2 instances, **affichés une image sur deux**), **corbeau** (pal. 5, 48 poses, devant tout) ; 123 tuiles 16×16 `$14801-$1487B` |

---

## 1. Méthode (reprise de `decors_ws/DECORS-WS.md`, adaptée)

1. **Partie** (`lua/explore.lua`) : 2 pièces (`Coin 1` images 600 et 640), `1 Player Start` (760), `P1 Button 1`
   toutes les 30 images jusqu'au combat (Ryu = curseur par défaut). **Décor forcé** par prise d'écriture sur
   `$FF8100` → `$0000` à partir de l'image **FS0 = 700**. Combat = `$FF800C == 2` et octet `+4` des deux joueurs `== 2`
   et `$FF80A8 == $0100` ; après 120 images stables : capture + `manager.machine:save("combat_00")`
   → `sta/sfa2u/combat_00.sta` (adversaire : Guy).
   - Piège : avec FS0 = 1000 (valeur de CARTE-sfa2 pour l'attraction), en partie le décor est déjà choisi à
     l'image 933 (`$FF8100 = $20`, décor de Zangief) ; FS0 = 700 est après le test RAM (fini vers l'image 110)
     et avant le choix : pas de « WORK RAM NG ».
2. **Balayage** (`lua/rec_sfa2.lua`, adapté de `rec_all.lua`) : rechargement de l'état, X des joueurs imposés
   (J1 = c − 96, J2 = c + 96), vies maintenues, 4 px/image, trajet
   `80:60:nat, 480:60:nat, 480:50:haut, 80:50:haut, 80:40:cup, 480:40:cup, 480:40:cuh, 80:40:cuh, 80:40:cdn, 480:40:cdn, 280:10:nat`
   (cible hexa du centre c : maintien : mode Y) — **1 993 images** :
   - `nat` : Y naturel, J1 saute pendant les maintiens ; `haut` : Y des joueurs +$100 → caméra à sa butée haute
     naturelle (mesurée : `$FF82A4 = 16`) ;
   - `cup` / `cuh` / `cdn` : caméra Y **forcée** (prise d'écriture sur `$FF82A4`) à butée + 32 (= 48 px),
     butée + 80 (= **96 px**) et −16 px : course Y bien plus grande que celle du pilote SFA3 (−16/+5).
   - Relevé de **chaque image** (`rec/00/full.rec`, format FRM2, 155 Mo) : CPS-A (64 o), CPS-B (64 o), palette MAME
     (pens 0-`$BFF`), RAM vidéo `$900000-$90FFFF` ; **objets** (`rec/00/obj.bin`, nouveau) : objram1, objram2,
     registres `:output` (12 o), RAM des objets de décor `$FFB000-$FFB3FF`.
3. **Passes de contrôle** (`capture.sh`, déterministes, écran 384×224 toutes les 4 images, 499 captures/passe) :
   `full` (écran complet), `0` (3 plans sans sprites), `1`/`2`/`3` (plan seul), **`4` (sprites seuls, nouveau)**.
   - **Piège sfa2u** : le jeu écrit les registres CPS-A/B au **miroir `$800100-$80017F`** (layer control =
     **`$800166`**), jamais en `$804166` comme SFA3 : la prise d'écriture doit viser `$800166` (sinon les passes
     « plan isolé » montrent les 3 plans). Le Lua pose les deux.
4. **Rendu hors ligne** (`py/cpsgfx.py`, inchangé hormis le chemin) depuis la région `:gfx` de sfa2u vidée par Lua
   (`gfx/gfx_region.bin`, **20 Mo**) ; tuiles de plans à +8 Mo (mapper CPS2), pen 15 transparent.
   Synchronisation identique à SFA3 : image affichée à *t* = registres CPS-A/B de *t−1* + VRAM/palette de *t*.
5. **Sprites hors ligne** (`py/sprites.py`, nouveau, fidèle à `cps2_render_sprites` de MAME) : blocs nx×ny,
   flips, `code + ((y & $6000) << 3)`, décalages `:output[4]/[5]`, tuiles 16×16 à `code × 128` dans la région ;
   **la dernière entrée de la liste est au-dessus** (MAME dessine de la fin vers le début et marque le pixel).
   **Liste affichée à *t*** = objram écrite à *t−3* : le jeu **alterne objram1/objram2 à chaque image** et la
   banque affichée est celle qui n'a PAS été écrite à *t−2* (déduite des changements d'une image à l'autre).
   Compositeur complet (`sprites.compose`) : plans avec codes de priorité 1/2/4 + masques `primasks` de MAME
   (CPS2 `$400004` = `$2641`).
6. **Recollage** (`py/build_world.py`, inchangé) puis **export** (`py/export_sfa2.py`, adapté de `export_tous.py`) :
   PNG par plan, PSD, ACT, `palettes.json`, `carte_tuiles.json`, `controle.json`.
7. **Mesures** (`py/mesures.py`), **sprites de décor** (`py/sprites_decor.py`), **poses de référence**
   (`lua/pose_camera.lua` + `pose_camera.sh` + `py/pose_camera.py`, §8).

## 2. Adresses SFA2 (`sfa2u`) vérifiées

| Quoi | Où | Vérification |
|---|---|---|
| décor | `$FF8100` (= décor × 2) | forcé à `$0000` → temple enneigé |
| structures joueurs | **`$FF8400` (J1), `$FF8800` (J2)** | — |
| X / Y joueur | **`+$10` / `+$14`** (mots ; sol Y = `$0028`) | X suit Droite/Gauche (sonde), Y = `$28` au sol |
| vies | **`+$50` / `+$52`** (max `$0090`) | décroissent ensemble aux coups (sonde 2) |
| état joueur | octet `+$04` = 2 en combat | — |
| état de jeu | `$FF800C` = 2 pendant le round (4 = fin de round), `$FF80A8` = `$0100` partie en cours, `$FF8004` = 4 en jeu | — |
| caméra X maître (scroll2) | **`$FF8290`** (= scroll2X + `$100` ; butées `$100-$280`) ; copies `$FF82A0`, `$FF82A8` | corrélation 1,00 |
| caméra Y maître | **`$FF82A4`** (décalage, + = haut ; scroll2Y = `$300 − $FF82A4`) ; copies `$FF82AC` | forçage OK (−64…+128) |
| caméra scroll1 / scroll3 | `$FF8210`/`$FF8214` (s1X = `$FF8210 − $40`, s1Y = `$100 − $FF8214`) ; `$FF8310`/`$FF8314` (s3X = `$FF8310 − $40`, s3Y = `$700 − $FF8314`) | dérivées du maître par parallaxe |
| registres CPS-A / CPS-B | écrits au **miroir `$800100-$80017F`** (MAME : partages `:cps_a_regs` / `:cps_b_regs`) | prise d'écriture `$800000-$8FFFFF` |
| layer control CPS-B | **`$800166` = `$270E`** | constant |
| priorités sprites/plans CPS2 | `$400004` (`:output[2]`) = **`$2641`** ; `:output` = `7000 807D 2641 0000 0040 0010` | compositeur 0 px |
| objram | écriture du jeu en `$708000+` ; banques MAME `:objram1`/`:objram2` alternées à chaque image | rendu 0 px |
| objets de décor (RAM) | **`$FFB080`** (routine `$4E01`, nuages), **`$FFB100`** (`$4E00`, nuages), **`$FFB180`** (`$0000`, temple) — emplacements de `$80` o ; X `+$10`, Y `+$14`, routine `+$02` | §6 |
| liste d'objets (ROM) | table `$1EB66` (espace opcodes, `$100(A5)` → déplacement `$011A`) → liste **`$1EC80`** (espace DONNÉES) : 4 × 16 o | §6 |

Bases VRAM (constantes sur les 1 992 images) : scroll1 `$9000` → `$900000`, scroll2 `$9040` → `$904000`,
scroll3 `$9080` → `$908000`, rowscroll « other » `$90E0` → `$90E000` (un seul tampon, ne tourne pas),
palette `$90C0` → `$90C000`. Video control `$804122` = `$000F`, décalage rowscroll `$804120` = `$01F3`.

## 3. Caméra : bornes et parallaxe

### Bornes (registres CPS-A ; valeurs déroulées, registre = valeur mod 512/1024/2048)

| Plan | X (course réelle) | course X | Y réel (nominal → haut) | Y exporté (forcé) |
|---|---|---|---|---|
| scroll2 (maître) | `$000` → `$180` | **384 px** | `$300` → `$2F0` (16 px) | `$2A0` (96 haut) → `$310` (16 bas) = 112 px |
| scroll1 | `$0F0` → `$210` (registre `$010`) | **288 px** | `$100` → `$0F4` (12 px) | `$0B8` → `$10C` = 84 px |
| scroll3 | `$0D0` → `$130` | **96 px** | `$700` → `$6FC` (4 px) | `$6E8` → `$704` = 28 px |

Caméra Y naturelle : uniquement vers le haut (sauts, butée `$FF82A4 = 16`), aucune secousse observée vers le bas.
X : butée gauche atteinte pour un centre des joueurs ≤ `$1C0`, droite ≥ `$340` (caméra = centre − `$C0`).

### Parallaxe (exacte sur 1 992/1 992 images, `out/decor00/mesures.json`)

```
s1X = $00F0 + ceil (3/4 · s2X)        s1Y = $0100 + floor(3/4 · (s2Y − $300))
s3X = $00D0 + floor(1/4 · s2X)        s3Y = $0700 + ceil (1/4 · (s2Y − $300))
```
Pentes : scroll1 **0,75** (X et Y), scroll2 1,00, scroll3 **0,25** (X et Y). Décalages à s2X = 0 : `$F0` et `$D0`.
(Comparer : décor SFA3 `$0C` du pilote = aucune parallaxe.)

### Rowscroll
Actif (bit 0 de `$804122`), table `$90E000`, décalage `$20` = `$01F3` ; **les 1 024 entrées valent `+$C0`** à
toutes les images → décalage constant, **pas de perspective** ; scroll2 effectif = s2X + `$C0` (le monde scroll2
est exporté en coordonnées tilemap, décalage inclus).

## 4. Plans, ordre, priorités

- CPS-B `$270E` : l0 = sprites, puis **scroll3 (ciel, lune, montagnes) → scroll1 (collines) → scroll2 (pin, sol)**.
- CPS2 `$2641` → priorités de plan scroll3 = 2, scroll1 = 4, scroll2 = 6 ; masques sprites MAME par priorité p :
  `FF FE FE FC FC F0 F0 00`. Un sprite p = 3 passe **devant scroll3, derrière scroll1 et scroll2** (temple, nuages) ;
  p = 7 passe **devant tout** (corbeau, persos, HUD).
- Attributs des cases : groupe de priorité de tuile (`attr>>7 & 3`) = 0 partout ; palettes utilisées :
  scroll1 `$20-$22`, scroll2 `$40-$4B`, scroll3 `$60-$63` (le reste est libre dans ce décor).
- Tilemaps : **scroll2 et scroll3 statiques** (0 mot changé sur 1 992 images) ; **scroll1 = anneau de 512 px recomposé**
  (53 images avec écritures, ≤ 88 mots) ; marge composée autour de la vue : **48-96 px à gauche, 24-72 px à droite**.

| Plan | Tuile | Monde exporté (tilemap px) | Grille JSON | Contenu |
|---|---|---|---|---|
| scroll1 | 8 | X 240-1040, Y 200-512 (800 × 312) | 100 × 39 | collines enneigées, arbuste à gauche |
| scroll2 | 16 | X 192-1088, Y 688-1024 (896 × 336) | 56 × 21 | pin penché, sol enneigé (premier plan) |
| scroll3 | 32 | X 192-832, Y 1760-2048 (640 × 288) | 20 × 9 | ciel, pleine lune, montagnes |

Le monde vu en 4:3 : scroll2 X 256-1024 (bord droit = **bord de la tilemap 1024**), scroll1 X 304-976, scroll3 X 272-752.
Canevas d'export (PSD/PNG) : **912 × 336**, chaque plan placé sur l'écran de l'image de référence (butée gauche,
Y nominal) en (80, 96) ; avec la parallaxe, **chaque PNG est dans SES coordonnées** (origine dans
`carte_tuiles.json` → `origine_dans_canevas_psd`), la superposition n'est juste qu'à la butée gauche.
Zones à combler pour 448×224 (course réelle) : 32 px de chaque côté pour scroll1/scroll2 (15 104 / 15 360 px),
16 px pour scroll3 (tuiles de 32 px déjà composées) ; marge Y forcée en sus (layers « marge Y »).

## 5. Animations et palettes

- **Tuiles animées : aucune** (0 case à plusieurs entrées dans les 3 plans).
- **Palettes cycliques : aucune** (plans `$20-$7F` et sprites `$00-$06`), hors **42 images de flash global**
  (assombrissement des supers de l'IA) exclues du repérage. Conversion mots CPS2 → RGB : 1 536/1 536.
- Animations portées par les **sprites** (§6) : corbeau (48 poses), dérive et clignotement des nuages.

## 6. Objets du décor en sprites

Filtre : codes de tuiles **`$14800-$14FFF`** (zone des sprites de décor). **123 tuiles 16×16 distinctes
`$14801-$1487B`**, palettes de sprites **1, 4, 5** (chargées par le décor ; aucune variation hors flashes).
Liste ROM (`$1EC80`, 16 o : X, Y, groupe, +5, routine…) :
`X $026E Y $00B1 grp 4 routine $0000` (temple) · `X $0015 Y $0044 grp $0C routine $0000` (*corbeau, hypothèse*) ·
`grp 4 routine $4E00` · `grp 4 routine $4E01` (nuages).

| Objet | Pal. | Prio | Entrées | Position / parallaxe (mesurée) | Animation |
|---|---|---|---|---|---|
| **Temple / pagode** (gauche) — RAM `$FFB180` | 1 | 3 | 14 entrées (blocs 8×4, 4×1, 5×1, 2×2, 1×3…), image 176×96 | écran_x = **41 − 9/16·s2X**, écran_y = **108 − 9/16·(s2Y − $300)** (coin de la 1re entrée ; résidu **0 px**) → parallaxe **0,5625** (ni scroll1 ni scroll3) | aucune |
| **Nuages** — RAM `$FFB080` (`$4E01`), `$FFB100` (`$4E00`) | 4 | 3 | 4 formes (3 à 6 entrées) | écran_x = X_instance − **1/4·s2X** + cte (résidu 0,5 px), Y à la parallaxe 1/4 (scroll3) ; dérive **−1/6** et **−3/16 px/image** | chaque objet porte **2 instances** (+$50/+$54 et +$58/+$5C, X en 16.16) et n'en dessine **qu'une par image, en alternance** → nuages à **30 Hz (transparence par scintillement)** |
| **Corbeau** sur la branche du pin | 5 | 7 | 1 entrée (1×1 ou 2×1 ailes ouvertes, flips) | fixe dans le monde à la parallaxe **1,0** : écran_x ≈ 356 − s2X (± 11 px selon la pose), écran_y = 54 − (s2Y − $300) | **48 codes** `$14843-$1487B` (71 poses avec flips) : repos, tête tournée, envol (`$14863-$1487B`) ; séquence complète dans `sprites_decor.json` |

Le temple est donc un **sprite de fond** et non un plan : un trou dans les plans à sa place est normal (il est
dessiné derrière scroll1/scroll2, devant le ciel). Le corbeau est dessiné **devant tout**, persos compris.
Références visuelles : `out/decor00/sprites/objet_*.png`, `planche_oiseau_pal05.png`, et pour chaque pose
`*_sprites_decor.png` (sprites de décor seuls), `*_decor_complet_sans_persos.png` (3 plans + sprites de décor
avec priorités), `*_difference_complet_moins_plans.png`.

## 7. Contrôles d'exactitude

| Contrôle | Images | Écart |
|---|---|---|
| Rendu direct d'un plan (VRAM + registres de l'image) vs capture du plan isolé (`py/verif_iso.py`) | 497 × 3 | **0 px** |
| Composite des 3 plans (ordre CPS-B) vs capture « 3 plans sans sprites » | 497 | **0 px** |
| Écran recomposé depuis les **images MONDE** exportées vs plans isolés (`export_sfa2.py` → `controle.json`) — modes nat 156 / haut 89 / cup 84 / cuh 84 / cdn 84 | 497 × 3 | **0 px** (0 case animée) |
| Idem composite 3 plans | 497 | **0 px** |
| Cohérence colonnes composées / cases vues ; trous dans la course réelle | — | 0 / 0 |
| Sprites hors ligne (liste t−3, banque alternée) vs passe « sprites seuls » | 497 | **0 px** |
| **Écran complet** recomposé (plans + tous les sprites, priorités) vs capture MAME | 497 | **0 px** |
| 9 poses de référence (`pose_camera`) : 3 plans isolés, 3 plans, sprites seuls, écran complet recomposé | 9 × 6 | **0 px** |
| Relecture PSD (psd-tools) : calques de plans vs PNG | 3 | 0 px |

## 8. Script réutilisable « pose caméra » (comparaison future à caméra identique)

`lua/pose_camera.lua` (MAME sfa2u) + `pose_camera.sh` (6 passes, 2 MAME à la fois) + `py/pose_camera.py` :

```
cd <workspace>/work/decors_sfa2/export
POS="0,C0,180,C0:48" [ST=combat_00] [HOLD=60] ./pose_camera.sh <dossier>
```
- `POS` = liste `s2x[:camy]` : **valeur visée du registre CPS-A scroll2 X** (hexa, `$000-$180` ici) et décalage
  caméra Y `$FF82A4` (décimal, + = haut, imposé ; défaut 0 = nominal, ce qui neutralise aussi les secousses).
  Les joueurs sont placés au centre s2x + `$1C0` (± 96) puis corrigés jusqu'à ce que le registre **affiché** (celui
  de l'image t−1) vaille exactement s2x ; la capture attend aussi l'absence de flash (palettes de plans = début).
- Sorties par position : PNG `posN_s2xXXX_s2yYYY_{ecran_complet, plans_sans_sprites, scroll1_seul, scroll2_seul,
  scroll3_seul, sprites_seuls, sprites_decor, decor_complet_sans_persos, difference_complet_moins_plans}.png`,
  `frm.rec` (FRM2 des images t−1 et t), `obj.bin` (listes de sprites), `poses.json` (tous les registres CPS-A :
  scroll1/2/3 X/Y, `$20`, `$22`, bases ; layer control ; écarts pixel de contrôle).
- Pour comparer le décor importé dans un autre jeu : imposer dans ce jeu **les mêmes registres scroll1/2/3 X/Y**
  (`poses.json`) et comparer plan par plan. Le Lua est spécifique à sfa2u (joueurs `$FF8400/$FF8800 +$10`, caméra
  `$FF8290/$FF82A4`, layer control au miroir `$800166`) ; pour SFA3 : mêmes joueurs et `$FF82A4`, layer control `$804166`.
- Références produites : `out/decor00/references/` — gauche/centre/droite (`s2X = $000/$0C0/$180`, Y nominal),
  les mêmes caméra haute naturelle (`$2F0`), centre à +48 et +96 px, et −16 px.

## 9. Fichiers produits

- `out/decor00/` : `plan_scroll{1,2,3}.png` (images monde RGBA, pen 15 transparent, palette de l'image de
  référence), `apercu_decor.png`, `apercu_zones.png`, **`carte_tuiles.json`** (par plan : origine monde/canevas,
  grille `[code, palette 0-31, flipX, flipY, prio, attr]`, bases VRAM, parallaxe, rowscroll, bornes, zones à
  combler), **`palettes.json`** (mots CPS2 + RGB, versions), `palettes_scroll{1,2,3}_XX-YY.act`, `controle.json`,
  `verif_iso.json`, **`mesures.json`** (registres, bornes, formules de parallaxe, rowscroll, anneau scroll1),
  `decor00_sfa2.psd` (facultatif : groupes par plan + zones + repères, 912×336).
- `out/decor00/sprites/` : `sprites_decor.json` (contrôles, priorités, objets, entrées, formules, séquence du
  corbeau, palettes de sprites 0-6 en mots CPS2/RGB, RAM des objets), `objet_temple_pal01.png`,
  `objet_nuage{1-4}_pal04.png`, `planche_oiseau_pal05.png`, `palettes_sprites_00-0F.act`.
- `out/decor00/references/` : poses de référence (§8).
- Données brutes : `rec/00/` (`full.rec`, `obj.bin`, `scr_{full,0,1,2,3,4}.bin`, journaux), `work/monde_00.pkl`,
  `gfx/gfx_region.bin` (région `:gfx` de sfa2u, 20 Mo), `sta/sfa2u/combat_00.sta`.
- Scripts : `mame.sh`, `capture.sh` (6 passes), `capture_iso.sh` (passes 1-4 seules), `pose_camera.sh` ;
  `lua/explore.lua`, `lua/rec_sfa2.lua`, `lua/pose_camera.lua`, `lua/dump_gfx.lua`, sondes (`sonde.lua`,
  `sondecam.lua`, `sondecamy.lua`, `cherche_obj.lua`, `info.lua`, `t_lc.lua`) ; `py/recio.py`, `py/cpsgfx.py`,
  `py/build_world.py`, `py/world_render.py`, `py/export_sfa2.py`, `py/psdwriter.py`, `py/verif_iso.py`,
  `py/sprites.py`, `py/sprites_decor.py`, `py/mesures.py`, `py/pose_camera.py`, `py/planche.py` ; essais dans
  `py/essais/`. `py3` = Python du venv de `decors_ws` (numpy, Pillow, psd-tools) sous `nice -n 19`.
- Captures d'étude : `cap/` (sondes, planches, comparaisons).

## 10. Reproduire

```
cd <workspace>/work/decors_sfa2/export
OUT=gfx/gfx_region.bin ./mame.sh lua/dump_gfx.lua                 # région :gfx (une fois)
STG=00 OUT=cap/explore_00.txt ./mame.sh lua/explore.lua            # partie -> sta/sfa2u/combat_00.sta
./capture.sh 00                                                    # 6 passes -> rec/00/
./py3 py/verif_iso.py 00                                           # contrôle rendu direct
./py3 py/build_world.py rec/00/full.rec work/monde_00.pkl          # recollage
./py3 py/export_sfa2.py --decor 00 [--sans-psd]                    # export + contrôle monde
./py3 py/mesures.py 00                                             # bornes, parallaxe, rowscroll, anneau
./py3 py/sprites_decor.py 00                                       # objets sprites + contrôles sprites/écran
POS="0,C0,180,0:16,C0:16,180:16,C0:48,C0:96,C0:-16" ./pose_camera.sh out/decor00/references
```
Variables de `rec_sfa2.lua` : `PATH_C`, `SPEED` (4), `GAP` (96), `CUPX` (32), `CUPX2` (80), `CDN` (16), `SNAPP`,
`ISO` (0-4), `REC`, `OBJ`, `SCR`, `ST`.

## 11. Limites

- Décor forcé par `$FF8100` (adversaire Guy) : décor complet et cohérent, pas le chemin « naturel » du mode arcade.
- Course Y réelle limitée aux sauts de Ryu (16 px haut) ; au-delà (−96/+16) caméra **forcée** : le contenu des
  plans y est exact (rendu = MAME) mais ce n'est pas une position que le jeu atteint seul ; au-dessus, scroll2
  est transparent (ciel de scroll3) et sous −16 px le décor s'arrête.
- Image monde = palette d'une image de référence calme (pas de flash).
- Corbeau : objet RAM non identifié (hypothèse : enregistrement 2 de la liste) ; nuages : formule Y en fonction
  de l'Y d'instance non établie (seule la parallaxe 1/4 et les dérives X sont mesurées).
- Les sprites de décor ne sont pas « recollés » en monde : formules de position + images assemblées + poses.
