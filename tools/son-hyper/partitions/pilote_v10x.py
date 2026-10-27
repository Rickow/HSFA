#!/usr/bin/env python3
"""pilote_v10x.py -- lecture des donnees des pilotes son Z80 CPS2 v1.04 / v1.05 (SSF2, SSF2T, SFA1, SFA2).

Version de chaque pilote (chaine en 0x000E de l'image) :
  ssf2  v1.04 (1993 / NOVEM.)    en-tete $7C10, table $7C16 (zone fixe) ; octet haut de l'entree = $10 | banque
  ssf2t v1.04 (1993 / NOVEMBER)  en-tete $9000, table $9006
  sfa   v1.05A (1993 / JUNE)     en-tete $9000, table $9006
  sfa2  v1.05C (1996 / FEB.)     en-tete $9000, table $9006
  hsf2  v1.06b (1996 / APR.)     en-tete $9000, table $9006 ; musique identique a ssf2t octet pour octet
En-tete : mot BE = nombre de commandes N (le pilote fait c mod N). Entree de commande : [b, H, L, x] -> adresse
lineaire 24 bits du morceau. Adresse lineaire L -> image : L si L < 0x8000, sinon L + 0x8000 (banque = (L >> 14) - 2).
Morceau : octet 0 = priorite (0 = musique), puis 16 decalages BE (voies 0-15, relatifs au morceau, 0 = vide).
Meme routine de commande dans les cinq (Z80 $01E3-$0225 environ), seules les adresses changent.
"""
HDR = {'sfa': (0x9000, 0x9006), 'sfa2': (0x9000, 0x9006), 'ssf2': (0x7C10, 0x7C16), 'ssf2t': (0x9000, 0x9006),
       'hsf2': (0x9000, 0x9006)}


def reg(L):
    return L if L < 0x8000 else L + 0x8000


class Pilote:
    def __init__(self, path, jeu):
        self.z = open(path, 'rb').read()
        a, self.t = HDR[jeu]
        self.n = (self.z[reg(a)] << 8) | self.z[reg(a) + 1]

    def o(self, L):
        return self.z[reg(L)]

    def cmd(self, c):
        c %= self.n
        p = reg(self.t + 4 * c)
        b, h, l, _ = self.z[p:p + 4]
        if self.t < 0x8000:
            b &= 0x0F          # v1.04 de SSF2 : drapeau $10 + banque
        return (b << 16) | (h << 8) | l

    def morceau(self, c):
        L = self.cmd(c)
        if not L:
            return None
        offs = [(self.o(L + 1 + 2 * k) << 8) | self.o(L + 2 + 2 * k) for k in range(16)]
        return dict(L=L, prio=self.o(L), pistes=[(k, L + v) for k, v in enumerate(offs) if v])
