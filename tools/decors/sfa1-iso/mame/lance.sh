#!/bin/sh
# lance.sh STG : sonde MAME 0.285 de sfa (arcade SFA1, oracle local) sur le decor STG (= $FFAE00 hexa) ;
# par le lanceur commun (HSFA_AGENT=decors_sfa1), dossiers nvram/cfg/etat propres et temporaires, sans -state.
D=${SONDE_DIR:-$(dirname "$(readlink -f "$0")")}
STG=$1; N=stg$1
T=$(mktemp -d ${TMPDIR:-/tmp}/sfa1d_mame_XXXX)
mkdir -p $D/snap/$N $D/out
cd $D && STG=$STG OUT=$D/out/$N HSFA_AGENT=decors_sfa1 ${HSFA_WORKSPACE}/work/outils/lance_emu --agent decors_sfa1 -- \
  /usr/games/mame sfa -rompath ${HSFA_WORKSPACE}/work/banc_coups/roms_arc \
  -nvram_directory $T/nv -cfg_directory $T/cfg -state_directory $T/sta -snapshot_directory $D/snap/$N \
  -video none -sound none -nothrottle -skip_gameinfo -autoboot_script $D/lua/sonde.lua
rm -rf $T
