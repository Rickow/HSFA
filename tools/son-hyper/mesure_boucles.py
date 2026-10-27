#!/usr/bin/env python3
"""Mesure intro et boucle des morceaux d'un pilote Z80 CPS2 (v1.04 / v1.05) en faisant tourner le pilote lui-meme.

Carte memoire (MAME cps2) : 0000-7FFF ROM fixe, 8000-BFFF fenetre de banque (region 0x10000 + banque * 0x4000,
banque ecrite en D003), C000-CFFF RAM partagee avec le 68K, D000-D002 QSound (donnee haute, basse, registre),
D007 etat QSound (pret = 0x80), F000-FFFF RAM. IRQ a 250 Hz, Z80 a 8 MHz.
Commande : CFFF = 0xFF (depart), CFFD = 0x88 (68K pret), C000 = code haut, C001 = code bas, C00F != 0xFF (poste ; le Z80 remet 0xFF).

Mesure : on pose un point de lecture sur l'opcode 16 (saut de boucle) de chaque piste du morceau. Le 1er passage
donne la fin de la 1re boucle (intro + boucle), l'ecart entre deux passages donne la boucle.
Usage : mesure_boucles.py jeu image_z80.bin [codes hexa, ex. 01-0c,32] [--secondes 400]
Dependance : paquet Python `z80` (pip install z80), emulateur Z80 utilise comme banc.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[0])))
import z80
from pilote import Pilote, reg
from parcours import piste, A10

HZ_IRQ, HORLOGE = 250, 8_000_000
PAS = HORLOGE // HZ_IRQ


class Banc:
    def __init__(self, image):
        self.r = image
        self.m = m = z80.Z80Machine()
        m.set_memory_block(0, image[:0x8000])
        self.banque = -1; self.change_banque(0)
        self.points = {}          # adresse Z80 -> liste de (banque ou None, cle)
        self.hits = {}
        m.set_read_callback(self.lit)
        m.set_write_callback(self.ecrit)
        m.mark_addrs(0xD000, 8, m.READ_MARK | m.WRITE_MARK)
        self.t = 0

    def change_banque(self, b):
        b &= 0x0F
        if b != self.banque:
            o = 0x10000 + b * 0x4000
            self.m.set_memory_block(0x8000, self.r[o:o + 0x4000]); self.banque = b

    def lit(self, a):
        if a == 0xD007: return 0x80
        if 0xD000 <= a < 0xD008: return 0
        for b, cle in self.points.get(a, ()):
            if b is None or b == self.banque:
                self.hits.setdefault(cle, []).append(self.t)
        return self.m.memory[a]

    def ecrit(self, a, v):
        if a == 0xD003: self.change_banque(v)
        elif 0xD000 <= a < 0xD008: pass
        else: self.m.memory[a] = v

    def point(self, L, cle):
        if L < 0x8000: za, b = L, None
        else: za, b = 0x8000 + (L & 0x3FFF), (L >> 14) - 2
        self.points.setdefault(za, []).append((b, cle))
        self.m.mark_addr(za, self.m.READ_MARK)

    def tourne(self, n_irq):
        """IRQ maintenue jusqu'a sa prise en compte (HOLD_LINE de MAME) : on retente par tranches de 256 cycles."""
        m = self.m
        for _ in range(n_irq):
            reste, attente = PAS, True
            while reste > 0:
                if attente and m.on_handle_active_int(): attente = False
                q = min(256 if attente else reste, reste)
                m.ticks_to_stop = q
                while True:
                    m.run()
                    if m.ticks_to_stop == 0: break
                reste -= q
            self.t += 1


def mesure(jeu, image, code, secondes):
    p = Pilote(image, jeu)
    mo = p.morceau(code)
    if not mo or mo['prio'] != 0 or not mo['pistes']: return None
    banc = Banc(open(image, 'rb').read())
    sauts = 0
    for k, L in mo['pistes']:
        _, ops, _ = piste(p, L, A10)
        for a, op, arg in ops:
            if op == 0x16: banc.point(a, k); sauts += 1
    mem = banc.m.memory
    banc.tourne(HZ_IRQ // 10)                 # demarrage : le Z80 ecrit 0x77 en CFFF et attend le 68K
    mem[0xCFFD] = 0x88; mem[0xCFFF] = 0xFF; mem[0xC00F] = 0xFF   # signaux du 68K ; boite aux lettres vide
    banc.tourne(HZ_IRQ)                       # initialisation du pilote (1 s)
    mem[0xC000] = code >> 8; mem[0xC001] = code & 0xFF; mem[0xC00F] = 0
    t0 = banc.t
    banc.tourne(int(secondes * HZ_IRQ))
    if not sauts: return dict(boucle=None, fin=None, pistes=len(mo['pistes']))
    premiers, boucles = [], []
    for k, ts in banc.hits.items():
        ts = sorted(set(ts))
        if ts: premiers.append((ts[0] - t0) / HZ_IRQ)
        if len(ts) >= 2: boucles.append((ts[1] - ts[0]) / HZ_IRQ)
    if not premiers: return dict(boucle=None, fin=None, pistes=len(mo['pistes']))
    fin = max(premiers); b = max(boucles) if boucles else None
    return dict(fin=fin, boucle=b, intro=(fin - b) if b else None, pistes=len(mo['pistes']))


def codes(txt):
    out = []
    for part in txt.split(','):
        a, _, b = part.partition('-'); out += range(int(a, 16), int(b or a, 16) + 1)
    return out


if __name__ == '__main__':
    jeu, image = sys.argv[1], sys.argv[2]
    lst = codes(sys.argv[3]) if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else range(1, 0x40)
    sec = float(sys.argv[sys.argv.index('--secondes') + 1]) if '--secondes' in sys.argv else 400
    print('code\tvoies\tintro_s\tboucle_s\tintro+boucle_s')
    for c in lst:
        r = mesure(jeu, image, c, sec)
        if r is None: continue
        f = lambda x: '%.2f' % x if x is not None else '-'
        print('%04x\t%d\t%s\t%s\t%s' % (c, r['pistes'], f(r.get('intro')), f(r['boucle']), f(r['fin'])), flush=True)
