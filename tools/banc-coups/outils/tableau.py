#!/usr/bin/env python3
"""(banc_coups) TABLEAUX ET RESUME a partir de resultats/<module>/*.tsv (une ligne par variante) :
  resultats/variantes_<module>.tsv  toutes les variantes ;
  resultats/coups_<module>.tsv      une ligne par coup du tableau (ligne du CSV) et par isme / version :
                                    OK si toutes les variantes jouees sont OK (variantes NC tolerees, signalees),
                                    KO si une variante est KO (cause de la premiere, nombre), NC si toutes NC, NT ;
  resultats/RESUME.md               taux de reussite par module, par perso et par version.
Taux = OK / (OK + KO) ; NC (ne sort pas a l'arcade non plus / aucun effet) et NT (non testable) a part.
"""
import csv, glob, os, collections
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(B, 'resultats')


def agrege(vs):
    v = [x['verdict'] for x in vs]
    if all(x == 'NT' for x in v):
        return 'NT', vs[0]['cause'], ''
    ko = [x for x in vs if x['verdict'] == 'KO']
    ok = [x for x in vs if x['verdict'].startswith('OK')]
    dec = [x for x in vs if x['verdict'] == 'DÉCALÉ']
    nc = [x for x in vs if x['verdict'] == 'NC']
    if ko:
        return 'KO', ko[0]['cause'], '%d/%d variantes KO (%s)' % (len(ko), len(vs), ', '.join(x['variante'] for x in ko[:4]))
    if dec:
        return 'DÉCALÉ', dec[0]['cause'], '%d/%d variantes décalées (%s)' % (len(dec), len(vs), ', '.join(x['variante'] for x in dec[:4]))
    if ok:
        return 'OK', '', ('%d variantes NC : %s' % (len(nc), ', '.join(x['variante'] for x in nc[:3]))) if nc else ''
    return 'NC', nc[0]['cause'] if nc else '', ''


def main():
    resume = ['# Banc des coups — résumé des taux de réussite', '',
              'Taux = OK / (OK + DÉCALÉ + KO), par coup du tableau (toutes variantes de boutons / directions agrégées). '
              'DÉCALÉ = même suite d\'états, mêmes dégâts et objets que l\'arcade, mais une réaction arrive une image plus tôt / tard. '
              'NC = le coup ne sort pas à l\'arcade non plus (manip ou condition du guide à revoir) ou n\'a aucun effet '
              'mesurable ; NT = non testable par le banc (combo, enchaînement, condition de jeu).', '']
    for mod in sorted(os.listdir(R)):
        d = os.path.join(R, mod)
        if not os.path.isdir(d):
            continue
        lignes = []
        for f in sorted(glob.glob(os.path.join(d, '*.tsv'))):
            ver = os.path.basename(f)[:-4].rsplit('_', 1)[1]
            for x in csv.DictReader(open(f), delimiter='\t'):
                x['version'] = ver
                lignes.append(x)
        if not lignes:
            continue
        cols = ['module', 'version', 'id', 'ligne', 'jeu', 'perso', 'type', 'coup', 'variante', 'verdict', 'cause', 'detail']
        with open(os.path.join(R, 'variantes_%s.tsv' % mod), 'w') as fo:
            fo.write('\t'.join(cols) + '\n')
            for x in lignes:
                fo.write('\t'.join(x.get(c, '') for c in cols) + '\n')
        g = collections.OrderedDict()
        for x in lignes:
            g.setdefault((x['perso'], x['version'], x['ligne']), []).append(x)
        coups = []
        for (perso, ver, ligne), vs in g.items():
            v, c, d = agrege(vs)
            coups.append({'module': mod, 'perso': perso, 'version': ver, 'ligne': ligne, 'jeu': vs[0]['jeu'],
                          'type': vs[0]['type'], 'coup': vs[0]['coup'], 'verdict': v, 'cause': c, 'detail': d})
        cols = ['module', 'perso', 'version', 'ligne', 'jeu', 'type', 'coup', 'verdict', 'cause', 'detail']
        with open(os.path.join(R, 'coups_%s.tsv' % mod), 'w') as fo:
            fo.write('\t'.join(cols) + '\n')
            for x in coups:
                fo.write('\t'.join(x[c] for c in cols) + '\n')
        n = collections.Counter(x['verdict'] for x in coups)
        taux = lambda c: '%.1f %%' % (100.0 * c['OK'] / (c['OK'] + c['KO'] + c['DÉCALÉ'])) if c['OK'] + c['KO'] + c['DÉCALÉ'] else '—'
        resume += ['## Module %s' % mod, '',
                   'Coups : %d OK, %d DÉCALÉ, %d KO, %d NC, %d NT — taux %s (variantes : %s)' % (
                       n['OK'], n['DÉCALÉ'], n['KO'], n['NC'], n['NT'], taux(n),
                       ', '.join('%s %d' % kv for kv in sorted(collections.Counter(x['verdict'] for x in lignes).items()))), '',
                   '| perso | version | OK | DÉCALÉ | KO | NC | NT | taux |', '|---|---|---|---|---|---|---|---|']
        pp = collections.OrderedDict()
        for x in coups:
            pp.setdefault((x['perso'], x['version']), collections.Counter())[x['verdict']] += 1
        for (p, v), c in pp.items():
            resume.append('| %s | %s | %d | %d | %d | %d | %d | %s |' % (p, v, c['OK'], c['DÉCALÉ'], c['KO'], c['NC'], c['NT'], taux(c)))
        causes = collections.Counter(x['cause'].split(' (')[0].split(' :')[0] for x in coups if x['verdict'] == 'KO')
        if causes:
            resume += ['', 'Causes des KO : ' + ' ; '.join('%s (%d)' % kv for kv in causes.most_common())]
        resume.append('')
    open(os.path.join(R, 'RESUME.md'), 'w').write('\n'.join(resume) + '\n')
    print('\n'.join(l for l in resume if l.startswith('Coups') or l.startswith('## ')))


if __name__ == '__main__':
    main()
