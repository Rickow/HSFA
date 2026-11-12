#!/bin/bash
# build_x86_glibc_ancienne.sh [hsfa hsfaws] : coeurs Linux x86_64 HSFA lies a des versions de symboles glibc anciennes
# (<= 2.27) sans conteneur ni root, avec la chaine d'outils de la machine (essaye avec GCC 15 / glibc 2.43).
#   FBNEO=<arbre FBNeo HSFA>  SORTIE=<dossier>  [JOBS=3]
# Meme commande que le lot (make platform=unix SUBSET=... REGEN_HEADERS=1, drapeaux du Makefile inchanges), plus :
#   -include hsfa_x86_compat.h  (exp/log/pow/atan2f -> GLIBC_2.2.5)
#   hsfa_x86_compat.o au lien    (stat/stat64 -> __xstat*@GLIBC_2.2.5 ; __isoc23_strto* -> strto*)
set -e
C=$(cd "$(dirname "$0")" && pwd)
FBNEO=${FBNEO:?arbre FBNeo}; SORTIE=${SORTIE:?dossier de sortie}; mkdir -p "$SORTIE"; SORTIE=$(cd "$SORTIE" && pwd)
gcc -O2 -fPIC -Wall -c "$C/hsfa_x86_compat.c" -o "$SORTIE/hsfa_x86_compat.o"
cd "$FBNEO/src/burner/libretro"
for s in ${@:-hsfa hsfaws}; do
  export LDFLAGS="$SORTIE/hsfa_x86_compat.o"
  A=(platform=unix SUBSET=$s "PLATFORM_DEFINES=-include $C/hsfa_x86_compat.h")
  make "${A[@]}" clean-objs >/dev/null 2>&1 || true
  rm -f fbneo_${s}_libretro.so
  make -j${JOBS:-3} "${A[@]}" REGEN_HEADERS=1
  cp fbneo_${s}_libretro.so "$SORTIE/"
  M=$(objdump -T "$SORTIE/fbneo_${s}_libretro.so" | grep -o 'GLIBC_[0-9.]*' | sed 's/GLIBC_//' | sort -uV | tail -1)
  echo "$SORTIE/fbneo_${s}_libretro.so : GLIBC max = $M"
  [ "$(printf '%s\n%s\n' "$M" 2.27 | sort -V | tail -1)" = 2.27 ] || { echo "ERREUR : symboles au-dela de GLIBC_2.27"; exit 2; }
done
rm -f "$SORTIE/hsfa_x86_compat.o"
