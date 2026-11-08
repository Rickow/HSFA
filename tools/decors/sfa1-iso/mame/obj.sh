#!/bin/sh
# obj.sh STG [MODE] : sonde des POSITIONS de sprites de decor (lua/obj.lua) ; MODE = balai (defaut) | combat ;
# lanceur commun (agent decors_restes), nvram/cfg temporaires, sans -state. Sortie : out/stgXX[_combat]_pos.txt
D=${SONDE_DIR:-$(dirname "$(readlink -f "$0")")}; STG=$1; MODE=${2:-balai}
N=stg$1; [ "$MODE" = combat ] && N=stg$1_combat
mkdir -p ${TMPDIR:-/tmp}; T=$(mktemp -d ${TMPDIR:-/tmp}/sfa1r_mame_XXXX)
cd $D && STG=$STG MODE=$MODE OUT=$D/out/$N HSFA_AGENT=decors_restes ${HSFA_WORKSPACE}/work/outils/lance_emu --agent decors_restes -- \
  /usr/games/mame sfa -rompath ${HSFA_WORKSPACE}/work/banc_coups/roms_arc \
  -nvram_directory $T/nv -cfg_directory $T/cfg -state_directory $T/sta -snapshot_directory $T/snap \
  -video none -sound none -nothrottle -skip_gameinfo -autoboot_script $D/lua/obj.lua > $D/out/$N.objlog 2>&1
rm -rf $T
