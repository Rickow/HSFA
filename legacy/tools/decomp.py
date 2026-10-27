#!/usr/bin/env python3
"""
decomp.py — Décompile des fonctions R5900 (PS2 EE) d'un dump mémoire brut,
via pyghidra + extension ghidra-emotionengine-reloaded. Version Linux.

Prérequis (via `source <workspace>/env.sh`) :
  - GHIDRA_INSTALL_DIR pointant sur ghidra_12.1.3_PUBLIC (avec l'extension EE)
  - venv actif (pyghidra installé)

Le dump 32 Mo EST la RAM EE : une adresse virtuelle 0xXXXXXX = offset 0xXXXXXX
(base image 0), donc on passe les VA directement.

Usage :
  python decomp.py <dump.bin> <va1> [va2 ...]
  python decomp.py ~/CLAUDE\\ CODE/hyper_re/eeMemory_versus.bin 0x2865f0
"""
import os, sys, pyghidra

pyghidra.start()
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
from ghidra.app.cmd.function import CreateFunctionCmd
from ghidra.app.cmd.disassemble import DisassembleCommand

PROJ = os.environ.get("HSFA", "<workspace>") + "/ghidra_projects"


def run(dump, vas, maxlen=8000):
    os.makedirs(PROJ, exist_ok=True)
    pname = "d_" + os.path.splitext(os.path.basename(dump))[0]
    with pyghidra.open_program(dump, project_location=PROJ, project_name=pname,
                               analyze=False, language="r5900:LE:32:default",
                               compiler="default") as flat:
        program = flat.getCurrentProgram()
        fm = program.getFunctionManager()
        af = program.getAddressFactory().getDefaultAddressSpace()
        decomp = DecompInterface(); decomp.openProgram(program)
        monitor = ConsoleTaskMonitor()
        for va in vas:
            addr = af.getAddress(va)
            DisassembleCommand(addr, None, True).applyTo(program, monitor)
            fn = fm.getFunctionContaining(addr)
            if fn is None:
                CreateFunctionCmd(addr).applyTo(program, monitor)
                fn = fm.getFunctionContaining(addr)
            if fn is None:
                print("no fn @ 0x%x" % va); continue
            res = decomp.decompileFunction(fn, 150, monitor)
            df = res.getDecompiledFunction()
            called = sorted("0x%x" % f.getEntryPoint().getOffset()
                            for f in fn.getCalledFunctions(monitor))
            print("\n===== FUN_%x  appelle=%s =====" %
                  (fn.getEntryPoint().getOffset(), called))
            print((df.getC() if df else "(fail)")[:maxlen])


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    dump = sys.argv[1]
    vas = [int(a, 16) for a in sys.argv[2:]]
    run(dump, vas)
