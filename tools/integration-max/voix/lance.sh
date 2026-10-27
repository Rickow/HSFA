#!/bin/bash
# lance.sh <dossier_rom_son> <journal> [options MAME...] : injection voix.lua (programme muet) sur le fork sfa3hx,
# ROM son = HSFA_SON=<dossier_rom_son> (hx3.*). nvram/cfg dans ce dossier ; jamais -state.
D=${HSFA_WORKSPACE}/work/agent_voix_max
export HSFA_SON=$1; export OUT=$2; shift 2
NV=$D/nvram/$(basename $OUT .txt); rm -rf $NV; mkdir -p $NV $D/cfg
cd $D
BANC_DIR=${HSFA_WORKSPACE}/work/agent_son_ro5/banc_ro5/ exec nice -n 19 ${HSFA_WORKSPACE}/mame-fork/mame/cps2f sfa3hx \
  -rompath $D/rp -nvram_directory $NV -cfg_directory $D/cfg -snapshot_directory $D/nvram -video none -sound none \
  -nothrottle -skip_gameinfo -autoboot_script $D/${LUA:-voix.lua} "$@"
