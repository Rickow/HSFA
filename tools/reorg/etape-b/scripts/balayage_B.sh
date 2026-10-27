#!/bin/bash
# (etape B) BALAYAGE DES FINS SFA3 (copie de scripts/untranspile/balayage_fins.sh, ro3 seulement) sur un dossier de
# l'etape B : balayage_B.sh <dossier> [persos hex...]   (P paralleles, defaut 3 ; NF images, defaut 24000 / 40000 pour 07)
# Sorties : work/agent_reorg_B/balayages/<nom du dossier>_<date-heure>/ (pNN.txt, pNN/ captures, res.txt).
# Resume : « NN manches FIN|EXCEPTION … fin=avant|dans|finie captures=K ref=R » (ref : arcade, ±1 attendu).
H=${HSFA_WORKSPACE}; B=$H/work/agent_reorg_B; W=${1:?dossier}; shift
D=$B/balayages/$(basename $W)_$(date +%Y%m%d-%H%M%S); mkdir -p $D
if [ $# -gt 0 ]; then PERSOS="$*"; else PERSOS=$(for p in $(seq 0 31); do printf "%02x " $p; done); fi
un() {
  p=$1; cd $W; mkdir -p $D/p$p
  nf=${NF:-24000}; [ $p = 07 ] && nf=40000
  BANC_DIR=$W/ PERSO=$p FORCE="Lff8540=ffffffff" NF=$nf SNAPP=150 SNAPFIN=1 OUT=$D/p$p.txt nice -n 19 mame sfa3ud -rompath $W/roms_tr \
    -video none -sound none -nothrottle -skip_gameinfo -snapshot_directory $D/p$p -nvram_directory $D/nv$p -cfg_directory $D/cfg$p \
    -autoboot_script ${SCRIPT:-$H/work/mame/tournee.lua} >/dev/null 2>&1
  sd=$D/p$p/sfa3ud
  st=$(awk '$2==":" {print $5}' $D/p$p.txt | awk 'BEGIN{s="avant"} $1=="000a"&&s=="avant"{s="dans"} $1!="000a"&&s=="dans"{s="finie"} END{print s}')
  n=$(ls $sd 2>/dev/null | wc -l)
  ref=" ref=$(awk -v p=$p '$1==p{print $2}' $H/work/balayages/ref_sfa3_captures.txt)"
  echo "$p $(grep -c COMBAT $D/p$p.txt) manches $(grep -E 'EXC|FIN' $D/p$p.txt | head -1) fin=$st captures=$n$ref" >> $D/res.txt
  rm -rf $D/nv$p $D/cfg$p
}
export -f un; export D H W
echo $PERSOS | tr ' ' '\n' | grep . | xargs -P ${P:-3} -I{} bash -c 'un {}'
sort -o $D/res.txt $D/res.txt; echo "$D"; cat $D/res.txt
awk '{n="";r="";for(i=1;i<=NF;i++){if($i~/^captures=/){split($i,x,"=");n=x[2]} if($i~/^ref=/){split($i,y,"=");r=y[2]}} d=n-r; if(d<0)d=-d; if(d>1 || $0 !~ /fin=finie/) print "ECART", $0}' $D/res.txt
