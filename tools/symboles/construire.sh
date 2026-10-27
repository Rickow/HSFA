#!/bin/sh
# Reconstruit toute la carte des symboles de ro3 à partir de l'image traduite COURANTE du banc
# (roms_tr + carte_image.txt, générés ensemble par mame_test.py). N'écrit que dans ce dossier.
set -e
D=$(dirname "$(readlink -f "$0")")
M=${HSFA_WORKSPACE}/work/mame
cd "$D"
cp "$M/carte_image.txt" _carte_image_snapshot.txt
python3 - <<'PY'
d='${HSFA_WORKSPACE}/work/mame/roms_tr/sfa3ud/'
n=["sz3ud.03c","sz3ud.04c","sz3.05c","sz3.06c","sz3.07c","sz3.08c","sz3.09c","sz3.10b"]
sw=b''.join(open(d+x,'rb').read() for x in n)
open('_trad.bin','wb').write(bytes(b for i in range(0,len(sw),2) for b in (sw[i+1],sw[i])))
PY
rm -f _cache/trad.pkl _cache/trad.bin
cd outils
nice -n 19 python3 aligne.py | grep -v '^  A5'
nice -n 19 python3 carte_fonctions.py
nice -n 19 python3 auto.py
nice -n 19 python3 paires_a5.py
nice -n 19 python3 fusion.py
cd ..
nice -n 19 python3 annoter.py --carte _carte_image_snapshot.txt
