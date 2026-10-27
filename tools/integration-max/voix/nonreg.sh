#!/bin/bash
# nonreg.sh : 296 commandes existantes (agent_son_ro5/hybride/codes.txt : musiques, sons d'Upper, bruitages, voix)
# jouees avec la ROM hybride d'origine puis avec roms_voix/ : journaux de registres et WAV doivent etre IDENTIQUES ;
# tap de lecture sur les banques QSound des voix MAX : aucune lecture attendue.
D=${HSFA_WORKSPACE}/work/agent_voix_max; cd $D
C=$(tr ',' ' ' < ${HSFA_WORKSPACE}/work/agent_son_ro5/hybride/codes.txt)
CODES="$C" PAS=60 WAV=$D/journaux/regr_base.wav timeout 900 ./lance.sh ${HSFA_WORKSPACE}/work/agent_son_ro5/hybride/roms_hybride $D/journaux/regr_base.txt > journaux/regr_base.stdout 2>&1 &
CODES="$C" PAS=60 WAV=$D/journaux/regr_voix.wav LUA=lectures.lua LECT=$D/journaux/regr_lect.txt ZONES=$D/journaux/zones.txt \
  timeout 900 ./lance.sh $D/roms_voix $D/journaux/regr_voix.txt > journaux/regr_voix.stdout 2>&1
wait
echo "commandes : $(grep -c '^C' journaux/regr_base.txt) / $(grep -c '^C' journaux/regr_voix.txt)"
cmp -s journaux/regr_base.txt journaux/regr_voix.txt && echo "journaux de registres QSound : IDENTIQUES" || echo "journaux : DIFFERENTS"
cmp -s journaux/regr_base.wav journaux/regr_voix.wav && echo "WAV : IDENTIQUES" || echo "WAV : DIFFERENTS"
echo "lectures dans les banques des voix MAX : $(wc -l < journaux/regr_lect.txt)"
