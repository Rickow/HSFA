"""Exécute une manipulation image par image et relève l'état du joueur 1.
python manip.py "down:2 down,right:2 right:2 right,square:3 -:30"  (étape = boutons séparés par des virgules : n images)"""
import sys
from ppdbg import Dbg, adr
TOUS = ["up", "down", "left", "right", "square", "triangle", "cross", "circle", "ltrigger", "rtrigger"]
def jouer(d, seq, J1, rel=None):
    d.pause()
    def avance(): d.req("cpu.runUntilTime", attendre="cpu.stepping", relativeUs=16700)
    t = 0; out = []
    try:
        for et in seq.split():
            b, _, n = et.partition(":"); bs = set(b.split(",")) - {"-"}
            d.req("input.buttons.send", buttons={x: (x in bs) for x in TOUS})
            for _ in range(int(n or 1)):
                avance(); t += 1
                st = d.lire(J1 + 4, 4).hex()
                out.append("%3d %-14s état %s anim %04x %s" % (t, b, st, d.r32(J1 + 0x1C) & 0xFFFF, rel(d) if rel else ""))
        d.req("input.buttons.send", buttons={x: False for x in TOUS})
    finally: d.reprise()
    return out
if __name__ == "__main__":
    d = Dbg(45678); J1 = d.r32(adr(0x213F88))
    print("\n".join(jouer(d, sys.argv[1], J1)))
