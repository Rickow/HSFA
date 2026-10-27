#!/usr/bin/env python3
"""Couverture croisee par fenetres de K instructions MIPS (adresses : cibles jal/j et lui+addiu/ori masquees),
insensible au decoupage et a l'ordre (methode de carto_ro9/couverture.py), sur les zones 68K de zones.py.
Matrice : part des instructions de LIGNE couvertes par une fenetre presente dans COLONNE. K=64 et 128."""
import sys, numpy as np
sys.path.insert(0, '.')
import commun as C, zones as Zm
MODS = ['ro1','ro2','ro3','ro4','ro5','ro6','ro7','ro8','ro9']
def stream(mod):
    Z = Zm.zones(mod)['m68k']; ws = []
    for z0, z1 in Z:
        lui = set()
        for x in C.seg(mod, z0, z1):
            w = x.w; op = w >> 26
            if op in (2, 3): w &= 0xfc000000
            elif op == 0x0f: w &= 0xffff0000; lui.add((w >> 16) & 0x1f)
            elif op in (0x09, 0x0d) and ((w >> 21) & 0x1f) in lui: w &= 0xffff0000
            ws.append(w)
    return np.array(ws, dtype=np.uint64)
def windows(ws, K):
    h = np.zeros(len(ws) - K + 1, dtype=np.uint64); P = np.uint64(1000003)
    for i in range(K): h = h * P + ws[i:len(ws) - K + 1 + i]
    return h
S = {m: stream(m) for m in MODS}
for K in (64, 128):
    H = {m: windows(S[m], K) for m in MODS}
    U = {m: np.unique(H[m]) for m in MODS}
    print('K=%d : part des instructions de la ligne couvertes par la colonne' % K)
    print('      ' + ' '.join('%6s' % m for m in MODS))
    for X in MODS:
        row = []
        for R in MODS:
            if R == X: row.append('     -'); continue
            hit = np.isin(H[X], U[R]); cov = np.zeros(len(S[X]), dtype=bool)
            idx = np.nonzero(hit)[0]
            # marquer les K instructions de chaque fenetre trouvee
            d = np.zeros(len(S[X]) + 1, dtype=np.int64); np.add.at(d, idx, 1); np.add.at(d, idx + K, -1)
            cov = np.cumsum(d)[:-1] > 0
            row.append('%5.1f%%' % (100 * cov.mean()))
        print('%-5s ' % X + ' '.join(row), flush=True)
    print()
