# Documentation

Documentation de travail du projet HSFA, en français. Présentation et état : [README](../README.fr.md).

## Guide — pour s'en servir

| Document | Sujet |
|---|---|
| [guide/demarrage.md](guide/demarrage.md) | de l'ISO au jeu traduit au banc MAME, diagnostic, non-régression |
| [guide/construction-iso.md](guide/construction-iso.md) | construire les trois jeux et les archives du cœur depuis l'ISO (`hsfa_build.py`) |
| [guide/installation-android.md](guide/installation-android.md) | cœur FBNeo HSFA sur RetroArch Android |
| [guide/installation-rocknix.md](guide/installation-rocknix.md) | cœur sur RGB10X / ROCKNIX |

## Architecture — comment c'est fait

| Document | Sujet |
|---|---|
| [architecture/traducteur.md](architecture/traducteur.md) | le traducteur MIPS → 68000 : principe, chaîne, ce que le portage a ajouté |
| [architecture/memoire-cps2.md](architecture/memoire-cps2.md) | la recette mémoire « mode CPS2 » (§29), conversion des adresses, pièges |
| [architecture/banc-mame.md](architecture/banc-mame.md) | banc MAME, scripts Lua, fork `sfa3hx` |
| [architecture/coeur-fbneo.md](architecture/coeur-fbneo.md) | cœur libretro FBNeo « HSFA » : pilotes, archives, son, plates-formes |
| [architecture/ARCHI-Reorganisation-Donnees.md](architecture/ARCHI-Reorganisation-Donnees.md) | réorganisation des données : supprimer les adaptateurs, disposition arcade |
| [architecture/voie-b-greffe.md](architecture/voie-b-greffe.md) | voie B : greffer le mode Arcade d'Upper sur Hyper |
| [architecture/OUTILS.md](architecture/OUTILS.md) | **référence détaillée** : pipeline, fiche de chaque script, banc, formats, recettes, incohérences connues |

## Référence — à consulter

| Document | Sujet |
|---|---|
| [reference/adresses.md](reference/adresses.md) | adresses utiles (RAM de jeu, matériel, image produite) |
| [reference/carte-modules.md](reference/carte-modules.md) | modules de l'Anthology, groupes de `X_DATA.BIN` |
| [reference/formats.md](reference/formats.md) | formats des fichiers produits, des données de l'Anthology, des décors et du son |
| [reference/SYMBOLES.md](reference/SYMBOLES.md) | carte des symboles de SFA3 dans les trois espaces d'adresses |
| [reference/FRAMES-Anthology.md](reference/FRAMES-Anthology.md) | format des frames de sprites |
| [MAX-Etude-Contenu-Persos.md](MAX-Etude-Contenu-Persos.md) | SFA3 MAX (PSP) : contenu des persos, conversion vers la CPS2 (document de la session MAX, laissé à la racine de `docs/`) |

## Méthodes — comment travailler

| Document | Sujet |
|---|---|
| [methodes/oracle-et-non-regression.md](methodes/oracle-et-non-regression.md) | oracle arcade, batterie de non-régression, interrupteurs, pertes silencieuses |
| [methodes/pieges-du-traducteur.md](methodes/pieges-du-traducteur.md) | pièges rencontrés, par famille |

## Journal et rapports

| Document | Sujet |
|---|---|
| [journal/README.md](journal/README.md) | le journal (`HANDOFF.md`, §1-§146), son index, l'état des lieux ; correspondance des anciens chemins |
| [rapports/README.md](rapports/README.md) | rapports d'études détaillés (2026-10-07 au 2026-10-11) |

## Ailleurs dans le dépôt

- [src/hsfa/README.md](../src/hsfa/README.md) : les scripts du traducteur ;
- [scripts/README.md](../scripts/README.md) : construction, validation, qualité ;
- [tools/README.md](../tools/README.md) : outils par thème ;
- [patches/README.md](../patches/README.md) : patchs des forks MAME et FBNeo ;
- [legacy/README.md](../legacy/README.md) : époque PNACH ;
- [max/README.md](../max/README.md) : session SFA3 MAX.

Les chemins absolus sont remplacés par `<workspace>` (espace de travail du développeur) ; voir
[scripts/correspondances.tsv](../scripts/correspondances.tsv).
