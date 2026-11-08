#!/bin/sh
# lance_region.sh STG REGION : sonde_region.lua (= sonde de phase 1 + code de région forcé dans $FF8090) ;
# lanceur commun (agent decors_restes), dossiers propres et temporaires, jamais -state.
D=${SONDE_DIR:-$(dirname "$(readlink -f "$0")")}
STG=$1; R=$2; N=r${R}_stg$1
T=$(mktemp -d ${TMPDIR:-/tmp}/sfa2r_mame_XXXX)
mkdir -p $D/snap_region/$N $D/out_region
cd $D && STG=$STG REGION=$R OUT=$D/out_region/$N HSFA_AGENT=decors_restes nice -n 19 ${HSFA_WORKSPACE}/work/outils/lance_emu --agent decors_restes -- timeout ${TMAX:-900} \
  /usr/games/mame sfa2u -rompath ${HSFA_WORKSPACE}/work/carto_sfa2/roms \
  -nvram_directory $T/nv -cfg_directory $T/cfg -state_directory $T/sta -snapshot_directory $D/snap_region/$N \
  -video none -sound none -nothrottle -skip_gameinfo -autoboot_script $D/lua/${LUA:-sonde_region.lua}
rm -rf $T
