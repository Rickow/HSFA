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
| `banc_ref.sh`, `banc_ref.py`, `banc_ref_lua/` | **banc unique de non-régression** : une construction contre une référence (`--contre`), toutes les parties par un seul lanceur (environnement vide, nvram / cfg neufs, `-noreadconfig`, contexte md5 par partie), résultats de la référence en cache (rejoués si leur contexte change), résumé `RESUME.md`. Greffe : VERSUS, TRAINING, Arcade par le menu, CONTINUE, GAME OVER, 2e joueur (défi), 85 fins, 40 décors (jumelle `TIRAGE_CPU=0`), japonais (non disponible, motif écrit) ; Upper MAX : Arcade, croisés, fins. États de DIAGNOSTIC par construction (sauvegarde / chargement par le Lua, jamais `-state`), jamais comptés comme preuve. |
| `preuve_traces.py` | compare les sorties du banc unique à des traces établies par d'autres harnais (autres noms de fichiers). |
| `banc_jour.conf.example` | réglages du banc de jour : versions figées, places, budget, étapes. Copier en `banc_jour.conf`. |
| `compare_zips.py` | md5 des zips de deux sorties de construction, et membres qui changent. |

```sh
source config.env                         # HSFA_WORKSPACE (voir config.example.env)
tools/bancs/lance_emu --liste             # ce qui tourne, pour qui (et les émulateurs « hors registre »)
tools/bancs/lance_emu --agent essai -- mame sfa3u ...   # attend une place libre
tools/bancs/banc_jour.sh --sec            # essai à blanc : versions, empreintes attendues, commandes, durée
tools/bancs/banc_jour.sh                  # le banc complet -> <workspace>/work/banc_jour/AAAA-MM-JJ/RESUME.md
tools/bancs/banc_ref.sh ro9a45_fige --contre ro9a44_fige [--parties versus,fins] [--attendus F] [--upper]
                                          # banc unique -> <workspace>/work/banc_unique/runs/<nom>/RESUME.md
```

Banc unique (`banc_ref.sh --help`) : tout vient de la construction essayée (ROM, blocs, banques, tuiles `decors_gfx`,
`hsfa_gfx_max.bin`) ; les tuiles communes viennent des références figées (`work/references/<VERSION>` de
`banc_jour.conf`). La navigation du menu s'adapte seule à l'interrupteur `MENU_CURSEUR_ARCADE` lu dans `greffe.json`.
Deux parties ne se comparent que si leurs lignes « banc » de contexte sont égales (cps2f, Lua, tuiles communes,
recette) ; sinon « NON COMPARABLE ». Le verdict de chaque partie (exception, blocage, scène non atteinte) ne dépend pas
de la comparaison. Les différences déclarées dans un fichier `--attendus` sont « attendues », les autres « à qualifier ».
Fichiers d'attendus : `banc_ref_attendus/` (une ligne par différence voulue, avec sa justification ; « ~motif » = expression
rationnelle sur le détail). Arrêt d'un banc : `kill <PID du script>` (il arrête ses `lance_emu` et ses émulateurs par PID ;
`lance_emu --arrete` seul laisse vivant un `lance_emu` qui attend une place). États de diagnostic : `--diag-sauve IMAGE` /
`--diag-charge NOM` (une partie, sauvegarde / chargement par le Lua, nom = empreinte de la construction, refus sinon ;
le résumé l'écrit « DIAGNOSTIC », jamais une preuve). Preuve à une lecture : `preuve_traces.py FAMILLE BANC ETABLI [PREFIXE]`.
Atelier (cache, parties, états de diagnostic) : `BANC_REF_ATELIER`, défaut `<workspace>/work/banc_unique` ; écran :
`BANC_REF_DISPLAY` (Xvfb lancé s'il manque ; jamais `:0`).

Le banc de jour lit les constructions figées de l'espace de travail : `work/references/<version>`,
`work/greffe_arcade/constructions/ro9a<N>_fige` et les copies MAX de `work/banc_coups/`. Les scripts Lua viennent de
`work/mame` (copie localisée de `src/hsfa/mame`, voir `scripts/localiser.py --lua`) et de `tools/hyper-etats`,
`tools/greffe-arcade/lua`, `tools/banc-coups/lua`. Aucune donnée de jeu n'est dans ce dossier.
