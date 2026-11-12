#!/usr/bin/env python3
"""paths.py -- common paths of the graft review tools (tools/reviews/graft/). Imported by the other scripts; nothing
to run.

The tools are static and read-only. They read a FROZEN build of Hyper + Arcade (a ro9aNN_fige folder made by the
graft: greffe.json, greffe_donnees.bin, zone_decors.bin, ro9a_module.bin, b9/carte_image.txt), Upper's decompressed
module (ro5), the graft's code and recordings kept in the repository (tools/greffe-arcade/construction/<state>/ and
releves_<state>/), and, for a few of them, the arcade animation file 390. Nothing is written except to standard
output.

Environment variables:
  HSFA_GRAFT_BUILD  frozen build folder (ro9aNN_fige); a command-line argument overrides it where the tool takes one
  HSFA_GRAFT_STATE  state of the repository's frozen graft copy (default: ro9a38) -> construction/<state>/greffe and
                    construction/releves_<state>/
  HSFA_MODULES      folder holding the decompressed modules roN_usa_prog68k.bin
                    (default: $HSFA_WORKSPACE/anthology_extract/decompressed)
  HSFA_F390         arcade animation file 390 as used by the CPS2 build (default: $HSFA_WORKSPACE/work/cps2/anims/f390.bin)
  HSFA_REVIEW_OUT   folder of this review's own outputs read back by later tools (classe.tsv from
                    classe_relogements.py, laisses.txt from laisses.py); default: ./sorties
  HSFA_WORKSPACE    the workspace (<workspace>), used only for the defaults above
"""
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.normpath(os.path.join(ICI, "..", "..", ".."))
SRC = os.path.join(DEPOT, "src", "hsfa")
GC = os.path.join(DEPOT, "tools", "greffe-arcade", "construction")
ETAT = os.environ.get("HSFA_GRAFT_STATE", "ro9a38")
CODE = os.path.join(GC, ETAT)                       # ro9a38/ : greffe/, carto/, eu/, paquet/
GREFFE = os.path.join(CODE, "greffe")
REL = os.path.join(GC, "releves_" + ETAT)
BASE = 0x1F0000                                     # base of Upper's module in PS2 memory (file offset + BASE)


def _erreur(msg):
    sys.exit("paths.py: " + msg)


def _espace(*p):
    w = os.environ.get("HSFA_WORKSPACE")
    if not w:
        return None
    return os.path.join(w, *p)


def dossier_modules():
    d = os.environ.get("HSFA_MODULES") or _espace("anthology_extract", "decompressed")
    if not d:
        _erreur("set HSFA_MODULES (folder of roN_usa_prog68k.bin) or HSFA_WORKSPACE")
    return d


def chemin_module(mod):
    return mod if os.sep in mod or "/" in mod else os.path.join(dossier_modules(), "%s_usa_prog68k.bin" % mod)


def module(mod):
    """bytes of the decompressed module (name roN, or a path)"""
    with open(chemin_module(mod), "rb") as f:
        return f.read()


def construction(arg=None):
    """frozen build folder: argument, else HSFA_GRAFT_BUILD"""
    c = arg or os.environ.get("HSFA_GRAFT_BUILD")
    if not c:
        _erreur("give the frozen build folder (ro9aNN_fige) as argument or in HSFA_GRAFT_BUILD")
    if not os.path.isdir(c):
        _erreur("not a folder: %s" % c)
    return c


def chemin_f390():
    f = os.environ.get("HSFA_F390") or _espace("work", "cps2", "anims", "f390.bin")
    if not f:
        _erreur("set HSFA_F390 (arcade animation file 390) or HSFA_WORKSPACE")
    return f


def sortie(nom):
    """one of this review's outputs read back by a later tool (HSFA_REVIEW_OUT, default ./sorties)"""
    return os.path.join(os.environ.get("HSFA_REVIEW_OUT", "sorties"), nom)


def traces():
    """folder of Upper's read recordings (releves_<state>/greffe/traces)"""
    return os.path.join(REL, "greffe", "traces")


# short names used by some tools
SRC_HSFA = SRC
lit_module = module
f390 = chemin_f390
