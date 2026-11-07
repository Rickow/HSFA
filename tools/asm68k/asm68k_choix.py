# SPDX-License-Identifier: MIT
"""asm68k_choix.py -- choix de l'assembleur 68000 de la construction (Upper MAX).

  HSFA_ASM absent ou « hsfa » : hsfa_asm68k (Python, MIT, embarqué, même sortie que vasm à l'octet) ;
  HSFA_ASM=vasm               : vasmm68k_mot (chemin donné par l'appelant, ou HSFA_VASM, ou le PATH) ;
  HSFA_ASM=compare            : les deux ; échec si binaire ou liste diffèrent (contrôle de maintenance).

assemble(args, vasm=None) prend les arguments de la ligne de commande de vasm (sans le nom du programme) et rend un
objet (returncode, stdout, stderr) comme subprocess.run(..., capture_output=True, text=True)."""
import os
import shutil
import subprocess
import sys
import tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import hsfa_asm68k  # noqa: E402


def _vasm(vasm):
    v = vasm if vasm and os.path.exists(vasm) else (os.environ.get("HSFA_VASM") or shutil.which("vasmm68k_mot"))
    if not v or not os.path.exists(v):
        raise SystemExit("HSFA_ASM=%s : vasm (vasmm68k_mot) introuvable ; HSFA_VASM=CHEMIN ou --vasm"
                         % os.environ.get("HSFA_ASM"))
    return v


def _sortie(args, opt):
    return args[args.index(opt) + 1] if opt in args else None


def assemble(args, vasm=None):
    mode = os.environ.get("HSFA_ASM", "hsfa")
    if mode == "vasm":
        return subprocess.run([_vasm(vasm)] + list(args), capture_output=True, text=True, errors="replace")
    r = hsfa_asm68k.lance(args)
    if mode != "compare" or r.returncode:
        return r
    # contrôle : vasm sur la même source, sorties dans un dossier temporaire, comparaison octet à octet
    d = tempfile.mkdtemp(prefix="asm68k_compare_")
    try:
        a2 = list(args)
        bo, lo = _sortie(args, "-o"), _sortie(args, "-L")
        a2[a2.index("-o") + 1] = os.path.join(d, "v.bin")
        if lo:
            a2[a2.index("-L") + 1] = os.path.join(d, "v.lst")
        rv = subprocess.run([_vasm(vasm)] + a2, capture_output=True, text=True, errors="replace")
        ecarts = []
        if rv.returncode:
            ecarts.append("vasm a échoué")
        else:
            if open(bo, "rb").read() != open(os.path.join(d, "v.bin"), "rb").read():
                ecarts.append("binaire")
            if lo and open(lo, "rb").read() != open(os.path.join(d, "v.lst"), "rb").read():
                ecarts.append("liste")
        if ecarts:
            r.returncode = 1
            r.stdout += "\nerror 9999 : HSFA_ASM=compare : hsfa_asm68k et vasm diffèrent (%s) sur %s\n" % (
                ", ".join(ecarts), args[-1])
        else:
            r.stdout += "HSFA_ASM=compare : hsfa_asm68k = vasm (binaire%s) pour %s\n" % (" et liste" if lo else "",
                                                                                     args[-1])
        return r
    finally:
        shutil.rmtree(d, ignore_errors=True)
