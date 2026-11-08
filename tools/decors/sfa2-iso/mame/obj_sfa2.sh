#!/bin/sh
# obj_sfa2.sh STG : sonde des POSITIONS de sprites de decor au pixel (lua/obj_sfa2.lua, sfa2u, oracle local) ;
# lanceur commun (agent decors_restes), dossiers temporaires, jamais -state. Sortie : out_pos/stgSTG_pos.txt
D=${SONDE_DIR:-$(dirname "$(readlink -f "$0")")}; STG=$1; N=stg$1
mkdir -p ${TMPDIR:-/tmp} $D/out_pos; T=$(mktemp -d ${TMPDIR:-/tmp}/sfa2r_mame_XXXX)
cd $D && STG=$STG OUT=$D/out_pos/$N HSFA_AGENT=decors_restes ${HSFA_WORKSPACE}/work/outils/lance_emu --agent decors_restes -- timeout ${TMAX:-1500} \
  /usr/games/mame sfa2u -rompath ${HSFA_WORKSPACE}/work/carto_sfa2/roms \
  -nvram_directory $T/nv -cfg_directory $T/cfg -state_directory $T/sta -snapshot_directory $T/snap \
  -video none -sound none -nothrottle -skip_gameinfo -autoboot_script $D/lua/obj_sfa2.lua > $D/out_pos/$N.run 2>&1
rm -rf $T
