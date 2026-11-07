# tools/asm68k — assembleur 68000 de la construction (hsfa_asm68k)

`hsfa_asm68k.py` assemble le code des persos MAX d'Upper MAX (sources Motorola produites chez le joueur). Il remplace
`vasmm68k_mot`, dont la licence interdit de l'embarquer dans le constructeur tout-en-un.

- **Python 3.8 ou plus, bibliothèque standard seulement**, licence MIT. Écrit de zéro, sans code de vasm.
- Il donne **la même sortie à l'octet que** `vasmm68k_mot -m68000 -spaces -Fbin -quiet [-L liste]` : binaire plat, liste
  complète (table des symboles comprise) et messages. Les optimisations implicites de vasm sont reproduites :
  - taille des branchements en plusieurs passes, avec les branchements vers l'instruction suivante supprimés ;
  - absolu court, PC-relatif ou absolu long ;
  - `moveq`, `addq`/`subq`, `lea`, `tst`, `not`, `suba` ;
  - `jmp`/`jsr` transformés en `bra`/`bsr`.
- Ligne de commande compatible : `python3 hsfa_asm68k.py -m68000 -spaces -Fbin -quiet [-maxerrors=N] [-L liste] -o
  sortie.bin source.s`. Code de retour 0 si aucune erreur. Les messages suivent le format de vasm
  (`error N in line L of "fichier": ...`).
- Bibliothèque :
  - `hsfa_asm68k.lance(argv)` : appel dans le processus, sans sous-processus ni interpréteur, d'où son intérêt pour
    l'exécutable PyInstaller ;
  - `hsfa_asm68k.assemble_fichier(chemin)` : renvoie le binaire, les symboles et la liste.

## Choix de l'assembleur dans la construction (`asm68k_choix.py`)

| `HSFA_ASM` | effet |
|---|---|
| absent / `hsfa` | hsfa_asm68k (défaut) |
| `vasm` | vasmm68k_mot : `--vasm CHEMIN`, sinon `HSFA_VASM`, sinon le PATH |
| `compare` | les deux ; échec si le binaire ou la liste diffèrent (contrôle de maintenance) |

## Couverture

- Tout le jeu du 68000, toutes tailles et tous modes d'adressage.
- Directives : `org`, `equ` / `=` / `set`, `dc` / `dcb` / `blk` / `ds` (.b/.w/.l), `even`, `cnop`, `align`,
  `ifd` / `ifnd` / `if` / `ifeq` / `ifne` / `ifgt` / `ifge` / `iflt` / `ifle` / `else` / `endif`, `end`.
- Étiquettes : globales, et locales en `.nom` ou `nom$`.
- Expressions : toutes les opérations de vasm, avec ses priorités et une arithmétique sur 32 bits signés.
- Hors du sous-ensemble : macros, `include`, `incbin`, `section`, 68020 et suivants. Ces cas donnent une erreur
  claire.

Preuves, limites et méthode : rapport de l'agent `work/assembleur68k/RAPPORT.md` (atelier).
