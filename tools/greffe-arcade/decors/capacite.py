#!/usr/bin/env python3
"""capacite.py : tuiles (contenus distincts, blocs communs compris) utilisees par l'ensemble des decors d'Upper
absents d'Hyper ($00-$4C), par plan, et blocs de bibliotheque cites -> place a prevoir dans les plans d'Hyper."""
import os, sys
sys.argv = [sys.argv[0]]
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import importlib.util, io, contextlib
spec = importlib.util.spec_from_file_location("td", os.path.join(H, "tuiles_decor.py"))
src = open(os.path.join(H, "tuiles_decor.py")).read().split("out = open(")[0]   # definitions seulement
ns = {"__file__": os.path.join(H, "tuiles_decor.py")}
with contextlib.redirect_stdout(io.StringIO()): exec(compile(src, "td", "exec"), ns)
codes, get, S9 = ns["codes"], ns["get"], ns["S9"]
tot = {1: set(), 2: set(), 3: set()}; cont = {1: set(), 2: set(), 3: set()}; blocs = {1: set(), 2: set(), 3: set()}
for d in range(0, 0x4E, 2):
    t, C, bl = codes("ro5", d)
    for L in (1, 2, 3):
        tot[L] |= C[L]; blocs[L] |= bl[L]
        for c in C[L]:
            x = get("ro5", L, c)
            if x: cont[L].add(x)
for L in (1, 2, 3):
    neuf = cont[L] - S9[L]
    print("scroll%d : codes locaux %d (max %x), contenus distincts %d, absents d'Hyper %d ; blocs cites %d (max %d)" %
          (L, len(tot[L]), max(tot[L]), len(cont[L]), len(neuf), len(blocs[L]), max(blocs[L])))
