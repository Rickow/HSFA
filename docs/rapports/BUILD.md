# `hsfa_build.py` : construire les jeux HSFA à partir de l'ISO de l'utilisateur

Agent `agent_build`, 2026-10-10. J'ai écrit dans `<workspace>/work/agent_build/`. Les dossiers `work/mame*`,
`roms*`, l'ISO et le disque externe ont été lus, jamais modifiés (les sous-processus tournent avec
`PYTHONPYCACHEPREFIX` : aucun `__pycache__` n'est écrit dans les dossiers d'outils). Exception, après vérification
md5 (§9) : trois outils partagés ont reçu un correctif, `untranspile/hsfa_gfx.py`, `untranspile/banques.py` et
`work/fbneo/paquet_fbneo.py` (diffs et originaux dans `correctifs/`).

Fichiers :

| Fichier | Rôle |
|---|---|
| `hsfa_build.py` | le script (Python 3 standard ; numpy pour les étapes graphiques) |
| `sortie_propre/` | construction complète depuis zéro (SFA3 + Upper + Hyper), 598 Mo, 4 min 32 s |
| `sortie_propre/EMPREINTES.txt` | md5 de toutes les ROM produites et du contenu des archives |
| `sortie_propre/journal.txt`, `journaux/*.log` | journal en français, sortie complète de chaque script appelé |
| `comparaison/` | archives reconstruites depuis le banc (`HSFA_WORK=<workspace>/work`, lecture seule) pour la comparaison |
| `md5_banc_debut.txt`, `md5_banc_fin.txt` | md5 des ROM du banc relevées avant et après mes constructions |
| `rom_iso.py` | reconstruction de la ROM graphique CPS2 de SFA3 depuis l'ISO seule (§5) |
| `sortie_iso/`, `sortie_iso2/` | deux constructions **ISO seule** indépendantes (sans `--arcade`) : `EMPREINTES.txt` et zips identiques à l'octet |
| `sortie_arc/` | construction avec `--arcade`, depuis zéro, outils corrigés : identique à `sortie_propre/` (§9) |
| `iso_seule/` | mesures de la voie ISO seule (`equivalence.py`, `fidelite.py`, `plan_eq.py`, `manquantes.py` et leurs sorties `.txt`) |
| `banc/` | attractions MAME `sfa3ud` (rompaths copiés, `lance.sh`, `compare_snaps.py`, `comparaisons.txt`) |
| `correctifs/` | diffs et originaux des outils partagés, essais `t_*` |

## 0. En bref

1. **Les ROM programme sont reproduites à l'identique pour les trois jeux** : SFA3, Upper et Hyper, 8/8 fichiers
   chacun, md5 égales à celles du banc. Il en va de même pour tout le reste : blocs externes, `carte_image.txt`,
   `chutes.json`, tables de banques (55 / 104 / 70 fichiers), `hsfa_gfx.bin`, `hsfa_plans.bin`, ROM son de SFA3,
   ROM son hybride d'Upper et table du lecteur de flux.
2. **Les archives FBNeo sont identiques membre à membre** à celles que `paquet_fbneo.py` produit depuis le banc :
   - `sfa3uhsfa.zip` : 27/27 membres identiques ;
   - `sfa3hsfa.zip` : il manque seulement le bloc MAX de démonstration (`ext_b00000.bin`, `pl26.bin`), qui ne vient
     pas de l'ISO PS2. `paquet_fbneo.py` suit maintenant une liste explicite des fichiers attendus (§8).
3. **L'ISO seule suffit (voie par défaut).** `--arcade` devient facultatif. Sans lui, `rom_iso.py` reconstruit
   `sz3.13m`-`sz3.20m` au format MAME/FBNeo à partir de X_DATA (§5) :
   - `sz3.14m`, `16m`, `18m`, `20m` : **md5 de l'arcade** ;
   - `sz3.13m`, `15m`, `17m`, `19m` : différents, et **ne peuvent pas** être identiques : 9 tuiles de l'arcade
     n'existent nulle part dans X_DATA, et l'ordre des tuiles de sprites du quart 0 n'est pas dans l'ISO ;
   - programmes, son et tables restent identiques au banc (8/8 × 3 jeux) ; l'attraction MAME `sfa3ud` donne le
     même journal des modes et des images identiques à 1-13 pixels près (§5.5).
4. **Zips déterministes** : deux constructions donnent des zips identiques à l'octet (§7).
5. **Correctifs** : `hsfa_gfx.py` idempotent, `paquet_fbneo.py` (dates fixes, liste explicite), `banques.py`
   (option de fenêtre des plans, qui corrige aussi un défaut de la voie arcade) : §8-§9.
6. **Trouvé en route : le banc travaille sur une variante de X_DATA.** `work/xdata/X_DATA.BIN` (md5 `53821dc5…`)
   provient de l'ISO « All Unlocked » (`~/hsfa/iso/SFA_Anthology_AllUnlocked_WORK.iso`), pas de l'ISO USA d'origine
   (md5 `97a0b8de…`).
   - Seuls deux groupes changent : `b_usa` e203 et la gfx ro6 e527.
   - Aucun des deux ne sert à SFA3, Upper ou Hyper, d'où les résultats identiques.
   - Le script vérifie donc l'ISO **par groupe de jeu**, pas en bloc.
7. **Le banc n'a pas bougé pendant mes constructions** : md5 identiques au début (12 h 56, dernière reconstruction de
   la validation) et à la fin (13 h 27), et encore à 14 h 50 (`sz3ud.03c` des trois jeux inchangés depuis 12 h 56-57).
   Le traducteur partagé n'a pas changé non plus : dernier fichier modifié à 12 h 54.

## 1. Chaîne recensée

### 1.1 Entrées

**ISO PS2** *Street Fighter Alpha Anthology* (USA, SLUS-21317, 4 698 767 360 o). Copie de l'utilisateur :
`<disque>/HDD 2To 2/ROMS/PS2/Street Fighter Alpha Anthology/Street Fighter Alpha Anthology (USA).iso`. Je l'ai
trouvée à partir du chemin par défaut `E:/ROMS/PS2/...` d'`extract_anthology.py`, par un accès ciblé au disque
externe.

| Fichier ISO 9660 | Taille | md5 | Usage |
|---|---|---|---|
| `SYSTEM.CNF` | 57 | `b28f4071bad98c50b51cf02db9c451a2` | identification (non bloquant) |
| `SLUS_213.17` | 572 352 | `11e411ffa03dded28a26fd4241523c35` | identification (non bloquant) |
| `X_DATA.BIN` (LBA 1 306 224, ISO `0x9F738000`) | 200 214 528 | `97a0b8de2b7437898602415077bac31f` (origine) ; `53821dc5…` (All Unlocked) | **seul fichier consommé par la construction** |
| `Y_DATA.BIN` | 1 823 404 032 | (taille seulement) | flux ADX, lus à l'exécution par le cœur (`ydata.txt` → ISO) |

**Contrôle par groupe de jeu.** X_DATA est une archive AFS de 553 entrées. Ses groupes sont délimités par les modules
MWo3. Chaque groupe a une empreinte (md5 de la concaténation de ses entrées) :

| Groupe | Entrées | md5 | Requis pour |
|---|---|---|---|
| `b` | e203-e205 | `e535bb5c…` | — (modifié par « All Unlocked ») |
| `ro1` | e206-e223 | `b93119d8…` | Hyper (banques SFA1 208-220) |
| `ro2` | e224-e252 | `dfdbe6bc…` | Hyper (banques SFA2 229-248) |
| `ro3` | e253-e347 | `be7e3bab…` | SFA3, Upper (son ro3 e287/e288), Hyper |
| `ro4` | e348-e349 | `44b7dd98…` | — |
| `ro5` | e350-e525 | `e3741dd9…` | Upper, Hyper, **et SFA3** : banques 391-412 et 456-457 de sa carte |
| `ro6` | e526-e535 | `0b0e4d1a…` | — (e527 modifié par « All Unlocked ») |
| `ro7`, `ro8` | e536-e543 | … | — |
| `ro9` | e544-e552 | `7fc8e6e0…` | Hyper, table du lecteur de flux |

Entrées AFS effectivement lues (relevé de la construction) :
- **modules MWo3** : e253 (ro3), e350 (ro5), e544 (ro9) ;
- **son** : e287/e288 (Z80 / QSound de SFA3), e388/e389 (Upper) ;
- **fichiers « anim » et fichiers fixes** (`assets_natifs`) : 289-311, 390, 458-524, 547 ;
- **banques SFA3** : 254, 258-285, 312, 391-412 (sauf 404 et 406), 456, 457 ;
- **banques Upper** : 351, 355-386, 391-457, 525 (32×32), 353 (décor) ;
- **banques Hyper** : 208-220, 229-248, 355-386, 545, 546 (décor), 548 (32×32).

**Empreintes intermédiaires** (contrôlées par le script) :
- `manifest.csv` : `673d96d8…` en fins de ligne LF ; la référence `76a76db5…` a été écrite sous Windows en CRLF,
  contenu identique ;
- modules décompressés : `ro3` `e4826fe4…`, `ro5` `17e47592…`, `ro9` `b4662de9…`.

**Hors ISO, facultatif** : la ROM graphique d'arcade de SFA3 `sz3.13m`-`sz3.20m` (`--arcade`, md5 dans
`REF_ARCADE_GFX`), commune à tous les jeux `sfa3*` de MAME/FBNeo ; ici lue dans `work/mame/roms/sfa3ud`. Sans elle,
la ROM est reconstruite depuis X_DATA (§5 ; md5 de la reconstruction dans `REF_ISO_GFX`). Avec elle, les tables
sont celles du banc à l'octet.

**Hors ISO, facultatif** : l'ISO PSP de SFA3 MAX (persos MAX, étape non implémentée).

**Données d'outils (dans le dépôt, sans contenu de jeu)** : `hooks_fork_ro*.json`, `map_chain2.json`,
`map_ro3_sfa3.json`, `const_evidence.json`… Ce sont des adresses et des correspondances, lues par `translate` et
`mame_test`. On les régénère avec `hooks_fork.py` si le module change.

### 1.2 Étapes

Toutes les étapes sont des appels aux scripts existants (sous-processus `hsfa_build.py _lancer spec.json` ; voir §2.3).

| Étape | Script appelé | Entrées | Sorties (dans `--sortie`) | Durée | État |
|---|---|---|---|---|---|
| `iso` | (lecteur ISO 9660 interne) | ISO | `cache/iso/X_DATA.BIN` + contrôles | 1-6 s | **fait** |
| `afs` | `extract_anthology.main()` | X_DATA | `cache/anthology_extract/` (manifeste, MWo3, Z80, gfx, `carto.txt`) | 1 s | **fait** |
| `module_roN` | `mwo3_codec.decompress` | `roN_usa_prog68k.mwo3` | `decompressed/roN_usa_prog68k.bin` | 1 s | **fait** |
| `son_sfa3` | `gen_son.lire/decoupe('ro3')` | X_DATA e287/e288 | `travail/mame/roms_tr/sfa3ud/sz3.01/02/11m/12m` (= arcade) | <1 s | **fait** |
| `son_upper` | `gen_hybride.main()` | X_DATA e287/288/388/389 | `travail/agent_son_ro5/hybride/roms_hybride/hx3.*` | 1 s | **fait** |
| `prog_sfa3/upper/hyper` | `mame_test.main()` (`MODULE`, `TRAVAIL`, `XDATA`, `ANIM_CACHE`) | module, X_DATA | `travail/mame*/roms_*/sfa3ud/sz3*.0xc`, `ext_*.bin`, `carte_image.txt`, `chutes.json`, `audit_exacts.txt` | 45-70 s | **fait** |
| `arcade` | `rom_iso.py` (sans `--arcade`) ou interne (avec) | X_DATA e254-e286 / `--arcade` | `cache/arcade/sfa3ud/sz3.13m-20m` + `phoenix.key` (20 × `$FF`) | 16 s / <1 s | **fait** (placée après les programmes : son et programmes se construisent sans elle) |
| `gfx_sfa3` | `banques.py tout`, `banques.py 312`, `banques.py plans` (`HSFA_PLANS_FENETRE=1` en voie ISO) | X_DATA, ROM graphique, module | `travail/mame/banques/` | 25-45 s | **fait** |
| `gfx_upper` | idem (`525`), puis `hsfa_gfx.py`, `hsfa_plans.py` | idem | `banques/`, `banques_hx/`, `hsfa_gfx.bin`, `hsfa_plans.bin` | 45-60 s | **fait** |
| `gfx_hyper` | idem (`548`) avec `HSFA_GFX_BASE` = ROM étendue d'Upper | idem + `gfx_upper` | idem (`mame_ro9`) | 35-40 s | **fait** (identique au banc), non publié |
| `paquet_sfa3/upper` | `paquet_fbneo.construit()` (`HSFA_WORK`, `HSFA_SORTIE`) | tout ce qui précède | `sfa3hsfa.zip` (racine de la sortie), `sfa3uhsfa.zip` (+ `_sources.txt`) | 3-5 s | **fait** |
| `paquet_hyper` | — | — | — | — | **à faire** : pilote FBNeo d'Hyper et entrée de `paquet_fbneo.JEUX` |
| `flux` | `gen_table_flux.main()` (`--module ro9 --toc ""`) | module ro9 | `systeme/fbneo/hsfa/hsfa_flux_table.txt` + `ydata.txt` (chemin de l'ISO) | <1 s | **fait** (558 codes, identique hors commentaires) |
| `max` | — | `--max ISO_PSP` | — | — | **squelette** (ignorée sans `--max`, refusée avec) |
| `empreintes` | (interne) | toutes les sorties | `EMPREINTES.txt` (+ comparaison `--comparer`) | 1 s | **fait** |

Le dossier `travail/` reprend la disposition de `<workspace>/work` (`mame`, `mame_ro5`, `mame_ro9`,
`agent_son_ro5/hybride/roms_hybride`). `paquet_fbneo.py` le prend donc tel quel par `HSFA_WORK`, sans modification.

### 1.3 Chemins codés en dur (liste de paramétrages à faire)

Je les ai tous contournés à l'exécution : le lanceur interne importe le module, remplace l'attribut, puis appelle
`main()`. Pour se passer de ces remplacements, il faut que chaque script lise une variable d'environnement
(proposition : `HSFA_EXTRACT`, `HSFA_XDATA`, `HSFA_ARCADE`, `HSFA_ANIMS`, `HSFA_BANQUES`).

| Script (copie de référence `src/hsfa`) | Ligne | Valeur en dur | Contournement |
|---|---|---|---|
| `CLAUDE CODE/extract_anthology.py` | 14-15 | `PATH = E:/ROMS/PS2/.../X_DATA.BIN`, `OUTDIR = E:/CLAUDE CODE/anthology_extract` | attributs remplacés |
| `profils.py` | 6 | `EXTRACT` (modules décompressés), **sans variable** | attribut remplacé |
| `profils.py` | 22/39/57 | `travail` = `work/mame*` | variable `TRAVAIL` (existe) |
| `assets_natifs.py` | 22 | `EXTRACT` (manifeste) | attribut remplacé |
| `assets_natifs.py` | 23 | `CACHE = work/cps2/anims`, **lu en premier** : une construction prendrait des fichiers d'un autre poste | `CACHE` et `CACHE_ECRIT` remplacés (+ `ANIM_CACHE`) |
| `assets_natifs.py` | 82 | `os.environ["XDATA"]` obligatoire si le cache manque | variable `XDATA` |
| `census.py` | 22 | `RO3` = module selon `MODULE` | attribut remplacé (étapes gfx) |
| `banques.py` | 18-21, 27, 32 | `XDATA` (variable existe), `MANIF`, `ROMDIR` (arcade), `OUT` et `MOD['out']` (**ne suivent pas `TRAVAIL`**) | attributs remplacés |
| `banques.py` | 105 ; `hsfa_plans.py` 19 | `sys.path` → `<workspace>/anthology_extract` (mwo3_codec) | dossier des outils MWo3 ajouté à `sys.path` |
| `gen_son.py` | 15-17 | `XDATA`, `EXTRACT`, `ARCADE` ; `main()` en ro3 **ouvre l'arcade sans tester** | attributs remplacés ; appel de `lire`/`decoupe` au lieu de `main` |
| `agent_son_ro5/hybride/gen_hybride.py` | 44 | `ARCADE` (recoupement facultatif) ; importe `gen_son` depuis `..` | attribut remplacé ; `gen_son` pré-importé |
| `agent_son_ro5/hybride/z80son.py` | 5 | `X` (inutilisé par `gen_hybride`) | attribut remplacé |
| `mame_test.py` | 565 | liens symboliques vers `<workspace>/work/mame/roms/sfa3ud` (plante si le dossier n'existe pas) | `os.listdir` neutralisé pour ce chemin (aussi `<workspace>/…`) |
| `mame_test.py` | 268-330 | `~/.cache/sfa3max/converti/…` | sous `MAX_DEMO` / `MAX_PAL` / `MAX_PORTRAITS` : l'environnement des sous-processus est **nettoyé** |
| `agent_hyper_son/table_son.py` | 11 | `DEC` (module décompressé) | attribut remplacé |
| `agent_flux/gen_table_flux.py` | 20 | `SON = work/agent_hyper_son` (+ `--csv`/`--toc` par défaut) | attribut remplacé, `--module ro9 --toc ""` |
| `paquet_fbneo.py` | — | rien (`HSFA_WORK`, `HSFA_SORTIE`) ; mais disposition fixe (`mame/roms_tr`, `agent_son_ro5/hybride/roms_hybride`) et inclusion de **tout** `ext_*.bin`/`banques/*.bin` présent | disposition reproduite |

Ces chemins en dur ne servent que dans `__main__`, donc pas pendant la construction : `extra_regs.py` 69/243,
`assemble.py` 366, `translate.py` 3955-3957, `hooks_fork.py` 33, `natmiss.py` 8 (lu à l'import, mais `natmiss` n'est
importé que par `hooks_fork`), `mwo3_codec.py` 97.

**`hsfa_gfx.py` n'était pas idempotent** (relancé, il récrivait un `hsfa_gfx.bin` vide) : corrigé à la source (§8.1).
L'étape `gfx_*` efface encore `banques/` et `banques_hx/` avant d'enchaîner `banques` → `hsfa_gfx` → `hsfa_plans`,
pour ne garder aucune table d'une version précédente.

## 2. Usage

```
python3 hsfa_build.py --anthology "Street Fighter Alpha Anthology (USA).iso" --sortie hsfa_sortie \
        [--arcade sfa3.zip] [--jeux sfa3,upper,hyper] [--max SFA3MAX.iso] \
        [--etape NOM] [--jusqua NOM] [--force] [--liste] [--comparer <workspace>/work] [--sans-flux] \
        [--date-source SECONDES] [--plans-fenetre auto|oui|non]
```

- `--anthology` accepte l'ISO, ou un dossier extrait qui contient `X_DATA.BIN`. Les images `.chd`, `.bin` et `.cso`
  sont refusées avec un message : il faut une ISO à 2 048 o/secteur.
- `--arcade` (**facultatif**) accepte un zip (`sfa3.zip`, ou tout zip contenant `sz3.13m`…`sz3.20m`) ou un
  dossier ; on peut le donner plusieurs fois. Chaque fichier est vérifié par md5. Sans lui : voie ISO seule (§5).
- `--date-source` : date fixe des membres des zips, en secondes Unix (défaut : `$SOURCE_DATE_EPOCH`, sinon
  315532800 = 1980-01-01). Voir §7.
- `--plans-fenetre` : tables `plan1`/`plan2` restreintes aux codes que le banc et FBNeo honorent (§5.4). `auto`
  (défaut) = `oui` sans `--arcade`, `non` avec (tables identiques au banc).
- `--iso-differente` : continuer malgré une empreinte de groupe différente.
- `--python-numpy` : interpréteur à utiliser pour numpy (défaut : l'interpréteur courant, sinon `<HSFA>/venv`).
- `--outils-*` (ou `HSFA_OUTILS_*`) : emplacement des scripts, avec les défauts de ce poste.
- Les étapes `paquet_hyper` et `max` échouent proprement sans arrêter la suite.

### 2.1 État et cache

- **`etat.json`** : pour chaque étape, une clé et la liste des sorties (taille, md5). La clé est le sha1 de trois
  choses : les paramètres utiles, les sorties des étapes dont elle dépend, et l'empreinte de ses outils (tous les
  `.py`/`.json` du dossier `untranspile`, etc.).
- **Saut d'une étape** : elle est sautée si sa clé n'a pas changé et que ses sorties sont intactes. Une relance sans
  changement prend 1,6 s.
- **Granularité** : une modification du traducteur ne refait que `prog_*`, `gfx_*`, `paquet_*`. Un changement de
  `--jeux` ne refait pas les jeux déjà construits (modules décompressés un par un).
- **`--etape X`** refait X puis les suivantes (les précédentes doivent être faites). **`--jusqua Y`** s'arrête après Y.
- ⚠ `hsfa_build.py` lui-même n'entre pas dans la clé. Après une modification du lanceur, utiliser `--force`.

### 2.2 Journal

- **`journal.txt`** : horodaté, en français. Marques : `>>` étape, `ok` faite, `!!` anomalie.
- **`journaux/<étape>.log`** : sortie complète du script appelé, avec la commande et les variables passées.
- **`specs/`** : description exacte de chaque appel (patchs, argv), pour le rejouer à la main.

### 2.3 Lanceur interne

`python3 hsfa_build.py _lancer spec.json` fait, dans l'ordre :
1. ajoute les dossiers d'outils à `sys.path` ;
2. importe les modules à corriger et remplace leurs attributs (`banques.MOD.out` = clé de dictionnaire) ;
3. appelle `module.main()`, ou exécute un court code d'appel (`gen_son`, `mwo3_codec`, `paquet_fbneo.construit`).

Les sous-processus tournent avec :
- `nice -n 19` (POSIX) ;
- un **environnement propre** : `PATH`, `HOME`, `LANG`… plus `MODULE`, `TRAVAIL`, `XDATA`, `ANIM_CACHE`. Ainsi aucun
  réglage d'essai (`MAX_DEMO`, `MAINS`, `PILE`, interrupteurs de `translate`) ne fuit dans une construction ;
- `PYTHONPYCACHEPREFIX` pointé dans le cache de la sortie.

## 3. Test de reproductibilité

### 3.1 Programmes (référence : `src/hsfa`, banc reconstruit le 2026-10-10 à 12 h 56)

| Jeu | `sz3ud.03c` produit | banc `roms_*/sfa3ud` | 8 fichiers |
|---|---|---|---|
| SFA3 (`ro3`) | `f2f46b7e534b60577142d4b90a16acb6` | `f2f46b7e…` | **identiques** |
| Upper (`ro5`) | `0485973bd788209793db22a6508d0329` | `0485973b…` | **identiques** |
| Hyper (`ro9`) | `69b2ac41d791f9285ad85afcede18493` | `69b2ac41…` | **identiques** |

Ont aussi été comparés au banc, tous identiques :
- **SFA3** : `ext_a04000.bin`, `ext_liste.txt`, `carte_image.txt`, `chutes.json`, `audit_exacts.txt`, les 55 tables
  de `banques/` ;
- **Upper** : idem (`ext_b04000`, `ext_c80000`), plus `hsfa_gfx.bin`, `hsfa_plans.bin` (version VIDE15 de 12 h 11)
  et les 104 + 104 tables de `banques/` et `banques_hx/` ;
- **Hyper** : `ext_940000`, `ext_c84000`, `hsfa_gfx.bin` (avec la ROM étendue d'Upper en tête), `hsfa_plans.bin`,
  70 + 70 tables.

Deux constructions (incrémentale, puis depuis zéro dans `sortie_propre/`) donnent des `EMPREINTES.txt`
identiques, à l'octet près des zips (voir §3.3). `PYTHONHASHSEED` n'a pas besoin d'être fixé.

### 3.2 Son et table de flux

- `sz3.01/02/11m/12m` tirés de X_DATA : identiques à l'arcade `sfa3ud`.
- `hx3.*` : identiques à `agent_son_ro5/hybride/roms_hybride` (2026-10-04).
- `hsfa_flux_table.txt` : 558 codes identiques à la table d'`agent_flux`. Seuls les commentaires de durée diffèrent :
  l'outil d'origine les lit dans `ydata_toc.csv`, tiré de Y_DATA, et le script ne le lui donne pas.

### 3.3 Archives FBNeo

- **Comparaison avec les archives que `paquet_fbneo.py` produit depuis le banc à 13 h 27** (dossier `comparaison/`) :
  - `sfa3uhsfa.zip` : **27/27 membres identiques**, sauf `hsfa_info.txt` (dates et chemins) ;
  - `sfa3hsfa.zip` : seuls diffèrent `hsfa_ext.bin` (pages `$B00000-$B11FFF`) et `hsfa_tab.bin`. La cause est que
    le banc contient `work/mame/ext_b00000.bin` et `banques/pl26.bin`. Ce sont le bloc de frames et la table du
    perso MAX `pl26` (Eagle) de la démonstration §99/§105 (`banques_max.py`, données de l'ISO PSP).
    `paquet_fbneo.py` inclut tout ce qu'il trouve. Une construction de référence sans `MAX_DEMO` ne pointe pas vers
    `$B00000`. **À confirmer** par une partie dans le cœur.
- **Comparaison avec les archives publiées le 2026-10-07** (`work/fbneo/*.zip`). En plus de ce qui précède :
  - le programme diffère, car le traducteur a évolué depuis (§140-§141) ;
  - `hsfa_gfx.bin` d'Upper diffère, car `hsfa_plans.bin` a été reconstruit ce midi (tuile 32×32 vide → pen 15).
- **Les octets des zips sont maintenant reproductibles** (§7). `EMPREINTES.txt` donne en plus le md5 de chaque
  membre. (Les zips de `sortie_propre/`, construits avant le correctif, ont des dates réelles.)

### 3.4 Banc pendant le test

| | début (13 h 08) | fin (13 h 27) |
|---|---|---|
| `mame/roms_tr/sfa3ud/sz3ud.03c` | `f2f46b7e…` (12 h 56) | `f2f46b7e…` (12 h 56) |
| `mame_ro5/roms_ro5/sfa3ud/sz3ud.03c` | `0485973b…` (12 h 56) | `0485973b…` (12 h 56) |
| `mame_ro9/roms_ro9/sfa3ud/sz3ud.03c` | — | `69b2ac41…` (12 h 57) |

Le banc n'a pas changé pendant mes constructions. Les fichiers complets sont dans `md5_banc_debut.txt` et
`md5_banc_fin.txt`.

## 4. Points à rendre portables

1. **Chemins des scripts** (§1.3) : variables d'environnement, avec des défauts relatifs au dépôt
   (`src/hsfa`…). Ensuite, le lanceur peut perdre ses remplacements d'attributs.
2. **Outils absents du dépôt `github/`** :
   - `extract_anthology.py` ;
   - `mwo3_codec.py` (le décompresseur existe en double dans `legacy/tools/unlock_patcher.py`) ;
   - `agent_hyper_son/table_son.py`.

   Ce qui y est déjà : `gen_hybride.py` et `z80son.py` (`src/hsfa`), `paquet_fbneo.py`
   (`tools/fbneo-hsfa`), `gen_table_flux.py` (`tools/flux`), `lz148778.py`.
3. **La copie publiée `src/hsfa` est en retard et n'est pas exécutable telle quelle.**
   - `translate.py` a 53 lignes d'écart hors chemins ; `mame_test.py` 2 lignes.
   - Les chemins y sont remplacés par la chaîne `<workspace>`.

   Il faut publier la copie de référence avec les chemins en variables d'environnement, et fixer une **version
   (commit) de référence** des outils dans `BUILD`.
4. **Dépendance arcade** : levée (voie ISO seule, §5) ; `--arcade` reste possible.
5. **Outils externes** :
   - *nécessaires* : **Python 3 + numpy** (seulement `gfx_*` : `banques`, `cps2rom`, `anthgfx`, `hsfa_gfx`,
     `hsfa_plans`). Pillow et capstone ne servent pas (capstone : `kernel68k.__main__` seulement) ;
   - *inutiles pour construire* : **MAME** (banc et `diag.py`), **unidasm** (`prof_an.py`, diagnostics), **vasm**
     (seulement `tools/integration-max/conversion`, donc l'étape MAX à venir). L'assembleur 68K de la chaîne est
     `assemble.py`, en Python pur ;
   - *ISO* : lue en Python pur (ISO 9660), ni montage, ni 7-Zip.
6. **Cœurs FBNeo HSFA** (Linux, Android, widescreen, flux) : compilés à part depuis les patchs
   (`patches/fbneo/*.patch`) et publiés comme binaires. Ils ne contiennent
   aucune donnée de jeu. Le script ne les compile pas : c'est une chaîne de compilation séparée (NDK, etc.).
7. **Hyper** : le programme et les graphismes sont reproduits. Restent :
   - le pilote FBNeo `sfa3hhsfa` (ROM étendue à `HSFA_GFX`, plans `300,340,3a0`, `BANC_COMMUN=545`, pointeur `FF40BC`) ;
   - l'entrée `paquet_fbneo.JEUX['hyper']` ;
   - le son : Hyper n'a pas de Z80 dans son groupe. Il faudra la ROM hybride d'Upper plus le lecteur de flux.
8. **MAX** : il faudra extraire de l'ISO PSP (`--max`) ce que `~/.cache/sfa3max/converti/plNN/` contient
   aujourd'hui (palettes, frames, portraits), puis appeler `banques_max.py` et `mame_test` avec
   `MAX_DEMO`/`MAX_PAL`/`MAX_PORTRAITS`. L'étape est prévue et sa clé tient déjà compte de `--max`.

## 5. Voie ISO seule

### 5.1 Principe (`rom_iso.py`, étape `arcade` sans `--arcade`)

L'Anthology contient la ROM graphique CPS2 de SFA3 en valeurs **brutes** (HANDOFF §45 ; FBNeo affiche 15 − brute),
dans ses propres conteneurs (`anthgfx.py`). `rom_iso.py` la remet au format MAME/FBNeo (`cps2rom.encode`, aller-retour
exact) :

| Zone CPS2 (tuiles 16×16) | Source dans X_DATA | Placement |
|---|---|---|
| quart 1, `$10000-$1DFFF` | `e255` : 22 528 tuiles 8×8 (dupliquées dans les deux moitiés), 4 096 32×32, 29 696 16×16 | **à leur place** |
| quart 2 | `e257` (65 536 16×16) | **à leur place** |
| quart 3 | `e286` (65 536 16×16) | **à leur place** |
| quart 0 + fin du quart 1 (`$1E000-$1FFFF`) : 73 728 places | banques de sprites `e254` (communs) puis `e258`-`e285` (persos), 16×16 | contenus distincts, non vides, absents des quarts 1-3 : **72 192**, rangés dans l'ordre des banques ; 1 536 places restent vides (`$1FA00-$1FFFF`, valeur brute 15) |

Seul le groupe `ro3` est lu (empreinte de groupe contrôlée). 16 s, numpy. `phoenix.key` (20 × `$FF`) est générée.
Le résultat est vérifié par md5 (`REF_ISO_GFX` dans `hsfa_build.py`) ; la reconstruction est déterministe (deux
constructions indépendantes, mêmes md5).

### 5.2 Résultat comparé à l'arcade (`iso_seule/rom/rom_iso.json`)

| Fichier | md5 reconstruit | md5 arcade | octets égaux |
|---|---|---|---|
| `sz3.13m` | `03209d40778fe8bdb9efdd31e0042319` | `47cd1261e9affa4340752f333cd9d1bd` | 56,3 % |
| `sz3.14m` | `5a50dd038a8c6d442be3d969eedce032` | **identique** | 100 % |
| `sz3.15m` | `e941f0517d7ec3e7cc0d833e7a3c69d6` | `d1a50389059d4d2e3b977808401f7766` | 60,8 % |
| `sz3.16m` | `7612958e66c88b17e30d376f876b77c7` | **identique** | 100 % |
| `sz3.17m` | `aa08a44c45b7f48b58b2de1e8a5cbb28` | `4087aabf55ef7e7fe5e24d141c744962` | 56,5 % |
| `sz3.18m` | `ee582226a3430d844c54924f3f4a652b` | **identique** | 100 % |
| `sz3.19m` | `73fb9e595fd853cd0ff6216f8d915195` | `5a0b9c825183d6efe62698e772fa0022` | 61,0 % |
| `sz3.20m` | `50bd0e58150ea9e65ffa54353ba007a3` | **identique** | 100 % |

Les fichiers pairs (`14m`…`20m`) portent les quarts 2-3, les impairs (`13m`…`19m`) les quarts 0-1. Tuile à tuile :
quart 0 : 2 / 65 536 à leur place ; quart 1 : 57 760 / 65 536 ; quarts 2 et 3 : 65 536 / 65 536.

### 5.3 Pourquoi `13m`/`15m`/`17m`/`19m` ne peuvent pas être identiques

1. **Contenus absents du disque** (`iso_seule/manquantes.py`, `manquantes.txt`). 12 tuiles de l'arcade (toutes au
   quart 0) n'ont leur contenu dans aucune banque de `ro3` :
   - `069c6`, `069c7`, `069c9` existent ailleurs (`e225`/`e247` SFA2, `e359` Upper, `e527`) ;
   - `07e88`, `07e89`, `07e8e`-`07e91`, `07ecf`, `07edf`, `082ec` (13 à 256 pixels opaques) n'existent **nulle part**
     dans X_DATA (conteneurs 8×8/16×16/32×32 de tous les groupes, mémoires de décor `e256`/`e353`/`e546`).
     Aucune banque de l'Anthology ne les utilise.
2. **Ordre perdu.** Les banques sont des sous-ensembles **réorganisés** (ordre d'utilisation, HANDOFF §45/§82) et le
   programme de l'Anthology désigne les tuiles par (emplacement, numéro local), jamais par le code CPS2 : la position
   des 65 536 tuiles du quart 0 et des 8 192 de la fin du quart 1 n'est pas sur le disque.
3. Inversement, 627 contenus de la reconstruction n'existent pas dans l'arcade : tuiles **retouchées par
   l'Anthology** (souvent quelques pixels).

Conséquence : cette ROM ne remplace **pas** `sfa3.zip` pour le jeu d'arcade d'origine. Le programme `sfa3ud` stock,
qui vise les codes CPS2, affiche des persos en désordre (§5.5). Elle est faite pour la chaîne HSFA, qui retrouve chaque
tuile **par son contenu** (`banques.py`) et la désigne par les tables.

### 5.4 Tables : équivalence et correctif des plans (`iso_seule/equivalence.txt`, `fidelite.txt`)

`equivalence.py` compare, entrée par entrée, la tuile **affichée** (règles de `banc_sprites.lua` / `banc_plans.lua`)
entre la construction arcade et la construction ISO :
- **sprites** : SFA3, 425 120 entrées ; seules diffèrent 1 003 entrées **vides** côté arcade (tuile propre à
  l'Anthology, absente de la ROM d'arcade), résolues côté ISO. Upper et Hyper (`banques_hx`) : identiques, car
  `hsfa_gfx.py` range ces tuiles dans la ROM étendue dans les deux cas ;
- **`f312`** (scroll3) : identique ;
- **`plan1`** (scroll1, 8×8) : **régression** de la voie ISO, 427 entrées (SFA3). Le banc n'honore un code que dans
  la fenêtre du plan (`$20000-$2FFFF` en unités 8×8 ; plan2 : `$10000-$1FFFF`), sinon il affiche le code brut.
  Parmi les copies d'un même contenu, la règle de continuité de `banques.py plans` choisissait parfois une copie du
  quart 0 (moitié d'une tuile de sprite), donc hors fenêtre. L'arcade avait le défaut symétrique (156 entrées
  `plan2` sur une tuile vide du quart 0).

**Correctif** (`banques.py`, variable `HSFA_PLANS_FENETRE=1`, option `--plans-fenetre`) : les copies dans la fenêtre
passent d'abord. Mesure contre la vérité (la mémoire de décor de l'Anthology, `e256`, décompressée) :

| SFA3 | `plan1` justes / 141 312 | `plan2` justes / 35 328 |
|---|---|---|
| arcade, tables du banc | 24 591 (17,4 %) | 29 648 |
| ISO, sans fenêtre | 24 263 | 29 804 |
| **ISO, fenêtre** (défaut de la voie ISO) | **41 821 (29,6 %)** | **29 804** |
| arcade, fenêtre | 41 821 | 29 804 |

Avec la fenêtre, l'affichage de `plan1`/`plan2`/`f312` de SFA3 est **identique** entre arcade et ISO (`plan_eq.py` :
0 écart). Upper et Hyper servent leurs plans tels quels (`HSFA_PLANS`, fork : `banc_plans.lua` s'arrête avant la
conversion), leurs tables `plan1`/`plan2` ne servent pas à l'affichage.

**Proposition (non appliquée)** : la fenêtre par défaut aussi avec `--arcade` (+17 230 entrées `plan1` justes pour
SFA3). Cela change `plan1.bin`/`plan2.bin` du banc, donc à valider au banc avant. Ici, `auto` garde les tables du banc
avec `--arcade`.

### 5.5 Rendu au banc (attraction MAME `sfa3ud`, `banc/`)

`banc/lance.sh` : MAME stock `sfa3ud`, copie du rompath (`banc/rp_*`), `-nvram_directory`/`-cfg_directory` propres,
`-noreadconfig`, jamais `-state`, `nice -n 19`, aucune entrée, 6 000 images, 39 captures (image 300, puis toutes les
150). `compare_snaps.py` compare pixel à pixel et le journal des modes (`$FF8000-$FF8004`). Résultats
(`banc/comparaisons.txt`) :

| A | B | journal des modes | captures identiques | écarts |
|---|---|---|---|---|
| `run_arc` (`sortie_propre`) | `run_arc2` (`sortie_arc`, outils corrigés) | identique | **39 / 39** | — |
| `run_arc2` (arcade, tables du banc) | `run_iso` (ISO seule) | identique | 28 / 39 | 1 à 13 pixels par capture |
| `run_arc_fen` (arcade, fenêtre) | `run_iso` | identique | 29 / 39 | 1 à 6 pixels : les tuiles retouchées de l'Anthology (seul écart restant des tables, §5.4) |
| `run_arc2` | `run_arc_fen` | identique | 32 / 39 | 3 à 13 pixels : effet du seul correctif des plans |
| `run_orig_arc` (programme d'arcade d'origine, ROM d'arcade) | `run_orig_iso` (même programme, ROM ISO) | identique | 28 / 39 | **460 à 15 900 pixels** : sprites des persos en désordre, décors intacts |

La voie ISO seule donne donc, pour SFA3, le même déroulement et la même image que la voie arcade, aux tuiles
retouchées de l'Anthology près (là, c'est la voie ISO qui est fidèle au jeu PS2).

### 5.6 Intégration

- `--arcade` facultatif ; sans lui, l'étape `arcade` dépend d'`afs` et de `rom_iso.py`, `anthgfx.py`, `cps2rom.py`,
  `lz148778.py` (clé de cache) et contrôle les md5 de `REF_ISO_GFX`.
- Les archives FBNeo embarquent la ROM reconstruite. Le pilote HSFA garde les CRC d'arcade de `sz3.13m`-`20m` ; dans
  le cœur libretro, une ROM d'un pilote `hsfa` introuvable par CRC est cherchée **par nom** et chargée avec un
  avertissement (« Using ROM with unknown crc », `libretro.cpp`, l. 1162-1190 du clone `fbneo-hsfa-ws`). **Non essayé
  dans le cœur** ; le FBNeo autonome (hors libretro) refuserait probablement ces CRC. Si besoin : CRC à 0 pour ces
  huit fichiers dans le pilote.
- Hyper : inchangé (`HSFA_GFX_BASE` = ROM étendue d'Upper, construite contre la ROM reconstruite).
- Construction complète ISO seule : environ 7 min (trois jeux, deux constructions en parallèle).

## 6. Proposition pour Windows

- **Le script** est déjà en Python pur et multiplateforme :
  - `os.path` partout, aucun lien symbolique (copies) ;
  - `nice` seulement s'il existe ;
  - environnement propre qui garde `SYSTEMROOT`, `USERPROFILE`, `TEMP` ;
  - `PYTHONIOENCODING=utf-8` ;
  - chemins avec espaces gérés, ISO lue directement (pas de montage).
- **Distribution, au choix** :
  - (a) Python 3.12+ de python.org, `pip install numpy`, puis
    `py hsfa_build.py --anthology "D:\...\SFA Anthology (USA).iso" --arcade sfa3.zip --sortie D:\hsfa` ;
  - (b) un `hsfa_build.exe` (PyInstaller, environ 30 Mo avec numpy) qui embarque `tools/` ;
  - (c) le paquet « Python embarquable » (zip officiel) + numpy, avec un `hsfa_build.bat`.
- **À corriger dans les outils d'abord** :
  - les chemins en dur (§1.3) ;
  - `open()` sans `encoding=` : les fichiers écrits sont ASCII, mais lire un fichier UTF-8 sous cp1252 casserait ;
  - les fins de ligne : un CSV écrit en mode texte sous Windows a des CRLF, d'où les deux md5 du manifeste. Le
    script normalise avant de comparer.
- **Image `.chd`** : `chdman extractdvd` d'abord. Le script le dit dans son message d'erreur.

## 7. Zips déterministes

`paquet_fbneo.py` lit `SOURCE_DATE_EPOCH` (convention reproducible-builds.org) ; `hsfa_build.py` la lui passe toujours
(`--date-source`, défaut `$SOURCE_DATE_EPOCH`, sinon 315532800 = 1980-01-01 00:00). Avec elle :
- chaque membre est écrit par un `ZipInfo` à date fixe (UTC, 1980 au plus tôt), `create_system = 3`, droits `0644`,
  deflate niveau 6 ; l'ordre des membres était déjà fixe ;
- `hsfa_info.txt` : « construite le » = cette date, et les dates des sources sont ramenées à cette date au plus.

Sans la variable, le comportement est l'ancien (dates réelles).

Vérification :
- `sortie_iso/` et `sortie_iso2/` (deux constructions indépendantes) : `sfa3hsfa.zip` `eb31ea2679d57460d6bc9dea04c345d0`
  et `sfa3uhsfa.zip` `2e10f73d1448a6894ceb89121ec82959` **des deux côtés**, `EMPREINTES.txt` identiques hors date
  d'en-tête ;
- depuis le banc : `correctifs/t_ep1` et `t_ep2` identiques à l'octet.

## 8. Correctifs

### 8.1 `hsfa_gfx.py` idempotent (`correctifs/hsfa_gfx.diff`, appliqué)

Cause : il complétait `banques_hx/f<N>.bin` **en place** et ne recopiait `banques/` que si `banques_hx/` n'existait pas.
Relancé, il ne trouvait plus de tuile absente et récrivait un `hsfa_gfx.bin` vide. Correction : chaque table étendue
est recalculée depuis la table d'origine `banques/f<N>.bin` ; `banques_hx/` reçoit à chaque passage une copie fraîche
de `banques/` (sauf `plan2.bin`, écrite par `hsfa_plans.py`).

Essai (`correctifs/t_gfx`, Upper) : original relancé → `hsfa_gfx.bin` vide (`d41d8cd9…`) ; corrigé, deux passages →
`0dd63024f9e5cc3c392c763bc1ed5e7e` les deux fois, égal à la référence, tables identiques.

### 8.2 `paquet_fbneo.py` (`correctifs/paquet_fbneo.diff`, appliqué)

- `SOURCE_DATE_EPOCH` : §7.
- `HSFA_STRICT=1` : **liste explicite des fichiers attendus** par jeu. Blocs `ext_<adresse>.bin` = ceux de
  `ext_liste.txt` (écrite par `mame_test.py`) ; tables = `f<banque commune>`, les `f<N>` de `carte.txt` (lignes
  `perso`/`anim`), `f312`, `plan1`, `plan2`, plus `JEUX[..]['tables_en_plus']`. Un fichier attendu absent est une
  erreur ; un fichier en trop est ignoré et signalé (`ignore (absent de ext_liste.txt) : ext_b00000.bin`,
  `ignore (table non attendue) : pl26.bin`). Rien n'a été supprimé dans `work/mame`.
- `hsfa_build.py` passe toujours `HSFA_STRICT=1`.

Essais depuis le banc (`correctifs/t_*`, `membres.py`) :
- sans variable (`t_orig` contre `t_mod`) : tous les membres identiques, sauf `hsfa_info.txt` (dates) ;
- strict : `sfa3hsfa.zip` sans les restes MAX (56 tables au lieu de 57, pas de bloc `$B00000`) ; `sfa3uhsfa.zip`
  identique.

**Proposition (non appliquée)** : strict par défaut (`correctifs/paquet_fbneo_strict_par_defaut.diff`) ; cela
changerait le `sfa3hsfa.zip` produit depuis le banc. Le diff « hyper » d'un autre agent
(`agent_fbneo_hyper/paquet/paquet_fbneo.diff`) n'a pas été touché.

### 8.3 `banques.py` : `HSFA_PLANS_FENETRE` (`correctifs/banques.diff`, appliqué)

Voir §5.4. Sans la variable, sorties identiques : `plan1.bin`/`plan2.bin` de `ro3`, `ro5`, `ro9` refaits avec la
version corrigée = md5 de référence, contre la ROM d'arcade comme contre la ROM ISO (`correctifs/t_plans/*_def`).
Les autres sous-commandes (`tout`, `312`) n'ont pas changé de code.

## 9. Vérification après correctifs

- `sortie_arc/` : construction depuis zéro avec `--arcade` et les trois outils corrigés (6 min 26 s). Toutes les lignes
  d'`EMPREINTES.txt` (ROM, blocs, tables, `hsfa_gfx.bin`, `hsfa_plans.bin`, membres des zips) sont **identiques** à
  `sortie_propre/`. Les membres des zips aussi, sauf `hsfa_info.txt` (dates fixes). Programmes : 8/8 × 3 identiques
  au banc.
- `sortie_iso/` (reprise incrémentale) et `sortie_iso2/` : programmes 8/8 × 3 identiques au banc, mêmes empreintes.
- Rien n'a été écrit dans `work/mame*` (en particulier `mame_ro5`, où tourne une validation).

## 10. Upper MAX (`--jeux uppermax --psp-iso`) : les persos de SFA3 MAX depuis les deux disques

Agent `script_um`, 2026-11-07 (§202 du journal). Le jeu `uppermax` produit `sfa3umhsfa.zip` : Upper avec Eagle,
Maki, Yun et Ingrid, à l'état du lot **2b31** (banc_max52). Il part de deux entrées seulement :
- l'ISO PS2 de l'Anthology ;
- l'ISO PSP de *SFA3 MAX*, **européenne** (ULES-00235 v1.01) ou **américaine** (ULUS-10062, depuis le 13/11 : §10.7).

Il n'utilise ni programme d'arcade, ni EBOOT déchiffré, ni fichier d'atelier. Les outils sont dans
`tools/integration-max/upper_max/` (README) et `max/` (session MAX). Il faut aussi **vasm** (`vasmm68k_mot`,
`--vasm`), en plus de numpy.

### 10.1 Étapes

| Étape | Outil | Durée (07/11, machine chargée) |
|---|---|---|
| `psp` | édition (`PARAM.SFO` : ULES00235 ou ULUS10062), empreintes de `BOOT.BIN` (EBOOT **déjà en clair** dans l'ISO ; US : remis en disposition européenne) et des 4 `plXX_e.pac` | < 1 s (US : 3 s) |
| `max_donnees` | `regen_max.py` : cache MAX v2 et sources `.s`, produits par les outils de `max/` ; il ajoute les compléments (scripts et palettes de fin, portraits de victoire, sauts, parcours) | 83 s |
| `son_uppermax` | `son/chaine_son.py` : voix (VAG des pac), `se_mid`, table son ro9 → ROM son MAX (6 fichiers) et `commandes_*_max.s` | 8 s |
| `prog_uppermax` | `um_prog.py` : intégration MAX=1 figée à l'état 2b31 (`integration_2b31/`), vasm, traducteur | 56 s |
| `paquet_uppermax` | `paquet_fbneo.py upper_max` | 5 s |

Construction complète (Upper + Upper MAX), depuis zéro : 5 min 10 s, dont 2 min 32 s pour la partie MAX. Elle
occupe 1,1 Go. Sans `--psp-iso`, `uppermax` = `--jeux upper`, à l'octet.

### 10.2 Ce qui remplace le programme d'arcade `sfa3ud`

On a tracé les octets lus par chaque outil (`<workspace>/work/script_uppermax/outils/trace_site`).
- **Apprentissage** de la Rosette, qui lit le code 68K d'arcade : `tout`, `tailles68`, `evaluer`, `appris_acteurs`,
  `mouvements`, `champs_projectiles`. Leurs sorties lues ensuite sont **versionnées** dans
  `max/outils/rosette_code/` : `api_arcade_psp.json`, `champs_votes.json`, `tailles68.json`, `carte_champs.json`,
  `api_acteurs.json`. Elles ne contiennent que des adresses, des numéros de champs et des votes. Les autres sorties
  ne sont lues par personne.
- **Acteurs des fins** : les décisions de `rosette_donnees.py` (n° d'animations) sont versionnées dans
  `rosette_donnees_appris.json`. On ne peut pas lire les enregistrements du module ro3 à la place : l'Anthology y a
  modifié des octets (+1, +3, +6, +$1B-$1F) sur 26 fins sur 33.
- **Scripts de fin** des modèles d'arcade : lus dans le module **ro3** de l'ISO (table PS2 `0x584600` = `$26DCC`).
  Les 4 fins MAX converties sont identiques.
- `brouillons`, `tables_explicites`, `projectiles_max`, `acteurs_fins`, `anims_fins_max` importent le désassembleur
  mais lisent 0 octet du programme d'arcade.

### 10.3 Preuves

1. **Avec la ROM graphique d'arcade** (`--arcade`, programme d'arcade absent ; `<workspace>/work/script_uppermax/zero_arc`) : le zip
   est **identique au 2b31 sur 28/29 membres**. Seul `hsfa_info.txt` change (chemins, dates). Deux constructions
   donnent le même zip à l'octet (CRC `ba29a84e`).
2. **Voie ISO seule** (`zero_iso2`, construction depuis zéro dans une copie `git archive` du dépôt, auditée par
   `strace`) :
   - les fichiers ouverts sont uniquement la sortie, la copie du dépôt, les deux ISO, le venv, vasm et le système ;
   - **programme** (`sz3ud.03c` `7ede9d19` … `sz3.10b`), **ROM son** (hx3.* 6/6), `hsfa_ext.bin` et flux sont
     identiques au 2b31 ;
   - les différences sont celles de la voie ISO (§5) : `sz3.13m`/`15m`/`17m`/`19m`, `hsfa_gfx.bin`, `hsfa_tab.bin`.
3. **Équivalence d'affichage** (`tools/integration-max/upper_max/equivalence_um.py`, méthode du §5.4) : sur les 114 tables du banc
   (673 527 entrées, dont les banques des 4 persos MAX et les portraits), la tuile désignée est **la même**.
   Il y a une seule exception, `plan1`, et elle existe déjà pour Upper seul : Upper sert ses plans tels quels, la table
   n'est pas affichée.
4. **Cœur FBNeo** (cœur du 05/11, pilote de l'intégration) : chaque perso MAX contre Ryu, 6 000 à 9 000 images,
   zip 2b31 contre zip ISO seule. **656 captures sur 656 sont identiques au pixel** et les journaux du jeu et du
   lecteur de flux sont identiques. Le cœur charge par leur nom les ROM aux CRC inconnus (avertissement attendu).

### 10.4 Défaut corrigé en route (voie ISO seule)

Les outils MAX numérotent leurs tuiles neuves après les tuiles propres d'Upper (`hsfa_gfx.bin`). Le paquet et
l'intégration les placent en `G_MAX = $4DAAB` (`max_cache.py`). En voie ISO, Upper a **569 tuiles propres de moins**
(celles de l'Anthology sont dans la ROM reconstruite). Sans correctif, les banques MAX visaient `$4D872` : les persos
s'affichaient faux. `regen_max.py --g-max 4DAAB` complète la copie de `hsfa_gfx.bin` lue par les outils MAX avec des
tuiles nulles jusqu'à G_MAX. Ce correctif est sans effet en voie arcade.

### 10.5 Écarts connus et limites

- **Upper MAX suit le traducteur courant (v161)** : l'étape `prog_upper_v160` a été retirée (11/11). L'intégration ne lit
  plus aucune adresse d'image écrite en dur : `integre_max.py` trouve ses sites par motif unique et sauts décodés, puis les
  recoupe avec les va MIPS de la carte de construction ; une adresse du moteur non résolue par `convertit_max.py` arrête
  la préparation. Preuves : avec les interrupteurs v161 à 0 (`um_prog.py --env`) et `CONV_SANS_ADRESSES=1B6B6`, le
  programme est celui du lot max55 à l'octet ; outils de contrôle `tools/integration-max/upper_max/controle/`
  (`equiv_integration.py`, `equiv_pointeurs.py`) à repasser à chaque version du traducteur qui déplace le code.
  Marge à surveiller : le code d'Upper finit en `$A0EB8` (+ talon de 78 o), les données commencent en `$A1000` ; au-delà,
  la base des données saute de `$1000`. Cas exercé le 11/11 sur des bases d'essai (`LONG_POSTINC=0` : code +178 o ;
  `DROP_SR=0` : code +`$1656`, données +`$2000`) : mêmes 739 va modifiées, aucune différence inexpliquée
  (`equiv_pointeurs.py maxA maxB 2000`). Ces bases ne sont pas jouées : contrôle statique seulement.

- **Écarts du cache MAX régénéré** face au cache de l'atelier (121/126 identiques) :
  - scripts de fin : lignes opA (vitesse 0 au lieu du décalage PSP), que l'intégration remet de toute façon à 0 ;
  - `parcours_max.json` : commentaires seulement.
- `s/acteurs_fins_max.s` reste à l'**état 2b31** : il est produit avec le `traduire.py` de d98c4f1
  (`traduire_2b31.py`). La version actuelle de la session MAX passera d'abord par un lot d'essai et un banc des fins.
- **Région** : EU et US (§10.7), même jeu à l'octet. JP (ULJM) refusée : autre disposition du code, textes japonais.
- **Assembleur** : depuis le 2026-11-07, `tools/asm68k/hsfa_asm68k.py` (MIT, bibliothèque standard) remplace vasm,
  dont la licence ne permet pas de l'embarquer. Sortie identique à vasm (binaire, liste, symboles) sur les 5 appels
  de la construction et sur un corpus synthétique ; construction Upper MAX sans vasm = même zip (128fb48d). Variables :
  `HSFA_ASM=vasm` (vasm), `HSFA_ASM=compare` (les deux, échec s'ils diffèrent : à faire une fois par nouveau lot de
  sources). Détail : `tools/asm68k/README.md`.

### 10.6 Sous-ensemble de vasm employé (référence de l'assembleur maison)

Il y a cinq appels : `tout.s` dans `prepare_max.py`, puis les 4 blocs de frames (`bloc_d80000`, `bloc_dc0000`,
`bloc_e00000`, `bloc_e40000`) dans `conv/convertit_frames.py`, dont les symboles sont relus dans la liste. L'appel
principal :

`vasmm68k_mot -m68000 -spaces -Fbin -quiet -maxerrors=500 -L tout.lst -o tout.bin tout.s`

- **Source** : un seul fichier (`tout.s`, 73 195 lignes), syntaxe Motorola. Les espaces sont admis dans les
  opérandes (`-spaces`). Il n'y a ni `include`, ni macro, ni section.
- **Sortie** : binaire brut (`-Fbin`). La liste `-L` sert à relire les symboles (format « Symbols by name »).
- **Directives** :
  - `org` (3 : `$3A0000`, `$B80000`, `$D68000`) ;
  - `equ` (3 833) ;
  - `dc.b` / `dc.w` / `dc.l`, `dcb.b` / `dcb.w`, `ds.b` / `ds.l` ;
  - `even`, `cnop 0,4` ;
  - un seul `ifnd` / `endif`.
- **Étiquettes** : globales, et locales en `.nom` (166).
- **Expressions** : `+ - * / << >> & |` et parenthèses ; constantes `$hex` et décimales.
- **Instructions** : 106 mnémoniques du 68000 avec taille explicite (`.b/.w/.l`). Les branchements sont courts
  (`.s`) ou laissés à l'assembleur (`bsr`, `bra`, `bcc` sans taille : choix de la taille par vasm, à reproduire à
  l'identique). Mnémoniques particulières : `movem.l`, `move sr`/`move ccr`, `scc`, `dbra`, `divs.w`, `muls`, `exg`,
  `swap`.
- **Modes d'adressage** :
  - `Dn`, `An`, `(An)`, `(An)+`, `-(An)` ;
  - `d(An)`, `d(An,Xn)`, `d(PC)` ;
  - `abs.w`, `abs.l`, `#imm`, listes de registres.

### 10.7 Disque PSP américain (ULUS-10062, agent `psp_us`, 13/11)

Demande : construire Upper MAX sans mélanger une ISO PS2 américaine et une ISO PSP européenne. Décision (13/11) : la
US est acceptée et donne le **même jeu** que l'EU (textes à l'orthographe de l'Anthology).

- **Fichiers** : 381 de chaque côté (`USRDIR/USA/DATA`, suffixe `_U`, contre `USRDIR/EUR/DATA`, `_E`). 366 sont
  identiques à l'octet, dont `PL26-29` (sprites, palettes, sons des 4 persos MAX), `SE_MID`, tous les `WIN`, `OP`, `PL`.
  Différents : icônes, `PARAM.SFO` (US v1.00, EU v1.01), mise à jour système, logo du titre (`TITLE`, `OPEN` : non
  lus), `BOOT.BIN`, et 4 fichiers de textes.
- **`BOOT.BIN`** (EBOOT en clair, PRX) : une seule différence de code, une fonction d'écran du moteur (`0xBDAB4`) plus
  courte de 2 instructions en US. Tout le code qui suit, dont les modules des 41 persos (`0xE9724-0x1CAF0C`), est 8 octets
  plus bas ; `.rodata`, `.data`, `.bss` ne bougent pas. `psp_region.relaie()` remet le code US aux adresses européennes :
  2 `nop` en `0xBDAC4`, puis branches, `j`/`jal`, paires HI16/LO16 et mots R_MIPS_32 recalculés grâce aux tables `.rel.*`
  du PRX, en-têtes de section et de programme (2 branches, 9 180 sauts, 41 paires, 9 005 mots). Le résultat diffère
  encore de l'EBOOT européen en 30 zones (10 754 o), aucune lue par la construction : cette fonction d'écran, une
  variable de `.bss`, une image PNG intégrée et les variables qui la suivent, les chaînes de région (`usa`/`eur`,
  `_u`/`_e`, numéro de série), 4 numéros de sprite d'une animation d'écran (`0x2234E4`).
- **Textes** : 6 lignes écrivent « Shadowloo » sur le disque US, « Shadaloo » sur l'EU et partout dans l'Anthology
  (78 fois dans Upper) : le scénario d'Eagle et la fin d'Ingrid (`END26`, `END29`), un dialogue d'Eagle et trois de
  Yun (`BD26`, `BD28`). `psp_region.normalise()` les réécrit (octet de longueur − 1, x de la ligne + 3 ou 4 : 6 règles,
  aucun texte du jeu dans le dépôt) ; les 4 fichiers obtenus ont l'empreinte des fichiers européens (contrôlé).
- **Lecture** : étape `psp` (édition par le DISC_ID, empreintes de la table de la version, `cache/psp/BOOT.BIN` en
  disposition européenne) ; `regen_max.py` copie le `DATA` de l'édition sous les noms européens ;
  `max/outils/convert/dialogues_max.py`, qui relit l'ISO (`eur/data` en dur), est lancé avec une lecture servie par
  ce cache : `max/` n'est pas modifié. Le disque japonais (ULJM) est refusé avec un message qui le nomme.
- **Preuves** (même ISO PS2, voie ISO seule) : `sfa3umhsfa.zip` construit depuis l'ISO EU avec le code d'avant, et
  avec le code neuf depuis l'ISO PSP US d'origine, l'ISO US « déchiffrée », l'ISO EU et l'ISO EU « déchiffrée » (sorties
  neuves, puis disque changé dans la même sortie, dans les deux sens) : **les 7 zips sont identiques à l'octet**
  (29/29 membres, md5 `5e40447a92ef6947c44d5eb3bc12966d`). Le cache MAX
  régénéré (`cache/max_regen`) est identique hors `title_e.pac` / `open_e.pac` (non lus) et dates du zip graphique
  interne. Les ISO « déchiffrées » ne diffèrent des ISO d'origine que par `SYSDIR/EBOOT.BIN`, qui n'est pas lu.

## 11. Hyper + Arcade (`--jeux hyperarcade`) : la greffe du mode Arcade d'Upper, depuis l'ISO (expérimental)

Agent `script_ha`, 2026-11-08 (journal §212) ; passage à ro9a36 le 11/11 (§217, §11.6), à ro9a37 (traducteur v161)
le 12/11 (§221, §11.7), à ro9a38 le 12/11 (§223, §11.8), à ro9a39 le 12/11 (§224, §11.9), à ro9a40 le 13/11 (§228, §11.10), à ro9a41 le 13/11 (§230, §11.11). Le jeu `hyperarcade` produit `sfa3hahsfa.zip` (pilote `sfa3hahsfa`) à l'état **ro9a41** de la
greffe (programme `sz3ud.03c` `be88f3f9…`, `sz3ud.04c` `ae411424…` ; ro9a40 : même `sz3ud.03c`, `sz3ud.04c` `998374db…` ; ro9a39 : `2459b5a5…` ; ro9a38 : `2dfdb15c…` ; ro9a37 : `627c98c4…` ; ro9a36 : `93e88fee…` ; ro9a35b : `650b1bec…`). Il ajoute `upper` et `hyper` : la greffe part de leurs sorties.

### 11.1 Étapes

| Étape | Outil | Durée (08/11, 4 constructions en parallèle) |
|---|---|---|
| `greffe_hyperarcade` | `tools/greffe-arcade/construction/greffe_ha.py` : code figé `ro9a41/` + relevés (`releves_ro9a41/`, TSV reconstitués par `releves_tsv.py`) matérialisés dans `cache/greffe_ha` ; plan seul → table A5 → module, bloc, traduction (traducteur de la greffe v161) | 150-160 s |
| `paquet_hyperarcade` | `ro9a41/paquet/paquet_fbneo.py ro9a` (flux Ogg : encodeur v3 portable) | 8 s |

Entrées venues de la construction : modules ro5 / ro9 décompressés, cache des anims, `X_DATA.BIN`, banques d'Hyper et
d'Upper, module ro9 (corrigé si la table du rejeu est donnée, sinon d'origine). Recette : `ro9a41/greffe/vars_ro9a41.txt`
(interrupteurs de ro9a40 + `PAIRES_CODE=1` ; `HA_VARS` la remplace ; `vars_ro9a40.txt` redonne ro9a40, = ro9a39 + `PAL_VERSION=1 COUL_CPU_VERSION=1 PORT_VERSION=1 BARRE_LOGO_FACE=1` ; `vars_ro9a39.txt` redonne ro9a39, = ro9a38 + `X2_TABLES=1 D4_REGLE=regle_d4_l1.tsv` ; `vars_ro9a38.txt` redonne ro9a38 ; ro9a38 = ro9a37 + R3, X6, A2a, E2b ; `vars_ro9a37.txt` redonne ro9a37, `vars_ro9a36.txt` ro9a36,
`vars_ro9a35b.txt` ro9a35b). L'état vient d'une seule
constante de `hsfa_build.py`, `HA_ETAT`. Python + NumPy seulement : pas de MAME, pas de vasm ; la greffe
relance le traducteur par `sys.executable` (constructeur tout-en-un) et copie au lieu de lier si le système refuse
les liens symboliques.

### 11.2 Relevés

La greffe relit des relevés de l'atelier : journaux d'adresses lues par Upper sous MAME, cartes RAM d'Hyper et
d'Upper, analyses (routines de l'Arcade, homologues, variables A5, couverture). Ils ne contiennent que des adresses,
des numéros, des drapeaux et des étiquettes (vérifié objet par objet : aucun octet, aucun texte désassemblé). Ils sont
versionnés en 18 tableaux TSV (4,5 Mo au lieu de 75 Mo) : en-tête d'origine et de mesure, journaux réduits à leur
union par groupe en plages d'adresses, cartes RAM en plages, analyses en enregistrements. `releves_tsv.py verifier`
redonne des objets égaux aux relevés d'origine. Trois analyses se régénèrent aussi depuis l'ISO à l'octet
(`homologues`, `ram_statique_ro9`, `couv_k`) ; `inverse_ro5` se régénère mais diffère (profils faits avec un
traducteur plus ancien). Sans les journaux, la greffe change de 2,3 Mo ; sans les cartes RAM, la table A5 change.

### 11.3 Preuves (08/11, état ro9a35b ; copie `git archive` 847b17c + versement)

1. **Copie figée, entrées d'atelier** (`runA35`) : construction = `ro9a35b_fige` à l'octet (28/29 de MD5SUMS, seul
   `env.sh` : chemins). Depuis les relevés TSV : idem (`c_tsv2`).
2. **ROM d'arcade + table du rejeu** (`p_arc`, 5 jeux) : greffe = ro9a35b (MD5SUMS) ; zip **31/32 membres identiques**
   à ro9a35b, seul `hsfa_info.txt` diffère (provenance). Audit de la greffe : aucun fichier lu hors de la sortie, de la
   copie du dépôt et des relevés. Avec les relevés TSV du dépôt (`p_tsv`, défaut, `--jeux hyperarcade`, 359 s en tout) : greffe = ro9a35b (MD5SUMS),
   zip **identique à l'octet** à celui de `p_arc` (relevés d'origine). `hsfa_info.txt` ne diffère de ro9a35b que par la
   provenance (chemins et dates des sources ; md5 et tailles identiques).
3. **ISO seule, avec la table** (`p_iso_t`) : programme identique ; 25/32 membres ; diffèrent `sz3.13m` / `15m` /
   `17m` / `19m` (ROM reconstruite), `hsfa_gfx.bin`, `hsfa_tab.bin` (codes de tuiles) et `hsfa_info.txt`, comme Hyper (§5).
4. **ISO seule, sans la table** (`p_iso_s`) : module d'Hyper d'origine (voix de SFA3) ; en plus du point 3 : `sz3ud.04c`
   (12 o), `sz3.06c` (185 o), `hsfa_ext.bin` (113 o : voix « par pas » non appliquées) ; `hsfa_rejeu.bin` et
   `hsfa_rejeu_table.txt` absents. `sz3ud.03c` reste `650b1bec`.
5. **Autres jeux** : SFA3, Upper, Hyper et Upper MAX construits avec le versement (`p_arc`) et sans (`p_ref`, même
   copie du dépôt, mêmes entrées) : **4 zips identiques à l'octet**, empreintes identiques.
6. Durée : `p_ref` (4 jeux) 502 s, `p_arc` (5 jeux) 681 s, soit environ 3 min de plus ; ISO seule `upper,hyper,hyperarcade`
   575 s. Place : 1,9 Go contre 1,5 Go (+0,4 Go).

7. **Versement définitif** (`p_final`, relevés TSV par défaut, 5 jeux) : les 5 zips identiques à l'octet à ceux de
   `p_ref` / `p_arc` ; voie du joueur (`p_joueur`, ISO seule, aucune option) : zip identique à l'octet à `p_iso_s`.
8. **Cœur Linux du 10/11** (partie Arcade de Ryu, pilote de `hsfa_run`) : zip ISO seule + table : journal et musique
   identiques au zip ro9a35b livré sur 25 000 images ; captures toutes les 250 images : 46 / 56 identiques au pixel,
   les 10 autres diffèrent de 26 à 633 pixels, uniquement l'**ombre au sol** des persos (transparente avec la ROM
   d'arcade, opaque en voie ISO : cause et correctif au §11.5). Sans table : partie complète, voix de SFA3.

### 11.4 Limites

- Expérimental. Avec la ROM d'arcade et la table du rejeu, le zip est ro9a41, le zip livré le 13/11, hors
  `hsfa_info.txt` et la ROM son (sons PS2 du §218 ; `HSFA_SONS_PS2=0` : identique) (§11.11).
- Voie ISO seule : ombres au sol opaques au lieu de transparentes (Hyper seul aussi) : corrigé, §11.5.
- Windows : liens symboliques remplacés par des copies ou des jonctions (§215 ; voie Windows simulée sous Linux :
  zips identiques, §11.6) ; constructeur tout-en-un : modules embarqués suffisants (relevé des imports), non essayé.

### 11.5 Ombre au sol en voie ISO seule (`HSFA_OMBRE_CODES`, 11/11)

- **Symptôme** : avec l'ISO seule, l'ombre au sol des persos ZERO / ZERO 2 d'Hyper et d'Hyper + Arcade est opaque.
  Avec la ROM d'arcade, elle est transparente (noir à 75 %, patch `0011`). Il n'y a pas de trame : les tuiles d'ombre
  sont pleines (couleur 14) dans les deux ROM. Avec l'option, on voit simplement le sol au travers.
- **Cause** : le patch `0011` reconnaît une ombre à sa palette (0x14) et à son code global (`0284A`, `305DF-30613`,
  `50888-5088A`). Les trois tuiles d'ombre des persos ZERO (banc commun e545, locaux `$2F29-$2F2B`) sont absentes de
  la ROM de SFA3. Elles vont donc en ROM étendue, où leur code est leur **rang** d'apparition. La ROM reconstruite
  depuis l'ISO contient d'autres tuiles (retouches de l'Anthology, §5.3), donc il y a moins de tuiles absentes (Upper
  55 410 au lieu de 55 979, Hyper 67 330 au lieu de 67 906). Les ombres tombent alors en `50648-5064A` : même contenu,
  mais un code hors de la liste.
  Preuve au cœur : avec `HSFA_OMBRES=0`, la voie ISO égale la voie arcade au pixel ; seule la transparence les sépare.
- **Correctif** (`src/hsfa/hsfa_gfx.py`, `ombres_aux_codes_du_coeur`, Hyper / ro9 seulement) : les tuiles de e545
  `$2F29`, `$2F2A`, `$2F2B` (données du disque, contrôle : couleurs 14 et 15 seulement) sont placées aux codes
  `50888`, `50889`, `5088A`. Si un code est déjà occupé, les deux tuiles sont échangées, dans le contenu et dans toutes
  les tables. Si la ROM étendue est plus courte (cas de la voie ISO, fin en `50701`), elle est prolongée par des tuiles
  transparentes, et l'ancienne copie reste en place sans renvoi. Avec la ROM d'arcade, les tuiles sont déjà à ces
  codes et rien ne change. La règle ne copie aucune donnée d'arcade : les codes viennent du patch `0011` et les tuiles
  du disque. `HSFA_OMBRE_CODES=0` donne la sortie d'avant à l'octet.
- **Preuves** (11/11, `work/ombre_iso`, RAPPORT) :
  - interrupteur 0, 5 jeux en voie ISO : zips identiques membre à membre à ceux du 08/11, à `hsfa_info.txt` près
    (date) ; Upper MAX diffère par le commit `3ce06a0` seulement ;
  - interrupteur 1 : SFA3, Upper et Upper MAX inchangés. Hyper et Hyper + Arcade ne changent que dans `hsfa_gfx.bin`
    et `hsfa_tab.bin`. La voie arcade est inchangée (voir RAPPORT) ;
  - cœur 10/11, Hyper (5 affiches VERSUS) et Hyper + Arcade (3 persos), comparé à la voie ISO d'avant : avec
    `HSFA_OMBRES=0`, 0 pixel d'écart ; avec 1, seules les lignes d'ombre (y 195-221) changent, et la voie ISO égale
    alors la voie arcade.

### 11.6 Passage à ro9a36 (11/11, §217)

- **Écart ro9a35b → ro9a36** : la copie figée, matérialisée avec les chemins de l'atelier, est identique aux 200
  fichiers d'origine, aux correctifs de portabilité du §215 près. Seul `etape3/greffe3.py` change (diff de la session
  e46 : `DECOR_E0`, `CONT_SORTIE`, `CONT_CHIFFRE`, à 0 = ro9a35b) ; les 79 relevés lus sont inchangés.
- **Report** : le diff de l'atelier, appliqué sur la copie du dépôt (les correctifs Windows restent). Une nouvelle
  copie les aurait perdus. Le nouveau code lisait les banques par un chemin d'atelier écrit en dur : il passe par les
  marques `@HA_MAME_RO9@` / `@HA_MAME_RO5@`. Dossiers renommés `ro9a36/`, `releves_ro9a36/` ; recette
  `vars_ro9a36.txt` ; constante `HA_ETAT` de `hsfa_build.py`.
- **Preuves** (clone du dépôt + versement ; une construction à la fois) :
  1. greffe seule, depuis le code et les TSV du dépôt : = `ro9a36_fige` à l'octet (34/35 de MD5SUMS, seul `env.sh` :
     chemins) ; avec `vars_ro9a35b.txt` : = `ro9a35b_fige` à l'octet ;
  2. ROM d'arcade + table du rejeu, `--jeux hyperarcade`, `HSFA_OMBRE_CODES=0` (444 s, 1,3 Go) : `sz3ud.03c`
     `93e88fee` ; zip **31/32 membres identiques au zip livré** (CRC `31F7E170`), seul `hsfa_info.txt` diffère (date
     et chemins ; md5 et tailles identiques). Avec `HSFA_OMBRE_CODES=1` : les 3 zips identiques à l'octet ;
  3. ISO seule, aucune option (voie du joueur, 5 jeux, `--psp-iso`, 847 s, 1,9 Go) : règle d'ombre appliquée
     (`$50648` → `$50888`...) ; zip = voie arcade sauf les écarts connus (§11.3 point 4 et §11.5) : ROM graphique
     reconstruite, `hsfa_gfx.bin`, `hsfa_tab.bin`, `sz3ud.04c` 12 o, `sz3.06c` 185 o, `hsfa_ext.bin` 113 o, sans rejeu ;
  4. cœur Linux du 10/11 (partie Arcade de Ryu en ZERO 3) : voie 3 contre voie 2, 32 000 images, 36 manches jusqu'à la
     fin : **0 capture différente** (31 captures, et 56 jusqu'à l'image 14 000), journal de la partie et flux musicaux
     identiques ; une seule commande son diffère (image 24 354 : voix de SFA3 sans la table du rejeu, attendu) ;
  5. SFA3, Upper, Hyper et Upper MAX (voie 3) contre le dépôt sans le versement : **4 zips identiques à l'octet** ;
  6. Windows simulé (E/S texte cp1252 + CRLF, `HSFA_SANS_LIENS=1`, méthode du §215 ; voie 2) : 358 s, aucun lien
     symbolique dans la sortie, banques sources intactes (`f351.bin` réécrit seulement dans la construction) ; les 3
     zips (Upper, Hyper, Hyper + Arcade) **identiques à l'octet** à ceux de Linux.

### 11.7 Passage à ro9a37 : traducteur de la greffe v161 (12/11, §221)

- **Report** : `e47/untranspile3_v161` = `e42/untranspile3_v160` du dépôt + le diff v160 → v161 du traducteur (aucun
  rejet). Recette `vars_ro9a37.txt` = celle de ro9a36 avec `TRAD=@HA_G@/e47/untranspile3_v161`. Code de la greffe,
  paquet, décisions et relevés inchangés. Dossiers renommés `ro9a37/`, `releves_ro9a37/` ; `fige35.py` copie aussi
  le traducteur e47 ; `HA_ETAT = "ro9a37"`. `vars_ro9a36.txt` = recette de ro9a36 (traducteur v160, gardé dans `e42/`).
- **Atelier** : interrupteurs v161 à 0 = `ro9a36_fige` à l'octet ; ro9a37 : `sz3ud.03c` `627c98c4…`, zip CRC
  `51882820` ; garde-fous de construction à 0 (comparaisons sans forme 68K, aides non rendues, Bcc après appel).
- **Preuve** (clone du dépôt + versement, ROM d'arcade + table du rejeu, `HSFA_OMBRE_CODES=0`) : greffe seule (code et TSV du dépôt) = `ro9a37_fige` à l'octet (34/35 de MD5SUMS, seul `env.sh` : chemins) ; avec `HSFA_SONS_PS2=0` (423 s, 1,3 Go) : `sz3ud.03c` `627c98c4`, zip **31/32 membres identiques au zip livré** (CRC `51882820`), seul `hsfa_info.txt` diffère ; par défaut (sons PS2 du §218), en plus `hx3.01`, `hx3.02`, `hx3.14m` (le zip livré garde la ROM son hybride) ; Upper `ac053140`, Hyper `dbfd237d` (v161, inchangés).

### 11.8 Moving to ro9a38: four fixes from the review of the graft (12/11, §223)

- **Carry-over**: diff of the workshop code (`etape2/donnees2.py`, `etape3/force3.py`, `etape3/greffe3.py`) applied to the
  build copy; folders renamed `ro9a38/`, `releves_ro9a38/` (records unchanged); `HA_ETAT = "ro9a38"`. Recipe
  `vars_ro9a38.txt` = `vars_ro9a37.txt` + `R3_CREUX=1 R3_CIBLES=1 X6_FINS=1 A2A_VS=1 E2B_DEFI=1`. Translator and package
  unchanged. `X2_TABLES` (MAX ids) is in the code, off.
- **Workshop**: all switches at 0 = `ro9a37_fige` byte for byte; ro9a38: `sz3ud.03c` `2dfdb15c…`, zip CRC `AC7D9F00`;
  v161 build guards as in ro9a37.
- **Proof** (clone of the repository + hand-over, arcade ROM + replay table, `HSFA_OMBRE_CODES=0`, `HSFA_SONS_PS2=0`):
  graft alone (code and TSV of the repository) = `ro9a38_fige` byte for byte (34/35 of MD5SUMS, only `env.sh`: paths); full build (488 s, 1.3 GB): `sz3ud.03c` `2dfdb15c`, zip **31/32 members identical to the delivered zip** (CRC `AC7D9F00`), only `hsfa_info.txt` differs; Upper `ac053140`, Hyper `dbfd237d` (unchanged).

### 11.9 Moving to ro9a39: L1 of the MAX characters, invisible (12/11, §224)

- **Carry-over**: folder `ro9a38/` -> `ro9a39/` (workshop code `greffe_arcade/e49/code`: `etape3/greffe3.py` X2 v2 and
  `D4_REGLE`, new `etape3/x2_tables.tsv`, `decors/d4/regle_d4_l1.tsv`, `vars_ro9a39.txt`), `releves_ro9a38/` ->
  `releves_ro9a39/` (records unchanged); `HA_ETAT = "ro9a39"`. Recipe `vars_ro9a39.txt` = `vars_ro9a38.txt` +
  `X2_TABLES=1 D4_REGLE=regle_d4_l1.tsv`. Translator and package unchanged. New step `sons_ps2_hypermax` (MAX sound
  ROM + Hyper's PS2-only sounds at 0x2A000), only with `HSFA_ETAPES_PLUS=sons_ps2_hypermax`: no package uses it yet.
- **Workshop**: all switches at 0 = `ro9a38_fige` byte for byte; ro9a39: `sz3ud.03c` `2459b5a5…`, zip CRC `D31889B0`
  (against ro9a38: `sz3ud.03c`, `sz3ud.04c`, `sz3.10b`, `hsfa_ext.bin`, `hsfa_trous.bin`, `hsfa_info.txt`; sound ROM and
  graphics identical).
- **Proof**: graft alone (code and TSV of the repository) = `ro9a39_fige` byte for byte (34/35 of MD5SUMS, only `env.sh`); with the arcade ROM, the replay table, `HSFA_OMBRE_CODES=0` and `HSFA_SONS_PS2=0` (495 s, 1.3 GB): `sz3ud.03c` `2459b5a5`, zip **31/32 members identical to the delivered zip** (CRC `D31889B0`), only `hsfa_info.txt` differs; Upper `ac053140`, Hyper `dbfd237d` (unchanged).

### 11.10 Moving to ro9a40: colours and portraits of the versions, green band of the logo transition (13/11, §228)

- **Carry-over**: folder `ro9a39/` -> `ro9a40/` (code already carried over in place by §225, §226 and §227, switches at 0),
  `releves_ro9a39/` -> `releves_ro9a40/` (records unchanged); `HA_ETAT = "ro9a40"`. Recipe `vars_ro9a40.txt` =
  `vars_ro9a39.txt` + `PAL_VERSION=1 COUL_CPU_VERSION=1 PORT_VERSION=1 BARRE_LOGO_FACE=1`. Translator and package
  unchanged.
- **Workshop**: recipe `vars_ro9a39.txt` on the ro9a40 code = `ro9a39_fige` byte for byte (34/35 of MD5SUMS, only
  `env.sh`); ro9a40: `sz3ud.03c` `be88f3f9…`, zip CRC `68B5EE56` (against ro9a39: `sz3ud.03c`, `sz3ud.04c`, `sz3.10b`,
  `hsfa_ext.bin`, `hsfa_trous.bin`, `hsfa_info.txt`; sound ROM and graphics identical).
- **Proof**: graft alone (code and TSV of the repository) = `ro9a40_fige` byte for byte (it is the frozen copy); with the arcade ROM, the replay table, `HSFA_OMBRE_CODES=0` and `HSFA_SONS_PS2=0` (612 s, 1.3 GB): `sz3ud.03c` `be88f3f9`, zip **31/32 members identical to the delivered zip** (CRC `68B5EE56`), only `hsfa_info.txt` differs; Upper `ac053140`, Hyper `dbfd237d` (unchanged).

### 11.11 Moving to ro9a41: word pairs no longer relocated as code pointers (13/11, §230)

- **Carry-over**: folder `ro9a40/` -> `ro9a41/` (new switch `PAIRES_CODE` in `greffe/etape2/donnees2.py`, default 0, and
  its list `greffe/donnees/ptr_exclus_paires.txt`), `releves_ro9a40/` -> `releves_ro9a41/` (records unchanged);
  `HA_ETAT = "ro9a41"`. Recipe `vars_ro9a41.txt` = `vars_ro9a40.txt` + `PAIRES_CODE=1`. Translator and package unchanged.
- **Workshop**: recipe `vars_ro9a40.txt` on the ro9a41 code = `ro9a40_fige` byte for byte (34/35 of MD5SUMS, only
  `env.sh`); ro9a41: `sz3ud.03c` `be88f3f9…` (unchanged), `sz3ud.04c` `ae411424…`, zip CRC `C9107FC2` (against ro9a40:
  `sz3ud.04c`, `hsfa_ext.bin`, `hsfa_trous.bin` and `hsfa_info.txt` change; `sz3ud.03c`, `sz3.10b`, sound ROM and
  graphics identical).
- **Proof**: graft alone (code and TSV of the repository) = `ro9a41_fige` byte for byte (it is the frozen copy); with the arcade ROM, the replay table, `HSFA_OMBRE_CODES=0` and `HSFA_SONS_PS2=0` (423 s, 1.3 GB): `sz3ud.03c` `be88f3f9`, `sz3ud.04c` `ae411424`, zip **31/32 members identical to the delivered zip** (CRC `C9107FC2`), only `hsfa_info.txt` differs; Upper `ac053140`, Hyper `dbfd237d` (unchanged).
