# Installer le cœur HSFA sur RGB10X (ROCKNIX)

Pour les consoles RK3326 sous ROCKNIX : Powkiddy RGB10X, et aussi RGB10, R36S, RG351… Essayé par l'utilisateur sur
RGB10X (§145). Notice complète, avec l'essai par SSH et les réglages du RK3326 :
[tools/rocknix/LISEZMOI-rocknix.md](../../tools/rocknix/LISEZMOI-rocknix.md). Rapport technique :
[rapports/ROCKNIX.md](../rapports/ROCKNIX.md).

| Cœur | Fichier | Image |
|---|---|---|
| FinalBurn Neo HSFA (conseillé : remplit l'écran 640×480) | `fbneo_hsfa_libretro.so` + `.info` | 4:3 |
| FinalBurn Neo HSFA Widescreen | `fbneo_hsfaws_libretro.so` + `.info` | 16:9, image réduite avec bandes |

Il faut ROCKNIX d'octobre 2024 ou plus récent (glibc 2.38 au moins).

## Compiler les cœurs

Compilation croisée aarch64 (Cortex-A35) : [`tools/rocknix/build.sh`](../../tools/rocknix/build.sh) `hsfa` ou
`hsfaws`, sur un arbre FBNeo auquel on a appliqué les patchs de [patches/fbneo](../../patches/fbneo/README.md).
`rocknix_compat.h`, inclus de force, évite un symbole de glibc trop récent.

## Installer

1. **Accès aux fichiers** : dans EmulationStation, **Start → Network Settings**, activer Wi-Fi, Samba et SSH ;
   utilisateur `root`.
2. **Cœurs** : copier les `.so` et `.info` dans `/tmp/cores/` (en réalité `/storage/cores`, conservé au redémarrage) :
   ```sh
   scp fbneo_hsfa_libretro.so fbneo_hsfa_libretro.info \
       fbneo_hsfaws_libretro.so fbneo_hsfaws_libretro.info root@<IP>:/tmp/cores/
   ```
   Ne pas les renommer.
3. **Jeux** : `/storage/roms/hsfa/` ← `sfa3hsfa.zip`, `sfa3uhsfa.zip`, `sfa3hhsfa.zip` (sans les renommer), et
   [`gamelist.xml`](../../tools/rocknix/gamelist.xml) pour des noms lisibles.
4. **Système EmulationStation** : copier [`es_systems_hsfa.cfg`](../../tools/rocknix/es_systems_hsfa.cfg) dans
   `/storage/.config/emulationstation/`, puis redémarrer EmulationStation. Le système « Street Fighter Alpha HSFA »
   propose les deux cœurs (4:3 par défaut).
5. **Musiques du disque PS2** : lues d'abord dans le zip du jeu (archives construites depuis le §145), sinon dans
   `/storage/roms/bios/fbneo/hsfa/` : `hsfa_flux_table.txt` et `Y_DATA.BIN` (conseillé : il tient sur une carte
   FAT32), ou `anthology.iso`, ou `ydata.txt`.

Choisir le cœur 16:9 pour un jeu : options du jeu → **Advanced Game Options → Emulator / Core =
`retroarch / fbneo_hsfaws`** ; pour tout le système : **Per System Advanced Configuration**.
