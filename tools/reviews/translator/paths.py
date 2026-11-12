#!/usr/bin/env python3
"""paths.py -- common paths of the translator review tools (tools/reviews/translator/). Imported by the other scripts;
nothing to run.

The tools are static and read-only: they read a decompressed PS2 module (MIPS), the translator's map of a build
(carte_image.txt: image address, MIPS file offset, emitted 68K text) and, for a few of them, other files of that
build. Nothing is written except to standard output.

Environment variables:
  HSFA_MODULES      folder holding the decompressed modules roN_usa_prog68k.bin
                    (default: $HSFA_WORKSPACE/anthology_extract/decompressed)
  HSFA_WORKSPACE    the workspace (<workspace>), used only for the default above
  HSFA_BUILD        folder of a translator build, with "%s" standing for the module, e.g.
                    <workspace>/work/v161/constr/%s_a6  (carte_image.txt, etapeB_reloge.txt, etapeC_ram.txt, roms_*/)
  CARTE             explicit path of a carte_image.txt (overrides HSFA_BUILD for the map only; one module at a time)
  IMG               explicit folder of the translated program ROM files (sz3ud.03c ...; overrides HSFA_BUILD, img.py)
  HSFA_ARCADE_PROG  decrypted arcade program of sfa3ud, one file, 68K byte order (arc.py)
The translator's own modules (mips.py, extra_regs.py, hooks_fork_roN.json) are taken from the repository's src/hsfa.
"""
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(ICI, "..", "..", "..", "src", "hsfa"))


def _erreur(msg):
    sys.exit("paths.py: " + msg)


def dossier_modules():
    d = os.environ.get("HSFA_MODULES")
    if d:
        return d
    w = os.environ.get("HSFA_WORKSPACE")
    if not w:
        _erreur("set HSFA_MODULES (folder of roN_usa_prog68k.bin) or HSFA_WORKSPACE")
    return os.path.join(w, "anthology_extract", "decompressed")


def chemin_module(mod):
    return os.path.join(dossier_modules(), "%s_usa_prog68k.bin" % mod)


def module(mod):
    """bytes of the decompressed module roN_usa_prog68k.bin"""
    with open(chemin_module(mod), "rb") as f:
        return f.read()


def construction(mod):
    """folder of the translator build for this module (HSFA_BUILD, "%s" = module)"""
    g = os.environ.get("HSFA_BUILD")
    if not g:
        _erreur("set HSFA_BUILD to a translator build folder, '%s' = module (e.g. <workspace>/work/v161/constr/%s_a6)")
    return g % mod if "%s" in g else g


def fichier_construction(mod, nom):
    return os.path.join(construction(mod), nom)


def chemin_carte(mod):
    """carte_image.txt of the build (CARTE overrides)"""
    return os.environ.get("CARTE") or fichier_construction(mod, "carte_image.txt")
