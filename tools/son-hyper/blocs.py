#!<workspace>/venv/bin/python
"""Blocs de voix par perso : SFA3 (0x300 + base*0x20 + n, cote 1, sans les voix MAX), SFA2 (blocs delimites par la
paire finale « v13 seule + sequence v11,12 »), SFA1 (0x160-0x1F3, a segmenter)."""
import json, os
D = "<workspace>/work/agent_son_hyper_rom"
def cat(jeu): return json.load(open(os.path.join(D, "catalogue", jeu + ".json")))
MAX = set(int(a["cmd"], 16) for a in json.load(open("<workspace>/work/agent_voix_max/roms_voix/attribution.json")))
def sfa3():
    C = cat("sfa3")["commandes"]; out = {}
    for b in range(0x20):
        L = []
        for n in range(32):
            c = 0x300 + b * 0x20 + n
            if c in MAX: continue
            v = C.get("%04x" % c)
            if v and v["echantillons"]: L.append((c, v["echantillons"][0], v["genre"]))
        out[b] = L
    return out
def sfa2(jeu="sfa2"):
    C = cat(jeu)["commandes"]; blocs, cur = [], []
    for lo, hi in ((0x180, 0x1ff), (0x300, 0x37f)):
        for c in range(lo, hi + 1):
            v = C.get("%04x" % c)
            if not v or not v["echantillons"]: continue
            cur.append((c, v["echantillons"][0], v["genre"]))
            if v["genre"] == "sequence" and 11 in v["voies"] and 12 in v["voies"]:
                blocs.append(cur); cur = []
        if cur: blocs.append(cur); cur = []
    return blocs
def sfa1():
    C = cat("sfa1")["commandes"]; L = []
    for c in range(0x160, 0x1f4):
        v = C.get("%04x" % c)
        if v and v["echantillons"]: L.append((c, v["echantillons"][0], v["genre"]))
    return L
if __name__ == "__main__":
    b = sfa2(); print(len(b), [("%04x-%04x" % (x[0][0], x[-1][0]), len(x)) for x in b])
    s = sfa3(); print({"%02x" % k: len(v) for k, v in s.items()})
