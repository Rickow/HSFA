#!/usr/bin/env python3
"""Compare les durees des flux d'Hyper (jeux A, B, C, longs) aux morceaux mesures au banc (CPS2 ou CPS-1).

Durees des flux : commentaires de tools/flux/hsfa_flux_table.txt (« ; 69.8 s boucle »), qui valent « intro + une
boucle » (calibrage SFA1 / SFA2 : 3 % pres pour 24 morceaux sur 32). Jeux de flux : colonnes jeu / index / flux de
variantes_ssf2.tsv. Mesures : TSV de mesure_boucles.py ou de banc_cps1.py (colonnes code et intro+boucle_s).

Association : un pour un dans chaque jeu de flux, gloutonne par ecart relatif croissant (ecart = |flux - morceau| /
morceau). Une duree seule est un indice faible : regarder la proportion de flux proches, pas une ligne isolee.
Usage : compare_durees.py hsfa_flux_table.txt variantes_ssf2.tsv mesures.tsv [--detail]
"""
import csv, sys


def durees_flux(table):
    out = {}
    for l in open(table, encoding='utf-8'):
        if l.startswith('#') or ';' not in l: continue
        y = int(l.split()[1])
        try: out[y] = float(l.split(';')[-1].split('s')[0])
        except ValueError: pass
    return out


def mesures(chemin):
    lignes = [l for l in open(chemin, encoding='utf-8') if l.strip() and not l.startswith('#')]
    out = {}
    for r in csv.DictReader(lignes, delimiter='\t'):
        if r.get('code') == 'code': continue                 # en-tete repete (fichiers concatenes)
        try: v = float(r['intro+boucle_s'])
        except (ValueError, TypeError): continue
        if r.get('boucle_s', '-') != '-' and v >= 5: out[r['code'][-2:].upper()] = v
    return out


def associe(flux, morceaux):
    paires = sorted((abs(d - v) / v * 100, y, c) for y, d in flux.items() for c, v in morceaux.items())
    pris, out = set(), {}
    for e, y, c in paires:
        if y in out or c in pris: continue
        out[y] = (c, e); pris.add(c)
    return out


def main():
    table, jeux, mes = sys.argv[1:4]
    detail = '--detail' in sys.argv
    d = durees_flux(table); m = mesures(mes)
    rows = list(csv.DictReader(open(jeux, encoding='utf-8'), delimiter='\t'))
    print('%d morceaux mesures (boucle trouvee, >= 5 s)' % len(m))
    print('jeu\tflux\t<=0.4%\t<=1%\t<=2.5%\t>5%')
    for jeu in ('A', 'B', 'C', 'longs'):
        r = [x for x in rows if x['jeu'] == jeu]
        flux = {int(x['flux'][1:]): d[int(x['flux'][1:])] for x in r}
        a = associe(flux, m); e = [a[y][1] for y in flux if y in a]
        print('%s\t%d\t%d\t%d\t%d\t%d' % (jeu, len(flux), sum(x <= .4 for x in e), sum(x <= 1 for x in e),
                                         sum(x <= 2.5 for x in e), sum(x > 5 for x in e)))
        if detail:
            for x in r:
                y = int(x['flux'][1:]); c, ec = a.get(y, ('-', float('nan')))
                print('  %s\tY%d\t%.1f s\t%s\t%s\t%.2f %%' % (x['index'], y, flux[y], c,
                      '%.2f' % m[c] if c in m else '-', ec))


if __name__ == '__main__':
    main()
