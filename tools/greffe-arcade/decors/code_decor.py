#!/usr/bin/env python3
"""code_decor.py : code d'Upper atteint depuis ses tables et routines PAR DECOR (graphe_ro5.pkl, cle 'succ', profondeur
bornee, arret sur les routines atteintes aussi par > 40 appelants = bibliotheque commune), classe par couverture K=12
dans Hyper (couv_k.pkl) : absent < 50 %, modifie 50-90 %, present >= 90 %. -> code_decor.tsv"""
import os, sys, pickle, struct, collections
os.environ["GRAIN"] = "routine"
sys.path.insert(0, "<workspace>/work/carto_ro9")
import commun as K
E = "<workspace>/work/etude_upper_hyper"
G = pickle.load(open(os.path.join(E, "graphe_ro5.pkl"), "rb")); cov = pickle.load(open(os.path.join(E, "couv_k.pkl"), "rb"))
succ = G['succ']; F = dict(G['funcs'])
pred = collections.Counter(t for s in succ.values() for t in s)
B5 = open("<workspace>/anthology_extract/decompressed/ro5_usa_prog68k.bin", "rb").read(); BASE = 0x1F0000
def cibles(t, n=40): return [struct.unpack_from('<I', B5, t - BASE + 4 * k)[0] - BASE for k in range(n)]
GROUPES = {
  "gestionnaires de plans (T_614850/T_6149B0/T_614AD0, init+course)": cibles(0x614850) + cibles(0x6149B0) + cibles(0x614AD0),
  "ordre des plans (T_6147B0)": cibles(0x6147B0),
  "effet par decor (T_6135A0, 0x13BB10)": cibles(0x6135A0) + [0x13BB10],
  "objets de decor (0x4C1B0, T_950CE0) + objet 0x105C70 + anim. 0xFDC10": [0x4C1B0, 0x105C70, 0xFDC10],
  "positions / masques / animations par decor (0x196F50, 0x198A00, 0x199530, 0x199DA0, 0x371920)": [0x196F50, 0x198A00, 0x199530, 0x199DA0, 0x371920],
  "palettes de sprites de decor (0x4AA60, 0x4B930)": [0x4AA60, 0x4B930],
  "musique par decor (0x139AD0)": [0x139AD0],
}
H = os.path.dirname(os.path.abspath(__file__))
out = open(os.path.join(H, "code_decor.tsv"), "w"); out.write("groupe\troutine_ro5\ttaille\tcouv_k\tetat\n")
vus_glob = set()
for nom, racines in GROUPES.items():
    vus = set(); pile = [(r, 0) for r in racines if r in F or K.func_of('ro5', r)]
    pile = [(K.func_of('ro5', r)[0], 0) for r, _ in pile]
    while pile:
        a, d = pile.pop()
        if a in vus: continue
        vus.add(a)
        if d >= 3: continue
        for t in succ.get(a, ()):
            if pred[t] <= 40 and t not in vus: pile.append((t, d + 1))
    tot = collections.Counter()
    for a in sorted(vus):
        b = F.get(a) or K.func_of('ro5', a)[1]; sz = b - a; c = cov.get(a, 1.0)
        e = "absent" if c < 0.5 else ("modifie" if c < 0.9 else "present")
        tot[e] += sz
        out.write("%s\t%x\t%d\t%.2f\t%s\n" % (nom, a, sz, c, e))
    vus_glob |= vus
    print("%-95s %3d routines ; absent %5.1f Ko, modifie %5.1f Ko, present %5.1f Ko" % (nom, len(vus), tot['absent']/1024, tot['modifie']/1024, tot['present']/1024))
out.close()
