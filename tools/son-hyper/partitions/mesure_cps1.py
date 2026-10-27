#!/usr/bin/env python3
"""mesure_cps1.py -- intro et boucle des musiques d'un pilote son CPS-1 (Z80 + YM2151 + OKI), en faisant tourner le
pilote (paquet pip « z80 », facultatif). Teste sur Final Fight (pilote « version 2.00 », musiques 0x40-0x5F).

NON CALIBRE : aucun morceau CPS-1 n'a de flux connu pour verifier la methode (timers YM2151 emules, periode des
key-on). Les resultats servent de filtre, pas de preuve. Final Fight (pilote v2.00) : boucles stables et vraisemblables.
SF2 Hyper Fighting (pilote v4.25) : boucles de 70-157 s et intros de 40-50 s, invraisemblables -> NON FIABLE
(cadence ou variantes du pilote mal reproduites ; a revoir avant toute conclusion).

Carte memoire (MAME cps1, sub_map) : 0000-7FFF ROM fixe, 8000-BFFF banque (region 0x10000 + banque * 0x4000, banque
ecrite en F004), D000-D7FF RAM, F000/F001 YM2151 (adresse / donnee ; lecture F001 = etat), F002 OKI, F008 commande
du 68K (latch), F00A 2e latch. Z80 a 3,579545 MHz ; l'IRQ vient des timers A/B du YM2151 (registres 10-14).

Le pilote CPS-1 n'a pas la meme grille d'opcodes que le QSound : on ne cherche pas le saut de boucle, on mesure la
periode de la suite des key-on YM2151 (registre 08) et des declenchements OKI. Boucle = plus petite periode P
(>= 4 s) telle que la suite d'evenements se repete ; intro = premier instant a partir duquel elle se repete.
Image : image_z80.py. Usage : mesure_cps1.py image_z80.bin codes_hexa [--secondes 420]
"""
import sys
import z80

HORLOGE = 3_579_545
YM = 3_579_545


class Banc:
    def __init__(self, image):
        self.r = image
        self.m = m = z80.Z80Machine()
        m.set_memory_block(0, image[:0x8000])
        self.banque = -1; self.banque_w(0)
        self.ym_adr = 0; self.regs = [0] * 256
        self.ta = self.tb = 0.0        # compteurs en cycles Z80
        self.flags = 0
        self.latch = 0xFF; self.latch2 = 0xFF
        self.ev = []; self.t = 0       # (cycle, code)
        m.set_read_callback(self.lit); m.set_write_callback(self.ecrit)
        m.mark_addrs(0xF000, 0x10, m.READ_MARK | m.WRITE_MARK)

    def banque_w(self, b):
        b &= 0x0F
        if b != self.banque:
            o = 0x10000 + b * 0x4000
            blk = self.r[o:o + 0x4000]
            if len(blk) < 0x4000: blk = blk + bytes(0x4000 - len(blk))
            self.m.set_memory_block(0x8000, blk); self.banque = b

    def lit(self, a):
        if a == 0xF001: return self.flags & 3          # jamais occupe
        if a == 0xF008: return self.latch
        if a == 0xF00A: return self.latch2
        if a == 0xF002: return 0x00
        return 0xFF

    def ecrit(self, a, v):
        if a == 0xF000: self.ym_adr = v
        elif a == 0xF001:
            r = self.ym_adr; self.regs[r] = v
            if r == 0x08 and v & 0x78: self.ev.append((self.t, 0x100 | v))
            if r == 0x14:
                if v & 0x10: self.flags &= ~1
                if v & 0x20: self.flags &= ~2
        elif a == 0xF002:
            if v & 0x80: self.ev.append((self.t, 0x200 | (v & 0x7F)))
        elif a == 0xF004: self.banque_w(v)

    def periodes(self):
        na = (self.regs[0x10] << 2) | (self.regs[0x11] & 3)
        nb = self.regs[0x12]
        pa = 64 * (1024 - na) * HORLOGE / YM
        pb = 1024 * (256 - nb) * HORLOGE / YM
        return pa, pb

    def tourne(self, cycles):
        m = self.m; fin = self.t + cycles; attente = False
        while self.t < fin:
            pa, pb = self.periodes(); r14 = self.regs[0x14]
            prochain = []
            if r14 & 1: prochain.append(('a', pa - self.ta))
            if r14 & 2: prochain.append(('b', pb - self.tb))
            pas = min([max(1, int(d)) for _, d in prochain] + [2000, fin - self.t])
            if attente: pas = min(pas, 128)
            if attente and m.on_handle_active_int(): attente = False
            m.ticks_to_stop = pas
            while True:
                m.run()
                if m.ticks_to_stop == 0: break
            self.t += pas
            if r14 & 1:
                self.ta += pas
                if self.ta >= pa:
                    self.ta -= pa
                    if r14 & 4: self.flags |= 1; attente = True
            if r14 & 2:
                self.tb += pas
                if self.tb >= pb:
                    self.tb -= pb
                    if r14 & 8: self.flags |= 2; attente = True
            if self.flags and (r14 & 0x0C): attente = attente or (self.flags & ((r14 >> 2) & 3)) != 0


def boucle(ev, t0, duree, g=0.01, seuil=0.98):
    """periode de la suite des key-on, comparee par cases de g s (+-1 case), sans tenir compte de l'ordre d'ecriture
    dans une meme case. Boucle = plus petit decalage (>= 4 s) qui reproduit 98 % des evenements de la 2e partie ;
    intro = 1re fenetre de 2 s qui se retrouve une boucle plus loin. Renvoie (intro_s depuis la 1re note, boucle_s)."""
    import numpy as np
    ev = [((t - t0) / HORLOGE, c) for t, c in ev]
    return _per(ev, g, seuil, np)


def _per(ev, g, seuil, np):

    if len(ev) < 50: return None
    fin = max(t for t, _ in ev); n = int(fin / g) + 2
    codes = sorted(set(c for _, c in ev)); idx = {c: i for i, c in enumerate(codes)}
    X = np.zeros((len(codes), n), np.float32)
    for t, c in ev: X[idx[c], int(t / g)] = 1
    Xd = np.maximum(X, np.maximum(np.roll(X, 1, 1), np.roll(X, -1, 1)))
    deb = int(0.4 * n)
    lag = None
    for L in range(int(4 / g), n - deb - int(4 / g)):
        a = X[:, deb:n - L]; s = a.sum()
        if s and (a * Xd[:, deb + L:n]).sum() / s >= seuil: lag = L; break
    if lag is None: return None
    w = int(2 / g); first = min(tt for tt, _ in ev); t = int(first / g)
    while t + lag + w < n:
        a = X[:, t:t + w]; s = a.sum()
        if s and (a * Xd[:, t + lag:t + lag + w]).sum() / s >= seuil: break
        t += max(1, int(0.05 / g))
    first = min(tt for tt, _ in ev)
    return max(0.0, t * g - first), lag * g


def mesure(image, code, secondes, latence=0.0):
    b = Banc(open(image, 'rb').read())
    b.tourne(HORLOGE // 2)                       # demarrage du pilote
    b.ev.clear()
    b.latch = code; t0 = b.t
    b.tourne(HORLOGE // 20); b.latch = 0xFF      # commande tenue 50 ms
    b.tourne(int(secondes * HORLOGE))
    if len(b.ev) < 50: return dict(n=len(b.ev))
    debut = (b.ev[0][0] - t0) / HORLOGE
    r = boucle(b.ev, t0, secondes)
    if not r: return dict(n=len(b.ev), debut=debut)
    intro, P = r
    return dict(n=len(b.ev), debut=debut, intro=intro + latence, boucle=P)


if __name__ == '__main__':
    image = sys.argv[1]
    codes = []
    for part in sys.argv[2].split(','):
        a, _, z = part.partition('-'); codes += range(int(a, 16), int(z or a, 16) + 1)
    sec = float(sys.argv[sys.argv.index('--secondes') + 1]) if '--secondes' in sys.argv else 420
    print('code\tevenements\tintro_s\tboucle_s\tintro+boucle_s')
    for c in codes:
        r = mesure(image, c, sec)
        if 'boucle' in r:
            print('%02x\t%d\t%.2f\t%.2f\t%.2f' % (c, r['n'], r['intro'], r['boucle'], r['intro'] + r['boucle']), flush=True)
        else:
            print('%02x\t%d\t-\t-\t-' % (c, r['n']), flush=True)
