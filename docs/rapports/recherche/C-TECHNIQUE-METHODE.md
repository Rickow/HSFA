# C — Ce que la recherche apporte au projet HSFA, et une méthode pour une version 1.0 solide

> Rédigé le 2026-10-20 à partir de la recherche documentaire (`research_notes/Histoire de Street Fighter Alpha/`,
> les fichiers `_verif` priment) et de l'état du dépôt `SFA-Anthology-PS2-mods` (README.fr, CHANGELOG,
> ETAT-DES-LIEUX, HANDOFF §140-§161 et §167, SESSION-CLOUD-2026-10-16, `docs/methodes/`, `docs/architecture/`,
> `docs/reference/sfz2a-dash-cps2.md`).
>
> **Légende de fiabilité.** **[lu]** : source primaire ouverte et lue (code MAME/FBNeo/HBMAME, README, notes de patch,
> interview). **[wiki]** : Wikipédia, recoupée ou non sourcée (précisé). **[interne]** : mesure du projet HSFA.
> **[inférence]** : déduction de ce document, à vérifier. Rien ici ne décrit comment contourner une protection : on cite
> seulement ce que MAME déclare publiquement.

---

## 0. L'essentiel en dix points

1. **HSFA dépasse la CPS-2 réelle sur tous les axes** : graphismes (32 Mo réels, 128 Mo au fork, 64 Mo au cœur),
   QSound (8 Mo réels pour *Alpha 3*, 16 Mo pour la ROM hybride, plus un 2ᵉ et un 3ᵉ QSound), programme (4 Mo plus
   des blocs externes), musique en flux (201 Mo). Le produit est une **« CPS-2 étendue émulée »**. Il faut le dire
   ainsi, comme strygo le fait pour ses sets « 8 Mo » (« ne tournent que sur HBMAME et MiSTer »).
2. **Il existe un précédent officiel de matériel CPS-2 fictif accepté en amont** : la « CPS2 Turbo » de *SFZ3 Mix*
   (`Cps2TurboInit` dans FBNeo, `cps2t.cpp` dans HBMAME). C'est la voie la plus réaliste pour faire entrer les pilotes
   HSFA dans FBNeo, puis peut-être dans Fightcade.
3. **QSound** : MAME émule la puce en **LLE** (programme du DSP16A, depuis 0.196) ; FBNeo emploie la **HLE de
   superctr**, « fondée sur le code DSP désassemblé » (2018), et non une émulation « simplifiée » comme le dit
   `coeur-fbneo.md`. Les tests son doivent donc être **exacts au bit dans une même implémentation**, et **par
   tolérance** (corrélation, niveau) entre le fork (LLE) et le cœur (HLE).
4. **Les sets de fans du même mois** (Zer0-NexuS `sfz2al20`, strygo `sfa2g`/`sfz2d`…) montrent la forme attendue
   d'une intégration : un clone déclaré dans `cps2mis.cpp` d'HBMAME et `d_cps2.cpp` de FBNeo, avec ROM listées par CRC
   et des régions agrandies (QSound 8 Mo). Deux projets voisins : un contact est utile (voix de Cammy ALPHA,
   déclaration des sets étendus).
5. **Les bancs communautaires sont réutilisables** : `sfa3_support` (0xZERO3) lit la RAM et les boîtes de SFA3 sur
   l'arcade **et sur la PS2 (PCSX2-rr)**, et même la version GBA d'Upper (Eagle, Maki, Yun). HSFA reproduit la vue
   mémoire de la PS2 : ce script peut devenir un afficheur de boîtes pour HSFA, et un **oracle à trois voies** (arcade,
   PS2, HSFA).
6. **CFC2 (2025) est un oracle partiel de MAX dans Upper** : Capcom y a ajouté Eagle, Maki, Yun et Ingrid, puis
   corrigé des coups de Bison et de R. Mika qui ne touchaient pas ces quatre persos. C'est exactement la classe de
   défauts que l'intégration MAX dans les places `$26-$29` risque de produire.
7. ***Upper* NAOMI aurait une image de retard sur la CPS-2** (ja.wikipedia, sans source). Pour HSFA, c'est un
   décalage attendu face à l'oracle MAME `sfz3ugd`, et une mesure à faire, pas un argument publicitaire.
8. **Netplay (rollback)** : le cœur est déterministe et gère les états, mais trois points doivent être levés avant
   toute partie en ligne : le petit écart du son après rechargement d'un état (corrélation 0,996-0,999, origine
   inconnue), l'identité des réglages entre les deux joueurs (horloge 68K, options), et l'identité de l'état sur x86
   et sur ARM.
9. **Ce que Capcom dit de ses propres rééditions** (CFC2) : « la version à laquelle le plus de joueurs ont joué » ;
   son refait d'après les cartes, à 99 % : hauteur, volume, **priorité de déclenchement, polyphonie**. HSFA doit écrire
   sa **politique de référence** aspect par aspect (arcade, Hyper PS2, amélioration HSFA), et tester la polyphonie
   que le 2ᵉ QSound du rejeu modifie.
10. **Distribution** : script de construction depuis l'ISO + patchs de sources, zips déterministes (empreintes
    publiées), aucune ROM, aucun IPS/BPS de ROM. La licence FBNeo **interdit toute recette et même l'appel aux dons**
    pour un projet qui utilise son code : à respecter strictement.

---

## 1. Faits techniques utiles au projet

### 1.1 Limites de la CPS-2 et place de HSFA

| Ressource | CPS-2 réelle | HSFA aujourd'hui | Source |
|---|---|---|---|
| ROM graphique | **32 Mo**, pleine avec SFA3 (7 734 tuiles 16×16 libres au banc) ; Upper dépasse d'au moins 9 % (58 000 tuiles absentes de SFA3) | 128 Mo au fork (`HSFA_GFX`), 64 Mo au cœur ; codes d'objet sur 20 bits | [interne] HANDOFF R§4, §115-§116 ; chap. 12 « Plus grand que la carte » |
| ROM programme 68K | `$000000-$3FFFFF` (FBNeo ne mappe que cette plage) | 4 Mo + blocs externes `$A00000-$EFFFFF` (`hsfa_ext.bin`) | [interne] §135, `coeur-fbneo.md` |
| Échantillons QSound | *Alpha* et *Alpha 2* : **4 Mo** (`0x400000`) ; *Alpha 3* : **8 Mo** (`0x800000`) ; *Zero 2 Alpha* : 4 Mo, mêmes CRC que *Alpha 2* | ROM hybride de **16 Mo**, pleine (0,27 Mo récupérable) ; 2ᵉ QSound (rejeu, 8 Mo lus dans `X_DATA.BIN`) ; 3ᵉ QSound (carte musique) | [lu] MAME `cps2.cpp` (07_son §1) ; [interne] SON-HYPER-ROM §0, §11-§12 |
| Plafond d'adressage QSound | inconnu sur carte réelle | 16 Mo (la banque tient sur un octet dans l'entrée d'échantillon) | [interne] SON-HYPER-ROM §6 |
| Musique | partitions Z80 + échantillons | flux Ogg Vorbis de l'ISO (zip d'Hyper 201 Mo) ; carte musique (pilotes Z80 d'origine) en option | [interne] §150-§152 |
| Sauvegarde | EEPROM 93C46 (128 octets) | idem, plus options du cœur | [interne] ETAT-DES-LIEUX §2 |

- **Le saut de 4 à 8 Mo** est cohérent avec ce que dit Funamizu pour *Vampire Savior* (1997, même carte) : « nous
  sommes passés de 32 à 64 mégabits pour le son » [lu] shmuplations, *Vampire Savior* (07_son_verif, citation 5).
  C'est une inférence pour *Alpha 3*, mais elle colle aux régions de MAME.
- **Les sets « 8 Mo » de strygo** (rétroportages d'*Alpha 2 Gold* / *Zero 2 Dash*) : « The 8 MB builds hold more
  QSound audio than the original CPS-2 hardware supports, so they run only on HBMAME and MiSTer. » [lu]
  `strygo/arcade-patches`, `data/patches.json` (10_bidouilleurs_verif, « Nouveaux faits »). Le « matériel d'origine »
  vise sans doute la configuration de la carte B d'*Alpha 2* ; *Alpha 3* a déjà 8 Mo [inférence].
- **Conséquence pour HSFA** : aucun des trois jeux ne tourne sur une carte réelle en l'état. Même SFA3 traduit passe
  par la conversion des codes de tuiles et d'objets (`banc_plans.lua`, `banc_sprites.lua` → `cps_hsfa.cpp`). La
  question « vrai matériel / MiSTer » est hors du périmètre de la 1.0. Elle demanderait un cœur FPGA dédié.
- **Fréquence** : sortie QSound à 24,038 kHz (60 MHz / 2 / 1248) ; échantillons 16 bits en théorie, « but Capcom only
  has 8-bit ROMs connected » ; 16 voies PCM + 3 voies ADPCM à 8 kHz [lu] MAME `qsound.cpp`, `qsoundhle.cpp`
  (07_son §1). Ne pas reprendre les « 4 MHz » de Wikipédia (07_son_verif, correction 12).

### 1.2 Émulation QSound : HLE, LLE, et ce que cela change pour les tests son

Chronologie [lu] (10_bidouilleurs §4, 10_bidouilleurs_verif « QSound ») :

| Version | Ce qui change |
|---|---|
| MAME ≤ 0.195 | HLE ancienne (Leaman, Horna, « thanks to CAB ») |
| MAME 0.196 (28/03/2018) | **LLE** de Vas Crabb : le programme interne du DL-1425 (`dl-1425.bin`, 0x2000 octets, CRC `d6cf5ef5`) tourne sur un DSP16A émulé ; le pilote CPS-2 l'instancie déjà (`QSOUND`) |
| FBNeo, mai 2018 | `qs_c.cpp` : « Capcom DL-1425 QSound emulator by superctr (Ian Karlsson) with thanks to Valley Bell — 2018-05-12 - 2018-05-15 » |
| MAME 0.201 (29/08/2018) | `qsoundhle.cpp` remplacé par le portage du programme DSP (superctr, ValleyBell) |
| MAME 0.203 | « Saturate voice and output accumulators (MT07115) » dans la HLE |

**Ce qu'utilise HSFA** [interne] :
- fork MAME `sfa3hx` : QSound principal = **LLE** de MAME ; 2ᵉ QSound du rejeu = `qsound_hle_device` (« qsound_hsfa ») ;
- cœur FBNeo : QSound principal = **HLE `qs_c.cpp`** ; 2ᵉ et 3ᵉ QSound = `tools/son-hyper/hsfa_qsound.h`, copie
  instanciable de `qs_c.cpp` (« la banque est lue sans tester le bit 15 », comme la HLE de MAME).

**Conséquences pour les tests son** :
1. **Corriger `docs/architecture/coeur-fbneo.md` §5** : « QSound simplifié de FBNeo » est inexact. C'est la HLE de
   superctr, tirée du programme du DSP. L'écart LLE/HLE existe, mais il est petit.
2. **Deux régimes de comparaison** :
   - *même implémentation, même construction* : sortie **exacte au bit** (déjà vrai pour `-wavwrite`, HANDOFF §79 :
     « déterministes au bit près ») → test de non-régression strict ;
   - *fork (LLE) contre cœur (HLE)*, ou *HSFA contre arcade sous MAME* : tolérances (corrélation de spectrogramme,
     niveau en dB, instants de départ/arrêt à l'image près), comme dans SESSION-CLOUD §6.
3. **Vérifier la saturation** (MT07115, MAME 0.203) dans le `qs_c.cpp` de la base FBNeo (`af5d3f3`) et dans
   `hsfa_qsound.h` : un diff de quelques lignes contre `qsoundhle.cpp` actuel suffit. Sans saturation, une voix
   rejouée forte peut « enrouler » au lieu d'écrêter [inférence].
4. **Oracles son d'arcade** : faire tourner les références (`sfa`, `sfa2`, `sfz2al`, `sfa3`) sous **MAME en HLE**
   quand on compare au cœur (même famille d'algorithme), et en LLE seulement pour trancher un doute.
5. **Polyphonie et priorité** (voir §1.7) : le rejeu ajoute un 2ᵉ QSound. Une voix SFA1/SFA2 ne vole donc plus de
   voie aux bruitages, contrairement à l'arcade d'origine. C'est peut-être un mieux, mais c'est un **écart de
   comportement** à documenter et à mesurer (nombre de voix simultanées, coupures).

### 1.3 Régions, révisions, clés, sets déchiffrés (ce que MAME déclare)

- **Sets Phoenix** : MAME range en « bootleg » des sets déchiffrés de la série, `sfad`, `sfz2ad`, `sfz2jd`, `sfz2ald`,
  **`sfa3ud`** (USA 980904), `sfz3jr2d`. Ils tournent sur la machine `dead_cps2` avec `phoenix.key` [lu] MAME `cps2.cpp`
  (10_bidouilleurs §1). HSFA part de `sfa3ud` (banc stock et fork `sfa3hx`, clone de `sfa3ud`).
- **Clés** : depuis MAME 0.178 (28/09/2016), les clés des sets d'origine sont des fichiers `.key` « that can be
  programmed onto a CPS2 motherboard » [lu] whatsnew 0.178. Les sets de strygo gardent une région `key` (programme
  chiffré) ; celui de Zer0-NexuS tourne en `dead_cps2` [lu] HBMAME `cps2mis.cpp`. Rien de plus n'est utile ici.
- **Révisions de SFA3** (MAME) : `sfa3us` USA 980616 « SAMPLE » ; 980629 (`sfz3jr2`, `sfa3ur1`…) ; Asie 980701 ;
  Japon 980727 ; **980904** (`sfa3`, `sfa3u`…) [lu] (04_zero3_verif). Arcade-history : la révision 1 avait deux bogues
  de Karin (super en X-ISM ; projection à 99 % de dégâts en MAZI) (04_zero3_verif). **Le module `ro3` suit 980904**
  (13 fonctions sur 250 plus proches de 980904, 0 de 980629) [interne] HANDOFF.
- **Révisions dans l'Anthology** : le menu SECRET OPTION choisit une date (98/06/29 ou 98/07/27 pour SFA3) ; la liste
  de 18 interrupteurs de *Zero 2* laisse penser que les révisions sont des **commutateurs** dans un seul programme
  [interne] CARTE-MODULES §4 ; chap. 10 « Les révisions deviennent des interrupteurs ». **Point ouvert** : HSFA expose
  difficulté, dégâts, chrono, vitesse et manches dans les options du cœur (§147), mais pas la révision. Les bogues de
  Karin rev. 1 font une sonde toute trouvée pour vérifier ce commutateur.
- **Régions et disques** : le dépôt ne reconnaît que l'ISO **USA `SLUS-21317`** (CRC `72CE7A78`). Le disque japonais
  (`SLPM-66409`, 25/05/2006) a ses propres versions arrangées et la liste des coups à la pause [lu] IGN ; ja.wikipedia
  (09_anthology_hyper_verif). Le PAL (SLES) n'est documenté nulle part. Les « English Restoration » de strygo
  rappellent que les versions occidentales ont perdu des répliques (*Alpha 3* US : huit répliques génériques par
  perso, contre 625 répliques propres à l'adversaire) [lu] `strygo/arcade-patches` (affirmations de l'auteur).
  **Point ouvert** : quelle région affichent les modules USA retraduits, et que donnerait un module du disque
  japonais ?

### 1.4 Comment MAME, HBMAME et FBNeo déclarent les sets de fans

| Set | Auteur, date | Déclaré où | Ce qu'il a résolu | Ce qu'on en apprend |
|---|---|---|---|---|
| **SFZ2A Dash / Gold** `sfz2al20` (« 960813U ») ; FBNeo « Hack, v1.2.1 » | Zer0-NexuS, 2026 | HBMAME `cps2mis.cpp` ; FBNeo `d_cps2.cpp` | Cammy de *Gold* dans `sfz2ald` depuis l'Anthology : graphismes, animations, collisions, 85 attaques, 363 projections lues dans `X_0526`, portraits, fin, **voix de `X_0333_MOMO`** (14 échantillons en PCM 12 019 Hz) ; tient dans les **4 Mo** QSound en rééchantillonnant 156 longs échantillons à 15/16 ; musique convertie avec perte ; variantes à la touche Start | La voie « à la main » tient dans le matériel d'origine, au prix de compromis audio. Prudence affichée : « not yet established as a perfect, complete port of every Gold rule ». Révision 31 : cris inversés corrigés, comme nos corrections de cris (§158) |
| **PS2 Backport** `sfa2d`, `sfa2g`, `sfz2d`, `sfz2da` (12/10/2026) ; `sfa2ex`, `sfz2ex` (15/10) | strygo | HBMAME `cps2mis.cpp` | Éditions de l'Anthology reconstruites « comme un vrai jeu CPS-2 » | **Région QSound déclarée à `0x800000`** : HBMAME accepte un set qui agrandit une région de la carte. Région `key` gardée |
| **English Restoration** SFA, SFZ, SFA2, SFZ2, SFZ2A (11-13/10/2026) ; FBNeo « Warriors' Dreams Restoration (USA RC1) » | strygo | HBMAME, FBNeo | Répliques, sang, musique du Dramatic Battle, correctifs de révisions | Mine sur les différences régionales (à recouper dans MAME) |
| **SFZ3 Mix** 0.07-0.13 (2022), « Turbo Mix » 0.20-0.32 (2023-2026) | Zero800 | HBMAME `cps2t.cpp` ; FBNeo `Cps2TurboInit` (v0.32 et v0.13) ; Fightcade v0.13 | Machine **fictive** : 68K à 32 MHz, Z80 16 MHz, programme 6 Mo, objets en `$665000`, gfx 64 Mo, QSound 16 Mo, 416 px de large, musique en WAV | **Précédent d'un matériel étendu accepté par FBNeo en amont.** Format différent du fork HSFA (HANDOFF §136 : « regardé, non repris ») |
| **SFA3 Challenger's Edition** (« 210408U ») | Grego, Gnawtor | HBMAME, FBNeo, **Fightcade** | Persos secrets d'office, couleur = ISM, marque Zero/Alpha, choix du décor, palettes console ; patch IPS « DARKSOFT ROMS » | Une édition de compétition entre dans Fightcade |
| **ZERO3 Training Edition v1.2** | 0xZERO3 (2020-2022) | HBMAME, FBNeo, Fightcade | Entraînement sur 980629 JAPAN, sur carte réelle aussi | Liste de fonctions d'entraînement attendue par les joueurs |

Sources : [lu] HBMAME `cps2mis.cpp`, `cps2t.cpp` ; FBNeo `d_cps2.cpp` ; Fightcade `fightcade-fbneo/.../d_cps2.cpp` ;
README `Zer0-NexuS/sfz2a-dash-cps2`, `originalgrego/sfa3ce`, `0xZERO3/ZERO3TE` (10_bidouilleurs §2 ;
`docs/reference/sfz2a-dash-cps2.md`).

**Ce qu'il faut retenir pour HSFA**
1. **Forme d'une déclaration** : un clone d'un parent (`sfa3`), une liste de ROM figée (noms, tailles, CRC/SHA-1), des
   régions explicites. HSFA a déjà les ingrédients : zips **déterministes** (`SOURCE_DATE_EPOCH`) et liste stricte
   (`HSFA_STRICT=1`). Chaque version publiée aurait donc des CRC fixes [interne] BUILD.md §7.
2. **Ce qui gêne une entrée en amont** : les variables d'environnement (`HSFA_LAT4`, `HSFA_CLOCK`…), les fichiers lus
   hors du zip (`<système>/fbneo/hsfa/`), des membres non standard (`hsfa_ext.bin`, `hsfa_tab.bin`, flux de 201 Mo).
   L'en-tête de « ROM auto-descriptive » prévu (`ARCHI-Reorganisation-Donnees.md` §2.4) et des options du cœur à la
   place des variables vont dans le bon sens.
3. **Les flux musicaux** : aucun set de fans n'embarque 200 Mo de musique. *SFZ3 Mix* joue des WAV, ce qui prouve
   qu'un lecteur d'échantillons hors QSound est admis. La **carte musique** (partitions jouées par les pilotes Z80
   d'origine, §151) réduit la part des flux pour ZERO et ZERO 2 et rapproche HSFA du modèle accepté.

**Opportunité de contact** (par ordre d'utilité) :

| Qui | Pourquoi | Ce qu'on peut offrir |
|---|---|---|
| **Zer0-NexuS** | Même source (Anthology). Ils ont extrait les voix de Cammy de `X_0333_MOMO`, et Cammy ALPHA (`$7E`) est **muette** dans HSFA. Ils ont décodé `X_0526` (projections de *Gold*). Leur méthode de validation est à connaître | Cartes de modules (`CARTE-MODULES.md`), traducteur et carte RAM, comparaison de voix contre `sfz2al` ; bêta-test croisé |
| **strygo** | Déclaration HBMAME de sets à **QSound agrandi** ; connaissance fine des différences régionales ; déblocage de région d'Upper NAOMI (« one byte in the disc header ») | Retours sur les révisions vues dans l'Anthology (interrupteurs de ro2) |
| **Mainteneurs HBMAME / FBNeo** (et Zero800 pour la « CPS2 Turbo ») | Chemin d'entrée d'un pilote à matériel étendu | Patchs propres, sets à CRC fixes, aucune ROM |
| **0xZERO3** (`sfa3_support`, Training Edition) | Profil PS2 de son script ; communauté japonaise | Adresses RAM de la traduction |
| **Grego** (*Challenger's Edition*, *Final Fight* sur carte SFA3 avec le pilote Z80 de SFA3) | Même principe que notre ROM son hybride (HANDOFF §135) | — |
| **Zero Division** (Discord *Alpha 3*) | Bêta-testeurs de haut niveau (voir §3.6) | Builds de test et grille de retour |

Règles du contact : présenter le projet sans aucune donnée de jeu, poser une question technique précise, citer et
créditer, respecter les licences (la licence FBNeo s'applique aux patchs du cœur).

### 1.5 Rollback, Fightcade, netplay : ce qu'il faudrait pour jouer HSFA en ligne

Faits [lu] (10_bidouilleurs §4, _verif ; 08_competition_verif ; 06_portages_alpha3_compilations_verif) :
- GGPO : « Rollback networking uses input prediction and speculative execution » ; MIT depuis le 9/10/2019. La
  démonstration décisive faite à Capcom fin 2007 était une partie d'**Alpha 2** sur Final Burn Alpha + GGPO.
- Fightcade (Pau « Pof » Oliva, bêta fin 2014, 2.0 en 2017) : « emulator built with FBNeo and GGPO » ; il intègre déjà
  *Challenger's Edition*, *Training Edition*, *SFZ3 Mix* 0.13, des hacks « A-ISM only », etc. Ses sauvegardes d'état
  SFA3 ont « déjà les DIP switches activés » (SuperCombo).
- La scène actuelle d'*Alpha 3* joue sur Fightcade 2, sur la 30th (rollback, version **internationale** en ligne même
  au Japon) et sur CFC2 (*Upper*, rollback ; **les persos MAX et les modes NORMAL/MAZI/SAIKYO/CLASSIC sont refusés
  en parties classées**). Communauté : Zero Division (Discord).
- En compétition sur Hyper, le **S-ISM rose (CE-ISM) est banni** : il donne des infinis à plusieurs persos
  (SuperCombo, 09_anthology_hyper Q3).

Ce que le rollback demande au cœur HSFA, et ce qui est déjà acquis [interne] :

| Exigence | État HSFA | Action |
|---|---|---|
| Émulation déterministe pour des entrées données | oui : même cœur, mêmes entrées → même partie (151 VERSUS rejoués) | tests d'empreinte RAM, §3.4 |
| États de sauvegarde complets et rapides | oui (état du banc, flux 124 octets, carte musique en un bloc) ; run-ahead vérifié pour Vorbis | **écart du son après rechargement (corrélation 0,996-0,999, écart max 1 490) d'origine inconnue, présent avant les patchs 8-10** (SESSION-CLOUD §6). Si cet écart vient d'un état Z80/QSound mal sauvé que le 68K peut lire (boîte aux lettres, compteur `$618021`), il **désynchronise** une partie en ligne. Priorité haute |
| Même état sur toutes les plates-formes | son « à ±1 près » entre x86 et ARM (qemu) : des calculs flottants (Vorbis, mixage) diffèrent | vérifier que **rien de flottant ne revient vers le 68K ou le Z80** (fin de flux, position) : empreinte RAM identique x86 / ARM / Windows sur une tournée |
| Mêmes réglages des deux côtés | horloge 68K (`HSFA_CLOCK`) : elle **change le tirage aléatoire** (HASARD §0) ; options du cœur ; `lat4=` dans le zip | un **préréglage « en ligne »** figé, et son empreinte affichée |
| Même jeu des deux côtés | zips déterministes, CRC fixes | publier les CRC attendus par version |
| Marge de calcul (re-simulation de plusieurs images) | inconnue sur RGB10X (kit `essai_son` non lancé) | mesurer les images/s en re-simulation pure |

**Comment un set HSFA pourrait être joué sur Fightcade** [inférence, à vérifier auprès de Fightcade] :
1. d'abord sur **RetroArch** (netplay de libretro, à base d'états et de re-simulation) entre deux cœurs HSFA
   identiques : c'est le banc le plus proche, il ne demande rien à personne ;
2. ensuite, faire accepter les pilotes HSFA dans **FBNeo en amont** (modèle `Cps2Turbo`), avec des sets à CRC fixes ;
3. enfin, demander leur ajout au FBNeo de **Fightcade**. Fightcade ne fournit pas les données : chaque joueur
   construirait son zip depuis son ISO, et le déterminisme garantit un zip identique pour tous.

Le préréglage de tournoi est à fixer **avec la communauté** : vitesse (défaut de l'Anthology : TURBO2), manches,
chrono, ISM et versions admises (CE-ISM exclu ?), persos EX, MAX.

### 1.6 Outils communautaires réutilisables comme bancs de test

| Outil | Ce qu'il fait | Usage pour HSFA | Source |
|---|---|---|---|
| **`sfa3_support` v1.21** (0xZERO3) | RAM, boîtes (poussée, 3 zones de vulnérabilité, attaque, projection, projectiles, boîte de Take No Prisoner), invincibilité, no-throw, valeur du turbo (0 / 6 / 8, jusqu'à `0x0F`), arrêt sur coup. Testé sur MAME 0200b-0242b, mame-rr, fba-rr, **Fightcade2 (FBNeo 0.2.97.44)**, BizHawk (Saturn, PS, GBA), **PCSX2-rr (PS2)** | **Oracle à trois voies** : le profil PS2 lit la RAM vue par le portage, que HSFA reproduit (recette §29 : mot = même adresse, octet XOR 1, long échangé). Adapter le profil aux bases HSFA (`$FF0000` = RAM PS2 `0x900000` pour ro3) → afficheur de boîtes HSFA, puis **comparaison image par image des boîtes** arcade ↔ PS2 ↔ HSFA. Le profil GBA couvre Eagle, Maki et Yun (contrôle des boîtes MAX) | [lu] `github.com/0xZERO3/sfa3_support` ; HANDOFF §135 |
| **`cps2-hitboxes.lua`** (dammit, 2012) | Boîtes de SFA, SFA2, SFZ2A, SFA3 (« tripwire », « axis throw ») ; décalages par révision, y compris `sfad`, `sfz2ald` | Référence des boîtes pour les versions ZERO et ZERO 2 d'Hyper face à leur arcade | [lu] `Jesuszilla/mame-rr-scripts` |
| **`fbneo-training-mode`** (peon2) | Mode entraînement générique pour FBNeo (SFA, SFA2, SFA3) | Base pour un mode entraînement Lua sur FBNeo autonome ; liste des attentes des joueurs | [lu] `peon2/fbneo-training-mode` |
| **ZERO3 Training Edition** | Free Play, retour rapide à la sélection, temps infini, pas de K.O., vie remise au maximum entre combos, jauge MAX ou 50 %, étourdissement et guard crush coupables, *counter* forcé, CPU ou humain, *recovery*, vitesses NORMAL / TURBO1 / TURBO2 / max | **Cahier des charges** du TRAINING d'HSFA et des triches utiles aux tests (vie remise au maximum = combos longs testables) | [lu] `0xZERO3/ZERO3TE` |
| **Challenger's Edition** | Choix du décor, couleur = ISM, persos secrets d'office | Ce que les joueurs attendent d'une édition « compétition » (choix du décor maintenu Start) | [lu] `originalgrego/sfa3ce` |
| **Tableau des coups BradyGames** | 1 652 lignes, corrigées contre SuperCombo | Matrice des coups d'Hyper (§3.3) | [interne] HANDOFF §167 |

Limite : **les scripts Lua ne tournent pas dans le cœur libretro**. Deux voies : les porter au fork MAME (scripts Lua
déjà présents) ; compiler les pilotes HSFA dans le **FBNeo autonome** (Lua disponible), ce qui ouvre aussi la voie
Fightcade. **L'étape E de la réorganisation** (RAM typée, disposition arcade) rendrait ces scripts utilisables tels
quels avec leurs adresses arcade : c'est un argument de plus pour elle.

### 1.7 Ce que la CFC2, la 30th et l'Arcade Stadium disent de la reproduction des versions

- **Choix de la version** : Shūhei Matsumoto (CFC2) : pour certains jeux « les cartes de l'époque n'existent plus »,
  ou les mises à jour sont si nombreuses qu'il est difficile d'en relever les différences ; « nous retenons donc, en
  principe, la version à laquelle le plus grand nombre de joueurs a joué » [lu] Famitsu, avril 2025.
- **Son** : l'équipe de la CFC2 a refait les bruitages « un par un » d'après les documents, en réglant « hauteur,
  volumes, priorité de déclenchement, nombre de sons simultanés aligné sur l'original », et en **enregistrant les
  cartes** quand les données manquaient : « environ 99 % de fidélité sonore » [lu] capcom.co.jp, interview CFC2
  (07_son_verif, citation 10).
- **Ce qu'on coupe** : la 30th retire l'insertion de crédits et l'écran QSound d'introduction, sauf pour *Zero 3*
  [wiki] ja.wikipedia. Eurogamer : « there might be some debate about what exactly 30th Anniversary Collection has
  chosen to emulate. These are the vanilla arcade editions » [lu] Eurogamer, 31/05/2018.
- **Upper dans la CFC2** : version NAOMI ; version anglaise « built using the Japanese version's data as a base »,
  décors retouchés, Shin Akuma et Final Bison jouables [lu] Nintendo Life, 9/03/2025. Patch de juin 2025 : « Reduced
  instances where some moves would not hit the opponent ». Mise à jour du 7/08/2025 : Eagle, Maki, Yun, Ingrid
  (désactivés en ligne classée), modes NORMAL / MAZI / SAIKYO / CLASSIC, sélection « On / Off / Original ». Patch du
  9-10/09/2025 : « Fixed an issue where M. Bison's Head Press and Somersault Skull Diver attacks would not hit Eagle,
  Maki, Yun, or Ingrid » et de même pour la Sardine Beach Special de R. Mika [lu] EventHubs (06_..._verif). Famitsu
  signale une option EX qui **rétablit le *crouch cancel*** supprimé par *Upper* [lu] Famitsu, 7/02/2025.
- **Arcade 2nd Stadium** (22/07/2022) : *Zero*, *Zero 2*, *Zero 3*, avec retour arrière [lu] 4Gamer.

**Leçons pour HSFA**
1. Écrire une **politique de référence** explicite (§3.0) : « ce que HSFA reproduit » aspect par aspect. Sans elle,
   chaque retour de joueur devient un débat.
2. Le contrôle son doit inclure **priorité et polyphonie**, pas seulement le timbre (voir §1.2, point 5).
3. **MAX** : les correctifs de la CFC2 désignent des tests précis. Head Press, Somersault Skull Diver et Sardine Beach
   Special contre les quatre persos MAX, et plus largement tout coup qui teste le perso adverse par une table indexée
   par id (tables de 40 entrées étendues à 42, `T_619b50`, `T_61a100`).
4. **Ne rien couper sans le dire** : HSFA garde l'écran QSound, les fins, le générique caché « STAFF ». Les
   différences voulues (OPTION/EXIT ramenés au menu, roulette sur la touche Pièce) vont dans une liste publique.

### 1.8 Le retard d'une image d'*Upper* NAOMI

- ja.wikipedia (phrase **sans source**) : *Upper* NAOMI « faisait tourner en émulation la version CPS-2 enrichie des
  ajouts console, d'où un retard d'1/60 s [entre l'entrée et l'écran] par rapport à la CPS-2 ». Capcom (CFC2,
  4Gamer 16/05/2025) écrit seulement qu'Upper est « basé sur la carte de *Zero 3*, avec les éléments console portés
  dessus » (06_..._verif, correction 9 ; 09_anthology_hyper_verif).
- MAME émule l'Upper NAOMI : `sfz3ugd`, « Street Fighter Zero 3 Upper (Japan) (GDL-0002) » [lu] MAME `naomi.cpp`
  (04_zero3_verif).
- **Pour HSFA** :
  - l'Upper de l'Anthology descend du programme CPS-2 de SFA3, non de la NAOMI ([wiki] ja.wikipedia :
    « アーケードのCPS-2版『ZERO3』をベースに… NAOMI版『ZERO3↑』風にアレンジ ») ; HSFA ne devrait donc pas avoir ce
    retard ;
  - **mesure à faire** (petite, utile) : latence entrée → première écriture RAM (état du perso) → première image
    changée, sur MAME `sfa3` (CPS-2), MAME `sfz3ugd` (NAOMI) et HSFA Upper, avec le même geste scripté. On s'attend à
    CPS-2 = HSFA, et NAOMI = +1 image ;
  - en comparant des **durées** à l'oracle NAOMI (fins, enchaînements), prévoir ce décalage constant ; il ne touche
    pas la logique.
- **Autre usage de `sfz3ugd`** : le mode **Final Battle** de la borne NAOMI mène directement à la fin de chaque
  perso [lu] Game Watch, 31/01/2001. C'est un raccourci pour comparer les fins des persos ajoutés par Upper (T. Hawk,
  Dee Jay, Fei Long, Guile…) à une référence d'arcade, sachant que l'Anthology présente 629 écarts face à SFA3
  (`ECARTS-UPPER.md`).

### 1.9 Autres faits pertinents

- **Le CPU joue en VERSUS sur PS2** (« プレイヤー設定を変更することで片方、または両方をコンピュータ操作にすることができる »),
  et un mode VS caché (× + △ + R2) « tire au hasard persos et modes et enchaîne les combats sans fin » [wiki]
  ja.wikipedia (09_anthology_hyper_verif). C'est un **banc d'endurance gratuit sur PCSX2** : CPU contre CPU, des
  heures, pour savoir si un plantage d'HSFA existe aussi sur PS2.
- **Défauts probables du jeu d'origine** (non vérifiés sur PS2) : EX Bison et EX Sagat ZERO 2 (`$58`, `$59`) dont les
  45 tables pointent vers Ryu (« en morceaux » au banc) ; 3 tables d'Upper à 40 entrées lues par l'id étendu
  (débordement pour les ids ≥ `$28`) [interne] INDEX-HYPER §0.4, ETATS-HYPER §1.2-§1.3. À trancher sur PCSX2 avant de
  les compter comme défauts HSFA.
- **Réputation de l'Anthology chez les compétiteurs** : pour *Alpha 1* PS2, « getting moves out is harder and charging
  takes too long so some combos are impossible. AVOID. » [lu] SuperCombo (09_anthology_hyper Q4). Le portage lit la
  manette par une couche native ; HSFA la remplace par des talons qui lisent les ports CPS-2. Il faudra **prouver
  par la mesure** que l'exécution d'HSFA est celle de l'arcade (le test des 42 commandes l'a fait pour SFA3 ; à
  étendre à Upper et aux versions d'Hyper). C'est la première question que poseront les joueurs.
- **Crouch cancel** : supprimé dans *Upper* NAOMI (infinis en V-ism) [lu] Wikipédia EN, Famitsu 2025 ; présent dans
  la CPS-2, standard sur Fightcade. **Point ouvert** : l'Upper de l'Anthology l'a-t-il ? `ECARTS-UPPER.md` n'en parle
  pas. Les joueurs le vérifieront.
- **Les ISM d'Hyper** (SHADALOO A-D) : vert = chaînes, push block ; bleu = parade et super cancel ; rose = persos de
  *SF2'* (« high damage, no Supers »), **banni en tournoi** ; rouge = coups des *VS* [lu] SuperCombo ; [wiki]
  ja.wikipedia. Correspondance confirmée au banc HSFA (NORMAL → vert, MAZI → bleu, CLASSIC → rouge, SAIKYO → rose).
- **Hyper n'a ni démo d'intro ni démo jouée par le CPU** [wiki] ja.wikipedia : l'absence d'attraction dans HSFA Hyper
  n'est pas un défaut.
- **Balayage progressif sur PS2** (△ + × au démarrage) [lu] FAQ Capcom : sans effet sur la logique, à garder hors des
  comparaisons.
- **Licence FBNeo** : « You may not sell, lease, rent or otherwise seek to gain monetary profit from FB Neo », et
  aucun appel aux dons pour un projet qui utilise son code [lu] `FBNeo/src/license.txt`. L'affaire Capcom Home Arcade
  (2019) montre la sensibilité du sujet [lu] Game Developer, Time Extension.

---

## 2. Risques et points ouverts que la recherche éclaire

Priorité : **P1** bloque la 1.0 ; **P2** à traiter avant la bêta ouverte ; **P3** amélioration.

| # | Risque / point ouvert | Ce que la recherche apporte | Prio | Action proposée |
|---|---|---|---|---|
| R1 | **Pas de politique de référence écrite** (arcade, Hyper PS2 ou amélioration HSFA ?). Exemples : voix SFA1/SFA2 ajoutées (Hyper PS2 ne les a pas), cris corrigés sur l'arcade, roulette sur Pièce, musique « All tracks » | CFC2 : « la version la plus jouée », son aligné sur la carte. La 30th : débat sur « ce qui est émulé » | P1 | Tableau §3.0, publié avec la 1.0 ; chaque écart voulu y est listé avec son option du cœur |
| R2 | **Désynchronisation en ligne** : écart du son après rechargement d'un état, d'origine inconnue ; flottants x86/ARM ; options différentes | GGPO, Fightcade, 30th et CFC2 font du rollback : la communauté jouera en ligne | P1 si netplay est dans la 1.0, sinon P2 | Test d'état (§3.4-e) ; empreinte RAM multi-plates-formes ; préréglage en ligne figé |
| R3 | **Intégration MAX** : tables de 40 → 42 entrées, pseudo-ids `$28/$29`, coups qui testent l'id adverse | CFC2 a dû corriger des coups de Bison et de Mika contre les persos MAX | P1 (si MAX dans la 1.0) | Matrice « attaquant × MAX » (§3.3) ; profil GBA de `sfa3_support` pour les boîtes d'Eagle, Maki, Yun |
| R4 | **Voie B inachevée** (plantage au K.O. du 3ᵉ combat, `0x840688`) | — | P1 | Oracle : Upper retraduit (40/40 fins) ; scènes comparées par `tournee_greffe.lua` ; balayage des 40 parcours |
| R5 | **Exécution des coups** : réputation « PS2 = exécution plus difficile » | SuperCombo (*Alpha 1* PS2 « AVOID ») | P1 | Étendre le test des commandes (42/42 SFA3) à Upper et aux versions d'Hyper ; mesure de latence (§1.8) |
| R6 | **QSound** : comparaisons fork (LLE) ↔ cœur (HLE) prises pour des régressions ; saturation peut-être absente | Chronologie MAME 0.196 / 0.201 / 0.203 ; `qs_c.cpp` de superctr | P2 | Deux régimes de tests (§1.2) ; diff `qs_c.cpp` / `qsoundhle.cpp` ; corriger `coeur-fbneo.md` |
| R7 | **Polyphonie et priorité changées par le 2ᵉ QSound** | CFC2 aligne « le nombre de sons simultanés » sur l'original | P2 | Mesure : nombre de voies actives et coupures, arcade SFA1/SFA2 contre Hyper HSFA, même geste |
| R8 | **Défauts d'origine pris pour des défauts HSFA** (EX Bison/Sagat ZERO 2, débordement ids ≥ `$28`) ou l'inverse | VS CPU contre CPU et mode VS aléatoire sur PS2 | P2 | Les reproduire sur PCSX2 ; étiquette « origine » / « HSFA » dans le suivi des défauts |
| R9 | **Révisions non exposées** (SECRET OPTION) | Bogues de Karin rev. 1 (X-ISM, MAZI) ; liste des 18 interrupteurs de ro2 | P3 | Localiser l'octet de révision ; option du cœur ; sondes Karin |
| R10 | **ISO USA seule** (`72CE7A78`) | Disque JP `SLPM-66409` (liste des coups, versions arrangées), PAL non documenté | P3 | Profils de disque dans `hsfa_build.py` ; refus propre avec un message clair si le disque est inconnu |
| R11 | **Crouch cancel dans Upper Anthology ?** | Supprimé par la NAOMI, réactivable en option dans la CFC2 | P2 | Test scripté (V-ism, perso connu) sur SFA3 arcade, Upper HSFA, `sfz3ugd` |
| R12 | **Upper NAOMI a +1 image** | ja.wikipedia (non sourcé) | P3 | Mesure §1.8 ; ne rien affirmer avant |
| R13 | **Entrée en amont / Fightcade bloquée** par les variables d'environnement, les fichiers hors du zip, le patch des décors hors chaîne | Modèle `Cps2Turbo` ; sets de fans à CRC fixes | P2 | Options du cœur à la place des variables ; tout dans le zip ; en-tête de ROM auto-descriptive ; rebaser `fbneo-hsfa-decors.patch` |
| R14 | **Licence et communication** | Licence FBNeo (pas de profit, pas de dons) ; affaire Home Arcade | P1 | Aucun lien de don ; notices de licence par composant (§3.8) |
| R15 | **Concurrence de la CFC2** (Upper + MAX + rollback, officiel) | CFC2 2025 | P3 | Positionner HSFA sur ce que personne n'a : Hyper en CPS-2, Hyper avec mode Arcade (voie B), portables hors ligne, versions ZERO / ZERO 2 avec leurs voix |
| R16 | **Écart LLE/HLE et tirage aléatoire** entre fork et cœur (phase Z80 / 68K) | HASARD §0 | P2 | Comparer fork et cœur seulement jusqu'à la première divergence du générateur (`$FF80AE`), ou neutraliser le tirage décoratif des particules en mode test |

---

## 3. Stratégie de solidité, par priorité

### 3.0 Politique de référence (à écrire en premier)

| Aspect | Référence (oracle) | Tolérance | Si écart voulu |
|---|---|---|---|
| Logique de jeu SFA3 (`ro3`) | arcade `sfa3ud` 980904 sous MAME | **exacte** : RAM typée, positions, captures ±1, 42/42 commandes | — |
| Logique d'Upper (`ro5`) | **Anthology PS2** (PCSX2) ; SFA3 arcade pour le code partagé ; NAOMI `sfz3ugd` à titre informatif (+1 image ?) | exacte face à la PS2 ; écarts face à la NAOMI documentés (629 écarts connus) | — |
| Logique d'Hyper (`ro9`) | **Hyper PS2** (PCSX2) : c'est le programme qu'on traduit | exacte | correctifs de défauts d'origine **seulement en option** |
| Versions ZERO / ZERO 2 / ALPHA d'Hyper | Hyper PS2 pour le comportement ; arcade `sfa` / `sfa2` / `sfz2al` **à titre informatif** (Capcom a refait ces moteurs dans Hyper) | écart à l'arcade = information, pas défaut | — |
| Voix et cris par version | arcade (`sfa`, `sfa2`, `sfz2al`) : décision de l'utilisateur, au-delà d'Hyper PS2 | code de voix identique au geste près | option « voix PS2 d'origine » |
| Musique | flux PS2 (« All tracks ») par défaut ; partitions d'arcade (carte musique) en option | départs, boucles, fondus à l'image ; niveau ±0,5 dB | options du cœur |
| Son (moteur) | même implémentation : bit à bit ; entre implémentations : corrélation ≥ 0,95 et niveau ±1 dB | — | — |
| Ergonomie | CPS-2 (pas de Select) | — | roulette sur Pièce ; OPTION/EXIT ramenés au menu ; listés |
| MAX (Eagle, Maki, Yun, Ingrid) | SFA3 MAX PSP pour les données ; CFC2 pour l'intégration à Upper (observations) ; profil GBA de `sfa3_support` pour les boîtes | données identiques ; interactions vérifiées par la matrice MAX | — |

### 3.1 P0 — Figer, versionner, mesurer (avant tout le reste)

1. **Identifiant de build** : une version (SemVer, `0.9.0-beta.1`…) et un **manifeste** produit par `hsfa_build.py` :
   md5 de chaque sortie (ROM programme des trois jeux, blocs, tables, zips), état des interrupteurs du traducteur,
   compteurs par règle, commit du dépôt, commit FBNeo et liste des patchs. Le cœur affiche cet identifiant au
   démarrage (journal) et dans une option en lecture seule.
2. **Une seule batterie** : `valide_tout.sh` (≈ 1 h en parallèle) devient la porte d'entrée, avec un rapport machine
   (JSON) et une ligne « VERT / ÉCART ». Interdire toute publication si la batterie n'est pas verte sur le commit exact.
3. **Corpus figé** : copies des ROM produites et de leurs md5 pour chaque version publiée (règle déjà écrite dans
   `oracle-et-non-regression.md` §6), traces dorées (§3.4) rangées par version.

### 3.2 P1 — Les oracles

| Oracle | Ce qu'il juge | Outillage existant | À ajouter |
|---|---|---|---|
| **Arcade sous MAME** (`sfa3ud`, `sfa3`, `sfa`, `sfa2`, `sfz2al`) | SFA3 exact ; voix et cris ; commandes | `tournee.lua`, `commandes.lua`, `compare_ram.py`, `compare_voix_arcade.py`, `mesure_cris_arcade.py` | mesure de latence ; boîtes via `cps2-hitboxes.lua` / `sfa3_support` |
| **Anthology sur PCSX2** (Upper, Hyper) | ce que fait réellement le programme traduit | états PCSX2 copiés (`etats_ps2/`), `visu.lua` | **RAM PS2 ↔ RAM traduite** : la recette §29 rend les deux vues directement comparables (même disposition, bases différentes). Vidages à des points de contrôle (début de manche, K.O.) depuis des états PCSX2 pris au même moment ; enregistrement d'entrées PCSX2 pour rejouer le même scénario ; VS CPU contre CPU pour l'endurance |
| **Upper NAOMI** (MAME `sfz3ugd`) | fins et comportements des persos d'Upper, crouch cancel, latence | — | scénarios courts ; mode Final Battle pour les fins |
| **CFC2** (observation humaine, aucune donnée extraite) | interactions des persos MAX, modes NORMAL/MAZI/SAIKYO/CLASSIC dans Upper | — | fiche d'observations datée (version du jeu CFC2) |
| **Guide BradyGames + SuperCombo** | liste des coups par jeu, version, ISM | tableau de 1 652 lignes (hors dépôt) | génération automatique des gestes à partir du tableau (§3.3) |
| **Interne : Upper retraduit** | voie B (mode Arcade greffé) | 40/40 fins, `nonreg_ro5.sh` | comparaison scène par scène de la greffe |

Règle de méthode (déjà la bonne, `oracle-et-non-regression.md` §1) : **une grandeur, pas l'œil** ; vérifier d'abord
que l'écart vient du jeu traduit et non du banc ou du cœur (§146).

### 3.3 P2 — Les matrices de tests

Le produit combine 36 persos (40 avec MAX) × 4 familles de version (ZERO, ZERO 2, ALPHA, ZERO 3) + EX × 3 ISM +
4 S-ISM + 4 modes (NORMAL, MAZI, SAIKYO, CLASSIC) × modes de jeu (VERSUS, TRAINING, ARCADE greffé…) × côté (J1/J2) ×
plates-formes. Tout croiser est impossible ; on étage.

**Niveau 1 — fumée exhaustive** (automatique, toutes les combinaisons valides, une manche, K.O. forcé) :
- pour chaque id jouable et chaque ISM / mode / version EX, en J1 **et** en J2 : sélection conforme (`$102`, `$116`,
  `$117`, `$D3`, `$133`), aucune exception, 2 manches, musique demandée = table du 68K, aucun flux en échec, cris et
  voix aux codes attendus ;
- acquis : 151 VERSUS, 231 VERSUS de modes, 52 de persos EX, 194/216 codes musicaux entendus [interne] §154-§156.
  **À compléter** : le côté J2 pour tous, les 10 codes `01E6-01F7` et les 12 morceaux ZERO 3 hors VERSUS, et
  l'ARCADE greffé quand la voie B tournera.

**Niveau 2 — coups** (automatique, depuis le tableau BradyGames) :
- pour chaque ligne (jeu, version, ISM, perso, manipulation, boutons) : générer le geste à l'image près, l'exécuter
  depuis un état sauvé commun, relever : animation déclenchée, nombre de coups, dégâts, jauge consommée, voix ;
- comparer à Hyper PS2 (oracle) et, pour information, à l'arcade de la version ;
- inclure les 9 lignes « à tester » du tableau et les sondes connues : supers d'Akuma et de Dan (`TAILBR`), boules de
  Sakura et Rose (`LUIDN`), projection HK d'Akuma EX (`$74`), bogues de Karin rev. 1 (révision).

**Niveau 3 — interactions sensibles** (scripté, ciblé) :
- **MAX** : chaque attaquant qui teste l'id ou la classe adverse (Head Press, Somersault Skull Diver, Sardine Beach
  Special, projections, coups à boîte spéciale) contre Eagle, Maki, Yun, Ingrid, et l'inverse ;
- **ids ≥ `$28`** et tables de 40 / 42 entrées ;
- **combat miroir** (même perso, zones A8/D8, §130) ;
- **S-ISM** : infinis connus du CE-ISM (vérifier qu'ils existent : c'est un signe de fidélité, pas un défaut),
  parade et super cancel du S-ISM bleu ;
- **mécaniques de compétition** : crouch cancel (SFA3, Upper), guard crush V-ism, custom combos, liens à 1 image sur
  quelques combos de référence (V-Akuma, Dhalsim, Sodom : le haut de la tier list de VER).

**Niveau 4 — parcours longs** (nuit) :
- SFA3 : 32 fins ; Upper : 40 fins ; Hyper augmenté : 40 parcours Arcade (voie B) ; SURVIVAL, DRAMATIC, TRAINING
  (enregistrement / rejeu) ;
- endurance : attraction de 40 000 images ; VERSUS CPU contre CPU en boucle pendant des heures (aussi sur PCSX2 pour
  la comparaison).

**Niveau 5 — plates-formes** : un sous-ensemble fixe du niveau 1 (20 matchs) et du niveau 4 (3 fins) sur chaque
cible (§3.5).

### 3.4 P3 — Non-régression automatisée

**a. Contrôles statiques (à chaque construction, en minutes)**
- `=0` sur chaque interrupteur redonne des ROM identiques (md5) ;
- compteurs par règle, `chutes.json`, `mem_miss.json`, `audit_exacts.txt`, `census.py` : toute variation non
  expliquée = signal ;
- `verifier_liens.py`, `verifier_imports.py`.

**b. Traces dorées** (le cœur sans fenêtre est l'outil le plus rapide : `hsfa_run`, `joue_linux`)
- pour chaque scénario du corpus, enregistrer à chaque image une **empreinte** (hachage) de zones choisies : variables
  A5, structures des joueurs `$FF8400 + $400·k`, liste d'objets, graine `$FF80AE`, registres de la boîte aux lettres
  QSound. Plus une capture toutes les N images ;
- en cas d'écart : **première image divergente**, puis zone et champ (`disposition.lua` pour lire par adresse arcade),
  puis instruction (`carte_image.txt`), comme `diag.py` / `diverge.py` ;
- un seul **format d'entrées** commun aux trois bancs (MAME Lua `INPUTS`, frontal `HSFA_ENTREES` / `tournee.h`,
  enregistrement PCSX2) : un convertisseur suffit, et le même scénario tourne partout.

**c. Rejeux d'entrées**
- corpus versionné : scénarios du niveau 1-4, gestes du tableau de coups, **parties humaines enregistrées pendant la
  bêta** (avec l'accord des joueurs). Chaque défaut corrigé laisse son scénario dans le corpus ;
- les replays Fightcade de SFA3 sont des entrées image par image sur l'arcade [inférence : format à étudier]. Ils ne
  se rejouent pas à l'identique sur la traduction (le tirage dépend de la phase Z80 / 68K), mais ils peuvent servir
  de **gestes réalistes** en mode d'entraînement, sans hasard.

**d. Son**
- même implémentation : WAV identique au bit (régression) ;
- entre implémentations ou contre l'arcade : corrélation de spectrogramme, niveau, instants de départ / fin / boucle
  (outils existants : `empreintes.py`, `compare_rejeu.py`, `HSFA_FLUX_LOG`) ;
- polyphonie : nombre de voies actives par image et coupures (§1.2-5).

**e. États et rollback**
- pour chaque scénario : partir de l'image N, sauver, continuer jusqu'à N + 600 ; recharger, refaire ; **empreintes
  identiques image par image**. Puis rechargement toutes les 7 images (re-simulation façon rollback) ;
- d'abord **trouver l'origine** de l'écart du son après rechargement (SESSION-CLOUD §6) ; si un état Z80 / QSound
  manque, l'ajouter ;
- versionner le format d'état (le changement de taille au §146 doit être détecté et refusé proprement).

**f. Multi-plates-formes**
- même scénario sur x86_64 Linux, Windows (Wine), aarch64 (qemu, puis matériel) : **empreintes RAM identiques**
  exigées. Le son peut différer de ±1 (flottants), la logique jamais.

**g. Cadence**
- par commit du traducteur : a + b (scénarios courts) ;
- chaque nuit : niveaux 1, 2 et 4 ;
- avant une publication : tout, plus les plates-formes.

### 3.5 P4 — Matériel et émulateurs

| Cible | Rôle | Contrôles |
|---|---|---|
| Fork MAME `sfa3hx` (0.285) | banc de développement, débogueur, Lua, oracles arcade | intégrer le rejeu (`rejeu-sur-fork-flux.patch`) ; protéger l'EEPROM de `sfa3hx` (piège n° 8) |
| Cœur Linux x86_64 | tests automatiques | toute la batterie |
| Windows x64 (MinGW, statique) | joueurs PC, bêta | niveau 5 sous Wine, puis sur une vraie machine |
| Android arm64 (RG477M, Retroid) | joueurs portables | installation, un match d'Hyper avec le zip Ogg, carte musique, états, run-ahead |
| ROCKNIX aarch64 (RGB10X, RG Arc-D) | cible la plus faible | `essai_son_hyper.sh` (> 60 images/s attendu) ; marge en re-simulation ; touche Select = raccourci RetroArch (conflit à vérifier avec la roulette) |
| PCSX2 (Anthology) | oracle | états, enregistrement d'entrées, VS CPU |
| MAME NAOMI `sfz3ugd` | oracle informatif d'Upper | latence, crouch cancel, fins |
| FBNeo autonome (option) | scripts Lua (`sfa3_support`, `fbneo-training-mode`), étape vers Fightcade | compiler les pilotes HSFA hors libretro |

### 3.6 P5 — Bêta-test communautaire

**Phases**
1. **Alpha fermée** (2-4 semaines) : 3-6 testeurs choisis (Zero Division, un joueur d'*Alpha 2*, un utilisateur de
   ROCKNIX, un d'Android). Builds identifiés, grille obligatoire.
2. **Bêta ouverte** : annonce sur GitHub (issues avec modèle), Zero Division, forums de portables. Aucune donnée
   fournie : guide de construction depuis l'ISO, empreintes à vérifier.
3. **Bêta en ligne** (si netplay dans la 1.0) : sessions RetroArch netplay organisées, préréglage figé, enregistrement
   des parties.

**Ce qu'on demande aux joueurs de tournoi** (ils sentent ce que les scripts ne voient pas) :
- exécution et « sensation » : charges, quarts de cercle, liens à 1 image, custom combos, guard crush ;
- signatures du moteur : crouch cancel (SFA3, Upper), infinis connus, glitches célèbres (tengu de Sodom, Valle CC en
  *Alpha 2*) ;
- versions anciennes d'Hyper : ZERO et ZERO 2 « sonnent » et « se jouent » comme la borne ?
- règles : quelles versions, ISM et persos admettre en tournoi (CE-ISM, EX, MAX) ?

**Grille de retour** (modèle d'issue GitHub ; champs obligatoires en gras)

| Champ | Contenu |
|---|---|
| **Build** | identifiant affiché par le cœur (version + empreinte) |
| **Plate-forme** | appareil, système, RetroArch (version), cœur 4:3 ou 16:9 |
| **Réglages** | options du cœur (musique, horloge, difficulté, vitesse, manches), run-ahead |
| **Jeu et mode** | SFA3 / Upper / Hyper ; ARCADE, VERSUS, TRAINING… |
| **Persos** | J1 et J2 : perso, version (ZERO / ZERO 2 / ALPHA / ZERO 3 / EX), ISM ou mode |
| **Ce qui se passe** | description courte, image ou vidéo |
| **Ce qui était attendu, et selon quoi** | arcade, Anthology PS2, guide, SuperCombo, souvenir (préciser) |
| **Reproductible ?** | toujours / parfois / une fois ; étapes |
| Pièces jointes | état de sauvegarde juste avant, enregistrement d'entrées, journal du cœur |
| **Gravité** | S1 plantage, blocage, désynchronisation en ligne ; S2 écart de jeu (coup, dégâts, hitbox, timing) ; S3 son ou image faux ; S4 cosmétique ou suggestion |
| Triage (équipe) | origine : HSFA / jeu d'origine (vu sur PCSX2) / émulateur ; scénario ajouté au corpus (oui / non) |

Chaque retour S1-S2 confirmé devient un **scénario de non-régression** avant sa correction.

### 3.7 P6 — Critères de la « version 1.0 »

Une 1.0 est publiée quand **tous** les points suivants sont vrais sur le build candidat :

1. **Construction** : `hsfa_build.py` reconstruit tout depuis l'ISO seule, deux fois, avec des empreintes
   identiques ; manifeste publié ; refus clair pour un disque inconnu.
2. **SFA3** : non-régression verte (42/42, 133,3 %), 32/32 fins = arcade ±1, RAM typée identique à l'arcade sur
   les zones comparables.
3. **Upper** : 40/40 fins ; SURVIVAL, VERSUS, DRAMATIC, TRAINING ; aucun écart face à PCSX2 sur le corpus.
4. **Hyper** (produit principal, voie B si elle est dans la 1.0) : niveau 1 complet en J1 et J2 sans exception ;
   niveau 2 sans écart non expliqué face à Hyper PS2 ; 40 parcours Arcade jusqu'à la fin ; aucun défaut S1 ouvert.
5. **MAX** (si dans la 1.0) : matrice d'interactions verte ; boîtes conformes aux données MAX.
6. **Son** : voix et cris conformes aux tables arcade (`voix_arcade.tsv`, `cris_arcade.tsv`) ; musique : 216 codes
   vérifiés ou justifiés ; aucun flux en échec ; polyphonie mesurée et documentée.
7. **États** : rechargement exact au bit sur la logique ; écart du son expliqué et corrigé ou borné.
8. **Plates-formes** : niveau 5 vert sur Linux, Windows, Android, ROCKNIX ; ≥ 60 images/s soutenues sur RGB10X en
   combat ; empreintes RAM identiques x86 / ARM.
9. **Bêta** : au moins 4 semaines de bêta ouverte ; zéro S1 ouvert ; S2 ouverts listés et acceptés publiquement.
10. **Documentation** : politique de référence publiée, liste des différences voulues, guide de construction et
    d'installation, notes de version, licences.

Netplay : **critère de la 1.1** si les tests e/f (§3.4) ne sont pas verts au moment de la 1.0, plutôt que de retarder
la 1.0.

### 3.8 P7 — Documentation et distribution propres

- **Aucune donnée de jeu** dans le dépôt ni dans les publications : ni ROM, ni ISO, ni zip de jeu, ni échantillon,
  ni capture de texte protégé (le tableau BradyGames reste hors dépôt). Les cœurs compilés ne contiennent que du code.
- **Pas d'IPS/BPS de ROM** : la ROM traduite est entièrement dérivée du disque ; un patch binaire contiendrait le jeu.
  Le modèle est le bon : **script de construction + patchs de sources** (fork MAME, FBNeo).
- **Empreintes publiées** par version (md5 / SHA-1 des ROM produites et des zips) : chaque utilisateur vérifie sa
  construction ; c'est aussi la base d'une déclaration future dans FBNeo / Fightcade.
- **Licences par composant** : code HSFA en MIT ; patchs FBNeo sous la licence FBNeo (pas de vente, pas de dons) ;
  fork MAME sous la licence de MAME ; `stb_vorbis` domaine public / MIT ; `hsfa_qsound.h` dérivé de `qs_c.cpp`
  (BSD-3-Clause, comme indiqué dans son en-tête) ; crédits (superctr, Valley Bell, Razoola et l'équipe CPS2Shock déjà
  cités par MAME, 0xZERO3 ou dammit si leurs scripts sont adaptés).
- **Documents pour les joueurs** : « Ce que HSFA reproduit » (politique §3.0) ; « Différences voulues » ;
  « Construire depuis votre ISO » ; « Installer » (Android, ROCKNIX, Windows) ; « Signaler un défaut » (grille) ;
  préréglage de tournoi.
- **Notes de version** au format Keep a Changelog (déjà en place), avec l'identifiant de build et le résumé de la
  batterie.
- **Historique Git** : vérification complète avant publication (HANDOFF §144 : adresse e-mail et chemins locaux
  retirés) ou dépôt neuf.

### 3.9 Ordre de marche proposé

| Étape | Contenu | Sort |
|---|---|---|
| 1 | Politique de référence (§3.0), identifiant de build et manifeste (§3.1) ; correction de `coeur-fbneo.md` (QSound) | P0 |
| 2 | Traces dorées dans le cœur (`joue_linux`, `hsfa_run`) et format d'entrées commun ; test d'états (§3.4-e) et recherche de l'écart du son après rechargement | P0-P1 |
| 3 | Oracle PCSX2 : vidages RAM aux points de contrôle, VS CPU ; trancher EX Bison/Sagat et le débordement des ids | P1 |
| 4 | Voie B jusqu'aux 40 fins ; matrice niveau 1 en J1 et J2 | P1 |
| 5 | Matrice des coups (niveau 2) depuis le tableau BradyGames ; extension du test des commandes à Upper et Hyper ; latence | P1 |
| 6 | MAX : intégration puis matrice d'interactions (CFC2) ; profil GBA de `sfa3_support` | P1-P2 |
| 7 | Plates-formes (niveau 5), mesures RGB10X ; empreintes x86 / ARM | P2 |
| 8 | Contacts (Zer0-NexuS, strygo, mainteneurs) ; alpha fermée | P2 |
| 9 | Bêta ouverte ; corpus enrichi des parties de joueurs | P2 |
| 10 | 1.0 ; puis netplay RetroArch (1.1), FBNeo en amont, Fightcade | P3 |

---

## 4. Sources

**Notes de recherche** (`<workspace>/research_notes/Histoire de Street Fighter Alpha/`)
- `07_son.md` §1 (QSound : MAME `qsound.cpp`, `qsoundhle.cpp`, régions de `cps2.cpp`) ; `07_son_verif.md` (corrections
  12 et 14, citations 5 et 10 : Funamizu 32 → 64 Mbit, équipe son de la CFC2).
- `10_bidouilleurs.md` §1-§4 et `10_bidouilleurs_verif.md` (sets Phoenix, clés 0.178, chronologie QSound 0.196 / 0.201 /
  0.203, Zer0-NexuS, strygo et ses sets 8 Mo, SFZ3 Mix / CPS2 Turbo, Challenger's Edition, Training Edition,
  `sfa3_support`, `cps2-hitboxes.lua`, `fbneo-training-mode`, GGPO, Fightcade, licence FBNeo).
- `09_anthology_hyper.md` Q2-Q6 et `09_anthology_hyper_verif.md` (S-ISM, VS contre le CPU, mode VS aléatoire, disque
  japonais, Upper NAOMI et son image de retard, SuperCombo sur l'exécution PS2).
- `06_portages_alpha3_compilations_verif.md` (CFC2 : notes de patch du 7/08 et du 10/09/2025, version anglaise
  construite sur les données japonaises, crouch cancel ; 30th : rollback, version internationale en ligne ;
  Matsumoto sur le choix des versions).
- `08_competition.md` §3, §5 et `08_competition_verif.md` (Fightcade 2, Zero Division, tier list de VER, CE-ISM
  banni, sauvegardes Fightcade).
- `04_zero3_verif.md` (révisions MAME de SFA3, bogues de Karin rev. 1, `sfz3ugd`).
- `12_ja_wikipedia.md` l. 841 (1/60 s), l. 1360 (30th et écran QSound).
- `chapitres_v2/10.md`, `11.md`, `12.md` (synthèse, chronologie du projet, « Octobre 2026, les voisins »).

**Sources primaires citées par ces notes** (ouvertes pendant la recherche)
- MAME : `src/mame/capcom/cps2.cpp`, `src/devices/sound/qsound.cpp`, `qsoundhle.cpp`, `src/mame/sega/naomi.cpp` ;
  whatsnew 0.178, 0.196, 0.201, 0.203 (mamedev.org/releases).
- HBMAME : `src/hbmame/drivers/cps2mis.cpp`, `cps2t.cpp` (github.com/Robbbert/hbmame).
- FBNeo : `src/burn/drv/capcom/d_cps2.cpp`, `qs_c.cpp`, `src/license.txt` (github.com/finalburnneo/FBNeo) ;
  Fightcade : github.com/FightcadeOrg/fightcade-fbneo.
- github.com/Zer0-NexuS/sfz2a-dash-cps2 (README) ; github.com/strygo/arcade-patches (`data/patches.json`) ;
  github.com/originalgrego/sfa3ce ; github.com/0xZERO3/ZERO3TE ; github.com/0xZERO3/sfa3_support ;
  github.com/Jesuszilla/mame-rr-scripts (`cps2-hitboxes.lua`) ; github.com/peon2/fbneo-training-mode ;
  github.com/pond3r/ggpo.
- capcom.co.jp/sound/interview/cfc2_interview/ ; famitsu.com/article/202504/39834 ; famitsu.com/article/202502/32494 ;
  eventhubs.com (notes de patch CFC2 du 6/08 et du 10/09/2025) ; nintendolife.com (9/03/2025) ; 4gamer.net
  (16/05/2025) ; game.watch.impress.co.jp/docs/20010131/zero3.htm ; eurogamer.net (30th, 31/05/2018) ;
  wiki.supercombo.gg (pages *Alpha*, *Alpha 3*, *Hyper Street Fighter Alpha*) ; ja.wikipedia.org
  (ストリートファイターZERO ; ストリートファイターZERO ファイターズ ジェネレーション).

**Dépôt HSFA** (`<workspace>/SFA-Anthology-PS2-mods/`)
- `README.fr.md`, `CHANGELOG.md`, `docs/journal/ETAT-DES-LIEUX.md`, `docs/journal/HANDOFF.md` §135-§161 et §167,
  `docs/journal/SESSION-CLOUD-2026-10-16.md` §4-§6.
- `docs/methodes/oracle-et-non-regression.md`, `docs/methodes/pieges-du-traducteur.md`.
- `docs/architecture/banc-mame.md`, `coeur-fbneo.md`, `memoire-cps2.md`, `traducteur.md`, `voie-b-greffe.md`,
  `ARCHI-Reorganisation-Donnees.md`.
- `docs/reference/sfz2a-dash-cps2.md` ; `docs/rapports/HASARD.md`, `SON-HYPER-ROM.md`, `BUILD.md`,
  `PLAN-VORBIS.md`, `PLAN-PARTITIONS-HYPER.md`, `ECARTS-UPPER.md` ; `patches/fbneo/README.md` ;
  `tools/son-hyper/hsfa_qsound.h`.
