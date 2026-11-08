#!/bin/bash
# lance_ps2.sh : PCSX2 (COPIE de configuration $PS2_DIR/cfg) dans l'Xvfb $PS2_DISPLAY, ISO $PS2_ISO, PINE activé
# (socket $PS2_DIR/run/pcsx2.sock). Passe par le lanceur commun (lance_emu --exec : même PID, écrit dans run/pcsx2.pid).
#   PS2_ISO=<iso> PS2_DIR=<dossier> [PS2_DISPLAY=:97] [LANCE_EMU=<chemin de lance_emu>] lance_ps2.sh &
# Préalables : Xvfb lancé sur $PS2_DISPLAY par vous ; $PS2_DIR/cfg/PCSX2 = copie d'une configuration avec PINE activé
# (EmuCore/EnablePINE=true) ; ne jamais pointer XDG_CONFIG_HOME vers la configuration de l'utilisateur.
ICI=$(dirname "$(readlink -f "$0")"); . "$ICI/env_ps2.sh"
: "${PS2_ISO:?PS2_ISO : ISO de l Anthology}"
[ -d "$PS2_DIR/cfg/PCSX2" ] || { echo "lance_ps2.sh : $PS2_DIR/cfg/PCSX2 absent (copier une configuration PCSX2)" >&2; exit 2; }
DISPLAY=$PS2_DISPLAY xdotool getdisplaygeometry > /dev/null 2>&1 || { echo "lance_ps2.sh : écran $PS2_DISPLAY injoignable (Xvfb ?)" >&2; exit 2; }
LANCE_EMU=${LANCE_EMU:-$ICI/../bancs/lance_emu}
mkdir -p "$PS2_DIR/run" "$PS2_DIR/shots"; chmod 700 "$PS2_DIR/run"
echo $$ > "$PS2_DIR/run/pcsx2.pid"     # exec ci-dessous : PCSX2 garde ce PID
exec env -u WAYLAND_DISPLAY DISPLAY=$PS2_DISPLAY QT_QPA_PLATFORM=xcb XDG_CONFIG_HOME=$PS2_DIR/cfg XDG_RUNTIME_DIR=$PS2_DIR/run \
  HSFA_AGENT=${HSFA_AGENT:-ps2_oracle} "$LANCE_EMU" --exec --agent "${HSFA_AGENT:-ps2_oracle}" -- \
  nice -n 19 pcsx2-qt -batch -fastboot -- "$PS2_ISO" > "$PS2_DIR/pcsx2.log" 2>&1
