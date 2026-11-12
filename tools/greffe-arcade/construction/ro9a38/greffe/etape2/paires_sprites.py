# (e35) enregistrements d'images (sprites) d'Upper dans les donnees du module : 0002 id (n-1) 0000 ptr(fichier 390, $00B0xxxx..)
# puis n paires (code, attr). Rend l'ensemble des cases (exec PS2, longs alignes sur 4 qui recouvrent une paire).
import struct, donnees2 as D, plan as PL
def paires():
    b = PL.b5; base = D.BASE; lo, hi = D.LO, D.HI
    S = set(); recs = 0
    for a in range(lo, hi - 12, 2):
        o = a - base
        w0, w1, w2, w3 = struct.unpack_from('<4H', b, o)
        if w0 != 2 or w3 != 0 or w2 > 0x80: continue
        p = struct.unpack_from('<I', b, o + 8)[0]
        if not (D.F390 <= p < D.F390_1): continue
        n = w2 + 1; deb = a + 12; fin = deb + 4 * n
        if fin > hi: continue
        recs += 1
        for c in range(deb & ~3, fin, 4): S.add(c)
    return S, recs
if __name__ == '__main__':
    S, r = paires(); print('enregistrements', r, 'cases', len(S))
    for t in (0x652414, 0x6522c0, 0x652494, 0x652bd4, 0x64f550, 0x64f560, 0x64f6d0):
        print(hex(t), t in S)
