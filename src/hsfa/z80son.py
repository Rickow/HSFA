#!/usr/bin/env python3
"""Lecture des donnees du pilote son Capcom (Z80, CPS2) de SFA3 / Upper : adresses lineaires, table des commandes,
en-tetes de morceaux, pistes (opcodes 00-1F, notes >= 20)."""
import struct
X = "<workspace>/anthology_extract/"
HDR = {"ro3": 0x3C00, "ro5": 0x3800}
ENV = {"ro3": 0x8000, "ro5": 0x6305}      # base de la table des enveloppes (ld bc,$xxxx en $13B4)

def lin2reg(L):  # adresse lineaire du pilote -> decalage dans la region audiocpu
    return L if L < 0x8000 else L + 0x8000

# longueur des arguments par opcode (0x1b : sous-opcode + 1 octet)
ARGS = {0: 0, 1: 0, 2: 0, 3: 0, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 0xa: 1, 0xb: 1, 0xc: 1, 0xd: 1,
        0xe: 3, 0xf: 3, 0x10: 3, 0x11: 3, 0x12: 3, 0x13: 3, 0x14: 3, 0x15: 3, 0x16: 2, 0x17: 0,
        0x18: 1, 0x19: 1, 0x1a: 1, 0x1b: 2, 0x1c: 2, 0x1d: 1, 0x1e: 1, 0x1f: 1}
SAUT = {0xe, 0xf, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16}   # 2 derniers octets d'argument = saut relatif signe

class Z80:
    def __init__(self, data, mod):
        self.z = bytearray(data); self.mod = mod; self.h = HDR[mod]
    def rb(self, L): return self.z[lin2reg(L)]
    def hdr(self):
        z, h = self.z, self.h
        return dict(b0=z[h], tabcmd=struct.unpack_from("<H", z, h + 1)[0],
                    tabech=struct.unpack_from("<H", z, h + 3)[0], tprog=h + 5)
    def cmdtab(self):
        L = self.hdr()["tabcmd"]
        n = (self.rb(L) << 8) | self.rb(L + 1)
        return L + 6, n
    def cmd(self, c):
        base, n = self.cmdtab()
        L = base + 4 * c
        return (self.rb(L) << 16) | (self.rb(L + 1) << 8) | self.rb(L + 2), L
    def morceau(self, p):
        """en-tete : priorite + 16 decalages BE relatifs a l'en-tete -> liste des debuts de piste"""
        pr = self.rb(p)
        t = []
        for k in range(16):
            o = (self.rb(p + 1 + 2 * k) << 8) | self.rb(p + 2 + 2 * k)
            t.append(p + o if o else None)
        return pr, t
    def piste(self, L, maxlen=0x40000):
        """parcourt une piste (tous les chemins) ; renvoie l'ensemble des octets touches et la liste des opcodes"""
        vus, ops, pile = set(), [], [L]
        while pile:
            a = pile.pop()
            while a not in vus:
                op = self.rb(a)
                if op >= 0x20:
                    vus.add(a); a += 1; continue
                n = ARGS[op]
                if op == 0x1b: n = 2
                for k in range(n + 1): vus.add(a + k)
                arg = [self.rb(a + 1 + k) for k in range(n)]
                ops.append((a, op, arg))
                if op in SAUT:
                    rel = (arg[-2] << 8) | arg[-1]
                    if rel >= 0x8000: rel -= 0x10000
                    cible = a + 1 + n + rel
                    if op == 0x16:
                        a = cible; continue
                    pile.append(cible)
                if op == 0x17: break
                a += n + 1
        return vus, ops

def charge(mod):
    return Z80(open(X + mod + "_usa_z80.bin", "rb").read(), mod)
