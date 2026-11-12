# Memory in "CPS2 mode" (§29)

**Français : [memoire-cps2.fr.md](memoire-cps2.fr.md)**

## 1. The problem

The PS2 code reads and writes memory as **little-endian**, at PS2 addresses. The CPS2's 68000 is
**big-endian**, with its own map (RAM `$FF0000`, video `$900000`, objects `$700000`…). On top of that, the recompiler
typed memory **field by field** (§44): the same 68K byte is not always in the same place, depending on how
the field is read. Recovering the exact arcade layout requires typing each field; that is the eventual goal of
the [data relayout](ARCHI-Reorganisation-Donnees.md).

## 2. The universal recipe

Decision of §29: for a game **that works**, it is enough for the 68K to see memory **the way the PS2 code sees it**.

| PS2 access (host address h) | 68K translation |
|---|---|
| word | same address h |
| byte | h XOR 1 |
| long | same address, halves swapped (`SWAP`) |

The recipe needs no knowledge of the fields. It holds for longs at 2 mod 4 and for all three games. Cost:
one `SWAP` per long access, except memory → memory copies and immediates, pre-swapped at translation.

## 3. Address conversion

`translate.addr_to_68k` converts address constants, in this order:
1. port variables that "mirror" the hardware → real CPS-A/B registers, inputs `$804000…` (§57, §62);
2. PS2 RAM → `$FF0000`, QSound → `$618000`, objects → `$700000/$708000`, video → `$900000` (`ADDRMAP`);
3. module data → `DATA_BASE` in ROM, or `DATA_EXT` when the program exceeds 4 MB (`$C80000` Upper,
   `$940000` Hyper);
4. variables of the port itself → `PORT_RAM` (`$F00000`).

Hardware addresses get the high byte `$01` (`HW_TAG`), ignored by the 24-bit bus, so that they are not
converted again (§63).

**Pointers read from memory**: they are PS2 addresses. A data pointer is converted after each `MOVEA` that
loads it ("convert An" stubs at `$000400`, §63, §104). A code pointer goes through a **hash table**
PS2 address → 68K (`$3C0000`, 16,384 entries, §98) before each `JSR/JMP (An)`.

## 4. Register bank of the recompiler (correct version)

| Slot `0x7000xxxx` | 68K register |
|---|---|
| `0x1100-0x111C` | A0-A7 (A7 = MIPS stack of the port) |
| `0x1120` | **A8** (extra) |
| `0x1124-0x1140` | D0-D7 |
| `0x1144` | **D8** (extra) |
| `0x114C` | private stack |
| `0x1150` | RES (Z, N) |
| `0x1154` | X |
| `0x1158` | **C (carry)** |

Execution base `0x1F0000`; the 68K starts at `0x22B00` (ro3, ro5) or `0x22DE0` (ro9). See also
[OUTILS.md](OUTILS.md) §2.4.1.

## 5. Exceptions and pitfalls

1. **Signed A5 displacements**: `$BE48(A5)` = `$FF3E48`, `-$7178(A5)` = `$FF0E88` (§67, §86, §108).
2. **Exact bytes** (no XOR): input ports and QSound (§62, §78); `(An)+` streams, odd indexes, byte after
   `ADDA Dk,An`: the exact address is computed at run time (§65, §66, §97).
3. **Longs with swapped halves in memory**: an object's X/Y at `+$12/+$16` instead of `+$10/+$14`; state bytes
   `$4-$7` swapped per word; a long pushed as is stays swapped (§77).
4. Byte-reversed word read from an **indexed** table (§92, §100); long stored byte by byte (`bswap32`, §90).
5. An **odd** constant is never a data address (§101).

**Consequence for the tools**: any script that compares the translation with the arcade must normalise (byte `a` of the
ROM = byte `a ^ 1` of the translation, X/Y shifted, state bytes swapped). The accessor `disposition.lua`
([tools/reorg](../../tools/reorg/)) reads the translated RAM by arcade address.

## 6. Map of the produced image

The 4 MB program ROM holds the vectors, the conversion stubs, the task kernel (`$000B00`), the translated
code (`$001000…`), the module data, the resources, the hash table (`$3C0000`) and the table of function
starts (`$3E0000`). Outside the ROM: task stacks (`$660000`), object memory, video, external blocks (`$A00000-$EFFFFF`),
work RAM (`$FF0000`). Full table: [OUTILS.md](OUTILS.md) §1.4; useful addresses:
[reference/adresses.md](../reference/adresses.md).
