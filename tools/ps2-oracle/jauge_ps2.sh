#!/bin/bash
# jauge_ps2.sh PREFIXE ADR valeurs... : pour chaque valeur (hexa), écrit le mot ADR (hexa, PINE) en continu ~3 s et
# prend une capture à 1,5 s -> shots/PREFIXE_<valeur>.png. Écritures permises (décision du 07/11) : vie de l'adversaire
# et niveau de jauge, pour des essais, sur un PCSX2 lancé par lance_ps2.sh seulement.
ICI=$(dirname "$(readlink -f "$0")"); . "$ICI/env_ps2.sh"
PRE=$1; A=$2; shift 2
for v in "$@"; do
  python3 - "$ICI" "$A" "$v" <<'PY' &
import sys, time
sys.path.insert(0, sys.argv[1]); import pine
a, v = int(sys.argv[2], 16), int(sys.argv[3], 16); t = time.time()
while time.time() - t < 3.2:
    pine.w(16, a, v); time.sleep(0.004)
PY
  sleep 1.6; "$ICI/shot.sh" "${PRE}_$v" > /dev/null; wait
done
