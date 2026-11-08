#!/bin/bash
# vue.sh NOM : capture (shot.sh) + vignette 320x240 $PS2_DIR/shots/NOMs.png
ICI=$(dirname "$(readlink -f "$0")"); . "$ICI/env_ps2.sh"
"$ICI/shot.sh" "$1" > /dev/null || exit 2
python3 -c "import sys; from PIL import Image; Image.open(sys.argv[1]).resize((320,240)).save(sys.argv[2])" "$PS2_DIR/shots/$1.png" "$PS2_DIR/shots/$1s.png"
