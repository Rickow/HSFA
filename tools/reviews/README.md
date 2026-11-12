# Tools of the critical reviews (2026-11-11 / 12)

Static analysis tools written by the critical reviews of the translator, of the graft "Hyper + Arcade", of the MAX
character tables and of the Upper MAX integration, kept because they still serve: **guards** to rerun after a change
(translator build, graft state, Upper MAX integration) and **audits** to reopen a finding. The reports, with what each
tool found, are in [`docs/rapports/reviews/`](../../docs/rapports/reviews/README.md). One-off scripts, bench trial
scripts and the outputs stayed in the workshop (`<workspace>/work/revue_*`, `tables_max_greffe`, `arbitrages_um`).

Common points:
- Python 3, standard library (`compare_psp2.py`: numpy; `arc.py`, `img.py`, `fragments_atteints.py`: capstone, both in
  `requirements.txt`). Run with `nice -n 19 python3 -I <tool>.py ...` from any folder. The usage is at the top of
  each file (docstring).
- **Read only**: they read the user's data (decompressed PS2 modules, builds, the PSP EBOOT) and print to standard
  output. Nothing from the game goes into the repository: keep the outputs in the workshop.
- No personal path: each folder has a `paths.py` that resolves the inputs from arguments or environment variables
  (below); the repository's own files (`src/hsfa`, `tools/greffe-arcade/construction/`, `tools/integration-max/`) are
  found relative to the tool. File names are those cited by the reports (French).

## `translator/` — translator review (report [translator.md](../../docs/rapports/reviews/translator.md))

Variables: `HSFA_MODULES` (folder of `roN_usa_prog68k.bin`; default `$HSFA_WORKSPACE/anthology_extract/decompressed`),
`HSFA_BUILD` (translator build, `%s` = module, e.g. `<workspace>/work/v161/constr/%s_a6`), or `CARTE` (one
`carte_image.txt`), `IMG` (program ROM folder, `img.py`), `HSFA_ARCADE_PROG` (decrypted `sfa3ud` program, `arc.py`).
Shell scripts: `HSFA_TRAD` (runnable copy of the translator), `SORTIE` (default `./revue_interrupteurs`),
`RO9_EXTRACT_MODULES` / `RO9_SON_DONNEES` for ro9.

```sh
export HSFA_MODULES=<workspace>/anthology_extract/decompressed HSFA_BUILD=<workspace>/work/v161/constr/%s_a6
for m in ro3 ro5 ro9; do python3 -I tools/reviews/translator/bcc_apres_appel.py $m | tail -1; done   # 0 expected
python3 -I tools/reviews/translator/drapeaux.py ro3 > <workspace>/work/<folder>/drapeaux_ro3.txt
```

| tool | role |
|---|---|
| `paths.py` | common paths (HSFA_MODULES, HSFA_BUILD / CARTE, IMG, HSFA_ARCADE_PROG); library |
| `carte.py` | reader of a build's `carte_image.txt` (image address, MIPS offset, text); library |
| `voir.py roN OFF` | MIPS around a file offset with named slots + the 68K lines emitted at each address |
| `ctx.py roN ADR` | map lines around an image address |
| `img.py roN ADR` | disassembles the translated image of a build (capstone) |
| `arc.py dis ADR` / `cherche HEX` | disassembles / searches the decrypted arcade program (capstone) |
| `appelants.py roN OFF` | function containing OFF, its callers, whether they re-read RES/C after the return |
| `drapeaux.py roN` | **guard**: every Bcc, MIPS flag slot vs last 68K flag setter (ECRASE, PERDU, TAILLE, APPEL, OPERANDE) |
| `bcc_apres_appel.py roN` | **guard**: Bcc reading a callee's flags while the MIPS recomputes RES (lost compare); 0 expected (v161) |
| `aides_appels.py roN` | **guard**: recompiler helper calls (movem, andi_ccr, abcd, roxr, sbcd) rendered inline or lost; 0 "NON RENDU" expected |
| `a8_hors_zone.py roN` | **guard**: A8 / D8 slot accesses outside any borrowed zone of extra_regs.plan |
| `rendus.py roN` | flags returned to the caller through RTS: last setter vs last MIPS write of RES |
| `scc.py roN` | Scc rendered as Bcc/MOVE/BRA/CLR whose old flags are still read |
| `retenue.py roN` | last setter before BCS/BCC/ADDX/ROXR/ABCD suspect for the carry |
| `tailles.py roN` | size of the MIPS write of a Dn slot vs size of the emitted 68K instruction |
| `decalages.py roN` | 68K form emitted for each sllv/srlv/srav |
| `mults.py roN` | mult/div of the translated zone and what is emitted |
| `parite.py roN` | byte d16(An) accesses with fixed XOR 1 while An is statically odd |
| `parite_mixte.py roN` | same An used by a byte stream and by a fixed byte access |
| `parite_tri.py roN [class]` | sorting of the fixed byte accesses by parity proof (even strong / weak, odd, unknown) |
| `adda_trou.py roN` | (An) byte accesses after ADDA in the old byte_after_adda hole |
| `flux_meme.py roN` | byte stream pointers re-read then stored, with fixed accesses in between |
| `flux_ptr.py roN` | pointers stored after a byte advance and fixed accesses through a re-read of the same field |
| `relectures.py roN EA` | every re-read MOVEA.L EA,An of a field with the following lines |
| `ecritures_mem.py roN` | MIPS memory writes with no map entry (independent of AUDIT_MEM) |
| `ecritures_an.py roN` | writes of A0-A6 slots with no nearby map entry |
| `zones_conflit.py roN` | borrowed zones: real register used, calls inside, overlaps |
| `tables_sauts.py roN` | jump tables vs data (truncated?, holes, index bound) |
| `non_alignes.py roN` | lwl/lwr/swl/swr pairs and leftovers, what is emitted |
| `reloge_refs.py roN` | indirect readers of the tables relocated by steps B / C |
| `recense_mips.py roN` | census of the MIPS mnemonics of the 68K zone |
| `appels_c.py roN` | jal to native C functions: listed in hooks_fork or not, caller recompiled or C |
| `fragments_c.py roN FILE` | what the image executes at the label of an unlisted C function (fragments) |
| `fragments_atteints.py roN FILE` | real target (stub / fragment / other) of those calls in the image bytes |
| `natifs.py roN [lo hi]` | functions of a zone: 68K slots, map lines, callers, hooks class |
| `natif_ecrit.py roN START` | memory writes of one native function, classed by target |
| `cibles_natives.py roN` | code pointers of translated code that point to a native C function |
| `construit.sh NAME [VAR=val]` | one translator build (no emulator) from a runnable copy (`HSFA_TRAD`) |
| `interrupteurs.sh [module]` | switch audit: one build per switch off (and default-0 switches on), ~75 builds for ro3 |
| `interrupteurs_liste.sh mod VAR=val…` | same for a given list of settings |
| `interrupteurs_bilan.py RES DIR [mod]` | digest of the switch audit: identical / different / failure, log and map differences |

The build itself already runs the main guards (`build.log`, "GARDE-FOU (v161)", journal §219); these tools give the
site lists. The historical switches found by the switch audit are listed in
[pieges-du-traducteur.md §10](../../docs/methodes/pieges-du-traducteur.md).

## `graft/` — graft review (report [graft.md](../../docs/rapports/reviews/graft.md))

Variables: `HSFA_GRAFT_BUILD` (frozen build `ro9aNN_fige`; an argument overrides it where the tool takes one),
`HSFA_GRAFT_STATE` (repository copy of the graft, default `ro9a38`), `HSFA_MODULES`, `HSFA_F390` (arcade animation
file 390, default `$HSFA_WORKSPACE/work/cps2/anims/f390.bin`), `HSFA_REVIEW_OUT` (folder of `classe.tsv` /
`laisses.txt` read back by later tools, default `./sorties`).

```sh
export HSFA_MODULES=... HSFA_F390=... HSFA_GRAFT_BUILD=<workspace>/work/greffe_arcade/e48/ro9a38_fige
mkdir -p sorties && G=<repository>/tools/reviews/graft
python3 -I $G/classe_relogements.py > sorties/classe.tsv && python3 -I $G/laisses.py > sorties/laisses.txt
grep ' preuve ' sorties/laisses.txt      # R3 check: nothing expected since ro9a38
python3 -I $G/registres.py --detail 804166
```

| tool | role |
|---|---|
| `paths.py` | common paths; library |
| `classe_relogements.py [build]` | classify every aligned long of Upper's copied data: relocated or left raw, nature, proofs, reads (`classe.tsv`, base of R1-R5) |
| `laisses.py` | candidate pointers left raw, by target (copied / reused / absent), proof and reads; R3 check |
| `tri_128.py` | sort the "absent target, no proof, read/read" cells into data / pointer / undecidable |
| `r3_creux.py` | cause of each proven pointer left raw (bank hole, segment, exclusion list, target) |
| `ctx.py ADR` | 16-bit words around a cell of Upper's data, relocated cells marked |
| `decision.py SITE` | the graft's decision (grafted block or last decision) for an Upper routine |
| `orig.py ADR` / `uADR` | file offset of a copy of Upper <-> Upper's file offset |
| `refs_code.py LO HI [mod]` | code constants (lui + addiu / ori / access) falling in a range: who refers to a table |
| `refs.py MOD ADR` | who references an execution address in any module (e.g. `ro9a_module.bin`): jal / j, code constants, aligned data words |
| `dis_mips.py MOD OFF N` | MIPS disassembly with the repository's decoder (renamed from `dis.py`: that name hides Python's `dis`) |
| `p2_cmp.py U H` | compare the MIPS body of an Upper routine with its Hyper homologue (unified diff) |
| `atteint2.py START SITE [build]` | reachability by direct and far calls (lui / addiu / jalr) in the graft's MIPS |
| `registres.py [build] [--detail REG]` | writes and reads of the hardware registers and the graft's A5 variables, by side (Hyper / copy / stub) |
| `index_tables.py [build]` | index of the data tables read by the grafted code and by Hyper (symbolic execution); shared tables, MAX ids |
| `banque_e0.py [build]` | sprite entries whose common-bank entry differs between Hyper and Upper, and what `DECOR_E0` did |

## `max-tables/` — per-character-id tables (report [max-tables.md](../../docs/rapports/reviews/max-tables.md))

Variables: those of `graft/` plus `HSFA_UM_BANC` (bench folder of an Upper MAX build: `max_agrandies.txt`,
`ext_e80000.bin`), `HSFA_HYPER_INDEX` (Hyper's static index: `tables_homologues.json`, `scan_tables102.json`,
`tables_102.json`); see `paths.py`. Outputs go to `HSFA_REVIEW_OUT` (default `./sorties`).

```sh
M=<repository>/tools/reviews/max-tables
python3 -I $M/croise_upper_max.py > sorties/croise_upper_max.txt && python3 -I $M/maitre.py   # about 20 s -> sorties/TABLES.tsv
```

| tool | role |
|---|---|
| `paths.py`, `lib_idx.py` | paths; symbolic-execution engine of `graft/index_tables.py` as a library, with memory writes and constant sites |
| `croise_upper_max.py` | net 1: Upper MAX's list of per-id tables carried over into the graft build, with readers |
| `feuilles_id.py`, `propage_id.py`, `scan2.py`, `scan_feuilles.py` | nets 2-3: fields that carry an id, propagation, tables read with them |
| `forme40.py`, `entetes40.py` | nets 4-5: tables by shape (40 / 48 entries, offset headers) |
| `maitre.py`, `notes.py` | merge into `TABLES.tsv`; hand corrections (French notes) |

## `upper-max/` — Upper MAX integration (reports [upper-max.md](../../docs/rapports/reviews/upper-max.md), [upper-max-arbitrations.md](../../docs/rapports/reviews/upper-max-arbitrations.md))

Variables: `HSFA_CACHE` (`<output>/cache` of a `hsfa_build.py` run: default for the next two), `HSFA_MODULES`,
`HSFA_PSP_BOOT` (decrypted SFA3 MAX EBOOT, EU). `BENCH` = bench folder of an Upper MAX build
(`max_agrandies.txt`, `ext_*.bin`, `max_journal.txt`).

```sh
U=<repository>/tools/reviews/upper-max
python3 -I $U/essai_controles.py                       # site checks of integre_max.py: 0 failure expected
SFA3MAX_CACHE=<cache>/max_regen python3 -I $U/essai_nr.py <build>   # 9/9 expected
python3 -I $U/non_posees.py <bench> > non_posees.tsv
```

| tool | role |
|---|---|
| `paths.py` | common paths; library |
| `essai_controles.py [integre_max.py]` | negative tests of the integration's site checks (`_site_unique`, `_cible`, `_recoupe`) on a synthetic image |
| `essai_nr.py BUILD` | negative tests of the blocking "unresolved conversion" check and its allow-list (9 tests) |
| `non_posees.py BENCH` | per-id tables extended to 48: is each MAX entry set, or left at the default |
| `rangees.py` | per-id tables declared with one row whose room allows several (repository files only) |
| `recense_id.py CARTE` | independent census of the tables read by the character id in Upper's map, unknown to the integration |
| `compare_psp2.py BENCH` | PSP homologue of each per-id table by best alignment, MAX entries against the PSP (numpy) |
| `releve_tables.py BENCH` | table `0x615940` and the Arcade masks: PSP, Upper, Upper MAX copy (switches `MAX_615940_PSP`, `MAX_MASQUES_PSP`) |
| `releve_palettes.py BENCH CONV PAC` | effect palettes beyond 30 and what the engine reads instead (switch `MAX_PALE_PLEINES`) |

Already in the repository before (not duplicated here): the equivalence controls of the integration,
`tools/integration-max/upper_max/controle/` (`compare_cartes.py`, `equiv_integration.py`, `equiv_pointeurs.py`,
`litteraux_figes.py`).
