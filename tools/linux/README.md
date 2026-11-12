# Cœur Linux x86_64 compatible glibc ancienne (2.27)

## Constat

Le cœur Linux x86_64 du lot du 10/11 (`linux/fbneo_hsfa_libretro.so` ef13c96a, `fbneo_hsfaws` cdf953d7) est compilé
avec la glibc de la machine de construction (2.43) et demande :
`GLIBC_2.43` (atan2f), `GLIBC_2.38` (`__isoc23_strtol`, `__isoc23_strtoul`, `__isoc23_strtoull`),
`GLIBC_2.33` (stat64), `GLIBC_2.29` (exp, log, pow).

Batocera 43.1 a la glibc 2.40 : RetroArch refuse le cœur (essai réel, VM) :
```
[ERROR] [Core] Failed to open libretro core: "/tmp/lot1011/fbneo_hsfa_libretro.so"
[ERROR] [Core] Error(s): /lib/libm.so.6: version `GLIBC_2.43' not found (required by ...)
```
Même refus attendu sur toute distribution plus ancienne que la glibc 2.43 (Ubuntu 24.04 = 2.39, Debian 12 = 2.36…).

## Recette (sans root, sans conteneur)

Même principe que les cœurs Recalbox (`tools/recalbox/recalbox_compat.h` et `.c`), adapté à x86_64 :
- `hsfa_x86_compat.h`, inclus en tête de chaque fichier (`-include`) : `.symver` de `exp`, `log`, `pow`,
  `atan2f` vers `GLIBC_2.2.5` ;
- `hsfa_x86_compat.c` (objet ajouté au lien) : `stat`/`stat64` → `__xstat`/`__xstat64@GLIBC_2.2.5`
  (`_STAT_VER_LINUX` = 1 sur x86_64) ; `__isoc23_strto*` → `strto*` (symboles cachés, `link.T` n'exporte que
  `retro_*`) ;
- `build_x86_glibc_ancienne.sh` (`FBNEO=<arbre patché> SORTIE=<dossier>`) : arbre ff6298e (copie de l'arbre Linux du lot, 0001-0026 + 0027, arbre git
  52d0220a), **même commande que le lot** (`make platform=unix SUBSET=hsfa|hsfaws REGEN_HEADERS=1`, drapeaux du
  Makefile inchangés), plus `PLATFORM_DEFINES=-include …/hsfa_x86_compat.h` et `LDFLAGS=…/hsfa_x86_compat.o`.
  libstdc++ et libgcc_s restent dynamiques (`GLIBCXX_3.4.21` au plus : GCC ≥ 5).

Les trois fichiers sont dans ce dossier (`tools/linux/`).

## Résultat

| Cœur | md5 | taille | GLIBC max | GLIBCXX max | NEEDED |
|---|---|---|---|---|---|
| fbneo_hsfa_libretro.so | 652eb5d1… | 10 798 464 | **2.27** | 3.4.21 | libstdc++.so.6, libm.so.6, libgcc_s.so.1, libc.so.6 |
| fbneo_hsfaws_libretro.so | 8f66a3a0… | 10 828 856 | **2.27** | 3.4.21 | idem |

Versions de symboles demandées (les deux cœurs) : `GLIBC_2.2.5 2.3 2.3.4 2.4 2.7 2.14 2.17 2.27`,
`GLIBCXX_3.4 3.4.9 3.4.21`, `CXXABI_1.3`. Liste complète : `symboles_glibc.txt`.
Chaînes personnelles : 0 ; version `GITff6298e`.

## Non-régression (harnais sans écran `hsfa_run`, mêmes réglages que nr_lot.sh L43/Lst « d_on »)

Référence = cœur Linux du lot 10/11, rejouée dans les mêmes conditions. 5 jeux × 4:3 / 16:9 :

```
OK    sfa3   43  : captures 60/60 differentes 0 ; log.txt =, son.wav =
OK    sfa3   st  : captures 60/60 differentes 0 ; log.txt =, son.wav =
OK    upper  43  : captures 60/60 differentes 0 ; log.txt =, son.wav =
OK    upper  st  : captures 60/60 differentes 0 ; log.txt =, son.wav =
OK    max    43  : captures 80/80 differentes 0 ; log.txt =, son.wav =
OK    max    st  : captures 80/80 differentes 0 ; log.txt =, son.wav =
OK    hyper  43  : captures 80/80 differentes 0 ; log.txt =, son.wav =
OK    hyper  st  : captures 80/80 differentes 0 ; log.txt =, son.wav =
OK    greffe 43  : captures 80/80 differentes 0 ; log.txt =, son.wav =
OK    greffe st  : captures 80/80 differentes 0 ; log.txt =, son.wav =
```
Images, journaux et son **identiques octet pour octet** (zips : sfa3 = script 08/11 43d2310d, autres = zips de
`combat.sh`).

## Essai réel

Batocera 43.1 x86_64 (VM) : les deux cœurs se chargent, les 5 jeux vont jusqu'au combat en 4:3 et 16:9 (voir
`docs/guide/installation-batocera.md` ; captures hors dépôt).

## Adoption

Retenu par le porteur le 11/11 : les cœurs Linux des lots à partir du 11/11 (patch 0029) sont construits avec cette
recette ; ils marchent partout où marchait l'ancien (glibc ≥ 2.27 au lieu de 2.43), avec un comportement identique.
