# HSFA builder (all-in-one executable) / Constructeur HSFA tout-en-un

One executable per system turns the player's own discs into the HSFA game archives, with nothing else to install:
- the *Street Fighter Alpha Anthology* PS2 image (`.iso` or `.chd`);
- optionally, the *SFA3 MAX* PSP ISO (USA or Europe, `.iso` or `.chd`), for Upper MAX.

It is THE way to build the games on Windows, Linux and macOS (since v0.1.11: no more `construire.bat` nor
`hsfa-<version>-construction.zip` in the releases; Windows: `hsfa-constructeur-windows-x86_64.zip`, with a window).
Advanced use: clone the repository (or GitHub's "Source code" archive) and run `hsfa_build.py` or `construire.sh`.
It runs `scripts/construction/hsfa_build.py` unchanged. It embeds Python with NumPy, Capstone and Pillow, the HSFA
scripts (`scripts/`, `src/`, `tools/`, `max/`) and four native tools:
- `hsfa_oggenc` (`tools/flux/oggenc`): the portable Ogg encoder, which gives the same zips on every system;
- `fluxtool`;
- `hsfa_rejeu_iso` (`tools/son-hyper/rejeu_iso`): runs the SFA1 / SFA2 sound drivers of the disc to rebuild
  Hyper's replay table;
- libchdr.

It contains no game data. Licences: `TIERS.md`. User guide: `LISEZMOI.txt` (FR), `README.txt` (EN), shipped in each zip.

| File | Role |
|---|---|
| `hsfa_constructeur.py` | entry point: a window (tkinter) or text prompts; `--auto-test`; it also acts as the « python » of each build step (`exe script.py`, `-c`, `-m`) |
| `chd_iso.py` | `.chd` (DVD) → `.iso` (libchdr via ctypes). PS2: a sparse image holding only the needed files. PSP: the whole image |
| `natifs.py` | `hsfa_oggenc`, `fluxtool`, `hsfa_rejeu_iso` and libchdr for one target, from official sources; zig cross-compiles all five targets from Linux |
| `fabrique.py`, `hsfa_constructeur.spec` | PyInstaller (one file), then `--auto-test` |
| `test_selection.py` | game selection (`--jeux`, check boxes) against `hsfa_build.py`'s plan, without game data nor Tk |
| `imports_embarques.py`, `releve_imports.py` | modules imported by the build steps, from an import trace of a full 4-game build |
| `requirements-constructeur.txt` | build environment, pinned with hashes (`pip install --require-hashes`) |
| `../../.github/workflows/constructeur.yml` | CI: natives (zig), one executable per system, Ogg and `hsfa_rejeu_iso` determinism checks on each system, attached to published releases |

Duration and progress: before building, the builder announces the estimated time per game and in total (for example
`SFA3 ~2 min, Upper ~2 min, Hyper ~3 min, Upper MAX ~2 min ; total ~10 min`, longer on a slow machine; only the steps
that will run count, the steps already up to date in the output folder count for nothing; with a `.chd` image, before
unpacking it). The window shows a progress bar (`ttk.Progressbar`, standard library) « step n / N » with the time left,
updated at each step; the build runs in its own thread, the window only reads a queue, so it never freezes. In a
terminal, each step line carries the same information. The estimate comes from `hsfa_build.py` (`DUREES_REF`,
`prevoit()`, callback `AVANCEMENT`), calibrated on a measurement: the 5 games from an empty output folder in 12 min on an
i5-13500H (Windows). In the window, each game box shows its approximate time below it (« ≈ 2 min » for a game that will
be built, « +≈ 2 min » for what ticking a free box adds) and the selection's total (« Total ≈ 10 min »); the log area
grows with the window.

Games (`--jeux` / `--games`, one check box per game in the window): SFA3, Upper, Hyper, Upper MAX (greyed until a PSP
ISO is given, ticked when one is) and Hyper + Arcade (experimental graft; its version is the one `hsfa_build.py` sets,
`HA_ETAT` and its recipe). Hyper + Arcade MAX is not offered: it needs core patch 0033, absent from the published cores.
Without `--jeux` nothing changes: `sfa3,upper,hyper`, plus `uppermax` with `--psp`. What a choice pulls in is read from
`hsfa_build.py`'s own plan (`Construction.etapes()`, built in a throwaway folder: the output folder is never touched)
and shown as it is: a game whose zip is made too is ticked and greyed, « needed by … » (Hyper + Arcade builds Upper and
Hyper with their zips; Upper MAX builds Upper with its zip); steps run without their zip are named (Hyper alone runs
Upper's `son_upper` and `gfx_upper`, no Upper zip). The estimated time follows the selection (empty output folder; the
announcement at the start of the build then counts only the steps that will run). A small counter next to the progress
bar shows the elapsed time; the log, and `hsfa-travail/journal.txt`, end with « Durée totale / total time ». A PSP ISO
given without Upper MAX chosen is not read. Checks without game data: `test_selection.py` (CI) and `--auto-test` (plan
of Hyper + Arcade).

Output format (`--cible`, also a menu in the window): `fbneo-hsfa` (default, the current zips, unchanged);
`fbneo-autonome` (standalone FinalBurn Neo HSFA for Windows, test build, `patches/fbneo-autonome`): the builder announces
its concession (RetroArch save states do not load in it), asks for confirmation, then builds the same zips as
`fbneo-hsfa`, byte for byte; `mister` and `cps2-banques` do not exist yet: the builder announces, per game, the
concessions of that format and the measured budgets (`scripts/construction/cibles.py`), asks for confirmation and builds
nothing (report mode). `--oui` / `--yes` confirms without asking. The announcements are in French or English
(`HSFA_LANGUE=fr|en`, otherwise the system language).

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

Durée et avancement : avant de construire, le constructeur annonce la durée estimée par jeu et au total (par exemple
`SFA3 ~2 min, Upper ~2 min, Hyper ~3 min, Upper MAX ~2 min ; total ~10 min`, plus sur une machine lente ; seules les
étapes qui vont tourner comptent, celles déjà à jour dans le dossier de sortie ne comptent pas ; avec une image `.chd`,
avant de la décompresser). La fenêtre montre une barre d'avancement (`ttk.Progressbar`, bibliothèque standard)
« étape n / N » avec le temps restant, mise à jour à chaque étape ; la construction tourne dans son propre fil, la
fenêtre ne fait que lire une file : elle ne se fige jamais. Dans un terminal, chaque ligne d'étape porte la même
information. L'estimation vient de `hsfa_build.py` (`DUREES_REF`, `prevoit()`, rappel `AVANCEMENT`), recalée sur une
mesure : les 5 jeux depuis un dossier de sortie vide en 12 min sur un i5-13500H (Windows). Dans la fenêtre, chaque case
de jeu porte sa durée approximative en dessous (« ≈ 2 min » pour un jeu qui sera construit, « +≈ 2 min » pour ce que
cocher une case libre ajoute) et le total de la sélection (« Total ≈ 10 min ») ; la zone du journal s'agrandit avec la
fenêtre.

Jeux (`--jeux` / `--games`, une case par jeu dans la fenêtre) : SFA3, Upper, Hyper, Upper MAX (grisée tant qu'aucune
ISO PSP n'est donnée, cochée quand elle l'est) et Hyper + Arcade (greffe expérimentale ; sa version est celle que fixe
`hsfa_build.py`, `HA_ETAT` et sa recette). Hyper + Arcade MAX n'est pas proposé : il demande le patch 0033 du cœur,
absent des cœurs publiés. Sans `--jeux`, rien ne change : `sfa3,upper,hyper`, plus `uppermax` avec `--psp`. Ce qu'un
choix entraîne est lu dans le plan de `hsfa_build.py` lui-même (`Construction.etapes()`, dans un dossier jetable : le
dossier de sortie n'est jamais touché) et montré tel quel : un jeu dont le zip est produit aussi est coché et grisé,
« requis par … » (Hyper + Arcade construit Upper et Hyper avec leurs zips ; Upper MAX construit Upper avec son zip) ; les
étapes faites sans leur zip sont nommées (Hyper seul fait `son_upper` et `gfx_upper` d'Upper, sans zip d'Upper). La
durée estimée suit la sélection (dossier de sortie vide ; l'annonce au début de la construction ne compte ensuite que les
étapes qui vont tourner). Un petit compteur à côté de la barre montre le temps écoulé ; le journal, et
`hsfa-travail/journal.txt`, finissent par « Durée totale / total time ». Une ISO PSP donnée sans Upper MAX choisi n'est
pas lue. Contrôles sans donnée de jeu : `test_selection.py` (CI) et `--auto-test` (plan d'Hyper + Arcade).

Format de sortie (`--cible`, ou menu de la fenêtre) : `fbneo-hsfa` par défaut (les zips actuels, inchangés) ;
`fbneo-autonome` (FinalBurn Neo HSFA autonome pour Windows, version d'essai, `patches/fbneo-autonome`) : le constructeur
annonce sa concession (les sauvegardes d'état de RetroArch ne s'y chargent pas), demande confirmation, puis construit les
mêmes zips que `fbneo-hsfa`, à l'octet ; `mister` et `cps2-banques` n'existent pas encore : le constructeur annonce les
concessions de ce format pour chaque jeu et les budgets mesurés (`scripts/construction/cibles.py`), demande confirmation
et ne construit rien (mode bilan). `--oui` / `--yes` confirme sans question. Annonces en français ou en anglais
(`HSFA_LANGUE=fr|en`, sinon la langue du système).

Sortie (v0.1.11) : les zips des jeux sont **à la racine** du dossier de sortie ; tout le reste (cache, travail,
journaux, `etat.json`, `journal.txt`, `EMPREINTES.txt`, `<jeu>_sources.txt`, ISO tirées d'un `.chd`) est dans
`hsfa-travail/`. Un dossier de sortie d'une version précédente (`archives/`, `etat.json` à la racine) est rangé ainsi au
premier passage (`hsfa_build.dossier_travail()` ; le rangement ne force aucune étape). Reprise : depuis la v0.1.11,
l'exécutable réutilise les étapes déjà faites (une construction finie ou interrompue) ; jusqu'à la v0.1.10 il refaisait
tout à chaque lancement, car les clés des étapes contenaient son dossier temporaire d'extraction (`_MEI…`, nouveau à
chaque lancement) : une sortie faite par l'exécutable v0.1.10 est donc reconstruite une fois. Fin de la construction : son du système (sans
dépendance : `bell()` de Tk et `winsound` sous Windows, cloche du terminal sinon), fenêtre ramenée au premier plan et
message « Terminé : N jeux dans … » ou l'échec avec le chemin du journal.

L'exécutable sert aussi de « python » aux étapes (`<exe> script.py …`, `-c`, `-m`). L'exécutable gelé démarre Python
**isolé** (`sys.flags.isolated = 1`) : il ignore `PYTHONPATH`, `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`… et ne met
pas le dossier courant dans `sys.path`. En rôle d'interpréteur, `_role_python()` refait donc ce que fait CPython au
démarrage : `sys.path[0]` (dossier courant pour `-c` / `-m`, dossier du script sinon), `PYTHONPATH` (avant les modules
embarqués), `-B` / `PYTHONDONTWRITEBYTECODE`, `PYTHONPYCACHEPREFIX`, `-u` / `PYTHONUNBUFFERED`, `PYTHONIOENCODING`,
`-E` / `-I` / `-P` ; trace et code 1 sur une exception, code 2 pour un script absent. Restent différents (fixés au
démarrage) : mode UTF-8 toujours actif (`.spec`) et hachage non aléatoire. L'attente « Entrée pour fermer » (Windows,
image glissée sur l'exécutable) ne se fait jamais en rôle d'interpréteur, et les étapes ont l'entrée standard fermée.
Contrôle sans donnée de jeu (CI, 5 systèmes) : `test_windows.py --parties interprete --exe <exe>` (mêmes réponses que le
vrai python : `PYTHONPATH`, dossier courant, `-I`, `-B`, codes de sortie, script à un argument avec l'entrée ouverte).

Essai de bout en bout par l'exécutable (local, il faut les images du joueur ; impossible en CI sans donnée de jeu) :
fabriquer l'exécutable comme la CI (`python -m pip install --require-hashes -r tools/constructeur/requirements-constructeur.txt`
dans un venv, puis `fabrique.py --natifs <natifs de ce système> --dist DIST`), puis le lancer comme un joueur,
environnement vide, sans python dans le `PATH` et entrée standard fermée (une attente d'Entrée échoue au lieu de
bloquer) :

```bash
mkdir -p path_min && ln -sf "$(command -v nice)" path_min/nice
env -i HOME="$HOME" LANG=C.UTF-8 PATH="$PWD/path_min" DIST/hsfa-constructeur --console ANTHOLOGY.iso \
    --psp SFA3MAX.iso --sortie SORTIE_VIDE </dev/null
md5sum SORTIE_VIDE/*.zip    # = construction de contrôle par python (hsfa_build.py) du même commit
grep -h "^=== .*_lancer" SORTIE_VIDE/hsfa-travail/journaux/*.log | grep -vc hsfa-constructeur   # 0 : tout par l'exe
```
