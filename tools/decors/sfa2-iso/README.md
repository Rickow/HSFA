# Décors de SFA2 extraits de l'ISO

Les 18 décors de *Street Fighter Alpha 2 / Zero 2* (module `ro2` = e224, tuiles e227 / e226, sprites de décor e249) sont
extraits de l'ISO seule : plans, animations, défilements, reflets de Gen. Même méthode que `../sfa1-iso`. Ce dossier
n'a rien à voir avec `../sfa2/` (import d'un décor de SFA2 depuis l'arcade, rapport DECOR-SFA2).

| fichier | rôle |
|---|---|
| `extrait_sfa2.py --iso <ISO> --sortie <dossier>` | extraction. Appelle `anims_sfa2.py` ; lit `xdata.py` et les ADRESSES de `carte_ro2.json` / `carte_anims_ro2.json`. |
| `rendu_sfa2.py`, `rejoue_anims.py`, `planches_sfa2.py` | rendu hors jeu, rejeu des 263 animations, planches |
| `localise_ro2.py`, `localise_anims_ro2.py`, `arcade_anims.py`, `anims_observees.py` | oracle : localisation des tables (arcade `sfa2u` vidée par MAME). `anims_observees.json` est un relevé : il n'est pas publié, `anims_observees.py` le refait. |
| `oracle_anims.py`, `controle_anims.py`, `controle_pos.py`, `compare_mame.py`, `analyse_chrono.py`, `dump_mame.py` | oracle : contrôles statiques et image par image |
| `compare_versions.py`, `effets_sfa2.py`, `chiffrage.py` | 4 modules SFA2 de l'Anthology contre révisions arcade ; constantes du rowscroll ; tailles pour l'intégration |
| `mame/` | sondes MAME (`sonde_sfa2`, `anim_sfa2`, `obj_sfa2`, défilement, région, reflets) et lanceurs (`tous*.sh`) |

```sh
HSFA_SRC=<dépôt>/src/hsfa python3 extrait_sfa2.py --help
```
Résultats de référence : 2 079 cadres, 0 écart ; 165 258 dessins au pixel identiques (seul écart : Sagat, révision).
