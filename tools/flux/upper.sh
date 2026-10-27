#!/bin/bash
# upper.sh <nom> [options MAME] : Upper (ro5, work/mame_ro5/roms_fork) sur la copie du fork avec lecteur de flux.
# Variables du banc comme scripts/untranspile/nonreg_ro5.sh ; + PERSO, PERSO2, VS, MODE, MODE_ADR, NF, WAVF, HSFA_FLUX...
# Sorties : essais/<nom>.txt (tournee), <nom>.son (commandes), <nom>.flux (decisions du lecteur), nv_<nom>/, cfg_<nom>/.
D=${HSFA_WORKSPACE}/work/agent_flux; W5=${HSFA_WORKSPACE}/work/mame_ro5; N=$1; shift
rm -rf $D/essais/nv_$N $D/essais/cfg_$N $D/essais/snap_$N; mkdir -p $D/essais/nv_$N $D/essais/cfg_$N $D/essais/snap_$N
cd ${HSFA_WORKSPACE}/work/mame
export HSFA_SON=${HSFA_SON-${HSFA_WORKSPACE}/work/agent_son_ro5/hybride/roms_hybride}
export HSFA_YDATA=${HSFA_YDATA-${HSFA_WORKSPACE}/iso/SFA_Anthology_AllUnlocked_WORK.iso} HSFA_FLUX_TABLE=${HSFA_FLUX_TABLE-$D/hsfa_flux_table.txt}
HSFA_FLUX_LOG=$D/essais/$N.flux OUTSON=$D/essais/$N.son OUT=$D/essais/$N.txt \
BANC_COMMUN=351 HSFA_PLANS=300,340,3a0 HSFA_GFX=$W5/hsfa_gfx.bin,$W5/hsfa_plans.bin@3000000 BANC_BANQUES=$W5/banques_hx/ \
BANC_PTR_ANIM=FF40BC BANC_GFX_INTRO=456 BANC_DIR=$W5/ nice -n 19 ${CPS2F:-$D/mame-fork-flux/cps2f} sfa3hx \
  -rompath $W5/roms_fork -nvram_directory $D/essais/nv_$N -cfg_directory $D/essais/cfg_$N -snapshot_directory $D/essais/snap_$N \
  -video none -sound none -nothrottle -skip_gameinfo -autoboot_script $D/lua/flux_journal.lua "$@" > $D/essais/$N.mame.txt 2>&1
