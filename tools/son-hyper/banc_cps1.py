#!/usr/bin/env python3
"""Banc du pilote son CPS-1 (Z80 + YM2151 + OKI6295) : intro et boucle des morceaux, sans connaitre leur format.

Carte memoire (MAME cps1, sub_map) : 0000-7FFF ROM fixe, 8000-BFFF fenetre de banque (region 0x10000 + banque * 0x4000,
banque ecrite en F004), D000-D7FF RAM, F000/F001 YM2151 (registre / donnee, lecture F001 = etat), F002 OKI, F004 banque,
F006 broche 7 de l'OKI, F008 commande du 68K, F00A 2e latch (fondus). Z80 et YM2151 a 3,579545 MHz. Le Z80 est
interrompu par la sortie IRQ du YM2151 (timers A et B), qu'on emule ici : periode A = 64 x (1024 - TA) cycles,
periode B = 1024 x (256 - TB) cycles ; registre $14 : bits 0/1 chargement, 2/3 IRQ, 4/5 remise a zero des drapeaux.

Commande : le 68K laisse le code dans F008 ; le pilote compare a la valeur precedente.

Mesure : le pilote CPS-1 n'a pas l'opcode de boucle des pilotes CPS2, on ne pose donc pas de point de lecture. On releve
les notes de chaque voie FM (key-on, registre $08, avec le code de note $28-$2F de la voie) et on cherche, voie par voie,
la plus petite periode p (en notes) telle que la suite se repete a partir d'une note T. La duree de boucle est l'ecart
moyen entre une note et sa repetition (le tempo fractionnaire du pilote decale les notes d'un tick d'une boucle a
l'autre : on ne peut pas comparer tick par tick). Les voies sont decalees entre elles : boucle = mediane des voies,
debut de boucle = borne haute commune (plus petite premiere note periodique). Les percussions OKI ne sont pas utilisees.
Usage : banc_cps1.py image_z80.bin [codes hexa, ex. 01-3f] [--secondes 260] [--trace]
  image_z80.bin : region audiocpu MAME (fichier .09 : 0x0000-0x7FFF puis 0x10000-...), cf. image_z80.py --cps1
Dependances : paquets Python z80 et numpy.
"""
import sys
import numpy as np
import z80

HORLOGE = 3_579_545
TRANCHE = 64                  # cycles entre deux tests de l'IRQ


class YM:
    def __init__(self):
        self.reg = [0] * 256; self.adr = 0
        self.ta = self.tb = None      # cycles restants, None = arrete
        self.flags = 0
        self.ecrits = []              # (registre, valeur) depuis le dernier tick

    def per_a(self): return 64 * (1024 - ((self.reg[0x10] << 2) | (self.reg[0x11] & 3)))
    def per_b(self): return 1024 * (256 - self.reg[0x12])

    def ecrit(self, v):
        a = self.adr; self.reg[a] = v
        if a == 0x14:
            if v & 1:
                if self.ta is None: self.ta = self.per_a()
            else: self.ta = None
            if v & 2:
                if self.tb is None: self.tb = self.per_b()
            else: self.tb = None
            self.flags &= ~((v >> 4) & 3)
        elif a == 0x08 or a >= 0x20:
            self.ecrits.append((a, v))

    def avance(self, n):
        """Avance de n cycles ; rend le nombre de debordements (timers A et B sous IRQ)."""
        ticks = 0
        for t in ('ta', 'tb'):
            c = getattr(self, t)
            if c is None: continue
            c -= n
            while c <= 0:
                c += self.per_a() if t == 'ta' else self.per_b()
                bit = 1 if t == 'ta' else 2
                if self.reg[0x14] & (bit << 2):
                    self.flags |= bit; ticks += 1
            setattr(self, t, c)
        return ticks

    def irq(self): return bool(self.flags & (self.reg[0x14] >> 2) & 3)


class Banc:
    trace_defaut = False

    def __init__(self, image, trace=None):
        self.r = image; self.trace = self.trace_defaut if trace is None else trace
        self.m = m = z80.Z80Machine()
        m.set_memory_block(0, image[:0x8000])
        self.banque = -1; self.change_banque(0)
        self.ym = YM(); self.latch = 0xFF; self.latch2 = 0xFF
        self.oki = []
        m.set_read_callback(self.lit); m.set_write_callback(self.ecrit)
        m.mark_addrs(0xF000, 0x10, m.READ_MARK | m.WRITE_MARK)
        m.mark_addrs(0x0000, 0x8000, m.WRITE_MARK)      # ROM : ecritures ignorees
        self.cycles = 0; self.tick = 0; self.kc = [0] * 8
        self.notes = []                                 # (tick, voie, code de note) a chaque key-on

    def change_banque(self, b):
        nb = max(1, (len(self.r) - 0x10000) // 0x4000)
        b %= nb
        if b != self.banque:
            o = 0x10000 + b * 0x4000
            self.m.set_memory_block(0x8000, self.r[o:o + 0x4000]); self.banque = b

    def lit(self, a):
        if a == 0xF001: return self.ym.flags          # jamais occupe
        if a == 0xF008: return self.latch
        if a == 0xF00A: return self.latch2
        if a == 0xF002: return 0                       # OKI au repos
        if 0xF000 <= a < 0xF010: return 0xFF
        return self.m.memory[a]

    def ecrit(self, a, v):
        if a < 0x8000: return
        if a == 0xF000: self.ym.adr = v
        elif a == 0xF001:
            if self.trace and self.ym.adr in (0x10, 0x11, 0x12, 0x14):
                print('  %8.3f s  YM[%02x] = %02x' % (self.cycles / HORLOGE, self.ym.adr, v))
            self.ym.ecrit(v)
        elif a == 0xF002: self.ym.ecrits.append((0x100, v))
        elif a == 0xF004: self.change_banque(v)
        elif 0xF000 <= a < 0xF010: pass
        else: self.m.memory[a] = v

    def tourne(self, secondes):
        m, fin = self.m, self.cycles + int(secondes * HORLOGE)
        while self.cycles < fin:
            if self.ym.irq(): m.on_handle_active_int()
            m.ticks_to_stop = TRANCHE
            while True:
                m.run()
                if m.ticks_to_stop == 0: break
            self.cycles += TRANCHE
            n = self.ym.avance(TRANCHE)
            for _ in range(n):
                for a, v in self.ym.ecrits:
                    if 0x28 <= a < 0x30: self.kc[a - 0x28] = v
                    elif a == 0x08 and v & 0x78: self.notes.append((self.cycles, v & 7, self.kc[v & 7]))
                self.ym.ecrits = []; self.tick += 1


def boucle_voie(notes, min_rep=1.5):
    """(cycle de la 1re note periodique, cycle de la derniere note non periodique, boucle en cycles) ou None."""
    sym = [x for t, x in notes]; tt = np.array([t for t, x in notes]); n = len(sym)
    for p in range(1, n // 2):
        bad = [i for i in range(n - p) if sym[i] != sym[i + p]]
        T = bad[-1] + 1 if bad else 0
        if n - p - T >= min_rep * p and tt[n - 1] - tt[T] >= min_rep * (tt[T + p] - tt[T]):
            return int(tt[T]), (int(tt[T - 1]) if T else -1), float((tt[T + p:n] - tt[T:n - p]).mean())
    return None


def mesure(image, code, secondes):
    b = Banc(open(image, 'rb').read())
    b.tourne(1.0)                                    # initialisation du pilote
    t0 = b.cycles
    b.notes = []; b.latch = code
    b.tourne(secondes)
    if not b.notes: return None
    tick_s = 1 / HORLOGE
    voies = {}
    for t, v, x in b.notes: voies.setdefault(v, []).append((t - t0, x))
    res = {v: boucle_voie(e) for v, e in voies.items() if len(e) >= 8}
    ok = [r for r in res.values() if r]
    out = dict(voies=len(voies), periodiques=len(ok), tick=tick_s, intro=None, boucle=None,
               duree=(max(t for t, v, x in b.notes) - t0) * tick_s)
    if ok:
        out['boucle'] = float(np.median([r[2] for r in ok])) * tick_s
        out['intro'] = min(r[0] for r in ok) * tick_s       # borne haute du point de boucle
        out['intro_min'] = (max(r[1] for r in ok) + 1) * tick_s
    return out


def codes(txt):
    out = []
    for part in txt.split(','):
        a, _, b = part.partition('-'); out += range(int(a, 16), int(b or a, 16) + 1)
    return out


if __name__ == '__main__':
    image = sys.argv[1]
    lst = codes(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else range(1, 0x40)
    sec = float(sys.argv[sys.argv.index('--secondes') + 1]) if '--secondes' in sys.argv else 260
    trace = '--trace' in sys.argv
    if trace: Banc.trace_defaut = True
    print('code\tvoies\tvoies_bouclees\tintro_s\tboucle_s\tintro+boucle_s\tderniere_note_s')
    f = lambda x: '%.2f' % x if x is not None else '-'
    for c in lst:
        r = mesure(image, c, sec)
        if r is None: continue
        ib = r['intro'] + r['boucle'] if r['boucle'] is not None else None
        print('%04x\t%d\t%d\t%s\t%s\t%s\t%.2f' % (c, r['voies'], r['periodiques'], f(r['intro']), f(r['boucle']), f(ib),
              r['duree']), flush=True)
