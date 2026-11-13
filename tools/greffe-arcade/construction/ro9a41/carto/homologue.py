#!/usr/bin/env python3
"""Homologues entre modules : fonction contenant une adresse, meilleur partenaire dans un autre module
(niveaux de comparaison.py), puis correspondance d'instruction a instruction par alignement (difflib) des
mots MIPS normalises (adresses masquees). Ancres = fonctions identiques UNIQUES des deux cotes."""
import os, pickle, collections, difflib, bisect
import commun as C
import comparaison as K

_P = {}; _I = {}
def P(mod):
    if mod not in _P:
        f = os.path.join(C.OUT, "profil_%s%s.pkl" % (mod, C.SUF))
        if os.path.exists(f): _P[mod] = pickle.load(open(f, "rb"))
        else:
            _P[mod] = K.profile(mod); pickle.dump(_P[mod], open(f, "wb"))
        _I[mod] = K.index(_P[mod])
    return _P[mod]

def norm_words(mod, a, b):
    out = []; lui = set()
    for x in C.seg(mod, a, b):
        w = x.w; op = w >> 26
        if op in (2, 3): w &= 0xfc000000
        elif op == 0x0f: w &= 0xffff0000; lui.add((w >> 16) & 0x1f)
        elif op in (0x09, 0x0d) and ((w >> 21) & 0x1f) in lui: w &= 0xffff0000
        out.append((x.va, w))
    return out

def partner(src, a, dst):
    p = P(src)[a]; P(dst)
    return K.best(p, _P[dst], _I[dst])

def homologue(src, va, dst):
    """-> dict(fonction_src, classe, partenaire, score, va_dst (instruction homologue ou None))"""
    f = C.func_of(src, va)
    if f is None: return None
    a, b = f
    kind, pa, j = partner(src, a, dst)
    r = dict(src_fonction=a, classe=K.classe(kind, j), partenaire=pa, score=round(j, 3), va_dst=None, sur=0.0)
    if pa is None: return r
    pb = _P[dst][pa]['b']
    s1 = norm_words(src, a, b); s2 = norm_words(dst, pa, pb)
    sm = difflib.SequenceMatcher(None, [w for _, w in s1], [w for _, w in s2], autojunk=False)
    idx = [v for v, _ in s1]
    i = bisect.bisect_left(idx, va)
    for blk in sm.get_matching_blocks():
        if blk.a <= i < blk.a + blk.size:
            r['va_dst'] = s2[blk.b + i - blk.a][0]; break
    r['sur'] = round(sm.ratio(), 3)
    return r

def ancres(m1, m2):
    """fonctions identiques uniques des deux cotes -> [(a1, a2)] tries"""
    P1, P2 = P(m1), P(m2)
    c1 = collections.Counter(p['ex'] for p in P1.values()); c2 = collections.Counter(p['ex'] for p in P2.values())
    inv2 = {p['ex']: a for a, p in P2.items() if c2[p['ex']] == 1}
    return sorted((a, inv2[p['ex']]) for a, p in P1.items() if c1[p['ex']] == 1 and p['ex'] in inv2 and p['b'] - a >= 64)

if __name__ == "__main__":
    import json
    out = {}
    for m2 in ('ro5', 'ro3'):
        an = ancres('ro9', m2)
        seq, segs = K.segments(an)
        # regroupement : segments consecutifs (petits ecarts de decalage) -> grandes zones
        print("ro9 / %s : %d ancres uniques (>= 64 o), %d dans l'ordre (%.0f %%), %d segments de decalage constant" % (
            m2, len(an), len(seq), 100*len(seq)/max(1, len(an)), len(segs)))
        big = sorted(segs, key=lambda s: -s['n'])[:12]
        for s in sorted(big, key=lambda s: s['debut9']):
            print("   ro9 fichier %s..%s  ->  %s = ro9 %+#x  (%d ancres)" % (C.h(s['debut9']), C.h(s['fin9']), m2, s['delta'], s['n']))
        out[m2] = dict(ancres=len(an), ordre=len(seq), segments=segs)
    json.dump(out, open(os.path.join(C.OUT, "ancres_ro9.json"), "w"), indent=0)
