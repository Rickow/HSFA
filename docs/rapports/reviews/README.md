# Critical reviews of 2026-11-11 / 12

Reviews made by agents, mostly by static reading (MIPS of the PS2 modules, translated image, arcade, build outputs),
some followed by bench trials. Each file below starts with an **English summary** (main findings, what was fixed and
where, what is still open) followed by the **original report in French, kept as written** (only the paths are
anonymised: `<workspace>/...`). The journal section that points to them is §222 of
[`docs/journal/HANDOFF.md`](../../journal/HANDOFF.md); the fixes are in §219 (translator v161), §220 (Upper MAX on v161),
§221 (Hyper + Arcade ro9a37) and §223 (ro9a38). The tools that still serve are in
[`tools/reviews/`](../../../tools/reviews/README.md); the one-off scripts and the trial scripts stayed in the workshop
(`<workspace>/work/<review folder>/`), together with the outputs (some contain game data).

| report | subject | fixed in | still open (short) | tools |
|---|---|---|---|---|
| [translator.md](translator.md) | translator v160, two passes (A1-A3, B1-B4, E1-E8) | §219 (v161: 10 rules + build guards), §220, §221 | Scc / ADDI fragilities, rules without switch, parity of ~600 accesses undecidable statically, restart request `$F009C0`, historical switches ([pieges §10](../../methodes/pieges-du-traducteur.md)) | [`translator/`](../../../tools/reviews/translator/) |
| [graft.md](graft.md) | Hyper + Arcade ro9a36 / ro9a37: relocation R1-R5, banks, shared tables and ids, transitions; bench trials; blur zones (7 files) | §223 (ro9a38: R3, X6, A2a, E2b) | MAX ids (X2), R1 / R2 / R4 lists, residual stage differences, B1, T2 | [`graft/`](../../../tools/reviews/graft/) |
| [max-tables.md](max-tables.md) + [tables-max-ids.tsv](tables-max-ids.tsv) | every table indexed by a character id in ro9a37, for the MAX characters (210 tables) | — (X2 not in ro9a38) | ids and `T_BASE` values to decide, 41 tables to add to `X2_LISTE` | [`max-tables/`](../../../tools/reviews/max-tables/) |
| [upper-max.md](upper-max.md) | Upper MAX on v161 (part A) and review of the MAX integration (part B, 16 findings) | §220 (A, B1) | B2, B6, B8-B13; bench of the B4 / B5 / B7 switches | [`upper-max/`](../../../tools/reviews/upper-max/) |
| [upper-max-arbitrations.md](upper-max-arbitrations.md) | arbitration files A1-A4, A6 of the major findings B2-B5, B7 | commit `54d43f8` (A2 merged; A3, A4, A6 behind switches at 0) | A1 Yun `$32D` fix, bench trials E1-E3 | [`upper-max/`](../../../tools/reviews/upper-max/) |
| [core.md](core.md) | FBNeo HSFA core patches: first review (D1) and targeted v0.1.9 review (R1-R9) | v0.1.9: patch `0032` (R1), `W06` (R3) | D1 68000 registers survive a reload; R2, R4, R5, R7, R9; files not read | — |
| [anthology-jp.md](anthology-jp.md) | Japanese disc *Fighter's Generation* against the US *Anthology* | — | maintainer's choice between recognising the disc only and a "Zero 3" Japanese track | — |

`tables-max-ids.tsv` is the `TABLES.tsv` of the inventory (addresses, shapes, readers, what to set); it stays here
rather than in `re/`, whose files follow a fixed column format checked by `re/outils/verifie.py` (one line per address,
name, role, type): this one is the working table of a review, with its own 19 columns. Values longer than 4 bytes are
masked in this copy.

Reviews started and stopped (not written up): catching up the `re/` index (`<workspace>/work/rattrapage_re/`),
specification of the banked map (`<workspace>/work/spec_banques/`).
