#!/bin/bash
# Cœurs FBNeo HSFA pour Android (arm64-v8a) : 4:3 (hsfa) et 16:9 (hsfaws).
# usage : NDK=<android-ndk-r28c> FBNEO=<arbre libretro/FBNeo af5d3f3 + patchs 0001-0014 et 0007b> build_android.sh [sortie]
#   (chaine complete : patches/fbneo/README.md). Licence du coeur : patches/fbneo/LICENSE-FBNeo.txt, a joindre a toute
#   archive (NOTICE.md).
# Sortie : fbneo_hsfa_libretro_android.so, fbneo_hsfa_ws_libretro_android.so (noms des notices LISEZMOI-*).
set -e
: "${NDK:?NDK = dossier du NDK Android (r28c)}"
: "${FBNEO:?FBNEO = arbre FBNeo patche}"
OUT=$(realpath -m "${1:-.}"); mkdir -p "$OUT"
cd "$FBNEO/src/burner/libretro/jni"
for SUB in hsfa hsfaws; do
  NOM=fbneo_hsfa_libretro_android.so; [ $SUB = hsfaws ] && NOM=fbneo_hsfa_ws_libretro_android.so
  rm -rf ../obj ../libs
  "$NDK/ndk-build" -j"$(nproc)" APP_ABI=arm64-v8a SUBSET=$SUB NDK_PROJECT_PATH=.. NDK_APPLICATION_MK=Application.mk \
    APP_BUILD_SCRIPT=Android.mk > "$OUT/build_android_$SUB.log" 2>&1 || { tail -20 "$OUT/build_android_$SUB.log"; exit 1; }
  cp ../libs/arm64-v8a/libretro.so "$OUT/$NOM"
  echo "$NOM : $(stat -c %s "$OUT/$NOM") octets"
done
