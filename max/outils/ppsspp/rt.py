"""Appuis en temps RÉEL (wall-clock) : python rt.py "start down:2 cross att3" capture.png"""
import sys, time
from ppdbg import Dbg
S = "~/.cache/sfa3max/ppsspp/captures/"
d = Dbg(45678)
for a in sys.argv[1].split():
    if a.startswith("att"): time.sleep(float(a[3:])); continue
    b, _, n = a.partition(":")
    for _ in range(int(n or 1)):
        d.req("input.buttons.send", buttons={b: True}); time.sleep(0.6)
        d.req("input.buttons.send", buttons={b: False}); time.sleep(1.2)
time.sleep(1)
print(d.capture(S + (sys.argv[2] if len(sys.argv) > 2 else "rt.png")))
