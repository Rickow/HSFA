#!/usr/bin/env python3
"""sites_a5.py : acces A5+d (d = $100, $172, $174, $C178, $DC...) dans ro5 et ro9, par routine (GRAIN=routine),
avec le partenaire ro9 de chaque routine ro5 (inverse_ro5.pkl) -> sites_a5.tsv"""
import os, sys, pickle, collections
os.environ.setdefault("GRAIN", "routine")
sys.path.insert(0, "<workspace>/work/carto_ro9")
import commun as C, vars_a5 as V
D = [int(x, 16) for x in (sys.argv[1:] or "100 172 174 c178 dc 110".split())]
inv = pickle.load(open("<workspace>/work/etude_upper_hyper/inverse_ro5.pkl", "rb"))
cov = pickle.load(open("<workspace>/work/etude_upper_hyper/couv_k.pkl", "rb"))
out = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sites_a5.tsv"), "w")
out.write("module\tdep\tva_instr\tmnemo\troutine\tpartenaire_ro9\tclasse\tcouv_k\n")
for mod in ("ro5", "ro9"):
    A = V.a5_access(mod)
    for va, (d, m) in sorted(A.items()):
        if d not in D: continue
        f = C.func_of(mod, va)[0]
        p = inv.get(f) if mod == "ro5" else None
        ps = cl = ""
        if p:
            if isinstance(p, dict): ps, cl = p.get('partenaire'), p.get('classe')
            elif isinstance(p, (tuple, list)): ps, cl = p[0], p[1] if len(p) > 1 else ""
            else: ps = p
        cv = ("%.2f" % cov[f]) if mod == "ro5" and f in cov else ""
        out.write("%s\t$%04X\t%x\t%s\t%x\t%s\t%s\t%s\n" % (mod, d, va, m, f, ("%x" % ps) if isinstance(ps, int) else ps, cl, cv))
out.close()
