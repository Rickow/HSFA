# Playing HSFA on Batocera (v43)

Installs the **FinalBurn Neo HSFA** cores on Batocera and sets up the five HSFA games
(`sfa3hsfa`, `sfa3uhsfa`, `sfa3umhsfa`, `sfa3hhsfa`, `sfa3hahsfa`).

> **Tested on Batocera 43.1 PC (x86_64)**, official image, in a virtual machine: all five games start from the
> Batocera game list and reach a fight, in 4:3 and 16:9, with sound (including Hyper's PS2 music). The install
> survives a reboot and uninstalls cleanly. Raspberry Pi 4/5 and ARM 64-bit handhelds: **not tested on hardware**;
> only file compatibility was checked (see "Machines").

## 1. Which folder

| Machine | `uname -m` | Folder |
|---|---|---|
| PC (Batocera x86_64) | `x86_64` | `x86_64/` |
| Raspberry Pi 3 / 4 / 400 / 5, ARM 64-bit handhelds | `aarch64` | `aarch64/` |
| Raspberry Pi 0 / 1 / 2, Odroid XU4 (32-bit Batocera) | `armv6l` / `armv7l` | **none** (see §7) |

Cores: `fbneo_hsfa` (4:3, default) and `fbneo_hsfaws` (16:9).

**Why an installer.** Batocera only loads libretro cores from `/usr/lib/libretro/` (plus a `.info` file in
`/usr/share/libretro/info/`, otherwise the game is not launched). Those folders belong to the read-only system image,
rebuilt at every boot. `batocera-save-overlay` changes are wiped by every Batocera update, so the installer uses a
**service** (Batocera v43: `/userdata/system/services/<name>`, which replaces `custom.sh`): the cores are kept in
`/userdata/system/hsfa/` and the `hsfa` service copies them to `/usr/lib/libretro/` at every boot. **The install
survives reboots and Batocera updates.**

## 2. Copy the files

Over the network share (`\\BATOCERA\share`, `smb://<IP>/share`, or `scp`):
- copy the whole `hsfa-batocera/` folder into `share/` (it becomes `/userdata/hsfa-batocera/`);
- put the five games in `share/roms/hsfa/` (create it). **Do not rename them** (the zip name selects the driver), and
  do not put them in `roms/fbneo/`.

No game is provided: build them from your own *Street Fighter Alpha Anthology* ISO (see the repository build guide).

## 3. Install

SSH in (`ssh root@<IP>`, Batocera's default password is `linux`), then:

```sh
bash /userdata/hsfa-batocera/installer-hsfa-batocera.sh
batocera-es-swissknife --restart
```

The script picks `x86_64/` or `aarch64/`, checks glibc (2.27 or newer; Batocera 42/43 ship 2.40), stores the cores
in `/userdata/system/hsfa/`, installs and enables the `hsfa` service (also listed in **Main menu → System settings →
Services**), installs `/userdata/system/configs/emulationstation/es_systems_hsfa.cfg` (system "Street Fighter Alpha
HSFA", folder `roms/hsfa`), adds `hsfa.emulator=libretro`, `hsfa.core=fbneo_hsfa` and `hsfa.bezel=none` to
`batocera.conf` if they are missing, and creates `roms/hsfa/gamelist.xml`. Nothing else is touched.

> Never name the system file `es_systems_custom.cfg`: with that name Batocera replaces its **whole** system list.

## 4. Playing

- **Coin = Select, Start = Start**. Exit: Hotkey + Start.
- **Hyper** only has **Versus** mode: two controllers are needed.
- **Hyper + Arcade**: on the title screen pick the mode with **left / right** (ARCADE, VERSUS, TRAINING, OPTION).
- **16:9**: add one line per game to `/userdata/system/batocera.conf`, e.g.
  `hsfa["sfa3hsfa.zip"].core=fbneo_hsfaws` (same for the other four zips), or set `hsfa.core=fbneo_hsfaws` for all.
- **Keep the bezel off** (`hsfa.bezel=none`): Batocera's default 4:3 bezel squeezes the 16:9 picture. To keep bezels
  for 4:3 games only, remove `hsfa.bezel=none` and add `hsfa["<game>.zip"].bezel=none` for each 16:9 game.

## 5. Updates

Batocera updates: nothing to do. New HSFA cores: copy the new `hsfa-batocera/` folder and run the installer again.

## 6. Uninstall

```sh
bash /userdata/hsfa-batocera/installer-hsfa-batocera.sh retirer
batocera-es-swissknife --restart
```

Removes the service, the cores, `es_systems_hsfa.cfg` (restoring a previous file if there was one) and every
`hsfa.…` / `hsfa["…"]…` setting from `batocera.conf` (backup: `batocera.conf.avant-retrait-hsfa`). Games and saves
are kept.

## 7. Machines

glibc read from the official Batocera images: x86_64 43.1, bcm2711 (Pi 4) 43.1, rk3326 42 and odroidxu4 43.1 all
ship **glibc 2.40**; the HSFA cores need 2.27. The `armhf` core (built for Recalbox on the Pi 3) uses ARMv8
instructions (`vmaxnm`, `crc32`, `lda`) that ARMv7 (Odroid XU4) and ARMv6 (Pi 0/1) lack: no 32-bit ARM Batocera
support. Under Batocera the Pi 3 runs the 64-bit image: use `aarch64/`.

The x86_64 core must be the one in `hsfa-batocera/x86_64/`: the older `linux/` build needs glibc 2.43 and Batocera
refuses it (`version 'GLIBC_2.43' not found`).

## 8. Troubleshooting

- System missing: at least one game must be in `roms/hsfa/`; restart the UI.
- Back to the list at launch: `batocera-services status hsfa` must report both cores "en place"
  (otherwise `batocera-services start hsfa`).
- Logs: `/userdata/system/logs/es_launch_stderr.log` and `es_launch_stdout.log`.
