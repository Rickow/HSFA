#!/bin/bash
# controle.sh <dossier des coeurs (structure de livraison)> <dossier du lot de reference (05/11)> : controles statiques des 12 coeurs
# architecture, attributs ARM, GLIBC max, NEEDED / DLL, symboles retro_* exportes, chaines personnelles, version GIT,
# options presentes, octet par defaut du Dip A (dipdef.py contre le meme coeur du 04/11), taille
# HSFA_MOTIFS_PERSO = motifs personnels a chercher dans les binaires (expression grep -E : nom, e-mail, dossier) ;
# ils ne sont pas dans ce fichier (anonymat) : les donner dans config.env.
D=$1; R=$2; O=$(dirname "$(readlink -f "$0")")   # dipdef.py a cote
for so in $D/linux/*.so $D/android/*.so $D/rocknix/*.so $D/recalbox/armhf/*.so $D/recalbox/aarch64/*.so $D/windows/*.dll; do
  rel=${so#$D/}
  case $rel in linux/*) T=x86_64-linux-gnu;; recalbox/armhf/*) T=arm-linux-gnueabihf;; windows/*) T=x86_64-w64-mingw32;; *) T=aarch64-linux-gnu;; esac
  echo "== $rel ($(stat -c %s $so) octets ; 04/11 : $(stat -c %s $R/$rel 2>/dev/null))"
  file -b "$so" | cut -c1-110
  if [ $T = x86_64-w64-mingw32 ]; then
    echo "DLL : $($T-objdump -p $so | grep 'DLL Name' | awk '{print $3}' | tr '\n' ' ')"
    echo "exports : $($T-objdump -p $so | sed -n '/\[Ordinal\/Name Pointer\] Table/,/^$/p' | grep -c 'retro_') retro_* ; total $($T-objdump -p $so | sed -n '/\[Ordinal\/Name Pointer\] Table/,/^$/p' | grep -c '\]')"
  else
    OD=objdump; [ $T != x86_64-linux-gnu ] && OD=$T-objdump; RE=readelf; [ $T != x86_64-linux-gnu ] && RE=$T-readelf
    [ $T = arm-linux-gnueabihf ] && $RE -A "$so" | grep -E 'Tag_CPU_name|Tag_CPU_arch:|Tag_FP_arch|Tag_Advanced_SIMD|Tag_ABI_VFP_args' | tr -s ' ' | tr '\n' ';' && echo
    case $rel in android/*) ;; *) echo "GLIBC max : $($OD -T "$so" | grep -o 'GLIBC_[0-9.]*' | sed 's/GLIBC_//' | sort -uV | tail -1) ; versions particulieres : $($OD -T "$so" | grep -E ' (exp|log|pow|atan2f)$' | awk '{print $(NF-1)":"$NF}' | tr '\n' ' ')";; esac
    echo "NEEDED : $($RE -d "$so" | grep NEEDED | grep -o '\[.*\]' | tr '\n' ' ')"
    echo "exports : $($OD -T "$so" | grep -v UND | grep -E ' (g|w) ' | awk '{print $NF}' | grep -c '^retro_') retro_* ; hors retro_ : $($OD -T "$so" | grep -v UND | grep -E ' (g|w) ' | awk '{print $NF}' | grep -v '^retro_' | tr '\n' ' ')"
  fi
  echo "chaines perso : $(strings -a "$so" | grep -ciE "/home/|${HSFA_MOTIFS_PERSO:-claude}")"
  echo "version : $(strings -a "$so" | grep -m1 -oE 'GIT[0-9a-f]{7}') ; Skip idle loops : $(strings -a "$so" | grep -c 'Skip idle loops (faster)') ; Screen format : $(strings -a "$so" | grep -c '^Screen format (fill height)$') ; Widescreen edges : $(strings -a "$so" | grep -c '^Widescreen edges$') ; cle ws-edges : $(strings -a "$so" | grep -c '^fbneo-hsfa-ws-edges$') ; Stage-locked view : $(strings -a "$so" | grep -cx 'Stage-locked view') ; Blood : $(strings -a "$so" | grep -c '^Blood (applies on load or restart)$')/$(strings -a "$so" | grep -cx 'Red (uncensored)') ; valeurs stage/mirror/repeat/black/raw (strings -n 3) : $(for v in stage mirror repeat black raw; do strings -a -n 3 "$so" | grep -cx $v; done | tr '\n' '/')"
  python3 $O/dipdef.py $R/$rel $so
done
