# HSFA builder (all-in-one executable) / Constructeur HSFA tout-en-un

One executable per system turns the player's own discs into the HSFA game archives, with nothing else to install:
- the *Street Fighter Alpha Anthology* PS2 image (`.iso` or `.chd`);
- optionally, the *SFA3 MAX* PSP ISO (Europe, `.iso` or `.chd`), for Upper MAX.

It runs `scripts/construction/hsfa_build.py` unchanged. It embeds Python with NumPy, Capstone and Pillow, the HSFA
scripts (`scripts/`, `src/`, `tools/`, `max/`) and three native tools:
- `hsfa_oggenc` (`tools/flux/oggenc`): the portable Ogg encoder, which gives the same zips on every system;
- `fluxtool`;
- libchdr.

It contains no game data. Licences: `TIERS.md`. User guide: `LISEZMOI.txt` (FR), `README.txt` (EN), shipped in each zip.

| File | Role |
|---|---|
| `hsfa_constructeur.py` | entry point: a window (tkinter) or text prompts; `--auto-test`; it also acts as the « python » of each build step (`exe script.py`, `-c`, `-m`) |
| `chd_iso.py` | `.chd` (DVD) → `.iso` (libchdr via ctypes). PS2: a sparse image holding only the needed files. PSP: the whole image |
| `natifs.py` | `hsfa_oggenc`, `fluxtool` and libchdr for one target, from official sources; zig cross-compiles all five targets from Linux |
| `fabrique.py`, `hsfa_constructeur.spec` | PyInstaller (one file), then `--auto-test` |
| `imports_embarques.py`, `releve_imports.py` | modules imported by the build steps, from an import trace of a full 4-game build |
| `requirements-constructeur.txt` | build environment, pinned with hashes (`pip install --require-hashes`) |
| `../../.github/workflows/constructeur.yml` | CI: natives (zig), one executable per system, Ogg determinism check on each system, attached to published releases |

Local build (Linux):

```
python3 tools/constructeur/natifs.py --cible hote --sortie natifs --sources sources --telecharge --cc gcc --cxx g++
python3 -m pip install --require-hashes -r tools/constructeur/requirements-constructeur.txt
python3 tools/constructeur/fabrique.py --natifs natifs     # -> tools/constructeur/dist/hsfa-constructeur
```

**En français.** Un exécutable par système, sans rien installer : ni Python, ni ffmpeg, ni gcc. Le joueur donne son
image PS2 (`.iso` ou `.chd`) et, s'il le veut, l'ISO PSP de SFA3 MAX ; il obtient les zips. Comme `hsfa_oggenc` est
portable, les zips ont les mêmes empreintes sur Windows, macOS et Linux (x86_64, ARM). Aucune donnée de jeu dans
l'exécutable.
