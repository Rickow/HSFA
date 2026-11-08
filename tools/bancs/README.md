# Bancs : lanceur commun, empreinte, banc de jour

Outils communs à toutes les mesures du projet. Dans l'espace de travail, ils vivent dans `<workspace>/work/outils/` :
les autres bancs (`tools/banc-coups`, `tools/frame-data-max`, `tools/greffe-arcade/outils`…) les appellent par ce chemin.
Copier ce dossier là, ou y faire un lien.

| fichier | rôle |
|---|---|
| `lance_emu` | **lanceur commun** des émulateurs (MAME / fork, FBNeo, PPSSPP, PCSX2). Il applique `nice -n 19` et limite les places de la machine (verrous `flock`). Il tient un registre (`registre_emu/`, ou `LANCE_EMU_REGISTRE`) et refuse `-state` pour MAME. Les arrêts se font par PID enregistré, jamais par `pkill -f`. |
| `empreinte.py`, `empreinte.sh`, `empreinte.lua` | **empreinte** de ce que l'émulateur charge vraiment, calculée sur la ligne de commande effective. `ATTENDU_MD5` / `ATTENDU_REF` : en cas d'écart, rien n'est lancé (code 86). `empreinte.lua` donne une preuve interne : CRC de la ROM vue par le 68000. |
| `references.example.tsv` | références nommées pour `ATTENDU_REF` (versions figées). Copier en `references.tsv` et adapter. |
| `banc_jour.sh`, `banc_jour.py`, `banc_jour_lance.sh` | **banc de jour** : non-régression des 4 jeux sur les dernières versions FIGÉES, en 8 étapes et en 8 h au plus. Les étapes sont : commandes et fins SFA3, fins d'Upper, VERSUS d'Hyper, fins de la greffe, Upper MAX. |
| `banc_jour.conf.example` | réglages du banc de jour : versions figées, places, budget, étapes. Copier en `banc_jour.conf`. |
| `compare_zips.py` | md5 des zips de deux sorties de construction, et membres qui changent. |

```sh
source config.env                         # HSFA_WORKSPACE (voir config.example.env)
tools/bancs/lance_emu --liste             # ce qui tourne, pour qui (et les émulateurs « hors registre »)
tools/bancs/lance_emu --agent essai -- mame sfa3u ...   # attend une place libre
tools/bancs/banc_jour.sh --sec            # essai à blanc : versions, empreintes attendues, commandes, durée
tools/bancs/banc_jour.sh                  # le banc complet -> <workspace>/work/banc_jour/AAAA-MM-JJ/RESUME.md
```

Le banc de jour lit les constructions figées de l'espace de travail : `work/references/<version>`,
`work/greffe_arcade/constructions/ro9a<N>_fige` et les copies MAX de `work/banc_coups/`. Les scripts Lua viennent de
`work/mame` (copie localisée de `src/hsfa/mame`, voir `scripts/localiser.py --lua`) et de `tools/hyper-etats`,
`tools/greffe-arcade/lua`, `tools/banc-coups/lua`. Aucune donnée de jeu n'est dans ce dossier.
