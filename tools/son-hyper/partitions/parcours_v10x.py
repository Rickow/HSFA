#!/usr/bin/env python3
"""parcours_v10x.py -- parcours statique des pistes de musique v1.04 / v1.05 avec la grille d'opcodes de v1.71.

Grille : src/hsfa/z80son.py (ARGS, SAUT : opcodes 00-1F, notes >= 20, 16 = saut, 17 = fin). Seule difference
mesuree : l'opcode 05 (tempo) prend 2 octets en v1.0x (1 en v1.71). Avec cette seule modification, 100 % des pistes
de musique se parcourent (sfa 597, sfa2 861, ssf2 812, ssf2t 811 : fin sur 17 ou boucle sur 16, sans debordement).

Usage : python3 parcours_v10x.py jeu image_z80.bin      -> bilan, histogramme des opcodes, tempos, instruments
"""
import os, sys, collections
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
sys.path.insert(0, os.path.join(ICI, '..', '..', '..', 'src', 'hsfa'))
from z80son import ARGS as A71, SAUT
from pilote_v10x import Pilote

A10 = dict(A71)
A10[5] = 2


def piste(p, L, args=A10, limite=0x8000):
    """renvoie (octets touches, [(adresse, opcode, arguments)], erreur ou None)"""
    vus, ops, pile = set(), [], [L]
    while pile:
        a = pile.pop(); pas = 0
        while a not in vus:
            pas += 1
            if pas > limite:
                return vus, ops, 'trop long'
            try:
                op = p.o(a)
            except IndexError:
                return vus, ops, 'hors image %06x' % a
            if op >= 0x20:
                vus.add(a); a += 1; continue
            n = args[op]
            arg = [p.o(a + 1 + k) for k in range(n)]
            for k in range(n + 1):
                vus.add(a + k)
            ops.append((a, op, arg))
            if op in SAUT:
                rel = (arg[-2] << 8) | arg[-1]
                rel -= 0x10000 if rel >= 0x8000 else 0
                cible = a + 1 + n + rel
                if op == 0x16:
                    a = cible; continue
                pile.append(cible)
            if op == 0x17:
                break
            a += n + 1
    return vus, ops, None


def musiques(p, maxc=0x80):
    for c in range(min(p.n, maxc)):
        try:
            m = p.morceau(c)
        except IndexError:
            continue
        if m and m['prio'] == 0 and len(m['pistes']) >= 4:
            yield c, m


if __name__ == '__main__':
    jeu, fic = sys.argv[1], sys.argv[2]
    p = Pilote(fic, jeu)
    hist, bilan, tempos, instr = (collections.Counter() for _ in range(4))
    for c, m in musiques(p):
        boucle = False
        for k, L in m['pistes']:
            _, ops, err = piste(p, L)
            bilan['erreur' if err else 'ok'] += 1
            if err:
                print('  %04x voie %d : %s' % (c, k, err))
            for a, op, arg in ops:
                hist[op] += 1
                if op == 5: tempos[(arg[0] << 8) | arg[1]] += 1
                if op in (8, 0x1f): instr[(op, arg[0])] += 1
                if op == 0x16: boucle = True
        bilan['morceaux'] += 1; bilan['morceaux en boucle'] += boucle
    print(jeu, dict(bilan))
    print('  opcodes :', ' '.join('%02x:%d' % kv for kv in sorted(hist.items())))
    print('  tempos 16 bits distincts :', len(tempos))
    print('  instruments distincts (08/1F) :', len(instr))
