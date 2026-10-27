"""Trajet automatique jusqu'au combat d'entraînement J1 = perso (rangée du bas : eagle, maki, yun, ingrid) contre Ken.
python allez.py ingrid   (PPSSPP lancé avec --debugger-run=45678 ; temps émulé, reproductible)"""
import sys, time
from ppdbg import Dbg
S = "~/.cache/sfa3max/ppsspp/captures/"
d = Dbg(45678)
d.pause()
def att(sec): d.req("cpu.runUntilTime", attendre="cpu.stepping", relativeUs=int(sec * 1e6))
def appui(b, n=1):
    for _ in range(n):
        d.req("input.buttons.send", buttons={b: True}); att(0.1)
        d.req("input.buttons.send", buttons={b: False}); att(0.35)
def ecran(nom): d.capture(S + nom, reprendre=False); print("capture", nom)
try:
    st = d.req("cpu.status"); print("temps émulé %.1f s" % (st["us"] / 1e6))
    if st["us"] < 20e6: att(20 - st["us"] / 1e6)
    ecran("a1_invite.png")
    appui("up"); appui("cross"); att(3)
    appui("start"); att(2); appui("start"); att(2)
    ecran("a2_menu.png")
    appui("down", 2); appui("cross"); att(3)
    ecran("a3_selection.png")
    # curseur J1 : depuis (0,1) -> rangée du bas : bas ×1 puis contrôle pas à pas (la grille a des trous)
    perso = sys.argv[1] if len(sys.argv) > 1 else "ingrid"
    appui("down", 5)
    cible = {"eagle": 2, "maki": 3, "yun": 5, "ingrid": 6}[perso]
    appui("right", cible - 1)
    ecran("a4_curseur.png")
finally:
    d.reprise()
