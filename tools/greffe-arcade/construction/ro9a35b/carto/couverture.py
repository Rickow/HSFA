#!/usr/bin/env python3
"""Couverture de ro9 par des fenetres de K instructions MIPS presentes dans ro5 / ro3 (insensible au decoupage
en fonctions et a l'ordre). Deux normalisations :
  'adresses' : cibles de jal/j et constantes d'adresse (lui + addiu/ori qui suit) masquees ; le reste exact
  'forme'    : tous les immediats et deplacements masques aussi
+ ancres (fonctions identiques UNIQUES des deux cotes) -> ordre et decalages ro9 -> ro5 / ro3."""
import os, sys, pickle, collections, bisect
import numpy as np
import commun as C
K = 12
LS = {0x20,0x21,0x23,0x24,0x25,0x28,0x29,0x2b,0x37,0x3f,0x1e,0x1f}

def stream(mod, forme):
    s0 = C.start68k(mod); L = [x for x in C.instrs(mod) if x.va >= s0]
    ws = []; lui = set()
    for x in L:
        w = x.w; op = w >> 26
        if op in (2, 3): w &= 0xfc000000
        elif op == 0x0f: w &= 0xffff0000; lui.add((w >> 16) & 0x1f)
        elif op in (0x09, 0x0d) and ((w >> 21) & 0x1f) in lui: w &= 0xffff0000
        elif forme and (op in (0x08,0x09,0x0a,0x0b,0x0c,0x0d,0x0e) or op in LS or op in (1,4,5,6,7)): w &= 0xffff0000
        ws.append(w)
    return np.array(ws, dtype=np.uint64), np.array([x.va for x in L])

def windows(ws):
    # hachage polynomial des fenetres de K mots
    h = np.zeros(len(ws) - K + 1, dtype=np.uint64)
    P = np.uint64(1000003)
    for i in range(K):
        h = h * P + ws[i:len(ws) - K + 1 + i]
    return h

def cover(mod, refs, forme):
    w9, va9 = stream(mod, forme); h9 = windows(w9)
    cov = np.zeros(len(w9), dtype=bool)
    hits = np.zeros(len(h9), dtype=bool)
    for r in refs:
        wr, _ = stream(r, forme); hr = set(windows(wr).tolist())
        hits |= np.fromiter((x in hr for x in h9.tolist()), dtype=bool, count=len(h9))
    for i in np.nonzero(hits)[0]: cov[i:i+K] = True
    return cov, va9

def main():
    res = {}
    for forme in (False, True):
        for refs in (('ro5',), ('ro3',), ('ro5', 'ro3')):
            cov, va = cover('ro9', refs, forme)
            res[(forme, refs)] = cov
            print("ro9 couvert par %-9s (fenetres de %d instr., %-9s) : %5.1f %% des instructions 68K-recompilees" % (
                '+'.join(refs), K, 'forme' if forme else 'adresses', 100*cov.mean()))
    # symetrique : part d'Upper retrouvee dans Hyper
    for forme in (False, True):
        cov, _ = cover('ro5', ('ro9',), forme)
        print("ro5 couvert par ro9 (%s) : %5.1f %%" % ('forme' if forme else 'adresses', 100*cov.mean()))
        cov, _ = cover('ro3', ('ro5',), forme)
        print("ro3 couvert par ro5 (%s) : %5.1f %%" % ('forme' if forme else 'adresses', 100*cov.mean()))
    _, va = stream('ro9', False)
    pickle.dump(dict(va=va, cov={("forme" if f else "adresses", "+".join(r)): c for (f, r), c in res.items()}),
                open(os.path.join(C.OUT, "couverture_ro9.pkl"), "wb"))

if __name__ == "__main__":
    main()
