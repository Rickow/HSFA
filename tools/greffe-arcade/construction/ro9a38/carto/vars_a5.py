#!/usr/bin/env python3
"""Correspondance des VARIABLES GLOBALES (A5 + d) ro3 -> ro9 (et ro5), par les instructions homologues :
chaque acces A5+d de ro3 est projete sur l'instruction homologue de ro9 (alignement de homologue.py) ; vote.
Interet : l'outillage ro3 (mame_test.py, scripts Lua) code en dur des variables ($C18E, $C000/$C001, $BE48...)."""
import os, collections, json, bisect
os.environ.setdefault("GRAIN", "routine")
import commun as C, homologue as H

def a5_access(mod):
    out = {}
    for a, b in C.funcs(mod):
        base = set()
        for x in C.seg(mod, a, b):
            if x.m == 'lw' and x.imm == 0x1114: base.add(x.rt); continue
            if x.m in ('lb','lbu','lh','lhu','lw','sb','sh','sw') and x.rs in base: out[x.va] = (x.simm & 0xffff, x.m)
            d = x.rt if x.m in ('lb','lbu','lh','lhu','lw','andi','lui','ori','addiu') else (x.rd if x.op == 0 else None)
            if d is not None: base.discard(d)
    return out

def project(src, dst, A_src, A_dst):
    votes = collections.defaultdict(collections.Counter)
    byf = collections.defaultdict(list)
    for va in A_src: byf[C.func_of(src, va)[0]].append(va)
    for f, vas in byf.items():
        r = H.homologue(src, f, dst)
        if not r or r['partenaire'] is None or r['score'] < 0.7: continue
        # alignement complet de la fonction
        a, b = C.func_of(src, f); pa = r['partenaire']; pb = H.P(dst)[pa]['b']
        import difflib
        s1 = H.norm_words(src, a, b); s2 = H.norm_words(dst, pa, pb)
        sm = difflib.SequenceMatcher(None, [w & 0xffff0000 if (w >> 26) in (0x20,0x21,0x23,0x24,0x25,0x28,0x29,0x2b) else w for _, w in s1],
                                     [w & 0xffff0000 if (w >> 26) in (0x20,0x21,0x23,0x24,0x25,0x28,0x29,0x2b) else w for _, w in s2], autojunk=False)
        idx = {v: k for k, (v, _) in enumerate(s1)}
        for blk in sm.get_matching_blocks():
            for k in range(blk.size):
                v1 = s1[blk.a + k][0]; v2 = s2[blk.b + k][0]
                if v1 in A_src and v2 in A_dst and A_src[v1][1] == A_dst[v2][1]:
                    votes[A_src[v1][0]][A_dst[v2][0]] += 1
    return votes

if __name__ == "__main__":
    A3, A5_, A9 = a5_access('ro3'), a5_access('ro5'), a5_access('ro9')
    res = {}
    for dst, Ad in (('ro9', A9), ('ro5', A5_)):
        V = project('ro3', dst, A3, Ad)
        res[dst] = {"%04x" % d: {"%04x" % k: n for k, n in c.most_common(3)} for d, c in V.items()}
        moved = {d: c.most_common(1)[0][0] for d, c in V.items() if c.most_common(1)[0][0] != d}
        same = sum(1 for d, c in V.items() if c.most_common(1)[0][0] == d)
        print("ro3 -> %s : %d variables A5 projetees ; %d au meme deplacement, %d deplacees" % (dst, len(V), same, len(moved)))
        deltas = collections.Counter((moved[d] - d) & 0xffff for d in moved)
        print("   decalages les plus frequents : %s" % ', '.join('%+#x x%d' % ((k - 0x10000) if k >= 0x8000 else k, n) for k, n in deltas.most_common(6)))
        for d in (0xc000, 0xc001, 0xc010, 0xc012, 0xc018, 0xc019, 0xc18e, 0xc18c, 0xc1a4, 0xbe48, 0xc178, 0x0100, 0x0016, 0x00dc, 0x0062, 0x0058, 0x005c):
            c = V.get(d)
            print("   ro3 $%04x -> %s %s" % (d, dst, ', '.join('$%04x x%d' % kv for kv in c.most_common(2)) if c else '(non projete)'))
    json.dump(res, open(os.path.join(C.OUT, "vars_a5.json"), "w"), indent=0)
