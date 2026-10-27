# Projet — SFA Anthology PS2 : Widescreen 16:9 + Ajout de décors (tiles) — **tous les jeux**

> Doc de **reprise propre** consolidé. Objectif Rickow : le 16:9 **et** l'extension
> de décor (ajout de tiles / cross-stage) doivent viser **tous les jeux de la
> compilation Anthology PS2**, pas seulement Hyper.
>
> Renvois détaillés (dans `E:\CLAUDE CODE\hyper_re\`) :
> `PROJET-Hyper-Widescreen.md` (pipeline GS §7) · `ANALYSE-Widescreen-ISO.md`
> (pourquoi baker dans l'ISO) · `ANALYSE-Cross-Stage-Multi.md` +
> `CAVE-Loader-Design.md` + `LOADER-Implementation-Spec.md` (loader/tiles) ·
> `PROJET-Hyper-Arcade.md` (mode arcade, même binaire).

---

## 1. La compilation (structure commune)

- **Un seul binaire PS2** : `SLUS-21317` (CRC `72CE7A78`). Tous les jeux tournent
  dans **le même moteur** « CPS2 recompilé en MIPS R5900 » → **le pipeline de rendu
  GS est partagé** (clé pour « tous les jeux » : un patch viewport touche tout le
  monde d'un coup).
- Données jeux = **10 conteneurs MWo3** dans `X_DATA.BIN` (archive **AFS**),
  décompressés en RAM à la volée (streaming). Noms internes `zeroN_usa.bin`.

| AFS | Conteneur | Jeu | Note |
|---|---|---|---|
| e203 | `zb` | BIOS/boot CPS2 commun (41 Ko) | **code moteur partagé + descripteurs** |
| e206 | `zero1` | SFA1 (Warriors' Dreams) 1995 | |
| e224 | `zero2` | SFA2 / SFZ2 1996 | |
| e253 | `zero3` | **SFA3 / SFZ3** 1998 | base arcade |
| e348 | `zero4` | SFA2 Gold / Alpha2' 1996 | |
| e350 | `zero5` | **SFA3 UPPER (Zero3 ↑)** 1998 | ⭐ meilleure cible widescreen ; source des stages cross-stage |
| e526 | `zero6` | SFA2 variante (ZERO2ALP) 1996 | conf. moyenne |
| e536 | `zero7` | Super Gem Fighter / Pocket Fighter 1997 | |
| e543 | `zero8` | SFA2 variante 1996 | conf. moyenne |
| e544 | `zero9` | **HYPER SFA** 1998 (3,5 Mo) | le + gros ; chargé au mode Hyper |

- Mapping adresses 68K→EE : `addr_EE = addr_68K − 0x470000`. Base globale par jeu
  `A5` (Hyper = `0xb88000`), lue au scratchpad EE `0x70000000+0x1114`.

---

## 2. Le moteur de rendu (partagé, dans le binaire SLUS / zb)

Pipeline BG (adresses SLUS, valables tous jeux — vérifiées sur Hyper) :
- **Frame BG** `0x1d0750` → **orchestrateur** `0x1d0854` (boucle 4 couches, modes
  `desc+0x8c+L*4`) → **sélecteur de bande scanline** `FUN_1d0e90(y)` → `[0x1dc070/74/78]`.
- **Drawers** : `0x1d18a0` (SCR1 8×8, qwc2) · `0x1d1ed0`/`0x1d1da0` (SCR2 16×16 bank,
  qwc8, rowscroll) · `0x1d25c0` (SCR3 32×32 conteneur segmenté, **qwc=0x20**) ·
  `0x1d2840`/`0x1d2dc0` (objets/sprites, liste SPR `0x70002000`).
- **Viewport / render-target** : `FUN_14afd0` pose largeur **384** (`0x180`) →
  descripteur `[0x1ae448]+0x494` ; `FUN_14a550` = render-target (FBW=w/64) ;
  `FUN_14a740` = centrage `(0x1000−dim)/2`.
- **Décompresseurs** : `0x148698` (MWo3 mot-LZSS — ⚠️ **boucles de copie en DO/WHILE** :
  tout token à longueur étendue 0 = runaway 65536+ mots = crash `FQC=0 VIF FIFO` ; ne
  JAMAIS en émettre, valider avec `mwo3_splice.decompress_strict`) · `0x148778`
  (byte-LZSS : ctrl 8b MSB, token off=(b>>4)+1 / len=(b&0xf)+2).

Décompilés disponibles : projet pyghidra `dump` sur `eeMemory_versus.bin` →
`E:\CLAUDE CODE\ghidra_sfa3\out\v7\FUN_*.c`.

---

## 3. AXE A — Widescreen 16:9 natif — ✅ **LIVRÉ (v10, 2026-07-12)**

**ÉTAT : FONCTIONNEL, validé in-game sur Upper** (décor rempli des 2 côtés, action/HUD
centrés, persos alignés au sol). **Patcher autonome : `hyper_re\sfa_anthology_ws_patcher.py`**
(codec MWo3 + compresseur DP embarqués, table de patches tolérante vanilla/All-Unlocked,
vérifs octet-à-octet + round-trip + readback). Usage :
`python sfa_anthology_ws_patcher.py SRC.iso [DST.iso]`. ISO livrable :
`SFA Anthology [Widescreen] (USA).iso` (sortie vérifiée bit-identique à la v10 testée).

### ⭐ La découverte centrale : le modèle « RING » (remplace le plan S1/S2 initial)
- Chaque couche BG lit une **tilemap-RING circulaire recomposée autour de la caméra** :
  8px = ring 512px (`&0x1ff`), 16px = ring 1024px (`&0x3ff`), 32px = adressage direct.
  En 4:3 la fenêtre composée laisse **~58-62px de marge de chaque côté** de la vue.
  ⚠️ Le wrap d'adresse n'est PAS « la fin des tiles » (l'approche « stop au wrap » = escaliers, abandonnée).
- **LE FIX = recentrer la vue élargie dans la fenêtre composée** :
  (a) lecture tilemap **Xstart −= 32px** (caves sur les `lw` Xstart des drawers BG) ;
  (b) **sprites/HUD/objets +32px écran** (caves sur les X init des 2 drawers sprites).
  → l'extension 64px se répartit 32px gauche + 32px droite. = l'équivalent exact du
  « +48 émetteur / hooks Xstart » du patcher PSP [[project-sfa3max-streamer]].
- **Sol = cas spécial** : il passe par une **passe rowscroll par scanline = BLIT GS par ligne**
  (`FUN_1d1da0` → templates `FUN_1d3860`, update TRXPOS `FUN_1d3960`) dont la **largeur est
  câblée TRXREG RRW=384** (`addiu t6,zero,0x180` @`0x1d38d4`) → élargie à 448. C'était le verrou final.
- Le « décalé à gauche global » (menus inclus) n'était PAS un problème d'affichage : les menus
  CPS2 sont des tilemaps des mêmes drawers. Le site de centrage FUN_14a740 (0x14b0a0) = hors sujet.

### Carte des couches (kill-test in-game, stage Upper temple)
| Drawer | Couche | Fix appliqué |
|---|---|---|
| `FUN_1d1810` → 1d18a0/1d1a00 (8px) | **le ciel** | templates 49→57 (`0x1d17b0`), buffers relogés, Xstart−32 |
| `FUN_1d1da0` → 1d1ed0/1d2080 (16px) | **le sol + arbres devant** | counts 25→29, Xstart−32, **blit scanline 384→448** |
| `FUN_1d23c0` → 1d25c0 (32px) | **cascade + montagne derrière** | templates+drawer 13→15, buffers relogés, Xstart−32 |
| `FUN_1d2dc0` | **le temple** (objets) | X écran +32 (@`0x1d2ef8`) |
| `FUN_1d2840` | **persos + interface** | X écran +32 (@`0x1d292c`) ; ⚠️ NE PAS killer (crash) |

Méthode kill-test : écrire `jr ra ; nop` (0x03e00008, 0) à l'entrée du drawer via PINE, observer,
restaurer. ⚠️ Ne PAS faire clignoter un poke de code (crash) ; ne PAS forcer le re-init
`[0x1dc2b0]=0` en live (freeze — les templates se reconstruisent au chargement de stage naturel).

### Architecture rendu élucidée (sert AUSSI à l'arcade et au cross-stage)
- **Templates pré-bakés** : à l'init one-shot (flag `[0x1dc2b0]`), `FUN_1d1250/1d1720/1d1c60/1d22d0`
  construisent des paquets GIF **pré-remplis avec coords écran fixes** (0x100 o/tuile) dans des
  buffers par couche ; les drawers per-frame n'y écrivent que le ptr GFX (`FUN_1d3850`) + palette
  (`FUN_1d3d80`). `FUN_1d36a0` = DMAtag CALL vers le buffer de couche (RET en fin, compte figé →
  ne JAMAIS bumper un count sans son template).
- **Table des buffers de couche = STATIQUE dans zb @`0x1dbcf0`** : 8px=[+0/+4], 16px=[+8/+c],
  32px=[0x1dbd00/+4], scanline=[+8/+c], principal=[0x1dbd10/+4] (double-buffer, parité frame
  `[struct+0x114]`). Buffers packés au juste 4:3 → pour agrandir : **REPOINTER vers la RAM libre**
  (pure data), pas étendre en place.
- **Frame BG** : `FUN_1d0750` (init/orchestration) → `FUN_1d35b0` (reset ptr paquets [struct+0x118] ;
  buffer principal 0x9ee80/frame = énorme marge) → drawers → `FUN_1d40b0` (FRAME/SCISSOR/XYOFFSET,
  relit [+0x494]) → `FUN_1d47d0` (kick DMA + swap). Struct maître `[0x1dc078]`=0x1dc2b0.

### Table des patches v10 (référence rapide — vérité = le patcher)
- **SLUS (S1)** : `0x4ae28`/`0x4b270`/`0x4b2a0` : 0x180→0x1c0 (fileoff SLUS ; ISO = +0x13e000).
- **zb** : unlock ×4 (`0x1c8e58/74/90/ac`) · reloc 8px `0x1dbcf0`→0x1580000, `0x1dbcf4`→0x15F0000 ·
  templates 8px `0x1d17b0` 0x31→0x39 · counts 8px `0x1d19b0`/`0x1d1b9c`→0x39 · counts 16px
  `0x1d1f7c`/`0x1d2140`/`0x1d223c` 0x19→0x1d · reloc 32px `0x1dbd00`→0x1660000, `0x1dbd04`→0x1680000 ·
  32px `0x1d2360`/`0x1d2774` 0xd→0xf · **blit sol `0x1d38d4` 0x180→0x1c0** · intercepts→caves :
  `0x1d18ec`/`0x1d1a84` (ciel, lw d4), `0x1d1f2c`/`0x1d20e4` (sol, lw d8), `0x1d2644` (cascade, lw dc),
  `0x1d292c`/`0x1d2ef8` (sprites X+32) · **caves @`0x1d7e90/eb0/ed0/ef0/f10/f30/f50`**.

### Reste à faire (mineur)
1. **Bugs sur certains écrans hors combat** (constat Rickow, à inventorier — suspect n°1 : le +32
   sprites sur des écrans qui n'en veulent pas ; candidat fix = gater le +32 selon le mode).
2. **Petit bout de ciel wrappé au bord EXTRÊME de la course caméra** (la fenêtre composée est
   clampée au bord du monde → plus de marge pour le −32 ; candidats : clamp du shift près des
   bornes, ou élargir la compo côté composer).
3. **Tester les autres jeux zeroN** (zb partagé → le patch est actif dans TOUS les jeux ; vérifier
   stage par stage : zero3, zero2/4/6/8, zero1, zero7).
4. Pop éventuel d'objets aux bords (cull logique 4:3 en amont : demi-largeur `0xc0`, clamps `0x17f`).

---

## 4. AXE B — Ajout de décors / tiles (cross-stage & monde complet)

Deux besoins liés : (a) **combler la zone morte** que le 16:9 révèle quand un stage
n'a pas assez d'art ; (b) **porter des stages** d'un jeu à l'autre (ex. décors Upper
dans Hyper).

### ⚠️⚠️ CONFLITS À GÉRER (maj 2026-07-19, post-bake ARCADE) — LIRE AVANT DE COMBINER
1. **RAM libre partiellement ALLOUÉE par le widescreen** : les buffers de templates relogés
   occupent désormais **~0x1580000–0x1660000** (8px ×2, 0x67500 chacun @0x1580000/0x15F0000)
   **+ ~0x1660000–0x1690000** (32px ×2 @0x1660000/0x1680000). Or le LOADER cross-stage utilisait
   **dst=0x1580000 / staging=0x1700000** (slot 11 du descripteur v8) → **COLLISION avec les buffers
   8px**. Pour combiner : déplacer le dst du loader (ex. ≥0x1700000) ou re-répartir. **RAM restante
   réellement libre ≈ 0x1690000–0x19d0000 (~3,4 Mo)** (staging 0x1700000 et section V7PG 0x186a000
   du chantier Hyper y vivent déjà — cartographier avant d'allouer).
2. **Caves zb 0x1d7e90–0x1d7f6x = OCCUPÉES par le widescreen** (7 caves). Le doc cross-stage
   proposait « cave render bake @0x1d7e90 (384 o libres) » → **CADUC**. Espace cave restant dans zb :
   zéros après 0x1d7f70 (à re-vérifier), sinon reloger. ⚠️ Le padding de FIN du SLUS (ex. 0x18b60c)
   n'est PAS file-backed (BSS) → inutilisable pour des caves ; le milieu du SLUS (trous zéros
   file-backed, cf. scan) reste candidat.
3. **CRC de l'ISO patchée SLUS = `72CE7A38`** (≠ 72CE7A78) → les pnach `_72CE7A78` ne s'appliquent
   plus. L'arcade existe en pnach `_72CE7A38` ET en bake. ⚠️ Le bake arcade ne change PAS le CRC
   (X_DATA seul modifié) → les gamesettings/cheats sont COMMUNS à l'ISO widescreen et à l'ISO
   widescreen+arcade.
4. **⚠️ LES PNACH CORROMPENT LES AUTRES JEUX (vérifié 2026-07-19)** : les adresses zero9 du pnach
   arcade (`0x5b5e9c`, `0x5c55dc`…) contiennent du **CODE MIPS dans Upper/z5** — les écritures
   per-vsync écrasent des instructions des autres jeux du disque. Le pnach cross-stage a le même
   problème potentiel (`0x290834` = code zero9 ; `0x1d0750` = code zb partagé par tous les jeux !).
   → Ne cocher un cheat que pour le jeu qu'il vise, ou BAKER (la voie propre).
5. **Caves zero9 FILE-BACKED (bake)** : le prog e544 décompressé (0x977200 o) mappe
   **offset fichier = EE − 0x1F0000** (validé 3000/3000) ; la zone pnach 0x1c0000 n'est PAS dans
   le fichier. Deux zones de zéros file-backed vierges au runtime identifiées :
   **`0x5CEF00–0x5CF300`** (0x410 o — **occupée 0x5CEF00–0x5CF108 par le bake ARCADE**, reste
   ~0x1F0) et **`0x5D16F0–0x5D1B00`** (0x410 o, LIBRE — candidate pour le bake cross-stage).
   Marge restante du slot AFS e544 : **880 octets** compressés.
6. **Synergie modèle RING** : la « fenêtre composée ±60px autour de la caméra » du widescreen est le
   MÊME mécanisme que le composer z5/z9 du cross-stage (recomposition des colonnes au scroll). La
   passe rowscroll du sol (blit par scanline `FUN_1d1da0`/`1d3860`/`1d3960`, table `[bande+0x110]`)
   et la carte des couches (§3) s'appliquent telles quelles au chantier monde z5.

### Architecture LOADER data-driven (la voie retenue, cf. `ANALYSE-Cross-Stage-Multi.md`)
- Chargement Hyper = **machine à états à handlers**, table `0x1d4980`, step courant =
  byte `0x19e441`. Étape **WALKER `FUN_1c94a0`** : itère **12 slots FIXES** de 0xc
  octets à `desc+0x14+n*0xc` ; entrée `{u16 type, u16 file_ref, u32 dst, u32 staging}` ;
  `file==0` → slot sauté ; type 2/4 = load compressé→staging puis `FUN_148698` ;
  type 1/3 = brut→dst.
- **Descripteur version v8 (Hyper) = `0x1dbc30`** (dans **zb**, offset `0x13c30`).
  **Slot 11 (`desc+0x98`) = tout zéro = slot d'insertion libre.**
- **Insérer un stage = pure data** : slot 11 = `{2, <index AFS>, 0x1580000, 0x1700000}`
  (RAM libre `0x1580000–0x19d0000` = 4,4 Mo, vide dans tous les dumps). Le framework
  charge+décompresse tout seul (aucun hook code requis pour le LOAD).
- **API alternative** : `FUN_154c9c(id1,id2,src,dst)` (enqueue async, poll `0x1a2450==0`) ;
  `FUN_154b00(0, INDEX_AFS, buffer)` (read **synchrone** — ⚠️ **jamais en plein rendu** :
  crash `FQC=0 VIF FIFO`).

### Rendu = repoint de pointeurs (data-driven)
- Bank de tuiles : `[0x1dc2b0]+0x34 = 0x1dc2e4` → repointer vers `0x1580010`.
- Conteneurs classes 5/6/7 : `0x1dc2f4/f8/fc` (repoint per-frame en combat).
- Tilemap → `memcpy` vers `0xba0000`. Descripteur bande `0xbe2180`, table buffers `0xb84130`.

### Format package (build-time)
- 1 stage packagé = tuiles + tilemap + palette, indices **remappés compacts**
  (0x1..N au lieu d'épars) → `E:\tmp\stage_upper_pkg.mwo3` (65 Ko ; ~15-20 stages ≈ 1,2 Mo)
  + `stage_upper_remap.json`. Inséré comme **fichier AFS 553** (`X_DATA+0x10000`, TOC count 554).
- Recompression — **choisir selon la taille du fichier (maj 2026-07-19)** :
  - **petits fichiers (≤ ~100 Ko, ex. zb)** : `anthology_extract\compress_opt.py` (parse optimal
    DP, réécrit 2026-07-12) — taille ≈ encodeur original, gère les caves en zones de zéros.
  - **gros fichiers (e544 = 9,9 Mo : compress_opt = >20 min sur 3 Mo, INUTILISABLE)** :
    **`anthology_extract\mwo3_splice.py`** = recompression **chirurgicale par splice** (2026-07-19,
    éprouvée par le bake arcade : 0,7 s, +604 o). La fenêtre LZSS 0x7FF mots rend la compression
    locale : on ré-encode seulement les clusters modifiés (+0x800 mots de marge aval), tranche
    re-sérialisée maison en scindant des matchs (L→L1+L2 même offset) jusqu'à un multiple de 16
    entrées pile (frontière ctrl exacte, sans token FIN), couture avec le flux original.
  - ⚠️ **LEÇON (crash in-game splice v1)** : le décodeur RÉEL `FUN_148698` copie en **do/while**
    → longueur étendue 0 = runaway. Ne jamais valider un flux avec son propre codec : utiliser
    **`mwo3_splice.decompress_strict`** (émulation fidèle du do/while, refuse L=0).
  - Diagnostic des autres encodeurs : `patch_reemit` = OK mots isolés mais **casse sur cave en
    zero-run** ; `mwo3_codec.compress` (greedy) = trop gros ; `comp_test.py` = **buggé**.
  ⇒ règle : **compress_opt (petit) ou splice (gros) + assert `decompress_strict(C)==attendu` +
  assert taille ≤ slot.**

### Chantier Hyper (le stage Upper Blanka) — état actuel
- **v7.30 livré** (cave 490 instr, fin `0x1c0ba8`, pnach 636 patches) : repoint conteneurs
  + **routine de parallaxes** (le versus z9 n'applique pas les parallaxes du stage →
  couches désalignées + fenêtres hors-données = le « fond noir »). Préflight émulateur OK.
- **Verdict monde (2026-07-12)** : **nos données z5 sont COMPLÈTES** (union des rings aux
  3 caméras = 0 cellule manquante). La zone morte vient de la **caméra versus z9 qui sort
  de la course native du stage** (mesuré Blanka : scroll SCR1 X ∈ `[0x152,0x1ae]`, 92 px).
- **Décision Rickow** : porter le **layout complet du monde z5** (fondation multi-stage)
  plutôt que brider la caméra. Structures natives z5 localisées (ctx couches `0xa08000+L*0x400`,
  tables strips `+0x2b0..`, source palettes `+0x14c`). Reste : décompiler le **composer z5**
  (projet pyghidra `dumpz5` sur `ee_z5blanka.bin`) → réimplémenter offline → générer les
  pages du monde complet → rebuild section ISO.
- Résiduels : rectangle bleu vif (objet versus non tué), feuilles, **serpent** (port des
  scripts d'émission — interpréteur `0x29c050`, allocateur `0x581990`, records `0x696148+`).

---

## 5. Outils & chemins (état 2026-07-12)

### Émulation / test
- **PCSX2** portable : `E:\EMU\Emulateurs\pcsx2-v1.7.2790-windows-64bit-AVX2-Qt\`
  (exe `pcsx2-qtx64-avx2.exe -batch "<iso>"`). ⚠️ `EnableCheats=false` par défaut chez Rickow.
- **pnach** projet : `…\cheats\SLUS-21317_72CE7A78.pnach` (format SERIAL_CRC, sections
  `[Nom]`, type `word`). Widescreen inerte : `…pnach.WSTEST`.
- **ISO vivante** : `E:\ROMS\PS2\Street Fighter Alpha Anthology\SFA Anthology - Hyper Loader Test (USA).iso`
  (⚠️ la copie à la racine `E:\ROMS\PS2\` est **périmée**). Original :
  `…\Hyper Street Fighter Alpha (USA).iso`.
- **ISO de JEU de référence (2026-07-19)** : `…\SFA Anthology [Widescreen] (USA) [Arcade].iso`
  = widescreen v10 + arcade v30 bakés, sans cheats (décocher `[Hyper Arcade]` !). Jeux cachés
  du shell (Upper/Hyper) = débloqués par la SAVE memory card, pas par l'ISO.

### PINE (pilotage live PCSX2) — itération instantanée
- TCP `127.0.0.1:28011`. rd32 = `pack('<IBI',9,2,addr)` → `{u32 size,u8 res,u32 val}`.
  Harnais `E:\tmp\pine_lab.py` (rd/wr 8-32, `snap()`, `blackness()`).
- Boucle autonome : write → `MsgSaveState(9)` → le `.p2s` contient `Screenshot.png`
  (zip, non compressé) → lecture directe = « je vois l'écran ». ⚠️ zstd des `.p2s` =
  `read_across_frames=True` (sinon tronqué 64K).
- Marche des persos live = `PostMessage(hwnd, WM_KEYDOWN, vk, 1|(scan<<16))` ~30 Hz
  (keybd_event ne marche PAS pour le pad). Bindings dans `PCSX2.ini [Pad1]/[Pad2]`
  (backup `PCSX2.ini.bak_crossstage`).
- **Leçons 2026-07-12** : PCSX2 ne se met PAS en pause sur perte de focus (musique/jouable) —
  le savestate PINE n'écrit que si le jeu AVANCE (frames statiques = mtime inchangé, attendre du
  mouvement) ; **⚠️ ISO patchée SLUS → CRC `72CE7A38`** : savestates dans `…(72CE7A38).*.p2s` et
  les pnach `_72CE7A78` inopérants (voulu : tout est baké). Pokes live : OK sur code résident
  (SLUS/zb) mais un reset/relance les efface ; ne pas faire clignoter un poke de CODE (crash) ;
  ne pas killer FUN_1d2840 (persos+UI, crash) ; res=255 sur les regs GS privilégiés (0x12000000,
  non lisibles — lire les paquets A+D en RAM EE à la place).
- **Kill-test par couche** (méthode validée, cf. §3) : `jr ra;nop` à l'entrée d'un drawer → la
  couche disparaît → identification visuelle par Rickow → restaurer. Rapide et sûr.

### Debugger PCSX2 (2026-07-12 — décisif pour pinpointer les crashs de cave)
- Debug → onglet R5900 : **breakpoint Execute** sur une adresse (ex. l'entrée d'un cave), onglet
  **Threads** (un PC=0x00000000 sur le thread RUN = crash par saut dans le vide), onglet **Stack**
  (chaîne d'appels), Registers, Disassembly (Ctrl+G). C'est ce qui a trouvé le bug d'encodage
  `j` du cave wrap (0x0876646E au lieu de 0x0807466E → PC=0).
- ⚠️ **Le padding de FIN de segment du SLUS (ex. 0x18b60c) n'est PAS file-backed** (BSS/scratch) :
  un cave écrit là dans le fichier ISO ne se charge JAMAIS. Les zones zéros du MILIEU du SLUS
  (file-backed) et les zones zéros de zb (ex. 0x1d7e90+) se chargent bien.

### GS dump (Shift+F8 → `snaps\*.gs.zst`) — parser maison
Format : magic 0xffffffff + header@8 {state_ver, state_size, serial_off/size, crc, ss_w/h/off/size} ;
screenshot RGBA@54 (640×480×4) ; état GS (~4 Mo) ; **flux de paquets** ensuite (id 0=Transfer{path,size},
1=VSync, 2=ReadFIFO2, 3=Registers 0x2000). Décompression zstd standard. Utile pour lire FRAME/TEX0/
XYOFFSET réellement émis (les regs GS ne sont pas lisibles par PINE).

### Patchers ISO — outillage livré
- **`hyper_re\sfa_anthology_ws_patcher.py`** = patcher widescreen (SLUS + zb, cf. §3).
- **`hyper_re\hyper_arcade_iso_patcher.py`** = patcher arcade (e544/zero9 via splice, cf.
  `ARCADE-Hyper-SFA.md` §8) — s'applique PAR-DESSUS l'ISO widescreen (chaînables).
- `anthology_extract\compress_opt.py` = recompresseur DP optimal (petits fichiers).
- **`anthology_extract\mwo3_splice.py`** = recompression chirurgicale gros fichiers +
  `decompress_strict` (validation fidèle au décodeur réel do/while).
- Décompilés frais dans `ghidra_sfa3\out\v7\` : FUN_1d0750/1d35b0/1d40b0/1d44a0/1d47d0 (frame BG +
  builders GS), FUN_1d1250/1d1720/1d1c60/1d22d0 (init templates), FUN_1d18a0/1d1a00/1d1ed0/1d2080/
  1d25c0 (drawers), FUN_1d1da0/1d3860/1d3960 (passe rowscroll/blit), FUN_1d36a0/1d3700 (DMA/templates).

### RE / build
- **pyghidra** (Ghidra 12.0 + extension `ghidra-emotionengine-reloaded`, langage `r5900:LE:32`)
  — projets `E:\CLAUDE CODE\ghidra_sfa3\` : `dump` (z9 vanilla), `dumpz5` (monde z5).
  Sorties `ghidra_sfa3\out\v7\FUN_*.c`. **Lancer pyghidra soi-même** ([[feedback-use-pyghidra]]).
- **capstone** MIPS32 LE (`skipdata=True`) pour désasm rapide.
- **Émulateur R5900 python** : `E:\tmp\emu_r5900.py` (64-bit, delay slots, LWL/R, SWL/R,
  famille d*) — préflight des caves / rejeu offline sur dumps.
- **Assembleur du cave** : `E:\tmp\asm_v7pg.py` (⚠️ **CRLF/ASCII only** sinon SyntaxError)
  → `v7pg_lines.txt` (lignes pnach) + `v7_section.bin` (section à écrire dans l'ISO).
- Extraction savestate : `E:\tmp\p2s_ee.py` (eeMemory d'un `.p2s` zstd) ;
  `E:\tmp\decode_log.py` (ring buffer du build DEV).

### Dumps de référence (`E:\tmp\` sauf indiqué)
- z9 vanilla : `E:\CLAUDE CODE\hyper_re\eeMemory_versus.bin`
- z5 Blanka référence : `ee_z5blanka.bin` (+ `spr_z5blanka.bin`) ; `ee_s3ref.bin` (in-game)
- monde z5 (captures union) : `z5_world_right.bin`, `z5_world_left.bin`, `union_scr2.bin`, `union_scr3.bin`
- états z9 patchés : `ee_v7*_XX.bin`

---

## 6. État par jeu & reste à faire

| Jeu | Widescreen (AXE A) | Décor/tiles (AXE B) |
|---|---|---|
| Upper (zero5) | ✅ **v10 VALIDÉ in-game** (rempli + centré + aligné) | source des stages cross-stage |
| Hyper (zero9) | ✅ validé (ISO [Arcade] jouée) — **+ AXE C arcade baké** | v7.30, monde z5 à porter (composer + serpent) |
| SFA3 (zero3) | patch actif — boot vérifié sur ISO bakée, stages à valider | — |
| SFA2 &co (zero2/4/6/8) | patch actif — à valider stage/stage | — |
| SFA1 (zero1) | patch actif — à valider | — |
| Pocket Fighter (zero7) | patch actif — à valider | — |

**Priorités (maj 2026-07-19) :**
1. ~~AXE C (arcade)~~ → ✅ **FAIT : ISO `SFA Anthology [Widescreen] (USA) [Arcade].iso` validée
   in-game** (widescreen + arcade v30 sans cheats ; patcher `hyper_re\hyper_arcade_iso_patcher.py`,
   méthode complète dans `ARCADE-Hyper-SFA.md` §8 : mapping e544 = EE−0x1F0000, caves file-backed
   0x5CEF00, splice). Rappel : cheat `[Hyper Arcade]` à DÉCOCHER (CRC commun avec l'ISO WS).
2. **AXE B (cross-stage) = LA PROCHAINE ÉTAPE** : finir le monde z5 (composer offline `dumpz5`)
   — **en tenant compte des conflits §4** (RAM 0x1580000+ = buffers widescreen ; caves zb
   0x1d7e90+ = widescreen ; loader dst/staging à re-répartir dans ~0x1690000–0x19d0000 ;
   pour le bake final : zone file-backed zero9 libre `0x5D16F0` + marge slot e544 = 880 o,
   ou insérer un fichier AFS dédié comme le package 553). Puis généraliser loader/package,
   et régler le pnach cross-stage (mêmes risques multi-jeux que l'arcade, cf. §4.4).
3. **Finitions AXE A** : bugs des écrans hors combat (suspect : +32 sprites à gater par mode) ·
   bout de ciel au bord extrême de course caméra · validation des autres zeroN · pop d'objets
   aux bords (culls `0xc0`/`0x17f`) si observé.
4. Bake final unifié (widescreen + arcade + cross-stage dans UNE ISO) : les briques existent —
   patcher widescreen (SLUS+zb via compress_opt) + patcher arcade (e544 via splice) ; le
   cross-stage s'y ajoutera (zb/zero9/zero5 + fichier AFS package).

> Voir aussi [[project-sfa-anthology-cps2-extraction]] (extraction conteneurs),
> [[project-sfa3max-streamer]] (RE tilemap PSP, cousin), [[project-darkstalkers-widescreen]]
> (moteur frère, 16:9 très favorable).
```
