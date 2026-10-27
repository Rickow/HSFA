"""Manipulation puis arrêt au PREMIER changement de l'octet d'état $6 du joueur 1 (interprète requis) : pile d'appels."""
import json, sys
from ppdbg import Dbg, adr, CODE
from manip import TOUS
d = Dbg(45678); J1 = d.r32(adr(0x213F88)); off = int(sys.argv[1], 16) if len(sys.argv) > 1 else 6
d.pause()
try:
    for b, n in [("down", 2), ("down,right", 2), ("right", 2)]:
        d.req("input.buttons.send", buttons={x: (x in b.split(",")) for x in TOUS})
        for _ in range(n): d.req("cpu.runUntilTime", attendre="cpu.stepping", relativeUs=16700)
    print("avant : état", d.lire(J1 + 4, 4).hex())
    d.req("memory.breakpoint.add", address=J1 + 4, size=4, write=True, enabled=True)
    d.req("input.buttons.send", buttons={x: (x in ("right", "square")) for x in TOUS})
    for n in range(12):
        d.ticket += 1; d._envoi(json.dumps({"event": "cpu.resume", "ticket": d.ticket}))
        while True:
            op, m = d._trame(); m = json.loads(m)
            if m.get("event") == "cpu.stepping": break
        pc = d.req("cpu.status")["pc"]; st = d.lire(J1 + 4, 4)
        print("arrêt %d : pc EBOOT %x ; état %s" % (n, pc - CODE, st.hex()))
        for f in d.req("hle.backtrace").get("frames", [])[:9]:
            print("   fonction %x  (retour en %x)" % (f.get("entry", 0) - CODE, f.get("pc", 0) - CODE))
        if st[2] == 7: break
finally:
    try: d.req("memory.breakpoint.remove", address=J1 + 4, size=4)
    except Exception as e: print(e)
    d.req("input.buttons.send", buttons={x: False for x in TOUS})
    try: d.reprise()
    except Exception: pass
