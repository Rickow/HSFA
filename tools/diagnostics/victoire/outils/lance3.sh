#!/bin/bash
# lance3.sh <nom> <ref|tr> [rompath] : SFA3 MAME standard (sfa3ud), tournee.lua (ou SCRIPT). Env : NF SNAPP SNAP0 PERSO SCRIPT BASE_LUA
V=${HSFA_WORKSPACE}/work/agent_victoire; N=$1; T=$V/essais/$N; rm -rf $T; mkdir -p $T/nv $T/cfg $T/snap
if [ "$2" = ref ]; then export REF=1; RP=${3:-${HSFA_WORKSPACE}/work/agent_bandeau_A/roms_ref}; else unset REF; RP=${3:-$V/mame3/roms_tr}; export BANC_DIR=${BANC_DIR:-$V/mame3/}; fi
cd $T
PERSO=${PERSO:-00} OUT=$T/tour.txt TOUT=$T/trace.txt timeout ${TMO:-1500} nice -n 19 mame sfa3ud -rompath $RP -video none -sound none -nothrottle -skip_gameinfo $XOPT \
  -nvram_directory $T/nv -cfg_directory $T/cfg -snapshot_directory $T/snap -autoboot_script ${SCRIPT:-${HSFA_WORKSPACE}/work/mame/tournee.lua} > $T/mame.txt 2>&1
rm -rf $T/nv $T/cfg
