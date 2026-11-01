#!/bin/bash
# Installe (ou retire) les coeurs FBNeo HSFA sur Recalbox 10.x. A lancer en SSH, en root, depuis le dossier livre :
#   bash /recalbox/share/hsfa-recalbox/installer-hsfa.sh            -> installe ou reinstalle (apres une mise a jour)
#   bash /recalbox/share/hsfa-recalbox/installer-hsfa.sh retirer    -> retire les deux coeurs de /usr/lib/libretro
# Il choisit armhf (Raspberry Pi 3, uname -m = armv7l) ou aarch64 selon la machine, verifie la glibc, rend la
# partition systeme inscriptible le temps de la copie, sauvegarde un ancien coeur HSFA s'il y en a un, puis installe
# systemlist.xml et gamelist.xml s'ils n'existent pas encore (il ne remplace jamais les votres).
set -u
D=$(cd "$(dirname "$0")" && pwd)
CORES=/usr/lib/libretro
SYS=/recalbox/share/system/.emulationstation/systemlist.xml
ROMS=/recalbox/share/roms/hsfa
SAUVE=$D/sauvegarde

rw() { mount -o remount,rw / || { echo "Impossible de rendre / inscriptible (mount -o remount,rw /)."; exit 1; }; }
ro() { sync; mount -o remount,ro / 2>/dev/null || true; }

if [ "${1:-}" = "retirer" ]; then
  rw
  rm -f "$CORES/fbneo_hsfa_libretro.so" "$CORES/fbneo_hsfaws_libretro.so"
  ro
  echo "Coeurs HSFA retires de $CORES. Le systeme « hsfa » reste declare dans $SYS : retirez son bloc <system> si"
  echo "vous ne voulez plus le voir (il est cache tant que $ROMS est vide). Puis : es restart"
  exit 0
fi

case $(uname -m) in
  armv7l|armv8l|armhf) A=armhf ;;
  aarch64|arm64)       A=aarch64 ;;
  *) echo "Architecture $(uname -m) non prevue (armhf ou aarch64 seulement)."; exit 1 ;;
esac
# glibc : les coeurs demandent au plus GLIBC_2.27
V=$( (ldd --version 2>/dev/null || /lib/libc.so.6 2>/dev/null) | head -1 | grep -o '[0-9]\+\.[0-9]\+' | tail -1)
echo "Machine : $(uname -m) -> coeurs $A ; glibc : ${V:-inconnue}"
if [ -n "$V" ]; then
  MA=${V%%.*}; MI=${V#*.}
  if [ "$MA" -lt 2 ] || { [ "$MA" -eq 2 ] && [ "$MI" -lt 27 ]; }; then
    echo "glibc $V trop ancienne (2.27 au moins)."; exit 1
  fi
fi
for f in fbneo_hsfa_libretro.so fbneo_hsfaws_libretro.so; do
  [ -f "$D/$A/$f" ] || { echo "Fichier manquant : $D/$A/$f"; exit 1; }
done

rw
mkdir -p "$SAUVE"
for f in fbneo_hsfa_libretro.so fbneo_hsfaws_libretro.so; do
  [ -f "$CORES/$f" ] && cp -f "$CORES/$f" "$SAUVE/$f.precedent"
  cp -f "$D/$A/$f" "$CORES/$f" && chmod 644 "$CORES/$f" && echo "installe : $CORES/$f"
done
ro

if [ ! -f "$SYS" ]; then
  mkdir -p "$(dirname "$SYS")" && cp "$D/systemlist.xml" "$SYS" && echo "installe : $SYS"
elif grep -q 'name="hsfa"' "$SYS"; then
  echo "deja declare : systeme hsfa dans $SYS"
else
  echo "ATTENTION : $SYS existe deja, sans le systeme hsfa. Ajoutez-y a la main le bloc <system> de"
  echo "            $D/systemlist.xml (dans <systemList>), puis relancez l'interface."
fi
mkdir -p "$ROMS"
[ -f "$ROMS/gamelist.xml" ] || { cp "$D/gamelist.xml" "$ROMS/gamelist.xml" && echo "installe : $ROMS/gamelist.xml"; }
echo
echo "Fini. Mettez sfa3hsfa.zip, sfa3uhsfa.zip, sfa3umhsfa.zip, sfa3hhsfa.zip, sfa3hahsfa.zip dans $ROMS"
echo "(sans les renommer), puis relancez l'interface : es restart"
