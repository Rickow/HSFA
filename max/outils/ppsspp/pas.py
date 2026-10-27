"""Pas à pas en temps ÉMULÉ (reproductible) : python pas.py "att:5 start cross:2 down:3 ..." capture.png
att:s = attendre s secondes émulées ; bouton[:n] = n appuis (0,1 s appuyé, 0,35 s relâché)."""
import sys
from ppdbg import Dbg
S = "~/.cache/sfa3max/ppsspp/captures/"
d = Dbg(45678); d.pause()
def att(sec): d.req("cpu.runUntilTime", attendre="cpu.stepping", relativeUs=int(sec * 1e6))
try:
    for a in sys.argv[1].split():
        b, _, n = a.partition(":")
        if b == "att": att(float(n)); continue
        for _ in range(int(n or 1)):
            d.req("input.buttons.send", buttons={b: True}); att(0.1)
            d.req("input.buttons.send", buttons={b: False}); att(0.35)
    f = sys.argv[2] if len(sys.argv) > 2 else "pas.png"
    d.capture(S + f, reprendre=False); print("temps %.1f s ->" % (d.req("cpu.status")["us"] / 1e6), f)
finally: d.reprise()
