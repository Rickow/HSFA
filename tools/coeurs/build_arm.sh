#!/bin/bash
# build_arm.sh recalbox-armhf|recalbox-aarch64|rocknix hsfa|hsfaws <sortie>  (FBNEO=<arbre>, JOBS=3, LTO=1)
# Drapeaux du coeur Recalbox d'essai (coeur_recalbox_essai/outils/build_essai.sh, valide par l'utilisateur sur Pi 3) :
#   -O3 effectif (pas de -O2 final dans PLATFORM_DEFINES), HSFA_NO_FLOAT_STORE=1 (patch 0021c), LTO une partition
#   (les .symver en asm de tete de recalbox_compat.h / rocknix_compat.h restent avec les appels), -O3 et CPU au lien.
# Recalbox : objet recalbox_compat.o, --wrap=pthread_once, glibc <= 2.27 ; ROCKNIX : rocknix_compat.h, -mcpu=cortex-a35.
set -e
CIBLE=$1; SUB=$2; OUT=${3:?sortie}
G=${HSFA_TOOLS:-$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)}   # tools/ de ce depot (recalbox_compat, rocknix_compat)
FBNEO=${FBNEO:?arbre}; JOBS=${JOBS:-3}; LTO=${LTO:-1}
FLTO=""; [ "$LTO" = 1 ] && FLTO="-flto=$JOBS -flto-partition=one"
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
EXTRA_LD=""
case $CIBLE in
  recalbox-armhf)   T=arm-linux-gnueabihf; CPU="-marm -mcpu=cortex-a53 -mfpu=neon-vfpv4 -mfloat-abi=hard"; ABI="-U_TIME_BITS -U_FILE_OFFSET_BITS"; INC=$G/recalbox/recalbox_compat.h; GLIBC_MAX=2.27;;
  recalbox-aarch64) T=aarch64-linux-gnu; CPU="-march=armv8-a+crc+simd -mtune=cortex-a72"; ABI=""; INC=$G/recalbox/recalbox_compat.h; GLIBC_MAX=2.27;;
  rocknix)          T=aarch64-linux-gnu; CPU="-mcpu=cortex-a35"; ABI=""; INC=$G/rocknix/rocknix_compat.h; GLIBC_MAX=;;
  *) echo "cible inconnue $CIBLE"; exit 1;;
esac
case $CIBLE in recalbox-*)
  $T-gcc -O2 -fPIC $CPU $ABI -Wall -c "$G/recalbox/recalbox_compat.c" -o "$OUT/recalbox_compat.o"
  EXTRA_LD="-Wl,--wrap=pthread_once $OUT/recalbox_compat.o";;
esac
cd "$FBNEO/src/burner/libretro"
export LDFLAGS="-O3 $CPU $FLTO -static-libstdc++ -static-libgcc -Wl,-O1 -Wl,--as-needed $EXTRA_LD"
ARGS=(platform=unix SUBSET=$SUB CC=$T-gcc CXX=$T-g++ HSFA_NO_FLOAT_STORE=1
  "PLATFORM_DEFINES=$CPU $ABI $FLTO -U__FAST_MATH__ -include $INC")
nice -n 19 make "${ARGS[@]}" clean-objs >/dev/null
rm -f fbneo_${SUB}_libretro.so
nice -n 19 make -j$JOBS "${ARGS[@]}" REGEN_HEADERS=1
SO=fbneo_${SUB}_libretro.so
case $CIBLE in
  recalbox-*) $T-strip --strip-unneeded -o "$OUT/$SO" "$SO";;
  rocknix) cp "$SO" "$OUT/$SO";;
esac
MAXV=$($T-objdump -T "$OUT/$SO" | grep -o 'GLIBC_[0-9.]*' | sed 's/GLIBC_//' | sort -uV | tail -1)
echo "$OUT/$SO : version GLIBC maximale demandee = $MAXV (limite ${GLIBC_MAX:-aucune})"
if [ -n "$GLIBC_MAX" ] && [ "$(printf '%s\n%s\n' "$MAXV" "$GLIBC_MAX" | sort -V | tail -1)" != "$GLIBC_MAX" ]; then
  echo "ERREUR : symboles au-dela de GLIBC_$GLIBC_MAX"; exit 2
fi
