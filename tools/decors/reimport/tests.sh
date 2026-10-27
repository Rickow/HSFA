#!/bin/sh
# Tous les tests de reimport (decor $0C) ; MAME=1 : relance aussi l'essai MAME (temoin + 2 injections)
cd ${HSFA_WORKSPACE}/work/decors_ws
PY="nice -n 19 venv/bin/python"
$PY reimport/reimport.py --sortie reimport/test_psd_origine > reimport/test_psd_origine.log 2>&1
$PY reimport/test_synthetique.py --sortie reimport/test_0C > reimport/test_0C.log 2>&1
$PY reimport/injection_prog.py --sortie reimport/test_0C >> reimport/test_0C.log 2>&1
$PY reimport/test_synthetique.py --perturber --sortie reimport/test_0C_pal > reimport/test_0C_pal.log 2>&1
$PY reimport/injection_prog.py --sortie reimport/test_0C_pal >> reimport/test_0C_pal.log 2>&1
$PY reimport/test_synthetique.py --perturber --tramage ordonne --sortie reimport/test_0C_pal_reloge \
    --palettes-libres 3C,3D,3E,3F,57,58,59,5A,5B,5C,5D,5E,5F,7A,7D,7E,7F > reimport/test_0C_pal_reloge.log 2>&1
grep -H "RECOMPOSITION\|VERIFICATION\|reprises" reimport/*.log | cut -c1-220
if [ "$MAME" = 1 ]; then
  cd reimport
  OUT=essai/temoin INJ_GFX= INJ_PROG= timeout 900 mame/lance.sh lua/essai_injection.lua > essai/temoin_mame.txt 2>&1 &
  OUT=essai/inj INJ_GFX=test_0C/injection.lua INJ_PROG=test_0C/injection_prog.lua timeout 900 mame/lance.sh lua/essai_injection.lua > essai/inj_mame.txt 2>&1 &
  OUT=essai/pal INJ_GFX=test_0C_pal/injection.lua INJ_PROG=test_0C_pal/injection_prog.lua timeout 900 mame/lance.sh lua/essai_injection.lua > essai/pal_mame.txt 2>&1 &
  wait
  cd .. && $PY reimport/essai_compare.py
fi
