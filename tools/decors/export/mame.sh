#!/bin/sh
# lance MAME (ROM arcade d'origine) avec un script Lua ; dossiers propres a decors_ws
D=${HSFA_WORKSPACE}/work/decors_ws
S=$1; shift
cd $D && exec nice -n 19 mame sfa3ud -rompath ${HSFA_WORKSPACE}/work/mame/roms \
  -nvram_directory $D/nvram -cfg_directory $D/cfg -state_directory $D/sta -snapshot_directory ${SNAPD:-$D/snap} \
  -video none -sound none -nothrottle -skip_gameinfo -autoboot_script $S "$@"
