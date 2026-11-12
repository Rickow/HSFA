# Scripts: build, validation, quality

**Français : [README.fr.md](README.fr.md)**

| Path | Role |
|---|---|
| [`construction/hsfa_build.py`](construction/hsfa_build.py) | builds SFA3, Upper and Hyper from the user's ISO ([guide](../docs/guide/construction-iso.md), [BUILD](../docs/rapports/BUILD.md)) |
| [`construction/rom_iso.py`](construction/rom_iso.py) | SFA3 CPS2 graphics ROM rebuilt from the ISO alone |
| `construction/correctifs/` | diffs applied to the shared tools while the build was being developed (history, BUILD §8) |
| [`validation/valide_tout.sh`](validation/valide_tout.sh) | full validation after a translator fix (≈ 1 h 15, steps in parallel; `PARALLELE=0`: ≈ 3 h) |
| [`validation/nonreg.sh`](validation/nonreg.sh) | SFA3 non-regression: 3 diagnostics + 42 commands |
| [`validation/nonreg_ro5.sh`](validation/nonreg_ro5.sh) | Upper non-regression on the fork |
| [`validation/balayage_fins.sh`](validation/balayage_fins.sh) | one Arcade game per character up to its ending |
| [`validation/nonreg_coeur.sh`](validation/nonreg_coeur.sh) | FBNeo HSFA core non-regression: the same games played by a reference core and by the core under test (screenshots, logs, replay, streams, sound; §162) |
| [`localiser.py`](localiser.py) | runnable copy of the repository: `<workspace>` replaced by your paths (`config.env`) |
| [`correspondances.tsv`](correspondances.tsv) | workspace folders → repository folders |
| [`qualite/verifier_liens.py`](qualite/verifier_liens.py) | Markdown links and paths cited in the documentation |
| [`qualite/verifier_imports.py`](qualite/verifier_imports.py) | compiles every `.py`, resolves their imports, checks the files called by the shell scripts |

The scripts in `validation/` read `HSFA_WORKSPACE` (required) and take the tools from `src/hsfa` (path relative to the script: `$S/../../src/hsfa`, or
`HSFA_SRC`). They run MAME (long computations, `nice -n 19`): run them from a localised copy. Method and
expected results: [oracle and non-regression](../docs/methodes/oracle-et-non-regression.md).

Before publishing a change to the documentation or the tools:

```bash
python3 scripts/qualite/verifier_liens.py      # expected: « Liens ou chemins casses : 0 »
python3 scripts/qualite/verifier_imports.py    # expected: « compilation en echec : 0 », « ECHEC : 0 »
```
