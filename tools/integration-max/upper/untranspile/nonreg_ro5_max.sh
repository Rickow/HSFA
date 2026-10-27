#!/bin/bash
# (agent_integration_max) copie de nonreg_ro5.sh pour un dossier de construction quelconque (avec ou sans MAX=1) :
#  BANC=<dossier> (défaut : banc_ref) ; 1) 20 000 images d'attraction (diag.py, MAME standard) ; 2) trois parties Arcade
#  complètes sur le fork (tournee.lua d'origine) : Ryu 00, Chun-Li 04, Akuma 02 (NR5_PERSOS). nvram ET cfg propres.
H=${HSFA_WORKSPACE}; U=$(dirname $(readlink -f $0)); I=$(dirname $U); W=$H/work/mame; W5=$H/work/mame_ro5
B=$(readlink -f ${BANC:-$I/banc_ref}); [ -s $B/sfa3max_cache.txt ] && export SFA3MAX_CACHE=$(cat $B/sfa3max_cache.txt); eval $(python3 $(dirname $(readlink -f $0))/max_cache.py); G=${MAXFORK%/}
GP=""; [ -f $B/max_plus_gfx.bin ] && GP=",$B/max_plus_gfx.bin@$PLUSG"   # (agent_integration_max) HUD / aperçu MAX
T=$(mktemp -d -p $I)
cd $U
MODULE=ro5 TRAVAIL=$B MAXF=20000 timeout 1500 nice -n 19 python3 diag.py 30 --nobuild 2>&1 | tail -1
cd $W
un() {
  p=$1; mkdir -p $T/p$p
  BANC_COMMUN=351 PERSO=$p NF=${NR5_NF:-70000} HSFA_PLANS=$PLANS HSFA_EXT=$B HSFA_SON=$H/work/agent_son_max/roms_son_max_pas \
  HSFA_GFX=$W5/hsfa_gfx.bin,$G/max_gfx.bin@$MAXG,$G/max_portraits_gfx.bin@$PORTG${GP},$W5/hsfa_plans.bin@$PLANSG \
  BANC_BANQUES=$B/banques_hx/ BANC_PTR_ANIM=FF40BC \
  BANC_GFX_INTRO=456 BANC_DIR=$B/ OUT=$T/p$p.txt timeout 2400 nice -n 19 $H/mame-fork/mame/cps2f sfa3hx \
    -rompath $B/roms_fork -video none -sound none -nothrottle -skip_gameinfo -nvram_directory $T/nv$p -cfg_directory $T/cfg$p \
    -autoboot_script tournee.lua >/dev/null 2>&1
  st=$(awk '$2==":" {print $5}' $T/p$p.txt | awk 'BEGIN{s="avant"} $1=="000a"&&s=="avant"{s="dans"} $1!="000a"&&s=="dans"{s="finie"} END{print s}')
  echo "perso $p : $(grep -c COMBAT $T/p$p.txt) manches, $(grep -E 'EXC|FIN' $T/p$p.txt | head -1) fin=$st"
}
for p in ${NR5_PERSOS:-00 04 02}; do un $p & done; wait
rm -rf $T
