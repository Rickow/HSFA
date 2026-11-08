# Third-party components of the HSFA builder / Composants tiers du constructeur HSFA

The HSFA builder is one executable per system. It contains HSFA's own code (MIT, see `LICENSE`) and the components
below, each under its own licence. It contains **no game data**: the games are rebuilt from your own discs.
Everything is rebuilt from public sources by `.github/workflows/constructeur.yml` (`tools/constructeur/natifs.py`,
`fabrique.py`); the source archives are checked against fixed SHA-256 sums (`tools/flux/oggenc/construit_oggenc.py`),
a fixed commit (libchdr) or `--require-hashes` (PyPI).

| Component | Version | Use | Licence |
|---|---|---|---|
| Python | 3.14 | runs the HSFA scripts | PSF License 2.0 |
| NumPy | 2.5.4 | graphics, sound and build steps | BSD-3-Clause; its wheels bundle OpenBLAS (BSD-3-Clause), libgfortran (GPL-3.0 with the GCC Runtime Library Exception) and libquadmath (LGPL-2.1; source: https://gcc.gnu.org), see NumPy's `LICENSE.txt` |
| Capstone | 5.0.9 | Upper MAX steps (68000 disassembly of the PSP code, no game data embedded) | BSD-3-Clause |
| Pillow | 13.0.0 | Upper MAX steps (portraits, screens) | MIT-CMU (HPND); its wheels bundle libjpeg-turbo, libpng, zlib, libtiff, libwebp, FreeType, LittleCMS, OpenJPEG, HarfBuzz…, each under its licence (BSD-style, zlib, IJG, FreeType License), see Pillow's `LICENSE` |
| Tcl/Tk (tkinter) | 8.6 / 9.0 | builder window | Tcl/Tk licence (BSD-style) |
| PyInstaller bootloader | 6.22.3 | single-file executable | GPL-2.0 with the bootloader exception (any licence allowed for the bundled program) |
| libvorbis, libogg (Xiph.Org) | 1.3.7, 1.3.6 | `hsfa_oggenc`: Ogg Vorbis music, unmodified except four lines of `lib/os.h` (portable rounding, see `tools/flux/oggenc/README.md`) | BSD-3-Clause |
| musl (math functions, fdlibm) | 1.1.21 | `hsfa_oggenc`: the same math results on every system (15 files of `src/math`) | MIT; fdlibm files: Sun Microsystems notice (free use, notice kept) |
| stb_vorbis (Sean Barrett) | 1.22 | Ogg check in `fluxtool` | public domain or MIT |
| libchdr (Romain Tisserand) | commit 47d7941 | reads `.chd` disc images | BSD-3-Clause; includes LZMA SDK (public domain), miniz (MIT), zstd (BSD-3-Clause), dr_flac (public domain / MIT-0); `LICENSE-libchdr.txt` |
| zig toolchain runtime (native tools only) | 0.17.1 | C runtime linked into `hsfa_oggenc`, `fluxtool`, libchdr: musl libc (Linux, MIT), mingw-w64 runtime (Windows: ZPL-2.1 / MIT / public domain), LLVM libc++ / compiler-rt (Apache-2.0 WITH LLVM-exception) | as listed |

Not included: FFmpeg (not needed since `flux_ogg` version 3), vasm (HSFA uses its own 68000 assembler,
`tools/asm68k/`), MAME / chdman, any ROM, BIOS or disc image.

**En français.** Le constructeur contient le code d'HSFA (MIT) et les composants ci-dessus, chacun sous sa licence ;
aucune donnée de jeu. Tout se reconstruit depuis les sources publiques par la CI du dépôt (`tools/constructeur/`),
avec des empreintes fixées. Ni FFmpeg, ni vasm, ni MAME : la musique est encodée par `hsfa_oggenc` (libvorbis /
libogg, BSD-3 ; fonctions mathématiques de musl, MIT), les persos MAX par l'assembleur 68000 du projet.
