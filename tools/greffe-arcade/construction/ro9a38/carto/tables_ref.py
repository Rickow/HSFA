#!/usr/bin/env python3
"""Homologue d'une TABLE de donnees : sites qui forment l'adresse X (lui + addiu/ori, ou deplacement d'un
load/store) dans le module source -> instruction homologue dans le module cible -> constante formee la."""
import os, pickle, collections, functools
import commun as C
import homologue as H

@functools.lru_cache(None)
def cmap(mod):
    f = os.path.join(C.OUT, "consts_%s%s.pkl" % (mod, C.SUF))
    if os.path.exists(f): return pickle.load(open(f, "rb"))
    s0 = C.start68k(mod)
    L = [x for x in C.instrs(mod) if x.va >= s0]
    byva = {}; byval = collections.defaultdict(list)
    # par fonction (pour ne pas propager un lui d'une fonction a l'autre)
    for a, b in C.funcs(mod):
        for va, v, kind in C.consts32(C.seg(mod, a, b)):
            if kind == 'lui': continue
            byva[va] = v; byval[v].append(va)
    r = (byva, dict(byval)); pickle.dump(r, open(f, "wb")); return r

def sites(mod, X): return cmap(mod)[1].get(X, [])

def homologue_table(src, X, dst, tol=0x40):
    """-> Counter(constante cible), details. tol : on accepte une constante formee a +-tol d'un X legerement
    decale (tables indexees par base+deplacement)"""
    byva_d = cmap(dst)[0]
    votes = collections.Counter(); det = []
    for va in sites(src, X):
        r = H.homologue(src, va, dst)
        v = byva_d.get(r['va_dst']) if r and r['va_dst'] is not None else None
        det.append((va, r and r['classe'], r and r['partenaire'], r and r['va_dst'], v))
        if v is not None: votes[v] += 1
    return votes, det

if __name__ == "__main__":
    import sys
    src, dst = sys.argv[1], sys.argv[2]
    for x in sys.argv[3:]:
        X = int(x, 16); v, d = homologue_table(src, X, dst)
        print("%s %s -> %s : %s" % (src, C.h(X), dst, ', '.join('%s x%d' % (C.h(k), n) for k, n in v.most_common(4))))
        for row in d[:6]: print("    site %x (%s, partenaire %s) -> %s : %s" % (row[0], row[1], row[2] and hex(row[2]), row[3] and hex(row[3]), row[4] and hex(row[4])))
