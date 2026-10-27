#!/bin/bash
# lance.sh NOM DOSSIER SCRIPT.lua [VAR=val ...] : MAME sfa3ud standard sur DOSSIER/roms_tr (DOSSIER=ref : arcade),
# nvram/cfg propres a ce lancement (supprimes a la fin), nice 19 ; journal MAME dans logs/NOM.log
B=${HSFA_WORKSPACE}/work/agent_reorg_B
nom=$1; W=$2; s=$3; shift 3
if [ "$W" = ref ]; then RP=${HSFA_WORKSPACE}/work/mame/roms; BD=${HSFA_WORKSPACE}/work/mame/; else RP=$W/roms_tr; BD=$W/; fi
T=$(mktemp -d -p $B/tmp ${nom}_XXXX)
cd $B
env BANC_DIR=$BD "$@" timeout ${DUREE:-7200} nice -n 19 mame sfa3ud -rompath $RP -video none -sound none -nothrottle -skip_gameinfo \
  -nvram_directory $T/nv -cfg_directory $T/cfg -snapshot_directory $T/snap -autoboot_script $s > $B/logs/$nom.log 2>&1
echo "$nom termine ($?)" >> $B/logs/$nom.log; rm -rf $T
