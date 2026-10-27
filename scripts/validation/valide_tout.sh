#!/bin/bash
# (HANDOFF §142) VALIDATION COMPLETE apres une modification du traducteur : reconstruit SFA3 (ro3), Upper (ro5) et
# Hyper (ro9) dans leurs dossiers de travail, puis :
#   1) non-regression SFA3 (nonreg.sh) et Upper (nonreg_ro5.sh) ;
#   2) une partie VERSUS d'Hyper (tools/hyper-etats/tournee_hyper.lua du depot) : aucune exception attendue ;
#   3) balayage des fins SFA3 (32, captures = arcade ±1) puis Upper (40, fin=finie).
# Duree : ~1 h 15 (etapes en parallele depuis le §148 ; PARALLELE=0 : enchainement d'origine, ~3 h). Sortie : journal sur la sortie standard (« ECART » = defaut) ; md5 des ROM en tete.
# Options : SANS_BALAYAGE=1 (s'arrete apres les non-regressions), MODULES="ro3 ro5 ro9" (reconstructions).
# Chemins : HSFA_DEPOT (depot HSFA, pour tools/hyper-etats ; defaut : ce depot), HSFA_CPS2F (fork MAME),
# HSFA_MODULES_SON (modules d'Hyper corriges ; defaut $H/work/modules_son, a preparer par
# tools/son-hyper/prepare_modules_son.py).
S=$(dirname "$(readlink -f "$0")"); H=${HSFA_WORKSPACE:?"HSFA_WORKSPACE non defini (voir config.example.env)"}; U=${HSFA_SRC:-$S/../../src/hsfa}; cd $U
D=${HSFA_DEPOT:-$S/../..}
# Hyper (§145) : module corrige pour la redirection des voix et bloc de donnees $E70000 (SON-HYPER-ROM §13).
# Le dossier se prepare depuis les modules extraits de l'ISO :
#   tools/son-hyper/prepare_modules_son.py <modules extraits> <redirection_68k/donnees.bin> $H/work/modules_son
# (donnees.bin : sortie de tools/son-hyper/gen_redirection.py). SON_HYPER=0 reconstruit Hyper sans la redirection.
SON9=${HSFA_MODULES_SON:-$H/work/modules_son}
if [ "${SON_HYPER:-1}" = 1 ] && [ ! -f $SON9/son_donnees_ro9.bin ] && echo " ${MODULES:-ro3 ro5 ro9} " | grep -q " ro9 "; then
  echo "ECART : $SON9/son_donnees_ro9.bin absent : Hyper sera construit SANS la redirection des voix"; fi
for m in ${MODULES:-ro3 ro5 ro9}; do echo "== construction $m"
  if [ $m = ro9 ] && [ "${SON_HYPER:-1}" = 1 ] && [ -f $SON9/son_donnees_ro9.bin ]; then
    export EXTRACT_MODULES=$SON9 HSFA_SON_DONNEES=$SON9/son_donnees_ro9.bin; else unset EXTRACT_MODULES HSFA_SON_DONNEES; fi
  MODULE=$m nice -n 19 python3 mame_test.py 2>&1 | grep -E "HANDOFF §1[34][0-9]|sans trace|reset ->"; done
md5sum $H/work/mame/roms_tr/sfa3ud/sz3ud.03c $H/work/mame_ro5/roms_ro5/sfa3ud/sz3ud.03c $H/work/mame_ro9/roms_ro9/sfa3ud/sz3ud.03c
J=$(mktemp -d)
hyper_versus() {
  T=$(mktemp -d); W=$H/work/mame_ro9
  (cd $H/work/mame; LISTE="00.A/01.Z,02.Z/03.Z" MODEJEU=1 NF=20000 OUT=$T/vs.log BANC_COMMUN=545 HSFA_PLANS=300,340,3a0 \
    HSFA_GFX=$W/hsfa_gfx.bin,$W/hsfa_plans.bin@3000000 BANC_BANQUES=$W/banques_hx/ BANC_PTR_ANIM=FF40BC BANC_DIR=$W/ HSFA_BANC_LUA=$H/work/mame \
    timeout 2400 nice -n 19 ${HSFA_CPS2F:-$H/mame-fork/mame/cps2f} sfa3hx -rompath $W/roms_fork -nvram_directory $T/nv -cfg_directory $T/cfg \
    -video none -sound none -nothrottle -skip_gameinfo \
    -autoboot_script $D/tools/hyper-etats/tournee_hyper.lua > $T/mame.txt 2>&1)
  grep -E "SELECTION|MANCHE|EXC|FIN" $T/vs.log | tail -n 6; rm -rf $T
}
balayage() {   # $1 = ro3|ro5 ; P paralleles
  P=$2 $S/balayage_fins.sh $1 > /dev/null 2>&1
  D=$(ls -d $H/work/balayages/$1_* | grep -v interrompu | tail -1); echo $D; wc -l < $D/res.txt
  if [ $1 = ro3 ]; then
    awk '{n="";r="";for(i=1;i<=NF;i++){if($i~/^captures=/){split($i,x,"=");n=x[2]} if($i~/^ref=/){split($i,y,"=");r=y[2]}} d=n-r; if(d<0)d=-d; if(d>1 || $0 !~ /fin=finie/) print "ECART", $0}' $D/res.txt
  else grep -v "fin=finie" $D/res.txt | sed 's/^/ECART /'; fi
}
if [ "${PARALLELE:-1}" = 1 ]; then
  # 12 coeurs : nonreg ro3 (1 MAME), nonreg ro5 (1 puis 3), VERSUS (1), balayages ro3 (P=3) et ro5 (P=4) en meme temps
  $S/nonreg.sh > $J/nr3 2>&1 &
  $S/nonreg_ro5.sh > $J/nr5 2>&1 &
  hyper_versus > $J/vs 2>&1 &
  if [ "$SANS_BALAYAGE" != 1 ]; then
    balayage ro3 ${P3:-3} > $J/b3 2>&1 &
    sleep 70; balayage ro5 ${P5:-4} > $J/b5 2>&1 &   # dossiers horodates a la minute : decaler les deux balayages
  fi
  wait
  echo "== nonreg ro3"; tail -n 6 $J/nr3; echo "== nonreg ro5"; tail -n 5 $J/nr5; echo "== hyper versus"; cat $J/vs
  [ "$SANS_BALAYAGE" != 1 ] && { echo "== balayage ro3"; cat $J/b3; echo "== balayage ro5"; cat $J/b5; }
else
  echo "== nonreg ro3"; $S/nonreg.sh 2>&1 | tail -n 6
  echo "== nonreg ro5"; $S/nonreg_ro5.sh 2>&1 | tail -n 5
  echo "== hyper versus"; hyper_versus
  [ "$SANS_BALAYAGE" = 1 ] && { echo FINI; rm -rf $J; exit 0; }
  echo "== balayage ro3"; balayage ro3 ${P3:-3}
  echo "== balayage ro5"; balayage ro5 ${P5:-3}
fi
rm -rf $J
echo FINI
