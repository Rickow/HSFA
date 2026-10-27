#!/bin/bash
# (HANDOFF §131) BALAYAGE DES FINS : une partie Arcade par perso jusqu'a sa fin (tournee.lua), en parallele.
#   balayage_fins.sh ro3|ro5 [persos hex...]     (defaut : ro3 00-1f avec FORCE comme §111 ; ro5 00-27 sans FORCE)
# Sorties : work/balayages/<module>_<date-heure>/ (pNN.txt journal, pNN/ captures de la fin, res.txt resume).
# Resume par perso : « NN manches FIN|EXCEPTION … fin=avant|dans|finie captures=K » ; ro3 : comparaison des captures
# a work/balayages/ref_sfa3_captures.txt (arcade, ±1 attendu). Variables : P (paralleles, 3), NF (images).
S=$(dirname "$(readlink -f "$0")"); H=${HSFA_WORKSPACE:?"HSFA_WORKSPACE non defini (voir config.example.env)"}; W=$H/work/mame; W5=$H/work/mame_ro5
MOD=${1:-ro3}; shift
D=$H/work/balayages/${MOD}_$(date +%Y%m%d-%H%M); mkdir -p $D
if [ $# -gt 0 ]; then PERSOS="$*"; elif [ $MOD = ro3 ]; then PERSOS=$(for p in $(seq 0 31); do printf "%02x " $p; done); else PERSOS=$(for p in $(seq 0 39); do printf "%02x " $p; done); fi
un() {
  p=$1; cd $W; mkdir -p $D/p$p
  if [ $MOD = ro3 ]; then
    nf=${NF:-24000}; [ $p = 07 ] && nf=40000
    PERSO=$p FORCE="Lff8540=ffffffff" NF=$nf SNAPP=150 SNAPFIN=1 OUT=$D/p$p.txt nice -n 19 mame sfa3ud -rompath roms_tr \
      -video none -sound none -nothrottle -skip_gameinfo -snapshot_directory $D/p$p -nvram_directory $D/nv$p \
      -autoboot_script tournee.lua >/dev/null 2>&1
    sd=$D/p$p/sfa3ud
  else
    nf=${NF:-90000}; [ $p = 07 ] && nf=180000
    BANC_COMMUN=351 PERSO=$p NF=$nf SNAPP=150 SNAPFIN=1 HSFA_PLANS=300,340,3a0 \
      HSFA_GFX=$W5/hsfa_gfx.bin,$W5/hsfa_plans.bin@3000000 BANC_BANQUES=$W5/banques_hx/ BANC_PTR_ANIM=FF40BC \
      BANC_GFX_INTRO=456 BANC_DIR=$W5/ OUT=$D/p$p.txt nice -n 19 $H/mame-fork/mame/cps2f sfa3hx -rompath $W5/roms_fork \
      -video none -sound none -nothrottle -skip_gameinfo -snapshot_directory $D/p$p -nvram_directory $D/nv$p \
      -autoboot_script tournee.lua >/dev/null 2>&1
    sd=$D/p$p/sfa3hx
  fi
  st=$(awk '$2==":" {print $5}' $D/p$p.txt | awk 'BEGIN{s="avant"} $1=="000a"&&s=="avant"{s="dans"} $1!="000a"&&s=="dans"{s="finie"} END{print s}')
  n=$(ls $sd 2>/dev/null | wc -l); ref=""
  [ $MOD = ro3 ] && ref=" ref=$(awk -v p=$p '$1==p{print $2}' $H/work/balayages/ref_sfa3_captures.txt)"
  echo "$p $(grep -c COMBAT $D/p$p.txt) manches $(grep -E 'EXC|FIN' $D/p$p.txt | head -1) fin=$st captures=$n$ref" >> $D/res.txt
  rm -rf $D/nv$p
}
export -f un; export D MOD H W W5
echo $PERSOS | tr ' ' '\n' | grep . | xargs -P ${P:-3} -I{} bash -c 'un {}'
sort -o $D/res.txt $D/res.txt; echo "$D"; cat $D/res.txt
