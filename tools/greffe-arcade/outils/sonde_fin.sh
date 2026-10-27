#!/bin/bash
# (etape 7) SONDE DE REGISTRES pendant une fin, Upper ET ro9a (2 MAME) : lua/sonde_regs.lua a l'entree d'un PC 68K.
# Usage : sonde_fin.sh PERSO CONSTRUCTION PREFIXE PC_UPPER PC_RO9A REL N "SONDE_MEM" [QUI=ur]
#   REL : nombre d'images apres le debut de la fin (SCENE_A) a partir duquel on sonde ; N : nombre de passages notes.
#   Sorties : traces/sd_u_PERSO.txt, traces/sd_r_PERSO.txt. Upper : debut d'apres donnees/fins_upper.tsv ; ro9a : d'apres
#   traces/<PREFIXE>_<perso>_Z3 (arret a l'exception s'il y en a une).
G=${HSFA_WORKSPACE}/work/greffe_arcade; p=$1; C=$2; PF=$3; UPC=$4; RPC=$5; REL=$6; N=$7; MEM=$8; QUI=${9:-ur}; cd $G
UA=$(awk -v p=$p '$1==p {print $2}' donnees/fins_upper.tsv); RA=$(grep -o "SCENE_A [0-9]*" traces/${PF}_${p}_Z3/journal.txt | awk '{print $2}')
RE=$(grep -o "EXCEPTION [0-9]*" traces/${PF}_${p}_Z3/journal.txt | awk '{print $2}'); RE=${RE:-$((RA+REL+600))}
PC=$(awk '{v=strtonum("0x"$2); if (v>=0x24f9d0 && v<0x24fbd0) {print $1; exit}}' fige/ro5/carte_image.txt)
if [[ $QUI == *u* ]]; then
(TMAX=5000 outils/lance_upper_lua.sh sd_u_$p "PERSO=$p LUA_BASE=$G/lua/graine_pc.lua LUA_BASE_G=$G/lua/tournee_greffe.lua GRAINE_PC=$PC GRAINE_OUT=$G/traces/sd_u_$p.graine FORCE_ADR=ff8120=32,ff8123=82 SONDE_PC=$UPC SONDE_F0=$((UA + REL)) SONDE_N=$N SONDE_MEM=$MEM SONDE_OUT=$G/traces/sd_u_$p.txt" $((UA + REL + 600)) $G/lua/sonde_regs.lua > /dev/null 2>&1) &
fi
if [[ $QUI == *r* ]]; then
SCRIPT_LUA=$G/lua/sonde_regs.lua TMAX=5000 outils/oracle_ro9a.sh $C sd_r_$p $((RE + 5)) "PERSO=$p.Z3 SCENEA_PASSIF=1 BLOCAGE=20000 LUA_BASE=$G/lua/graine_pc.lua LUA_BASE_G=$G/lua/tournee_arcade.lua SONDE_PC=$RPC SONDE_F0=$((RA + REL)) SONDE_N=$N SONDE_MEM=$MEM SONDE_OUT=$G/traces/sd_r_$p.txt" > /dev/null 2>&1
fi
wait
echo "== $p (Upper A $UA, ro9a A $RA, arret $RE)"
