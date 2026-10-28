#!/bin/bash
# (etape 7) fa_coeur.sh <nom> <coeur.so> <zip> : partie ARCADE de ro9a dans le coeur FBNeo (hsfa_run d'agent_coeur_banques,
# lecture seule, PILOTE=arcade = portage de lua/tournee_arcade.lua). Variables : NF, PERSO, GRAINE, SNAPETAT, SNAPS, SNAPSC,
# NOCONT, SCENEA_PASSIF, BLOCAGE. Sorties : livraison/essais/fa_<nom>/
G=${HSFA_WORKSPACE}/work/greffe_arcade; N=$1; C=${2:?coeur}; Z=${3:?zip}
D=${ESSAIS:-$G/livraison/essais}/fa_$N; rm -rf $D; mkdir -p $D/snap $D/sys/fbneo/hsfa
export HSFA_NOROUL=${HSFA_NOROUL-1}
PILOTE=arcade JOURNAL=$D/journal.txt HSFA_PLANS_LOG=$D/plans.txt OUTDIR=$D/snap SYSDIR=$D/sys OUT=$D/log.txt WAV=${WAV-} \
  VERBOSE=1 timeout ${TMAX:-3000} nice -n 19 ${HSFA_WORKSPACE}/work/agent_coeur_banques/tests/hsfa_run $C $Z > $D/fb.out 2>&1
echo "$N : $(tail -1 $D/journal.txt)"
