# Banc des coups (MAME)

Banc rejouable des coups spéciaux et des supers. Une partie VERSUS est lancée et sauvegardée **par le script Lua**
(jamais `-state`). Chaque coup du plan est ensuite rejoué depuis cette sauvegarde, image par image. On compare la
traduction à l'oracle arcade (`sfa3ud`), ou à une référence figée pour la non-régression. Rapport :
[BANC-COUPS](../../docs/rapports/BANC-COUPS.md). Variante FBNeo du banc : `tools/sondes-recherche/banc_coups.py`.

| entrée | rôle |
|---|---|
| `banc_coups.sh <ro3\|ro5\|ro9> [perso] [version]` | banc des coups d'un jeu (tableau des coups du guide, produit par `tools/guide-coups`) |
| `banc_max.sh <copie figée MAX> [coups\|fins\|max\|croises\|arcade]` | **non-régression de l'intégration MAX**. C'est la condition de livraison de tout lot MAX : aucune régression native. |
| `frame_data.sh [perso…]` | frame data des coups normaux contre SuperCombo (étalonnage sur Ryu / Ken) |
| `determinisme.sh <n> <module> <plan> <id>` | reproductibilité d'un essai |
| `lance.sh <sortie> <module> <script.lua>` | une partie MAME. Modules : `ref3` / `refjp` (arcades), `ro3`, `ro5`, `ro9`, `max`, `sfa` / `sfa2` / `sfz2al` / `sfa2u`. |
| `outils/` | plan, notation, verdicts (`compare.py`, `compare_strict.py`), tableaux, résumés, comparaisons de passages |
| `lua/banc_coups.lua` | script du banc ; `lua/tournee_max_copie.lua` = copie FIGÉE de `tools/integration-max/upper/lua/tournee_max.lua` plus le compteur de tours (banc MAX et banc de jour) ; ajouts `LUA_EN_PLUS` : `trace_*`, `dump_objram`, `stat_sprites` ; sondes `sonde_etat`, `sonde_arcade` |

Configuration : `HSFA_WORKSPACE` (références figées `work/references/<v>`, fork MAME, `work/mame`) et `HSFA_BANC_LUA`
(dossier de `banc_mem.lua`, `banc_plans.lua`, `banc_sprites.lua` ; défaut `<workspace>/work/mame`). Les données vivent
dans `<workspace>/work/banc_coups/` : tableau des coups, `roms_arc`, `oracle_jp`, copies MAX, résultats. Elles ne sont
pas publiées : ROM, relevés et frame data récupérée. La frame data publiée vient du wiki SuperCombo (crédit).

```sh
source config.env
tools/banc-coups/banc_coups.sh ro3 Ryu A
tools/banc-coups/banc_max.sh <workspace>/work/banc_coups/max53 coups fins
```

`banc_max.sh … fins` (max58, 13/11): the Arcade script is `TOURNEE_FINS` (default `<HSFA_WORKSPACE>/work/mame/tournee.lua`,
the folder `lance.sh` runs in; the step stops if it is missing). Options: `FINS="00,01"` (subset, hex ids), `FINS_PAR`
(games run side by side; default `MAXMAME`/2, set it to `MAXMAME` once the references are cached), `REPRISE=1` (skips
the ids already in `fins.tsv`). A game with no frame logged (reference or candidate) is `VIDE`, never `OK`, and is
listed apart in `RESUME-MAX.md` ("non concluant", to rerun); `lance.sh` refuses an empty output folder or Lua script.
Before this fix the copies outside `<workspace>/work/banc_coups` ran MAME with no script and wrote "OK, 0 round".
