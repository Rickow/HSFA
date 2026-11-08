#!/bin/sh
# anim2.sh STG : chronologie des animations du décor STG sous MAME (sfa2u, oracle local), lua/anim_sfa2.lua ;
# lanceur commun (agent decors_sfa2), dossiers temporaires, jamais -state. Sortie : out_chrono/stgSTG_chrono.txt
D=${SONDE_DIR:-$(dirname "$(readlink -f "$0")")}; STG=$1; N=stg$1
T=$(mktemp -d ${TMPDIR:-/tmp}/sfa2a_mame_XXXX)
mkdir -p $D/out_chrono
cd $D && STG=$STG OUT=$D/out_chrono/$N HSFA_AGENT=decors_sfa2 ${HSFA_WORKSPACE}/work/outils/lance_emu --agent decors_sfa2 -- timeout ${TMAX:-1500} \
  /usr/games/mame sfa2u -rompath ${HSFA_WORKSPACE}/work/carto_sfa2/roms \
  -nvram_directory $T/nv -cfg_directory $T/cfg -state_directory $T/sta -snapshot_directory $T/snap \
  -video none -sound none -nothrottle -skip_gameinfo -autoboot_script $D/lua/anim_sfa2.lua
rm -rf $T
