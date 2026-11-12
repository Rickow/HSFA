# Oracle and non-regression

**Français : [oracle-et-non-regression.fr.md](oracle-et-non-regression.fr.md)**

Working method of the translator, valid for any project retranslating a recompiled binary (HSFA, and the
PSP transcription of SFA3 MAX). The "§N" references point to the [journal](../journal/HANDOFF.md).

## 1. An oracle first, never the eye

1. **The reference is the arcade under MAME** (ROM `sfa3ud`, `REF=1`), not the console emulator.
2. The same **scripted** game (Lua, inputs to the frame) runs on both sides: `tournee.lua`, `commandes.lua`,
   `jeu.lua` ([banc-mame](../architecture/banc-mame.md)).
3. We compare **quantities**: RAM, object positions frame by frame, screenshots, number of frames until an
   event. A defect that "shows" is proven by a quantity: the big A's text that scrolled wrongly was reduced
   to the position of 6 sub-objects, equal to the arcade over 346 frames once fixed.
4. Before touching the translator, check that the difference comes from the **translated game**: the glitch of Upper's portrait
   came from the bench and the core, which switched graphics bank too early (§146). First compare the order of the
   game's writes with the arcade.

## 2. The non-regression suite

Run again after **each** rule added to the translator ([`scripts/validation/`](../../scripts/validation/)):

| Script | Check | Expected | Duration |
|---|---|---|---|
| `nonreg.sh` | SFA3: attract mode 20,000 frames without input, 20,000 with coin / Start / button, offensive game of 60,000 frames, then test of the 42 controls | 3 × "aucune exception" (no exception), "42 actions, 0 différentes" (0 different), 5,359 turns in 4,019 frames (133.3 %) | ~2 h |
| `nonreg_ro5.sh` | Upper: attract mode 20,000 frames, then three Arcade games (Ryu, Chun-Li, Akuma) on the fork | "aucune exception", "fin=finie" (ending finished) ×3 | ~15 min |
| `balayage_fins.sh` | one Arcade game per character up to its ending (32 SFA3, 40 Upper) | SFA3: screenshots = arcade ± 1; Upper: "fin=finie" | long |
| `valide_tout.sh` | rebuilds ro3, ro5, ro9, then all of the above + one Hyper VERSUS game | no "ECART" (difference) line | ~3 h |

Many regressions showed **only in the endings** (§137): the ending sweep is not optional.

## 3. One switch per rule

- Each translator rule has its environment variable; `=0` restores the old behaviour.
- **`=0` must give back ROMs identical to the byte (md5).** Then you can bisect, isolate the effect of a rule and
  deliver a fix as a diff without risk.
- Examples: `TAILBR`, `LUIDN` (§143), `CMPMM` (§145), `FLUXEA` (`(An)+` byte streams, big A), `EXT_MEM` (§128).
- Each build prints a **counter per rule** ("CMP mémoire-mémoire : n sites"): an unexpected
  change is a signal.

## 4. "0 unresolved" does not mean correct

The worst defects are **silent losses**: a source instruction that produces nothing, or a wrong form
that still assembles. Tools:

| Tool | Role | § |
|---|---|---|
| `census.py` | what the translator misses, over the whole binary | §17-§18 |
| `chutes.json` (audit of register writes) | registers written with no instruction emitted | §107, §132, §137 |
| `AUDIT_MEM=1` → `mem_miss.json` | memory writes with no trace | §107, §138 |
| `audit_exacts.txt` | "exact flags" comparisons with an unknown operand | §126 |
| `diverge.py` | **first** divergence from the arcade | §37 |
| `verify.py` | independent checker (reliable where the translator emitted something) | §3 |
| `e2e.py` | **static** oracle: translate, assemble, compare with the arcade ROM function by function | §23 |
| `hooks.py` | map of the zones: original code, code added by the port, data, veneers | §21 |
| "GARDE-FOU (v161)" in `build.log` | access to A8 without a lent register, Bcc on the flags of a call while the MIPS recomputes RES, comparison with no 68K form (`enc_cmp`) and recompiler helper not inlined (these last two: the build fails) | §219 |
| `drapeaux.py`, `a8_hors_zone.py` (critical review, `<workspace>/work/revue_traducteur/outils`) | after the fact: per branch, last 68K setter against last MIPS write of RES / C; A8 / D8 accesses outside a zone | §219 |

91 % of the SFA3 code aligns function by function with the arcade ROM (`layout_pairs.json`); for a binary without
an answer key, look for the counterpart of each routine in a game that has one (Upper for MAX).

## 5. RAM oracle and conversion log

Step A of the data relayout ([ETAPE-A](../rapports/ETAPE-A.md), tools in
[`tools/reorg/`](../../tools/reorg/)) adds two oracles:
- **RAM translation ↔ arcade** (`compare_ram.py`): same game, dumps at the start of the rounds; a typed zone must be
  identical to the arcade;
- **conversion log** (`journal_conv.lua`): each raw PS2 address seen by a conversion stub; the goal
  is an empty log.

## 6. Hygiene

- Never trace on a build that someone else may redo: freeze a copy of the ROMs, note the md5s.
- One heavy computation at a time, `nice -n 19`.
- MAME: temporary `-nvram_directory` and `-cfg_directory`, never `-state` on the command line, never `pkill -f`.
- After each rebuild, read `carte_image.txt` again before setting a breakpoint.
