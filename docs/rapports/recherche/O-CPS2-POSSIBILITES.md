# Ce que la CPS-2 permet au 68000, et comment y faire tenir plus (2026-11-10)

Question : inventaire de ce qu'un programme 68000 peut piloter sur une CPS-2, des astuces connues (Capcom ou non), des
limites câblées et des leviers matériels légers, pour faire tenir *Upper* (≥ 9 % au-delà des 32 Mo de ROM graphique,
HANDOFF §49 ; ≈ 5-6 Mo de tuiles manquantes, §115) sur une carte, ou au plus près.

Repères de lecture :
- **[MAME]** lu dans le pilote MAME (`cps2.cpp`, `cps1_v.cpp`, `cps1.cpp`, `qsound.cpp`, `qsoundhle.cpp`, branche master,
  téléchargés le 2026-11-10) ; **[cps2recomp]** lu dans `tmcleroy/cps2recomp` (faits seulement, aucun code repris) ;
  **[jt]** README du cœur FPGA jtcps de jotego ; **[forum]** témoignage de forum, non recoupé ; **[HSFA]** mesure ou
  acquis de ce dépôt.
- **[déduit]** : raisonnement de l'auteur à partir des faits cités, non vérifié sur une carte.
- Sites non joignables depuis cette session (à autoriser pour compléter) : `morphus56k.com`, `wiki.arcadeotaku.com`,
  `petitl.fr` (étude du DL-1827), `misterfpga.org`, `shmups.system11.org`.

## 1. Ce que le 68000 peut piloter

| fonction | registre / mémoire | ce qu'on peut en tirer | source |
|---|---|---|---|
| Programme | `000000-3FFFFF` (4 Mo, chiffré : opcodes déchiffrés, données en clair) | rien au-delà de 4 Mo en ROM | [MAME] `CODE_SIZE 0x400000`, `cps2_base_map` |
| Espace libre du bus | `A00000-EFFFFF` non décodé par la carte | place pour un périphérique ajouté (registre de banque, ROM supplémentaire) sur une carte modifiée ; HSFA y met ses « blocs externes » en émulation | [cps2recomp] `machine.h` (« the CPS-2 board leaves A00000-EFFFFF unused ») ; [HSFA] `reference/adresses.md` |
| RAM de travail | `FF0000-FFFFFF` (64 Ko) | — | [MAME] |
| RAM d'extension | `660000-663FFF` (16 Ko), présente si le bit 14 de `804030` vaut 0 | 16 Ko de plus ; selon jotego, inutilisée par les jeux ordinaires | [MAME] commentaire de `cps2_qsound_volume_r` ; [jt] |
| Liste d'objets | deux banques de `0x2000` octets ; fenêtre `708000-709FFF` (miroir jusqu'à `70FFFF`) = banque cachée, `700000` = banque affichée ; bit 0 de `8040E0` échange | double tampon : on remplit la banque cachée, on échange en vblank ; la carte **recopie** la liste au début du vblank (ligne 240) | [MAME] `cps2_objram_*`, `cps2_objram_latch` ; [cps2recomp] `RunLine` |
| Entrée d'objet | 4 mots : X (bits 0-9 position, 13-15 priorité 0-7), Y (bits 0-9 position, 13-14 = bits 16-17 du code, Y ≥ `8000` = fin de liste), code (16 bits), attributs (0-4 palette, 5 miroir H, 6 miroir V, 7 « offset », 8-11 largeur-1, 12-15 hauteur-1 ; `FF00`+ = fin) | code de tuile sur **18 bits** (262 144 tuiles de 16×16) ; blocs jusqu'à 16×16 tuiles ; un bloc non retourné **reboucle dans sa rangée de 16 codes** ; bits 10-12 de X et Y non lus (cps2recomp marque le bit 12 de X pour ses besoins, « which the board does not read ») | [MAME] `cps2_render_sprites`, `find_last_sprite` ; [cps2recomp] `video.cpp`, `video.h` |
| Registres d'objets | `400000-40000B` : `+4` priorités des plans (4 bits par plan), `+8`/`+A` décalages X/Y (usuellement `40`/`10`) ; `+0`, `+2`, `+6` mal connus | ordre objets/plans réglable par niveau ; le bit 7 d'attribut ajoute le décalage (crédits de *MvC*) | [MAME] constantes `CPS2_OBJ_*`, note « Known Bug List » |
| CPS-A | `804100-80413F` (miroir `800100`) : bases objets/scroll1/2/3/row scroll/palette (÷256), défilements X/Y des trois plans, départ du row scroll (`+20`), contrôle vidéo (`+22` : bit 0 row scroll du plan 2, bits 2-3 plans 2-3, bit 15 retournement) | plusieurs cartes de plans en VRAM, commutables d'une image à l'autre ou en cours d'image | [MAME] `cps1_v.cpp` « CPS-A Registers » |
| Palette | écrire la base palette (`+0A`) déclenche une **copie DMA** des pages activées (CPS-B `+30`, bits 0-5) de la VRAM vers la palette interne ; 6 pages × 512 couleurs (`0xC00` entrées) ; objets 32 palettes, chaque plan 32 palettes ; couleur = luminosité 4 bits + RVB 4 bits | fondus par le quartet de luminosité (de 1/3 à 1 : `(0x0F + 2b) / 0x2D`) ; changer de palette en cours d'image (la copie a lieu à la ligne suivante) **[déduit]** ; coût : 512 mots de DMA par page | [MAME] `cps1_build_palette`, note du registre `+30` ; [cps2recomp] `LineDma`, `TIMING.md` |
| CPS-B | `804140-80417F` : ordre et activation des plans (`+26` : bits 6-13 ordre, 1-3 activation), masques de priorité `+28-+2E`, contrôle palette `+30`, multiplicateur 16×16 (`+40`/`+42` → `+44`/`+46`) | multiplication câblée gratuite | [MAME] `CPS_B_21_DEF`, `cps1_cps_b_r` ; [cps2recomp] `ReadRegister` |
| Interruptions | IRQ2 au début du vblank (ligne 240 sur 262) ; **IRQ4 raster** : deux compteurs de lignes (CPS-B `+10`, `+12`, rechargement manuel au bit 15) et une position horizontale (`+0E`) | effets à mi-écran : changer défilements, ordre des plans, base palette, base d'une carte de plan | [MAME] `raster_scanline`, `cps1_cps_b_w` ; [cps2recomp] `RunLine` |
| Row scroll | plan 2 (16×16) seulement ; table de 1 024 mots en VRAM (base CPS-A `+08`, départ `+20`) | un décalage X par ligne : sols en perspective, vagues, déformations | [MAME] ; [cps2recomp] `DrawScroll` |
| Plans | scroll1 8×8 (code 16 bits), scroll2 16×16 (16 bits), scroll3 32×32 (14 bits) ; cartes 64×64 ; VRAM `900000-92FFFF` | les tuiles de plans sont lues dans **la fenêtre 8-16 Mo** de la ROM graphique | [MAME] `mapper_cps2` (« 20000-3ffff physical ») ; [cps2recomp] « a CPS-2's scroll screens' tiles are in the second 8 MB » |
| Son | RAM partagée QSound `618000-619FFF` (octet bas) ; bit 3 de `804040` libère le Z80 | requêtes au pilote Z80 | [MAME] |
| EEPROM 93C46 | bits de `804040` (données, horloge, sélection) / lecture `804020` | 128 octets non volatils (réglages, scores) | [MAME] `cps2_eeprom_port_w` |
| Liaison | carte « Tournament » (CN7) : USART µPD71051 en `620000`/`620020`, routage `620008` ; présence lue au bit 15 de `804030` | seul *SSF2 Tournament Battle* ; non émulée par MAME | [MAME] `cps2_comm_base_map`, en-tête |
| Volume | `804030` (lecture du volume numérique) | — | [MAME] |

## 2. Astuces employées par les jeux Capcom

| astuce | jeu(x) | comment | source |
|---|---|---|---|
| Effets raster | *SSF2* (décors de Cammy, Dee Jay, T.Hawk), *Marvel Super Heroes* (lave de Blackheart, Chaos Dimension) | IRQ4 : défilements des plans 2-3 et ordre des plans changés en cours d'image (*MSH* : routine `0007B6`, 381 écritures sur un essai) | [MAME] note CPS-B ; [cps2recomp] `NATIVE_VIDEO.md` |
| Row scroll (perspective) | *Vampire Savior* et variantes, *SF2* | table refaite à chaque image d'après la caméra (sol, murs, vague d'un super) | [cps2recomp] `vampire_savior/PROGRESS.md` (`01FDFE`, `rows.cpp`) |
| Clignotement une image sur deux | *Vampire Savior* (flammes de Vanity Paradise, train) | un bit qui bascule chaque image ; les pièces ne sont dessinées qu'une image sur deux : transparence simulée sans matériel | [cps2recomp] `vampire_savior/PROGRESS.md` |
| Ombres | tous les jeux de combat | objets ordinaires dans une palette dédiée (SFA3 : jeu de couleurs `14` ; *Alpha* : `1F`, tuiles `1B7A0-1B7AF`) ; pas de mélange de couleurs matériel | [cps2recomp] `sfa3/PROGRESS.md`, `sfa/PROGRESS.md` |
| Transparence | partout | pen 15 de chaque palette = transparent, pour objets **et** plans (câblé) | [MAME] `prio_transpen(...,15)` ; [cps2recomp] |
| Données cachées en VRAM | *MSH* | les tables de pièces des objets sont rangées dans des zones de VRAM que la carte n'affiche jamais | [cps2recomp] `NATIVE_VIDEO.md` |
| Copie de la liste d'objets | *SSF2T*, *HSF2* | chaque pièce écrite deux fois (objets + copie en VRAM), recopiée en vblank, banque échangée depuis la boucle principale | [cps2recomp] `NATIVE_VIDEO.md` |
| Liste bornée | *Alpha 2* | au plus `0x380` (896) entrées par image, appelées par groupes de priorité | [cps2recomp] `NATIVE_VIDEO.md` |
| Palettes en tampons multiples | famille *Alpha* | plusieurs tampons de palette en VRAM (`90C0..`, `92A0..`…), choix par la base palette en vblank ; fondus en relisant/réécrivant ces tampons | [cps2recomp] `NATIVE_VIDEO.md` |
| Réutilisation de données | *Hyper SF II* (2004) | 32 Mo, en réutilisant les graphismes des épisodes précédents | [HSFA] `N-PARADIGMES-LIMITES-ROM.md` |

## 3. Limites dures

| ressource | limite | vérifié / déduit | source |
|---|---|---|---|
| ROM graphique | **32 Mo** : 8 supports × 32 Mbit ; code d'objet 18 bits × 128 octets = 32 Mo, exactement | vérifié | [MAME] tableau des ROM de la carte B, `cps2_render_sprites` |
| Tuiles de plans | fenêtre de 8 Mo (8-16 Mo de la ROM) ; scroll2 = même format que les objets (16×16, 128 octets), donc partageables **[déduit]** | vérifié (fenêtre) | [MAME] `mapper_cps2` ; [cps2recomp] |
| ROM programme | 4 Mo (8 × 27C4096) | vérifié | [MAME] |
| Échantillons QSound | 8 Mo sur la carte (2 × 32 Mbit : *Alpha 3*, *MvC*…) ; le DSP calcule `banque << 16 | décalage`, banque sur 15 bits (« théoriquement 2 gigaéchantillons ») ; échantillons 8 bits | carte : vérifié ; au-delà de 8 Mo : câblage inconnu | [MAME] `qsound.cpp`, `qsoundhle.cpp` ; [jt] tableau des tailles |
| Voix QSound | 16 voies PCM + 3 voies ADPCM (8 kHz), sortie 24,038 kHz, une commande par période d'échantillon | vérifié | [MAME] `qsound.cpp` |
| Programme Z80 | 32 Ko fixes + 16 banques de 16 Ko (registre `D003`, 4 bits) : 256 Ko ; 2 supports 1 Mbit | vérifié | [MAME] `qsound_banksw_w`, `QSOUND_SIZE 0x50000` |
| Objets | 1 024 entrées par image (chacune jusqu'à 16×16 tuiles) | vérifié | [MAME] `m_cps2_obj_size = 0x2000` |
| Objets par ligne / budget de dessin | **inconnu** : MAME et cps2recomp ne modélisent aucune limite ; les objets sont dessinés une image en retard (tampon d'image) | non vérifié | [MAME] « Sprites are currently lagged by one frame » ; [jt] « the object DMA needs a frame » |
| Palettes à l'écran | 32 palettes de 15 couleurs utiles pour les objets, 32 par plan ; 4 bits par composante | vérifié | [MAME] |
| Taille des objets | 16×16 uniquement, pas de zoom, pas de rotation, pas de 8×8 | vérifié | [MAME] |
| Bus 68000 | 16 MHz, mais un cycle d'attente hors `500000-7FFFFF` et 7-13 % de l'image pris par le DMA vidéo | vérifié (contre jtcps2, pas contre une carte) | [cps2recomp] `TIMING.md`, `ARCADE_ACCURACY.md` |
| Image | 384×224 visibles, 512×262, 59,637 Hz | vérifié | [MAME] `cps1.h` |

## 4. Leviers matériels légers

**Ce qui est établi :**
- Le 68000 (DL-1525 SPA) et toutes les ROM sont **sur la carte B** ; la carte B a des connecteurs pour cartes filles :
  CN5 et CN6 (96 broches), CN7 pour la carte de liaison, qui voit le bus 68000 en `620000`. [MAME] en-tête de `cps2.cpp`.
- Capcom a déjà déporté des ROM graphiques sur des **cartes filles** avec leur propre PAL et des cavaliers : 93661G-2
  (*SFZ2* : PAL « BGSG2B », 4 ROM graphiques sur la fille) ; 93646C-3 (location : 40 supports 27C4096 pour les
  graphismes) ; 00716C-3 (SIMM de flash 29F016 pour les graphismes et le QSound). [MAME] en-tête.
- Les cavaliers de la carte B adaptent les supports à d'autres tailles de ROM. [MAME] en-tête.
- La PAL3 de la carte B est propre à une révision ou un jeu (« BGSB3 » de *SSF2*, la « G-PAL » des cartes plus récentes).
  Sur les cartes « all-in-one » noires, les ROM sont de 64 Mbit et une PAL dédiée choisirait la seconde « page » de
  32 Mbit ; ce point est contesté dans le fil. [forum] arcade-projects (fil 4566).
- Le kit Darksoft remplace programme, graphismes et son par des mémoires rechargées depuis une carte SD et réécrit la clé ;
  il installe une sous-carte sur les supports du programme. Rien de public sur son câblage interne. [forum].

**Ce qui est supposé [déduit] :**
- Les PAL de la carte B décodent les **sélections de puces** (quel support répond pour quelle partie de l'espace de
  32 Mo, selon la taille des ROM), sans traduire les codes de tuiles. Le code d'objet de 18 bits plafonne l'espace vu par
  la vidéo à 32 Mo **quelle que soit la PAL**.
- Une carte B modifiée pourrait quand même afficher plus de 32 Mo **par banques**. Il faudrait un verrou écrit par le
  68000 à une adresse libre (`A00000-EFFFFF`, ou l'espace de CN7), dont les sorties pilotent les bits d'adresse hauts
  d'une grande flash à la place des sélections de puces. Une GAL/CPLD et une flash de 64-128 Mo suffiraient. C'est
  exactement le schéma « emplacement → base de banque » du fork HSFA (§48), en matériel.
  - Limite : la banque vaut pour toute l'image. Il faudrait donc découper la fenêtre de 32 Mo en sous-fenêtres
    (communs fixes, plus un emplacement par personnage et par décor), chacune avec son registre.
  - Non prouvé : le câblage exact des lignes d'adresse graphiques vers CN5/CN6 et vers les supports. Il faut un schéma ou
    une mesure sur carte.
- Le bit 15 du mot Y, que le fork HSFA emploie comme bit 18 du code (§115), est la **marque de fin de liste** sur la
  carte d'après MAME : il ne peut pas servir sur une vraie carte. Les bits 10-12 de X et Y, eux, ne sont lus ni par MAME
  ni par cps2recomp. Rien ne dit que la puce les transmet à la carte B.
- QSound au-delà de 8 Mo : l'adresse calculée par le DSP est assez large, mais le nombre de lignes réellement câblées
  vers les supports n'est pas documenté.

## 5. Pistes classées pour faire tenir plus de graphismes

| # | piste | gain possible | coût | vraie carte ? |
|---|---|---|---|---|
| 1 | **Recensement des tuiles réellement affichées** : journaliser, dans le banc ou le cœur, tous les codes d'objet et de plan dessinés pendant les parties scriptées, toutes les fins et tous les coups. Comparer à la ROM : les tuiles jamais lues sont candidates au retrait. Les SFA3 inutilisées font de la place aux nouvelles d'Upper. | inconnu, **à mesurer** ; c'est la seule piste sans perte qui pourrait couvrir les 9 % | faible (sondes déjà là) ; risque : couverture incomplète, une tuile rare oubliée | oui |
| 2 | Déduplication + redécoupage hors grille de 16 px (déjà mesuré, M) | 4-6 % au plus, 0,4 % pour les miroirs | moyen à fort : réécrire les tables d'images. Les blocs bouclent sur des rangées de 16 codes, donc un redécoupage exige des objets 1×1 ou de nouvelles rangées, ce qui coûte des entrées (1 024 au plus, ~900 utilisées) | oui |
| 3 | Pistes 1 et 2 réunies, plus des sacrifices ciblés (images intermédiaires d'animation, décors en double entre SFA3 et Upper) | de quoi combler le reste | perte de contenu à arbitrer avec l'utilisateur (règle 9) | oui |
| 4 | **Carte B à banques** (verrou + grande flash, § 4) | ×2 ou plus ; le jeu de travail d'un combat suffit (deux personnages, un décor, les communs : à mesurer, N) | fort : conception d'une carte, aucune référence publique ; le schéma logiciel existe déjà (fork) | oui, après fabrication |
| 5 | Panneau (barres, textes) en scroll1 8×8 au lieu d'objets : le panneau de SFA3 est fait d'objets | probablement < 1 % | moyen | oui |
| 6 | Rapiéçage (une image = une autre + quelques tuiles) | non mesuré | fort : tables d'images, objets en plus | oui |
| 7 | Code d'objet élargi (fork MAME 128 Mo, cœur 64 Mo ; précédent *SFZ3 Mix*, 64 Mo dans HBMAME/FBNeo) ; dans jtcps2, élargir le bus graphique | illimité | déjà fait en émulation ; faisable en FPGA (le README de jtcps note déjà des modules de 64 Mo pour les jeux CPS-2 lourds) | non (émulateur / FPGA) |

À exclure : la compression (la vidéo lit la ROM directement, sans RAM de tuiles) ; les tuiles 8×8 pour les objets
(n'existent pas, M) ; les palettes pour faire varier des formes (2,1 % au plus, M) ; les bits libres du mot Y pour
étendre le code sur carte réelle (aucune preuve qu'ils sortent de la puce).

## Sources

- MAME, pilote CPS-2 : [cps2.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/capcom/cps2.cpp),
  [cps1_v.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/capcom/cps1_v.cpp),
  [cps1.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/capcom/cps1.cpp),
  [cps1.h](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/capcom/cps1.h),
  [qsound.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/devices/sound/qsound.cpp),
  [qsoundhle.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/devices/sound/qsoundhle.cpp).
- cps2recomp (dépôt local, lecture seule) : `machine/machine.h`, `machine/machine.cpp`, `machine/romset.h`,
  `video/video.h`, `video/video.cpp`, `docs/TIMING.md`, `docs/ARCADE_ACCURACY.md`, `docs/NATIVE_VIDEO.md`,
  `games/{sfa,sfa3,vampire_savior,msh,...}/PROGRESS.md`.
- jotego, [README de jtcps (tailles des ROM CPS-2, mémoire)](https://raw.githubusercontent.com/jotego/jtcores/master/cores/cps2/README.md).
- [arcade-projects, « CPS2 Black all-in-one conversion »](https://www.arcade-projects.com/threads/cps2-black-all-in-one-conversion-multi.4566/post-64424) ;
  [Darksoft CPS2 Multi (fiche revendeur)](https://paradisearcadeshop.com/products/darksoft-cps2-multi-kit) ;
  [arcade-projects, carte B de SSF2 et Darksoft](https://www.arcade-projects.com/threads/still-not-sure-if-this-b-board-from-super-street-fighter-2-is-compatible-with-darksoft-cps2-multi.6169).
- HSFA : `docs/journal/HANDOFF.md` §48, §49, §115, §116 ; `docs/rapports/recherche/M-REUTILISATION-TUILES.md`,
  `N-PARADIGMES-LIMITES-ROM.md`, `C-TECHNIQUE-METHODE.md` ; `docs/reference/adresses.md`.

## Annexe (2026-11-10) : les connecteurs de la carte B, d'après l'en-tête de `cps2.cpp` (MAME, branche master)
- **CN1-CN4** (96 broches, DIN 41612, sous la carte) : liaison avec la carte A.
- **CN5 / CN6** (96 broches, au-dessus) : cartes filles de ROM. CN6 n'est pas monté sur toutes les cartes B (93646B-3).
  Cartes filles connues :
  - **93661G-2** (*Street Fighter Zero 2*, certaines versions) : 4 ROM graphiques (ROM21-24) sur la fille, une PAL « BGSG2B »,
    16 cavaliers ;
  - **93646C-3** (cartes de location jaunes) : toutes les ROM son et graphiques sur la fille, 40 supports 27C4096 pour les
    graphismes (ROM59-98), 8 pour le son ; plus aucune ROM graphique ni son sur la carte B ;
  - **00716C-3** : six supports SIMM 72 broches portant de la mémoire flash 29F016 (graphismes sur SIMM 1 et 3, QSound sur
    SIMM 5), les mêmes SIMM que la CPS-3 ; MAME ignore pourquoi Capcom les a employés.
  ⇒ **Vérifié** : les bus des ROM graphiques et QSound passent par CN5/CN6, au moins pour les tailles de ces cartes, et
  Capcom remplaçait déjà les ROM de la carte B par une carte fille, y compris en mémoire flash.
- **CN7** (64 broches) : carte de communication du *SSF2 Tournament Battle* (93656D-3 : SRAM 8 Ko, UART D71051, MAX232, PAL
  « SFSRD », EEPROM) ; elle voit le **bus du 68000**. Cela prouve qu'une carte fille peut recevoir des écritures du programme.
- **CN9** (6 broches, cartes récentes) : JTAG, pour reprogrammer les puces maison (clé de chiffrement probablement).

**Piste matérielle précisée (déduite, non prouvée)** : une carte fille sur CN5/CN6 portant une grande mémoire flash (comme
00716C-3), plus une liaison au bus 68000 (par CN7, comme la carte de communication) pour un registre de banques écrit au
changement de combat. Le programme et les puces de Capcom resteraient d'origine. Inconnu décisif : quelles lignes d'adresse
graphiques arrivent réellement sur CN5/CN6 (toutes, jusqu'à 32 Mo, ou seulement celles des supports concernés). Source à
consulter : le relevé communautaire « CPS2 B-Board Complete Wiring List » (arcade-projects, fil 9291), non lisible depuis la
session. Précédent proche : le multi CPS-2 de Darksoft (flash chargée depuis une carte SD), qui se branche toutefois sur
les supports de ROM de la carte B, pas sur CN5/CN6.

### Brochage vérifié (2026-11-10) : relevé « CPS2 B-Board Wiring » de WydD (Loïc Petit), cartes B4 et B6
Source : tableur public lié depuis arcade-projects (fil 9291), onglets `Readme`, `Wiring`, `CN3`, `CN4`, `CN7` ; schéma
complet rétro-ingénieré par le même auteur : gitlab.com/loic.petit/cps2-reverse (non lu). Faits seulement, rien de copié.

- **« CN5 est une copie de CN3, CN6 une copie de CN4 »** ; « CN5/6 servent à déporter les ROM ; la PAL3 (9J) choisit la
  ROM active » (onglet `Readme`).
- **CN3 + CN4 (donc CN5 + CN6) portent tout le bus graphique** :
  - données des quatre paires de ROM graphiques (13/14, 15/16, 17/18, 19/20), Q0-Q15 chacune : le bus de 64 bits complet
    vers la puce DL-2027 (CGD) ;
  - adresses A0-A19 (A20 par cavalier) sorties de la DL-1927 (CGA), deux bus (paires 13-16 et 17-20) ;
  - les bits d'adresse hauts de la CGA qui entrent dans la PAL 9J (sélection des puces), et la validation de sortie /G ;
  - en plus : adresses de la ROM QSound (11/12) et adresses / données du programme son Z80 (ROM 1-2).
  ⇒ une carte fille sur CN5/CN6 voit **toute** la fenêtre graphique de 32 Mo (8 puces × 32 Mbit) et peut remplacer toutes les
  ROM graphiques, comme le fait la 93646C-3 de Capcom.
- **CN7 porte le bus du 68000** : seize lignes de données passant par des tampons LS245, des lignes d'adresse, des signaux de
  contrôle reliés aux puces DL-1727 (MIF) et DL-1827 (CIF), et l'EEPROM. Une carte fille peut donc y recevoir les écritures du
  programme (c'est ce que fait la carte de communication de Capcom).
- Limite inchangée : la CGA ne produit pas d'adresse au-delà de la fenêtre de 32 Mo ; tout supplément passe par des banques.

**Conception qui en découle (déduite, faisable sur le papier)** : une carte fille branchée sur CN5/CN6 **et** CN7, portant
une mémoire flash ou SRAM de 64-128 Mo et un petit circuit logique (CPLD). Le 68000 écrit, à une adresse libre vue par CN7,
des registres « emplacement → banque » ; le CPLD découpe la fenêtre de 32 Mo en emplacements (éléments communs, personnage 1,
personnage 2, décor…) et ajoute à chaque adresse la base de la banque choisie. C'est le schéma de banques du fork HSFA (§48)
en matériel, avec le même programme. Points à valider : temps d'accès de la mémoire face au rythme de lecture de la CGA (les
SIMM flash 29F016 de la 00716C-3 prouvent qu'une flash convient), place mécanique dans le boîtier, alimentation.

### Émulateurs et cps2recomp face à une carte fille à banques (2026-11-10)
- **MAME / FBNeo** : ils ne simulent pas les connecteurs, seulement l'espace de ROM vu par la puce graphique. Les cartes filles
  de Capcom sont donc transparentes (*Progear*, graphismes sur SIMM, est une simple liste de fichiers). Une carte fille à
  banques **nouvelle** n'existe pour aucun des deux : il faudrait y ajouter le registre de banques, comme dans le cœur HSFA. Le
  MAME officiel s'en tient au matériel d'époque ; la place naturelle serait HBMAME (hacks et homebrew), FBNeo parfois, ou notre
  cœur. Règle à tenir si la carte se fait : même adresse et même format de registre dans la carte et dans l'émulateur, pour que
  le même programme tourne partout.
- **cps2recomp (tmcleroy)** : aucune mention de CN5/CN6/CN7 ni des cartes filles ; il note seulement que `A00000-EFFFFF` est
  libre (`machine/machine.h`). Pour *Vampire Savior Definitive* (Donovan, Phobos, Pyron tirés de *Vampire Savior 2*), il place le
  second jeu entier à `A00000` (`game.cfg` : `extra_set`, `extra_base`), ajoute un second circuit son (`machine/sound_board.h`),
  et choisit pour chaque objet ou tuile de décor la réserve de graphismes à employer **en devinant** : si le programme du second
  jeu vient d'être lu comme données juste avant l'écriture de l'entrée (`objectsFromExtra`, `scrollFromExtra`). Même principe
  que nos banques (deux réserves de tuiles et un aiguillage), mais aiguillage déduit du comportement, purement logiciel et non
  transposable sur une carte ; le registre explicite du fork HSFA s'y prête mieux.

### Note (2026-11-12) : article de morphus56k, « CPS2 maximum ROM expansion » (lu le 12/11, mis à jour par son auteur le 27/07/2026)
- Ses chiffres « 128 Mo de graphismes / 16 Mo de son » sont la TAILLE DES FICHIERS d'un hack de *MvC* (8 puces × 16 Mo,
  2 × 8 Mo), pas de l'espace adressable : l'auteur corrige lui-même sa première version (« 148 Mo adressables » faux). Sur
  MAME d'origine et sur une vraie carte, la fenêtre reste 32 Mo / 8 Mo ; il atteint 64 Mo de graphismes et 16 Mo de son
  avec un cœur FBNeo modifié (bit 12 de Y reporté sur le bit 18 du code, comme le 19e bit du fork HSFA).
- Programme : 4 Mo au plus ; *MvC* et *Alpha 3* les remplissent déjà (il ne reste que quelques blocs libres).
- Désaccord à trancher : il donne au DSP QSound un registre de banque de 8 bits (16 Mo adressables), cette fiche (ligne
  « Échantillons QSound ») 15 bits d'après MAME. Sans effet pratique : la carte câble 8 Mo.
- Rien sur CN5 / CN6 / CN7, les cartes filles ni les kits à carte SD.
