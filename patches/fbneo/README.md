# Cœur libretro FBNeo « HSFA »

Patchs contre [libretro/FBNeo](https://github.com/libretro/FBNeo), commit `af5d3f3`.

- Fonctionnement du cœur : [docs/architecture/coeur-fbneo.md](../../docs/architecture/coeur-fbneo.md).
- Une fiche par patch (problème, solution, alternatives écartées, fichiers, comment le couper) :
  [docs/architecture/coeur-fbneo-patchs.md](../../docs/architecture/coeur-fbneo-patchs.md). La fiche porte le numéro
  de la colonne « # ».
- Archives de jeu et notices : [tools/fbneo-hsfa](../../tools/fbneo-hsfa/README.md).
- **Licence** : les cœurs construits avec ces patchs sont FinalBurn Neo et en suivent la licence, recopiée mot pour mot
  dans [LICENSE-FBNeo.txt](LICENSE-FBNeo.txt) (ni vente, ni dons ; sources des modifications = ces patchs). Notices
  de stb_vorbis (patch `0004`) et du QSound HLE BSD-3 (patch `0001`) : [NOTICE.md](../../NOTICE.md). À joindre à toute
  archive de cœur.

## Patchs, dans l'ordre d'application

| # | patch | contenu | pourquoi | sources |
|---|---|---|---|---|
| 1 | `fbneo-hsfa.patch` | pilotes `sfa3hsfa` / `sfa3uhsfa` ; `cps_hsfa.cpp` (blocs externes, plans, liste d'objets convertie, ROM graphique étendue, codes d'objet sur 20 bits, son hybride) ; `Makefile.hsfa` ; lanceur `hsfa/hsfa_run.c` | jouer les programmes retraduits sans MAME ni scripts Lua | §136 |
| 2 | `fbneo-hsfa-widescreen.patch` | variante 448 × 224 16:9 (512 × 224 depuis le patch 26) (`-DHSFA_WS`, `Makefile.hsfaws`, cœur « FinalBurn Neo HSFA Widescreen ») | le décor existe au-delà des 384 px | §139 |
| 3 | `fbneo-hsfa-ws-flux.patch` | lecteur de flux musique ADX (`hsfa_flux.h`, `Y_DATA.BIN`), DIP « PS2 music » | des musiques n'existent qu'en flux sur le disque PS2 | §142, [FLUX](../../docs/rapports/FLUX.md) |
| 4 | `hyper-HSFA-pilote-sfa3hhsfa-Hyper-Street-Fighter-Alpha-mod.patch` | pilote `sfa3hhsfa` (Hyper) ; base des blocs externes déduite de `hsfa_ext.bin` ; `hsfa_run` `PILOTE=hyper` | Hyper a ses blocs en `$940000` et sa musique en flux | §143, [FBNEO-HYPER](../../docs/rapports/FBNEO-HYPER.md) |
| 5 | `0001-HSFA-rejeu-QSound-des-sons-SFA1-SFA2-d-Hyper-donnees.patch` | 2ᵉ QSound qui rejoue les sons SFA1 / SFA2 ; flux et rejeu lus dans le zip du jeu | la ROM QSound de 16 Mo est pleine | §145, [REJEU-FBNEO](../../docs/rapports/REJEU-FBNEO.md) |
| 6 | `0002-HSFA-chargement-differe-emplacement-4.patch` | chargement différé de l'emplacement 4 (`HSFA_LAT4`) | sur PS2 l'ancien fichier reste affiché quelques images (portrait d'Upper) | §146, [PORTRAITS](../../docs/rapports/PORTRAITS.md) |
| 7 | `0003-HSFA-options-du-coeur.patch` | réglages de l'écran OPTION en DIP B-H, écrits au menu des modes | l'écran OPTION PS2 est du C natif, non traduit | §147, [OPTIONS](../../docs/rapports/OPTIONS.md) |
| 8 | `0004-HSFA-stb_vorbis.patch` | décodeur stb_vorbis 1.22 (domaine public / MIT), API mémoire ; `-DHSFA_FLUX_VORBIS` | zip d'Hyper environ 5 fois plus léger | §150, [PLAN-VORBIS](../../docs/rapports/PLAN-VORBIS.md) |
| 9 | `0005-HSFA-flux-musique-Ogg-Vorbis.patch` | flux Ogg Vorbis dans `hsfa_flux.h` (ADX et Ogg cohabitent, boucles, états inchangés) | idem, sans changer le jeu | §150, [PLAN-VORBIS](../../docs/rapports/PLAN-VORBIS.md) |
| 10 | `0006-HSFA-carte-musique.patch` | carte musique d'Hyper : 2ᵉ Z80 (pilotes SFA1 / SFA2 d'origine) et 3ᵉ QSound ; aiguillage carte → flux → Z80 principal | musiques ZERO / ZERO 2 par leurs pilotes d'origine plutôt qu'enregistrées | §151, [PLAN-PARTITIONS-HYPER](../../docs/rapports/PLAN-PARTITIONS-HYPER.md) |
| 11 | `0007-HSFA-roulette-touche-piece.patch` | roulette de la sélection d'Hyper sur la touche Pièce (Select) ; Start reste au jeu | sur PS2 la roulette vient de Select ; Start gênait les EX | §157, [ETATS-HYPER](../../docs/rapports/ETATS-HYPER.md) §1.1 |
| 11b | `0007b-HSFA-hsfa_run-options-du-coeur-HSFA_VARS.patch` | lanceur d'essai seulement : `HSFA_VARS`, `HSFA_VARS2` / `HSFA_VARS2_IMAGE` servent les options du cœur | essayer les options sans RetroArch ; morceau absent du patch 7 | [OPTIONS](../../docs/rapports/OPTIONS.md) §3.2 |
| 12 | `0008-HSFA-registres-des-plans-ro9a.patch` | registres `$804200-$804205` complétés (mot en une fois, mise à jour au changement), région graphique déduite de `hsfa_gfx.bin` (80 Mo pour `ro9a`), pilote d'essai `sfa3hahsfa`, `hsfa_run` `PILOTE=arcade` | `ro9a` change de banque de plans en jeu, au-delà de 64 Mo | [COEUR-BANQUES](../../docs/rapports/COEUR-BANQUES.md) §A |
| 13 | `0009-HSFA-prototype-trous-carte-68K.patch` | prototype : les 7 trous libres de la carte 68K (5,08 Mo) servis en ROM depuis le membre facultatif `hsfa_trous.bin` ; sans ce membre, rien ne change | ROM programme et blocs externes pleins | [COEUR-BANQUES](../../docs/rapports/COEUR-BANQUES.md) §B |
| 14 | `0010-HSFA-melange-des-objets-transparence.patch` | mélange des objets : registres `$804220-$80423F` (un mode par palette OBJ) et `$804240` (mode des objets marqués par le bit 12 du mot X de la liste brute) ; modes 0 opaque, 1 additif, 2 alpha 50 %, 3 alpha 75 %, 4 soustractif, 5 noir 75 % ; priorité bit 12 > palette > option > opaque ; états compatibles dans les deux sens | les effets MAX sont dessinés en additif sur PSP (décidé par objet, champ +0xAA), le CPS2 n'a pas de transparence | [TRANSPARENCE](../../docs/rapports/TRANSPARENCE.md), [par objet](../../docs/rapports/TRANSPARENCE-PAR-OBJET.md) |
| 15 | `0011-HSFA-option-ombres-transparentes-PSP.patch` | option « Transparent shadows (PSP) » (DIP A bit 7, activée par défaut ; `HSFA_OMBRES=0/1` pour les essais) : tuiles d'ombre (palette 0x14, codes `0284A`, `305DF-30613`, `50888-5088A`) en noir à 75 % | ombres translucides comme sur PSP ; la palette 0x14 sert aussi au décor, d'où la règle par code de tuile | [OMBRES](../../docs/rapports/TRANSPARENCE-OMBRES-JAUGES.md) |
| 16 | `0012-HSFA-16-9-format-remplir-la-hauteur.patch` | cœur 16:9 : option « Screen format (fill height) » (Off, 4:3, 3:2, 14:9, 16:10, 5:3, 16:9) ; largeur = format × 288 (pixels arcade : 384 px ↔ 4:3), paire, plafonnée à la largeur du jeu (448, 512 depuis le patch 26) ; rognage centré, géométrie libretro suivie | montrer sur un écran moins large que 16:9 la part du décor élargi qui y tient (forks « remplir la hauteur ») | [TRANSPARENCE](../../docs/rapports/TRANSPARENCE.md) §13 |
| 17 | `0013-HSFA-pilote-sfa3umhsfa-Upper-MAX.patch` | pilote `sfa3umhsfa` « Street Fighter Alpha 3 Upper MAX (HSFA) » : mêmes ROM, init et options que `sfa3uhsfa`, `hsfa_trous.bin` facultatif, sans parent ; paquet : entrée `upper_max` → `sfa3umhsfa.zip` | Upper et Upper + MAX côte à côte (zips, états, réglages séparés), comparaison à l'œil des régressions | décision du 2026-10-24 |
| 18 | `0014-HSFA-provocation-sur-Select-en-combat.patch` | option « Taunt on Select (in fight) » (DIP A bit 6, par défaut ; `HSFA_PROVOC`) : en combat (`$FF8000` = 2, `$FF8004` = 4), Pièce du joueur N ajoute le bit 15 aux écritures de `$378` (sans crédit) ; gestionnaire `$FF8400-$FF8BFF` installé pour tous les pilotes HSFA | le portage pose Start dans `$370` ET `$372` à la même image : le front `$378` n'existe jamais, la provocation par Start est impossible | décision du 2026-10-24 |
| 19 | `0015-HSFA-banque-commune-Upper-greffe-ro9a.patch` | clés `commun_upper` / `base_upper` du `config` (pilote `sfa3hahsfa`) : quand la base scroll1 (`$804200`) vaut celle des plans d'Upper, l'emplacement 0 prend la banque commune d'Upper (e351) ; sans les clés, rien ne change | les écrans d'Upper greffés dans Hyper (CONTINUE, GAME OVER, portraits des fins, « NEXT STAGE ») codent leurs objets pour e351, Hyper range e545 dans l'emplacement 0 | greffe ro9a11, 2026-10-28 |
| 20 | `0016-HSFA-roulette-sur-piece-Upper.patch` | pilotes `sfa3uhsfa` / `sfa3umhsfa` (mode 2 sans Hyper) : les écritures de `$FF84F3` / `$FF88F3` (drapeau de roulette d'Upper, recopie de Start par l'image 68K `$055404`) prennent la touche Pièce du joueur, sur la grille seulement (phases 2/2/4, état 0), comme `$D3` d'Hyper (patch 11) ; `HSFA_NOROUL=1` vaut aussi pour Upper ; Hyper et la greffe (`$D3`, déjà couverts) inchangés | Start tenu sur la grille lançait la roulette : Start + bouton sur Akuma / Balrog (Shin Akuma `$24`, EX Balrog `$25`, routine `$0570BE`) donnait un perso au hasard | étude « persos cachés d'Upper », décision du 2026-11-01 |
| 21 | `0017-HSFA-bases-marquees-ciel-du-CONTINUE-ro9a.patch` | clé `marque_upper` du `config` (masque hexa, ex. `8000` ; pilote `sfa3hahsfa`) : les bits de marquage des registres de plans `$804200-$804205` sont ignorés pour adresser les tuiles ; une base scroll1 marquée donne aussi à l'emplacement 0 la banque commune d'Upper (`commun_upper`), comme `base_upper` ; la greffe pose `$8300` (plans d'Hyper + banque d'Upper) ; sans la clé, rien ne change | à la citation du vaincu et au CONTINUE, le ciel du décor d'Hyper est sur scroll1 en codes d'Hyper, mais la base d'Upper (`$400`) sert de signal à 0015 pour les barres CONTINUE : taches, puis ciel noir (`CONT_S1_MASQUE`, ro9a16) | greffe ro9a18, 2026-11-02 |
| 22 | `0018-HSFA-option-sang-rouge-par-defaut.patch` | option du cœur « Blood (applies on load or restart) » (bit 2 du Dip A, tous les pilotes HSFA) : « Red (uncensored) » par défaut, « White (censored) » = comportement d'avant ; au chargement et à chaque remise à zéro (`HsfaReset`), l'immédiat du `MOVE.B #imm,$BA(A5)` du réglage REGULATION est posé à 0 (rouge) ou 1 (blanc) dans la ROM programme (`CpsRom` et copie des opcodes `CpsCode`) ; site cherché par signature (`1B7C 000x 00BA 6004 422D 00BA`), 1 attendu (2 pour `sfa3hahsfa`), sinon ROM intacte et message au journal ; `HSFA_SANG=0/1` pour les essais | la traduction garde `MOVE.B #1,$BA(A5) ; BRA.S ; CLR.B $BA(A5)` sans la condition du portage : REGULATION toujours à 1 (sang blanc, portrait de Zangief sans sang, objets de fin d'export) ; le jeu réécrit l'octet et recharge les palettes dans la même image, d'où la correction en ROM | étude `work/sang` (01/11), décision du 2026-11-01 |
| 23 | `0019-HSFA-option-saut-des-boucles-d-attente-68000.patch` | option du cœur « Skip idle loops (faster) » (bit 3 du Dip A, tous les pilotes HSFA ; **Off** dans ce patch, **On** par défaut depuis 0021b) : saut exact de la boucle d'attente d'image du 68000 (`MOVE.W $663888.L,D5 ; CMP.W D6,D5 ; BEQ.W`, `$000BF8` dans les 5 jeux) ; la page `$663800-$663BFF` est lue par un gestionnaire qui, quand ce MOVE lit une valeur égale à D6, retire du compte de cycles restant les tours entiers (30 cycles) qui précèdent le dernier de la tranche : même cycle, même PC, mêmes registres en fin de tranche ; site cherché par signature (`3A39 0066 3888 BA46 6700 FFF6`), 1 attendu, sinon rien et message au journal ; `HSFA_IDLE=0/1`, `HSFA_IDLE_STATS=1` pour les essais | lenteur sur Raspberry Pi 3 (Hyper, greffe) : la boucle fait 26 à 40 % des instructions et 37 % des cycles du 68000 ; −7 % de temps hôte à elle seule (x86) | étude `work/coeur_perf` (01/11) |
| 24 | `0020-HSFA-saut-de-la-boucle-d-attente-du-Z80-QSound.patch` | même option : saut exact de la boucle d'attente du minuteur du Z80 QSound (pilote son de la borne, `$01C7-$01D7` : `LD HL,$F001 … JR Z,$01C7`, signature `21 01 F0 7E B7 28 04 35 CD xx xx 21 02 F0 7E B7 28 EE`) ; `z80.cpp` reçoit un saut générique `Z80SetIdleLoop` (à la tête de boucle atteinte par son saut arrière, sans interruption prenable, mémoire lue nulle : ICount, R et compteur de T-states avancent des tours retirés) ; Z80 n° 0 seulement ; `HSFA_IDLE_Z80=0` garde le seul 68000 | le Z80 fait 70 % (SFA3) à 91 % (Hyper) de ses instructions dans cette boucle et pesait 23-28 % du temps hôte ; 0019+0020 : −23 à −25 % (x86) | étude `work/coeur_perf` (01/11) |
| 25 | `0021-HSFA-crochets-Z80-Musashi-et-FIR-QSound-plus-rapides.patch` | sans option, résultats identiques : chemins rapides en ligne des crochets de contention ZX Spectrum du Z80 (`store_rwinfo`, `run_script`, `eat_cycles`) quand la contention est coupée, rappel par instruction de Musashi non appelé quand c'est le rappel vide, filtre FIR du QSound (`qs_c.cpp` et `hsfa_qsound.h`) parcouru en deux segments linéaires (vectorisé NEON en armhf, vérifié à l'assembleur) | ~8 % du temps hôte dans des appels inutiles par accès / instruction ; FIR = boucle avec test de bouclage à chaque prise | étude `work/coeur_perf` (01/11) |
| 25b | `0021b-HSFA-option-saut-des-boucles-d-attente-active-par-defaut.patch` | « Skip idle loops (faster) » **On par défaut** : bit 3 posé dans l'octet par défaut du Dip A (`HsfaDIPList` 0xc1 → 0xc9 : SFA3, Upper, Upper MAX ; `HhsfaDIPList` 0xc2 → 0xca : Hyper, greffe) ; clé RetroArch inchangée (`fbneo-dipswitch-<pilote>-Skip_idle_loops_(faster)` = On / Off ; Off = comportement d'avant 0019) ; le message d'init n'annonce plus « inactif (option) » (les DIP n'y sont pas encore posés) : l'état réel est écrit au journal à la 1re image et à chaque changement | essai sur Raspberry Pi 3 (cœur Recalbox armhf, option On) : « ça tourne beaucoup mieux, pas de ralentissement » ; saut exact (5 jeux, 4:3 et 16:9 : images, son et journaux identiques On / Off / lot du 03/11) | décision de l'utilisateur du 2026-11-01, lot du 04/11 (`work/coeur_lot_1104`) |
| 25c | `0021c-libretro-Makefile-interrupteur-HSFA_NO_FLOAT_STORE.patch` | Makefile libretro : `HSFA_NO_FLOAT_STORE=1` retire `-ffloat-store` (ajouté pour tout gcc) ; sans la variable, rien ne change ; passé par `tools/recalbox/build.sh` et `tools/rocknix/build.sh` (constructions ARM) | `-ffloat-store` ne sert qu'aux FPU à précision étendue (x87) ; en VFP / NEON / AArch64 il ne change aucune valeur, seulement des rangements en mémoire (assembleur armhf comparé : mêmes opérations flottantes) | essai Recalbox (`work/coeur_recalbox_essai`, 01/11), lot du 04/11 |
| 26 | `0022-HSFA-16-9-512-px-bords-en-miroir.patch` | cœur 16:9 en **512 × 224** (rapport 512:288 = 16:9 exact aux pixels de la borne, `nCpsGlobalXOffset` = 64 ; `HSFA_WS_W` pour d'autres largeurs aux essais) ; « Screen format (fill height) » (patch 16) plafonné à 512 : Off = 16:9 = 512 px, 14:9 = 448 px (l'ancienne image) ; option « Widescreen edges » (`fbneo-hsfa-ws-edges`) : `mirror` (défaut jusqu'au patch 27) / `repeat` / `black` / `raw`. En combat (`$FF8000` = 2, `$FF8004` = 4, `$FF8008` = 6), avant les plans, passes de fond limitées aux bandes (largeur d'écran et décalage X des plans changés le temps de la passe, dessin en place coupé à la bande, sans objets) : lignes couvertes par une rangée de tuiles opaques sautées ; chaque plan prolongé en miroir par tuile (tuiles retournées de l'autre côté de son bord = 1re tuile vide depuis la fenêtre 4:3 vers l'extérieur), rangée par rangée, défilement par ligne de scroll2 compris ; plans à bord en silhouette (dernière tuile en partie transparente) dessinés d'abord, plans à bord coupé (dernière tuile opaque) par-dessus ; l'image du jeu par-dessus : le miroir n'apparaît que là où rien n'est dessiné. Colonnes périmées de l'anneau scroll1 (512 px recomposés autour de la caméra, suivi par comparaison des 64 colonnes à une copie) retirées des bandes (tous modes sauf `raw`). Hors combat : bandes noires (sauf `raw`). Rien n'est calculé pour les bandes rognées par le format (`nHsfaWsVisible`). La fenêtre 4:3 n'est jamais touchée ; cœur 4:3 inchangé (tout sous `HSFA_WS`) | l'ancien cœur 448 × 224 déclaré 16:9 étirait l'image de 512/448 (+14 %) ; au-delà de la vue 4:3, la plupart des décors s'arrêtent (butées de caméra, plans lents) : décision du 02/11, bords en miroir par défaut, noir hors combat | étude `work/ws512` (RAPPORT-WS512), version propre `work/coeur_0022/ws512_propre` (lot du 05/11) |
| 27 | `0023-HSFA-16-9-vue-calee-sur-le-decor-HUD-fixe.patch` | « Widescreen edges » : nouvelle valeur `stage` (**Stage-locked view**), **par défaut** ; `mirror` / `repeat` / `black` / `raw` gardés. Le jeu est inchangé (logique, caméra, mémoire, son). En combat, la scène (plans, persos, ombres, effets, objets de décor) n'est plus toujours centrée : marge montrée m, position x = m au milieu de la course, x = caméra près de la butée gauche (caméra < m), x = caméra − $180 + 2m près de la butée droite (scroll2 X, butées 0 / $180 dans tous les décors des 5 jeux) ; x suit la caméra (pas de saut sans saut de caméra) ; hors combat : centré. `nCpsGlobalXOffset` = x le temps du dessin, objets de la scène décalés de `nHsfaWsObjDx` (X sur 10 bits relu dans [−256, 768)). **HUD fixe au centre** (`HsfaWsHud`) : SFA3, codes $16000-$19FFF ; Upper, Upper MAX, Hyper, greffe : objets de l'emplacement 1 (table `plan2`, graphismes système), marqués par `HsfaEclater` (bit 12 du mot Y, libre après la conversion) ; les 5 jeux : palette $1D, palette $1E avec un code $02xxx / $3Exxx / $3Fxxx (textes et bandeaux K.O., PERFECT, ROUND n). Ce qui reste sans décor : miroir du patch 26 sur des bandes de largeur quelconque (`HSFA_WS_REPLI=black` aux essais). scroll1 (tous modes sauf `raw`) : une colonne fixe de l'anneau n'est montrée en bande que si le jeu l'a recomposée, si elle a déjà été vue dans la fenêtre 4:3, ou si elle est dans l'étendue parcourue sur toute la course (pente k de scroll1 mesurée, gardée par décor $FF8100 ; défilement automatique : sans restriction) | aux butées, le décor arcade s'arrête au bord 4:3 : 21 à 32 % des bandes étaient inventées par le miroir ; la vue calée montre le vrai décor (reste 5 à 26 % selon le jeu, plans lents) ; décision de l'utilisateur du 03/11 (idée tirée de cps2recomp, mode « Invisible walls » : aucune ligne de code reprise) ; bloc orange de colonnes jamais montrées par la borne (ciel lent de SFA3 $00) | `work/coeur_0023` (RAPPORT-0023) |
| 28 | `0024-HSFA-SFA3-tuiles-d-objets-en-miroir.patch` | SFA3 : tuiles d'objets que le portage PS2 range **en miroir**. Les tables d'objets `f<N>` (banques.py) relient une tuile locale du portage à la ROM graphique de la borne par **contenu exact** ; une tuile rangée retournée n'avait pas d'entrée et `HsfaEclater` la retirait. Traducteur v157 (`OBJ_MIROIR`, défaut 1, SFA3 seul) : l'entrée vaut la tuile de la ROM \| bit 29 (X) / bit 30 (Y) ; `HsfaEclater` masque le code sur 20 bits et XORe le drapeau dans l'attribut de la tuile 16×16 émise (bits 5-6). Tables sans ces bits (Upper, Upper MAX, Hyper, greffe, SFA3 d'avant v157 : 0 entrée sur 5 zips) : sortie identique au pixel | trous dans les objets de SFA3 : 1 084 tuiles non vides retirées sur 17 parties Arcade (ex. jambes de Dhalsim dans l'intro) ; décision de l'utilisateur du 03/11 | `work/ciel_ryu` (RAPPORT §2-§3), `work/sfa3_miroirs` |

**Numérotation.** « # » est le rang dans la chaîne ; les rapports disent « patch 8 » pour la ligne 8. Le patch 11b
a été extrait du commit `bca36de` de l'arbre de référence. Il garde le préfixe `0007b` pour ne pas renuméroter 0008
et 0009, déjà cités par les rapports. Les patchs 12 et 13 s'appliquent avec ou sans lui.

**Hors chaîne :**
- `fbneo-hsfa-decors.patch` : décors widescreen injectés (mode « bases de plans » pour SFA3), posé sur les patchs
  1-2 ; ne s'applique pas après le patch 6 sans adaptation de `cps_hsfa.cpp`
  ([INJECTION-FORK](../../docs/rapports/INJECTION-FORK.md)).
- `hsfa_run-sysdir.diff` : correctif du lanceur (dossier système copié dans un tampon), relevé pour ROCKNIX
  ([ROCKNIX](../../docs/rapports/ROCKNIX.md) §3). Sur la chaîne actuelle : `patch -p1 < hsfa_run-sysdir.diff`
  (décalage de 143 lignes) ; `git apply` le refuse.

## Construire

Chaîne vérifiée le 2026-10-24 depuis un arbre neuf au commit `af5d3f3` : les 17 patchs (16 plus le 11b)
s'appliquent sans erreur (un avertissement d'espace pour le patch 4), et l'arbre obtenu est identique, hors fichiers
générés, à l'arbre de référence `94c666a` (`git diff` vide). Les cœurs 4:3 et 16:9 se construisent.

```bash
git clone https://github.com/libretro/FBNeo.git && cd FBNeo && git checkout af5d3f3
P=<depot>/patches/fbneo
git apply $P/fbneo-hsfa.patch $P/fbneo-hsfa-widescreen.patch
for p in fbneo-hsfa-ws-flux.patch hyper-HSFA-pilote-sfa3hhsfa-Hyper-Street-Fighter-Alpha-mod.patch \
         0001-HSFA-rejeu-QSound-des-sons-SFA1-SFA2-d-Hyper-donnees.patch 0002-HSFA-chargement-differe-emplacement-4.patch \
         0003-HSFA-options-du-coeur.patch 0004-HSFA-stb_vorbis.patch 0005-HSFA-flux-musique-Ogg-Vorbis.patch \
         0006-HSFA-carte-musique.patch 0007-HSFA-roulette-touche-piece.patch \
         0007b-HSFA-hsfa_run-options-du-coeur-HSFA_VARS.patch 0008-HSFA-registres-des-plans-ro9a.patch \
         0009-HSFA-prototype-trous-carte-68K.patch 0010-HSFA-melange-des-objets-transparence.patch \
         0011-HSFA-option-ombres-transparentes-PSP.patch 0012-HSFA-16-9-format-remplir-la-hauteur.patch \
         0013-HSFA-pilote-sfa3umhsfa-Upper-MAX.patch \
         0014-HSFA-provocation-sur-Select-en-combat.patch \
         0015-HSFA-banque-commune-Upper-greffe-ro9a.patch \
         0016-HSFA-roulette-sur-piece-Upper.patch \
         0017-HSFA-bases-marquees-ciel-du-CONTINUE-ro9a.patch \
         0018-HSFA-option-sang-rouge-par-defaut.patch \
         0019-HSFA-option-saut-des-boucles-d-attente-68000.patch \
         0020-HSFA-saut-de-la-boucle-d-attente-du-Z80-QSound.patch \
         0021-HSFA-crochets-Z80-Musashi-et-FIR-QSound-plus-rapides.patch \
         0021b-HSFA-option-saut-des-boucles-d-attente-active-par-defaut.patch \
         0021c-libretro-Makefile-interrupteur-HSFA_NO_FLOAT_STORE.patch \
         0022-HSFA-16-9-512-px-bords-en-miroir.patch \
         0023-HSFA-16-9-vue-calee-sur-le-decor-HUD-fixe.patch \
         0024-HSFA-SFA3-tuiles-d-objets-en-miroir.patch; do
  git apply --exclude=gamelist.txt --exclude='src/dep/generated/*' $P/$p
done
cd src/burner/libretro
nice -n 19 make -j4 SUBSET=hsfa REGEN_HEADERS=1       # Linux x86_64 -> fbneo_hsfa_libretro.so (≈ 40 s)
nice -n 19 make SUBSET=hsfa clean
nice -n 19 make -j4 SUBSET=hsfaws REGEN_HEADERS=1     # 16:9 -> fbneo_hsfaws_libretro.so
```

- **Fichiers générés** (`gamelist.txt`, `src/dep/generated/*`) : seul le patch 4 en contient, faits sur un arbre
  déjà régénéré ; il faut les exclure. `REGEN_HEADERS=1` les refait, et c'est **obligatoire** : sans lui, la table
  des pilotes du `.so` ne connaît pas les pilotes ajoutés (`sfa3hahsfa` en dernier).
- **Avec `git am`** (historique propre) : `git apply` des patchs 1 à 3, `git apply --exclude=…` du patch 4, un
  commit, puis `git am` des patchs suivants (11b compris) sans exclusion. Vérifié le 2026-10-18 jusqu'au patch 13.
- **Android** (arm64-v8a, NDK r28c) : `ndk-build` ne régénère pas les en-têtes. Lancer d'abord
  `make SUBSET=hsfa generate-files` dans `src/burner/libretro`, puis
  `NDK=<ndk> FBNEO=<arbre> tools/android/build_android.sh <sortie>` (les deux cœurs).
- **ROCKNIX** (aarch64, glibc ≤ 2.38) : `FBNEO=<arbre> tools/rocknix/build.sh hsfa` (puis `hsfaws`).
- **Recalbox 10** (Raspberry Pi 3 = armhf 32 bits, Pi 4 / 5 = aarch64 ; glibc 2.39, cœurs liés à ≤ 2.27) : `FBNEO=<arbre> tools/recalbox/build.sh armhf|aarch64 hsfa|hsfaws` ; installation : [docs/guide/installation-recalbox.md](../../docs/guide/installation-recalbox.md).
- **Windows x64** (MinGW-w64, depuis Linux) : `tools/windows/build_win.sh <arbre> tous`.
- **Lanceur d'essai** : `gcc -O2 -Isrc/burner/libretro/libretro-common/include -o hsfa_run hsfa/hsfa_run.c -ldl -lm`.

### Contrôler le résultat

- Le md5 d'un cœur change d'une construction à l'autre : `libretro.o` contient le hash court du commit Git de l'arbre
  (`GITaf5d3f3` pour un arbre patché sans commit). Comparer donc les objets, ou le comportement.
- Comportement : `scripts/validation/nonreg_coeur.sh` (§162) avec `COEUR=<nouveau .so>` et `REF=<cœur de
  référence>` ; attendu `IDENTIQUE` pour SFA3, Upper et Hyper.
- **Depuis le patch 15**, les ombres sont transparentes par défaut : contre une référence plus ancienne, lancer avec
  `HSFA_OMBRES=0` (option coupée) ; sinon les captures diffèrent, et c'est voulu. Le patch 16 ne touche que le cœur
  16:9 (format Off par défaut) : le cœur 4:3 est identique à l'octet avec ou sans lui.
- Le 2026-10-24 (chaîne à 17 patchs, zips `livraison_v148`, cœur 4:3) :
  - `HSFA_OMBRES=0`, contre la référence `linux_hsfa_501aebd.so` (antérieure à 0010) : `IDENTIQUE` sur les trois jeux
    (30, 30 et 40 captures, journaux, rejeu, flux, WAV) ;
  - options par défaut, contre le cœur Linux de l'arbre de référence (construit le 2026-10-18 avec 0010-0011) :
    `IDENTIQUE` sur les trois jeux ;
  - options par défaut, contre `linux_hsfa_501aebd.so` : seules les captures diffèrent (journaux, rejeu, flux, WAV
    identiques).
  - le cœur 16:9 a été construit, mais pas passé en non-régression (vérifications du patch 16 :
    [TRANSPARENCE](../../docs/rapports/TRANSPARENCE.md) §13).
- Le 2026-10-18 (14 patchs) : 124 objets sur 126 identiques à l'octet à ceux de l'arbre de référence (les deux
  autres, `burn.o` et `libretro.o`, ne diffèrent que par la table des pilotes générée et le hash Git).
