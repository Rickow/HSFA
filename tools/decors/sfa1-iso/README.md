# Décors de SFA1 extraits de l'ISO

Les 13 décors de *Street Fighter Alpha / Zero* (module `ro1`, entrée e206 de `X_DATA.BIN`) sont extraits de l'ISO de
l'utilisateur, **sans ROM d'arcade** : plans, palettes, objets, animations. Le côté ORACLE (arcade `sfa` sous MAME,
programme déchiffré) n'a servi qu'à localiser les tables et à contrôler le résultat.

| fichier | rôle |
|---|---|
| `extrait_sfa1.py --iso <ISO> --sortie <dossier>` | extraction (JSON, plans, pixels des objets) ; lit les ADRESSES de `carte_ro1.json` et `carte_anims_ro1.json` (aucun octet du jeu) |
| `rendu_sfa1.py`, `rejoue_anims.py`, `planche_controle.py` | rendu hors jeu, rejeu des animations (PNG, GIF), planches de contrôle |
| `localise_ro1.py`, `localise_anims_ro1.py` | oracle : retrouvent les tables dans `ro1` et réécrivent les cartes |
| `compare_mame.py`, `controle_anims.py`, `controle_pos.py`, `dump_mame.py` | oracle : contrôles contre SFA1 joué sous MAME (VRAM, chronologie, positions au pixel) |
| `mame/` | sondes MAME (`lance.sh`, `anim.sh`, `anim2.sh`, `obj.sh` et leurs Lua), par `lance_emu`, sans `-state` |

Résultats de référence : 42 animations OK, 0 écart ; 20 594 dessins au pixel, 0 écart. Dépendances : numpy, PIL,
`src/hsfa` (`HSFA_SRC`, `mwo3_codec`). Les données produites restent dans l'espace de travail.
