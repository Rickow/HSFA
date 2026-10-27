#!<workspace>/venv/bin/python
"""Blocs de voix SOURCES par perso de base (id SFA3) et par jeu, deduits des balayages et de l'appariement DTW
(assigne.py) : SFA2 = 17 blocs dans l'ordre des ids 0x00-0x10 ; SFA1 = segments de 0x160-0x1F3 (fin de bloc =
sequence voix + bruitage), + cri par perso 0x1E7 + id. Gen (0x11) n'a pas de voix dans SFA2."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blocs
SFA1 = {0x00: (0x160, 0x168), 0x01: (0x169, 0x173), 0x07: (0x174, 0x17f), 0x03: (0x180, 0x188), 0x0b: (0x189, 0x193),
        0x04: (0x194, 0x1a1), 0x09: (0x1a2, 0x1ac), 0x05: (0x1ad, 0x1b7), 0x06: (0x1b8, 0x1c0), 0x0a: (0x1c3, 0x1cb),
        0x02: (0x1cc, 0x1d2), 0x08: (0x1d3, 0x1de), 0x0c: (0x1e5, 0x1e6)}
ORDRE1 = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c]   # cris 0x1E7 + rang
def source(jeu, base):
    """liste [(commande, echantillon, genre)] du perso de base dans le jeu ('sfa1' | 'sfa2')"""
    if jeu == "sfa2":
        B = blocs.sfa2("sfa2")
        return B[base] if base < len(B) else []
    if base not in SFA1: return []
    C = blocs.cat("sfa1")["commandes"]
    a, b = SFA1[base]
    cs = list(range(a, b + 1)) + [0x1e7 + ORDRE1.index(base)]
    out, vus = [], set()
    for c in cs:
        v = C.get("%04x" % c)
        if v and v["echantillons"] and v["echantillons"][0] not in vus:
            vus.add(v["echantillons"][0]); out.append((c, v["echantillons"][0], v["genre"]))
    return out
