# The MAME bench and the `sfa3hx` fork

**Français : [banc-mame.fr.md](banc-mame.fr.md)**

Decision of §109: a **MAME fork** serves as the development and validation bench, ahead of the final FBNeo core.
It keeps the debugger, the Lua scripts and the comparison with the arcade ROM. Full details: [OUTILS.md](OUTILS.md)
§4; scripts: [`src/hsfa/mame/`](../../src/hsfa/mame/); patches: [`patches/mame-fork/`](../../patches/mame-fork/README.md).

## 1. Two benches

| | "Stock" bench | `sfa3hx` fork |
|---|---|---|
| binary | official MAME 0.285, Phoenix game `sfa3ud` (unencrypted program) | `cps2f` (MAME 0.285 + patch), game `sfa3hx` (clone of `sfa3ud`) |
| used for | translated SFA3 and reference arcade ROM (`REF=1`): diagnosis, controls test, endings | Upper and Hyper (tiles beyond the SFA3 ROM), Upper non-regression, Hyper VERSUS |
| external blocks | `banc_mem.lua` (read taps) | `HSFA_EXT` (ROM `$A00000-$CFFFFF`) |
| tiles outside the SFA3 ROM | impossible | `HSFA_GFX`: 128 MB graphics ROM, 20-bit object codes |
| planes | `banc_plans.lua` (renumbering) | registers `$804200-$804205`: one base per plane (`HSFA_PLANS`) |
| sprites | `banc_sprites.lua` + `banques/` | `banc_sprites.lua` + `banques_hx/` |
| 68K clock | — | `HSFA_CLOCK` |
| sound | `sfa3ud` ROM | `HSFA_SON`: Upper's hybrid ROM; ADX stream player; SFA1/SFA2 replay (later patches) |

## 2. The three Lua layers

Loaded in this order, before the scenario script:
1. **`banc_mem.lua`**: serves the `ext_<adresse>.bin` files to the 68K (big-endian words).
2. **`banc_plans.lua`**: converts the port's plane tile codes into CPS2 codes (`plan1.bin`, `plan2.bin`,
   `f312.bin`); with `HSFA_PLANS` (fork), only writes the plane bases.
3. **`banc_sprites.lua`**: hijacks the object list, splits each object into 16×16 tiles and converts each code
   through the table of its **slot** (bits 13-15 of Y): 0 common bank, 1 stage, 2/3 characters of P1/P2, 4 graphics
   file of the scene, 6/7 players 3/4. Writes the converted list into both object banks.
   `BANC_LAT4` (§146) delays the file change of slot 4 while its objects are on screen.

⚠ A Lua tap set before `banc_sprites.lua` sees the converted list: read `BANC_OMBRE` (§106). `banc_mem.lua` must
be loaded in every one-off script, otherwise execution diverges (§75).

## 3. Scenario scripts

| Script | Role |
|---|---|
| `jeu.lua` | game with scripted inputs (`INPUTS`), mode log, screenshots (`SNAPS`) |
| `commandes.lua` | controls test: 42 actions compared with the arcade (`commandes.py`) |
| `tournee.lua` | full Arcade game of one character (`PERSO`, `MODE`, `FORCE`…), stop on exception; basis of the ending sweeps |
| `force_stage.lua` | forced stage |
| `visu.lua` | PS2 state viewer: renders a PCSX2 state in MAME (§89) |
| `_prof_adapt.lua` | profile of the memory adapters (§138) |

Variables: [journal/ETAT-DES-LIEUX.md](../journal/ETAT-DES-LIEUX.md) §6 and [OUTILS.md](OUTILS.md) §4.3.

## 4. Typical launches

```bash
# Upper on the fork (from $HSFA_WORK/mame; W5=$HSFA_WORK/mame_ro5)
BANC_COMMUN=351 PERSO=00 NF=70000 HSFA_PLANS=300,340,3a0 \
HSFA_GFX=$W5/hsfa_gfx.bin,$W5/hsfa_plans.bin@3000000 BANC_BANQUES=$W5/banques_hx/ BANC_PTR_ANIM=FF40BC \
BANC_GFX_INTRO=456 BANC_DIR=$W5/ OUT=p00.txt nice -n 19 $HSFA_CPS2F sfa3hx -rompath $W5/roms_fork \
  -video none -sound none -nothrottle -skip_gameinfo -nvram_directory /tmp/nv -autoboot_script tournee.lua
```

Hyper: same form with `BANC_COMMUN=545` and the `work/mame_ro9` folder (see
[`valide_tout.sh`](../../scripts/validation/valide_tout.sh)). `roms_fork/sfa3hx` is a link to the `sfa3ud`
folder of the translation.

## 5. Hygiene rules

- Always `-video none -sound none -nothrottle -skip_gameinfo` and `nice -n 19`; one heavy computation at a time.
- Never `-state` on the command line (it hangs on the checksum screen): `SAVEAT`/`SAVENAME`, then
  `manager.machine:load(nom)` from Lua (§110).
- Frozen EEPROM (`~/.mame/nvram/sfa3ud` read-only) or a temporary `-nvram_directory`: otherwise the games
  diverge (§81).
- Never trace on a build that someone else may redo: freeze a copy of the ROMs and note the md5s.
- A write recorded at "frame N" happens during N+1; `-debug` shifts the timing (§67, §81).

## 6. What remains to do in the fork

Object list lock and bank slots in native code (still in Lua); `HSFA_EXT` only serves fixed
bases (nothing for Hyper's blocks `$940000` / `$C84000`, served by `banc_mem.lua`); integrate the replay into the
reference fork (`rejeu-sur-fork-flux.patch`, §145).
