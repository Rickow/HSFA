#!/bin/bash
# (etape B) NON-REGRESSION d'Upper (copie de scripts/untranspile/nonreg_ro5.sh) sur un dossier de l'etape B :
#   nonreg_ro5_B.sh <dossier>   (TRAVAIL de MODULE=ro5 mame_test.py ; roms_fork/sfa3hx -> ../roms_ro5/sfa3ud)
# 1) 20 000 images d'attraction (diag.py de la copie) ; 2) parties Arcade sur le fork : Ryu 00, Chun-Li 04, Akuma 02.
# Graphismes / banques : work/mame_ro5 (lecture seule). Attendu : « aucune exception », puis « FIN fin=finie » x3.
H=${HSFA_WORKSPACE}; B=$H/work/agent_reorg_B; U=$B/untranspile; W5=${1:?dossier}; G=$H/work/mame_ro5
T=$(mktemp -d -p $W5 nr5_XXXX)
cd $U
MODULE=ro5 TRAVAIL=$W5 MAXF=20000 timeout 1500 nice -n 19 python3 diag.py 30 --nobuild 2>&1 | tail -1
cd $T
un() {
  p=$1; mkdir -p $T/p$p
  BANC_COMMUN=351 PERSO=$p NF=${NR5_NF:-70000} HSFA_PLANS=300,340,3a0 \
  HSFA_GFX=$G/hsfa_gfx.bin,$G/hsfa_plans.bin@3000000 BANC_BANQUES=$G/banques_hx/ BANC_PTR_ANIM=FF40BC \
  BANC_GFX_INTRO=456 BANC_DIR=$W5/ OUT=$T/p$p.txt timeout 2400 nice -n 19 $H/mame-fork/mame/cps2f sfa3hx \
    -rompath $W5/roms_fork -video none -sound none -nothrottle -skip_gameinfo -nvram_directory $T/nv$p -cfg_directory $T/cfg$p \
    -snapshot_directory $T/snap$p -autoboot_script $H/work/mame/tournee.lua >/dev/null 2>&1
  st=$(awk '$2==":" {print $5}' $T/p$p.txt | awk 'BEGIN{s="avant"} $1=="000a"&&s=="avant"{s="dans"} $1!="000a"&&s=="dans"{s="finie"} END{print s}')
  echo "perso $p : $(grep -c COMBAT $T/p$p.txt) manches, $(grep -E 'EXC|FIN' $T/p$p.txt | head -1) fin=$st"
}
for p in ${NR5_PERSOS:-00 04 02}; do un $p & done; wait
rm -rf $T
