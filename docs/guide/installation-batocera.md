# Playing HSFA on Batocera (v43)

**Français : [installation-batocera.fr.md](installation-batocera.fr.md)**

This guide installs the **FinalBurn Neo HSFA** cores on Batocera and sets up the five HSFA games
(`sfa3hsfa`, `sfa3uhsfa`, `sfa3umhsfa`, `sfa3hhsfa`, `sfa3hahsfa`).

> **Tried on Batocera 43.1 PC (x86_64)**, official image, in a virtual machine: the five games start
> from Batocera's game list and reach the fight, in 4:3 and in 16:9, with sound (Hyper's PS2 music
> included). The installation survives a reboot and uninstalls cleanly.
> Raspberry Pi 4/5 and ARM 64-bit handhelds: **not tried on a real machine**; only the compatibility
> of the files was checked (see "Machines").

## 1. In short

| Your machine | `uname -m` | Folder |
|---|---|---|
| PC (Batocera x86_64) | `x86_64` | `x86_64/` |
| Raspberry Pi 3 / 4 / 400 / 5, ARM 64-bit handhelds (RK3326, H700, RK3566…) | `aarch64` | `aarch64/` |
| Raspberry Pi 0 / 1 / 2, Odroid XU4 (32-bit Batocera) | `armv6l` / `armv7l` | **none** (see §8) |

Each folder holds two cores:

| Core | File | Picture |
|---|---|---|
| FinalBurn Neo HSFA (default) | `fbneo_hsfa_libretro.so` | 4:3, like the arcade cabinet |
| FinalBurn Neo HSFA Widescreen | `fbneo_hsfaws_libretro.so` | 16:9 (wider stage) |

**Why an installer.** Batocera only loads a libretro core from `/usr/lib/libretro/` (with its `.info`
file in `/usr/share/libretro/info/`, otherwise it refuses to launch the game). These folders belong to the system, which
is read-only and rebuilt at every boot. Batocera's documentation offers two ways to add to it:
- `batocera-save-overlay`: the change is **wiped by every Batocera update**;
- a **service** (Batocera v43: `/userdata/system/services/<nom>`, which replaces `custom.sh`): a small script
  run at every boot. This is what the installer does: it keeps the cores on the data partition
  (`/userdata/system/hsfa/`) and the `hsfa` service copies them to `/usr/lib/libretro/` at every boot.
  **The installation therefore survives Batocera reboots and updates.**

## 2. Reaching the machine (SSH)

1. On Batocera, note the IP address: **Menu (Start) → Network Settings**.
2. From the PC: `ssh root@<IP>` (or `ssh root@batocera`). Batocera's default password: `linux`.
   On Windows: PowerShell (`ssh` is built in) or PuTTY.
3. Check:
   ```sh
   uname -m                  # x86_64 or aarch64
   ldd --version | head -1   # Batocera 42 and 43: glibc 2.40 (2.27 or newer is needed)
   ```

## 3. Copying the files

The simplest way is the network share: in Windows Explorer, `\\BATOCERA\share` (or `\\<IP>\share`); on
Linux or macOS, `smb://<IP>/share`, or `scp`.

- copy **the whole delivered folder** `hsfa-batocera/` into `share/`: it becomes `/userdata/hsfa-batocera/`;
- put the five games in `share/roms/hsfa/` (folder to create): `sfa3hsfa.zip`, `sfa3uhsfa.zip`,
  `sfa3umhsfa.zip`, `sfa3hhsfa.zip`, `sfa3hahsfa.zip`. **Do not rename them**: the zip name selects the core's
  driver. Do not put them in `roms/fbneo/`: Batocera's FBNeo does not know these games.

The games are made from your ISO of *Street Fighter Alpha Anthology* (see the repository's build
guide). No game is provided.

## 4. Installing

Over SSH:

```sh
bash /userdata/hsfa-batocera/installer-hsfa-batocera.sh
batocera-es-swissknife --restart        # restarts the interface
```

The script:
1. picks `x86_64/` or `aarch64/` from `uname -m` and checks glibc;
2. stores the two cores and their `.info` files in `/userdata/system/hsfa/`;
3. installs the service `/userdata/system/services/hsfa`, enables it (`batocera-services enable hsfa`) and starts it:
   the cores are in place in `/usr/lib/libretro/` straight away (it is also visible in
   **Menu → System Settings → Services**);
4. installs `/userdata/system/configs/emulationstation/es_systems_hsfa.cfg`: the system "Street Fighter Alpha HSFA"
   (folder `roms/hsfa`, extensions `.zip .7z`). If a file with this name already existed, it keeps a copy of it
   (`.avant-hsfa`);
5. writes to `/userdata/system/batocera.conf`, only if these settings are not there yet:
   `hsfa.emulator=libretro`, `hsfa.core=fbneo_hsfa` (default core: Batocera ignores the `default="true"` of the
   es_systems files) and `hsfa.bezel=none` (no bezel, see §5);
6. creates `roms/hsfa/` and puts `gamelist.xml` (readable names) in it if there is none.

It touches nothing else: not the games, not the saves, not the other systems.

**Without SSH**, by hand over the network share: the two `.so` files of the right folder in `system/hsfa/cores/`, the two
`.info` files in `system/hsfa/info/`, the `hsfa` file in `system/services/`, `es_systems_hsfa.cfg` in
`system/configs/emulationstation/`; add the three lines of point 5 at the end of `system/batocera.conf`, then
enable the service in **Menu → System Settings → Services** and reboot.

> Never name the system file `es_systems_custom.cfg`: under that name, Batocera replaces its **whole** list
> of systems with this file.

## 5. Playing

The **Street Fighter Alpha HSFA** system appears in the list (FinalBurn Neo logo), with the five games.

- **Coin = Select, Start = Start** (controller configured by Batocera). Quit the game: Hotkey + Start.
- **SFA3, Upper, Upper MAX**: coin, Start, then character select.
- **Hyper**: the game only has **Versus** mode: **two controllers** are needed (each player picks a character).
- **Hyper + Arcade**: on the title screen, pick the mode with **left / right** (ARCADE, VERSUS, TRAINING,
  OPTION), then Start.
- Sound is there, including Hyper's PS2 music, read from the game's zip.

### 16:9 (Widescreen core)

Add at the end of `/userdata/system/batocera.conf` (share: `system/batocera.conf`), one line per game:

```
hsfa["sfa3hsfa.zip"].core=fbneo_hsfaws
hsfa["sfa3uhsfa.zip"].core=fbneo_hsfaws
hsfa["sfa3umhsfa.zip"].core=fbneo_hsfaws
hsfa["sfa3hhsfa.zip"].core=fbneo_hsfaws
hsfa["sfa3hahsfa.zip"].core=fbneo_hsfaws
```

or, for all the games at once, replace `hsfa.core=fbneo_hsfa` with `hsfa.core=fbneo_hsfaws`. The choice applies at
the next launch, no need to reboot. (The same setting exists in the interface's advanced game options,
"Emulator / Core"; it is the `batocera.conf` line above that was tried.)

**The bezel must stay on "none"** (`hsfa.bezel=none`, set by the installer): with Batocera's bezel,
the 16:9 picture is squeezed into the bezel's 4:3 frame. If you want the bezel for the 4:3 games
only, remove `hsfa.bezel=none` and add `hsfa["<jeu>.zip"].bezel=none` for each 16:9 game.

## 6. Updates

- **Batocera updates itself**: nothing to redo (the service and the cores are on the data partition).
- **New HSFA cores**: copy the new `hsfa-batocera/` folder and run the installer again (it replaces the
  cores and keeps your settings).

## 7. Uninstalling

```sh
bash /userdata/hsfa-batocera/installer-hsfa-batocera.sh retirer
batocera-es-swissknife --restart
```

Removes the service, the cores, `es_systems_hsfa.cfg` (and puts back your previous file if there was one) and all the
`hsfa.…` / `hsfa["…"]…` settings from `batocera.conf` (copy of the previous file: `batocera.conf.avant-retrait-hsfa`).
The games in `roms/hsfa/` and the saves stay: delete them by hand if you want.

## 8. Machines: what was checked

glibc read in Batocera's official images (without running them):

| Official image | Version | glibc | HSFA cores |
|---|---|---|---|
| x86_64 (PC) | 43.1 | 2.40 | `x86_64/`: **fully tried** (virtual machine) |
| bcm2711 (Raspberry Pi 4/400) | 43.1 | 2.40 | `aarch64/` (glibc 2.27 required): compatible, not tried |
| rk3326 (handhelds) | 42 | 2.40 | `aarch64/`: compatible, not tried |
| odroidxu4 (32-bit ARM) | 43.1 | 2.40 | **incompatible**: the `armhf` core (made for Recalbox's Pi 3) contains ARMv8 instructions (`vmaxnm`, `crc32`, `lda`) that the XU4's ARMv7 lacks |
| bcm2835 (Pi 0/1, ARMv6) | 43 | — | incompatible (ARMv6 processor) |

On Batocera, the Raspberry Pi 3 uses the 64-bit image (`bcm2837`): folder `aarch64/`.

**The Linux x86_64 core must be the one from the `hsfa-batocera/x86_64/` folder**, not the one from the `linux/` folder
of earlier deliveries: the latter needs glibc 2.43 and Batocera (2.40) refuses it
(`version 'GLIBC_2.43' not found`).

## 9. Troubleshooting

| Symptom | What to do |
|---|---|
| The HSFA system does not appear | At least one game is needed in `roms/hsfa/`; restart the interface; check `system/configs/emulationstation/es_systems_hsfa.cfg`. |
| Immediate return to the list at launch | `batocera-services status hsfa` must say "en place" (in place) for both cores; otherwise `batocera-services start hsfa`. |
| Black screen / missing core message | Look at `/userdata/system/logs/es_launch_stderr.log` (`GLIBC_… not found` = wrong core). |
| 16:9 picture squeezed in a frame | The bezel is active: `hsfa.bezel=none` (§5). |

Files to send back: `es_launch_stdout.log`, `es_launch_stderr.log` (in `/userdata/system/logs/`), the installer's
output, and `uname -m`.

## Sources (official Batocera documentation)

- Custom systems: wiki.batocera.org/emulationstation:customize_systems
- Overlay and read-only: wiki.batocera.org/modify_the_system_while_it_s_running
- Services (v43, `custom.sh` abolished): wiki.batocera.org/launch_a_script
- SSH: wiki.batocera.org/access_the_batocera_via_ssh
- Batocera 43.1 code (batocera-linux/batocera.linux repository, branch `batocera-43.1`):
  `configgen/generators/libretro/libretroGenerator.py` (core path and mandatory `.info`),
  `libretroPaths.py`.
