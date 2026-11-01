#!/bin/bash
# Compilation croisee du coeur FBNeo HSFA pour ROCKNIX (RK3326, Cortex-A35, aarch64 glibc)
# usage : build.sh hsfa|hsfaws   (nettoie les objets avant : les deux coeurs partagent l'arbre)
# FBNEO=<arbre FBNeo patche> pour un autre arbre (libretro/FBNeo af5d3f3 + chaine complete de patches/fbneo/README.md :
#   patchs 0001-0021c et 0007b). Licence du coeur : patches/fbneo/LICENSE-FBNeo.txt, a joindre a toute archive (NOTICE.md).
set -e
SUB=${1:-hsfa}
D=${HSFA_WORKSPACE}/work/agent_rocknix
ICI=$(cd "$(dirname "$0")" && pwd)
# Drapeaux (lot du 04/11) : -O3 effectif, sans -ffloat-store (HSFA_NO_FLOAT_STORE=1, patch 0021c), LTO en une partition
# (garde le .symver d'atan2f de rocknix_compat.h) ; LTO=0 pour s'en passer.
FLTO=""; [ "${LTO:-1}" = 1 ] && FLTO="-flto=4 -flto-partition=one"
cd ${FBNEO:-$D/fbneo}/src/burner/libretro
export LDFLAGS="-O3 -mcpu=cortex-a35 $FLTO -static-libstdc++ -static-libgcc -Wl,-O1 -Wl,--as-needed"
ARGS=(platform=unix SUBSET=$SUB CC=aarch64-linux-gnu-gcc CXX=aarch64-linux-gnu-g++ HSFA_NO_FLOAT_STORE=1
  "PLATFORM_DEFINES=-mcpu=cortex-a35 $FLTO -U__FAST_MATH__ -include $ICI/rocknix_compat.h")
nice -n 19 make "${ARGS[@]}" clean-objs >/dev/null
nice -n 19 make -j4 "${ARGS[@]}" REGEN_HEADERS=1
