#!/bin/sh
# Essai par SSH du son d'Hyper sur la console (ROCKNIX, aarch64) : un VERSUS pilote (Ryu A-ISM contre Ryu X-ISM,
# adversaire a 1 PV), 8 000 images, sans ecran. Mesure la vitesse et verifie les musiques jouees.
# usage : sh essai_son_hyper.sh [dossier_coeurs] [dossier_zips]   (defauts : /storage/cores, /storage/roms/hsfa)
# Quitter le jeu en cours avant (RetroArch ferme) pour que la mesure de vitesse soit juste.
ICI=$(cd "$(dirname "$0")" && pwd)
COEURS=${1:-/storage/cores}
ZIPS=${2:-/storage/roms/hsfa}
SYS=/storage/roms/bios
N=8000
OUT=$ICI/resultats
mkdir -p "$OUT"
chmod +x "$ICI/joue_arm" 2>/dev/null
ok=0; ko=0
for C in hsfa hsfaws; do
  SO=$COEURS/fbneo_${C}_libretro.so
  [ -f "$SO" ] || { echo "$C : coeur absent ($SO)"; continue; }
  R=$OUT/$C; mkdir -p "$R"; rm -f "$R"/*
  t0=$(date +%s.%N 2>/dev/null || date +%s)
  HSFA_NOROUL=1 HSFA_TOURNEE="00.Z3.iA/00.Z3.iX" HSFA_TOURNEE_LOG=$R/tournee.log HSFA_FLUX_LOG=$R/flux.log \
    "$ICI/joue_arm" "$SO" "$ZIPS/sfa3hhsfa.zip" "$SYS" $N "$R/son.wav" > "$R/sortie.log" 2>&1
  t1=$(date +%s.%N 2>/dev/null || date +%s)
  ips=$(awk -v a="$t0" -v b="$t1" -v n=$N 'BEGIN { d = b - a; if (d > 0) printf "%.0f", n / d; else print "?" }')
  echo "== $C : $N images en $(awk -v a="$t0" -v b="$t1" 'BEGIN { printf "%.1f", b - a }') s, soit $ips images/s (il en faut 60)"
  grep -E "^[0-9A-F]{4} ->" "$R/flux.log" 2>/dev/null | sed 's/ vol.*//' > "$R/musiques.txt"
  if cmp -s "$R/musiques.txt" "$ICI/musiques_attendues.txt"; then
    echo "   musiques : conformes (0002, 0181, 0192, 0181, 0192, 0004)"; ok=$((ok+1))
  else
    echo "   musiques : DIFFERENTES de l'attendu, voir $R/musiques.txt et $R/sortie.log"; ko=$((ko+1))
  fi
  grep "HSFA flux\|HSFA rejeu\|HSFA musique" "$R/sortie.log" | head -3 | sed 's/^/   /'
  echo "   son : $R/son.wav (a ecouter sur le PC) ; md5 $(md5sum "$R/son.wav" | cut -c1-8)"
done
echo "Bilan : $ok conforme(s), $ko different(s). Envoyer le dossier $OUT si quelque chose cloche."
