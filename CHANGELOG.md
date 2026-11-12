# Journal des modifications

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/). Depuis la v0.1 (2026-10-27), une entrée
par release publique ; avant, les entrées sont datées par jalon (date à laquelle la fonction a marché en jeu). Le détail de chaque point
est dans le [journal](docs/journal/HANDOFF.md) (« §N ») et dans les [rapports](docs/rapports/README.md).

> **Language**: from 2026-11-12 on, the entries of this changelog are written in English (starting with the
> v0.1.9 section below); the older entries stay in French.

## Unreleased

- **Hyper + Arcade** (ro9a38): four fixes from the critical review of the graft. After a VERSUS played on an Upper
  stage, the next character select no longer shows its background in wrong tiles; when a new challenger joins during
  Upper's map, face-off or an Arcade fight, the 2-3 frames of full-screen wrong tiles are gone (a few black frames
  under the banner instead); 13 pieces of Upper's ending actors (Guy, Sagat and the endings of characters 0F, 10, 18,
  19, 1A, 1C) no longer run Hyper fight routines; 142 proven pointers of Upper's data are now converted. With the fixes
  off, the build gives ro9a37 byte for byte; VERSUS identical to ro9a37, stages unchanged, all endings reached.
  `hsfa_build.py --jeux hyperarcade` builds ro9a38 (§223).
- **Upper and Upper MAX: Dee Jay's taunt is no longer silent.** Like Hyper before v0.1.9, Upper keeps the hybrid sound
  ROM, whose Z80 has no sound for two commands that the PS2 port plays from its own sound banks: Dee Jay's taunt
  (`057D`) and entry 15 of Birdie's sound table (`040F`). The build adds them to Upper's and Upper MAX's sound ROMs from
  your ISO (`tools/son-hyper/sons_ps2.py --jeu upper|uppermax`, steps `sons_ps2_upper` / `sons_ps2_uppermax`, same
  switch `HSFA_SONS_PS2`; `0` = previous ROMs byte for byte); Hyper's sound ROM does not change
  ([report](docs/rapports/SONS-PS2-UPPER.md)).

## v0.1.9 (2026-11-12, pre-release)

- **Savestates: HSFA zone checked before being applied** (patch `0032`, core batch of 12/11b; v0.1.9
  review): a damaged state, padded with zeros by a frontend or from a future version, is no longer applied blindly
  (before: silent game and black 1st frame, or even a crash); it loads like a state from before v0.1.9, with a
  message. Valid states load as before, byte for byte. **Standalone FBNeo** (test, `W06`): rewind
  and run-ahead also restore the sound, the objects, the palette and the transparency of Upper / Hyper (like the
  file states): same sequence of pictures and sound as the libretro core.
- Upper MAX follows translator v161: the integration of the MAX characters no longer reads any hard-coded image address (sites found by pattern and cross-checked with the build map); the `$1B6B6` call of the ending actors (Maki's and Yun's endings) finally targets the right routine; the `prog_upper_v160` step is gone.
- **16:9: "Widescreen edges" = *Raw* by default** (patch `0031`, core batch of 12/11; standalone FBNeo: `W05`):
  the picture drawn by the game, free view in the PSP manner, as before v0.1.5. The view locked onto the stage art
  (*Stage-locked view*), *Mirror*, *Repeat* and *Black* remain options. Reason: near the ends of the arena, the locked
  view freezes the ground and makes the far layers slide the other way, up to three times faster than in the arcade,
  and some background tiles arrived late (filtered columns shown mirrored, then replaced). The 4:3 core does not
  change (byte for byte); in 16:9 with the option on *Stage-locked view*, pictures and sound are identical to the
  batch of 11/11. A setting already saved by RetroArch (or in `fbneo64ws.ini`) is kept: choose *Raw* in the menu.
- **Translator v161** (SFA3, Upper, Hyper, Hyper + Arcade): silent losses found by the critical review of the translator, fixed
  and proven against the arcade: MAZI mode ×1.5 damage bonus never applied, combo score bonus never added,
  hit character's shake missing (SFA3), 2nd letter of the initials written on the 4th (SFA3, Upper),
  and nine other comparisons or byte accesses (custom combo freeze, scrolling text, 2nd player's colour in mirror matches of Upper
  and Hyper…). The build now counts these losses and stops on an untranslated comparison or recompiler
  helper (§219).
  Upper MAX benefits too (see the Upper MAX line above, §220).
- **Hyper and Hyper + Arcade**: 21 sounds of the PS2 port were silent (empty commands in the arcade Z80s):
  parry in Mazi S-ISM (issue #1), ZERO 2 / ALPHA custom combo, Birdie, Sagat in Saikyo S-ISM, Cammy ALPHA (×14),
  Dee Jay's taunt, `0245`. The build adds them to Hyper's sound ROM from your ISO
  (`tools/son-hyper/sons_ps2.py`, `HSFA_SONS_PS2`), at the pitch and level of the PS2
  ([report](docs/rapports/SONS-PS2-HYPER.md)).
- **Building on Windows** (issue #2, fixed): Upper MAX builds without the right to create symbolic links (junctions or
  copies, `src/hsfa/liens.py`); three other Windows failures fixed (home folder, paths in the generated code,
  encoding); zips identical to Linux's (line endings, `.gitattributes`) (§215).
- **Hyper + Arcade** (ro9a36): CONTINUE, stages of Ryu, Sodom and Cammy, Ken's ending. `hsfa_build.py --jeux hyperarcade`
  now builds ro9a36 (with the arcade ROM and the replay table: zip as delivered, byte for byte except `hsfa_info.txt`) (§217).
- **Hyper + Arcade** (ro9a37) moves to translator v161: Mazi mode ×1.5 damage bonus, combo score bonus
  and 2nd player's colour in mirror matches, as in Hyper; VERSUS identical to ro9a36, stages
  unchanged. `hsfa_build.py --jeux hyperarcade` builds ro9a37 (zip as delivered, byte for byte except `hsfa_info.txt`, with `HSFA_SONS_PS2=0`) (§221).
- **Upper MAX**: round behaviour of the MAX characters aligned on the PSP (4 bytes).
- **Chun-Li**: the Kikosho arcs and the Kikoken wave were not missing (they flicker at 30 Hz as in the arcade;
  the old bench compared the wrong frame): removed from the known limits, nothing to fix (§214).
- **Ground shadow on the ISO-only route** (Hyper, Hyper + Arcade, ZERO / ZERO 2 characters): opaque instead of transparent, because
  its tiles took other codes in the extended ROM than the ones patch `0011` recognises. The build places these
  tiles (taken from the disc) at the core's codes (`HSFA_OMBRE_CODES`, `hsfa_gfx.py`); only `hsfa_gfx.bin` and
  `hsfa_tab.bin` change, and only the shadow changes on screen: ISO route = arcade route to the pixel (§216).
- **Cores** (batch of 11/11): complete and deterministic savestates (patch `0029`: run-ahead, rewind, netplay);
  Linux x86_64 core compatible with glibc 2.27 (the one of v0.1.7 / v0.1.8 required 2.43: refused by
  Batocera 43 and older distributions), same output byte for byte (`tools/linux/`). Batch of 12/11: patch `0030`
  (system folder of standalone FBNeo under Windows; libretro cores identical byte for byte) and `0031` (16:9, see above).
- **Output formats** (`--cible`, also a menu in the builder): `fbneo-hsfa` stays the default, with the same
  zips byte for byte. `fbneo-autonome` (standalone FinalBurn Neo HSFA for Windows, test build) states its concession
  (RetroArch savestates do not load in it), asks for confirmation, then builds the same zips byte for
  byte. `mister` and `cps2-banques` do not exist yet: the build states, game by game, the concessions of
  that format and the measured budgets, asks for confirmation, then stops without building anything
  (`scripts/construction/cibles.py`). Messages in French or English (`HSFA_LANGUE`, otherwise the system language).
- **Standalone FinalBurn Neo HSFA (Windows x64)**, test build, without RetroArch: official FBNeo `84faab7` (common
  base of libretro `af5d3f3`) + the repository's chain (0001-0027, 0029-0031) + 5 patches of the Windows interface
  (`patches/fbneo-autonome/`); two programs (4:3, 16:9); HSFA options in the DIPs, 16:9 in the Video menu;
  tried under Wine: pictures, game states and sound identical to the RetroArch core (within ±1 on a few samples of the
  Ogg streams). Not tried on a real Windows yet.
- **Batocera** (v43, tried on the official 43.1 PC image in a virtual machine): installer
  `tools/batocera/installer-hsfa-batocera.sh` (an `hsfa` service puts the cores in place at every boot: survives
  reboots and updates; uninstall with `retirer`), `es_systems_hsfa.cfg` system, guide FR + EN; the 5
  games up to the fight from the game list, in 4:3 and 16:9, with sound. ARM 64-bit: glibc checked, not tried;
  ARM 32-bit: not supported. **RetroBat**: installation note (`tools/retrobat/`, not tried).
- **`re/` index**: four contradictions with cps2recomp's notes settled on the MAME bench (cps2recomp was right);
  Upper → Hyper counterparts proposed by its `portmap.py` tool run locally (ro5 +284, ro9 +1,404); journal §213.
- **Research**: sheets J to R (`docs/rapports/recherche/`): cross-check with cps2recomp, neighbouring projects, room on
  a real CPS-2 (banks, budgets).

## v0.1.8 (2026-11-08, pré-version)

- **Hyper + Arcade** (pilote `sfa3hahsfa`), expérimental, première construction publique : `hsfa_build.py --jeux
  hyperarcade` (ou le constructeur). En Arcade, chaque adversaire de l'ordinateur prend un mode au hasard (ZERO / ZERO 2
  / ALPHA / ZERO 3, EX et S-ISM compris), avec son thème et son décor ; thèmes rival et final d'Upper quand les deux
  joueurs sont en ZERO 3 ; fins corrigées. Relevés d'adresses de la greffe versionnés (adresses seulement).
- **Cœurs** (patch `0027`) : les sprites arrivent à la même image que leur palette, comme sur la carte d'arcade.

## v0.1.7 (2026-11-08)

- **Constructeur tout-en-un** (`hsfa-constructeur-<système>.zip`, Windows / Linux / macOS, construit par GitHub) : rien à
  installer ; encodeur Ogg portable (mêmes octets partout : reconstruire Upper et Hyper une fois).
- **Upper MAX** (Eagle, Maki, Yun, Ingrid), expérimental, depuis vos deux disques (`--jeux uppermax --psp-iso`) ;
  assembleur 68000 du projet à la place de vasm.
- **SFA3** : écran du logo QSound et une tuile de l'intro comme sur PS2 (patch `0026`) ; curseur de la sélection sur Ryu
  (traducteur v159).
- **Hyper** : jauge de super des versions anciennes ; musiques rapides « vie basse » au bon seuil (traducteur v159-v160).

## v0.1.6 (2026-11-07)

- **SFA3** (traducteur v158 + patch 0025) : tuiles d'objets redessinées par le portage PS2, absentes de la ROM d'arcade
  (poupées de Shadaloo dans les fins de Cammy, E. Honda, R. Mika et Cody : 684 tuiles) ajoutées telles quelles en ROM
  graphique étendue (`hsfa_gfx.bin`, facultatif pour le pilote `sfa3hsfa`). Reconstruire SFA3 ; Upper et Hyper
  inchangés. Cœurs 0001-0025.
- README : état des chantiers (greffe Hyper + Arcade, Upper MAX, réorganisation en pause) ; crédits et index `re/`.

## v0.1.5 (2026-11-07)

- **Vrai 16:9** (patchs 0022-0023) : le cœur 16:9 dessine 512 × 224 au rapport exact (l'ancien 448 px était étiré de
  ~14 %) ; aux bouts de l'arène, où le décor peint s'arrête, la vue se cale sur le décor (« Stage-locked view », par
  défaut) : décor, persos et effets glissent, le HUD reste centré, le jeu ne change pas. Option « Widescreen edges » :
  mirror / repeat / black / raw ; « Screen format » 14:9 = ancien rendu 448.
- **SFA3** (traducteur v157 + patch 0024) : tuiles rangées en miroir par le portage PS2 et perdues à la conversion :
  ciel du décor de Ryu (traînées) et 155 autres cases sur 18 décors, 1 311 tuiles de sprites (ex. jambes de Dhalsim
  dans l'intro). Reconstruire SFA3 ; Upper et Hyper inchangés.
- Crédits (`CREDITS.md`).

## v0.1.4 (2026-11-04)

- Cœurs plus rapides (patchs 0019-0021c) : option « Skip idle loops (faster) », activée par défaut, qui saute les
  boucles d'attente du 68000 et du Z80 du son ; crochets Z80 / Musashi et filtre QSound plus rapides. 33 à 41 % de calcul
  en moins par image (sur PC ; davantage sur ARM), image, son et parties identiques. Recalbox et ROCKNIX : compilation
  -O3, LTO, sans -ffloat-store. Essayé sur Raspberry Pi 3 : Hyper + Arcade ne ralentit plus.
- Jeux inchangés (mêmes empreintes que la v0.1.3).

## v0.1.3 (2026-11-03)

- Option du cœur « Blood » (patch 0018) : sang rouge, non censuré, par défaut ; « blanc » = censuré, comme l'arcade US et
  la PS2. Elle porte sur les coups, les portraits (Zangief) et les fins, dans les 5 jeux et toutes les versions d'Hyper ;
  prise en compte au chargement ou au redémarrage du jeu. Les zips des jeux ne changent pas.
- Traducteur v154 (Hyper seulement ; SFA3 et Upper identiques à l'octet) : récupération du Hadoken de Sakura ZERO 3 en
  S-ISM rouge (39 → 55 images, comme la PS2) ; couleur des boules de feu de type Hadoken hors X-ism (visible quand Rose
  les renvoie). Programme d'Hyper : `dda35430` (depuis l'ISO), `b8e699cf` (avec la table du rejeu). Reconstruire Hyper.
- Recalbox : essayé sur Raspberry Pi 3B (cœur 32 bits) ; le lancement depuis la liste de jeux de Recalbox ne marche pas
  encore (charger le cœur depuis le menu de RetroArch).

## v0.1.2 (2026-11-02)

- Cœurs FBNeo HSFA avec les patchs 0001-0017 (et 0007b), construits le 2026-11-02. 0016 : dans Upper, Start tenu + un
  bouton sur Akuma / Balrog redonne Shin Akuma / EX Balrog (la roulette passe sur Pièce / Select, sur la grille
  seulement). 0015 et 0017 ne servent qu'à la greffe du mode Arcade (rien ne change pour SFA3, Upper et Hyper).
- Cœurs Recalbox 10 (Raspberry Pi 3 armhf, Pi 4 / 5 aarch64), script d'installation et guide
  ([installation-recalbox](docs/guide/installation-recalbox.md)) ; pas encore essayés sur le matériel.
- Jeux inchangés : `scripts/construction` est identique à la v0.1.1, mêmes empreintes.

## v0.1.1 (2026-10-28)

- Traducteur v153 : Guy se figeait au milieu d'une figure de sa Bushin dans Hyper (index d'état écrasé avant un test de
  version), ce qui pouvait bloquer une manche indéfiniment. SFA3 et Upper sont inchangés ; le programme d'Hyper vaut
  maintenant `f3641d03` (construit depuis l'ISO, voix de SFA3) ou `a5f7fae0` (avec la table du rejeu).
- Lanceurs en une étape `construire.sh` / `construire.bat`.

## [Non publié]

### Préparation de la release publique v0.1 (2026-10-27)
- `hsfa_build.py`, étape `son_hyper` : module `ro9` corrigé et bloc `$E70000` de la redirection des voix d'Hyper
  régénérés depuis l'ISO (`gen_redirection.py` paramétrable, `ids_102.tsv`) ; avec la table du rejeu, le programme
  d'Hyper est celui de la v151 (`39985037`) et le zip contient le rejeu.
- Flux Ogg reproductibles (`-fflags +bitexact`) : deux constructions donnent les mêmes zips.
- Licences par composant (`NOTICE.md`, `patches/fbneo/LICENSE-FBNeo.txt`) ; README « Play in 3 steps » ; guide
  BradyGames : plus de citation ni de transcription.

### Modifié
- Réorganisation du dépôt : traducteur et chaîne dans `src/hsfa/`, chaînes de construction et de validation dans
  `scripts/`, patchs des forks dans `patches/`, documentation rangée en `docs/guide`, `architecture`, `reference`,
  `methodes`, `journal`, `rapports` ; époque PNACH dans `legacy/`.
- README réécrits (français et anglais) ; ce journal des modifications au format Keep a Changelog.

### Ajouté
- Musique d'Hyper en partitions : plan d'action ([PLAN-SON-HYPER](docs/rapports/PLAN-SON-HYPER.md)) et étude
  ([PARTITIONS-HYPER](docs/rapports/PARTITIONS-HYPER.md)). `tools/son-hyper/partitions/` : lecture des pilotes Z80
  v1.04/v1.05, bancs Z80 (QSound, CPS-1), appariement des variantes. Établi : le jeu de variantes A vient de Super SF2.
- `config.example.env`, `src/hsfa/hsfa_config.py` et `scripts/localiser.py` : chemins locaux par variables
  d'environnement, copie exécutable du dépôt.
- `requirements.txt` (numpy, capstone, pillow).
- `scripts/qualite/verifier_liens.py` et `verifier_imports.py` : liens de la documentation, compilation et imports
  de tous les scripts Python.
- Guides (démarrage, construction depuis l'ISO, Android, ROCKNIX), documents d'architecture, de référence et de
  méthode.

## 2026-10-11

### Corrigé
- Hyper : jauge de super du P2 sans plafond et plantage en TRAINING. Un `CMP` mémoire-mémoire était perdu (règle
  `CMPMM`). Confirmé sur console (§145).
- Upper : glitch du grand portrait au face-à-face. Le fichier de l'emplacement 4 attend que ses objets ne soient
  plus affichés : `BANC_LAT4` au banc, `HSFA_LAT4` dans le cœur (§146).

### Ajouté
- Hyper : voix de SFA1 et de SFA2 selon la version du perso, rejouées sur un 2ᵉ QSound à partir des données de
  l'ISO, au fork et dans le cœur FBNeo (§144-§145).
- Archives « tout dans le jeu » : le zip d'Hyper contient la musique en flux et les données du rejeu (§145).
- Voie B, préparation : scènes nommées, cœur à greffer mesuré, table de relogement A5, règle `$102` → `$116`,
  prototype de greffe sans non-résolu (§145).

## 2026-10-10

### Ajouté
- Construction depuis l'ISO de l'utilisateur (`hsfa_build.py`, `rom_iso.py`) et outils d'extraction : ROM programme
  identiques (md5) au banc, voie « ISO seule », zips déterministes (§143-§144).
- `valide_tout.sh` : validation complète après chaque correctif du traducteur (§143).
- Pilote FBNeo `sfa3hhsfa` : Hyper dans le cœur HSFA (§143).
- Lecteur de flux musique ADX (fork et cœur) : musiques absentes du Z80 lues dans le `Y_DATA.BIN` de l'ISO (§142).
- Décors : export exact de tous les décors de SFA3 en PSD, réimportation PSD → tuiles CPS2, import d'un décor de
  SFA2 dans SFA3 traduit (§142, §144).
- MAX : tout le contenu des 4 persos converti vers l'image d'Upper (code, données, frames, animations, voix) (§144).
- Cœurs ROCKNIX (RGB10X, aarch64), 4:3 et 16:9 (§144).
- Réorganisation des données, étape A : journal des conversions, oracle RAM traduction ↔ arcade (§142).

### Corrigé
- Super boule d'Akuma et de Dan (`TAILBR`), boules multi-coups de Sakura et de Rose (`LUIDN`) (§143).
- Upper : tuiles de décor manquantes sur 16 décors (tuiles 32×32 vides opaques) (§142).

### Modifié
- Stratégie : le produit final part d'Hyper, avec la couche Arcade d'Upper greffée (voie B) (§144).

## 2026-10-07

### Ajouté
- Cœur libretro FBNeo « HSFA » : SFA3 et Upper sans MAME, Android et Linux, 4:3 et 16:9 (§136, §139).
- Hyper au fork : banques propres, balayage des modes et des 113 versions (§133).
- Balayage des fins, outil permanent (§131).

### Corrigé
- Audits du « code perdu » : écritures de registre et de mémoire sans traduction, dans SFA3, Upper et Hyper
  (§132, §137, §138) ; régression des fins de SFA3 corrigée (§137).
- Zones de registres prêtés A8/D8 à sorties latérales (combat miroir) (§130).
- Code C du portage : aiguilleurs par table de longs (fin de match VERSUS d'Hyper) (§140).

## 2026-10-04

### Ajouté
- SFA3 : partie Arcade complète jusqu'au générique ; les 32 fins conformes à l'arcade ; modes console dans la durée
  (§110-§112).
- Fork MAME `sfa3hx` : ROM graphique de 128 Mo, codes d'objet sur 20 bits, blocs externes, une base par plan
  (§116, §120).
- Upper : au banc, puis jouable de bout en bout avec ses 40 fins ; ROM son hybride (§108-§128).
- Documentation : architecture des outils (`OUTILS.md`), carte des symboles de SFA3, index du journal (§117, §123).
- MAX : Eagle affiché dans Upper sur le fork (§129).

## 2026-10-02 au 2026-10-03

### Ajouté
- SFA3 jouable : boucle de jeu complète, menu des modes, écran de combat complet (§80-§101).
- Test des commandes contre la ROM arcade : 42/42 (§93, §97).
- Visualiseur d'état PS2 dans MAME (§89).
- Conversion des adresses de code par hachage : cadence turbo de l'arcade retrouvée (§98).

## 2026-09-26 au 2026-09-27

### Ajouté
- Preuve que l'Anthology est une recompilation statique 68000 → MIPS ; traducteur par idiomes, assembleur 68000,
  recette mémoire « cps2 » (§1-§58).
- Premier démarrage du SFA3 traduit dans MAME, noyau de tâches 68K reconstruit, attraction stable, son validé à
  l'oreille (§59-§79).
- Étude de SFA3 MAX (PSP) : format des persos et des frames, conversion des tuiles vers la CPS2.

## Époque PNACH (PCSX2), avant le 2026-09-26

Conservée dans [`legacy/`](legacy/README.md).

### Ajouté
- Mode Arcade pour Hyper Street Fighter Alpha : parcours d'adversaires CPU, continue, fin, en MIPS injecté.
- Widescreen 16:9 natif, géométrie juste (modèle en anneau du compositeur de décor), validé sur Hyper et Upper.
- Tout débloqué : patch d'octets.

### Inachevé
- Cross-stage (chaque perso dans son décor) : compositeur, tables et palettes cartographiés, décompresseur LZ porté
  en Python à l'octet près, approche par repointage du contexte de couche validée.
