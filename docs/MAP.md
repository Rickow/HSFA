# Project map

One page to find your way around HSFA: the games, where each kind of information lives, how a change is proven, and
the project's vocabulary. It summarises and links; it copies nothing. State on 2026-11-14 (release v0.1.10, journal
up to §231). If this page and a linked source disagree, the source is right.

## 1. The project in three sentences

*Street Fighter Alpha Anthology* (PS2) ships its arcade games as a static recompilation of the original 68000 code to
MIPS. HSFA translates that MIPS back to 68000, assembles CPS2 program ROMs and runs them in a patched FinalBurn Neo
core ("HSFA"). Everything is rebuilt from the user's own disc; the repository holds no game data.
Details: [AGENTS.md](../AGENTS.md) §1, [README](../README.md).

## 2. Games and drivers

| game | PS2 module | driver = archive | `--jeux` value | state |
|---|---|---|---|---|
| Street Fighter Alpha 3 | `ro3` | `sfa3hsfa` | `sfa3` | complete |
| SFA3 Upper | `ro5` | `sfa3uhsfa` | `upper` | complete |
| Hyper Street Fighter Alpha | `ro9` | `sfa3hhsfa` | `hyper` | VERSUS complete |
| Upper MAX (Upper + the four PSP characters) | `ro5` + PSP disc | `sfa3umhsfa` | `uppermax --psp-iso` | experimental |
| Hyper + Arcade (Upper's Arcade mode grafted onto Hyper, "route B") | `ro9` + Arcade layer of `ro5` | `sfa3hahsfa` | `hyperarcade` | experimental, state `ro9a41` |
| Hyper + Arcade with the MAX characters | same + PSP disc | `sfa3hamhsfa` | `hyperarcademax --psp-iso` | in progress: Eagle playable in VERSUS (§231), not released |

Building: [guide/construction-iso.md](guide/construction-iso.md). What each release contains:
[CHANGELOG.md](../CHANGELOG.md), [guide/LIVRAISONS.md](guide/LIVRAISONS.md). Development bench: a MAME fork, game
`sfa3hx` ([architecture/banc-mame.md](architecture/banc-mame.md)).

## 3. Where to find what

| need | where |
|---|---|
| rules, method, pitfalls, open work | [AGENTS.md](../AGENTS.md) (§2 rules, §3 method, §4 findings and MAX pitfalls, §5 open work) |
| what changed, version by version | [CHANGELOG.md](../CHANGELOG.md) |
| the detailed journal (French) | [journal/HANDOFF.md](journal/HANDOFF.md), sections "§N"; one line per section: [journal/INDEX-HANDOFF.md](journal/INDEX-HANDOFF.md) |
| an address, a field, a memory area | [re/README.md](../re/README.md): `python3 re/outils/quoi.py <address or name>`, `re/allocations.tsv`, known conflicts in [re/CONFLITS.md](../re/CONFLITS.md) |
| how the translator works, and its pitfalls | [architecture/traducteur.md](architecture/traducteur.md), [methodes/pieges-du-traducteur.md](methodes/pieges-du-traducteur.md) |
| CPS2 memory layout used by the project | [architecture/memoire-cps2.md](architecture/memoire-cps2.md) |
| the FBNeo core and its patch chain | [architecture/coeur-fbneo.md](architecture/coeur-fbneo.md), [patches/fbneo/README.md](../patches/fbneo/README.md) |
| the graft (route B) | [architecture/voie-b-greffe.md](architecture/voie-b-greffe.md); states `ro9a35b` to `ro9a41` and their switches: [tools/greffe-arcade/construction/LISEZMOI.md](../tools/greffe-arcade/construction/LISEZMOI.md) |
| the MAX characters | [max/notes/SAVOIR-MAX.md](../max/notes/SAVOIR-MAX.md), [rapports/INTEGRATION-MAX-UPPER.md](rapports/INTEGRATION-MAX-UPPER.md) |
| proving a change | [methodes/oracle-et-non-regression.md](methodes/oracle-et-non-regression.md), [tools/bancs/README.md](../tools/bancs/README.md) |
| tools | [tools/README.md](../tools/README.md), [scripts/README.md](../scripts/README.md) |
| study reports and critical reviews | [rapports/README.md](rapports/README.md), [rapports/reviews/README.md](rapports/reviews/README.md) |
| build report | [rapports/BUILD.md](rapports/BUILD.md) |
| credits and licences | [CREDITS.md](../CREDITS.md), [NOTICE.md](../NOTICE.md), [LICENSE](../LICENSE) |
| the whole documentation | [README.md](README.md) |

Repository layout: `src/hsfa/` translator and chain · `scripts/` build and validation · `tools/` tools by theme ·
`patches/` MAME fork and FBNeo core patches · `docs/` guide, architecture, reference, methods, journal, reports ·
`re/` knowledge index · `max/`, `tools/max/` MAX characters (separate session: do not change) · `legacy/` earlier
PNACH era.

## 4. How a change is proven

1. **An oracle, never the eye.** The arcade ROM under MAME for SFA3, Upper for the graft, the PSP game for the MAX
   characters. The same scripted game runs on both sides and quantities are compared.
2. **Every fix sits behind a switch** (an environment variable). At 0 the ROMs are byte-identical to the reference.
3. **Frozen copies.** Measurements run on a read-only copy of a build with its checksums, never on a build that
   someone else can rebuild. Each bench checks the fingerprint of what the emulator really loads.
4. **Benches before delivery**: the 42 commands and 32 endings of SFA3, Upper's 40 endings, Hyper's VERSUS, the 85
   Arcade runs of the graft, the MAX bench. See [tools/bancs/README.md](../tools/bancs/README.md).
5. **A control build before each release**: the five games rebuilt from the disc, from a clean archive of the
   repository, and their program checksums compared with the delivered ones.
6. **Hand-over**: a diff made with `git diff` in a clone rebased just before delivery, then
   `tools/verifie_versement.sh` ([AGENTS.md](../AGENTS.md) §2, rule 11).

## 5. Workstreams on 2026-11-14

Kept short on purpose; the table that is maintained is [AGENTS.md](../AGENTS.md) §5.

| workstream | state |
|---|---|
| MAX characters in the graft | five steps: L1 tables and sound (done, invisible to the player), L2 Eagle in VERSUS (done, §231), L3 Eagle complete (designed), L4 Maki and L5 Yun and Ingrid (designed) |
| SFA1 / SFA2 stages in the graft | data step done; first wiring step ready; shown through a core option during the prototype |
| Upper MAX | fidelity to the PSP game audited; remaining ending defects being fixed |
| Hyper's per-version voices from the disc alone | designed (replay table rebuilt during the build, planned for v0.2) |
| Fidelity audit of the translator and the graft | done; the largest gap is the 68000 load in fights |
| Output targets | standalone FinalBurn Neo for Windows as a test build; a "banked board" specification later |

## 6. Vocabulary

| word | meaning |
|---|---|
| `ro3`, `ro5`, `ro9` | the PS2 modules of SFA3, Upper and Hyper |
| `ro9a`, `ro9aNN` | "augmented ro9": Hyper plus Upper's Arcade mode; NN is the delivered state |
| graft, route B | grafting Upper's Arcade layer onto Hyper at MIPS level (route A, dropped: start from Upper) |
| MAX characters | Eagle, Maki, Yun, Ingrid, from the PSP game *SFA3 MAX*; `maxNN` is a validated Upper MAX batch |
| native | a character or code path of the original game, as opposed to the MAX characters |
| switch | environment variable that turns a fix on; at 0 the output is byte-identical to the reference |
| recipe | the file listing the switches of one graft state (`vars_ro9aNN.txt`) |
| frozen copy | read-only copy of a build with checksums, used as a measurement reference |
| byte witness | a rebuild with the new switches at 0, compared file by file with the previous frozen copy |
| fingerprint | checksum of what the emulator actually loads; a mismatch stops the bench |
| oracle | the measured reference (arcade, Upper, PSP or PS2 game) |
| image address, va, map | address in the produced 68000 image; original MIPS address; `carte_image.txt` links them. Image addresses change with every build: never hard-code one |
| tag `$01` | high byte put on a 68000 address outside the ROM so that it is not converted like a PS2 address |
| `RETAG24` | translator rule that restores the `$01` tag after a 24-bit mask; its code depends on the number of tagged ranges, so adding a range moves the translated code |
| holes | free areas of the CPS2 memory map that receive added data |
| slot 0-7 | graphics bank of an object: 0 common, 1 stage, 2 / 3 characters of players 1 / 2, 4 scene, 6 / 7 players 3 / 4 |
| `plan2` | renumbering table of the scroll2 layer, also used as slot 1 |
| X2 | window of the graft's data where per-character tables are copied with 48 entries |
| T4, T5 | memory areas reserved for the MAX characters' data and frames |
| MAX base | the graft with the MAX areas and tables but no MAX character: byte reference of the driver with MAX |
| stub | small added code that a site is redirected to; none is allowed on the natives' path during fights |
| springboard | inert site reserved in the code, later filled with a jump to a MAX routine |
| dispatch table | indexed jump table; "extended at the source" means enlarged before translation |
| §N | a section of the journal |
| L1-L5, E0-E8 | steps of the MAX integration in the graft; steps of the stage prototype |

## Clean integration principles

The project aims at the cleanest, best converted and most faithful result. Before writing a fix, check that it follows
these principles; if it cannot, stop and say why.

1. **No added code on the native characters' path in fights**: enlarge tables and redirect their readers (same
   instruction, same cost), extend jump tables at the source, write values in place. Outside fights, only if listed and
   proven (all 85 Arcade endings identical).
2. **Every change behind a switch**, with its default proven and a **byte-for-byte witness** with the switch off.
3. **Fix the cause, not the symptom**: a wrong value is fixed in the conversion (converter, relocation list, typing),
   not patched afterwards.
4. **The original is the oracle** (arcade for SFA3, PS2 for Upper / Hyper, Upper for the graft, PSP for the MAX
   characters): compare before deciding; a kept difference is a recorded decision, never an oversight.
5. **Reuse a proven method** (Upper MAX, earlier graft steps) before inventing one.
6. **No hard-coded image address**, no game data in the repository, everything rebuilt from the player's disc.
