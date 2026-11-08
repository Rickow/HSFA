#!/usr/bin/env python3
"""(banc_coups) PALETTE GENERIQUE DE COMMANDES pour les persos sans ligne dans le tableau des coups (persos MAX Eagle,
Maki, Yun, Ingrid ; natifs d'Upper Guile, Fei-Long, Dee Jay, T. Hawk, Evil Ryu, Shin Akuma, Balrog EX).
Aucune liste de manips des persos MAX n'existe dans le depot (max/notes) ni dans ~/.cache/sfa3max : on joue toutes les
commandes classiques de la serie ; le banc releve lesquelles donnent un special ($6 = $0E) ou un super ($10) et leur
n° ($AA), ce qui tient lieu de liste de coups.

Usage : palette.py <plan> <index> <perso> [isme]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from notation import seq_motion_bouton, motion, jt

NB = {'1': 'LP', '2': 'MP', '3': 'HP', '4': 'LK', '5': 'MK', '6': 'HK'}
# (nom, manip en fleches ou mot-cle, boutons, drapeaux)
MANIPS = [
    ('quart avant', '↓↘→', 'P K'), ('quart arrière', '↓↙←', 'P K'), ('dragon', '→↓↘', 'P K'),
    ('dragon arrière', '←↓↙', 'P K'), ('demi-cercle avant', '←↙↓↘→', 'P K'), ('demi-cercle arrière', '→↘↓↙←', 'P K'),
    ('charge arrière-avant', '← (charge) →', 'P K'), ('charge bas-haut', '↓ (charge) ↑', 'P K'),
    ('360', '360°', 'P K'), ('avant-arrière-avant', '→←→', 'P'),
    ('double quart avant', '↓↘→↓↘→', 'P K'), ('double quart arrière', '↓↙←↓↙←', 'P K'),
    ('double demi-cercle arrière', '→↘↓↙←→↘↓↙←', 'P K'), ('charge ←→←→', '← (charge) →←→', 'P K'),
    ('charge ↙↘↙↗', '↙ (charge) ↘↙↗', 'P K'),
]
NORMAUX = [('debout', '', ['1', '2', '3', '4', '5', '6']), ('accroupi', 'D', ['1', '2', '3', '4', '5', '6']),
           ('avant +', 'F', ['2', '3', '5', '6']), ('arrière +', 'B', ['2', '3', '5', '6'])]


def essais():
    """liste de (nom, seq1, seq2, dist, type, obs)"""
    e = []
    for pos, d, bs in NORMAUX:
        for b in bs:
            s = ('6:%s 3:%s+%s 2:N' % (d, d, b)) if d else '3:%s 2:N' % b
            e.append(('normal %s %s' % (pos, NB[b]), s, '', 0x40, 'normal', ''))
    e.append(('saut avant + HK', '3:U+F 10:N 3:6 2:N', '', 0x60, 'normal', ''))
    e.append(('saut vertical + HP', '3:U 10:N 3:3 2:N', '', 0x60, 'normal', ''))
    for b in (('1', '2'), ('4', '5')):
        for dd in ('F', 'B'):
            e.append(('lancer %s + %s' % (dd, '+'.join(NB[x] for x in b)), '1:%s 3:%s+%s 2:N' % (dd, dd, '+'.join(b)), '',
                      0x20, 'lancer', '300'))
    for nom, m, bt in MANIPS:
        mot = motion(m)
        sup = nom.startswith('double') or '←→←→' in nom or '↘↙↗' in nom
        for g in bt.split():
            for b in (('1', '3') if g == 'P' else ('4', '6')):
                s = ' '.join(seq_motion_bouton(mot, [b]) + ['2:N'])
                e.append(('%s + %s' % (nom, NB[b]), s, '', 0x20 if '360' in nom else 0x60,
                          'super' if sup else 'special', '600' if sup else '200'))
    e.append(('provocation (Start)', '3:S 2:N', '', 0x60, 'special', ''))
    return e


def ecrit(plan, index, perso, ism=''):
    with open(plan, 'w') as fp, open(index, 'w') as fi:
        fi.write('id\tligne\tjeu\tperso\tism\ttype\tcoup\tvariante\tstatut\traison\tdrapeaux\n')
        for k, (nom, s1, s2, d, typ, obs) in enumerate(essais(), 1):
            tid = 'P%d' % k
            fp.write('T|%s|%x|90|%s|%s|%s|%s\n' % (tid, d, s1, s2, obs, nom))
            fi.write('\t'.join([tid, 'P%d' % k, 'palette', perso, ism, typ, nom, nom, 'TEST', '', 'palette']) + '\n')
    return k


if __name__ == '__main__':
    print(ecrit(*sys.argv[1:5]), 'essais')
