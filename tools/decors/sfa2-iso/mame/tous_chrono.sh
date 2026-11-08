#!/bin/sh
# tous_chrono.sh : anim2.sh sur les 18 décors, 3 voies (au plus 3 MAME, lanceur commun)
cd "$(dirname "$(readlink -f "$0")")"
voie() { for s in "$@"; do ./anim2.sh $s > out_chrono/run$s.txt 2>&1; done; }
mkdir -p out_chrono; rm -f out_chrono/tous.fini
voie 00 06 0C 12 18 1E &
voie 02 08 0E 14 1A 20 &
voie 04 0A 10 16 1C 22 &
wait
echo FINI > out_chrono/tous.fini
