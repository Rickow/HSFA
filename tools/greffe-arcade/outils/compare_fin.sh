#!/bin/bash
# (etape 5) Compare le SCRIPT DE FIN d'un perso : Upper (oracle tournee_greffe, debut d'apres donnees/fins_upper.tsv) et
# ro9a (debut d'apres le balayage traces/<PREFIXE>_<perso>_Z3) ; journaux surv de $FF0034-$FF003B puis compare_script.py.
# Usage : compare_fin.sh PERSO CONSTRUCTION [PREFIXE=f5]
G=${HSFA_WORKSPACE}/work/greffe_arcade; p=$1; C=$2; PF=${3:-f5}; cd $G
UA=$(awk -v p=$p '$1==p {print $2}' donnees/fins_upper.tsv); RA=$(grep -o "SCENE_A [0-9]*" traces/${PF}_${p}_Z3/journal.txt | awk '{print $2}')
RE=$(grep -o "EXCEPTION [0-9]*" traces/${PF}_${p}_Z3/journal.txt | awk '{print $2}'); RE=${RE:-$((RA+15000))}
PC=$(awk '{v=strtonum("0x"$2); if (v>=0x24f9d0 && v<0x24fbd0) {print $1; exit}}' fige/ro5/carte_image.txt)
(TMAX=4000 outils/lance_upper_lua.sh cf_u_$p "PERSO=$p LUA_BASE=$G/lua/graine_pc.lua LUA_BASE_G=$G/lua/tournee_greffe.lua GRAINE_PC=$PC GRAINE_OUT=$G/traces/cf_u_$p.graine FORCE_ADR=ff8120=32,ff8123=82 SURV2=ff0034:8:$((UA-50)) SURV2_N=40000 SURV2_OUT=$G/traces/cf_u_$p.txt" $((UA + RE - RA + 300)) $G/lua/surv.lua > /dev/null 2>&1) &
SCRIPT_LUA=$G/lua/surv.lua TMAX=5000 outils/oracle_ro9a.sh $C cf_r_$p $((RE + 5)) "PERSO=$p.Z3 SCENEA_PASSIF=1 BLOCAGE=20000 LUA_BASE=$G/lua/graine_pc.lua LUA_BASE_G=$G/lua/tournee_arcade.lua SURV2=ff0034:8:$((RA-50)) SURV2_N=40000 SURV2_OUT=$G/traces/cf_r_$p.txt" > /dev/null 2>&1
wait
echo "== $p (Upper A $UA, ro9a A $RA, arret $RE)"; python3 etape4/compare_script.py traces/cf_u_$p.txt traces/cf_r_$p.txt
