#!/bin/bash
# (etape B) BALAYAGE DES FINS d'Upper (copie de scripts/untranspile/balayage_fins.sh, ro5) sur un dossier de l'etape B :
#   balayage_ro5_B.sh <dossier> [persos hex...]   (P paralleles, defaut 3 ; NF images, defaut 90000 / 180000 pour 07)
# Fork cps2f sfa3hx ; graphismes / banques : work/mame_ro5 (lecture seule). Resume : « fin=finie » attendu pour les 40.
H=${HSFA_WORKSPACE}; B=$H/work/agent_reorg_B; W5=${1:?dossier}; shift; G=$H/work/mame_ro5
D=$B/balayages/ro5_$(basename $W5)_$(date +%Y%m%d-%H%M%S); mkdir -p $D
if [ $# -gt 0 ]; then PERSOS="$*"; else PERSOS=$(for p in $(seq 0 39); do printf "%02x " $p; done); fi
un() {
  p=$1; cd $D; mkdir -p $D/p$p
  nf=${NF:-90000}; [ $p = 07 ] && nf=180000
  BANC_COMMUN=351 PERSO=$p NF=$nf SNAPP=150 SNAPFIN=1 HSFA_PLANS=300,340,3a0 \
    HSFA_GFX=$G/hsfa_gfx.bin,$G/hsfa_plans.bin@3000000 BANC_BANQUES=$G/banques_hx/ BANC_PTR_ANIM=FF40BC \
    BANC_GFX_INTRO=456 BANC_DIR=$W5/ OUT=$D/p$p.txt nice -n 19 $H/mame-fork/mame/cps2f sfa3hx -rompath $W5/roms_fork \
    -video none -sound none -nothrottle -skip_gameinfo -snapshot_directory $D/p$p -nvram_directory $D/nv$p -cfg_directory $D/cfg$p \
    -autoboot_script $H/work/mame/tournee.lua >/dev/null 2>&1
  sd=$D/p$p/sfa3hx
  st=$(awk '$2==":" {print $5}' $D/p$p.txt | awk 'BEGIN{s="avant"} $1=="000a"&&s=="avant"{s="dans"} $1!="000a"&&s=="dans"{s="finie"} END{print s}')
  n=$(ls $sd 2>/dev/null | wc -l)
  echo "$p $(grep -c COMBAT $D/p$p.txt) manches $(grep -E 'EXC|FIN' $D/p$p.txt | head -1) fin=$st captures=$n" >> $D/res.txt
  rm -rf $D/nv$p $D/cfg$p
}
export -f un; export D H W5 G
echo $PERSOS | tr ' ' '\n' | grep . | xargs -P ${P:-3} -I{} bash -c 'un {}'
sort -o $D/res.txt $D/res.txt; echo "$D"; cat $D/res.txt
grep -v "fin=finie" $D/res.txt | sed 's/^/ECART /'
