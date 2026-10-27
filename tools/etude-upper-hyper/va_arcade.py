#!/usr/bin/env python3
"""Correspondance routine d'Upper (va MIPS) -> adresses arcade SFA3 alignees (agent_upper_ecarts/realign.pkl) :
va_arcade.pkl {routine_ro5: (n_alignees, arcade_min, arcade_mediane, arcade_max)}"""
import os, pickle, bisect, collections
import atteint as AT
OUT = os.path.dirname(os.path.abspath(__file__))
res, table, T, carte = pickle.load(open("<workspace>/work/agent_upper_ecarts/realign.pkl", "rb"))
starts = [a for a, _ in AT.G('ro5')['funcs']]
par = collections.defaultdict(list)
for img, (va, txt) in carte.items():
    if img in res:
        k = bisect.bisect_right(starts, va) - 1
        if k >= 0: par[starts[k]].append(res[img][0])
out = {}
for f, L in par.items():
    L.sort(); out[f] = (len(L), L[0], L[len(L) // 2], L[-1])
pickle.dump(out, open(os.path.join(OUT, "va_arcade.pkl"), "wb"))
print("routines d'Upper avec au moins une instruction alignee sur l'arcade : %d" % len(out))
