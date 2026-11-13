# Outils par thème

**English: [README.md](README.md)**

Outils d'étude et de production écrits au fil des chantiers. Chaque dossier correspond à un rapport de
[`docs/rapports/`](../docs/rapports/README.md), qui en décrit l'usage et les résultats. Le traducteur lui-même est dans
[`src/hsfa/`](../src/hsfa/README.md) ; les chaînes de construction et de validation dans [`scripts/`](../scripts/README.fr.md).

| Dossier | Thème | Rapport |
|---|---|---|
| [`carto-modules/`](carto-modules/) | cartographie de tous les modules de l'Anthology (SFA, SFA2 et variantes, Pocket Fighter, menu) | [CARTE-MODULES](../docs/rapports/CARTE-MODULES.md) |
| [`decors/export/`](decors/export/) | export exact des décors en PSD (balayage de caméra, recollage) | [DECORS-WS](../docs/rapports/DECORS-WS.md) |
| [`decors/reimport/`](decors/reimport/) | PSD → tuiles CPS2, palettes, blocs libres | [REIMPORT](../docs/rapports/REIMPORT.md) |
| [`decors/injection/`](decors/injection/) | injection des décors widescreen dans le programme traduit (fork, cœur) | [INJECTION-FORK](../docs/rapports/INJECTION-FORK.md) |
| [`decors/sfa2/`](decors/sfa2/) | import d'un décor de SFA2 dans SFA3 traduit | [DECOR-SFA2](../docs/rapports/DECOR-SFA2.md), [DECOR-SFA2-EXPORT](../docs/rapports/DECOR-SFA2-EXPORT.md) |
| [`diagnostics/`](diagnostics/) | enquêtes ponctuelles : `banque-1a`, `coups` (Sakura / Akuma), `explosion`, `portraits`, `zangief` | [BANQUE-1A](../docs/rapports/BANQUE-1A.md), [COUPS](../docs/rapports/COUPS.md), [EXPLOSION](../docs/rapports/EXPLOSION.md), [PORTRAITS](../docs/rapports/PORTRAITS.md), [ZANGIEF](../docs/rapports/ZANGIEF.md) |
| [`etude-upper-hyper/`](etude-upper-hyper/) | voie A / voie B pour « Upper + modes d'Hyper » | [ETUDE-UPPER-HYPER](../docs/rapports/ETUDE-UPPER-HYPER.md) |
| [`fbneo-hsfa/`](fbneo-hsfa/README.md) | archives du cœur (`paquet_fbneo.py`) et notices d'installation | [FBNEO-HYPER](../docs/rapports/FBNEO-HYPER.md), [REJEU-FBNEO](../docs/rapports/REJEU-FBNEO.md) |
| [`flux/`](flux/) | lecteur de flux musique (ADX et Ogg Vorbis) : table des flux, lanceurs d'essai, encodeur Vorbis `flux_ogg.py` / `fluxtool.cpp`, banc `tests/lance_tests.sh` | [FLUX](../docs/rapports/FLUX.md), [PLAN-VORBIS](../docs/rapports/PLAN-VORBIS.md) |
| [`greffe-arcade/`](greffe-arcade/) | voie B : greffe du mode Arcade d'Upper sur Hyper (outils, données, décors) ; `construction/` ([LISEZMOI](greffe-arcade/construction/LISEZMOI.md)) : copie figée ro9a41 qui sert à `hsfa_build.py --jeux hyperarcade` (§212, §217, §221, §223, §224, §228) | [GREFFE-PREPARATION](../docs/rapports/GREFFE-PREPARATION.md), [GREFFE-DECORS](../docs/rapports/GREFFE-DECORS.md), [BUILD §11](../docs/rapports/BUILD.md) |
| [`hyper-etats/`](hyper-etats/) | machine à états d'Hyper, écran de mode, tournée de référence `tournee_hyper.lua` | [ETATS-HYPER](../docs/rapports/ETATS-HYPER.md) |
| [`integration-max/`](integration-max/README.md) | conversion du code et des frames MAX vers l'image d'Upper ; voix MAX ; `upper_max/` : étapes d'Upper MAX dans `hsfa_build.py --jeux uppermax` (`regen_max.py`, copie figée `integration_2b31`, §202) | [CONV-MAX](../docs/rapports/CONV-MAX.md), [VOIX-MAX](../docs/rapports/VOIX-MAX.md) |
| [`reorg/`](reorg/) | réorganisation des données, étape A : journal des conversions, oracle RAM, `disposition.lua` | [ETAPE-A](../docs/rapports/ETAPE-A.md) |
| [`rocknix/`](rocknix/) | cœurs pour ROCKNIX (RGB10X) : compilation croisée, système EmulationStation, notice | [ROCKNIX](../docs/rapports/ROCKNIX.md) |
| [`son-hyper/`](son-hyper/) | son d'Hyper : voix SFA1/SFA2 par version, rejeu QSound, redirection | [SON-HYPER-ROM](../docs/rapports/SON-HYPER-ROM.md) |
| [`son-hyper/partitions/`](son-hyper/partitions/README.md) | musique d'Hyper en partitions : pilotes v1.0x, bancs Z80, appariement des variantes | [PARTITIONS-HYPER](../docs/rapports/PARTITIONS-HYPER.md) |
| [`symboles/`](symboles/) | carte des symboles de SFA3 (`symboles_ro3.csv`) et ses outils | [SYMBOLES](../docs/reference/SYMBOLES.md) |
| [`max/`](max/README.md) | outils de la session SFA3 MAX (PSP) — **ne pas déplacer** : la session MAX les importe par ce chemin | [MAX-Etude-Contenu-Persos](../docs/MAX-Etude-Contenu-Persos.md) |
| [`android/`](android/README.md) | construction des deux cœurs Android (arm64-v8a, NDK r28c) | [installation-android](../docs/guide/installation-android.fr.md) |
| [`windows/`](windows/LISEZMOI-windows.md) | cœurs Windows x64 (MinGW-w64 depuis Linux) et notice | [LISEZMOI-windows](windows/LISEZMOI-windows.md) |
| [`recalbox/`](recalbox/LISEZMOI-recalbox.md) | cœurs Recalbox 10 (armhf / aarch64), installation | [installation-recalbox](../docs/guide/installation-recalbox.md) |
| [`batocera/`](batocera/INSTALL-batocera-EN.md) | Batocera 43 : installeur `installer-hsfa-batocera.sh` (service `hsfa` qui repose les cœurs à chaque démarrage ; `retirer` pour désinstaller), système `es_systems_hsfa.cfg`, `gamelist.xml`, notice anglaise | [installation-batocera](../docs/guide/installation-batocera.fr.md) |
| [`linux/`](linux/README.md) | cœur Linux x86_64 compatible glibc 2.27 (celui des v0.1.7 / v0.1.8 demande la 2.43) : recette `build_x86_glibc_ancienne.sh`, cales `hsfa_x86_compat.{c,h}` | [README](linux/README.md) |
| [`retrobat/`](retrobat/NOTE-RETROBAT.md) | RetroBat (Windows) : note d'installation et système `es_systems_hsfa.cfg`, **non essayés** | [NOTE-RETROBAT](retrobat/NOTE-RETROBAT.md) |
| [`ps2-patchs/`](ps2-patchs/README.md) | patcheurs de l'ISO PS2 : tout débloqué, 16:9 natif | [README](ps2-patchs/README.md) |
| [`options/`](options/) | écran OPTION et retour au menu (diffs du traducteur et du cœur), BGM d'Hyper dans Upper | [OPTIONS](../docs/rapports/OPTIONS.md), [OPTIONS-HYPER-UPPER](../docs/rapports/OPTIONS-HYPER-UPPER.md) |
| [`reviews/`](reviews/README.md) | outils des revues critiques des 11-12/11 : garde-fous et audits du traducteur, relogement / tables / registres de la greffe, tables par id de perso, contrôles de l'intégration d'Upper MAX | [reviews](../docs/rapports/reviews/README.md) |
| [`sondes-recherche/`](sondes-recherche/README.md) | sonde de PC du cœur, déchiffreur CPS2, désassembleur, banc des coups FBNeo ; ajoutés le 11/11 : `croise_cps2recomp.py` (index contre les notes de cps2recomp), `tuiles_cps2*.py` (réutilisation des tuiles d'une ROM CPS-2), `ocr_gamemachine.sh` (OCR de revues scannées, recherche du livre) | [D-SONDES](../docs/rapports/recherche/D-SONDES.md), [J](../docs/rapports/recherche/J-CROISEMENT-CPS2RECOMP-SFA3.md), [M](../docs/rapports/recherche/M-REUTILISATION-TUILES.md), [Q](../docs/rapports/recherche/Q-OPTIMISATION-IMAGES.md) |
| [`guide-coups/`](guide-coups/README.md) | relevé des commandes du guide officiel (sans son texte) et vérification SuperCombo | [BANC-COUPS](../docs/rapports/BANC-COUPS.md) |
| [`ppsspp-banc/`](ppsspp-banc/PPSSPP-BANC.md), [`banc-max-psp/`](banc-max-psp/BANC-PSP.md) | PPSSPP comme oracle des persos MAX ; mode B du banc des coups (PSP contre Upper MAX) | [PPSSPP-BANC](ppsspp-banc/PPSSPP-BANC.md), [BANC-PSP](banc-max-psp/BANC-PSP.md) |
| [`bancs/`](bancs/README.md) | **outils communs des mesures** : lanceur `lance_emu` (places, registre, arrêts par PID), empreinte de ce que l'émulateur charge, banc de jour (non-régression des 4 jeux sur versions figées), `compare_zips.py` | [README](bancs/README.md) |
| [`banc-coups/`](banc-coups/README.md) | banc des coups sous MAME (oracle arcade), **banc de non-régression MAX** `banc_max.sh` (condition de livraison d'un lot MAX), frame data contre SuperCombo | [BANC-COUPS](../docs/rapports/BANC-COUPS.md) |
| [`frame-data-max/`](frame-data-max/README.md) | données d'images des persos MAX en tours de jeu : PSP (oracle) contre Upper MAX, passé à chaque lot MAX | [README](frame-data-max/README.md) |
| [`decors/sfa1-iso/`](decors/sfa1-iso/README.md), [`decors/sfa2-iso/`](decors/sfa2-iso/README.md) | décors de SFA1 (13) et SFA2 (18) extraits de l'ISO seule (plans, animations), contrôles contre l'arcade sous MAME | [README SFA1](decors/sfa1-iso/README.md), [README SFA2](decors/sfa2-iso/README.md) |
| [`decors/integration/`](decors/integration/README.md) | convertisseur commun SFA1 / SFA2 → lots « HSFADC01 » de la zone des décors de la greffe, aller-retour prouvé | [README](decors/integration/README.md) |
| [`coeurs/`](coeurs/README.md) | construction et contrôles statiques du lot des 12 cœurs (Linux, Windows, Android, ROCKNIX, Recalbox) | [LIVRAISONS](../docs/guide/LIVRAISONS.fr.md) |
| [`ps2-oracle/`](ps2-oracle/README.md) | PCSX2 comme oracle : Xvfb dédié, xdotool sur le PID lancé, PINE (lecture ; écritures limitées) | [README](ps2-oracle/README.md) |
| [`asm68k/`](asm68k/README.md) | assembleur 68000 maison `hsfa_asm68k` (remplace vasm dans la construction) | [README](asm68k/README.md) |
| [`constructeur/`](constructeur/README.md) | constructeur tout-en-un (un exécutable par système, CI) | [README](constructeur/README.md) |

## Chemins

Ces outils ont été écrits dans l'espace de travail du développeur ; leurs chemins sont publiés sous la forme
`<workspace>/...`. Beaucoup lisent des dossiers de travail (`<workspace>/work/agent_*`, `work/carto_ro9`…) qui ne sont
pas publiés : ce sont des **archives d'étude**, réutilisables en adaptant les chemins. Correspondance des dossiers
publiés : [`scripts/correspondances.tsv`](../scripts/correspondances.tsv) ; copie exécutable :
[`scripts/localiser.py`](../scripts/localiser.py). Les imports de chaque script sont vérifiés par
[`scripts/qualite/verifier_imports.py`](../scripts/qualite/verifier_imports.py) (dépendances non publiées classées
« externes »).

Les outils communs (`bancs/`, `banc-coups/`, `coeurs/`, `ps2-oracle/`) se règlent par variables d'environnement
(`HSFA_WORKSPACE`, `HSFA_BANC_LUA`, `LOT`, `PS2_*` : voir leur README) et se lancent depuis le dépôt. Dans l'espace de
travail, `lance_emu`, `empreinte.*` et `banc_jour.*` vivent dans `<workspace>/work/outils/` : les autres bancs les y
appellent.
