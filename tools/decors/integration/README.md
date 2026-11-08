# Intégration des décors SFA1 / SFA2 dans la greffe

Convertisseur commun des extractions `../sfa1-iso` et `../sfa2-iso`. Il produit des lots « HSFADC01 » prêts à poser
dans la zone des décors de la greffe `ro9a`, avec les preuves d'aller-retour. Rien n'est branché : un lot est une donnée.
Il est produit dans l'espace de travail et n'est jamais publié.

| fichier | rôle |
|---|---|
| `format_zone.py` | briques du format HSFADC01 (conventions de la zone des décors) |
| `convertit_decors.py` | JSON d'extraction -> lot + banque OBJ |
| `relit_blocs.py` | relecture du lot seul -> JSON comparés à l'entrée (égalité profonde) |
| `reconstruit.py`, `controle_tuiles_anim.py`, `compare_planches.py` | dossier « donnees » rebâti depuis le lot ; tuiles des blocs d'animation ; planches au pixel |
| `mesure_rom68k.py <construction figée>` | occupation de la ROM programme 68K, à croiser avec `re/allocations.tsv` |

Toute zone occupée se réserve d'abord dans `re/allocations.tsv` (`re/outils/zones.py --verifie`).
