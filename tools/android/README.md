# Cœurs Android (arm64-v8a)

`build_android.sh` construit les deux cœurs HSFA pour RetroArch Android avec le NDK r28c :

```sh
NDK=<android-ndk-r28c> FBNEO=<arbre libretro/FBNeo af5d3f3 + patchs 0001-0014 et 0007b de patches/fbneo/> tools/android/build_android.sh <sortie>
```

- Sortie : `fbneo_hsfa_libretro_android.so` (4:3) et `fbneo_hsfa_ws_libretro_android.so` (16:9), noms des notices
  `tools/fbneo-hsfa/LISEZMOI-*.md`. Journaux `build_android_<cœur>.log`. Environ 2 min par cœur sur 4 cœurs.
- Construit et vérifié le 2026-10-16 (session cloud) : 9,4 Mo chacun ; `NEEDED` = `libc.so`, `libm.so`, `libdl.so` ;
  53 fonctions `retro_*` exportées ; segments alignés sur 16 Ko (Android 15+) ; Vorbis (`LOOPSTART`) et carte
  musique présents ; le 16:9 s'annonce « FinalBurn Neo HSFA Widescreen ».
- Non exécutés sur Android (pas d'émulateur Android dans la session). Le même code compilé pour ARM Linux a joué un
  match d'Hyper sous `qemu-aarch64` (`docs/rapports/ROCKNIX.md` §7).
