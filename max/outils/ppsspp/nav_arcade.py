"""Du démarrage (carte mémoire neuve) jusqu'au début d'une partie Arcade avec le perso donné (n° hexa, ex. 26).
Appuis en temps réel ; perso imposé en écrivant J1 + 0x152 sur l'écran de sélection (comme tournee.lua, +$102)."""
import sys, time
from ppdbg import Dbg
perso = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x26
S = "~/.cache/sfa3max/ppsspp/captures/"
d = Dbg(45678); J1 = 0x092E3EA0
def appui(b, n=1, avant=0.5, apres=1.3):
    for _ in range(n):
        d.req("input.buttons.send", buttons={b: True}); time.sleep(avant)
        d.req("input.buttons.send", buttons={b: False}); time.sleep(apres)
time.sleep(8); appui("up"); appui("cross"); time.sleep(6)
for k in range(10):                       # titre -> menu des modes -> ARCADE (1er élément) -> sélection
    appui("start", apres=1.5)
    d.capture(S + "nav_%d.png" % k)
for _ in range(3):
    d.req("memory.write_u8", address=J1 + 0x152, value=perso); time.sleep(0.5)
appui("cross"); d.req("memory.write_u8", address=J1 + 0x152, value=perso)
appui("cross"); appui("cross", apres=3)
print("perso J1 = %#x" % d.r8(J1 + 0x152)); d.capture(S + "nav_fin.png")
