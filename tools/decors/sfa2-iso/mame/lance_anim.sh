#!/bin/sh
# lance.sh STG : sonde MAME 0.285 de sfa2u (arcade SFA2, oracle local) sur le décor STG (= $FF8100 hexa) ;
# lanceur commun (HSFA_AGENT=decors_sfa2), dossiers nvram/cfg/état propres et temporaires, jamais -state.
D=${SONDE_DIR:-$(dirname "$(readlink -f "$0")")}
STG=$1; N=stg$1
T=$(mktemp -d ${TMPDIR:-/tmp}/sfa2d_mame_XXXX)
mkdir -p $D/out_anim
cd $D && STG=$STG OUT=$D/out_anim/$N ANIM=1 HSFA_AGENT=decors_sfa2 ${HSFA_WORKSPACE}/work/outils/lance_emu --agent decors_sfa2  -- timeout ${TMAX:-900} \
  /usr/games/mame sfa2u -rompath ${HSFA_WORKSPACE}/work/carto_sfa2/roms \
  -nvram_directory $T/nv -cfg_directory $T/cfg -state_directory $T/sta -snapshot_directory $T/snap \
  -video none -sound none -nothrottle -skip_gameinfo -autoboot_script $D/lua/sonde_sfa2.lua
rm -rf $T
