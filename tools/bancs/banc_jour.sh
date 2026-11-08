#!/bin/bash
# banc_jour.sh — BANC DE JOUR (à lancer le matin ; la machine ne tourne pas la nuit). Détail : banc_jour.py (en-tête).
#   banc_jour.sh --sec          essai à blanc : versions, empreintes attendues, commandes, durée estimée (rien n'est lancé)
#   banc_jour.sh                tout (≤ BUDGET_H, défaut 8 h) -> work/banc_jour/AAAA-MM-JJ/RESUME.md
#   banc_jour.sh --etapes upper_fins --cles 00     une seule partie (essai)
# Réglages : banc_jour.conf (VERSION, GREFFE, MAX_VALIDE, PLACES_BANC, BUDGET_H, ETAPES). À lancer en fond :
#   nohup ${HSFA_WORKSPACE}/work/outils/banc_jour.sh > ${HSFA_WORKSPACE}/work/banc_jour/dernier.log 2>&1 &
# Arrêt : ${HSFA_WORKSPACE}/work/outils/lance_emu --arrete banc_jour (arrête les parties ; tuer aussi ce script par son PID).
exec nice -n 19 python3 -B "$(dirname "$(readlink -f "$0")")/banc_jour.py" "$@"
