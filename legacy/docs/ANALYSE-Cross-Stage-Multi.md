# Cross-Stage Hyper SFA — Analyse pour le BUT FINAL : tous les stages (perso → stage maison)

> Objectif réel : chaque perso de Hyper (zero9) joue sur son **stage maison**, repris d'Upper (zero5).
> ~15-20 stages à gérer, pas un hack mono-stage. Cette analyse évalue toutes les voies dans cette optique.
> (Le mono-stage est déjà **prouvé rendable** : savestate 10 = tilemap Upper composée correctement à
> l'écran. Donc le pipeline RE+injection fonctionne ; la question ici est l'ARCHITECTURE scalable.)

## 1. Contrainte fondamentale (mesurée, 2026-06-28)
- **Bank tuiles résidente zero9 = 2.98 Mo (e546), PLEINE à 99.7%** : 287 tuiles libres / 93184, aucun
  bloc contigu > 16 tuiles. → **Impossible d'AJOUTER un stage en résident** ; on ne peut que *remplacer*.
- zero9 a **3 stages RÉSIDENTS** (toujours en RAM), **PAS de loader de stage** (≠ zero3/zero5 qui en ont
  beaucoup et les **streament**). C'est l'architecture qui bloque le multi-stage, pas la place ISO.
- Tuiles/strips/index/palette sont **PARTAGÉS** entre système / HUD / menus / les 3 stages. Tout overwrite
  résident touche du partagé → c'est pourquoi le e546 *sparse* a cassé menus+HUD (tuiles système mises à 0).
- **RAM LIBRE confirmée : 0x1580000–0x19d0000 = 4.4 Mo**, vide dans TOUS les dumps testés (combat, stage3,
  s10…). Assez pour charger un stage entier (tuiles ~2 Mo + tilemap + palette).
- **La base bank est un POINTEUR data** (`[0x1dc078]+0x34` = `0x1dc2e4` = 0xdb4000), pas une constante :
  aucun builder lui/addiu de 0xdb4000 dans le code. Le drawer lit ce pointeur à chaque frame.
  ⇒ **repointer la bank = un write data, le drawer suit. Trivial.** (linchpin du loader)

## 2. Les 5 options (questions de Rickow) évaluées POUR TOUS les stages

### Option 1 — Bake dans le fichier compressé (overwrite résident) = ce que j'ai fait
- ✅ Marche pour démontrer 1 stage. ❌ **Ne scale pas** : bank pleine → ne peut que remplacer les 3 stages
  existants (donc 3 stages MAX), et chaque remplacement corrompt du partagé (overlay limite la casse mais
  ne l'élimine pas ; sparse casse tout). Pour 15-20 stages c'est mort.
- Verdict : **outil de démo, pas l'architecture finale.**

### Option 2 — Loader depuis l'autre jeu (charger par match) = ⭐ LA solution
- Par match, après char-select : charger le stage du perso dans la **RAM libre 0x1580000**, puis **repointer**
  la bank (`0x1dc2e4`) + la source tilemap + la palette. **Résident JAMAIS touché → zéro corruption,
  nombre de stages ILLIMITÉ.** C'est exactement comme les persos se chargent par match.
- Reuse le file-loader + décompresseur MWo3 du framework (le jeu sait déjà charger/décompresser des fichiers AFS).
- Verdict : **la seule voie qui atteint le but final.** Le reste sont des briques de celle-ci.

### Option 3 — Réécrire l'index pour gérer plus
- Seul, inutile : la bank est pleine, un meilleur index n'ajoute pas de place résidente.
- MAIS **brique nécessaire du loader pour la TILEMAP** : le drawer compose la tilemap depuis des *strips +
  table d'index* (format CPS2 colonnes). Pour un stage chargé, il faut soit (a) écrire ses strips+index dans
  une zone scratch par-match, soit (b) étendre/repointer l'index vers la tilemap chargée. → à décompiler (opt 4).
- Verdict : **composant du loader**, pas une solution autonome.

### Option 4 — Décompilation supplémentaire pour sécuriser
- **OUI, nécessaire** pour dérisquer le loader. À décompiler (4-5 fonctions) :
  1. **Source tilemap** : qui lit les strips/index (base 0x644000 / table 0x660240) — hardcodé ou pointeur ?
     décide entre scratch-par-match vs repoint.
  2. **File-loader du framework** : la fonction qui charge un fichier AFS + lance MWo3 → à appeler depuis le cave.
  3. **Point de hook** : où injecter le load (après char-select, avant montage du stage).
  4. **Palette** : localisation + repoint (source + buffer GS).
- Verdict : **étape obligatoire avant de coder le loader.** Faisable (pyghidra opérationnel).

### Option 5 — Changer la compression de l'archive
- ❌ **Ne résout pas le problème.** La contrainte est la **RAM** (le stage décompressé doit tenir dans un
  buffer RAM) et le pipeline de rendu — PAS la compression ni la taille ISO (4.7 Go, large).
- MWo3 est le codec **du jeu**, décompressé par SON code (IOP `FUN_148698`). Le remplacer = injecter un
  nouveau décompresseur dans le jeu (gros travail) pour **zéro bénéfice** sur la RAM/streaming.
- Le streaming runtime lit depuis la RAM **déjà décompressée** → le codec n'affecte pas le streaming.
- Techno PS2-era : LZSS (= MWo3 lui-même), Huffman, RLE, IPU (MPEG, vidéo only). Homebrew LZ4/zlib :
  inutilisables sans embarquer leur décompresseur dans le jeu. MWo3 (LZSS) est déjà rapide à décoder.
- Verdict : **à écarter** (sauf si un jour on veut réduire la taille ISO, ce qui n'est pas le besoin).

## 3. Architecture recommandée (loader par match, but final)

```
BUILD-TIME (offline, par stage) :
  Pour chaque stage maison d'Upper :
   1. Capturer le stage (savestate Upper sur ce stage, OU décoder la source zero5 byte-encodée).
   2. Extraire {tuiles référencées, tilemap 4 couches, palette}.
   3. REMAP les tuiles vers des indices COMPACTS (0x1..N) + réécrire la tilemap → buffer tuiles ~80-300 Ko
      au lieu de 2 Mo (au lieu d'indices épars jusqu'à 0xfffe). Rend le load léger.
   4. Compresser (MWo3) en un "package stage" ; ajouter à l'ISO (nouveaux fichiers AFS en fin, ou région
      appendée). Place ISO = illimitée.
  + table perso → stage maison (mapping ~30 persos → ~15-20 stages).

RUNTIME (cave, par match) :
   1. Hook après char-select : lire le perso → stage maison ID.
   2. Appeler le file-loader du framework : charger le package dans 0x1580000 (tuiles), +zone tilemap, +palette.
   3. Repointer : bank 0x1dc2e4 → tuiles chargées ; source tilemap → strips/index chargés ; palette → chargée.
   4. Le drawer/composeur rendent le stage chargé. Résident intact.
```

**Pourquoi ça marche / pourquoi c'est propre :**
- Repoint bank = trivial (pointeur data, vérifié).
- Résident jamais modifié → menus/HUD/système/persos intacts (le bug du sparse disparaît par construction).
- 1 seul stage en RAM à la fois (le courant) → tient large dans 4.4 Mo. Stages illimités côté ISO.
- Réutilise le décompresseur du jeu → pas besoin de toucher la compression (option 5 inutile).

**Risques / inconnues à lever (= option 4) :**
- Repoint de la **source tilemap** (le maillon le moins trivial — bank OK, tilemap à confirmer).
- Trouver/appeler le **file-loader** proprement (timing, DMA IOP→EE).
- **Palette** : repoint + format.
- Le **hook** char-select sans casser le flux (technique cave data-redirect déjà maîtrisée = arcade mode).

## 3bis. CONFIRMATION RE (2026-06-28) : le rendu de stage est 100% pointer-driven en DATA
- `FUN_21fcfc` câble un **descripteur de stage** (`0xbe2180` : +0=source `0xb90000`, +4 params, dims 64×16…)
  dans la struct BG via `[0x1dc078]+0xd0..0xe8`. `FUN_22daa4` pose ces valeurs (toutes en data).
- Struct BG (`0x1dc2b0`) entièrement à pointeurs : **+0x34 = base bank** (tuiles), **+4 = tilemap**,
  **+0xd0..0xe8 = source/scroll** (→ descripteur 0xbe2180). Table buffers `0xb84130` (0xba0000/4000/8000/c000).
- ⇒ **Aucune adresse de stage n'est codée en dur dans le chemin de rendu** : bank ET source tilemap ET scroll
  sont des **pointeurs data**. Le loader n'a qu'à écrire ces pointeurs vers la zone chargée — **zéro patch
  code dans le pipeline de dessin** (le cave ne sert qu'au hook de déclenchement du load). Les 2 linchpins
  (bank + tilemap) sont donc **confirmés repointables**. Risque rendu du loader ≈ levé.
- Reste à décompiler côté LOAD (pas rendu) : la fonction qui charge un fichier AFS mid-game (réutiliser le
  loader de PERSOS, qui charge déjà des tuiles par match dans 0x108c000+) + la palette.

## 3ter. CONFIRMATION RE (2026-06-28) : le LOAD est aussi réutilisable (queue framework)
- `FUN_154db0` = machine à états de chargement **pilotée par une FILE de requêtes** à `0x1a2440` (entrées de
  0x40 octets, index courant `0x1a2454`, flag "non-vide" `0x1a2450`). Entrée = {*+0:flags, +1/+2:id fichier,
  +4:src, +6:dst, +8:filename}. Charge async (func 0x1292e8/0x1298d0), poll (0x129bb0==2 busy), puis sur
  complétion **si flags&0x40 → `FUN_148698` décompresse MWo3 src→dst** ; avance la queue.
- `FUN_151f40` = enregistre les segments décompressés (table `0x1a1400`, 0x208/slot, tags 'M'/'O').
- ⇒ **Charger un stage = ENFILER une requête** {flags=0x40, id du package stage, dst=0x1580000} dans la queue
  0x1a2440 + `0x1a2450=1`. Le framework charge + décompresse tout seul. **Pas besoin d'écrire un loader.**
- Les DEUX côtés sont donc réutilisables : **LOAD = enqueue (data) ; RENDER = repoint pointeurs (data)** ;
  le cave ne sert qu'au petit hook (lire perso→stage, enfiler, repointer au bon moment). Risque global ≈ levé.

## 4. Plan d'attaque par étapes (vers le but final)
1. **Décompiler les 4-5 fonctions clés** (opt 4) : source tilemap, file-loader, hook char-select, palette.
2. **Prototype loader 1 stage** : charger le package Upper dans 0x1580000 + repoint (bank d'abord, puis
   tilemap, puis palette). Valider le rendu SANS toucher le résident (≠ l'overwrite actuel).
3. **Pipeline build-time par stage** : capture + remap compact + package + ajout ISO.
4. **Boucler sur tous les stages** + table perso→stage maison.
5. Polissage (transitions, palette par stage, scroll).

## 5. État actuel (mono-stage, pour mémoire)
- Démo mono-stage : rendu Upper prouvé (savestate 10). Outils prêts : `mwo3_codec.py`, repack X_DATA in-place.
- e546 *overlay* (préserve système+HUD, corrige le bug sparse) construit mais **dépasse la région in-place de
  ~128 Ko** (e544+111K + e546+17K) → nécessiterait un rebuild ISO complet. **Non prioritaire** vu le pivot
  vers le loader : la démo a déjà prouvé le rendu, on bascule sur l'archi scalable.
- Dumps/outils : `ee_upper_combat.bin` (zero5 Upper), région libre 0x1580000, pointeur bank 0x1dc2e4.
```
```

## 6. ⭐⭐⭐ COMPOSER DU RING ENTIÈREMENT DÉCODÉ (2026-07-04) — v7 = 100% DATA, format prouvé octet par octet

### Architecture d'exécution (qui compose quand)
- `FUN_296750` = **coroutine maître BG** (spawnée via `FUN_22f660`, entry posée dans SPR+0x1100=0x296750 par
  `FUN_22ec20`) : boucle infinie → dispatch état `u16[0xb88000]` via table `0x5b6320` (états 0-8 → 0x296800,
  0x2968a0, 0x2968e0, 0x296930, 0x296980) → yield `0x22fab0`.
- État 8 (`FUN_296980`) spawne la **tâche composer** `FUN_2518c0` (+ `0x2500b0`).
- `FUN_2518c0` = boucle composer : dispatch `u16[0xb88000]` via **table `0x5b41c0`** → puis `0x252150`
  (si octets dirty ctx+0x62/0x63 → re-clear + respawn upload) → `0x57e890` → yield.
  - **`[0xb674f8] != 0` → état forcé 6 = FULL RE-LAYOUT + recompose + réupload** (+ pose 0xfe dans 2 octets
    dirty). C'EST LE LEVIER "force refresh" pour un pnach post-load.
- Sous-états par stage : `FUN_251c90` dispatch `u16[0xb88004]` via table `0x5b41d8` ; `FUN_252390` dispatch
  `u16[0xb88008]` via `0x5b41e8` (les triples 0xb88004/8/c du diff savestates = positions dans ces machines).
- Scroll = PAS de recompose : `FUN_2524f0` anime `ctx+0x28 (-=0x100 &0x3ff, toutes les 6 frames via ctx+0x16)`.
  Le ring est composé UNE FOIS au layout ; le décor scrolle par registres. (⇒ le "pile incohérente" v6 =
  on écrivait le ring APRÈS l'upload unique.)
- `FUN_57ab50` = clear+schedule des buffers (0xba4000 p=0x20, 0xba8000 p=0x1020, 0xbac000, 0xbb0000 UI).

### Format des données (PROUVÉ par recomposition offline = match 1024/1024 et 256/256)
- **SCR2 : pool de pages à `0x640960`** (17 pages max jusqu'à 0x643c60). Page = **0x300 octets =
  u16 tiles[256] (+0) puis u8 attrs[256] (+0x200)** = 16×16 cellules. Composée par `FUN_505ab0` en paires
  {u16 tile**+0x1000**, u16 attr} → bloc ring de 0x400.
- **SCR3 : pool de pages à `0x643c60`** (~30 pages jusqu'à ~0x6452e0). Page = **0xc0 octets = u16 tiles[64]
  (+0) puis u8 attrs[64] (+0x80)** = 8×8 cellules. Composée par `FUN_505ef0`, sans offset, bloc ring 0x100.
- **Ring SCR2 = 0xba4000-0xba7fff** (16 blocs 0x400 = grille 4×4 pages = 64×64 tuiles) ;
  **ring SCR3 = 0xba8000-0xbbffff** (64 blocs 0x100). Versus dump : SCR2 = page0×12 + [4,1,2,3] (bande sol),
  SCR3 = [0e 0f 10 11 12 13 19 19 14 15 16 17 18 0 ...]. SCR1 0xba0000-0xba3fff = vide (0x20) en combat.
- **Wrappers data-driven** : `FUN_5059f0`/`FUN_505e4c` composent une **LISTE DE BYTES de sels de pages**
  (SPR+0x1110=ptr liste, +0x1140=count) → le layout d'un stage est une simple liste d'octets.
- **⭐ DESCRIPTEUR DE LAYOUT DU STAGE VERSUS trouvé à `0x695ff4-0x6960a0`** (blob e544, données pures) :
  header u16 `02 00 02 00 08 00 0c 00 10 00 10 00`, plusieurs listes SCR2 de 16 bytes
  (`0x696018` = [0×12,4,1,2,3] ; variantes à 0x696004/0x696028/0x696038), quads u16 de scroll
  (`08 00 18 00 28 00 28 00`, `08 00 48 00 88 00 88 00`), **liste SCR3 64 bytes à `0x696050`**
  (+ copie à `0x696090`).
- SOL/rowscroll (0xbac000+) = module `0x250xxx` par frame : `FUN_250a90` dispatch `[0xb88138]` via
  `0x5b41b0` → paires (ctx couche 0xb88400/800/c00/1000 → dst 0xbac000/0a0/140) via `FUN_250d50`
  (pages 0x3c0 table `0x6452e0`) ; + strips `0x65f820/0x65f980/0x661660/0x663a80/0x665ea0` indexés par
  rotation `ctx+0x128`, et tables `0x660240/0x661e60` indexées par `stage_sel(0xb84178)+[0xb88100]`.

### Plan v7 (tout data, zéro patch code rendu)
1. **Package v7** : pools Upper (SCR2 pages ≤17 dédupliquées ; SCR3 ≤30 dédupliquées — si ça déborde,
   patcher les constantes de base pool dans FUN_505ab0/505ef0 (code blob zb) vers la zone package) +
   listes de pages (16B + 64B) + quads scroll + strips SOL + bank complète v6 + palettes v6.
2. **Injection** : slot 11 charge le package (en place) → pnach (puis zb bake) : memcpy pools sur
   0x640960/0x643c60, listes sur 0x696018/0x696050 (+ scrolls), strips SOL, puis **`0xb674f8=1`** →
   le jeu re-layoute, re-compose, ré-uploade, scrolle et anime NATIVEMENT.
3. Bank tuiles + palettes = déjà résolus en v6 (repoint 0x1dc2e4 + rangées 32-127 → 0x1dc400+/twin).
4. Multi-stage : table perso→stage pose le file_ref du slot 11 + les writes ci-dessus par stage.

Décompilations : `ghidra_sfa3\out\v7\FUN_*.c`. Scripts session : gh_v7_bgupdate.py, gh_v7_b.py, gh_v7_c.py.
