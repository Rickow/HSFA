# Documentation

**Français : [README.fr.md](README.fr.md)**

Working documentation of the HSFA project. Overview and status: [README](../README.md).

> **Language**: English is the default language of the repository since 2026-11-12. The key documents (entry pages,
> guides, architecture, translator methods) are in English; each keeps its French version next to it as
> `<name>.fr.md`. The journal (`journal/`), the reports (`rapports/`), the reference pages (`reference/`) and the
> other documents not yet translated are in French.

## Guide — using it

| Document | Topic |
|---|---|
| [guide/demarrage.md](guide/demarrage.md) | from the ISO to the translated game on the MAME bench, diagnosis, non-regression |
| [guide/construction-iso.md](guide/construction-iso.md) | building the three games and the core archives from the ISO (`hsfa_build.py`) |
| [guide/installation-android.md](guide/installation-android.md) | FBNeo HSFA core on RetroArch Android |
| [guide/installation-rocknix.md](guide/installation-rocknix.md) | core on RGB10X / ROCKNIX |
| [guide/installation-recalbox.md](guide/installation-recalbox.md) | core on Recalbox 10 (Raspberry Pi) |
| [guide/installation-fbneo-autonome-windows.md](guide/installation-fbneo-autonome-windows.md) | standalone FinalBurn Neo HSFA for Windows, without RetroArch (test build, planned with the next version) |
| [guide/installation-batocera.md](guide/installation-batocera.md) | cores and five games on Batocera 43 (installer and service; tried on PC); RetroBat: [untested note](../tools/retrobat/NOTE-RETROBAT.md) |
| [guide/LIVRAISONS.md](guide/LIVRAISONS.md) | register of the cores and archives handed over (names, md5) up to 2026-10-24; after that, the cores of each release and the unpublished batches (§4) |

## Architecture — how it is built

| Document | Topic |
|---|---|
| [architecture/traducteur.md](architecture/traducteur.md) | the MIPS → 68000 translator: principle, chain, what the port added |
| [architecture/memoire-cps2.md](architecture/memoire-cps2.md) | the "CPS2 mode" memory recipe (§29), address conversion, pitfalls |
| [architecture/banc-mame.md](architecture/banc-mame.md) | MAME bench, Lua scripts, `sfa3hx` fork |
| [architecture/coeur-fbneo.md](architecture/coeur-fbneo.md) | FBNeo libretro core "HSFA": drivers, archives, sound, platforms |
| [architecture/coeur-fbneo-patchs.md](architecture/coeur-fbneo-patchs.md) | one sheet per core patch (rows 1 to 16 of the table in `patches/fbneo/README.md`) |
| [architecture/ARCHI-Reorganisation-Donnees.md](architecture/ARCHI-Reorganisation-Donnees.md) | data relayout: removing the adapters, arcade layout |
| [architecture/voie-b-greffe.md](architecture/voie-b-greffe.md) | route B: grafting Upper's Arcade mode onto Hyper |
| [architecture/OUTILS.md](architecture/OUTILS.md) | **detailed reference**: pipeline, sheet of each script, bench, formats, recipes, known inconsistencies |

## Reference — to look things up (in French)

| Document | Topic |
|---|---|
| [reference/adresses.md](reference/adresses.md) | useful addresses (game RAM, hardware, produced image) |
| [reference/carte-modules.md](reference/carte-modules.md) | Anthology modules, groups of `X_DATA.BIN` |
| [reference/formats.md](reference/formats.md) | formats of the produced files, of the Anthology data, of the stages and of the sound |
| [reference/SYMBOLES.md](reference/SYMBOLES.md) | map of SFA3's symbols in the three address spaces |
| [reference/FRAMES-Anthology.md](reference/FRAMES-Anthology.md) | sprite frame format |
| [reference/sfz2a-dash-cps2.md](reference/sfz2a-dash-cps2.md) | third-party project SFZ2A-DASH-CPS2 (Gold Cammy on the Zero 2 Alpha arcade board) |
| [MAX-Etude-Contenu-Persos.md](MAX-Etude-Contenu-Persos.md) | SFA3 MAX (PSP): content of the characters, conversion to the CPS2 (document of the MAX session, left at the root of `docs/`) |

## Methods — how to work

| Document | Topic |
|---|---|
| [methodes/oracle-et-non-regression.md](methodes/oracle-et-non-regression.md) | arcade oracle, non-regression battery, switches, silent losses |
| [methodes/pieges-du-traducteur.md](methodes/pieges-du-traducteur.md) | pitfalls met, by family |

## Journal and reports (in French)

| Document | Topic |
|---|---|
| [journal/README.md](journal/README.md) | the journal (`HANDOFF.md`, §1-§221), its index, the state of play; mapping of the old paths |
| [rapports/README.md](rapports/README.md) | detailed study reports (since 2026-10-07) |
| [rapports/recherche/README.md](rapports/recherche/README.md) | research: sheets A to R (arcade versions and bugs, probes, MAX moves, neighbouring projects, cross-check with cps2recomp, room on a real CPS-2); sheets J to R (2026-11-10, revised on 11/11): [J](rapports/recherche/J-CROISEMENT-CPS2RECOMP-SFA3.md), [K](rapports/recherche/K-CPS2RECOMP-PISTES.md), [L](rapports/recherche/L-PROJETS-OUVERTS-2026-11.md), [M](rapports/recherche/M-REUTILISATION-TUILES.md), [N](rapports/recherche/N-PARADIGMES-LIMITES-ROM.md), [O](rapports/recherche/O-CPS2-POSSIBILITES.md), [P](rapports/recherche/P-SYNTHESE-PLACE-CPS2.md) (synthesis), [Q](rapports/recherche/Q-OPTIMISATION-IMAGES.md), [R](rapports/recherche/R-SOLUTIONS-PAR-JEU.md) |

## Elsewhere in the repository

- [src/hsfa/README.md](../src/hsfa/README.md): the translator's scripts;
- [scripts/README.md](../scripts/README.md): build, validation, quality;
- [tools/README.md](../tools/README.md): tools by topic;
- [patches/README.md](../patches/README.md): patches of the MAME and FBNeo forks;
- [legacy/README.md](../legacy/README.md): PNACH era;
- [max/README.md](../max/README.md): SFA3 MAX session.

The maintainer's decisions and expectations: `ATTENTES-ET-DECISIONS.md`, in the private repository only (not exported).

Absolute paths are replaced by `<workspace>` (the developer's workspace); see
[scripts/correspondances.tsv](../scripts/correspondances.tsv).
