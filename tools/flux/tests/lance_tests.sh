#!/bin/bash
# Banc du lecteur de flux Ogg Vorbis (hsfa_flux.h) : fabrique les flux de test (ffmpeg), compile, lance.
# Usage : tools/flux/tests/lance_tests.sh [dossier de travail, defaut /tmp/hsfa_fluxtest]
set -e
T=${1:-/tmp/hsfa_fluxtest}; ICI=$(cd "$(dirname "$0")" && pwd); FLUX=$(dirname "$ICI")
mkdir -p "$T"
python3 -I "$ICI/fabrique_flux_test.py" "$T/flux"
gcc -O2 -c -I "$FLUX" -o "$T/stb.o" "$ICI/stb_vorbis_impl.c" 2>/dev/null
g++ -O2 -Wall -DHSFA_FLUX_VORBIS -I "$FLUX" -o "$T/test_flux_vorbis" "$ICI/test_flux_vorbis.cpp" "$T/stb.o"
"$T/test_flux_vorbis" "$T/flux"
