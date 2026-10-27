#!/bin/bash
# banc_psp.sh <dossier candidat> [options de banc_psp.py]  — mode B du banc des coups : PSP (oracle) contre candidat Upper MAX.
cd "$(dirname "$(readlink -f "$0")")" && exec nice -n 19 ${HSFA_WORKSPACE}/venv/bin/python3 -I banc_psp.py "$@"
