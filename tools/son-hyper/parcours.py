"""Parcours statique des pistes v1.04 / v1.05 avec la grille d'opcodes de z80son.py (v1.71), 05 sur 2 octets."""
import os, sys, collections
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, '..', '..', 'src', 'hsfa')); sys.path.insert(0, ICI)
from z80son import ARGS as A71, SAUT
from pilote import Pilote
A10 = dict(A71); A10[5] = 2

def piste(p, L, args, limite=0x8000):
    vus, ops, pile, err = set(), [], [L], None
    while pile:
        a = pile.pop(); pas = 0
        while a not in vus:
            pas += 1
            if pas > limite: return vus, ops, 'trop long'
            try: op = p.o(a)
            except IndexError: return vus, ops, 'hors image %06x' % a
            if op >= 0x20: vus.add(a); a += 1; continue
            n = args[op]
            arg = [p.o(a + 1 + k) for k in range(n)]
            for k in range(n + 1): vus.add(a + k)
            ops.append((a, op, arg))
            if op in SAUT:
                rel = (arg[-2] << 8) | arg[-1]; rel -= 0x10000 if rel >= 0x8000 else 0
                cible = a + 1 + n + rel
                if op == 0x16: a = cible; continue
                pile.append(cible)
            if op == 0x17: break
            a += n + 1
    return vus, ops, err

if __name__ == '__main__':
    jeu, fic = sys.argv[1], sys.argv[2]
    p = Pilote(fic, jeu)
    hist, bilan = collections.Counter(), collections.Counter()
    tempos, instr = collections.Counter(), collections.Counter()
    for c in range(min(p.n, 0x80)):
        try: m = p.morceau(c)
        except IndexError: continue
        if not m or m['prio'] != 0 or len(m['pistes']) < 4: continue
        boucle = False
        for k, L in m['pistes']:
            vus, ops, err = piste(p, L, A10)
            bilan['erreur' if err else 'ok'] += 1
            if err: print('  %04x voie %d : %s' % (c, k, err))
            for a, op, arg in ops:
                hist[op] += 1
                if op == 5: tempos[(arg[0] << 8) | arg[1]] += 1
                if op in (8, 0x1f): instr[(op, arg[0])] += 1
                if op == 0x16: boucle = True
        bilan['morceaux'] += 1; bilan['morceaux en boucle'] += boucle
    print(jeu, dict(bilan))
    print('  opcodes :', ' '.join('%02x:%d' % kv for kv in sorted(hist.items())))
    print('  tempos 16 bits distincts :', len(tempos), sorted(tempos)[:12], '...')
    print('  instruments distincts (08/1F) :', len(instr))
