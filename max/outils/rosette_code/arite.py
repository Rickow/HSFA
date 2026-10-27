"""Arité des fonctions moteur PSP : registres a1-a3 écrits juste avant le jal (3 instructions + créneau), sur tous
les modules de persos ; arité = dernier registre écrit dans >= 60 % des sites."""
import sys, json, collections
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max")); sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "src", "hsfa"))
from relocs import img
from mips import decode
import modules
def ecrit(i):
    if i.op == 0: return i.rd if i.m not in ("jr", "jalr", "mult", "multu", "div", "divu") else None
    if i.m in ("sw", "sh", "sb", "beq", "bne", "beql", "bnel", "j", "jal", "regimm", "bgez", "bltz", "blez", "bgtz"): return None
    return i.rt
B = modules.module_bounds(); LO, HI = min(a for a, _ in B.values()), max(e for _, e in B.values())
ins = list(decode(img, LO, HI))
n, w = collections.Counter(), collections.defaultdict(collections.Counter)
for k, i in enumerate(ins):
    if i.m != "jal" or LO <= i.tgt < HI: continue
    n[i.tgt] += 1
    regs = {ecrit(x) for x in ins[max(0, k - 3):k + 2]}
    for r in (5, 6, 7):
        if r in regs: w[i.tgt][r] += 1
ar = {}
for t, c in n.items():
    a = 0
    for r in (5, 6, 7):
        if w[t][r] >= 0.6 * c: a = r - 4
    ar["%x" % t] = a
json.dump(ar, open("arite.json", "w"))
print(len(ar), "fonctions ; arité", collections.Counter(ar.values()))
print({k: ar[k] for k in ("5d6ec", "5d63c", "68a2c", "5d848", "330d8", "79144")})
