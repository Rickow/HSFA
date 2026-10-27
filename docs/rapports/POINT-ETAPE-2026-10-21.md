# Point d'étape du 2026-10-21 : ce que toutes les parties prenantes doivent savoir

Passe sur tout le dépôt (`main` au commit `412456e` du 2026-10-18, branche `claude/zealous-darwin-4wgvrd`, branche
`son-hyper-partitions`, déjà fusionnée) et sur le dépôt `SFA3max-PSP-widescreen` (stable depuis le 2026-09-26).
Quatre lectures croisées :
- intégration MAX ;
- greffe Arcade (voie B) ;
- cœur, son, décors et construction ;
- audit « documenté mais absent du code ».

Les constats marqués **(vérifié)** ont été recontrôlés à la main ; les autres viennent des lectures, avec leurs
renvois.

But : dire ce qu'un chantier sait et que les autres ignorent, ce qui bloque l'ensemble, et les décisions à prendre.
Ce rapport ne corrige rien chez les autres : il signale. Les propriétaires gardent la main sur leurs documents.

## 0. En dix lignes

1. **Le code du dépôt est en retard sur le savoir.** Des correctifs décrits comme faits n'existent que dans les
   dossiers de travail :
   - `EXG_PILE_D`, `AIDE_ROXR`, `BITOP_DN` (traducteur) ;
   - les interrupteurs des étapes 4 à 6 de la greffe ;
   - les crochets `MAX=1` ;
   - le paquet ro9a ;
   - plusieurs options du cœur (§2.1).
2. **Les archives en circulation sont toutes antérieures à au moins un correctif connu.** Hyper du 2026-10-11 (avant
   `PILE_LUI` et le §171), Upper + MAX du 2026-10-18 (base v149, avant le §171). Le Killer Bee Assault de Cammy y
   rate, la cause est prouvée (§171).
3. **La validation complète ne tourne pas depuis le dépôt seul** : `valide_tout.sh` utilise `$S` sans le définir
   **(vérifié)**, et dépend de `work/agent_hyper_etats` et de `work/modules_son`.
4. **Un conflit de RAM latent n'est recensé nulle part** **(vérifié)** : `$FF7F00` porte à la fois la table de
   transparence MAX (Upper) et le drapeau « partie Arcade » de la greffe (Hyper). Les deux espaces sont distincts,
   donc `zones.py` ne le voit pas. Il deviendra réel quand MAX passera dans Hyper, ce que prévoit la voie B.
5. **Les numéros d'ID des persos MAX ne sont pas tranchés.** Hyper réserve `$26-$29`, alors qu'Upper utilise
   `$26`, `$27`, `$2D` et `$2E` (dans Upper, `$28` et `$29` sont des pseudo-ID). C'est à décider avant la
   transposition.
6. **L'oracle SFA3 est discutable.** Le banc compare à l'arcade 980904, que l'Anthology n'offre pas (980629 et 980727
   seulement), et la preuve du §96 n'oppose pas les bonnes révisions (recherche B §3). Les ROM japonaises sont
   nécessaires.
7. **Une matrice de 203 coups** (Hyper Z3 contre arcade) laisse 22 écarts à expliquer. C'est le premier test
   systématique des coups (D-SONDES §3).
8. **Les tableaux de bord sont en retard** :
   - `AGENTS.md` §5 parle des lots 2b4-2b9 et des « patchs 1-11 », alors que la chaîne en compte 15 plus le 11b ;
   - `INDEX-HANDOFF.md` s'arrête au §115 ;
   - `ETAT-DES-LIEUX.md` est un instantané du 2026-10-04.
9. **`zones.py --verifie` sort 30 conflits**, dont deux réglés dans `GREFFE-ETAPE4.md` mais pas reportés
   (`CONFLITS.md` n° 1 et 2).
10. **Sept décisions attendent l'utilisateur** (§3).

## 1. Où en sont les chantiers

| Chantier | Où | Dernier état daté | Prochaine étape écrite |
|---|---|---|---|
| Traducteur (SFA3, Upper, Hyper) | `src/hsfa`, §162-§163 | **v150 validée** (2026-10-17) : SFA3 `6230bba0`, Upper `36fc4f37`, Hyper `cb9b37b9` (inchangée depuis v149) | verser `EXG_PILE_D` / `AIDE_ROXR` / `BITOP_DN` (§171), reconstruire, valider |
| Persos MAX dans Upper (`MAX=1`) | `INTEGRATION-MAX-UPPER.md`, §164, §166, `max/` | lot **2b15** (vers le 2026-10-18) : Eagle, Maki, Yun, Ingrid jouables, 20 VERSUS et 4 Arcade sans exception, non-régression = `MAX=0` | fins (décors gris-vert, invités en mosaïque, règle 8k), Maki (sauts, chope), super d'Eagle bloquée en `$10/06`, yeux VS, RESULT |
| Données MAX (session MAX) | `max/notes`, `max/outils` | code, frames, animations, fins, HUD fournis ; variante Hyper de `$2B8` prête | `BOITES_A/B` et attaques sur 40 octets pour Hyper (`FORMAT-UPPER-HYPER.md:79-84`, `BLOC-HYPER.md:224`) |
| Greffe Arcade sur Hyper (voie B) | `GREFFE-*.md`, §165 | **étape 6** (`ro9a6_fige`) ; à l'étape 5 : 59 fins sur 85 combinaisons sélectionnables, durées à ±2,2 % ; CONTINUE à la bonne durée et au bon fond | persos 05, 15, 17, 19, 1B, 1C, 1D, 21, 22 (et 06 Z, 0F A, 11 Z2) ; chiffre et texte de CONTINUE ; lettres de GAME OVER ; décor du boss (attend le chantier des décors) |
| Cœur FBNeo | `patches/fbneo`, `docs/architecture/coeur-fbneo*.md` | chaîne de 15 patchs plus le 11b ; 0010 v3 et 0011 (transparence) le 2026-10-18, 8 cœurs construits | jauges à 50 % (décision de l'utilisateur), fiches 14-15, vérification de la chaîne avec 0010/0011 |
| Son d'Hyper | `SON-HYPER*.md`, `PLAN-*.md`, §149-§161 | Ogg, carte musique et voix corrigées (2026-10-16) ; 194 codes sur 216 entendus | essais locaux : Vorbis contre ADX, puis Vorbis par défaut ; carte musique, étapes 0 et 4 |
| Options | `OPTIONS*.md` | OPTION/EXIT validés (§148) ; BGM d'Hyper dans Upper greffée, non intégrée | intégrer après validation de MAX ; le patch « 0012 » BGM n'est pas dans la chaîne |
| Décors 16:9 et SFA2 | `DECORS-WS.md`, `DECOR-SFA2*.md` | export, réimport et injection faits (2026-10-10) | 17 décors SFA2, patch des décors hors chaîne, conflits SFA2 contre 16:9 (`CONFLITS.md` 5-8) |
| Réorganisation, étapes C et D | `ARCHI-Reorganisation-Donnees.md` | « presque finie, mise de côté » | aucun rapport C/D dans le dépôt (`work/agent_reorg_CD/ETAPES-CD.md` seulement) |
| Cœurs pour les plateformes | `ROCKNIX.md`, §153-§157 | ROCKNIX sous qemu ; Android construit, jamais lancé sur un appareil | vitesse sur RGB10X ; essai Android réel |
| Widescreen PSP (autre dépôt) | `SFA3max-PSP-widescreen` | v1.1 et patcheur d'ISO (2026-09-26) | rien d'ouvert |
| Recherche, bancs de coups (cette session) | `docs/rapports/recherche/`, §167-§171 | fiches A-D, tableau des coups, matrice, cause du Killer Bee Assault | voir §5 |

## 2. Ce qui bloque l'ensemble

### 2.1 Correctifs décrits mais absents du dépôt

Les rapports et l'index les décrivent comme faits, mais **aucune ligne de code** ne les porte dans le dépôt (audit
des 819 noms en capitales des documents, recherche dans `src/`, `scripts/`, `tools/`, `max/`, `patches/`, `legacy/`).

| Quoi | Cité dans | Effet tant que c'est absent |
|---|---|---|
| `EXG_PILE_D`, `AIDE_ROXR`, `BITOP_DN` (traducteur) **(vérifié)** | `sfa3_arcade.tsv:9184`, `ro3.tsv:843`, §171 | Killer Bee Assault de Cammy raté (SFA3, Upper, Hyper) ; 4 autres `EXG` perdus dans Hyper, 20 paires dans Upper. `ro3.tsv:843` dit à tort « reconnue par AIDE_ROXR (profils.py) » |
| aides `roxr` et `sbcd` dans `profils.py` | `ro3.tsv:843-844`, `ro9.tsv:169` | `profils.py` ne connaît que 4 aides. Doublons dans l'index : `ro3.tsv:526`/`:843` et `:527`/`:844` |
| `RELOGE_ANIMNAT` (étapes C/D) **(vérifié)** | `sfa3_arcade.tsv:10`, `:9163`, `champs.tsv:181` | ne pas confondre avec `RELOGE_NATIF` (`assemble.py:327`) |
| interrupteurs de la greffe, étapes 4-6 : `RELAIS_J`, `FENETRES`, `PTR_*`, `DEC_*`, `FIN_J*`, `PTR_BAS`, `FE_TABLE`, `PLANS_CONT`, `ANIM_GREFFE`… **(vérifié pour `RELAIS_J`, `PTR_BAS`)** | `GREFFE-ETAPE4..6.md`, §165 | le dépôt n'a que les outils des étapes 2-3. Copie du traducteur `untranspile3/` et diffs 05/06/07 hors dépôt |
| crochets `MAX=1` (`integre_max.py`, `agrandit_max.py`, crochets de `mame_test.py`) **(vérifié)** | `INTEGRATION-MAX-UPPER.md` | `prepare_max.py:86-87` importe `integre_max` depuis `untranspile/`, hors dépôt |
| entrées `upper_max` et `sfa3hahsfa` / `hsfa_trous.bin` de `paquet_fbneo.py` | `VOIX-MAX.md:245-247`, `COEUR-BANQUES.md:284` | le paquet du dépôt ne sait construire ni Upper + MAX ni ro9a |
| `HSFA_MELANGE`, `HSFA_G_STATS`, `HSFA_PAL_STATS`, `HSFA_ESSAI_BIT12`, `HSFA_OBJ_STATS` **(vérifié pour `HSFA_MELANGE`)** | `TRANSPARENCE*.md` | options d'essai citées sans patch |
| petits restes | `SYNC_SEED` (`ETAPE-A.md:91`), `HSFA_FLUX_ZERO12`, `FORCEOCT`, `HSFA_ARCADE`/`ANIMS`/`BANQUES` (`BUILD.md:140`), `OBJ_BASE` (le code dit `OBJBASE`) | à vérifier ou à retirer des documents |

**À faire** : chaque propriétaire verse ses diffs (ou les range dans `tools/<chantier>/` avec un README), puis on
reconstruit les trois jeux et on lance la validation complète une fois, pour tous.

### 2.2 Archives et cœurs en circulation

| Objet | Date / base | Correctifs manquants |
|---|---|---|
| `sfa3hhsfa.zip` (Hyper) | 2026-10-11 | `PILE_LUI` (v149), `VRAM_TABLE` (v150), §171 |
| `sfa3uhsfa.zip` (Upper + MAX) | 2026-10-18, v149 | §171 ; `VRAM_TABLE` à confirmer |
| zip ro9a `sfa3hahsfa` | construit sur `ro9a4_fige` | étapes 5 et 6 ; voix d'Hyper non vérifiées (`COEUR-BANQUES.md:63-70`) |
| référence de `nonreg_coeur.sh` | `linux_hsfa_501aebd.so`, zips `livraison_v148` | antérieure à 0010/0011 et à la v150 |
| cœurs ROCKNIX | trois jeux de md5 (`ROCKNIX.md:191`, `TRANSPARENCE.md:452`, paquet du §157 sans md5) | aucun registre ne dit lequel est livré |

**À faire** : un registre unique « livré » (archive, cœur, md5, base, date). Proposition : une table en tête de
`docs/guide/` ou `BUILD.md`.

### 2.3 Validation et construction

- **`scripts/validation/valide_tout.sh:9`** : `U=${HSFA_SRC:-$S/../../src/hsfa}` alors que `S` n'est défini nulle
  part **(vérifié)**. Même chose dans `nonreg.sh`. Sans `HSFA_SRC`, le script part de `/../../src/hsfa`.
- Le script lit `work/agent_hyper_etats/lua/tournee_hyper.lua` (ligne 24) alors que `tools/hyper-etats/tournee_hyper.lua`
  existe, et `work/modules_son` (ligne 12) **(vérifié)**.
- `hsfa_build.py` (construction depuis l'ISO) n'applique pas le module son corrigé que la validation utilise. Il ne
  construit pas l'archive d'Hyper (`construction-iso.md:116`). « Hyper identique au banc » (`BUILD.md:28`) date
  d'avant le §145.
- `tools/integration-max/upper/assembler.sh:7` : `S=${1:-<scratchpad>` sans accolade fermante **(vérifié)**,
  probablement cassé par l'anonymisation. L'affectation avale la suite jusqu'à la prochaine `}`.
- Chaîne de patchs : vérifiée « 14 patchs » depuis un arbre neuf, avec `git am` des patchs 5 à 13 **(vérifié)**.
  0010 et 0011 ne sont donc pas couverts par cette vérification. Fiches 14-15 manquantes dans
  `coeur-fbneo-patchs.md`.

### 2.4 Savoir qui ne vit que dans `work/`

Ces rapports sont cités comme sources par l'index ou les rapports, mais n'ont **aucun équivalent dans le dépôt**. Le
savoir n'y existe que sous forme de lignes TSV :

| Rapport hors dépôt | Citations | Ce qui n'est que là |
|---|---|---|
| `agent_integration_max/INTEGRATION-MAX.md`, `ETAT.md` | ~117 | tables MAX d'Upper (fins `T_60b220`, effets `T_60d070`, musique `T_613350`, grille `T_61bfb0`, portraits `T_674c00`) ; lots 2b10-2b15 (seulement dans les commentaires de `prepare_max.py`) |
| `re/rosette_code/tableau_api.md`, `api_a_fournir.md` | ~67 | API du moteur PSP |
| `agent_couverture/COUVERTURE-ARCADE.md` | 41 | variables arcade `$FF80xx`, crédits, démarrage, débogage |
| `agent_ro9/MISE-EN-ROUTE-ro9.md`, `BANQUES-ET-MODES-ro9.md` | 42 | RAM d'Hyper, bloc externe `$940000`, fichier 547, chargeur de banques (cité par `profils.py:43`) |
| `agent_reorg_CD/ETAPES-CD.md` | 28 | toutes les étapes C et D |
| `agent_defauts_banc/DEFAUTS-BANC.md`, `lua/banc_trace.lua` | 11 | les trois règles du §171, « fantômes » du super, ordre des joueurs (`$0277EE`), atterrissage de Ryusei Raku |
| `agent_pal_ro5/PALETTES-PLANS-ro5.md` | 11 | palettes perso et effets d'Upper |
| `greffe_arcade/ETAT.md`, `traces/tableau_f8.md` | — | « à lire en premier » ; le résultat chiffré de l'étape 6 |
| `banc_coups/BANC-COUPS.md`, `banc_coups.lua`, `frame_data.py` | 10 | banc MAME des coups (cité 4 fois comme outil) |
| `agent_alpha/ALPHA-PSP.md`, `gedump.py` | 9 | en partie résumé dans `TRANSPARENCE.md` |

**À faire** : verser au moins `ETAPES-CD.md`, `DEFAUTS-BANC.md`, `INTEGRATION-MAX.md` (ou leur résumé) et
`greffe_arcade/ETAT.md` dans `docs/rapports/`. Les outils cités par l'index sont à verser dans `tools/`.
`verifie.py` en signale 9 introuvables.

## 3. Décisions à prendre

| # | Décision | Qui | Éléments |
|---|---|---|---|
| D1 **(décidé le 2026-10-21, `re/CONFLITS.md`)** | IDs des persos MAX dans Hyper : `$26-$29` (réservés) ou les numéros d'Upper (`$2D`/`$2E`) | utilisateur, sessions MAX et greffe | `allocations.tsv:210-214`, `BLOC-HYPER.md:197-200`, `FORMAT-UPPER-HYPER.md:77-79` |
| D2 **(décidé le 2026-10-21, `re/CONFLITS.md`)** | `$FF7F00` : déplacer la table de transparence MAX ou le drapeau de la greffe | sessions MAX et greffe | `allocations.tsv:146`, `:347` ; à ajouter à `CONFLITS.md` |
| D3 **(décidé le 2026-10-21, `re/CONFLITS.md`)** | `$3A0000-$3BFFFF` dans ro9a : animations natives d'Upper (greffe) contre code MAX | sessions MAX et greffe | `allocations.tsv:42` |
| D4 **(décidé le 2026-10-24 : règle 2, le décor suit le joueur 2, son perso et sa version, SFA1 compris, sans hasard ; GREFFE-ETAPE4 §9)** | Choix du décor de l'Arcade greffée : hasard SFA3/SFA2 (SFA1 écarté), ou décor selon la version de J2 (SFA1 compris) | utilisateur | §143 (`HANDOFF.md:4574`) contre `GREFFE-ETAPE4.md:264-276` |
| D5 **(2026-10-24 : abandonné ; la PSP ne teinte pas les jauges, elle remplit les barres d'un dégradé ; barres jaunes de l'arcade gardées)** | Jauges à 50 % (transparence) | utilisateur | `TRANSPARENCE-OMBRES-JAUGES.md:72-76` |
| D6 **(décidé le 2026-10-24 : oui ; `paquet_fbneo.py` vaut `ogg` par défaut)** | Vorbis par défaut | utilisateur, après l'essai local | `PLAN-VORBIS.md:16-17` |
| D7 **(2026-10-24 : oracle 980727 construit, module `refjp` du banc ; la traduction mêle 980727 et 980904, sfa3ud reste l'oracle par défaut ; BANC-COUPS.md §8)** | Oracle de SFA3 : rester sur 980904 ou passer à la révision par défaut de l'Anthology (980727) | utilisateur | recherche B §3 ; il faut les ROM japonaises |

## 4. Par chantier : ce que les autres doivent savoir

### 4.1 Persos MAX (Upper)

- **Ce qu'ils attendent des autres** :
  - les règles du §171 dans le traducteur (Upper + MAX est à reconstruire après) ;
  - les patchs 0010/0011 dans tous les cœurs ;
  - une entrée `upper_max` dans `paquet_fbneo.py`.
- **Ce que les autres doivent savoir** :
  - `0x623E50` (table de Bison par adversaire) est lue dans sa copie étendue 3 × 48 de `hsfa_ext.bin`, alors que
    `tables_par_id.json:291-295` la classe `simple` (D-SONDES §2.2) ;
  - le Skull Diver rate Sakura sans MAX aussi : ce n'est pas une régression MAX, ni la famille du §171 (D-SONDES §4.5) ;
  - le bloc d'Eagle est dit libre en `$D40000` d'un côté, et en `$D40000+$40000·k` ailleurs (`CONV-MAX.md:407`, §144).
- **Questions sans réponse écrite** (session MAX) :
  - octet `$0D` des pas (`$0B-$0E` ramenés à 0) ;
  - intros croisées ;
  - prologue Arcade ;
  - `SONS_COMMUNS` `$06` et `$2E` (écoute de l'utilisateur).
- `INTEGRATION-MAX-UPPER.md` s'arrête au lot 2b9 ; son tableau d'état (`:13-14`, `:492`) contredit ses §8.9-8.13.

### 4.2 Greffe Arcade (Hyper)

- **Ce qu'elle attend des autres** :
  - patch 0009 (trous de la carte) encore au stade de prototype ;
  - une banque commutée (`$804210`), seule solution pour faire tenir les décors (marge ≈ 28 Ko) ;
  - le chantier des décors pour la scène 1 des fins ;
  - un rebase sur le traducteur après le §171.
- **Défauts du traducteur contournés dans sa copie mais pas corrigés dans `src/hsfa`** : test perdu des prologues
  `sq`, adresses « formées par décalage » (`GREFFE-ETAPE3.md:285-286`).
- **Divergences de chiffres** sur les variables A5 relogées (36 ou 41 ; `$FF43BA` ou `$FF43BE`, jusqu'à `$FF4C8F`,
  `$FF4CA2` ou `$FF7FFF`) : à unifier.
- **À mettre à jour** :
  - conflits n° 1 et 2 réglés (`GREFFE-ETAPE4.md:240-248`), seules 2 des 5 lignes proposées ont été versées ;
  - « 64 Mo à étendre » est dépassé par le patch 12 ;
  - persos 1A, 1E, 1F, 20 : réparés ou non ?
  - `tools/greffe-arcade` n'a pas de README.

### 4.3 Cœur, son, décors, construction

- La BGM d'Upper (« patch 0012 » de `OPTIONS-HYPER-UPPER.md:203`) n'est pas dans la chaîne. Son diff est dans
  `tools/options/hyper-upper/`. « Patch 12 » désigne déjà le rang des plans ro9a (fichier `0008`) : à renuméroter.
- Les noms de patchs ont changé, mais les rapports n'ont pas suivi : `TRANSPARENCE.md:12,110,316`,
  `COEUR-BANQUES.md:40,167,279-280`, `FBNEO-HYPER.md:62,221`, `PLAN-VORBIS.md:143`. Le journal dit « patch 10 » tantôt
  pour le rang, tantôt pour le préfixe de fichier.
- `ETAPE-B.md:8` et le commentaire `assemble.py:181` disent « tous à 0 par défaut », alors que le code les met à 1
  (`assemble.py:183`).
- `SON-HYPER-ROM.md:392-401` est périmé : il dit encore « Hyper n'existe pas dans FBNeo ».
- Liens morts : `TRANSPARENCE.md:411` (`ETUDE-OMBRES-JAUGES.md`), `OPTIONS.md:217` (`construit_coeurs.sh`).
- « v150 » désigne deux choses : la validation de `VRAM_TABLE` (§163) et les règles d'`agent_defauts_banc`. Les
  secondes sont à renommer quand elles seront versées.

### 4.4 Index `re/`

- `verifie.py` : 0 erreur, 24 avertissements :
  - 14 doublons d'adresse ;
  - 9 outils introuvables ;
  - 1 renvoi aux conflits.
- `zones.py --verifie` : 30 conflits, dont les n° 1 et 2 déjà réglés, et la table MAX `$FF7F00` classée en conflit
  avec la plage du traducteur, alors que `CONFLITS.md:28` la juge sans conflit.
- 125 lignes d'`allocations.tsv` citent `<workspace>/work`, dont `:348-352`, qui renvoient à
  `work/.../GREFFE-ETAPE4.md`, désormais dans `docs/rapports/`.

## 5. Apports de cette session (recherche et bancs de coups)

| Apport | Où | Ce que les autres doivent en retenir |
|---|---|---|
| Livre et recherche documentaire relus pour le projet | `docs/rapports/recherche/` A, B, C, §168 | révisions par jeu, S-ISM SHADALOO, EX `$58`/`$59` probablement défauts PS2, différences régionales, projets cousins (Zer0-NexuS : voix de Cammy ALPHA), voie Fightcade, 12 tests prioritaires |
| Tableau des coups (guide BradyGames, 90 coquilles corrigées) | `tools/guide-coups/`, §167 | tableau hors dépôt (texte protégé), à demander à l'utilisateur |
| Banc des coups dans le cœur FBNeo | `tools/sondes-recherche/banc_coups.py`, §169 | un geste contre une liste d'adversaires sur Upper, Hyper ou l'arcade, sans MAME. Pièges : ISM par défaut, Start J2 avant la grille, début de manche par paire dans Hyper, son vers `/dev/null` |
| Matrice des coups Hyper Z3 contre arcade | `banc_matrice.py`, D-SONDES §3, §170 | 203 coups, 22 écarts restants (Dan Hissho Burai Ken, Honda Fuji Oroshi, Sagat Tiger Genocide, supers de Balrog, nombres de coups). Réserve 980904 contre 980727 |
| Cause du Killer Bee Assault | D-SONDES §4, §171 | prouvée au banc. Concerne le traducteur, MAX (reconstruction) et la greffe (rebase) |
| Outils sans MAME | `sonde_pc_fbneo.diff`, `dechiffre_cps2.c`, `desas68.py`, `paires_exg.py`, `rustine_angle.py` | trouver le PC d'un écart dans le cœur, lire le programme déchiffré de l'arcade, chercher les `EXG` perdus |
| Sondes Hyper | D-SONDES §1-2 | Mazi = 1 manche ; S-ISM rose = distribution de *SF2'* ; Head Press juste contre MAX |

Hors dépôt, mais disponible : idée d'un mode de difficulté nourri des replays Fightcade (format FBNeo `.fr` =
sauvegarde d'état plus entrées par image ; extraction des combos par le banc). Rien n'est commencé.

## 6. Ordre de marche proposé

1. **Remettre le code au niveau du savoir** :
   - verser les règles du §171, les aides `roxr`/`sbcd`, les outils et interrupteurs de la greffe 4-6, les crochets
     `MAX=1` et le paquet ro9a ;
   - réparer `valide_tout.sh` (`$S`) et `assembler.sh`.
2. **Une reconstruction et une validation complètes pour tous** (SFA3, Upper, Upper + MAX, Hyper, ro9a), puis :
   - le registre « livré » (§2.2) ;
   - de nouvelles références de non-régression du cœur ;
   - les vérifications à refaire : `paires_exg.py` à 0, Killer Bee Assault = 60.
3. **Appliquer D1 à D3**, décidées le 2026-10-21 (`re/CONFLITS.md`), avant toute transposition de MAX dans Hyper. Mettre
   `CONFLITS.md` à jour.
4. **Verser les rapports qui ne vivent que dans `work/`** (§2.4), puis rafraîchir `AGENTS.md` §5, `INDEX-HANDOFF.md`
   et `ETAT-DES-LIEUX.md`.
5. **Essais de l'utilisateur** : Vorbis, carte musique, Android réel, RGB10X ; décisions D4 à D7.
6. **Ensuite seulement**, reprendre les écarts de la matrice et les persos restants de la greffe.
