#!/bin/bash
# (§162) NON-REGRESSION DU COEUR FBNeo HSFA : memes parties scriptees jouees par un coeur de REFERENCE et par le coeur
# a tester, sur les MEMES zips ; captures (md5), journal du jeu, journaux du rejeu et des flux et SON (WAV) compares.
#   nonreg_coeur.sh                      coeur Linux de l'arbre work/agent_fbneo_rejeu/fbneo contre la reference
#   COEUR=<.so> REF=<.so> ZIPS=<dossier contenant sfa3hsfa.zip, sfa3uhsfa.zip, sfa3hhsfa.zip> nonreg_coeur.sh
#   JEUX="sfa3 upper hyper" (defaut : les trois)
# Attendu : « IDENTIQUE » pour chaque jeu. Une difference voulue (nouvelle fonction du coeur) se lit dans le detail.
# Duree : ~5 min (3 jeux x 2 coeurs en parallele). Sorties : work/agent_fbneo_rejeu/tests/essais/nrc_<jeu>_{ref,new}/
S=$(dirname "$(readlink -f "$0")"); H=${HSFA_WORKSPACE:?"HSFA_WORKSPACE non defini (voir config.example.env)"}; T=$H/work/agent_fbneo_rejeu/tests
COEUR=${COEUR:-$H/work/agent_fbneo_rejeu/fbneo/src/burner/libretro/fbneo_hsfa_libretro.so}
REF=${REF:-$H/work/references/coeurs/linux_hsfa_501aebd.so}
ZIPS=${ZIPS:-$H/work/livraison_v148}
[ -f "$COEUR" ] && [ -f "$REF" ] || { echo "coeur ou reference introuvable : $COEUR / $REF"; exit 2; }
partie() {   # $1 jeu, $2 ref|new, $3 coeur
  case $1 in
    sfa3)  Z=sfa3hsfa;  P=""; export INPUTS="100-106::IN0:Coin 1;200-206::IN0:1 Player Start;300-9000%200,6::IN0:1 Player Start;400-9000%200,6::IN0:P1 Button 1;500-9000%400,40::IN0:P1 Right" NF=9000 ;;
    upper) Z=sfa3uhsfa; P=""; export INPUTS="100-106::IN0:Coin 1;200-206::IN0:1 Player Start;300-9000%200,6::IN0:1 Player Start;400-9000%200,6::IN0:P1 Button 1;500-9000%400,40::IN0:P1 Right" NF=9000 ;;
    hyper) Z=sfa3hhsfa; P=hyper; export LISTE=00.Z/01.Z2,01.Z/00.Z2,00.Z2/01.A MODEJEU=1 CONTOURNE_E=1 NF=12000 ;;
  esac
  SNAPS=$(seq -s, 300 300 $NF) PILOTE=$P $T/fb.sh nrc_$1_$2 "$3" $ZIPS/$Z.zip
}
for j in ${JEUX:-sfa3 upper hyper}; do partie $j ref "$REF" & partie $j new "$COEUR" & done; wait
r=0
for j in ${JEUX:-sfa3 upper hyper}; do
  A=$T/essais/fb_nrc_${j}_ref; B=$T/essais/fb_nrc_${j}_new; d=""
  [ "$(cd $A/snap && md5sum * 2>/dev/null)" = "$(cd $B/snap && md5sum * 2>/dev/null)" ] || d="$d captures"
  for f in journal.txt rejeu.txt flux.txt son.wav; do { [ -f $A/$f ] || [ -f $B/$f ]; } && ! cmp -s $A/$f $B/$f && d="$d $f"; done
  n=$(ls $A/snap | wc -l)
  if [ -z "$d" ]; then echo "$j : IDENTIQUE ($n captures)"; else echo "$j : DIFFERENT :$d  ($A / $B)"; r=1; fi
done
exit $r
