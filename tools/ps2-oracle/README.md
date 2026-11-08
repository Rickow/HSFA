# PCSX2 comme oracle (Xvfb + PINE)

Pour comparer au jeu PS2 d'origine (musique, jauges, écrans), PCSX2 tourne sans écran visible, dans un Xvfb dédié.
Il est piloté au clavier (xdotool) et lu par PINE (lecture de la mémoire ; écritures limitées).

Règles (AGENTS.md §2) :
- jamais la configuration ni les sauvegardes PCSX2 de l'utilisateur : `$PS2_DIR/cfg` est une **copie**, avec PINE activé ;
- xdotool toujours sur l'écran dédié écrit en dur (`PS2_DISPLAY`, `:0` refusé), après `getdisplaygeometry`, sur la
  fenêtre du PID lancé par `lance_ps2.sh` ;
- arrêt par PID (`tools/bancs/lance_emu --arrete`) ;
- écritures PINE permises : vie de l'adversaire et niveau de jauge, pour des essais.

```sh
Xvfb :97 -screen 0 1280x960x24 &                       # écran dédié
export PS2_DIR=$PWD/ps2 PS2_DISPLAY=:97 PS2_ISO=<votre ISO de l'Anthology>
cp -a <copie d'une configuration PCSX2> "$PS2_DIR/cfg/PCSX2"
tools/ps2-oracle/lance_ps2.sh &                        # PCSX2 par lance_emu (PID dans $PS2_DIR/run/pcsx2.pid)
tools/ps2-oracle/touche.sh Return                      # appui
tools/ps2-oracle/pine.py r16 <adresse>                 # lecture
tools/ps2-oracle/shot.sh nom                           # capture F8 -> $PS2_DIR/shots/nom.png
tools/ps2-oracle/jauge_ps2.sh essai <adresse> 00 30 60 # mot écrit en boucle + capture, par valeur
```
Réécrits pour la publication à partir des outils de l'agent `hyper_jauge` (07/11), qui avaient le dossier, l'ISO et
l'écran codés en dur. Non relancés après réécriture (aucun émulateur pendant la préparation) : faire un essai avant usage.
