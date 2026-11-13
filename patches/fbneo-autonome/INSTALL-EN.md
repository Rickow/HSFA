# Standalone FinalBurn Neo HSFA (Windows) — install

**Test build**, attached to v0.1.9 (pre-release) and v0.1.10 (same build); see `CHANGELOG.md`.
FinalBurn Neo for 64-bit Windows, without RetroArch, with the HSFA drivers and settings. It runs **the same game archives** as the libretro core (`sfa3hsfa.zip`, `sfa3uhsfa.zip`, `sfa3umhsfa.zip`,
`sfa3hhsfa.zip`, `sfa3hahsfa.zip`, built by the project's script from your own discs).

## Two programs

- `fbneo64.exe`: arcade 4:3 picture (384 × 224), like the `fbneo_hsfa` core.
- `fbneo64ws.exe`: 16:9 (512 × 224, wider stages), like the `fbneo_hsfaws` core.

16:9 is a build-time choice of the core, hence two programs. Each has its own settings file (`config\fbneo64.ini`,
`config\fbneo64ws.ini`); they can share one folder, the archives and the per-game settings (`config\games\`). All the
other FinalBurn Neo games work as in the official release.

## Install

1. Unzip the folder anywhere (Windows 10 or 11, 64-bit; nothing to install).
2. Put the HSFA archives, **exactly as the script built them** (do not repack them: music streams and voice replay are
   read in place from the archive, stored uncompressed), in `roms\` next to the program, or add their folder in
   *Misc → Configure ROM paths…*. Use `.zip` (not `.7z`), in a path made of characters of the Windows code page.
3. Start the program, *Game → Load game…* (F6), search for "HSFA". Command line: `fbneo64ws.exe sfa3hhsfa`
   (add `-w` for a window).

Game names: `sfa3hsfa` (SFA3), `sfa3uhsfa` (Upper), `sfa3umhsfa` (Upper MAX), `sfa3hhsfa` (Hyper), `sfa3hahsfa`
(Hyper + Upper's Arcade mode). The rebuilt ROMs do not have the arcade CRCs: for HSFA games a ROM found by name with
the right size is accepted silently, as in the RetroArch core.

## Settings

- **HSFA options** (RetroArch "core options"): *Input → Set dipswitches…* (Ctrl+F5) once the game runs. Same names and
  **same defaults** as in RetroArch (PS2 music, PSP transparent shadows, taunt on Select, blood, skip idle loops,
  OPTION screen settings). Saved per game in `config\games\<game>.ini`.
- **16:9** (`fbneo64ws.exe`): *Video → HSFA widescreen → Widescreen edges* (Raw by default since patch 0031: the picture
  drawn by the game, free PSP-like view; Stage-locked view, Mirror, Repeat, Black) and *Screen format (fill height)* (Off by default, 4:3, 3:2, 14:9, 16:10, 5:3, 16:9). Saved in
  `config\fbneo64ws.ini` (`nHsfaWsEdges`, `nHsfaFormat`; an `.ini` written by an older build keeps its choice:
  `nHsfaWsEdges 0` = stage-locked view, pick *Raw* in the menu). Greyed out in `fbneo64.exe`. Suggested: *Video → Stretch →
  Correct aspect ratio*.
- **Sound**: FBNeo for Windows defaults to 44100 Hz, RetroArch to 48000 Hz (*Audio → Plugin options → 48000Hz
  samplerate* gives the same output as the RetroArch core).
- **Controls**: *Input → Map game inputs…* (F5). Coin also drives the character roulette (Hyper, Upper) and the taunt in
  fights, as in RetroArch.

## Saves

The arcade EEPROM (settings, records) is kept automatically (`config\games\<game>.fs`). Save states: *Game → Save
states…*; they include the HSFA zones of the core (sprite blending, QSound, sprites, palette, 16:9; patches 0010 and
0029): after a load, picture and sound go on exactly as without loading. Since patch W06, this also holds for the
rewind (*Game → Rewind*) and the run-ahead (*Video → RunAhead*). RetroArch states and standalone FBNeo states
are **not** interchangeable, and states of `fbneo64.exe` and `fbneo64ws.exe` should not be mixed.

## Notes and known limits

- Windows only (64-bit) for now.
- Music or voice replay **outside the archive**: like the RetroArch core (`<system>/fbneo/hsfa/`), the program looks
  for `Y_DATA.BIN`, `anthology.iso` or `ydata.txt` (music), `X_DATA.BIN` or `xdata.txt` (replay) and the tables
  `hsfa_flux_table.txt` / `hsfa_rejeu_table.txt` in **`support\hiscores\hsfa\`** (patch 0030). Not needed with the
  archives built by the script, which contain everything.
- The About box shows the compiler of the build machine (Linux), not the one of the executable.

## Licence

FinalBurn Neo and its HSFA changes follow the FinalBurn Neo licence (full text in `LICENSE-FBNeo.txt`): not for sale,
no donations, sources of all changes are public (the project's patches). Other components (stb_vorbis, QSound HLE):
`NOTICE.md`. No ROM is provided: games are rebuilt from your own discs.
