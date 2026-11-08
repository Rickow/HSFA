#!/usr/bin/env python3
"""(banc_coups) RESUME-MAX.md d'un passage de banc_max.sh : resume_max.py resultats_max/<etiquette>
Classement des defauts : regression native (coups ou fins des natifs differents de la reference) = GRAVE ;
defaut MAX (persos MAX, croises, arcade MAX) = a transmettre a la session MAX."""
import csv, glob, os, sys, collections
R = sys.argv[1]
et = os.path.basename(R.rstrip('/'))
L = ['# Non-régression de l\'intégration MAX — candidat `%s`' % et, '',
     'Référence : Upper v150 (`references/v150/ro5`). Outil : `banc_max.sh` (détail des méthodes dans BANC-COUPS.md §7).', '']
graves, maxd, ralentis = [], [], []
# 1. coups des natifs
n, parp = collections.Counter(), collections.defaultdict(collections.Counter)
for f in sorted(glob.glob(os.path.join(R, 'coups_*.tsv'))):
    for r in csv.DictReader(open(f), delimiter='\t'):
        n[r['verdict']] += 1
        parp[r['etiquette']][r['verdict']] += 1
        if r['verdict'] == 'INSTABLE':
            ralentis.append('INSTABLE | %s | %s (%s) | %s' % (r['etiquette'], r['coup'], r['variante'], r['detail'][:110]))
        elif r['verdict'] == 'RALENTI':
            ralentis.append('%s | %s (%s) | %s' % (r['etiquette'], r['coup'], r['variante'], r['detail'][:90]))
        elif r['verdict'] != 'IDENTIQUE':
            graves.append('coups natifs | %s | %s (%s) | %s : %s' % (r['etiquette'], r['coup'], r['variante'], r['verdict'], r['detail']))
L += ['## 1. Coups des natifs (candidat contre référence, image par image)', '',
      'Variantes : ' + ', '.join('%s %d' % kv for kv in sorted(n.items())) + ' ; travaux : %d' % len(parp), '']
pas_ok = [(k, c) for k, c in parp.items() if set(c) - {'IDENTIQUE'}]
if pas_ok:
    L += ['| perso isme | ' + ' | '.join(sorted(n)) + ' |', '|---' * (len(n) + 1) + '|']
    for k, c in pas_ok:
        L.append('| %s | %s |' % (k, ' | '.join(str(c[x]) for x in sorted(n))))
    L.append('')
# 2. fins
f = os.path.join(R, 'fins.tsv')
if os.path.exists(f):
    rows = list(csv.DictReader(open(f), delimiter='\t'))
    c = collections.Counter(r['verdict'] for r in rows)
    L += ['## 2. Fins d\'Arcade des natifs', '', ', '.join('%s %d' % kv for kv in sorted(c.items())) + ' (sur %d persos)' % len(rows), '']
    for r in rows:
        if r['verdict'] != 'OK':
            graves.append('fin native | $%s | %s : %s' % (r['perso'], r['verdict'], r['detail']))
# 3. persos MAX
n3 = collections.Counter(); sp = collections.defaultdict(list)
for f in sorted(glob.glob(os.path.join(R, 'max_*.tsv'))):
    nom = os.path.basename(f)[4:-4]
    for r in csv.DictReader(open(f), delimiter='\t'):
        n3[r['verdict']] += 1
        if r['verdict'] == 'KO':
            maxd.append('coup MAX | %s | %s : %s' % (nom, r['variante'], r['cause']))
        if r['verdict'] == 'OK' and r['type'] in ('special', 'super'):
            sp[nom].append(r['variante'])
if n3:
    L += ['## 3. Persos MAX : palette de commandes (sort, rend la main, sans exception)', '',
          ', '.join('%s %d' % kv for kv in sorted(n3.items())), '',
          'Commandes qui donnent un spécial ou un super (liste de fait, faute de liste de manips MAX) :', '']
    for k, v in sp.items():
        L.append('- %s : %s' % (k, ', '.join(v)))
    L.append('')
# 4. croises
f = os.path.join(R, 'croises.tsv')
if os.path.exists(f):
    rows = list(csv.DictReader(open(f), delimiter='\t'))
    c = collections.Counter(r['verdict'] for r in rows)
    L += ['## 4. Croisés MAX contre natifs (VERSUS, entrées aléatoires des deux joueurs)', '',
          ', '.join('%s %d' % kv for kv in sorted(c.items())) + ' (sur %d)' % len(rows), '']
    for r in rows:
        if r['verdict'] != 'OK':
            maxd.append('croisé | %s contre %s (%s) | %s' % (r['max'], r['natif'], r['sens'], r['detail']))
# 5. arcade
f = os.path.join(R, 'arcade.tsv')
if os.path.exists(f):
    rows = list(csv.DictReader(open(f), delimiter='\t'))
    L += ['## 5. Arcade complète des persos MAX', '', '| perso | verdict | détail |', '|---|---|---|']
    for r in rows:
        L.append('| %s | %s | %s |' % (r['max'], r['verdict'], r['detail']))
        if r['verdict'] != 'OK':
            maxd.append('arcade MAX | %s | %s' % (r['max'], r['detail']))
    L.append('')
L += ['## Défauts', '', '### Régressions natives (GRAVE) : %d' % len(graves), '']
L += ['- ' + g for g in graves[:200]] or ['- aucune']
L += ['', '### Ralentissements (même jeu tour par tour) et essais INSTABLES (non reproductibles) des natifs : %d' % len(ralentis), '']
L += ['- ' + g for g in ralentis[:100]] or ['- aucun']
L += ['', '### Défauts MAX (à transmettre) : %d' % len(maxd), '']
L += ['- ' + g for g in maxd[:200]] or ['- aucun']
an = os.path.join(R, 'ANALYSES.md')
if os.path.exists(an):
    L += ['', open(an).read()]
open(os.path.join(R, 'RESUME-MAX.md'), 'w').write('\n'.join(L) + '\n')
print('RÉSUMÉ %s : natifs %s ; régressions natives %d ; défauts MAX %d' % (et, dict(n), len(graves), len(maxd)))
