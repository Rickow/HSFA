#!/bin/sh
# HSFA : construit SFA3, Upper et Hyper pour le coeur FinalBurn Neo HSFA, depuis VOTRE ISO de
# Street Fighter Alpha Anthology (PS2, USA, SLUS-21317). Linux, macOS, WSL.
# Builds SFA3, Upper and Hyper for the FinalBurn Neo HSFA core from YOUR Anthology ISO.
#
#   ./construire.sh                     demande le chemin de l'ISO / asks for the ISO path
#   ./construire.sh ISO [SORTIE]        sortie par defaut / default output : ./sortie
#
# Il faut Python 3.8+. Facultatif : ffmpeg (avec libvorbis), gcc et g++ pour la musique en Ogg Vorbis
# (archives plus petites) ; sinon la musique reste en ADX. / Needs Python 3.8+; ffmpeg + gcc + g++ optional (Ogg music).
set -e
ICI=$(cd "$(dirname "$0")" && pwd)

ISO=${1:-}
if [ -z "$ISO" ]; then
  printf "Chemin de l'ISO de l'Anthology (vous pouvez glisser le fichier ici) / ISO path: "
  read -r ISO
fi
ISO=$(printf '%s' "$ISO" | sed -e "s/^[\"']//" -e "s/[\"'] *$//")
[ -f "$ISO" ] || { echo "ISO introuvable / ISO not found: $ISO"; exit 1; }
SORTIE=${2:-$ICI/sortie}

PY=$(command -v python3 || command -v python || true)
[ -n "$PY" ] || { echo "Python 3.8+ est requis / Python 3.8+ is required: https://www.python.org/downloads/"; exit 1; }
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' \
  || { echo "Python 3.8 ou plus recent est requis / Python 3.8+ is required"; exit 1; }

# environnement Python local (une seule fois) / local Python environment (once)
if [ ! -x "$ICI/.venv/bin/python" ]; then
  echo "Preparation de Python (une seule fois) / Setting up Python (once)..."
  "$PY" -m venv "$ICI/.venv"
fi
"$ICI/.venv/bin/python" -m pip install -q --disable-pip-version-check -r "$ICI/requirements.txt"

FORMAT=ogg
for outil in ffmpeg gcc g++; do command -v "$outil" >/dev/null 2>&1 || FORMAT=adx; done
if [ "$FORMAT" = ogg ] && ! ffmpeg -hide_banner -encoders 2>/dev/null | grep -q libvorbis; then FORMAT=adx; fi
if [ "$FORMAT" = adx ]; then
  echo "ffmpeg (libvorbis), gcc ou g++ absent : musique en ADX (archives d'Upper et d'Hyper plus grosses)."
  echo "ffmpeg (libvorbis), gcc or g++ missing: music kept as ADX (bigger Upper and Hyper archives)."
fi

echo "Construction (quelques minutes) / Building (a few minutes)..."
"$ICI/.venv/bin/python" "$ICI/scripts/construction/hsfa_build.py" \
  --anthology "$ISO" --sortie "$SORTIE" --jeux sfa3,upper,hyper --flux-format "$FORMAT"

echo
echo "Termine / Done. Archives pour le coeur / core archives:"
ls -1 "$SORTIE/archives/"*.zip
echo "Copiez-les dans le dossier des ROM de FinalBurn Neo (voir README) / copy them to your FBNeo ROM folder."
