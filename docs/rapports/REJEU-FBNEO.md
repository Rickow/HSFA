# Rejeu des sons SFA1/SFA2 d'Hyper dans le cœur FBNeo « HSFA », et données lues dans le zip du jeu

Agent `agent_fbneo_rejeu`, 2026-10-10.

**Où j'ai écrit** : seulement dans `<workspace>/work/agent_fbneo_rejeu/`, plus le scratchpad de la session.

**Lecture seule** :
- `agent_fbneo_hyper/` (copie de départ), `agent_son_hyper_rom/` (table, en-tête, `b9_son`, références), `agent_flux/` ;
- `work/fbneo/paquet_fbneo.py` (original : un diff est proposé) ;
- `work/xdata/`, l'ISO.

**Non touchés** : `mame_ro9`, `agent_rocknix`. Aucun MAME lancé : la comparaison au fork utilise ses enregistrements
existants.

**Précautions** : compilations en `nice -n 19`, `make -j4`. Rien n'a été poussé ; le commit est local, sur la branche
`rejeu`.

**aarch64 Linux non construit** : l'agent `agent_rocknix` travaillait dans son dossier (essais `hsfa_run_x86_64` en
cours). Je lui ai laissé cette construction.

## 0. En bref

1. **Le rejeu tourne dans FBNeo.** Commit `97a9b1c` sur la branche locale `rejeu` de `fbneo/`, posé sur `464b23a`.
   Patch : `patchs/0001-HSFA-rejeu-…patch`.
   - Le 2ᵉ QSound est `hsfa_qsound.h` : le HLE de `qs_c.cpp` (superctr, BSD-3), rendu instanciable, avec la sémantique
     du `qsound_hle_device` du fork.
   - Il est piloté par `hsfa_rejeu.h`, le même lecteur que le fork, avec deux ajouts compatibles.
   - Le crochet est à la pose de commande (`$61801F = 0`), juste après le lecteur de flux.
   - La sortie est mixée au QSound principal, avec le même volume.
   - Les états sauvegardés sont gérés.
2. **Décisions de l'utilisateur appliquées : tout est dans le zip du jeu.**
   - `paquet_fbneo.py` (ma copie) ajoute quatre membres **stockés**, que le cœur lit sur place, sans les déclarer comme
     ROM. FBNeo ne les charge donc pas en mémoire.

     | membre | contenu |
     |---|---|
     | `hsfa_flux.bin` | AFS réduit : Hyper 216 flux, 695 Mo ; Upper 7 flux, 22 Mo |
     | `hsfa_flux_table.txt` | table des flux |
     | `hsfa_rejeu.bin` | e222 + e251, 8 Mo, CRC contrôlés |
     | `hsfa_rejeu_table.txt` | table du rejeu |

   - Ordre de recherche : membre du zip, puis `<système>/fbneo/hsfa/` (`Y_DATA`, `X_DATA`, ISO, `ydata.txt` /
     `xdata.txt`), sinon inactif.
3. **Validation contre le fork** : même scénario que son essai « programme » `pg_ryuZ_kenZ2` (ROM `b9_son`).
   - **Mêmes sons, dans le même ordre**, avec les mêmes décisions (dont les `ALIAS` vers le Z80).
   - Corrélation avec la référence du pilote d'origine : **médiane 0,658** (fork : 0,66) ; témoin sans rejeu : 0,036.
   - **Mêmes décalages au ms près** (28,8 / 33,9 / 29,4 / 31,6 ms) et **même gain** (≈ 1,00).
4. **Non-régression**
   - SFA3 et Upper : son, journal et 30 captures **identiques** au cœur `hyper`, avec et sans `Y_DATA`. Upper avec
     ses flux dans le zip donne aussi un résultat identique.
   - Hyper sans aucun membre : identique à l'octet au cœur `hyper` (son, journaux, 24 captures).
   - Flux lus dans le zip : identiques à l'octet aux flux lus depuis l'ISO du dossier système.
   - Rejeu par le zip, par `X_DATA.BIN` ou par l'**ISO** : mêmes octets dans les trois cas.
   - États : image restaurée identique. Le son du 2ᵉ QSound est **identique à l'échantillon près** après restauration,
     testé en 3 points, dont un pendant un K.O. avec écho.
5. **Coûts**
   - Chargement inchangé (≈ 0,17 s sur PC).
   - Mémoire en régime établi : +14 Mo avec le rejeu ; les 695 Mo de flux ne sont jamais chargés. Pic au chargement
     inchangé (141 Mo).
   - Temps de calcul : environ 0,16 ms par image sur PC (906 contre 1 059 images/s).
6. **Cœurs** (`livraison/`) :
   - Linux x86_64 : `fbneo_hsfa_libretro.so`, md5 `b6da7e53…` ;
   - Android arm64-v8a : `fbneo_hsfa_libretro_android.so`, NDK r28c, API 21, pages de 16 Ko, md5 `31fc9592…` ;
   - tous deux en `GIT97a9b1c`.
   - Le cœur Android n'a pas été essayé sur un appareil.

## 1. Ce que fait le cœur

### 1.1 Fichiers (commit `97a9b1c` : 9 fichiers modifiés, +369/−11, et 2 en-têtes nouveaux)

| fichier | modification |
|---|---|
| `capcom/hsfa_qsound.h` (nouveau) | 2ᵉ QSound HLE (voir 1.2) |
| `capcom/hsfa_rejeu.h` (nouveau) | copie de `agent_son_hyper_rom/rejeu/hsfa_rejeu.h`, plus `ouvre_texte` (table en mémoire), `charge_xdata` (partie X_DATA de `ouvre`), `verifie_rom` (CRC d'une image déjà chargée), et `trace` en `vsnprintf` + `fwrite` (la couche fichiers de libretro ne redirige pas `vfprintf`) |
| `capcom/hsfa_flux.h` | `ouvre_texte` (table en mémoire) ; `ouvre_y` (partie Y_DATA de `ouvre`). `ouvre` se comporte comme avant |
| `capcom/cps_hsfa.cpp` | lecteur de zip (membres stockés), recherche des données, rejeu (temps, rendu, mixage, états), journal |
| `capcom/cps_mem.cpp` | après le flux : `HsfaRejeuCommande` remplace le code transmis au Z80 (code vide ou `ALIAS`) |
| `capcom/qs.cpp` | `QsndEndFrame` : `HsfaRejeuRendu` après le flux |
| `capcom/cps.h`, `burn.h`, `burn.cpp` | déclarations ; `szBurnHsfaArchive` (chemin de l'archive, défini dans `burn.cpp` pour ne pas dépendre du pilote Capcom) |
| `burner/libretro/libretro.cpp` | renseigne `szBurnHsfaArchive` pour les pilotes `*hsfa*` (1ʳᵉ archive localisée) |
| `hsfa/hsfa_run.c` | `STATETEST` compare aussi le son des images rejouées après restauration (`ETAT SON`) |

### 1.2 Le 2ᵉ QSound

- Le code est celui de `qs_c.cpp` (le QSound de FBNeo est déjà le HLE de superctr), mais l'état est dans un objet.
  La ROM est fournie par l'hôte : 8 Mo, lus en miroir.
- Deux points suivent `qsoundhle.cpp` de MAME plutôt que `qs_c.cpp` :
  - la banque est lue **sans tester le bit 15** ;
  - les tables de panoramique et de filtres sont celles que `qs_c.cpp` a extraites du DSP. Il n'y a donc **pas de ROM
    DSP `dl-1425`** à fournir.
- Cadence : un échantillon toutes les 2 496 périodes de 60 MHz (24 038 Hz), comme MAME.

### 1.3 Temps, rendu, mixage

- **Horloge** : périodes de 60 MHz depuis la mise sous tension.
  - L'image n couvre `[n·6·10⁹/nBurnFPS, (n+1)·6·10⁹/nBurnFPS)`.
  - L'instant d'une commande s'en déduit avec les cycles 68000 déjà exécutés dans l'image (`SekTotalCycles` /
    `nCpsCycles`).
  - Le rejeu reçoit des µs, comme dans le fork.
- **Rendu en fin d'image** :
  - pour chaque échantillon de sortie, on produit les échantillons du 2ᵉ QSound jusqu'à son instant ;
  - les écritures dues sont appliquées avant l'échantillon de leur instant ;
  - la sortie est interpolée linéairement à `nBurnSoundRate`, puis ajoutée avec saturation ;
  - gain `Cps2Volume / 39`, comme le QSound principal (le fork aussi met le même gain sur les deux QSound).
- Sans sortie son (`pBurnSoundOut` nul), le 2ᵉ QSound avance quand même jusqu'à la fin de l'image. Son état ne dépend
  que du temps.
- Le résultat est l'**horloge du fork** : les décalages mesurés coïncident (§3).

### 1.4 Membres du zip lus sur place

- `HsfaZipMembre` lit le répertoire central et l'en-tête local, puis rend le décalage des données d'un membre.
- Le membre doit être **stocké** : méthode 0 et tailles égales. Le zip64 n'est pas géré, ce qui ne pose pas de
  problème (le zip d'Hyper fait 709 Mo).
- Libretro donne le nom de l'archive **sans extension**. Le cœur essaie `""`, `.zip` et `.ZIP`, et vérifie la
  signature zip. Un 7z ne donne donc aucun membre.
- **Flux** : `ouvre("<zip>@<décalage>")`. `hsfa_flux.bin` est un **AFS réduit** : mêmes 588 indices que `Y_DATA.BIN`,
  entrées inutiles de taille 0, données alignées sur 2 Ko. Le lecteur lit par blocs de 64 Ko, comme avant.
  - Un code dont le flux est absent du zip échoue proprement : la commande passe au Z80, ce qui donne la musique
    QSound.
- **Rejeu** :
  - `hsfa_rejeu.bin` (8 Mo, image de la ROM du 2ᵉ QSound) est lu dans le tampon du 2ᵉ QSound, puis
    `verifie_rom` contrôle les CRC des lignes `SOURCE` ;
  - la table est lue en mémoire puis libérée.

### 1.5 Ordre de recherche et variables

| donnée | 1. zip du jeu | 2. `<système>/fbneo/hsfa/` | 3. sinon |
|---|---|---|---|
| flux | `hsfa_flux.bin` | `Y_DATA.BIN`, `y_data.bin`, `anthology.iso`, `ydata.txt` (comme avant) | musique QSound |
| table des flux | `hsfa_flux_table.txt` | `hsfa_flux_table.txt` | — |
| ROM du rejeu (Hyper) | `hsfa_rejeu.bin` | `X_DATA.BIN`, `x_data.bin`, `xdata.txt`, puis l'ISO du flux (`anthology.iso` / `ydata.txt`) | sons SFA3 |
| table du rejeu | `hsfa_rejeu_table.txt` | `hsfa_rejeu_table.txt` | sons SFA3 |

**Variables PC** (essais ; elles passent avant le zip) :
- `HSFA_YDATA`, `HSFA_FLUX_TABLE` (existantes) ;
- `HSFA_XDATA`, `HSFA_REJEU_TABLE`, `HSFA_REJEU_LOG` (journal au format du fork) ;
- `HSFA_REJEU=0` (rejeu inactif) ;
- `HSFA_REJEU_SEUL=1` (sortie = 2ᵉ QSound seul, pour les essais d'états).

**Le rejeu n'existe que pour Hyper** (`HsfaHyper`) : SFA3 et Upper ne lisent ni table ni X_DATA.

### 1.6 États sauvegardés

- Zones `HsfaRejeu` (instances, voies), `HsfaQs2` (état du chip) et horloge (`nRejeuTrame`, `nRejeuEch`,
  échantillon précédent).
- **Elles sont toujours présentes pour Hyper.** Quand le rejeu est inactif, elles contiennent un état « vide », sans
  instance active.
  - Conséquence : un état se recharge **avec ou sans** les données du rejeu (même taille, 658 329 o).
  - Les états d'Hyper du cœur `464b23a` (652 769 o) ne sont plus compatibles.
- Le lecteur de flux garde son comportement : sa zone n'existe que si un flux est ouvert. C'est préexistant.

## 2. Archive (`paquet/`)

- `paquet/paquet_fbneo.py` : ma copie, faite à partir de celle d'`agent_fbneo_hyper`, qui contient l'entrée `hyper`.
- `paquet/paquet_fbneo.diff` : **diff proposé pour l'original** `work/fbneo/paquet_fbneo.py` (311 lignes, entrée
  `hyper` comprise). Vérifié : il s'applique et redonne la copie.

**Membres stockés**, chacun écrit seulement si sa source est fournie :

| membre | source | sélection |
|---|---|---|
| `hsfa_flux.bin` | `HSFA_YDATA` (Y_DATA.BIN ou ISO) | Hyper : codes de `agent_hyper_son/codes_musique_hyper.txt` (220 codes, 216 flux), sauf l'intro `x` ; Upper : codes `0030-0036` (persos d'Upper, sans équivalent QSound) ; SFA3 : rien ; `HSFA_FLUX_ZERO3=1` ajoute `0002-002F` à SFA3 et Upper (pour « All tracks », ≈ 117 Mo) |
| `hsfa_flux_table.txt` | `HSFA_FLUX_TABLE` (défaut `agent_flux/hsfa_flux_table.txt`) | table entière |
| `hsfa_rejeu.bin` | `HSFA_XDATA`, sinon l'ISO de `HSFA_YDATA`, sinon `<work>/xdata/X_DATA.BIN` | lignes `SOURCE` de la table : décalage, taille, banque, **CRC vérifié** |
| `hsfa_rejeu_table.txt` | `HSFA_REJEU_TABLE` (défaut `agent_son_hyper_rom/rejeu/`) | — |

- Le flux est copié par blocs de 1 Mo, sans tout lire en mémoire. Le zip d'Hyper complet se construit en 6 s.
- Le zip reste déterministe avec `SOURCE_DATE_EPOCH`. `hsfa_info.txt` note la source et le nombre de flux, ainsi
  que le md5 de `hsfa_rejeu.bin`.
- Autres variables : `HSFA_SANS_FLUX=1`, `HSFA_SANS_REJEU=1`, `HSFA_CODES_HYPER`, et pour les essais `HSFA_ROMS` /
  `HSFA_DOSSIER` (autre ROM programme / autres blocs `ext_*`).
- **Sans source, les zips SFA3 et Upper sont identiques à l'octet à ceux de l'original** (`SOURCE_DATE_EPOCH` fixé ;
  `tests/zips/orig` contre `tests/zips/copie`).

**Tailles**

| zip | taille |
|---|---|
| Hyper | 709 Mo = 34,7 Mo d'origine + 694,7 (flux) + 8,4 (rejeu) + 3,2 (table du rejeu) |
| Upper avec ses flux | 56 Mo (+22) |

## 3. Validation sur PC (`tests/`)

### 3.1 Construction d'essai

- **Zip d'essai** `tests/zips/essai/sfa3hhsfa.zip` (709 Mo, md5 `8595ff31c36e…`) :
  - ROM programme et blocs `ext` de `agent_son_hyper_rom/b9_son` (ro9 corrigé, §13 de SON-HYPER-ROM) ;
  - le reste comme le zip d'`agent_fbneo_hyper` ;
  - les quatre membres (ISO WORK, `work/xdata/X_DATA.BIN`).
- `tests/zips/nu/` : le même zip, sans aucun membre.

### 3.2 Scénario

- C'est celui de l'essai `pg_ryuZ_kenZ2` du fork, retrouvé dans son journal :
  `LISTE=00.Z/01.Z2,01.Z/00.Z2,00.Z2/01.A MODEJEU=1 CONTOURNE_E=1 NF=12000`, avec `HSFA_NOROUL=1` (le `NOROUL` du
  Lua).
- Lanceur `tests/fb.sh`. Le dossier système est **vide** par défaut : tout vient du zip.

### 3.3 Résultats

| essai | résultat |
|---|---|
| tournée (`fb_pg`, `fb_h_zip`) | 7 sélections, 12 manches, comme le fork. Le rejeu prend **les mêmes décisions dans le même ordre** : `2160`, `4708→Z80 0820`, `2169`, `4700` (SFA2 `028A`), `216F`, `3180`, `4808→Z80 0820`… Instants à ±35-65 ms, l'écart habituel des parties (images, hasard des cycles, FBNEO-HYPER §6.1). Seul `216F` tombe dans un autre combat |
| contre la référence du pilote d'origine (`valide_rejeu_jeu.py`, copie avec `T_IMG1` réglable ; `fb_pg_validation.tsv`) | 18 sons mesurés : **médiane 0,658** (min 0,474), fork 0,66 (0,49-1,00) ; témoin sans rejeu : médiane 0,036 (max 0,063). Par son : `2160` 0,66-0,70 (fork 0,66-0,70), `2169` 0,71-0,75 (0,69-0,82), `216F` 0,96 (1,00), `3180` 0,55-0,59 (0,57-0,61), `4700` 0,47-0,51 (0,49) |
| décalage du son dans le WAV (même `T_IMG1` que le fork) | **28,8 / 33,9 / 29,5 / 31,7 ms**, contre 28,8 / 33,9 / 29,4 / 31,6 ms au fork |
| niveau (`gain_rejeu.py` : projection sur la référence) | FBNeo `2160` 0,96-1,00, `2169` 0,96-0,99, `3180` 0,95-1,01, `4700` 0,67-0,72 ; fork 1,00 / 0,97-1,00 / 0,98-1,00 / 0,67-0,70 |
| image | captures et journal **identiques** avec et sans rejeu : le rejeu ne touche que le son |

### 3.4 Chemins de recherche (12 000 images, 24 captures)

| comparaison | résultat |
|---|---|
| ancien cœur + zip nu + ISO / nouveau cœur + zip nu + ISO (rejeu absent : « pas de table ») | WAV, journaux, flux, captures **identiques** |
| ancien cœur + zip nu + ISO / nouveau cœur + zip complet, `HSFA_REJEU=0` (flux lus dans le zip) | **identiques** |
| rejeu par le zip / par `X_DATA.BIN` + table du dossier système / par **l'ISO** (`ydata.txt`) + table | WAV, journaux du rejeu, captures **identiques** (le `X_DATA` de l'ISO WORK passe le CRC) |

### 3.5 Non-régression SFA3 et Upper (`nonreg.sh`)

Partie scriptée de 9 000 images, cœur `464b23a` contre nouveau cœur, zips d'origine :
- SFA3 : son, journal et 30 captures **identiques** ;
- Upper : identiques aussi, sans `Y_DATA`, avec `Y_DATA` (`ydata.txt`), et avec le zip d'Upper contenant ses flux.

### 3.6 États (`STATETEST`, pilote rejoué)

- Hyper, restauration aux images 1290 (Hadoken rejoué en cours), 1340 et 3262 (K.O. SFA2 avec écho) : image finale
  **identique**.
- Avec `HSFA_REJEU_SEUL=1`, le son du 2ᵉ QSound est **identique à l'échantillon près** sur les 700 à 1 200 images
  suivantes.
- Taille d'état 658 329 o, avec ou sans rejeu.
- SFA3 / Upper : mêmes tailles et mêmes résultats que le cœur `464b23a`.

### 3.7 Constat préexistant

Après une restauration, le **son du QSound principal** diffère de la 1ʳᵉ passe : environ 77 % des échantillons, sans
flux ni rejeu.
- C'est **identique avec le cœur `464b23a`**, et pour SFA3 et Upper.
- Cause probable : la phase du rééchantillonnage de `qs_c.cpp` (`nDelta`, tampon d'interpolation) n'est pas
  sauvegardée par `QscScan`.
- Hors du sujet, je n'y ai pas touché. Ce n'est sans doute pas audible, mais le run-ahead pourrait l'être.

### 3.8 Chargement et mémoire (Hyper, PC)

| | ancien cœur, zip nu + ISO | nouveau, zip complet sans rejeu | nouveau, zip complet |
|---|---|---|---|
| chargement + 1 image | 0,17 s | — | 0,17 s |
| mémoire en fin de partie (`VmRSS`) | 110 Mo | 114 Mo | 128 Mo |
| pic (`VmHWM`) | 141 Mo | 141 Mo | 141 Mo |

- Le pic vient des tampons graphiques du chargement.
- Le rejeu ajoute la ROM (8 Mo) et la table analysée (≈ 2,5 Mo).
- Les flux sont lus par blocs : seul le flux en cours est en mémoire, comme avant.

## 4. Points à savoir

- **Coût CPU sur console** : le 2ᵉ QSound tourne en permanence, comme le principal (24 038 échantillons/s, filtres de
  95 points).
  - Sur PC : environ 0,16 ms par image.
  - Sur un RK3326 (RGB10X), ce coût est à mesurer.
  - Si c'est trop, deux pistes :
    - suspendre le 2ᵉ QSound quand aucun son n'est actif et que sa sortie est nulle (ce qui change les octets, pas
      l'écoute) ;
    - une option du cœur pour désactiver le rejeu.
- **Table du rejeu** : seuls la dernière section `INIT` et la dernière `STOP` sont gardées (celles de SFA2).
  - C'est le comportement du fork.
  - Sans conséquence : les blocs SFA1 et SFA2 sont identiques et n'écrivent aucun registre de banque.
- **Fork MAME** : les en-têtes communs ont changé de façon compatible. Diffs proposés :
  - `patchs/hsfa_rejeu_h-pour-mame.diff` ;
  - `patchs/hsfa_flux_h-pour-mame.diff` (le `hsfa_flux.h` du fork est celui de `464b23a`).
  - Ils ne sont pas compilés dans MAME ; syntaxe vérifiée en C++98 (`g++ -fsyntax-only`).
- **Widescreen** (`SUBSET=hsfaws`) : même code, non construit.
- **Limites héritées du rejeu** (SON-HYPER-ROM §12.6) : pas d'interaction avec les voix SFA3 du Z80 ; sons coupés
  à la fenêtre des traces.

## 5. Reconstruire

```
cd agent_fbneo_rejeu/fbneo/src/burner/libretro && nice -n 19 make -j4 SUBSET=hsfa
cd jni && nice -n 19 ~/Android/Sdk/ndk/28.2.13676358/ndk-build -j4 APP_ABI=arm64-v8a SUBSET=hsfa
HSFA_WORK=<workspace>/work HSFA_YDATA=<ISO> python3 agent_fbneo_rejeu/paquet/paquet_fbneo.py hyper upper sfa3
```

Zip d'essai avec la ROM `b9_son` : ajouter
`HSFA_ROMS=…/agent_son_hyper_rom/b9_son/roms_ro9/sfa3ud HSFA_DOSSIER=…/agent_son_hyper_rom/b9_son`.

Avec la ROM ro9 corrigée officielle, il suffit de reconstruire le zip normalement.

## 6. Fichiers

- `fbneo/` : copie, branche `rejeu` (commit `97a9b1c` sur `464b23a`).
- `patchs/` :
  - `0001-HSFA-rejeu-QSound-…patch` (le commit) ;
  - `hsfa_rejeu_h-pour-mame.diff`, `hsfa_flux_h-pour-mame.diff`.
- `paquet/` : `paquet_fbneo.py`, `paquet_fbneo.diff`.
- `livraison/` : `fbneo_hsfa_libretro.so`, `fbneo_hsfa_libretro_android.so`, `LISEZMOI.md` (installation : tout dans
  le zip ; replis ; fabrication).
- `tests/` :
  - lanceurs : `fb.sh`, `nonreg.sh`, `hsfa_run` (compilé depuis la branche) ;
  - mesures : `valide_rejeu_jeu.py` (copie, `T_IMG1` réglable), `gain_rejeu.py`, `rss.py` ;
  - `coeur_hyper_464b23a.so` (référence) ;
  - `zips/` : `essai` (709 Mo), `nu`, `orig` / `copie` (SFA3 et Upper), `membres` (Upper avec flux) ;
  - `essais/fb_*` : journaux, WAV, captures. `fb_pg_validation.tsv` contient les mesures du §3.3.
- Journaux de construction : `build_android*.log`.

**Supprimables** : `tests/zips/` (≈ 1 Go), `tests/essais/*/son.wav`.
