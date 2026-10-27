#!/bin/bash
# Assemble tout le code 68K des persos MAX en un binaire d'essai (vasm, syntaxe Motorola) — 2026-10-07
# ./assembler.sh [sortie]   -> erreurs regroupées ; vasm : ~/outils/vasm/vasmm68k_mot
cd "$(dirname "$0")"
# (2026-10-07) sauvegarde horodatée des sources 68K à chaque assemblage
mkdir -p sauvegardes && tar czf sauvegardes/s68k_$(date +%Y%m%d_%H%M%S).tgz *.s 2>/dev/null; ls -t sauvegardes/*.tgz | tail -n +31 | xargs -r rm
S=${1:-${TMPDIR:-/tmp}}
{ echo "        org     \$200000"
  for f in commandes_voix_max.s commandes_son_max.s symboles_frames_max.s symboles_anims_max.s symboles_externes_max.s moteur_max_main.s gestionnaires_main.s contres_max.s sons_pas_max.s moteur_max_auto.s brouillon_eagle.s brouillon_maki.s brouillon_yun.s brouillon_ingrid.s acteurs_fins_max.s acteurs_fins_main.s \
           tables_explicites_eagle.s tables_explicites_maki.s tables_explicites_yun.s tables_explicites_ingrid.s donnees_max.s donnees_sauts_max.s donnees_projectiles_max.s donnees_acteurs_fins.s donnees_fins_t12c.s; do
    echo "; ==== $f"; cat $f; echo; done; } > $S/tout_max.s
~/outils/vasm/vasmm68k_mot -m68000 -spaces -Fbin -quiet -maxerrors=5000 -o $S/tout_max.bin $S/tout_max.s > $S/asm_tout.log 2>&1
echo "erreurs : $(grep -c '^error' $S/asm_tout.log)"
grep "^error" $S/asm_tout.log | sed -E 's/in line [0-9]+ of "[^"]*"//' | sort | uniq -c | sort -rn | head
