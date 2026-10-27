#!/bin/bash
# nonreg_tout.sh : TOUTES les commandes non vides de l'hybride (hors voix MAX), 40 images chacune, ROM d'origine
# contre roms_voix/ : journaux de registres QSound identiques + tap de lecture sur les banques des voix MAX.
D=${HSFA_WORKSPACE}/work/agent_voix_max; cd $D
C=$(${HSFA_WORKSPACE}/venv/bin/python -c "
import sys; sys.path.insert(0,'.')
from gen_voix_max import lit_base, pilote, BASE
z,q=lit_base(BASE); p=pilote(z)
print(' '.join('%04x'%c for c in range(0xC00) if p.cmd(c)[0]))")
CODES="$C" PAS=40 timeout 3000 ./lance.sh ${HSFA_WORKSPACE}/work/agent_son_ro5/hybride/roms_hybride $D/journaux/tout_base.txt > journaux/tout_base.stdout 2>&1 &
CODES="$C" PAS=40 LUA=lectures.lua LECT=$D/journaux/tout_lect.txt ZONES=$D/journaux/zones.txt \
  timeout 3000 ./lance.sh $D/roms_voix $D/journaux/tout_voix.txt > journaux/tout_voix.stdout 2>&1
wait
echo "commandes : $(grep -c '^C' journaux/tout_base.txt) / $(grep -c '^C' journaux/tout_voix.txt)"
cmp -s journaux/tout_base.txt journaux/tout_voix.txt && echo "journaux de registres QSound : IDENTIQUES" || echo "journaux : DIFFERENTS"
echo "lectures dans les banques des voix MAX : $(wc -l < journaux/tout_lect.txt)"
