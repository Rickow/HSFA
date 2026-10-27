#!/usr/bin/env python3
"""Parente des DONNEES entre modules (methode de carto_ro9/donnees.py : fenetres de 32 o au pas de 4, phases 0 et 2,
longs 'pointeurs' [0x1F0000, 0xC00000) masques, fenetres nulles ecartees). Matrice : part des octets de donnees de
LIGNE retrouves dans COLONNE (non exclusif). Plus : part non nulle 'neuve' (absente de tous les autres modules)."""
import sys, numpy as np
sys.path.insert(0, '.')
import commun as C
MODS = ['ro1','ro2','ro3','ro4','ro5','ro6','ro7','ro8','ro9']; W = 32
def data(m):
    b = C.load(m); e = C.header(m)['code_end'] + 0x40
    return np.frombuffer(b, dtype=np.uint8)[e:].copy()
def wh(a, ph):
    a = a.copy(); n = (len(a) - ph) // 4; u = a[ph:ph + 4*n].view(np.uint32)
    u[(u >= 0x1F0000) & (u < 0xC00000)] = 0
    u = u.astype(np.uint64); k = W // 4
    h = np.zeros(n - k + 1, np.uint64); z = np.ones(n - k + 1, bool); P = np.uint64(0x100000001B3)
    for i in range(k):
        h = h * P + u[i:n - k + 1 + i] + np.uint64(i + 1); z &= (u[i:n - k + 1 + i] == 0)
    return h, ~z
D = {m: data(m) for m in MODS}
H = {m: [wh(D[m], ph) for ph in (0, 2)] for m in MODS}
U = {m: np.unique(np.concatenate([h[nz] for h, nz in H[m]])) for m in MODS}
def cover(X, refs):
    cov = np.zeros(len(D[X]) + W + 4, np.int64)
    for ph, (h, nz) in zip((0, 2), H[X]):
        hit = np.zeros(len(h), bool)
        for R in refs: hit |= np.isin(h, U[R])
        idx = np.nonzero(hit & nz)[0] * 4 + ph
        np.add.at(cov, idx, 1); np.add.at(cov, idx + W, -1)
    return (np.cumsum(cov)[:len(D[X])] > 0)
print('Donnees : taille (Mo) ' + ' '.join('%s %.2f' % (m, len(D[m]) / 2**20) for m in MODS))
print('Part des octets de donnees de LIGNE retrouves dans COLONNE (fenetres de 32 o, pointeurs masques)')
print('      ' + ' '.join('%6s' % m for m in MODS) + '   tous  zeros   neuf')
for X in MODS:
    row = []
    for R in MODS:
        row.append('     -' if R == X else '%5.1f%%' % (100 * cover(X, [R]).mean()))
    allc = cover(X, [R for R in MODS if R != X]); z = (D[X] == 0) & ~allc
    row.append('%5.1f%%' % (100 * allc.mean())); row.append('%5.1f%%' % (100 * z.mean())); row.append('%5.1f%%' % (100 * (~allc & ~z).mean()))
    print('%-5s ' % X + ' '.join(row), flush=True)
