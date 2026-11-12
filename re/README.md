# `re/` — knowledge index (reverse engineering)

**Français : [README.fr.md](README.fr.md)**

A **lightweight** index of what the project knows about the addresses, tables, fields and routines of SFA3 (arcade), of
the PS2 modules `ro3` / `ro5` / `ro9`, of the final game `ro9a` and of SFA3 MAX (PSP). Purpose: **not to rediscover**
what is already established (the `$1A` field of the banks, Upper's reused slots `$27`-`$29`, `T_6139A4` made of pairs
of coordinates and not of pointers…) and **not to repeat mistakes**. It is not the decompilation kit yet (see the
end).

No game data here: only addresses, names, sizes, types and descriptions.

## Files

| file | content |
|---|---|
| `connaissances/sfa3_arcade.tsv` | SFA3 arcade: decrypted `sfa3ud` 68K ROM and arcade RAM (`$…`) |
| `connaissances/ro3.tsv`, `ro5.tsv`, `ro9.tsv` | SFA3, Upper, Hyper: PS2 (MIPS) **runtime** addresses |
| `connaissances/ro9a.tsv` | final game: Hyper + Upper's Arcade mode (graft, route B) + MAX characters |
| `connaissances/max_psp.tsv` | SFA3 MAX PSP (EU `ULES-00235`) |
| `connaissances/sfa1_arcade.tsv`, `sfa2_arcade.tsv`, `ssf2_arcade.tsv`, `cps1_arcade.tsv` | other measured arcade games (sfa/sfz; sfa2/sfz2al; ssf2/ssf2t; sf2hf/ffight): 68K addresses |
| `connaissances/z80_son.tsv` | Z80 sound drivers (v1.04 / v1.05 / v1.71…): addresses in each game's sound ROM (driver and game stated at the start of the role) |
| `connaissances/champs.tsv` | structure fields: player (`$FF8400 + $400·k`), objects, tasks, A5, PSP structures… |
| `allocations.tsv` | register of occupied areas (68K images, external blocks, RAM, character ids, graphics ROM…) |
| `outils/quoi.py` | lookup by address (any space, homologues and ranges included), name or keyword |
| `outils/verifie.py` | check: columns, address forms, duplicates, sources, anonymity, overlaps |
| `outils/zones.py` | list of areas per target, lookup of a range, overlap check |

Columns of the address files: `adresse`, `adresse_autres` (homologues `espace:adr; …`), `genre` (fonction |
table | variable | champ | structure | format | constante), `nom`, `role`, `taille_type`, `mises_en_garde`,
`source`, `confiance`, then two **optional** columns at the end of the line: `score` (matching, e.g.
"0,82 (12 votes)" for the Rosetta) and `outil` (script that produces or uses the entry). `champs.tsv`: `structure`, `decalage_ps2`, `decalage_arcade`, `decalage_autres`, `espaces`,
then the same columns. `allocations.tsv`: `cible`, `debut`, `fin` (inclusive), `occupant`, `etat` (utilisé |
réservé | libre prouvé), `source`, `remarque`.

```
python3 re/outils/quoi.py 0x6139A4        # PS2 runtime address
python3 re/outils/quoi.py T_749838        # name (and the address it contains)
python3 re/outils/quoi.py Juli            # keyword
python3 re/outils/quoi.py '$FF8503'       # CPS2 RAM: also finds player 1 +$103 (= $102 as a byte, XOR 1) and A5
python3 re/outils/quoi.py +$1A -s joueur  # field
python3 re/outils/quoi.py 0x20E500 --va   # va = offset in the module file (+ 0x1F0000)
python3 re/outils/zones.py image68k_ro5 0x3A0000 0x3BFFFF   # who occupies this range?
python3 re/outils/verifie.py
```

## Address conventions

| space (`adresse_autres`) | form | meaning |
|---|---|---|
| `arcade` | `$0DD412` (6 digits) | decrypted `sfa3ud` 68K ROM, or arcade RAM `$FFxxxx` |
| `ro3`, `ro5`, `ro9` | `0x749838` | PS2 **runtime** address = offset in the module file **+ `0x1F0000`**. Many reports write "va" for the file offset: `quoi.py` tries both |
| `ro9a` | see the header of `ro9a.tsv` | augmented module and image of the cited frozen build |
| `psp` | `0x00183A38` (8 digits) | SFA3 MAX PSP: **base-0 VA** of the decrypted EU EBOOT (MAX tools, Ghidra base 0 `FUN_…`) = **file offset − `0x74`** (the tools take `EBOOT[0x74:]`); segment 0 (code then read-only data): va `0`-`0x2D4F2F`; segment 1 (`.data` then `.bss`): from va `0x2D4F30`. Real memory under PPSSPP = `0x08804000 +` va. It is **not** a file offset, and `+ 0x1F0000` never applies to it. Offsets inside the entries of a `.pac` are not VAs: lines without an address (`format`) |
| `sfa1_arcade`, `sfa2_arcade`, `ssf2_arcade`, `cps1_arcade` | `$0012AB` | program ROM / 68K RAM of the named arcade game |
| `z80_son` | `$F000` (4 digits) | Z80 address in the sound ROM; the driver and the game are stated in the role |
| `img_ro3`, `img_ro5`, `img_ro9`, `img_ro9a` | `$1DFB78` | address in **the translated 68K image**: specific to **one build**, it moves with every rebuild (reread `carte_image.txt`) |
| `cps2` | `$FF40BC` | fixed address in the CPS2 map of the translated program (RAM, external blocks, registers): does not move |

- Arcade program: `sfa3_prog.bin` is the **opcodes** view (readable code, scrambled data); the **data**
  are read in the `sfa3ud` ROM (concatenated files, bytes swapped in pairs). A table read in
  `sfa3_prog.bin` is wrong (`max/outils/convert/README.md`).
- **Exact** space names in `adresse_autres`: `arcade` (SFA3), `ro3`, `ro5`, `ro9`, `ro9a`, `psp`, `img_ro3`,
  `img_ro5`, `img_ro9`, `img_ro9a`, `cps2`, `sfa1_arcade`, `sfa2_arcade`, `ssf2_arcade`, `cps1_arcade`, `z80_son`.
  Tolerated synonyms (to avoid): `upper` = `ro5`, `hyper` = `ro9`, `sfa3` = `arcade`, `max` = `psp`.
- **"CPS2 mode" recipe**: byte = address **XOR 1**, word = same address, long = halves swapped. So
  `MOVE.B $5(A6)` (image) = `MOVE.B $4(A6)` (arcade) = `lb 4(A6)` (MIPS). `quoi.py` tries the address XOR 1 for RAM.
- Game RAM on the PS2 side: `0x900000-0x90FFFF` (ro3) and `0xA00000-…` (Upper) = `$FF0000-$FFFFFF`. `A5 = $FF8000`.
- A5 fields: **unsigned** 16-bit displacement (`$C0BC(A5)` = `$FF40BC`; `-$7178(A5)` is written `+$8E88`).
  `quoi.py` goes from `$FFxxxx` to the A5 displacement and to the player field (`$FF8400 + $400·k + décalage`).
- `decalage_ps2` = displacement used by the MIPS (and by the image, bytes XOR 1 aside); `decalage_arcade` =
  original 68K numbering. The port relocated part of the A5 variables of the lower half (see
  `docs/reference/SYMBOLES.md` §4).
- Reference builds of the `img_*` addresses:

| space | build | md5 |
|---|---|---|
| `img_ro3`, `img_ro5`, `img_ro9` when the `source` cites `references/v149` (added automatically to functions) | **v149 references** (`<workspace>/work/references/v149/roN`, translator at git tag `v149`): 1st instruction produced for the function's va (gap < `0x40`) in `carte_image.txt` | `sz3ud.03c` ro3 `7e22b1ec7d7a20ff05f401ddaa36c2da`, ro5 `7898814ceb4335d6cba06f58d3496ddf`, ro9 `cb9b37b90c2adc848abd6dad72c536e5` (restated in `source`) |
| `img_ro9a` | `ro9a3_fige` (graft, step 3) | `sz3ud.03c` `217fc51c03d1c0a581d95a1c00029700`, module `ro9a_module.bin` `4440a95de9ee61a19622c4f4dec4d2bc` |
| `img_*` of the other lines | the one of the report cited in `source` | often older than v149 and not recorded: recheck in `carte_image.txt` |

## Confidence levels

- **mesuré** (measured): observed on the bench or in the code and verified (trace, comparison with the arcade,
  reading of an instruction).
- **déduit** (deduced): inferred by static reading or reasoning (automatic alignment, code homology), without
  verification on the bench.
- **supposé** (assumed): hypothesis, "probable", unvalidated automatic transfer, outdated section. To be checked
  before using it.

Taken over from `tools/symboles/symboles_ro3.csv`: "sûr" (sure) from the journal → mesuré; automatic "sûr" → déduit;
"probable" and "hypothèse" → supposé (the original level is restated in `source`). Upper's functions taken
from the transfer sketch (`symboles_ro5_esquisse.csv`, "identique" or "structure" matching,
score ≥ 0.9) are "supposé", except those confirmed by an independent source: address cited by an Upper
report (the report's line is authoritative), or agreement of the first 68K instructions produced for ro3 and ro5
in the v149 maps (≥ 6 identical instructions, absolute addresses masked) → "déduit".

## Adding a line

1. **Before analysing an address**, `quoi.py <adresse>`: what is already known, and above all the warnings.
2. After a discovery: one line in the TSV of the **main** space (a single line per thing; the
   other spaces go into `adresse_autres`); a field goes into `champs.tsv`.
3. Always a `source` (journal `§N`, or report path + section; outside the repository: `<workspace>/…`) and a
   `confiance`. **Nothing invented**: when in doubt, "supposé". Pitfalls go into `mises_en_garde`.
4. A code or data area we are going to occupy: **reserve it first** in `allocations.tsv`, then
   `zones.py --verifie`.
5. `python3 re/outils/verifie.py` must end with "0 erreur(s)".

An empty address is allowed only for a `format`, a `structure` or a `constante` without an address (file format,
rule). No tab or line break in a cell; hexadecimal in upper case; a range is written `a-b`
(inclusive) in `adresse`, or as the size `N × B|W|L` at the start of `taille_type`, or `(N o)`.

## Later: the decompilation kit

At the end of the project, this index will be the basis of the **full kit**: exports to Ghidra / IDA / MAME (labels,
types, comments), C headers of the structures (player, objects, A5, formats), annotated maps per build.
None of this is done yet: here, only the knowledge, with sources.

Known conflicts and decisions: [CONFLITS.md](CONFLITS.md).
