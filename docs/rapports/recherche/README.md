# Ce que la recherche du livre apporte au projet

Version du 2026-10-20. La recherche documentaire faite pour le livre « Street Fighter Alpha — Histoire d'une
renaissance » (11 axes, sources anglaises et japonaises, presse d'époque, code de MAME / FBNeo / HBMAME, guide
officiel BradyGames de l'Anthology) a été relue sous l'angle du projet. Trois fiches détaillées, chacune sourcée et
avec un niveau de confiance par fait :

| Fiche | Contenu |
|---|---|
| [A — Personnages cachés et modes secrets](A-PERSOS-CACHES.md) | commandes exactes jeu par jeu (arcade, CPS Changer, consoles, Anthology, Hyper), présence dans Hyper, procédure de test avec les outils du dépôt, 13 conflits de sources, 12 tests prioritaires |
| [B — Révisions, bugs, différences](B-REVISIONS-BUGS.md) | révisions datées de chaque jeu et ce qu'elles changent, interrupteurs de révision de l'Anthology, différences Japon / export, Zero 3 → Upper → MAX → CFC2, sondes de version pour Hyper, 7 actions priorisées |
| [C — Technique et méthode](C-TECHNIQUE-METHODE.md) | limites CPS-2 et place de HSFA, émulation QSound, sets de fans dans MAME / HBMAME / FBNeo, netplay, outils communautaires, stratégie de solidité P0-P7, critères de la 1.0, distribution |
| [D — Sondes lancées](D-SONDES.md) | mesures du 2026-10-20 dans le cœur : modes d'Hyper, test CFC2 sur Upper + MAX (Head Press juste, Skull Diver qui rate Sakura et Ingrid), matrice des coups Hyper contre arcade, cause du Killer Bee Assault (aide `roxr`, `EXG`, `BCLR`) |
| [E — Coups des persos MAX](E-COUPS-MAX.md) | listes de coups d'Eagle, Maki, Yun et Ingrid selon les wikis (GBA, PSP, CFE, CFC2), désaccords d'ISM à trancher dans les données PSP, la version MAX elle-même ; recherche du 2026-10-26 |
| [F — Prototypes et projets voisins](F-PROTOS-PROJETS.md) | aucun autre build avec débogage (CvS2, CFE, lignée de MAX) ; projet Dreamcast d'irnutsmurt (persos MAX recompilés depuis la PSP, ~30 adresses concordantes avec l'index) ; afficheurs de boîtes CvS2/CFE ; ordre de marche pour la session MAX ; 2026-10-26 |
| [G — Méthode Capcom des persos MAX](G-METHODE-CAPCOM-MAX.md) | préfixes CvS2 / CFE (Eagle pl23, Maki pl24, Yun pl2c, Ingrid pl22), convention de découpage Capcom (atck, special_ck, spN → phases spNM, nml / sit / jatck, tirs pshl, effets pls), 409 appariements avec les fonctions PSP, ce que les noms disent des défauts de Yun et d'Ingrid ; 2026-10-27 |

Les premières sondes ont été lancées : [D — Sondes](D-SONDES.md) (Mazi, S-ISM rose, Bison en S-ISM rouge, test CFC2
sur Upper + MAX, matrice des coups Hyper contre arcade : 24 écarts, dont le Killer Bee Assault de Cammy, cause trouvée et prouvée au banc, D §4). Le reste, ce sont des protocoles. Aucune donnée de jeu dans le dépôt ; le guide BradyGames reste
hors dépôt (texte protégé), seules ses commandes sont citées avec la page.

## 1. Les découvertes qui changent quelque chose

1. **L'oracle SFA3 n'est pas celui de l'Anthology.** Le guide (p. 3) : *Alpha 3* n'offre que les révisions 98/06/29
   et 98/07/27 (défaut). La 980904 de `sfa3ud` n'y est pas. Et la conclusion du §96 (« code = USA 980904 ») n'est pas
   prouvée : `revision.py` ne compare que les ROM 03-04, régionales ; il oppose USA et Japon, pas les révisions
   (B §3). À refaire Japon contre Japon sur les ROM 05-10.
2. **Sens des quatre S-ISM SHADALOO** (A §9.4-9.5), recoupé avec les tables d'animations du dépôt : curseur 4 = A
   (rouge : Classic, Final Bison, coups des *Vs.*), 5 = B (bleu : parade, super cancel), 6 = C (vert : chaînes, garde
   repoussante, alpha counter gratuit), 7 = D (rose : les 12 persos de *SF2'*). `$15C = $80` sur Bison en curseur 4
   serait Final Bison ; `$122` serait la S-ISM elle-même (le test « sans effet » de SON-HYPER §2.3 est à refaire en
   S-ISM réelle).
3. **Les EX Bison / Sagat ZERO 2 (`$58`/`$59`) « en morceaux » et `$5A`-`$5C`, `$5E` sont très probablement des
   défauts du jeu PS2** : ces versions n'ont jamais existé dans l'*Alpha 2* d'arcade (elles arrivent avec *Zero 2
   Alpha*). À confirmer sur PCSX2 avant tout correctif (A §11.1-4, B §7).
4. **EX Balrog `$25` = le Balrog de l'arcade *Zero 3*** (« EXバイソン ») : oracle direct `sfa3ud` (A §9.3).
5. **MAX : un test tout fait.** La *Capcom Fighting Collection 2* a dû corriger en septembre 2025 le Head Press et le
   Skull Diver de Bison et la Sardine Beach Special de R. Mika, qui ne touchaient pas Eagle, Maki, Yun et Ingrid. Cela
   rejoint la table de Bison par adversaire d'ECARTS-UPPER (`0x433E50`, 3 × 40) : à étendre avant MAX en `$26-$29`
   (B §5.3, C §0-6).
6. **QSound de FBNeo** : ce n'est pas un QSound « simplifié » (erreur corrigée dans `coeur-fbneo.md`) mais l'émulation
   de superctr, déduite du code du DSP ; MAME émule le DSP depuis la 0.196. Conséquence : son comparé au bit près dans
   une même implémentation, par tolérance entre fork et cœur (C §1.2).
7. **Projets cousins et contacts.** Zer0-NexuS (*SFZ2A Dash* 1.2.1, déjà dans HBMAME et FBNeo) a extrait les voix de
   Cammy de `X_0333` : c'est notre Cammy ALPHA muette. strygo publie des « PS2 Backport » à région QSound de 8 Mo
   (« HBMAME et MiSTer seulement »). FBNeo et HBMAME acceptent déjà une CPS-2 fictive (« CPS2 Turbo » de *Zero 3
   Mix*) : c'est la voie réaliste vers FBNeo officiel puis Fightcade (C §1.4).
8. **Un banc à trois voies existe** : `sfa3_support` (0xZERO3) lit RAM et boîtes de SFA3 sur l'arcade, sur PS2
   (PCSX2) et sur l'*Upper* GBA. HSFA reproduisant la vue mémoire PS2, il peut servir d'oracle arcade / PS2 / HSFA
   (C §1.6).
9. **Différences régionales qui touchent le jeu** : CPU, dégâts à deux joueurs, réglages d'usine (strygo), 825 répliques
   de victoire japonaises contre 8 génériques à l'export, sang rouge « Regulation », musique de la Dramatic Battle
   (JASRAC), noms Vega / Bison / Balrog. À trancher pour la voie B (B §4).
10. **Pièges d'outillage** : `.m4`-`.m7` n'ont pas le même sens dans `tournee.h` et dans `tournee_hyper.lua` ; le
    journal `CHOIX` affiche des octets en numérotation 68K sous des libellés PS2 (A §0.4, §1).

## 2. Les tests à lancer d'abord

Personnages et modes (A §12) et révisions (B §10), fusionnés et dans l'ordre d'utilité :

| # | Test | Où | Ce qu'il tranche |
|---|---|---|---|
| 1 | `revision.py` Japon contre Japon (980629 / 980727 / 980904) sur les ROM 05-10 | statique | quelle révision suit la traduction SFA3 |
| 2 | Juni / Juli : direction de sélection, lecture de `$FF8502` | `sfa3ud` | conflit n° 1 des sources |
| 3 | Final Bison par S-ISM rouge : `$15C` (68K) = `$80`, sprite | cœur, fork, `sfa3ud` | sens des S-ISM ; `$15C = $80` vu, rien de visible (D §1) |
| 4 | Parade, garde repoussante, alpha counter gratuit, absence de super en rose | cœur, `HSFA_GESTES` | effets des S-ISM au-delà de la sélection |
| 5 | `$58`/`$59`, roulette, garde auto ZERO, Alpha Counter ALPHA | PCSX2 | défaut de Capcom ou de traduction |
| 6 | Inventaire CUSTOMIZE / `$BB` (`ro3`, `ro5`, `ro9`) et les 18 lignes de `ro2` | statique | ce que la traduction applique par défaut |
| 7 | Mazi : une manche perdue = défaite | cœur | **fait** : confirmé (D §1) |
| 8 | EX Balrog contre Balrog d'arcade | cœur + `sfa3ud` | fidélité de `$25` |
| 9 | Diff des données d'attaque `ro3` / `ro5`, Tatsumaki de Ryu comme témoin | statique | équilibrage d'Upper, jamais publié |
| 10 | Sondes de version d'Hyper (Sodom imparable, Soul Illusion, Adon 960430, bugs de Karin…) | PCSX2 + traduction | quelle révision chaque version d'Hyper reproduit |
| 11 | Random Battle (`0x98DA0`), générique STAFF (R1 + OPTION ?), S-ISM dans Upper | cœur | fonctions cachées non encore vues |
| 12 | Déblocage SFA3 par semaines, EEPROM vierge | `sfa3ud` | état de `ro3` |

## 3. Pour une version solide

Résumé de C §3 (détail, critères chiffrés et ordre de marche dans la fiche) :

- **P0** — écrire une politique de référence aspect par aspect (arcade, Hyper PS2 ou amélioration HSFA voulue) ;
  identifiant de build et manifeste ; traces dorées dans le cœur (`joue_linux`, `hsfa_run`) avec un format d'entrées
  commun aux trois bancs ; élucider l'écart du son après rechargement d'état (bloquant pour tout netplay).
- **P1** — oracles : PCSX2 (vidages RAM aux points de contrôle, VS CPU contre CPU), NAOMI `sfz3ugd` pour *Upper*
  (mesurer l'éventuel retard d'une image avant d'en parler) ; voie B jusqu'aux 40 fins ; matrices en 5 niveaux, dont
  les coups générés depuis le tableau BradyGames (déjà vérifié contre SuperCombo).
- **P2** — MAX avec la matrice d'interactions de la CFC2 ; plates-formes (Linux, Windows, Android, ROCKNIX, 60 i/s sur
  RGB10X, empreintes RAM x86 = ARM) ; contacts (Zer0-NexuS, strygo, mainteneurs) ; alpha fermée.
- **P3** — bêta ouverte en trois phases (grille de retour S1-S4, communauté Zero Division / Fightcade) ; 1.0 ; netplay
  en 1.1 si les tests d'états ne sont pas verts.
- **Distribution** — script de construction depuis l'ISO de l'utilisateur et patchs de sources, jamais d'IPS de ROM ;
  empreintes publiées ; licences par composant (la licence FBNeo interdit vente et appels aux dons) ; historique Git
  vérifié avant toute publication.

## 4. Apports du 2026-10-25 (pages TCRF et MobyGames fournies par l'utilisateur)

Ce qui touche le projet. Détail hors dépôt, dans les notes du livre.

- **Bug de Karin (projection Yashiro Kuzushi qui vide la barre de vie)** : en mode **Saikyo**, présent dans toutes les
  versions **avant la 980904**. Les deux révisions de l'Anthology (980629, 980727) l'ont donc. C'est une sonde de
  révision toute faite pour SFA3 et pour les ZERO 3 d'Upper et d'Hyper (test 10 de la synthèse).
- **Death Cross Dance de Juni et Juli** en Saikyo (Dramatic Battle) : 80 % de dégâts d'un coup avant la 980904. C'est
  une deuxième sonde.
- **Vitesse par défaut de SFA3 selon la région** : Turbo 1 au Japon, Turbo 2 aux États-Unis, au Brésil et en Amérique
  hispanique, Free 1 en Asie et en Europe. L'oracle `sfa3` (Euro) démarre donc en Free 1. La matrice compare des
  dégâts, ce qui n'est pas affecté, mais une comparaison image par image devra imposer la même vitesse.
- **Réglage « Regulation »** (sang) : actif par défaut sauf au Japon, et repris par l'Anthology. Il est à exposer dans
  les options du cœur si l'on veut le sang de l'arcade japonaise.
- **SFA1** : menu de test des personnages par FF8001 = `0A` dans le menu de test (arcade ; à essayer sur la
  traduction).
- **SFA2** : Evil Ryu a ses dialogues et sa fin dans l'arcade d'export, mais aucun portage localisé ne les reprend.
  C'est à vérifier dans Hyper (version d'Evil Ryu en ZERO 2).
- **Générique de l'Anthology** (MobyGames) : directeur et programmeur Nobuaki Minomiya, productrice Hitomi Nishimoto,
  producteur exécutif Keiji Inafune, planning Motohide Eshiro, son Hiroaki Kondo, Seiko Kobuchi et Ryoji Yamamoto.
  Développeur : Capcom Production Studio 2.
- **Musiques laissées sur le disque** (`X_DATA` / ADX) : *Super Puzzle Fighter II Turbo* au complet, *Pocket Fighter*
  PS/Saturn, « Theme of Chun-Li » de *Marvel vs. Capcom*, « Killing Moon » de *3rd Strike*.

## 5. Apports du 2026-10-26 (persos MAX, exécutables de CvS2 et de CFE)

- **Coups des quatre persos MAX** : [E-COUPS-MAX.md](E-COUPS-MAX.md). Eagle, Maki et Yun sont ceux de *CvS2* (Yun
  n'est pas celui de *3rd Strike* : Senkyutai, pas de Genei-Jin) ; Ingrid est celle de *Capcom Fighting Jam*. Les
  wikis se contredisent sur l'ISM de plusieurs coups (Eagle : Canterbury Blue, St. Andrew's Green, Union Jack
  Platinum ; Yun : Tetsuzankou, Senkyutai ; Ingrid : Sun Delta, Wrap Around) et sur la vitalité perdue par le
  Reppukyaku de Maki : les données PSP ou l'oracle PPSSPP tranchent. Aucune frame data SFA3 publiée. Les tables par
  id adverse que le rapport met en tête sont déjà couvertes par `docs/rapports/AUDIT-TABLES-ID.md` (§174).
- **Exécutables PS2 fournis par l'utilisateur** (hors dépôt) :

  | Exécutable | Jeu | md5 | Contenu |
  |---|---|---|---|
  | `SLUS_202.46` | *Capcom vs. SNK 2* (US) | `c3d7795d6609aa66d6c39deb45e6cfdd` | `.symtab` : 26 599 symboles, pas de débogage |
  | `SLPM_650.47` | *Capcom vs. SNK 2* (JP) | `d6028a6e2260ad826e5a67e48ec8b7f8` | `.symtab` : 26 693 symboles, pas de débogage ; en plus : installation sur disque dur (`Hdd_*`) |
  | `SLPM_650.47` (préversion du 2001-07-24) | *Capcom vs. SNK 2* (JP, bêta) | `b20cf51e1de4c20194d5366d5ffa03a0` | `.symtab` : 26 750 symboles, pas de débogage ; en plus : affichages de mise au point (`flDebug*`, `fps_*`) ; routines des persos inchangées |
  | GameCube `GEOP08` (EU, ISO) | *CvS2 EO* | — | liste des fichiers lue à distance : **aucun `.map`** ; un module REL par perso (`pl23.rel` Eagle, `pl24.rel` Maki, `pl2c.rel` Yun), sans noms ; `snk2.str` ne donne que les chemins des modules (`D:\NGC\AcrSDK Rel1.0\snk2pal\...`), le même kit « AcrSDK » que les sources de CFE (`E:\jam\acrsdk\`) ; un dossier `ps2/` reste sur le disque |
  | GameCube `GEOJ08` Rev 1 et démo de magasin `DEOJ08` (JP, RVZ lus avec `nodtool`) | *CvS2 EO* | — | **aucun `.map` non plus**. La démo garde en clair le dossier de travail `ps2/work/` : par perso `plXX_hit.bin` (boîtes), `plXX_tbl.bin`, `plXX_fac.bin`, `plXXpak.bin`, IA `emXX_dat.bin`, `edit_pXX.bin`, et `filedef.txt`, la liste ordonnée des fichiers empaquetés dans les AFS (noms des entrées des archives du jeu du commerce) |
  | `SLUS_209.50` | *Capcom Fighting Evolution* (US ; identique à l'octet à celui de la préversion « Review » du 2004-09-29) | `ed206e8cdcd996e76f9a6e17afca6b9e` | `.symtab` : 15 663 symboles, **DWARF 1 complet** (`.debug`, `.line`) |

  - *CvS2* : ids `EAG` `$23`, `MAK` `$24`, `YUN` `$2C` (table des noms courts). Routines nommées par perso
    (`plXX_appear`, `nage`, `nml_p/k`, `sit_p/k`, `sp0`…`spa` avec un aiguillage par coup, `special_ck`, `win`,
    `*_rate`) et vérifications de commandes (`cmd_hayagake_ck`, `cmd_reppu_ck`, `cmd_hiten_ck`).
  - *CFE* : Ingrid = `pl22` (`chrdef22.c`) : spéciaux `sp0`…`spa`, `atemi_set` (Sun Upper / Sun Lower), projectiles
    `pshl22_00-02`, IA `em22_special`. Surtout, **la structure de travail du joueur `_PlayerWork_` est nommée** :
    1 472 octets, 430 champs avec décalages (`piyo_*` étourdissement, `oricom_*` Original Combo, `gc_*` Guard Cancel
    = ZERO Counter, `pl_ism_flag`, `sp_gauge`, `atemi_req`, `em_*` IA du CPU…), plus `_work_struct_` (objets),
    `_hit_work_struct_` et `SysAllWork`. Lecture : `tools/sondes-recherche/dwarf1.py`.
  - Pistes, non essayées : (1) nommer les champs connus du travail joueur de SFA3 (`re/`) avec le vocabulaire de
    Capcom (les décalages ne se transposent pas : C 32 bits) ; (2) l'EBOOT de MAX est aussi du C MIPS : une
    comparaison de forme avec *CvS2* (Eagle, Maki, Yun) et *CFE* (Ingrid) pourrait nommer ses fonctions `psp_`.
- **Prototypes et projets voisins** : [F-PROTOS-PROJETS.md](F-PROTOS-PROJETS.md). À lire d'abord par la session MAX :
  le projet Dreamcast `irnutsmurt/Street-Alpha-3-Dreamcast-Recomp` (GPL-3 : reprendre les faits et les adresses, pas
  le code) recompile les quatre persos depuis l'EBOOT US de MAX ; ses adresses concordent avec `re/connaissances/max_psp.tsv`
  et y ajoutent l'IA du CPU et l'octet aléatoire ; deux rôles divergent (`0x67B1C`, `0x1D044`), à trancher à l'oracle
  PPSSPP. Défaut à mettre au banc MAX : en Final Battle, la mauvaise fin d'Evil Ryu affiche le texte de Birdie (PSP et
  CFC2, TCRF).
- **AcrSDK** (kit maison de Capcom des portages PS2 / GameCube : fonctions `fl…`, son `CapSndEng`) : attesté dans
  CFE (DWARF), *CvS2 EO* GameCube (chemins) et *Street Fighter Anniversary Collection*, dont le module *3rd Strike*
  est reconstitué par la décompilation publique `crowded-street/3s-decomp` (arborescence `AcrSDK/common`, `ps2`,
  `MiddleWare`). Piste, non essayée : si l'exécutable PS2 de l'Anthology (2006) repose sur le même kit, ces noms
  pourraient nommer sa couche d'exécution (rendu, manettes, mémoire, son) ; à vérifier en cherchant `flPS2`,
  `CapSndEng`, `acrmw` dans l'ELF de l'Anthology. Aucune trace publique d'un accès extérieur au kit.

