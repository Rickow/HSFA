#!/bin/sh
# lance_defil.sh STG NOM [POKE] : sonde_defil.lua (sonde de phase 1 + RAM des défilements à chaque image), HOLD=${HOLD:-1500} ;
# lanceur commun (agent decors_restes), dossiers propres et temporaires, jamais -state. Sorties : out_defil/NOM_*.
D=${SONDE_DIR:-$(dirname "$(readlink -f "$0")")}
STG=$1; N=$2
T=$(mktemp -d ${TMPDIR:-/tmp}/sfa2f_mame_XXXX)
mkdir -p $D/snap_defil/$N $D/out_defil
cd $D && STG=$STG POKE="$3" HOLD=${HOLD:-1500} OUT=$D/out_defil/$N HSFA_AGENT=decors_restes nice -n 19 ${HSFA_WORKSPACE}/work/outils/lance_emu --agent decors_restes -- timeout ${TMAX:-1500} \
  /usr/games/mame sfa2u -rompath ${HSFA_WORKSPACE}/work/carto_sfa2/roms \
  -nvram_directory $T/nv -cfg_directory $T/cfg -state_directory $T/sta -snapshot_directory $D/snap_defil/$N \
  -video none -sound none -nothrottle -skip_gameinfo -autoboot_script $D/lua/${LUA:-sonde_defil.lua}
rm -rf $T
