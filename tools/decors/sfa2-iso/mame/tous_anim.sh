#!/bin/sh
cd "$(dirname "$(readlink -f "$0")")"
voie() { for s in "$@"; do ./lance_anim.sh $s > out_anim/run$s.txt 2>&1; done; }
mkdir -p out_anim
voie 00 06 0C 12 18 1E &
voie 02 08 0E 14 1A 20 &
voie 04 0A 10 16 1C 22 &
wait
echo FINI > out_anim/tous.fini
