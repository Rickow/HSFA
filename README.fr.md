# HSFA — Street Fighter Alpha Anthology (PS2) retraduit en 68000 CPS2

**English: [README.md](README.md)** (page principale : l'anglais est la langue par défaut du dépôt ; traductions françaises des documents clés en `<nom>.fr.md`)

## Jouer en 3 étapes

> **Aucune donnée de jeu n'est fournie.** Il faut votre propre copie de *Street Fighter Alpha Anthology* (PS2, USA,
> `SLUS-21317`). **Upper MAX** (les quatre persos de SFA3 MAX) et **Hyper + Arcade** (mode Arcade d'Upper greffé sur
> Hyper) sont expérimentaux : voir plus bas.

1. **Télécharger les cœurs** depuis la page des [releases](../../releases) : `hsfa-<version>-cores-<plateforme>.zip`
   pour Android (arm64), ROCKNIX (aarch64 : RGB10X, R36S…), Windows (x64), Linux (x86_64) ou Recalbox 10 (Raspberry
   Pi ; essayé sur un Pi 3B) ; Batocera 43 : voir son guide (ses cœurs arrivent avec la prochaine version, voir le
   [CHANGELOG](CHANGELOG.md), « En cours »). Chaque archive contient le cœur 4:3 (`fbneo_hsfa`) et le cœur 16:9
   (`fbneo_hsfaws`), avec leur licence. Les pré-versions (v0.1.8 : Hyper + Arcade) sont sur la même page.
2. **Construire les jeux depuis votre ISO** (Python 3.8+, environ 6 minutes). Sans rien installer : le constructeur
   tout-en-un `hsfa-constructeur-<système>.zip` de la release (Windows, Linux, macOS). Sinon : télécharger
   `hsfa-<version>-construction.zip` dans la release (ou ce dépôt), puis lancer **`construire.sh`** (Linux, macOS, WSL) ou
   double-cliquer sur **`construire.bat`** (Windows, expérimental : pas encore testé) et lui donner votre ISO. Il prépare
   Python, compile l'encodeur Ogg si `gcc` est là et construit les trois jeux dans `sortie/archives/`. À la main :
   ```bash
   pip install -r requirements.txt
   python3 scripts/construction/hsfa_build.py --anthology "Street Fighter Alpha Anthology (USA).iso" --sortie hsfa_sortie
   ```
   On obtient `hsfa_sortie/archives/sfa3hsfa.zip` (SFA3), `sfa3uhsfa.zip` (Upper) et `sfa3hhsfa.zip` (Hyper).
   - L'ISO doit être l'USA (`SLUS-21317`), en image `.iso` (2 048 octets par secteur) ; la variante « All Unlocked »
     convient aussi. Un `.chd` se convertit d'abord (`chdman extractdvd`).
   - La musique est rangée en Ogg Vorbis : il faut `gcc` et `g++`. L'encodeur (`tools/flux/oggenc`) se compile une
     fois depuis les sources officielles de libvorbis : `python3 tools/flux/oggenc/construit_oggenc.py --sources DIR
     --telecharge`, puis `HSFA_OGGENC_SOURCES=DIR`. Il donne les mêmes octets sur tous les systèmes. Sans `gcc` /
     `g++`, ajouter `--flux-format adx` (zip d'Hyper plus gros).
   - `--arcade sfa3.zip` (facultatif) prend la ROM graphique de SFA3 dans votre jeu d'arcade au lieu de la
     reconstruire depuis l'ISO ; les zips sont alors identiques à ceux de la construction de référence du projet. Détails :
     [docs/guide/construction-iso.fr.md](docs/guide/construction-iso.fr.md).
3. **Installer et jouer** : copier le cœur dans le dossier `cores` de RetroArch et les trois zips dans le dossier des
   ROM (sans les renommer), puis charger un zip avec « FinalBurn Neo HSFA » (4:3) ou « FinalBurn Neo HSFA
   Widescreen » (16:9). Guides : [Android](docs/guide/installation-android.fr.md),
   [ROCKNIX / RGB10X](docs/guide/installation-rocknix.fr.md), [Recalbox](docs/guide/installation-recalbox.md), [Batocera](docs/guide/installation-batocera.fr.md),
   [Windows](tools/windows/LISEZMOI-windows.md) ; sous
   Linux, copier les `.so` dans `~/.config/retroarch/cores/`.

**Retours** : bugs et questions dans les [Issues](../../issues) (français ou anglais), Recalbox compris (essayé sur un
Raspberry Pi 3B ; le lancement depuis la liste de jeux de Recalbox ne marche pas encore : charger le cœur depuis le menu de RetroArch).

Vous préférez le jeu PS2 lui-même ? Deux patcheurs d'ISO (tout débloqué, 16:9 natif) sont décrits
[plus bas](#jouer-lanthology-sur-ps2--pcsx2).

**Remerciements** : tous ceux sur le travail desquels HSFA s'appuie, dans [CREDITS.md](CREDITS.md).

## Ce qu'est HSFA

*Street Fighter Alpha Anthology* (PS2, `SLUS-21317`, CRC `72CE7A78`) n'émule pas les cartes arcade. Ses jeux sont une
**recompilation statique du 68000 d'origine en MIPS R5900** : les registres 68K vivent dans le scratchpad de la PS2.
HSFA fait le chemin inverse. Il **reconnaît les idiomes du recompilateur et réémet le 68000 d'origine**, assemble une
ROM programme CPS2 et la fait tourner sur une CPS2 émulée. Trois jeux sont traités :

| Module PS2 | Jeu | Pilote |
|---|---|---|
| `ro3` | Street Fighter Alpha 3 | `sfa3hsfa` |
| `ro5` | SFA3 **Upper** (roster élargi de la version console) | `sfa3uhsfa` |
| `ro9` | **Hyper** Street Fighter Alpha (versions ZERO / ZERO 2 / ALPHA / ZERO 3 de chaque perso) | `sfa3hhsfa` |

Ils tournent dans deux environnements :
- un **fork de MAME** : banc de développement, jeu `sfa3hx` ;
- un **cœur libretro FBNeo « HSFA »** pour RetroArch : Android (arm64), Linux (x86_64), Windows (x64), ROCKNIX (RGB10X,
  aarch64) et Recalbox 10 (Raspberry Pi : armhf et aarch64), en 4:3 et en 16:9 (12 cœurs par release) ; Batocera 43
  par un installeur ([guide](docs/guide/installation-batocera.fr.md)). Les cœurs contiennent aussi deux pilotes
  expérimentaux : `sfa3umhsfa` (Upper MAX, constructible depuis vos deux disques depuis la v0.1.7) et `sfa3hahsfa`
  (Hyper + Arcade, constructible depuis votre ISO depuis la pré-version v0.1.8).

> **Aucune donnée de jeu ici.** Le dépôt ne contient que des outils, des patchs et de la documentation. Tout ce qui
> vient du jeu (programmes, graphismes, sons) est reconstruit **depuis votre propre ISO** de l'Anthology.


> **Reprendre le projet** (personne ou agent) : lire [AGENTS.md](AGENTS.md), qui condense règles, méthode, acquis et chantiers, tenu à jour à chaque découverte.

## État (2026-11-11 ; release stable v0.1.7, pré-version v0.1.8)

« Prochaine version » ci-dessous = ce qui est dans ce dépôt mais pas encore dans une release (section « En cours » du
[CHANGELOG](CHANGELOG.md)).

**Ce qui marche**

| | État | Détails |
|---|---|---|
| SFA3 (`ro3`) | complet : attraction ; mode Arcade jusqu'au générique, **32/32 fins** conformes à l'arcade (v0.1.6 : les poupées de Shadaloo redessinées par le portage PS2 dans quatre fins sont revenues, avec les cœurs v0.1.6) ; VERSUS, SURVIVAL, DRAMATIC, TRAINING ; commandes **42/42** identiques à l'arcade ; cadence turbo de l'arcade (133,3 %) ; son validé | [journal §110-§113](docs/journal/HANDOFF.md), [non-régression](docs/methodes/oracle-et-non-regression.fr.md) |
| Upper (`ro5`) | jouable de bout en bout, **40/40 fins** ; ROM son hybride (musiques de SFA3 + voix d'Upper) ; les musiques qui n'existent qu'en flux sur le disque sont rangées dans le zip en Ogg Vorbis | [§122-§128](docs/journal/HANDOFF.md), [FLUX](docs/rapports/FLUX.md) |
| Hyper (`ro9`) | VERSUS sans exception (tournée de 151 combats) ; les supers des versions ZERO / ZERO 2 / ALPHA ne plantent plus ; jauge de super et TRAINING corrigés ; musiques ZERO / ZERO 2 / ALPHA dans le zip (Ogg Vorbis) ; voix SFA1 / SFA2 par version, rejouées sur un 2ᵉ QSound, quand la table du rejeu est là (voir plus bas). Prochaine version : 21 sons propres au portage PS2, muets jusque-là (parade en Mazi S-ISM, ticket #1 ; custom combo de ZERO 2 / ALPHA, Birdie, Sagat en Saikyo S-ISM, Cammy ALPHA, provocation de Dee Jay…), ajoutés à la ROM son depuis votre ISO (aussi dans Hyper + Arcade) ; ombre au sol des persos ZERO / ZERO 2 transparente aussi avec l'ISO seule | [§145-§173](docs/journal/HANDOFF.md), [§216, §218](docs/journal/HANDOFF.md), [FBNEO-HYPER](docs/rapports/FBNEO-HYPER.md), [REJEU-FBNEO](docs/rapports/REJEU-FBNEO.md), [SONS-PS2-HYPER](docs/rapports/SONS-PS2-HYPER.md) |
| Menus | OPTION et EXIT ramènent au menu des modes ; les réglages de l'écran d'options PS2 (difficulté, dégâts, chrono, vitesse, manches) sont des options du cœur | [§147-§148](docs/journal/HANDOFF.md), [OPTIONS](docs/rapports/OPTIONS.md) |
| Traducteur | **v161** pour SFA3, Upper, Hyper, Hyper + Arcade et Upper MAX (prochaine version ; releases : v160) : pertes silencieuses trouvées par la revue critique du traducteur, corrigées et prouvées contre l'arcade : bonus de dégâts ×1,5 du mode Mazi jamais appliqué, bonus de score des enchaînements jamais ajouté, tremblement du perso touché absent (SFA3), 2ᵉ lettre des initiales écrite sur la 4ᵉ (SFA3, Upper), et neuf autres comparaisons ou accès d'octet (gel du custom combo, texte défilant, couleur du 2ᵉ joueur en match miroir d'Upper et d'Hyper…) ; la construction compte ces pertes et s'arrête sur une comparaison ou une aide du recompilateur non traduite. **Hyper + Arcade** garde sa copie figée du traducteur v160 (état ro9a36) tant que l'état ro9a37 (v161) n'est pas versé | [journal §219-§220](docs/journal/HANDOFF.md), [pièges](docs/methodes/pieges-du-traducteur.fr.md) |
| Cœur FBNeo HSFA | patchs 0001-0026 (v0.1.7), 0001-0027 (v0.1.8) ; prochaine version : 0029, 0030 et 0031 en plus (sauvegardes d'état complètes et déterministes : run-ahead, rembobinage, jeu en ligne ; dossier système de l'autonome sous Windows ; 16:9 : « Widescreen edges » = Raw par défaut) et cœur Linux x86_64 qui ne demande que glibc 2.27 ; Android, Linux, ROCKNIX, Windows, Recalbox 10 (Raspberry Pi, essayé sur un Pi 3B), Batocera 43 (essayé sur PC) ; option « Blood » (sang rouge, non censuré, par défaut) ; option « Skip idle loops » (activée par défaut : 33 à 41 % de calcul en moins par image, même résultat) ; vrai 16:9 (v0.1.5 : 512 × 224, rapport exact ; vue calée sur le décor aux bouts de l'arène avec HUD centré, par défaut jusqu'à la v0.1.8, en option depuis 0031) ; 4:3 et 16:9 (avec « Screen format (fill height) » pour les écrans de 4:3 à 16:10) ; ombres transparentes comme sur PSP ; provocation sur Select en combat ; persos cachés d'Upper (v0.1.2 : Start tenu + un bouton sur Akuma / Balrog pour Shin Akuma / EX Balrog, Pièce pour la roulette) ; essayé par l'utilisateur sur RG477M et RGB10X | [patchs](patches/fbneo/README.fr.md), [Android](docs/guide/installation-android.fr.md), [ROCKNIX](docs/guide/installation-rocknix.fr.md) |
| Construction depuis l'ISO | `hsfa_build.py` (ou le constructeur tout-en-un) construit les trois jeux depuis votre ISO seule ; programmes du traducteur v161 (prochaine version) : SFA3 `a569c361`, Upper `ac053140`, Hyper `dbfd237d` avec la table du rejeu (`ffc5eac1` sans) ; v160 (v0.1.7, v0.1.8) : SFA3 `9b06c7cf`, Upper `3a9b7fd9`, Hyper `0baed6af` (`e3806660`) ; zips identiques d'une construction et d'un système à l'autre ; prochaine version : Upper MAX se construit sous Windows sans droit de lien symbolique (ticket #2) | [guide](docs/guide/construction-iso.fr.md), [BUILD](docs/rapports/BUILD.md) |
| Formats de sortie | prochaine version : `--cible` (constructeur : menu *Format de sortie*) : `fbneo-hsfa` (défaut, zips inchangés) ; `fbneo-autonome` (FinalBurn Neo HSFA autonome pour Windows, version d'essai : mêmes zips, annonce des concessions puis confirmation) ; `mister` et `cps2-banques` : bilan seulement (concessions et budgets mesurés, rien n'est construit) | [`cibles.py`](scripts/construction/cibles.py), [étude](docs/rapports/recherche/P-SYNTHESE-PLACE-CPS2.md) |
| FinalBurn Neo HSFA autonome (Windows x64) | **version d'essai** (prochaine version), sans RetroArch : FBNeo officiel `84faab7` + chaîne de patchs du dépôt + 5 patchs de l'interface Windows (W01-W05) ; deux programmes (4:3, 16:9) ; options HSFA dans les DIP, 16:9 dans le menu Vidéo ; essayé sous Wine : images, états du jeu et son identiques au cœur RetroArch (±1 sur quelques échantillons des flux Ogg) ; pas encore essayé sur un vrai Windows | [guide](docs/guide/installation-fbneo-autonome-windows.fr.md), [patchs](patches/fbneo-autonome/README.md) |
| Batocera 43 | prochaine version : installeur `tools/batocera/installer-hsfa-batocera.sh` (service `hsfa` qui remet les cœurs en place à chaque démarrage : survit aux redémarrages et aux mises à jour ; désinstallation `retirer`) et système `hsfa` ; essayé sur l'image officielle 43.1 PC en machine virtuelle : les cinq jeux depuis la liste de jeux jusqu'au combat, en 4:3 et 16:9, avec le son | [guide](docs/guide/installation-batocera.fr.md) |
| Upper MAX (`sfa3umhsfa`) | **expérimental** : Eagle, Maki, Yun et Ingrid (SFA3 MAX, PSP) dans Upper, construit depuis vos deux disques (Anthology PS2 + ISO PSP européenne de *SFA3 MAX*, ULES-00235) : `hsfa_build.py --jeux uppermax --psp-iso <ISO PSP>` ; sans l'ISO PSP, Upper normal. Prochaine version : traducteur v161 (plus aucune adresse d'image écrite en dur dans l'intégration ; l'appel `$1B6B6` des acteurs de fin, fins de Maki et de Yun, vise la bonne routine) ; comportement de manche des MAX aligné sur la PSP | [guide §5](docs/guide/construction-iso.fr.md), [CONV-MAX](docs/rapports/CONV-MAX.md), [INTEGRATION-MAX-UPPER](docs/rapports/INTEGRATION-MAX-UPPER.md) |
| Hyper + Arcade (`sfa3hahsfa`) | **expérimental** (pré-version v0.1.8) : mode Arcade d'Upper greffé sur Hyper (« voie B ») ; prochaine version : état ro9a37 (CONTINUE, décors de Ryu, Sodom et Cammy, fin de Ken ; traducteur v161 : bonus ×1,5 du mode Mazi, bonus de score des enchaînements, couleur du 2ᵉ joueur en match miroir), `hsfa_build.py --jeux hyperarcade` ; avec la ROM d'arcade et la table du rejeu, zip de ro9a37 à l'octet hors `hsfa_info.txt` et les sons propres au portage PS2 (`HSFA_SONS_PS2=0` : à l'octet) | [guide §6](docs/guide/construction-iso.fr.md), [architecture](docs/architecture/voie-b-greffe.fr.md) |

**Limites connues de la v0.1.x**

- **Voix d'Hyper par version** : il faut la table du rejeu QSound de SFA1 / SFA2 (`--rejeu-table`, voir le
  [guide de construction](docs/guide/construction-iso.fr.md)). Sans elle, `hsfa_build.py` garde les voix de SFA3 pour toutes les versions d'Hyper (traducteur v161 : programme
  `ffc5eac1` au lieu de `dbfd237d`) et le zip n'a pas de rejeu. Prévu en v0.2 : la construction recréera la table depuis votre ISO.
- Sauvegardes d'état : avec les cœurs des v0.1.7 / v0.1.8, charger un état (et le run-ahead / rembobinage de
  RetroArch) ne reprend pas exactement le même son ni la même première image, déjà vrai du QSound de FBNeo d'origine ;
  corrigé par le patch `0029` (cœurs de la prochaine version).
- Le cœur Linux x86_64 des v0.1.7 / v0.1.8 exige glibc 2.43 (refusé par Batocera 43 et la plupart des distributions
  actuelles) ; la recette d'un cœur compatible glibc 2.27, identique en sortie, est dans
  [`tools/linux/`](tools/linux/README.md) (cœurs de la prochaine version).
- Construction sous Windows : Upper MAX demandait le droit de créer des liens symboliques (ticket #2) ; corrigé dans le
  dépôt (prochaine version).
- 16:9 en *Raw* (défaut depuis le patch `0031`) : l'image telle que le jeu la dessine, donc, aux bouts de l'arène, les
  bandes des côtés peuvent montrer des colonnes noires ou périmées ; la vue calée (*Stage-locked view*, en option)
  garde le décor d'arcade jusqu'à son bord.
- FinalBurn Neo autonome pour Windows : version d'essai, essayée sous Wine seulement ; les sauvegardes d'état de
  RetroArch ne s'y chargent pas (ni l'inverse).
- Batocera : ARM 64 bits pas essayé sur une vraie machine (seule la compatibilité des fichiers est vérifiée) ; ARM
  32 bits non pris en charge.
- Un flux musique d'Hyper (Y27) reste en ADX dans le zip (sa version Ogg ne passe pas notre contrôle de qualité ; inaudible).
- Le patcheur PS2 16:9 n'est validé que sur Upper et Hyper ; quelques écrans hors combat sont décalés.
- Les cœurs ROCKNIX et Android ont été vérifiés sur PC (émulation ARM) et par l'utilisateur sur deux consoles, pas
  sur tous les appareils.

**En cours (pas terminé)**

- **Hyper + Arcade** : suite de la greffe (Upper comme oracle) ; ensuite, décors SFA1 / SFA2 extraits de l'ISO avec
  leurs animations,
  puis les quatre persos MAX ([architecture](docs/architecture/voie-b-greffe.fr.md)).
- **Upper MAX** : mises au point par lots ([CHANGELOG](CHANGELOG.md)).
- **Réorganisation des données** : phases 1-2 faites et étiquetées, non activées (gain faible sur l'hôte ; en pause
  jusqu'à l'arrivée des MAX dans la greffe) ([architecture](docs/architecture/ARCHI-Reorganisation-Donnees.fr.md)).
- **Décors widescreen redessinés** (export PSD exact, réimportation, injection au fork et au cœur) : en attente ; le
  cœur 16:9 montre l'image dessinée par le jeu (*Raw*) ou, en option, se cale sur le décor d'arcade à la place
  ([DECORS-WS](docs/rapports/DECORS-WS.md), [INJECTION-FORK](docs/rapports/INJECTION-FORK.md)).

## Démarrer

1. **Prérequis** : Python 3.8 ou plus récent, puis `pip install -r requirements.txt` (numpy, capstone, pillow) ;
   votre ISO de *Street Fighter Alpha Anthology* (USA). Pour le banc (facultatif) : MAME 0.285 et le fork.
2. **Chemins** (facultatif : seulement pour d'autres outils ou le banc MAME) : `cp config.example.env config.env`,
   adapter, puis `source config.env`.
3. **Construire les jeux depuis l'ISO** :
   ```bash
   python3 scripts/construction/hsfa_build.py --anthology "Street Fighter Alpha Anthology (USA).iso" \
       --sortie hsfa_sortie --jeux sfa3,upper,hyper
   ```
   Options et empreintes attendues : [docs/guide/construction-iso.fr.md](docs/guide/construction-iso.fr.md).
4. **Installer les cœurs** : les télécharger depuis les releases ou les compiler depuis
   [`patches/fbneo/`](patches/fbneo/README.fr.md), puis suivre le guide [Android](docs/guide/installation-android.fr.md),
   [ROCKNIX / RGB10X](docs/guide/installation-rocknix.fr.md), [Recalbox](docs/guide/installation-recalbox.md),
   [Batocera](docs/guide/installation-batocera.fr.md) ou [Windows](tools/windows/LISEZMOI-windows.md).

Le parcours complet (banc MAME, diagnostic, non-régression) : [docs/guide/demarrage.fr.md](docs/guide/demarrage.fr.md).

## Organisation du dépôt

```
README.md, README.fr.md, CHANGELOG.md, CREDITS.md, NOTICE.md, LICENSE
AGENTS.md, CLAUDE.md    reprendre le projet (règles, méthode, acquis)
construire.sh/.bat      construction en un clic depuis l'ISO
config.example.env      chemins locaux (HSFA_WORKSPACE, HSFA_EXTRACT...) ; requirements.txt
docs/
  guide/                démarrage, construction depuis l'ISO, installation Android / ROCKNIX / Recalbox / Batocera, livraisons
  architecture/         traducteur, mémoire CPS2, banc MAME, cœur FBNeo, réorganisation des données, voie B
  reference/            symboles, formats, carte des modules, adresses
  methodes/             oracle et non-régression, pièges du traducteur
  journal/              HANDOFF.md (journal §1-§221) et son index
  rapports/             rapports d'études détaillés
src/hsfa/               traducteur MIPS -> 68000 et chaîne de construction (mame/ : scripts Lua du banc)
scripts/                construction/ (depuis l'ISO), validation/ (non-régression), qualite/, localiser.py
tools/                  outils par thème (bancs, décors, son d'Hyper, greffe, cœurs, Batocera, flux...)
patches/                mame-fork/ (jeu sfa3hx), fbneo/ (cœur HSFA), traducteur/ (diff du traducteur de la greffe)
re/                     index des connaissances : adresses, champs, zones mémoire (outils dans re/outils/)
max/, tools/max/        travaux de la session SFA3 MAX (PSP)
legacy/                 époque PNACH (PCSX2) : patchs, anciens outils, anciens documents
```

Index de la documentation : [docs/README.fr.md](docs/README.fr.md). Les « §N » cités partout renvoient au
[journal](docs/journal/HANDOFF.md) ; index thématique : [INDEX-HANDOFF](docs/journal/INDEX-HANDOFF.md).

## Jouer l'Anthology sur PS2 / PCSX2

Deux patchs pour l'ISO elle-même ([`tools/ps2-patchs/`](tools/ps2-patchs/README.md)), sans aucune donnée de jeu :
ils écrivent une copie patchée de **votre** ISO USA, la source n'est jamais modifiée.

- **Tout débloqué** : `python3 tools/ps2-patchs/unlock_patcher.py SOURCE.iso [DEST.iso]` ; Upper et Hyper
  disponibles sans carte mémoire (Select sur l'écran de choix de version).
- **Widescreen 16:9 natif** (plus de décor, pas d'image étirée ; comprend le tout-débloqué) :
  `python3 tools/ps2-patchs/sfa_anthology_ws_patcher.py SOURCE.iso [DEST.iso]`, puis régler PCSX2 ou l'écran en 16:9.
- Limites : le 16:9 est validé sur Upper et Hyper, pas décor par décor sur les autres jeux du disque ; quelques écrans
  hors combat décalés. Il change le CRC PCSX2 (`72CE7A78` → `72CE7A38`) : les `.pnach` écrits pour `72CE7A78` ne
  s'appliquent plus à l'ISO 16:9. Détails : [tools/ps2-patchs](tools/ps2-patchs/README.md).

## Époque PNACH

Le projet a commencé par des patchs PCSX2 pour la version PS2 : mode Arcade pour Hyper, widescreen natif, tout
débloqué, essais de décors croisés. Ces travaux sont conservés dans [`legacy/`](legacy/README.md), sans suite.

## Mentions légales

Projet indépendant d'étude et de préservation, à des fins d'interopérabilité. *Street Fighter*, *Street Fighter
Alpha* et les marques associées appartiennent à Capcom. Ce projet n'est ni affilié à Capcom, ni approuvé par Capcom.
**Aucun contenu protégé n'est inclus ni distribué** : ni ROM, ni ISO, ni BIOS, ni graphisme, ni son. Les outils lisent
les données dans la copie du jeu que vous possédez légalement, et les fichiers produits restent chez vous.

## Licence

Chaque composant garde sa licence. Textes complets et notices : [NOTICE.md](NOTICE.md).

| Composant | Licence |
|---|---|
| Code et documentation propres à HSFA (traducteur, construction, outils, docs) | [MIT](LICENSE) |
| Cœurs FBNeo HSFA (`patches/fbneo/`, binaires des releases) | [licence de FinalBurn Neo](patches/fbneo/LICENSE-FBNeo.txt), mot pour mot : **ni vente, ni dons** ; les sources de chaque modification sont dans `patches/fbneo/` |
| stb_vorbis 1.22 (patch `0004`) | domaine public ou MIT (Sean Barrett) |
| 2ᵉ QSound HLE `hsfa_qsound.h` (d'après `qs_c`, DL-1425, patch `0001`) | BSD-3-Clause (superctr, Valley Bell) |
| Fork MAME du banc (`patches/mame-fork/`) | licence de MAME : GPL-2.0 ou ultérieure pour l'ensemble |
