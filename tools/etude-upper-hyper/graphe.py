#!/usr/bin/env python3
"""Graphe d'appels approche d'un module (ro5 / ro9), grain 'routine' de carto_ro9 :
  - aretes : cibles de jal ; constantes 32 bits (lui+addiu/ori) tombant dans le code (jalr a constante, entrees de
    taches) ; tables de pointeurs de code en donnees referencees par une constante (aiguillages, tables de scenes,
    tables par perso) : toutes leurs entrees (suite de longs 0 / pointeurs de code, au plus 256) ;
  - references de donnees : constantes tombant dans la section de donnees.
Sortie : graphe_<mod>.pkl = dict(funcs=[(a,b)], succ={a:set}, data={a:set(exec)}, tables={exec:[cibles]})"""
import os, sys, pickle, struct, bisect, collections
os.environ["GRAIN"] = "routine"
sys.path.insert(0, "<workspace>/work/carto_ro9")
import commun as C
import tables_ref as TR
OUT = os.path.dirname(os.path.abspath(__file__))

def build(mod):
    b = C.load(mod); h = C.header(mod); s0 = C.start68k(mod); ce = h['code_end']
    F = C.funcs(mod); starts = [a for a, _ in F]
    lo, hi = C.BASE + s0, C.BASE + ce
    dlo, dhi = C.BASE + ce, h['fin_exec']
    def fstart(va):
        k = bisect.bisect_right(starts, va) - 1
        return starts[k] if k >= 0 else None
    byva, byval = TR.cmap(mod)
    debuts = {v for v in byval if dlo <= v < dhi}      # toute adresse de donnees formee par le code = debut de table
    tables = {}
    def table(ex):
        if ex in tables: return tables[ex]
        o = ex - C.BASE; out = []; nz = 0
        for k in range(256):
            if o + 4 * k + 4 > len(b): break
            if k and (ex + 4 * k) in debuts: break      # debut d'une autre table referencee : fin de celle-ci
            v = struct.unpack_from('<I', b, o + 4 * k)[0]
            if v == 0:
                nz += 1
                if nz > 8: break
                continue
            if lo <= v < hi and (v & 3) == 0: out.append(v - C.BASE); nz = 0
            else: break
        tables[ex] = out if out else []
        return tables[ex]
    succ = collections.defaultdict(set); data = collections.defaultdict(set)
    petit = collections.defaultdict(set)              # sans les aretes des grandes tables (> 24 entrees : par perso, par objet)
    for x in C.instrs(mod):
        if x.va < s0: continue
        if x.m == 'jal':
            t = x.tgt - C.BASE
            if s0 <= t < ce: succ[fstart(x.va)].add(fstart(t)); petit[fstart(x.va)].add(fstart(t))
    for va, v in byva.items():
        f = fstart(va)
        if f is None: continue
        if lo <= v < hi: succ[f].add(fstart(v - C.BASE)); petit[f].add(fstart(v - C.BASE))
        elif dlo <= v < dhi:
            data[f].add(v)
            T = table(v)
            for t in T:
                succ[f].add(fstart(t))
                if len(T) <= 24: petit[f].add(fstart(t))
    for f in list(succ): succ[f].discard(None)
    for f in list(petit): petit[f].discard(None)
    g = dict(funcs=F, succ=dict(succ), petit=dict(petit), data=dict(data), tables=tables)
    pickle.dump(g, open(os.path.join(OUT, "graphe_%s.pkl" % mod), "wb"))
    ne = sum(len(s) for s in succ.values())
    print("%s : %d routines, %d aretes, %d routines referencant des donnees, %d tables de code" % (
        mod, len(F), ne, len(data), sum(1 for t in tables.values() if t)))

if __name__ == "__main__":
    for m in sys.argv[1:] or ['ro5', 'ro9']: build(m)
