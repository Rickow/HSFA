# Sondes de la recherche

Outils des mesures de [`docs/rapports/recherche/D-SONDES.md`](../../docs/rapports/recherche/D-SONDES.md).

## `banc_coups.py`

Joue un geste de J1 contre une liste d'adversaires, dans le cœur FBNeo HSFA, sur Upper (+MAX), Hyper ou SFA3 d'arcade.
Chaque essai relance une partie VERSUS depuis la mise sous tension, environ 4 s sur un PC. Le script lit la vie de J2
dans la RAM, ou, avec `--trace`, la trajectoire de J1.

```sh
export HSFA_JOUE=<workspace>/joue_linux HSFA_COEUR=<workspace>/fbneo_hsfa_libretro.so HSFA_SYS=<workspace>/system
HSFA_ZIP=<workspace>/sfa3uhsfa.zip python3 banc_coups.py --jeu upper --j1 0a --gestes sd_30_n_mp,hp --adv 00,0d,26,27,2d,2e
HSFA_ZIP=<workspace>/sfa3hhsfa.zip python3 banc_coups.py --jeu hyper --j1 0a.Z3.iX --gestes sd_30_n_mp --adv 00.Z3.iX,0d.Z3.iX
HSFA_ZIP=<workspace>/sfa3.zip      python3 banc_coups.py --jeu arcade --j1 0a --gestes sd_30_n_mp --adv 00,0d
HSFA_ZIP=<workspace>/sfa3uhsfa.zip python3 banc_coups.py --jeu upper --j1 0a --gestes sd_30_n_mp --adv 0d --trace
```

`joue_linux` se compile depuis `tools/fbneo-hsfa/essais/joue_linux.c` (voir l'en-tête de ce fichier). Les essais vont
dans `banc_coups/` (option `--sortie`). Chaque dossier garde ses entrées, le journal du cœur et les captures.

Points à connaître :

- **Touches** : depuis le patch 11, Select fait office de pièce et de roulette sur la grille, et Start sert aux EX et
  aux S-ISM. Start J2 n'est donc appuyé qu'une fois, avant la grille.
- **Persos** : le pilote de sélection (`tournee.h`) est écrit pour la grille d'Hyper. Sur Upper, il valide, mais le
  perso est imposé par `HSFA_POKE` : octet 68K `+$103` en ordre de traduction, `+$102` sur l'arcade.
- **ISM** : Upper part en X-ISM par défaut, l'arcade en A-ISM. Dans Hyper, l'ISM est dans la spécification (`.iX`,
  `.iA`, `.iV`). Comparer à ISM égale.
- **Temps** : le geste part au début de manche + 303 images (`HSFA_ECART` ; 450 pour la matrice, car l'intro de Karin
  dans Hyper rend la main plus tard). Le début est fixe sur Upper (2627) et sur l'arcade (3466),
  où les persos sont imposés. Dans Hyper, il dépend du trajet du curseur sur la grille (1084 pour Ryu/Ryu, 1108 pour
  Bison/Sakura) : `debut_manche()` le mesure une fois par paire. Ces valeurs valent pour les constructions notées dans
  D-SONDES ; à remesurer sur une autre construction (journal `tournee.log`).
- **Gestes** : `hp`, `hpsd_<t>_<av|ar>`, `sd_<t>_<av|ar|n>_<lp|mp|hp>`. Voir l'en-tête du script.

## `banc_matrice.py`

Joue tous les coups spéciaux, supers et lancers de SFA3 du tableau BradyGames (hors dépôt : texte protégé ; voir
`tools/guide-coups/`). Chaque coup est joué par J1 contre Ryu, à deux distances, dans deux jeux à ISM égale (par défaut
Hyper Z3 et l'arcade, en A-ISM). Le script compare ensuite les dégâts.

```sh
export HSFA_ZIP_HYPER=<workspace>/sfa3hhsfa.zip HSFA_ZIP_ARCADE=<workspace>/sfa3.zip   # + HSFA_JOUE, HSFA_COEUR, HSFA_SYS
python3 banc_matrice.py --tableau <workspace>/coups_sfa_anthology.csv --jeux hyper,arcade --proc 4
python3 banc_matrice.py --coup "Ryu:↓↘→↓↘→:Punch" --jeux hyper,arcade     # un seul coup
```

- **Résultat** : `banc_matrice/matrice.tsv`, une ligne par coup et par distance. Les écarts sont marqués `ECART`, et
  les coups non joués ont leur raison.
- **Geste** : 3 images par direction, 60 pour une charge. 360° = → ↘ ↓ ↙ ← ↖ ↑. Le bouton part sur la dernière
  direction. `--force L|M|H` choisit la force pour « Punch » / « Kick ».
- **Jauge** : le niveau est le mot `+$21C`, mis à `$1B0` (3 niveaux de `$90` ; la taille d'un niveau est en `+$11E`)
  avant le geste. Elle vaut pour l'A-ISM. Sur Upper en X-ISM, ça ne suffit pas : la super ne part pas.
- **Distances** : « loin » = départ de manche (x `$220` / `$2E0`) ; « pres » = J2 replacé à 56 px.
- **Limites** : les supers à suites (Sardine's Beach Special de R. Mika) dépendent de l'instant de chaque appui ; un
  écart isolé est à revoir à la main avant d'en conclure quoi que ce soit.

## Trouver le code d'un écart (D-SONDES §4)

Sans MAME, on trouve la routine fautive en quatre outils :

- **`sonde_pc_fbneo.diff`** : sonde à appliquer à un arbre FBNeo de banc (jamais au cœur livré). Elle écrit une ligne
  `image Wn|Rn PC adresse valeur` par accès 68K dans une plage.
  - variables : `HSFA_SW=lo-hi` (écritures), `HSFA_SR=lo-hi` (lectures), `HSFA_SI=i0-i1` (images), `HSFA_SF=fichier` ;
  - construction : patcher `src/cpu/m68000_intf.cpp`, recompiler ce seul fichier (ligne de `cps_mem.cpp` du journal de
    construction), relier sous un autre nom, puis remettre le fichier d'origine ;
  - usage : `HSFA_COEUR=<sonde.so> HSFA_SW=ff8400-ff84ff python3 banc_coups.py ...` (vitesses `+$40` / `+$44`, angle
    `+$3C` de J1, etc.).
- **`dechiffre_cps2.c`** : déchiffre le programme 68K d'un zip CPS2 (`sfa3.zip`) en deux images (instructions,
  données). Il reprend l'algorithme de FBNeo, voir l'en-tête.
- **`desas68.py IMAGE ADRESSE N`** : désassemble (capstone). Image d'une construction HSFA : `sz3ud.03c` … `sz3.10b`
  concaténés, octets échangés par mot.
- **`paires_exg.py IMAGE FIN`** : liste les `MOVE Dy,Dx ; MOVE Dx,Dy`, signature d'un `EXG` perdu.

Pour un essai de correctif, **`rustine_angle.py ZIP ZIP_SORTIE [roxr,exg,bclr,autres]`** réécrit, dans une copie de
l'archive d'Hyper du 2026-10-11, les pertes de §4 (sites vérifiés octet par octet). C'est une preuve au banc : la
correction se fait dans le traducteur.

Pièges :

- le frontal `joue_linux` prend **16 captures au plus** par essai : tracer par lots de 16 ;
- l'image de la sonde est `nCurrentFrame`, qui peut avoir une image d'écart avec les captures ;
- dans les traductions, un long a ses moitiés échangées (`a3000004` = `$0004A300`) et les octets sont au mot près
  inversés (`+$3C` de l'arcade = `+$3D`).

## `dwarf1.py`

`python3 dwarf1.py SECTION_DEBUG [STRUCTURE]` : lit une section `.debug` DWARF 1 (compilateur MetroWerks MIPS des jeux
PS2 de Capcom) extraite par `objcopy -O binary --only-section=.debug JEU.elf sortie.debug`. Sans argument, liste les
structures (nom, taille, nombre de champs) ; avec un nom (`_PlayerWork_`), ses champs et leurs décalages. Exemple :
l'exécutable de *Capcom Fighting Evolution* (README de la recherche, §5).

