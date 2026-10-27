#!<workspace>/venv/bin/python
"""Assignation des blocs de voix d'un jeu (SFA2 / ro6 / SFA1) aux persos SFA3 par DTW des MFCC et par correlation
de forme d'onde (meme echantillon reutilise)."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blocs, audio
from empreintes import empreinte, dtw
NOMS = {0:"Ryu",1:"Ken",2:"Akuma",3:"Charlie",4:"Chun-Li",5:"Adon",6:"Sodom",7:"Guy",8:"Birdie",9:"Rose",0xa:"Bison",
        0xb:"Sagat",0xc:"Dan",0xd:"Sakura",0xe:"Rolento",0xf:"Dhalsim",0x10:"Zangief",0x11:"Gen",0x12:"(12)",0x13:"Gen2",
        0x14:"(14)",0x15:"Balrog",0x16:"Cammy",0x17:"EvilRyu",0x18:"Honda",0x19:"Blanka",0x1a:"Mika",0x1b:"Cody",0x1c:"Vega",
        0x1d:"Karin",0x1e:"Juli",0x1f:"Juni"}
def matrice(jeu, B):
    S3 = blocs.sfa3()
    persos = [b for b in S3 if S3[b] and b not in (0x12, 0x14)]
    M = np.zeros((len(B), len(persos)))
    for i, bl in enumerate(B):
        for j, b in enumerate(persos):
            ds = []
            for c, e, g in bl:
                A = empreinte(jeu, e)["m"]
                ds.append(min(dtw(A, empreinte("sfa3", e3)["m"]) for _, e3, _ in S3[b]))
            M[i, j] = np.mean(sorted(ds)[:max(3, len(ds) // 2)])
    return M, persos
if __name__ == "__main__":
    jeu = sys.argv[1]
    B = blocs.sfa2(jeu)
    M, P = matrice(jeu, B)
    np.save(os.path.join(blocs.D, "catalogue", "matrice_%s.npy" % jeu), M)
    for i, bl in enumerate(B):
        o = np.argsort(M[i])
        print("%04x-%04x" % (bl[0][0], bl[-1][0]), " ".join("%s:%.3f" % (NOMS[P[k]], M[i, k]) for k in o[:4]))
