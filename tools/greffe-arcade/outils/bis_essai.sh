#!/bin/bash
# (28/10) bissection : bis_essai.sh NOM fichier.json -> construit e11j + DECISIONS_ANCIENNES, joue 10 Z3, 18 Z3, 0d Z3, 1d Z3
G=${HSFA_WORKSPACE}/work/greffe_arcade; cd $G
outils/construit_e3.sh $1 "LISTE_ARCADE=$G/donnees/couv_tous_liste_arcade.pkl ENTIERS_SANS_CREUX=1 FEN2_DEBUT=C70000 TROUS_PLAN=1 PTR_EXCLUS=$G/donnees/ptr_exclus_e11.txt DECISIONS_ANCIENNES=$2" > traces/construit_$1.log 2>&1
printf "$1 10 Z3 b_$1\n$1 18 Z3 b_$1\n$1 0d Z3 b_$1\n$1 1d Z3 b_$1\n" > outils/liste_b_$1.txt
P=4 outils/joue.sh outils/liste_b_$1.txt > /dev/null 2>&1
for t in traces/b_$1_*/; do echo "$t $(grep -E "EXC|^FIN" $t/journal.txt | head -1 | cut -c1-60)"; done
