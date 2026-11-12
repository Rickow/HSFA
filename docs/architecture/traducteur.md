# The MIPS → 68000 translator

**Français : [traducteur.fr.md](traducteur.fr.md)**

Overview. The details of each script (inputs, outputs, variables, functions) are in
[OUTILS.md](OUTILS.md); the code is in [`src/hsfa/`](../../src/hsfa/README.md).

## 1. Why it is possible

The Anthology games are not emulated: the original 68000 was **statically recompiled to MIPS R5900**. The
recompiler keeps each 68K register in a scratchpad slot (`0x70001100…`) and holds the flags in memory.
It produces **stereotyped idioms**: a 68000 instruction always gives the same sequence of MIPS instructions.
The translator **recognises these idioms and re-emits the original instruction**. It is not a decompiler: it does not
understand the program, it undoes a mechanical transformation (§1-§21 of the journal).

The SFA3 arcade ROM serves as the **answer key**: 91 % of the SFA3 code aligns with it function by function. Upper and
Hyper have no answer key, but share the same machine (§30): what is validated on SFA3 carries over.

## 2. Modules

| Module | Game | Recompiled 68K code (file) | Emulated PS2 RAM | Working folder |
|---|---|---|---|---|
| `ro3` | SFA3 | `0x22B00-0x393C40` | `0x900000` | `work/mame` |
| `ro5` | Upper | `0x22B00-0x41ACC0` | `0xA00000` | `work/mame_ro5` |
| `ro9` | Hyper | `0x22DE0-0x3BF140` | `0xB80000` | `work/mame_ro9` |

Load base `0x1F0000` for all three. Before the 68K, the file holds **recompiled Z80** (the sound
program), never retranslated (§16). The other Anthology modules (SFA, SFA2 and variants, Pocket Fighter) also go
through the translator at 98-99 %: [module map](../reference/carte-modules.md).

`profils.py` gathers the constants of each module (`MODULE=ro3|ro5|ro9`): entry points, recompiler helpers,
patched routines, tables. A missing value disables the matching feature.

## 3. The chain

```
module MIPS (roN_usa_prog68k.bin) ──► translate.py ──► assemble.py ──► mame_test.py ──► CPS2 program ROM (4 MB)
        X_DATA.BIN (ISO) ─────────────────────────────────────────────┘  (68K kernel,     + external blocks ext_*.bin
                                                                          resources,      + carte_image.txt, chutes.json
                                                                          stubs)
X_DATA.BIN ──► banques.py / hsfa_gfx.py / hsfa_plans.py ──► bank tables, extended graphics ROM, planes
X_DATA.BIN ──► gen_son.py / gen_hybride.py ──► sound ROM (SFA3; hybrid for Upper)
```

| Step | Script | Role |
|---|---|---|
| profile | `profils.py` | module constants |
| translation | `translate.py` | symbolic tracking of the MIPS registers; when a complete pattern is recognised, emission of the 68000 instruction; pre-passes (unaligned pairs, private stack, zones of lent registers) and post-passes (shortenings, byte streams, merging of `(An)+`) |
| | `extra_regs.py` | extra recompiler registers, "A8" and "D8" (§53): lent to a free register per zone, otherwise kept at a home in RAM |
| | `dn_alu.py` | lost register writes (audit, §107) |
| assembly | `assemble.py` | iterative placement, short or long branches, PC-relative jump and data tables |
| image | `mame_test.py` | entry point: profile → translation → assembly, then task kernel (`kernel68k.py`), resources loaded by the native code (`assets_natifs.py`), stubs of the port; writes the ROM and its side files |
| check | `diag.py`, `watch.py` | first exception on the bench and faulty MIPS instruction (through `carte_image.txt`); watchpoint |
| graphics | `banques.py`, `anthgfx.py`, `cps2rom.py`, `hsfa_gfx.py`, `hsfa_plans.py` | Anthology banks and planes → CPS2 ROM codes; extended graphics ROM of the fork |
| sound | `gen_son.py`, `gen_hybride.py`, `z80son.py` | sound ROM in MAME format; Upper's hybrid ROM |

The other scripts of `src/hsfa` (`census.py`, `verify.py`, `e2e.py`, `diverge.py`, `chain*.py`, `rosetta*.py`…)
are measuring tools or historical steps: [OUTILS.md](OUTILS.md) §3.

## 4. What the port added, and how it is replaced

The recompiled code is not alone in the module. The PS2 port added a **hardware layer** (CPS-A/B registers,
QSound, inputs "mirrored" into variables, §57-§58), **hooks**, **native C code** (dispatchers through tables of
longs, §140) and a **task kernel**. HSFA replaces:
- the kernel with a rebuilt 68K kernel (`kernel68k.py`, §60-§61);
- the hardware variables with the real CPS2 registers (`HWREG`, `ADDRMAP` of `translate.py`);
- the resources read by the native code (animations, frame file at a fixed address) with blocks prepared at
  build time (`assets_natifs.py`, §75);
- `setjmp` / `longjmp`, the joypad and a few routines with hand-written stubs.

## 5. Memory

The PS2 code sees a **little-endian** memory; the CPS2 is big-endian. Rather than recover the arcade layout
field by field, the translator applies a **universal recipe** (§29): word at the same address, byte at
the address XOR 1, long with its halves swapped. Pointers stay PS2 addresses, converted on use. Details
and pitfalls: [memoire-cps2.md](memoire-cps2.md). The cost of these adapters (~20 % of the 68K time in fights, §138) is
the subject of the [data relayout](ARCHI-Reorganisation-Donnees.md).

## 6. Switches

Each added rule has an environment variable; `=0` restores the old behaviour and must give back ROMs
**identical to the byte**. Examples: `TAILBR`, `LUIDN` (§143), `CMPMM` (§145), `EXT_MEM` (§128), `FTC_AVANT`,
`EXG_PILE` (§126), `EXTRA_REGS`, `A8_HOME`, `D8_HOME`. List: [journal/ETAT-DES-LIEUX.md](../journal/ETAT-DES-LIEUX.md)
§6 and [OUTILS.md](OUTILS.md) §2.4. Method: [methodes/oracle-et-non-regression.md](../methodes/oracle-et-non-regression.md).

## 7. Outputs worth knowing

| File | Content |
|---|---|
| `roms_tr/sfa3ud/sz3ud.03c…sz3.10b` (ro3; `roms_ro5`, `roms_ro9`) | 4 MB program ROM, as 8 × 512 KB |
| `ext_<adresse>.bin`, `ext_liste.txt` | blocks served outside the program ROM (cut data, files at a fixed address) |
| `carte_image.txt` | one line per emitted instruction: 68K address, MIPS va, mnemonic |
| `chutes.json` | register writes without a translation (audit of silent losses) |

Formats: [OUTILS.md](OUTILS.md) §5 and [reference/formats.md](../reference/formats.md).
