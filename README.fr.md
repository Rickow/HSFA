# HSFA — Street Fighter Alpha Anthology (PS2) retraduit en 68000 CPS2

**English: [README.md](README.md)**

## Jouer en 3 étapes

> **Aucune donnée de jeu n'est fournie.** Il faut votre propre copie de *Street Fighter Alpha Anthology* (PS2, USA,
> `SLUS-21317`). Pas dans cette release : **Upper MAX** (les quatre persos de SFA3 MAX) et la **greffe du mode
> Arcade** sur Hyper.

1. **Télécharger les cœurs** depuis la page des [releases](../../releases) : `hsfa-v0.1.6-cores-<plateforme>.zip` pour
   Android (arm64), ROCKNIX (aarch64 : RGB10X, R36S…), Windows (x64), Linux (x86_64) ou Recalbox 10 (Raspberry Pi ;
   essayé sur un Pi 3B). Chaque archive contient le
   cœur 4:3 (`fbneo_hsfa`) et le cœur 16:9 (`fbneo_hsfaws`), avec leur licence.
2. **Construire les jeux depuis votre ISO** (Python 3.8+, environ 6 minutes). Le plus simple : télécharger
   `hsfa-v0.1.6-construction.zip` dans la release (ou ce dépôt), puis lancer **`construire.sh`** (Linux, macOS, WSL) ou
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
     [docs/guide/construction-iso.md](docs/guide/construction-iso.md).
3. **Installer et jouer** : copier le cœur dans le dossier `cores` de RetroArch et les trois zips dans le dossier des
   ROM (sans les renommer), puis charger un zip avec « FinalBurn Neo HSFA » (4:3) ou « FinalBurn Neo HSFA
   Widescreen » (16:9). Guides : [Android](docs/guide/installation-android.md),
   [ROCKNIX / RGB10X](docs/guide/installation-rocknix.md), [Recalbox](docs/guide/installation-recalbox.md),
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
  aarch64) et Recalbox 10 (Raspberry Pi : armhf et aarch64), en 4:3 et en 16:9 (12 cœurs par release). Les cœurs
  contiennent aussi deux pilotes plus récents : `sfa3umhsfa` (Upper MAX, constructible depuis vos disques depuis le
  2026-11-07, voir plus bas) et `sfa3hahsfa` (Hyper + Arcade, versions d'essai seulement).

> **Aucune donnée de jeu ici.** Le dépôt ne contient que des outils, des patchs et de la documentation. Tout ce qui
> vient du jeu (programmes, graphismes, sons) est reconstruit **depuis votre propre ISO** de l'Anthology.


> **Reprendre le projet** (personne ou agent) : lire [AGENTS.md](AGENTS.md), qui condense règles, méthode, acquis et chantiers, tenu à jour à chaque découverte.

## État (2026-11-08, release v0.1.6)

**Ce qui marche**

| | État | Détails |
|---|---|---|
| SFA3 (`ro3`) | complet : attraction ; mode Arcade jusqu'au générique, **32/32 fins** conformes à l'arcade (v0.1.6 : les poupées de Shadaloo redessinées par le portage PS2 dans quatre fins sont revenues, avec les cœurs v0.1.6) ; VERSUS, SURVIVAL, DRAMATIC, TRAINING ; commandes **42/42** identiques à l'arcade ; cadence turbo de l'arcade (133,3 %) ; son validé | [journal §110-§113](docs/journal/HANDOFF.md), [non-régression](docs/methodes/oracle-et-non-regression.md) |
| Upper (`ro5`) | jouable de bout en bout, **40/40 fins** ; ROM son hybride (musiques de SFA3 + voix d'Upper) ; les musiques qui n'existent qu'en flux sur le disque sont rangées dans le zip en Ogg Vorbis | [§122-§128](docs/journal/HANDOFF.md), [FLUX](docs/rapports/FLUX.md) |
| Hyper (`ro9`) | VERSUS sans exception (tournée de 151 combats) ; les supers des versions ZERO / ZERO 2 / ALPHA ne plantent plus ; jauge de super et TRAINING corrigés ; musiques ZERO / ZERO 2 / ALPHA dans le zip (Ogg Vorbis) ; voix SFA1 / SFA2 par version, rejouées sur un 2ᵉ QSound, quand la table du rejeu est là (voir plus bas) | [§145-§173](docs/journal/HANDOFF.md), [FBNEO-HYPER](docs/rapports/FBNEO-HYPER.md), [REJEU-FBNEO](docs/rapports/REJEU-FBNEO.md) |
| Menus | OPTION et EXIT ramènent au menu des modes ; les réglages de l'écran d'options PS2 (difficulté, dégâts, chrono, vitesse, manches) sont des options du cœur | [§147-§148](docs/journal/HANDOFF.md), [OPTIONS](docs/rapports/OPTIONS.md) |
| Cœur FBNeo HSFA | Android, Linux, ROCKNIX, Windows, Recalbox 10 (Raspberry Pi, essayé sur un Pi 3B) ; option « Blood » (sang rouge, non censuré, par défaut) ; option « Skip idle loops » (activée par défaut : 33 à 41 % de calcul en moins par image, même résultat) ; vrai 16:9 (v0.1.5 : 512 × 224, rapport exact, vue calée sur le décor aux bouts de l'arène, HUD centré) ; 4:3 et 16:9 (avec « Screen format (fill height) » pour les écrans de 4:3 à 16:10) ; ombres transparentes comme sur PSP ; provocation sur Select en combat ; persos cachés d'Upper (v0.1.2 : Start tenu + un bouton sur Akuma / Balrog pour Shin Akuma / EX Balrog, Pièce pour la roulette) ; essayé par l'utilisateur sur RG477M et RGB10X | [patchs](patches/fbneo/README.md), [Android](docs/guide/installation-android.md), [ROCKNIX](docs/guide/installation-rocknix.md) |
| Construction depuis l'ISO | `hsfa_build.py` construit les trois jeux depuis votre ISO seule ; ROM programme identiques (md5) aux archives officielles v154 (SFA3 `e0f1cfdc`, Upper `0b8ecca2`, Hyper `b8e699cf` avec la table du rejeu) ; zips identiques d'une construction à l'autre | [guide](docs/guide/construction-iso.md), [BUILD](docs/rapports/BUILD.md) |

**Limites connues de la v0.1.x**

- **Voix d'Hyper par version** : il faut la table du rejeu QSound de SFA1 / SFA2 (`--rejeu-table`, voir le
  [guide de construction](docs/guide/construction-iso.md)). Sans elle, `hsfa_build.py` garde les voix de SFA3 pour toutes les versions d'Hyper (programme `dda35430` au lieu de
  `b8e699cf`) et le zip n'a pas de rejeu. Prévu en v0.2 : la construction recréera la table depuis votre ISO.
- Kikosho de Chun-Li : les grands arcs restent invisibles (défaut de dessin de SFA3, en cours).
- Un flux musique d'Hyper (Y27) reste en ADX dans le zip (pas encore de contrôle de qualité).
- Le patcheur PS2 16:9 n'est validé que sur Upper et Hyper ; quelques écrans hors combat sont décalés.
- Les cœurs ROCKNIX et Android ont été vérifiés sur PC (émulation ARM) et par l'utilisateur sur deux consoles, pas
  sur tous les appareils.

**En cours (pas dans cette release)**

- **Voie B, « Hyper + Arcade »** : mode Arcade d'Upper greffé sur Hyper (« ro9 augmenté », pilote `sfa3hahsfa`), avec
  Upper comme oracle ; versions d'essai pour l'instant. **Construction expérimentale depuis l'ISO** (état ro9a35b) :
  `hsfa_build.py --jeux hyperarcade` ; avec la ROM d'arcade et la table du rejeu, zip de ro9a35b à l'octet hors
  `hsfa_info.txt` ([guide §6](docs/guide/construction-iso.md)). Ensuite : décors SFA1 / SFA2 extraits de l'ISO avec leurs
  animations, puis les quatre persos MAX ([architecture](docs/architecture/voie-b-greffe.md)).
- **Upper MAX** : Eagle, Maki, Yun et Ingrid (SFA3 MAX, PSP) dans Upper, pilote `sfa3umhsfa`. **Construction expérimentale
  depuis vos deux disques** (Anthology PS2 + ISO PSP européenne de *SFA3 MAX*, ULES-00235), rien d'autre à installer
  (assembleur 68000 du projet) : `hsfa_build.py --jeux uppermax --psp-iso <ISO PSP>` ; sans l'ISO PSP, Upper normal
  ([guide §5](docs/guide/construction-iso.md), [CONV-MAX](docs/rapports/CONV-MAX.md), [INTEGRATION-MAX-UPPER](docs/rapports/INTEGRATION-MAX-UPPER.md)).
- **Réorganisation des données** : phases 1-2 faites et étiquetées, non activées (gain faible sur l'hôte ; en pause
  jusqu'à l'arrivée des MAX dans la greffe) ([architecture](docs/architecture/ARCHI-Reorganisation-Donnees.md)).
- **Décors widescreen redessinés** (export PSD exact, réimportation, injection au fork et au cœur) : en attente ; la vue
  16:9 se cale sur le décor d'arcade à la place
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
   Options et empreintes attendues : [docs/guide/construction-iso.md](docs/guide/construction-iso.md).
4. **Installer les cœurs** : les télécharger depuis les releases ou les compiler depuis
   [`patches/fbneo/`](patches/fbneo/README.md), puis suivre le guide [Android](docs/guide/installation-android.md),
   [ROCKNIX / RGB10X](docs/guide/installation-rocknix.md), [Recalbox](docs/guide/installation-recalbox.md) ou
   [Windows](tools/windows/LISEZMOI-windows.md).

Le parcours complet (banc MAME, diagnostic, non-régression) : [docs/guide/demarrage.md](docs/guide/demarrage.md).

## Organisation du dépôt

```
README.md, README.fr.md, CHANGELOG.md, CREDITS.md, NOTICE.md, LICENSE
AGENTS.md, CLAUDE.md    reprendre le projet (règles, méthode, acquis)
construire.sh/.bat      construction en un clic depuis l'ISO
config.example.env      chemins locaux (HSFA_WORKSPACE, HSFA_EXTRACT...) ; requirements.txt
docs/
  guide/                démarrage, construction depuis l'ISO, installation Android / ROCKNIX / Recalbox, livraisons
  architecture/         traducteur, mémoire CPS2, banc MAME, cœur FBNeo, réorganisation des données, voie B
  reference/            symboles, formats, carte des modules, adresses
  methodes/             oracle et non-régression, pièges du traducteur
  journal/              HANDOFF.md (journal §1-§201) et son index
  rapports/             rapports d'études détaillés
src/hsfa/               traducteur MIPS -> 68000 et chaîne de construction (mame/ : scripts Lua du banc)
scripts/                construction/ (depuis l'ISO), validation/ (non-régression), qualite/, localiser.py
tools/                  outils par thème (décors, son d'Hyper, greffe, réorganisation, flux, ROCKNIX...)
patches/                mame-fork/ (jeu sfa3hx), fbneo/ (cœur HSFA), traducteur/ (diff du traducteur de la greffe)
re/                     index des connaissances : adresses, champs, zones mémoire (outils dans re/outils/)
max/, tools/max/        travaux de la session SFA3 MAX (PSP)
legacy/                 époque PNACH (PCSX2) : patchs, anciens outils, anciens documents
```

Index de la documentation : [docs/README.md](docs/README.md). Les « §N » cités partout renvoient au
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
