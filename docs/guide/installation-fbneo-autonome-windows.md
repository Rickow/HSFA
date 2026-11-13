# Standalone FinalBurn Neo HSFA (Windows) — guide

**Français : [installation-fbneo-autonome-windows.fr.md](installation-fbneo-autonome-windows.fr.md)**

**Test** build, attached to v0.1.9 (pre-release) and v0.1.10 (same build); see `CHANGELOG.md`.
FinalBurn Neo for 64-bit Windows, without RetroArch, with the drivers and settings of the HSFA core. It runs the **same game archives** as the libretro core (`sfa3hsfa.zip`, `sfa3uhsfa.zip`,
`sfa3umhsfa.zip`, `sfa3hhsfa.zip`, `sfa3hahsfa.zip`, built by the project's script from your discs).

## 1. Two programs

| program | picture | RetroArch equivalent |
|---|---|---|
| `fbneo64.exe` | arcade 4:3 (384 × 224) | core `fbneo_hsfa` |
| `fbneo64ws.exe` | 16:9 (512 × 224, wider stage) | core `fbneo_hsfaws` |

16:9 is a choice made when the core is compiled (like the two libretro cores): hence two programs.
Each has its own settings file (`config\fbneo64.ini`, `config\fbneo64ws.ini`); they can share the same folder,
the same archives and the same game settings (`config\games\`).

These are complete FinalBurn Neo builds: all the other FBNeo games work as in the official version.

## 2. Installation

1. Unzip the folder wherever you want (nothing to install). Windows 10 or 11, 64-bit, is needed.
2. Put the HSFA archives, **as the script built them** (do not recompress them: the music and the
   replay are read directly from the archive, stored without compression), in the `roms\` folder next to the program,
   or give their folder in *Misc → Configure ROM paths…*.
3. Start `fbneo64.exe` (or `fbneo64ws.exe`), *Game → Load game…* (F6), search for "HSFA". On the command line:
   `fbneo64ws.exe sfa3hhsfa` (window: add `-w`).

Game names: `sfa3hsfa` (SFA3), `sfa3uhsfa` (Upper), `sfa3umhsfa` (Upper MAX), `sfa3hhsfa` (Hyper),
`sfa3hahsfa` (Hyper + Upper's Arcade mode).

FBNeo normally reports ROMs whose CRC is not the arcade one. For the HSFA games (rebuilt from
the disc at every build), a ROM found by its name and of the right size is accepted without a message,
as in the RetroArch core.

## 3. Settings

### HSFA game options (= RetroArch's "core options")

*Input → Set dipswitches…* (Ctrl+F5), once the game is running. Same names and **same default values** as in
RetroArch: PS2 music, transparent shadows (PSP), taunt on Select, blood (red by default), skip idle
loops (on), OPTION screen settings (difficulty, timer, etc.). They are kept per game in
`config\games\<jeu>.ini`. As in RetroArch, blood and some settings apply on loading or on
reset (*Game → Reset game*).

### 16:9 (`fbneo64ws.exe`)

*Video → HSFA widescreen*:

- **Widescreen edges**: *Raw* (default since patch 0031: the picture drawn by the game, free PSP-like view),
  *Stage-locked view* (view locked onto the stage, fixed HUD), *Mirror*, *Repeat*, *Black* — same rendering as the
  "Widescreen edges" option of RetroArch. An `fbneo64ws.ini` written by an earlier version keeps its choice
  (`nHsfaWsEdges 0` = stage-locked view): pick *Raw* in the menu;
- **Screen format (fill height)**: *Off* (default, full 16:9, 512 px), 4:3, 3:2, 14:9 (448 px), 16:10, 5:3, 16:9:
  for a screen narrower than 16:9, the picture fills the height and the sides are cropped (centred).

These two choices are kept in `config\fbneo64ws.ini` (`nHsfaWsEdges`, `nHsfaFormat`). In `fbneo64.exe` (4:3) the
menu is greyed out.

Recommended: *Video → Stretch → Correct aspect ratio*, to keep the shape of the arcade pixels.

### Sound

FBNeo for Windows outputs 44,100 Hz by default, RetroArch 48,000 Hz: *Audio → Plugin options → 48000Hz
samplerate* gives the same output as the RetroArch core. Interpolation is set in the same menu.

### Controller

*Input → Map game inputs…* (F5). The Coin key is also used, as in RetroArch, for the roulette of the
character select (Hyper, Upper) and for the taunt in fights ("Taunt on Select" option).

## 4. PS2 music and voice replay

Nothing to set: the streamed music (`hsfa_flux.bin`) and, if the archive contains it, the replay of Hyper's SFA1 /
SFA2 voices and sound effects (`hsfa_rejeu.bin`, `hsfa_rejeu_table.txt`) are read from the game's archive, as in RetroArch.
The archive must be a `.zip` (not `.7z`) and its path must only contain characters of the Windows code
page (e.g. no Chinese characters on a French system).

## 5. Saves

- The arcade save (EEPROM: settings, records) is kept automatically by FBNeo when the game exits
  (`config\games\<jeu>.fs`, as for any CPS-2 game).
- States: *Game → Save states…* (Ctrl+F10 / Ctrl+F9, slots F8 / F11). They also contain the core's HSFA
  zones (object transparency of Upper / Hyper, patch 0010; QSound, objects, palette, 16:9, patch 0029): after a
  load, the picture and the sound go on exactly as without loading. Since patch W06, this is also true of
  rewind (*Game → Rewind*) and run-ahead (*Video → RunAhead*).
- RetroArch states and standalone FBNeo states **are not interchangeable** (different formats of the two
  frontends). A state made with `fbneo64.exe` must not be loaded in `fbneo64ws.exe`, and the other way round.

## 6. Known limits

- Windows only for now (64-bit). The 32-bit version has not been tried.
- Music or replay **outside the archive**: like the RetroArch core (`<system>/fbneo/hsfa/`), the program looks for
  `Y_DATA.BIN`, `anthology.iso` or `ydata.txt` (music), `X_DATA.BIN` or `xdata.txt` (replay) and the tables
  `hsfa_flux_table.txt` / `hsfa_rejeu_table.txt` in **`support\hiscores\hsfa\`** (patch 0030). Not needed with the
  archives built by the script, which contain everything.
- The "About" box shows the compiler of the build machine (Linux), not the one of the executable.

## 7. Licence

FinalBurn Neo and its HSFA changes follow the FinalBurn Neo licence (full text: `LICENSE-FBNeo.txt`):
no sale, no donations, sources of the changes public (the project's patches). Other components (stb_vorbis,
QSound HLE): `NOTICE.md`. No ROM is provided: the games are rebuilt from your own discs.
