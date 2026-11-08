#!/bin/bash
# (banc_coups) NON-RÉGRESSION DE L'INTÉGRATION MAX, relançable à chaque lot :
#   banc_max.sh <dossier candidat (copie figée d'une construction MAX)> [coups|fins|max|croises|arcade ...]
# Copier d'abord la construction (cp -a agent_integration_max/banc_maxN <ici>/maxNN), y laisser env_max_cache.txt
# (sortie figée de max_cache.py) et MD5_COPIE.txt. Référence : references/v150/ro5 (journaux en cache, essais/max_ref).
# Sorties : resultats_max/<candidat>/ (TSV, RESUME-MAX.md). Variables : MAXMAME (défaut 2), PERSOS="Ryu,Ken" (étape coups).
cd "$(dirname "$(readlink -f "$0")")" && exec nice -n 19 python3 outils/banc_max.py "$@"
