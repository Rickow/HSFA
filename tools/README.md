# Tools by theme

**Français : [README.fr.md](README.fr.md)**

Study and production tools written as the work went along. Each folder matches a report in
[`docs/rapports/`](../docs/rapports/README.md), which describes its use and results. The translator itself is in
[`src/hsfa/`](../src/hsfa/README.md); the build and validation chains are in [`scripts/`](../scripts/README.md).

| Folder | Theme | Report |
|---|---|---|
| [`carto-modules/`](carto-modules/) | map of every module of the Anthology (SFA, SFA2 and variants, Pocket Fighter, menu) | [CARTE-MODULES](../docs/rapports/CARTE-MODULES.md) |
| [`decors/export/`](decors/export/) | exact export of the stages to PSD (camera sweep, stitching) | [DECORS-WS](../docs/rapports/DECORS-WS.md) |
| [`decors/reimport/`](decors/reimport/) | PSD → CPS2 tiles, palettes, free blocks | [REIMPORT](../docs/rapports/REIMPORT.md) |
| [`decors/injection/`](decors/injection/) | injection of the widescreen stages into the translated program (fork, core) | [INJECTION-FORK](../docs/rapports/INJECTION-FORK.md) |
| [`decors/sfa2/`](decors/sfa2/) | import of an SFA2 stage into translated SFA3 | [DECOR-SFA2](../docs/rapports/DECOR-SFA2.md), [DECOR-SFA2-EXPORT](../docs/rapports/DECOR-SFA2-EXPORT.md) |
| [`diagnostics/`](diagnostics/) | one-off investigations: `banque-1a`, `coups` (Sakura / Akuma), `explosion`, `portraits`, `zangief` | [BANQUE-1A](../docs/rapports/BANQUE-1A.md), [COUPS](../docs/rapports/COUPS.md), [EXPLOSION](../docs/rapports/EXPLOSION.md), [PORTRAITS](../docs/rapports/PORTRAITS.md), [ZANGIEF](../docs/rapports/ZANGIEF.md) |
| [`etude-upper-hyper/`](etude-upper-hyper/) | route A / route B for "Upper + Hyper's modes" | [ETUDE-UPPER-HYPER](../docs/rapports/ETUDE-UPPER-HYPER.md) |
| [`fbneo-hsfa/`](fbneo-hsfa/README.md) | core archives (`paquet_fbneo.py`) and installation notes | [FBNEO-HYPER](../docs/rapports/FBNEO-HYPER.md), [REJEU-FBNEO](../docs/rapports/REJEU-FBNEO.md) |
| [`flux/`](flux/) | music stream player (ADX and Ogg Vorbis): stream table, test launchers, Vorbis encoder `flux_ogg.py` / `fluxtool.cpp`, bench `tests/lance_tests.sh` | [FLUX](../docs/rapports/FLUX.md), [PLAN-VORBIS](../docs/rapports/PLAN-VORBIS.md) |
| [`greffe-arcade/`](greffe-arcade/) | route B: graft of Upper's Arcade mode onto Hyper (tools, data, stages); `construction/` ([LISEZMOI](greffe-arcade/construction/LISEZMOI.md)): frozen copy ro9a38 used by `hsfa_build.py --jeux hyperarcade` (§212, §217, §221, §223) | [GREFFE-PREPARATION](../docs/rapports/GREFFE-PREPARATION.md), [GREFFE-DECORS](../docs/rapports/GREFFE-DECORS.md), [BUILD §11](../docs/rapports/BUILD.md) |
| [`hyper-etats/`](hyper-etats/) | Hyper's state machine, mode screen, reference tour `tournee_hyper.lua` | [ETATS-HYPER](../docs/rapports/ETATS-HYPER.md) |
| [`integration-max/`](integration-max/README.md) | conversion of the MAX code and frames to Upper's image; MAX voices; `upper_max/`: Upper MAX steps in `hsfa_build.py --jeux uppermax` (`regen_max.py`, frozen copy `integration_2b31`, §202) | [CONV-MAX](../docs/rapports/CONV-MAX.md), [VOIX-MAX](../docs/rapports/VOIX-MAX.md) |
| [`reorg/`](reorg/) | data relayout, step A: conversion log, RAM oracle, `disposition.lua` | [ETAPE-A](../docs/rapports/ETAPE-A.md) |
| [`rocknix/`](rocknix/) | cores for ROCKNIX (RGB10X): cross-compilation, EmulationStation system, notes | [ROCKNIX](../docs/rapports/ROCKNIX.md) |
| [`son-hyper/`](son-hyper/) | Hyper's sound: per-version SFA1/SFA2 voices, QSound replay, redirection | [SON-HYPER-ROM](../docs/rapports/SON-HYPER-ROM.md) |
| [`son-hyper/partitions/`](son-hyper/partitions/README.md) | Hyper's music as scores: v1.0x drivers, Z80 benches, matching of the variants | [PARTITIONS-HYPER](../docs/rapports/PARTITIONS-HYPER.md) |
| [`symboles/`](symboles/) | SFA3 symbol map (`symboles_ro3.csv`) and its tools | [SYMBOLES](../docs/reference/SYMBOLES.md) |
| [`max/`](max/README.md) | tools of the SFA3 MAX (PSP) session — **do not move**: the MAX session imports them by this path | [MAX-Etude-Contenu-Persos](../docs/MAX-Etude-Contenu-Persos.md) |
| [`android/`](android/README.md) | build of the two Android cores (arm64-v8a, NDK r28c) | [installation-android](../docs/guide/installation-android.md) |
| [`windows/`](windows/LISEZMOI-windows.md) | Windows x64 cores (MinGW-w64 from Linux) and notes | [LISEZMOI-windows](windows/LISEZMOI-windows.md) |
| [`recalbox/`](recalbox/LISEZMOI-recalbox.md) | Recalbox 10 cores (armhf / aarch64), installation | [installation-recalbox](../docs/guide/installation-recalbox.md) |
| [`batocera/`](batocera/INSTALL-batocera-EN.md) | Batocera 43: installer `installer-hsfa-batocera.sh` (an `hsfa` service that puts the cores back at every boot; `retirer` to uninstall), system `es_systems_hsfa.cfg`, `gamelist.xml`, English notes | [installation-batocera](../docs/guide/installation-batocera.md) |
| [`linux/`](linux/README.md) | Linux x86_64 core compatible with glibc 2.27 (the one of v0.1.7 / v0.1.8 needs 2.43): recipe `build_x86_glibc_ancienne.sh`, shims `hsfa_x86_compat.{c,h}` | [README](linux/README.md) |
| [`retrobat/`](retrobat/NOTE-RETROBAT.md) | RetroBat (Windows): installation note and system `es_systems_hsfa.cfg`, **not tried** | [NOTE-RETROBAT](retrobat/NOTE-RETROBAT.md) |
| [`ps2-patchs/`](ps2-patchs/README.md) | PS2 ISO patchers: all unlocked, native 16:9 | [README](ps2-patchs/README.md) |
| [`options/`](options/) | OPTION screen and return to the menu (translator and core diffs), Hyper's BGM in Upper | [OPTIONS](../docs/rapports/OPTIONS.md), [OPTIONS-HYPER-UPPER](../docs/rapports/OPTIONS-HYPER-UPPER.md) |
| [`reviews/`](reviews/README.md) | tools of the critical reviews of 11-12/11: translator guards and audits, graft relocation / tables / registers, per-character-id tables, Upper MAX integration checks | [reviews](../docs/rapports/reviews/README.md) |
| [`sondes-recherche/`](sondes-recherche/README.md) | core PC probe, CPS2 decrypter, disassembler, FBNeo moves bench; added on 11/11: `croise_cps2recomp.py` (index against the cps2recomp notes), `tuiles_cps2*.py` (reuse of the tiles of a CPS-2 ROM), `ocr_gamemachine.sh` (OCR of scanned magazines, search for the book) | [D-SONDES](../docs/rapports/recherche/D-SONDES.md), [J](../docs/rapports/recherche/J-CROISEMENT-CPS2RECOMP-SFA3.md), [M](../docs/rapports/recherche/M-REUTILISATION-TUILES.md), [Q](../docs/rapports/recherche/Q-OPTIMISATION-IMAGES.md) |
| [`guide-coups/`](guide-coups/README.md) | list of the commands of the official guide (without its text) and SuperCombo check | [BANC-COUPS](../docs/rapports/BANC-COUPS.md) |
| [`ppsspp-banc/`](ppsspp-banc/PPSSPP-BANC.md), [`banc-max-psp/`](banc-max-psp/BANC-PSP.md) | PPSSPP as the oracle of the MAX characters; mode B of the moves bench (PSP against Upper MAX) | [PPSSPP-BANC](ppsspp-banc/PPSSPP-BANC.md), [BANC-PSP](banc-max-psp/BANC-PSP.md) |
| [`bancs/`](bancs/README.md) | **common measurement tools**: launcher `lance_emu` (slots, registry, stops by PID), fingerprint of what the emulator loads, daily bench (non-regression of the 4 games on frozen versions), `compare_zips.py` | [README](bancs/README.md) |
| [`banc-coups/`](banc-coups/README.md) | moves bench under MAME (arcade oracle), **MAX non-regression bench** `banc_max.sh` (delivery condition of a MAX batch), frame data against SuperCombo | [BANC-COUPS](../docs/rapports/BANC-COUPS.md) |
| [`frame-data-max/`](frame-data-max/README.md) | frame data of the MAX characters in game rounds: PSP (oracle) against Upper MAX, run on every MAX batch | [README](frame-data-max/README.md) |
| [`decors/sfa1-iso/`](decors/sfa1-iso/README.md), [`decors/sfa2-iso/`](decors/sfa2-iso/README.md) | SFA1 (13) and SFA2 (18) stages extracted from the ISO alone (layers, animations), checks against the arcade under MAME | [README SFA1](decors/sfa1-iso/README.md), [README SFA2](decors/sfa2-iso/README.md) |
| [`decors/integration/`](decors/integration/README.md) | common SFA1 / SFA2 converter → "HSFADC01" batches of the graft's stage area, round trip proven | [README](decors/integration/README.md) |
| [`coeurs/`](coeurs/README.md) | build and static checks of the batch of 12 cores (Linux, Windows, Android, ROCKNIX, Recalbox) | [LIVRAISONS](../docs/guide/LIVRAISONS.md) |
| [`ps2-oracle/`](ps2-oracle/README.md) | PCSX2 as the oracle: dedicated Xvfb, xdotool on the launched PID, PINE (reads; limited writes) | [README](ps2-oracle/README.md) |
| [`asm68k/`](asm68k/README.md) | in-house 68000 assembler `hsfa_asm68k` (replaces vasm in the build) | [README](asm68k/README.md) |
| [`constructeur/`](constructeur/README.md) | all-in-one builder (one executable per system, CI) | [README](constructeur/README.md) |

## Paths

These tools were written in the developer's workspace; their paths are published in the form
`<workspace>/...`. Many read working folders (`<workspace>/work/agent_*`, `work/carto_ro9`…) that are not
published: they are **study archives**, reusable by adapting the paths. Mapping of the published
folders: [`scripts/correspondances.tsv`](../scripts/correspondances.tsv); runnable copy:
[`scripts/localiser.py`](../scripts/localiser.py). The imports of each script are checked by
[`scripts/qualite/verifier_imports.py`](../scripts/qualite/verifier_imports.py) (unpublished dependencies classed as
"external").

The common tools (`bancs/`, `banc-coups/`, `coeurs/`, `ps2-oracle/`) are set through environment variables
(`HSFA_WORKSPACE`, `HSFA_BANC_LUA`, `LOT`, `PS2_*`: see their README) and run from the repository. In the
workspace, `lance_emu`, `empreinte.*` and `banc_jour.*` live in `<workspace>/work/outils/`: the other benches call
them there.
