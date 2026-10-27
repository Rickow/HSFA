"""Décompilation Ghidra (extension Allegrex) de fonctions de l'EBOOT SFA3 MAX — projet $GHIDRA_PROJET (défaut ghidra_psp) (base 0 :
adresses = VA de nos outils ; adresse PSP réelle = 0x08804000 + VA). Usage : python ghidra_decomp.py 1d4c48 [...]
Environnement : JAVA_HOME=$HSFA_TOOLS/jdk-21…, GHIDRA_INSTALL_DIR=$HSFA_TOOLS/ghidra_12.1.3_PUBLIC, python du venv HSFA."""
import os, sys
os.environ.setdefault("JAVA_HOME", __import__("os").path.join(__import__("os").environ.get("HSFA_TOOLS", "tools"), "jdk-21.0.12.1+1"))
os.environ.setdefault("GHIDRA_INSTALL_DIR", __import__("os").path.join(__import__("os").environ.get("HSFA_TOOLS", "tools"), "ghidra_12.1.3_PUBLIC"))
import pyghidra
pyghidra.start()
from ghidra.base.project import GhidraProject
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
P = os.environ.get("GHIDRA_PROJET", "ghidra_psp")   # dossier du projet Ghidra (import : voir README)
proj = GhidraProject.openProject(P, "SFA3MAX_PSP", True)
prog = proj.openProgram("/", "ULES00235_EBOOT.elf", True)
dec = DecompInterface(); dec.openProgram(prog)
fm = prog.getFunctionManager(); af = prog.getAddressFactory()
rm = prog.getReferenceManager()
args = sys.argv[1:]
if args and args[0] == "--xrefs":                 # références vers des adresses -> fonctions qui les emploient
    for x in args[1:]:
        a = af.getDefaultAddressSpace().getAddress(int(x, 16))
        fs = set()
        for r in rm.getReferencesTo(a):
            f = fm.getFunctionContaining(r.getFromAddress())
            fs.add((str(r.getFromAddress()), f.getName() if f else "?"))
        print("%s : %s" % (x, sorted(fs)))
    args = []
if args and args[0] == "--plage":                 # décompile toutes les fonctions d'une plage, filtre par motif regex
    import re
    lo, hi, motif = int(args[1], 16), int(args[2], 16), re.compile(args[3])
    sp = af.getDefaultAddressSpace()
    for f in fm.getFunctions(sp.getAddress(lo), True):
        if f.getEntryPoint().getOffset() >= hi: break
        r = dec.decompileFunction(f, 60, ConsoleTaskMonitor())
        if not r.decompileCompleted(): continue
        c = r.getDecompiledFunction().getC()
        lignes = [l.strip() for l in c.splitlines() if motif.search(l)]
        if lignes: print("// %s : %s" % (f.getName(), " | ".join(lignes[:4])))
    args = []
for x in args:
    a = af.getDefaultAddressSpace().getAddress(int(x, 16))
    f = fm.getFunctionAt(a) or fm.getFunctionContaining(a)
    if f is None: print("// %s : pas de fonction" % x); continue
    r = dec.decompileFunction(f, 60, ConsoleTaskMonitor())
    print("// ---- %s (%s)" % (f.getName(), f.getEntryPoint())); print(r.getDecompiledFunction().getC() if r.decompileCompleted() else r.getErrorMessage())
proj.close()
