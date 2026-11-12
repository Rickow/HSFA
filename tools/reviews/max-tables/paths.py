"""Path resolution shared by the per-character-id table tracer (tools/reviews/max-tables/); same variables as
tools/reviews/graft/paths.py, plus the Upper MAX bench and Hyper's index. No personal path: everything comes from
arguments or from these environment variables.

  HSFA_WORKSPACE    workspace root (<workspace>); only used to build the defaults below.
  HSFA_MODULES      folder of the decompressed PS2 modules roN_usa_prog68k.bin
                    (default: $HSFA_WORKSPACE/anthology_extract/decompressed).
  HSFA_F390         Upper's file 390 (sprite frames, f390.bin) (default: $HSFA_WORKSPACE/work/cps2/anims/f390.bin).
  HSFA_GRAFT_BUILD  frozen graft build (folder ro9aNN_fige: greffe.json, ro9a_module.bin, greffe_donnees.bin,
                    zone_decors.bin, b9/carte_image.txt), used when the tool gets no build folder as argument.
  HSFA_GRAFT_STATE  state of the graft code copy in the repository (default "ro9a38"):
                    tools/greffe-arcade/construction/<state>/ and releves_<state>/.
  HSFA_REVIEW_OUT   output folder of the tracer (croise.pkl, porteurs.pkl, feuilles.pkl, maitre.pkl, *.txt and
                    TABLES.tsv), also read back by the later steps (default: ./sorties).
  HSFA_UM_BANC      bench folder of an Upper MAX build: max_agrandies.txt (tables by id extended to 48) and
                    ext_e80000.bin (default: $HSFA_WORKSPACE/work/agent_integration_max/banc_max55).
  HSFA_HYPER_INDEX  folder of Hyper's static index: tables_homologues.json, scan_tables102.json, tables_102.json
                    (default: $HSFA_WORKSPACE/work/agent_hyper_index).

Game data (modules, file 390, builds) stays in the workspace: these tools only read it.
"""
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.normpath(os.path.join(ICI, "..", "..", ".."))
SRC_HSFA = os.path.join(DEPOT, "src", "hsfa")
CONSTRUCTION = os.path.join(DEPOT, "tools", "greffe-arcade", "construction")
BASE = 0x1F0000          # PS2 execution address of file offset 0 of a module


def _ws(*p):
    w = os.environ.get("HSFA_WORKSPACE")
    if not w:
        sys.exit("set HSFA_WORKSPACE (or the specific variable, see paths.py)")
    return os.path.join(w, *p)


def module(mod):
    """path of a decompressed module: a file path is returned as is, otherwise roN -> $HSFA_MODULES/roN_usa_prog68k.bin"""
    if os.path.isfile(mod):
        return mod
    d = os.environ.get("HSFA_MODULES") or _ws("anthology_extract", "decompressed")
    return os.path.join(d, "%s_usa_prog68k.bin" % mod)


def lit_module(mod):
    with open(module(mod), "rb") as f:
        return f.read()


def f390():
    return os.environ.get("HSFA_F390") or _ws("work", "cps2", "anims", "f390.bin")


def etat():
    return os.environ.get("HSFA_GRAFT_STATE", "ro9a38")


def code_greffe():
    """tools/greffe-arcade/construction/<state>/greffe (graft code, e35/ lists, recipes)"""
    return os.path.join(CONSTRUCTION, etat(), "greffe")


def carto():
    return os.path.join(CONSTRUCTION, etat(), "carto")


def releves():
    """tools/greffe-arcade/construction/releves_<state> (read traces, proven pointers, homologues)"""
    return os.path.join(CONSTRUCTION, "releves_" + etat())


def construction(arg=None):
    """frozen build: argument, else $HSFA_GRAFT_BUILD"""
    c = arg or os.environ.get("HSFA_GRAFT_BUILD")
    if not c or not os.path.isdir(c):
        sys.exit("frozen graft build not found: give it as argument or set HSFA_GRAFT_BUILD (folder ro9aNN_fige)")
    return c


def sorties(nom):
    """file in the output folder (created if needed)"""
    d = os.environ.get("HSFA_REVIEW_OUT", "sorties")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, nom)


def banc_um(nom):
    return os.path.join(os.environ.get("HSFA_UM_BANC") or _ws("work", "agent_integration_max", "banc_max55"), nom)


def index_hyper(nom):
    return os.path.join(os.environ.get("HSFA_HYPER_INDEX") or _ws("work", "agent_hyper_index"), nom)
