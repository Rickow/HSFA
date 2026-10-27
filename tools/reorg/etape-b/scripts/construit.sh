#!/bin/bash
# (etape B) RECONSTRUCTION des variantes dans work/agent_reorg_B/ avec la copie du traducteur (untranspile/) :
#   construit.sh <module ro3|ro5|ro9> <dossier> [VAR=val ...]   ex. construit.sh ro3 mame1c RELOGE_CODE=1 RELOGE_NATIF=1 RELOGE_RAM=1
# Cree roms_fork/sfa3hx (ro5/ro9) et copie ext_b00000.bin (ro3, present dans work/mame) pour reproduire le banc partage.
H=${HSFA_WORKSPACE}; B=$H/work/agent_reorg_B; m=${1:?module}; d=${2:?dossier}; shift 2
[[ $d = /* ]] || d=$B/$d; mkdir -p $d
E=""; if [ $m = ro9 ]; then E="EXTRACT_MODULES=$H/work/modules_son HSFA_SON_DONNEES=$H/work/modules_son/son_donnees_ro9.bin"; fi
cd $B/untranspile && env $E "$@" MODULE=$m TRAVAIL=$d nice -n 19 python3 mame_test.py > $d/build.log 2>&1
grep -E "etape|reset ->|Error|assert" $d/build.log
rm -f $d/dis_*.txt                                   # cache de prof_an.py (desassemblage) perime
if [ $m = ro3 ]; then cp $H/work/mame/ext_b00000.bin $d/ 2>/dev/null; md5sum $d/roms_tr/sfa3ud/sz3ud.03c
else mkdir -p $d/roms_fork; ln -sfn ../roms_$m/sfa3ud $d/roms_fork/sfa3hx; md5sum $d/roms_$m/sfa3ud/sz3ud.03c; fi
