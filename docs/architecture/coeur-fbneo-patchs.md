# FBNeo core "HSFA": one sheet per patch

**Français : [coeur-fbneo-patchs.fr.md](coeur-fbneo-patchs.fr.md)**

Complements [coeur-fbneo.md](coeur-fbneo.md) (how it works) and [`patches/fbneo/README.md`](../../patches/fbneo/README.md)
(order of application, build). Each sheet gives: the problem, the solution, the rejected alternatives (with
their source), the files touched, and how to turn off or check the patch. "§" refers to the journal
`docs/journal/HANDOFF.md`. When a source cites no alternative, the sheet says so.

The numbers are those of the README table ("#" column). The sheets stop at row 16 (`0012`): for
rows 17 to 29 (`0013`-`0025`, `0021b`, `0021c`), the README table serves as the sheet (content, reason, source). Older reports say "patch 8" for row 8
(`0004-…`), "patch 10" for `0006-…`, etc.

Check common to all: `scripts/validation/nonreg_coeur.sh` against a reference core (`IDENTIQUE` expected
on SFA3, Upper and Hyper, unless the change is intended; since patch 15, with `HSFA_OMBRES=0`).

## 1. `fbneo-hsfa.patch` — SFA3 and Upper drivers

- **Problem**: play the retranslated programs on console, without MAME or Lua scripts.
- **Solution**: `cps_hsfa.cpp` takes over in C++ the three Lua layers of the bench (`banc_mem`, `banc_plans`,
  `banc_sprites`) and the extensions of the `sfa3hx` fork (extended graphics ROM, 20-bit object codes, plane
  bases, hybrid sound). Hooks in `cps*.cpp`, all behind `HsfaMode`. CRC-less ROMs looked up by name. Z80 IRQ
  at 250 Hz like MAME. Savestates. `hsfa_run` launcher. `Makefile.hsfa` subset.
- **Alternatives**: keep MAME as the final product, rejected in §109 (the fork stays the development tool, FBNeo the
  core for Android / RetroArch). FBNeo's `Cps2Turbo` looked at, not carried over: different format from the fork (§136).
- **Files**: `cps_hsfa.cpp` (new), `d_cps2.cpp`, `cps.cpp`, `cps.h`, `cps_mem.cpp`, `cps_obj.cpp`,
  `cps_run.cpp`, `cps_rw.cpp`, `cps_scr.cpp`, `qs.cpp`, `libretro.cpp`, `Makefile.hsfa`, `jni/Android.mk`,
  `hsfa/hsfa_run.c`, `hsfa/paquet_fbneo.py` (old copy).
- **Turn off / check**: only the `*hsfa` drivers set `HsfaMode`; the other CPS games keep the original code.
  `HSFA_STATS=1` prints the object list statistics. Original validation: §136.

## 2. `fbneo-hsfa-widescreen.patch` — 16:9 core

- **Problem**: wide screens; the games' stage art exists beyond the CPS2's 384 px.
- **Solution**: `-DHSFA_WS` switches the HSFA drivers to 448 × 224 and 16:9; FBNeo recentres planes and objects. A
  separate core "FinalBurn Neo HSFA Widescreen", **same driver names**, hence the same zips (§139).
- **Alternatives**: none is documented.
- **Files**: `d_cps2.cpp`, `Makefile.hsfaws`, `libretro.cpp`.
- **Check**: centre of the picture identical to the pixel to 4:3 (520 captures, §139). Known defects: coeur-fbneo.md §11.

## 3. `fbneo-hsfa-ws-flux.patch` — ADX music streams

- **Problem**: some music exists only as streams on the PS2 disc: Upper's characters (`0030-0036`), Hyper's ZERO,
  ZERO 2 and ALPHA music. The Z80 does not know them.
- **Solution**: `hsfa_flux.h` (shared with the fork) reads the user's `Y_DATA.BIN`. Interception at
  `$61801F = 0`; a piece of music played as a stream becomes `FF05` for the Z80; `FFxx` applied to the stream. DIP
  "PS2 music": `Off`, `Missing tracks only`, `All tracks`.
- **Alternatives**: let the code through to the Z80 (it keeps its music: test `z_a`); send `FF00` (also cuts
  the voices: test `z_i`). The intro `0001` is never streamed: its `$618021` cues come from the Z80
  ([FLUX](../rapports/FLUX.md) §1.2).
- **Files**: `hsfa_flux.h` (new), `cps_hsfa.cpp`, `cps_mem.cpp`, `qs.cpp`, `cps.h`, `d_cps2.cpp`.
- **Turn off / check**: DIP `Off`, or `HSFA_FLUX=0` on PC; log `HSFA_FLUX_LOG=<fichier>`. In mode 1 with no
  music outside the QSound, WAV identical to the previous core ([FLUX](../rapports/FLUX.md) §3).

## 4. `hyper-HSFA-pilote-sfa3hhsfa-Hyper-Street-Fighter-Alpha-mod.patch` — Hyper driver

- **Problem**: Hyper (`ro9`) has external blocks at `$940000` and `$C84000`, a common bank 545, and almost
  all its music as streams.
- **Solution**: driver `sfa3hhsfa`, Upper's mechanisms (`HsfaMode = 2`) plus `HsfaHyper = 1`. The base of the external
  blocks is deduced from the size of `hsfa_ext.bin` (`$F00000` − size). Music DIP on `All tracks`. Test
  hook `HSFA_NOROUL`. `hsfa_run`: `PILOTE=hyper`.
- **Alternatives**: a first driver had its own mode (`HsfaMode = 3`); the delivered version reuses Upper's
  mode ([FBNEO-HYPER](../rapports/FBNEO-HYPER.md) §1-§2).
- **Files**: `d_cps2.cpp`, `cps_hsfa.cpp`, `cps.h`, `hsfa/hsfa_run.c`, and the generated files `gamelist.txt`,
  `driverlist.h` (to be excluded when applying: the only patch of the chain that contains them).
- **Check**: VERSUS tour of 13,000 frames against the fork: same 14 choices, 17/26 captures identical to the pixel
  ([FBNEO-HYPER](../rapports/FBNEO-HYPER.md) §4).

## 5. `0001-HSFA-rejeu-QSound-…` — SFA1 / SFA2 sounds, data in the zip

- **Problem**: Hyper's ZERO and ZERO 2 versions must have their original voices and sound effects. The 16 MB QSound
  ROM is full, the Z80 driver has no free command number left.
- **Solution**: a 2nd QSound (`hsfa_qsound.h`) replays each sound as the original driver wrote it
  (`hsfa_rejeu.h`, 1,323 sounds). The Z80 receives an empty code. All the data (streams, replay) are **stored**
  members of the zip, read in place.
- **Alternatives**: (a) QSound ROM extended to 32 MB, rejected: the Z80 driver would need surgery (no free numbers,
  no free entries, no bank bit); "home-made" sample player, rejected: volume, panning, echo and
  sequences to rewrite ([SON-HYPER-ROM](../rapports/SON-HYPER-ROM.md) §12.1). Data outside the zip: replaced by
  "everything in the zip", the user's decision ([REJEU-FBNEO](../rapports/REJEU-FBNEO.md) §0).
- **Files**: `hsfa_qsound.h`, `hsfa_rejeu.h` (new), `cps_hsfa.cpp`, `hsfa_flux.h`, `cps_mem.cpp`, `qs.cpp`,
  `cps.h`, `burn.cpp`, `burn.h`, `libretro.cpp`, `hsfa/hsfa_run.c`.
- **Turn off / check**: `HSFA_REJEU=0`; `HSFA_REJEU_LOG=<fichier>`; `HSFA_REJEU_SEUL=1`. Hyper without any member:
  identical to the byte to the previous core. Measured cost: 0.16 ms per frame on PC, +14 MB of memory.

## 6. `0002-HSFA-chargement-differe-emplacement-4.patch` — face-off portrait

- **Problem**: in Upper, 5 frames of VS-screen tiles instead of the large portrait, when the dialogue before
  the 1st fight closes.
- **Solution**: the new file of slot 4 waits until no object of that slot is displayed any more
  (10 frames at most), like the PS2's queued read.
- **Alternatives**: delay the write of the `$C0BC` pointer in the translator, rejected: the game reads that pointer straight
  away (animation of the pair, ending actors). Leads "translation fault", "write order" and
  "double buffer" refuted ([PORTRAITS](../rapports/PORTRAITS.md) §2.3, §3.2).
- **Files**: `cps_hsfa.cpp` (`HsfaSuivre4`, `HsfaFrameDone`, `HsfaScan`).
- **Turn off / check**: `HSFA_LAT4=0` or `lat4=0` in the zip's configuration (identical to the pixel to the old
  core); `HSFA_LAT4_MAX`. The size of the states changes.

## 7. `0003-HSFA-options-du-coeur.patch` — OPTION screen settings

- **Problem**: the Anthology's OPTION screen is native C, not translated; its copy of the settings into the game's
  RAM is lost.
- **Solution**: 24 settings in DIP B-H, written into the game's bytes each time through the mode menu. "Game
  default" writes nothing.
- **Alternatives**: (a) options screen in 68K in the program, 1.5 to 3 days; (c) arcade test menu and EEPROM,
  graft of about 10 KB, SFA3 only, and the game no longer reads the EEPROM. Writing at character select
  as well: tried then removed, it overwrote TRAINING's infinite timer ([OPTIONS](../rapports/OPTIONS.md) §2,
  §4).
- **Files**: `cps_hsfa.cpp` (`HsfaOptions`), `d_cps2.cpp` (DIP), `cps.h`. The test launcher part is patch 11b.
- **Turn off / check**: `HSFA_OPTIONS=0`. All DIPs at default: 60/60 Hyper captures identical
  ([OPTIONS](../rapports/OPTIONS.md) §4).

## 8. `0004-HSFA-stb_vorbis.patch` — Ogg Vorbis decoder

- **Problem**: Hyper's zip is about 710 MB with the ADX streams.
- **Solution**: stb_vorbis 1.22 (a single C file, public domain / MIT), memory API only
  (`STB_VORBIS_NO_STDIO`, `STB_VORBIS_NO_PUSHDATA_API`); `-DHSFA_FLUX_VORBIS` in `Makefile.hsfa`.
- **Alternatives**: libvorbis (0.40 s CPU for 120 s of music versus 0.14 s) and Opus (0.92 s), slower; a
  version of stb_vorbis older than 1.22 (`seek` fixes) ([PLAN-VORBIS](../rapports/PLAN-VORBIS.md) §2.1,
  §6).
- **Files**: `src/dep/libs/stb_vorbis/` (new), `Makefile.hsfa`.
- **Check**: builds on Linux, Android, ROCKNIX, Windows.

## 9. `0005-HSFA-flux-musique-Ogg-Vorbis.patch` — Ogg streams

- **Problem**: play Ogg streams without changing anything in the game's behaviour.
- **Solution**: an AFS entry can be a complete Ogg (recognised by `OggS`). Loop through `LOOPSTART` /
  `LOOPEND`; 2.7 s ring buffer; ADX and Ogg live side by side.
- **Alternatives**: new state fields with a version number, planned by the plan; replaced by
  reusing `pos_abs` and `boucle_ok`: the state keeps its size, a state written with an ADX zip reloads with an
  Ogg zip ([PLAN-VORBIS](../rapports/PLAN-VORBIS.md), "Écarts avec le plan" (differences from the plan)).
- **Files**: `hsfa_flux.h`, `cps_hsfa.cpp`.
- **Check**: `tools/flux/tests/lance_tests.sh` (23 checks). A core without this patch cannot read an Ogg zip.

## 10. `0006-HSFA-carte-musique.patch` — ZERO / ZERO 2 scores

- **Problem**: Hyper's ZERO and ZERO 2 music are recordings (about 112 MB of ADX) while their
  original sound drivers are in the user's `X_DATA.BIN`.
- **Solution**: "music board": a 2nd Z80 (Zet no. 1) runs the SFA1 or SFA2 driver (snapshot taken after it
  starts, restored for each piece), a 3rd QSound reads the ROM already loaded for the replay. Routing: board,
  then stream, then main Z80.
- **Alternatives**: B, scores converted to v1.71 for the main Z80 (no free numbers, entries or bank
  bit); C, share the replay's QSound (both drivers would write to the same channels); D, replay recorded
  QSound writes (loop seam not guaranteed), kept as a fallback
  ([PLAN-PARTITIONS-HYPER](../rapports/PLAN-PARTITIONS-HYPER.md) §2).
- **Files**: `hsfa_musique.h` (new), `cps_hsfa.cpp`, `hsfa_flux.h`, `qs.cpp`, `cps.h`.
- **Turn off / check**: `HSFA_MUSIQUE=0`, or a zip without `hsfa_musique.bin`. Z80 no. 1 is always created for
  Hyper, so that the state layout does not depend on the data. Bench: `lance_tests_carte.sh`.

## 11. `0007-HSFA-roulette-touche-piece.patch` — roulette on Select

- **Problem**: the translation copies the Start bit into the roulette byte `$D3`: Start held on confirmation
  gave a random character, which got in the way of the EX versions.
- **Solution**: on the character grid only, the core writes `$FF84D3` / `$FF88D3` from the player's Coin
  (Select) button, like Select on PS2. Start stays with the game (EX, EX Balrog, S-ISM).
- **Alternatives**: force the byte to 0 (`HSFA_NOROUL`, like the bench's `NOROUL`), kept for tests only: the
  roulette would disappear ([ETATS-HYPER](../rapports/ETATS-HYPER.md) §1.1).
- **Files**: `cps_hsfa.cpp` (`HsfaRoulette`, write tap `$FF8400-$FF8BFF`).
- **Check**: tour of 151 VERSUS identical with and without `HSFA_NOROUL` (§157).

## 11b. `0007b-HSFA-hsfa_run-options-du-coeur-HSFA_VARS.patch` — core options in the launcher

- **Problem**: try the core options without RetroArch, including a change during the game.
- **Solution**: `hsfa_run` serves `HSFA_VARS="clé=valeur;…"` to the core's `GET_VARIABLE` requests; `HSFA_VARS2`
  replaces `HSFA_VARS` from frame `HSFA_VARS2_IMAGE` on, and `GET_VARIABLE_UPDATE` answers true once.
- **Why a separate patch**: this piece of the original diff ([OPTIONS](../rapports/OPTIONS.md) §3.2) was missing from
  the published patch 7. It was extracted from commit `bca36de` of the reference tree. Patch 12 applies with or without it.
- **Alternatives**: not applicable.
- **Files**: `hsfa/hsfa_run.c` only: the `.so` core is not touched.
- **Check**: with `HSFA_VARS="fbneo-dipswitch-sfa3hsfa-Option__Timer_speed=Infinity"` and `DUMPRAM=1400`, an
  SFA3 game stopped in the mode menu has `$FF80A3 = 4` (1 without the variable); checked on 2026-10-18.

## 12. `0008-HSFA-registres-des-plans-ro9a.patch` — `ro9a` planes

- **Problem**: in `ro9a` (Hyper + Upper's Arcade), the program writes the bases `$400/$440/$4A0` of Upper's
  screens. They fell beyond the 64 MB region; the address mask brought them back onto SFA3's tiles.
- **Solution**: word write handled in one go (byte mask kept for bytes); `nCpsGfxScroll` updated
  only on change; region size deduced from `hsfa_gfx.bin` (80 MB for `ro9a`, Upper and Hyper
  unchanged); `hsfa_gfx.bin` converted in place (no 32 to 48 MB buffer); test driver `sfa3hahsfa`;
  `HSFA_PLANS_LOG`; `hsfa_run` `PILOTE=arcade`.
- **Alternatives**: the fork's `mark_all_dirty` invalidation has no equivalent to write, since FBNeo has no tile
  cache. Replacing the Hyper driver straight away: deferred, it will be enough to pass the size in
  `Sfa3hhsfaRomDesc` ([COEUR-BANQUES](../rapports/COEUR-BANQUES.md) §A.2).
- **Files**: `cps_hsfa.cpp`, `cps_rw.cpp`, `cps.h`, `d_cps2.cpp`, `hsfa/hsfa_run.c`.
- **Check**: `HSFA_PLANS_LOG=<f>`: sequence `300` → `400` → `300` at the same frames as the bench; `STATETEST=700`.
  The `sfa3hahsfa` driver only exists in the `.so` if the headers were regenerated (`REGEN_HEADERS=1`).

## 13. `0009-HSFA-prototype-trous-carte-68K.patch` — holes of the map as ROM

- **Problem**: the program ROM is full and the external blocks of `ro9a` are saturated (margin of about 28 KB).
- **Solution**: the 7 free ranges of the 68K map (5.08 MB) served as ROM from the optional member
  `hsfa_trous.bin`, declared by `sfa3hahsfa` alone. Zero cost in cycles.
- **Alternatives**: data bank switched by a `$804210` register, estimated but kept for later (a
  pointer only makes sense if the right page is in place; useful beyond about 5 MB); Hyper's dead data;
  `$F20000-$F7FFFF` (`ro9` only); beyond 16 MB, impossible (24-bit bus)
  ([COEUR-BANQUES](../rapports/COEUR-BANQUES.md) §B.2-§B.4).
- **Files**: `cps_hsfa.cpp` (`HsfaTrous`, `HsfaLoadData`, `HsfaInit`), `d_cps2.cpp`.
- **Turn off / check**: without the member, nothing is mapped. The core log reads the 1st and last word of
  each hole (`HSFA : trou $…`). Limits: no code in the holes; largest hole 2 MB; +5.1 MB of RAM.

## 14. `0010-HSFA-melange-des-objets-transparence.patch` — object blending

- **Problem**: on PSP, the MAX characters' effects are drawn with **saturated additive** blending (mode chosen per
  object, field `+0xAA` of the PSP engine). The CPS2 has no transparency at all: the same effects came out opaque,
  with a dark outline.
- **Solution**: blending modes set by the program and applied by the core when drawing the objects.
  - `$804220-$80423F`: one byte per OBJ palette (0 opaque at reset, 1 additive, 2 alpha 50 %, 3 alpha 75 %,
    4 subtractive; 5 black at 75 % since 0011);
  - `$804240-$804241`: low byte = mode of the **marked** objects, that is those whose X word in the raw list has
    bit 12 set (set by the EFFET_W stub of the MAX characters); 0 = bit ignored;
  - priority: marked object with `$804240` ≠ 0, then palette, then shadow option (0011), then opaque;
  - `HsfaEclater` keeps bit 12 (`x & $F000`); `Cps2ObjDraw` passes `nCpsBlend = 0x100 | mode`; blending in
    `cps_mix()` (24/32 bits) and `cps_mix16()` (16 bits, 565 or 1555);
  - states: the registers are the last area of the libretro state, read only if it exists: old states
    reload (registers at 0), and new ones reload in an old core.
- **Alternatives**:
  - (v1) per-palette registers only: the PSP decides per object, not per palette ([TRANSPARENCE](../rapports/TRANSPARENCE.md)
    §9);
  - (b) block of "additive" palettes: 5 palettes not proven free, and colour copies that would not follow
    the super flashes and darkening; rejected in favour of bit 12, never set by the translated programs
    (0 out of 10.99 M entries) ([TRANSPARENCE-PAR-OBJET](../rapports/TRANSPARENCE-PAR-OBJET.md) §2-§3);
  - registers saved by `SCAN_VAR` (v1): 32 more bytes, old states unreadable; replaced by the optional final
    area (§9.2).
- **Files**: `cps_hsfa.cpp`, `cps.h`, `cps_obj.cpp`, `ctv.cpp`, `ctv_do.h`, `src/burner/libretro/retro_memory.cpp`.
- **Turn off / check**: registers never written = picture identical to the pixel (`nonreg_coeur` ×3 in 32 and 16 bits, 4:3
  and 16:9). Tests: `HSFA_OBJMIX=oo:m[,…]` (offset from `$804220`; `21` = marked objects) forces values at
  reset, `HSFA_MIX_LOG=<fichier>` logs the changes. Mode 2 only (Upper, Hyper, `ro9a`).

## 15. `0011-HSFA-option-ombres-transparentes-PSP.patch` — transparent shadows

- **Problem**: the PSP draws the characters' shadows in black at 75 %; the translated programs draw them opaque
  (OBJ tiles of palette `0x14`).
- **Solution**: core option "Transparent shadows (PSP)", bit 7 of DIP A, **on by default**, for all
  HSFA drivers (modes 1 and 2). A tile is a shadow if its OBJ palette is `0x14` **and** its global code is
  `0x0284A`, `0x305DF-0x30613` or `0x50888-0x5088A` (the same in all four games). New mode 5: black at 75 %.
  The modes set by the game (0010) take precedence over the option.
- **Alternatives**:
  - palette `0x14` alone: it is also used by the stage (foreground posts), which must stay opaque;
  - add a state test (`$FF8000 = 2`, `$FF8004 = 4`): the shadows of demo fights would stay opaque; not
    recommended;
  - mode 3 (alpha 75 % of the colour) would tint the shadow with palette `0x14`: hence mode 5
    ([TRANSPARENCE-OMBRES-JAUGES](../rapports/TRANSPARENCE-OMBRES-JAUGES.md) §3);
  - gauges at 50 % (D5): abandoned, the PSP does not tint the gauges, it fills the bars with a gradient.
- **Files**: `cps_hsfa.cpp`, `cps.h`, `cps_obj.cpp`, `ctv.cpp`, `d_cps2.cpp`.
- **Turn off / check**: DIP off, or `HSFA_OMBRES=0` (takes priority over the DIP): picture identical to the pixel. Automatic
  check over 7 games and 980 captures: 0 pixel changed outside a shadow tile; the codes only appear
  in fights (demo included), never in a menu, a portrait or an ending ([TRANSPARENCE](../rapports/TRANSPARENCE.md)
  §10). **Every non-regression run against an earlier reference is launched with `HSFA_OMBRES=0`.**

## 16. `0012-HSFA-16-9-format-remplir-la-hauteur.patch` — 16:9 core, "fill height"

- **Problem**: on a screen narrower than 16:9 (4:3, 3:2, 16:10…), the 16:9 core shrank the whole picture and
  left bands at the top and bottom.
- **Solution**: option `fbneo-hsfa-format`, "Screen format (fill height)", in the **16:9 core only** and for
  the HSFA drivers: Off (default, unchanged), 4:3, 3:2, 14:9, 16:10, 5:3, 16:9. The picture fills the height and both
  sides are cropped (centred). Width shown = format × 288 (arcade pixels: 384 px ↔ 4:3), even, capped at 448:
  4:3 → 384, 3:2 → 432, 14:9 and above → 448. The cropping is done at the video output (offset pointer); the libretro
  geometry follows the option (`SET_GEOMETRY`). It is not a register: the game knows nothing about it.
- **Alternatives**: number 0012 was planned for the gauges (D5), abandoned. The 14:9 value (full width,
  arcade pixels) was proposed for the Off mode, which stays unchanged by choice
  ([TRANSPARENCE](../rapports/TRANSPARENCE.md) §13). Same principle as the user's "fill height" forks for
  other emulators.
- **Files**: `src/burner/libretro/libretro.cpp`, `retro_common.cpp`, `retro_common.h`.
- **Turn off / check**: Off = picture identical to the pixel. Each format is exactly the centred crop of the Off
  picture; announced geometry: 4:3 → 384 × 224 at 1.3333, 3:2 → 432 × 224 at 1.5, 14:9 → 448 × 224 at 1.5556.

## Outside the chain

- **`fbneo-hsfa-decors.patch`** — widescreen stages injected into SFA3. Problem: 16:9 bands empty or wrong.
  Solution: the "plane bases" mode applies to any game whose configuration gives `plans=`, SFA3 included;
  `hsfa_gfx.bin` optional. Applied on top of patches 1-2; does not apply after patch 6 without adapting
  `cps_hsfa.cpp` ([INJECTION-FORK](../rapports/INJECTION-FORK.md) §7).
- **`hsfa_run-sysdir.diff`** — the launcher passed `getenv("SYSDIR")` to the core, which reads `MAX_PATH` bytes from it: crash
  when the string is at the end of the stack ([ROCKNIX](../rapports/ROCKNIX.md) §3). Fix: copy into a buffer. It
  applies to the current chain with `patch -p1` (offset of 143 lines), not with `git apply`.
