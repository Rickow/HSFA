#!/usr/bin/env python3
"""Validation des tuiles contre la CPS2 d'origine (vérité terrain : sfa3.zip décodé comme FBNeo).

1. PSP : part des tuiles d'un perso identiques / de même forme (couleurs renumérotées) qu'une tuile CPS2.
2. Permutation d'index PSP -> CPS2 déduite des tuiles appariées (attendu : i -> 16-i, 0 -> 0).
3. Anthology (anthgfx.py, espace FBNeo) : unités identiques aux tuiles CPS2 (HANDOFF §45).
Usage : python3 validate_cps2.py [pl00 pl01 pl0b ...]   (défaut : pl00 pl01 pl0b pl20)"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import collections
from cps2_tiles import cps2_pixels
from cmp_tiles import psp_tiles
from ro_tiles import tileset

def canon(p):
    m = {0: 0}; return bytes(m.setdefault(c, len(m)) for c in p)
pix = lambda t: bytes(n for b in t for n in (b & 0xF, b >> 4))

def main(pls):
    C = [t for t in cps2_pixels() if len(set(t)) > 2]
    Cs, Cidx = set(C), collections.defaultdict(list)
    for p in C: Cidx[canon(p)].append(p)
    print(f"CPS2 : {len(C)} tuiles non triviales\n")
    for pl in pls:
        P = [pix(t) for t in psp_tiles(pl) if len(set(pix(t))) > 2]
        ex = sum(p in Cs for p in P); m = [p for p in P if canon(p) in Cidx]
        pairs = collections.Counter()
        for p in m:
            for a, b in {(a, b) for a, b in zip(p, Cidx[canon(p)][0])}: pairs[(a, b)] += 1
        best = {}
        for a in range(16):
            o = [(n, b) for (x, b), n in pairs.items() if x == a]
            if o: n, b = max(o); best[a] = (b, round(100 * n / sum(k for k, _ in o)))
        print(f"{pl}: {len(P)} tuiles | identiques {100*ex/len(P):.1f} % | même forme {100*len(m)/len(P):.1f} %")
        print("   permutation PSP->CPS2 (confiance %):", " ".join(f"{a}->{b}({c})" for a, (b, c) in sorted(best.items())))
    # Anthology : unités CPS2 en espace FBNeo (ro_tiles.py, HANDOFF §45)
    for mod in ("ro3", "ro5"):
        U = [u for u in tileset(mod) if len(set(u)) > 2]
        ex = sum(u in Cs for u in U)
        print(f"\nAnthology {mod} : {len(U)} unités non triviales | identiques à une tuile CPS2 de SFA3 {100*ex/len(U):5.1f} %")
    T = [t for t in cps2_pixels() if len(set(t)) > 2]; A3 = tileset("ro3")
    print(f"tuiles CPS2 de SFA3 présentes dans ro3 : {100*sum(t in A3 for t in T)/len(T):.2f} %")

if __name__ == "__main__":
    main(sys.argv[1:] or ["pl00", "pl01", "pl0b", "pl20"])
