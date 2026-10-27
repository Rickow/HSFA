# HSFA — Street Fighter Alpha Anthology (PS2) retranslated to CPS2 68000

**Français : [README.fr.md](README.fr.md)** (the working language of the project; all documentation is in French)

## Play in 3 steps

> **No game data is provided.** You need your own copy of *Street Fighter Alpha Anthology* (PS2, USA, `SLUS-21317`).
> Not in this release: **Upper MAX** (the four SFA3 MAX characters) and the **Arcade-mode graft** onto Hyper.

1. **Download the cores** from the [releases](../../releases) page: `hsfa-v0.1-cores-<platform>.zip` for Android
   (arm64), ROCKNIX (aarch64: RGB10X, R36S…), Windows (x64) or Linux (x86_64). Each archive holds the 4:3 core
   (`fbneo_hsfa`) and the 16:9 core (`fbneo_hsfaws`), with their licence.
2. **Build the games from your ISO** (Python 3.8+, about 6 minutes):
   ```bash
   pip install -r requirements.txt
   python3 scripts/construction/hsfa_build.py --anthology "Street Fighter Alpha Anthology (USA).iso" --sortie hsfa_out
   ```
   You get `hsfa_out/archives/sfa3hsfa.zip` (SFA3), `sfa3uhsfa.zip` (Upper) and `sfa3hhsfa.zip` (Hyper).
   - The ISO must be the USA one (`SLUS-21317`), as a `.iso` image (2,048 bytes per sector); the "All Unlocked"
     variant is accepted too. Convert a `.chd` first (`chdman extractdvd`).
   - Music is packed as Ogg Vorbis: this needs `ffmpeg` (libvorbis), `gcc` and `g++`. Without them, add
     `--flux-format adx` (bigger Hyper zip).
   - `--arcade sfa3.zip` (optional) takes the SFA3 graphics ROM from your own arcade set instead of rebuilding it from
     the ISO; the zips are then identical to the project's reference build. Details:
     [docs/guide/construction-iso.md](docs/guide/construction-iso.md) (in French).
3. **Install and play**: copy the core into RetroArch's `cores` folder and the three zips into your ROM folder (keep
   their names), then load a zip with "FinalBurn Neo HSFA" (4:3) or "FinalBurn Neo HSFA Widescreen" (16:9). Guides
   (in French): [Android](docs/guide/installation-android.md), [ROCKNIX / RGB10X](docs/guide/installation-rocknix.md),
   [Windows](tools/windows/LISEZMOI-windows.md); on Linux, copy the `.so` files into `~/.config/retroarch/cores/`.

Prefer the PS2 game itself? Two ISO patchers (all unlocked, native 16:9) are described
[below](#playing-the-anthology-on-ps2--pcsx2).

## What HSFA is

*Street Fighter Alpha Anthology* (PS2, `SLUS-21317`, CRC `72CE7A78`) does not emulate the arcade boards. Its games
are a **static recompilation of the original 68000 code to MIPS R5900**: the 68K registers live in the PS2 scratchpad.
HSFA goes the other way. It **recognises the recompiler's idioms and re-emits the original 68000**, assembles a CPS2
program ROM and runs it on an emulated CPS2. Three games are covered:

| PS2 module | Game | Driver |
|---|---|---|
| `ro3` | Street Fighter Alpha 3 | `sfa3hsfa` |
| `ro5` | SFA3 **Upper** (the console version's extended roster) | `sfa3uhsfa` |
| `ro9` | **Hyper** Street Fighter Alpha (ZERO / ZERO 2 / ALPHA / ZERO 3 versions of each character) | `sfa3hhsfa` |

They run in two environments:
- a **MAME fork**: development bench, game `sfa3hx`;
- a **FBNeo libretro core "HSFA"** for RetroArch: Android (arm64), Linux (x86_64) and ROCKNIX (RGB10X, aarch64), in
  4:3 and 16:9.

> **No game data here.** This repository only contains tools, patches and documentation. Everything that comes from
> the game (programs, graphics, sound) is rebuilt **from your own ISO** of the Anthology.


> **Picking the project up** (human or agent): read [AGENTS.md](AGENTS.md) (in French): rules, method, findings and open work, updated with every discovery.

## Status (2026-10-27, release v0.1)

**Working**

| | Status | Details |
|---|---|---|
| SFA3 (`ro3`) | complete: attract mode; Arcade mode to the credits, **32/32 endings** match the arcade; VERSUS, SURVIVAL, DRAMATIC, TRAINING; controls **42/42** identical to the arcade; arcade turbo rate (133.3%); sound validated | [journal §110-§113](docs/journal/HANDOFF.md), [non-regression](docs/methodes/oracle-et-non-regression.md) |
| Upper (`ro5`) | playable end to end, **40/40 endings**; hybrid sound ROM (SFA3 music + Upper voices); the music that exists only as streams on the disc is packed in the zip as Ogg Vorbis | [§122-§128](docs/journal/HANDOFF.md), [FLUX](docs/rapports/FLUX.md) |
| Hyper (`ro9`) | VERSUS without exceptions (151-match tour); supers of the ZERO / ZERO 2 / ALPHA versions no longer crash; super gauge and TRAINING fixed; ZERO / ZERO 2 / ALPHA music in the zip (Ogg Vorbis); per-version SFA1 / SFA2 voices replayed on a 2nd QSound when the replay table is present (see below) | [§145-§173](docs/journal/HANDOFF.md), [FBNEO-HYPER](docs/rapports/FBNEO-HYPER.md), [REJEU-FBNEO](docs/rapports/REJEU-FBNEO.md) |
| Menus | OPTION and EXIT return to the mode menu; the PS2 option-screen settings (difficulty, damage, timer, speed, rounds) are core options | [§147-§148](docs/journal/HANDOFF.md), [OPTIONS](docs/rapports/OPTIONS.md) |
| FBNeo HSFA core | Android, Linux, ROCKNIX, Windows; 4:3 and 16:9 (with "Screen format (fill height)" for 4:3 to 16:10 screens); PSP-style transparent shadows; taunt on Select in fights; tested by the user on RG477M and RGB10X | [patches](patches/fbneo/README.md), [Android](docs/guide/installation-android.md), [ROCKNIX](docs/guide/installation-rocknix.md) |
| Build from the ISO | `hsfa_build.py` builds the three games from your ISO alone; program ROMs identical (md5) to the official v151 archives (SFA3 `e0f1cfdc`, Upper `0b8ecca2`, Hyper `39985037` with the replay table); zips identical from one build to the next | [guide](docs/guide/construction-iso.md), [BUILD](docs/rapports/BUILD.md) |

**Known limits of v0.1**

- **Hyper's per-version voices** need the QSound replay table of SFA1 / SFA2 (`--rejeu-table`, see the
  [build guide](docs/guide/construction-iso.md)). Without it,
  `hsfa_build.py` keeps Hyper's SFA3 voices for every version (program `e21ebb89` instead of `39985037`) and the zip
  has no replay. Planned for v0.2: the build will regenerate the table from your own ISO.
- Chun-Li's Kikosho: the big arcs are still invisible (SFA3 drawing issue being tracked).
- One Hyper music stream (Y27) stays in ADX inside the zip (no quality check yet).
- The 16:9 PS2 patcher is validated on Upper and Hyper only; a few non-fight screens are offset.
- The ROCKNIX and Android cores were checked on PC (ARM emulation) and by the user on two handhelds, not on every
  device.

**In progress (not in this release)**

- **Route B**: graft Upper's Arcade-mode layer onto Hyper ("augmented ro9"), with Upper as the oracle
  ([architecture](docs/architecture/voie-b-greffe.md)).
- **Upper MAX**: Eagle, Maki, Yun and Ingrid (SFA3 MAX, PSP) in Upper, driver `sfa3umhsfa`
  ([CONV-MAX](docs/rapports/CONV-MAX.md), [INTEGRATION-MAX-UPPER](docs/rapports/INTEGRATION-MAX-UPPER.md)).
- **Data relayout**: remove the memory adapters, ~20% of 68K time in fights
  ([architecture](docs/architecture/ARCHI-Reorganisation-Donnees.md)).
- **Widescreen stages** and SFA2 stages: exact PSD export, re-import, injection in the fork and the core
  ([DECORS-WS](docs/rapports/DECORS-WS.md), [INJECTION-FORK](docs/rapports/INJECTION-FORK.md)).

## Getting started

1. **Requirements**: Python 3.8 or newer, then `pip install -r requirements.txt` (numpy, capstone, pillow); your ISO
   of *Street Fighter Alpha Anthology* (USA). For the bench (optional): MAME 0.285 and the fork.
2. **Paths** (optional; only for other tool locations or the MAME bench): `cp config.example.env config.env`, edit,
   then `source config.env`.
3. **Build the games from the ISO**:
   ```bash
   python3 scripts/construction/hsfa_build.py --anthology "Street Fighter Alpha Anthology (USA).iso" \
       --sortie hsfa_sortie --jeux sfa3,upper,hyper
   ```
   Options and expected fingerprints: [docs/guide/construction-iso.md](docs/guide/construction-iso.md).
4. **Install the cores**: build them from [`patches/fbneo/`](patches/fbneo/README.md), then follow the
   [Android](docs/guide/installation-android.md) or [ROCKNIX / RGB10X](docs/guide/installation-rocknix.md) guide.

Full walkthrough (MAME bench, diagnosis, non-regression): [docs/guide/demarrage.md](docs/guide/demarrage.md).

## Repository layout

```
README.md, README.fr.md, CHANGELOG.md
config.example.env      local paths (HSFA_WORKSPACE, HSFA_EXTRACT...); requirements.txt
docs/
  guide/                getting started, build from the ISO, Android and ROCKNIX install
  architecture/         translator, CPS2 memory, MAME bench, FBNeo core, data relayout, route B
  reference/            symbols, formats, module map, addresses
  methodes/             oracle and non-regression, translator pitfalls
  journal/              HANDOFF.md (journal §1-§146) and its index
  rapports/             detailed study reports
src/hsfa/               MIPS -> 68000 translator and build chain (mame/: bench Lua scripts)
scripts/                construction/ (from the ISO), validation/ (non-regression), qualite/, localiser.py
tools/                  tools by topic (stages, Hyper sound, graft, relayout, streams, ROCKNIX...)
patches/                mame-fork/ (sfa3hx game), fbneo/ (HSFA core)
max/, tools/max/        SFA3 MAX (PSP) session work
legacy/                 PNACH era (PCSX2): patches, old tools, old documents
```

Documentation index: [docs/README.md](docs/README.md). The "§N" references point to the
[journal](docs/journal/HANDOFF.md); thematic index: [INDEX-HANDOFF](docs/journal/INDEX-HANDOFF.md).

## Playing the Anthology on PS2 / PCSX2

Two patchers for the ISO itself ([`tools/ps2-patchs/`](tools/ps2-patchs/README.md), notes in French), with no game
data: they write a patched copy of **your** USA ISO; the source is never modified.

- **All unlocked**: `python3 tools/ps2-patchs/unlock_patcher.py SOURCE.iso [DEST.iso]`; Upper and Hyper available
  without a memory card (Select on the version screen).
- **Native 16:9 widescreen** (more stage, no stretching; includes the unlock):
  `python3 tools/ps2-patchs/sfa_anthology_ws_patcher.py SOURCE.iso [DEST.iso]`, then set PCSX2 or the TV to 16:9.
- Limits: 16:9 is validated on Upper and Hyper, not stage by stage on the other games of the disc; a few non-fight
  screens are offset. It changes the PCSX2 CRC (`72CE7A78` → `72CE7A38`): `.pnach` files written for `72CE7A78` no
  longer apply to the 16:9 ISO. Details: [tools/ps2-patchs](tools/ps2-patchs/README.md).

## PNACH era

The project started with PCSX2 patches for the PS2 version: Arcade mode for Hyper, native widescreen, all unlocked,
cross-stage experiments. That work is kept, frozen, in [`legacy/`](legacy/README.md).

## Legal

Independent study and preservation project, for interoperability. *Street Fighter*, *Street Fighter Alpha* and related
marks are trademarks of Capcom. This project is not affiliated with or endorsed by Capcom. **No copyrighted content is
included or distributed**: no ROM, ISO, BIOS, graphics or sound. The tools read the data from the copy of the game you
legally own, and the files they produce stay with you.

## License

Each component keeps its own licence. Full texts and notices: [NOTICE.md](NOTICE.md).

| Component | Licence |
|---|---|
| HSFA's own code and documentation (translator, build scripts, tools, docs) | [MIT](LICENSE) |
| FBNeo HSFA cores (`patches/fbneo/`, release binaries) | [FinalBurn Neo licence](patches/fbneo/LICENSE-FBNeo.txt), verbatim: **no sale, no donations**; the source of every change is in `patches/fbneo/` |
| stb_vorbis 1.22 (patch `0004`) | public domain or MIT (Sean Barrett) |
| 2nd QSound HLE `hsfa_qsound.h` (from `qs_c`, DL-1425, patch `0001`) | BSD-3-Clause (superctr, Valley Bell) |
| MAME fork of the bench (`patches/mame-fork/`) | MAME licence: GPL-2.0-or-later for MAME as a whole |
