#!/usr/bin/env python3
"""fins_tsv.py TRACES [PREF=u] : tableau donnees/fins_upper*.tsv depuis les journaux tournee_greffe (mots $FF8000-$FF800E
a chaque changement ; 3e mot = $FF8004) des references TRACES/PREF_<perso>/journal.txt : 1re image a $A (debut_A),
1re image suivante a une autre valeur (fin_A), duree, scene suivante. « - » si absente."""
import sys, glob, os, re
T = sys.argv[1]; P = sys.argv[2] if len(sys.argv) > 2 else 'u'
print('perso\tdebut_A\tfin_A\tduree\tscene_suivante')
for d in sorted(glob.glob(os.path.join(T, P + '_??'))):
    p = os.path.basename(d)[len(P) + 1:]
    deb = fin = suiv = None
    for l in open(os.path.join(d, 'journal.txt'), encoding='utf-8', errors='replace'):
        m = re.match(r'\s*(\d+) : (\w{4}) (\w{4}) (\w{4})', l)
        if not m: continue
        k, w = int(m.group(1)), m.group(4)
        if deb is None and w == '000a': deb = k
        elif deb is not None and w != '000a': fin, suiv = k, w; break
    print('%s\t%s\t%s\t%s\t%s' % (p, deb if deb is not None else '-', fin if fin is not None else '-',
                                  fin - deb if fin is not None else '-', suiv or '-'))
