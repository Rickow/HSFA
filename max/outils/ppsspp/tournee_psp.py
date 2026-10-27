"""Partie Arcade PSP pilotée jusqu'à la fin (équivalent de tournee.lua d'HSFA) : vie du CPU ramenée à 1 (si > 1), vie de J1 au
maximum, bouton croix en rafale (coups + passage des écrans) ; capture toutes les PERIODE s dans DOSSIER.
python tournee_psp.py <dossier> [minutes] [période s]"""
import sys, os, time
from ppdbg import Dbg
D = sys.argv[1]; os.makedirs(D, exist_ok=True)
duree = float(sys.argv[2]) * 60 if len(sys.argv) > 2 else 900; periode = float(sys.argv[3]) if len(sys.argv) > 3 else 4
d = Dbg(45678); J1 = 0x092E3EA0; J2 = J1 + 0x498
t0 = time.time(); k = 0; der = 0; appui = False
while time.time() - t0 < duree:
    try:
        v = d.r16(J2 + 0x70)
        if 1 < v < 0x8000: d.req("memory.write_u16", address=J2 + 0x70, value=1)   # jamais de résurrection après K.O.
        d.req("memory.write_u16", address=J1 + 0x70, value=0x90)
    except Exception as e: print("écriture", e)
    appui = not appui
    d.req("input.buttons.send", buttons={"cross": appui, "square": not appui})
    if time.time() - der > periode:
        der = time.time(); d.capture(os.path.join(D, "%05d.png" % k)); k += 1
    time.sleep(0.12)
d.req("input.buttons.send", buttons={"cross": False, "square": False})
print("fin du pilotage,", k, "captures")
