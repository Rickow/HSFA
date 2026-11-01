# Installing the HSFA core on Recalbox 10 (Raspberry Pi 3)

Full French guide, with sources: [tools/recalbox/LISEZMOI-recalbox.md](../../tools/recalbox/LISEZMOI-recalbox.md).

> **Tested by the user on a Raspberry Pi 3B (Recalbox 10, 32-bit `armhf` core): it works.** Launching from
> Recalbox's game list does not work yet: open RetroArch's menu, load the core ("Load Core"), then the game.
> Hyper + Arcade slows down a little on a Pi 3 (Frameskip "Auto" and Samplerate 32000 in the core options help).

| Machine | `uname -m` | Folder |
|---|---|---|
| **Raspberry Pi 3** / Zero 2, Recalbox 10 | `armv7l` | `armhf/` |
| Raspberry Pi 4 / 400 / 5, Recalbox 10 | `aarch64` | `aarch64/` |

Each folder holds `fbneo_hsfa_libretro.so` (4:3, default) and `fbneo_hsfaws_libretro.so` (16:9).
Recalbox 10 for the Pi 3 is a **32-bit** system (Cortex-A53 in AArch32, `bcm2709` kernel, glibc 2.39 from
buildroot 2024.05.3). That is why the 64-bit ROCKNIX core does not load there.

## Build

`tools/recalbox/build.sh armhf|aarch64 hsfa|hsfaws` (set `HSFA_WORKSPACE`; `FBNEO=<tree>` = libretro/FBNeo `af5d3f3`
plus the full `patches/fbneo/` chain). It links libstdc++/libgcc statically. `recalbox_compat.h` and
`recalbox_compat.c` bind the core to old glibc symbol versions, and the script stops if `objdump -T` shows any
version above GLIBC_2.31.

## Install

1. SSH in: `ssh root@<IP>` (default password `recalboxroot`). Check `uname -m` and `ldd --version`
   (glibc 2.27 or newer is needed).
2. Copy the whole delivery folder to `share/hsfa-recalbox/` (`/recalbox/share/hsfa-recalbox/`). Copy the games
   to `share/roms/hsfa/`: `sfa3hsfa.zip`, `sfa3uhsfa.zip`, `sfa3umhsfa.zip`, `sfa3hhsfa.zip`, `sfa3hahsfa.zip`.
   Do not rename them.
3. Run `bash /recalbox/share/hsfa-recalbox/installer-hsfa.sh && es restart`. The script:
   - picks the folder from `uname -m`;
   - runs `mount -o remount,rw /` and copies the cores to `/usr/lib/libretro/` with mode 644;
   - installs `systemlist.xml` in `/recalbox/share/system/.emulationstation/` and `gamelist.xml`, but only if
     they do not exist yet.

   Manual steps are in the French guide.

Recalbox only accepts cores that are listed for the game's system. `systemlist.xml` therefore adds a new system,
"Street Fighter Alpha HSFA" (folder `roms/hsfa/`), with the cores `fbneo_hsfa` (default) and `fbneo_hsfaws`.

## 16:9

You can set the 16:9 core at four levels:
- the whole system: `hsfa.emulator=libretro` and `hsfa.core=fbneo_hsfaws` in `recalbox.conf`;
- one game, from its *Edit game → Emulator / Core* menu;
- a folder: a `.recalbox.conf` file in it, containing `global.emulator=libretro` and `global.core=fbneo_hsfaws`;
- one game, by file: `roms/hsfa/<game>.zip.recalbox.conf`, with the same keys as `recalbox.conf`.

## Updates and rollback

`/usr/lib/libretro` lives in Recalbox's overlay partition, and a system update wipes it, so the cores are lost.
Everything under `/recalbox/share` stays. After each update, run the installer again. The previous cores are kept
in `hsfa-recalbox/sauvegarde/` and, until the next update, in `/overlay/upper.old/usr/lib/libretro/`. To remove
the cores, run `installer-hsfa.sh retirer`, then delete the `hsfa` block from `systemlist.xml`. Recalbox's own
FBNeo is never touched.

Music from the PS2 disc goes in `/recalbox/share/bios/fbneo/hsfa/`, or inside the game zips. No game data is
provided. Licence: `patches/fbneo/LICENSE-FBNeo.txt` (not for sale, no donations).
