#!/usr/bin/env python3
"""Lecture statique des donnees du pilote Z80 CPS2 « version 1.05 » (SFA1 = 1.05A 1993, SFA2/Alpha = 1.05C 1996).
Region Z80 (image audiocpu 0x48000) : lineaire L -> region L (L < 0x8000) ou L + 0x8000 (L >= 0x8000).
En-tete en $9000 (banque 0 = region 0x11000) : mot BE = nombre de commandes N (le pilote fait c mod N),
table des commandes en $9006 + 4c : [b, H, L, x] -> pointeur lineaire 24 bits b:H:L du morceau.
Morceau : octet 0 = priorite (0 -> $04B6, >= $80 -> commande speciale $0563), puis 16 decalages BE (pistes 0-15,
relatifs au debut du morceau ; 0 = piste vide)."""
import sys, struct

def reg(L):
    return L if L < 0x8000 else L + 0x8000

class Z80:
    def __init__(self, path):
        self.z = open(path, 'rb').read()
        self.n = struct.unpack_from('>H', self.z, 0x11000)[0]
    def octet(self, L): return self.z[reg(L)]
    def cmd(self, c):
        c %= self.n
        b, h, l, x = self.z[0x11006 + 4 * c: 0x11006 + 4 * c + 4]
        return (b << 16) | (h << 8) | l
    def morceau(self, c):
        L = self.cmd(c)
        if L == 0: return None
        prio = self.octet(L)
        pistes = []
        if prio < 0x80 and prio != 0:
            for k in range(16):
                o = (self.octet(L + 1 + 2 * k) << 8) | self.octet(L + 2 + 2 * k)
                if o: pistes.append((k, L + o))
        return dict(L=L, prio=prio, pistes=pistes)

if __name__ == '__main__':
    z = Z80(sys.argv[1])
    print('N =', hex(z.n))
    for c in range(z.n):
        m = z.morceau(c)
        if m is None: continue
        print('%04x L=%06x prio=%02x pistes=%s' % (c, m['L'], m['prio'], ' '.join('%d@%06x' % p for p in m['pistes'])))
