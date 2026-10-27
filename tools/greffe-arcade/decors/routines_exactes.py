#!/usr/bin/env python3
"""routines_exactes.py VA... : une routine d'Upper (GRAIN=routine) a-t-elle une copie EXACTE dans Hyper (mots MIPS,
cibles jal et immediats lui/addiu/ori masques) ? -> adresse(s) Hyper. Sans argument : cibles des tables de gestionnaires
(gestionnaires.tsv)."""
import os, sys, csv, functools
os.environ.setdefault("GRAIN", "routine")
sys.path.insert(0, "<workspace>/work/carto_ro9")
import commun as K
def norm(mod, a, b):
    r = []
    for x in K.seg(mod, a, b):
        w = x.w if hasattr(x, 'w') else None
        r.append((x.m, getattr(x, 'rs', None), getattr(x, 'rt', None), getattr(x, 'rd', None),
                  None if x.m in ('jal', 'lui', 'addiu', 'ori', 'j') else getattr(x, 'imm', None),
                  None if x.m in ('jal', 'j') else getattr(x, 'sa', None)))
    return tuple(r)
@functools.lru_cache(None)
def index9():
    d = {}
    for a, b in K.funcs('ro9'):
        if b - a > 0x4000: continue
        d.setdefault(norm('ro9', a, b), []).append(a)
    return d
def cherche(va):
    a, b = K.func_of('ro5', va)
    return a, b, index9().get(norm('ro5', a, b), [])
if __name__ == "__main__":
    H = os.path.dirname(os.path.abspath(__file__))
    vas = [int(x, 16) for x in sys.argv[1:]] or sorted({int(r['cible_upper(fichier)'], 16) for r in csv.DictReader(open(os.path.join(H, "gestionnaires.tsv")), delimiter='\t')})
    for v in vas:
        a, b, h = cherche(v)
        print("%x (%x-%x, %d o) -> Hyper %s" % (v, a, b, b - a, ' '.join('%x' % x for x in h) or 'AUCUNE copie exacte'))
