#!/bin/bash
# shot.sh NOM : capture F8 de PCSX2 -> $PS2_DIR/shots/NOM.png (réduite à 640x480) ; affiche le chemin
ICI=$(dirname "$(readlink -f "$0")"); . "$ICI/env_ps2.sh"
S=$PS2_DIR/cfg/PCSX2/snaps; mkdir -p "$S" "$PS2_DIR/shots"; n0=$(ls "$S" | wc -l)
"$ICI/touche.sh" F8 60 || exit 2
for i in $(seq 30); do [ "$(ls "$S" | wc -l)" -gt "$n0" ] && break; sleep 0.2; done; sleep 1.5
f=$(ls -t "$S"/*.png | head -1)
python3 -c "import sys; from PIL import Image; Image.open(sys.argv[1]).convert('RGB').resize((640,480)).save(sys.argv[2])" "$f" "$PS2_DIR/shots/$1.png"
echo "$PS2_DIR/shots/$1.png"
