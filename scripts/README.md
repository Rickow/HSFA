# Scripts : construction, validation, qualité

| Chemin | Rôle |
|---|---|
| [`construction/hsfa_build.py`](construction/hsfa_build.py) | construit SFA3, Upper et Hyper depuis l'ISO de l'utilisateur ([guide](../docs/guide/construction-iso.md), [BUILD](../docs/rapports/BUILD.md)) |
| [`construction/rom_iso.py`](construction/rom_iso.py) | ROM graphique CPS2 de SFA3 reconstruite depuis l'ISO seule |
| `construction/correctifs/` | diffs appliqués aux outils partagés pendant la mise au point de la construction (historique, BUILD §8) |
| [`validation/valide_tout.sh`](validation/valide_tout.sh) | validation complète après un correctif du traducteur (~3 h) |
| [`validation/nonreg.sh`](validation/nonreg.sh) | non-régression de SFA3 : 3 diagnostics + 42 commandes |
| [`validation/nonreg_ro5.sh`](validation/nonreg_ro5.sh) | non-régression d'Upper sur le fork |
| [`validation/balayage_fins.sh`](validation/balayage_fins.sh) | une partie Arcade par perso jusqu'à sa fin |
| [`localiser.py`](localiser.py) | copie exécutable du dépôt : `<workspace>` remplacé par vos chemins (`config.env`) |
| [`correspondances.tsv`](correspondances.tsv) | dossiers de l'espace de travail → dossiers du dépôt |
| [`qualite/verifier_liens.py`](qualite/verifier_liens.py) | liens Markdown et chemins cités dans la documentation |
| [`qualite/verifier_imports.py`](qualite/verifier_imports.py) | compilation de tous les `.py`, résolution de leurs imports, fichiers appelés par les scripts shell |

Les scripts de `validation/` lisent `HSFA_WORKSPACE` (obligatoire) et prennent les outils dans `src/hsfa` (chemin relatif au script : `$S/../../src/hsfa`, ou
`HSFA_SRC`). Ils lancent MAME (longs calculs, `nice -n 19`) : à lancer depuis une copie localisée. Méthode et
résultats attendus : [oracle et non-régression](../docs/methodes/oracle-et-non-regression.md).

Avant de publier une modification de la documentation ou des outils :

```bash
python3 scripts/qualite/verifier_liens.py      # attendu : « Liens ou chemins casses : 0 »
python3 scripts/qualite/verifier_imports.py    # attendu : « compilation en echec : 0 », « ECHEC : 0 »
```
