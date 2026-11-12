#!/bin/bash
# construit.sh NAME [VAR=val ...] -- one translator build (no emulator), for the switch trials of the translator review
# (review E8, 11/11/2026, docs/rapports/reviews/). Runs mame_test.py of a RUNNABLE copy of the translator under nice 19
# and writes the build to $SORTIE/constr/NAME (build.log, carte_image.txt, roms_*/, ext_*.bin).
# Prints one line: "NAME code=<exit code> <md5 of all program ROMs> <md5[:8] of sz3ud.03c>".
# Environment:
#   HSFA_TRAD   folder of a runnable copy of the translator (src/hsfa with its workspace paths resolved, e.g. the
#               copy made by hsfa_build.py or <workspace>/scripts/untranspile); it is not modified
#   SORTIE      output folder (default: ./revue_interrupteurs)
#   MODULE      ro3 (default), ro5 or ro9; for ro9 also pass EXTRACT_MODULES=... HSFA_SON_DONNEES=... as VAR=val
# The animation cache is redirected to $SORTIE/constr/_anims.
set -u
N=${1:?usage: construit.sh NAME [VAR=val ...]}; shift
TRAD=${HSFA_TRAD:?HSFA_TRAD: folder of a runnable copy of the translator}
S=$(mkdir -p "${SORTIE:-./revue_interrupteurs}" && cd "${SORTIE:-./revue_interrupteurs}" && pwd)
T=$S/constr/$N; rm -rf "${T:?}"; mkdir -p "$T"
unset EXTRACT_MODULES HSFA_SON_DONNEES
for kv in "$@"; do export "$kv"; done
export MODULE=${MODULE:-ro3} TRAVAIL=$T PYTHONDONTWRITEBYTECODE=1 ANIM_CACHE=$S/constr/_anims
(cd "$TRAD" && nice -n 19 python3 mame_test.py) > "$T/build.log" 2>&1
c=$?
echo "$N code=$c $(cat "$T"/roms_*/sfa3ud/* 2>/dev/null | md5sum | cut -c1-32) $(md5sum "$T"/roms_*/sfa3ud/sz3ud.03c 2>/dev/null | cut -c1-8)"
