# Persos MAX dans Upper (option MAX=1)

Ajoute à Upper (ro5) les quatre persos de SFA3 MAX : Eagle ($26), Maki ($27), Yun ($2D) et Ingrid ($2E).
Sans `MAX=1`, la construction ne change pas : la ROM reste identique au bit près.

## Construire

```sh
SFA3MAX_CACHE=~/.cache/sfa3max_v2_etire BANC=banc_max MAX_FINS=1 MAX_CONTRES=1 ./construit_max.sh
mkdir -p banc_max/roms_fork && ln -sfn ../roms_ro5/sfa3ud banc_max/roms_fork/sfa3hx
```

1. `prepare_max.py` traduit et assemble le code et les données MAX de la session MAX.
2. `mame_test.py` lance avec `MAX=1` les crochets d'`integre_max.py`. Ils posent les données par perso, agrandissent les tables par ID à 48 entrées (`agrandit_max.py`) et ajoutent les talons au code de l'image.

## Vérifier

- Nonreg : `BANC=banc_max bash untranspile/nonreg_ro5_max.sh`. Résultat attendu :
  - 20 000 images sans exception ;
  - trois parties Arcade finies : 00 en 27 manches, 04 en 24, 02 en 34.
- Paquet FBNeo (pilote `sfa3umhsfa`, patch 0013) : `MAX_BANC=<banc relatif à HSFA_WORK> python3 tools/fbneo-hsfa/paquet_fbneo.py upper_max`.
  Le paquet importe `max_cache.py` depuis `scripts/untranspile` (`src/hsfa` du dépôt), ou depuis `HSFA_MAX_CACHE_DIR` :
  `max_cache.py` doit donc être publié à cet endroit.

## Variables

| Variable | Rôle |
|---|---|
| `SFA3MAX_CACHE` | Cache de la session MAX. Le cache utilisé est noté dans le banc. |
| `MAX_FINS=1` | Fins des persos MAX. |
| `MAX_CONTRES=1` | Contres des persos MAX. |
| `MAX_ALPHA_EFFETS`, `MAX_ALPHA_REMANENCES` | Bit 12 additif des effets et des rémanences (1 par défaut). |
| `MAX_GARDE_INGRID` | Garde de la liste d'effets d'Ingrid (1 par défaut). |
| `MAX_SON` | ROM son du paquet. |

La liste des fichiers est dans `fichiers.txt`. Avant de publier, il faut :
- reporter à la main les deux blocs du correctif de `mame_test.py` qui ne s'appliquent plus ;
- remplacer les chemins écrits en dur (§4 de `fichiers.txt`) par des variables.
