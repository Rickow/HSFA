#!/bin/sh
# zoom.sh <page> <x0> <y0> <x1> <y1> : zone d'une page du PDF du guide (fractions 0-1), rendue a 300 dpi
# GUIDE = dossier de travail (hors depot), PDF = guide scanne (defaut $GUIDE/manuel.pdf)
GUIDE=${GUIDE:-.}; PDF=${PDF:-$GUIDE/manuel.pdf}; W=2480; H=3070
p=$1
x=$(python3 -c "print(int($2*$W))"); y=$(python3 -c "print(int($3*$H))")
w=$(python3 -c "print(int(($4-$2)*$W))"); h=$(python3 -c "print(int(($5-$3)*$H))")
mkdir -p "$GUIDE/zoom"; o=$GUIDE/zoom/z-$p-$2-$3
pdftoppm -r 300 -f "$p" -l "$p" -x "$x" -y "$y" -W "$w" -H "$h" -png -singlefile "$PDF" "$o"
echo "$o.png"
