"""Lecture des pilotes Z80 CPS2 v1.04 / v1.05 (en-tete parametrable)."""
import struct
def reg(L): return L if L < 0x8000 else L + 0x8000
HDR = {'sfa': (0x9000, 0x9006), 'sfa2': (0x9000, 0x9006), 'ssf2': (0x7C10, 0x7C16), 'ssf2t': (0x9000, 0x9006)}
class Pilote:
    def __init__(self, path, jeu):
        self.z = open(path, 'rb').read(); a, t = HDR[jeu]; self.t = t
        self.n = (self.z[reg(a)] << 8) | self.z[reg(a) + 1]
    def o(self, L): return self.z[reg(L)]
    def cmd(self, c):
        c %= self.n; p = reg(self.t + 4 * c)
        b, h, l, x = self.z[p:p + 4]
        if self.t < 0x8000: b &= 0x0F   # v1.04 : octet haut = drapeau 0x10 + banque
        return (b << 16) | (h << 8) | l
    def morceau(self, c):
        L = self.cmd(c)
        if not L: return None
        offs = [(self.o(L + 1 + 2 * k) << 8) | self.o(L + 2 + 2 * k) for k in range(16)]
        return dict(L=L, prio=self.o(L), pistes=[(k, L + v) for k, v in enumerate(offs) if v])
