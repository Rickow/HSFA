#!/bin/bash
# (banc_coups) BANC DE TEST DES COUPS — rejouable apres chaque correction du traducteur.
#   banc_coups.sh <module> [perso] [version]
#   module  : ro3 (SFA3, oracle arcade sfa3ud) | ro5 (Upper) | ro9 (Hyper)
#   perso   : nom du tableau entre guillemets (« Ryu », « M. Bison ») ou « tous » (defaut)
#   version : ro3/ro5 : X | A | V (isme ; defaut les trois) ; ro9 : Z | Z2 | A | Z3 | Z3X | Z3A | Z3V (defaut tout)
# Constructions testees : work/references/v150 (variable REFS=<dossier> pour une autre construction figee, voir lance.sh).
# Sorties : resultats/<module>/<perso>_<version>.tsv, resultats/coups_<module>.tsv, resultats/RESUME.md.
# Variables : MAXMAME (defaut 4) ; REPRISE=1 saute les travaux deja faits ; ORACLE=refjp : oracle japonais 980727
# (resultats/<module>-jp, journal de la traduction repris si meme plan).
cd "$(dirname "$(readlink -f "$0")")" && exec nice -n 19 python3 outils/banc.py "$@"
