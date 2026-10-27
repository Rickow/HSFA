# Lecteur de flux musique ADX : fork MAME `sfa3hx` et cœur FBNeo HSFA

Agent `agent_flux`, 2026-10-07 → 2026-10-10. J'ai écrit seulement dans `<workspace>/work/agent_flux/`.

- `mame-fork`, `fbneo-hsfa*`, `mame_ro5`, `mame_ro9`, l'ISO et les dossiers des autres agents sont restés en lecture
  seule.
- MAME a tourné en `nice -n 19`, avec ses propres `-nvram_directory` et `-cfg_directory`, sans `-state` en ligne de
  commande. Il y avait au plus 5 MAME en même temps (essais Z80 courts), en général 1 ou 2.

## 0. En bref

1. **Le lecteur marche dans le fork et dans FBNeo.** Les musiques que le Z80 ne connaît pas sont jouées depuis le
   `Y_DATA.BIN` de l'utilisateur. Le mode « musique PS2 » joue toutes les musiques en flux.
   - Le décodage ADX est **identique à l'échantillon près** à `adx.py`, boucles comprises.
   - Dans la sortie MAME, le flux se retrouve **bit pour bit** (résidu −240 dB sur une injection).
   - Le niveau est calé sur la musique QSound : un même morceau mesure −30,8 dBFS en flux et −30 dBFS en QSound.
2. **Validé en jeu** (fork) :

   | jeu | code | flux | gain mesuré dans l'enregistrement |
   |---|---|---|---|
   | Upper, décor de Guile | `0030` | Y48 | 1,000 ; corrélation 1,0000 hors bruitages |
   | Hyper, Ken ZERO | `0042` | Y57 | 1,00 ± 0,01 |
   | Hyper, Ken ZERO 2 | `0052` | Y71 | 1,00 ± 0,02 |
   | Hyper, Ken ALPHA | `02C2` | Y171 | 1,00 |

   Le flux démarre à l'image où la commande est posée. Les fondus et l'arrêt suivent les commandes du jeu
   (`FF07`, `FF05`). La musique ZERO 3 suivante repasse au Z80.
3. **Aucune donnée de jeu dans le code.**
   - La musique est lue dans `Y_DATA.BIN`. L'utilisateur peut aussi donner l'ISO entière ou `fichier@décalage`.
   - La correspondance code → flux est dans une table texte séparée (`hsfa_flux_table.txt`, 26 Ko, 558 codes). Le
     script `gen_table_flux.py` la produit depuis la table native PS2.
4. **Non-régression.**
   - Upper, 2 500 images, mode 1, aucune musique hors QSound : son et journal **identiques** au fork d'origine.
   - FBNeo, attraction d'Upper en mode 1 : WAV **identique** au cœur d'origine.
   - Les états sauvegardés pendant un flux reprennent à l'échantillon près (MAME et lecteur seul). Dans FBNeo, l'image
     reprend à l'identique.
5. **FBNeo** : branche locale `flux` (commit `dfd2de8`, rien de poussé). J'ai compilé deux cœurs : Linux x86_64 et
   Android arm64. Le cœur Android n'a pas été essayé sur un appareil.

## 1. Conception

### 1.1 Ce que fait le pilote PS2 (relu dans l'ELF et le module)

Le pilote natif (exéc. `0x5A9B40`, cf. SON-HYPER §1.2) recopie la boîte aux lettres, puis :
- pour une commande `< 0x1200` de **type 1** : flux ADX `fid` sur le canal 0, volume `o5` (0-127) ;
- pour une commande `FFxx` : table de sauts `0xB671C0`, fonctions de l'ELF `0x1553D0` à `0x155820`.

| commande | effet sur le flux (PS2) | effet sur le Z80 QSound (mesuré au banc) |
|---|---|---|
| `FF00` | tout arrêter (`0x155A90`) | tout coupe, voix comprises |
| `FF05` | arrêt des flux (`0x155430`) | **musique coupée, voix intactes** |
| `FF06 p v` | fondu vers `v/255` en `0xFFFF/p` images, puis reprise si en pause | — |
| `FF07 p v` | fondu vers `v/255` en `0xFFFF/p` images (`p=FFFF` : 1 image ; `p=00CC` : 321 images = 5,4 s) | même chose : coupure nette ou fondu de 5 s |
| `FF0C`, `FF0D p` | fondu vers 0 | — |

Détails du volume et des fondus :
- **Volume** (`0x155470`, `mult` R5900 à 3 opérandes) : indice = `vol × niveau / 127`. Il passe par une table en
  dB (`0x183E60` = 20·log₁₀(i/127)). L'amplitude vaut donc `vol/127 × niveau/127`.
- **Fondu** (`0x155820`, à chaque image) : linéaire, de l'indice courant vers la cible. Un niveau 0 met le flux en
  pause.
- **Particularité reproduite** : le fondu part de l'**indice** (`vol × niveau/127`), pas du niveau. Au début d'un
  fondu, le son baisse donc d'un coup de `vol/127` (≈ −3 dB).
- `o6 & 0x80` (code `0001` seulement) : le flux démarre en pause et attend `FF06`.

### 1.2 Interception (fork et FBNeo)

Au moment où le 68K écrit `$61801F = 0` (commande posée), et avant que le Z80 ne la voie, le lecteur lit
`cmd = $618001/3`, `v = $618005`, `p = $618007/9`.

| cas | lecteur | Z80 |
|---|---|---|
| musique de la table, jouée en flux : mode 1 = code sans `q` (pas de musique QSound) ; mode 2 = tout sauf `x` | démarre le flux (le précédent s'arrête) | la commande devient **`FF05`** : la musique QSound en cours s'arrête, les voix et bruitages continuent |
| autre musique de la table (`q`, mode 1) | arrête le flux | commande inchangée |
| `FFxx` | appliqué au flux (§1.1) | commande inchangée |
| bruitages, voix | rien | commande inchangée |

Pourquoi `FF05` : un code musique inconnu du Z80 (`0030`) **laisse la musique QSound continuer** (essai `z_a`).
`FF05` la coupe sans toucher aux voix (essais `z_c`, `z_g` ; `FF00` couperait aussi les voix, essai `z_i`).

**Intro (`0001`, drapeau `x`) : jamais en flux.** Les repères `$618021` qui cadencent l'intro viennent du Z80.

### 1.3 Lecteur (`src/hsfa_flux.h`, en-tête seul, C++98, ~370 lignes, commun aux deux émulateurs)

- **Source** :
  - `Y_DATA.BIN` (AFS) ;
  - ou une ISO de l'Anthology : `Y_DATA.BIN` est cherché dans la racine ISO9660 ;
  - ou `fichier@décalage hexa`.
  - Lecture paresseuse par blocs de 64 Ko, pour éviter un à-coup au démarrage (un flux fait jusqu'à 10 Mo).
  - Sous libretro, la lecture passe par la VFS (`RFILE`, `rfseek` 64 bits).
- **Décodage ADX** : CRI type 3, 4 bits. Coefficients calculés depuis la fréquence de coupure de l'en-tête. Échelle
  +1, comme `adx.py`.
  - Boucle prise dans l'en-tête (v3 / v4). L'historique est mémorisé à la trame de début de boucle, pour un retour
    exact.
  - Rééchantillonnage linéaire vers la fréquence de sortie (48 kHz : pas de 1, identité).
- **Mixage** : le flux est ajouté et saturé à la sortie. Le gain suit une rampe sur chaque tick de 60 Hz (pas de
  claquement pendant les fondus).
- **Gain global** : 0,26 × `HSFA_FLUX_VOL` %. Il est calé sur la musique QSound du fork : `0009` QSound −33,0 dBFS
  contre ADX brut −21,5 dBFS, puis vérifié sur `000C`.
- **État sauvegardable** : structure `etat_t` de types simples.
  - Elle garde l'historique d'**avant** la trame en cours. Une reprise d'état ne redécode qu'**une** trame, et ne
    recharge l'en-tête que si le flux a changé.
  - Le coût est donc constant, ce qui reste compatible avec le « run-ahead » de RetroArch.

### 1.4 Table code → flux (`gen_table_flux.py` → `hsfa_flux_table.txt`)

- **Source** : la table native PS2. Elle est lue par défaut dans `agent_hyper_son/table_son_ro9.csv`, ou directement
  dans le module avec `--module ro9`. Les deux sorties sont identiques.
- On garde les entrées de type 1 dont le `fid` n'est pas nul, soit **558 codes**.
- **Format d'une ligne** : `CODE FID VOLUME DRAPEAUX # commentaire`, avec la famille et la durée tirées de
  `ydata_toc.csv`.
- **Drapeaux** :
  - `q` : le Z80 joue aussi ce code (`0001-002F`) ;
  - `p` : démarrage en pause ;
  - `x` : jamais en flux (`0001`).

Familles couvertes : ZERO 3 `0002-002F`, persos d'Upper `0030-0036`, ZERO `0041-004D`, ZERO 2 `0051-0063`, variantes
`0180-01F7`, ALPHA `02C1-02FC`, plus les codes des autres modules.

## 2. Fork MAME (`mame-fork-flux/`, copie `cp -a` du fork ; chemins absolus du dossier `build/` réécrits)

Compilation incrémentale, comme le fork (≈ 20 s) :
`make SUBTARGET=cps2f SOURCES=src/mame/capcom/cps2.cpp TOOLS=0 USE_QTDEBUG=0 NO_USE_PORTAUDIO=1 NO_USE_PIPEWIRE=1 -j4`.

Ajouts dans `cps2.cpp` :
- périphérique son `hsfa_flux_device` (flux 48 kHz stéréo, routé vers le haut-parleur, états sauvegardés) ;
- `hsfa_qsound_w` sur `$618000-$619FFF` dans `hsfa_map` ;
- `src/mame/capcom/hsfa_flux.h`.

| variable | rôle |
|---|---|
| `HSFA_YDATA` | `Y_DATA.BIN`, ou ISO, ou `fichier@décalage`. Sans elle, le lecteur est inactif et le comportement ne change pas |
| `HSFA_FLUX_TABLE` | table (défaut : `hsfa_flux_table.txt` à côté de `HSFA_YDATA`) |
| `HSFA_FLUX` | `1` (défaut) complément ; `2` toutes les musiques sauf l'intro ; `0` inactif |
| `HSFA_FLUX_VOL` | volume en % (défaut 100) |
| `HSFA_FLUX_LOG` | journal des décisions |

Patchs :
- `patchs/sfa3hx-flux-mame0285.patch` : patch complet contre `mame0285`. Il remplace `sfa3hx-mame0285.patch` et
  contient aussi le fork existant.
- `patchs/flux-sur-fork-sfa3hx.patch` : différence avec le fork actuel, soit `cps2.cpp` et le nouvel en-tête.

## 3. FBNeo (`fbneo-flux/`, copie de `fbneo-hsfa-ws`, branche locale `flux`, commit `dfd2de8`)

| fichier | modification |
|---|---|
| `cps_mem.cpp` | crochet dans `CPSQSoundC0WriteByte`, au moment de `$61801F = 0` |
| `qs.cpp` | flux ajouté dans `QsndEndFrame` |
| `cps_hsfa.cpp` | ouverture, état dans `HsfaScan` |
| `cps.h` | déclarations |
| `d_cps2.cpp` | DIP **« PS2 music »** (`Off` / `Missing tracks only` (défaut) / `All tracks`) pour `sfa3hsfa` et `sfa3uhsfa`. RetroArch l'affiche dans les options du cœur (commutateurs DIP) |

**Comment l'utilisateur fournit la musique** : dans le dossier système de RetroArch, créer `fbneo/hsfa/` et y
mettre :
- `Y_DATA.BIN`, extrait de l'ISO (1,82 Go) ;
- **ou** l'ISO, renommée `anthology.iso` ;
- **ou** un fichier `ydata.txt` contenant le chemin du `Y_DATA.BIN` ou de l'ISO ;
- **et** `hsfa_flux_table.txt`.

Sans ces fichiers, le cœur se comporte comme avant (message dans le journal). Sur PC, les mêmes variables que le fork
s'appliquent (`HSFA_YDATA`, `HSFA_FLUX_TABLE`, `HSFA_FLUX` impose le mode, `HSFA_FLUX_VOL`, `HSFA_FLUX_LOG`).

- **Compilation** (`RAPPORT-fbneo.md`, avec `SUBSET=hsfaws`) :
  - `coeurs/fbneo_hsfaws_flux_libretro.so` (Linux, 10,4 Mo) ;
  - `coeurs/fbneo_hsfaws_flux_libretro_android.so` (NDK r28c, arm64-v8a, API 21, 9,2 Mo).
- **Patch** : `patchs/fbneo-hsfa-ws-flux.patch` (`git format-patch`).
  - Sur `master` (`2b57422`), `git apply` échoue sur les deux lignes de pilote de `d_cps2.cpp`.
  - Un `git cherry-pick` du commit passe proprement (essayé dans un clone jetable).

Validation FBNeo (`work/fbneo/tests/hsfa_run`, `sfa3uhsfa.zip`) :
- **Mode 2, attraction** : `002F` → Y47, puis `0019` → Y25, en flux. Y25 est retrouvé dans le WAV à la position de la
  commande, gain 0,995-1,003.
- **Mode 1** : WAV identique au cœur d'origine.
- **`STATETEST` pendant un flux** : image identique.
- **Coût** : non mesurable (≈ 1 000 images/s dans les deux cas).

## 4. Validation (fork)

| essai | résultat |
|---|---|
| `outils/test_flux` contre `adx.py` : Y9 (10 s), Y5 (14 s, deux boucles) | 0 échantillon différent |
| `outils/test_etat` : reprise de l'état d'un lecteur par un autre lecteur, après la boucle, pendant un fondu | 0 / 288 000 |
| injection (`inj.sh`, programme 68K muet) : `0009` QSound, `0030` flux, `FF07 00CC`, voix `0105` | QSound coupé net à `0030` ; flux seul dans la sortie (corrélation 1,0000, gain 1,000, résidu −240 dB) ; fondu de 5,4 s puis pause ; la voix passe (`wav/inj_qsound0009_puis_flux0030_fondu.wav`) |
| même injection en mode 2 | `0009` en flux Y9, au même niveau que le QSound (−30/−31 dBFS) |
| état MAME (Lua `save`/`load` pendant un flux, `etat_flux.lua`) | WAV après rechargement identique : 0 / 303 360 |
| **Upper**, VERSUS, décor `$FF8100 = $40` imposé pendant la sélection (`DECOR=40:1950-2640`, `flux_journal.lua`) | voir ci-dessous |
| **Hyper**, VERSUS Ken ZERO / ZERO 2 (`tournee_hyper.lua`, 9 000 images, 9 manches, 0 exception) | `0042` → Y57, `0052` → Y71, deux fois chacun ; arrêts et fondus aux fins de match ; `0002`/`0004` au Z80 |
| **Hyper**, Ken ALPHA | `02C2` → Y171 ; le flux démarre à 21,363 s pour une commande à l'image 1274 (= 21,362 s) |
| non-régression Upper (mode 1, 2 500 images) | WAV et journal identiques au fork d'origine |

Détail de l'essai Upper :
- En VERSUS, Upper choisit la musique par le **décor** : `T_613380[$FF8100]`, indice en octets (`$40` → `0030`).
- Le jeu envoie `FF07 FFFF` puis `0030`. Le flux Y48 joue dans le décor de Guile.
- Gain 1,00 dans toutes les fenêtres ; corrélation 1,0000 et résidu −86 dB après le K.O.
- Extrait : `wav/upper_vs_decor_guile_0030_Y48.wav`.

Pour Hyper, les gains de 1,00 ± 0,02 et le décalage constant prouvent la présence exacte du flux. La corrélation
brute (0,3-0,7) est faible à cause des bruitages du combat automatique.

**WAV de contrôle** (`wav/`, 14 s chacun) :
- `upper_vs_decor_guile_0030_Y48.wav` ;
- `hyper_ken_zero_0042_Y57.wav` ;
- `hyper_ken_zero2_0052_Y71.wav` ;
- `hyper_ken_alpha_02C2_Y171.wav` ;
- `inj_qsound0009_puis_flux0030_fondu.wav`.

**Lanceurs** :
- `inj.sh` : injection, avec un rompath propre `rp_inj/`. Celui de `agent_son_ro5/hybride/rp_inj` a des liens
  relatifs cassés.
- `upper.sh` : Upper, variables de `nonreg_ro5.sh`, plus `PERSO2` et `DECOR`.
- `hyper.sh` : Hyper, modèle `agent_hyper_etats/lance.sh`, scénario `tournee_hyper.lua`.
- Tous passent par `lua/flux_journal.lua` (journal des commandes avec le numéro d'image).

**Outils** : `outils/rms.py`, `niveau.py`, `correl.py`, `cherche.py` (corrélation FFT), `compare_ref.py`,
`extrait.py`.

## 5. Limites

- **Variantes non validées en jeu.** Les variantes `0180-01F7` (X-ISM, EX, CLASSIC) et le 2ᵉ code `$C3B6` ne l'ont pas
  été. Elles passent par le même chemin et sont dans la table.
- **Démarrage en pause non reproduit.** Le pilote PS2 démarre aussi un flux en pause quand un octet du jeu
  (`[0x70001114]-0x3E00`) vaut 5. Je n'ai pas trouvé à quoi correspond cet octet, donc ce cas n'est pas reproduit.
  Seul le drapeau `p` de la table compte, et il ne concerne que `0001`, qui reste au Z80.
- **Volume** :
  - Le volume « musique » des options PS2 (`+20`, défaut supposé 127) n'est pas lu.
  - Le rapport musique/bruitages est calé sur la musique QSound, pas sur la PS2.
  - Le volume numérique CPS2 (`$804030`) ne s'applique pas au flux.
- **Tick des fondus** : 60 Hz en temps de son (la PS2 compte en vsync). Dans FBNeo, le flux est rendu par trame
  entière : une commande prend effet au début du tampon de la trame, soit ≤ 17 ms d'avance.
- **Hyper n'existe pas dans FBNeo** (seulement `sfa3hsfa` / `sfa3uhsfa`). Le DIP marche aussi pour SFA3 traduit : en
  mode « All tracks », les musiques SFA3 sont jouées par les flux PS2.
- **Upper au banc** : le décor a été imposé pour obtenir la musique de Guile. Le choix naturel (Arcade contre Guile)
  passe par le même code.
- Le cœur Android n'a pas été essayé sur un appareil, en particulier le débit de lecture par la VFS sur une carte SD.

## 6. Tailles

| élément | taille |
|---|---|
| code | `hsfa_flux.h` 15,5 Ko ; ajouts de 115 lignes dans `cps2.cpp` (MAME) et de 146 lignes dans FBNeo |
| table | 26 Ko (558 codes) |
| données lues chez l'utilisateur | `Y_DATA.BIN` 1,82 Go (ou l'ISO de 4,7 Go) ; aucune copie |
| mémoire | le flux en cours (≤ 10 Mo pour les plus longs, 1 à 5 Mo d'habitude), chargé par blocs de 64 Ko |
| état sauvegardé | ≈ 140 octets |
| dossier | `essais/` 166 Mo (WAV complets, supprimables) ; `mame-fork-flux/` 1,9 Go et `fbneo-flux/` 261 Mo (copies de travail) |
