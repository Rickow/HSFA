# Outils par thème

Outils d'étude et de production écrits au fil des chantiers. Chaque dossier correspond à un rapport de
[`docs/rapports/`](../docs/rapports/README.md), qui en décrit l'usage et les résultats. Le traducteur lui-même est dans
[`src/hsfa/`](../src/hsfa/README.md) ; les chaînes de construction et de validation dans [`scripts/`](../scripts/README.md).

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
| [`greffe-arcade/`](greffe-arcade/) | voie B : greffe du mode Arcade d'Upper sur Hyper (outils, données, décors) | [GREFFE-PREPARATION](../docs/rapports/GREFFE-PREPARATION.md), [GREFFE-DECORS](../docs/rapports/GREFFE-DECORS.md) |
| [`hyper-etats/`](hyper-etats/) | machine à états d'Hyper, écran de mode, tournée de référence `tournee_hyper.lua` | [ETATS-HYPER](../docs/rapports/ETATS-HYPER.md) |
| [`integration-max/`](integration-max/) | conversion du code et des frames MAX vers l'image d'Upper ; voix MAX | [CONV-MAX](../docs/rapports/CONV-MAX.md), [VOIX-MAX](../docs/rapports/VOIX-MAX.md) |
| [`reorg/`](reorg/) | réorganisation des données, étape A : journal des conversions, oracle RAM, `disposition.lua` | [ETAPE-A](../docs/rapports/ETAPE-A.md) |
| [`rocknix/`](rocknix/) | cœurs pour ROCKNIX (RGB10X) : compilation croisée, système EmulationStation, notice | [ROCKNIX](../docs/rapports/ROCKNIX.md) |
| [`son-hyper/`](son-hyper/) | son d'Hyper : voix SFA1/SFA2 par version, rejeu QSound, redirection | [SON-HYPER-ROM](../docs/rapports/SON-HYPER-ROM.md) |
| [`son-hyper/partitions/`](son-hyper/partitions/README.md) | musique d'Hyper en partitions : pilotes v1.0x, bancs Z80, appariement des variantes | [PARTITIONS-HYPER](../docs/rapports/PARTITIONS-HYPER.md) |
| [`symboles/`](symboles/) | carte des symboles de SFA3 (`symboles_ro3.csv`) et ses outils | [SYMBOLES](../docs/reference/SYMBOLES.md) |
| [`max/`](max/README.md) | outils de la session SFA3 MAX (PSP) — **ne pas déplacer** : la session MAX les importe par ce chemin | [MAX-Etude-Contenu-Persos](../docs/MAX-Etude-Contenu-Persos.md) |
| `untranspile` | **lien** vers `../src/hsfa` (ancien emplacement du traducteur, utilisé par `max/paths.py`) | — |

## Chemins

Ces outils ont été écrits dans l'espace de travail du développeur ; leurs chemins sont publiés sous la forme
`<workspace>/...`. Beaucoup lisent des dossiers de travail (`<workspace>/work/agent_*`, `work/carto_ro9`…) qui ne sont
pas publiés : ce sont des **archives d'étude**, réutilisables en adaptant les chemins. Correspondance des dossiers
publiés : [`scripts/correspondances.tsv`](../scripts/correspondances.tsv) ; copie exécutable :
[`scripts/localiser.py`](../scripts/localiser.py). Les imports de chaque script sont vérifiés par
[`scripts/qualite/verifier_imports.py`](../scripts/qualite/verifier_imports.py) (dépendances non publiées classées
« externes »).
