#!/bin/bash
# (etape 5) Pointeur du SCRIPT DE FIN d'Upper ($8034, surv de $FF0034-$FF0037) pendant toute la fin de chaque perso
# (oracle tournee_greffe ; debut/fin d'apres donnees/fins_upper.tsv, fin inconnue -> +13 000). P en parallele.
# Sorties traces/su_<perso>.txt. Usage : scripts_upper.sh "05 06 ..." [P=3]
G=${HSFA_WORKSPACE}/work/greffe_arcade
run() {
  p=$1; cd $G; UA=$(awk -v p=$p '$1==p {print $2}' donnees/fins_upper.tsv); UF=$(awk -v p=$p '$1==p {print $3}' donnees/fins_upper.tsv)
  [ "$UA" = "-" ] && return; [ "$UF" = "-" ] && UF=$((UA + 13000))
  PC=$(awk '{v=strtonum("0x"$2); if (v>=0x24f9d0 && v<0x24fbd0) {print $1; exit}}' fige/ro5/carte_image.txt)
  TMAX=6000 outils/lance_upper_lua.sh su_$p "PERSO=$p LUA_BASE=$G/lua/graine_pc.lua LUA_BASE_G=$G/lua/tournee_greffe.lua GRAINE_PC=$PC GRAINE_OUT=$G/traces/su_$p.graine FORCE_ADR=ff8120=32,ff8123=82 SURV2=ff0034:4:$((UA-50)) SURV2_N=200000 SURV2_OUT=$G/traces/su_$p.txt" $((UF + 50)) $G/lua/surv.lua > /dev/null 2>&1
}
export -f run; export G
echo $1 | tr ' ' '\n' | xargs -P ${P:-3} -I{} bash -c 'run {}'
