#!/bin/bash
# (agent_hyper_etats) modes caches de ZERO 3 (sous-etats 4..7 du curseur $5C, etat 6 de selection) en TRAINING.
# J1 = perso de la grille (DROITE=n deplacements a droite depuis Ryu), version ZERO 3 ; J2 = choix par defaut.
# Usage : [MODES="m0 m6 ..."] [DROITE=n] [PFX=mc] modes_caches.sh -> essais/<PFX>_<mode>.log + captures
B=${HSFA_WORKSPACE}/work/agent_hyper_etats
D=""; for i in $(seq 1 ${DROITE:-0}); do D="$D;$((600+20*i))-$((603+20*i))::IN0:P1 Right"; done
BASE="300-305::IN2:Coin 1;400-405::IN2:1 Player Start;470-474::IN0:P1 Down;520-525::IN0:P1 Button 1$D;700-705::IN0:P1 Button 1;820-823::IN0:P1 Down;840-843::IN0:P1 Down;860-863::IN0:P1 Down;900-905::IN0:P1 Button 1"
FIN="1100-1105::IN0:P1 Button 1;1300-1305::IN0:P1 Button 1;1500-1505::IN0:P1 Button 1;1700-1705::IN0:P1 Button 1;1900-1905::IN0:P1 Button 1"
SR="1040-1070::IN2:1 Player Start;1050-1053::IN0:P1 Right"     # Start maintenu + Droite
entrees() { case $1 in
  m0) echo "$BASE;$FIN";;
  m1) echo "$BASE;1000-1003::IN0:P1 Down;$FIN";;
  m2) echo "$BASE;1000-1003::IN0:P1 Down;1020-1023::IN0:P1 Down;$FIN";;
  m3) echo "$BASE;1000-1003::IN0:P1 Up;$FIN";;
  m6) echo "$BASE;$SR;$FIN";;
  m5) echo "$BASE;1000-1003::IN0:P1 Down;$SR;$FIN";;
  m7) echo "$BASE;1000-1003::IN0:P1 Down;1020-1023::IN0:P1 Down;$SR;$FIN";;
  m4) echo "$BASE;1000-1003::IN0:P1 Up;$SR;$FIN";;
esac; }
export NF=${NF:-2900} SNAPS=${SNAPS:-1080} SNAPVS=${SNAPVS:-60} SNAPC=${SNAPC:-100,300} WATCH=FF845C,FF8523,FF8533,FF855F,FF8530,FF855B,FF8522,FF84F1,FF84ED,FF84EA,FF855C
n=0
for m in ${MODES:-m0 m6 m5 m7 m4 m3}; do
  INPUTS="$(entrees $m)" $B/lance.sh ${PFX:-mc}_$m & n=$((n+1))
  if [ $n -ge 2 ]; then wait -n; n=$((n-1)); fi
done; wait
