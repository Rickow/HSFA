# OPTIONS.md — rendre les options accessibles (SFA3 `ro3`, Upper `ro5`, Hyper `ro9`)

Agent `agent_options`, 2026-10-11. J'ai écrit seulement dans `work/agent_options/`. Les outils partagés
(traducteur, fork MAME, arbres FBNeo, `work/mame*`), la configuration PCSX2 et ses sauvegardes ont été lus, jamais
modifiés.

## 0. En bref

1. **Correction du §102.** `0x118A60` est un simple `memcpy` de l'exécutable : la tâche OPTION copie la sauvegarde
   de l'Anthology (`0x3000` octets). L'écran d'options est du **code C du portage, dans le module** :
   - SFA3 `0x573E20` → `0x57A2xx`, Upper `0x5F22E0`, Hyper `0x214AB0` → `0x21Cxxx` (adresses d'exécution) ;
   - textes Shift-JIS dessinés par le GS (`0x150340`), donc aucun graphisme CPS2 ;
   - réglages rangés dans la sauvegarde de l'Anthology, `*(0x19E438)` = `0x19D1000`.

   À la sortie de l'écran, une fonction C les recopie **dans les octets de configuration de l'EEPROM arcade**
   (`$A0`-`$A5`, `$DE`-`$DF` de A5). Le traducteur ne sait pas exprimer ce C : la recopie est perdue et la tâche
   OPTION traduite attend sans fin (écran noir).
2. **Le jeu traduit lit toujours ces octets**, aux mêmes endroits que l'arcade. Au démarrage, il y range les valeurs
   par défaut du portage, qui sont celles de la PS2 (difficulté 5 étoiles, etc.). Il ne lit **ni l'EEPROM ni le menu
   de test CPS2** : aucun accès à `$804040`, et le portage a retiré ce code. La voie (c) est donc fermée sans greffe
   de code arcade.
3. **Voie retenue : (b) + correctif ROM.**
   - **ROM, traducteur.** `OPTION_RETOUR=1` (défaut) : l'adresse de la tâche OPTION se convertit en celle de la
     routine de sortie de l'écran, qui est traduite. OPTION ramène donc au menu des modes, curseur sur OPTION, dans
     les trois jeux, au banc comme dans le cœur. `EXIT_RETOUR=1` fait de même pour EXIT, qui donnait aussi un écran
     noir. Avec les deux interrupteurs à `0`, les ROM sont identiques à l'octet (8/8 × 3 jeux).
   - **Cœur FBNeo.** 24 réglages dans « Options du cœur » (DIP `Option: …` / `Extra option: …`), écrits dans la RAM
     à chaque passage au menu des modes. « Game default » n'écrit rien. `HSFA_OPTIONS=0` coupe tout.
   - **Banc MAME.** `lua/banc_options.lua` fait la même chose avec des variables `HSFA_OPT_*`.
4. **Validation.**
   - Chrono infini (Hyper : `∞` affiché ; SFA3 : chrono arrêté), chrono rapide (Upper : 37 contre 69 à la même
     image), 1 manche, VS MODE 2P = COM (Ken joue seul) : captures.
   - Options par défaut : **captures identiques** au cœur actuel (Hyper 60/60, SFA3 30/30, Upper 30/30), journaux
     et niveaux sonores identiques, états de sauvegarde de même taille et restaurés à l'identique.

## 1. L'écran OPTION de l'Anthology (ce que fait la PS2)

### 1.1 Mécanique (vidages EE `menu_option` pour SFA3 et `ee_hyper.bin` ; image ELF + module pour Upper)

| rôle | SFA3 (`ro3`) | Upper (`ro5`) | Hyper (`ro9`) |
|---|---|---|---|
| tâche OPTION créée par le menu (C, `A5 = base`, `memcpy(sauvegarde → copie, 0x3000)`, automate d'états) | `0x573E20` (table `0x59DEF8`) | `0x5F22E0` | `0x214AB0` (table `0x5B10F8`) |
| dessin d'une liste de textes (`{drapeaux, couleur, x, y, ptr}`, Shift-JIS, GS natif `0x150250-0x150340`) | `0x5793C0`, table `0x59DC60` | — | `0x218690`, table `0x5B0E60` |
| sortie de l'écran (enregistre, applique, met A5+0..A5+$B à zéro, crée la tâche du menu, se termine) | `0x5792E0` | `0x5F72E0` | `0x2185B0` |
| **application** (recopie dans la RAM du jeu) | `0x579990` | `0x5F7990` | `0x218C30` |
| bloc des réglages dans la sauvegarde (`0x19D1000 +`) | `0x33C` | `0xF5C` | `0x1F9C` |
| tâche relancée par la sortie | `0x237DD0` | — | `0x2526E0` (menu ; garde le curseur seulement s'il vaut OPTION) |

Le menu racine de l'écran PS2 comporte GAME OPTION, CONTROLLER SETTINGS, SOUND OPTION, DISPLAY ADJUST, SAVE/LOAD
et EXIT. Un menu caché, SECRET OPTION, donne accès aux EXTRA OPTION (1)-(4). Textes complets :
`decomp/ro3_textes.txt` et `decomp/ro9_textes.txt`.

### 1.2 Inventaire des réglages et de leur lecture dans le jeu traduit

Conventions :
- le C du portage écrit en **adresses hôte** (A5 PS2 + d), qui sont les décalages de l'arcade ;
- dans la traduction, un octet hôte `d` est l'octet 68K `d ^ 1` (A5 = `$FF8000`) ;
- défaut = valeur de la PS2, identique à celle que la traduction charge au démarrage.

| réglage (écran PS2) | sauvegarde SFA3 / Upper / Hyper | octet arcade (= hôte) | **adresse CPS2 traduite** | valeurs | effet (lecteurs dans les ROM livrées) |
|---|---|---|---|---|---|
| DIFFICULTY | `0x33C` / `0xF5C` / `0x1F9C` | `$A0` | **`$FF80A1`** | 0-7 (8 étoiles), défaut 4 | copié dans la difficulté courante `$BF` au début du mode (SFA3 `$4CDB2`, Upper `$57864`, Hyper `$FDC4`) |
| DAMAGE LEVEL | `+1` | `$A1` | **`$FF80A0`** | 0-3, défaut 1 | dégâts (SFA3 `$4FF2`, Upper `$53BC`, Hyper `$7D9E`) |
| TIMER SPEED | `+2` | `$A2` | **`$FF80A3`** | 0-3, **4 = INFINITY** (absent de l'arcade), défaut 1 | vitesse (table : SFA3 `$4F0BE`, Hyper `$119C0`) ; `∞` dans le HUD (SFA3 `$1FFD6`, Hyper `$2DD8`) ; TRAINING force 4 au début du mode (SFA3 `$4CDC0`, Hyper `$FDD2`) |
| SPEED SELECT | `+3` | `$A3` | **`$FF80A2`** | 0 NORMAL, 1 TURBO1, 2 TURBO2, 3 FREE1, 4 FREE2 ; défaut 2 | vitesse du jeu (SFA3 `$2D3F2`…, Hyper `$FEE2`, `$79E26`) |
| MAX ROUND (1P) (Hyper : « MAX ROUND ») | `+4` | `$DE` | **`$FF80DF`** | 0-2 = 1/3/5 manches, défaut 1 | manches gagnantes ; Hyper recopie ce champ dans le champ VS au début du match (`$FDDC`) |
| MAX ROUND (VS) (SFA3, Upper) | `+5` | `$DF` | **`$FF80DE`** | idem | idem en VERSUS |
| JOIN IN (SFA3, Upper) | `+6` | `$A4` | **`$FF80A5`** | 0 OFF, 1 ON, défaut 1 | entrée d'un 2ᵉ joueur ; SURVIVAL le coupe (`$4CDAE`) |
| (version, SECRET OPTION) | `+7` | `$BB` | `$FF80BA` | — | aussitôt écrasé par la fonction d'application (`$BB` = résultat d'un test) |
| VS MODE (1P) / (2P) | `+8` / `+9` | SFA3 `A5-$3EF0/-$3EEF`, Upper/Hyper `A5-$3CF0/-$3CEF` | **SFA3 `$FF4111`/`$FF4110`, Upper/Hyper `$FF4311`/`$FF4310`** | 0 HUMAN, 1 COM | recopié dans `$124` du joueur (`$524`/`$924`) à l'init. VERSUS (Hyper `$1073E`, SFA3 `$4D5D0`, Upper `$581B0`) : côté joué par l'ordinateur |
| EXTRA OPTION (1) | `0x346` / `0xF66` / `0x1FA6` | SFA3 `A5-$3E5B`, Upper `-$3C59`, Hyper `-$3C46` | **SFA3 `$FF41A4`, Upper `$FF43A6`, Hyper `$FF43BB`** | bits 0-5 : VITALITY 1P/2P (NORMAL/RECOVER), SP GAUGE 1P/2P (NORMAL/RECOVER), SP GAUGE (LV3 START/LV0 START), GUARD GAUGE (ON/OFF) | petites fonctions « BTST » traduites (Hyper `$1B28`-`$1B50`, SFA3 `$91C1A`…). Exemple : le bit 4 coupe le remplissage de jauge `$10FA2` |
| EXTRA OPTION (2) | `+1` | `+1` | **SFA3 `$FF41A7`, Upper `$FF43A9`, Hyper `$FF43BA`** | bits 0-5 : GUARD DAMAGE, COUNTER DAMAGE, GROUND GUARD, MID-AIR GUARD, THROW, THROW ESCAPE (ON/OFF) | Hyper `$1B58`-`$1B80` |
| EXTRA OPTION (3) | `+2` | `+2` | **SFA3 `$FF41A6`, Upper `$FF43A8`, Hyper `$FF43BD`** | bits 0-4 : BREAK FALL, DEFENSIVE ROLL (ON/OFF), COMMAND TIMER (ARCADE/LONG), FRIENDSHIP (NORMAL/INFINITY), ALPHA COUNTER (ON/OFF) | Hyper `$1B88`-`$1BA8` |
| CONTROLLER SETTINGS (affectation des boutons J1/J2, VIBRATION) | `0x34C` / `0xF6C` / `0x1FAC` (8 o) | `A5-$3E8E` / `-$3C8E` | — | matrice de bits | lue par la couche manette **native** (`0x381900` / `0x241B0`), identité dans la traduction : remplacée par le remappage de RetroArch / MAME |
| SOUND OPTION (MONAURAL/STEREO, VOLUME, SOUND TEST), DISPLAY ADJUST, SAVE/LOAD | exécutable | — | — | — | propres à la PS2 (son, image, carte mémoire) : sans objet sur CPS2 |

Le même fichier de sauvegarde porte aussi les palettes modifiées (`+0x2840`) et des records (`+0x36C`, `+0x8DC`). La
fonction d'application les recopie, mais ce ne sont pas des réglages de l'écran OPTION.

### 1.3 Comparaison avec l'arcade (EEPROM, menu de test)

- **Mêmes champs que l'arcade.** Le menu de test de SFA3 (CONFIGURATION / GAME) propose DIFFICULTY, DAMAGE LEVEL,
  TIMER SPEED, GAME SPEED, 1P MAX ROUND, 2P MAX ROUND, EVENT et JOIN-IN. Ce sont les octets 0x10-0x17 de l'EEPROM,
  rangés en `$A0, $A1, $A2, $A3, $DE, $DF, $A5, $A4` (arcade `$1B5C` / `$1C54`).
- **Ce que la PS2 change.**
  - INFINITY s'ajoute au chrono ;
  - les manches passent à 1/3/5 (l'arcade va jusqu'à 7) ;
  - EVENT (`$A5` arcade) disparaît ;
  - VS MODE et les EXTRA OPTION s'ajoutent (hors EEPROM).
- **Le jeu traduit ne lit plus l'EEPROM** : aucun accès à `$804040` dans les trois ROM. Le portage a remplacé les
  routines EEPROM, le menu de test et l'interrupteur TEST (COUVERTURE-ARCADE). Au démarrage, la traduction charge les
  défauts du portage depuis une table de données (Hyper `$9EBC`, table `$14B560` ; SFA3 `$A6xx`).
- Pour passer par l'EEPROM et le menu de test CPS2 (voie c), il faudrait greffer le mode test et l'EEPROM arcade
  (`$D800`-`$11000` et `$1B8E`-`$2578`, environ 10 Ko, 64 appels sortants : P3 de `agent_couverture`). Cela ne vaut
  que pour SFA3 (ses menus), sans INFINITY ni les options console.

## 2. Choix et coûts

| voie | coût | pour | contre |
|---|---|---|---|
| **(b) options du cœur + Lua du banc** (retenue) | fait : ~50 lignes C, 110 lignes de DIP, 60 lignes Lua | menu natif de RetroArch (manette, console), tous les réglages PS2 utiles, réglable en jeu | effet au **prochain passage au menu des modes** ; options mémorisées par RetroArch (fichier d'options du jeu), pas par le jeu |
| **correctif ROM OPTION/EXIT** (retenu) | fait : ~30 lignes du traducteur (`mame_test.py`, `profils.py`) | plus d'écran noir, au banc comme dans tous les cœurs, sans code de cœur | OPTION ne montre pas d'écran : retour direct au menu des modes |
| (a) écran d'options en 68K dans le programme traduit | **1,5 à 3 jours**, détail ci-dessous | indépendant du cœur, aspect « jeu » | texte à afficher (scroll1 converti par le banc pour SFA3, bases de plans pour Upper/Hyper), entrées, 3 modules, essais banc + FBNeo + 16:9 ; pas de sauvegarde sans réintroduire l'EEPROM |
| (c) menu de test CPS2 / EEPROM | greffe ~10 Ko (P3), moyen | réglages persistants (EEPROM émulée) | SFA3 seulement, sans les options console ; le jeu traduit ne lit pas l'EEPROM aujourd'hui |

Ce que demanderait (a) :
1. Une tâche 68K écrite à la main, à l'adresse où pointe OPTION ; le même mécanisme de table que le correctif
   remplacerait la routine de sortie par cette tâche.
2. Le contenu de cette tâche :
   - effacer l'écran avec les fonctions traduites déjà appelées par la tâche OPTION (Hyper `0x57F330` / `0x57AB50`) ;
   - écrire 9-12 lignes de texte ;
   - lire les fronts de manette (`$C214`/`$C218` de A5) ;
   - modifier les octets du §1.2 ;
   - à EXIT, sauter à la routine de sortie traduite.
3. Le texte. Les libellés du menu des modes sont des objets (effet `$78`, frames de type `$0A`, lettres
   `0x0200|car`) : on pourrait réutiliser ce moteur avec des frames neuves en données. L'autre voie est le texte
   scroll1 avec la police 8×8 du menu de test arcade, présente dans la ROM graphique.

Estimation : 300-400 lignes 68K (vasm), plus données et essais. À faire si l'on veut un écran « dans le jeu » ;
(b) reste utile pour les consoles.

## 3. Ce qui est livré

### 3.1 Traducteur : `diffs/traducteur_option_exit.diff` (copie de travail `untranspile/`)

- `profils.py` : `option = (tâche OPTION, sortie de l'écran, créer une tâche, finir une tâche, curseur des modes)`
  par module :
  - ro3 `(0x573E20, 0x5792E0, 0x21F710, 0x21F8E0, $FF4001)` ;
  - ro5 `(0x5F22E0, 0x5F72E0, 0x222CE0, 0x222EB0, $FF4201)` ;
  - ro9 `(0x214AB0, 0x2185B0, 0x22F660, 0x22F830, $FF4201)`.
- `mame_test.py` :
  - **`OPTION_RETOUR`** (défaut 1) : dans la table des adresses de code (dichotomie `$3E0000` et hachage `$3C0000`),
    la tâche OPTION reçoit l'adresse traduite de la routine de sortie (SFA3 `$91C26`, Upper `$9E452`, Hyper `$19F2`).
    4 octets changent dans `sz3.10b`.
  - **`EXIT_RETOUR`** (défaut 1) : l'appel natif `0x1CAC80` du choix EXIT passe par un tremplin en `$804` (libre
    entre le RTE `$802` et `STUB_ANIM` `$810`). Ce tremplin mène à un talon en `CODECONV-$20` :
    `MOVE.B #5,curseur ; MOVE.W #$40,D0 ; LEA sortie,A0 ; JSR créer ; JMP finir`.
    - Il fallait une nouvelle tâche : le menu tourne dans l'emplacement `$80`, celui que la sortie recrée.
    - Il fallait aussi le curseur sur OPTION : sinon la tâche relancée démarre le mode du curseur (EXIT
      recommence, VERSUS part).
- **Interrupteurs à 0** : ROM identiques à l'octet aux ROM actuelles du banc (`work/mame/roms_tr`,
  `mame_ro5/roms_ro5`, `mame_ro9/roms_ro9` : 8/8 chacune), ainsi que `carte_image.txt` et `ext_liste.txt`.
- ROM construites :
  - avec les deux interrupteurs à 1 : `build/ro{3,5,9}_r2/`, 3 jeux de 8 fichiers ;
  - OPTION seul : `r1` ;
  - interrupteurs à 0 : `r0` et `_z`.
- Zips d'essai (sans flux ni rejeu) : `zips/r0`, `zips/r1`, `zips/r2`.

### 3.2 Cœur FBNeo : `diffs/fbneo_options.diff` (clone `fbneo/`, branche `rejeu` @ `3bc21ed`, non commité)

- `cps_hsfa.cpp` : `HsfaOptions()`, appelé à chaque fin d'image (`HsfaFrameDone`).
  - Si `$FF8000 = 4` (menu des modes, mêmes valeurs dans les trois jeux), il écrit les octets du §1.2 choisis dans
    les DIP.
  - Valeur 0 (« Game default ») : rien n'est écrit pour ce réglage.
  - `HSFA_OPTIONS=0` : aucune écriture.
  - Pas de nouvelle variable d'état : la taille des états est inchangée.
- `d_cps2.cpp`, entrées `Dip B`-`Dip H` (`HsfaOptDip[7]`) :
  - jeu : `Option: Difficulty`, `Damage level`, `Timer speed` (dont Infinity), `Speed select`, `Max round (1P)` /
    `(VS)` (Hyper : `Max round`), `VS mode (1P)` / `(2P)`, `Join in` (SFA3/Upper) ;
  - 17 `Extra option: …`.

  Les libellés suivent l'écran PS2, avec « (PS2 default) » sur la valeur par défaut. Clés RetroArch :
  `fbneo-dipswitch-<jeu>-Option__Timer_speed`, etc.
- `cps.h` : déclaration. `hsfa/hsfa_run.c` (lanceur d'essai) :
  - `HSFA_VARS="clé=valeur;…"` sert les options du cœur ;
  - `HSFA_VARS2` / `HSFA_VARS2_IMAGE` les changent en cours de partie.
- **Cœur Linux de test** : `coeurs/fbneo_hsfa_libretro_options.so` (md5 `f3c4e7f9…`). Cœur de référence reconstruit
  sans modification : `coeurs/ref_3bc21ed.so`. Lanceur : `coeurs/hsfa_run`.

### 3.3 Banc MAME : `lua/banc_options.lua`

Le script se charge par `dofile` depuis un scénario, comme `banc_mem.lua`. Exemple : `lua/essai_tournee_options.lua`.

- Variables, toutes facultatives : `HSFA_OPT_DIFFICULTE` 1-8, `_DEGATS` 1-4, `_CHRONO` 1-5 (5 = infini),
  `_VITESSE` 1-5, `_MANCHES` / `_MANCHES_VS` 1-3, `_VS1P` / `_VS2P` 1 humain, 2 COM, `_JOIN` 1-2, `_EXTRA=p1,p2,p3`
  (hexa).
- `HSFA_OPT_DIP` reprend les octets DIP B-H du cœur. `HSFA_OPT_JEU` est déduit de `BANC_COMMUN`.
- Sans variable : le script ne fait rien.

## 4. Validation (cœur Linux, `hsfa_run`, et fork `sfa3hx`)

| essai | résultat |
|---|---|
| OPTION, ROM actuelle (r0) | écran noir dans les 3 jeux (`captures/sfa3_option_avant_ecran_noir.png`) |
| OPTION, ROM corrigée | retour au menu ~20 images après, curseur sur OPTION, menu réactif (Bas → EXIT, Haut → OPTION, TRAINING) dans les 3 jeux, FBNeo et MAME (`captures/*_option_retour_menu.png`) |
| EXIT, ROM corrigée | retour au menu, curseur sur OPTION, dans les 3 jeux. L'écran se relance deux fois (~30 images) avant de se stabiliser (`captures/exit_retour_menu_sfa3_upper_hyper.png`) |
| Hyper, `Timer speed = Infinity` | `$FF80A3 = 4`, `∞` dans le HUD (FBNeo et MAME : `captures/hyper_chrono_infini_*.png`, `mame_banc_hyper_chrono_infini.png`) |
| SFA3 (Arcade), Infinity | chrono **arrêté** ; le symbole `∞` ne s'affiche pas (case vide, `captures/sfa3_chrono_zoom_*.png`) : voir §5 |
| Upper (Arcade), `Timer speed = 4 stars` | 37 contre 69 à l'image 3000 (`captures/sfa3_upper_*.png`) |
| Hyper, `Max round = 1` | 1 manche par sélection au lieu de 2 (journal) |
| Hyper, `VS mode (2P) = COM` | Ken saute et attaque seul (`captures/hyper_vsmode2p_com_*.png`) |
| Hyper TRAINING avec `Timer speed = 2 stars` | `$A3` reste 4 (infini) : l'init. du TRAINING passe après l'écriture du menu |
| changement en cours de session (`HSFA_VARS2`) | pris au passage suivant au menu des modes. Un enchaînement VERSUS (sélection → match → sélection) ne repasse pas par le menu. L'écriture à la sélection a été essayée puis **retirée** : elle écrasait le chrono infini du TRAINING |
| **non-régression, options par défaut** | Hyper, tournée VERSUS de 6 000 images : **60/60 captures**, journal et niveaux sonores identiques au cœur de référence avec la ROM actuelle. Vrai avec ROM r0, r1 et r2, et avec `HSFA_OPTIONS=0` plus un DIP actif. SFA3 et Upper, partie scriptée de 9 000 images : **30/30** captures et journaux identiques (r0 et r2) |
| états de sauvegarde (Hyper, `STATETEST=1300`) | 658 217 o comme la référence, image identique après restauration |
| ROM avec interrupteurs à 0 | 8/8 × 3 identiques aux ROM du banc |

Scripts : `essais/lance.sh`, `essais/nonreg_su.sh`, `essais/mame_hyper.sh`.

## 5. Remarques et suites

- **SFA3, `∞` invisible.** Les tuiles `$261F` / `$263F` qu'écrit le HUD (`$1FFE2`) s'affichent vides. C'est à
  regarder dans les banques / plans de SFA3 ; le chrono, lui, est bien infini. Hyper affiche `∞`.
- **Chrono du TRAINING (hypothèse, non vérifiée)** :
  - le TRAINING force `$A3 = 4` et, sur PS2, la fonction d'application rétablissait le réglage au mode suivant ;
  - dans la traduction, cette recopie est perdue ;
  - un VERSUS lancé après un TRAINING garderait donc le chrono infini ;
  - avec `Timer speed` réglé, le cœur rétablit la valeur au menu.
- **Libellés des EXTRA OPTION** : repris de l'écran PS2, bit à 0 = 1ʳᵉ valeur.
  - « SP GAUGE : LV3 START » est la valeur par défaut. Le bit 4 commande une routine de remplissage de jauge
    (`$10FA2`, sous conditions) : sens exact à confirmer en jeu.
  - Les autres bits n'ont pas été essayés un par un.
- **À reconstruire pour livrer** :
  - les ROM, avec le traducteur corrigé (appliquer le diff, puis `valide_tout.sh`) ;
  - les zips (`paquet_fbneo.py`, sans changement) ;
  - les cœurs Android / ROCKNIX / 16:9 depuis la branche portant le diff FBNeo (`construit_coeurs.sh`).
- Mémorisation : RetroArch garde les DIP par jeu (« Enregistrer les options du jeu ») ; pas d'EEPROM.

## 6. Fichiers

`OPTIONS.md` · `diffs/traducteur_option_exit.diff` · `diffs/fbneo_options.diff` · `lua/banc_options.lua`,
`lua/essai_tournee_options.lua` · `coeurs/fbneo_hsfa_libretro_options.so`, `coeurs/ref_3bc21ed.so`,
`coeurs/hsfa_run` · `captures/` · `untranspile/` (copie corrigée du traducteur) · `fbneo/` (clone modifié) ·
`build/` (ROM r0/r1/r2/_z) · `zips/` · `essais/` · `decomp/` (décompilations Ghidra du C du portage, textes, listes
68K) · `outils/` (désassembleurs MIPS/68K, `decomp_plage.py`, `textes.py`, `cherche_option.py`, `xref_abs.py`, copie
de `paquet_fbneo.py`).
