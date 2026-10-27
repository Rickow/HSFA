# Cœur FBNeo « HSFA » : une fiche par patch

Complète [coeur-fbneo.md](coeur-fbneo.md) (fonctionnement) et [`patches/fbneo/README.md`](../../patches/fbneo/README.md)
(ordre d'application, construction). Chaque fiche dit : le problème, la solution, les alternatives écartées (avec
leur source), les fichiers touchés, et comment couper ou vérifier le patch. « § » renvoie au journal
`docs/journal/HANDOFF.md`. Quand une source ne cite aucune alternative, la fiche le dit.

Les numéros sont ceux du tableau du README (colonne « # »). Les rapports anciens disent « patch 8 » pour la ligne 8
(`0004-…`), « patch 10 » pour `0006-…`, etc.

Vérification commune à tous : `scripts/validation/nonreg_coeur.sh` contre un cœur de référence (`IDENTIQUE` attendu
sur SFA3, Upper et Hyper, sauf changement voulu ; depuis le patch 15, avec `HSFA_OMBRES=0`).

## 1. `fbneo-hsfa.patch` — pilotes SFA3 et Upper

- **Problème** : jouer les programmes retraduits sur console, sans MAME ni scripts Lua.
- **Solution** : `cps_hsfa.cpp` reprend en C++ les trois couches Lua du banc (`banc_mem`, `banc_plans`,
  `banc_sprites`) et les extensions du fork `sfa3hx` (ROM graphique étendue, codes d'objet sur 20 bits, bases de
  plans, son hybride). Crochets dans `cps*.cpp`, tous derrière `HsfaMode`. ROM sans CRC cherchées par nom. IRQ du Z80
  à 250 Hz comme MAME. États de sauvegarde. Lanceur `hsfa_run`. Sous-ensemble `Makefile.hsfa`.
- **Alternatives** : garder MAME comme produit final, écarté au §109 (le fork reste l'outil de développement, FBNeo le
  cœur pour Android / RetroArch). `Cps2Turbo` de FBNeo regardé, non repris : format différent du fork (§136).
- **Fichiers** : `cps_hsfa.cpp` (nouveau), `d_cps2.cpp`, `cps.cpp`, `cps.h`, `cps_mem.cpp`, `cps_obj.cpp`,
  `cps_run.cpp`, `cps_rw.cpp`, `cps_scr.cpp`, `qs.cpp`, `libretro.cpp`, `Makefile.hsfa`, `jni/Android.mk`,
  `hsfa/hsfa_run.c`, `hsfa/paquet_fbneo.py` (vieille copie).
- **Couper / vérifier** : seuls les pilotes `*hsfa` posent `HsfaMode` ; les autres jeux CPS gardent le code d'origine.
  `HSFA_STATS=1` affiche les statistiques des listes d'objets. Validation d'origine : §136.

## 2. `fbneo-hsfa-widescreen.patch` — cœur 16:9

- **Problème** : écrans larges ; le décor des jeux existe au-delà des 384 px de la CPS2.
- **Solution** : `-DHSFA_WS` passe les pilotes HSFA à 448 × 224 et 16:9 ; FBNeo recentre plans et objets. Cœur
  distinct « FinalBurn Neo HSFA Widescreen », **mêmes noms de pilotes**, donc mêmes zips (§139).
- **Alternatives** : aucune n'est documentée.
- **Fichiers** : `d_cps2.cpp`, `Makefile.hsfaws`, `libretro.cpp`.
- **Vérifier** : centre de l'image identique au pixel au 4:3 (520 captures, §139). Défauts connus : coeur-fbneo.md §11.

## 3. `fbneo-hsfa-ws-flux.patch` — flux musique ADX

- **Problème** : des musiques n'existent qu'en flux sur le disque PS2 : persos d'Upper (`0030-0036`), musiques ZERO,
  ZERO 2 et ALPHA d'Hyper. Le Z80 ne les connaît pas.
- **Solution** : `hsfa_flux.h` (commun avec le fork) lit le `Y_DATA.BIN` de l'utilisateur. Interception à
  `$61801F = 0` ; une musique jouée en flux devient `FF05` pour le Z80 ; `FFxx` appliqués au flux. DIP
  « PS2 music » : `Off`, `Missing tracks only`, `All tracks`.
- **Alternatives** : laisser passer le code au Z80 (il garde sa musique : essai `z_a`) ; envoyer `FF00` (coupe aussi
  les voix : essai `z_i`). L'intro `0001` n'est jamais en flux : ses repères `$618021` viennent du Z80
  ([FLUX](../rapports/FLUX.md) §1.2).
- **Fichiers** : `hsfa_flux.h` (nouveau), `cps_hsfa.cpp`, `cps_mem.cpp`, `qs.cpp`, `cps.h`, `d_cps2.cpp`.
- **Couper / vérifier** : DIP `Off`, ou `HSFA_FLUX=0` sur PC ; journal `HSFA_FLUX_LOG=<fichier>`. En mode 1 sans
  musique hors QSound, WAV identique au cœur d'avant ([FLUX](../rapports/FLUX.md) §3).

## 4. `hyper-HSFA-pilote-sfa3hhsfa-Hyper-Street-Fighter-Alpha-mod.patch` — pilote Hyper

- **Problème** : Hyper (`ro9`) a des blocs externes en `$940000` et `$C84000`, une banque commune 545, et presque
  toutes ses musiques en flux.
- **Solution** : pilote `sfa3hhsfa`, mécanismes d'Upper (`HsfaMode = 2`) plus `HsfaHyper = 1`. La base des blocs
  externes se déduit de la taille de `hsfa_ext.bin` (`$F00000` − taille). DIP musique sur `All tracks`. Crochet
  d'essai `HSFA_NOROUL`. `hsfa_run` : `PILOTE=hyper`.
- **Alternatives** : un premier pilote avait un mode propre (`HsfaMode = 3`) ; la version livrée réutilise le mode
  d'Upper ([FBNEO-HYPER](../rapports/FBNEO-HYPER.md) §1-§2).
- **Fichiers** : `d_cps2.cpp`, `cps_hsfa.cpp`, `cps.h`, `hsfa/hsfa_run.c`, et les fichiers générés `gamelist.txt`,
  `driverlist.h` (à exclure à l'application : seul patch de la chaîne qui les contient).
- **Vérifier** : tournée VERSUS de 13 000 images contre le fork : mêmes 14 choix, 17/26 captures identiques au pixel
  ([FBNEO-HYPER](../rapports/FBNEO-HYPER.md) §4).

## 5. `0001-HSFA-rejeu-QSound-…` — sons SFA1 / SFA2, données dans le zip

- **Problème** : les versions ZERO et ZERO 2 d'Hyper doivent avoir leurs voix et bruitages d'origine. La ROM QSound
  de 16 Mo est pleine, le pilote Z80 n'a plus de numéro de commande libre.
- **Solution** : un 2ᵉ QSound (`hsfa_qsound.h`) rejoue chaque son tel que le pilote d'origine l'écrivait
  (`hsfa_rejeu.h`, 1 323 sons). Le Z80 reçoit un code vide. Toutes les données (flux, rejeu) sont des membres
  **stockés** du zip, lus sur place.
- **Alternatives** : (a) ROM QSound étendue à 32 Mo, écartée : il faudrait opérer le pilote Z80 (ni numéros libres,
  ni entrées libres, ni bit de banque) ; lecteur d'échantillons « maison », écarté : volume, panoramique, écho et
  séquences à réécrire ([SON-HYPER-ROM](../rapports/SON-HYPER-ROM.md) §12.1). Données hors du zip : remplacé par
  « tout dans le zip », décision de l'utilisateur ([REJEU-FBNEO](../rapports/REJEU-FBNEO.md) §0).
- **Fichiers** : `hsfa_qsound.h`, `hsfa_rejeu.h` (nouveaux), `cps_hsfa.cpp`, `hsfa_flux.h`, `cps_mem.cpp`, `qs.cpp`,
  `cps.h`, `burn.cpp`, `burn.h`, `libretro.cpp`, `hsfa/hsfa_run.c`.
- **Couper / vérifier** : `HSFA_REJEU=0` ; `HSFA_REJEU_LOG=<fichier>` ; `HSFA_REJEU_SEUL=1`. Hyper sans aucun membre :
  identique à l'octet au cœur d'avant. Coût mesuré : 0,16 ms par image sur PC, +14 Mo de mémoire.

## 6. `0002-HSFA-chargement-differe-emplacement-4.patch` — portrait du face-à-face

- **Problème** : dans Upper, 5 images de tuiles de l'écran VS à la place du grand portrait, quand le dialogue d'avant
  le 1ᵉʳ combat se ferme.
- **Solution** : le nouveau fichier de l'emplacement 4 attend qu'aucun objet de cet emplacement ne soit plus affiché
  (10 images au plus), comme la lecture mise en file de la PS2.
- **Alternatives** : retarder l'écriture du pointeur `$C0BC` dans le traducteur, écarté : le jeu lit ce pointeur tout
  de suite (animation de la paire, acteurs de fin). Pistes « défaut de traduction », « ordre des écritures » et
  « double tampon » réfutées ([PORTRAITS](../rapports/PORTRAITS.md) §2.3, §3.2).
- **Fichiers** : `cps_hsfa.cpp` (`HsfaSuivre4`, `HsfaFrameDone`, `HsfaScan`).
- **Couper / vérifier** : `HSFA_LAT4=0` ou `lat4=0` dans la configuration du zip (identique au pixel à l'ancien
  cœur) ; `HSFA_LAT4_MAX`. La taille des états change.

## 7. `0003-HSFA-options-du-coeur.patch` — réglages de l'écran OPTION

- **Problème** : l'écran OPTION de l'Anthology est du C natif, non traduit ; sa recopie des réglages dans la RAM du
  jeu est perdue.
- **Solution** : 24 réglages en DIP B-H, écrits dans les octets du jeu à chaque passage au menu des modes. « Game
  default » n'écrit rien.
- **Alternatives** : (a) écran d'options en 68K dans le programme, 1,5 à 3 jours ; (c) menu de test et EEPROM de
  l'arcade, greffe d'environ 10 Ko, SFA3 seulement, et le jeu ne lit plus l'EEPROM. Écriture aussi à la sélection des
  persos : essayée puis retirée, elle écrasait le chrono infini du TRAINING ([OPTIONS](../rapports/OPTIONS.md) §2,
  §4).
- **Fichiers** : `cps_hsfa.cpp` (`HsfaOptions`), `d_cps2.cpp` (DIP), `cps.h`. La partie lanceur d'essai est le patch 11b.
- **Couper / vérifier** : `HSFA_OPTIONS=0`. Tous DIP par défaut : 60/60 captures d'Hyper identiques
  ([OPTIONS](../rapports/OPTIONS.md) §4).

## 8. `0004-HSFA-stb_vorbis.patch` — décodeur Ogg Vorbis

- **Problème** : le zip d'Hyper fait environ 710 Mo avec les flux ADX.
- **Solution** : stb_vorbis 1.22 (un seul fichier C, domaine public / MIT), API mémoire seulement
  (`STB_VORBIS_NO_STDIO`, `STB_VORBIS_NO_PUSHDATA_API`) ; `-DHSFA_FLUX_VORBIS` dans `Makefile.hsfa`.
- **Alternatives** : libvorbis (0,40 s CPU pour 120 s de musique contre 0,14 s) et Opus (0,92 s), plus lents ; une
  version antérieure à 1.22 de stb_vorbis (corrections de `seek`) ([PLAN-VORBIS](../rapports/PLAN-VORBIS.md) §2.1,
  §6).
- **Fichiers** : `src/dep/libs/stb_vorbis/` (nouveau), `Makefile.hsfa`.
- **Vérifier** : compilation Linux, Android, ROCKNIX, Windows.

## 9. `0005-HSFA-flux-musique-Ogg-Vorbis.patch` — flux Ogg

- **Problème** : lire des flux Ogg sans rien changer au comportement du jeu.
- **Solution** : une entrée de l'AFS peut être un Ogg complet (reconnu à `OggS`). Boucle par `LOOPSTART` /
  `LOOPEND` ; anneau de 2,7 s ; ADX et Ogg cohabitent.
- **Alternatives** : de nouveaux champs d'état avec un numéro de version, prévus par le plan ; remplacés par la
  réutilisation de `pos_abs` et `boucle_ok` : l'état garde sa taille, un état écrit avec un zip ADX se recharge avec un
  zip Ogg ([PLAN-VORBIS](../rapports/PLAN-VORBIS.md), « Écarts avec le plan »).
- **Fichiers** : `hsfa_flux.h`, `cps_hsfa.cpp`.
- **Vérifier** : `tools/flux/tests/lance_tests.sh` (23 contrôles). Un cœur sans ce patch ne lit pas un zip Ogg.

## 10. `0006-HSFA-carte-musique.patch` — partitions ZERO / ZERO 2

- **Problème** : les musiques ZERO et ZERO 2 d'Hyper sont des enregistrements (environ 112 Mo d'ADX) alors que leurs
  pilotes son d'origine sont dans le `X_DATA.BIN` de l'utilisateur.
- **Solution** : « carte musique » : un 2ᵉ Z80 (Zet n° 1) exécute le pilote SFA1 ou SFA2 (photo prise après son
  démarrage, restaurée à chaque morceau), un 3ᵉ QSound lit la ROM déjà chargée pour le rejeu. Aiguillage : carte,
  puis flux, puis Z80 principal.
- **Alternatives** : B, partitions converties en v1.71 pour le Z80 principal (ni numéros, ni entrées, ni bit de
  banque libres) ; C, partager le QSound du rejeu (les deux pilotes écriraient sur les mêmes voies) ; D, rejouer des
  écritures QSound enregistrées (raccord de boucle non garanti), gardée en repli
  ([PLAN-PARTITIONS-HYPER](../rapports/PLAN-PARTITIONS-HYPER.md) §2).
- **Fichiers** : `hsfa_musique.h` (nouveau), `cps_hsfa.cpp`, `hsfa_flux.h`, `qs.cpp`, `cps.h`.
- **Couper / vérifier** : `HSFA_MUSIQUE=0`, ou un zip sans `hsfa_musique.bin`. Le Z80 n° 1 est toujours créé pour
  Hyper, pour que la disposition des états ne dépende pas des données. Banc : `lance_tests_carte.sh`.

## 11. `0007-HSFA-roulette-touche-piece.patch` — roulette sur Select

- **Problème** : la traduction recopie le bit de Start dans l'octet de roulette `$D3` : Start tenu à la validation
  donnait un perso au hasard, ce qui gênait les EX.
- **Solution** : sur la grille des persos seulement, le cœur écrit `$FF84D3` / `$FF88D3` d'après la touche Pièce
  (Select) du joueur, comme Select sur PS2. Start reste au jeu (EX, EX Balrog, S-ISM).
- **Alternatives** : forcer l'octet à 0 (`HSFA_NOROUL`, comme `NOROUL` du banc), gardé pour les essais seulement : la
  roulette disparaîtrait ([ETATS-HYPER](../rapports/ETATS-HYPER.md) §1.1).
- **Fichiers** : `cps_hsfa.cpp` (`HsfaRoulette`, prise d'écriture `$FF8400-$FF8BFF`).
- **Vérifier** : tournée de 151 VERSUS identique avec et sans `HSFA_NOROUL` (§157).

## 11b. `0007b-HSFA-hsfa_run-options-du-coeur-HSFA_VARS.patch` — options du cœur dans le lanceur

- **Problème** : essayer les options du cœur sans RetroArch, y compris un changement en cours de partie.
- **Solution** : `hsfa_run` sert `HSFA_VARS="clé=valeur;…"` aux demandes `GET_VARIABLE` du cœur ; `HSFA_VARS2`
  remplace `HSFA_VARS` à partir de l'image `HSFA_VARS2_IMAGE`, et `GET_VARIABLE_UPDATE` répond vrai une fois.
- **Pourquoi un patch à part** : ce morceau du diff d'origine ([OPTIONS](../rapports/OPTIONS.md) §3.2) manquait au
  patch 7 publié. Il a été extrait du commit `bca36de` de l'arbre de référence. Le patch 12 s'applique avec ou sans.
- **Alternatives** : sans objet.
- **Fichiers** : `hsfa/hsfa_run.c` seulement : le cœur `.so` n'est pas touché.
- **Vérifier** : avec `HSFA_VARS="fbneo-dipswitch-sfa3hsfa-Option__Timer_speed=Infinity"` et `DUMPRAM=1400`, une
  partie de SFA3 arrêtée au menu des modes a `$FF80A3 = 4` (1 sans la variable) ; vérifié le 2026-10-18.

## 12. `0008-HSFA-registres-des-plans-ro9a.patch` — plans de `ro9a`

- **Problème** : dans `ro9a` (Hyper + Arcade d'Upper), le programme écrit les bases `$400/$440/$4A0` des écrans
  d'Upper. Elles tombaient au-delà de la région de 64 Mo ; le masque d'adresse les ramenait sur les tuiles de SFA3.
- **Solution** : écriture de mot traitée en une fois (masque d'octet gardé pour les octets) ; `nCpsGfxScroll` mis à
  jour seulement au changement ; taille de la région déduite de `hsfa_gfx.bin` (80 Mo pour `ro9a`, Upper et Hyper
  inchangés) ; `hsfa_gfx.bin` converti sur place (pas de tampon de 32 à 48 Mo) ; pilote d'essai `sfa3hahsfa` ;
  `HSFA_PLANS_LOG` ; `hsfa_run` `PILOTE=arcade`.
- **Alternatives** : l'invalidation `mark_all_dirty` du fork n'a pas d'équivalent à écrire, FBNeo n'ayant pas de cache
  de tuiles. Remplacer tout de suite le pilote d'Hyper : différé, il suffira de passer la taille dans
  `Sfa3hhsfaRomDesc` ([COEUR-BANQUES](../rapports/COEUR-BANQUES.md) §A.2).
- **Fichiers** : `cps_hsfa.cpp`, `cps_rw.cpp`, `cps.h`, `d_cps2.cpp`, `hsfa/hsfa_run.c`.
- **Vérifier** : `HSFA_PLANS_LOG=<f>` : suite `300` → `400` → `300` aux mêmes images que le banc ; `STATETEST=700`.
  Le pilote `sfa3hahsfa` n'existe dans le `.so` que si les en-têtes ont été régénérés (`REGEN_HEADERS=1`).

## 13. `0009-HSFA-prototype-trous-carte-68K.patch` — trous de la carte en ROM

- **Problème** : la ROM programme est pleine et les blocs externes de `ro9a` sont saturés (marge d'environ 28 Ko).
- **Solution** : les 7 plages libres de la carte 68K (5,08 Mo) servies en ROM depuis le membre facultatif
  `hsfa_trous.bin`, déclaré par `sfa3hahsfa` seul. Coût en cycles nul.
- **Alternatives** : banque de données commutée par un registre `$804210`, chiffrée mais gardée pour plus tard (un
  pointeur n'a de sens que si la bonne page est en place ; utile au-delà d'environ 5 Mo) ; données mortes d'Hyper ;
  `$F20000-$F7FFFF` (`ro9` seulement) ; au-delà de 16 Mo, impossible (bus de 24 bits)
  ([COEUR-BANQUES](../rapports/COEUR-BANQUES.md) §B.2-§B.4).
- **Fichiers** : `cps_hsfa.cpp` (`HsfaTrous`, `HsfaLoadData`, `HsfaInit`), `d_cps2.cpp`.
- **Couper / vérifier** : sans le membre, rien n'est projeté. Le journal du cœur lit le 1ᵉʳ et le dernier mot de
  chaque trou (`HSFA : trou $…`). Limites : pas de code dans les trous ; plus grand trou de 2 Mo ; +5,1 Mo de RAM.

## 14. `0010-HSFA-melange-des-objets-transparence.patch` — mélange des objets

- **Problème** : sur PSP, les effets des persos MAX sont dessinés en **additif saturé** (mode choisi par objet, champ
  `+0xAA` du moteur PSP). La CPS2 n'a aucune transparence : les mêmes effets sortaient opaques, avec un contour sombre.
- **Solution** : des modes de mélange posés par le programme et appliqués par le cœur au dessin des objets.
  - `$804220-$80423F` : un octet par palette OBJ (0 opaque au reset, 1 additif, 2 alpha 50 %, 3 alpha 75 %,
    4 soustractif ; 5 noir à 75 % depuis 0011) ;
  - `$804240-$804241` : octet bas = mode des objets **marqués**, c'est-à-dire dont le mot X de la liste brute a le
    bit 12 (posé par le talon EFFET_W des persos MAX) ; 0 = bit ignoré ;
  - priorité : objet marqué avec `$804240` ≠ 0, puis palette, puis option des ombres (0011), puis opaque ;
  - `HsfaEclater` garde le bit 12 (`x & $F000`) ; `Cps2ObjDraw` passe `nCpsBlend = 0x100 | mode` ; mélange dans
    `cps_mix()` (24/32 bits) et `cps_mix16()` (16 bits, 565 ou 1555) ;
  - états : les registres sont la dernière zone de l'état libretro, lue seulement si elle existe : les anciens états
    se rechargent (registres à 0), et les nouveaux se rechargent dans un ancien cœur.
- **Alternatives** :
  - (v1) registres par palette seuls : la PSP décide par objet, pas par palette ([TRANSPARENCE](../rapports/TRANSPARENCE.md)
    §9) ;
  - (b) bloc de palettes « additives » : 5 palettes non prouvées libres, et des copies de couleurs qui ne suivraient
    pas les flashs et assombrissements de super ; écarté au profit du bit 12, jamais posé par les programmes traduits
    (0 sur 10,99 M d'entrées) ([TRANSPARENCE-PAR-OBJET](../rapports/TRANSPARENCE-PAR-OBJET.md) §2-§3) ;
  - registres sauvés par `SCAN_VAR` (v1) : 32 octets de plus, anciens états illisibles ; remplacé par la zone finale
    facultative (§9.2).
- **Fichiers** : `cps_hsfa.cpp`, `cps.h`, `cps_obj.cpp`, `ctv.cpp`, `ctv_do.h`, `src/burner/libretro/retro_memory.cpp`.
- **Couper / vérifier** : registres jamais écrits = image identique au pixel (`nonreg_coeur` ×3 en 32 et 16 bits, 4:3
  et 16:9). Essais : `HSFA_OBJMIX=oo:m[,…]` (décalage depuis `$804220` ; `21` = objets marqués) impose des valeurs au
  reset, `HSFA_MIX_LOG=<fichier>` journalise les changements. Mode 2 seulement (Upper, Hyper, `ro9a`).

## 15. `0011-HSFA-option-ombres-transparentes-PSP.patch` — ombres transparentes

- **Problème** : la PSP dessine les ombres des persos en noir à 75 % ; les programmes traduits les dessinent opaques
  (tuiles OBJ de la palette `0x14`).
- **Solution** : option du cœur « Transparent shadows (PSP) », bit 7 du DIP A, **activée par défaut**, pour tous les
  pilotes HSFA (modes 1 et 2). Une tuile est une ombre si sa palette OBJ vaut `0x14` **et** son code global est
  `0x0284A`, `0x305DF-0x30613` ou `0x50888-0x5088A` (les mêmes dans les quatre jeux). Nouveau mode 5 : noir à 75 %.
  Les modes posés par le jeu (0010) passent avant l'option.
- **Alternatives** :
  - la palette `0x14` seule : elle sert aussi au décor (poteaux du premier plan), qui doit rester opaque ;
  - ajouter un test d'état (`$FF8000 = 2`, `$FF8004 = 4`) : les ombres des combats de démo resteraient opaques ; non
    recommandé ;
  - le mode 3 (alpha 75 % de la couleur) teinterait l'ombre de la palette `0x14` : d'où le mode 5
    ([TRANSPARENCE-OMBRES-JAUGES](../rapports/TRANSPARENCE-OMBRES-JAUGES.md) §3) ;
  - jauges à 50 % (D5) : abandonnées, la PSP ne teinte pas les jauges, elle remplit les barres d'un dégradé.
- **Fichiers** : `cps_hsfa.cpp`, `cps.h`, `cps_obj.cpp`, `ctv.cpp`, `d_cps2.cpp`.
- **Couper / vérifier** : DIP coupé, ou `HSFA_OMBRES=0` (prioritaire sur le DIP) : image identique au pixel. Contrôle
  automatique sur 7 parties et 980 captures : 0 pixel modifié hors d'une tuile d'ombre ; les codes n'apparaissent
  qu'en combat (démo comprise), jamais dans un menu, un portrait ou une fin ([TRANSPARENCE](../rapports/TRANSPARENCE.md)
  §10). **Toute non-régression contre une référence antérieure se lance avec `HSFA_OMBRES=0`.**

## 16. `0012-HSFA-16-9-format-remplir-la-hauteur.patch` — cœur 16:9, « remplir la hauteur »

- **Problème** : sur un écran moins large que 16:9 (4:3, 3:2, 16:10…), le cœur 16:9 réduisait toute l'image et
  laissait des bandes en haut et en bas.
- **Solution** : option `fbneo-hsfa-format`, « Screen format (fill height) », dans le **cœur 16:9 seulement** et pour
  les pilotes HSFA : Off (défaut, inchangé), 4:3, 3:2, 14:9, 16:10, 5:3, 16:9. L'image remplit la hauteur et les deux
  côtés sont rognés (centré). Largeur montrée = format × 288 (pixels arcade : 384 px ↔ 4:3), paire, plafonnée à 448 :
  4:3 → 384, 3:2 → 432, 14:9 et plus → 448. Le rognage se fait à la sortie vidéo (pointeur décalé) ; la géométrie
  libretro suit l'option (`SET_GEOMETRY`). Ce n'est pas un registre : le jeu n'en sait rien.
- **Alternatives** : le numéro 0012 était prévu pour les jauges (D5), abandonnées. La valeur 14:9 (pleine largeur,
  pixels arcade) a été proposée pour le mode Off, qui reste inchangé par choix
  ([TRANSPARENCE](../rapports/TRANSPARENCE.md) §13). Même principe que les forks « remplir la hauteur » de
  l'utilisateur pour d'autres émulateurs.
- **Fichiers** : `src/burner/libretro/libretro.cpp`, `retro_common.cpp`, `retro_common.h`.
- **Couper / vérifier** : Off = image identique au pixel. Chaque format est exactement la découpe centrée de l'image
  Off ; géométrie annoncée : 4:3 → 384 × 224 à 1,3333, 3:2 → 432 × 224 à 1,5, 14:9 → 448 × 224 à 1,5556.

## Hors chaîne

- **`fbneo-hsfa-decors.patch`** — décors widescreen injectés dans SFA3. Problème : bandes du 16:9 vides ou fausses.
  Solution : le mode « bases de plans » vaut pour tout jeu dont la configuration donne `plans=`, SFA3 compris ;
  `hsfa_gfx.bin` facultatif. Posé sur les patchs 1-2 ; ne s'applique pas après le patch 6 sans adaptation de
  `cps_hsfa.cpp` ([INJECTION-FORK](../rapports/INJECTION-FORK.md) §7).
- **`hsfa_run-sysdir.diff`** — le lanceur passait `getenv("SYSDIR")` au cœur, qui en lit `MAX_PATH` octets : plantage
  quand la chaîne est en fin de pile ([ROCKNIX](../rapports/ROCKNIX.md) §3). Correctif : copie dans un tampon. Il
  s'applique sur la chaîne actuelle par `patch -p1` (décalage de 143 lignes), pas par `git apply`.
