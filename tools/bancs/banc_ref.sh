#!/bin/bash
# banc_ref.sh — BANC UNIQUE de non-régression (banc_unique, 16/11) : CONSTRUCTION --contre REFERENCE [options] ;
# détail : banc_ref.py (docstring) ou banc_ref.sh --help. Résultat : runs/<nom>/RESUME.md. DISPLAY de l'atelier en dur
# (BANC_REF_DISPLAY, défaut :97 = Xvfb de banc_unique ; jamais :0). Arrêt : lance_emu --arrete banc_unique + PID du script.
exec nice -n 19 python3 -B "$(dirname "$(readlink -f "$0")")/banc_ref.py" "$@"
