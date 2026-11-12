# Architecture of the data relayout (project, 2026-10-07)

**Français : [ARCHI-Reorganisation-Donnees.fr.md](ARCHI-Reorganisation-Donnees.fr.md)**

Goal: remove the adapters measured in §138 (pointer conversions 13 %, swapped longs ~7 %, XOR 1 bytes,
lent registers: ~20-22 % of the 68000's work in fights) AND make memory identical to the arcade (real CPS2
layout). Ultimate target: translated SFA3 = arcade byte for byte where the code is aligned; Upper/Hyper/MAX in
the arcade layout.

## 1. Starting point

| layer | today | measured cost (§138) | volume (SFA3 / Upper) |
|---|---|---|---|
| data pointers | raw PS2 addresses in the tables and the RAM, `JSR CONV_An` after each `MOVEA` loaded from memory | 8.6 % + calls 0.8 % | ~630 call sites |
| code pointers | PS2 address → hash table `$3C0000` before each `JSR/JMP (An)` | 3.7 % | a few dozen sites, hot |
| longs | "universal recipe" §29: halves swapped in memory, `SWAP` (+ `MOVE SR/CCR`, stack) | ~6.7 % | 4,693 / 5,096 emissions |
| bytes | address XOR 1 (indexed: toggle at run time) | 0.3 % | 128 / 130 sites at run time |
| A8/D8 registers | homes `$87E0`/`$87F0(A5)`, lent per zone | 0.2 % | 371 / 435 |

## 2. Principle: a single map, reversible steps, an oracle

1. **A single source of truth: `carte_types`** (JSON + Python module, read by the translator, the data
   assembler, the Lua tools and the FBNeo core):
   - RAM zones: A5 variables by ADDRESS (unambiguous); structures by TYPE (players `$FF8400+$400·k`,
     object pools, projectiles `$100`, sprite buffers…) with their ORIGIN (where the pointer comes from);
   - for each field: PS2 offset, type (`u8`, `s16`, `s32`, `u8[4]`, `s16[2]`, `ptr_donnees`, `ptr_code`),
     arcade offset;
   - data tables in ROM: range, element size, fields (including pointers), matching arcade address.
   Sources: `typed_rule.py` (access sizes, 94 %), `const_evidence.json` (ROM constants, 95 %), pairs of
   functions aligned with the arcade (`layout_pairs.json`, alignment by the coverage agent: 91 % of the SFA3 code),
   execution traces (conversion log, `watch.py`).
2. **Each step has its switch** (like the whole translator: variable `=0` → old behaviour) and the
   current recipe remains the **safety net** for everything not yet typed. We switch over zone by zone.
3. **Oracle**:
   - SFA3: **RAM compared with the arcade** (same game played by `tournee.lua`, `REF=1` against the translation, `DUMPC`
     dumps at the start of the rounds and during attract mode); once typed, a zone must be IDENTICAL to the arcade
     (apart from the port's own variables). Upper shares 72 % of SFA3's A5 variables, Hyper 77 % (§30): what is
     validated on SFA3 carries over.
   - All: non-regression, 42 controls, sweep of the 72 endings, screenshots ±1, **empty conversion log**
     (no raw PS2 address seen by the stubs), profile `_prof_adapt.lua`.
4. **Self-describing ROM**: a small header at a fixed address in the program ROM (layout version, addresses
   of the variables read by the bench: object list, animation pointer `$FF40BC`, plane bases…). The MAME fork,
   the Lua scripts and the FBNeo core read this header instead of hard-coded addresses → **a new layout does not
   require recompiling the core**, only a new zip (`paquet_fbneo.py`, format unchanged).

## 3. Steps

| # | step | gain | risk | validation |
|---|---|---|---|---|
| A | **Instrumentation**: `CONV` stubs in log mode (Lua: value, source instruction `MOVEA.L d(Ax),An` → original memory slot); RAM comparison tool translation/arcade; Lua accessor `disposition.lua` (all tools read the RAM through the map) | 0 | none | — |
| B | **Code pointers** relocated at assembly (tables and slots identified by the log → 68K labels); removal of the hash at the sites whose origins are all relocated | ~3.7 % | low (a miss = wrong jump, visible at once) | empty log over the 72 endings + modes |
| C | **Data pointers of the ROM tables** relocated (log + check against the arcade table when it exists) | | medium | same |
| D | **Pointers in RAM**: when all their sources are relocated, removal of the `JSR CONV` after the `MOVEA`s | ~9.4 % | medium | empty log, then stubs removed |
| E | **Typed RAM**: A5 variables (fixed addresses) → player structures (A6 of the character code) → objects/projectiles → A0-A4 by origin. Native longs (no more `SWAP`), bytes/words at arcade offsets | ~7 % | HIGH (wrongly typed field = silent corruption) | RAM identical to the arcade zone by zone (SFA3), then Upper/Hyper |
| F | **Typed data tables** (big-endian per element, like 3SX `section_element_sizes`); for SFA3, copy/check from the arcade ROM | fidelity | medium | bytes identical to the arcade tables |
| G | **Lent registers**: global allocation (A8/D8 in real free registers per function) | ~0.2 % + size | low | non-regression |

Proposed order: A → B → C → D (quick performance gain, contained risk), then E by zones, F, G.
Known hard points: unions (`s16[2]` / `s32` depending on the function, §44), base registers that point to different
structures (A4 `$0/$2/$4/$8`), generic copies (MOVEM, copy loops: indifferent to the
layout if both sides are of the same type and aligned on 4), the C code of the port (left on the recipe).

## 4. What it brings beyond speed

- **Arcade layout**: the known addresses and RAM maps of SFA3 (MAME cheat codes, training tools,
  documentation) hold for Upper and Hyper; comparisons with the arcade become exact.
- **MAX**: the MAX session already reasons in arcade addresses (`$32F46`, `$1C1C8`, fields `$362`/`$3F3`) → direct
  integration, with no PS2 transposition.
- **Simpler tools**: no more longs written as two swapped words in the scripts (`FORCE="L…"`).

## 5. What it does not bring

On a small console (RGB10X), the emulator simulates the 68000 at a fixed rate, wait loop included: the load on
the host does not drop. The gain is for the game itself: more headroom (turbo without repeated frames, §104, without
overclocking). The host load depends on the core's CPS2 rendering and QSound.
