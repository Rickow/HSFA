#!/bin/bash
# (HANDOFF §126) NON-REGRESSION d'Upper (ro5), apres reconstruction (MODULE=ro5 mame_test.py) :
#  1) 20 000 images d'attraction sans entree (diag.py, MAME standard) ;
#  2) trois parties Arcade completes sur le fork (jeu sfa3hx, tournee.lua), en parallele :
#     Ryu (00 : parcours de reference), Chun-Li (04 : combat contre Juli et Juni), Akuma (02 : Vega sur le grillage).
# Attendu : « aucune exception » puis, pour chaque perso, « FIN fin=finie » (sequence de fin atteinte et terminee).
# Duree : ~15 min. Option : NR5_PERSOS="00 04 02" (liste des persos), NR5_NF=70000 (images par partie).
S=$(dirname "$(readlink -f "$0")"); H=${HSFA_WORKSPACE:?"HSFA_WORKSPACE non defini (voir config.example.env)"}; U=${HSFA_SRC:-$S/../../src/hsfa}; W=$H/work/mame; W5=$H/work/mame_ro5
T=$(mktemp -d)
cd $U
MODULE=ro5 MAXF=20000 timeout 1500 nice -n 19 python3 diag.py 30 --nobuild 2>&1 | tail -1
cd $W
un() {
  p=$1; mkdir -p $T/p$p
  BANC_COMMUN=351 PERSO=$p NF=${NR5_NF:-70000} HSFA_PLANS=300,340,3a0 \
  HSFA_GFX=$W5/hsfa_gfx.bin,$W5/hsfa_plans.bin@3000000 BANC_BANQUES=$W5/banques_hx/ BANC_PTR_ANIM=FF40BC \
  BANC_GFX_INTRO=456 BANC_DIR=$W5/ OUT=$T/p$p.txt timeout 2400 nice -n 19 $H/mame-fork/mame/cps2f sfa3hx \
    -rompath $W5/roms_fork -video none -sound none -nothrottle -skip_gameinfo -nvram_directory $T/nv$p \
    -autoboot_script tournee.lua >/dev/null 2>&1
  # fin : $FF8004 = $000A vu puis quitte (colonne 5 du journal de tournee.lua)
  st=$(awk '$2==":" {print $5}' $T/p$p.txt | awk 'BEGIN{s="avant"} $1=="000a"&&s=="avant"{s="dans"} $1!="000a"&&s=="dans"{s="finie"} END{print s}')
  echo "perso $p : $(grep -c COMBAT $T/p$p.txt) manches, $(grep -E 'EXC|FIN' $T/p$p.txt | head -1) fin=$st"
}
for p in ${NR5_PERSOS:-00 04 02}; do un $p & done; wait
rm -rf $T
