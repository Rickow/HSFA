#!/bin/bash
# Relance complète de la passe de conversion MAX -> image Upper (à faire après CHAQUE reconstruction d'Upper ou
# modification des sources MAX). Aucun fichier hors de ce dossier n'est écrit.
#   1. convertit_max.py   : sources converties + adresses_upper.s (résolution va MIPS -> carte actuelle) + journal
#   2. valide_contre_upper.py : comparaison des réécritures aux sites arcade alignés de l'image (realign.pkl)
#   3. blocs externes (frames + animations + animations de fin) : convertit_frames.py, contrôle des pas (Ryu)
#   4. assemblage vasm d'essai du code (symboles des blocs externes : symboles_*_max.s de la session MAX)
set -e
cd "$(dirname "$0")"
python3 convertit_max.py "$@" > sortie/derniere_execution.txt
grep -E '"(réécrit|inchangé|NON RÉSOLU|AVERTISSEMENT|adresses_resolues|adresses_non_resolues|swap_annules)"' sortie/derniere_execution.txt
head -1 sortie/controle_image.txt
python3 valide_contre_upper.py | head -6
echo "acteurs de fin (contre le code d'acteurs d'Upper, arcade \$A5000-\$AD000) :"; python3 valide_contre_upper.py --acteurs | head -6
# blocs externes des persos MAX (session MAX, disposition arcade : frames_*.s, anims_*.s, fin_anims_*.s) -> UN binaire
# par bloc (ext_d40000.bin = $D40000-$D7FFFF…), disposition image ; contrôle taille / chevauchement / symboles
ROS="${ROSETTE:-$HOME/CLAUDE CODE/sfa3max-psp-widescreen/work/re/rosette_code}"
python3 controle_pas_ryu.py
python3 convertit_frames.py "$ROS"
# adresses des frames et des animations (symboles_*_max.s de la session MAX) ; à défaut, valeurs factices pour l'essai
if [ -f "$ROS/symboles_frames_max.s" ]; then cp "$ROS/symboles_frames_max.s" sortie/_essai_frames.s
  if [ -f "$ROS/symboles_anims_max.s" ]; then cat "$ROS/symboles_anims_max.s" >> sortie/_essai_frames.s; fi
else grep -ohE '\bF2[6-9]_[0-9]+\b' sortie/tables_explicites_*.s | sort -u | awk '{printf "%s equ $%X\n", $1, NR*4+0x700000}' > sortie/_essai_frames.s; fi
cat sortie/_essai_frames.s sortie/tout_max_upper.s > sortie/_essai.s
~/outils/vasm/vasmm68k_mot -m68000 -spaces -Fbin -quiet -maxerrors=5000 -o sortie/_essai.bin sortie/_essai.s > sortie/asm.log 2>&1 \
  && echo "vasm : 0 erreur ($(stat -c %s sortie/_essai.bin) octets)" \
  || { echo "vasm : $(grep -c '^error' sortie/asm.log) erreurs (sortie/asm.log)"; exit 1; }
