#!/usr/bin/env python3
"""homol_const.py VAL... : pour chaque constante de donnees d'Upper (exec.), sites ro5 -> routine -> partenaire ro9
(inverse_ro5.pkl) ; constantes de la routine partenaire appariees par rang (meme ordre) -> homologue probable."""
import os, sys, pickle
os.environ.setdefault("GRAIN", "routine")
sys.path.insert(0, "<workspace>/work/carto_ro9"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import commun as K, consts as CS
inv = pickle.load(open("<workspace>/work/etude_upper_hyper/inverse_ro5.pkl", "rb"))
cov = pickle.load(open("<workspace>/work/etude_upper_hyper/couv_k.pkl", "rb"))
D5, D9 = CS.C('ro5'), CS.C('ro9')
def dconsts(mod, D, a, b, lo=0x500000, hi=0xC00000):
    r = sorted((s, v) for v, ss in D.items() if lo <= v < hi for s in ss if a <= s < b)
    return [v for s, v in r]
def homol(v):
    res = []
    for s in D5.get(v, []):
        a, b = K.func_of('ro5', s); p = inv.get(a, {})
        pa = p.get('partenaire'); cl = p.get('classe', '?')
        if pa is None: res.append((s, a, None, cl, None)); continue
        pb = K.func_of('ro9', pa)[1]
        c5 = dconsts('ro5', D5, a, b); c9 = dconsts('ro9', D9, pa, pb)
        h = None
        if v in c5 and len(c5) == len(c9): h = c9[c5.index(v)]
        res.append((s, a, pa, cl, h, c5, c9))
    return res
if __name__ == "__main__":
    for x in sys.argv[1:]:
        v = int(x, 16)
        for r in homol(v):
            if r[2] is None: print("%x : site %x r%x -> pas de partenaire (%s)" % (v, r[0], r[1], r[3])); continue
            print("%x : site %x r%x (couv %.2f) -> ro9 r%x %s ; homologue %s ; ro5 %s | ro9 %s" % (v, r[0], r[1], cov.get(r[1], -1), r[2], r[3],
                  ('%x' % r[4]) if r[4] else '?', ' '.join('%x' % c for c in r[5]), ' '.join('%x' % c for c in r[6])))
