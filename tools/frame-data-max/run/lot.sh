#!/bin/bash
# run/lot.sh <perso> <ism> ... : relevés PSP en série (un PPSSPP), journal run/psp_<perso>_<ism>.out
cd ${HSFA_WORKSPACE}/work/frame_data_max/outils
while [ $# -ge 2 ]; do
  nice -n 19 ${HSFA_WORKSPACE}/venv/bin/python3 -I fd.py psp $1 $2 > ../run/psp_$1_$2.out 2>&1
  shift 2
done
