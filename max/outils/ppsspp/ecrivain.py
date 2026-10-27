"""Qui écrit la globale ? python ecrivain.py <va hex> <action : bouton | rien> [secondes]
Pose un point d'arrêt mémoire (changement) sur adr(va), déclenche l'action, relève PC/RA à chaque arrêt (max 6)."""
import sys, time, json
from ppdbg import Dbg, adr, CODE
va = int(sys.argv[1], 16); act = sys.argv[2]; dur = float(sys.argv[3]) if len(sys.argv) > 3 else 3
d = Dbg(45678); A = adr(va)
d.req("memory.breakpoint.add", address=A, size=1, change=True, enabled=True)
try:
    if act != "rien": d.appui(act, 0.1)
    t0 = time.time(); n = 0
    d.k.settimeout(1.0)
    while time.time() - t0 < dur and n < 6:
        try: op, m = d._trame()
        except Exception: continue
        m = json.loads(m)
        if m.get("event") == "cpu.stepping":
            d.k.settimeout(30)
            pc = m.get("pc"); ra = d.req("cpu.getReg", name="ra")["uintValue"]
            val = d.r8(A)
            print("arrêt : pc %08x (EBOOT %x)  ra EBOOT %x  valeur -> %02x" % (pc, pc - CODE, ra - CODE, val)); n += 1
            d.reprise(); d.k.settimeout(1.0)
finally:
    d.k.settimeout(30)
    d.req("memory.breakpoint.remove", address=A, size=1)
    try: d.reprise()
    except Exception: pass
