#!/usr/bin/env python3
"""Niveau 'identique 68K' (comme carto_ro9/comparaison.py) : suite des opcodes 68K emis par le traducteur (mode hote,
deplacements de Bcc masques) egale -> insensible a la forme des CMP du recompilateur (ro6 et ro3 sont mixtes).
Usage : GRAIN=routine id68k.py X R1 R2... (part du code recompile de X identique MIPS, puis identique 68K)"""
import os, sys, pickle, hashlib, collections
os.environ.setdefault('GRAIN', 'routine'); os.environ.setdefault('MEMMODE', 'hote')
sys.path.insert(0, '.')
import commun as C
import mips
X, refs = sys.argv[1], sys.argv[2:]
PROF = pickle.load(open('comparaison_mod_profils.pkl', 'rb'))
def h68(mod):
    import translate as T
    if C.funcs(mod)[0][0] < mips.CODE0: mips.CODE0 = 0x40
    buf = C.load(mod); T._RAM_CACHE[bytes(buf[:32])] = {'ro1':0x60,'ro2':0x80,'ro4':0x80,'ro6':0x80,'ro7':0x66,'ro8':0x80,'ro3':0x90,'ro5':0xa0,'ro9':0xb8}[mod]
    out = {}
    for a, b in C.funcs(mod):
        try: o, _ = T.translate(buf, a, b)
        except Exception: continue
        w = []
        for va, mn, ws in o:
            if not ws: continue
            x = ws[0]
            if 0x6000 <= x <= 0x6fff: x &= 0xff00
            w.append(x)
        if len(w) >= 8: out[a] = hashlib.blake2b(repr(w).encode(), digest_size=12).digest()
    return out
H = {m: h68(m) for m in [X] + refs}
PX = PROF[X]; tot = sum(p['b'] - a for a, p in PX.items() if not p['nat'])
exR = set().union(*[{p['ex'] for p in PROF[R].values()} for R in refs])
hR = set().union(*[set(H[R].values()) for R in refs])
c = collections.Counter()
for a, p in PX.items():
    if p['nat']: continue
    if p['ex'] in exR: c['identique MIPS'] += p['b'] - a
    elif H[X].get(a) in hR: c['identique 68K seulement'] += p['b'] - a
    else: c['autre'] += p['b'] - a
print('%s contre %s : ' % (X, '+'.join(refs)) + ' | '.join('%s %.1f %% (%.0f Ko)' % (k, 100 * v / tot, v / 1024) for k, v in c.items()))
