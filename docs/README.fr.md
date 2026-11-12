# Documentation

**English: [README.md](README.md)**

Documentation de travail du projet HSFA, en français. Présentation et état : [README](../README.fr.md).

## Guide — pour s'en servir

| Document | Sujet |
|---|---|
| [guide/demarrage.fr.md](guide/demarrage.fr.md) | de l'ISO au jeu traduit au banc MAME, diagnostic, non-régression |
| [guide/construction-iso.fr.md](guide/construction-iso.fr.md) | construire les trois jeux et les archives du cœur depuis l'ISO (`hsfa_build.py`) |
| [guide/installation-android.fr.md](guide/installation-android.fr.md) | cœur FBNeo HSFA sur RetroArch Android |
| [guide/installation-rocknix.fr.md](guide/installation-rocknix.fr.md) | cœur sur RGB10X / ROCKNIX |
| [guide/installation-recalbox.md](guide/installation-recalbox.md) | cœur sur Recalbox 10 (Raspberry Pi) |
| [guide/installation-fbneo-autonome-windows.fr.md](guide/installation-fbneo-autonome-windows.fr.md) | FinalBurn Neo HSFA autonome pour Windows, sans RetroArch (version d'essai, prévue avec la prochaine version) |
| [guide/installation-batocera.fr.md](guide/installation-batocera.fr.md) | cœurs et cinq jeux sous Batocera 43 (installeur et service ; essayé sur PC) ; RetroBat : [note non essayée](../tools/retrobat/NOTE-RETROBAT.md) |
| [guide/LIVRAISONS.fr.md](guide/LIVRAISONS.fr.md) | registre des cœurs et archives remis (noms, md5) jusqu'au 2026-10-24 ; ensuite, cœurs de chaque release et lots non publiés (§4) |

## Architecture — comment c'est fait

| Document | Sujet |
|---|---|
| [architecture/traducteur.fr.md](architecture/traducteur.fr.md) | le traducteur MIPS → 68000 : principe, chaîne, ce que le portage a ajouté |
| [architecture/memoire-cps2.fr.md](architecture/memoire-cps2.fr.md) | la recette mémoire « mode CPS2 » (§29), conversion des adresses, pièges |
| [architecture/banc-mame.fr.md](architecture/banc-mame.fr.md) | banc MAME, scripts Lua, fork `sfa3hx` |
| [architecture/coeur-fbneo.fr.md](architecture/coeur-fbneo.fr.md) | cœur libretro FBNeo « HSFA » : pilotes, archives, son, plates-formes |
| [architecture/coeur-fbneo-patchs.fr.md](architecture/coeur-fbneo-patchs.fr.md) | une fiche par patch du cœur (lignes 1 à 16 du tableau de `patches/fbneo/README.md`) |
| [architecture/ARCHI-Reorganisation-Donnees.fr.md](architecture/ARCHI-Reorganisation-Donnees.fr.md) | réorganisation des données : supprimer les adaptateurs, disposition arcade |
| [architecture/voie-b-greffe.fr.md](architecture/voie-b-greffe.fr.md) | voie B : greffer le mode Arcade d'Upper sur Hyper |
| [architecture/OUTILS.fr.md](architecture/OUTILS.fr.md) | **référence détaillée** : pipeline, fiche de chaque script, banc, formats, recettes, incohérences connues |

## Référence — à consulter

| Document | Sujet |
|---|---|
| [reference/adresses.md](reference/adresses.md) | adresses utiles (RAM de jeu, matériel, image produite) |
| [reference/carte-modules.md](reference/carte-modules.md) | modules de l'Anthology, groupes de `X_DATA.BIN` |
| [reference/formats.md](reference/formats.md) | formats des fichiers produits, des données de l'Anthology, des décors et du son |
| [reference/SYMBOLES.md](reference/SYMBOLES.md) | carte des symboles de SFA3 dans les trois espaces d'adresses |
| [reference/FRAMES-Anthology.md](reference/FRAMES-Anthology.md) | format des frames de sprites |
| [reference/sfz2a-dash-cps2.md](reference/sfz2a-dash-cps2.md) | projet tiers SFZ2A-DASH-CPS2 (Cammy de Gold sur l'arcade Zero 2 Alpha) |
| [MAX-Etude-Contenu-Persos.md](MAX-Etude-Contenu-Persos.md) | SFA3 MAX (PSP) : contenu des persos, conversion vers la CPS2 (document de la session MAX, laissé à la racine de `docs/`) |

## Méthodes — comment travailler

| Document | Sujet |
|---|---|
| [methodes/oracle-et-non-regression.fr.md](methodes/oracle-et-non-regression.fr.md) | oracle arcade, batterie de non-régression, interrupteurs, pertes silencieuses |
| [methodes/pieges-du-traducteur.fr.md](methodes/pieges-du-traducteur.fr.md) | pièges rencontrés, par famille |

## Journal et rapports

| Document | Sujet |
|---|---|
| [journal/README.md](journal/README.md) | le journal (`HANDOFF.md`, §1-§221), son index, l'état des lieux ; correspondance des anciens chemins |
| [rapports/README.md](rapports/README.md) | rapports d'études détaillés (depuis le 2026-10-07) |
| [rapports/recherche/README.md](rapports/recherche/README.md) | recherche : fiches A à R (versions et bogues de l'arcade, sondes, coups MAX, projets voisins, croisement avec cps2recomp, place sur une vraie CPS-2) ; fiches J à R (2026-11-10, reprises le 11/11) : [J](rapports/recherche/J-CROISEMENT-CPS2RECOMP-SFA3.md), [K](rapports/recherche/K-CPS2RECOMP-PISTES.md), [L](rapports/recherche/L-PROJETS-OUVERTS-2026-11.md), [M](rapports/recherche/M-REUTILISATION-TUILES.md), [N](rapports/recherche/N-PARADIGMES-LIMITES-ROM.md), [O](rapports/recherche/O-CPS2-POSSIBILITES.md), [P](rapports/recherche/P-SYNTHESE-PLACE-CPS2.md) (synthèse), [Q](rapports/recherche/Q-OPTIMISATION-IMAGES.md), [R](rapports/recherche/R-SOLUTIONS-PAR-JEU.md) |

## Ailleurs dans le dépôt

- [src/hsfa/README.md](../src/hsfa/README.md) : les scripts du traducteur ;
- [scripts/README.fr.md](../scripts/README.fr.md) : construction, validation, qualité ;
- [tools/README.fr.md](../tools/README.fr.md) : outils par thème ;
- [patches/README.md](../patches/README.md) : patchs des forks MAME et FBNeo ;
- [legacy/README.md](../legacy/README.md) : époque PNACH ;
- [max/README.md](../max/README.md) : session SFA3 MAX.

Décisions et attentes du porteur : `ATTENTES-ET-DECISIONS.md`, dans le dépôt privé seulement (non exporté).

Les chemins absolus sont remplacés par `<workspace>` (espace de travail du développeur) ; voir
[scripts/correspondances.tsv](../scripts/correspondances.tsv).
