#!/bin/bash
# interrupteurs_liste.sh <module> VAR=val [VAR=val ...] -- like interrupteurs.sh, but for a given list of settings
# (the review used it for a second round on ro9 / ro5 of the switches with no effect on ro3). Builds the module's
# reference first if it is missing. Results appended to $SORTIE/interrupteurs_<module>.txt (same format).
# Environment: HSFA_TRAD, SORTIE, RO9_EXTRACT_MODULES / RO9_SON_DONNEES (see interrupteurs.sh, construit.sh).
# Tool of the translator review (E8, 11/11/2026, docs/rapports/reviews/).
set -u
ICI=$(dirname "$(readlink -f "$0")"); M=${1:?usage: interrupteurs_liste.sh <module> VAR=val ...}; shift
export SORTIE=$(mkdir -p "${SORTIE:-./revue_interrupteurs}" && cd "${SORTIE:-./revue_interrupteurs}" && pwd)
S=$SORTIE/interrupteurs_$M.txt; C=$SORTIE/constr
EXTRA=()
if [ "$M" = ro9 ]; then EXTRA=("EXTRACT_MODULES=${RO9_EXTRACT_MODULES:?}" "HSFA_SON_DONNEES=${RO9_SON_DONNEES:?}"); fi
un() { n=$1; shift
  r=$(MODULE=$M "$ICI/construit.sh" "${M}_$n" "${EXTRA[@]}" "$@")
  d=$(diff <(cut -d' ' -f1,3- "$C/${M}_ref/carte_image.txt" 2>/dev/null) <(cut -d' ' -f1,3- "$C/${M}_$n/carte_image.txt" 2>/dev/null) | grep -c '^[<>]')
  x=$(cat "$C/${M}_$n"/ext_*.bin 2>/dev/null | md5sum | cut -c1-8)
  echo "$* | $r | ext=$x | carte_diff=$d" >> "$S"
  rm -rf "$C/${M}_$n"/roms_* "$C/${M}_$n"/ext_*.bin "$C/${M}_$n"/banques_hx 2>/dev/null
}
[ -f "$C/${M}_ref/carte_image.txt" ] || un ref
for kv in "$@"; do un "$(echo "$kv" | tr '=' '_' | sed 's/_0$//')" "$kv"; done
echo FIN >> "$S"
