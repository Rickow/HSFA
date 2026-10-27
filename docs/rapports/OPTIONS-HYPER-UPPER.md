# OPTIONS-HYPER-UPPER.md — les réglages d'Hyper dans Upper

Agent `agent_options_hyper`, 2026-10-17. J'ai écrit seulement dans `work/agent_options_hyper/`. Tout le reste a été lu
sans être modifié : traducteur partagé, `work/mame*`, arbres FBNeo, dépôt GitHub, `max/`. PCSX2 n'a pas été touché.
Les réglages PS2 ont été lus dans les vidages EE déjà copiés (`work/etats_ps2/ee/`).

## 0. En bref

1. **Upper a déjà presque tout ce qu'a Hyper.** Les deux écrans d'options partagent le même code C et les mêmes
   textes. Côté GAME OPTION et EXTRA OPTION, Hyper est un **sous-ensemble** d'Upper. Dans la ROM Upper traduite, chaque
   réglage d'Hyper a un octet et un lecteur, et le cœur actuel les propose déjà pour Upper :
   - le chrono INFINITY : `∞` s'affiche et le chrono reste arrêté (capture) ;
   - les 17 bits des EXTRA OPTION (1)-(3) : 17 lecteurs, et deux bits vérifiés à l'écran.

   Ce sont les cas « l'octet suffit ».
2. **Un seul réglage est propre à Hyper : le BGM**, à 3 valeurs : 【RANDOM】, 【1P】, 【2P】.
   - On le règle sur la page RANDOM PLAYER du menu de pause. Il est rangé en `+0x1FAB` de la sauvegarde, puis en
     `$FF43B5`.
   - Il choisit le thème du perso de J1 ou de J2. Upper joue à la place la musique **du décor** en VERSUS, en TRAINING
     et dans le VERSUS caché (mode 7).
   - Le code manquait dans Upper. **La greffe est faite** :
     - côté traducteur, `BGM_UPPER` : un talon de 86 octets ;
     - côté cœur, l'option « Option: BGM (versus, training) » ;
     - côté banc, `HSFA_OPT_BGM`.
   - Validation : le journal des commandes son et des WAV montrent l'effet, au cœur comme au banc MAME.
3. **Options par défaut = Upper inchangé, au cycle près.**
   - La ROM `BGM_UPPER=1` ne diffère que dans une zone libre jamais exécutée. Le cœur ne pose le saut vers le talon que
     si le réglage est choisi, et seulement en VERSUS, TRAINING et mode 7.
   - Résultats : partie Arcade scriptée 30/30 captures identiques au cœur actuel, VERSUS scripté 16/16, journaux
     identiques, banc MAME identique.
   - Avec `BGM_UPPER=0`, la ROM est identique à l'octet (22/22 fichiers), et SFA3 aussi (20/20).
4. **Sans objet** :
   - MAX ROUND unique : Upper a les deux champs ;
   - EXTRA OPTION (4) : page vide et inaccessible dans les deux jeux ;
   - les versions de RANDOM MODE (ZERO, ALPHA…) : ce sont des modes, exclus par la demande ;
   - les persos EX de RANDOM PLAYER : effectif d'Hyper ;
   - les bits de version `0`, `2`, `6` testés par Hyper : toujours à 0.
5. **Deux erreurs de documentation corrigées** (voir §1.4) :
   - les 8 octets `+0xF6C` / `+0x1FAC` ne sont pas les CONTROLLER SETTINGS, mais la grille de version de SECRET OPTION ;
   - `SON-HYPER.md` §2.2 inverse le rôle du réglage `$C3B5`.

## 1. Inventaire comparé (Upper `ro5` / Hyper `ro9`)

### 1.1 Sources

- **Textes.** Les tables de listes `{drapeaux, couleur, x, y, ptr}` sont en Upper `0x626550` (nouvelle, absente
  d'OPTIONS.md) et en Hyper `0x5B0E60`. Fichiers : `ro5_textes.txt`, `ro9_textes_complet.txt` et les chaînes
  `ro{5,9}_chaines.txt`.
  - Différences de chaînes, et il n'y en a pas d'autre : MAX ROUND(1P)/(VS), JOIN IN et SCORE RESET (Upper
    seulement), les trois BGM (Hyper seulement), et les versions de RANDOM MODE (Hyper seulement).
- **Code C.** Upper a été décompilé de `0x5F2000` à `0x5F7240` (`decomp/ro5_option.c`, Ghidra dans mon dossier).
  Hyper a été comparé à `agent_options/decomp/ro9_port.c`. La GAME OPTION, l'EXTRA OPTION et la SECRET OPTION ont la
  même logique, à quelques écarts près :
  - nombre d'entrées ;
  - deux tables ;
  - pour Hyper : `0x2150E0`, `0x2157F0`, `0x215D10`, la page RANDOM PLAYER `0x21C610` et le dessin `0x21B1F0` ;
  - pour Upper : `0x5F2930`, `0x5F3250`, `0x5F3770`.
- **Application** (recopie dans la RAM du jeu) : Upper `0x5F7990`, Hyper `0x218C30`. Hyper copie en plus
  `+0x1FAB → A5-$3C4C` (le BGM), ainsi que 8 longs `+0x134`… au lieu de 4 (les réserves RANDOM PLAYER par joueur).
- **Réglages PS2 réels.** Les 46 vidages EE de `work/etats_ps2/ee/` ont tous la même sauvegarde (`*(0x19E438)` =
  `0x19D1000`) :
  - SFA3, Upper et Hyper : `04 01 01 02 01 01 01 00 | 00 00 | 00 00 00 | … | FF` ;
  - bits de version tous à 0 ;
  - réserves RANDOM à 0 ;
  - BGM d'Hyper = `$FF` (RANDOM).

  Les défauts de la traduction sont les mêmes. Je n'ai pas lu les cartes mémoire : leur copie m'a été refusée, et les
  vidages suffisaient.

### 1.2 Tableau

Adresses : celles de la traduction (68K) ; octet hôte `d` = octet 68K `d ^ 1`.

| réglage d'Hyper | valeurs / effet dans Hyper | Upper : écran PS2 | Upper traduit : octet + lecteur | cas |
|---|---|---|---|---|
| DIFFICULTY | 8 étoiles | identique | `$FF80A1` → `$BF` | déjà dans le cœur |
| DAMAGE LEVEL | 4 | identique | `$FF80A0` | déjà dans le cœur |
| TIMER SPEED **INFINITY** | 0-3, 4 = ∞ | **identique** (0-4, texte INFINITY) | `$FF80A3` = 4 : lecteurs en `$2986A` (HUD `∞`), `$543DA`, `$544FC`, `$58C56`, table `$59DAE` ; le TRAINING force 4 en `$57872` | **le code existe** : `∞` affiché et chrono arrêté (`captures/upper_chrono_infini_*.png`) ; déjà dans le cœur (« Infinity ») |
| SPEED SELECT | NORMAL, TURBO1/2, FREE1/2 | identique | `$FF80A2` ; FREE (≥ 3) : choix à la sélection (`CMPI.B #3,$A2(A5)` Upper `$557CA`, Hyper `$78F62`) | déjà dans le cœur |
| **MAX ROUND** (un seul) | 1/3/5 ; Hyper recopie le champ 1P dans le champ VS au début du match | MAX ROUND (1P) **et** (VS) | `$FF80DF` / `$FF80DE` | **sans objet** : Upper a plus. Pour imiter Hyper, mettre la même valeur aux deux |
| VS MODE (1P)/(2P) | HUMAN, COM | identique | `$FF4311` / `$FF4310` | déjà dans le cœur |
| EXTRA OPTION (1) : VITALITY 1P/2P, SP GAUGE 1P/2P, SP GAUGE (LV3/LV0 START), GUARD GAUGE | bits 0-5 | identique (même automate) | `$FF43A6` ; lecteurs `$9E348`-`$9E370` (1, 1, 1, 1, 1, 13 appels ; Hyper : idem) | **le code existe** : LV0 START et GUARD GAUGE OFF vus à l'écran (`captures/upper_extra_*.png`) ; déjà dans le cœur |
| EXTRA OPTION (2) : GUARD DAMAGE, COUNTER DAMAGE, GROUND GUARD, MID-AIR GUARD, THROW, THROW ESCAPE | bits 0-5 | identique ; la valeur de THROW ESCAPE n'a pas de texte sur l'écran PS2 d'Upper (défaut d'affichage seulement : le bit bascule) | `$FF43A9` ; lecteurs `$9E378`-`$9E3A0` (1, 2, 2, 2, **4**, 1 appels ; Hyper : THROW **6**, les 2 de plus sont dans le code des versions) | déjà dans le cœur |
| EXTRA OPTION (3) : BREAK FALL, DEFENSIVE ROLL, COMMAND TIMER, FRIENDSHIP, ALPHA COUNTER | bits 0-4 | identique | `$FF43A8` ; lecteurs `$9E3A8`-`$9E3C8` (1, 1, 2, 1, 2 appels, comme Hyper) | déjà dans le cœur |
| **EXTRA OPTION (4)** | titre seul : 16 textes vides ; la page est inaccessible (`page = (page ± 1) mod 3`) | identique | — | **sans objet** dans les deux jeux |
| SECRET OPTION : version « 00/11/20ver », grille CUSTOMIZE | 8 octets `+0x1FAC` → `A5-$3C8E` = `$FF4372-79` ; préréglage `b87d205a5786`, grille de 25 bits | **même texte « 00/11/20ver »** ; préréglage `b87d205a5787`, grille de 26 bits : Hyper retire seulement le bit `0x28` | Upper : 26 tests `BTST` (`$115C`-`$1224`) ; Hyper : 28 (les bits 0, 2 et 6 en plus ne sont jamais posés, et le bit 40 manque) | le code existe, mais ce n'est **pas propre à Hyper**. Absent du cœur dans les trois jeux ; défaut PS2 = 0 partout. Voir §3 |
| **BGM 【RANDOM】【1P】【2P】** (page RANDOM PLAYER du menu de pause) | `+0x1FAB` → `$FF43B5` : −1 au hasard, 0 J1, 1 J2 (défaut PS2 −1). Effet au §1.3 | **absent** | pas d'octet, pas de lecteur ; Upper choisit la musique autrement (§1.3) | **code manquant → greffe FAITE** (§2) |
| RANDOM PLAYER (réserve de persos par joueur) | 42 entrées dont EX, `+0x134`… | même écran, effectif d'Upper (`+0x10C`…) | — | sans objet : effectif propre ; sert le mode 7 |
| RANDOM MODE (réserve d'ismes / de modes) | X/A/V-ISM, NORMAL, MAZI, SAIKYO, CLASSIC, SHADALOO-A..D, **ALPHA, ALPHA2, ALPHA2G, ALPHA3** | X/A/V-ISM… SHADALOO | — | **exclu** : versions = modes de jeu |
| Valeurs par défaut | `04 01 01 02 01 01 01`, extra 0, version 0 | identiques | identiques | — |

### 1.3 Le BGM d'Hyper et la musique d'Upper

- **Hyper**, 68K `$8BE7A` (MIPS `0x5791xx`, vérifié dans le MIPS). Le curseur des modes `$FF4201` vaut 1 en VERSUS et
  4 en TRAINING. Dans ces deux modes, le thème est celui de J1 ou de J2, **au hasard**. Dans les autres modes, c'est
  `$C3B5` qui décide.
- Le seul de ces autres modes accessible est le **mode 7** :
  - c'est un VERSUS caché, lancé avec la combinaison `$5200` de `$C214` maintenue, en `$9A78` ;
  - c'est aussi le seul mode où le menu de pause montre RANDOM PLAYER et RANDOM MODE (`0x21BA70` : `[0xF]` = 2).
- Le BGM est donc un réglage du VERSUS caché. En VERSUS normal, Hyper se comporte comme 【RANDOM】.
- **Upper**, 68K `$2B884` (MIPS `0x329C18`) :
  - en VERSUS (1), en TRAINING (4) et en mode 7, il joue la **musique du décor** (`T_613380[$100]`, variante tirée au
    hasard) ;
  - sinon, il joue le thème du perso du joueur humain (table `$A9690`).
  - Upper a lui aussi le mode 7, lancé par le même `$5200` en `$7268`.

### 1.4 Corrections de la documentation

- `agent_options/OPTIONS.md` §1.2 (et `docs/rapports/OPTIONS.md`) : la ligne « CONTROLLER SETTINGS … `0xF6C` /
  `0x1FAC` (8 o) … couche manette native » est **fausse**.
  - Ces 8 octets sont la grille de **SECRET OPTION** :
    - fonction de l'écran : Hyper `0x215D10`, Upper `0x5F3770` ;
    - préréglage « 00/11/20ver », DEFAULT = 0 ;
    - dessin en ★/☆ par `0x2163D0` / `0x5F3E30`.
  - Ils sont lus par les tests `BTST` du jeu traduit (§1.2). Les réglages de manette sont ailleurs.
- `docs/rapports/SON-HYPER.md` §2.2 :
  - en VERSUS et en TRAINING, Hyper tire J1 ou J2 au hasard, quel que soit `$C3B5` ;
  - `$C3B5` ne sert que dans les autres modes : 0 → J1, > 0 → J2, < 0 → au hasard.

## 2. Ce qui est fait : la greffe BGM dans Upper

### 2.1 Traducteur — `diffs/traducteur_bgm_upper.diff` (copie : `untranspile/`)

- `profils.py`, ro5 : `bgm=(0x139C18, 0x139E70, 0x139FB8)`, c'est-à-dire :
  - `CMPI.B #7,$C201(A5)` du choix de la musique ;
  - le `JSR` du hasard (variante de décor) ;
  - `MOVEQ #0,D0`, juste après le choix de A4 de la branche « thème du perso ».
- `mame_test.py`, juste avant l'écriture de la ROM :
  - les trois sites sont retrouvés par la carte, et leurs formes sont vérifiées par `assert` ;
  - **talon de 86 octets en `CODECONV-$100` = `$3FEF00`**, dans une zone libre et vérifiée nulle, entre la table des
    adresses de code et `CODECONV` ;
  - **descripteur en `$3FEEF0`** : `'HSFABGM1'` suivi de l'adresse du site (`$2B884` dans la ROM actuelle).
- Fonctionnement du talon :
  - si `$FF43B5 = 0`, il refait le `CMPI` d'origine puis saute au `Bcc` d'origine ;
  - sinon, en mode 1, 4 ou 7, il prend `A4 = J1` (2), `J2` (3) ou l'un des deux au hasard (1 : même `JSR` que le jeu,
    donc même nombre de tirages), puis saute à `$2B8DA`, la branche « thème du perso » d'Upper ;
  - le désassemblage du talon a été vérifié.
- Interrupteur `BGM_UPPER` :

  | valeur | effet |
  |---|---|
  | `1` (défaut) | talon et descripteur seulement. Le site n'est pas touché, donc le jeu est inchangé. Seul `sz3.10b` change, de 83 octets dans la zone libre. |
  | `2` | `JMP` posé dans la ROM. À éviter : les quelques cycles en plus au choix de la musique suffisent à décaler une partie scriptée d'une image, ce qui change la graine du hasard à l'image 3581 (essais `decalage_jmp_statique_*`). C'est pour cela que le saut est posé par le cœur. |
  | `0` | ROM identique (22/22). |

- Profils ro3/ro9 : pas de clé `bgm`, rien ne change. ro3 a été reconstruit : 20/20 fichiers identiques.

### 2.2 Cœur FBNeo — `diffs/fbneo_bgm_upper.diff`

Diff contre l'arbre `work/agent_fbneo_rejeu/fbneo` (branche `rejeu`, HEAD `501aebd`), appliqué sur une copie.

- **`d_cps2.cpp`** : `UhsfaDIPList` pour `sfa3uhsfa` seulement (SFA3 et Hyper gardent leur liste). Elle reprend les
  options d'Upper et ajoute **« Option: BGM (versus, training) »**, dans les bits 2-3 du Dip E. Il n'y a pas de nouvelle
  entrée, ni de décalage des DIP. Valeurs :
  - « Game default (stage music) » ;
  - « Random 1P/2P theme (Hyper) » ;
  - « 1P theme » ;
  - « 2P theme ».

  Clé RetroArch : `fbneo-dipswitch-sfa3uhsfa-Option__BGM_(versus,_training)`.
- **`cps_hsfa.cpp`, `HsfaOptBgm()`**, appelée à chaque image, avant le test du menu des modes :
  - si le descripteur est présent, si le réglage est choisi et si `$FF4201` ∈ {1, 4, 7}, elle pose `JMP $3FEF00` sur le
    site, dans `CpsRom` (et dans `CpsCode` s'il y a lieu), puis écrit `$FF43B5` ;
  - sinon, elle remet le `CMPI` d'origine ;
  - ARCADE, SURVIVAL et DRAMATIC restent donc identiques au cycle près, réglage choisi ou non ;
  - avec une ROM sans descripteur (ancienne ROM, SFA3, Hyper), elle ne fait rien.
- **`HSFA_CMD_LOG=<fichier>`** (aide aux essais) : journal `image code` de toutes les commandes son du 68K.
- **Cœur Linux de test** : `coeurs/fbneo_hsfa_libretro_bgm.so` (md5 `bf3608cc…`). Référence sans modification :
  `coeurs/ref_501aebd.so`, copie du cœur `501aebd`. Lanceur : `coeurs/hsfa_run` (celui d'`agent_options`).
- Je n'ai pas construit le cœur widescreen (`hsfaws`). Il compile le même code ; seule la largeur change.

### 2.3 Banc MAME — `lua/banc_options.lua` (diff `diffs/banc_options_bgm.diff`)

- Nouvelle variable `HSFA_OPT_BGM` : 1 au hasard, 2 J1, 3 J2. Elle correspond aux bits 2-3 de l'octet E de
  `HSFA_OPT_DIP`.
- La logique est celle du cœur. L'écriture se fait dans la région `:maincpu` **et** dans la copie `:decrypted_opcodes`,
  car le fork exécute les opcodes depuis cette copie.
- Scénario d'essai : `lua/essai_bgm_mame.lua`. Il ajoute une prise sur `$618000-$61801F` qui journalise les commandes
  son, puis lance `tournee.lua VS=1 MODE=1`. Lanceur : `essais/mame_bgm.sh`.

## 3. Validation (cœur Linux + fork `sfa3hx`)

Partie scriptée = entrées de `nonreg_su.sh` (Arcade, 9 000 images). VERSUS scripté : Ryu (J1) contre Ken (J2).

| essai | résultat |
|---|---|
| **défaut, Arcade** : cœur 501aebd + ROM actuelle, contre nouveau cœur + ROM actuelle, contre nouveau cœur + ROM `BGM_UPPER=1` | **30/30 captures**, journal d'états et niveaux sonores identiques ; commandes son identiques (408) entre les deux ROM (`essais/nonreg.sh`, `nonreg_essai4.txt`) |
| **défaut, VERSUS** (5 000 images) | **16/16 captures**, journaux identiques, commandes son identiques (225) |
| Arcade avec « 1P theme » choisi | 30/30, journal et commandes identiques : le `JMP` n'est pas posé hors des modes 1, 4 et 7 |
| **VERSUS, décor 4** (`bgm_vs2_*`) | musique du combat : défaut **`001B`** (décor) ; 1P **`0009`** (Ryu) ; 2P **`000A`** (Ken) ; hasard `0009`. `$FF43B5` = 0/2/3/1. WAV de 13 s : `wav/upper_vs_bgm_{defaut,j1,j2}.wav` (corrélations entre elles 0,12-0,14) |
| VERSUS, 40 000 images, 4 matchs (`bgm.sh`) | 2P : `000A` à chaque match ; hasard : `0009`, `000A`, `0009` ; « 2P » puis retour à « Game default » à l'image 12000 : `000A`, puis la musique du décor (le `CMPI` est bien remis) |
| **TRAINING** (`bgm_tr_*`) | défaut `0009` (décor 0) ; 2P `000A` |
| SURVIVAL avec le réglage choisi | inchangé (`000E`) : le `JMP` n'est pas posé |
| état sauvé à 1900, juste avant la musique (`STATETEST`) | `000A` dans les trois passes. Le résultat « DIFFERENT » du lanceur existe aussi avec le cœur et la ROM de référence : c'est une limite du lanceur avec des entrées scriptées, sans rapport avec la greffe |
| **banc MAME** (fork, `tournee.lua VS=1`) | ROM actuelle et ROM BGM sans réglage : journal et commandes **identiques** ; `HSFA_OPT_BGM=3` → `000A` au lieu de `0009` (décor 0, celui de Ryu) |
| ROM avec interrupteurs à 0 | `BGM_UPPER=0` : 22/22 fichiers identiques à `work/mame_ro5` ; `BGM_UPPER=1` : seul `sz3.10b` diffère (83 octets, zone libre) ; ro3 : 20/20 |
| réglages existants dans Upper | Infinity : `∞` et chrono arrêté (`captures/upper_chrono_infini_*`) ; SP gauge LV0 et Guard gauge Off : jauges vides, plus de jauge de garde (`captures/upper_extra_*`) |

## 4. Ce qui reste (chiffré)

| sujet | coût | remarque |
|---|---|---|
| **Intégrer** :<br>- traducteur → reconstruire ro5 → `valide_tout.sh` (aucun changement exécuté par défaut : non-régressions inchangées attendues) ;<br>- zips (paquet du dépôt) ;<br>- patch FBNeo (nouveau n° 0012 sur la branche `rejeu`) puis cœurs Android / ROCKNIX / 16:9 ;<br>- `tools/options/lua/banc_options.lua` | ~2 h, surtout de la construction | décision de l'utilisateur. Libellés de l'option à revoir si besoin |
| BGM dans **Hyper** au cœur (`$FF43B5` : −1/0/1, octet et lecteur existants) | 20 min | n'agit que dans le VERSUS caché (mode 7) : peu utile |
| **Version** (SECRET OPTION) dans le cœur pour les trois jeux : 8 octets `$FF4372-79` (SFA3 : à localiser), préréglages « 00/11/20ver » (Upper `b87d205a5787`, Hyper `…86`) et « arcade / DEFAULT » (0) | 1 h de code ; **½ à 1 j** pour documenter l'effet de chacun des 26 bits | pas propre à Hyper. Le code existe (26 tests). Défaut PS2 = 0. Les effets sont des corrections de révision, difficiles à montrer à l'écran |
| RANDOM PLAYER / RANDOM MODE (réserves du mode 7) | ½ j | lié au VERSUS caché, donc mode de jeu ; non demandé |
| Écran OPTION « dans le jeu » | 1,5-3 j | voie (a) d'`agent_options`, inchangée |

## 5. Fichiers

- Rapport : `OPTIONS-HYPER-UPPER.md`.
- Diffs :
  - `diffs/traducteur_bgm_upper.diff` (contre `src/hsfa`) ;
  - `diffs/fbneo_bgm_upper.diff` (contre `agent_fbneo_rejeu/fbneo`) ;
  - `diffs/banc_options_bgm.diff` (contre `tools/options/lua/banc_options.lua`).
- Copies :
  - `untranspile/` (modifiée) et `untranspile.orig/` ;
  - `fbneo/` (modifiée, construite) et `fbneo_ref/` ;
  - `lua/banc_options.lua` (+ `.orig`), `lua/essai_bgm_mame.lua`.
- Cœurs : `coeurs/fbneo_hsfa_libretro_bgm.so`, `coeurs/ref_501aebd.so`, `coeurs/hsfa_run`.
- Constructions :
  - ROM : `build/ro5_ref` (contrôle = `work/mame_ro5`), `build/ro5_bgm` (`BGM_UPPER=1`, `roms_fork/` pour le banc),
    `build/ro5_bgm0`, `build/ro5_bgm2`, `build/ro3_ctrl` ;
  - zips de test sans flux : `zips/ref`, `zips/bgm`.
- Essais : `essais/lance.sh`, `nonreg.sh`, `bgm.sh`, `mame_bgm.sh`, résultats `nonreg_essai4.txt` et `bgm_essai4.txt`.
- Preuves : `captures/`, `wav/`.
- Analyse :
  - `ro5_textes.txt`, `ro9_textes_complet.txt`, `ro{5,9}_chaines.txt` ;
  - `decomp/ro5_option.c` (écran d'options d'Upper décompilé) ;
  - `outils/` (copies des outils d'`agent_options`, `decomp_plage.py` pointé sur mon projet Ghidra).
