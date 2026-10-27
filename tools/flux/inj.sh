#!/bin/bash
# inj.sh <nom> : programme 68K muet (rp_inj d'agent_son_ro5/hybride) + inj_flux.lua ; variables PROG, WAV, NF, HSFA_SON,
# HSFA_YDATA, HSFA_FLUX_TABLE, HSFA_FLUX ; CPS2F = binaire (defaut : copie de travail mame-fork-flux).
D=${HSFA_WORKSPACE}/work/agent_flux; N=$1; shift
export OUT=$D/essais/$N.txt
rm -rf $D/essais/nv_$N; mkdir -p $D/essais/nv_$N $D/essais/cfg
cd $D
BANC_DIR=${HSFA_WORKSPACE}/work/agent_son_ro5/banc_ro5/ nice -n 19 ${CPS2F:-$D/mame-fork-flux/cps2f} sfa3hx \
  -rompath $D/rp_inj -nvram_directory $D/essais/nv_$N -cfg_directory $D/essais/cfg \
  -snapshot_directory $D/essais/snap -video none -sound none -nothrottle -skip_gameinfo \
  -autoboot_script $D/lua/inj_flux.lua "$@" > $D/essais/$N.mame.txt 2>&1
