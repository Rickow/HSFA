# tools/max — SFA3 MAX (PSP) : persos, graphismes, code

Documentation : **[`docs/MAX-Etude-Contenu-Persos.md`](../../docs/MAX-Etude-Contenu-Persos.md)**.
Aucune donnée de jeu dans le dépôt : les outils lisent vos fichiers, désignés par variables d'environnement.

## Variables d'environnement

| Variable | Fichier attendu | Utilisée par |
|---|---|---|
| `SFA3MAX_EBOOT` | EBOOT EU **déchiffré** de SFA3 MAX (`ULES00235_EBOOT.BIN`, dump PPSSPP) | décodeur, code, `nature/` |
| `SFA3MAX_ISO` | ISO EU de SFA3 MAX (ULES-00235) | `plpac.py` (extraction) |
| `SFA3WS_DIR` | clone de `Rickow/SFA3max-PSP-widescreen` (lecteur ISO9660) | `plpac.py` |
| `SFA3_ZIP` | set CPS2 **complet** `sfa3.zip` (programme + graphismes) | vérité terrain CPS2, sondes |
| `ANTHOLOGY_DIR` | conteneurs extraits de l'Anthology (`roN_usa_gfx_*.bin`) | comparaisons Anthology |
| `EE_STD`, `EE_HYPER` | dumps EE 32 Mo de l'Anthology (SFA3, Hyper) | `nature/` |
| `SFA3MAX_CACHE` | *(optionnel)* dossier des caches, défaut `~/.cache/sfa3max` — **hors dépôt** | tous |
| `SFA3MAX_PAC_DIR` | *(optionnel)* fichiers `plXX` extraits, défaut `$SFA3MAX_CACHE/pac` | tous |

Exemple : un fichier `env_max.sh` à côté de votre `env.sh`, qui exporte ces variables, puis `source env_max.sh`.

## Outils

| Fichier | Rôle |
|---|---|
| `paths.py` | lecture des variables ci-dessus |
| `plpac.py` | conteneur `plXX_e.pac` (9 entrées) ; `python3 plpac.py` extrait les 43 fichiers |
| `maxtile.py` | décodeur de tuiles, portage exact de `FUN_000ceb6c` (698 180/698 180 validées) |
| `pvr.py` | liste de coups (GBIX/PVRT, pixels linéaires) |
| `frames.py` | entrée [0] : table de frames et grilles de cases (4 tuiles, en colonnes) |
| `render.py` | assemblage d'une frame : sous-palette, miroirs |
| `sprites.py` | rendu de frames ; `--ingrid` : structure composite d'Ingrid + poses recomposées |
| `movelists.py` | rend les 43 listes de coups + planche des noms (→ `pl_mapping.json`) |
| `inventory.py` | palettes, tuiles, volume en format CPS2, par perso |
| `cps2gfx.py` | décodage des graphismes CPS2 à l'identique de FBNeo (`Cps2LoadTiles`) |
| `cps2_tiles.py` | tuiles CPS2 d'origine en index de pixels (vérité terrain) |
| `ro_tiles.py` | unités CPS2 de l'Anthology via `src/hsfa/anthgfx.py` (espace FBNeo, tous conteneurs) |
| `cmp_tiles.py` | tuiles PSP (espace FBNeo) retrouvées dans Upper (`ro5`) |
| `validate_cps2.py` | PSP et Anthology contre la CPS2 : même forme, permutation `i → 16−i`, unités Anthology exactes |
| `relocs.py` | relocations de l'EBOOT → mots-pointeurs exacts |
| `modules.py` | **méthode finale** : modules de code par perso (référence : `modules_resultats.txt`) |
| `charcode2.py` | fonctions communes d'analyse du code (`reach()` ne mesure PAS le code d'un perso) |
| `charcode3.py` | tentative intermédiaire, remplacée par `modules.py` |
| `xref.py`, `lzc.py` | références code → adresse ; LZ de l'Anthology (test négatif sur le PSP) |
| `pl_mapping.json` | ID → perso, établi visuellement |
| `nature/` | preuve que MAX est un port C natif : `regfile*.py`, `probe_scan.py`, `xref_arcade.py`, `disasm.py`, `sig68k.py` (signatures non discriminantes, conservé pour mémoire) |
