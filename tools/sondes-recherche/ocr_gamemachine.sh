#!/bin/sh
# OCR japonais des numéros de Game Machine (PDF scannés d'onitama.tv), pour repérer les pages utiles au livre.
# Usage : ocr_gamemachine.sh DOSSIER_PDF DOSSIER_TESSDATA DOSSIER_SORTIE
# Les PDF et le texte OCR restent hors dépôt (textes protégés) ; seules les références et citations courtes vont au livre.
set -e
IN="$1"; TD="$2"; OUT="$3"; mkdir -p "$OUT"
for pdf in "$IN"/*.pdf; do
  n=$(basename "$pdf" .pdf); mkdir -p "$OUT/$n"
  pdftoppm -r 200 -gray -png "$pdf" "$OUT/$n/p"
  for img in "$OUT/$n"/p-*.png; do
    b=$(basename "$img" .png)
    [ -f "$OUT/$n/$b.txt" ] || tesseract "$img" "$OUT/$n/$b" --tessdata-dir "$TD" -l jpn+jpn_vert --psm 3 >/dev/null 2>&1 || true
  done
done
