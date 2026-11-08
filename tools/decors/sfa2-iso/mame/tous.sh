#!/bin/sh
# tous.sh : sonde des 18 décors de persos (3 MAME au plus en parallèle, par le lanceur commun)
cd "$(dirname "$(readlink -f "$0")")"
voie() { for s in "$@"; do rm -rf snap/stg$s out/stg${s}*; ./lance.sh $s > out/run$s.txt 2>&1; done; }
voie 00 06 0C 12 18 1E &
voie 02 08 0E 14 1A 20 &
voie 04 0A 10 16 1C 22 &
wait
echo FINI > out/tous.fini
