"""Joue une manipulation image par image avec points d'arrêt sur des fonctions PSP (relevé a0-a3, ra) — 2026-10-07.
python super_bp.py "seq" 1dc32c,1f338"""
import sys
from ppdbg import Dbg, adr
from manip import TOUS
d = Dbg(45678)
seq = sys.argv[1]; bps = [int(x, 16) for x in sys.argv[2].split(",")]
# forçages : adresse:registre=valeur (ex. 1c37fc:v0=1)
FORCE = [(int(a, 16), r, int(v, 0)) for a, rv in (f.split(":") for f in sys.argv[3:]) for r, v in [rv.split("=")]]
bps += [x[0] for x in FORCE if x[0] not in bps]
for b in bps: d.req("cpu.breakpoint.add", address=adr(b), enabled=True)
R = lambda: {r["name"]: r for r in d.req("cpu.getAllRegs")["categories"][0]["registers"]} if False else d.req("cpu.getAllRegs")
def regs():
    c = d.req("cpu.getAllRegs")["categories"][0]
    return dict(zip(c["registerNames"], c["uintValues"]))
d.pause(); t = 0
try:
    for et in seq.split():
        b, _, n = et.partition(":"); bs = set(b.split(",")) - {"-"}
        d.req("input.buttons.send", buttons={x: (x in bs) for x in TOUS})
        for _ in range(int(n or 1)):
            t += 1; reste = 16700
            while True:
                st0 = d.req("cpu.status")["us"]
                d.req("cpu.runUntilTime", attendre="cpu.stepping", relativeUs=reste)
                st = d.req("cpu.status"); pc = st["pc"]
                ecoule = st["us"] - st0
                if any(pc == adr(x) for x in bps):
                    r = regs()
                    print("image %d : %#x a0=%#x a1=%#x a2=%#x v0=%#x ra=%#x" % (t, pc - 0x08804000, r["a0"], r["a1"], r["a2"], r["v0"], r["ra"] - 0x08804000))
                    for x in FORCE:
                        if pc == adr(x[0]): d.req("cpu.setReg", category=0, register=list(regs()).index(x[1]), value=x[2]); print("   forcé", x)
                    reste -= max(ecoule, 1)
                    if reste <= 0: break
                    continue
                break
    d.req("input.buttons.send", buttons={x: False for x in TOUS})
finally:
    for b in bps: d.req("cpu.breakpoint.remove", address=adr(b))
    d.reprise()
