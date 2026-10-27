#!/bin/bash
# Coeurs libretro HSFA pour Windows 64 bits (RetroArch), compiles depuis Linux avec MinGW-w64.
#   apt-get install g++-mingw-w64-x86-64-posix gcc-mingw-w64-x86-64-posix
#   tools/windows/build_win.sh <dossier FBNeo patche (patches/fbneo/README.md : 0001-0014 et 0007b)> [hsfa|hsfaws|tous]
# Licence du coeur : patches/fbneo/LICENSE-FBNeo.txt, a joindre a toute archive (NOTICE.md).
# Sortie : fbneo_hsfa_libretro.dll / fbneo_hsfaws_libretro.dll dans src/burner/libretro.
# LIBS=-static : sans lui, la DLL depend de libwinpthread-1.dll, absente de RetroArch, et le coeur ne se charge pas.
set -e
FB=${1:?dossier FBNeo patche}
QUOI=${2:-tous}
[ "$QUOI" = tous ] && SUBS="hsfa hsfaws" || SUBS=$QUOI
cd "$FB/src/burner/libretro"
M=(platform=win CC=x86_64-w64-mingw32-gcc CXX=x86_64-w64-mingw32-g++ LIBS=-static)
for s in $SUBS; do
  make "${M[@]}" SUBSET=$s clean-objs >/dev/null 2>&1 || true
  rm -f fbneo_${s}_libretro.dll
  nice -n 19 make -j"$(nproc)" "${M[@]}" SUBSET=$s REGEN_HEADERS=1
  x86_64-w64-mingw32-objdump -p fbneo_${s}_libretro.dll | grep "DLL Name"   # attendu : KERNEL32.dll, msvcrt.dll
done
