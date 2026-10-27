#!/usr/bin/env python3
"""tableau_fins.py [PREFIXE=f5] : tableau du balayage des fins (traces/<prefixe>_<perso>_<version>/journal.txt) contre
les durees d'Upper (donnees/fins_upper.tsv)."""
import sys, os, glob, re
G = '<workspace>/work/greffe_arcade'; P = sys.argv[1] if len(sys.argv) > 1 else 'f5'
U = {}
for l in open(os.path.join(G, 'donnees/fins_upper.tsv')):
    x = l.split('\t')
    if x[0] != 'perso' and x[3].strip() != '-': U[x[0]] = int(x[3])
rows = []
for d in sorted(glob.glob(os.path.join(G, 'traces', P + '_*_*'))):
    j = os.path.join(d, 'journal.txt')
    if not os.path.isdir(d) or not os.path.exists(j): continue
    _, p, v = os.path.basename(d).split('_', 2)
    t = open(j).read()
    a = re.search(r'SCENE_A (\d+)', t); f = re.search(r'FIN_A (\d+) duree (\d+) scene (\w+)', t)
    e = re.search(r'EXCEPTION (\d+) pc=(\w+) sp=\w+ pile=(.*)', t); b = re.search(r'BLOQUE (\d+)', t)
    m = re.findall(r'MANCHE (\d+) image \d+ J1 (\w+)/(\w+)/(\w+)', t)
    ids = '/'.join(m[0][1:]) if m else '-'
    if f: st = 'aboutie'; dur = int(f.group(2))
    elif e: st = 'EXCEPTION %s (%s)' % (e.group(1), 'pendant la fin' if a else 'avant la fin'); dur = None
    elif b: st = 'BLOQUE %s' % b.group(1); dur = None
    elif not re.search(r'^FIN ', t, re.M): st = 'en cours'; dur = None
    else: st = 'fin non atteinte'; dur = None
    VC = {'Z3': '10', 'Z': '01', 'Z2': '22', 'A': '06'}
    if m and (m[0][2] != p or m[0][3] != VC.get(v)): st = 'non sélectionnable (partie de %s)' % ids; dur = None
    up = U.get(p)
    ec = ('%+.1f %%' % (100.0 * (dur - up) / up)) if dur and up else '-'
    rows.append((p, v, ids, a.group(1) if a else '-', dur or '-', up or '-', ec, st, (e.group(2) + ' ' + e.group(3)) if e else ''))
print('| perso | version | ids J1 | début A | durée | Upper | écart | état | détail |')
print('|---|---|---|---|---|---|---|---|---|')
for r in rows: print('| ' + ' | '.join(str(x) for x in r) + ' |')
ok = sum(1 for r in rows if r[7] == 'aboutie'); ns = sum(1 for r in rows if r[7].startswith('non s'))
print('\n%d parties, %d combinaisons non selectionnables, %d fins abouties sur %d' % (len(rows), ns, ok, len(rows) - ns), file=sys.stderr)
