#!/usr/bin/env python3
"""compare_variantes.py -- rapproche les flux d'Hyper des morceaux mesures (mesure_boucles.py / mesure_cps1.py).

Base : la duree d'un flux ADX vaut intro + une boucle (calibre sur ZERO / ZERO 2, voir mesure_boucles.py). On
compare la duree de chaque flux (tools/flux/hsfa_flux_table.txt) a l'intro + boucle des morceaux d'un jeu, avec une
affectation un pour un (scipy si present, sinon plus proche voisin sans unicite).

Jeux de variantes (PARTITIONS-HYPER §2) : A = Y553-586, B = Y494-527, C = Y460-493,
longs = Y433-439, Y528-529, Y543-552.
Usage : python3 compare_variantes.py resultats/mesures_ssf2.tsv [autres.tsv ...] [--sortie variantes.tsv]
"""
import os, re, sys

ICI = os.path.dirname(os.path.abspath(__file__))
TABLE = os.path.join(ICI, '..', '..', 'flux', 'hsfa_flux_table.txt')
JEUX = {'A': list(range(553, 587)), 'B': list(range(494, 528)), 'C': list(range(460, 494)),
        'longs': list(range(433, 440)) + [528, 529] + list(range(543, 553))}


def table_flux():
    t = {}
    for l in open(TABLE, encoding='utf-8'):
        m = re.match(r'([0-9A-F]{4}) (\d+) \d+ \S+\s+# (.*?) ; ([\d.]+) s', l)
        if m:
            t[int(m.group(2))] = (int(m.group(1), 16), float(m.group(4)))
    return t


def mesures(fic):
    nom = os.path.basename(fic).replace('mesures_', '').replace('.tsv', '')
    out = []
    for l in open(fic, encoding='utf-8').read().splitlines()[1:]:
        c = l.split('\t')
        if c[-2] != '-' and c[-1] != '-':
            out.append((nom, int(c[0], 16), float(c[-1])))
    return out


def affecte(cout):
    try:
        from scipy.optimize import linear_sum_assignment
        import numpy as np
        ri, ci = linear_sum_assignment(np.array(cout))
        return list(zip(ri, ci))
    except ImportError:
        return [(i, min(range(len(r)), key=r.__getitem__)) for i, r in enumerate(cout)]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    sortie = sys.argv[sys.argv.index('--sortie') + 1] if '--sortie' in sys.argv else None
    if sortie in args:
        args.remove(sortie)
    tab = table_flux()
    pool = [m for f in args for m in mesures(f)]
    lignes = ['jeu\tindex\tflux\tcode_hyper\tduree_flux_s\tsource\tcode_source\tintro+boucle_s\tecart_%\tposition']
    for nom, ys in JEUX.items():
        cout = [[abs(p[2] - tab[y][1]) / tab[y][1] for p in pool] for y in ys]
        paires = affecte(cout)
        e = [cout[i][j] * 100 for i, j in paires]
        print('jeu %-5s : %2d flux | <= 0,25 %% : %2d | <= 1 %% : %2d | <= 2 %% : %2d'
              % (nom, len(ys), sum(x <= .25 for x in e), sum(x <= 1 for x in e), sum(x <= 2 for x in e)))
        for i, j in paires:
            y, (src, c, d) = ys[i], pool[j]
            attendu = (0x01 + i if i < 16 else 0x11 + (i - 17)) if nom != 'longs' else -1
            lignes.append('%s\t%d\tY%d\t%04X\t%.1f\t%s\t%02X\t%.2f\t%.2f\t%s' % (
                nom, i, y, tab[y][0], tab[y][1], src, c, d, cout[i][j] * 100, 'oui' if c == attendu else ''))
    if sortie:
        open(sortie, 'w', encoding='utf-8').write('\n'.join(lignes) + '\n')


if __name__ == '__main__':
    main()
