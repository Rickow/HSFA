#!/bin/bash
# frame_data.sh <copie figée Upper MAX> [--ref <copie précédente>] [--persos "eagle maki yun ingrid"] [--ismes "A X V"]
#               [--jobs N] [--mesure-seule] [--filtre RE]
# BANC REJOUABLE des données d'images des 4 persos MAX : rejoue dans Upper (MAME, module max du banc des coups) les entrées
# EFFECTIVES des relevés PSP en cache (psp_cache/, faits par outils/fd.py psp ; la PSP n'est PAS relancée), mesure les deux côtés.
#
# UNITÉ = TOUR DE JEU (depuis le 03/11). PSP : un relevé par tour par construction (point d'arrêt 0x55650 au début du traitement de
# chaque joueur, indexé par le compteur de tours 0x092E51C6 ; les images PSP n'interviennent pas). Upper : lua/tours.lua relève J1 / J2
# au moment où le 68000 écrit le compteur de tours $FF851C (début du tour = état « après le tour précédent », comme sur PSP). Les images
# MAME où $FF851C n'est pas écrit sont des images de RALENTISSEMENT du 68000 (tour plus long qu'une image) : elles ne comptent pas et
# sont comptées à part, colonne `ralentis` (w/h/b = à vide / touche / garde). Voir RAPPORT.md §1.6.
#
# Sorties : resultats/<copie>/{frame_data_<perso>.tsv,.md, ecarts.tsv, bilan.md, lignes.json} = mesure EN TOURS ;
#           resultats/<copie>/images/… = même chose en IMAGES BRUTES (ancien mode, pour comparer) ;
#           resultats/<copie>/modes.md = écarts qui disparaissent en tours (dus aux ralentissements) / qui restent (vrais défauts) ;
#           avec --ref : resultats/<copie>/bouge_depuis_<ref>.md (valeurs Upper qui ont bougé, en tours).
# Options : --jobs N (MAME en parallèle, défaut 3, via work/outils/lance_emu, étiquette $HSFA_AGENT ou frame_data) ;
#           --mesure-seule : ne relance pas MAME, remesure les traces de essais/<copie>/ (traces sans lignes G, d'avant le 03/11 :
#           repli « images sans tour sautées », méthode R33, moins exact) ; --filtre RE : seulement les essais dont l'id correspond.
# Empreinte : chaque lot vérifie que MAME charge la copie demandée (empreinte.py, contrôle MD5_COPIE) et la preuve interne
# (empreinte.lua : CRC de la ROM programme vue par le 68000) -> essais/<copie>/<perso>_<isme>/empreinte.txt ; écart = ARRÊT.
set -u
cd "$(dirname "$(readlink -f "$0")")"
CAND=$(readlink -f "$1"); shift
REF=""; PERSOS="eagle maki yun ingrid"; ISMES="A X V"; JOBS_N=3; SEULE=0
while [ $# -gt 0 ]; do
  case $1 in --ref) REF=$2; shift 2;; --persos) PERSOS=$2; shift 2;; --ismes) ISMES=$2; shift 2;; --jobs) JOBS_N=$2; shift 2;;
    --mesure-seule) SEULE=1; shift;; --filtre) export FD_FILTRE=$2; shift 2;; *) echo "option inconnue $1"; exit 2;; esac
done
export HSFA_AGENT=${HSFA_AGENT:-frame_data}
PY=${HSFA_WORKSPACE}/venv/bin/python3
[ -f "$CAND/env_max_cache.txt" ] || { echo "pas une copie figée MAX : $CAND"; exit 2; }
if [ $SEULE = 0 ]; then
  JOBS=()
  for p in $PERSOS; do for i in $ISMES; do [ -f psp_cache/${p}_$i.json ] && JOBS+=("$p $i"); done; done
  printf '%s\n' "${JOBS[@]}" | xargs -P "$JOBS_N" -I{} sh -c "cd outils && nice -n 19 $PY -I fd.py upper '$CAND' {}" \
    || { echo "ARRÊT (empreinte ou lancement) : voir essais/$(basename "$CAND")/*/empreinte.txt"; exit 86; }
fi
cd outils && nice -n 19 $PY -I fd.py mesure "$CAND" --images && nice -n 19 $PY -I fd.py mesure "$CAND" \
  && nice -n 19 $PY -I modes.py "$CAND" && nice -n 19 $PY -I annexe.py "$CAND"
[ -n "$REF" ] && nice -n 19 $PY -I bouge.py "$CAND" "$REF"
echo "résultats : $(readlink -f ../resultats/$(basename "$CAND"))"
