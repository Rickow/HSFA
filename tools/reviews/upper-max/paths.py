#!/usr/bin/env python3
"""paths.py -- common paths of the Upper MAX review tools (tools/reviews/upper-max/). Imported by the other scripts;
nothing to run.

The tools are static and read-only. They read an Upper MAX build's bench folder ("banc": max_agrandies.txt,
ext_e80000.bin, ext_b80000.bin, max_journal.txt, carte_image.txt, roms_ro5/), Upper's decompressed module (ro5), the
decrypted PSP EBOOT of SFA3 MAX (BOOT.BIN, EU) and the Upper MAX integration code kept in the repository
(tools/integration-max/upper_max/integration_2b31/ag/). Nothing is written except to standard output (essai_nr.py
works in a temporary folder).

Environment variables:
  HSFA_CACHE        cache folder of a hsfa_build.py output (<output>/cache): holds anthology_extract/decompressed/,
                    psp/BOOT.BIN and max_regen/; used for the defaults below
  HSFA_MODULES      folder holding the decompressed modules roN_usa_prog68k.bin
                    (default: $HSFA_CACHE/anthology_extract/decompressed)
  HSFA_PSP_BOOT     decrypted PSP EBOOT of SFA3 MAX (default: $HSFA_CACHE/psp/BOOT.BIN); virtual address = offset - 0x74
"""
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.normpath(os.path.join(ICI, "..", "..", ".."))
AG = os.path.join(DEPOT, "tools", "integration-max", "upper_max", "integration_2b31", "ag")
MAX_OUTILS = os.path.join(DEPOT, "tools", "max")
RB = 0x1F0000                 # PS2 execution address of file offset 0 of a module


def _erreur(msg):
    sys.exit("paths.py: " + msg)


def _cache(*p):
    c = os.environ.get("HSFA_CACHE")
    return os.path.join(c, *p) if c else None


def chemin_module(mod="ro5"):
    if os.sep in mod or "/" in mod:
        return mod
    d = os.environ.get("HSFA_MODULES") or _cache("anthology_extract", "decompressed")
    if not d:
        _erreur("set HSFA_MODULES (folder of roN_usa_prog68k.bin) or HSFA_CACHE")
    return os.path.join(d, "%s_usa_prog68k.bin" % mod)


def module(mod="ro5"):
    with open(chemin_module(mod), "rb") as f:
        return f.read()


def chemin_boot():
    b = os.environ.get("HSFA_PSP_BOOT") or _cache("psp", "BOOT.BIN")
    if not b:
        _erreur("set HSFA_PSP_BOOT (decrypted SFA3 MAX EBOOT) or HSFA_CACHE")
    return b


def boot(chemin=None):
    """EBOOT bytes from the virtual address 0 (file offset 0x74)"""
    with open(chemin or chemin_boot(), "rb") as f:
        return f.read()[0x74:]


def banc(arg):
    """bench folder of an Upper MAX build (argument)"""
    if not arg or not os.path.isdir(arg):
        _erreur("give the bench folder of an Upper MAX build (max_agrandies.txt, ext_e80000.bin ...)")
    return arg


def lit_texte(p):
    with open(p, encoding="utf-8") as f:
        return f.read()
