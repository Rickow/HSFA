#!/bin/bash
# lance3.sh <nom> <ref|tr> [rompath] : SFA3 standard MAME (sfa3ud), tournee + journal des registres. Env : NF SNAPP SNAP0 REG0 REG1 PERSO BANC_DIR
B=${HSFA_WORKSPACE}/work/agent_bandeau_A; N=$1; T=$B/essais/$N; rm -rf $T; mkdir -p $T/nv $T/cfg $T/snap
if [ "$2" = ref ]; then export REF=1; RP=${3:-$B/roms_ref}; else unset REF; RP=${3:-$B/roms_tr3}; fi
cd ${HSFA_WORKSPACE}/work/mame
PERSO=${PERSO:-00} OUT=$T/tour.txt REGOUT=$T/regs.txt timeout ${TMO:-1500} nice -n 19 mame sfa3ud -rompath $RP -video none -sound none -nothrottle -skip_gameinfo \
  -nvram_directory $T/nv -cfg_directory $T/cfg -snapshot_directory $T/snap -autoboot_script ${SCRIPT:-$B/lua/trace_a.lua} > $T/mame.txt 2>&1
rm -rf $T/nv $T/cfg
