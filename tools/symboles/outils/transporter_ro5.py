#!/usr/bin/env python3
"""ESQUISSE : transporte symboles_ro3.csv vers Upper (ro5) par les homologues de work/carto_ro5/.

 - fonctions / étiquettes : fonction ro3 englobante -> partenaire ro5 (appariement_ro3_ro5.json) ; un point
   interne n'est transporté que si les deux fonctions ont la même taille (décalage conservé) ;
 - variables A5 : décalages de zone de a5_ro3_ro5.json (numérotation MIPS) ; le reste est inchangé ;
 - champs : inchangés sauf ceux que a5_ro3_ro5.json['A6'] déplace ;
 - registres matériels / constantes de la plateforme : recopiés ; tables de données : non transportées.
La colonne « arcade » garde l'adresse de l'HOMOLOGUE SFA3 (Upper n'a pas de ROM arcade).
Sortie : symboles_ro5_esquisse.csv (puis annoter.py --csv ... --carte work/mame_ro5/carte_image.txt)."""
import sys, os, csv, json, bisect, struct, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fonctions as F
ICI = os.path.dirname(os.path.abspath(__file__)); RAC = os.path.join(ICI, '..')
C5 = '<workspace>/work/carto_ro5'
CARTE5 = '<workspace>/work/mame_ro5/carte_image.txt'
ORDRE = {'sûr': 3, 'probable': 2, 'hypothèse': 1}

def num(s):
    s = (s or '').strip()
    try:
        if s.startswith('+$'): return int(s[2:], 16)
        if s.startswith('$'): return int(s[1:], 16)
        if s.lower().startswith('0x'): return int(s, 16)
    except ValueError: pass
    return None

def main():
    S = list(csv.DictReader(open(os.path.join(RAC, 'symboles_ro3.csv'), encoding='utf-8'), delimiter=';'))
    app = {int(k, 16): v for k, v in json.load(open(os.path.join(C5, 'appariement_ro3_ro5.json'))).items()}
    a5j = json.load(open(os.path.join(C5, 'a5_ro3_ro5.json')))
    dep = {int(k, 16): int(v['ro5'], 16) for k, v in a5j['A5']['deplaces'].items() if v['votes'] >= 2 and v['votes'] >= 0.6 * v['total']}
    dep6 = {int(k, 16): int(v['ro5'], 16) for k, v in a5j.get('A6', {}).get('deplaces', {}).items() if v['votes'] >= 2}
    starts3 = sorted(app)
    vas5 = []; va2t5 = {}
    for l in open(CARTE5):
        p = l.split(' ', 2)
        try: t, va = int(p[0], 16), int(p[1], 16)
        except (ValueError, IndexError): continue
        va2t5.setdefault(va, t)
    vas5 = sorted(va2t5)
    def trad5(m):
        i = bisect.bisect_left(vas5, m)
        return va2t5[vas5[i]] if i < len(vas5) and vas5[i] - m <= 0x80 else None
    out = []; n = {'fonctions': 0, 'perdues': 0, 'a5': 0, 'champs': 0}
    for r in S:
        ty = r['type']; r5 = dict(r)
        if ty in ('fonction', 'étiquette'):
            if r['mips'].startswith('moteur'):
                out.append(r5); continue
            m = num(r['mips'])
            if m is None: n['perdues'] += 1; continue
            k = bisect.bisect_right(starts3, m) - 1
            if k < 0: n['perdues'] += 1; continue
            s3 = starts3[k]; p = app[s3]; off = m - s3
            if off and p.get('taille3') != p.get('taille5'): n['perdues'] += 1; continue
            if off >= p.get('taille3', 0) and off: n['perdues'] += 1; continue
            m5 = int(p['ro5'], 16) + off
            t5 = trad5(m5)
            r5['mips'] = '0x%X' % m5; r5['trad'] = '$%06X' % t5 if t5 is not None else ''
            if p['score'] < 0.9 and ORDRE.get(r['confiance'], 0) > 2: r5['confiance'] = 'probable'
            r5['source'] = r['source'] + ' + ro3 0x%X (%s, score %.2f)' % (m, p['type'], p['score'])
            n['fonctions'] += 1
        elif ty == 'variable A5':
            t3 = num(r['trad']); p3 = num(r['mips'])
            if t3 is None or p3 is None or not (0x900000 <= p3 < 0x910000): n['perdues'] += 1; continue
            d3 = (p3 - 0x908000) & 0xffff
            d5 = dep.get(d3, d3)
            if (d5 - d3) & 0xffff:
                r5['source'] = r['source'] + ' + a5_ro3_ro5.json (A5 %04X -> %04X)' % (d3, d5)
            delta = (d5 - d3) & 0xffff
            r5['mips'] = '0x%X' % (0xA08000 + ((d5 + 0x8000) & 0xffff) - 0x8000)
            r5['trad'] = '$%06X' % (0xFF0000 + ((t3 - 0xFF0000 + delta) & 0xffff))
            n['a5'] += 1
        elif ty in ('champ joueur', 'champ objet'):
            a = num(r['arcade'])
            if a in dep6:
                r5['source'] = r['source'] + ' + champ déplacé dans ro5 ($%X -> $%X)' % (a, dep6[a])
                r5['trad'] = '+$%X' % (dep6[a] ^ (num(r['trad']) ^ a))
                r5['mips'] = '+$%X' % dep6[a]
            n['champs'] += 1
        elif ty in ('registre matériel', 'constante', 'variable portage'):
            pass
        else:
            continue
        out.append(r5)
    with open(os.path.join(RAC, 'symboles_ro5_esquisse.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(S[0].keys()), delimiter=';', lineterminator='\n')
        w.writeheader(); w.writerows(out)
    print('ro5 : %d symboles (fonctions %d, A5 %d, champs %d) ; non transportés %d' % (
        len(out), n['fonctions'], n['a5'], n['champs'], n['perdues']))

if __name__ == '__main__':
    main()
