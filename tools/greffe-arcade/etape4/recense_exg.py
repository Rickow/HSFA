#!/usr/bin/env python3
"""Recensement des echanges de registres D (EXG_PILE_D) : oracle ancien (v153) contre nouvel oracle (v161).
Usage : recense_exg.py ANCIEN_DIR NOUVEAU_DIR [AUTRE_DIR ...]
Pour chaque site EXG_PILE_D de NOUVEAU (carte_image.txt) : adresse MIPS, 68K, octets reels lus dans
roms_fork/sfa3hx/sz3ud.03c/04c (mots echanges), et ce que l'ANCIEN fait a la meme adresse MIPS (texte + octets).
Recense aussi les paires croisees MOVE.L Dx,Dy ; MOVE.L Dy,Dx de chaque carte."""
import sys, os, re

def carte(d):
    L = []
    for l in open(os.path.join(d, 'carte_image.txt'), encoding='utf-8', errors='replace'):
        p = l.rstrip('\n').split(' ', 2)
        if len(p) == 3 and re.fullmatch(r'[0-9a-f]+', p[0]) and re.fullmatch(r'[0-9a-f]+', p[1]):
            L.append((int(p[0], 16), int(p[1], 16), p[2]))
    return L

_rom = {}
def octets(d, a, n):
    k = (d, a >> 19)
    if k not in _rom:
        f = os.path.join(d, 'roms_fork', 'sfa3hx', 'sz3ud.%s' % ('03c' if a < 0x80000 else '04c'))
        b = open(f, 'rb').read()
        _rom[k] = bytes(x for i in range(0, len(b), 2) for x in (b[i + 1], b[i]))
    o = a & 0x7FFFF
    return _rom[k][o:o + n]

MV = re.compile(r'MOVE\.L D(\d),D(\d)$')
def croises(L):
    r = []
    for i in range(len(L) - 1):
        m1 = MV.match(L[i][2].strip()); m2 = MV.match(L[i + 1][2].strip())
        if m1 and m2 and m1.group(1) == m2.group(2) and m1.group(2) == m2.group(1) and L[i + 1][0] == L[i][0] + 2:
            r.append(i)
    return r

anc, nouv = sys.argv[1], sys.argv[2]
A = carte(anc); N = carte(nouv)
iA = {}
for i, (a68, am, t) in enumerate(A): iA.setdefault(am, i)
sites = [i for i, x in enumerate(N) if 'EXG_PILE_D' in x[2]]
print('# sites EXG_PILE_D dans %s : %d' % (nouv, len(sites)))
print('# mips\t68k_nouv\toctets_nouv\ttexte_nouv\t68k_anc\toctets_anc\ttexte_anc\tverdict')
ok = 0
for i in sites:
    a68, am, t = N[i]
    bn = octets(nouv, a68, 2).hex()
    m = re.match(r'EXG D(\d),D(\d)', t)
    rx, ry = int(m.group(1)), int(m.group(2))
    attendu = '%04x' % (0xC140 | (rx << 9) | ry)            # EXG Dx,Dy (mode donnees)
    j = iA.get(am)
    if j is None:
        print('%06x\t%06x\t%s\t%s\t-\t-\t(absent)\t?' % (am, a68, bn, t)); continue
    ta = A[j][2]; tb = A[j + 1][2] if j + 1 < len(A) else ''
    ba = octets(anc, A[j][0], 4).hex()
    casse = MV.match(ta.strip()) and MV.match(tb.strip())
    v = ('JUSTE' if bn == attendu else 'OCTETS?') + ('/ancien_CASSE' if casse else '/ancien_?')
    ok += bn == attendu
    print('%06x\t%06x\t%s\t%s\t%06x\t%s\t%s ; %s\t%s' % (am, a68, bn, t.split('  [')[0], A[j][0], ba, ta, tb, v))
print('# octets EXG Dx,Dy justes dans le nouveau : %d / %d' % (ok, len(sites)))
for nom, L, d in (('ancien', A, anc), ('nouveau', N, nouv)):
    c = croises(L)
    print('# paires croisees MOVE.L Dx,Dy ; MOVE.L Dy,Dx dans %s : %d' % (nom, len(c)))
    for i in c: print('#   %06x mips %06x  %s' % (L[i][0], L[i][1], octets(d, L[i][0], 4).hex()))
for d in sys.argv[3:]:
    # autre construction (programme seul, meme disposition que NOUVEAU) : octets aux adresses 68K du nouveau
    eg = sum(octets(d, N[i][0], 2) == octets(nouv, N[i][0], 2) for i in sites)
    print('# %s : %d / %d sites aux octets identiques au nouveau' % (d, eg, len(sites)))
