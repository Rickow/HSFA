#!/bin/bash
# valide.sh : injecte les 134 voix (cote 1 avec WAV, cote 2 registres seuls) avec roms_voix/, puis controles.
D=${HSFA_WORKSPACE}/work/agent_voix_max; cd $D
C1=$(python3 -c "
import json,math
a=json.load(open('roms_voix/attribution.json'))
print(' '.join('%s:%d'%(v['cmd'].lower(), math.ceil((v['duree_note']+0.35)*59.637)+6) for v in a))")
C2=$(python3 -c "
import json,math
a=json.load(open('roms_voix/attribution.json'))
print(' '.join('%s:%d'%(v['cmd2'].lower(), math.ceil((v['duree_note']+0.35)*59.637)+6) for v in a))")
CODES="$C1" WAV=$D/journaux/cote1.wav timeout 900 ./lance.sh $D/roms_voix $D/journaux/cote1.txt > journaux/cote1.stdout 2>&1 &
CODES="$C2" timeout 900 ./lance.sh $D/roms_voix $D/journaux/cote2.txt > journaux/cote2.stdout 2>&1
wait
python3 analyse_regs.py journaux/cote1.txt
python3 analyse_regs.py journaux/cote2.txt cote2
${HSFA_WORKSPACE}/venv/bin/python compare_voix.py journaux/cote1.txt journaux/cote1.wav
