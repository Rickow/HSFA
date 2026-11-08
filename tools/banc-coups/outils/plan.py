#!/usr/bin/env python3
"""(banc_coups) PLAN D'ESSAIS : lignes du tableau des coups pour un jeu, un perso et un isme / une version ->
fichier de plan (lu par lua/banc_coups.lua) + index (TSV : id, ligne du CSV, coup, variante, statut).

Usage : plan.py --jeu "Street Fighter Alpha 3" --perso Ryu [--ism A] --plan p.txt --index i.tsv
Lignes « Tous » retenues pour chaque perso : Alpha Counter (A / V), lancer générique (si le perso n'a aucun lancer
propre), activation du Variable Combo (V).
"""
import argparse, csv, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from notation import variantes, NonTestable

CSV = '<workspace>/work/guide_coups/coups_sfa_anthology.csv'
TYPES_TEST = ('special', 'super', 'lancer', 'alpha counter')
# ids $102 des persos de SFA3 / Upper (HANDOFF §51)
IDS_SFA3 = {'Ryu': 0x00, 'Ken': 0x01, 'Akuma': 0x02, 'Charlie': 0x03, 'Chun-Li': 0x04, 'Adon': 0x05, 'Sodom': 0x06,
            'Guy': 0x07, 'Birdie': 0x08, 'Rose': 0x09, 'M. Bison': 0x0A, 'Sagat': 0x0B, 'Dan': 0x0C, 'Sakura': 0x0D,
            'Rolento': 0x0E, 'Dhalsim': 0x0F, 'Zangief': 0x10, 'Gen': 0x11, 'Balrog': 0x15, 'Cammy': 0x16,
            'Evil Ryu': 0x17, 'E. Honda': 0x18, 'Blanka': 0x19, 'R. Mika': 0x1A, 'Cody': 0x1B, 'Vega': 0x1C,
            'Karin': 0x1D, 'Juli': 0x1E, 'Juni': 0x1F, 'Guile': 0x20, 'Fei-Long': 0x21, 'Dee Jay': 0x22,
            'T. Hawk': 0x23, 'Shin Akuma': 0x24}
NOMS_CSV = {'M.Bison': 'M. Bison', 'Bison': 'M. Bison', 'Fei Long': 'Fei-Long', 'E.Honda': 'E. Honda',
            'R.Mika': 'R. Mika', 'T.Hawk': 'T. Hawk', 'DeeJay': 'Dee Jay'}
ISM_NOM = {'X': 'X-ISM', 'A': 'A-ISM', 'V': 'V-ISM'}


def lignes():
    with open(CSV, encoding='utf-8') as f:
        for i, r in enumerate(csv.DictReader(f, delimiter=';'), 2):
            r['_ligne'] = i
            r['personnage'] = NOMS_CSV.get(r['personnage'], r['personnage'])
            yield r


def ism_ok(r, ism):
    vs = r['version_style']
    if ism is None or 'ISM' not in vs:
        return True
    return ISM_NOM[ism] in vs


def selection(jeu, perso, ism=None, style=None):
    """lignes du jeu pour le perso (+ lignes « Tous » utiles) ; style = filtre libre sur version_style (SFA2)"""
    tout = [r for r in lignes() if r['jeu'] == jeu]
    propres = [r for r in tout if r['personnage'] == perso]
    a_lancer = any(r['type'] == 'lancer' for r in propres)
    a_ac = any(r['type'] == 'alpha counter' for r in propres)
    res = []
    for r in tout:
        if r['personnage'] == perso:
            if not ism_ok(r, ism):
                continue
            if style and r['version_style'] and 'ISM' not in r['version_style'] and style not in r['version_style']:
                continue
            res.append(r)
        elif r['personnage'] == 'Tous':
            n = r['nom_du_coup']
            if r['type'] == 'alpha counter' and not a_ac and ism_ok(r, ism):
                res.append(r)
            elif r['type'] == 'lancer' and not a_lancer and 'générique' in n:
                res.append(r)
            elif n.startswith('Variable Combo VC') and ism == 'V':
                res.append(r)
    return res


def ecrit(rows, plan, index, ism=None, jeu='', perso=None):
    np = 0
    with open(plan, 'w') as fp, open(index, 'w') as fi:
        fi.write('id\tligne\tjeu\tperso\tism\ttype\tcoup\tvariante\tstatut\traison\tdrapeaux\n')
        for r in rows:
            v = variantes(r, ism)
            base = 'L%d' % r['_ligne']
            qui = perso if (perso and r['personnage'] == 'Tous') else r['personnage']
            com = [base, str(r['_ligne']), r['jeu'] or jeu, qui, ism or '', r['type'], r['nom_du_coup']]
            if isinstance(v, NonTestable):
                fi.write('\t'.join(com + ['', 'NT', v.raison, '']) + '\n')
                continue
            for k, x in enumerate(v):
                tid = '%s.%d' % (base, k + 1)
                obs = '300' if r['type'] in ('super', 'lancer') else ''   # supers et prises longs : 300 images
                fp.write('T|%s|%x|%x|%s|%s|%s|%s\n' % (tid, x.dist, x.jauge, x.seq1, x.seq2, obs, x.nom.replace('|', '/')))
                fi.write('\t'.join([tid] + com[1:] + [x.nom, 'TEST', '', ','.join(x.drap)]) + '\n')
                np += 1
    return np


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--jeu', required=True)
    ap.add_argument('--perso', required=True)
    ap.add_argument('--ism')
    ap.add_argument('--style')
    ap.add_argument('--plan', required=True)
    ap.add_argument('--index', required=True)
    a = ap.parse_args()
    rows = selection(a.jeu, a.perso, a.ism, a.style)
    n = ecrit(rows, a.plan, a.index, a.ism, a.jeu, a.perso)
    print('%d lignes, %d essais' % (len(rows), n))
