#!/bin/bash
# env_ps2.sh — réglages communs de l'oracle PCSX2 (à SOURCER par les autres scripts de ce dossier).
#   PS2_DIR      dossier de travail (copie de configuration cfg/, run/ : socket PINE et PID, shots/) ; défaut : $PWD/ps2
#   PS2_ISO      ISO de l'Anthology (OBLIGATOIRE pour lance_ps2.sh) : celle de l'utilisateur, jamais publiée
#   PS2_DISPLAY  écran Xvfb DÉDIÉ (défaut :97) ; « :0 » (l'écran de l'utilisateur) est REFUSÉ
#   PINE_SOCK    socket PINE (défaut $PS2_DIR/run/pcsx2.sock)
# Règles (AGENTS.md §2.7, consignes du 07/11) : jamais la configuration ni les sauvegardes PCSX2 de l'utilisateur
# (cfg/ est une COPIE) ; xdotool toujours avec l'écran écrit en dur et sur la fenêtre du PID lancé par lance_ps2.sh.
PS2_DIR=${PS2_DIR:-$PWD/ps2}
PS2_DISPLAY=${PS2_DISPLAY:-:97}
PINE_SOCK=${PINE_SOCK:-$PS2_DIR/run/pcsx2.sock}
export PS2_DIR PS2_DISPLAY PINE_SOCK
case "$PS2_DISPLAY" in :0|:0.*|"") echo "env_ps2.sh : écran $PS2_DISPLAY refusé (écran de l'utilisateur) : utiliser un Xvfb dédié" >&2; exit 2;; esac
