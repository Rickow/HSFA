# The FBNeo libretro core "HSFA"

**Français : [coeur-fbneo.fr.md](coeur-fbneo.fr.md)**

This document explains how the core runs the retranslated games, why each mechanism exists and where to find it in
the code. It applies to the `libretro/FBNeo` tree at commit `af5d3f3` plus the
[`patches/fbneo/`](../../patches/fbneo/README.md) chain (checked on 2026-10-18). One sheet per patch:
[coeur-fbneo-patchs.md](coeur-fbneo-patchs.md). Equivalent development bench: [banc-mame.md](banc-mame.md).
Technical terms are defined in the [glossary](#glossary), at the end of the document.

## 1. The principle

The PS2 Anthology contains no emulator: each game is a **static recompilation** of the original 68000 to the PS2's
MIPS. HSFA goes the other way and produces a **68000 program ROM** for the CPS2.

The retranslated program keeps PS2 habits that a real CPS2 cannot serve:

| habit of the PS2 port | on a real CPS2 |
|---|---|
| module data at fixed addresses, well beyond 4 MB | the program ROM is 4 MB |
| graphics files loaded by "slot", tile codes **local** to each file | **global** tile codes |
| Upper and Hyper tiles missing from the SFA3 graphics ROM | 32 MB of graphics ROM |
| music read from the disc (ADX streams) | music played by the Z80 on the QSound |
| SFA1 / SFA2 sounds for Hyper's ZERO / ZERO 2 versions | a single 16 MB QSound ROM, full |
| options screen in native C, not translatable | test menu and EEPROM, which the game no longer reads |

Two answers are possible: change the program (the translator), or **extend the machine**. The core picks the
second whenever the program would have had to be rewritten in depth. It is an FBNeo CPS2 with extensions, which this
document calls the **"HSFA virtual hardware"** (§5).

Three rules hold it all together:
- **Nothing changes for the other games.** Every hook tests `HsfaMode` (0 = ordinary game).
- **The core imitates the MAME bench** (`sfa3hx` fork + Lua scripts). The same zip must give the same game on both
  sides, randomness aside (§11).
- **No game data in the code.** Everything comes from the game archive, built on the user's machine by
  `tools/fbneo-hsfa/paquet_fbneo.py`, or from its PS2 files. A new translation needs a new zip, not a new core.

## 2. Where the code is

Everything is in the patched FBNeo tree. Paths relative to `src/burn/drv/capcom/` unless stated.

| file | role |
|---|---|
| `cps_hsfa.cpp` | the heart of HSFA: tables, object list, planes, options, roulette, streams, replay, music board, states, loading |
| `d_cps2.cpp` | the 4 drivers, their ROM lists, inputs and DIPs; `HsfaSfa3Init`, `HsfaUpperInit`, `HsfaHyperInit` |
| `hsfa_flux.h` | ADX and Ogg Vorbis music stream player (header only, shared with the MAME fork) |
| `hsfa_rejeu.h`, `hsfa_qsound.h` | replay of the SFA1 / SFA2 sounds; instantiable 2nd QSound (HLE of `qs_c.cpp`) |
| `hsfa_musique.h` | music board: original Z80 driver + dedicated QSound |
| `cps.cpp`, `cps_mem.cpp`, `cps_obj.cpp`, `cps_run.cpp`, `cps_rw.cpp`, `cps_scr.cpp`, `qs.cpp` | hooks (a few lines each) |
| `src/burner/libretro/libretro.cpp` | CRC-less ROMs looked up by name; archive path (`szBurnHsfaArchive`); core name |
| `src/burner/libretro/Makefile.hsfa`, `Makefile.hsfaws` | CPS1/CPS2 subset + `cps_hsfa.cpp` + stb_vorbis; 16:9 variant |
| `src/dep/libs/stb_vorbis/` | Ogg Vorbis decoder (stb_vorbis 1.22, public domain / MIT) |
| `hsfa/hsfa_run.c` | windowless test launcher (§10) |

`hsfa/paquet_fbneo.py`, in the FBNeo tree, is an old copy: the reference tool is
`tools/fbneo-hsfa/paquet_fbneo.py` in the repository.

## 3. Path of a frame

`Cps2Frame()` (`cps_run.cpp`) stays FBNeo's own. The extensions slot in as follows:

1. **The 68000 runs the translated program**, in slices, with the CPS2 IRQs.
   - It reads its data from the **external blocks** (`$940000-$EFFFFF` for Hyper) as from a ROM.
   - It writes its object list to `$700000-$70FFFF`. Each write goes through `HsfaObjWrite`, which keeps a raw copy
     of it (`Ombre`). When the **end marker** arrives (X = Y = `$8000`), `HsfaEclater` converts the whole list
     (§5.1) and writes it into both object banks.
   - For a sound, it fills the QSound mailbox (`$618001-$618019`) then writes `$61801F = 0`. The hook in
     `CPSQSoundC0WriteByte` (`cps_mem.cpp`) then decides who plays the command (§6) and may rewrite it for the Z80.
   - Upper and Hyper: a write to `$804200-$804205` changes the base of a plane (§5.2).
2. **At the same time, the main Z80** plays the sound ROM (SFA3, or hybrid ROM `hx3.*`), with an IRQ at 250 Hz
   like MAME.
3. **`CpsDraw()`** draws the planes from `nCpsGfxScroll` and the objects with their 20-bit codes.
4. **`HsfaFrameDone()`** (`cps_hsfa.cpp`), the equivalent of the bench's `frame_done`:
   - on the 1st frame, writes the plane bases from the configuration (`plans=` in `hsfa_tab.bin`);
   - follows the animation pointer of slot 4 and completes a deferred load (§5.1);
   - in the mode menu (`$FF8000 = 4`), writes the core option settings into RAM (§7);
   - increments the frame counter `nImage`.
5. **`QsndEndFrame()`** (`qs.cpp`) mixes, in order: main QSound, music stream, 2nd QSound (replay), then the
   music board (2nd Z80 + 3rd QSound).

Example: a Hyper fight against Ken in the ZERO version. The game sets music code `0042`
([FLUX](../rapports/FLUX.md) §0). If the zip contains the music board, it starts the SFA1 driver on its QSound;
otherwise stream `Y57` is played. In both cases, the main Z80 receives `FF05`: its music stops, the voices carry
on. The ZERO-version voices and sound effects (replay codes, `$2000` and up) go to the 2nd QSound, and the Z80
receives an empty code.

## 4. Drivers and archives

### 4.1 Drivers

| driver | game | `HsfaMode` | external blocks | graphics ROM | sound | DIP |
|---|---|---|---|---|---|---|
| `sfa3hsfa` | SFA3 (`ro3`) | 1: renumbered planes | `$A00000-$EFFFFF` | SFA3's 32 MB | SFA3 ROM | `HsfaDIPList` (PS2 music: "Missing tracks only") |
| `sfa3uhsfa` | Upper (`ro5`) | 2: plane bases | `$A00000-$EFFFFF` | 64 MB (`hsfa_gfx.bin` at `$2000000`) | hybrid `hx3.*` + streams | `HsfaDIPList` |
| `sfa3hhsfa` | Hyper (`ro9`) | 2, `HsfaHyper = 1` | `$940000-$EFFFFF` | 64 MB | hybrid + streams + replay + board | `HhsfaDIPList` ("All tracks") |
| `sfa3hahsfa` | `ro9a` test (Hyper + Upper's Arcade) | 2, `HsfaHyper = 1` | `$940000-$EFFFFF` (+ holes, §5.3) | 80 MB (48 MB `hsfa_gfx.bin`) | like Hyper | `HhsfaDIPList` |

The program remains a CPS2 "Phoenix" one (unencrypted). The same driver names are used by the 16:9 core: only the
core changes (§9).

### 4.2 Zip members

"Declared": member of the driver's ROM list, loaded by FBNeo. "In place": read by the core from the zip, at its
offset, without going through the ROM list; it must be **stored** (uncompressed).

| member | drivers | mode | content | read by |
|---|---|---|---|---|
| `sz3ud.03c`, `sz3ud.04c`, `sz3.05c` … `sz3.10b` | all | declared, CRC 0 | translated 68000 program, 8 × 512 KB, swapped words | FBNeo (looked up **by name**: `libretro.cpp`) |
| `sz3.13m` … `sz3.20m` | all | declared | SFA3 graphics ROM (arcade, or rebuilt from the ISO) | FBNeo |
| `phoenix.key` | all | declared | Phoenix key | FBNeo |
| `sz3.01`, `sz3.02`, `sz3.11m`, `sz3.12m` | `sfa3hsfa` | declared | SFA3 Z80 and QSound | FBNeo |
| `hx3.01`, `hx3.02`, `hx3.11m` … `hx3.14m` | Upper, Hyper, `ro9a` | declared, CRC 0 | Upper's hybrid sound: Z80 + 16 MB QSound | FBNeo |
| `hsfa_ext.bin` | all | declared | image of the external blocks up to `$EFFFFF`; its **size gives the base** | `HsfaExtTaille`, `HsfaLoadData` |
| `hsfa_tab.bin` | all | declared | bank and plane tables, map, configuration (§4.4) | `HsfaParseTab` |
| `hsfa_gfx.bin` | Upper, Hyper, `ro9a` | declared | extended graphics region, in MAME's internal format, converted on load | `HsfaConvertGfx` |
| `hsfa_trous.bin` | `sfa3hahsfa` | declared **optional** (`BRF_OPT`) | the 7 holes of the 68K map end to end, 5.08 MB (prototype) | `HsfaInit` |
| `hsfa_flux.bin` | Upper, Hyper | in place | reduced AFS: same indices as `Y_DATA.BIN`, ADX or Ogg streams, unused entries empty | `HsfaFluxInit` |
| `hsfa_flux_table.txt` | Upper, Hyper | in place | music code → stream table | `hsfa_flux::lecteur` |
| `hsfa_rejeu.bin` | Hyper | in place | 2nd QSound ROM, 8 MB (SFA1 at +0, SFA2 at +4 MB), CRCs checked | `HsfaRejeuCharge` |
| `hsfa_rejeu_table.txt` | Hyper | in place | QSound writes of each SFA1 / SFA2 sound | `hsfa_rejeu::rejeu` |
| `hsfa_musique.bin`, `hsfa_musique_table.txt` | Hyper (`HSFA_PARTITIONS=1`) | in place | SFA1 and SFA2 Z80 sound programs; Hyper code → driver table | `HsfaMusiqueInit` |
| `hsfa_info.txt` | all | ignored | build date and sources | — |

Search order for the sound data: **zip member**, then `<système RetroArch>/fbneo/hsfa/` (`Y_DATA.BIN`,
`X_DATA.BIN`, `anthology.iso`, or `ydata.txt` / `xdata.txt` holding a path); otherwise the feature stays inactive
and the game runs anyway. A 7z archive gives no "in place" member.

### 4.3 How the core finds the archive

- The zero-CRC ROMs of a driver whose name contains `hsfa` are looked up **by name** (`open_archive`,
  `libretro.cpp`): the program changes with every translation.
- The frontend records the archive path in `szBurnHsfaArchive` (`burn.cpp`). `HsfaResoutArchive` tries the name
  without extension, `.zip` then `.ZIP`, and checks the zip signature.
- `HsfaZipMembre` reads the central directory and returns the data offset. Zip64 is not supported (Hyper's zip
  with ADX is about 710 MB).

### 4.4 `hsfa_tab.bin`

Header `HSFATAB1`, number of entries, then `{ nom[24], décalage, longueur }` per entry (little-endian).

| entry | content |
|---|---|
| `f<N>` | PS2 graphics file no. N: for each local code, the global code (u32, `$FFFFFFFF` = empty) |
| `plan1`, `plan2`, `f312` | SFA3 plane renumbering tables (scroll1, scroll2, scroll3); `plan2` also serves as slot 1 |
| `carte` | text: `perso <id> <fichier>` and `anim <pointeur> <fichier>` |
| `config` | `clé=valeur` text: `commun` (common bank: SFA3 254, Upper 351, Hyper 545), `ptr_anim` (`FF3E48` SFA3, `FF40BC` Upper / Hyper), `gfx_intro` (456), `plans` (Upper / Hyper `300,340,3a0`), `lat4`, `lat4_max` |

## 5. The HSFA virtual hardware

Each row is something a real CPS2 does not have, or does differently. "Program" = the translated 68000 program;
"core" = HSFA's C++ code.

| extension | address or interface | who writes it | why (PS2 → CPS2) | code | patch |
|---|---|---|---|---|---|
| CRC-less program | ROM `$000000-$3FFFFF` | — | it changes with every translation | `libretro.cpp` (`find_rom_by_name`) | 1 |
| external blocks | ROM `$A00000-$EFFFFF` (Hyper `$940000-`); base = `$F00000` − size of `hsfa_ext.bin` | read by the program | the PS2 module data sit at fixed addresses and do not fit in 4 MB | `HsfaExtTaille`, `SekMapMemory` in `HsfaInit` | 1, 4 |
| holes of the 68K map | 7 ranges, including `$410000-$617FFF` and `$FB0000-$FEFFFF` (§5.3) | read by the program | external blocks saturated in `ro9a`; +5.08 MB of data at no extra cycle | `HsfaTrous`, `HsfaInit` | 13 (prototype) |
| converted object list | writes to `$700000-$70FFFF`; end marker X = Y = `$8000` | program (raw list) → core (converted list) | tile codes **local** to a bank slot (bits 13-15 of Y) | `HsfaObjWrite`, `HsfaEclater`, `HsfaEmplacements` | 1 |
| 20-bit object codes | bits 16-17 → bits 13-14 of Y (like the CPS2); bits 18-19 → **bits 10-11 of X** (HSFA addition) | core | Upper / Hyper tiles beyond `$40000` | `HsfaEclater`; `Cps2ObjDraw` (`cps_obj.cpp`) | 1 |
| extended graphics ROM | region ≥ 64 MB, `hsfa_gfx.bin` at `$2000000`; `ro9a`: 80 MB | core, on load | Upper / Hyper characters and stages are not in SFA3's 32 MB | `HsfaGfxLenMin`, `HsfaConvertGfx`; `nCpsGfxLenMin` (`cps.cpp`) | 1, 12 |
| plane base registers | words `$804200`, `$804202`, `$804204` (scroll1-3), 64 KB units; 0 = original mapping | core on the 1st frame (`plans=`); program in `ro9a` | PS2 stages stored in `hsfa_plans.bin`: one base per plane | `HsfaPlaneWrite`, `HsfaPortWriteWord`, `HsfaUpdateScroll` | 1, 12 |
| plane renumbering (SFA3) | writes to video `$900000-$92FFFF` and to `$804102-$804107` (CPS-A) | program → core | SFA3 PS2's plane tile codes are not the arcade ones | `HsfaVramWrite`, `HsfaBaseWrite`, `HsfaReconvertit` | 1 |
| 14-bit scroll3 | `Cps2Scr3Draw` | core | like MAME | `cps_scr.cpp` | 1 |
| deferred slot 4 (LAT4) | animation pointer `$FF3E48` / `$FF40BC`; `lat4=`, `HSFA_LAT4` | core | on PS2 the file read is queued: the old portrait stays for a few frames | `HsfaSuivre4`, end of `HsfaFrameDone` | 6 |
| intercepted QSound mailbox | write `$61801F = 0` (command at `$618001/3`, volume `$618005`, parameter `$618007/9`) | program → core | route each command to the board, the stream, the replay or the Z80 | `CPSQSoundC0WriteByte` (`cps_mem.cpp`), `HsfaFluxCommande`, `HsfaRejeuCommande` | 3, 5, 10 |
| Z80 IRQ at 250 Hz | `QsndReset` | core | FBNeo uses 252 Hz; MAME 8 MHz / 32,000 = 250 Hz: music in sync as on the bench | `qs.cpp` | 1 |
| ADX / Ogg music stream | `hsfa_flux.bin` or `Y_DATA.BIN`; DIP A | core | on PS2, many pieces of music are **only** streams on the disc | `hsfa_flux.h`, `HsfaFluxInit`, `HsfaFluxRendu` | 3, 8, 9 |
| 2nd QSound (replay) | codes `$2000+`, `$3000+`, `$4000+`; ROM `hsfa_rejeu.bin` 8 MB | core | Hyper's SFA1 / SFA2 voices and sound effects: the 16 MB QSound ROM is full | `hsfa_rejeu.h`, `hsfa_qsound.h`, `HsfaRejeuRendu` | 5 |
| 2nd Z80 + 3rd QSound (music board) | Zet no. 1; replay ROM; `hsfa_musique.bin` | core | play the ZERO / ZERO 2 music with their original Z80 drivers instead of recordings | `hsfa_musique.h`, `HsfaMusZet`, `HsfaMusiqueRendu` | 10 |
| core options → RAM | DIP B-H; bytes `$FF80A0-$FF80A5`, `$FF80DE-$FF80DF`, VS MODE, EXTRA OPTION | core, in the mode menu | the PS2 OPTION screen is native C, not translated: its copy of the settings was lost | `HsfaOptions` | 7 |
| roulette on Select | `$FF84D3` / `$FF88D3`, write tap `$FF8400-$FF8BFF` | core (replaces the program's value) | on PS2 the roulette comes from Select; the translation copied it from Start | `HsfaRoulette`, `HsfaRouletteWrite*` | 11 |
| members read in place | `szBurnHsfaArchive`, `HsfaZipMembre` | core | one complete zip per game, without loading 700 MB into memory | `cps_hsfa.cpp`, `libretro.cpp`, `burn.cpp` | 5 |
| 16:9 picture | 448 × 224, `-DHSFA_WS` | — | the stage exists beyond 384 px | `d_cps2.cpp` (`HSFA_SCRW`), `Makefile.hsfaws` | 2 |
| object blending | `$804220-$80423F` (mode per OBJ palette), `$804240` (mode of the objects whose raw X word has bit 12); modes 0-5 | program (EFFET_W of the MAX characters, RAM table `$FF7F00`) | the PSP draws effects additively, decided per object; the CPS2 has no transparency | `Cps2ObjDraw` (`cps_obj.cpp`), `nCpsBlend` | 14 |
| transparent shadows | DIP A option bit 7 (default), `HSFA_OMBRES` | core | shadows at 75 % as on PSP; rule by tile code because palette 0x14 is also used by the stage | `Cps2ObjDraw` | 15 |
| screen format of the 16:9 core | option `fbneo-hsfa-format` ("Screen format (fill height)"): **video output option, not a register** | core (player setting) | fill the height of a screen narrower than 16:9 by cropping the sides of the widened stage | `libretro.cpp`, `retro_common.cpp` | 16 |

The patch numbers are those of the table in [`patches/fbneo/README.md`](../../patches/fbneo/README.md).

### 5.1 The object list and the slots

On PS2, an object carries a code **local** to the graphics file loaded into a **slot**. The slot is given by bits
13-15 of Y. `HsfaEmplacements` picks the table of each slot at each conversion:

| slot | table | from |
|---|---|---|
| 0 | common bank | `commun=` |
| 1 | stage | `plan2` entry |
| 2, 3 | P1, P2 characters | character id `$FF8503`, `$FF8903` → `perso` line of the map |
| 4 | graphics file of the scene | animation pointer (`ptr_anim=`) → `anim` line; null → `gfx_intro=` |
| 6, 7 | players 3, 4 | only if `$FF8C01` / `$FF9001` ≠ 0 |

`HsfaEclater` cuts each object into 16 × 16 tiles, translates each code, and stores at most 1,023 tiles. An entry
written more than 3 frames earlier is ignored (left over from a previous screen). The converted list is written
**into both object banks** (journal §103).

**Deferred load (LAT4)**: when the file of slot 4 changes, the new file waits until no list of the frame has any
object of slot 4 any more, 10 frames at most (`lat4_max=`). Without this, the large portrait of Upper's face-off
showed 5 frames of tiles from the VS screen ([PORTRAITS](../rapports/PORTRAITS.md)).

### 5.2 The planes: two modes

- **SFA3 (mode 1)**: the program writes PS2 tile codes into video memory. The core keeps the raw value
  (`Raw90`) and writes the arcade code, read from `plan1` / `plan2` / `f312`. If the game changes the base of a plane
  (`$804102-$804107`), the whole plane is reconverted. This is `banc_plans.lua` ported to C++.
- **Upper, Hyper (mode 2)**: the PS2 stages are separate tiles (`hsfa_plans.bin`, inside `hsfa_gfx.bin`). Each
  plane gets a base (`$804200-$804205`); the tilemap code becomes an index local to that base. The core
  writes `300,340,3a0` on the 1st frame. In `ro9a`, the program itself switches to `400,440,4a0` for Upper's
  screens. FBNeo redraws the planes every frame: it is enough to update `nCpsGfxScroll` when the value
  changes (the equivalent of the fork's `mark_all_dirty`). `HSFA_PLANS_LOG=<fichier>` logs each change.

### 5.3 The 68K map as seen by the translated program

| range | content |
|---|---|
| `$000000-$3FFFFF` | program ROM (full; the only area where code runs) |
| `$400000-$40000F` | CPS2 object registers |
| `$410000-$617FFF` | hole T1 (2,080 KB) |
| `$618000-$619FFF` | QSound shared RAM (mailbox) |
| `$61A000-$65FFFF` | hole T2 (280 KB) |
| `$660000-$667FFF` | extra RAM (stacks of the port) |
| `$668000-$6FFFFF` | hole T3 (608 KB) |
| `$700000-$70FFFF` | object memory (converted write) |
| `$710000-$7FFFFF` | hole T4 (960 KB) |
| `$800000-$80FFFF` | ports, CPS-A / CPS-B registers, HSFA registers `$804200`; `$808000-$80FFFF` kept for the future |
| `$810000-$8FFFFF` | hole T5 (960 KB) |
| `$900000-$92FFFF` | video memory |
| `$930000-$93FFFF` | hole T6 (64 KB) |
| `$940000-$EFFFFF` | external blocks (`$A00000-` for SFA3 and Upper) |
| `$F00000-$FAFFFF` | variables of the port (PORT_RAM): **not mapped**; the port copes with reads of 0 (measured on `ro9a`) |
| `$FB0000-$FEFFFF` | hole T7 (256 KB) |
| `$FF0000-$FFFFFF` | work RAM; A5 = `$FF8000` |

The holes are served only if the zip contains `hsfa_trous.bin` (only `sfa3hahsfa` declares it). A 68K pointer to
a hole or an external block must carry the `$01xxxxxx` tag, which the 24-bit bus ignores
([COEUR-BANQUES](../rapports/COEUR-BANQUES.md) §B.1).

## 6. Sound

A command set by the program (`$61801F = 0`) follows this routing:

1. **music board** (Hyper, if the zip contains its members): known ZERO or ZERO 2 code → the original driver
   plays it, the main Z80 receives `FF05`;
2. **stream** (depending on DIP A): music from the table → ADX or Ogg stream, the Z80 receives `FF05`; `FFxx` (stop,
   fades) applies to the stream and passes to the Z80;
3. **replay** (Hyper): SFA1 / SFA2 sound → 2nd QSound, the Z80 receives an empty code or an `ALIAS`;
4. **main Z80**: everything else, unchanged.

Why `FF05`: a code unknown to the Z80 would let its music carry on, and `FF00` would also cut the voices
([FLUX](../rapports/FLUX.md) §1.2).

| source | rate | gain | saved state |
|---|---|---|---|
| main QSound (FBNeo) | FBNeo's | `Cps2Volume / 39` | yes (FBNeo) |
| stream | file frequency, resampled to the output | 0.26 × `HSFA_FLUX_VOL` % | `HsfaFlux` block (if the player is active) |
| 2nd QSound (replay) | 24,038 Hz, 60 MHz clock timed by the 68K cycles | `Cps2Volume / 39` | `HsfaRejeu`, `HsfaQs2` blocks (always present for Hyper) |
| music board | Z80 8 MHz, IRQ 250 Hz; QSound 24,038 Hz | `Cps2Volume / 39` × table gain | `HsfaMusique` block + "Z80 #2" |

Ogg streams are decoded by stb_vorbis in memory; a 2.7 s ring buffer avoids any `seek` during run-ahead. The loop comes
from the `LOOPSTART` / `LOOPEND` comments ([PLAN-VORBIS](../rapports/PLAN-VORBIS.md)).

## 7. Options

**Core options** (RetroArch: Core options → DIP switches):

| DIP | setting | values |
|---|---|---|
| A | `PS2 music (ADX streams, Y_DATA.BIN)` | `Off` / `Missing tracks only` (default SFA3, Upper) / `All tracks` (default Hyper) |
| A, bit 7 | `Transparent shadows (PSP)` (patch 15) | on by default; shadows in black at 75 % |
| B-E | `Option: Difficulty`, `Damage level`, `Timer speed` (including `Infinity`), `Speed select`, `Max round`, `VS mode (1P/2P)`, `Join in` (SFA3, Upper) | `Game default` = nothing is written |
| F-H | 17 `Extra option: …` (one EXTRA OPTION page per DIP, one bit per setting) | 1st value = bit at 0 |

The settings are written at the end of every frame spent in the mode menu: they take effect the next time through
that menu. RetroArch key, for example: `fbneo-dipswitch-sfa3hhsfa-Option__Timer_speed`. Byte details:
[OPTIONS](../rapports/OPTIONS.md) §1.2.

**16:9 core only**: option `fbneo-hsfa-format`, "Screen format (fill height)" (Off by default, 4:3, 3:2,
14:9, 16:10, 5:3, 16:9). It crops the sides at the video output to fill the height of the screen (patch 16).

**Environment variables** (PC, tests only; never read on console):

| variable | effect |
|---|---|
| `HSFA_LAT4=0`, `HSFA_LAT4_MAX=<n>` | old immediate change of slot 4; maximum delay |
| `HSFA_OPTIONS=0` | no option writes |
| `HSFA_NOROUL=1` | `$FF84D3` / `$FF88D3` always at 0 (= the bench's `NOROUL`) |
| `HSFA_PLANS_LOG=<f>`, `HSFA_STATS=1` | log of the plane bases; object list statistics |
| `HSFA_FLUX=<0-2>`, `HSFA_YDATA`, `HSFA_FLUX_TABLE`, `HSFA_FLUX_VOL`, `HSFA_FLUX_LOG` | forced mode, sources, volume, stream log |
| `HSFA_REJEU=0`, `HSFA_XDATA`, `HSFA_REJEU_TABLE`, `HSFA_REJEU_LOG`, `HSFA_REJEU_SEUL=1` | replay off, sources, log, output of the 2nd QSound alone |
| `HSFA_MUSIQUE=0`, `HSFA_MUSIQUE_DATA`, `HSFA_MUSIQUE_TABLE` | music board off, sources |
| `HSFA_OMBRES=0/1` | transparent shadows forced (takes priority over the DIP); `0` to compare with an earlier reference |
| `HSFA_OBJMIX=oo:m[,…]`, `HSFA_MIX_LOG=<f>` | blending registers forced at reset; log of their changes |

## 8. Savestates

`HsfaScan` adds HSFA's state to FBNeo's: copies of the object list (`HsfaOmbre`, `HsfaAge`, `HsfaConv`,
`HsfaConvOk`), raw video memory (SFA3), frame counter, slot 4, plane bases, stream, replay and music
board. For Hyper, the replay and board blocks are **always present** (empty if inactive): a state
reloads with or without the sound data. The patches that add state variables (LAT4, replay, music board)
probably make the states of older cores unreadable.

## 9. Platforms

| target | build | note |
|---|---|---|
| Linux x86_64 | `make -j4 SUBSET=hsfa REGEN_HEADERS=1` in `src/burner/libretro` | `SUBSET=hsfaws`: "FinalBurn Neo HSFA Widescreen" core |
| Android arm64-v8a | `NDK=<ndk r28c> FBNEO=<arbre> tools/android/build_android.sh` | `ndk-build` does not regenerate the headers: run `make SUBSET=hsfa generate-files` first |
| ROCKNIX (RK3326) | `FBNEO=<arbre> tools/rocknix/build.sh hsfa\|hsfaws` | glibc ≤ 2.38, `rocknix_compat.h` |
| Windows x64 | `tools/windows/build_win.sh <arbre> [hsfa\|hsfaws\|tous]` | MinGW-w64, `LIBS=-static` |

Full chain and checked commands: [`patches/fbneo/README.md`](../../patches/fbneo/README.md#build). The
16:9 keeps the same drivers and the same zips; FBNeo recentres planes and objects (`nCpsGlobalXOffset = 32`).

## 10. Validation and test tools

**`hsfa/hsfa_run.c`**: windowless libretro launcher. It replays the same inputs as the bench's `jeu.lua`, and writes
a log, captures and WAV.

```bash
gcc -O2 -I<fbneo>/src/burner/libretro/libretro-common/include -o hsfa_run <fbneo>/hsfa/hsfa_run.c -ldl -lm
NF=9000 SNAPS=300,600 OUTDIR=snap OUT=journal.txt WAV=son.wav SYSDIR=sys \
  INPUTS="100-106::IN0:Coin 1;200-206::IN0:1 Player Start" ./hsfa_run fbneo_hsfa_libretro.so sfa3hsfa.zip
```

Other variables: `PILOTE=hyper` (Hyper VERSUS tour: `LISTE`, `MODEJEU`, `CONTOURNE_E`…), `PILOTE=arcade`
(Arcade game of `ro9a`), `STATETEST=<image>` (save, restore, picture and sound comparison), `CPUSPEED`,
`HSFA_VARS="clé=valeur;…"` / `HSFA_VARS2` + `HSFA_VARS2_IMAGE` (core options, changed during the game).

**`scripts/validation/nonreg_coeur.sh`** (§162): the same scripted games (SFA3, Upper, Hyper) played by a reference
core and by the core under test, on the same zips. Captures, game log, replay and stream logs, WAV
compared; expected: `IDENTIQUE` for each game, in 20 to 30 s on PC.

```bash
HSFA_WORKSPACE=<workspace> COEUR=<nouveau.so> REF=<reference.so> ZIPS=<dossier des 3 zips> \
  scripts/validation/nonreg_coeur.sh
```

It still depends on `fb.sh` and `hsfa_run` from a work folder (`work/agent_fbneo_rejeu/tests/`), outside the repository.

**What has been validated** (details in the reports): SFA3, attract log identical to MAME frame by frame over
8,000 frames (§136);
Upper identical to the pixel after frame 1656; Hyper: same course of play as the fork over a VERSUS tour of
13,000 frames ([FBNEO-HYPER](../rapports/FBNEO-HYPER.md)) and 151 VERSUS out of 151 (§154); replay: same decisions as
the fork, to the ms ([REJEU-FBNEO](../rapports/REJEU-FBNEO.md)); `ro9a`: complete Arcade game, bank switches
at the same frames as the bench ([COEUR-BANQUES](../rapports/COEUR-BANQUES.md)). On 2026-10-18, a core rebuilt
from `af5d3f3` and the published patches gives `IDENTIQUE` against the core of the reference tree on all three games.

## 11. Known differences

- **Randomness**: the program's random draw depends on the number of 68000 cycles per frame and on the Z80 phase.
  Opponents, demos, announcer lines and roulette may differ from MAME, with offsets of 1-2 frames
  ([HASARD](../rapports/HASARD.md)). With equal inputs, `HSFA_NOROUL=1` is needed to compare Hyper with the bench.
- **Main QSound**: FBNeo's. After restoring a state, its output differs slightly (resampling phase not saved by
  `QscScan`, already true without HSFA; [REJEU-FBNEO](../rapports/REJEU-FBNEO.md)
  §3.7). This emulation is superctr's (high level, derived from the DSP code); MAME has emulated the DSP itself
  since 0.196: compare sound bit for bit within the same implementation, by tolerance between the fork and the core
  ([research C §1.2](../rapports/recherche/C-TECHNIQUE-METHODE.md)).
- **Streams**: a command takes effect at the start of the frame's sound buffer (≤ 17 ms early); fades at 60 Hz in sound
  time; the CPS2 digital volume (`$804030`) does not apply to the stream ([FLUX](../rapports/FLUX.md) §5).
- **Music board**: it switches on as soon as the zip contains its members, whatever DIP A says; the core option
  "ZERO / ZERO 2 music" planned by the plan does not exist yet. The DIP A label says "ADX" but also applies
  to Ogg.
- **Slots 2 and 3**: they change table immediately (no fault seen, [PORTRAITS](../rapports/PORTRAITS.md)
  §5).
- **16:9**: 32 px band at the camera limits of some stages, objects cut at the 4:3 boundary, non-fight screens
  incomplete (§139). The injected widescreen stages are a separate patch, outside the chain.
- **`Cps2Turbo`** (FBNeo overclocking) is not carried over: different format from the fork (§136).
- **Generated headers**: `REGEN_HEADERS=1` literally writes `" HSFA_SUFFIXE "` in the comments of
  `gamelist.txt` and `driverlist.h` (cosmetic; [FBNEO-HYPER](../rapports/FBNEO-HYPER.md) §5).
- **Prototypes**: `sfa3hahsfa` and `hsfa_trous.bin` serve the `ro9a` tests; the switched data bank
  (`$804210`) is only estimated ([COEUR-BANQUES](../rapports/COEUR-BANQUES.md) §B.2).

## Glossary

| term | meaning |
|---|---|
| **CPS2** | Capcom arcade board: 68000 at 11.8 MHz, Z80 for sound, QSound chip, graphics ROM (32 MB for SFA3) |
| **CPS-A / CPS-B** | the two video chips of the CPS; their registers are at `$804100` / `$804140` (plane bases, scrolling, priorities) |
| **Phoenix** | version of a CPS2 ROM with a decrypted program (`sfa3ud`); HSFA starts from it |
| **QSound** | CPS2 sound chip (samples, 16 voices + 3 ADPCM, echo); emulated here in HLE (without the DSP ROM) |
| **Z80** | sound processor: it runs the "sound driver" that turns a command into QSound writes |
| **mailbox** | shared RAM `$618000`: the 68000 puts a sound code there, the Z80 reads it |
| **scroll1-3, plane** | the three tiled stage layers (8 × 8, 16 × 16, 32 × 32), described by tilemaps at `$900000` |
| **object** | sprite: moving element (characters, effects, text) described in the object list `$700000` |
| **tile** | square of pixels of the graphics ROM; its **global code** is its rank in the ROM |
| **bank** | here: a PS2 graphics file (`f<N>`) and its local code → global code table |
| **slot** | loading slot of a bank on PS2 (0 common, 1 stage, 2-3 characters…), given by bits 13-15 of Y |
| **A5** | base register of the game variables: `$FF8000`; "`$A0(A5)`" = byte `$FF80A0` |
| **external block** | PS2 module data served as ROM beyond 4 MB (`ext_<adresse>.bin` → `hsfa_ext.bin`) |
| **PORT_RAM** | variables specific to the port, at `$F00000`; not mapped in the core |
| **stream** | recorded music (CRI's ADX on PS2, Ogg Vorbis for the lighter zips), read in blocks |
| **replay** | SFA1 / SFA2 sounds replayed from the QSound writes their drivers made |
| **music board** | 2nd Z80 + 3rd QSound that run the original SFA1 / SFA2 sound drivers |
| **`X_DATA.BIN`, `Y_DATA.BIN`** | PS2 Anthology archives: data (including SFA1 / SFA2 sound), music (AFS of ADX streams) |
| **AFS** | CRI archive format: an index of entries, here taken over as is by `hsfa_flux.bin` |
| **DIP** | setting switch of an arcade game; RetroArch shows them in the core options |
| **savestate, run-ahead** | complete snapshot of the machine; run-ahead reloads one every frame to reduce latency |
| **swapped words** | bytes of each 16-bit word swapped, the storage format of 68000 ROMs in the zips |
| **bench** | the MAME fork `sfa3hx` and its Lua scripts, development tool and oracle of the core |
| **`ro3`, `ro5`, `ro9`, `ro9a`** | retranslated PS2 modules: SFA3, Upper, Hyper, Hyper + grafted Upper Arcade |
