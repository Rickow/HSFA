# Intégration des persos MAX dans Upper (`ro5`) — option de construction `MAX=1`

Agent `agent_integration_max`, 2026-10-11. Tout est dans `<workspace>/work/agent_integration_max/`.
Rien n'a été écrit ailleurs ; le traducteur partagé, `work/mame*`, le fork et les arbres FBNeo ne sont pas touchés.

## 0. État

| palier | contenu | état |
|---|---|---|
| **1** | **Eagle (`$26`) sélectionnable et jouable : VERSUS (J1 et J2) puis Arcade jusqu'à la fin** | **ATTEINT** (§3, §6) |
| 2a | **Maki (`$27`)** : mêmes points que le palier 1 | **ATTEINT** (§6b) |
| 2b | **Yun `$2D`, Ingrid `$2E`** (n° libres), tables par ID agrandies à 48, HUD, aperçu, citations, jauges | **ATTEINT sur v149** (§8) |
| 3 | fins MAX en Arcade | pas fait (Eagle joue aujourd'hui la fin de Ryu) |
| 4 | décors des fins MAX | pas fait |

**Option à 0 : ROM identique à l'octet.** `MAX` absent ou `MAX=0` : `mame_test.py` n'appelle rien de nouveau.
Base actuelle : traducteur **v149** (copie `untranspile/` = étiquette v149 + crochets MAX de `mame_test.py`) ;
`banc_ref` = les 8 fichiers de `work/references/v149/ro5` (`sz3ud.03c` `7898814c…`). (Paliers 1 / 2a : base v148,
`1908ec9e…`.)

**Option à 1, palier 2b (4 persos, v149)** : `banc_max4` (§8.3) ; zip FBNeo `fbneo/2b/sfa3uhsfa.zip` `855f8878…`.

**Option à 1, palier 2a livré (Eagle + Maki, v148)** : `banc_max/roms_ro5/sfa3ud/` : `sz3ud.03c` `28239b647757444425ac58dfd7e6431e`,
`sz3ud.04c` `3c39ddf881631e668c85ee75ebe778ae`, `sz3.05c` `dc94c14655dea38194422fd1a8dd9ea6`, `sz3.06c`
`69a73faede66db3960192aca26b2a72a`, `sz3.07c` `e17a3b4c…` (= Upper), `sz3.08c` `2570d06a…` (= Upper), `sz3.09c`
`43e2674282202d1e2fa11b9e99afd5d1`, `sz3.10b` `020a19919a8c85f3b69ce47c16b29c27`. Zip FBNeo d'essai
`fbneo/sfa3uhsfa.zip` `0b71207b14446bb272d9f08ee47c3c32`. (Étapes intermédiaires : palier 1 seul `a8033c36…`.)

## 1. Mode d'emploi

```
cd <workspace>/work/agent_integration_max
./construit_max.sh            # REF=1 : reconstruit aussi la référence banc_ref (MAX=0)
#   = outils/prepare_max.py (conversion + assemblage du code MAX contre banc_ref/carte_image.txt)
#   + MAX=1 MODULE=ro5 TRAVAIL=banc_max untranspile/mame_test.py
PERSO=26 PERSO2=00 VS=1 MODE=1 ALEA=1 NF=20000 SNAPP=200 ./lance_max.sh banc_max essais/x.txt   # fork sfa3hx
BANC=banc_max untranspile/nonreg_ro5_max.sh                                                    # non-régression
(cd fbneo; HSFA_STRICT=1 SOURCE_DATE_EPOCH=1791720000 HSFA_SORTIE=$PWD python3 paquet_fbneo.py upper_max)
```

- `MAX_PERSOS=26` (défaut : les persos « actif » de `outils/persos_max.json`) choisit les persos intégrés.
- `MAX_DIR` (défaut `prep/`) : préparation utilisée ; `MAX_RACINE` : ce dossier.
- `lance_max.sh` : nvram, cfg, états et captures dans `<sortie>.d/` (propres à chaque lancement), jamais `-state`.
  `HSFA_EXT=<banc>` (bloc des animations natives `$BC0000` et données MAX `$B80000` chargés en ROM par le fork),
  `HSFA_SON=work/agent_voix_max/roms_voix` (voix MAX v2), tuiles MAX après celles d'Upper (§5).

## 2. Architecture

### 2.1 Où va quoi

| contenu | adresse | pourquoi |
|---|---|---|
| **code MAX** (91 Ko : 4 persos, moteur PSP porté, acteurs de fin, enveloppes) | **image `$3A0000-$3B63EC`** | le fork n'exécute que `$0-$3FFFFF` (carte `AS_OPCODES` = ROM déchiffrée) : du code en `$B80000` donne des `ORI.B #0,D0` (vu au banc) |
| bloc des tables d'animation natives (261 200 o, était en image `$37AF00`) | **bloc externe `$BC0000`** (`ext_bc0000.bin`) | libère la place du code MAX ; base fixe du fork (`HSFA_EXT`) ; la plage CONV `VBASE $C00000` pointe dessus. Coupure des données inchangée |
| données MAX (tables explicites, données de combat, palettes, tables déplacées) | bloc externe `$B80000` | hors des plages converties par CONV (`$60ACC0-$A80000` et `$C00000-$C3FC50` sont converties) |
| frames + animations d'Eagle | **`$E40000`** (`ext_e40000.bin`, déplacé de `$D40000`) | libre, non converti ; `$D40000` voisinait la fin des données d'Upper (`$C80000-$D3B6A0`) |
| Maki / Yun / Ingrid | `$D80000` / `$DC0000` / `$E00000` | inchangés (convertit_frames.py) |
| portraits (mécanisme §130) | `$D60000` | libre maintenant |

Une première tentative abaissait le plafond des données (fin des données plus tôt en externe) : l'attraction se figeait
(coupure `$8C0490` au lieu de `$8E4AE0`). Abandonnée au profit du déplacement du bloc des animations natives.

### 2.2 Chaîne de construction

1. `outils/prepare_max.py` (contre une construction SANS MAX, `banc_ref`) :
   - copie des sources MAX `max_trad/rosette_code` (copie de la session MAX + gestionnaires d'Eagle, §4) dans
     `prep/src`, bloc d'Eagle déplacé (`org` de 4 fichiers, symboles `$D40000-$D7FFFF` + `$100000`) ;
   - `conv/convertit_max.py` (copie de `agent_conv_max`) : 9 093 réécrites, 121/122 adresses du moteur ;
   - `conv/convertit_frames.py` : blocs externes (Eagle en `$E40000` par `BLOC_EAGLE`) ;
   - `integration_max.s` (généré) : enveloppes des rappels, données de combat par perso, nom, bandeaux, palettes, zones
     réservées ;
   - vasm : CODE à `$3A0000`, DONNÉES à `$B80000`, symboles dans `prep/symboles.json` (+ md5 de la carte : adresses et
     va de chaque instruction).
2. `MAX=1 mame_test.py` (`untranspile/integre_max.py`, 3 crochets + 2 lignes) :
   - `donnees()` : pointeurs et valeurs PAR PERSO dans les données PS2 (§3.2) ;
   - `tables_code()` : après l'étape B, cases des tables de code relogées ; tables déplacées remplies ;
   - `image()` : LEA des tables déplacées, seuil de la grille, blocs externes ; contrôle que la carte est celle de la
     préparation (sinon : relancer `prepare_max.py`) ;
   - `fin()` : code MAX copié en `$3A0000` (zone vérifiée vide).

## 3. Ce que fait `MAX=1` pour un perso (Eagle, `$26`)

### 3.1 Rappels du perso : correspondance tables d'Upper ↔ gabarit PSP

Le PSP appelle le code d'un perso par un gabarit de 39 mots (pointé par l'objet + `0x1A0`, mots 16-27 = routines) ;
l'arcade (et Upper) par 20 tables de 32 (40) longs indexées par `$102`. **Correspondance mesurée** (sites moteur PSP
`lw x,0x1A0(a0) ; lw y,4k(x) ; jalr` appariés aux sites arcade `movea.l #table,a0 ; movea.l (a0,d0.w),a0 ; jmp/jsr`,
même ordre de source ; alternatives confirmées par leurs conditions : `$125` ↔ PSP `0x175`, adversaire `$31` ↔ `0x49`) :

| arcade | Upper (PS2) | site arcade | rappel PSP | Eagle |
|---|---|---|---|---|
| `$DCB92` | `748d98` | `$287CE` (`$293`, `$23E`) | 16 | `psp_1b0b90` |
| `$DCC12` / `$DCC92` | `748e38` / `748ed8` | `$28AE0` (selon `$125`) | 22 / 23 | `psp_1b18bc` |
| `$DCD12` / `$DCD92` | `748f78` / `749018` | `$29C20` (selon `$125`) | 24 / 25 | `psp_1b2f30` |
| `$DCE12` | `7490b8` | `$29D7C` | 18 | `psp_1b0238` |
| `$DCE92` | `749158` | `$29DA4` | 31 (commun `0x5AEFC`) | inchangée (commune) |
| `$DCF12` | `7491f8` | `$2A0A4` (entrée en scène) | 19 | `psp_1b03cc` |
| `$DCF92` | `749298` | `$2A9F6` | 17 | `psp_1b36f8` |
| `$DD192` | `749518` | `$27C54` (initialisation) | racine `0x215040[id]` | `psp_1b3668` |
| `$DD292` | `749658` | `$2B154` (`clr.b $254` = PSP `sb 0x234`) | 20 | `psp_1b1058` |
| `$DD312` / `$DD392` | `7496f8` / `749798` | `$2B19A` (adversaire `$31` ≠ 0 / = 0) | 27 / 26 | `psp_1b3614` / `psp_1b35a8` |
| `$DF412` | `74c038` | `$3289C` | 21 | `psp_1b17f0` |

Toutes ces tables sont relogées par l'étape B (adresses 68K « ordre 68K ») : chaque case `[$26]` reçoit une
**enveloppe** `MAXW_26_<table>` = `JSR MAX_ENTREES ; JMP rappel`. `MAX_ENTREES` appelle `psp_entrees` (miroir des
entrées au format PSP en `$3E0-$3E9`, moteur-integration §1) en gardant D0-D2 et le CCR. Pour les 4 persos :
`outils/persos_max.json` (Maki, Yun, Ingrid déjà calculés).

### 3.2 Tables par perso (données) — toutes `[$26]` valaient les copies de Ryu (`[$00]`), vérifié

| table (PS2) | arcade | contenu pour `$26` |
|---|---|---|
| `748cf8` | `$DCB12` | octets par coup normal (`$2A710`) : 3 décalages + sections PSP s17/s18 |
| `749338` | `$DD012` | 3 pointeurs d'isme → en-tête (5 mots) + boîtes `$90/$94/$98/$9C` (s08-s11) + attaques `$A0` (s12) |
| `7493d8` / `749478` | `$DD092` / `$DD112` | tables `$88` (s13) / `$C0` (s14) |
| `74c5d8` | `$DF892` | table `$264` (s19) |
| `749838` (`T_749838`) | `$DD412` | `ANIM_26_PTRS` (gabarit de 3 ismes × 4 tables, bloc externe) |
| `7498d8`… `74b098` | `$DD492`… `$DE792` | marche (8 o) et sauts (64 o) des 3 ismes : `physique_max_arcade.json` |
| `61c0e0` (`T_61c0e0`) | — | **propriétaire de banque `$00` → `$26`** (sinon Ryu en J2 était dessiné avec les tuiles d'Eagle, vu au banc) |
| `6102b0` | `$32F46` | type de projectile `$26` (libre) → `psp_fils_26` |
| `961b30` / `961c70` | — | nom (frame de type `$0C`, `noms.json`) |
| `9625b8`… `962978` | — | bandeaux défilants J1/J2 JP/US (`bandeau.json`) — sans effet visible, §7 |
| `962b3c` (liste `$10`, entrée 33) | — | icône de la grille (code plan2, attribut `$110F`) |
| `61bfb0` (grille) | — | case (0,2) `$A6 → $26` ; autres « ? » renumérotées `$67→$6B`, `$69→$6D`, `$A8→$AC` (restent des « ? ») |
| image, MIPS `0x255C84` | — | seuil des « ? » `CMPI.B #$26,D0` → `#$2A` |
| portraits | — | mécanisme §130-§131 refait pour plusieurs persos (`integre_max.portraits()`) : 33 poses, palettes de portrait, bloc `$D60000 + $2000·k`, talon des palettes de sélection (un test par ID MAX) |

**Données de combat** (`outils/donnees_joueur_max.py`) : sections de l'entrée `[6]` du pac PSP. Correspondance mesurée
sur Ryu, Ken, Akuma, Chun-Li, Dan (octets identiques à l'arcade). Contrôle `--controle` : Ryu recalculé contre Upper :
`$88` 460/460, `$C0` 116/116, attaques 2 919/2 976 (différences = retouches PSP), `$264` 117/128.
- format image = mots échangés de la section PSP (mots natifs, octets échangés par mot) ;
- **attaques : octets `$12` et `$14` = ×2 dans l'arcade** (sous-type de l'étincelle d'impact, autre champ) ; mesuré
  (Ryu 42+78 entrées, Ken 84+122, Akuma 60+93, sinon nuls). Sans cela : étincelle de classe 4 à sous-type impair →
  erreur d'adresse au premier coup porté (vu au banc).

### 3.3 Tables déplacées et agrandies (déjà pour les 4 persos)

| table | sites | nouvelle place | contenu |
|---|---|---|---|
| classes du réservoir d'effets `$4800(A5)` (`T_60d070`, 40) | 1 LEA (`$ADD4`) | `MAX_T_EFFETS` (64) | 40 entrées d'Upper relogées + classes MAX `$2F-$3A` (Eagle `$33` `psp_1b3904`, `$34` `psp_1b3c20`). Upper occupe `$00-$24` (8 libres seulement) : déplacer évite de renuméroter |
| palettes par perso (`T_6f72b0`, 40 décalages 16 bits signés) | **13 LEA** | `MAX_PAL_ZONE` (64 entrées au MILIEU des blocs recopiés + blocs MAX) | décalages recalculés (portée ±32 Ko) ; `[$26]` = 30 palettes d'Eagle (`palettes_module.bin`) |
| palettes d'EFFETS par perso (`T_700540`, 40 décalages signés) | 2 LEA | `MAX_PALE_ZONE` | idem ; blocs de taille réelle (Chun-Li, Sodom, Vega ont plus de 30 palettes d'effets) ; MAX : 30 premières de `palettes_effets_module.bin`. **Contrôle** : VERSUS Vega–Sodom, même graine, 6 000 images : 19/19 captures identiques au pixel à la référence |

## 4. Code d'Eagle : gestionnaires non traduits par la session MAX (corrigé ici)

**Constat** : `brouillons.py` traduit `[racine(id), racine(id+1))` (`modules.module_bounds`). Or chez Eagle, Maki,
Yun, Ingrid (et Juli/Juni), les **gestionnaires sont rangés AVANT la racine**. Donc `brouillon_eagle.s` contient la racine
d'Eagle, son rappel 17 et ses objets **plus les gestionnaires de Maki** ; `brouillon_maki.s` ceux de Yun ;
`brouillon_yun.s` ceux d'Ingrid. **Les gestionnaires d'Eagle (`0x1B0090-0x1B3668`, 114 fonctions) n'étaient
traduits nulle part** (ils sont dans le « module » de Balrog (alt), `0x25`). Maki, Yun et Ingrid sont complets.

`max_trad/rosette_code/brouillon_eagle_gestionnaires.py` (même `traduire_trad`, copie de `rosette_code`) :
- 114 fonctions, 2 403 lignes, 23 tables de saut, 6 tables `TABD_` nouvelles (`donnees_eagle_gestionnaires.s`) ;
- les fonctions déjà émises ailleurs (`moteur_max_auto.s`, autres brouillons) sont sautées ;
- 13 lignes « ?? » corrigées à la main :
  - `psp_1b07bc` (« l'adversaire aura-t-il une attaque active dans n images ? ») marchait les pas PSP de 10 o :
    réécrite en pas arcade de 20 o (`psp_1b07bc_main.s`) ;
  - `psp_1b33c8` : `traduire.py` prenait `0x1B3450` (créneau de délai d'un JAL, pointé par hasard par un mot de
    données) pour un début de fonction → fonction coupée, étiquettes perdues : réécrite à la main
    (`psp_1b33c8_main.s`) ; c'est le seul cas dans les 4 persos (vérifié) ;
  - `psp_1b24a8` (jamais atteinte) : recopie de champs PSP `0x2D8-0x2DE` sans équivalent retirée ;
  - `psp_1b2e54` = l'effacement de 72 longs depuis objet+`$350` (erreur CONV-MAX §4.2) → `bra psp_1b9544` (version
    corrigée de la session MAX) ;
  - PSP `lb 0x4D` traduit en `move.w $35` (adresse impaire) → octet étendu ;
- `eagle_complements.s` : 7 fonctions moteur PSP manquantes (`psp_cee54`, `psp_cfc88` vides ; `psp_cef74` ; enveloppes
  `psp_cf8cc`, `psp_cf900`, `psp_cf9a4` relues dans le MIPS ; `psp_cf858` neutralisée, seuls appelants jamais atteints) ;
- champ `$127` typé (`$126`, mesuré 15/15, `conv/types_complement.tsv`) ;
- **intros croisées retirées** (`psp_1b03cc`, rappel 19) : contre Sagat `$0B` et Zangief `$10`, Eagle attend des
  étapes de l'intro de l'adversaire qu'Upper ne joue pas → blocage avant le combat (vu au banc : Eagle en J2 contre
  Sagat, état `$0E02` sans fin). Les 3 autres ont le même schéma (Maki contre `$0E`, Yun contre `$21`, Ingrid contre
  `$19`) : à retirer au palier 2.
- Conversion : 4 « NON RÉSOLU » restants dans ce fichier = les accès volontairement écrits en disposition image dans
  `psp_1b07bc` (après `lea 20(a0)`).

## 5. Banc et cœur

- **Banques** : `banc_max/banques_hx/carte.txt` : `perso 38 3826`, `f3826.bin` = `~/.cache/sfa3max/fork/pl26_hx.bin`.
  `plan2.bin` prolongé (index `$A60C+k` → `$5C06C+k`, §130). Tuiles : `HSFA_GFX=…/hsfa_gfx.bin,max_gfx.bin@26D5580,
  max_portraits_gfx.bin@2E03600,hsfa_plans.bin@3000000`.
- **Son** : `HSFA_SON=work/agent_voix_max/roms_voix` (voix MAX v2 ; le code appelle `psp_78408` → `VOIX_26`).
- **FBNeo** : `fbneo/sfa3uhsfa.zip` (38,7 Mo, `HSFA_STRICT`, date fixe), entrée `upper_max` de la copie de
  `paquet_fbneo.py` : blocs `$B04000 $B80000 $BC0000 $C80000 $D60000 $D80000 $DC0000 $E00000 $E40000`, tables
  (106, dont `f3826`), tuiles MAX, ROM son avec voix. **Sans flux ADX** (pas de `HSFA_YDATA` ici). Essayé avec le cœur PC
  (`hsfa_run`, `work/fbneo/fbneo_hsfa_libretro.so`) : Eagle sélectionné au curseur, écran VS, combat Arcade contre Cody
  (`captures/palier1/fbneo_eagle_arcade_contre_cody.png`).

## 6. Validation du palier 1

| essai | résultat |
|---|---|
| option à 0 : ROM | **identique** (`1908ec9e…`, 8 fichiers) |
| option à 0 : `nonreg_ro5_max.sh` (`banc_ref`) | aucune exception / 20 000 ; 00 : 28 manches fin=finie ; 04 : 25 fin=finie ; 02 : 34 fin=finie |
| option à 1 : `nonreg_ro5_max.sh` (`banc_max`) | **identique** à l'option 0 (persos d'Upper non perturbés) |
| sélection au curseur (R,R,U,U,U, bouton) | case (0,2) : icône, portrait, nom « EAGLE » ; `$FF8502 = $26` |
| VERSUS Eagle J1 – Sagat (`$0B`), entrées aléatoires, 20 000 images | 2 manches, **aucune exception** |
| VERSUS Ryu – Eagle J2, 20 000 images | 2 manches, **aucune exception** |
| VERSUS Eagle – Guile (`$20`), 20 000 images | 2 manches, **aucune exception** ; écran de victoire avec le portrait d'Eagle |
| Arcade Eagle (`PERSO=26`), 90 000 images | 32 manches : parcours complet, Bison, **fin** (celle de Ryu), générique, entrée du nom, nouvelle partie ; aucune exception |
| FBNeo (zip d'essai) | sélection, VS, combat Arcade |

Captures : `captures/palier1/` (sélection, 3 planches VERSUS, Arcade contre Bison + fin, FBNeo).

### 6b. Palier 2a : Maki (`$27`)

Mêmes mécanismes (`persos_max.json` : `27` actif) : 13 rappels, données de combat (sections standard), propriétaire de
banque `$1E → $27`, palettes, nom, bandeaux, icône (entrée 35), portraits (**mécanisme du §130 refait pour plusieurs
persos** dans `integre_max.portraits()` : un bloc par perso en `$D60000 + $2000·k`, talon des palettes de sélection
qui reconnaît chaque ID), case (0,4) `$67 → $27`, classes d'effets `$2F/$30/$31`, intro croisée (contre `$0E`) retirée
(`prepare_max.py`, générique pour les 4 persos), banque `perso 39 3839` (`construit_max.sh` refait `banques_hx` à
chaque construction : `perso 38+k -> 3838+k`, `f38xx.bin` = `pl2x_hx.bin`).

Validation refaite sur la ROM livrée (`28239b64…`, Eagle + Maki, palettes d'effets, talon de sélection corrigé) :

| essai | résultat |
|---|---|
| non-régression (`banc_max`) | 20 000 images sans exception ; 00 : 28 manches fin=finie ; 04 (Juli et Juni) : 25 fin=finie ; 02 : 34 fin=finie — identique à l'option 0 |
| VERSUS Eagle–Sagat, Akuma–Maki (J2), Maki–Eagle ; Ryu–Eagle (J2), Maki–Ken, Eagle–Guile (20 000 images chacun) | 2 manches chacun, **aucune exception** |
| Arcade Eagle / Arcade Maki (90 000 images) | 32 / 40 manches, Bison, fin (Ryu / Juli), nouvelle partie, aucune exception |
| sélection au curseur (R,R,U,U,U puis R,R) | Eagle puis Maki : icônes, portraits (couleurs justes), noms ; `$FF8502` = `$26` puis `$27` |
| FBNeo (zip final) | Maki sélectionnée au curseur, Arcade contre Ryu (`captures/palier2/fbneo_maki.png`) |

Premières mesures (avant les palettes d'effets) :

| essai | résultat |
|---|---|
| VERSUS Maki J1 – Ken, 20 000 images | 2 manches, aucune exception |
| VERSUS Akuma – Maki J2, 20 000 images | 2 manches, aucune exception |
| VERSUS Maki – Eagle (deux persos MAX), 20 000 images | 2 manches, aucune exception |
| Arcade Maki, 90 000 images | 40 manches, Bison, fin (celle de Juli : `$27` = copie de Juli), nouvelle partie ; aucune exception |
| non-régression (`banc_max`, Eagle + Maki) | **identique** à l'option 0 : 20 000 images sans exception ; 00 / 04 (combat contre **Juli et Juni**, avec `$27` écrasé) / 02 : fin=finie |

Captures : `captures/palier2/`. Défauts en plus : barre de vie « JULI » et visage de Juli (HUD, §7), écran
d'histoire et écran de la carte de Juli dans la partie Arcade (tables `bios_par_perso` etc. : copies de Juli).

### 6c. Reprise des sources MAX corrigées (11/10) et revalidation d'Eagle et Maki

Sources resynchronisées (`max_trad/rosette_code` = copie de `sfa3max-psp-widescreen/work/re/rosette_code`, sans
`__pycache__` ni `sauvegardes`) : découpage corrigé (gestionnaires dans chaque `brouillon_XX.s`), `gestionnaires_main.s`,
projectiles ×2 (`donnees_projectiles_max.s`), `yun_entree6.md`. Mes fichiers d'avant sont dans `max_trad/mes_fichiers/`.
Écarts gardés ici (documentés) :
- `psp_1b07bc` : MA version (`mes_fichiers/psp_1b07bc_main.s`) remplace celle de `gestionnaires_main.s` dans la
  préparation. Raison : dans l'IMAGE, l'octet 0 d'un pas d'animation porte les drapeaux (`$80/$40`) et l'octet 1 la
  durée (mesuré : fin d'Eagle « 80 16 … », Ryu « 00 05 … ») ; la remarque « octet 0 = durée » de la session MAX vaut
  pour l'arcade, pas pour l'image (la conversion ne réécrit pas cette fonction écrite en disposition image).
- champ objet `$1A.w` (25 sites `move.w $1a(a1),$18(a6)`) : typé mot natif (`conv/types_complement.tsv`, mesuré :
  Upper l'écrit en mot au même déplacement, image `$31F58 MOVE.W D1,$1A(A6)`) ; `convertit_max.py` accepte `s16`.
Conversion : 16 NON RÉSOLUS, tous voulus (fonction écrite en disposition image, lignes mortes après `bra` des intros
retirées, `$1B6B6` des acteurs de fin = palier 3).

| essai (ROM `072b3d36…`, Eagle + Maki) | résultat |
|---|---|
| option 0 | ROM identique (`1908ec9e…`) |
| non-régression (`banc_max`) | 20 000 images sans exception ; 04 : 25 manches fin=finie ; 00 : 28 ; 02 : 34 (identique) |
| VERSUS Eagle–Sagat, Maki–Eagle, Akuma–Maki (J2), 20 000 images | 2 manches chacun, aucune exception |
| Arcade Eagle (graine 3) / Maki (graine 4), 90 000 images | 38 / 40 manches, fin jouée (fin=finie), aucune exception |

Journaux : `essais/r3/`.

## 7. Défauts connus (palier 1, cosmétique)

- **Petit portrait de la barre de vie** (HUD, J1/J2) : tuiles fausses. Il ne vient d'aucune des 5 familles de
  `portraits.json` → **question MAX**.
- **Bandeau défilant** du haut de la sélection : « 1P RYU » sur la case d'Eagle malgré les 4 tables patchées
  (`9625b8`… vérifiées dans l'image) : le bandeau ne lit pas (seulement) ces tables. À chercher.
- **Petit sprite d'aperçu** de la sélection : animation de Ryu.
- **Citation de victoire** et dialogues d'avant-combat (rival, Bison) : ceux de Ryu (`citations_upper.bin` fourni par
  la session MAX, pas encore raccordé).
- **Fin** : celle de Ryu (palier 3).
- Table des positions de projection `$DD212` (`7495b8`, ligne par attaquant, colonne par adversaire), `$E6`
  (`74c538`), positions d'objets attachés (`74c0d8`…) : copies de Ryu pour `$26` (pas de section PSP identifiée).
- Tables d'annulation `$DC9EA/$DCA72/$25204` : copies de Ryu (enchaînements de coups normaux de Ryu).

- **RÉGRESSION trouvée (palier 2a)** : la place 39 (`$27`) n'est PAS une simple copie de Juli dans deux structures :
  les poses de portraits `0x674C00` et la structure des noms / bandeaux `0x961AF0`. Upper y range la variante de
  Juli/Juni (`$103 = $1E/$1F` avec le bit 1 de `$100`) : `CMPI.B #$1E/#$1F ; BTST #1,$100(A4) ; MOVEQ #39,D1 ; LSL #3`
  (va `0x17E000`, `0x193324` pour les poses ; `0x182614` pour les noms). Maki écrase donc le portrait et le nom de
  cette variante. Correction prévue au palier 2b : listes par ID agrandies à 48, ancienne place 39 recopiée en 47,
  les 3 `MOVEQ #39` passés à `#47`.

## 8. Palier 2b : Yun `$2D`, Ingrid `$2E` (validé sur v149)

Décision du coordinateur : **option 2**, n° LIBRES `$2D/$2E` (au-delà des pseudo-ID `$28/$29` de Vega / Chun-Li X-ism et
des `$28-$2C` de la musique), tables par ID agrandies à 48 ; aucun pseudo-ID d'Upper renuméroté.

### 8.1 Moteur d'agrandissement (`untranspile/agrandit_max.py`)
Chaque table lue par ID est RECOPIÉE dans le bloc **`$E80000`** (`ext_e80000.bin`, 285 500 o) ; l'original reste en
place (accès intérieurs inchangés). Rangée de 48 : entrées 0-44 = octets d'origine (40-44 = ce qui suit : les pseudo-ID
lisent exactement les mêmes octets), 45/46 = Yun / Ingrid (valeurs MAX, sinon copie de l'entrée 0), 47 = ancienne
entrée 39. Lecteurs redirigés : `LEA abs.L` (et `MOVE.L / MOVEA.L #imm`, talons natifs `$370000-$3A0000`) de
l'adresse de la table, dans le code de l'image (192 sites) ; pointeurs PS2 des données vers le début d'une table
(citations ×7, `72bdf0`, `76e9fe`). Genres :
- **simples** (tables de `tables_par_id.json` + 20 trouvées ici : `60c680`, `615380`, `61bdb0`, `61b650`, `61d9f0`,
  `615940` (Vega, 42), visages HUD `95c8e0/95ca30/95cb80` (42), `614e20` (citation par gagnant), `61c160` (ID → ID,
  identité posée pour les MAX), tables de FIN `60b220…60b9c0` (44 entrées, index `$1C9(A5)`)) ; paires imbriquées
  `615570/72`, `615790/92`, `61aad0/d2` (lecteurs à +0 et +2) ;
- **à rangées** (constante de rangée 40·e → 48·e) : `616850`, `61b6d0`, `616130` (`ADDI.W #$28`), `620e30`
  (`#$50`), `61ba10` (3 rangées, `#$28/#$50`), noms de la barre de vie `95c700/95c7a0/95c840` (8 `LEA $50(An)` → `$60`),
  `623e50` (3 rangées, 4 `LEA $50(A0)`), structure `967bf0` (4 constantes) ;
- **rel16** (en-tête de décalages + données, décalages +$10) : 11 tables (`67e2a0` citations, `722080`, `748ba0`,
  `748c38`, `74c770`, `74c8e0`, `76e9fe`, `951ba0`, `960090`, `978d1c`, `97a20c`) + `97af50` (2 rangées, `ADDI.B #$28`
  → `#$30`, va `0x40D2BC` : sans elle, exception Yun J2) ;
- **pointeurs vers rel16** : `7495b8` (projections : [attaquant] → structure rel16 [défenseur]) : 27 structures
  recopiées agrandies (sans elle : erreur d'adresse quand Ingrid est la défenseuse) ;
- **structures** (listes 40 × 8 par ID, écart $140) : poses des portraits `674c00`, noms / bandeaux `961af0`, carte du
  monde `967f2a` (listes 2/3 : sans elle, BOUCLE INFINIE sur la carte de l'Arcade d'Ingrid, `$34(A6)` nul), `648bc8` ;
- **aiguillage en ligne** `620630` (40 mots après `JMP (PC,D1.W)`, va `0x33BC38`) : talon en `$3B6540` (ID ≥ $28 →
  entrée 0).
**Régression du palier 2a corrigée** : la place 39 (`$27`) des poses de portraits et des noms est la variante de
Juli/Juni (`$100` bit 1) ; ancienne entrée 39 → 47, les 3 `MOVEQ #39,D1` (va `0x17E000`, `0x193324`, `0x182614`) → `#47`.
Ignorées (aucun lecteur dans l'image) : `628320`, `628370`, `628470` (natifs), `60d070` (déjà déplacée).
Recherche des tables : statique (`outils/scan_id.py`, constantes de rangée), dynamique (`lua/espion.lua` +
`outils/diff_index.py` : lectures d'une même instruction à `base + 45·e` avec Yun et `base + 38·e` avec Eagle),
bissection (`outils/bissecte.sh`, `AG_SEL`) contre la partie 04 de référence (une divergence = table mal agrandie :
`623e50` trouvée ainsi).

### 8.2 Données des persos et habillage
- Yun / Ingrid : mêmes tables qu'Eagle (§3) aux entrées 45/46 ; propriétaires de banque `$24/$25` ; grille
  (6,4)=`$2D`, (6,2)=`$2E`, curseur `T_61be70` (déjà 48 entrées) ; seuil des cases « ? » `CMPI.B #$30` ; projectiles
  (Ingrid type `$2A` → entrée 42 de la copie de `T_6102b0`) ; palettes d'Ingrid = `palettes_module_upper.bin` (session
  MAX, 6 × 5) ; entrée [6] de Yun = décalage −5 (confirmé par la session MAX).
- **HUD** (`outils/hud_apercu_max.py`, tuiles dans `max_plus_gfx.bin` chargé à `$2E45000` = tuiles `$5C8A0+`, encodées
  par `gfx_fork.encode` de la session MAX) : noms de la barre de vie (emplacement 1, plan2 prolongé, code +$1C00),
  visages (un objet w × h, attr `(h-1)<<12 | (w-1)<<8 | r`, J2 x = 384 − 16w), **aperçu de sélection** (`T_97ca90` →
  `APS_xx` (3 décalages) → pas convertis + frames de type 2 ; banque commune `f351` prolongée : codes locaux `$7000+`,
  alignés sur 16), **jauges** garde / étourdissement (`74c680` / `74c6a8` : Eagle 40/72, Maki 40/68, Yun 40/64,
  Ingrid 40/68), **citations** (`citations_upper.bin` ajoutées à la copie de `67e2a0`).
- Correctifs locaux des sources MAX (`prepare_max.py`, signalés) : `psp_cfb6c` : `andi.w #$ff,d1` (index octet ;
  bits hauts non nuls → erreur d'adresse, Ingrid contre Yun/Maki) ; octet `$0D` des pas = `$0B/$0C` (Eagle, 24 pas),
  `$0D/$0E` (Ingrid, 4 pas) hors de la plage d'Upper (0-9, aiguillage de 6 entrées en `$40D4`) → 0 (exception Arcade
  Eagle sinon) : **sens à donner par la session MAX**.

### 8.3 Validation (v149, `banc_max4`)
| essai | résultat |
|---|---|
| option 0 | 8 fichiers = `work/references/v149/ro5` (`7898814c…`) |
| non-régression | 20 000 images sans exception ; 00 : 28 m., 04 : 25 m., 02 : 34 m. = option 0 ; **04 identique image par image** à `banc_ref` (Juli et Juni) |
| 20 VERSUS (20 000 images) | Yun/Ingrid J1 et J2 contre Ryu, Ken, Akuma, Sagat, Juli, Juni, Rose, Rolento, $0C, $0E, $14, Eagle, Maki, et entre eux ; Eagle/Maki : 2 manches chacun, **aucune exception** |
| Arcade (90 000 images) | Eagle 36 m., Maki 40 m., Yun 39 m., Ingrid 38 m. : parcours, Bison, fin (celle de Ryu / Juli), nouvelle partie, aucune exception |
| FBNeo (zip `fbneo/2b/sfa3uhsfa.zip` `855f8878…`, paquet du DÉPÔT + entrée `upper_max`) | Yun et Ingrid au curseur, prologue, combat contre Cammy, HUD |
Captures : `captures/palier2b/`. ROM : sz3ud.03c `10d62c98`, sz3ud.04c `d169a872`, sz3.05c `dc94c146`, sz3.06c `a3694328`,
sz3.07c `e17a3b4c`, sz3.08c `2570d06a`, sz3.09c `465c8132`, sz3.10b `c188839c` ; `ext_e80000.bin` `9480f1b0`.

### 8.4 Restes (cosmétiques)
Bandeau défilant « 1P RYU » de la sélection ; prologue et écrans d'histoire de l'Arcade (ceux de Ryu / Juli) ; fins
(palier 3) ; tableau RESULT du VERSUS (lignes des 40 persos d'Upper seulement : les compteurs MAX vont aux places
`$24/$25/$26/$27` du propriétaire de banque, sans débordement) ; pose 32 (bande partagée `A[pose-32+ID]` des portraits)
non posée pour `$2D/$2E`.

### 8.5 Zones occupées (pour `re/allocations.tsv`)
image : code MAX `$3A0000-$3B6536`, talon 620630 `$3B6540-$3B655E`, talon des palettes de sélection dans le trou après
la fin du code traduit (`$A0BA0`) ; blocs : données MAX `$B80000-$BA8E37`, animations natives d'Upper déplacées
`$BC0000-$BFFC4F`, portraits `$D60000-$D67FFF` (4 × `$2000`), Maki `$D80000-$DB11E9`, Yun `$DC0000-$DF1667`, Ingrid
`$E00000-$E308AB`, Eagle `$E40000-$E70903`, tables agrandies `$E80000-$EC5B3B` ; `$D40000-$D7FFFF` (ancien bloc
d'Eagle) : **libre** (l'ancien schéma `$D40000 + $40000·k` n'est plus suivi pour Eagle) ; tuiles `$2E45000` (région
graphique étendue, 1923 tuiles), banque commune locaux `$7000-$7653`.

### 8.6 Retours utilisateur sur le zip 2b : son, brouillons régénérés (17/10)
- Son : `T_74C538[ID]` = `SONS_PAS_26..29` de MAX (`sons_pas_max.s`), complétés à 256 index de 8 o (lecture
  au-delà = muet) ; `SONS_COMMUNS` de `moteur_max_main.s` ; `psp_78408` lit `$103(a0)` (disposition image).
  Journal QSound (`lua/sons.lua`, `outils/cmds_son.py`) : musique seulement au décor (0x0009) et après le match
  (ff07/0x0004), comme Ryu sur banc_ref ; voix MAX présentes. WAV : `captures/son/`. Zip `fbneo/2b3` bbcaa5bb.
- Voix MAX du 17/10 15:47 (14 voix reliées) reprises : banc_max4 04c 012a27d0 (03c 3b59242b inchangé).
- Revalidation (brouillons régénérés + voix) : 16 VERSUS sans exception (2 manches chacun), Arcade 26 37 m. (avant 36),
  27 40 m. (identique octet pour octet à avant), 2d 38 m. (avant 39), 2e 38 m., toutes jusqu'à la fin ; nonreg OK,
  Arcade 04 identique à a04_ref.
- Maki : QCF+K = manip PSP n° 2 (`psp_1b561c`, `$AA`=2, course avant) ; QCB+K = manip n° 4 (`psp_1b5888`, `$AA`=$14,
  course arrière, 17 images, animations $DA46AE-$DA4726), sprites propres, pas d'exception (`captures/revalidation/`).
  Dans les définitions arcade, le bit 1 des directions = AVANT, le bit 2 = ARRIÈRE (n° 2 = 4,6,2+K = QCF+K).
  Le coup normal ($DA49DE) qui suit vient d'un appui P1 de tournee_max.lua (entrée $0100), pas du jeu.
- Ingrid : le projectile s'affiche et atteint Sagat, mais ne le touche toujours pas (Sagat à 1 PV jamais KO ; Ryu le
  met KO dans le même essai).
- Outil : `lua/coup.lua` (manips de J1, directions AR/AV selon $FF840A, ORIENT=1) ; `lua/coup_etat.lua` (journal),
  `lua/coup_fiche.lua` (écritures dans les fiches de manip). Piège : les objets champ() de sol2 sont distincts à
  chaque appel ; la table des entrées doit être indexée par le nom du champ (sinon les diagonales se perdent).

- Portrait d'Ingrid (R_DIRECT) : `portraits()` lit `variantes.attributs` ; si « direct », bloc de base = palettes de
  fichier 3-5 en 0-2 et palettes de victoire 0-2 en 3-5 (attributs du 320x160 + 3) ; palettes de sélection : r -> 4v + r.
  Contrôle : 6 boutons = orange (B1), lavande (B2), noir (B3), bleu (B4), vert (B5), rose (B6), conforme à
  ingrid_variantes.png ; victoire inchangée (orange). Aperçu régénéré (1034 tuiles) repris : jambes présentes.
  max_plus_gfx.bin = 2490 tuiles (G_PLUS $5C8A0, HSFA_GFX $2E45000-$2E92D00).
- Échelle : en garde dans Upper, Ryu ~94 px, Maki ~98, Eagle ~102 (penché), Ingrid ~87 : proportions conformes
  aux hauteurs PSP (Ryu 90, Maki 101, Eagle 110 en médiane) ; aucun facteur à appliquer (`captures/revalidation/`).

- Tirs (17/10, correctif MAX BOITES_TIRS : tables_explicites_{ingrid,yun,eagle}.s) : le tir d'Ingrid met Sagat (1 PV)
  K.O. (« SPECIAL FINISH »). Pas du tir relevés en mémoire (ordre IMAGE, `lua/pas_tir.lua`) : +8 = attaque, +9 = index
  dans $88 (Upper lit `MOVE.B $9(A0)` -> ×4 -> $88(A6), image $2B31E) ; Hadoken de Ryu : 05/01 puis 01/01 ;
  Ingrid : 01/01 sur les premiers pas, puis 00/01 et 00/00. L'échange fait par MAX est donc le bon.
  Type d'objet des tirs ($2) = ID du perso (Yun $2D, Ingrid $2E au lieu de $27/$2A) : correctif dans prepare_max.
  Tir de Yun (↓ ↙ ← + P, manip n° 3) : Sagat à 1 PV mis K.O. à distance (captures/revalidation/yun_tir_ko_sagat.png).
  Tir d'Eagle = riposte du contre 11 : testable avec les contres. Pas d'Ingrid à attaque 0 : voulus (MAX).
  TYPE_PROJ $2D/$2E repris dans la source MAX : correctif local retiré.

### 8.7 Retours console sur le zip 2b4 (17/10 soir)
- a) Cris de Ryu : table des BASES DE CRIS par ID d'Upper = PS2 0x613490 (40 mots ; cri = base + 0..6, côté 2 +$500 ;
  Ryu $0300, Sagat $0460 ; même table que ro9 0x3D9A90). Entrées $26/$27 = $0300 (Ryu), $2D/$2E (copie agrandie) =
  entrée 0. Aucun cri MAX n'existe encore dans la ROM son : il faut 4 blocs de 7 commandes (session MAX + agent voix).
- b) Portrait de victoire : le bloc 0x72BDF0[ID] = 48 palettes = 6 COULEURS × 8 (Ryu : groupes de 8) ; seul le groupe 0
  était rempli (groupes 1-5 = Ryu). Corrigé : groupe v = portraits_victoire_variantes.bin (k·v + r) + palettes de
  sélection de la couleur v (4v + r) aux emplacements de sélection ; Ingrid (R_DIRECT) : sélection 0-2, victoire 3-5.
- e) Course de Maki devenue un dash : compteur PSP +0x3A = demi-mot, lu aussi en octet (lb = octet BAS) ; les brouillons
  testent « $3a(a6) » = octet HAUT (0) -> fin dès la 1re image (les anciens brouillons testaient « octet haut − 1 » ≠ 0,
  juste par chance). Correctif PROVISOIRE (prepare_max) : accès octet $3A(a6) -> $3B dans les 4 brouillons (Eagle 10,
  Maki 28, Yun 8, Ingrid 9). Contrôle : course de Maki identique image par image à l'ancienne ROM 072b3d36 (400 images).

### 8.8 Lot 2b4 (suite), palier 3 en cours, contres (17/10 nuit)
- g) Portrait de Ryu (bande noire, depuis le palier 1) : CORRIGÉ. Les poses >= 32 de 0x674C00 sont une bande PARTAGÉE
  A[pose − 32 + ID] ; y écrire la pose 32 (yeux 96x16) de $26/$27 abîmait d'autres couples (pose, ID). Plus d'écriture
  dans la bande (les yeux VS des MAX lisent A[ID] : talon à faire plus tard).
- c) d) f) : données / traduction MAX (frames $1140 de Yun ; aperçu d'Ingrid à 1 palette ($37FC2, J2 = emplacement
  suivant), contours alpha des tirs ; super d'Eagle bloquée état $10/06, pas $E64208).
- Bio (écran d'histoire) : illustration = fichiers natifs par perso T_PERSO 0x628470 (gfx 419-454, anim 486-521) ->
  $37AF00 -> $C0BC(A5) ; carte « anim <long échangé> <gfx> » + banques_hx/f4xx.bin.
- Palier 3 (banc_max5, MAX_FINS=1) : fin d'Eagle jouée jusqu'au bout sans exception ($9 ×2 provisoire, x9 corrigés par
  fins_integration.CORR_SCRIPT) ; Terre / magenta toujours faux après suppression du x9 initial (question MAX).
  Table des jeux de palettes $8008 : liste de pointeurs vers des descripteurs de 4 mots (format à établir).
- CONTRES (MAX_CONTRES=1) : contres_max.s converti (bases forcées A1/A3/A6, objet $EA u8) ; talon sur l'aiguillage
  image $40D4 (4-9 d'origine, 11-14 -> CONTRE_MAX_11..14, 10 / >= 15 -> coup normal) ; octets $0D 0B-0E gardés.
  Contrôle : contre 11 d'Eagle (→ ↓ ↘ + P) face aux Hadoken de Ryu -> tir d'Eagle, Ryu K.O. (« SPECIAL FINISH ») ;
  6 VERSUS sans exception (essais/vs5).

### 8.9 Palier 3, état au 17/10 nuit (banc_max5 : MAX_FINS=1 MAX_CONTRES=1)
- Fins des 4 branchées (FIN_MODELE 26/2E -> $10, 27 -> $07, 2D -> $06) ; x9 initiaux retirés ; jeu de palettes neuf
  d'Eagle (source n° 13 = 0x60B594, liste 24 jeux du modèle + jeu 24, x9 -> $18).
- EXPLO_PAS relogé (0x65B33C) ; table d'état 2 de la classe $4F (image $4C522) routée pour le sous-type $19.
- Eagle et Ingrid : fins jusqu'au bout ; Maki 43132 / Yun 45415 : exceptions restantes (après le générique entamé).
- Visuels : sprites de décor FD.. à codes locaux de l'emplacement 4 = palier 4 (fichier de fin MAX à construire).
- Cris : 0x613490 / 0x613440 (déjà agrandies) ; ROM son agent_son_max/roms_son_max.
- Aperçu de sélection : talon_apercu_pal (palettes d'aperçu propres aux persos MAX, chargeur image $37FF0).
- Effets créés par $1C368 : $1A recopié du créateur (prepare_max).

### 8.10 Réponses MAX du 18/10 soir, palier 4 (lot 2b7, banc_max5)
- **Contre 13 d'Ingrid** : la saisie `psp_1c3db4` / `psp_1c3e60` (écrite à la main dans `moteur_max_main.s`) adresse la
  victime par A0, que la passe ne type pas (« CONV NON RÉSOLU ») : octets laissés en disposition arcade. `$5F` arcade
  (minuterie, `$5E` image, décomptée en `$4EDBC`) était écrit en `$5F` image, recopié par l'ATH (`$308AC`) dans `$328` de
  l'adversaire puis pris pour index (`$1CFEB24` -> `$7(A6)` = `$FF`) : erreur d'adresse à l'image 2765. CORRECTIFS de
  `prepare_max.py` : `$5F`->`$5E`, `$25D`->`$25C`, `$5D`->`$5C` ; `psp_d014c` (chope de course de Maki) `$55`->`$54`.
  Contre 13 : prise puis riposte qui touche ; contre 14 : déclenché sur balayage de Ryu, Ryu réagit.
- **Entrées** : recalcul de `$3E2` (quand `$378` = 0) au codage de `psp_entrees .conv` (poings bits 8-10 -> `$10-$40`,
  pieds bits 12-14 -> `$80-$200`). Course de Maki : la chope au contact sort (états `$12-$18`) ; glissade et bond non :
  le sous-état `$08` (`psp_1b6424`) ne teste aucun bouton, les manips (`psp_1b5214` -> `psp_64a34`) tournent avec
  `$3E2` = `$0100` sans effet (trace `essais/rev3/mk_tr.log`).
- **Effets MAX** : `EFFET_W_xx` = gestionnaire, puis `move.b #$10,$9(a6)` (classe d'affichage `$10` -> `$19ED0`, au lieu
  de `$18` -> `$1DFF2` qui refait l'animation par type), puis `$19D9A` ; activé par défaut (`MAX_EFFETS_AFF=0` pour
  l'ôter). VERSUS Eagle-Ryu (ancien plantage 2340) et 3 autres : 20 000 images sans exception.
- **Témoin** : le banc MAME et le cœur FBNeo éclatent les blocs tuile par tuile (local `c + cx + 16·cy` -> table) ;
  `outils/compare_temoin.py` compare au pixel natif et témoin : 338 / 391 identiques, écarts dans les données MAX.
- **Palier 4** : `IM.bio` ajoute, par fin MAX, une copie du fichier d'animation de fin du modèle à une adresse propre
  (n° fictifs `3978/3979/3985/3986`, ligne `anim` de `carte.txt`) dont la banque est la table `decor_<id>_hx.bin`
  (`hud_apercu_max` §5 : `converti/plXX/fin/decor/tuiles.bin` à la suite dans `max_plus_gfx`) ; `fins_fichiers` y envoie
  le chargeur de fin. Jeu de palettes neuf d'Eagle : palettes 0-19 (toutes celles des frames FD). Reste : plans du
  modèle encore affichés ; homologues Upper de `$81522` (arcade `$A5B22`, classe `$48`, index `$70`, pas en `$50`) et
  `$301FA2` (ND = 0 provisoire) ; jeux de palettes des 3 autres fins.

### 8.11 Palier 4, deuxième passe (18/10 nuit ; option MAX_P4, défaut 1)
- `conv/convertit_frames.py` assemble `decor_fin_<perso>.s` dans le bloc du perso (+`$38000`) : frames FD et positions
  comme les frames (longs à moitiés échangées), table `FIN118_xx` inchangée, pas de 8 o avec octets échangés par paire.
  Avant, ces fichiers n'étaient PAS assemblés : `FIN118_xx` visait une zone vide.
- Table de classe `$48` (homologue d'Upper de `$81522` = PS2 `0x960180`, 12 entrées dont la 12e nulle) : copie
  agrandie (`agrandit_max` rel16n, entrées nulles gardées), `ND26_4` / `ND27_4` / `ND29_4` = 12 / 13 / 14, pas recopiés
  du bloc assemblé (`integre_max.fins`).
- Plans vides (`FIN_PLANS_VIDES`, x6 « 0, 1, 2 » des 4 scripts) ; jeux de palettes neufs des 4 fins (source n° 13
  partagée `FINMAX_PAL_SRC`, descripteur répété 4 fois car le x9 en lit 4, tous les x9 MAX vers le jeu neuf).
- Résultat : fond magenta et sprites du modèle en mosaïque ; avec `MAX_P4=0` (plans du modèle), les images de la fin
  MAX sont déjà affichées par les plans. Lot 2b7 livré avec `MAX_P4=0` (banc_max6), essai `MAX_P4=1` dans fbneo/2b7_p4.
- Saisie d'Ingrid / chope de Maki : A0 annoté par la session MAX, correctifs provisoires retirés (accès convertis en
  `$5E`, `$25C`, `$5C`, `$54`).

### 8.12 Course de Maki (lot 2b8)
- Défaut confirmé (↓ ↘ → + pied vers l'adversaire) : la course s'arrêtait au bout de 17 images sans suite. L'état 1
  (`psp_1b6100`) voyait encore le pied de lancement dans `$3E2` deux images plus tard : Upper garde l'appui dans `$378`
  plusieurs images, et ne met pas `$374` à jour pendant certains spéciaux. Le petit pied faisait donc l'arrêt
  (`psp_1b6a58`). De plus, la logique fait parfois 2 passes pour un même compteur d'images.
- `MAX_ENTREES` : front `$370 & ~précédent` calculé à chaque passe du rappel des manips (`MAX_ENTREES_TICK`, rappel
  `749658`), repris par les autres rappels ; recalculé si le compteur `$FF80B4` change sans passe de manips. Champs
  `$3F6` / `$3F8` / `$3FA` du joueur (libres dans Upper et dans le code MAX).
- Glissade (moyen pied, `$7` = 6, chope si contact `$5B`) et bond (gros pied, `$7` = 8) vérifiés au banc.
- Palier 4 selon la recette MAX (plans du modèle sauf Maki ; jeux neufs `[$34, n, 32·8k, 8]` par jeu PSP ; x9 du jeu 6
  d'Eagle -> `$16`) : `banc_max5` / `fbneo/2b8_p4` ; visuels encore faux.

### 8.13 Fins, recette MAX (lot 2b9)
- Palettes : scène `1108` (chargeur `$26710`) = 4 jeux (a5 OBJ 30 palettes, a6-a8 scroll1-3). Seul a5 est remplacé par un
  jeu neuf `[$34, n, 32·8k, 30]` (`K_1108` : Eagle 1,0,3,3,3,3,0,1,1,0,0,0 ; Maki 0 ; Yun 0…0,1 ; Ingrid 0,0,1,1,1,2,2,2) ;
  x9 initial retiré ; x9 final d'Eagle `$16` ; x9 du jeu 1 de Maki -> jeu neuf 1.
- Emplacement 4 : fichier propre par fin = table de banque du fichier de fin du modèle (gfx de T_FIN : f403 pour `$10`,
  f396 pour `$06`) puis tuiles des FD ; codes des frames FD décalés de N à l'assemblage.
- Plans : ceux du modèle, sauf Maki (plans vides).
- Constat : couleurs justes pour les invités (Guile, Bison) ; scènes de jeu PSP k >= 1 encore décalées (règle 8k à
  vérifier) ; quelques mosaïques restantes.

### 8b. Paliers 3-4 (fins, décors des fins) : ce qu'il faudra

Rien n'est branché : Eagle joue la fin de Ryu, Maki celle de Juli (tables de fin `$26/$27` = copies). Le code des
acteurs de fin MAX est déjà assemblé (`acteurs_fins_max.s`, `acteurs_fins_main.s` dans le code MAX) mais rien ne
l'appelle. À faire : sous-types MAX des classes `$4B` (`$52-$57`), `$4F` (`$19`), `$49` (`$2B-$2E`) dans les aiguillages
des acteurs ; scripts de fin (`converti/plXX/fin/script_fin_XX.s`) dans les tables de fin d'Upper (`0x60B220`, `0x60B5A0`,
`0x60B700`, `0x60B860`, `0x60B9C0`, 41 entrées, n° de fin `$1C6`) et le talon du chargeur de fin (`afin`) ;
`T_619b50[$26..]` → `FIN_ANIM_2x` ; `T_61c0e0` (fait) ; `EXPLO_PAS` relogé sur Upper ; les 4 NON RÉSOLUS de la
conversion (`$1B6B6`, `$1A.w` des acteurs) ; décors (`decor_fin_*.s`, tables `$81522` / `$301FA2` / `$2F4284` à
retrouver dans Upper, banque de l'emplacement 4 : lignes `anim` de `carte.txt`).

## 9. Questions pour la session MAX

1. **Gestionnaires d'Eagle** (§4) : `brouillons.py` découpe les modules à la racine, or les gestionnaires des persos
   MAX sont AVANT leur racine. Les 114 fonctions d'Eagle `0x1B0090-0x1B3668` ont été traduites ici avec votre
   traducteur ; merci de les relire (et de corriger le découpage pour les prochaines passes).
2. `traduire.py` prend `0x1B3450` (créneau de délai, pointé par un mot de données `0x2C8ED0`) pour un début de fonction.
3. Données de combat : les octets `$12/$14` des attaques sont ×2 dans l'arcade (§3.2) — à reporter dans vos outils.
4. Intros croisées (Eagle/Sagat-Zangief, Maki/`$0E`, Yun/`$21`, Ingrid/`$19`) : retirées ici ; à garder si vous voulez
   les recréer côté Upper (il faudrait la partie de l'adversaire).
5. Portrait de la barre de vie (HUD) des 4 persos : famille manquante dans `portraits.json`.
6. Yun : correspondance de son entrée `[6]` (boîtes, attaques) avec les tables arcade (gabarit rempli par `0x6A638`).
7. Ingrid : répartition de ses 48 palettes en groupes de 5 (6 couleurs) compatibles avec le moteur d'Upper.
8. Petit sprite d'aperçu de la sélection et visage / nom de la barre de vie (tables HUD `0x95C7A0`, `0x95C840`) : graphismes
   MAX à fournir.
9. Citations de victoire (`citations_upper.bin`) : format attendu par la table `0x67E2A0` (décalages relatifs) à confirmer.
(Points 3, 5-9 : répondus / livrés par la session MAX et intégrés au palier 2b.)
10. **Octet `$0D` des pas** (type de réaction quand le perso est touché) : Eagle a 24 pas à `$0B/$0C`, Ingrid 4 à
    `$0D/$0E` ; Upper n'accepte que 0-9 et `$FF` (aiguillage de 6 entrées pour 4-9, image `$40D4`) : ramenés à 0 ici
    (exception sinon). Quel est leur sens côté PSP, et quelle valeur d'Upper leur correspond ?
11. `psp_cfb6c` : l'index D1 est un octet (`lbu`), mais les appelants le chargent par `move.b` sans effacer les bits
    hauts ; corrigé ici par `andi.w #$ff,d1` en tête (à reporter dans `moteur_max_main.s`).
12. Prologue / écrans d'histoire et fins de l'Arcade : textes et scripts MAX à fournir (palier 3).

## 10. Fichiers

| fichier | rôle |
|---|---|
| `construit_max.sh`, `lance_max.sh` | construction (préparation + MAX=1), lancement du fork |
| `untranspile/` | copie du traducteur partagé ; seuls changements : `mame_test.py` (crochets `MAX`), `integre_max.py`, `nonreg_ro5_max.sh` |
| `outils/prepare_max.py`, `donnees_joueur_max.py`, `persos_max.json`, `tables_par_id.py/.json`, `planche.py` | préparation, données de combat, rappels par perso, tables à agrandir (palier 2b), planches |
| `conv/` | copies de `convertit_max.py` (sources et fichiers d'Eagle), `convertit_frames.py` (bloc d'Eagle déplaçable), tables |
| `max_trad/rosette_code/` | copie des sources MAX + `brouillon_eagle_gestionnaires.py/.s`, `psp_1b07bc_main.s`, `psp_1b33c8_main.s`, `eagle_complements.s` |
| `lua/` | `tournee_max.lua` (copie de `tournee.lua` : code MAX, `PERSO2`, `ALEA`, `SEQ`), `trace_etat.lua`, `wp_etat.lua`, `etat_ram.lua`, `objets.lua` |
| `fbneo/` | `paquet_fbneo.py` (entrée `upper_max`), `sfa3uhsfa.zip` |
| `diffs/` | diffs contre `scripts/untranspile`, `agent_conv_max`, `work/fbneo`, `work/mame/tournee.lua` |
| `banc_ref/`, `banc_max/`, `prep/`, `essais/`, `captures/` | constructions, préparation, journaux, captures |
