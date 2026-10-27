#!/bin/bash
# Upper (fige/ro5) avec un script Lua quelconque (enveloppes lire.lua, couv_images.lua...). Usage : lance_upper_lua.sh NOM "VARS" NF LUA
H=${HSFA_WORKSPACE}; W5=$H/work/mame_ro5; G=$H/work/greffe_arcade
nom=$1; vars=$2; nf=$3; LUA=$4; D=$G/traces/$nom; rm -rf $D; mkdir -p $D
cd $H/work/mame
env $vars BANC_COMMUN=351 NF=$nf HSFA_PLANS=300,340,3a0 HSFA_GFX=$W5/hsfa_gfx.bin,$W5/hsfa_plans.bin@3000000 \
  BANC_BANQUES=$W5/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_GFX_INTRO=456 BANC_DIR=$G/fige/ro5/ OUT=$D/journal.txt \
  timeout ${TMAX:-3600} nice -n 19 $H/mame-fork/mame/cps2f sfa3hx -rompath $G/fige/ro5/roms_fork -video none -sound none -nothrottle \
  -skip_gameinfo -nvram_directory $D/nv -cfg_directory $D/cfg -snapshot_directory $D/snap -autoboot_script $LUA > $D/mame.log 2>&1
echo "$nom termine : $(tail -1 $D/journal.txt)"
