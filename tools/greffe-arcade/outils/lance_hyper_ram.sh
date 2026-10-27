#!/bin/bash
# Carte dynamique de la RAM d'Hyper (mame_ro9 en LECTURE) : lance_hyper_ram.sh NOM "VARS..."
H=${HSFA_WORKSPACE}; W=$H/work/mame_ro9; G=$H/work/greffe_arcade
N=$1; vars=$2; D=$G/traces/h_$N; rm -rf $D; mkdir -p $D
cd $H/work/mame
env $vars OUT=$D/journal.txt RAMOUT=$D/ram.txt COUV=$D/couv.txt BANC_COMMUN=545 HSFA_PLANS=300,340,3a0 \
HSFA_GFX=$W/hsfa_gfx.bin,$W/hsfa_plans.bin@3000000 BANC_BANQUES=$W/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_DIR=$G/fige/ro9/ \
timeout 5400 nice -n 19 $H/mame-fork/mame/cps2f sfa3hx -rompath $G/fige/ro9/roms_fork -nvram_directory $D/nv \
  -cfg_directory $D/cfg -snapshot_directory $D/snap -video none -sound none -nothrottle -skip_gameinfo \
  -autoboot_script $G/lua/ram_hyper.lua > $D/mame.log 2>&1
echo "$N termine : $(tail -1 $D/journal.txt)"
