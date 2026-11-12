# Building the games from the ISO

**Français : [construction-iso.fr.md](construction-iso.fr.md)**

`scripts/construction/hsfa_build.py` rebuilds SFA3, Upper and Hyper from **your** ISO of *Street Fighter
Alpha Anthology*: extraction, translation of the three modules, graphics ROM, sound, tables, and FBNeo core archives.
Full report: [rapports/BUILD.md](../rapports/BUILD.md) (§143-§144 of the journal).

## 1. Requirements

- Python 3.8+ and the modules of `requirements.txt` (`pip install -r requirements.txt`, preferably in a venv);
  numpy is used by the graphics steps (`gfx_*`). No MAME, no external assembler: the chain's 68000 assembler is in
  Python.
- For the music of the Upper and Hyper archives in Ogg Vorbis (the default): `gcc` and `g++`. The encoder
  `hsfa_oggenc` (`tools/flux/oggenc/`, README) is compiled once, from the official sources of libvorbis,
  libogg and musl (`construit_oggenc.py --sources DIR --telecharge`, then `HSFA_OGGENC_SOURCES=DIR`, or a ready-made
  binary through `HSFA_OGGENC`). No more ffmpeg since 08/11 (§206). Without `gcc` / `g++`: `--flux-format adx` (Hyper
  zip of about 740 MB instead of 190) or `--sans-flux`. Without installing anything: the all-in-one builder
  (`tools/constructeur/`, one executable per system attached to the releases), which also reads `.chd` files.
- The USA ISO (`SLUS-21317`, 2,048 bytes/sector). `.chd`, `.bin` and `.cso` images are refused: convert to `.iso`
  first. A folder that contains `X_DATA.BIN` is accepted too.
- Optional: `--arcade sfa3.zip` (SFA3 arcade graphics ROM) instead of rebuilding it from the ISO.
- For **Upper MAX** (Upper + Eagle, Maki, Yun, Ingrid; §5): the **European** PSP ISO of *Street Fighter Alpha 3
  MAX* (ULES-00235 v1.01, `.iso`). Nothing else to install: the MAX code is assembled by the project's 68000
  assembler (`tools/asm68k/`, Python). vasm can still be used for comparison (`HSFA_ASM=vasm`, or `HSFA_ASM=compare`).

## 2. Configure

Nothing to configure: the tools are taken from the repository itself. `config.env` (copy of `config.example.env`) is
only used to take other tools (`HSFA_OUTILS_*`) or for the MAME bench.

The scripts called keep `<workspace>/...` paths: `hsfa_build.py` replaces them at run time (`PARAMETRAGES` table
of the script) and runs each tool in a subprocess with a clean environment.

## 3. Build

```bash
python3 scripts/construction/hsfa_build.py \
    --anthology "Street Fighter Alpha Anthology (USA).iso" --sortie hsfa_sortie --jeux sfa3,upper,hyper
```

| Option | Effect |
|---|---|
| `--jeux sfa3,upper,hyper` | games to build (default: the three); `uppermax` as well: Upper MAX (§5); `hyperarcade`: Hyper + Arcade (§6, experimental) |
| `--psp-iso ISO` | (Upper MAX) European PSP ISO of SFA3 MAX; without it, `uppermax` = Upper |
| `--vasm CHEMIN` | (Upper MAX, optional) path of `vasmm68k_mot` for `HSFA_ASM=vasm` or `compare` |
| `--arcade ZIP\|DOSSIER` | arcade graphics ROM (otherwise "ISO only" route, the default) |
| `--liste` | list of the steps |
| `--etape NOM` / `--jusqua NOM` | redo from NOM / stop after NOM |
| `--force` | redo everything (to use after a change to `hsfa_build.py` itself) |
| `--comparer DOSSIER` | compare the outputs with an existing bench |
| `--date-source SECONDES` | date of the zip members (default `$SOURCE_DATE_EPOCH`, otherwise 1980-01-01) |
| `--plans-fenetre auto\|oui\|non` | layer tables limited to the codes honoured by the bench and the core |
| `--flux-format ogg\|adx` | format of the Upper and Hyper music streams in the zips (default `ogg`) |
| `--sans-flux` | no stream table and no streams in the zips (disc music missing) |
| `--rejeu-table FICHIER` | (Hyper) replay table of the SFA1 / SFA2 sounds (default: `tools/son-hyper/rejeu/hsfa_rejeu_table.txt` if it is there); with it, per-version voice redirection and replay (§4) |
| `--sans-redirection` | (Hyper) neither voice redirection nor replay, even with the table |
| `--greffe-releves DOSSIER` | (Hyper + Arcade) graft records other than the repository's (§6) |
| `--outils-*` | location of each group of tools (otherwise `HSFA_OUTILS_*`) |

Each step is **idempotent**: it is skipped if its inputs, its tools and its parameters have not changed
(`etat.json`). A full build takes about 6 min (including 1 min 30 of Ogg encoding); a rerun without changes, a few seconds.

## 4. Outputs and checking

- `hsfa_sortie/EMPREINTES.txt`: md5 of all the ROMs produced and of the archive contents.
- `hsfa_sortie/journal.txt` (marks `>>` step, `ok`, `!!` anomaly) and `journaux/<étape>.log`.
- Core archives: `archives/sfa3hsfa.zip`, `sfa3uhsfa.zip`, `sfa3hhsfa.zip`. They are deterministic: two
  builds give the same bytes, Ogg included. Since 08/11 (§206, `hsfa_oggenc`), this holds from one
  system to another (Linux, Windows, macOS, x86_64, ARM): same fingerprints everywhere.

What is guaranteed (BUILD report §0, §3, §5; check of 2026-10-27 against the official v151 zips, redone on 2026-10-28 in v153 and on 2026-11-03 in v154
(from the ISO, without table: Hyper `dda35430…`), "All Unlocked" ISO, `--arcade`):
- the program ROMs are **identical (md5)** to those of the official zips: SFA3 `e0f1cfdc…`, Upper `0b8ecca2…`, Hyper
  `b8e699cf…` (with the replay table); since translator v161 (2026-11-11, §219): SFA3 `a569c361…`, Upper
  `ac053140…`, Hyper `dbfd237d…` (with the table; without: `ffc5eac1…`); v160 (§207): SFA3 `9b06c7cf…`, Upper `3a9b7fd9…`,
  Hyper `0baed6af…` / `e3806660…`; v159 (§203-§204): Upper
  `45fd0244…`, Hyper `8e4f9ef2…` / `1f06234d…`;
- with `--arcade`, the archives too, member by member, except `hsfa_info.txt` (build log) and
  `hsfa_flux.bin`: its Ogg streams have the same audio, Vorbis packet by Vorbis packet, and only their comment
  header changes (encoder string without version since `+bitexact`);
- on the "ISO only" route, `sz3.14m`, `16m`, `18m`, `20m` are identical to the arcade; `13m`, `15m`, `17m`, `19m`
  cannot be (9 arcade tiles do not exist in the ISO), with no effect on the HSFA games;
- the ISO is checked **per game group**: the "All Unlocked" variant of `X_DATA.BIN` is fine too.

**Hyper: per-version voices and replay** (step `son_hyper`, SON-HYPER-ROM §12-§13):
- `gen_redirection.py` reads the `ro9` module extracted from **your** ISO and produces the patched module (70 words, md5
  `dcda2bb…`) and the `$E70000` data block (`son_donnees_ro9.bin`, 19,712 bytes, `ebefd8b2…`). Both contain game
  bytes: they are **regenerated at every build** and never published. The repository only provides tables:
  `ids_102.tsv` (versions), `correspondance.tsv` (SFA3 code → SFA1 / SFA2 command).
- The **replay table** (QSound traces of the SFA1 / SFA2 drivers, 3.2 MB) is a separate input: `--rejeu-table` or
  `tools/son-hyper/rejeu/hsfa_rejeu_table.txt`. The build adds the per-version shouts section to it. With it,
  Hyper's program is the v161 one (`dbfd237d…`; v160: `0baed6af…`; v159: `8e4f9ef2…`; v154-v158: `b8e699cf…`) and the zip contains `hsfa_rejeu.bin` (8 MB, copied from the
  ISO's `X_DATA.BIN`, CRCs checked) and `hsfa_rejeu_table.txt`.
- Without the table, Hyper keeps SFA3's voices for all its versions (program `ffc5eac1…` in v161, `e3806660…` in v160, `1f06234d…` in v159, `dda35430…` in v154-v158) and the zip has no
  replay: without the table, the replay codes would have no sound.

## 5. Upper MAX (SFA3 MAX characters)

```bash
python3 scripts/construction/hsfa_build.py --anthology "Street Fighter Alpha Anthology (USA).iso" \
    --psp-iso "Street Fighter Alpha 3 MAX (Europe).iso" --sortie hsfa_sortie --jeux upper,uppermax
```

- Result: `archives/sfa3umhsfa.zip` (driver `sfa3umhsfa` of the core). It is the state of batch **2b31**, ported to the current translator (v161: the
  program follows Upper's). The sound ROM is identical to that batch; with `--arcade`, the graphics too, except `hsfa_info.txt`.
- No PPSSPP dump and no decrypted EBOOT are needed: the ISO's `BOOT.BIN` is already in the clear. The ISO is
  checked: identity and fingerprints of the files read. A patched ISO (16:9 for example), an encrypted EBOOT or
  another region are refused with a message.
- Only the **European edition** is supported. The US and JP editions have shifted code.
- Time: about 2 min 30 more than Upper alone; space: about 500 MB more.
- Details and proof: [rapports/BUILD.md](../rapports/BUILD.md) §10;
  [tools/integration-max/upper_max](../../tools/integration-max/upper_max/README.md).

## 6. Hyper + Arcade (Upper's Arcade mode grafted onto Hyper, experimental)

```bash
python3 scripts/construction/hsfa_build.py --anthology "Street Fighter Alpha Anthology (USA).iso" \
    --sortie hsfa_sortie --jeux hyperarcade [--rejeu-table hsfa_rejeu_table.txt] [--arcade sfa3.zip]
```

- Translator: the graft has its frozen copy of translator **v161** (`untranspile3_v161`, state ro9a37, §221): the
  v161 fixes (§219) reach Hyper + Arcade.
- Result: `archives/sfa3hahsfa.zip` (driver `sfa3hahsfa` of the core), state **ro9a37** (11/11). `hyperarcade`
  adds `upper` and `hyper`: the graft starts from their outputs (modules, animations, banks, sound). Extra steps:
  `greffe_hyperarcade` (frozen code of `tools/greffe-arcade/construction/`, about 3 min) and `paquet_hyperarcade`.
- **With the arcade ROM and the replay table**: the zip is the ro9a37 one (delivered on 12/11, CRC `51882820`), except
  `hsfa_info.txt` (provenance) and the sound ROM (`hx3.01`, `hx3.02`, `hx3.14m`: sounds specific to the PS2 port added,
  §218; with `HSFA_SONS_PS2=0`, identical).
- **Without the replay table**: the graft starts from Hyper's original module. Hyper keeps SFA3's voices for all
  the versions, and the zip has no replay (`hsfa_rejeu.bin`, `hsfa_rejeu_table.txt` absent), like Hyper alone.
- **Without the arcade ROM** ("ISO only" route): graphics ROM rebuilt from the ISO, as for Hyper; only the
  graphics ROM, `hsfa_gfx.bin` and `hsfa_tab.bin` change (tile codes), the program is the same. In the core, the
  game and the picture are the same (the ground shadow of the ZERO / ZERO 2 characters is transparent on both routes
  since `HSFA_OMBRE_CODES`, BUILD §11.5).
- **Records**: the graft reads tables taken from MAME passes and workshop analyses (addresses and numbers
  only, 4.5 MB of TSV in `tools/greffe-arcade/construction/releves_ro9a37/`); `--greffe-releves` provides
  others. Details: [tools/greffe-arcade/construction](../../tools/greffe-arcade/construction/LISEZMOI.md).
- Time: about 2 min 30 more than Upper + Hyper (graft 130-160 s, package 8 s); space: about 0.4 GB more.
- Details and proof: [rapports/BUILD.md](../rapports/BUILD.md) §11.

## 7. Next

- Copy the zips to the console: [installation-android.md](installation-android.md),
  [installation-rocknix.md](installation-rocknix.md).
- The cores are compiled separately: [patches/fbneo](../../patches/fbneo/README.md).
