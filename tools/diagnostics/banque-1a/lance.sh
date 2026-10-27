#!/bin/bash
# lance.sh arc|ro5 PERSO [NF] : partie Arcade jusqu'a la fin + releve des acteurs (copies des ROM dans ce dossier)
A=${HSFA_WORKSPACE}/work/agent_banque_1a; M=$1; p=$2; nf=${3:-90000}
T=$(mktemp -d $A/tmp_${M}_${p}_XXXX)
if [ $M = arc ]; then
  REF=1 PERSO=$p FORCE="${FORCE-Lff8540=ffffffff}" NF=$nf OUT=$A/out_${M}_$p.txt RELEVE=$A/releve_${M}_$p.txt \
    nice -n 19 mame sfa3ud -rompath $A/roms_arc -video none -sound none -nothrottle -skip_gameinfo \
    -nvram_directory $T/nv -cfg_directory $T/cfg -snapshot_directory $T/snap -autoboot_script $A/releve_fin.lua >$T/log 2>&1
else
  B=$A/banc_ro5
  BANC_COMMUN=351 PERSO=$p FORCE="${FORCE-}" NF=$nf HSFA_PLANS=300,340,3a0 \
    HSFA_GFX=$B/hsfa_gfx.bin,$B/hsfa_plans.bin@3000000 BANC_BANQUES=$B/banques_hx/ BANC_PTR_ANIM=FF40BC \
    BANC_GFX_INTRO=456 BANC_DIR=$B/ OUT=$A/out_${M}_$p.txt RELEVE=$A/releve_${M}_$p.txt \
    nice -n 19 ${HSFA_WORKSPACE}/mame-fork/mame/cps2f sfa3hx -rompath $B/roms_fork -video none -sound none -nothrottle \
    -skip_gameinfo -nvram_directory $T/nv -cfg_directory $T/cfg -snapshot_directory $T/snap \
    -autoboot_script $A/releve_fin.lua >$T/log 2>&1
fi
echo "fini $M $p : $(tail -1 $A/out_${M}_$p.txt)"
