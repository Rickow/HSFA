#!/bin/bash
# build_std.sh linux|windows|android|x86arm : coeurs aux drapeaux des lots du 03/11 au 09/11 (LOT=<dossier du lot>)
#   linux   : arbre fbneo,     make platform=unix (-O3 du Makefile, -ffloat-store garde) ; glibc <= 2.27 (tools/linux, HSFA_GLIBC_ANCIENNE)
#   windows : arbre fbneo_win, github/tools/windows/build_win.sh (MinGW, -O3, LIBS=-static)
#   android : arbre fbneo_and, github/tools/android/build_android.sh (NDK r28c, clang -O2 du NDK)
#   x86arm  : arbre fbneo_x86, coeur x86-64 aux memes changements que les coeurs ARM (-O3, sans -ffloat-store, LTO
#             une partition) : sert a la non-regression (pas d'execution ARM ici)
set -e
# LOT = dossier du lot (arbres fbneo, fbneo_win, fbneo_and, fbneo_x86 ; sortie/ et journaux/ y sont crees) ;
# NDK = Android NDK r28c ; G = racine de ce depot (tools/windows, tools/android).
L=${LOT:?LOT : dossier du lot}; G=${HSFA_DEPOT:-$(cd "$(dirname "$(readlink -f "$0")")/../.." && pwd)}
NDK=${NDK:-$HOME/Android/Sdk/ndk/28.2.13676358}
mkdir -p $L/sortie/linux $L/sortie/windows $L/sortie/android $L/sortie/x86 $L/journaux
S=$L/sortie; J=$L/journaux; J6=${JOBS:-4}
case $1 in
linux)
  # HSFA_GLIBC_ANCIENNE=1 (defaut) : tools/linux/build_x86_glibc_ancienne.sh (memes drapeaux du Makefile, versions de
  # symboles glibc anciennes : GLIBC <= 2.27, GLIBCXX <= 3.4.21, controle a la construction ; voir tools/linux/README.md).
  # Sans cela le coeur exige la glibc de la machine de construction (2.43 sur Ubuntu 26.04 : refuse par Batocera 43 et
  # la plupart des distributions). HSFA_GLIBC_ANCIENNE=0 : construction des lots du 03/11 au 10/11.
  if [ "${HSFA_GLIBC_ANCIENNE:-1}" = 1 ]; then
    FBNEO=$L/fbneo SORTIE=$S/linux JOBS=$J6 nice -n 19 bash $G/tools/linux/build_x86_glibc_ancienne.sh > $J/linux.log 2>&1
    grep 'GLIBC max' $J/linux.log; echo "linux ok $(date +%T)"
  else
    cd $L/fbneo/src/burner/libretro
    for s in hsfa hsfaws; do
      nice -n 19 make platform=unix SUBSET=$s clean-objs >/dev/null 2>&1 || true
      rm -f fbneo_${s}_libretro.so
      nice -n 19 make -j$J6 platform=unix SUBSET=$s REGEN_HEADERS=1 > $J/linux_$s.log 2>&1
      cp fbneo_${s}_libretro.so $S/linux/; echo "linux $s ok $(date +%T)"
    done
  fi;;
windows)
  nice -n 19 bash $G/tools/windows/build_win.sh $L/fbneo_win tous > $J/windows.log 2>&1
  cp $L/fbneo_win/src/burner/libretro/fbneo_hsfa_libretro.dll $L/fbneo_win/src/burner/libretro/fbneo_hsfaws_libretro.dll $S/windows/
  echo "windows ok $(date +%T)";;
android)
  cd $L/fbneo_and/src/burner/libretro; nice -n 19 make SUBSET=hsfa generate-files > $J/android_generate.log 2>&1
  FBNEO=$L/fbneo_and NDK=$NDK nice -n 19 bash $G/tools/android/build_android.sh $S/android
  mv $S/android/fbneo_hsfa_ws_libretro_android.so $S/android/fbneo_hsfaws_libretro_android.so
  mv $S/android/build_android_*.log $J/
  rm -rf $L/fbneo_and/src/burner/libretro/obj $L/fbneo_and/src/burner/libretro/libs
  echo "android ok $(date +%T)";;
x86arm)
  cd $L/fbneo_x86/src/burner/libretro
  for s in ${2:-hsfa hsfaws}; do
    export LDFLAGS="-O3 -flto=$J6 -flto-partition=one"
    A=(platform=unix SUBSET=$s HSFA_NO_FLOAT_STORE=1 "PLATFORM_DEFINES=-flto=$J6 -flto-partition=one")
    nice -n 19 make "${A[@]}" clean-objs >/dev/null 2>&1 || true
    rm -f fbneo_${s}_libretro.so
    nice -n 19 make -j$J6 "${A[@]}" REGEN_HEADERS=1 > $J/x86arm_$s.log 2>&1
    cp fbneo_${s}_libretro.so $S/x86/; echo "x86arm $s ok $(date +%T)"
  done;;
esac
