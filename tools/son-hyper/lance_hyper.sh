#!/bin/bash
# lance_hyper.sh <nom> [options MAME] : Hyper (ro9, work/mame_ro9/roms_fork, LECTURE SEULE) au fork sfa3hx avec la ROM son
# propre a Hyper (HSFA_SON, defaut roms_hyper/) et la redirection des voix par version (lua/redirection.lua, table REDIR,
# defaut roms_hyper/redirection.txt ; REDIR= vide -> aucune redirection), scenario tournee_hyper.lua (agent_hyper_etats ;
# variables LISTE, MODEJEU, NF...). Modele : agent_hyper_etats/lance.sh. nvram/cfg propres ; jamais -state.
# Sorties : essais/<nom>.son (commandes : code d'origine -> code joue, J1, J2), <nom>.txt (journal tournee), <nom>.wav (WAVF).
D=${HSFA_WORKSPACE}/work/agent_son_hyper_rom; W=${HSFA_WORKSPACE}/work/mame_ro9; RP9=${RP9:-$W/roms_fork}; BANC9=${BANC9:-$W/}; N=$1; shift
rm -rf $D/essais/nv_$N $D/essais/cfg_$N $D/essais/snap_$N; mkdir -p $D/essais/nv_$N $D/essais/cfg_$N $D/essais/snap_$N
cd ${HSFA_WORKSPACE}/work/mame
export HSFA_SON=${HSFA_SON-$D/roms_hyper}
export REDIR=${REDIR-$HSFA_SON/redirection.txt}
SCENARIO=${HSFA_WORKSPACE}/work/agent_hyper_etats/lua/tournee_hyper.lua \
OUTSON=$D/essais/$N.son OUT=$D/essais/$N.txt BANC_COMMUN=545 HSFA_PLANS=300,340,3a0 \
HSFA_GFX=$W/hsfa_gfx.bin,$W/hsfa_plans.bin@3000000 BANC_BANQUES=$W/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_DIR=$BANC9 \
nice -n 19 ${CPS2F:-${HSFA_WORKSPACE}/mame-fork/mame/cps2f} sfa3hx -rompath $RP9 -nvram_directory $D/essais/nv_$N \
  -cfg_directory $D/essais/cfg_$N -snapshot_directory $D/essais/snap_$N -video none -sound none -nothrottle -skip_gameinfo \
  -autoboot_script $D/lua/redirection.lua "$@" > $D/essais/$N.mame.txt 2>&1
