#!/bin/bash
# Bancs de la carte musique (hsfa_musique.h) avec les pilotes d'origine de SFA1 et SFA2.
#   1. test_carte : logique complete avec le Z80 de z80.h (demarrage, morceaux, changements, etats, fondus, pause) ;
#   2. test_zet   : meme carte avec le Z80 de FBNeo et la classe HsfaMusZet du coeur (extraite de cps_hsfa.cpp).
# Usage : lance_tests_carte.sh <sfa.zip> <sfa2.zip> [arbre FBNeo patche (patchs 1-10), pour test_zet] [dossier de travail]
# Aucune donnee de jeu dans le depot : les images sont faites depuis les zips par rendu_partitions.py.
set -e
ZIP1=${1:?sfa.zip}; ZIP2=${2:?sfa2.zip}; FB=$3; T=${4:-/tmp/hsfa_carte}
ICI=$(cd "$(dirname "$0")" && pwd); SH=$(dirname "$ICI"); DEP=$(cd "$SH/../.." && pwd)
mkdir -p "$T/img" "$T/paq"
python3 -I - "$SH" "$T/img" "$ZIP1" "$ZIP2" <<'PY'
import sys; sys.path.insert(0, sys.argv[1]); import rendu_partitions as R
R.depuis_zip("sfa", sys.argv[3], sys.argv[2]); R.depuis_zip("sfa2", sys.argv[4], sys.argv[2])
PY
( cd "$DEP/tools/fbneo-hsfa" && HSFA_PARTITIONS=1 HSFA_PILOTE_SFA1="$ZIP1" HSFA_PILOTE_SFA2="$ZIP2" HSFA_WORK="$T" python3 -I - "$T/paq" <<'PY'
import importlib.util, sys
s = importlib.util.spec_from_file_location("p", "paquet_fbneo.py"); p = importlib.util.module_from_spec(s); s.loader.exec_module(p)
d, t = p.membres_musique({"rejeu": True, "nom": "essai"})
open(sys.argv[1] + "/hsfa_musique.bin", "wb").write(d); open(sys.argv[1] + "/hsfa_musique_table.txt", "wb").write(t)
PY
)
g++ -O2 -std=c++11 -Wall -I "$SH" -I "$ICI" -o "$T/test_carte" "$ICI/test_carte.cpp"
"$T/test_carte" "$T/img" "$T" "$T/paq"
if [ -n "$FB" ]; then
  F="$FB/src"
  INC="-I$F/burn -I$F/burn/devices -I$F/burn/snd -I$F/cpu -I$F/cpu/z80 -I$F/burner -I$F/dep/generated -I$F/burner/libretro -I$F/burner/libretro/libretro-common/include -I$F/burn/drv/capcom -D__LIBRETRO__ -DLSB_FIRST -DUSE_SPEEDHACKS -std=gnu++98 -O2 -w"
  mkdir -p "$T/zet"; cd "$T/zet"
  for f in z80/z80 z80_intf z80/z80daisy z80/z80ctc z80/z80pio; do g++ $INC -c "$F/cpu/$f.cpp" -o "$(basename $f).o"; done
  g++ $INC -c "$ICI/stubs_fbneo.cpp" -o stubs.o
  awk '/^#define HSFA_MUS_CPU/,/^static HsfaMusZet \*HsfaMusProc = NULL;/' "$F/burn/drv/capcom/cps_hsfa.cpp" > zet_extrait.h
  g++ $INC -I. -o test_zet "$ICI/test_zet.cpp" z80.o z80_intf.o z80daisy.o z80ctc.o z80pio.o stubs.o
  ./test_zet "$T/img" "$T/paq" "$T/zet/zet_0041.raw"
fi
