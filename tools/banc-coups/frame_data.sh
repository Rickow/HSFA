#!/bin/bash
# (banc_coups) FRAME DATA des persos ajoutés (sans arcade de référence) contre SuperCombo, après étalonnage sur Ryu / Ken.
#   frame_data.sh [perso ...]   (défaut : tous ; noms ci-dessous)
# Sorties : frame_data/mesures/<perso>_<module>.tsv, frame_data/ecarts.tsv, frame_data/etalonnage.txt.
# 2 MAME en parallèle (variable PARA). Construction MAX : copie max6/ (module « max » de lance.sh).
cd "$(dirname "$(readlink -f "$0")")"; B=$PWD; mkdir -p frame_data/mesures
# perso:id:modules (ref3 = arcade sfa3ud, sert d'étalonnage ou de contrôle quand le perso y existe)
LISTE="Ryu:00:ref3,ro3 Ken:01:ref3,ro3 Juli:1e:ro5,ref3 Juni:1f:ro5,ref3 Balrog:15:ro5,ref3 Guile:20:ro5 FeiLong:21:ro5
DeeJay:22:ro5 THawk:23:ro5 EvilRyu:17:ro5 ShinAkuma:24:ro5 BalrogEX:25:ro5 Eagle:26:max Maki:27:max Yun:2d:max Ingrid:2e:max"
[ $# -gt 0 ] && LISTE=$(for p in "$@"; do echo "$LISTE" | tr ' ' '\n' | grep "^$p:"; done)
travail() {
  IFS=: read -r p id mods <<< "$1"
  python3 outils/frame_data.py plan "$p" essais/fd/$p
  for m in ${mods//,/ }; do
    ./lance.sh essais/fd/$p/$m $m lua/banc_coups.lua PLAN=$B/essais/fd/$p/plan.txt PERSO=$id PERSO2=00 ISM=A >/dev/null
    python3 outils/frame_data.py mesure essais/fd/$p essais/fd/$p/$m/log.txt frame_data/mesures/${p}_$m.tsv
    echo "$p $m : $(grep -c '^R ' essais/fd/$p/$m/log.txt) essais, $(grep SAVE essais/fd/$p/$m/log.txt)"
  done
}
export -f travail; export B
echo "$LISTE" | tr ' ' '\n' | grep . | xargs -P ${PARA:-2} -I{} bash -c 'travail {}'
python3 outils/frame_data.py ecarts frame_data/etalonnage_ecarts.tsv frame_data/mesures/Ryu_ref3.tsv frame_data/mesures/Ken_ref3.tsv
python3 outils/frame_data.py etalonne frame_data/etalonnage_ecarts.tsv frame_data/ecarts.tsv frame_data/mesures/*.tsv | tee frame_data/etalonnage.txt
python3 outils/frame_data.py synthese frame_data/ecarts.tsv frame_data/FRAME-DATA.md
