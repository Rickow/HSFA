"""Emplacements des fichiers de l'utilisateur. Le dépôt ne contient AUCUNE donnée de jeu :
tout se lit depuis des fichiers désignés par variables d'environnement (voir README.md).
Les caches (tuiles décodées = données dérivées du jeu) vont hors du dépôt."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)                              # tools/ du dépôt
UNTRANSPILE = os.path.join(os.path.dirname(TOOLS), "src", "hsfa")   # traducteur HSFA (ex-tools/untranspile)
MAPPING = os.path.join(HERE, "pl_mapping.json")
CACHE = os.path.expanduser(os.environ.get("SFA3MAX_CACHE", "~/.cache/sfa3max"))
os.makedirs(CACHE, exist_ok=True)
def _need(var, what):
    v = os.environ.get(var)
    if not v:
        sys.exit(f"Variable d'environnement {var} non définie : {what}.\nVoir tools/max/README.md.")
    return os.path.expanduser(v)
def eboot():      return _need("SFA3MAX_EBOOT", "EBOOT EU déchiffré de SFA3 MAX (ULES00235_EBOOT.BIN)")
def iso():        return _need("SFA3MAX_ISO", "ISO EU de SFA3 MAX (ULES-00235)")
def sfa3_zip():   return _need("SFA3_ZIP", "set CPS2 complet sfa3.zip (prog + gfx)")
def anthology():  return _need("ANTHOLOGY_DIR", "dossier des conteneurs extraits de l'Anthology (roN_usa_gfx_*.bin)")
def ee_std():     return _need("EE_STD", "dump EE 32 Mo de l'Anthology, SFA3")
def ee_hyper():   return _need("EE_HYPER", "dump EE 32 Mo de l'Anthology, Hyper SFA")
def sfa3ws_dir(): return _need("SFA3WS_DIR", "dépôt SFA3max-PSP-widescreen (lecteur ISO9660)")
def pac_dir():    return os.path.expanduser(os.environ.get("SFA3MAX_PAC_DIR", os.path.join(CACHE, "pac")))
