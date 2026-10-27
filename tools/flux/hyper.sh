#!/bin/bash
# hyper.sh <nom> [options MAME] : Hyper (ro9, work/mame_ro9/roms_fork) sur la copie du fork avec lecteur de flux,
# scenario tournee_hyper.lua (agent_hyper_etats ; variables LISTE, MODEJEU, NF, SNAPS...) sous flux_journal.lua.
# Modele : agent_hyper_etats/lance.sh. Son : ROM hybride (HSFA_SON) + flux (HSFA_YDATA, HSFA_FLUX_TABLE, HSFA_FLUX).
D=${HSFA_WORKSPACE}/work/agent_flux; W=${HSFA_WORKSPACE}/work/mame_ro9; N=$1; shift
rm -rf $D/essais/nv_$N $D/essais/cfg_$N $D/essais/snap_$N; mkdir -p $D/essais/nv_$N $D/essais/cfg_$N $D/essais/snap_$N
cd ${HSFA_WORKSPACE}/work/mame
export HSFA_SON=${HSFA_SON-${HSFA_WORKSPACE}/work/agent_son_ro5/hybride/roms_hybride}
export HSFA_YDATA=${HSFA_YDATA-${HSFA_WORKSPACE}/iso/SFA_Anthology_AllUnlocked_WORK.iso} HSFA_FLUX_TABLE=${HSFA_FLUX_TABLE-$D/hsfa_flux_table.txt}
SCENARIO=${HSFA_WORKSPACE}/work/agent_hyper_etats/lua/tournee_hyper.lua \
HSFA_FLUX_LOG=$D/essais/$N.flux OUTSON=$D/essais/$N.son OUT=$D/essais/$N.txt BANC_COMMUN=545 HSFA_PLANS=300,340,3a0 \
HSFA_GFX=$W/hsfa_gfx.bin,$W/hsfa_plans.bin@3000000 BANC_BANQUES=$W/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_DIR=$W/ \
nice -n 19 ${CPS2F:-$D/mame-fork-flux/cps2f} sfa3hx -rompath $W/roms_fork -nvram_directory $D/essais/nv_$N \
  -cfg_directory $D/essais/cfg_$N -snapshot_directory $D/essais/snap_$N -video none -sound none -nothrottle -skip_gameinfo \
  -autoboot_script $D/lua/flux_journal.lua "$@" > $D/essais/$N.mame.txt 2>&1
