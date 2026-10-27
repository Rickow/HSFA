# SAVOIR-MAX — passation de la session MAX (SFA3 MAX PSP → Upper / Hyper)

État au 2026-10-25. Ce fichier rassemble ce qui n'est écrit **nulle part ailleurs** ; pour le reste, il renvoie aux
notes existantes (liens relatifs au dépôt). Conventions de chemins :

| marque | chemin réel chez l'utilisateur |
|---|---|
| `<ws-max>` | dossier de travail de la session MAX (`…/sfa3max-psp-widescreen`), **hors dépôt** |
| `<hsfa>` | racine HSFA (contient `github/` = ce dépôt, `work/`, `tools/`, `venv/`) |
| `~/.cache/sfa3max` | racine de cache « non étirée » (référence md5 du 2026-10-17) |
| `~/.cache/sfa3max_v2_etire` | **racine v2** : celle que lit l'agent d'intégration depuis le lot 2b11 |

Adresses PSP : « VA » = adresse à base 0 de l'EBOOT EU (VA = décalage dans le fichier − 0x74 ; mémoire PSP réelle =
0x08804000 + VA ; RAM du segment 1 = 0x08AD8F30 + VA). Adresses Upper : PS2 (fichier `ro5_usa_prog68k.bin` = PS2 −
0x1F0000). Adresses arcade : `sfa3ud` (programme déchiffré).

---

## 1. La chaîne PSP → CPS2, étape par étape

Environnement commun : `source <hsfa>/env.sh ; source <hsfa>/env_max.sh` (exporte `SFA3MAX_EBOOT`, `SFA3MAX_ISO`,
`SFA3_ZIP`, `ANTHOLOGY_DIR`, `EE_STD`, `EE_HYPER`, `SFA3WS_DIR`, `SFA3MAX_CACHE`), Python = `<hsfa>/venv/bin/python`.
Les copies de travail des scripts sont dans `<ws-max>/work/re/` (chemins absolus) ; la copie publiée est
`max/outils/` (chemins relatifs), produite par `<ws-max>/work/re/publier_max.py [--appliquer]`. **Modifier d'abord la
copie de travail, puis publier**, ou modifier le dépôt et reporter à la main (c'est ce qui a été fait le 24-25/10 pour
`traduire.py`, `rosette_donnees.py`, `flammes_max.py`, `recul_max.py`, `frises_verticales_max.py`).

| # | étape | outil (dépôt) | entrée | sortie | validation |
|---|---|---|---|---|---|
| 1 | extraction des pac | `tools/max/plpac.py` | ISO EU (lecture seule) | `$SFA3MAX_CACHE/pac/plXX_e.pac` (43) ; textes / fins dans `~/.cache/sfa3max/data/textes/` | `tools/max/validate_cps2.py` |
| 2 | frames + banque CPS2 | `convert/convert_max.py` (`SFA3MAX_ETIRE`) | pac | `converti/plXX/bank.bin`, `frames.json`, `frames_XX.bin` | `convert/roundtrip_ryu.py`, `temoin_ryu.py` (§7) |
| 3 | palettes | `convert/palettes_max.py`, `palettes_ingrid_upper.py` | pac | `palettes_module.bin`, `palettes_cps2.bin` (+ `_upper` pour Ingrid) | Ryu 30/30 ([max-palettes.md](max-palettes.md)) |
| 4 | tables d'animation | `convert/tables_anim.py` (appelé par 2) | pac + EBOOT | `animations.json` | [max-tables-animation.md](max-tables-animation.md) |
| 5 | graphismes fork / Upper | `convert/gfx_fork.py`, `portraits_fork.py` | 2 | `fork/max_gfx.bin`, `max_portraits_gfx.bin`, `rapport*.txt` | codes $60055… (G0) |
| 6 | Rosette du code | `rosette_code/tout.py`, `evaluer.py`, `apprendre.py` | EBOOT + arcade | `api_arcade_psp.json`, `appris.json` | §4 |
| 7 | brouillons 68K | `rosette_code/brouillons.py` (`traduire.py`) | 6 | `brouillon_<perso>.s`, `moteur_max_auto.s`, `donnees_max.s`, `api_a_fournir.*` | « 0 ?? », `assembler.sh` 0 erreur |
| 8 | frames / anims 68K | `frames_max.py`, `anims_max.py`, `anims_fins_max.py`, `decor_fins_max.py` | 2, pac de fin | `frames_*.s`, `anims_*.s`, `fin_anims_*.s`, `decor_fin_*.s`, `symboles_*_max.s` | `assembler.sh` |
| 9 | données propres | `projectiles_max.py`, `tables_explicites.py`, `sons_pas_max.py`, `mouvements.py` | EBOOT | `donnees_*.s`, `sons_pas_max.s`, `tables_explicites_*.s` | `assembler.sh` |
| 10 | fins : scripts, acteurs, palettes | `convert/convertir_fin.py`, `script_fin.py`, `rosette_donnees.py acteurs_max`, `jeux_palettes_fin.py`, `rosette_code/acteurs_fins.py` | pac de fin + EBOOT | `converti/plXX/fin/*.s`, `jeux_palettes_cps2.bin`, `pose_generique_max.s` | planches PPSSPP (§7) |
| 11 | sons | `rosette_code/sons_pas_max.py` + `commandes_voix_max.s` (agent_voix_max d'HSFA) | EBOOT, se_mid | `sons_pas_max.s`, `VOIX_xx` dans `moteur_max_main.s` | à l'oreille au banc |
| 12 | habillage | `noms_max.py`, `bandeau_noms_max.py`, `frises_verticales_max.py`, `winner_noms_max.py`, `carte_noms_max.py`, `icones_max.py`, `hud_max.py`, `hud_noms_max.py`, `citations_max.py`, `bio_max.py`, `apercu_selection_max.py` | pac, ro5 | `converti/<nom>/…` (+ `source` → `.s`) | captures de l'agent |
| 13 | données de combat ajoutées le 24/10 | `flammes_max.py`, `recul_max.py`, `projections_max.py [natifs\|controle]` | pac, EBOOT, ro5 | `converti/flammes/`, `converti/recul/`, `rosette_code/projections*_max.s` | contrôles intégrés (§7) |

**Ordre de régénération imposé** (pièges §5) : `anims_max.py` réécrit `symboles_anims_max.s` → relancer ensuite
`anims_fins_max.py` puis `decor_fins_max.py`. `portraits_fork.py` doit tourner **après** les outils d'habillage (il
ajoute leurs tuiles et pose `code_global` dans leurs `.json`), puis `<outil> source` pour écrire les `.s`.

Racine v2 (étirée) : mêmes commandes avec `SFA3MAX_CACHE=~/.cache/sfa3max_v2_etire` (et
`SFA3MAX_PAC_DIR=~/.cache/sfa3max/pac` pour les outils qui lisent les pac, la v2 n'en a pas de copie). Les `.s` du
code sont recopiés dans `~/.cache/sfa3max_v2_etire/s/` (brouillons, `moteur_max_main.s`, `moteur_max_auto.s`,
frames, acteurs). L'agent d'intégration lit aussi **directement** `<ws-max>/work/re/rosette_code` (`SRC_DEF` de
`tools/integration-max/conversion/convertit_max.py`) : ne jamais y laisser un état cassé (§5, brouillons).

## 2. Où sont les choses

- **ISO** : EU ULES-00235 v1.01, `<ws-max>/work/iso/src/EU_RETAIL.iso`, md5 `5f58de7e83a0270bead43103f6c0136e`
  (l'US est décalé : ne pas l'utiliser). Copie 16:9 patchée pour PPSSPP : `<ws-max>/work/iso/out/EU_DECRYPTED_WS.iso`
  (md5 `8e8cbd12a6cc123469d4c70def23547b`, lue seulement).
- **EBOOT** : `<ws-max>/work/eboot/ULES00235_EBOOT.BIN` (déchiffré), md5 `4b2589b69977d9d9a5959b2c4a146b67`
  (= `PSP_GAME/SYSDIR/BOOT.BIN` du retail sans ses 344 octets de fin). C'est un ELF : .text à 0x74.
- **md5 de référence** de la racine non étirée : `<ws-max>/work/re/md5_reference.txt` (71 sorties, déterministes).
- **Ghidra** : projet `<ws-max>/work/ghidra_psp/SFA3MAX_PSP`, programme `ULES00235_EBOOT.elf`, image base 0,
  extension ghidra-allegrex v21.4 (installée dans `~/.config/ghidra/ghidra_12.1.3_PUBLIC/Extensions`), Ghidra et JDK
  de `<hsfa>/tools/`. En ligne de commande : `<hsfa>/venv/bin/python <ws-max>/work/re/ghidra_decomp.py 1d4c48 5fe1c`
  (décompile), `--xrefs 214d04` (qui référence), `--plage lo hi 'regex'` (décompile une plage et filtre les lignes).
  Adresses Ghidra = VA pour le code et les données statiques ; **RAM (segment 1) = VA + 0x2D4F30**
  (ex. état de fin 0x87FCB0 → 0xB54BE0). Copie publiée : `max/outils/ghidra/ghidra_decomp.py`.
- **PPSSPP sans fenêtre** : `~/ppsspp-fork/build-headless/PPSSPPHeadless --memstick=<scratch>/memstick
  --graphics=software --debugger-run=45678 --timeout-wall=3600 <ISO_WS>` ; scripts dans `<ws-max>/work/re/ppsspp/`
  (`README.md`) : `ppdbg.py` (client WebSocket : `r8/r16/r32`, `capture`, `cpu.breakpoint.add`…), `nav_arcade.py <perso>`
  (jusqu'à une partie Arcade avec le perso imposé par J1+0x152), `tournee_psp.py <dossier> [min] [période]` (joue
  jusqu'à la fin, captures), `super_bp.py` (points d'arrêt + relevé a0-a3/ra image par image). Joueurs : table
  0x213F88 → structures 0x092E3EA0 + 0x498·k (vie +0x70, perso +0x152). ⚠ `tournee_psp.py` finit par un GAME OVER puis
  reprend avec Ryu : repérer la fin dans les captures (fin d'Ingrid du 24/10 : captures 150-205 sur 365).
- **Dossiers de travail hors dépôt** : `<ws-max>/work/re/` (`rosette_code/`, `convert/`, `rosette_construction/`,
  `ppsspp/`, `sauvegardes/` de `assembler.sh`), arcade déchiffré `~/.cache/sfa3max/sfa3ud_donnees.bin`.
- **Variables propres à MAX** : `SFA3MAX_CACHE` (racine), `SFA3MAX_PAC_DIR`, `SFA3MAX_ETIRE` (liste de pl étirés,
  défaut `pl26,pl27,pl28` ; vide = aucun), `SFA3MAX_ETIRE_APERCU` (ID étirés de l'aperçu de sélection),
  `SFA3MAX_SORTIE_S` (dossier des `.s` de `frames_max.py`), `HSFA_PLANS`, `HSFA_WORK`, `ANTHOLOGY_DIR`.
- **Échanges** : `<hsfa>/work/echanges/MAX.md` (questions / réponses, md5 des livraisons).

## 3. Le moteur PSP : repères

Les fonctions déjà indexées sont dans `re/connaissances/max_psp.tsv` ; l'**annexe A** ajoute celles qui y manquent.
Ce qu'il faut savoir pour lire le code :

- **Objet de jeu** (taille 0x498 pour un joueur) : +4/+5/+6/+7 états, +0x12/+0x16 X/Y (mots, ±16.16 dans la zone
  « +2 »), +0x1C pas courant, +0x52 compteur, +0x54 n° d'anim, +0x5C adversaire (= 68K `$38`), +0x60/+0x64/+0x68/+0x6C
  vitesses / accélérations 16.16 (= `$40/$44/$48/$4C`), +0x70 vie, +0x77 type de réaction reçu (arcade `$57`), +0x84
  sol, +0x86 sens, +0xAA mélange, +0xAB étirement (copié en +0x57 du sprite), +0x124 table des sons par pas
  (gabarit + 0x90), +0x128 jeu de boîtes courant (12 o), +0x12C table « $C0 » (sons, octet 2), +0x151 n° de joueur,
  +0x152 perso, +0x19E variante de voix, +0x1A0 espace de travail (pointeurs vers les sections de l'entrée [6] du pac).
  Champs ↔ 68K : `max/outils/rosette_code/champs.py`, `appris.json`.
- **Gabarit par perso** (Eagle 0x2A3198, Maki 0x2A6268, Yun 0x2AD6DC, Ingrid 0x2B1EE0) : +0x30-0x3C pointeurs de
  données, +0x40-0x6C pointeurs de gestionnaires (états), +0x90 table des sons par pas.
- **Allocateur** : 0x1EEAC (alloc, = arcade $1C2C8) → FUN_0001EAEC remet à 0 +0x28…+0x38 (liens de la liste des
  effets), +0xAA, +0xA0-0xA4. Aucune fonction ne **retire** un objet de cette liste à sa libération (0x1F24C…).
- **Dessin** : FUN_0000D2A8 (cases de 32 texels) / FUN_0000CD84 (16) : si +0x57 du sprite ≠ 0, case dessinée sur
  0x26 / 0x13 px (×19/16) et ancre X ×12/10 ; FUN_001E10DC : mode de mélange selon +0x56 (0 = alpha, 1 = additif).
- **Pas d'animation** : 0x5D6EC / 0x5D724 posent l'anim, 0x5D75C charge le pas : jeu de boîtes = (*(+0x1A0) +0x10) +
  12 × u16 (pas + 8), rangé en +0x128 ; octet 2 → table +0x12C (4 o) → octet 2 = index de son → +0x124 → 0x78408.
- **Son** : 0x78408(obj, joueur, code) : code < $200 bruitage commun, $2nn = voix n du perso. Dégâts $201-$205
  (+ octet +0x19E, 0x59080…), K.O. $230 / $232 (0x62D4C). Pas d'appel « voix de victoire » : elle vient des sons des
  pas de la pose.
- **Recul** : FUN_0005FE1C (table 0x214D04, séquences 0x214C8C / 0x214EC4) ; **flammes** : FUN_00079A58 (index = octet
  +9 du jeu de boîtes, sans masque) ; **projections** : FUN_00069DCC (espace +0x24).
- **Fins** : état 0x87FCB0 (+0x110 anims d'acteurs = pas10 0x20001 indexés 0x20003 ; +0x114 boîtes 0x20005 ; +0x118
  images fixes = pas8 0x20002 indexés 0x20004 ; +0x11C palettes 0x4000019 ; +0x120 jeux de palettes) ; table maîtresse
  0x2B34B0 ; générateur d'acteurs 0x1DBEDC ; sous-types $4B 0x2B2358, $4F 0x2B2A00, $49 0x2B2158 ; jeux de palettes
  rejoués par 0x1DB62C / 0x1DC25C ; 0x1D4C48 donne à l'acteur « perso du joueur » l'emplacement de sprites du joueur.
- **Sélection / habillage** : fichiers `winXX_e.pac` (table de noms 0x1FF440 : 42 pointeurs ; 8 répliques de 0x80 o
  par perso, aucune par adversaire), visages du HUD `pit_e.pac`.

## 4. La Rosette du code

Principe, résultats et commandes : [`max/outils/rosette_code/README.md`](../outils/rosette_code/README.md) §1-5 et
[max-rosette-code.md](max-rosette-code.md). Ce qui n'y est pas :

- **Fiabilité** : l'API appariée (≈150 paires) est sûre pour le moteur commun ; les champs votés sont sûrs pour le
  JOUEUR, pas pour les objets fils (carte `PROJ`) ni les acteurs (carte `ACTEUR`). Toute correspondance douteuse se
  tranche dans Ghidra, pas par un nouveau vote.
- **Ré-entraîner** : `python tout.py` (≈30 min) → `python evaluer.py` → `python apprendre.py` (cumulatif : vérifier le
  diff d'`appris.json`, versionné) → `python brouillons.py` → `./assembler.sh`.
- **`brouillons.py` est un point fixe** : il relit `acces_psp.json(.ecritures)` et les `brouillon_*.s` existants.
  Toujours essayer une modification de `traduire.py` dans une **copie** de `rosette_code` (scratch), comparer les `.s`,
  puis seulement générer dans `<ws-max>/work/re/rosette_code`. Réparer : `.s` depuis `sauvegardes/s68k_*.tgz` +
  `acces_psp.json` d'une copie saine, puis relancer (incident du 24/10, 17h47-17h55).
- **Limites connues** : arguments de type autre qu'objet en a0 (aléa 0x1D368 : `A0_SANS_OBJET`), fonctions moteur sans
  équivalent (écrites à la main dans `moteur_max_main.s` / `gestionnaires_main.s`), tables de scripts passées par
  adresse (`tables_explicites.py`), deux tirages aléatoires émis avant leurs usages (`acteur_1d586c`).

## 5. Pièges (et règle pour chacun)

Ceux du tableau d'`AGENTS.md` (§ « Pièges de l'intégration MAX ») ne sont pas répétés. **À y ajouter** (proposition
pour la session principale ; je n'édite pas `AGENTS.md`) :

| piège | symptôme | règle |
|---|---|---|
| ordre « image » d'Upper (mots échangés) ≠ ordre logique 68K | octet +9 d'une fiche vu en +8, flammes « +$10 / +$11 » | dans l'image, octet logique i = octet i^1 ; les données recopiées du PSP (jeux de boîtes, ancres, séquences de recul) sont en **ordre image** = octets PSP tels quels ; ne jamais les rééchanger |
| `brouillons.py` point fixe | une génération ratée casse les suivantes | essai en copie, comparaison, sauvegardes (§4) |
| `anims_max.py` réécrit `symboles_anims_max.s` | `FIN_ANIM_` / `FIN118_` absents | relancer `anims_fins_max.py` puis `decor_fins_max.py` |
| constante homonyme dans `traduire.py` (`SANS_OBJET` = chaîne) | toutes les traductions échouent en silence | vérifier le nom avant d'ajouter une constante globale |
| vitesses `opA` des scripts de fin | dérive des scènes | `convertir_fin.py` met la vitesse opA à 0 |
| fond de la fenêtre de texte des fins = classe PSP $4F/04 anim $5D | rectangles magenta | converti en arcade $49/00 anim $5D à (192, 128) (`rosette_donnees.py`) |
| jeux de palettes des fins : 4 emplacements (OBJ, S1, S2, S3) rejoués **quand ils changent**, tous vers OBJ | couleurs de scène fausses | images de 32 palettes calculées par `jeux_palettes_fin.py` ; x9 = jeu a2 seul ; ne charger que OBJ 0-29 ($1E) : 30-31 sont réservées |
| acteurs « perso MAX lui-même » ($4B, +$1F = fin) | couleurs fausses | drapeau palette propre (bit 0 de +4) = palette de COMBAT du joueur (0x1D4C48) |
| frames de fin des persos MAX en **sous-palette 0** (attribut $20), combat en sous-palette 1 ($21) | portrait d'Ingrid vert / violet alors que le petit sprite est juste | la palette propre doit fournir tout le groupe du joueur (sous-palettes 0-3) et la scène ne doit pas écraser base + 0 |
| pose finale du générique $4E/00 : rang de liste = ID | pose de Ryu avec les tuiles de la fin MAX | +3 = ID (Yun : $2D et $3D) ; `pose_generique_max.s` aux rangs ID des listes $E / $F de $301FA2 |
| décor des fins : les classes $48/$49/$4A lisent **+$118 de la fin chargée** | images natives à la place des images MAX (soupçon) | n° voté sur les fins natives valable seulement si l'image arcade est la même ; sinon n° symbolique `ND<fin>_<n>` (règle préparée, non appliquée, §6) |
| étirement ×19/16 (+0x57) par OBJET | Eagle trop étroit ; Ingrid à moitié | voir Q1 (§6) : chez Ingrid, haut étiré et jambes non |
| tirs : boîtes dans la table **du tir** (+0x164), pas du perso | coups de tir sans effet | `tables_explicites.py` `BOITES_TIRS`, ordre image |
| octet $0D du pas = type de contre (>3 → 0x21DC10[n]) | contres inactifs (désactivés au lot 2b) | prolonger la table d'Upper + traduire 0x6CFA4 / 0x6D040 / 0x6D0C8 / 0x6D15C |
| répliques de victoire : 8 par gagnant ; chemin « par adversaire » de l'arcade ($92 = 0, une fois sur deux) | bulle vide | index borné à 0-7 pour les MAX |
| flammes : la PSP n'applique pas de masque | flamme mal placée pour un index ≥ 16 | 22 couples par perso MAX ; masque $1F seulement pour une victime MAX |
| voix d'Ingrid n° 40-51 = banque A commune de `se_mid` | voix absentes | importées dans la ROM QSound (`commandes_son_max.s`, `CMD_VOIX_29_A_095…`) |

## 6. État au 2026-10-25

**Fait et intégré** (lots 2b10-2b21) : code des 4 persos (brouillons, moteur), frames, animations, palettes,
étirement, fins (scripts, acteurs, décor, jeux de palettes, fenêtre de texte), sons par pas et voix, portraits, noms,
icônes, HUD, carte, WINNER, citations, frises 1P/2P (horizontales et colonnes), projections natifs × MAX, flammes
(22 couples), recul des types 28-32, liens d'effets à l'allocation, typage de a0 (super d'Ingrid), pose du générique.

**Livré, à vérifier à l'écran** : colonnes de sélection `frises_verticales_max.s` (6b10927), pose du générique
`pose_generique_max.s` + `acteurs_fin_26-29.s` (3554b83).

**Questions ouvertes** (`work/echanges/MAX.md`) :
- **Q1 (Ingrid, haut étiré ×19/16, jambes non)** : les frames d'Ingrid sont COMPOSITES (haut + jambes, fusionnées par
  la conversion : `tools/max/sprites.py --ingrid`, `convert/README.md` § Ingrid ; aperçu : corps 1026-1067 + jambes
  n+42). À établir dans PPSSPP : point d'arrêt sur FUN_0000D2A8 / FUN_0000CD84 pendant un combat d'Ingrid, relever
  +0x57 du sprite pour chaque calque. Puis convertir avec l'étirement sur le seul calque du haut, **avant** la fusion.
- **Q2 (rémanences d'Ingrid, jambes vertes)** : rémanences = classe $35 / 0, palette 0 comme J1 ; les frames de combat
  portent les sous-palettes 1 et 2 (2 = 28 objets sur 600 frames, vraisemblablement les jambes). Hypothèse : la
  sous-palette 2 n'est pas réglée pour la rémanence. À vérifier sur PSP : palette de chaque calque d'une rémanence.
- **Retours console** (note du 25/10 dans `MAX.md`) : Yun (intro suivie de celle d'Ingrid, QCB+P sans onde de choc,
  gros pied proche, demi-tour arrière + K) ; Ingrid (super 2×QCF+P qui doit enflammer, contres QCB+P/K).
- **Visages des fins** : vérifier la sous-palette 0 (§5) ; si des images natives restent à la place d'images MAX, appliquer la
  règle ND du décor (patch prêt mais non poussé : la reprendre dans `rosette_donnees.py`, branche « classes de décor
  lisent +$118 », puis régénérer `acteurs_fin_*.s` et étendre `decor_nouveaux_max.md`).

**Ensuite, dans l'ordre** : Q1 (mesure PPSSPP puis conversion) → Q2 → retours console Yun / Ingrid → visages des fins
→ pilote unique `construire_max.py` (une commande de l'ISO à la racine v2, md5 de référence v2) → contres (octet $0D)
→ voie B (Hyper : `anims_hyper_max.py`, `$2B8` 3 × 48).

## 7. Vérifier sans la session MAX

- **Racine non étirée** : régénérer, puis `cd ~/.cache/sfa3max && md5sum -c <(sed '/^#/d' <ws-max>/work/re/md5_reference.txt)`.
- **Témoin Ryu** : `convert/temoin_ryu.py` (Ryu passé par toute la chaîne, comparé au module d'Upper), `roundtrip_ryu.py`.
- **Code** : `cd <ws-max>/work/re/rosette_code && ./assembler.sh <scratch>` → « erreurs : 0 » ; `brouillons.py` → 0 « ?? ».
- **Contrôles intégrés** : `projections_max.py controle` (fiches natives = arcade) ; `recul_max.py` (types 0-27 et
  séquences 0-24 = Upper, écart A11 attendu) ; `flammes_max.py` (Ryu / Chun-Li / Sagat / Zangief identiques à
  0x74C358) ; `citations_max.py` (Ryu, Ken, Adon identiques à Upper).
- **Au pixel** : `max/outils/rosette_construction/` (frames et animations PSP ↔ Upper, 64 % identiques au pixel ; règles
  de construction dans son `README.md`).
- **Vérité terrain** : PPSSPP (`nav_arcade.py <perso>` puis `tournee_psp.py`), à comparer aux planches de l'agent
  d'intégration (`<hsfa>/work/agent_integration_max/essais/b*/`).

---

## Annexe A — lignes à ajouter à `re/connaissances/max_psp.tsv`

Même format que le fichier (colonnes : adresse, adresse_autres, genre, nom, rôle, taille_type, mises_en_garde, source,
confiance, score, outil). Source commune : cette note et `work/echanges/MAX.md`.

```tsv
0x0000CD84		fonction	dessin_sprite_cases16	Dessin d'un sprite à cases de 16 texels ; +0x57 du sprite ≠ 0 -> case sur 0x13 px (×19/16), ancre X ×12/10.	fonction		max/notes/SAVOIR-MAX.md §3	mesuré		ghidra_decomp.py
0x0000D2A8		fonction	dessin_sprite_cases32	Dessin d'un sprite à cases de 32 texels ; +0x57 ≠ 0 -> case sur 0x26 px (×19/16), ancre X ×12/10.	fonction	Ingrid : haut étiré, jambes non (Q1).	max/notes/SAVOIR-MAX.md §3	mesuré		ghidra_decomp.py
0x0001EAEC		fonction	allocateur_init_objet	Initialise tout objet alloué : remet à 0 +0x28..+0x38 (liens de la liste des effets), +0xAA, +0xA0-0xA4.	fonction	Aucune fonction ne délie un objet libéré : cette remise à 0 évite la boucle de 0x1C6D58.	max/notes/SAVOIR-MAX.md §3	mesuré		moteur_max_main.s psp_raz_alpha
0x00059080		fonction	voix_degats_aleatoire	Voix de dégâts : $201 ou $202 (+ octet +0x19E) au hasard.	fonction		max/notes/SAVOIR-MAX.md §3	mesuré		ghidra_decomp.py
0x0005FE1C	arcade:$02B5CC; upper:0x52DC8	fonction	recul_victime	Recul : T 0x214D04[+0x77×2 + côté] -> séquence (0x214C8C / 0x214EC4 selon +0x24C), pas s8 par image ajouté à +0x12.	fonction		max/outils/convert/recul_max.py	mesuré		recul_max.py
0x00062D4C		fonction	voix_ko	Voix de K.O. $230 ou $232 selon +0x19E.	fonction		max/notes/SAVOIR-MAX.md §3	mesuré		ghidra_decomp.py
0x00079A58	arcade:$080B28	fonction	flamme_position	Position d'une flamme sur la victime : couple n° (octet +9 du jeu de boîtes +0x128), SANS masque.	fonction	Upper masque & $F (arcade 0x80B3C) : les MAX vont jusqu'à 21.	max/outils/convert/flammes_max.py	mesuré		flammes_max.py
0x000784F8		fonction	voix_200_et_bruitage	Joue $200 puis le bruitage $2E (et $217 sous condition).	fonction		max/notes/SAVOIR-MAX.md §3	mesuré		ghidra_decomp.py
0x000CF1F4		fonction	appliquer_vitesses	Applique vitesses / accélérations 16.16 (+0x60-+0x6C) à la position de l'objet a0.	fonction	a0 peut être la victime (super d'Ingrid).	max/notes/SAVOIR-MAX.md §5	mesuré		moteur_max_auto.s
0x000CF644		fonction	test_sous_le_sol_decale	Retourne 1 si y + (octet 3 de la boîte du pas) + d < sol (+0x84).	fonction		max/notes/SAVOIR-MAX.md	mesuré		moteur_max_main.s
0x001C50B0		fonction	ingrid_super_qcb2_etat_0e	Super 2×QCB+P d'Ingrid, sous-état $0E : au bout du compteur, lance la victime (+0x5C) vers le haut (vitesses −2 / −0,5).	fonction	Appels sur la VICTIME (a0 = +0x5C).	work/echanges (b19)	mesuré		traduire.py 64f79e3
0x001C5228		fonction	ingrid_super_qcb2_etat_12	Sous-état $12 : déplace la victime et attend sa réception (cf5d8 sur la victime).	fonction	Appels sur la VICTIME.	work/echanges (b19)	mesuré		traduire.py 64f79e3
0x001D6390		fonction	acteur_4f_13	Acteur de fin $4F/13 : anim +0x74 prise dans +$118 de l'état de fin (0x1D807C).	fonction		max/notes/SAVOIR-MAX.md §3	mesuré		ghidra_decomp.py
0x001D807C		fonction	fin_anim_118	Pose sur l'acteur l'animation n de la table +$118 (images fixes) de l'état de fin.	fonction		max/notes/SAVOIR-MAX.md §3	mesuré		ghidra_decomp.py
0x001DB62C		fonction	fin_jeux_palettes_emplacements	Compare les 4 emplacements de jeux de palettes (+$7E..+$84) à leur cache (+$18..+$1E) et rejoue ceux qui changent.	fonction		max/outils/convert/jeux_palettes_fin.py	mesuré		jeux_palettes_fin.py
0x001DBEDC		fonction	fin_generateur_acteurs	Crée les acteurs d'un groupe : +6 -> +0xD, +$1D/+$1E -> +0x89/+0x8A, +$1F -> +0x49 (banque).	fonction		max/outils/convert/rosette_donnees.py	mesuré		rosette_donnees.py
0x001DC25C		fonction	fin_jouer_jeu_palettes	Joue un jeu de palettes (enregistrements 4 o, copiés si drapeaux & $7F == 0).	fonction		max/outils/convert/jeux_palettes_fin.py	mesuré		jeux_palettes_fin.py
0x001E10DC		fonction	mode_melange_sprite	Mode de mélange selon +0x56 du sprite (copié de +0xAA) : 0 alpha, 1 additif.	fonction		max/notes/SAVOIR-MAX.md §3	mesuré		ghidra_decomp.py
0x001FF440		table	noms_pac_victoire	42 pointeurs vers « winXX_e.pac » (répliques et images de victoire).	42 × u32		max/notes/SAVOIR-MAX.md §3	mesuré		
0x00214C8C	upper:0x9719C0	table	recul_sequences_a	30 pointeurs de séquences de recul (+0x24C == 0).	30 × u32	Séquences 0-24 = Upper sauf A11.	max/outils/convert/recul_max.py	mesuré		recul_max.py
0x00214D04	arcade:$02D0CC; upper:0x61B460	table	recul_types	Types de réaction -> n° de séquence (2 o par type, 33 types).	33 × 2 o	Upper : 28 types.	max/outils/convert/recul_max.py	mesuré		recul_max.py
0x00214EC4	upper:0x971CC0	table	recul_sequences_b	30 pointeurs de séquences de recul (+0x24C ≠ 0).	30 × u32		max/outils/convert/recul_max.py	mesuré		recul_max.py
0x002B2158		table	fin_sous_types_49	Gestionnaires des sous-types de la classe d'acteur $49.	u32[]		max/outils/convert/README.md § Acteurs	mesuré		acteurs_fins.py
0x002B2A00		table	fin_sous_types_4f	Gestionnaires des sous-types de la classe d'acteur $4F (26).	26 × u32		max/notes/SAVOIR-MAX.md §3	mesuré		acteurs_fins.py
```

## Annexe B — adresses Upper / arcade établies le 24-25/10 (pour l'index d'Upper)

- Upper 0x9625B8 / 0x9626F8 / 0x962838 / 0x962978 : colonnes de sélection (frames $0A, police ASCII | $80) 1P JP / 1P
  US / 2P JP / 2P US ; positions par longueur de motif (0x966058 « 1PRYU », 0x9660A8 7 lettres, 0x966104 6, 0x9661C8 8).
- Upper 0x9620B8 / 0x9621F8 / 0x962338 / 0x962478 : frises horizontales $0C 1P/2P JP/US (positions 0x965F50…).
- Arcade $301FA2 : listes de pas 8 o des acteurs $4A (rang = $BB(A5)+2) et $4E/00 (listes $E / $F selon $90(A5),
  rang = +3 = ID) ; gestionnaire $4E = $AACAC.
- Arcade $D0B2-$D0EA : choix de la réplique de victoire ($D174[$92] -> textes ; $D194[perdant] si $92 = 0 et $BF = 0).
- Arcade $2331E : `move.b $9(a3),$57(a1)` (type de réaction) ; $2B5CC recul ; $80B28 flammes ($DF692[ID]).
- Upper 0x48E2A0 (fichier) : répliques, 40 décalages par ID ; 0x614E00 : table par $92 (5 × textes US, 3 × dialogues).

## Complément du 2026-10-25 (Q3-Q5 de `work/echanges/MAX.md`)

- **Taille d'accès** : un champ lu sur un autre objet par un pointeur de l'objet courant prend la taille de l'accès
  PSP (`taille_lecture`), plus celle de la carte 68K (17b3221 ; symptôme : `cmpi.l #2,$4(a1)`, onde de choc de Yun).
- **Réarmement d'une touche** : arcade $22FB8 / PSP 0x71594 — fiche = $A0 + 32 × octet +9 du pas ; coup refusé si fiche
  +$0E (& $7F) == victime $25A[$5A de l'attaquant] (PSP +0x23A[+0x7A]). $5B (PSP +0x7B, « coup porté ») est remis à 0
  aux débuts de coups par $2AEBC (PSP 0x5F114).
- **Réactions** (fiche +$0D → victime $55, PSP +0x75) : PSP 0-36, arcade / Upper 0-33. Tables : anim arcade $2D5B2 =
  Upper 0x61B4A0 = PSP 0x214F3C (34 → 36, 35 → 23, 36 → 36) ; coup au sol arcade $23608 = PSP 0x21DC4C (en l'air
  0x21DD0C) ; gestionnaire arcade $28BF6 = PSP 0x2157C4 (34 = 18, 35 = 0x583E4, 36 = 0x584B4). Employées par Yun (34,
  36) et Ingrid (35 : fiche 38 de la riposte de ses contres). Brûlure : réactions 14 et 35 ($258 = 1, $26A = $7F).
  +$0C de la fiche = étourdissement (PSP 0x6E080), pas un élément.
- **Coup direct** (contres, saisies) : PSP 0x67144 → 0x672DC = arcade $2E7F2 ; chute ($2CA, PSP +0x2BA) si fiche +$12 ≠ 0.
- **Dessin** (relevé PPSSPP sur Ingrid) : objet → 0x84C8 (chaîne de sous-frames 12 o, +10 = suite) → 0xA150(…, 0) →
  D2A8 (cases 32) / CD84 (cases 16), étirés si +0x57 ; sprite attaché 0x968C (octet 6 du jeu de boîtes → espace +0x20 →
  banque commune 0x671AEC, dx non étiré) ; chemins sans étirement 0xA150(…, 1) → D7D0 / DBCC (0x8C08, 0x8CEC composite
  par table 0xADFE78[+0x94], 0x8E74, 0x9988) : effets et objets de types $2D-$30.
