# Hyper Street Fighter Alpha (`ro9`) dans le cœur libretro FBNeo « HSFA »

Agent `agent_fbneo_hyper`, 2026-10-10 (reprise d'un travail interrompu). J'ai écrit seulement dans
`<workspace>/work/agent_fbneo_hyper/`, plus quelques fichiers temporaires dans le scratchpad de la session.

Le reste est resté en lecture seule :
- `work/mame_ro9/` ;
- le fork `agent_flux/mame-fork-flux` ;
- `work/fbneo/` : l'original de `paquet_fbneo.py` n'a pas été modifié, un diff est proposé ;
- `work/mame_ro5`, où tourne une validation : je n'y ai pas touché.

Précautions :
- MAME a tourné en `nice -n 19`, avec ses propres `-nvram_directory`, `-cfg_directory` et `-snapshot_directory`
  (`tests/essais/{nv,cfg,snap}_m_<nom>`), jamais avec `-state` ;
- compilations en `nice -n 19 make -j4` ;
- **aucun `push`**.

## 0. En bref

1. **Hyper tourne dans FBNeo avec le pilote `sfa3hhsfa`.** Commit local `464b23a` sur la branche `hyper` de
   `fbneo/`, posé sur `dfd2de8` (le lecteur de flux).
   - Il reprend les mécanismes d'Upper :
     - mode 2 : bases de plans, ROM graphique étendue de 64 Mo, codes d'objet sur 20 bits ;
     - son hybride `hx3.*` ;
     - lecteur de flux ADX, réglé par défaut sur « All tracks ».
   - Il ajoute ce qui est propre à Hyper : banque commune 545, et blocs externes `$940000` et `$C84000`. La base de
     la zone externe se déduit de la taille de `hsfa_ext.bin` (5,75 Mo → `$940000-$EFFFFF`).
2. **Validation sur PC contre le fork** (même ROM, mêmes entrées, deux joueurs en VERSUS) :
   - **même déroulement** : titre, menu, 7 sélections (EX ALPHA, EX ZERO 3 curseur 7, EX Balrog, S-ISM, EX ZERO 2,
     Shin Akuma, Sakura bis), 12 manches, 0 exception. Mêmes choix, à 1-32 images près ;
   - **captures** : 17 sur 26 identiques au pixel, 23 sous 1 %. Les écarts restants sont des phases d'animation et
     une phrase d'annonce tirée au hasard ;
   - **musique** : le lecteur de flux prend les mêmes décisions que dans le fork. Les flux Y_DATA de l'ISO se
     retrouvent dans le WAV de FBNeo, avec le gain attendu.
3. **Non-régression.**
   - SFA3 et Upper, sur le nouveau cœur et sur le cœur `dfd2de8` : son, journal et 30 captures identiques à l'octet.
   - `paquet_fbneo.py` (copie) produit des zips SFA3 et Upper identiques à l'octet à ceux de l'original.
   - **Patch « décors »** : il s'applique sans conflit par-dessus Hyper. Le cœur combiné donne une tournée Hyper
     identique.
4. **Cœurs** : Linux x86_64 et Android arm64-v8a (API 21, pages de 16 Ko). Avec l'archive, la table des musiques et
   `LISEZMOI-hyper.md`, ils sont dans `livraison/`.
5. **Ce que j'ai trouvé**, détails au §6 :
   - le blocage d'EX Balrog vu par l'agent précédent venait **du lanceur d'essai, pas du cœur** ;
   - la fin de match VERSUS (scène `$E`), absente au 7 octobre (ETATS-HYPER §3.1), **fonctionne** avec la traduction
     du 10 octobre ;
   - **exception en TRAINING** au banc MAME : saut à l'adresse `$000001`, qui tombe sur une instruction illégale.
     C'est un défaut de traduction.

## 1. Reprise : état trouvé

- Pilote déjà écrit (`HsfaMode = 3`), zip construit, essais commencés (`kz`, `tour`, `balrog*`).
- `paquet_fbneo.py` avait été copié avant que l'original ne change à 13:53 : `HSFA_STRICT` et `SOURCE_DATE_EPOCH`
  y ont été ajoutés. J'ai **refait la copie** à partir de l'original actuel.
- **Essais « balrog »** : dans FBNeo, EX Balrog n'avançait pas.
  - Les vidages RAM montrent un bit `$1000` (bouton 4, lu en `$804011`) dans les entrées du portage `$FF4214`. MAME
    ne l'a pas.
  - Cause : l'ancienne version de `hsfa_run` appuyait « P1 Button 4 », comme le script Lua. Or, dans MAME, ce
    bouton est sur `:IN1`, et le script ne l'appuie donc jamais.
  - L'agent précédent l'avait déjà corrigé dans `hsfa_run.c` (binaire de 14:00) sans relancer l'essai. Je l'ai
    relancé : Balrog avance à l'image 1294, comme dans MAME (1292).

## 2. Ce que fait le cœur (commit `464b23a`, `patchs/0001-HSFA-pilote-sfa3hhsfa-….patch`)

| Fichier | Modification |
|---|---|
| `d_cps2.cpp` | pilote `sfa3hhsfa` (programme `mame_ro9`, ROM graphique `sz3`, son `hx3.*`, `hsfa_ext.bin` 0x5C0000, `hsfa_tab.bin`, `hsfa_gfx.bin` 32 Mo) ; DIP `HhsfaDIPList` = « PS2 music » à **All tracks** (`0x02`) par défaut ; `HsfaHyperInit` : `HsfaMode = 2`, `HsfaHyper = 1`, région graphique de 64 Mo |
| `cps_hsfa.cpp` | base externe = `$F00000 − taille(hsfa_ext.bin)`, lue dans la liste de ROM (`HsfaExtTaille`) : SFA3 et Upper `$A00000` comme avant, Hyper `$940000`. La même base sert au projeté `SekMapMemory`, à la reconversion et au chargement ; message `HSFA : donnees externes $…` |
| `cps_hsfa.cpp` | crochet d'essai **`HSFA_NOROUL=1`** (Hyper seulement, variable d'environnement, donc jamais actif sous Android) : `$FF84D3` et `$FF88D3` sont écrits à 0, comme le `NOROUL` des scripts du banc (roulette, ETATS-HYPER §1.1). Il sert à comparer avec le fork à entrées égales |
| `cps_hsfa.cpp` (patch 11, 2026-10-16) | le crochet de `$FF84D3` / `$FF88D3` est **toujours installé** pour Hyper : roulette sur la touche Pièce, sur la grille seulement ; `HSFA_NOROUL=1` le force à 0 comme avant |
| `cps.h` | `extern INT32 HsfaHyper` |
| `gamelist.txt`, `driverlist.h` | seulement les 3 lignes de `sfa3hhsfa` (fichiers générés remis à l'état d'origine) |
| `hsfa/hsfa_run.c` | `PILOTE=hyper` : portage C de `tournee_hyper.lua` (titre, menu, sélection par chemin dans la grille, versions, modes 0-7, ism, EX par Start, HANDICAP, combats avec K.O. forcés, `CONTOURNE_E`, `SNAPM`, journal au même format), `WATCHW`, `DUMPRAM` ; **`STATETEST` avec pilote** : entrées et écritures de la 1re passe enregistrées puis rejouées |

**Compatibilité avec le patch « décors »** (`decors_ws/injection_fork/fbneo-hsfa-decors.patch`, commit `682b2bb`) :
- Hyper passe par `HsfaMode == 2`. Les lignes que ce patch remplace par `bCfgPlans` sont donc **inchangées**.
- Hyper a `plans=` dans sa config. Avec le patch, il emprunte donc le même chemin.
- `git apply` échoue sur une section, mais **déjà sur `dfd2de8`** : le patch date d'avant le lecteur de flux.
- Un `cherry-pick` de `682b2bb` passe sans conflit sur `dfd2de8` comme sur `hyper`, avec les mêmes 21+/12− lignes.
- Le cœur `hyper` + « décors » donne une tournée Hyper **identique** au cœur `hyper` seul : journal, WAV et 26
  captures.

## 3. Archive (`paquet/`)

| Élément | Contenu |
|---|---|
| `paquet/paquet_fbneo.py` | copie de l'original actuel (`work/fbneo/paquet_fbneo.py`, 13:53) avec l'entrée `hyper` |
| `paquet/paquet_fbneo.diff` | **diff proposé pour l'original**, 94 lignes : il s'applique proprement et redonne la copie |
| `paquet/sfa3hhsfa.zip` | archive Hyper, 34,7 Mo |
| `paquet/sfa3hhsfa_sources.txt` | md5 et dates des fichiers pris |

Ajouts du diff :
- entrée `hyper` dans `JEUX` : `mame_ro9`, `banques_hx`, son `agent_son_ro5/hybride/roms_hybride`,
  config `commun=545 ptr_anim=FF40BC gfx_intro=456 plans=300,340,3a0`, gfx `mame_ro9/hsfa_gfx.bin` + `hsfa_plans.bin`
  en `+$1000000`, `ext=(0x940000, 0x5C0000)` ;
- `image_ext(dossier, ext)` : fin fixe `$F00000`, avec SFA3 et Upper inchangés ;
- défaut : les trois jeux.

Le `gfx_intro=456` correspond à la valeur par défaut de `banc_sprites.lua` quand `BANC_GFX_INTRO` est absent.

Contrôles :
- `HSFA_STRICT=1` donne les mêmes membres, identiques à l'octet (blocs `$940000` et `$C84000`, 71 tables) ;
- avec `SOURCE_DATE_EPOCH` fixé, `sfa3hsfa.zip` et `sfa3uhsfa.zip` sortent **identiques à l'octet** de l'original et
  de la copie.

Sources de l'archive :
- ROM `mame_ro9/roms_ro9` du 2026-10-10 12:57 (`sz3ud.03c` md5 `69b2ac41…`) ;
- `ext_940000.bin` (2 679 296 o) et `ext_c84000.bin` (553 352 o) du 10/10 ;
- `banques_hx`, `hsfa_gfx.bin` et `hsfa_plans.bin` du 7/10.

Commande : `HSFA_WORK=<workspace>/work python3 paquet_fbneo.py hyper`. `HSFA_WORK` est nécessaire hors de
`work/fbneo/`.

## 4. Validation sur PC

Dans `tests/` :
- `tour.sh <nom>` lance le fork (`mame.sh`) et FBNeo (`fb.sh`) en parallèle, avec les mêmes `LISTE`, `MODEJEU`,
  `NF`, `CONTOURNE_E`, `SNAPM` et `SNAPS` ;
- `compare_ordre.py` apparie les captures dans l'ordre des événements.

Musique :
- fork : `HSFA_FLUX=2`, `HSFA_YDATA` = ISO ;
- FBNeo : comme un utilisateur, `sys/fbneo/hsfa/ydata.txt` (chemin de l'ISO) + `hsfa_flux_table.txt`, avec le DIP par
  défaut (All tracks).

Liste de la tournée (paires de ETATS-HYPER §4) : `00.A.S/01.Z, 0a.Z3.m7/04.Z2.S, 15.Z3.S/00.Z3.m4, 01.Z3.m5/0b.Z2.S,
02.Z3.S/0d.A.S, 10.A.S/0f.Z2.S`, sur 13 000 images.

| Essai | Résultat |
|---|---|
| **Tournée VERSUS 2 joueurs** (`m_tour2.txt` / `fb_tour2/journal.txt`) | 7 sélections, 12 manches, 0 exception des deux côtés. **Mêmes 14 choix** (`$102`, base, drapeaux, mode, `$123`, `$15F`, ism), dont `7b`, `0a/98` (EX ZERO 3), `52`, `25` (EX Balrog), `00` S-ISM rouge, `59`, `24`, `7d`, `75`, `56`. Images décalées de +1 à +32 (cycles 68000, comme pour Upper, RAPPORT-fbneo §4) |
| Captures (`compare_ordre.py`, 26 paires : titre, VS + 60, combat + 150) | **17 identiques au pixel**, 23 sous 1 %, 25 sous 5 %. Écarts : grille qui glisse à l'image 420 (32 %, une image de phase), bandeaux défilants, jauge LEVEL qui clignote, phrase de l'annonce ROUND tirée au hasard. Planches `livraison/planche_hyper.png` et `tests/essais/tour2_ecarts.png` |
| Menu et sélection (`m_menu` / `fb_menu`) | menu VERSUS identique ; colonne des versions ALPHA / ALPHA2 / ALPHA2G / ALPHA3 qui diffère par le clignotement seul (`livraison/planche_menu.png`) |
| **Fin de match** sans contournement (`m_e_b1` / `fb_e_b1`) | scène `$E` → écran **RESULT** identique au pixel ; un bouton ramène à la sélection (A5+4 = 2 à l'image 2438) dans les deux émulateurs |
| TRAINING (`m_tr` / `fb_tr`) | mêmes choix, même manche ; flux identiques. Le fork s'arrête sur une exception à l'image 2945 (§6.3). FBNeo continue, mais les deux parties avaient déjà divergé (mannequin) |
| **Flux musique** (`m_tour2.flux` / `fb_tour2/flux.txt`) | 89 décisions de chaque côté, identiques sauf 2 matchs. Pour ces deux matchs, le jeu tire au hasard le joueur dont dépend la musique (`$C3B5` < 0 en VERSUS, SON-HYPER §2.2) : `001E` contre `0009`, et les variantes `01AC/01BD` contre `01C4/01D5`. Codes joués en flux : `0002`, `0004`, `0009`, `001B` (ZERO 3), `0042` (ZERO), `0053` (ZERO 2), `01A9/01BA` et `01C4/01D5` (variantes, avec le 2ᵉ code) |
| Flux dans le WAV de FBNeo (corrélation, `agent_flux/outils/cherche.py`) | Y57 gain 0,142 (attendu 0,26 × 69/127 = 0,141), Y72 0,093 (0,092), Y9 0,174 (0,176), Y518 0,220 (0,219), Y477 présent (corrélation 0,61 au milieu des bruitages). Y57 démarre à 21,365 s, soit l'image 1274 : c'est l'image où le fork envoie `0042` (`m_tour2.son`) |
| États sauvegardés (`STATETEST`, avec pilote rejoué) | état de 652 769 o ; restauré aux images 600 (sélection), 1500 (combat, flux Y57 en cours) et 2250 (après la scène `$E`) : image finale **identique** |
| Non-régression SFA3 / Upper (`nonreg.sh`) | partie de 9 000 images jusqu'au combat, sur le cœur `dfd2de8` et le nouveau : **WAV, journal et 30 captures identiques** pour chacun des deux jeux |
| Cœur + patch « décors » | tournée Hyper : journal, WAV et captures identiques (§2) |
| Vitesse | environ 600 à 800 images/s sur PC, soit plus de 10 fois le temps réel |

## 5. Cœurs et livraison (`livraison/`)

| Fichier | Détail |
|---|---|
| `fbneo_hsfa_libretro_android.so` | NDK r28c, arm64-v8a, API 21, segments alignés sur 16 Ko, `GIT464b23a`, md5 `837f3f06…` |
| `fbneo_hsfa_libretro.so` | Linux x86_64, `SUBSET=hsfa`, `GIT464b23a`, md5 `27ae4d0f…` |
| `sfa3hhsfa.zip` (+ `_sources.txt`) | md5 `ce961a7b…` |
| `hsfa_flux_table.txt` | copie de `agent_flux/hsfa_flux_table.txt` (558 codes) |
| `LISEZMOI-hyper.md` | installation (cœur, zip, `Y_DATA.BIN` ou ISO dans `system/fbneo/hsfa/`), DIP, commandes, EX, limites |
| `planche_hyper.png`, `planche_menu.png` | MAME \| FBNeo \| différence |

Le cœur Android **n'a pas été essayé sur une console** : pas d'appareil ici. Il reste à vérifier les performances et la
lecture du flux sur la carte SD.

Reconstruire :

```
cd agent_fbneo_hyper/fbneo/src/burner/libretro && nice -n 19 make -j4 SUBSET=hsfa REGEN_HEADERS=1
cd jni && nice -n 19 ~/Android/Sdk/ndk/28.2.13676358/ndk-build -j4 APP_ABI=arm64-v8a SUBSET=hsfa
```

`REGEN_HEADERS` réécrit `gamelist.txt` et `driverlist.h`, avec `" HSFA_SUFFIXE "` dans les noms. Il faut les remettre
avec `git checkout` après la construction.

## 6. Constats

### 6.1 Écarts FBNeo / fork : hasard seulement

Le hasard du programme traduit dépend des cycles 68000 (Musashi contre le 68000 de MAME). Il touche :
- le perso tiré par la roulette ;
- la phrase d'annonce ;
- le joueur dont dépend la musique en VERSUS ;
- le comportement du mannequin en TRAINING.

À entrées égales, `HSFA_NOROUL=1` est nécessaire. Sans lui, Start fait tourner la roulette. C'est le cas de l'essai
`fb_tour` de l'agent précédent : `$1a` au lieu de `$52`, `$3b` au lieu de `$25`.

### 6.2 Fin de match VERSUS (scène `$E`) : corrigée dans la traduction du 10 octobre

ETATS-HYPER §3.1 (7 octobre) la décrivait noire et sans issue. Avec `roms_ro9` du 10/10 12:57, elle avance jusqu'à
`A5+8 = $A` et affiche **RESULT**, la table V/D/N par perso. Un bouton y fait suivre `A5+C = 2`, puis
`A5+4 = 2`, puis la sélection. Résultat identique dans le fork et dans FBNeo.

Conséquence : `CONTOURNE_E=1` n'est plus nécessaire. Je l'ai gardé dans la tournée pour rester comparable aux essais
précédents.

### 6.3 Exception en TRAINING (programme traduit)

Conditions : fork, TRAINING, Ryu ZERO 3 contre Ken ZERO, image 2945, pendant un coup de Ryu (Ken étourdi).
- `pc = $A08`, c'est-à-dire le vecteur 4 (instruction illégale), qui contient `BRA *` ;
- `sp = $6614DA`, `sr = $3415` ;
- **PC empilé = `$000001`** : le programme a sauté à l'adresse 1.

Relevé : `tests/lua/exc.lua`, résultat dans `tests/essais/m_tr_exc.pc`. C'est cohérent avec les aiguillages perdus du
code TRAINING (ETATS-HYPER §3.2, `0x3B4300`, `0x2C440`). À traiter côté traducteur.

Dans FBNeo, les parties divergent avant ce moment : je ne l'ai pas reproduit. Le pilote d'essai ne détecte pas les
exceptions, car la pile en `$66xxxx` n'est pas exposée par libretro.

### 6.4 À savoir pour le joueur

Ces trois points sont repris dans `LISEZMOI-hyper.md` :
- Start sur la grille lance la roulette, ce qui gêne l'obtention d'EX Balrog ;
- `$58/$59` (EX Bison et EX Sagat ZERO 2) s'affichent en morceaux : c'est la donnée PS2 ;
- OPTION et EXIT ne font rien.

## 7. Non fait / suites

- **Cœur widescreen** (`SUBSET=hsfaws`) : le pilote y est compilé avec le même code, mais je ne l'ai ni construit ni
  essayé pour Hyper.
- `hsfa/paquet_fbneo.py` suivi dans le dépôt FBNeo est une vieille copie (commit `2b57422`), laissée telle quelle.
  L'outil de référence reste `work/fbneo/paquet_fbneo.py` : appliquer `paquet/paquet_fbneo.diff`.
- Hyper n'a pas de tableau des records (hiscore).
- Les variantes de musique ne sont validées que par corrélation. Le 2ᵉ code (`$C3B6`) est joué juste après le 1er, et
  c'est lui qu'on entend.

## 8. Fichiers

- `fbneo/` : copie de travail, branche `hyper` (`464b23a`) ;
- `patchs/0001-HSFA-pilote-sfa3hhsfa-Hyper-Street-Fighter-Alpha-mod.patch` ;
- `paquet/` : `paquet_fbneo.py`, `paquet_fbneo.diff`, `sfa3hhsfa.zip`, `sfa3hhsfa_sources.txt` ;
- `livraison/` : voir §5 ;
- `tests/` :
  - lanceurs : `hsfa_run` (compilé depuis `fbneo/hsfa/hsfa_run.c`), `fb.sh`, `mame.sh`, `tour.sh`, `nonreg.sh` ;
  - comparaison : `compare_ordre.py`, `compare.py`, `montage.py` ;
  - Lua : `lua/exc.lua`, `lua/watch.lua` ;
  - `essais/` : journaux, flux, captures, planches ;
- journaux de compilation : `build_linux*.log`, `build_android*.log`.
