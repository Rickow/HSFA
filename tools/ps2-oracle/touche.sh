#!/bin/bash
# touche.sh <touche> [durée ms=120] : appui (xdotool) sur la fenêtre du PCSX2 lancé par lance_ps2.sh, dans l'écran $PS2_DISPLAY.
# Vérifie avant la touche : écran dédié joignable (getdisplaygeometry), PID de run/pcsx2.pid vivant, fenêtre de CE PID.
ICI=$(dirname "$(readlink -f "$0")"); . "$ICI/env_ps2.sh"
PID=$(cat "$PS2_DIR/run/pcsx2.pid" 2>/dev/null); [ -n "$PID" ] && [ -d "/proc/$PID" ] || { echo "touche.sh : PCSX2 lancé par lance_ps2.sh introuvable" >&2; exit 2; }
DISPLAY=$PS2_DISPLAY xdotool getdisplaygeometry > /dev/null || exit 2
W=$(DISPLAY=$PS2_DISPLAY xdotool search --pid "$PID" --name 'Street Fighter Alpha Anthology' | head -1)
[ -n "$W" ] || { echo "touche.sh : fenêtre du jeu (PID $PID) introuvable sur $PS2_DISPLAY" >&2; exit 2; }
DISPLAY=$PS2_DISPLAY xdotool windowfocus --sync "$W" 2>/dev/null
DISPLAY=$PS2_DISPLAY xdotool keydown --window "$W" "$1"; sleep "$(echo "${2:-120}/1000" | bc -l)"; DISPLAY=$PS2_DISPLAY xdotool keyup --window "$W" "$1"
