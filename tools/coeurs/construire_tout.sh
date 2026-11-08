#!/bin/bash
# (lots des cœurs, version du 09/11) arbres préparés dans LOT : fbneo (Linux), fbneo_win, fbneo_and, fbneo_r32, fbneo_r64,
# fbneo_rk, fbneo_x86 = libretro/FBNeo + chaîne patches/fbneo (README) ; journaux dans LOT/journaux, cœurs dans LOT/sortie.
# construire_tout.sh : les 12 coeurs + les 2 coeurs x86 de controle ; 3 chaines en parallele (nice 19)
L=${LOT:?LOT : dossier du lot}; export LOT=$L; O=$(dirname "$(readlink -f "$0")"); mkdir -p $L/journaux $L/sortie; J=$L/journaux; S=$L/sortie
arm() { for s in hsfa hsfaws; do ( time FBNEO=$L/$2 JOBS=3 bash $O/build_arm.sh $1 $s $3 ) > $J/$1_$s.log 2>&1; echo "$1 $s : code $? ; $(grep -a 'GLIBC maximale' $J/$1_$s.log | sed 's/.*: //') $(date +%T)"; done; }
( JOBS=4 bash $O/build_std.sh linux; JOBS=4 bash $O/build_std.sh windows; bash $O/build_std.sh android ) > $J/chaine_std.out 2>&1 &
( arm recalbox-armhf fbneo_r32 $S/recalbox/armhf; arm rocknix fbneo_rk $S/rocknix ) > $J/chaine_arm1.out 2>&1 &
( arm recalbox-aarch64 fbneo_r64 $S/recalbox/aarch64; JOBS=3 bash $O/build_std.sh x86arm ) > $J/chaine_arm2.out 2>&1 &
wait; echo fini $(date +%T)
