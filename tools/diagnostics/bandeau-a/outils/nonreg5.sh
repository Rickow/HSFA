#!/bin/bash
# copie de scripts/untranspile/nonreg_ro5.sh sur MA construction (TRAVAIL=$B/mame_ro5 ; nvram/cfg temporaires)
B=${HSFA_WORKSPACE}/work/agent_bandeau_A; U=$B/untranspile; WD=${WD:-$B/mame_ro5}; W=${HSFA_WORKSPACE}/work/mame; W5=${HSFA_WORKSPACE}/work/mame_ro5
T=$(mktemp -d -p $B)
cd $U
MODULE=ro5 TRAVAIL=$WD MAXF=20000 timeout 1500 nice -n 19 python3 diag.py 30 --nobuild 2>&1 | tail -1
cd $W
un() {
  p=$1; mkdir -p $T/p$p
  BANC_COMMUN=351 PERSO=$p NF=${NR5_NF:-70000} HSFA_PLANS=300,340,3a0 \
  HSFA_GFX=$W5/hsfa_gfx.bin,$W5/hsfa_plans.bin@3000000 BANC_BANQUES=$W5/banques_hx/ BANC_PTR_ANIM=FF40BC \
  BANC_GFX_INTRO=456 BANC_DIR=$WD/ OUT=$T/p$p.txt timeout 2400 nice -n 19 ${HSFA_WORKSPACE}/mame-fork/mame/cps2f sfa3hx \
    -rompath $WD/roms_fork -video none -sound none -nothrottle -skip_gameinfo -nvram_directory $T/nv$p -cfg_directory $T/cfg$p \
    -autoboot_script tournee.lua >/dev/null 2>&1
  st=$(awk '$2==":" {print $5}' $T/p$p.txt | awk 'BEGIN{s="avant"} $1=="000a"&&s=="avant"{s="dans"} $1!="000a"&&s=="dans"{s="finie"} END{print s}')
  echo "perso $p : $(grep -c COMBAT $T/p$p.txt) manches, $(grep -E 'EXC|FIN' $T/p$p.txt | head -1) fin=$st"
}
for p in ${NR5_PERSOS:-00 04 02}; do un $p & done; wait
rm -rf $T
