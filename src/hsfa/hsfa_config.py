"""hsfa_config.py -- configuration centrale des chemins (proposition, NON branchee dans les scripts existants).

Le depot n'a aucune donnee de jeu. Les scripts ecrivent les chemins de l'espace de travail sous la forme
`<workspace>/...` (chemins absolus du poste de developpement, anonymises a la publication). Ce module dit ou se
trouvent ces dossiers sur VOTRE poste, a partir de variables d'environnement (voir config.example.env a la racine) :

  HSFA_WORKSPACE   racine de l'espace de travail (obligatoire) : work/, mame-fork/, venv/...
  HSFA_EXTRACT     extraction de l'ISO (manifest.csv, decompressed/roN_usa_prog68k.bin)
                   defaut : $HSFA_WORKSPACE/anthology_extract
  HSFA_XDATA       X_DATA.BIN de l'ISO                defaut : $HSFA_WORKSPACE/work/xdata/X_DATA.BIN
  HSFA_YDATA       Y_DATA.BIN (flux musique ADX)      defaut : $HSFA_WORKSPACE/work/xdata/Y_DATA.BIN
  HSFA_WORK        dossiers de travail (bancs, ROM)   defaut : $HSFA_WORKSPACE/work
  HSFA_SRC         outils du traducteur               defaut : le dossier de ce module (src/hsfa du depot)
  HSFA_CPS2F       binaire du fork MAME               defaut : $HSFA_WORKSPACE/mame-fork/mame/cps2f

Deux usages :
  - `localise(texte)` remplace les `<workspace>/...` d'un texte (script, commande) par les chemins locaux : c'est ce
    que fait scripts/localiser.py ;
  - `chemin("xdata")` etc. pour du code NEUF. Les scripts existants gardent leurs constantes et leurs variables
    d'environnement historiques (XDATA, EXTRACT_MODULES, HSFA_OUTILS_*, HSFA_WORK...) : les y brancher demande de
    revalider les ROM (md5) produites ; c'est a faire au fil de l'eau dans la copie de travail.
"""
import os

ICI = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.abspath(os.path.join(ICI, "..", ".."))
MARQUE = "<workspace>"


def workspace():
    w = os.environ.get("HSFA_WORKSPACE")
    if not w:
        raise SystemExit("HSFA_WORKSPACE n'est pas defini : voir config.example.env a la racine du depot.")
    return os.path.abspath(os.path.expanduser(w))


def chemin(nom):
    """chemin local d'un emplacement connu (voir l'en-tete du module)"""
    defauts = {
        "workspace": lambda: workspace(),
        "extract": lambda: os.path.join(workspace(), "anthology_extract"),
        "xdata": lambda: os.path.join(workspace(), "work", "xdata", "X_DATA.BIN"),
        "ydata": lambda: os.path.join(workspace(), "work", "xdata", "Y_DATA.BIN"),
        "work": lambda: os.path.join(workspace(), "work"),
        "src": lambda: ICI,
        "cps2f": lambda: os.path.join(workspace(), "mame-fork", "mame", "cps2f"),
    }
    if nom not in defauts:
        raise KeyError(nom)
    v = os.environ.get("HSFA_" + nom.upper())
    return os.path.abspath(os.path.expanduser(v)) if v else defauts[nom]()


def localise(texte, outils_du_depot=True):
    """remplace les chemins `<workspace>/...` d'un texte par leurs equivalents locaux.
    outils_du_depot=True : la copie de travail des outils (`<workspace>/scripts/untranspile`) et le depot
    (`<workspace>/github`) pointent vers CE depot ; les donnees (work/..., anthology_extract...) vers l'espace de
    travail (variables HSFA_*). Les modules Python publies ailleurs (mwo3_codec, lz148778) sont a cote de leurs
    utilisateurs dans src/hsfa : leurs anciens sys.path deviennent inutiles mais sans effet."""
    w = workspace()
    rempl = [
        (MARQUE + "/anthology_extract", chemin("extract")),
        (MARQUE + "/work/xdata/X_DATA.BIN", chemin("xdata")),
        (MARQUE + "/work", chemin("work")),
        (MARQUE + "/mame-fork/mame/cps2f", chemin("cps2f")),
    ]
    if outils_du_depot:
        rempl = [(MARQUE + "/scripts/untranspile", chemin("src")),
                 (MARQUE + "/github", DEPOT)] + rempl
    for a, b in rempl:
        texte = texte.replace(a, b)
    return texte.replace(MARQUE, w)
