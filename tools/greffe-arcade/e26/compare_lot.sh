#!/bin/bash
# (e26) compare_plans_u.py PAR_DECOR=1 pour chaque perso : Upper traces/<PU>_u_<p>.rec contre ro9a traces/<PH>_h_<p>.rec
# Usage : compare_lot.sh PU PH "persos" > resume ; detail dans e26/cmp_<PH>/<p>.txt
G=${HSFA_WORKSPACE}/work/greffe_arcade; mkdir -p $G/e26/cmp_$2
for p in $3; do
  PAR_DECOR=1 ${HSFA_WORKSPACE}/work/decors_sfa2/export/py3 $G/e26/compare_plans_u.py $G/traces/$1_u_$p.rec $G/traces/$2_h_$p.rec > $G/e26/cmp_$2/$p.txt 2>&1
  awk -v p=$p '/^images/{d=$14} /scroll2 tilemap/{s2=$6} /scroll3 tilemap/{s3=$6} /scroll1 VRAM/{s1=$9} /^  ecran/{print p, "decor", d, "s2", s2, "s3", s3, "s1_vram_cases", s1}' $G/e26/cmp_$2/$p.txt
done
