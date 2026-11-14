# HSFA — Street Fighter Alpha Anthology (PS2) retranslated to CPS2 68000

**Français : [README.fr.md](README.fr.md)** (English is the default language of the repository; the key documents keep a French translation as `<name>.fr.md`, the journal and the reports are in French)

## Play in 3 steps

> **No game data is provided.** You need your own copy of *Street Fighter Alpha Anthology* (PS2, USA, `SLUS-21317`).
> **Upper MAX** (the four SFA3 MAX characters) and **Hyper + Arcade** (Upper's Arcade mode grafted onto Hyper) are
> experimental: see below.

1. **Download the cores** from the [releases](../../releases) page: `hsfa-<version>-cores-<platform>.zip` for Android
   (arm64), ROCKNIX (aarch64: RGB10X, R36S…), Windows (x64), Linux (x86_64) or Recalbox 10 (Raspberry Pi; tested on
   a Pi 3B); Batocera 43: `hsfa-<version>-cores-batocera.zip` and its guide. Each archive holds the 4:3 core
   (`fbneo_hsfa`) and the 16:9 core (`fbneo_hsfaws`), with their licence. The stable version is **v0.1.10**; older
   versions and pre-releases are on the same page.
2. **Build the games from your ISO** (Python 3.8+, about 6 minutes). Nothing to install: the all-in-one builder
   `hsfa-constructeur-<system>.zip` from the release (Windows, Linux, macOS). Otherwise: download
   `hsfa-<version>-construction.zip` from the release (or this repository), then run **`construire.sh`** (Linux, macOS, WSL) or double-click
   **`construire.bat`** (Windows, experimental: untested so far) and give it your ISO. It sets up Python, builds the
   Ogg encoder if `gcc` is there, and builds the three games into `sortie/archives/`. By hand:
   ```bash
   pip install -r requirements.txt
   python3 scripts/construction/hsfa_build.py --anthology "Street Fighter Alpha Anthology (USA).iso" --sortie hsfa_out
   ```
   You get `hsfa_out/archives/sfa3hsfa.zip` (SFA3), `sfa3uhsfa.zip` (Upper) and `sfa3hhsfa.zip` (Hyper).
   - The ISO must be the USA one (`SLUS-21317`), as a `.iso` image (2,048 bytes per sector); the "All Unlocked"
     variant is accepted too. Convert a `.chd` first (`chdman extractdvd`).
   - Music is packed as Ogg Vorbis: this needs `gcc` and `g++`. The encoder (`tools/flux/oggenc`) is compiled once
     from the official libvorbis sources: `python3 tools/flux/oggenc/construit_oggenc.py --sources DIR --telecharge`,
     then `HSFA_OGGENC_SOURCES=DIR`. It gives the same bytes on every system. Without `gcc` / `g++`, add
     `--flux-format adx` (bigger Hyper zip).
   - `--arcade sfa3.zip` (optional) takes the SFA3 graphics ROM from your own arcade set instead of rebuilding it from
     the ISO; the zips are then identical to the project's reference build. Details:
     [docs/guide/construction-iso.md](docs/guide/construction-iso.md).
3. **Install and play**: copy the core into RetroArch's `cores` folder and the three zips into your ROM folder (keep
   their names), then load a zip with "FinalBurn Neo HSFA" (4:3) or "FinalBurn Neo HSFA Widescreen" (16:9). Guides:
   [Android](docs/guide/installation-android.md), [ROCKNIX / RGB10X](docs/guide/installation-rocknix.md), [Recalbox](docs/guide/installation-recalbox.md), [Batocera](docs/guide/installation-batocera.md),
   [Windows](tools/windows/LISEZMOI-windows.md) (in French); on Linux, copy the `.so` files into `~/.config/retroarch/cores/`.

**Feedback**: bugs and questions in the [Issues](../../issues) (English or French), including Recalbox (tested on a
Raspberry Pi 3B; launching from Recalbox's game list does not work yet, load the core from RetroArch's menu).

Prefer the PS2 game itself? Two ISO patchers (all unlocked, native 16:9) are described
[below](#playing-the-anthology-on-ps2--pcsx2).

**Credits**: everyone whose work HSFA builds on, in [CREDITS.md](CREDITS.md).

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
- a **FBNeo libretro core "HSFA"** for RetroArch: Android (arm64), Linux (x86_64), Windows (x64), ROCKNIX (RGB10X,
  aarch64) and Recalbox 10 (Raspberry Pi: armhf and aarch64), in 4:3 and 16:9 (12 cores per release); Batocera 43
  through an installer ([guide](docs/guide/installation-batocera.md)). The cores also hold two
  experimental drivers: `sfa3umhsfa` (Upper MAX, buildable from your two discs since v0.1.7) and `sfa3hahsfa`
  (Hyper + Arcade, buildable from your ISO since the v0.1.8 pre-release).

> **No game data here.** This repository only contains tools, patches and documentation. Everything that comes from
> the game (programs, graphics, sound) is rebuilt **from your own ISO** of the Anthology.


> **Picking the project up** (human or agent): read [AGENTS.md](AGENTS.md): rules, method, findings and open work, updated with every discovery.

## How this project is made

HSFA is developed with an AI coding assistant, Claude (Anthropic), directed, played and tested by Rickow; commits say so
(`Co-Authored-By: Claude`). Nothing is taken on trust: every change is checked against the arcade original by automated
benches (endings played to the credits, fights compared frame by frame, byte-for-byte witnesses with each new switch
off), larger steps are reviewed critically before they are merged, and the method and findings are written down in
[`docs/journal`](docs/journal) and [`re/`](re). No game data is in this repository: everything is rebuilt from your own
disc.

## Status (2026-11-13; stable release v0.1.10)

"Since v0.1.x" below = the release that brought it; the details of each release are in the
[CHANGELOG](CHANGELOG.md).

**Working**

| | Status | Details |
|---|---|---|
| SFA3 (`ro3`) | complete: attract mode; Arcade mode to the credits, **32/32 endings** match the arcade (v0.1.6: the Shadaloo dolls the PS2 port redrew in four endings are back, with the v0.1.6 cores); VERSUS, SURVIVAL, DRAMATIC, TRAINING; controls **42/42** identical to the arcade; arcade turbo rate (133.3%); sound validated | [journal §110-§113](docs/journal/HANDOFF.md), [non-regression](docs/methodes/oracle-et-non-regression.md) |
| Upper (`ro5`) | playable end to end, **40/40 endings**; hybrid sound ROM (SFA3 music + Upper voices); the music that exists only as streams on the disc is packed in the zip as Ogg Vorbis; since v0.1.10, two PS2-only sounds that were silent (Dee Jay's taunt, one of Birdie's sounds) are added from your ISO (also in Upper MAX) | [§122-§128](docs/journal/HANDOFF.md), [FLUX](docs/rapports/FLUX.md) |
| Hyper (`ro9`) | VERSUS without exceptions (151-match tour); supers of the ZERO / ZERO 2 / ALPHA versions no longer crash; super gauge and TRAINING fixed; ZERO / ZERO 2 / ALPHA music in the zip (Ogg Vorbis); per-version SFA1 / SFA2 voices replayed on a 2nd QSound when the replay table is present (see below). Since v0.1.9: 21 sounds of the PS2 port that were silent (parry in Mazi S-ISM, issue #1; ZERO 2 / ALPHA custom combo, Birdie, Sagat in Saikyo S-ISM, Cammy ALPHA, Dee Jay's taunt…) are added to the sound ROM from your ISO (also in Hyper + Arcade); the ground shadow of the ZERO / ZERO 2 characters is transparent with the ISO alone too | [§145-§173](docs/journal/HANDOFF.md), [§216, §218](docs/journal/HANDOFF.md), [FBNEO-HYPER](docs/rapports/FBNEO-HYPER.md), [REJEU-FBNEO](docs/rapports/REJEU-FBNEO.md), [SONS-PS2-HYPER](docs/rapports/SONS-PS2-HYPER.md) |
| Menus | OPTION and EXIT return to the mode menu; the PS2 option-screen settings (difficulty, damage, timer, speed, rounds) are core options | [§147-§148](docs/journal/HANDOFF.md), [OPTIONS](docs/rapports/OPTIONS.md) |
| Translator | **v161** for SFA3, Upper, Hyper, Hyper + Arcade and Upper MAX (since v0.1.9; v0.1.7 / v0.1.8: v160): silent losses found by the critical review of the translator, fixed and proven against the arcade: Mazi mode ×1.5 damage bonus never applied, combo score bonus never added, hit shake missing (SFA3), 2nd initial written on the 4th (SFA3, Upper), and nine other comparisons or byte accesses (custom combo freeze, scrolling text, 2nd player colour in mirror matches of Upper and Hyper…); the build now counts these losses and stops on an untranslated comparison or recompiler helper. **Hyper + Arcade** uses its own frozen copy of translator v161 (since state ro9a37) | [journal §219-§220](docs/journal/HANDOFF.md), [pitfalls](docs/methodes/pieges-du-traducteur.md) |
| FBNeo HSFA core | patches 0001-0027 and 0029-0032 (v0.1.9 and v0.1.10, same cores; v0.1.7: 0001-0026, v0.1.8: 0001-0027): complete and deterministic savestates (run-ahead, rewind, netplay), damaged states load safely; system folder of the standalone build under Windows; 16:9 "Widescreen edges" = Raw by default; Linux x86_64 core that needs glibc 2.27 only; Android, Linux, ROCKNIX, Windows, Recalbox 10 (Raspberry Pi, tested on a Pi 3B), Batocera 43 (tested on PC); "Blood" option (red, uncensored, by default); "Skip idle loops" option (on by default: 33-41 % less work per frame, same result); true 16:9 (v0.1.5: 512 x 224, exact aspect; stage-locked view at the arena ends with the HUD centred, the default up to v0.1.8, an option since 0031); 4:3 and 16:9 (with "Screen format (fill height)" for 4:3 to 16:10 screens); PSP-style transparent shadows; taunt on Select in fights; Upper's hidden characters (v0.1.2: hold Start + a button on Akuma / Balrog for Shin Akuma / EX Balrog, Coin for the roulette); tested by the user on RG477M and RGB10X | [patches](patches/fbneo/README.md), [Android](docs/guide/installation-android.md), [ROCKNIX](docs/guide/installation-rocknix.md) |
| Build from the ISO | `hsfa_build.py` (or the all-in-one builder) builds the three games from your ISO alone; translator v161 programs (v0.1.9, v0.1.10): SFA3 `a569c361`, Upper `ac053140`, Hyper `dbfd237d` with the replay table (`ffc5eac1` without); v160 (v0.1.7, v0.1.8): SFA3 `9b06c7cf`, Upper `3a9b7fd9`, Hyper `0baed6af` (`e3806660`); zips identical from one build, and one system, to the next; since v0.1.9: Upper MAX builds on Windows without the right to create symbolic links (issue #2) | [guide](docs/guide/construction-iso.md), [BUILD](docs/rapports/BUILD.md) |
| Output formats | since v0.1.9: `--cible` (builder: *Format de sortie / output* menu): `fbneo-hsfa` (default, unchanged zips); `fbneo-autonome` (standalone FinalBurn Neo HSFA for Windows, test build: same zips, byte for byte); `mister` and `cps2-banques` report only: per-game concessions and measured budgets, nothing is built | `scripts/construction/cibles.py`, [builder](tools/constructeur/README.md) |
| Standalone FinalBurn Neo HSFA (Windows x64) | **test build** (attached to v0.1.9 and v0.1.10), without RetroArch: official FBNeo `84faab7` + the repository's patch chain + 6 patches of the Windows interface (W01-W06); two programs (4:3, 16:9); HSFA options in the DIPs, 16:9 in the Video menu; tried under Wine: pictures, game states and sound identical to the RetroArch core (±1 on a few samples of the Ogg streams); not tried on a real Windows yet | [guide](patches/fbneo-autonome/INSTALL-EN.md), [patches](patches/fbneo-autonome/README.md) |
| Batocera 43 | since v0.1.9: installer `tools/batocera/installer-hsfa-batocera.sh` (an `hsfa` service puts the cores back at every boot: survives reboots and updates; `retirer` uninstalls) and an `hsfa` system; tried on the official 43.1 PC image in a virtual machine: the five games from the game list to the fight, in 4:3 and 16:9, with sound | [guide](tools/batocera/INSTALL-batocera-EN.md) |
| Upper MAX (`sfa3umhsfa`) | **experimental**: Eagle, Maki, Yun and Ingrid (SFA3 MAX, PSP) in Upper, built from your two discs (PS2 Anthology + PSP ISO of *SFA3 MAX*, USA ULUS-10062 or Europe ULES-00235): `hsfa_build.py --jeux uppermax --psp-iso <PSP ISO>`; without the PSP ISO, plain Upper is built. Since v0.1.9: translator v161 (no image address written in the integration any more; the `$1B6B6` call of the ending actors, Maki's and Yun's endings, now reaches the right routine); MAX characters' round behaviour aligned on the PSP. v0.1.10 (state max58): the US PSP disc is accepted as well as the European one (same zip, byte for byte); the 7 missing ending pieces are back; Yun's final credits and Maki's scene with Bison are no longer black; Guy drawn properly in Maki's ending; ending scene colours as on the PSP; linked effect positions and the Arcade route to the secret fight follow the PSP | [guide §5](docs/guide/construction-iso.md), [CONV-MAX](docs/rapports/CONV-MAX.md), [INTEGRATION-MAX-UPPER](docs/rapports/INTEGRATION-MAX-UPPER.md) |
| Hyper + Arcade (`sfa3hahsfa`) | **experimental** (since the v0.1.8 pre-release): Upper's Arcade mode grafted onto Hyper ("route B"); v0.1.10: state ro9a41 (version colours of the CPU and the player kept from the face-off to the end, version portraits coloured like Hyper, no green band at the logo transition before a dialogue screen; select after a VERSUS, new challenger, ending actors; 10 pairs of words of the graft's data no longer relocated as code pointers, not seen in the games played; preparation of the MAX characters, invisible); v0.1.9: state ro9a37 (CONTINUE, stages of Ryu, Sodom and Cammy, Ken's ending; translator v161: Mazi mode ×1.5 damage bonus, combo score bonus, 2nd player's colour in mirror matches); `hsfa_build.py --jeux hyperarcade`; with the arcade ROM and the replay table, the zip is ro9a41 byte for byte except `hsfa_info.txt` and the PS2-only sounds (`HSFA_SONS_PS2=0`: byte for byte) | [guide §6](docs/guide/construction-iso.md), [architecture](docs/architecture/voie-b-greffe.md) |

**Known limits of v0.1.x**

- **Hyper's per-version voices** need the QSound replay table of SFA1 / SFA2 (`--rejeu-table`, see the
  [build guide](docs/guide/construction-iso.md)). Without it,
  `hsfa_build.py` keeps Hyper's SFA3 voices for every version (translator v161: program `ffc5eac1` instead of
  `dbfd237d`) and the zip has no replay. Planned for v0.2: the build will regenerate the table from your own ISO.
- Upper MAX endings: in Eagle's ending, Charlie and Eagle have the wrong colours in the scenes with Charlie; in Yun's
  ending, one scene (« After many months of shooting ») shows a grid and bits of sprites where the PSP is black.
- Hyper + Arcade: the stage objects of 4 Upper stages do not behave exactly as in Upper (Hyper's fight engine: camera,
  random draws, frame counter); a character in a ZERO / ZERO 2 / ALPHA version keeps the colour-2 portrait whatever
  colour is picked, as in Hyper alone.
- 16:9 in *Raw* (the default from patch `0031`): the picture as drawn by the game, so at the ends of an arena the side
  bands can show black or stale columns; *Stage-locked view* (option) keeps the arcade art up to its edge.
- Standalone FinalBurn Neo for Windows: test build, tried under Wine only; RetroArch savestates do not load in it
  (and the other way round).
- Batocera: ARM 64-bit not tried on a real machine (file compatibility checked only); ARM 32-bit not supported.
- One Hyper music stream (Y27) stays in ADX inside the zip (its Ogg version fails our quality check; inaudible).
- The 16:9 PS2 patcher is validated on Upper and Hyper only; a few non-fight screens are offset.
- The ROCKNIX and Android cores were checked on PC (ARM emulation) and by the user on two handhelds, not on every
  device.

**In progress (not finished)**

- **Hyper + Arcade**: the graft goes on (Upper as the oracle); next, SFA1 / SFA2 stages extracted from the ISO with
  their animations,
  then the four MAX characters ([architecture](docs/architecture/voie-b-greffe.md)).
- **Upper MAX**: fixes by batches ([CHANGELOG](CHANGELOG.md)).
- **Data relayout**: phases 1-2 done and tagged but not enabled (small gain on the host; paused until the MAX
  characters go into the graft) ([architecture](docs/architecture/ARCHI-Reorganisation-Donnees.md)).
- **Redrawn widescreen stages** (exact PSD export, re-import, injection in the fork and the core): on hold; the 16:9
  core shows the picture drawn by the game (*Raw*) or, as an option, locks onto the arcade art instead
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
4. **Install the cores**: download them from the releases or build them from [`patches/fbneo/`](patches/fbneo/README.md),
   then follow the [Android](docs/guide/installation-android.md), [ROCKNIX / RGB10X](docs/guide/installation-rocknix.md),
   [Recalbox](docs/guide/installation-recalbox.md), [Batocera](docs/guide/installation-batocera.md) or
   [Windows](tools/windows/LISEZMOI-windows.md) guide.

Full walkthrough (MAME bench, diagnosis, non-regression): [docs/guide/demarrage.md](docs/guide/demarrage.md).

## Repository layout

```
README.md, README.fr.md, CHANGELOG.md, CREDITS.md, NOTICE.md, LICENSE
AGENTS.md, CLAUDE.md    picking the project up (rules, method, findings)
construire.sh/.bat      one-click build from the ISO
config.example.env      local paths (HSFA_WORKSPACE, HSFA_EXTRACT...); requirements.txt
docs/
  guide/                getting started, build from the ISO, Android / ROCKNIX / Recalbox / Batocera install, deliveries
  architecture/         translator, CPS2 memory, MAME bench, FBNeo core, data relayout, route B
  reference/            symbols, formats, module map, addresses
  methodes/             oracle and non-regression, translator pitfalls
  journal/              HANDOFF.md (journal §1-§221) and its index
  rapports/             detailed study reports
src/hsfa/               MIPS -> 68000 translator and build chain (mame/: bench Lua scripts)
scripts/                construction/ (from the ISO), validation/ (non-regression), qualite/, localiser.py
tools/                  tools by topic (benches, stages, Hyper sound, graft, cores, Batocera, streams...)
patches/                mame-fork/ (sfa3hx game), fbneo/ (HSFA core), traducteur/ (graft translator diff)
re/                     knowledge index: addresses, fields, memory allocations (tools in re/outils/)
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
