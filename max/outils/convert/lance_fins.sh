#!/bin/bash
# Captures MAME des fins d'arcade (sfa3ud) avec vidages plans + palettes : ./lance_fins.sh 10 0f 0c ...  (3 en parallèle)
ICI=$(cd "$(dirname "$(readlink -f "$0")")" && pwd); export ICI
un() { p=$1; O=~/.cache/sfa3max/mame_fin/f$p; rm -rf $O; mkdir -p $O; cd ${HSFA_WORK:-work}/mame
  nf=26000; [ $p = 07 ] && nf=40000
  VIDAGE=1 PAS=20 FIN_OUT=$O TOURNEE=${HSFA_WORK:-work}/mame/tournee.lua REF=1 PERSO=$p FORCE="Lff8540=ffffffff" NF=$nf \
    OUT=$O/tournee.txt nice -n 15 mame sfa3ud -rompath roms -video none -sound none -nothrottle -skip_gameinfo \
    -snapshot_directory $O/snap -nvram_directory $O/nv -autoboot_script "$ICI/mame_fin.lua" > $O/mame.log 2>&1
  echo "fin $p : $(wc -l < $O/journal.txt) captures"; }
export -f un
echo "$@" | tr ' ' '\n' | xargs -P ${P:-3} -I{} bash -c 'un {}'
