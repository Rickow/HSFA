#!/bin/bash
# lance.sh arc|ro5 NOM [NF] : tournee Arcade (portraits.lua) ; variables : SNAP_A, SNAP_B, PERSO, LUA (script)
A=${HSFA_WORKSPACE}/work/agent_portraits; M=$1; N=$2; nf=${3:-6000}
O=$A/runs/${M}_$N; rm -rf $O; mkdir -p $O; T=$(mktemp -d $A/tmp_XXXX)
L=${LUA:-$A/lua/portraits.lua}
if [ $M = ro3 ]; then   # SFA3 traduit : MAME d'origine, banc par defaut (FF3E48, e254)
  B=$A/ro3
  NF=$nf OUT=$O/tournee.txt JOURNAL=$O/journal.txt BANC_BANQUES=$B/banques/ BANC_DIR=$B/ BANC_PTR_ANIM=FF3E48 \
    nice -n 19 mame sfa3ud -rompath $B/roms_tr -video none -sound none -nothrottle -skip_gameinfo \
    -nvram_directory $T/nv -cfg_directory $T/cfg -snapshot_directory $O/snap -autoboot_script $L >$O/log 2>&1
elif [ $M = arc ]; then
  REF=1 NF=$nf OUT=$O/tournee.txt JOURNAL=$O/journal.txt \
    nice -n 19 mame sfa3ud -rompath $A/arc/roms -video none -sound none -nothrottle -skip_gameinfo \
    -nvram_directory $T/nv -cfg_directory $T/cfg -snapshot_directory $O/snap -autoboot_script $L >$O/log 2>&1
else
  B=$A/$M
  BANC_COMMUN=${BANC_COMMUN:-351} NF=$nf HSFA_PLANS=${HSFA_PLANS:-300,340,3a0} \
    HSFA_GFX=$B/hsfa_gfx.bin,$B/hsfa_plans.bin@3000000 BANC_BANQUES=$B/banques_hx/ BANC_PTR_ANIM=${BANC_PTR_ANIM:-FF40BC} \
    BANC_GFX_INTRO=456 BANC_DIR=$B/ OUT=$O/tournee.txt JOURNAL=$O/journal.txt \
    nice -n 19 ${HSFA_WORKSPACE}/mame-fork/mame/cps2f sfa3hx -rompath $B/roms_fork -video none -sound none -nothrottle \
    -skip_gameinfo -nvram_directory $T/nv -cfg_directory $T/cfg -snapshot_directory $O/snap \
    -autoboot_script $L >$O/log 2>&1
fi
rm -rf $T; echo "fini $M $N : $(tail -1 $O/tournee.txt)"
