"""Navigation : python nav.py bouton[:n] ... -> appuie (n fois), attend, capture ecran_N.png"""
import sys, time
from ppdbg import Dbg
S = "~/.cache/sfa3max/ppsspp/captures/"
d = Dbg(45678)
for a in sys.argv[1:-1] if len(sys.argv) > 2 else sys.argv[1:]:
    if a.startswith("att"): time.sleep(float(a[3:])); continue
    b, _, n = a.partition(":")
    for _ in range(int(n or 1)):
        d.appui(b, 0.1); time.sleep(0.4)
time.sleep(0.6)
print(d.capture(S + (sys.argv[-1] if len(sys.argv) > 2 and sys.argv[-1].endswith(".png") else "ecran.png")))
