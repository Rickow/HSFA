# Translator pitfalls

**Français : [pieges-du-traducteur.fr.md](pieges-du-traducteur.fr.md)**

Catalogue of the pitfalls met while retranslating the recompiler's MIPS into 68000, grouped by family. They hold
for any binary produced by a static recompiler (the SFA3 MAX session uses them for the PSP). The "§N"
references point to the [journal](../journal/HANDOFF.md); detection method: [oracle-et-non-regression.md](oracle-et-non-regression.md).

## 1. Addresses and bounds

- **Execution base off by 8 bytes** (§5) and **wrong code zone bounds** (§4): everything seems to work
  at 99 %. Check them against reliable cross-references (vectors, jump tables).
- The code zone held **two processors**: Z80 then 68000 (§16). In other modules, the Z80 is not at the
  start ([module map](../reference/carte-modules.md)).
- Writes to An **convert** 68K addresses into host addresses (§10). A data pointer read from memory
  is a host address, to be converted back on use (conversion stubs, §76).
- **Code** pointers are host addresses: a lookup table is needed, and a hash for
  performance (§98).
- A jump table can be indexed by a **raw index** instead of an index ×2 / ×4 (§102, §112: SURVIVAL
  crashed).
- Split the MIPS into functions by the `jal` targets, never by `jr ra`.

## 2. Memory layout (the most treacherous)

- The recompiler types **per field** (§44): the same 68K byte is not always in the same place, depending on the read.
- Recipe chosen ([memoire-cps2](../architecture/memoire-cps2.md)): byte = address XOR 1, word = same address,
  long = halves swapped. Pitfalls specific to this recipe:
  - byte-reversed word read from an **indexed** table (§92, §100);
  - long stored byte by byte (`bswap32`, §90);
  - byte read through an address register of **unknown parity** (after `ADDA Dn,An`): the exact address is computed at
    run time, the fixed XOR is wrong (§97);
  - **`(An)+` byte streams** (§65): after `MOVE.B (A3)+,x ; MOVE.B (A3)+,y`, the form `ADDQ #1,A3 ; MOVE.B -2(A3)`
    is only correct if A3 is odd; otherwise the neighbouring byte is read. Cause of the big A's text that scrolled wrongly in all
    three games (16 sites, rule `FLUXEA`);
  - unions (`s16[2]` / `s32` depending on the function, §44).
- Hyper was produced by a **more recent** version of the recompiler (§52), with other idioms: never
  assume that one binary follows the rules of another.

- **Stack temporary loaded from memory taken for the constant of a stale `lui` of the same register** (§162, `PILE_LUI`): the CMP is not emitted and the branch reads the caller's flags; telltale sign: functions with an `sq` prologue.

## 3. Flags and branches

- The status slots are not the ones you would expect: `0x1158` is the **carry**, not N (§11).
- The flags of `CMP` / `SUB` must be exact (§20); those of in-place `SUBI` too (§90).
- **Flags returned to the caller**: a routine ends with a `BTST` / `CMP` and it is the caller that branches (§87, §93,
  §125). A shared epilogue can overwrite them (§126). Follow the flags across returns.
- **Memory-to-memory `CMP`** (no direct 68K form): it was lost, and the branch read stale
  flags again. Cause of Hyper's gauge with no ceiling (`CMPMM`, §145).
- The recompiler's **DBRA** loops while ≥ 0 (`SUBQ.W ; BPL`), not while ≠ −1 (§74).
- Far branches; tail calls removed even though they were branch targets (`TAILBR`, §143);
  branch merging by the assembler (§91).

## 4. Silent losses seen

Since v161, `build.log` counts the ones we know how to recognise: "GARDE-FOU (v161)" lines (A8 without a lent register; Bcc on the flags of a call while the MIPS recomputes RES; comparison with no 68K form and recompiler helper not inlined: **the build fails**, `GARDE_CMP=0` / `GARDE_AIDES=0` to override).

All found through an in-game symptom, then proven against the arcade.

| Defect | Symptom | § |
|---|---|---|
| `ADDI.L` lost | wrong portraits | §85 |
| `MOVEA.W An,Am` lost | blocks in the stage at K.O. | §86 |
| extra sign extension | sound | §79 |
| sign-extended read lost | crash of Upper's character `$22` | §128 |
| lone `lui` constant stored in a data register, taken for an address | Akuma's and Dan's supers, Sakura's multi-hit fireballs (`LUIDN`) | §143 |
| register written with no instruction emitted | various | §107, §132, §137 |
| memory-to-memory `CMP` | Hyper's gauge, TRAINING crash (`CMPMM`) | §145 |
| recompiler's `EXG Dx,Dy` (register slots) rendered as two `MOVE`s: the slot read back after being overwritten; `BCLR` tested after the clear; unknown `roxr` helper translated as an empty stub | Cammy's Killer Bee Assault missing in Hyper and Upper (angle 0); `paires_exg.py` finds the other lost `EXG`s | §171 |
| access to A8 outside a lent zone (side entry coming from before the zone): nothing emitted | MAZI mode ×1.5 damage bonus never applied (3 games); Hyper: animation table, table slot (`A8_ENTREE`) | §219 |
| zero test read first by a branch on C; `zx` of a Dn; `mem + (−k)` stored in RES only; indexed byte in two steps | ±1 px shake of the character hit, table entry at fight 9, wait for an object, "not twice the same" draw, `CMP.B D0,D8` with D8 at home (2nd player's colour in mirror matches), "memory − Dn" (`TST_C`, `TST_ZX`, `CMP_MEMADD`, `CMP_IDX`, `CMP_D8`, `CMP_MEMDN`) | §219 |
| parity of An forgotten after BRA / JSR / RTS; odd An from a stream, odd LEA, stored pointer | initials entry (2nd letter on the 4th), custom combo freeze, scrolling text (`PARITE_FLOT`, `PARITE_SITES`) | §219 |
| `abcd` helper on bytes of **register slots**; undeclared `sbcd` helper: JSR to an empty body | combo score bonus never added (`BCD_REG`, `AIDE_SBCD`) | §219 |

## 5. Registers and stack

- The recompiler has **extra** registers "A8" and "D8" (§53). HSFA lends them to free registers
  per zone, with homes in RAM (`$87E0` / `$87F0(A5)`).
- **Side exits** from these zones are costly: mirror match (§130).
- Private stack of the recompiler at `0x114C` (§72), brought back onto the 68K stack.

## 6. Code added by the port

- Hooks inside the anchored functions themselves (§7, §12).
- Resources loaded by the native code, `setjmp` / `longjmp` (§75).
- Task kernel to rebuild (§60-§61).
- Hardware layer "mirrored" into variables (§57-§58).
- **C** code of the port: its own idioms (dispatchers through tables of longs, `lb ; bne r,zero`, §140). Do not
  translate it as recompiled 68K.

## 7. Assembler

- Jump table entries out of 16-bit range (§94).
- Iterative placement needed (§22).
- `assemble.py` reads back **markers in the mnemonics** produced by `translate.py` (`(cible …)`, `[mips …]`,
  `T_…`, `CODE_…`, `_ECH`): do not change their format.

## 8. Bench and data

- A write recorded at "frame N" happens during N+1; `-debug` shifts the timing; opcode taps see
  the prefetch (§67, §81, §82, §114).
- `sfa3_prog.bin` has wrong data in `$0-$BFFFF`: the tables are read from `sfa3ud_prog.bin` (§96).
- Coverage: always as a union, and tell "extent" from "usable" apart (R§6bis, C2).
- Profile: the memory adapters (pointer conversions, swapped longs, XOR bytes, lent registers) cost
  ~20 % of the 68K time in fights (§138): that is the subject of the
  [data relayout](../architecture/ARCHI-Reorganisation-Donnees.md).

## 9. PSP-specific pitfalls (PSP MIPS → 68K translator of the MAX session)

Translator: `max/outils/rosette_code/traduire.py`; details: [max-integration-upper](../../max/notes/max-integration-upper.md),
[max-portage-code](../../max/notes/max-portage-code.md).

- **0-based `jal` targets**: the PRX is relocated at load time; target = `imm26 << 2` (`tools/max/modules.py`).
- **Delay slot pointed to by data**: a data word can point at the instruction that follows a jump. It is
  not a function start, otherwise the function is cut (`0x1B3450`, `tools/max/charcode2.py`).
- **Splitting into modules**: the handlers of the MAX characters are stored BEFORE the root. Cut at the last
  function reached from the root, not at the next root (114 of Eagle's functions forgotten).
- **Read size**: the C widens fields. Read at the smaller of the PSP and 68K sizes; a byte read
  (`lb`) used in a word computation is read as a byte then extended, never `MOVE.W` at an odd address
  (`lb 0x4D` → `$35`).
- **PSP fields with no equivalent** (impact position `0x2CA-0x2DE`, attached effect `0x38`): omit both the write AND the
  read of the source.
- **Private fields**: do not put the fields specific to the MAX characters in `$28-$2F` (taken by the generic engine);
  `$5C` / `$60` are free.
- **Structures of different size**: PSP player of `0x498` bytes against `$400`; a PSP clearing loop (72 longs from
  `+0x350`) overflowed into the next player.
- **Tables of function pointers** wrongly read as animation scripts: settle it with Ghidra (Allegrex
  extension, `max/outils/ghidra/ghidra_decomp.py`).
- **Byte frame of reference**: the same byte has two numbers depending on the frame of reference. In the CPS2 memory image, byte 0 of a step holds
  the flags; in the arcade and in the raw bytes of the file, byte 0 is the duration. Always say in which
  frame of reference you are writing.
- **Copied data**: tables read by address copied as big-endian; attacks: bytes `$12` / `$14` ×2.
- **vasm**: `cnop` pads with `$4E71` (NOP), not with zeros: pad explicitly (`dcb.b`) when a byte
  matters.

List of the pitfalls of the bench and the environment: [journal/ETAT-DES-LIEUX.md](../journal/ETAT-DES-LIEUX.md) §7.
