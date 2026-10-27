#!/bin/bash
# (etape 2) plan -> relogement A5 -> module ro9a -> construction -> partie Arcade : cycle.sh NOM TRACE "VARS" NF
G=${HSFA_WORKSPACE}/work/greffe_arcade; cd $G
nice -n 19 python3 etape2/ecrit_greffe.py | head -1
nice -n 19 python3 etape2/relogement_a5_v2.py | tail -2
NOM=$1 nice -n 19 python3 etape2/greffe2.py --construire 2>&1 | tail -5
TMAX=${TMAX:-1800} outils/lance_ro9a.sh $1 $2 "$3" $4
grep -E "MANCHE|EXCEPTION|FIN" $G/traces/$2/journal.txt | head -20
