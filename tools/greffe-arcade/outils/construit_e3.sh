#!/bin/bash
# (etape 3) CONSTRUCTION ro9a avec etape3/greffe3.py (combat = Hyper) et le traducteur fusionne untranspile3/.
# Usage : construit_e3.sh NOM ["VARS..."]. Enchaine : plan seul (donnees/greffe_v3.pkl) -> table A5 recalculee pour
# l'ensemble greffe (etape3/relogement_a5_v3.py -> donnees/relogement_a5_v3.pkl) -> module, bloc, traduction.
G=${HSFA_WORKSPACE}/work/greffe_arcade; cd $G
env NOM=$1 PLAN_SEUL=1 $2 nice -n 19 python3 etape3/greffe3.py
GREFFER_PKL=donnees/greffe_v3.pkl nice -n 19 python3 etape3/relogement_a5_v3.py | tail -1
env NOM=$1 $2 nice -n 19 python3 etape3/greffe3.py --construire 2>&1 | tail -8
md5sum constructions/$1/b9/roms_ro9/sfa3ud/sz3ud.03c
mkdir -p constructions/$1/roms_fork && ln -sfn ../b9/roms_ro9/sfa3ud constructions/$1/roms_fork/sfa3hx
