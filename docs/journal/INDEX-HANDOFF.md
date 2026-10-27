# Index thématique de `docs/journal/HANDOFF.md`

> Journal indexé : `docs/journal/HANDOFF.md` (5 078 lignes, état du 2026-10-24, jusqu'à §172). Les sections §116 à §172
> ont une ligne chacune au §13 ; numéros de ligne recalés le 2026-10-24.
> Les numéros de ligne renvoient aux **titres** de section (`sed -n 'L,+40p' HANDOFF.md`, ou `Read` avec `offset=L`).
> ⚠ Ils changent dès qu'on insère du texte au-dessus. Pour les recalculer : `grep -n '^#' HANDOFF.md`.

## 0. Lire les numéros de section sans se tromper

Le journal mélange **trois séries de numéros**. Un « §5 » peut désigner trois sections différentes.

| Notation dans cet index | Série | Lignes | Remarque |
|---|---|---|---|
| **R§0 … R§8** (+ R§6bis) | chapitres « racine » `## N.` | 13–617 | les plus anciens ; ordre 0,1,2,3,4,5,**8**,6,6bis,7 ; beaucoup sont **dépassés** |
| **C1 … C5** | chapitre « Carte MIPS↔68K… » (l. 618), `### N.` | 620–713 | métrique et impasses de la carte |
| **§1 … §172** | chapitre « Recensement du traducteur… » (l. 715), puis « Assembleur… » (l. 1048) | 717–5078 | **série canonique** : §1-§21 puis §22-§172 sans rupture. Les renvois « §NN » du journal et de la mémoire (≥ 22) suivent cette série |

La ligne 1543 commence par `#imm,…` : ce n'est pas un titre (faux positif de `grep '^#'`).

Légende : ⛔ = **dépassé** (lire la section qui corrige) · ⭐ = section clé · 🔓 = question encore ouverte.

---

## 1. Traducteur MIPS → 68000 : idiomes et correctifs

### 1.1 Fondations (comprendre le recompilateur)
| Section | Ligne | Résumé |
|---|---|---|
| ⭐ R§1 | 30 | L'Anthology est une **recompilation statique** 68K→MIPS ; banc de registres 68K dans le scratchpad. ⛔ la table de correspondance des registres y est **fausse** (voir R§5 l.264, §11, §53) |
| R§5 | 151 | Grammaire du recompilateur (dsll32/dsra32 = extension, RES, branchements) ; ancre `MIPS 0x201fa8 ↔ 68K 0x9350` |
| R§5 « Correction du mapping » | 264 | ⭐ `0x1124` = D0 (et non D1) : A0-A7 = `0x1100-0x111C`, D0-D7 = `0x1124-0x1140` |
| R§5 « Bug à ne pas refaire » | 274 | invalider le dictionnaire des `lui` quand un registre est réécrit |
| R§5 « LOSSY » | 302 | `CLR.B` et `MOVE.B #0` donnent le même MIPS : 100 % d'identité impossible. ⛔ le choix « MOVE #0 plutôt que CLR » est renversé au §37 |
| R§5 « Base d'exécution » | 320 | ⛔ `0x1f0008` est faux → `0x1f0000` (§5, l.757) |
| R§5 « Couverture 99 % » | 344 | ⛔ ne valait que sur 12 blocs choisis ; réel 25,8 % au §1 |
| R§5 « Tables de données » | 359 | on génère sa propre disposition : tables de valeurs copiées, tables de pointeurs réécrites |
| R§5 « Chaîne complète » / « Architecture » | 384 / 405 | traducteur → assembleur 2 passes → octets 68K ; plan d'ensemble |
| §1 | 717 | `census.py` : recensement réel des effets traduits (25,8 % au départ) |
| §4 | 749 | bornes de code lues dans l'en-tête `MWo3` (`mips.code_bounds`) |
| ⭐ §5 | 757 | base d'exécution = **`0x1f0000`** |
| §6 | 767 | les « stubs » sont des veneers 68K (`JSR x ; JMP y`) ; appel terminal = `JMP` |
| §9 | 807 | appels / appels terminaux / RTS cohérents avec la ROM |
| ⭐ §10 | 840 | les cases An contiennent des **adresses hôtes PS2** ; idiome de conversion `MOVEA` (`+0x900000`), `movea_fixup` |
| ⭐ §11 | 860 | `0x1150` RES (Z et N) ; **`0x1158` = retenue C** (pas N) |
| §14 | 902 | `CMP`/`CMPI` ; instantané des sources avant invalidation |
| §15 | 920 | ⭐ aiguillage d'état Capcom `MOVE.W tbl(PC,D0.W),D1 ; JMP tbl(PC,D1.W)` reconstruit ; longueur des tables bornée par la suivante référencée |
| ⭐ §16 | 952 | zone de code = **Z80 (`0x20..0x22b00`) puis 68000 (`0x22b00..`)** |
| §17, §19 | 966, 993 | tables de valeurs indexées, opérations vers Dn, `SWAP` |
| §20 | 1007 | 2e variante CMP/SUB : drapeaux exacts (N⊕V → `BLT/BGE/BGT/BLE`) |
| ⭐ §21 | 1025 | carte des zones : code d'origine / code **ajouté** par l'Anthology (`hooks.py`) — à exclure des validations |
| §52 | 1978 | Hyper (et une partie d'Upper) = recompilateur **plus récent** (`full_flags_block`) |
| ⭐ §53 | 1993 | registres supplémentaires **A8 = `0x1120`**, **D8 = `0x1144`**, `0x114C` pile privée, `0x1154` X ?, `0x1158` C |
| §54 | 2017 | A8/D8 par « registre prêté » (`extra_regs.py`, `EXTRA_REGS=0` pour couper) |

### 1.2 Idiomes ajoutés (chronologique)
| Section | Ligne | Résumé |
|---|---|---|
| §2, §3 | 729, 739 | A5 généralisé à tout An ; idiomes sur Dn ; invalidation `dest_reg` |
| §36 | 1414 | `MOVEQ`, décalages, `NEG`, forme `(An)` (92,6 %) |
| §37 | 1431 | `CLR`, Bcc long inversé refusionné, aiguillage en appel (`diverge.py`) |
| §39 | 1482 | longs 32 bits, tables de longs, `MOVEA.L d16(An)`, indexé `d8(An,Dn)` |
| §40–§42 | 1501–1553 | `lui+ori`, `NEG` mémoire, absolu `(xxx).L`, `CMPA`, `EXG` ; valeurs suivies à travers la pile MIPS |
| §43 | 1570 | grande passe (97,5 %) ; `0x1144` = compteur de boucle ; règle « champs arithmétiques natifs / champs d'état octets inversés » |
| §61 | 2233 | pointeurs de code, tables `BRA.S`, `ROR.W #8` vers mémoire, `TST` octet indexé |
| §63 | 2316 | `BRA` (`beq zero,zero`), réalignement `(An+3)&~3`, tables partagées, tableaux de structures (forme absolue), conversion des pointeurs à l'exécution |
| §64–§66 | 2366–2435 | retours partagés (3 030), `v0` natif supposé nul, `LEA T(PC,Dn)`, flux `(An)+`, octet indexé impair, drapeaux rendus à l'appelant |
| §67–§68 | 2466–2485 | `MOVEA.L T(PC,Dn),An`, `EXT.W/EXT.L` (274), `swl/swr`, `MOVE.L An,d(Am)`, tables à trous |
| §70–§71 | 2530–2556 | octet lu via `lh` ; compteur demi-mot comparé en octet ; `JSR (An)` ; `Bcc.W` hors de portée |
| §72–§74 | 2569–2623 | pile privée `0x114C` → pile 68K ; domicile D8 `$87F0(A5)` ; ⭐ §74 : le « DBRA » du recompilateur = `SUBQ.W #1 ; BPL` (≥ 0) |
| §75 | 2637 | ressources chargées par le natif, setjmp/longjmp, bloc drapeaux exact (`derives_from`) |
| §76–§77 | 2690–2718 | adresses de code converties à l'usage ; fin de code réelle ; `ADDX`, `CMP.L` exact, `bsmem`, copie vers indexé |
| §78 | 2746 | revue des écritures perdues : QSound en octet exact, `BCLR` par masque, `d16(An,Dn)`… |
| §80–§81 | 2785–2847 | test de bit différé, domicile A8 `$87E0(A5)`, `MOVE.L An,d(An)`, `EOR` inversé, longs mémoire en opérande, états de suivi périmés, `TerminateThread` |
| §82–§83 | 2888–2922 | moitié haute d'un Dn (`SWAP`), long en ordre naturel, aides du recompilateur (`MOVEM`, `ANDI CCR`, `ABCD`), masques 32 bits, `ADDA.W T(PC,Dn)` |
| §85–§88 | 2987–3028 | `ADDI.L #$16000000` (lui seul), `MOVEA.W An,Am`, `BTST` rendu à l'appelant, `ROL.L`, constante adresse dans `CMPI.L` |
| §90, §92 | 3067, 3102 | `bswap32` / `bswap16_mem` ; `SUBI` en place + test ; `EORI` traduit en `BCHG` → `TST.B` |
| §93 | 3130 | `BTST #15,D0` rendu à l'appelant (provocation sur tout appui) |
| §97 | 3214 | octet via An de parité inconnue après `ADDA` : adresse exacte à l'exécution (70) |
| §100–§102 | 3289–3348 | `bswap16` depuis table indexée ; constante IMPAIRE ≠ adresse ; reclassement natif (`native_at`) ; index brut ×4 (mots) |
| §106–§107 | 3531–3556 | `MOVEA.L abs.L,An` ; audit des écritures muettes (`chutes.json`, `dn_alu.py`, `AUDIT_MEM`) |
| §110, §112 | 3662, 3721 | `vram_shift_const` (base de palettes) ; index brut ×4 (table de pointeurs) |
| §114 | 3764 | fusion si/sinon de A8 (`MERGE_IFELSE`) ; CMP « drapeaux exacts » rendu à l'appelant |

### 1.3 Bugs de CORRECTION numérotés (à ne jamais réintroduire)
| N° | Section | Ligne | Bug |
|---|---|---|---|
| 1–2 | §38 | 1450 | ancien An pris pour le nouveau (écriture décalée) ; `bgez` de fin de boucle oublié |
| 3 | §40 | 1497 | effacement `sw zero,Dn` supprimé par un souvenir débordant d'une fonction à l'autre |
| 4 | §42 | 1549 | échange de registres traduit en `MOVEA` seul (→ `EXG`) |
| 5–6 | §43 | 1566 | « masque 24 bits » = vrai `ANDI.L` ; immédiats négatifs tronqués à 16 bits |
| (assembleur) | §71, §91, §94 | 2552, 3083, 3159 | `Bcc.W` hors de portée ; fusion d'un saut qui est lui-même cible ; entrées de table > 32 Ko |

---

## 2. Disposition mémoire et « recette cps2 »

| Section | Ligne | Résumé |
|---|---|---|
| R§2 | 57 | état de jeu Hyper : `A5 = 0xb88000`, joueurs à +0x400, variable de décor `A5-0x3e88` (fil PS2) |
| §24 | 1076 | ⛔ problème « ouvert » de disposition (mots XOR 2…) — **dissous par §29** |
| §25 | 1115 | PINE : A5 = `0x908000` ⇒ RAM `$FF0000` = PS2 `0x900000` ; longs natifs à 2 mod 4 |
| §26–§27 | 1152–1189 | familles d'objets ; zones pointées ; idée « mémoire façon PS2 dans le fork » |
| ⭐ §29 | 1252 | **décision** : recette universelle (mot = même adresse, octet = XOR 1, long = `SWAP`) |
| §30 | 1273 | RAM émulée : SFA3 `0x900000`, Upper `0xa00000`, Hyper `0xb80000` ; vidéo juste après |
| ⭐ §32 | 1320 | recette intégrée (`MEMMODE=cps2`) et prouvée (`test_recette.py`) ; données à mots inversés |
| §34 | 1375 | carte des adresses PS2 → CPS2 (`ADDRMAP`) |
| ⭐ §44 | 1621 | typage PAR CHAMP (SF III 3SX) ; `MEMMODE=type` ; 🔓 annoncé comme « l'objectif », jamais généralisé |
| §63 (pt 5-6) | 2316 | pointeurs PS2 bruts en données → conversion `JSR CONV_An` (`$400`), adresses matérielles marquées `$01xxxxxx` |
| §65 (pt 4), §66 (pt 5), §97 | 2390, 2435, 3214 | octets dont la parité n'est connue qu'à l'exécution : séquences exactes |
| §69 | 2506 | conception fork : bus « octets XOR 1 » + plan mémoire identité (coût nul) ; 🔓 `MEMMODE=fork` jamais écrit |
| §62, §78 | 2277, 2746 | exceptions à la recette : ports d'entrée et QSound en octet **exact** |

---

## 3. Banc MAME et scripts Lua

| Section | Ligne | Résumé |
|---|---|---|
| ⭐ §59 | 2156 | `mame_test.py` : image traduite dans `sfa3ud` (Phoenix) ; pile 68K hors RAM du jeu ; noyau Capcom remplacé par des fils PS2 |
| §60–§62 | 2189–2277 | noyau de tâches Capcom (TRAP #0-#3) ; `kernel68k.py` ; entrées CPS2 reliées |
| ⭐ §63 | 2316 | `diag.py` (1 exécution = 1 faute localisée) et `watch.py` |
| §65 | 2390 | banc visuel `banc.lua`, `dumpv`, `cpsa`, `greffe`, `vcount` ; `-video none` |
| §67 | 2466 | `tapw.lua`, `objh.lua` ; rappels de méthode (déplacements A5 négatifs, image N / N+1) |
| §75 | 2637 | `banc_mem.lua` (blocs à adresse fixe) — à charger dans TOUT script ; `patch_call` |
| §80–§81 | 2785–2847 | `jeu.lua` (`INPUTS`), taps avec PC ; EEPROM partagée ; `-debug` décale le minutage |
| §82–§83 | 2888–2922 | `banc_sprites.lua` (banques, éclatement 16×16), `banc_plans.lua`, `banques.py` |
| §89 | 3044 | visualiseur d'état PS2 (`visu_rom.py`, `visu.lua`) ; 27 décors vérifiés |
| §92 | 3102 | `force_stage.lua` (`STG`, `SUIVI`) |
| ⭐ §93 | 3130 | `commandes.lua` + `commandes.py` : 42 actions arcade ↔ traduction |
| §98 | 3232 | `profil.lua` ; relancer les **trois** diagnostics |
| §103–§104 | 3383–3475 | `_scene`, `_stall`, `_finpos`, `_prof_ph`, `_conv`, `_bcd` ; correctif ghosting du banc |
| §106 | 3531 | `BANC_OMBRE` ; ⚠ une prise posée avant `banc_sprites.lua` voit la liste convertie |
| §108 | 3603 | `profils.py` (`MODULE`), données coupées (`$C80000`), `BANC_DIR` |
| ⭐ §110 | 3662 | `tournee.lua` (partie complète) ; `nonreg.sh` ; pièges `-state` et `pkill -f` |
| §111–§112 | 3696–3721 | `tournee.lua` : `PERSO`, `FORCE`, `SNAPFIN`, `MODE` |
| §114–§115 | 3764–3786 | `diag.py` suit `MODULE` ; banc graphique d'Upper (`BANC_BANQUES`, `BANC_PTR_ANIM`, `BANC_GFX_INTRO`) |

---

## 4. Graphismes : banques, plans, palettes

| Section | Ligne | Résumé |
|---|---|---|
| R§8 | 421 | ⛔ premier format de conteneur (tuiles 0x20 / 0x80) — précisé par §45 |
| ⭐ §45 | 1740 | l'Anthology contient **toute** la ROM graphique CPS2 de SFA3 (valeurs brutes, FBNeo = 15−brut) ; `anthgfx.py`, `cps2rom.py` ; banques de persos = sous-ensembles. ⛔ « emplacement = X>>13 » (voir §82) |
| §48 | 1872 | retouches matérielles du portage ; schéma de banques proposé pour le fork. ⛔ X → Y (§82) |
| ⭐ §49 | 1903 | Upper ne tient pas dans 262 144 tuiles CPS2 ⇒ fork obligatoire |
| §51 | 1949 | table perso → banque (ro3 `0x3AC0B0`, ro5 `0x438320`, ro9 `0x3BF1B0`) ; Hyper n'a aucune banque propre |
| §65 | 2390 | ⛔ décalages de plans `+$5600` / `+$B00` — remplacés par les tables de §83 |
| ⭐ §82 | 2888 | emplacement de banque = **bits 13-15 de Y** ; X>>13 = priorité ; `banques.py` |
| §83 | 2922 | plans : indices LOCAUX dans `e256` / `e312` (`plan1.bin`, `plan2.bin`, `f312.bin`) ; ⛔ « 6/7 = conteneurs de classe » (voir §102) |
| §84 → §85 | 2961 → 2983 | ⛔ « zone dynamique » de l'emplacement 1 (§84) **retirée** au §85 (vrai bug = `ADDI.L` perdu) |
| §89 | 3044 | rendus d'états PS2 ; graphismes retouchés par l'Anthology non reproductibles dans le banc |
| §95 | 3181 | format des frames de sprites (`docs/reference/FRAMES-Anthology.md`) |
| §99, §105 | 3261, 3516 | tuiles et palettes des persos MAX dans le banc |
| §102 | 3348 | ⭐ emplacements 6/7 = joueurs 3/4 **seulement si la structure est active** (`$FF8C01` / `$FF9001`) |
| §103 (2-3), §106 | 3383, 3531 | bannières de l'intro (reconversion au changement de base), portraits blancs, emplacement 4 quand `$BE48 = 0` |
| §110 | 3662 | fins noires : base des palettes non convertie |
| ⭐ §115 | 3786 | banc graphique d'Upper : couverture mesurée, ≈ 5-6 Mo de tuiles manquantes ⇒ fork MAME |

---

## 5. Son

| Section | Ligne | Résumé |
|---|---|---|
| R§4 | 122 | Z80 de SFA3 verbatim (offset 0x100 de `ro3_usa_z80.bin`) |
| §16 | 952 | le Z80 recompilé n'a pas à être retraduit |
| §58 | 2131 | mémoire partagée QSound : base RAM + `$60000` ↔ `$618000` |
| ⭐ §78–§79 | 2746–2770 | le son revient (boîte aux lettres `$61801F`, octets exacts) ; protocole conforme ; validé à l'oreille |
| §102 (fin), §103 (1) | 3348, 3383 | intro : le portage remplace le repère musique `$618021` par une table de ticks → patch (±1 image) |
| §108 | 3603 | repère musique désactivé pour ro5 (ROM son de SFA3 sans les repères d'Upper) |
| §113 | 3743 | musiques SFA2 : demanderaient un fork son |

---

## 6. Performance

| Section | Ligne | Résumé |
|---|---|---|
| §69 | 2506 | surcoût de la recette cps2 mesuré ; conception du bus XOR 1 |
| §93 | 3130 | cadence « turbo » : 4 tours / 3 images ; traduction 125,6 % contre 133,3 % |
| ⭐ §98 | 3232 | conversion des adresses de code par **hachage** (`$3C0000`) → 133,2 % |
| §103 (4-5) | 3383 | ghosting en turbo : dépassement du temps image ; banc écrit la liste dans les deux banques ; judas `merge_long_postinc` |
| ⭐ §104 | 3475 | conversion `$400` dichotomique, `drop_dead_sr`, réécritures à la main ; reste → surcadençage ~115-120 % |

---

## 7. Modules ro3 / ro5 / ro9 (et autres jeux)

| Section | Ligne | Résumé |
|---|---|---|
| R§4 | 122 | `ro1..ro9 = zero1..zero9` ; ro3 SFA3 (31 persos), ro5 Upper (36), ro9 Hyper (36, aucun perso ajouté) |
| §28 | 1222 | le traducteur appris sur SFA3 vaut pour Upper et Hyper ; filiation SFA3 → Upper → Hyper |
| §30, §33 | 1273, 1357 | bases RAM par module (`ram_hi_of`) |
| §31 | 1293 | ce qui pourrait être greffé d'Hyper dans Upper (`transplant.py`) |
| §46, §50 | 1818, 1919 | versions d'Hyper : `$102/$116/$117/$D3(A6)`, bits de version décodés |
| §55–§56 | 2040–2075 | programme entier assemblé (`link.py`) ; images (`build_rom.py`) : SFA3 tient dans 4 Mo, Upper non |
| ⭐ §108 | 3603 | Upper au banc : profils, bloc `$C80000`, chargement intro en `$B83800`, `$BE48` signé |
| §113 | 3743 | étude SFA2 (`ro2/ro4/ro6/ro8`) : décors ajoutables sur le fork |
| ⭐ §114 | 3764 | Upper : attraction en boucle, 12 000 images sans exception |
| §115 | 3786 | Upper : banc graphique |

---

## 8. MAX (SFA3 MAX PSP)

| Section | Ligne | Résumé |
|---|---|---|
| §95 | 3181 | format des frames transmis à la session MAX |
| §99 | 3261 | Eagle dans le banc (`banques_max.py`, `MAX_DEMO`, `roms_max`) — en pause |
| §105 | 3516 | palettes MAX (`MAX_PAL`, `MAX_PAL_ID`, table `0x451230`) |
| ⭐ §109 | 3633 | MAX ⊃ Upper ; 4 persos (Eagle, Maki, Yun, Ingrid) en `$26/$27` + 2 places à créer ; reste de MAX écarté |
| §110 | 3662 | fins MAX : réutiliser des fins existantes pour l'instant |
| §111 | 3696 | octets libres de la structure joueur : `$3F0` (octet), `$3F2` (mot) retenus par la session MAX |
| (hors journal) | — | `docs/MAX-Etude-Contenu-Persos.md` et dossier `max/` du dépôt = **propriété de la session MAX** |

---

## 8 bis. Upper au fork, puis Hyper et cœur, §116-§144

| Section | Ligne | Résumé |
|---|---|---|
| §116 | 3804 | fork `sfa3hx` : ROM graphique 128 Mo, code de sprite étendu (bits 10-11 de X), `HSFA_GFX` / `hsfa_gfx.py` |
| §118 | 3838 | son d'Upper : boîte aux lettres QSound ; Z80 d'Upper sans musique → ROM son SFA3 + repère (option B ; C = hybride) |
| §119-§120 | 3858, 3882 | palettes d'Upper (`0x5072B0`) ; une base par plan (`HSFA_PLANS`, `hsfa_plans.py`) |
| §121 | 3901 | logo du titre (`BANC_COMMUN=351`) ; Hyper (`ro9`) démarre |
| ⭐ §122 | 3927 | Upper de bout en bout : copies `daddu`, épilogue `lq`, chargeurs natifs (`LOAD_BASE $B83800`, fins) |
| §124-§125 | 3974, 3988 | comparaison exacte sur octet indexé ; `btst_dyn` rendu à l'appelant (Arcade droit à Bison) |
| ⭐ §126 | 4003 | Adon sans fin (`FTC_AVANT`), EXG par la pile, coupure des données sur bloc de perso (`blocs`), constantes `lui`/`const`, audit `audit_exacts.txt`, `nonreg_ro5.sh`, 38/40 fins |
| §127 | 4069 | son d'Upper : ROM son hybride (musiques SFA3 + voix d'Upper), `gen_hybride.py`, fork `HSFA_SON`, QSound 16 Mo |
| §128 | 4091 | plantage `$22` (MOVE + EXT perdu, `EXT_MEM`) ; SURVIVAL, mode 3, entraînement, VERSUS (`tournee.lua VS=1`) vérifiés |
| §129 | 4112 | MAX : Eagle dans Upper sur le fork (`max_gfx.bin@26D5580`, `pl26_hx`, bloc `$D40000`, `MAX_DEMO` ro5 à +`$D75EC`, `demo_max.lua`) |
| ⭐ §130 | 4135 | **état à la pause** : sorties latérales A8/D8 (`LATERAL`), portraits MAX (`MAX_PORTRAITS`, non testé), balayages des fins à relancer |
| §131 | 4161 | `balayage_fins.sh` ; SFA3 32/32 après §130 ; portraits d'Eagle justes (type 8 +`$1C00`, palettes de sélection `0x56E9C` déviées) |
| ⭐ §132 | 4190 | audit « code perdu » : `MULS` (perte silencieuse), décalages, rotations, tables indexées, D8 ; chutes SFA3 28→12, Upper 42→13 (reste = C du portage) |
| §133 | 4224 | Hyper au fork : banques e545/e546/e548/e547, modes (VERSUS/TRAINING), 113 versions balayées |
| §134-§136 | 4247 | pistes PSP (rosette), recherche web (CPS2 Turbo, sfa3_support.lua), cœur FBNeo libretro Android |
| ⭐ §137 | 4302 | audit d'Hyper ; `SHIFT_MR` (perte silencieuse), multiplications décomposées, `SPILL_Q` ; **régression `MEMSHIFT` des fins SFA3 corrigée** |
| ⭐ §138 | 4331 | zones d'ombre (1) : écritures perdues retrouvées (RMW indexé, `m1 += m2`, CPS-A `lui` seul, base objets `$400000`, décor `$DC` d'Upper, tables indexées par un champ) ; **profil des adaptateurs** (~20 % du travail, même marge que l'arcade) |
| §139 | 4398 | zones d'ombre (2) : hasard (`$FF80AE`), Upper face à l'arcade, adresses MAX dans Upper, index et son d'Hyper (flux ADX `Y_DATA`), cœur FBNeo widescreen |
| §140 | 4446 | code C du portage : aiguilleurs par table de longs, tests `lb ; bne r,zero` ; fin de match VERSUS d'Hyper (validation en cours) |
| §141 | 4465 | chantiers en cours (réimportation de tuiles, flux ADX, conversion MAX, étape A, usine de Zangief) et suite logique |
| §142 | 4503 | reprise du 2026-10-10 : retours console, tuiles vides d'Upper corrigées, étape A, flux ADX, réimportation de tuiles, conversion MAX ; rapports dans `docs/rapports/` |
| ⭐ §143 | 4539 | coups de Sakura/Akuma/Dan/Rose corrigés (`TAILBR`, `LUIDN`) ; `valide_tout.sh` ; script de construction depuis l'ISO ; carte de tous les modules ; décisions de stratégie |
| ⭐ §144 | 4584 | **décision voie B : base Hyper + mode Arcade d'Upper** ; tout MAX converti ; tous les décors SFA3 en PSD ; décor SFA2 importé ; rejeu QSound d'Hyper ; cœurs ROCKNIX ; construction ISO seule |

---

## 9. Fork MAME / FBNeo

| Section | Ligne | Résumé |
|---|---|---|
| R§4 | 122 | pourquoi un fork : plafond graphique CPS2 32 Mo |
| §27, §48, §49 | 1189, 1872, 1903 | mémoire façon PS2 ; schéma de banques ; fork obligatoire pour Upper |
| §55–§56 | 2040–2075 | surface de contact (~80 sites, `hooks_fork.py`) ; ROM programme étendue |
| §63, §69 | 2316, 2506 | plan mémoire identité ; bus octets XOR 1 ; surcadençage |
| §103 (5), §104 | 3383, 3475 | liste d'objets verrouillée à son marqueur ; surcadençage ~115-120 % |
| ⭐ §109 | 3633 | **décision** : fork **MAME** (jeu dérivé de `sfa3ud`) comme banc intermédiaire, puis cœur **FBNeo** |
| §113 | 3743 | registre de base par plan (décors SFA2) |
| §115 | 3786 | besoin : ROM graphique étendue (proposé : « bit 15 de Y = bit 18 du code ») + ROM programme `$C80000` |
| (hors journal) | — | état réel du fork : voir `ETAT-DES-LIEUX.md` §3 (driver `sfa3hx`, code étendu par **bits 10-11 de X**, pas encore dans le journal) |

---

## 10. Outils de test et de non-régression

| Section | Ligne | Résumé |
|---|---|---|
| C3 | 653 | `verify.py` (opcodes informatifs contre témoin au hasard) |
| §13 | 889 | outils qui signalent leurs exceptions (ne plus les avaler) |
| §23 | 1058 | `e2e.py batch` (traduire → assembler → comparer à la ROM) |
| §37 | 1431 | `diverge.py` |
| §41, §43 | 1522, 1570 | `opclass_e2e.py`, `unmatched.py`, `missclust.py`, `natmiss.py`, `show.py` |
| §63 | 2316 | ⭐ `diag.py`, `watch.py` |
| §78 | 2746 | `showmiss.py`, `MAXVA` |
| §93 | 3130 | ⭐ test des commandes (référence `work/mame/cmd_ref.txt`) |
| §96 | 3190 | `revision.py` : l'Anthology suit la révision USA 980904 ; Phoenix `sfa3ud` = bonne référence |
| §107 | 3556 | compteur « écritures de registre tombées » (`chutes.json`) ; `AUDIT_MEM=1` → `mem_miss.json` |
| §108 | 3603 | garde-fou md5 ro3 (⛔ valeur de §109 périmée dès qu'un correctif touche ro3) |
| ⭐ §110 | 3662 | `nonreg.sh` : 3 diagnostics + commandes |
| §111 | 3696 | série des 32 fins (arcade | traduction) |

---

## 11. Pièges (sections sources)

| Section | Ligne | Piège |
|---|---|---|
| R§3 | 81 | le live PINE sur un décor déjà cassé ne prouve rien : il faut un vrai chargement |
| ⭐ R§7 | 598 | filtrer par entropie ; dumps à ID forcé ; `nice -n 19` ; `*_prog68k.*` = du MIPS ; identité git |
| R§6bis | 511 | découper les fonctions MIPS par cibles de `jal` ; mesurer la couverture en **union** |
| C2 | 632 | « étendue » ≠ « utilisable » (4,2 %) |
| §25, §37 | 1115, 1431 | le scratchpad est vidé entre les sessions |
| §59 | 2156 | pile 68K hors RAM du jeu ; écritures dans A7 absorbées |
| §67 | 2466 | déplacements A5 négatifs ; image Lua N = écriture pendant N+1 ; A5 du portage = ROM − `$254` dans une zone |
| §75 | 2637 | `banc_mem.lua` obligatoire dans les scripts ponctuels |
| §81 | 2847 | EEPROM partagée ; `-debug` décale le minutage ; fusion d'entrées par clé « port|champ » |
| §82 | 2888 | `$700000` en écriture seule dans MAME |
| §93, §101 | 3130, 3314 | Start trop tôt perdu par le menu Anthology ; 2e Start pour valider le mode |
| §94 | 3163 | « `pc=$10` » = adresse du vecteur 4, pas une destination |
| §96 | 3190 | `sfa3_prog.bin` : données de `$0-$BFFFF` fausses → `sfa3ud_prog.bin` pour les tables |
| §98 | 3232 | toujours relancer les trois diagnostics |
| §106 | 3531 | prise avant `banc_sprites.lua` = liste convertie |
| §108 | 3603 | `$BE48(A5)` = `$FF3E48` (déplacement signé) |
| ⭐ §110 | 3662 | `-state` bloque ; `pkill -f` / `pgrep -f` tuent le shell |
| §114 | 3764 | les prises d'opcodes voient la prélecture (SP trompeur) |

---

## 12. Fil « cross-stage PS2 » (ancien, en sommeil)

| Section | Ligne | Résumé |
|---|---|---|
| R§0 | 13 | ⛔ tableau d'état du 2026-09-26 (features PS2 livrées ; voie B) — ne reflète pas §109 |
| R§2–R§3 | 57–81 | carte de l'état de jeu Hyper ; mécanisme cross-stage (repointer le contexte de couche) ; pnach « sans effet » |
| R§6 | 496 | ⛔ « prochaines étapes » d'origine |
| Docs liés | — | `legacy/docs/PLAN-Cross-Stage-Actualise.md`, `CARTO-Cross-Stage-Tables.md`, `PACKER-Recette.md`, `ANIMATION-et-Finitions.md` |

---

## 13. Suite du journal, §116-§172 (une ligne par section)

Titre abrégé et mots-clés. Les sections §116-§144 ont aussi un résumé au §8 bis ; les rapports cités sont dans
`docs/rapports/`.

| § | Ligne | Titre | Mots-clés |
|---|---|---|---|
| §116 | 3804 | Fork MAME `sfa3hx` : ROM graphique de 128 Mo | MAME 0.285, `cps2f`, `HSFA_GFX`, code d'objet étendu (bits 10-11 de X), persos d'Upper |
| §117 | 3827 | Documentation remise à plat | `INDEX-HANDOFF.md`, `ETAT-DES-LIEUX.md`, corrections relevées |
| §118 | 3838 | Son d'Upper : boîte aux lettres QSound perdue | X_DATA 388/389, Z80 d'Upper sans musiques, options B / C, `gen_son.py` |
| §119 | 3858 | Upper : palettes justes, plan 32×32 = `e525` | table `0x5072B0` (décalages signés), besoin d'une base par plan |
| §120 | 3882 | Fork : une base par plan | registres `$804200-$804205`, unités de 64 Ko, `HSFA_PLANS`, `hsfa_plans.py` |
| §121 | 3901 | Upper : logo du titre ; deux défauts du traducteur ; Hyper démarre | `BANC_COMMUN=351`, emplacement 0, ro9 |
| ⭐ §122 | 3927 | Upper jouable de bout en bout | Bison, fins des nouveaux persos, copies `daddu`, épilogue `lq`, chargeurs natifs, `LOAD_BASE` |
| §123 | 3956 | Documentation d'architecture et carte des symboles | `OUTILS.md`, fiches de scripts, symboles |
| §124 | 3974 | Comparaison exacte sur un octet indexé | `d8(An,Dn)`, `byte_index_exact`, carte du monde d'Upper |
| §125 | 3988 | Upper : l'Arcade allait droit à Bison | `btst_dyn` rendu à l'appelant, états PCSX2 |
| ⭐ §126 | 4003 | Upper : Adon sans fin ; EXG par la pile | `FTC_AVANT`, coupure des données (`blocs`), `nonreg_ro5.sh`, 38/40 fins |
| §127 | 4069 | Son d'Upper : ROM son hybride | option C, `gen_hybride.py`, `z80son.py`, `HSFA_SON`, QSound 16 Mo |
| §128 | 4091 | Upper : plantage du perso `$22` | `EXT_MEM` (lecture signée étendue perdue), SURVIVAL, VERSUS, entraînement |
| §129 | 4112 | MAX : Eagle dans Upper sur le fork | `max_gfx.bin`, bloc `$D40000`, `MAX_DEMO` |
| §130 | 4135 | Sorties latérales des zones A8/D8 ; portraits MAX d'Eagle | `LATERAL`, `MAX_PORTRAITS`, état à la pause |
| §131 | 4161 | Balayages des fins (outil permanent) | `balayage_fins.sh`, SFA3 32/32, portraits d'Eagle |
| ⭐ §132 | 4190 | Audit « code perdu » : écritures de registre sans traduction | `chutes.json`, `MULS`, décalages, rotations, SFA3 28→12, Upper 42→13 |
| §133 | 4224 | Hyper au fork : banques, modes, versions | e545-e548, VERSUS / TRAINING, 113 versions balayées |
| §134 | 4247 | Pistes « paradigmes » : réponse de la session MAX | code PSP en C, rosette (~150 paires arcade ↔ PSP) |
| §135 | 4264 | Recherche web | aucune documentation du recompilateur, CPS2 Turbo, `sfa3_support.lua` |
| §136 | 4283 | Cœur FBNeo libretro HSFA | `cps_hsfa.cpp`, `sfa3hsfa` / `sfa3uhsfa`, `paquet_fbneo.py`, `hsfa_run`, Android |
| ⭐ §137 | 4302 | Audit « code perdu » d'Hyper ; régression du §132 corrigée | `SHIFT_MR`, `SPILL_Q`, `MEMSHIFT`, fins de SFA3 |
| ⭐ §138 | 4331 | Zones d'ombre (1) : écritures mémoire perdues | `AUDIT_MEM`, `mem_miss.json`, profil des adaptateurs |
| §139 | 4398 | Zones d'ombre (2) | hasard `$FF80AE`, Upper face à l'arcade, adresses MAX, son d'Hyper, cœur 16:9 |
| §140 | 4446 | Code C du portage : aiguilleurs par table de longs | tests `lb ; bne r,zero`, fin de match VERSUS d'Hyper, TRAINING |
| §141 | 4465 | Chantiers lancés le 2026-10-07 | réimportation de tuiles, flux ADX, conversion MAX, étape A |
| §142 | 4503 | Reprise du 2026-10-10 | retours console, tuiles vides d'Upper (`HSFA_PLANS_VIDE15`), étape A, flux ADX |
| ⭐ §143 | 4539 | Coups de Sakura / Akuma corrigés ; construction depuis l'ISO | `TAILBR`, `LUIDN`, `valide_tout.sh`, `hsfa_build.py`, `CARTE-MODULES.md` |
| ⭐ §144 | 4584 | Décision voie B (base Hyper) | MAX converti, décors en PSD, décor SFA2, rejeu QSound, ROCKNIX, ISO seule |
| §145 | 4620 | Hyper corrigé (jauge, TRAINING) et voix SFA1/SFA2 | `CMPMM`, redirection des voix (module ro9 corrigé, bloc `$E70000`), zips « tout dans le jeu », greffe |
| §146 | 4675 | Glitch du grand portrait d'Upper | chargement différé de l'emplacement 4, `BANC_LAT4`, `HSFA_LAT4`, patch 0002 |
| §147 | 4698 | Gros A ; écran de victoire ; options ; étape B ; greffe étape 2 | `FLUXEA`, `OPTION_RETOUR`, patch 0003, `RELOGE_*`, dépôt réorganisé |
| ⭐ §148 | 4733 | Étape B et OPTION/EXIT intégrés et validés | `RELOGE_CODE` / `NATIF` / `RAM`, `valide_tout.sh` parallélisé, bloc par perso d'Hyper, `$2B8` |
| §149 | 4750 | Musique d'Hyper : origine des flux | banc Z80, jeux de flux A = *Super SF2*, plan partitions + compression |
| §150 | 4770 | Flux Ogg Vorbis dans le cœur ; cœurs Windows | patchs 0004-0005, `fluxtool`, `flux_ogg.py`, phase 1 du son d'Hyper |
| §151 | 4792 | Carte musique | `hsfa_musique.h`, 2ᵉ Z80, 3ᵉ QSound, patch 0006, `HSFA_PARTITIONS` |
| §152 | 4803 | Hyper : tous les flux en Ogg | zip 201 Mo, 216 flux, 2ᵉ code `$C3B6` |
| §153 | 4813 | Cœurs ROCKNIX avec les patchs 1-10 | glibc ≤ 2.38, `qemu-aarch64`, kit `essai_son` |
| §154 | 4820 | Tournée complète d'Hyper | 151 VERSUS, `tournee_complete.py`, 122 codes musique entendus |
| §155 | 4826 | Cœurs Android avec les patchs 1-10 | `build_android.sh`, NDK r28c |
| §156 | 4831 | Modes cachés de la sélection d'Hyper | S-ISM, CLASSIC, Mazi, musiques B / EX, 194 codes sur 216 |
| §157 | 4838 | Patch 11 : roulette sur la touche Pièce | `0007`, `$D3`, Start pour EX / S-ISM, cœurs 1-11 |
| §158 | 4845 | Cris de dégâts / K.O. d'Hyper pris sur l'arcade | `mesure_cris_arcade.py`, `corrige_cris.py` |
| §159 | 4853 | Voix « par pas » d'Hyper vérifiées sur l'arcade | `compare_voix_arcade.py`, `voix_arcade.tsv`, `corrige_voix.py` |
| §160 | 4861 | Voix d'Hyper : supers, persos cachés de SFA1, cris | `--super`, `--poke`, `HSFA_POKE`, rôle des cris |
| §161 | 4868 | SFZ2 Alpha comme référence ALPHA / EX | `sfz2al`, Rose, Akuma EX |
| §162 | 4874 | PILE_LUI ; v149 | temporaire de pile pris pour la constante d'un `lui`, prologues `sq`, `nonreg_coeur.sh` |
| §163 | 4898 | VRAM_TABLE ; v150 | décor de Cammy (`$2C`) sans son plan du dessus, adresses vidéo hôte |
| §164 | 4915 | Persos MAX dans Upper : lots 2b4-2b9 | collisions d'ID (`$2D`, `$2E`), cris, portraits de victoire, fins |
| ⭐ §165 | 4942 | Greffe Arcade sur Hyper : étapes 4 à 6 | 59/85 puis 60/85 fins, `PTR_BAS`, `FE_TABLE`, `ANIM_GREFFE`, `PLANS_CONT`, CONTINUE |
| §166 | 4955 | Persos MAX dans Upper : lots 2b10-2b15, transparence | échelle ×19/16, WINNER, fins, mélange des objets (0010), ombres (0011) |
| §167 | 4979 | Tableau des coups d'après le guide BradyGames | tableau hors dépôt (texte protégé), outils `tools/guide-coups/` |
| §168 | 4988 | Ce que la recherche du livre apporte | `docs/rapports/recherche/`, révision 980904 absente de l'Anthology, S-ISM SHADALOO |
| §169 | 4998 | Sondes de la recherche | `banc_coups.py`, Mazi = 1 manche, Head Press contre MAX |
| §170 | 5015 | Matrice des coups : Hyper Z3 contre l'arcade | `banc_matrice.py`, 203 coups, 22 écarts |
| ⭐ §171 | 5033 | Killer Bee Assault de Cammy | aide `roxr`, `EXG` et `BCLR` perdus ; `EXG_PILE_D`, `AIDE_ROXR`, `BITOP_DN`, `paires_exg.py` |
| ⭐ §172 | 5058 | Point d'étape transverse du 2026-10-21 | code en retard sur le savoir, archives périmées, `valide_tout.sh`, décisions D1-D7 |

---

## Annexe : table complète des titres (série canonique)

| § | Ligne | | § | Ligne | | § | Ligne | | § | Ligne |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 717 | | 44 | 1621 | | 87 | 3018 | | 130 | 4135 |
| 2 | 729 | | 45 | 1740 | | 88 | 3028 | | 131 | 4161 |
| 3 | 739 | | 46 | 1818 | | 89 | 3044 | | 132 | 4190 |
| 4 | 749 | | 47 | 1849 | | 90 | 3067 | | 133 | 4224 |
| 5 | 757 | | 48 | 1872 | | 91 | 3087 | | 134 | 4247 |
| 6 | 767 | | 49 | 1903 | | 92 | 3102 | | 135 | 4264 |
| 7 | 792 | | 50 | 1919 | | 93 | 3130 | | 136 | 4283 |
| 8 | 800 | | 51 | 1949 | | 94 | 3163 | | 137 | 4302 |
| 9 | 807 | | 52 | 1978 | | 95 | 3181 | | 138 | 4331 |
| 10 | 840 | | 53 | 1993 | | 96 | 3190 | | 139 | 4398 |
| 11 | 860 | | 54 | 2017 | | 97 | 3214 | | 140 | 4446 |
| 12 | 880 | | 55 | 2040 | | 98 | 3232 | | 141 | 4465 |
| 13 | 889 | | 56 | 2075 | | 99 | 3261 | | 142 | 4503 |
| 14 | 902 | | 57 | 2101 | | 100 | 3289 | | 143 | 4539 |
| 15 | 920 | | 58 | 2131 | | 101 | 3314 | | 144 | 4584 |
| 16 | 952 | | 59 | 2156 | | 102 | 3348 | | 145 | 4620 |
| 17 | 966 | | 60 | 2189 | | 103 | 3383 | | 146 | 4675 |
| 18 | 984 | | 61 | 2233 | | 104 | 3475 | | 147 | 4698 |
| 19 | 993 | | 62 | 2277 | | 105 | 3516 | | 148 | 4733 |
| 20 | 1007 | | 63 | 2316 | | 106 | 3531 | | 149 | 4750 |
| 21 | 1025 | | 64 | 2366 | | 107 | 3556 | | 150 | 4770 |
| 22 | 1050 | | 65 | 2390 | | 108 | 3603 | | 151 | 4792 |
| 23 | 1058 | | 66 | 2435 | | 109 | 3633 | | 152 | 4803 |
| 24 | 1076 | | 67 | 2466 | | 110 | 3662 | | 153 | 4813 |
| 25 | 1115 | | 68 | 2485 | | 111 | 3696 | | 154 | 4820 |
| 26 | 1152 | | 69 | 2506 | | 112 | 3721 | | 155 | 4826 |
| 27 | 1189 | | 70 | 2530 | | 113 | 3743 | | 156 | 4831 |
| 28 | 1222 | | 71 | 2556 | | 114 | 3764 | | 157 | 4838 |
| 29 | 1252 | | 72 | 2569 | | 115 | 3786 | | 158 | 4845 |
| 30 | 1273 | | 73 | 2596 | | 116 | 3804 | | 159 | 4853 |
| 31 | 1293 | | 74 | 2623 | | 117 | 3827 | | 160 | 4861 |
| 32 | 1320 | | 75 | 2637 | | 118 | 3838 | | 161 | 4868 |
| 33 | 1357 | | 76 | 2690 | | 119 | 3858 | | 162 | 4874 |
| 34 | 1375 | | 77 | 2718 | | 120 | 3882 | | 163 | 4898 |
| 35 | 1393 | | 78 | 2746 | | 121 | 3901 | | 164 | 4915 |
| 36 | 1414 | | 79 | 2770 | | 122 | 3927 | | 165 | 4942 |
| 37 | 1431 | | 80 | 2785 | | 123 | 3956 | | 166 | 4955 |
| 38 | 1454 | | 81 | 2847 | | 124 | 3974 | | 167 | 4979 |
| 39 | 1482 | | 82 | 2888 | | 125 | 3988 | | 168 | 4988 |
| 40 | 1501 | | 83 | 2922 | | 126 | 4003 | | 169 | 4998 |
| 41 | 1522 | | 84 | 2965 | | 127 | 4069 | | 170 | 5015 |
| 42 | 1553 | | 85 | 2987 | | 128 | 4091 | | 171 | 5033 |
| 43 | 1570 | | 86 | 3002 | | 129 | 4112 | | 172 | 5058 |

Racine : R§0 13 · R§1 30 · R§2 57 · R§3 81 · R§4 122 · R§5 151 · R§8 421 · R§6 496 · R§6bis 511 · R§7 598.
Chapitre carte : C1 620 · C2 632 · C3 653 · C4 683 · C5 700. En-têtes de chapitre : « Carte MIPS↔68K » 618 ·
« Recensement du traducteur » 715 · « Assembleur, test de bout en bout » 1048.
