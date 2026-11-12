# Route B: grafting Upper's Arcade mode onto Hyper

**Français : [voie-b-greffe.fr.md](voie-b-greffe.fr.md)**

User's decision of 2026-10-10 (§144, replaces the "Upper base" of §143): the final product starts from the
**Hyper** module (`ro9`). Upper's **Arcade mode** layer is grafted onto it **at the MIPS level** ("augmented ro9"). Upper
serves as the oracle: its 40 endings are validated. Reports: [ETUDE-UPPER-HYPER](../rapports/ETUDE-UPPER-HYPER.md) (the choice),
[GREFFE-PREPARATION](../rapports/GREFFE-PREPARATION.md) and [GREFFE-DECORS](../rapports/GREFFE-DECORS.md) (the
preparation). Tools: [`tools/greffe-arcade/`](../../tools/greffe-arcade/), [`tools/etude-upper-hyper/`](../../tools/etude-upper-hyper/).

## 1. Why B rather than A

| | Route A: Upper base + Hyper | Route B: Hyper base + Upper's Arcade |
|---|---|---|
| code to graft | ≈ 1.1 MB of MIPS, ≈ 34,000 68K instructions, 1,445 version tests | ≈ 98 KB missing (≈ 3,350 instr.), ≤ 260 KB as an upper bound |
| data | 2.4 MB, all the attack data to convert | ≈ 0.1-0.3 MB (ending scripts, opponents, scenes) |
| main risk | rebuilding Hyper inside Upper | the A5 RAM (Upper variables removed by Hyper) and the reads of `$102` |

Hyper has no Arcade mode; its PS2 Arcade patch ([legacy](../../legacy/README.md)) is not ported.

## 2. What is established (§145)

- **Scenes**: `A5+4 = 6` CONTINUE, `8` GAME OVER, `A` character ending and credits, `C` exit; between two fights,
  `A5+4 = 4` and `A5+8` is `0` (init), `2` (map), `4` (face-off, VS), `6` (fight), `8` (victory).
- **Core to graft**: 530 routines, 287 KB of MIPS, ≈ 9,950 68K instructions, of which 164 routines (111 KB) are missing
  from Hyper; the rest is modified by Hyper.
- **A5 relocation table**: 443 displacements used; 36 relocated into Hyper's free zone `$FF43BE-$FF7FFF`.
- **Rule `$102` → `$116`**: a read that indexes a per-character table goes through `$116`; a write of the id also sets
  `$116/$117`; a copy keeps `$102` (the version).
- **Host zone**: Hyper's recompiled Z80 (file `[0x20, 0x22B00)`, 142 KB), never translated nor called by
  Hyper's 68K. Not enough for everything: an added data block is served by the translator.
- **Prototype**: next opponent (`0x250EF0`) and its two callees; assembly of the augmented module with no unresolved symbol;
  the 68K translation of the graft is identical instruction for instruction to Upper's, apart from the relocated A5.
- **Stages**: 39 of Upper's 40 stages are missing from Hyper ([GREFFE-DECORS](../rapports/GREFFE-DECORS.md)).

## 3. Planned chain

1. `tools/greffe-arcade/outils/greffe.py` copies the core routines into the host zone, relocates the A5 and the `lui`,
   copies the tables.
2. The translator (dedicated copy) also translates the grafted zone; `mame_test.py` builds augmented Hyper.
3. Oracle: the same scripted games as Upper (`tournee.lua`, `tournee_greffe.lua`), comparison of scenes and endings.
4. MAX: integrated on Upper first, then transposed (98 engine addresses out of 120 identical in Hyper).

## 4. Current step

Step 2 of `greffe_arcade`: full graft of the core, ending data (gfx 391-418, anim 458-485), stages.
