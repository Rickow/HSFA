# Getting started with HSFA

**Français : [demarrage.fr.md](demarrage.fr.md)**

This guide goes from the ISO to a translated game running on the MAME bench, then to non-regression. To only build
the games and install them on a console, [construction-iso.md](construction-iso.md) is enough.

## 1. What you need

| Item | Role | Required |
|---|---|---|
| ISO of *Street Fighter Alpha Anthology* (USA, `SLUS-21317`) | all the game data | yes |
| Python 3.8+ and `pip install -r requirements.txt` | translator, build | yes |
| MAME 0.285 (`mame`) | reference bench (`sfa3ud`): diagnosis, controls test | for the bench |
| MAME fork `sfa3hx` (`cps2f`, [patches/mame-fork](../../patches/mame-fork/README.md)) | Upper and Hyper on the bench, Upper non-regression | for the bench |
| arcade ROM `sfa3ud` (Phoenix) | oracle: comparisons with the arcade, controls test | for validation |

The repository contains no game data. The files produced (translated ROMs, archives) stay on your machine.

## 2. The workspace

The scripts were written for a fixed workspace, whose paths are published in the form
`<workspace>/...`. Expected layout:

```
$HSFA_WORKSPACE/
  anthology_extract/        manifest.csv, decompressed/roN_usa_prog68k.bin (MIPS modules)   = $HSFA_EXTRACT
  work/                                                                                     = $HSFA_WORK
    xdata/X_DATA.BIN        extracted from the ISO (read-only)
    mame/                   SFA3 bench: Lua scripts, roms/ (reference arcade), roms_tr/ (translation)
    mame_ro5/, mame_ro9/    Upper and Hyper benches (roms_ro5/, roms_ro9/, roms_fork/, banques_hx/...)
    cps2/                   intermediate CPS2 ROMs (sfa3ud_prog.bin...)
  mame-fork/mame/cps2f      fork binary                                                      = $HSFA_CPS2F
```

1. Copy `config.example.env` to `config.env`, adjust the paths, then `source config.env`.
2. Make a runnable copy of the repository, where `<workspace>` is replaced by your paths:
   ```bash
   python3 scripts/localiser.py ~/hsfa-local --lua
   ```
   `--lua` also copies the bench scripts (`src/hsfa/mame/*.lua`) into `$HSFA_WORK/mame`, from where MAME runs them.
   The repository is not modified. Variables in detail: [`hsfa_config.py`](../../src/hsfa/hsfa_config.py).
3. Extract the modules and `X_DATA.BIN`: the simplest way is to run the build from the ISO once
   ([construction-iso.md](construction-iso.md)), which does the extraction and checks the fingerprints.

## 3. Translate a module

From `~/hsfa-local/src/hsfa` (localised copy):

```bash
MODULE=ro3 XDATA=$HSFA_XDATA nice -n 19 python3 mame_test.py      # SFA3   -> work/mame/roms_tr/sfa3ud/
MODULE=ro5 XDATA=$HSFA_XDATA nice -n 19 python3 mame_test.py      # Upper  -> work/mame_ro5/roms_ro5/
MODULE=ro5 nice -n 19 python3 banques.py tout                      # Upper's bank tables
```

In the report, watch the "écritures de registre tombées" (dropped register writes) and "non résolus" (unresolved)
counters: any increase is a regression. Never build a reference with `MAX_DEMO` or `MAX_PAL`. The role of each
script is described in [architecture/traducteur.md](../architecture/traducteur.md) and, in detail, in
[OUTILS.md](../architecture/OUTILS.md).

## 4. Run the bench

Always `-video none` (the window blocks MAME), `nice -n 19`, and never `-state` on the command line. From
`$HSFA_WORK/mame`:

```bash
# translated SFA3: coin, Start, button 1 held; snapshots at frames 3000 and 6000
INPUTS="1500-1508::IN2:Coin 1;1600-1608::IN2:Coin 2;2000-2006::IN2:1 Player Start;3500-19900%200,6::IN0:P1 Button 1" \
NF=20000 OUT=journal.txt SNAPS=3000,6000 nice -n 19 mame sfa3ud -rompath roms_tr -video none -sound none \
  -nothrottle -skip_gameinfo -snapshot_directory captures -autoboot_script jeu.lua
```

Upper and Hyper run on the fork (`cps2f sfa3hx`): see [architecture/banc-mame.md](../architecture/banc-mame.md)
for the variables (`HSFA_GFX`, `HSFA_PLANS`, `BANC_BANQUES`…) and the scenario scripts (`tournee.lua`,
`commandes.lua`…).

## 5. Look for a fault

```bash
MAXF=20000 nice -n 19 python3 diag.py 30 --nobuild              # ro3; without --nobuild: rebuilds first
MODULE=ro5 MAXF=12000 nice -n 19 python3 diag.py 30 --nobuild   # Upper
```

`diag.py` stops at the first exception and traces it back to the faulty MIPS instruction through `carte_image.txt`.
Expected end: "aucune exception" (no exception). Full method:
[methodes/oracle-et-non-regression.md](../methodes/oracle-et-non-regression.md).

## 6. Validate

After **every** translator fix, from the localised copy (`~/hsfa-local`):

```bash
bash scripts/validation/nonreg.sh        # SFA3: 3 diagnoses + 42 controls (up to ~2 h)
bash scripts/validation/nonreg_ro5.sh    # Upper, on the fork
bash scripts/validation/valide_tout.sh   # everything: rebuilds ro3/ro5/ro9, non-regressions, Hyper VERSUS, endings (~3 h)
```

These scripts read `HSFA_WORKSPACE` and take the tools from the neighbouring `src/hsfa` (or from `HSFA_SRC`): run
from the repository itself, they would find scripts with unreplaced `<workspace>` paths. Expected results:
3 × "aucune exception", "42 actions, 0 différentes" (42 actions, 0 different), 133.3 %; Upper "fin=finie" (ending
finished) for each character.

## 7. Pitfalls to know from the start

- A PS2 byte at address `a` is at `a ^ 1` on the 68K side; a long is stored with its halves swapped: any script that
  compares with the arcade must normalise ([architecture/memoire-cps2.md](../architecture/memoire-cps2.md)).
- The bench EEPROM (`~/.mame/nvram/sfa3ud`) is rewritten on every exit: freeze it, otherwise games diverge.
- `pkill -f` or `pgrep -f` with a pattern present in the command line kills the shell: use `ps -C mame`.
- After each rebuild, the 68K addresses move: read `carte_image.txt` again before setting a breakpoint.

Full list: [methodes/pieges-du-traducteur.md](../methodes/pieges-du-traducteur.md) and
[journal/ETAT-DES-LIEUX.md](../journal/ETAT-DES-LIEUX.md) §7.
