# Installing the HSFA core on Android (RetroArch)

**Français : [installation-android.fr.md](installation-android.fr.md)**

The "FinalBurn Neo HSFA" core is a modified FBNeo that runs the three retranslated games, without MAME or
scripts. It lives alongside the official FBNeo (separate file name and options). Tried by the user on an
Anbernic RG477M (§145).

| Core | File | Picture |
|---|---|---|
| FinalBurn Neo HSFA | `fbneo_hsfa_libretro_android.so` (arm64-v8a) | 384×224, 4:3 |
| FinalBurn Neo HSFA Widescreen | `fbneo_hsfa_ws_libretro_android.so` | 448×224, 16:9 |

The `.so` files are not in the repository: they are compiled from the patches of
[patches/fbneo](../../patches/fbneo/README.md). The games are the zips produced by the
[build from the ISO](construction-iso.md): `sfa3hsfa.zip` (SFA3), `sfa3uhsfa.zip` (Upper), `sfa3hhsfa.zip`
(Hyper).

## Installation

1. Copy the `.so` to the device (for example into `Download/`).
2. RetroArch: **Main Menu → Load Core → Install or Restore a Core**, then pick the file.
3. Copy the zips into a games folder, for example `ROMs/hsfa/`. **Do not rename them**: the zip name selects
   the game. Neither `sfa3.zip` nor a BIOS is needed.
4. **Load Content** → the zip → the **FinalBurn Neo HSFA** core (or **… Widescreen**).

In 16:9, if the picture stays 4:3 or looks stretched: **Settings → Video → Scaling → Aspect Ratio = "Core
Provided"**.

## Music and sounds from the PS2 disc

The music the arcade sound does not know (4 Upper tracks; ZERO, ZERO 2 and ALPHA in Hyper) and Hyper's SFA1 / SFA2
voices come from the Anthology disc. The core looks for them **first in the game's zip** (archives
built since §145 contain them), then in RetroArch's `fbneo/hsfa/` system folder: `Y_DATA.BIN`,
or the ISO renamed `anthology.iso`, or a `ydata.txt` that gives the path, with `hsfa_flux_table.txt`. Without this
data, the game still works, without this music.

Setting: **Core Options → DIP switches → "PS2 music (ADX streams, Y_DATA.BIN)"**: `Off`, `Missing tracks
only` or `All tracks` (default for Hyper).

## Controls and settings

| Controller | Game |
|---|---|
| Select | coin |
| Start | Start (a 2nd press confirms the mode in the menu) |
| Y / X / L | light / medium / heavy punch |
| B / A / R | light / medium / heavy kick |

- Leave "CPU clock" at 100 %.
- Savestates, rewind and run-ahead work.
- OPTION and EXIT in the menu stay a black screen (as on the bench).

## Known 16:9 defects

The game is designed for 4:3: empty bands at the ends of some stages, objects cut 32 px from the edge, non-fight
screens laid out for 4:3. The injected widescreen stages ([INJECTION-FORK](../rapports/INJECTION-FORK.md))
fix the first point; they are not in the delivered cores yet.

## Detailed notes

- [LISEZMOI-coeur.md](../../tools/fbneo-hsfa/LISEZMOI-coeur.md): SFA3 and Upper;
- [LISEZMOI-hyper.md](../../tools/fbneo-hsfa/LISEZMOI-hyper.md): Hyper and the music;
- [LISEZMOI-widescreen.md](../../tools/fbneo-hsfa/LISEZMOI-widescreen.md): 16:9 core.
