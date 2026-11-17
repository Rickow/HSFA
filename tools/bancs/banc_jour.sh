#!/bin/bash
# banc_jour.sh — BANC DE JOUR (à lancer le matin ; la machine ne tourne pas la nuit). Détail : banc_jour.py (en-tête).
#   banc_jour.sh --sec          essai à blanc : versions, empreintes attendues, commandes, durée estimée (rien n'est lancé)
#   banc_jour.sh                tout (≤ BUDGET_H, défaut 8 h) -> work/banc_jour/AAAA-MM-JJ/RESUME.md
#   banc_jour.sh --etapes upper_fins --cles 00     une seule partie (essai)
# Réglages : banc_jour.conf (VERSION, GREFFE, MAX_VALIDE, PLACES_BANC, BUDGET_H, ETAPES). À lancer en fond :
#   nohup ${HSFA_WORKSPACE}/work/outils/banc_jour.sh > ${HSFA_WORKSPACE}/work/banc_jour/dernier.log 2>&1 &
# Arrêt : ${HSFA_WORKSPACE}/work/outils/lance_emu --arrete banc_jour (arrête les parties ; tuer aussi ce script par son PID).
# (banc_unique, 16/11) Étapes banc_ref_greffe / banc_ref_max : BANC UNIQUE (work/banc_unique/banc_ref.sh) sur les copies
# figées témoins REF_GREFFE / REF_MAX de banc_jour.conf, rejouées et comparées à leur CACHE (même harnais, contexte md5 ;
# une référence dont le contexte a changé est rejouée et signalée). Elles remplacent greffe_fins / max_* de banc_jour.py
# (mêmes parties, plus VERSUS, TRAINING, Arcade par le menu, CONTINUE, GAME OVER, 2e joueur, décors). Résumés copiés dans
# work/banc_jour/AAAA-MM-JJ/banc_ref_<greffe|max>.md. --sec : affiche les commandes et l'essai à blanc de banc_ref.
O="$(dirname "$(readlink -f "$0")")"; H=${HSFA_WORKSPACE:-$HOME/hsfa}; CONF=$O/banc_jour.conf
BR=${BANC_REF:-$O/banc_ref.sh}; [ -x "$BR" ] || BR=$H/work/banc_unique/banc_ref.sh   # dépôt : tools/bancs/banc_ref.sh ; atelier : work/banc_unique
val() { sed -n "s/^$1=\"\{0,1\}\([^\"#]*\)\"\{0,1\}.*/\1/p" "$CONF" | tail -n 1 | sed 's/ *$//'; }
ET=$(val ETAPES); SEC=""; ARGS=()
while [ $# -gt 0 ]; do case $1 in --etapes) ET=${2//,/ }; shift 2;; --sec) SEC=1; ARGS+=("$1"); shift;; *) ARGS+=("$1"); shift;; esac; done
PY=""; for e in $ET; do case $e in banc_ref_*) ;; *) PY="$PY,$e";; esac; done
rc=0
[ -n "$PY" ] && { nice -n 19 python3 -B "$O/banc_jour.py" --etapes "${PY#,}" "${ARGS[@]}"; rc=$?; }
J=$H/work/banc_jour/$(date +%F); P=$(val PLACES_BANC)
for e in $ET; do
  case $e in
    banc_ref_greffe) C=$(val REF_GREFFE); JU=$(val REF_GREFFE_JUMELLE); PA=$(val BANC_REF_PARTIES_GREFFE)
      CMD=("$BR" "$C" --contre "$C" ${PA:+--parties "$PA"} ${JU:+--jumelle "$JU"} --places "${P:-4}" --nom "jour_$(date +%F)_greffe");;
    banc_ref_max) C=$(val REF_MAX); [ -n "$C" ] || C=$(val MAX_VALIDE); PA=$(val BANC_REF_PARTIES_MAX)
      CMD=("$BR" "$C" --contre "$C" ${PA:+--parties "$PA"} --places "${P:-4}" --nom "jour_$(date +%F)_max");;
    *) continue;;
  esac
  if [ -n "$SEC" ]; then echo; echo "== $e : ${CMD[*]}"; "${CMD[@]}" --sec | head -n 1; continue; fi
  mkdir -p "$J"; "${CMD[@]}" > "$J/banc_ref_${e#banc_ref_}.log" 2>&1; r=$?; [ $r -ne 0 ] && rc=$r
  cp "$(dirname "$BR")/runs/jour_$(date +%F)_${e#banc_ref_}/RESUME.md" "$J/banc_ref_${e#banc_ref_}.md" 2>/dev/null
  echo "$e : $(head -n 1 "$J/banc_ref_${e#banc_ref_}.md" 2>/dev/null) (code $r)"
done
exit $rc
