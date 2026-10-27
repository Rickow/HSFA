#!/bin/bash
# (etape 2) CONSTRUCTION « HYPER AUGMENTE » (ro9a) : plan de greffe -> relogement A5 -> module augmente, bloc de donnees,
# profil des chargeurs natifs, banques du fork -> traduction par la copie du traducteur (untranspile/).
# Usage : construit_ro9a.sh [NOM=ro9a]. Variables de la construction : constructions/<NOM>/env.sh (MODULE=ro9 +
# MODULE_FICHIER, GREFFE_C0, GREFFE_Z2, HSFA_GREFFE_DONNEES/_X/_Y/_PTRS, HSFA_GREFFE_ASSETS, EXTRACT_MODULES et
# HSFA_SON_DONNEES de la redirection des voix) : c'est le « profil » ro9a.
G=${HSFA_WORKSPACE}/work/greffe_arcade; cd $G
nice -n 19 python3 etape2/ecrit_greffe.py | head -1
nice -n 19 python3 etape2/relogement_a5_v2.py | tail -1
NOM=${1:-ro9a} nice -n 19 python3 etape2/greffe2.py --construire 2>&1 | tail -6
md5sum constructions/${1:-ro9a}/b9/roms_ro9/sfa3ud/sz3ud.03c
