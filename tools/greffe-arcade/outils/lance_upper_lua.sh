#!/bin/bash
# (e31 reprise) via lance_emu (HSFA_AGENT, empreinte)
# Upper (fige/ro5) avec un script Lua quelconque (enveloppes lire.lua, couv_images.lua...). Usage : lance_upper_lua.sh NOM "VARS" NF LUA
# UPPER_ORACLE (15/11, §234) : dossier de l'Upper sous greffe_arcade (defaut fige/ro5 = traducteur v153, celui des releves
# de la greffe) ; les lanceurs d'oracle des fins (oracle_upper.sh, compare_fin.sh, sonde_fin.sh, scripts_upper.sh) passent
# fige/ro5_v161 (traducteur v161 = Upper publie ; fige/ro5 a 19 echanges EXG Dx,Dy casses).
H=${HSFA_WORKSPACE}; W5=$H/work/mame_ro5; G=$H/work/greffe_arcade; U=$G/${UPPER_ORACLE:-fige/ro5}
nom=$1; vars=$2; nf=$3; LUA=$4; D=$G/traces/$nom; rm -rf $D; mkdir -p $D
cd $H/work/mame
env $vars BANC_COMMUN=351 NF=$nf HSFA_PLANS=300,340,3a0 HSFA_GFX=$W5/hsfa_gfx.bin,$W5/hsfa_plans.bin@3000000 \
  BANC_BANQUES=$W5/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_GFX_INTRO=456 BANC_DIR=$U/ OUT=$D/journal.txt \
  HSFA_AGENT=${HSFA_AGENT:-greffe} $H/work/outils/lance_emu --empreinte $D/empreinte.txt -- \
  timeout ${TMAX:-3600} nice -n 19 $H/mame-fork/mame/cps2f sfa3hx -rompath $U/roms_fork -video none -sound none -nothrottle \
  -skip_gameinfo -nvram_directory $D/nv -cfg_directory $D/cfg -snapshot_directory $D/snap -autoboot_script $LUA > $D/mame.log 2>&1
c=$?; [ $c = 86 ] && { echo "$nom : ARRÊT, empreinte différente ($D/empreinte.txt)" >&2; exit 86; }   # (e31 reprise : via lance_emu)
echo "$nom termine : $(tail -1 $D/journal.txt)"
