# Journal des modifications

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/). Le projet n'a pas encore de numéros de
version : les entrées sont datées par jalon (date à laquelle la fonction a marché en jeu). Le détail de chaque point
est dans le [journal](docs/journal/HANDOFF.md) (« §N ») et dans les [rapports](docs/rapports/README.md).

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
