# Cœur FBNeo HSFA pour ROCKNIX : Powkiddy RGB10X, RK3326 (2026-10-10)

Agent `agent_rocknix`.

- J'ai écrit seulement dans `<workspace>/work/agent_rocknix/` et dans le scratchpad de la session (sources de
  ROCKNIX lues pour la documentation).
- J'ai travaillé sur deux clones locaux de `agent_fbneo_hyper/fbneo`, branche `hyper`, commit `464b23a` : `fbneo/`
  pour aarch64 et `fbneo_x86/` pour le témoin.
- Je n'ai modifié aucune autre copie et je n'ai rien poussé.
- Compilations en `nice -n 19 make -j4`.

## 1. En bref

- **Deux cœurs aarch64** dans `livraison/` :

  | Fichier | Contenu | md5 |
  |---|---|---|
  | `fbneo_hsfa_libretro.so` | « FinalBurn Neo HSFA », 4:3 | `5597ec83…` |
  | `fbneo_hsfaws_libretro.so` | « FinalBurn Neo HSFA Widescreen », 448×224, 16:9 | `c0c4fa59…` |

  - Ils portent tous deux `GIT464b23a` et contiennent SFA3, Upper et Hyper.
  - Chacun pèse 10,7 Mo après `strip`.
- **Dépendances** :
  - `NEEDED` se limite à `libm.so.6`, `libc.so.6` et `ld-linux-aarch64.so.1` ;
  - libstdc++ et libgcc sont liées statiquement ;
  - les symboles exigent au plus **GLIBC_2.38**.
  - ROCKNIX 20261001 (version actuelle pour RK3326) a la glibc 2.41, et 20241029 la 2.40 : **c'est compatible**.
- **Pas de qemu-user** sur la machine : `qemu-system-*` seulement, et pas de binfmt aarch64. Je n'ai donc pas pu
  exécuter le cœur ARM. J'ai fait les contrôles suivants à la place :
  - symboles libretro exportés (liste identique à FBNeo) ;
  - en-têtes ELF, absence de pile exécutable, segments ;
  - témoin x86_64 compilé avec les mêmes options : ses captures sont **identiques à l'octet** à celles du cœur
    x86_64 livré par l'agent Hyper.
- **Vitesse probable** : sur PC, HSFA tourne à la même vitesse que le `sfa3` arcade d'origine dans le même cœur
  (1 090 à 1 100 images/s ; Hyper 1 037, soit −6 %). Le CPS2 de FBNeo tourne à pleine vitesse sur RK3326 : HSFA
  devrait donc suivre. **À confirmer sur la console** avec `livraison/essai_console/` (§4).
- **Notice** : `livraison/LISEZMOI-rocknix.md`, avec un système EmulationStation prêt à copier
  (`es_systems_hsfa.cfg`).

## 2. Compilation

`build.sh hsfa|hsfaws` lance `make` avec les paramètres suivants :

```
platform=unix SUBSET=<hsfa|hsfaws> REGEN_HEADERS=1 CC=aarch64-linux-gnu-gcc CXX=aarch64-linux-gnu-g++
PLATFORM_DEFINES="-mcpu=cortex-a35 -O2 -U__FAST_MATH__ -include rocknix_compat.h"
LDFLAGS (environnement) = -static-libstdc++ -static-libgcc -Wl,-O1 -Wl,--as-needed
```

Le script nettoie les objets avant de compiler, car les deux cœurs partagent l'arbre. Chaque cœur se compile en
environ 25 s. Le compilateur est GCC 15.2 (Ubuntu), avec la glibc 2.43 en en-têtes.

Choix et pièges :

- **`-O2`** : le Makefile ajoute `-O3`, mais `PLATFORM_DEFINES` arrive après dans `FBNEO_DEFINES`. C'est donc `-O2`
  qui s'applique, et `-fomit-frame-pointer` est conservé. `-mcpu=cortex-a35` correspond exactement au RK3326
  (ARMv8.0 + CRC).
- **`atan2f@GLIBC_2.43`** : avec `-ffast-math`, `atan2` passe en `atan2f` (`d_cps1.cpp`, `d_cps2.cpp`). La glibc 2.43
  a donné une nouvelle version à ce symbole, que ROCKNIX (2.41) n'a pas. `rocknix_compat.h`, inclus de force, lie
  le cœur à `atan2f@GLIBC_2.17` par `.symver`. Les sources ne sont pas modifiées.
- **`libmvec.so.1`** : avec `-ffast-math`, la glibc 2.43 déclare des variantes vectorielles des fonctions
  mathématiques. `burn_gun.o` appelait ainsi `_ZGVnN2v_log`, d'où une dépendance à libmvec. `-U__FAST_MATH__`
  désactive ces déclarations ; les optimisations de `-ffast-math` restent actives.
- **`__isoc23_strto*` (GLIBC_2.38)** : `g++` définit toujours `_GNU_SOURCE`, et la glibc 2.38 ou plus redirige alors
  `strtol` et les fonctions voisines. La glibc 2.38 est donc le minimum. Je ne l'ai pas contourné, puisque ROCKNIX
  est en 2.40 ou 2.41.
- Versions des symboles du `.so` :
  - 2.17 ;
  - 2.25, 2.29, 2.32, 2.33 ;
  - 2.34 (`pthread_once`) ;
  - 2.35 (`_dl_find_object`, appelé par l'unwinder de libgcc statique) ;
  - 2.36 (`arc4random`, appelé par libstdc++ statique) ;
  - 2.38.
- Ces options ne changent pas le résultat. Le témoin x86_64 (`build_x86.sh`, mêmes options sans `-mcpu`) donne,
  sur l'attraction de SFA3, 6 captures sur 6 identiques au cœur x86_64 de `agent_fbneo_hyper/livraison`.

Version de glibc dans ROCKNIX, lue dans le dépôt `ROCKNIX/distribution` :

| Tag | glibc | Fichier |
|---|---|---|
| `20261001` | 2.41 | `projects/ROCKNIX/packages/devel/glibc/package.mk`, qui l'emporte sur `packages/devel/glibc` (2.44, prévu pour `next`) |
| `20260601` | 2.41 | |
| `20250517` | 2.40 | |
| `20250118` | 2.40 | |
| `20241029` | 2.40 | |

## 3. Essais sur PC

`essais/` contient les essais, et `outils/essai_hsfa.sh` le script, aussi copié dans `livraison/essai_console/`.

**Référence x86_64** (`essais/x86_ref/`) :
- 2 cœurs × 3 jeux, attraction de 3 000 images ;
- captures aux images 300, 600, 1200, 1800, 2400 et 3000 ;
- empreintes dans `reference.md5`, valables pour les zips listés dans `reference_zips.md5` ;
- une seconde exécution par le script de la livraison donne **36 / 36** ;
- planche à l'image 1200 : `essais/planche_reference.png`. Le 16:9 est bien en 448×224 pour les trois jeux.

**Vitesse sur Ryzen 5 5600X**, 6 000 images, cœur témoin, en images par seconde :

| Jeu | Images/s |
|---|---|
| sfa3 d'origine | 1 092 – 1 101 |
| sfa3hsfa | 1 088 – 1 105 |
| sfa3uhsfa | 1 078 – 1 102 |
| sfa3hhsfa | 1 037 |

**Mémoire** : Hyper occupe 145 Mo de RSS maximum (`/usr/bin/time -v`).

**Défaut trouvé dans le lanceur `hsfa_run`, pas dans le cœur** : avec `env VAR=… hsfa_run` (env de uutils), le
programme plantait toujours dans `retro_load_game_common`.
- Cause : FBNeo copie le dossier système par `memcpy(g_system_dir, dir, sizeof(g_system_dir))`
  (`libretro.cpp` l. 2003, code d'origine de FBNeo). Il lit donc `MAX_PATH` octets à partir du pointeur fourni.
- Or `hsfa_run` renvoyait directement `getenv("SYSDIR")`. Quand cette chaîne est en fin de pile, la lecture sort de
  la mémoire projetée.
- RetroArch passe un tableau de 4 096 octets : il n'est pas touché.
- J'ai corrigé **ma copie** de `hsfa_run.c` (copie dans un tampon statique). Le diff est dans
  `hsfa_run-sysdir.diff`, à reporter si on veut dans l'original.

## 4. À faire sur la console

1. Installer selon `LISEZMOI-rocknix.md`.
2. Par SSH, lancer `sh essai_hsfa.sh` dans `essai_console/`. On attend :
   - plus de 60 images/s, idéalement 80 ou plus ;
   - **36 / 36** captures identiques.
3. Dans RetroArch, vérifier :
   - le son, et la latence de 32 ms de ROCKNIX ;
   - la lecture ADX de `Y_DATA.BIN` sur la carte SD ;
   - les manettes, en particulier Select, qui est aussi la touche de raccourci ;
   - le format 16:9 sur l'écran 640×480.

## 5. Côté ROCKNIX : ce qui a été vérifié dans les sources (tag 20261001)

- **Cœurs** : `retroarch.cfg` (RK3326) contient `libretro_directory = "/tmp/cores"`. Or `/tmp/cores` est un
  overlayfs (`tmp-cores.mount`) avec `lowerdir=/usr/lib/libretro` et `upperdir=/storage/cores`. Les cœurs de
  l'utilisateur vont donc dans `/storage/cores`, ou dans `/tmp/cores`, ce qui revient au même. Les `.info` vont au
  même endroit (`libretro_info_path = "/tmp/cores"`).
- **Lancement** : `runemu.sh` exécute `retroarch -L /tmp/cores/${CORE}_libretro.so`. `CORE` vient du `<core>` de
  `es_systems`.
- **Système ES** : EmulationStation (`ROCKNIX/emulationstation-next`, `SystemData::loadAdditionnalConfig`) fusionne
  les fichiers `/storage/.config/emulationstation/es_systems_*.cfg`.
  - Un nom de système nouveau ajoute un système.
  - Un nom existant voit ses balises remplacées, `<emulators>` en entier.
  - D'où le système séparé `hsfa`. Sa commande est copiée de `add_es_system`
    (`distributions/ROCKNIX/config/functions`).
- **Dossier système** : `system_directory = "~/roms/bios"`. Le cœur cherche donc dans
  `/storage/roms/bios/fbneo/hsfa/`.
- **Partages Samba** : `games-roms` (`/storage/roms`) et `config` (`/storage/.config`). Il n'y a pas de partage
  pour `/storage/cores` : les cœurs passent par SSH ou SCP, ou par « Installer ou restaurer un cœur » de RetroArch.
- **Réglages RK3326 par défaut** :
  - `video_driver gl`, `video_threaded true` ;
  - `audio_driver alsathread`, `audio_latency 32`, `audio_out_rate 48000` ;
  - `run_ahead_enabled false` ;
  - `aspect_ratio_index 22` (Core provided) ;
  - `config_save_on_exit false` ;
  - `global_core_options false`.

## 6. Fichiers

| Chemin | Contenu |
|---|---|
| `livraison/` | cœurs `.so` et `.info`, `jeux/` (3 zips + `_sources.txt`), `hsfa_flux_table.txt`, `es_systems_hsfa.cfg`, `gamelist.xml`, `essai_console/` (`hsfa_run_aarch64`, `essai_hsfa.sh`, références), `LISEZMOI-rocknix.md` |
| `build.sh`, `rocknix_compat.h` | compilation croisée |
| `build_x86.sh` | témoin x86_64 |
| `build_*.log` | journaux de compilation |
| `outils/` | lanceurs `hsfa_run` aarch64 et x86_64, cœurs témoins x86_64, script d'essai |
| `essais/` | référence x86 et planche |
| `hsfa_run-sysdir.diff` | correctif du lanceur |
| `fbneo/`, `fbneo_x86/` | clones de travail. Seuls changements : `hsfa_run.c` et les en-têtes générés `driverlist.h` / `gamelist.txt` (`REGEN_HEADERS`) |

Zips livrés (copies) :

| Zip | md5 | Provenance |
|---|---|---|
| `sfa3hsfa.zip` | `8c6b3f8e…` | `work/fbneo/`, 10/10 18:01 |
| `sfa3uhsfa.zip` | `9f618930…` | `work/fbneo/`, 10/10 18:01 |
| `sfa3hhsfa.zip` | `ce961a7b…` | `agent_fbneo_hyper/livraison/` |

Une nouvelle traduction demande seulement de recopier les zips. Les empreintes de `reference.md5` ne valent alors
plus : le script le signale.

Non fait :
- le patch « décors widescreen ». Sans lui, le 16:9 montre une bande claire au bord droit dans l'introduction
  d'Upper (planche) ;
- aucun essai sur la console.

## 7. Version du 2026-10-16 (session cloud, patchs FBNeo 1 à 10)

- Cœurs refaits sur l'arbre libretro/FBNeo `af5d3f3` + patchs 1 à 10 de `patches/fbneo/` (Vorbis, carte musique),
  avec `build.sh` (`FBNEO=<arbre>`). GCC 13.3 / glibc 2.39 (Ubuntu 24.04) : symboles au plus **GLIBC_2.38**,
  `NEEDED` = `libm`, `libc`, `ld-linux-aarch64` (inchangé). 10,7 Mo chacun après `strip`.
  md5 : `fbneo_hsfa_libretro.so` `d17e80a8…`, `fbneo_hsfaws_libretro.so` `f5fce850…` (`GITbdc9ef132`).
- **Exécutés pour la première fois sur ARM**, sous `qemu-aarch64` (la session cloud l'a ; la machine locale non) :
  frontal `tools/fbneo-hsfa/essais/joue_linux.c` compilé en aarch64, VERSUS d'Hyper piloté (Ryu A-ISM contre Ryu
  X-ISM, adversaire à 1 PV, 8 000 images), zip d'Hyper tout en Ogg (201 Mo).
  - mêmes choix et mêmes musiques qu'au PC x86_64 : `0002`, `0181 -> Y554`, `0192 -> Y571` (×2), `0004` ;
  - son : 969 échantillons sur 12,9 millions diffèrent de ±1 (arrondis flottants du décodage et du
    rééchantillonnage), corrélation 0,99999999997 ;
  - cœur 16:9 : 448×224, combat, K.O. et écran RESULT corrects (captures vérifiées) ;
  - `strip` sans effet sur la sortie (même md5 du WAV, `f4dd61dc`).
- La vitesse sous émulation ne dit rien de la console. Essai à faire : `tools/rocknix/essai_son/` (notice §7 bis
  de `LISEZMOI-rocknix.md`), qui mesure les images/s et vérifie les musiques ; à lancer avec le zip ADX puis Ogg.
- Paquet envoyé à l'utilisateur (hors dépôt) : `hsfa-rocknix-2026-10-16.zip` (cœurs, `.info`, notice, système ES,
  `essai_son/` avec `joue_arm`). Pas de zip de jeu : à construire avec `paquet_fbneo.py`.
- Le frontal d'essai se recompile ainsi :
  `aarch64-linux-gnu-gcc -O2 -o joue_arm tools/fbneo-hsfa/essais/joue_linux.c -ldl -lm` (glibc ≥ 2.34).

