# Sounds of the PS2 port that are silent in Upper and Upper MAX

Agent `sons_ps2_upper`, 2026-11-12. Follow-up of [SONS-PS2-HYPER.md](SONS-PS2-HYPER.md) (Hyper, §218), decision of
12/11 ("Upper: check Dee Jay's taunt and extend `sons_ps2` to Upper if it is silent"). Static analysis, then bench
(headless core and PCSX2, §4).

## 1. In short

- Upper keeps the hybrid sound ROM (Upper's Z80 + SFA3's music). Its PS2 module (`ro5`) has **the same native sound
  table as Hyper** (`0x1200` entries, identical byte for byte to `ro3` and `ro9`), so the same commands lead to an SPU2
  sample on PS2 and to an empty Z80 command on CPS2.
- Statically, Upper's code can send **only two** of these commands (each on both sides):

| command (side 1 / side 2) | when | PS2 sample (bank, SE index → Sset → VAG, rate, length) | evidence |
|---|---|---|---|
| `057D` / `0A7D` | **Dee Jay ($22): taunt** | `e342`, index 29 → Sset 28 → VAG 28, 22 050 Hz, 0.34 s | entry 34 of Dee Jay's sound table (module `0x638D94`, translated image `$0CF0D4`, same in Upper MAX); measured on PS2 in Hyper (SONS-PS2-HYPER §8.4) |
| `040F` / `090F` | **Birdie ($08)**: entry 15 of his sound table, move not identified | `e322`, index 15 → Sset 27 → VAG 27, 22 050 Hz, 1.08 s | Birdie's table (module `0x763F6C`, image `$1FA2AC`) ; the SFA3 arcade table (`$115D10`) has the same entry and the arcade Z80 has the same empty command |

- So **Dee Jay's taunt is silent in Upper and in Upper MAX** (confirmed at the bench, §4; as it was in Hyper before §218), and Birdie's entry 15
  is silent too (also in Hyper before §218, and in SFA3 arcade).
- Fix: `tools/son-hyper/sons_ps2.py --jeu upper` / `--jeu uppermax` adds these two sounds (same samples, same pitch
  and same levels as Hyper's) to a copy of Upper's sound ROM; build steps `sons_ps2_upper` and `sons_ps2_uppermax`;
  same switch `HSFA_SONS_PS2` (`0` = byte-identical copy). Hyper's sound ROM does not change (same MD5).

## 2. Method (as for Hyper, statically)

1. **Native table**: `ro5` (`0x628780`) = `ro9` (`0x5CB300`) = `ro3`, 0 differing entries. Bank of a command: type 3/4
   → `e345`/`e346`; type ≥ 5 → character `PT[type-5]` → file `T[character]`. Upper's `T` is at `0x628370` (Hyper:
   `0x5AF2B0`); it is Hyper's up to `$25`, except entry 38 (Cammy ALPHA, Hyper only: `e344` in Hyper, `e314` in Upper).
2. **Sample**: `o4` is an index of the SE table of the MOMO container (4th part), as found for Hyper (§8.1); a command
   "has a PS2 sound" if the index is active, its volume is not zero and the zone of its program resolves to a VAG.
3. **Empty on CPS2**: no piece in the Z80 command table of the hybrid ROM (Upper), or of the MAX sound ROM (Upper MAX).
   Result: 78 commands for the hybrid ROM, 50 for the MAX ROM (the MAX voices took some of these numbers, e.g. `041E`,
   `05EB`, `05F0`, `05F1`).
4. **Can Upper's code send them?** For each candidate (and its side-2 `+$500`):
   - MIPS immediates of the `ro5` module (`addiu`/`ori` from `$zero`) and `#$xxx` immediates of the map of the translated
     v161 image: only data words and one coordinate comparison (`CMPI.W #$550,$12(A3)` at `$0A076E`); no sender. In
     particular no `#$245` and no `#$27D` (both sent by immediates in Hyper) and no parry code.
   - **Per-character sound tables** (`$E6`, entries `[code, code_alt, 0, 0]`): Upper's pointer table, indexed by the
     character id, is at module `0x74C538` (found from Dee Jay's table, entry `$22`). Only two candidates appear: Dee
     Jay `[34] = 057D` and Birdie `[15] = 040F`. Evil Ryu (`$17`) and Shin Akuma (`$24`) use Ryu's and Akuma's tables.
     Birdie's table has 35 entries: no `041F` (Hyper's has 36).
   - **Cries / K.O.** (base + 0..6): Upper's base table is at module `0x613490`; all its bases have non-empty commands
     (Evil Ryu takes Ryu's `0300`), so no silent cry.
   - Other "tables" found by the pattern search (`0x6F243A` and two copies: `05EF/05F6`, `05F0/05F7`, …) are tile maps,
     not referenced by the sound code.
   - Upper MAX (image of the build `max57` + its external blocks): same two tables; the MAX characters' tables only use
     commands that the MAX sound ROM fills.
5. **Cross-check with Hyper's in-game sweep** (418 runs, SONS-PS2-HYPER §8.2): the ZERO 3 versions outside the S-ISM
   modes (code taken from Upper's; Upper has no S-ISM) only sent `057D` (Dee Jay) among these commands.

## 3. The fix (`sons_ps2.py --jeu upper|uppermax`)

- `SONS_UPPER = [("birdie", [0x040F], 322, [15]), ("dee_jay", [0x057D], 342, [29])]`, used for `upper` and `uppermax`;
  Hyper's list is unchanged (`--jeu hyper`, default).
- Same conversion and placement rules as Hyper's: native rate (pitch measured on PS2 for `e342` VAG 28 in Hyper), QSound
  bank `$FF` (not referenced by the hybrid ROM nor by the MAX ROM), Z80 sample entries 1535 and 1534, program table at
  `$7F80` through `NEWPT[23]`, op `07` levels of `VOLUMES` (calibrated for Hyper: `040F` `$7F`, `057D` `$6E`).
- **Pieces in bank 6** (`0x2A000`, inside the free zone `0x29B55-0x2BBFF` of SON-HYPER-ROM §6) for Upper and Upper
  MAX: in the MAX sound ROM, bank 15 is used up to `0x4FDCF` by the MAX voices, so Hyper's `0x4F400` is not free there.
  Hyper keeps `0x4F400` (its ROM does not change).
- Checks done by the tool (as for Hyper): the 3 068 other commands resolve to the same content, the QSound zones they
  reference are unchanged, the driver code is unchanged, the chosen zones are free.
- Results (hybrid of 2026-10-04 and MAX ROM of batch 2b31, user's X_DATA):
  - Upper: `hx3.01` `458551a8`, `hx3.02` `6b69a5d2`, `hx3.14m` `b3c1f692` (others = hybrid);
  - Upper MAX: `hx3.01` `5e878c14`, `hx3.02` `02d80006`, `hx3.14m` `144441ce` (others = MAX ROM);
  - Hyper with the modified tool: unchanged (`349593e9`, `d3affb3c`, `3aaf2675`);
  - `HSFA_SONS_PS2=0`: the six files are copied byte for byte (checked for the three games).
- Build: steps `sons_ps2_upper` (after `son_upper`; writes `agent_son_ro5/hybride/roms_upper`, read by `paquet_upper`
  through `HSFA_SON_UPPER`) and `sons_ps2_uppermax` (after `son_uppermax`; writes `agent_son_max/roms_son_max_ps2`,
  passed as `MAX_SON` to `paquet_uppermax`). `HSFA_SONS_PS2` is now part of the key of the three `sons_ps2*` steps
  (before, changing it did not redo Hyper's step).

## 4. Bench (12/11)

Headless core (core batch 12/11b; test zips = v0.1.9 control zips with the three sound members replaced):
- **Command queue**: Upper's 68K sound queue is at `$FFDE80` / `$FFEE80`, as in Hyper.
- **Isolated rendering** (each command posted alone in the attract mode, minus the same post on the v0.1.9 zip): the
  four commands play the PS2 sample (correlation 0.61-0.87 with the sample decoded from the ISO) in Upper and Upper MAX;
  on the v0.1.9 zip they play nothing. The level measured in the attract mode is noisy (±2 dB, voices taken from the
  demo music), but the QSound sample bytes and the Z80 track (op `05`/`06`/`07`/`1F`/note) are **identical to Hyper's**
  (whose level was calibrated at ±0.4 dB); only the program index differs.
- **In game, Dee Jay's taunt** (Arcade, Coin button of P1, Upper and Upper MAX): sound identical to v0.1.9 until the
  taunt, then the added sound correlates with `057D` (0.60); same game **without** the taunt: WAV identical byte for
  byte to v0.1.9.
- **Birdie**: 6 fights of ~100 s of random play (Upper and Upper MAX): `040F` never sent, WAV identical to v0.1.9.

PCSX2 (all-unlocked ISO; Upper = the SFA3 card confirmed while holding Select; 68K RAM at EE `0xA00000`, A5 read in the
scratchpad at `0x70001114`):
- **Dee Jay's taunt sends `057D` four times** (during the taunt animation, P1 side) and the SPU2 plays `e342` VAG 28 at
  its native rate (pitch `$0759`), as in Hyper.
- Birdie: 7 min of random play (about 450 commands, including Birdie's `0401`-`0403`, `0417`-`041D`): `040F` never sent.

## 5. Open

- Birdie's move for entry 15 is still unknown (never seen in Hyper's sweep, nor in these tests).
- SFA3 (arcade sound ROM) has the same silent Birdie entry; it is arcade-accurate and is not changed.
- Workshop tests and tools: `<workspace>/work/sons_ps2_upper/essais/` (`LISEZMOI.md`).
