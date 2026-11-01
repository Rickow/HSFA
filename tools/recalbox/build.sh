#!/bin/bash
# Compilation croisee du coeur FBNeo HSFA pour Recalbox 10.x.
#   Raspberry Pi 3 / Zero 2 : armhf (Cortex-A53 en 32 bits, glibc 2.39) ; Pi 4 / Pi 5 / PC... : aarch64 ou x86_64.
# usage : build.sh armhf|aarch64 hsfa|hsfaws [dossier de sortie]
#   (nettoie les objets avant : les quatre coeurs partagent l'arbre)
# FBNEO=<arbre FBNeo patche> : libretro/FBNeo af5d3f3 + chaine complete de patches/fbneo/README.md (0001-0017 et 0007b).
#   Par defaut ${HSFA_WORKSPACE}/work/recalbox/fbneo.
# Licence du coeur : patches/fbneo/LICENSE-FBNeo.txt, a joindre a toute archive (NOTICE.md).
#
# Lien a une glibc ancienne (<= 2.31) depuis la glibc d'Ubuntu (2.43) :
#   - libstdc++ et libgcc en statique ;
#   - recalbox_compat.h (inclus partout) : exp, log, pow, atan2f lies a leur version d'origine ;
#   - recalbox_compat.c (objet ajoute a l'edition de liens) : stat, __isoc23_strto*, arc4random, __ioctl_time64,
#     __libc_single_threaded definis localement, pthread_once detourne (--wrap) vers l'ancienne version ;
#   - armhf : -U_TIME_BITS -U_FILE_OFFSET_BITS (Ubuntu active time_t 64 bits par defaut ; glibc < 2.34 ne l'a pas).
# Controle final : aucune version GLIBC au-dela de GLIBC_MAX (2.31 par defaut) dans objdump -T.
set -e
ARCH=${1:-armhf}
SUB=${2:-hsfa}
ICI=$(cd "$(dirname "$0")" && pwd)
: "${HSFA_WORKSPACE:?definir HSFA_WORKSPACE (dossier qui contient work/)}"
FBNEO=${FBNEO:-$HSFA_WORKSPACE/work/recalbox/fbneo}
OUT=${3:-$HSFA_WORKSPACE/work/recalbox/sortie/$ARCH}
GLIBC_MAX=${GLIBC_MAX:-2.31}
case $SUB in hsfa|hsfaws) ;; *) echo "variante inconnue : $SUB (hsfa ou hsfaws)"; exit 1;; esac
case $ARCH in
  armhf)
    T=arm-linux-gnueabihf
    CPU="-marm -mcpu=cortex-a53 -mfpu=neon-fp-armv8 -mfloat-abi=hard -U_TIME_BITS -U_FILE_OFFSET_BITS" ;;
  aarch64)
    T=aarch64-linux-gnu
    CPU="-mcpu=cortex-a53" ;;
  *) echo "architecture inconnue : $ARCH (armhf ou aarch64)"; exit 1;;
esac
mkdir -p "$OUT"
# objet de compatibilite
$T-gcc -O2 -fPIC $CPU -Wall -c "$ICI/recalbox_compat.c" -o "$OUT/recalbox_compat.o"
cd "$FBNEO/src/burner/libretro"
export LDFLAGS="-static-libstdc++ -static-libgcc -Wl,-O1 -Wl,--as-needed -Wl,--wrap=pthread_once $OUT/recalbox_compat.o"
ARGS=(platform=unix SUBSET=$SUB CC=$T-gcc CXX=$T-g++
  "PLATFORM_DEFINES=$CPU -O2 -U__FAST_MATH__ -include $ICI/recalbox_compat.h")
nice -n 19 make "${ARGS[@]}" clean-objs >/dev/null
nice -n 19 make -j4 "${ARGS[@]}" REGEN_HEADERS=1
SO=fbneo_${SUB}_libretro.so
$T-strip --strip-unneeded -o "$OUT/$SO" "$SO"
# controle des versions de symboles
MAXV=$($T-objdump -T "$OUT/$SO" | grep -o 'GLIBC_[0-9.]*' | sed 's/GLIBC_//' | sort -uV | tail -1)
echo "$OUT/$SO : version GLIBC maximale demandee = $MAXV (limite $GLIBC_MAX)"
if [ "$(printf '%s\n%s\n' "$MAXV" "$GLIBC_MAX" | sort -V | tail -1)" != "$GLIBC_MAX" ]; then
  echo "ERREUR : symboles au-dela de GLIBC_$GLIBC_MAX :"
  $T-objdump -T "$OUT/$SO" | grep -o 'GLIBC_[0-9.]*) *[^ ]*' | sort -u | while read -r V S; do
    V=${V#GLIBC_}; V=${V%)}
    [ "$(printf '%s\n%s\n' "$V" "$GLIBC_MAX" | sort -V | tail -1)" = "$GLIBC_MAX" ] || echo "  $S GLIBC_$V"
  done
  exit 2
fi
