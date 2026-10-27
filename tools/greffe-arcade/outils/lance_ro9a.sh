#!/bin/bash
# Partie Arcade dans Hyper augmente (fork sfa3hx). Usage : lance_ro9a.sh CONSTRUCTION TRACE "VARS..." NF [script.lua]
# CONSTRUCTION = dossier constructions/<nom> (ROM dans b9/roms_ro9/sfa3ud, blocs ext dans b9/) ; graphismes d'Hyper
# (work/mame_ro9 : hsfa_gfx.bin, hsfa_plans.bin, banques_hx) en lecture seule. nvram/cfg propres a la trace.
H=${HSFA_WORKSPACE}; W9=$H/work/mame_ro9; G=$H/work/greffe_arcade
C=$G/constructions/$1; nom=$2; vars=$3; nf=$4; LUA=${5:-$G/lua/tournee_arcade.lua}
[ -d "$C/b9" ] || { echo "construction absente : $C" >&2; exit 1; }
case "$nom" in *=*|*" "*) echo "nom de trace invalide : $nom" >&2; exit 1;; esac
D=$G/traces/$nom; rm -rf $D; mkdir -p $D
mkdir -p $C/roms_fork; ln -sfn $C/b9/roms_ro9/sfa3ud $C/roms_fork/sfa3hx
md5sum $C/b9/roms_ro9/sfa3ud/sz3ud.03c > $D/md5_rom.txt
cd $H/work/mame
env $vars NF=$nf OUT=$D/journal.txt BANC_COMMUN=545 HSFA_PLANS=300,340,3a0 HSFA_GFX=$W9/hsfa_gfx.bin,$W9/hsfa_plans.bin@3000000$( [ "${PLANS_UPPER:-1}" = 1 ] && echo ",$H/work/mame_ro5/hsfa_plans.bin@4000000") \
  BANC_BANQUES=$( [ -d $C/banques_hx ] && echo $C/banques_hx/ || echo $W9/banques_hx/ ) BANC_PTR_ANIM=FF40BC BANC_DIR=$C/b9/ \
  timeout ${TMAX:-1800} nice -n 19 $H/mame-fork/mame/cps2f sfa3hx -rompath $C/roms_fork -video none -sound none -nothrottle \
  -skip_gameinfo -nvram_directory $D/nv -cfg_directory $D/cfg -snapshot_directory $D/snap \
  -autoboot_script $LUA > $D/mame.log 2>&1
echo "$nom termine : $(tail -1 $D/journal.txt)"
