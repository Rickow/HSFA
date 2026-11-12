# Installing the HSFA core on RGB10X (ROCKNIX)

**Français : [installation-rocknix.fr.md](installation-rocknix.fr.md)**

For RK3326 handhelds running ROCKNIX: Powkiddy RGB10X, and also RGB10, R36S, RG351… Tried by the user on
RGB10X (§145). Full notes, with the SSH trial and the RK3326 settings:
[tools/rocknix/LISEZMOI-rocknix.md](../../tools/rocknix/LISEZMOI-rocknix.md). Technical report:
[rapports/ROCKNIX.md](../rapports/ROCKNIX.md).

| Core | File | Picture |
|---|---|---|
| FinalBurn Neo HSFA (recommended: fills the 640×480 screen) | `fbneo_hsfa_libretro.so` + `.info` | 4:3 |
| FinalBurn Neo HSFA Widescreen | `fbneo_hsfaws_libretro.so` + `.info` | 16:9, smaller picture with bands |

ROCKNIX from October 2024 or newer is needed (glibc 2.38 at least).

## Compiling the cores

aarch64 cross-compilation (Cortex-A35): [`tools/rocknix/build.sh`](../../tools/rocknix/build.sh) `hsfa` or
`hsfaws`, on an FBNeo tree to which the patches of [patches/fbneo](../../patches/fbneo/README.md) were applied.
`rocknix_compat.h`, force-included, avoids a glibc symbol that is too recent.

## Installing

1. **File access**: in EmulationStation, **Start → Network Settings**, enable Wi-Fi, Samba and SSH;
   user `root`.
2. **Cores**: copy the `.so` and `.info` files to `/tmp/cores/` (actually `/storage/cores`, kept across reboots):
   ```sh
   scp fbneo_hsfa_libretro.so fbneo_hsfa_libretro.info \
       fbneo_hsfaws_libretro.so fbneo_hsfaws_libretro.info root@<IP>:/tmp/cores/
   ```
   Do not rename them.
3. **Games**: `/storage/roms/hsfa/` ← `sfa3hsfa.zip`, `sfa3uhsfa.zip`, `sfa3hhsfa.zip` (without renaming them), and
   [`gamelist.xml`](../../tools/rocknix/gamelist.xml) for readable names.
4. **EmulationStation system**: copy [`es_systems_hsfa.cfg`](../../tools/rocknix/es_systems_hsfa.cfg) to
   `/storage/.config/emulationstation/`, then restart EmulationStation. The "Street Fighter Alpha HSFA" system
   offers the two cores (4:3 by default).
5. **Music from the PS2 disc**: read first from the game's zip (archives built since §145), otherwise from
   `/storage/roms/bios/fbneo/hsfa/`: `hsfa_flux_table.txt` and `Y_DATA.BIN` (recommended: it fits on a FAT32
   card), or `anthology.iso`, or `ydata.txt`.

Choosing the 16:9 core for a game: game options → **Advanced Game Options → Emulator / Core =
`retroarch / fbneo_hsfaws`**; for the whole system: **Per System Advanced Configuration**.
